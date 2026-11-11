"""Conversions depuis le PDF (et les documents lisibles par MuPDF : XPS, EPUB, MOBI, FB2, CBZ)."""
from __future__ import annotations

import io
import logging
import re
import zipfile
from pathlib import Path

import pymupdf

from .. import formats as F
from ..util import FinalError, UserError, parse_pages

PAPER = {"a4": (595, 842), "letter": (612, 792), "a5": (420, 595), "legal": (612, 1008)}


def open_pdf(path):
    try:
        doc = pymupdf.open(str(path))
    except Exception as e:
        raise UserError(f"Impossible d'ouvrir le document : {e}")
    if doc.needs_pass:
        raise FinalError("Ce PDF est protégé par un mot de passe.")
    if doc.page_count == 0:
        raise FinalError("Le document ne contient aucune page.")
    return doc


def _title(doc, fallback):
    meta = doc.metadata or {}
    return (meta.get("title") or "").strip() or fallback, (meta.get("author") or "").strip()


# ---------------------------------------------------------------- Word
class _Pdf2DocxProgress(logging.Handler):
    def __init__(self, ctx):
        super().__init__()
        self.ctx, self.phase = ctx, 0

    def emit(self, record):
        try:
            msg = record.getMessage()
        except Exception:
            return
        if "[3/4]" in msg:
            self.phase = 1
            self.ctx.progress(0.1, "Analyse de la mise en page…")
        elif "[4/4]" in msg:
            self.phase = 2
            self.ctx.progress(0.55, "Création du document Word…")
        m = re.match(r"\((\d+)/(\d+)\)", msg)
        if m and self.phase:
            i, n = int(m[1]), int(m[2])
            base = 0.1 if self.phase == 1 else 0.55
            self.ctx.progress(base + 0.45 * i / max(n, 1))


def pdf_to_docx(ctx, src, sfmt, dst, d):
    from pdf2docx import Converter
    doc = open_pdf(src)
    n = doc.page_count
    pages = parse_pages(ctx.opts.get("pages"), n)
    doc.close()
    handler = _Pdf2DocxProgress(ctx)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    ctx.progress(0.02, "Ouverture du PDF…")
    cv = Converter(str(src))
    try:
        cv.convert(str(dst), pages=pages if len(pages) < n else None)
    finally:
        cv.close()
        root.removeHandler(handler)
    return [dst]


# ---------------------------------------------------------------- texte, Markdown, HTML
def _ocr_page(ctx, page) -> str:
    if not ctx.tools.get("ocr"):
        return ""
    from .ocr import ocr_image_file
    png = ctx.tmp / f"ocr_page_{page.number}.png"
    page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72), alpha=False).save(str(png))
    try:
        return ocr_image_file(ctx, png)
    except Exception:
        return ""


def pdf_to_text(ctx, src, sfmt, dst, d):
    from .htmlconv import html_to_markdown, wrap_html
    doc = open_pdf(src)
    pages = parse_pages(ctx.opts.get("pages"), doc.page_count)
    title, _ = _title(doc, ctx.stem)
    parts = []
    ocr_used = False
    for i, pno in enumerate(pages):
        page = doc[pno]
        ctx.progress(i / len(pages), f"Page {pno + 1}/{doc.page_count}…")
        if d == "txt":
            text = page.get_text("text").strip()
            if not text:
                text = _ocr_page(ctx, page).strip()
                ocr_used = ocr_used or bool(text)
            parts.append(text)
        else:
            x = page.get_text("xhtml")
            if not page.get_text("text").strip():
                t = _ocr_page(ctx, page).strip()
                if t:
                    from .htmlconv import _esc
                    x += "".join(f"<p>{_esc(line)}</p>" for line in t.splitlines() if line.strip())
            parts.append(x)
    if d == "txt":
        Path(dst).write_text("\n\n".join(parts).strip() + "\n", encoding="utf-8")
    elif d == "md":
        Path(dst).write_text(html_to_markdown("\n".join(parts)), encoding="utf-8")
    else:
        body = "\n<hr/>\n".join(parts)
        Path(dst).write_text(wrap_html(title, body), encoding="utf-8")
    return [dst]


# ---------------------------------------------------------------- images
def pdf_to_images(ctx, src, sfmt, dst, d):
    from .images import save_image
    from PIL import Image
    o = ctx.opts
    doc = open_pdf(src)
    pages = parse_pages(o.get("pages"), doc.page_count)
    dpi = int(o.get("dpi") or 150)
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    q = int(o.get("quality") or 90)
    ext = F.OUT[d][2]
    stem = Path(dst).stem

    def render(pno) -> bytes:
        page = doc[pno]
        if d == "svg":
            return page.get_svg_image(text_as_path=True).encode("utf-8")
        pix = page.get_pixmap(matrix=mat, alpha=False)
        if d == "png":
            return pix.tobytes("png")
        if d == "jpg":
            return pix.tobytes("jpg", jpg_quality=q)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        buf = io.BytesIO()
        save_image(img, buf, d, o)
        return buf.getvalue()

    if len(pages) == 1:
        name = f"{stem}.{ext}" if doc.page_count == 1 else f"{stem}-page{pages[0] + 1}.{ext}"
        out = Path(dst).parent / name
        ctx.progress(None, "Rendu de la page…")
        out.write_bytes(render(pages[0]))
        return [out]
    width = max(3, len(str(doc.page_count)))
    if o.get("zip"):
        out = Path(dst).parent / f"{stem}.zip"
        comp = zipfile.ZIP_DEFLATED if d in ("svg", "bmp", "ppm", "tiff", "tga", "pcx", "dds", "eps") else zipfile.ZIP_STORED
        with zipfile.ZipFile(out, "w", comp) as z:
            for i, pno in enumerate(pages):
                ctx.progress(i / len(pages), f"Page {pno + 1}/{doc.page_count}…")
                z.writestr(f"{stem}-{pno + 1:0{width}d}.{ext}", render(pno))
        return [out]
    folder = Path(dst).parent / stem
    folder.mkdir(parents=True, exist_ok=True)
    for i, pno in enumerate(pages):
        ctx.progress(i / len(pages), f"Page {pno + 1}/{doc.page_count}…")
        (folder / f"{stem}-{pno + 1:0{width}d}.{ext}").write_bytes(render(pno))
    return [folder]


