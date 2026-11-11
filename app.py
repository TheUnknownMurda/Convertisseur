"""Convertisseur — application locale de conversion de fichiers.

Lance un petit serveur sur 127.0.0.1 et ouvre l'interface dans sa propre fenêtre (Edge en mode application).
Rien n'est envoyé sur Internet : tout est converti sur cet ordinateur.

    python app.py               ouvre l'application
    python app.py --no-window   serveur seul (pour le développement)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import queue
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
LOG_FILE = APP_DIR / "convertisseur.log"
if sys.stdout is None or sys.stderr is None:          # pythonw : pas de console
    _log_stream = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _log_stream
    sys.stderr = sys.stderr or _log_stream
sys.path.insert(0, str(APP_DIR))

from flask import Flask, Response, abort, jsonify, request, send_file, send_from_directory  # noqa: E402

from convertisseur import __version__, graph, meta  # noqa: E402
from convertisseur import formats as F  # noqa: E402
from convertisseur import tools as T  # noqa: E402
from convertisseur.util import NO_WINDOW, kill_tree, rmtree_quiet, safe_name  # noqa: E402

DEFAULT_PORT = 47821
INSTANCE_FILE = APP_DIR / ".instance.json"          # port + jeton de l'instance ouverte (Envoyer vers)
TOKEN = secrets.token_urlsafe(24)
DATA_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Convertisseur"
RUN_DIR = Path(tempfile.gettempdir()) / "convertisseur" / f"run-{os.getpid()}"
log = logging.getLogger("convertisseur")

TOOLS: dict = {}
TOOLS_READY = threading.Event()


def _python_for_workers() -> str:
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe" and exe.with_name("python.exe").exists():
        return str(exe.with_name("python.exe"))
    return str(exe)


PYTHON = _python_for_workers()


# ---------------------------------------------------------------- réglages
COOKIE_BROWSERS = ("none", "firefox", "edge", "chrome", "brave", "opera", "vivaldi", "chromium")


class Settings:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.data = {"output_dir": str(T.downloads_dir() / "Convertisseur"), "next_to_source": False,
                     "open_folder": False, "gpu": True, "parallel": 2, "cookies": "none", "favorites": []}
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.data.update({k: v for k, v in saved.items() if k in self.data})
        except Exception:
            pass

    def __getitem__(self, key):
        return self.data[key]

    def public(self) -> dict:
        return dict(self.data)

    def update(self, d: dict) -> dict:
        with self.lock:
            if d.get("output_dir"):
                self.data["output_dir"] = str(d["output_dir"]).strip()
            for k in ("next_to_source", "open_folder", "gpu"):
                if k in d:
                    self.data[k] = bool(d[k])
            if isinstance(d.get("favorites"), list):
                self.data["favorites"] = [f for f in d["favorites"] if isinstance(f, dict) and f.get("target")][:50]
            if d.get("cookies") in COOKIE_BROWSERS:
                self.data["cookies"] = d["cookies"]
            if "parallel" in d:
                try:
                    self.data["parallel"] = max(1, min(4, int(d["parallel"])))
                except (TypeError, ValueError):
                    pass
            try:
                self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
            except OSError as e:
                log.warning("Réglages non enregistrés : %s", e)
        return self.public()


SETTINGS = Settings(APP_DIR / "config.json")


# ---------------------------------------------------------------- fichiers
class FileStore:
    def __init__(self):
        self.files: dict[str, dict] = {}
        self.lock = threading.Lock()

    def add(self, path: Path, name: str, temp: bool) -> dict:
        TOOLS_READY.wait(20)
        if not temp:
            with self.lock:
                for rec in self.files.values():
                    if not rec["temp"] and rec.get("path") and Path(rec["path"]) == path:
                        return rec
        info = meta.classify(TOOLS, path, name)
        rec = {"id": uuid.uuid4().hex[:12], "name": name, "path": str(path), "temp": temp,
               "size": path.stat().st_size, **info}
        with self.lock:
            self.files[rec["id"]] = rec
        return rec

    def add_link(self, item: dict) -> dict:
        with self.lock:
            for rec in self.files.values():
                if rec.get("url") == item["url"]:
                    return rec
        ext = "mp4" if item["has_video"] else "m4a"
        meta_ = {k: item[k] for k in ("duration", "width", "height", "site", "uploader") if item.get(k)}
        rec = {"id": uuid.uuid4().hex[:12], "name": f'{safe_name(item["title"])[:150]}.{ext}', "path": None,
               "temp": False, "url": item["url"], "thumb_url": item.get("thumbnail"), "size": None,
               "ext": ext, "fmt": ext, "family": "video" if item["has_video"] else "audio", "meta": meta_}
        with self.lock:
            self.files[rec["id"]] = rec
        return rec

    def add_web(self, url: str, title: str) -> dict:
        with self.lock:
            for rec in self.files.values():
                if rec.get("url") == url and rec["family"] == "web":
                    return rec
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        rec = {"id": uuid.uuid4().hex[:12], "name": f"{safe_name(title)[:150]}.html", "path": None, "temp": False,
               "url": url, "thumb_url": None, "size": None, "ext": "webpage", "fmt": "webpage", "family": "web",
               "meta": {"site": host}}
        with self.lock:
            self.files[rec["id"]] = rec
        return rec

    def get(self, fid) -> dict:
        rec = self.files.get(fid)
        if not rec:
            abort(404)
        return rec

    def remove(self, fid) -> None:
        with self.lock:
            rec = self.files.pop(fid, None)
        if rec and rec["temp"]:
            rmtree_quiet(Path(rec["path"]).parent)

    @staticmethod
    def public(rec: dict) -> dict:
        targets = graph.targets_for(rec["fmt"], rec["ext"], rec["family"], TOOLS) if rec["family"] else []
        return {"id": rec["id"], "name": rec["name"], "ext": rec["ext"], "fmt": rec["fmt"], "family": rec["family"],
                "family_label": F.FAMILY_LABEL.get(rec["family"], "Inconnu"), "size": rec["size"],
                "meta": rec["meta"], "targets": targets,
                "default": graph.default_target(rec["family"], rec["ext"], targets) if targets else None,
                "source": rec.get("url") or (None if rec["temp"] else rec["path"]), "url": rec.get("url")}


FILES = FileStore()


# ---------------------------------------------------------------- tâches
class Job:
    def __init__(self, mode, recs, target, options, out_dir):
        self.id = uuid.uuid4().hex[:12]
        self.mode, self.recs, self.target, self.options, self.out_dir = mode, recs, target, options, out_dir
        self.status, self.progress, self.message = "queued", 0.0, "En attente…"
        self.outputs: list[str] = []
        self.error = None
        self.created, self.started, self.ended = time.time(), None, None
        self.proc = None
        self.cancel_requested = False

    def public(self) -> dict:
        outs = []
        for p in self.outputs:
            pp = Path(p)
            try:
                if pp.is_dir():
                    files = [f for f in pp.iterdir() if f.is_file()]
                    outs.append({"name": pp.name, "path": str(pp), "is_dir": True, "count": len(files),
                                 "size": sum(f.stat().st_size for f in files)})
                else:
                    outs.append({"name": pp.name, "path": str(pp), "is_dir": False, "size": pp.stat().st_size})
            except OSError:
                outs.append({"name": pp.name, "path": str(pp), "is_dir": False, "size": 0, "missing": True})
        return {"id": self.id, "mode": self.mode, "file_ids": [r["id"] for r in self.recs],
                "names": [r["name"] for r in self.recs], "target": self.target, "status": self.status,
                "progress": self.progress, "message": self.message, "outputs": outs, "error": self.error,
                "created": self.created, "started": self.started, "ended": self.ended}


class History:
    """Conversions terminées, conservées d'un lancement à l'autre (200 au plus)."""

    def __init__(self, path: Path):
        self.path, self.lock = path, threading.Lock()
        try:
            self.items = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            self.items = []

    def add(self, job):
        label = F.COMBINE[job.mode]["label"] if job.mode in F.COMBINE else F.OUT.get(job.target, ("?",))[0]
        entry = {"id": job.id, "date": time.time(), "names": [r["name"] for r in job.recs], "target": label,
                 "outputs": list(job.outputs)}
        with self.lock:
            self.items = ([entry] + [i for i in self.items if i.get("id") != job.id])[:200]
            self._save()

    def clear(self):
        with self.lock:
            self.items = []
            self._save()

    def _save(self):
        try:
            self.path.write_text(json.dumps(self.items, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass

    def public(self):
        out = []
        for e in self.items:
            outs = [{"path": o, "name": Path(o).name, "exists": Path(o).exists()} for o in e.get("outputs", [])]
            out.append({**e, "outputs": outs})
        return out


HISTORY = History(APP_DIR / "historique.json")


class JobManager:
    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self.order: list[str] = []
        self.cv = threading.Condition()
        threading.Thread(target=self._dispatch, daemon=True, name="dispatch").start()

    def active(self) -> int:
        return sum(1 for j in self.jobs.values() if j.status in ("queued", "running"))

    def submit(self, mode, recs, target, options) -> Job:
        out_dir = Path(SETTINGS["output_dir"])
        if SETTINGS["next_to_source"] and len(recs) == 1 and not recs[0]["temp"] and recs[0].get("path"):
            parent = Path(recs[0]["path"]).parent
            if os.access(parent, os.W_OK):
                out_dir = parent
        out_dir.mkdir(parents=True, exist_ok=True)
        job = Job(mode, recs, target, options, out_dir)
        with self.cv:
            self.jobs[job.id] = job
            self.order.append(job.id)
            self.cv.notify_all()
        return job

    def _dispatch(self):
        while True:
            with self.cv:
                while True:
                    running = sum(1 for j in self.jobs.values() if j.status == "running")
                    queued = [self.jobs[i] for i in self.order if self.jobs[i].status == "queued"]
                    if queued and running < SETTINGS["parallel"]:
                        job = queued[0]
                        job.status, job.started, job.message = "running", time.time(), "Démarrage…"
                        break
                    self.cv.wait(1.0)
            threading.Thread(target=self._run, args=(job,), daemon=True, name=f"job-{job.id}").start()

    def _run(self, job: Job):
        work = RUN_DIR / "jobs" / job.id
        work.mkdir(parents=True, exist_ok=True)
        spec = {"job_id": job.id, "mode": job.mode, "target": job.target, "options": job.options,
                "tools": TOOLS, "gpu": TOOLS.get("gpu") if SETTINGS["gpu"] else None, "cookies": SETTINGS["cookies"],
                "out_dir": str(job.out_dir), "tmp_dir": str(work / "tmp"),
                "inputs": [{"path": r["path"], "name": r["name"], "fmt": r["fmt"], "family": r["family"],
                            "url": r.get("url")} for r in job.recs]}
        spec_path = work / "tache.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        result, errors = None, []
        try:
            proc = subprocess.Popen([PYTHON, "-X", "utf8", "-m", "convertisseur.worker", str(spec_path)],
                                    cwd=str(APP_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    creationflags=NO_WINDOW)
            job.proc = proc

            def drain():
                for raw in proc.stderr:
                    errors.append(raw.decode("utf-8", "replace").rstrip())
                    del errors[:-60]
            t = threading.Thread(target=drain, daemon=True)
            t.start()
            for raw in proc.stdout:
                try:
                    msg = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if "done" in msg or "error" in msg:
                    result = msg
                    continue
                job.progress = msg.get("p")
                if msg.get("m"):
                    job.message = msg["m"]
            rc = proc.wait()
            t.join(2)
        except Exception as e:  # lancement impossible
            rc, errors = -1, [str(e)]
        job.ended = time.time()
        if job.cancel_requested:
            job.status, job.message = "canceled", "Annulé"
            rmtree_quiet(job.out_dir / f".convertisseur-{job.id}")
        elif result and result.get("done"):
            job.status, job.progress, job.message = "done", 1.0, "Terminé"
            job.outputs = result.get("outputs", [])
            HISTORY.add(job)
            if SETTINGS["open_folder"] and job.outputs:
                reveal(job.outputs[0])
        else:
            job.status = "error"
            job.error = (result or {}).get("error") or f"Le convertisseur s'est arrêté de façon inattendue (code {rc})."
            rmtree_quiet(job.out_dir / f".convertisseur-{job.id}")
        if job.status == "error" or (errors and job.status != "done"):
            log.warning("Tâche %s (%s -> %s) : %s\n%s", job.id, [r["name"] for r in job.recs], job.target,
                        job.error, "\n".join(errors[-25:]))
        rmtree_quiet(work)
        with self.cv:
            self.cv.notify_all()

    def cancel(self, jid) -> Job:
        job = self.jobs.get(jid)
        if not job:
            abort(404)
        with self.cv:
            if job.status == "queued":
                job.status, job.message = "canceled", "Annulé"
            elif job.status == "running":
                job.cancel_requested = True
                job.message = "Annulation…"
                if job.proc:
                    kill_tree(job.proc.pid)
        return job

    def shutdown(self):
        for job in list(self.jobs.values()):
            if job.status in ("queued", "running"):
                job.cancel_requested = True
                job.status = "canceled"
                if job.proc:
                    kill_tree(job.proc.pid)
                rmtree_quiet(job.out_dir / f".convertisseur-{job.id}")


JOBS = JobManager()


# ---------------------------------------------------------------- dialogues Windows (fil dédié à Tk)
class Dialogs:
    def __init__(self):
        self.q: queue.Queue = queue.Queue()
        self.available = True
        threading.Thread(target=self._loop, daemon=True, name="dialogs").start()

    def _loop(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
        except Exception as e:
            log.warning("Dialogues indisponibles : %s", e)
            self.available = False
            root = None
        while True:
            kind, args, reply = self.q.get()
            if root is None:
                reply.put(None)
                continue
            try:
                root.lift()
                root.update()
                if kind == "files":
                    res = filedialog.askopenfilenames(parent=root, title=args.get("title") or "Choisir des fichiers",
                                                      filetypes=args.get("filetypes") or [("Tous les fichiers", "*.*")])
                    res = list(root.tk.splitlist(res)) if isinstance(res, str) else list(res or [])
                else:
                    res = filedialog.askdirectory(parent=root, title=args.get("title") or "Choisir un dossier",
                                                  initialdir=args.get("initial") or None, mustexist=False)
                root.update()
                reply.put(res)
            except Exception as e:
                log.warning("Dialogue : %s", e)
                reply.put(None)

    def ask(self, kind, **args):
        if not self.available:
            return None
        reply: queue.Queue = queue.Queue()
        self.q.put((kind, args, reply))
        return reply.get()


DIALOGS = Dialogs()


def reveal(path) -> None:
    p = Path(path)
    try:
        if p.is_dir():
            os.startfile(str(p))
        else:
            subprocess.Popen(f'explorer /select,"{p}"')
    except Exception as e:
        log.warning("Explorateur : %s", e)


# ---------------------------------------------------------------- serveur web
app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = None
STATE = {"last_seen": time.time(), "bye_at": None}


def bad(msg, code=400):
    return jsonify({"error": msg}), code


@app.before_request
def guard():
    host = (request.host or "").rsplit(":", 1)[0]
    if host not in ("127.0.0.1", "localhost"):
        abort(403)
    if request.path.startswith("/api/") and request.path != "/api/ping":
        token = request.headers.get("X-Token") or request.args.get("t") or ""
        if not secrets.compare_digest(token, TOKEN):
            abort(403)
        STATE["last_seen"] = time.time()


@app.get("/")
def index():
    page = (APP_DIR / "web" / "index.html").read_text(encoding="utf-8")
    page = page.replace("{{TOKEN}}", TOKEN).replace("{{VERSION}}", __version__)
    return Response(page, headers={"Cache-Control": "no-store", "Content-Type": "text/html; charset=utf-8"})


@app.get("/web/<path:name>")
def web(name):
    resp = send_from_directory(APP_DIR / "web", name)
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.get("/api/ping")
def ping():
    return jsonify({"app": "convertisseur", "version": __version__})


def tools_public() -> dict:
    """État des moteurs pour l'interface."""
    gpu = TOOLS.get("gpu")
    return {"ffmpeg": TOOLS.get("ffmpeg_version") if TOOLS.get("ffmpeg") else None,
            "gpu": T.GPU_ENCODERS[gpu][2] if gpu else None, "edge": bool(TOOLS.get("edge")),
            "libreoffice": bool(TOOLS.get("soffice")), "calibre": bool(TOOLS.get("calibre")),
            "voices": [v["name"] for v in TOOLS.get("voices") or []], "ocr": TOOLS.get("ocr"),
            "whisper": bool(TOOLS.get("whisper")), "whisper_models": TOOLS.get("whisper_models") or [],
            "whisper_gpu": bool(TOOLS.get("whisper_gpu")), "ytdlp": TOOLS.get("ytdlp_version"),
            "js_runtime": bool(T.find_node()), "sevenzip": bool(TOOLS.get("sevenzip"))}


