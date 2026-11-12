"""Processus de conversion lancé pour chaque tâche (annulable et isolé du serveur).

Usage : python -m convertisseur.worker tache.json
Protocole : une ligne JSON par message sur la sortie standard.
  {"p": 0.42, "m": "message"}       progression (p = null : indéterminée)
  {"done": true, "outputs": [...]}  succès
  {"error": "message"}              échec
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

from . import formats as F
from . import graph, i18n
from .i18n import tr
from .util import FinalError, UserError, hide_path, rmtree_quiet, safe_name, unique_path


class Ctx:
    def __init__(self, spec: dict, emit):
        self.spec, self.emit = spec, emit
        self.job_id = spec["job_id"]
        self.mode = spec.get("mode", "single")
        self.inputs = spec["inputs"]
        self.inp = self.inputs[0]
        self.target = spec.get("target")
        self.opts = spec.get("options") or {}
        self.tools = spec.get("tools") or {}
        self.gpu = spec.get("gpu")
        self.out_dir = Path(spec["out_dir"])
        self.tmp = Path(spec["tmp_dir"])
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.stage = self.out_dir / f".convertisseur-{self.job_id}"
        self.stem = safe_name(Path(self.inp["name"]).stem) or tr("fichier")
        self.last = True
        self.keep_alive: list = []
        self.tags: dict | None = None          # étiquettes à écrire dans le fichier final (Spotify)
        self.cover: bytes | None = None
        self._span = (0.0, 1.0)
        self._t = 0.0
        self._p = -1.0

    def progress(self, p=None, msg=None):
        a, b = self._span
        gp = None if p is None else a + (b - a) * max(0.0, min(1.0, float(p)))
        now = time.monotonic()
        if msg is None and gp is not None and now - self._t < 0.2 and gp < 0.999:
            return
        self._t = now
        self.emit({"p": None if gp is None else round(gp, 4), "m": msg})

    def stage_dir(self) -> Path:
        if not self.stage.exists():
            self.stage.mkdir(parents=True, exist_ok=True)
            hide_path(self.stage)
        return self.stage

    def finalize(self, outputs) -> list[Path]:
        final = []
        for p in outputs:
            p = Path(p)
            if p.parent == self.stage:
                dest = unique_path(self.out_dir, p.name)
                os.replace(p, dest)
                final.append(dest)
            else:
                final.append(p)
        rmtree_quiet(self.stage)
        return final


def _call(edge_fn: str):
    mod, fn = edge_fn.split(":")
    return getattr(importlib.import_module(f"convertisseur.engines.{mod}"), fn)


def run_path(ctx: Ctx, path: list[tuple], src: Path, base=(0.0, 1.0)) -> list[Path]:
    weights = [max(0.3, graph.EDGE_BY_NAME[e].cost_of(s, d)) for e, s, d in path]
    total = sum(weights)
    acc = 0.0
    lo, hi = base
    cur = Path(src)
    outs: list = []
    for i, (name, s, d) in enumerate(path):
        edge = graph.EDGE_BY_NAME[name]
        last = i == len(path) - 1
        ctx.last = last
        ctx._span = (lo + (hi - lo) * acc / total, lo + (hi - lo) * (acc + weights[i]) / total)
        acc += weights[i]
        ext = F.OUT[d][2] if d in F.OUT else d
        name = f"{ctx.stem}.{ext}"
        if last and d in F.SUFFIX:
            name = f"{ctx.stem} {tr(f'({F.SUFFIX[d]})')}.{ext}"
        elif last and ext.lower() == Path(ctx.inp["name"]).suffix.lstrip(".").lower():
            name = f"{ctx.stem} {tr('(converti)')}.{ext}"
        dst = (ctx.stage_dir() / name) if last else (ctx.tmp / f"etape{i + 1}.{ext}")
        if len(path) > 1:
            ctx.progress(0, f"Étape {i + 1}/{len(path)} : {F.OUT.get(s, (s.upper(),))[0] if s in F.OUT else s.upper()}"
                            f" → {F.OUT[d][0]}…")
        outs = _call(edge.fn)(ctx, cur, s, dst, d)
        if not outs or not Path(outs[0]).exists():
            raise UserError("La conversion n'a produit aucun fichier.")
        cur = Path(outs[0])
    return outs


def convert(ctx: Ctx) -> list[Path]:
    items = [(Path(i["path"] or "."), i["fmt"], i["name"]) for i in ctx.inputs]
    if ctx.mode != "single":
        from .engines import archives, images, media
        if ctx.mode == "combine_concat":
            return media.concat(ctx, items, ctx.out_dir)
        if ctx.mode == "combine_subs":
            return media.add_subtitles(ctx, items, ctx.out_dir)
        if ctx.mode == "combine_zip":
            return archives.combine(ctx, items, ctx.stage_dir(), ctx.opts.get("zip_fmt") or "zip",
                                    (ctx.opts.get("password") or "").strip())
        if ctx.mode in ("combine_logo", "combine_soundtrack", "combine_cover"):
            from .engines import mediatools
            return getattr(mediatools, ctx.mode)(ctx, items, ctx.out_dir)
        if ctx.mode == "combine_collage":
            from .engines import imagetools
            fmt = ctx.opts.get("collage_fmt") or "jpg"
            return imagetools.collage(ctx, items, ctx.stage_dir() / f"{ctx.stem} {tr('(collage)')}.{fmt}", ctx.opts)
        if ctx.mode in ("combine_rename", "combine_hash"):
            from .engines import filetools
            return getattr(filetools, ctx.mode)(ctx, items, ctx.stage_dir())
        ext = F.COMBINE[ctx.mode]["ext"]
        label = {"combine_pdf": "fusion", "combine_gif": "animation", "combine_video": "diaporama"}[ctx.mode]
        dst = ctx.stage_dir() / f"{ctx.stem} {tr(f'({label})')}.{ext}"
        fn = {"combine_pdf": lambda: images.images_to_pdf(ctx, items, dst, ctx.opts.get("img_page") or "a4"),
              "combine_gif": lambda: images.combine_gif(ctx, items, dst),
              "combine_video": lambda: images.combine_video(ctx, items, dst)}[ctx.mode]
        return fn()
    src, fmt, _ = items[0]
    base = (0.0, 1.0)
    if ctx.inp.get("family") == "web":          # page web : Edge s'en charge directement
        src, fmt = Path("page.webpage"), "webpage"
    elif ctx.inp.get("url"):                    # lien : téléchargement, puis conversion habituelle
        from . import meta
        from .engines.download import download
        src = download(ctx, ctx.inp["url"], ctx.target, (0.0, 0.7))
        fmt = meta.classify(ctx.tools, src, src.name)["fmt"] or src.suffix.lstrip(".").lower()
        o = ctx.opts
        untouched = (o.get("v_quality", "orig") == "orig" and not o.get("start") and not o.get("end")
                     and not o.get("mute"))
        if src.suffix.lower() == "." + F.OUT[ctx.target][2] and ctx.target in F.VIDEO_OUT and untouched:
            dst = ctx.stage_dir() / f"{ctx.stem}{src.suffix.lower()}"
            shutil.move(str(src), str(dst))
            return [dst]
        base = (0.7, 1.0)
    paths = graph.find_paths(fmt, ctx.target, ctx.tools, k=3)
    if not paths:
        raise UserError("Cette conversion n'est pas possible avec les outils installés.")
    first_error = None
    for k, path in enumerate(paths):
        try:
            if k:
                ctx._span = base
                ctx.progress(0, "Nouvel essai par un autre chemin…")
            outs = run_path(ctx, path, src, base)
            tags = dict(ctx.tags or {})          # morceau Spotify, puis étiquettes saisies dans les réglages
            for key, opt in (("title", "tag_title"), ("artist", "tag_artist"), ("album", "tag_album"), ("date", "tag_year")):
                if (ctx.opts.get(opt) or "").strip():
                    tags[key] = ctx.opts[opt].strip()
            if (tags or ctx.cover) and outs and Path(outs[0]).is_file():
                from .engines.download import write_tags
                write_tags(outs[0], tags, ctx.cover)
            return outs
        except FinalError:
            raise                    # le fichier lui-même bloque : un autre chemin n'y changerait rien
        except Exception as e:  # on tente le chemin suivant
            if first_error is None:
                first_error = e
            traceback.print_exc()
            rmtree_quiet(ctx.stage)
            for f in ctx.tmp.glob("etape*"):
                shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink(missing_ok=True)
    raise first_error


def _protocol():
    fd = os.dup(1)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    stream = os.fdopen(fd, "w", encoding="utf-8", buffering=1)

    def emit(obj):
        stream.write(json.dumps(obj, ensure_ascii=False) + "\n")
        stream.flush()
    return emit


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    i18n.set_lang(spec.get("lang"))
    emit = _protocol()
    ctx = Ctx(spec, emit)
    try:
        ctx.progress(0, "Préparation…")
        outputs = convert(ctx)
        final = ctx.finalize(outputs)
        emit({"done": True, "outputs": [str(p) for p in final]})
        return 0
    except UserError as e:
        rmtree_quiet(ctx.stage)
        emit({"error": str(e)})
    except MemoryError:
        rmtree_quiet(ctx.stage)
        emit({"error": "Mémoire insuffisante pour cette conversion."})
    except Exception as e:
        rmtree_quiet(ctx.stage)
        traceback.print_exc()
        emit({"error": f"Erreur inattendue : {type(e).__name__}: {e}"})
    return 1


if __name__ == "__main__":
    sys.exit(main())
