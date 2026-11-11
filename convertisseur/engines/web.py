"""Page web (lien) -> PDF, capture PNG/JPG ou HTML, avec Microsoft Edge en arrière-plan."""
from __future__ import annotations

import html as htmllib
import re
import subprocess
from pathlib import Path

from ..util import NO_WINDOW, FinalError, UserError


def capture(ctx, src, sfmt, dst, d):
    from .htmlconv import run_edge
    url = ctx.inp.get("url")
    if not url:
        raise FinalError("Aucune adresse de page web.")
    if not ctx.tools.get("edge") and d != "html":
        raise UserError("Microsoft Edge est nécessaire pour les pages web.")
    dst = Path(dst)
    if d == "pdf":
        ctx.progress(None, "Impression de la page en PDF…")
        run_edge(ctx, ["--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={dst}", url], dst)
    elif d in ("png", "jpg"):
        from PIL import Image, ImageChops
        width = int(ctx.opts.get("web_width") or 1366)
        shot = ctx.tmp / "capture.png"
        ctx.progress(None, "Capture de la page…")
        if not run_edge(ctx, [f"--window-size={width},6000", f"--screenshot={shot}", url], shot):
            raise FinalError("La capture de la page a échoué.")
        img = Image.open(shot).convert("RGB")
        corner = img.getpixel((img.width - 1, img.height - 1))
        box = ImageChops.difference(img, Image.new("RGB", img.size, corner)).getbbox()
        if box:                                          # retire le vide sous une page courte
            img = img.crop((0, 0, img.width, min(img.height, box[3] + 24)))
        img.save(dst, "PNG" if d == "png" else "JPEG", quality=90)
    elif d == "html":
        import urllib.request
        ctx.progress(None, "Lecture de la page…")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                page = r.read(30_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
        except Exception as e:
            raise FinalError(f"Page inaccessible : {e}")
        base = f'<base href="{htmllib.escape(url, quote=True)}">'
        m = re.search(r"<head[^>]*>", page, re.I)
        page = page[:m.end()] + base + page[m.end():] if m else base + page
        dst.write_text(page, encoding="utf-8")
    if not dst.exists() or dst.stat().st_size == 0:
        raise FinalError("La page n'a pas pu être enregistrée.")
    return [dst]


def page_title(url: str) -> str:
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            head = r.read(200_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
        m = re.search(r"<title[^>]*>(.*?)</title>", head, re.I | re.S)
        if m:
            return htmllib.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:120]
    except Exception:
        pass
    return re.sub(r"^https?://(www\.)?", "", url).split("?")[0].strip("/")[:120] or "page"