@app.get("/api/state")
def state():
    TOOLS_READY.wait(20)
    return jsonify({
        "version": __version__, "presets": F.presets_for_client(), "options": F.OPTIONS, "combine": F.COMBINE,
        "groups": F.GROUP_ORDER, "families": F.FAMILY_LABEL,
        "ext_family": {e: f for e, f in F.EXT_FAMILY.items() if e != "webp_anim"},
        "tools": tools_public(), "settings": SETTINGS.public(),
        "files": [FileStore.public(r) for r in FILES.files.values()],
        "jobs": [j.public() for j in JOBS.jobs.values()],
    })


@app.post("/api/upload")
def upload():
    name = safe_name(request.args.get("name") or "fichier")
    folder = RUN_DIR / "imports" / uuid.uuid4().hex[:10]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    try:
        with open(path, "wb") as f:
            while True:
                chunk = request.stream.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        rmtree_quiet(folder)
        return bad(f"Import interrompu : {e}")
    return jsonify(FileStore.public(FILES.add(path, name, temp=True)))


@app.post("/api/pick")
def pick():
    data = request.get_json(silent=True) or {}
    accept = data.get("accept") or []
    filetypes = []
    if accept:
        filetypes.append(("Fichiers pris en charge", " ".join(f"*.{e}" for e in accept)))
    filetypes.append(("Tous les fichiers", "*.*"))
    if not DIALOGS.available:
        return jsonify({"unavailable": True})
    paths = DIALOGS.ask("files", filetypes=filetypes, title="Choisir des fichiers à convertir")
    if paths is None:
        return jsonify({"unavailable": True})
    recs = []
    for p in paths:
        pp = Path(p)
        if pp.is_file():
            recs.append(FileStore.public(FILES.add(pp, pp.name, temp=False)))
    return jsonify({"files": recs})


