"""Identification des fichiers (format de routage, famille, métadonnées) et vignettes."""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import formats as F
from .util import NO_WINDOW


def classify(tools: dict, path, name: str) -> dict:
    ext = Path(name).suffix.lower().lstrip(".")
    fmt, family, meta = ext, F.EXT_FAMILY.get(ext), {}
    try:
        if family in ("video", "audio"):
            from .engines.media import probe_media
            info = probe_media(tools, path)
            meta = {k: info[k] for k in ("duration", "width", "height", "vcodec", "acodec") if info.get(k)}
            if family == "video" and not info["has_video"] and info["has_audio"]:
                fmt, family = "mka", "audio"          # conteneur vidéo sans image : traité comme audio
            if not info["has_video"] and not info["has_audio"]:
                meta["unreadable"] = True
        elif ext in ("png", "webp", "gif", "apng"):
            from PIL import Image
            with Image.open(path) as im:
                frames = getattr(im, "n_frames", 1)
                meta = {"width": im.width, "height": im.height}
                if frames > 1:
                    meta["frames"] = frames
            if ext == "png" and frames > 1:
                fmt, family = "apng", "anim"
            elif ext == "webp" and frames > 1:
                fmt, family = "webp_anim", "anim"
            elif ext == "apng" and frames <= 1:
                fmt, family = "png", "image"
        elif family == "image" and ext not in F.SVG_IN:
            from PIL import Image
            if ext in F.HEIC_IN:
                import pillow_heif
                pillow_heif.register_heif_opener()
            with Image.open(path) as im:
                w, h = im.size
                try:
                    if im.getexif().get(0x0112, 1) in (5, 6, 7, 8):
                        w, h = h, w
                except Exception:
                    pass
                meta = {"width": w, "height": h}
        elif family == "pdf":
            import pymupdf
            with pymupdf.open(str(path)) as doc:
                meta = {"pages": doc.page_count}
                if doc.needs_pass:
                    meta["encrypted"] = True
    except Exception:
        meta["unreadable"] = True
    return {"ext": ext, "fmt": fmt, "family": family, "meta": meta}


def thumbnail(tools: dict, path, fmt: str, family: str, out: Path, size: int = 160) -> bool:
    """Crée une vignette PNG ; retourne False si le type ne s'y prête pas."""
    try:
        if family in ("video", "audio"):
            ffmpeg = tools.get("ffmpeg")
            if not ffmpeg:
                return False
            from .engines.media import probe_media
            info = probe_media(tools, path)
            if not info["has_video"] and not info["attached_pic"]:
                return False
            at = min(5.0, (info.get("duration") or 0) * 0.1) if info["has_video"] else 0
            vf = f"scale={size}:{size}:force_original_aspect_ratio=decrease"
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.2f}", "-i", str(path),
                            "-frames:v", "1", "-vf", vf, "-an", "-update", "1", str(out)],
                           capture_output=True, timeout=60, creationflags=NO_WINDOW)
            return out.exists() and out.stat().st_size > 0
        if family in ("image", "anim"):
            from PIL import Image
            from .engines.images import normalize, open_image, svg_render
            if fmt in F.SVG_IN:
                img = svg_render(path, width=size * 2)
            elif family == "anim":
                img = Image.open(path)
                img.seek(0)
                img = img.convert("RGBA")
            else:
                img = open_image(path, fmt, min_side=1)
            img = normalize(img)
            img.thumbnail((size, size), Image.LANCZOS)
            img.save(out, "PNG")
            return True
        if family == "pdf" or fmt in ("epub", "mobi", "fb2", "fbz", "cbz"):
            import pymupdf
            with pymupdf.open(str(path)) as doc:
                if doc.needs_pass or doc.page_count == 0:
                    return False
                page = doc[0]
                zoom = size / max(page.rect.width, page.rect.height)
                page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False).save(str(out))
            return True
    except Exception:
        return False
    return False
