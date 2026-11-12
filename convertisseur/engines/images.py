"""Conversions d'images (Pillow, pillow-heif, resvg, vtracer) et assemblages (PDF, GIF)."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence

from .. import formats as F
from ..util import UserError

Image.MAX_IMAGE_PIXELS = 1_000_000_000

_HEIF = None


def _heif() -> None:
    global _HEIF
    if _HEIF is None:
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            _HEIF = True
        except Exception:
            _HEIF = False
    if not _HEIF:
        raise UserError("Le module pillow-heif est nécessaire pour les images HEIC.")


# ---------------------------------------------------------------- lecture
def svg_render(path, width=None, height=None) -> Image.Image:
    import resvg_py
    kw = {"svg_path": str(path)}
    if width:
        kw["width"] = int(width)
    elif height:
        kw["height"] = int(height)
    try:
        data = resvg_py.svg_to_bytes(**kw)
    except Exception as e:
        raise UserError(f"SVG illisible : {e}")
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


def open_image(path, fmt, svg_width=None, min_side=1024) -> Image.Image:
    if fmt in F.SVG_IN:
        if svg_width:
            return svg_render(path, width=svg_width)
        img = svg_render(path)
        if max(img.size) < min_side:
            img = svg_render(path, width=max(1, round(img.width * min_side / max(img.size))))
        return img
    if fmt in F.HEIC_IN:
        _heif()
    try:
        img = Image.open(path)
        img.load()
    except UserError:
        raise
    except Exception as e:
        raise UserError(f"Image illisible ou format non reconnu : {e}")
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    return img


def exif_bytes(img) -> bytes | None:
    try:
        ex = img.getexif()
        if not ex:
            return None
        if 0x0112 in ex:
            ex[0x0112] = 1
        return ex.tobytes()
    except Exception:
        return None


def normalize(img: Image.Image) -> Image.Image:
    m = img.mode
    if m.startswith("I;16") or m == "I":
        lo, hi = img.getextrema() if m != "I;16N" else (0, 65535)
        img = img.convert("I") if m != "I" else img
        if hi and hi > 255:
            img = img.point(lambda v: v * (255.0 / 65535.0))
        return img.convert("L")
    if m == "F":
        return img.convert("L")
    if m in ("CMYK", "YCbCr", "LAB", "HSV"):
        return img.convert("RGB")
    if m == "RGBa":
        return img.convert("RGBA")
    if m == "La":
        return img.convert("LA")
    if m in ("PA",):
        return img.convert("RGBA")
    if m == "P":
        return img.convert("RGBA") if "transparency" in img.info else img.convert("RGB")
    if m == "1":
        return img.convert("L")
    return img


def has_alpha(img) -> bool:
    return img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)


def flatten(img, bg="#ffffff") -> Image.Image:
    if has_alpha(img):
        rgba = img.convert("RGBA")
        base = Image.new("RGB", rgba.size, bg)
        base.paste(rgba, mask=rgba.getchannel("A"))
        return base
    return img if img.mode in ("RGB", "L") else img.convert("RGB")


def fit(img, max_w=None, max_h=None) -> Image.Image:
    if not max_w and not max_h:
        return img
    w, h = img.size
    s = min(max_w / w if max_w else 10 ** 9, max_h / h if max_h else 10 ** 9)
    if s >= 1:
        return img
    if img.mode in ("P", "1"):
        img = img.convert("RGBA")
    return img.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)


def square(img, size=None) -> Image.Image:
    img = img.convert("RGBA")
    side = max(img.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    if size and side != size:
        canvas = canvas.resize((size, size), Image.LANCZOS)
    return canvas


# ---------------------------------------------------------------- écriture
def save_image(img, target, d, opts=None, icc=None, exif=None) -> None:
    """Enregistre img au format d (id de sortie) dans target (chemin ou fichier binaire)."""
    opts = opts or {}
    q = int(opts.get("quality") or 90)
    bg = opts.get("bg") or "#ffffff"
    extra = {}
    if icc and d in ("jpg", "png", "webp", "avif", "tiff", "jp2", "heic"):
        extra["icc_profile"] = icc
    if exif and d in ("jpg", "webp", "png", "tiff", "avif", "heic"):
        extra["exif"] = exif

    def rgb_or_rgba(im):
        return im.convert("RGBA") if has_alpha(im) else (im if im.mode in ("RGB", "L") else im.convert("RGB"))

    def _save(im, fmt, **kw):
        try:
            im.save(target, fmt, **kw, **extra)
        except Exception:
            if not extra:
                raise
            if hasattr(target, "seek"):
                target.seek(0)
                target.truncate()
            im.save(target, fmt, **kw)

    if d == "jpg":
        im = flatten(img, bg)
        _save(im, "JPEG", quality=q, optimize=True, progressive=True, subsampling=0 if q >= 90 else 2)
    elif d == "png":
        im = img if img.mode in ("RGB", "RGBA", "L", "LA", "P") else img.convert("RGBA")
        _save(im, "PNG", compress_level=6)
    elif d == "webp":
        _save(rgb_or_rgba(img), "WEBP", quality=q, lossless=bool(opts.get("lossless")), method=4)
    elif d == "avif":
        _save(rgb_or_rgba(img), "AVIF", quality=q, speed=6)
    elif d == "heic":
        _heif()
        _save(rgb_or_rgba(img), "HEIF", quality=q)
    elif d == "gif":
        im = img if img.mode in ("RGB", "RGBA", "L", "P") else img.convert("RGBA")
        im.save(target, "GIF")
    elif d == "bmp":
        flatten(img, bg).save(target, "BMP")
    elif d == "tiff":
        im = img if img.mode in ("RGB", "RGBA", "L", "LA", "CMYK") else img.convert("RGBA")
        _save(im, "TIFF", compression="tiff_lzw")
    elif d == "ico":
        im = square(img)
        sizes = [s for s in (16, 24, 32, 48, 64, 128, 256) if s <= im.width] or [im.width]
        if im.width < 256 and im.width not in sizes:
            sizes.append(im.width)
        im.save(target, "ICO", sizes=[(s, s) for s in sizes])
    elif d == "icns":
        square(img, 1024).save(target, "ICNS")
    elif d == "tga":
        rgb_or_rgba(img).save(target, "TGA", compression="tga_rle")
    elif d == "jp2":
        im = rgb_or_rgba(img)
        if q >= 100:
            _save(im, "JPEG2000")
        else:
            _save(im, "JPEG2000", quality_mode="rates", quality_layers=[max(1.5, (101 - q) / 2.5)], irreversible=True)
    elif d == "ppm":
        flatten(img, bg).save(target, "PPM")
    elif d == "pcx":
        flatten(img, bg).save(target, "PCX")
    elif d == "qoi":
        rgb_or_rgba(img).save(target, "QOI")
    elif d == "dds":
        img.convert("RGBA").save(target, "DDS")
    elif d == "eps":
        flatten(img, bg).save(target, "EPS")
    else:
        raise UserError(f"Format d'image non géré : {d}")


# ---------------------------------------------------------------- convertisseurs
def convert_image(ctx, src, sfmt, dst, d):
    o = ctx.opts if ctx.last else {}
    ctx.progress(None, "Conversion de l'image…")
    img = open_image(src, sfmt, svg_width=o.get("svg_width"))
    icc, exif = img.info.get("icc_profile"), exif_bytes(img)
    if o.get("strip_meta"):                       # confidentialité : EXIF, GPS, XMP retirés (profil couleur gardé)
        exif = None
        img.info = {k: v for k, v in img.info.items() if k == "icc_profile"}
    img = normalize(img)
    if sfmt not in F.SVG_IN:
        img = fit(img, o.get("max_w"), o.get("max_h"))
    if o:
        from .imagetools import apply_edits
        img = apply_edits(img, o)
    limit = int(o.get("target_kb") or 0) * 1024
    if limit and d in F.LOSSY_IMAGE:
        Path(dst).write_bytes(fit_size(img, d, o, limit, icc, exif))
    else:
        save_image(img, dst, d, o, icc, exif)
    return [dst]


def fit_size(img, d, opts, limit, icc=None, exif=None) -> bytes:
    """Meilleure qualité qui tient dans limit octets (réduit l'image si nécessaire)."""
    def encode(im, q):
        buf = io.BytesIO()
        save_image(im, buf, d, {**opts, "quality": q, "lossless": False}, icc, exif)
        return buf.getvalue()
    while True:
        lo, hi, best = 5, 95, None
        while lo <= hi:
            q = (lo + hi) // 2
            data = encode(img, q)
            if len(data) <= limit:
                best, lo = data, q + 1
            else:
                hi = q - 1
        if best is not None or max(img.size) < 64:
            return best if best is not None else encode(img, 5)
        img = img.resize((max(1, int(img.width * 0.8)), max(1, int(img.height * 0.8))), Image.LANCZOS)


def to_png(src, sfmt, dst, max_side=None) -> Path:
    img = normalize(open_image(src, sfmt, min_side=1600))
    if max_side and max(img.size) > max_side:
        img = fit(img, max_side, max_side)
    save_image(img, dst, "png")
    return Path(dst)


VTRACER_PRESETS = {
    "logo": dict(colormode="color", hierarchical="stacked", mode="spline", filter_speckle=4, color_precision=6,
                 layer_difference=16, corner_threshold=60, length_threshold=4.0, max_iterations=10,
                 splice_threshold=45, path_precision=3),
    "poster": dict(colormode="color", hierarchical="stacked", mode="spline", filter_speckle=8, color_precision=5,
                   layer_difference=32, corner_threshold=60, length_threshold=4.0, max_iterations=10,
                   splice_threshold=45, path_precision=3),
    "photo": dict(colormode="color", hierarchical="stacked", mode="spline", filter_speckle=10, color_precision=8,
                  layer_difference=48, corner_threshold=180, length_threshold=4.0, max_iterations=10,
                  splice_threshold=45, path_precision=3),
    "bw": dict(colormode="binary", hierarchical="stacked", mode="spline", filter_speckle=4, color_precision=6,
               layer_difference=16, corner_threshold=60, length_threshold=4.0, max_iterations=10,
               splice_threshold=45, path_precision=3),
}


def vectorize(ctx, src, sfmt, dst, d):
    import vtracer
    ctx.progress(None, "Vectorisation…")
    img = normalize(open_image(src, sfmt))
    if max(img.size) > 2000:
        img = fit(img, 2000, 2000)
    img = img.convert("RGBA") if has_alpha(img) else img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    preset = VTRACER_PRESETS.get(ctx.opts.get("svg_preset") or "logo", VTRACER_PRESETS["logo"])
    svg = vtracer.convert_raw_image_to_svg(buf.getvalue(), img_format="png", **preset)
    Path(dst).write_text(svg, encoding="utf-8")
    return [dst]


def _frames(path):
    img = Image.open(path)
    for frame in ImageSequence.Iterator(img):
        yield frame.convert("RGBA"), int(frame.info.get("duration", img.info.get("duration", 100)) or 100)


def anim_to_image(ctx, src, sfmt, dst, d):
    o = ctx.opts if ctx.last else {}
    img = Image.open(src)
    count = getattr(img, "n_frames", 1)
    if o.get("frames") == "all" and count > 1:
        out = Path(dst).with_suffix(".zip")
        ext = F.OUT[d][2]
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for i, (frame, _) in enumerate(_frames(src)):
                buf = io.BytesIO()
                save_image(fit(frame, o.get("max_w"), o.get("max_h")), buf, d, o)
                z.writestr(f"{Path(dst).stem}-{i + 1:04d}.{ext}", buf.getvalue())
                ctx.progress((i + 1) / count, f"Image {i + 1}/{count}…")
        return [out]
    img.seek(0)
    frame = normalize(img.convert("RGBA"))
    save_image(fit(frame, o.get("max_w"), o.get("max_h")), dst, d, o)
    return [dst]


# ---------------------------------------------------------------- vers PDF
JPEG_EXT = {"jpg", "jpeg", "jfif", "pjpeg", "pjp", "jpe"}
PHOTO_EXT = JPEG_EXT | F.HEIC_IN | {"avif", "webp", "jp2", "j2k", "jpf", "jpx", "mpo", "psd"}


def _encode_for_pdf(img, photo: bool):
    img = normalize(img)
    buf = io.BytesIO()
    if has_alpha(img):
        img.convert("RGBA").save(buf, "PNG")
    elif photo:
        flatten(img).save(buf, "JPEG", quality=92)
    else:
        (img if img.mode in ("RGB", "L") else img.convert("RGB")).save(buf, "PNG")
    return buf.getvalue()


def _image_payloads(path, fmt):
    """Rend [(octets, largeur, hauteur, dpi)] pour une image (plusieurs pour une animation)."""
    if fmt in F.ANIM_IN:
        return [(_encode_for_pdf(fr, False), fr.width, fr.height, 96) for fr, _ in _frames(path)]
    if fmt in JPEG_EXT:
        try:
            with Image.open(path) as im:
                orientation = im.getexif().get(0x0112, 1)
                if orientation in (None, 1) and im.mode in ("RGB", "L", "CMYK"):
                    dpi = (im.info.get("dpi") or (96, 96))[0]
                    return [(Path(path).read_bytes(), im.width, im.height, dpi)]
        except Exception:
            pass
    img = open_image(path, fmt, min_side=2400)
    dpi = (img.info.get("dpi") or (96, 96))[0] if fmt not in F.SVG_IN else 96 * max(1.0, max(img.size) / 1024)
    return [(_encode_for_pdf(img, fmt in PHOTO_EXT), img.width, img.height, dpi)]


def _add_image_page(doc, data, w, h, dpi, mode):
    import pymupdf
    try:
        dpi = float(dpi)
    except (TypeError, ValueError):
        dpi = 96.0
    if not 40 <= dpi <= 1200:
        dpi = 96.0
    nat_w, nat_h = w * 72 / dpi, h * 72 / dpi
    if mode == "fit":
        page = doc.new_page(width=nat_w, height=nat_h)
        page.insert_image(page.rect, stream=data)
        return
    pw, ph = pymupdf.paper_size("a4" if mode == "a4" else "letter")
    if w > h:
        pw, ph = ph, pw
    page = doc.new_page(width=pw, height=ph)
    margin = 28
    bw, bh = pw - 2 * margin, ph - 2 * margin
    s = min(1.0, bw / nat_w, bh / nat_h) if nat_w and nat_h else 1.0
    iw, ih = nat_w * s, nat_h * s
    x, y = (pw - iw) / 2, (ph - ih) / 2
    page.insert_image(pymupdf.Rect(x, y, x + iw, y + ih), stream=data)


def images_to_pdf(ctx, items: list[tuple], dst, mode="a4"):
    import pymupdf
    doc = pymupdf.open()
    for i, (path, fmt, name) in enumerate(items):
        ctx.progress(i / len(items), f"Ajout de {name}…")
        if fmt == "pdf" or fmt in F.XPS_IN:
            src = pymupdf.open(path)
            if src.needs_pass:
                raise UserError(f"« {name} » est protégé par un mot de passe.")
            if fmt != "pdf":
                src = pymupdf.open("pdf", src.convert_to_pdf())
            doc.insert_pdf(src)
            continue
        for data, w, h, dpi in _image_payloads(path, fmt):
            _add_image_page(doc, data, w, h, dpi, mode)
    if doc.page_count == 0:
        raise UserError("Aucune page à créer.")
    doc.save(str(dst), garbage=3, deflate=True)
    return [dst]


def image_to_pdf(ctx, src, sfmt, dst, d):
    return images_to_pdf(ctx, [(src, sfmt, Path(src).name)], dst, ctx.opts.get("img_page") or "a4")


# ---------------------------------------------------------------- BD (CBZ) -> images
def cbz_to_images(ctx, src, sfmt, dst, d):
    o = ctx.opts
    ext = F.OUT[d][2]
    with zipfile.ZipFile(src) as z:
        names = sorted(n for n in z.namelist() if not n.endswith("/") and
                       n.rsplit(".", 1)[-1].lower() in {"jpg", "jpeg", "png", "webp", "gif", "bmp", "avif", "jxl",
                                                        "tif", "tiff"})
        if not names:
            raise UserError("Aucune image trouvée dans cette archive.")
        stem = Path(dst).stem
        width = max(3, len(str(len(names))))
        if o.get("zip"):
            out = Path(dst).parent / f"{stem}.zip"
            target = zipfile.ZipFile(out, "w", zipfile.ZIP_STORED)
        else:
            out = Path(dst).parent / stem
            out.mkdir(parents=True, exist_ok=True)
            target = None
        for i, n in enumerate(names):
            img = normalize(Image.open(io.BytesIO(z.read(n))))
            fname = f"{stem}-{i + 1:0{width}d}.{ext}"
            if target:
                buf = io.BytesIO()
                save_image(img, buf, d, o)
                target.writestr(fname, buf.getvalue())
            else:
                save_image(img, out / fname, d, o)
            ctx.progress((i + 1) / len(names), f"Page {i + 1}/{len(names)}…")
        if target:
            target.close()
    return [out]


# ---------------------------------------------------------------- assemblages multi-fichiers
def _load_frame(path, fmt):
    if fmt in F.ANIM_IN:
        img = Image.open(path)
        img.seek(0)
        return img.convert("RGBA")
    return normalize(open_image(path, fmt)).convert("RGBA")


def combine_gif(ctx, items, dst):
    from .media import _make_gif
    o = ctx.opts
    frames = []
    for i, (path, fmt, name) in enumerate(items):
        frames.append(_load_frame(path, fmt))
        ctx.progress(0.2 * (i + 1) / len(items), f"Lecture de {name}…")
    W, H = frames[0].size
    width = o.get("anim_width") or "orig"
    if width != "orig" and int(width) < W:
        H = max(1, round(H * int(width) / W))
        W = int(width)
    folder = ctx.tmp / "frames"
    folder.mkdir(exist_ok=True)
    for i, fr in enumerate(frames):
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fr = fr.copy()
        fr.thumbnail((W, H), Image.LANCZOS)
        canvas.paste(fr, ((W - fr.width) // 2, (H - fr.height) // 2), fr)
        canvas.save(folder / f"f{i + 1:05d}.png")
    ms = max(20, int(o.get("frame_ms") or 500))
    sub = type("Sub", (), {})()
    sub.tools, sub.tmp = ctx.tools, ctx.tmp
    sub.progress = lambda p=None, m=None: ctx.progress(None if p is None else 0.2 + 0.8 * p, m)
    _make_gif(sub, folder / "f%05d.png", dst, [], [], [], len(frames) * ms / 1000, stats="full",
              dither="sierra2_4a", loop=o.get("loop", True), input_args=["-framerate", f"1000/{ms}"])
    return [dst]


def combine_video(ctx, items, dst):
    from .media import slideshow
    folder = ctx.tmp / "frames"
    folder.mkdir(exist_ok=True)
    frames = []
    for i, (path, fmt, name) in enumerate(items):
        img = _load_frame(path, fmt)
        img = flatten(fit(img, 3840, 2160))
        f = folder / f"f{i + 1:05d}.png"
        img.save(f)
        frames.append(f)
        ctx.progress(0.5 * (i + 1) / len(items), f"Préparation de {name}…")
    slideshow(ctx, frames, dst, max(1, int(ctx.opts.get("slide_dur") or 3)))
    return [dst]