@app.post("/api/link")
def add_link():
    import re
    url = ((request.get_json(silent=True) or {}).get("url") or "").strip()
    if not re.match(r"^https?://\S+$", url, re.I):
        return bad("Collez une adresse complète, qui commence par https://")
    if not TOOLS.get("ytdlp_version"):
        return bad("Le module de téléchargement (yt-dlp) est manquant.")
    from convertisseur.engines.download import probe_link
    from convertisseur.util import UserError
    from convertisseur.engines.web import page_title
    if (request.get_json(silent=True) or {}).get("web"):
        return jsonify({"files": [FileStore.public(FILES.add_web(url, page_title(url)))]})
    try:
        items = probe_link(TOOLS, url, SETTINGS["cookies"])
    except UserError as e:
        if str(e).startswith("Lien non reconnu") and TOOLS.get("edge"):       # page web ordinaire
            return jsonify({"files": [FileStore.public(FILES.add_web(url, page_title(url)))]})
        return bad(str(e))
    except Exception as e:
        log.exception("Analyse du lien")
        return bad(f"Analyse du lien impossible : {e}")
    return jsonify({"files": [FileStore.public(FILES.add_link(it)) for it in items]})


@app.post("/api/update-ytdlp")
def update_ytdlp():
    r = subprocess.run([PYTHON, "-m", "pip", "install", "--disable-pip-version-check", "-U", "yt-dlp[default]"],
                       capture_output=True, timeout=900, creationflags=NO_WINDOW)
    TOOLS["ytdlp_version"] = T.ytdlp_version(fresh=True)
    if r.returncode != 0:
        return bad("La mise à jour a échoué : " + r.stderr.decode("utf-8", "replace").strip()[-300:])
    return jsonify({"ok": True, "version": TOOLS["ytdlp_version"]})


