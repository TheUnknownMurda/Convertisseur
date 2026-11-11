"""Archives : ZIP, 7Z, RAR, TAR, GZ, ISO… (7-Zip) -> ZIP, 7Z, TAR, TAR.GZ ou dossier ; compresser des fichiers."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

from ..util import NO_WINDOW, FinalError, UserError, unique_path

PY_READABLE = {"zip", "tar", "tgz", "gz", "bz2", "tbz2", "xz", "txz"}


def _run7z(ctx, args, what):
    exe = ctx.tools.get("sevenzip")
    if not exe:
        raise UserError("7-Zip est nécessaire pour ce type d'archive.")
    proc = subprocess.Popen([exe, *args, "-bsp1", "-bso0", "-y"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=NO_WINDOW)
    for raw in proc.stdout:
        m = re.search(rb"(\d+)%", raw)
        if m:
            ctx.progress(int(m.group(1)) / 100, what)
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() not in (0, 1):                      # 1 = avertissement (fichiers ignorés)
        if "password" in err.lower() or "mot de passe" in err.lower():
            raise FinalError("Cette archive est protégée par un mot de passe.")
        raise FinalError("7-Zip n'a pas pu traiter l'archive : " + err.strip()[-300:])


def extract(ctx, src, sfmt, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    if ctx.tools.get("sevenzip"):
        _run7z(ctx, ["x", str(src), f"-o{outdir}"], "Extraction…")
        inner = [p for p in outdir.iterdir()]
        if len(inner) == 1 and inner[0].suffix.lower() == ".tar":        # .tar.gz : deuxième niveau
            tar = inner[0]
            _run7z(ctx, ["x", str(tar), f"-o{outdir}"], "Extraction…")
            tar.unlink(missing_ok=True)
    elif sfmt in PY_READABLE:
        ctx.progress(None, "Extraction…")
        try:
            shutil.unpack_archive(str(src), str(outdir))
        except (shutil.ReadError, ValueError):
            if sfmt == "zip":
                with zipfile.ZipFile(src) as z:
                    z.extractall(outdir)
            else:
                with tarfile.open(src) as t:
                    t.extractall(outdir, filter="data")
    else:
        raise UserError("7-Zip est nécessaire pour ce type d'archive.")
    if not any(outdir.rglob("*")):
        raise FinalError("L'archive est vide.")
    return outdir


def pack(ctx, folder: Path, dst: Path, kind: str, names=None) -> Path:
    """Compresse le contenu de folder (ou la liste names de fichiers) dans dst."""
    files = names or [p for p in sorted(folder.rglob("*")) if p.is_file()]
    base = folder if names is None else None
    ctx.progress(None, "Compression…")
    if kind == "7z":
        if base is not None:
            _run7z(ctx, ["a", "-t7z", "-mx=7", str(dst), str(folder / "*")], "Compression…")
        else:
            lst = ctx.tmp / "liste.txt"
            lst.write_text("\n".join(str(f) for f in files), encoding="utf-8")
            _run7z(ctx, ["a", "-t7z", "-mx=7", "-scsUTF-8", str(dst), f"@{lst}"], "Compression…")
        return dst
    if kind == "zip":
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as z:
            for i, f in enumerate(files):
                z.write(f, f.relative_to(base) if base else f.name)
                ctx.progress((i + 1) / len(files))
        return dst
    mode = "w:gz" if kind == "tgz" else "w"
    with tarfile.open(dst, mode) as t:
        for i, f in enumerate(files):
            t.add(f, arcname=str(f.relative_to(base) if base else f.name))
            ctx.progress((i + 1) / len(files))
    return dst


def convert(ctx, src, sfmt, dst, d):
    work = extract(ctx, src, sfmt, ctx.tmp / "extrait")
    dst = Path(dst)
    if d == "folder":
        target = unique_path(dst.parent, ctx.stem)
        shutil.move(str(work), str(target))
        return [target]
    return [pack(ctx, work, dst, d)]


def combine(ctx, items, dst_dir: Path, kind: str) -> list[Path]:
    ext = {"zip": "zip", "7z": "7z"}.get(kind, "zip")
    dst = dst_dir / f"{ctx.stem} (archive).{ext}"
    seen, files = set(), []
    for path, _, name in items:
        if Path(path).name in seen:            # deux fichiers de même nom : on garde le premier
            continue
        seen.add(Path(path).name)
        files.append(Path(path))
    return [pack(ctx, files[0].parent, dst, ext, names=files)]