def pdf_to_cbz(ctx, src, sfmt, dst, d):
    doc = open_pdf(src)
    pages = parse_pages(ctx.opts.get("pages"), doc.page_count)
    dpi = int(ctx.opts.get("dpi") or 150)
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    width = max(3, len(str(doc.page_count)))
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as z:
        for i, pno in enumerate(pages):
            ctx.progress(i / len(pages), f"Page {pno + 1}/{doc.page_count}…")
            pix = doc[pno].get_pixmap(matrix=mat, alpha=False)
            z.writestr(f"{pno + 1:0{width}d}.jpg", pix.tobytes("jpg", jpg_quality=88))
    return [dst]


# ---------------------------------------------------------------- EPUB
def pdf_to_epub(ctx, src, sfmt, dst, d):
    from .epub import EpubImages, build_epub, fragment_from_html
    doc = open_pdf(src)
    pages = parse_pages(ctx.opts.get("pages"), doc.page_count)
    title, author = _title(doc, ctx.stem)
    images = EpubImages()
    frag = {}
    for i, pno in enumerate(pages):
        ctx.progress(0.9 * i / len(pages), f"Page {pno + 1}/{doc.page_count}…")
        frag[pno] = fragment_from_html(doc[pno].get_text("xhtml"), images)
    toc = [(e[2] - 1, e[1]) for e in doc.get_toc(simple=True) if e[0] == 1 and 1 <= e[2] <= doc.page_count]
    chapters = []
    if len(toc) >= 2:
        bounds = sorted(dict(toc).items())
        if pages[0] < bounds[0][0]:
            bounds.insert(0, (pages[0], title))
        for k, (start, ctitle) in enumerate(bounds):
            end = bounds[k + 1][0] if k + 1 < len(bounds) else doc.page_count
            body = "\n".join(frag[p] for p in pages if start <= p < end)
            if body.strip():
                chapters.append((ctitle, body))
    if not chapters:
        for k in range(0, len(pages), 10):
            chunk = pages[k:k + 10]
            label = f"Pages {chunk[0] + 1}–{chunk[-1] + 1}" if len(pages) > 10 else title
            chapters.append((label, "\n".join(frag[p] for p in chunk)))
    pix = doc[pages[0]].get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6), alpha=False)
    build_epub(dst, title, author, chapters, images, cover=(pix.tobytes("jpg", jpg_quality=85), "image/jpeg"))
    return [dst]


# ---------------------------------------------------------------- XPS / EPUB / MOBI / FB2 / CBZ -> PDF
def mupdf_to_pdf(ctx, src, sfmt, dst, d):
    try:
        doc = pymupdf.open(str(src))
    except Exception as e:
        raise UserError(f"Impossible d'ouvrir le document : {e}")
    if doc.is_reflowable:
        w, h = PAPER.get(ctx.opts.get("page_size") or "a4", PAPER["a4"])
        doc.layout(width=w, height=h, fontsize=int(ctx.opts.get("font_size") or 11))
    n = doc.page_count
    if n == 0:
        raise UserError("Le document ne contient aucune page.")
    out = pymupdf.open()
    step = 20
    for a in range(0, n, step):
        b = min(n, a + step) - 1
        ctx.progress(a / n, f"Mise en page {a + 1}–{b + 1} / {n}…")
        out.insert_pdf(pymupdf.open("pdf", doc.convert_to_pdf(a, b)))
    try:
        toc = doc.get_toc()
        if toc:
            out.set_toc(toc)
    except Exception:
        pass
    meta = doc.metadata or {}
    try:
        out.set_metadata({k: v for k, v in meta.items() if k in ("title", "author", "subject", "keywords") and v})
    except Exception:
        pass
    out.save(str(dst), garbage=3, deflate=True)
    return [dst]


# ---------------------------------------------------------------- compression
PDF_QUALITY = {"screen": (72, 45), "ebook": (150, 70), "print": (300, 85)}


def compress(ctx, src, sfmt, dst, d):
    import shutil
    doc = open_pdf(src)
    dpi, quality = PDF_QUALITY.get(ctx.opts.get("pdf_quality") or "ebook", PDF_QUALITY["ebook"])
    ctx.progress(None, "Compression des images…")
    try:
        doc.rewrite_images(dpi_threshold=dpi + 20, dpi_target=dpi, quality=quality, lossless=True, bitonal=True,
                           color=True, gray=True)
    except Exception:
        pass
    ctx.progress(None, "Optimisation des polices et de la structure…")
    try:
        doc.subset_fonts()
    except Exception:
        pass
    doc.save(str(dst), garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, clean=True, use_objstms=1)
    doc.close()
    if Path(dst).stat().st_size >= Path(src).stat().st_size:      # aucun gain : on garde l'original
        shutil.copyfile(src, dst)
    return [dst]