@app.get("/api/history")
def history():
    return jsonify(HISTORY.public())


@app.post("/api/history/clear")
def history_clear():
    HISTORY.clear()
    return jsonify({"ok": True})


@app.post("/api/history/open")
def history_open():
    data = request.get_json(silent=True) or {}
    paths = {o for e in HISTORY.items for o in e.get("outputs", [])}
    target = data.get("path")
    if target not in paths or not Path(target).exists():
        return bad("Ce fichier a été déplacé ou supprimé.")
    if data.get("reveal"):
        reveal(target)
    else:
        os.startfile(target)
    return jsonify({"ok": True})


INBOX: list[str] = []


def add_paths(paths) -> list[dict]:
    recs = []
    for raw in paths:
        pp = Path(raw)
        if pp.is_file():
            recs.append(FILES.add(pp, pp.name, temp=False))
        elif pp.is_dir():
            for f in sorted(x for x in pp.rglob("*") if x.is_file())[:500]:
                recs.append(FILES.add(f, f.name, temp=False))
    return recs


@app.post("/api/add-paths")
def api_add_paths():
    recs = add_paths((request.get_json(silent=True) or {}).get("paths") or [])
    INBOX.extend(r["id"] for r in recs)
    return jsonify({"ok": True, "count": len(recs)})


