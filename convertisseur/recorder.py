"""Enregistreur d'écran (avec ou sans micro) et de micro, avec FFmpeg (gdigrab, dshow)."""
from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

from .i18n import tr
from .util import NO_WINDOW, UserError, unique_path

TEST = bool(os.environ.get("CONVERTISSEUR_RECORD_TEST"))   # tests : sources synthétiques au lieu de l'écran et du micro


def list_microphones(ffmpeg: str) -> list[str]:
    if TEST:
        return ["Micro de test"]
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                           capture_output=True, timeout=20, creationflags=NO_WINDOW)
    except Exception:
        return []
    text = r.stderr.decode("utf-8", "replace")
    return list(dict.fromkeys(m.group(1) for m in re.finditer(r'"([^"]+)"\s*\(audio\)', text)))


class Recorder:
    def __init__(self):
        self.proc: subprocess.Popen | None = None
        self.lock = threading.Lock()
        self.kind = None
        self.started = 0.0
        self.temp: Path | None = None
        self.final: Path | None = None
        self.errors: deque = deque(maxlen=30)

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def status(self) -> dict:
        size = self.temp.stat().st_size if self.temp and self.temp.exists() else 0
        return {"running": self.running, "kind": self.kind, "elapsed": time.time() - self.started if self.running else 0,
                "size": size}

    def start(self, tools: dict, out_dir: Path, kind: str, mic: str | None, fps: int = 30, gpu: str | None = None) -> dict:
        ffmpeg = tools.get("ffmpeg")
        if not ffmpeg:
            raise UserError("FFmpeg est nécessaire pour enregistrer.")
        with self.lock:
            if self.running:
                raise UserError("Un enregistrement est déjà en cours.")
            if kind == "audio" and not mic:
                raise UserError("Choisissez un micro.")
            out_dir = Path(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            stamp = dt.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            fps = int(fps) if int(fps) in (15, 24, 30, 60) else 30
            inputs, codec = [], []
            if kind == "screen":
                inputs += (["-re", "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate={fps}"] if TEST else
                           ["-f", "gdigrab", "-framerate", str(fps), "-draw_mouse", "1", "-i", "desktop"])
                codec += (["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23"] if gpu == "nvenc" else
                          ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23"])
                codec += ["-pix_fmt", "yuv420p", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"]
                self.temp = unique_path(out_dir, f".enregistrement {stamp}.mkv")
                self.final = unique_path(out_dir, tr("Enregistrement d'écran") + f" {stamp}.mp4")
            else:
                self.temp = unique_path(out_dir, f".enregistrement {stamp}.mka")
                self.final = unique_path(out_dir, tr("Enregistrement audio") + f" {stamp}.mp3")
            if mic:
                inputs += (["-re", "-f", "lavfi", "-i", "sine=frequency=440"] if TEST else
                           ["-f", "dshow", "-audio_buffer_size", "50", "-i", f"audio={mic}"])
                codec += ["-c:a", "aac", "-b:a", "160k"] if kind == "screen" else ["-c:a", "flac"]
            maps = ["-map", "0:v:0"] + (["-map", "1:a:0"] if mic else []) if kind == "screen" else ["-map", "0:a:0"]
            cmd = [ffmpeg, "-hide_banner", "-y", "-loglevel", "error", *inputs, *maps, *codec, str(self.temp)]
            self.errors.clear()
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                         creationflags=NO_WINDOW)
            threading.Thread(target=self._drain, daemon=True).start()
            self.kind, self.started = kind, time.time()
        time.sleep(1.0)
        if not self.running:
            detail = " ".join(self.errors)[-300:]
            raise UserError("L'enregistrement n'a pas pu démarrer" + (f" : {detail}" if detail else "."))
        return self.status()

    def _drain(self):
        proc = self.proc
        for raw in proc.stderr:
            self.errors.append(raw.decode("utf-8", "replace").strip())

    def stop(self, tools: dict) -> Path:
        with self.lock:
            proc = self.proc
            if proc is None:
                raise UserError("Aucun enregistrement en cours.")
            try:
                proc.stdin.write(b"q")
                proc.stdin.flush()
                proc.wait(20)
            except Exception:
                proc.terminate()
                try:
                    proc.wait(10)
                except Exception:
                    proc.kill()
            self.proc = None
            temp, final, kind = self.temp, self.final, self.kind
        if not temp or not temp.exists() or temp.stat().st_size < 1000:
            raise UserError("L'enregistrement est vide.")
        codec = ["-c", "copy", "-movflags", "+faststart"] if kind == "screen" else ["-c:a", "libmp3lame", "-b:a", "192k"]
        r = subprocess.run([tools["ffmpeg"], "-hide_banner", "-y", "-loglevel", "error", "-i", str(temp), *codec,
                            str(final)], capture_output=True, timeout=600, creationflags=NO_WINDOW)
        if r.returncode == 0 and final.exists():
            temp.unlink(missing_ok=True)
            return final
        kept = temp.with_name(temp.name.lstrip("."))       # finalisation impossible : on garde la version brute
        temp.replace(kept)
        return kept