@app.get("/api/inbox")
def inbox():
    ids, INBOX[:] = list(INBOX), []
    return jsonify({"files": [FileStore.public(FILES.files[i]) for i in ids if i in FILES.files]})


@app.post("/api/sendto")
def sendto_shortcut():
    sendto = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "SendTo"
    if not sendto.is_dir():
        return bad("Dossier « Envoyer vers » introuvable.")
    return make_shortcut(sendto / "Convertisseur.lnk")


@app.post("/api/files/remove")
def remove_files():
    for fid in (request.get_json(silent=True) or {}).get("ids", []):
        FILES.remove(fid)
    return jsonify({"ok": True})


THUMB_LOCK = threading.Semaphore(3)


def remote_thumbnail(url: str, out: Path, size: int = 160) -> bool:
    import io
    from PIL import Image
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read(8_000_000)
        img = Image.open(io.BytesIO(data))
        img.thumbnail((size * 2, size * 2), Image.LANCZOS)
        img.convert("RGB").save(out, "PNG")
        return True
    except Exception:
        return False


@app.get("/api/thumb/<fid>")
def thumb(fid):
    rec = FILES.get(fid)
    folder = RUN_DIR / "vignettes"
    folder.mkdir(parents=True, exist_ok=True)
    out, none = folder / f"{fid}.png", folder / f"{fid}.none"
    if not out.exists() and not none.exists():
        with THUMB_LOCK:
            if rec.get("url"):
                ok = bool(rec.get("thumb_url")) and remote_thumbnail(rec["thumb_url"], out)
            else:
                ok = meta.thumbnail(TOOLS, Path(rec["path"]), rec["fmt"], rec["family"] or "", out)
            if not ok and not out.exists():
                none.touch()
    if out.exists():
        resp = send_file(out, mimetype="image/png")
        resp.headers["Cache-Control"] = "max-age=3600"
        return resp
    return Response(status=204)


@app.post("/api/convert")
def convert():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode") or "single"
    ids = data.get("file_ids") or []
    recs = [FILES.files.get(i) for i in ids]
    if not recs or any(r is None for r in recs):
        return bad("Fichier introuvable : réimportez-le.")
    try:
        if mode == "single":
            rec = recs[0]
            targets = graph.targets_for(rec["fmt"], rec["ext"], rec["family"], TOOLS) if rec["family"] else []
            target = next((t for t in targets if t["id"] == data.get("target")), None)
            if not target:
                return bad("Format de sortie non proposé pour ce fichier.")
            if not target["ok"]:
                return bad(target["reason"] or "Conversion indisponible.")
            options = F.clean_options(target["options"], data.get("options"))
            job = JOBS.submit("single", [rec], target["id"], options)
        elif mode in F.COMBINE:
            spec = F.COMBINE[mode]
            if any(not r.get("path") for r in recs):
                return bad("Les liens doivent d'abord être convertis en fichiers.")
            if spec["families"] != "*" and any(r["family"] not in spec["families"] for r in recs):
                return bad("Certains fichiers ne peuvent pas être assemblés ainsi.")
            options = F.clean_options(spec["options"], data.get("options"))
            job = JOBS.submit(mode, recs, None, options)
        else:
            return bad("Mode inconnu.")
    except OSError as e:
        return bad(f"Dossier de sortie inaccessible ({SETTINGS['output_dir']}) : {e.strerror or e}")
    return jsonify(job.public())


@app.get("/api/jobs")
def jobs():
    return jsonify([j.public() for j in JOBS.jobs.values()])


@app.post("/api/jobs/<jid>/cancel")
def cancel(jid):
    return jsonify(JOBS.cancel(jid).public())


def _output(data) -> Path:
    job = JOBS.jobs.get(data.get("job_id"))
    if not job or job.status != "done":
        abort(404)
    try:
        return Path(job.outputs[int(data.get("index") or 0)])
    except (IndexError, ValueError):
        abort(404)


@app.post("/api/open")
def open_output():
    p = _output(request.get_json(silent=True) or {})
    if not p.exists():
        return bad("Le fichier a été déplacé ou supprimé.")
    try:
        os.startfile(str(p))
    except OSError as e:
        return bad(f"Impossible d'ouvrir le fichier : {e}")
    return jsonify({"ok": True})


@app.post("/api/reveal")
def reveal_output():
    p = _output(request.get_json(silent=True) or {})
    if not p.exists():
        return bad("Le fichier a été déplacé ou supprimé.")
    reveal(p)
    return jsonify({"ok": True})


@app.post("/api/open-folder")
def open_folder():
    folder = Path(SETTINGS["output_dir"])
    folder.mkdir(parents=True, exist_ok=True)
    os.startfile(str(folder))
    return jsonify({"ok": True})


@app.get("/api/settings")
def get_settings():
    return jsonify(SETTINGS.public())


@app.post("/api/settings")
def set_settings():
    data = request.get_json(silent=True) or {}
    if data.get("output_dir"):
        try:
            Path(data["output_dir"]).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return bad(f"Dossier inutilisable : {e}")
    with JOBS.cv:
        result = SETTINGS.update(data)
        JOBS.cv.notify_all()
    return jsonify(result)


@app.post("/api/pick-folder")
def pick_folder():
    path = DIALOGS.ask("folder", initial=SETTINGS["output_dir"], title="Dossier où enregistrer les conversions")
    return jsonify({"path": path or None, "unavailable": not DIALOGS.available})


@app.post("/api/shortcut")
def shortcut():
    return make_shortcut(T.desktop_dir() / "Convertisseur.lnk")


def make_shortcut(lnk: Path):
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe") if exe.with_name("pythonw.exe").exists() else exe
    icon = APP_DIR / "web" / "logo.ico"     # nom neuf : Windows n'a pas l'ancien logo en cache
    q = lambda s: str(s).replace("'", "''")
    script = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{q(lnk)}'); "
              f"$s.TargetPath = '{q(pyw)}'; $s.Arguments = '\"{q(APP_DIR / 'app.py')}\"'; "
              f"$s.WorkingDirectory = '{q(APP_DIR)}'; $s.IconLocation = '{q(icon)}'; "
              f"$s.Description = 'Convertisseur de fichiers local'; $s.Save()")
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True,
                       timeout=30, creationflags=NO_WINDOW)
    if r.returncode != 0 or not lnk.exists():
        return bad("Impossible de créer le raccourci.")
    return jsonify({"ok": True, "path": str(lnk)})


@app.post("/api/heartbeat")
def heartbeat():
    STATE["bye_at"] = None
    return jsonify({"ok": True, "active": JOBS.active()})


@app.post("/api/bye")
def bye():
    STATE["bye_at"] = time.time()
    return jsonify({"ok": True})


# ---------------------------------------------------------------- démarrage
def detect_tools():
    global TOOLS
    try:
        basic = T.detect_basic()
        TOOLS.update(basic)
        TOOLS.update(T.detect_slow(basic))
        F.set_voice_choices(TOOLS.get("voices") or [])
        if TOOLS.get("whisper"):
            from convertisseur.engines.transcription import downloaded_models
            TOOLS["whisper_models"] = downloaded_models()
            from convertisseur.engines.transcription import cuda_available
            TOOLS["whisper_gpu"] = cuda_available()
            F.set_whisper_choices(TOOLS["whisper_models"])
        log.info("Outils : %s", {k: v for k, v in TOOLS.items() if k != "voices"})
    except Exception:
        log.exception("Détection des outils")
    finally:
        TOOLS_READY.set()


def port_free(port) -> bool:
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def instance_alive(port) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1.5) as r:
            return json.loads(r.read()).get("app") == "convertisseur"
    except Exception:
        return False


def open_window(url: str, browser_only=False):
    edge = T.find_edge()
    if edge and not browser_only:
        profile = DATA_DIR / "fenetre"
        profile.mkdir(parents=True, exist_ok=True)
        try:
            return subprocess.Popen([edge, f"--app={url}", f"--user-data-dir={profile}", "--no-first-run",
                                     "--no-default-browser-check", "--disable-sync", "--window-size=1320,880",
                                     "--disable-features=msEdgeSidebarV2,msUndersideButton"])
        except OSError as e:
            log.warning("Edge : %s", e)
    import webbrowser
    webbrowser.open(url)
    return None


def cleanup_old_runs():
    base = RUN_DIR.parent
    if not base.exists():
        return
    for d in base.glob("run-*"):
        if d != RUN_DIR and time.time() - d.stat().st_mtime > 6 * 3600:
            rmtree_quiet(d)


def main():
    ap = argparse.ArgumentParser(description="Convertisseur de fichiers local")
    ap.add_argument("--no-window", action="store_true", help="ne pas ouvrir de fenêtre")
    ap.add_argument("--browser", action="store_true", help="ouvrir dans le navigateur par défaut")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("files", nargs="*", help="fichiers ou dossiers à ajouter")
    args = ap.parse_args()
    logging.basicConfig(filename=str(LOG_FILE), level=logging.INFO, encoding="utf-8",
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    if instance_alive(args.port):
        if args.files and INSTANCE_FILE.exists():
            try:
                info = json.loads(INSTANCE_FILE.read_text(encoding="utf-8"))
                req = urllib.request.Request(f"http://127.0.0.1:{info['port']}/api/add-paths", method="POST",
                                             data=json.dumps({"paths": args.files}).encode(),
                                             headers={"Content-Type": "application/json", "X-Token": info["token"]})
                urllib.request.urlopen(req, timeout=60).read()
                return
            except Exception as e:
                log.warning("Envoi des fichiers à l'instance ouverte : %s", e)
        if not args.no_window:
            open_window(f"http://127.0.0.1:{args.port}/", args.browser)
        return
    port = args.port if port_free(args.port) else 0
    from werkzeug.serving import make_server
    server = make_server("127.0.0.1", port, app, threaded=True)
    port = server.server_port
    url = f"http://127.0.0.1:{port}/"
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=cleanup_old_runs, daemon=True).start()
    threading.Thread(target=detect_tools, daemon=True, name="tools").start()
    threading.Thread(target=server.serve_forever, daemon=True, name="http").start()
    log.info("Convertisseur %s sur %s", __version__, url)
    try:
        INSTANCE_FILE.write_text(json.dumps({"port": port, "token": TOKEN, "pid": os.getpid()}), encoding="utf-8")
        T.hide_file(INSTANCE_FILE) if hasattr(T, "hide_file") else None
    except OSError:
        pass
    if args.files:
        TOOLS_READY.wait(30)
        add_paths(args.files)
    print(f"Convertisseur prêt : {url}", flush=True)

    try:
        if args.no_window:
            while True:
                time.sleep(3600)
        proc = open_window(url, args.browser)
        started = time.time()
        if proc is not None:
            proc.wait()
            if time.time() - started > 6:          # fenêtre fermée par l'utilisateur
                return
        # Repli : la page signale sa fermeture (bye) ou cesse de donner signe de vie.
        STATE["last_seen"] = time.time()
        while True:
            time.sleep(2)
            idle = time.time() - STATE["last_seen"]
            bye = STATE["bye_at"]
            if bye and time.time() - bye > 8 and STATE["last_seen"] <= bye + 1:
                return
            if idle > 600 and not JOBS.active():
                return
    except KeyboardInterrupt:
        pass
    finally:
        JOBS.shutdown()
        server.shutdown()
        rmtree_quiet(RUN_DIR)
        try:
            if json.loads(INSTANCE_FILE.read_text(encoding="utf-8")).get("pid") == os.getpid():
                INSTANCE_FILE.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
