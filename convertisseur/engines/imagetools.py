"""Outils image : retouches (taille, recadrage, rotation, filtres, filigrane), détourage par IA,
lecture de QR codes et codes-barres, kit d'icônes pour site web, collage."""
from __future__ import annotations

import io
import json
import math
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from ..i18n import colon, tr
from ..util import FinalError, UserError

FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")
RATIOS = {"1:1": (1, 1), "4:5": (4, 5), "16:9": (16, 9), "9:16": (9, 16), "4:3": (4, 3), "3:2": (3, 2), "2:3": (2, 3)}
MODEL_DIR = Path(__file__).resolve().parents[2] / "modeles" / "detourage"
MODELS = {   # nom, taille approx., entrée, moyenne, écart-type (mêmes réglages que rembg)
    "fast": ("u2netp", 4.6e6, (320, 320), (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    "precise": ("isnet-general-use", 1.79e8, (1024, 1024), (0.485, 0.456, 0.406), (1.0, 1.0, 1.0)),
}
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/{name}.onnx"


# ---------------------------------------------------------------- retouches (options des images)
def _keep_alpha(img, fn):
    """Applique fn sur la partie couleur en conservant la transparence."""
    if img.mode in ("RGBA", "LA"):
        alpha = img.getchannel("A")
        out = fn(img.convert("RGB")).convert("RGBA")
        out.putalpha(alpha)
        return out
    return fn(img if img.mode in ("RGB", "L") else img.convert("RGB"))


def _sepia(rgb):
    gray = ImageOps.grayscale(rgb)
    return ImageOps.colorize(gray, black="#2b1d0e", white="#fff4e0", mid="#a67b4f")


def font(size: int):
    try:
        return ImageFont.truetype(str(FONT_BOLD) if FONT_BOLD.is_file() else "arial.ttf", size)
    except Exception:
        return ImageFont.load_default(size)


def _hex_rgb(value: str, default=(128, 128, 128)):
    try:
        h = value.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return default


def draw_watermark(img: Image.Image, text: str, pos="diagonal", size="medium", opacity=25, color="#808080"):
    text = (text or "").strip()
    if not text:
        return img
    base = img.convert("RGBA")
    w, h = base.size
    ratio = {"small": 0.045, "medium": 0.075, "large": 0.12}.get(size, 0.075)
    fs = max(10, int(min(w, h) * ratio))
    fnt = font(fs)
    alpha = int(255 * max(0.03, min(1.0, (opacity or 25) / 100)))
    rgb = _hex_rgb(color or "#808080")
    left, top, right, bottom = fnt.getbbox(text)
    tw, th = right - left, bottom - top
    if pos in ("diagonal", "tiled"):
        limit = 0.9 * math.hypot(w, h) if pos == "diagonal" else w
        if tw > limit:
            fnt = font(max(8, int(fs * limit / tw)))
            left, top, right, bottom = fnt.getbbox(text)
            tw, th = right - left, bottom - top
        stamp = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
        ImageDraw.Draw(stamp).text((4 - left, 4 - top), text, font=fnt, fill=(*rgb, alpha))
        stamp = stamp.rotate(35 if w >= h else 50, expand=True, resample=Image.BICUBIC)
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        if pos == "diagonal":
            layer.alpha_composite(stamp, ((w - stamp.width) // 2, (h - stamp.height) // 2))
        else:
            step_x, step_y = int(stamp.width * 1.15), int(stamp.height * 1.0)
            for row, y in enumerate(range(-step_y // 2, h + step_y, max(1, step_y))):
                for x in range(-step_x + (row % 2) * step_x // 2, w + step_x, max(1, step_x)):
                    layer.alpha_composite(stamp, (x, y))
        return Image.alpha_composite(base, layer)
    if tw > w * 0.9:
        fnt = font(max(8, int(fs * w * 0.9 / tw)))
        left, top, right, bottom = fnt.getbbox(text)
        tw, th = right - left, bottom - top
    m = max(8, int(min(w, h) * 0.03))
    x = {"tl": m, "bl": m, "tr": w - m - tw, "br": w - m - tw}.get(pos, (w - tw) // 2)
    y = {"tl": m, "tr": m, "top": m, "bl": h - m - th, "br": h - m - th, "bottom": h - m - th}.get(pos, (h - th) // 2)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    shadow = (0, 0, 0, alpha // 2) if sum(rgb) > 380 else (255, 255, 255, alpha // 2)
    draw.text((x - left + 1, y - top + 1), text, font=fnt, fill=shadow)
    draw.text((x - left, y - top), text, font=fnt, fill=(*rgb, alpha))
    return Image.alpha_composite(base, layer)


def apply_edits(img: Image.Image, o: dict) -> Image.Image:
    """Retouches demandées dans les réglages, dans l'ordre : recadrage, rotation, taille, filtre, filigrane."""
    ratio = RATIOS.get(o.get("img_ratio") or "")
    if ratio:
        rw, rh = ratio
        w, h = img.size
        if w / h > rw / rh:
            nw = max(1, round(h * rw / rh))
            img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = max(1, round(w * rh / rw))
            img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    rot = o.get("rotate") or "none"
    if rot != "none":
        op = {"cw": Image.Transpose.ROTATE_270, "ccw": Image.Transpose.ROTATE_90, "180": Image.Transpose.ROTATE_180,
              "hflip": Image.Transpose.FLIP_LEFT_RIGHT, "vflip": Image.Transpose.FLIP_TOP_BOTTOM}.get(rot)
        if op is not None:
            img = img.transpose(op)
    size = o.get("img_resize") or "none"
    if size != "none":
        if img.mode in ("P", "1"):
            img = img.convert("RGBA")
        w, h = img.size
        if size.endswith("%"):
            s = int(size[:-1]) / 100
        elif size.startswith("x"):
            s = float(size[1:])
        else:
            s = min(1.0, int(size) / max(w, h))
        if s != 1:
            img = img.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
            if s > 1:                                      # agrandissement : un peu de netteté
                img = _keep_alpha(img, lambda im: im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2)))
    adj = o.get("img_adjust") or "none"
    if adj != "none":
        fn = {"bw": lambda im: ImageOps.grayscale(im).convert("RGB"), "sepia": _sepia,
              "contrast": lambda im: ImageOps.autocontrast(im, cutoff=1),
              "sharpen": lambda im: im.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3)),
              "blur": lambda im: im.filter(ImageFilter.GaussianBlur(max(1.5, max(im.size) / 400))),
              "invert": lambda im: ImageOps.invert(im.convert("RGB"))}.get(adj)
        if fn:
            img = _keep_alpha(img, fn)
    if (o.get("wm_text") or "").strip():
        img = draw_watermark(img, o["wm_text"], o.get("wm_pos") or "diagonal", o.get("wm_size") or "medium",
                             o.get("wm_opacity") or 25, o.get("wm_color") or "#808080")
    return img


# ---------------------------------------------------------------- détourage (IA)
def _download(ctx, url: str, dest: Path, expected: float):
    import urllib.request
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "Convertisseur"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:
            total = int(r.headers.get("Content-Length") or expected)
            done = 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                ctx.progress(min(0.9, 0.9 * done / total), f"Téléchargement du modèle de détourage… {done / 1e6:.0f} / {total / 1e6:.0f} Mo".replace(".", ","))
    except Exception as e:
        part.unlink(missing_ok=True)
        raise UserError(f"Téléchargement du modèle impossible (connexion Internet ?) : {e}")
    part.replace(dest)


def _onnxruntime():
    from .transcription import _vad_available          # charge onnxruntime, même depuis un chemin très long
    if not _vad_available():
        raise UserError("Le module onnxruntime est introuvable : réinstallez les modules Python.")
    import onnxruntime
    return onnxruntime


def remove_background(ctx, src, sfmt, dst, d):
    import numpy as np
    from .images import normalize, open_image
    o = ctx.opts
    name, expected, size, mean, std = MODELS.get(o.get("nobg_model") or "precise", MODELS["precise"])
    model = MODEL_DIR / f"{name}.onnx"
    if not model.is_file():
        _download(ctx, MODEL_URL.format(name=name), model, expected)
    ort = _onnxruntime()
    ctx.progress(0.92, "Détourage du sujet…")
    img = normalize(open_image(src, sfmt, min_side=512))
    rgb = img.convert("RGB")
    arr = np.asarray(rgb.resize(size, Image.LANCZOS), dtype=np.float32)
    arr = arr / max(1.0, float(arr.max()))
    arr = (arr - np.array(mean, dtype=np.float32)) / np.array(std, dtype=np.float32)
    tensor = np.expand_dims(arr.transpose(2, 0, 1), 0).astype(np.float32)
    try:
        session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
        pred = session.run(None, {session.get_inputs()[0].name: tensor})[0][:, 0, :, :]
    except Exception as e:
        model.unlink(missing_ok=True)                     # modèle abîmé : il sera retéléchargé
        raise UserError(f"Le détourage a échoué : {e}")
    lo, hi = float(pred.min()), float(pred.max())
    mask = (pred - lo) / ((hi - lo) or 1.0)
    alpha = Image.fromarray((mask[0] * 255).astype("uint8"), "L").resize(rgb.size, Image.LANCZOS)
    out = rgb.convert("RGBA")
    if img.mode in ("RGBA", "LA"):                        # transparence d'origine conservée
        alpha = Image.fromarray(np.minimum(np.asarray(alpha), np.asarray(img.getchannel("A"))))
    out.putalpha(alpha)
    if o.get("nobg_crop"):
        box = alpha.point(lambda v: 255 if v > 24 else 0).getbbox()
        if box:
            m = max(4, int(max(out.size) * 0.01))
            out = out.crop((max(0, box[0] - m), max(0, box[1] - m), min(out.width, box[2] + m), min(out.height, box[3] + m)))
    bg = o.get("nobg_bg") or "none"
    if bg != "none":
        color = {"white": "#ffffff", "black": "#000000"}.get(bg, bg)
        flat = Image.new("RGBA", out.size, color)
        flat.alpha_composite(out)
        out = flat
    out.save(dst, "PNG", compress_level=6)
    return [dst]


# ---------------------------------------------------------------- QR codes et codes-barres
CODE_NAMES = {"QR_CODE": "QR code", "EAN_13": "EAN-13", "EAN_8": "EAN-8", "UPC_A": "UPC-A", "UPC_E": "UPC-E",
              "CODE_128": "Code 128", "CODE_39": "Code 39", "CODE_93": "Code 93", "ITF": "ITF", "CODABAR": "Codabar"}


ZXING_NAMES = {"QRCode": "QR code", "MicroQRCode": "Micro QR code", "DataMatrix": "Data Matrix", "PDF417": "PDF417",
               "Aztec": "Aztec", "EAN13": "EAN-13", "EAN8": "EAN-8", "UPCA": "UPC-A", "UPCE": "UPC-E",
               "Code128": "Code 128", "Code39": "Code 39", "Code93": "Code 93", "ITF": "ITF", "Codabar": "Codabar"}


def _decode(arr):
    """Lecture avec zxing-cpp (tous les codes courants), sinon OpenCV."""
    found = []
    try:
        import zxingcpp
        for r in zxingcpp.read_barcodes(arr):
            fmt = getattr(r.format, "name", str(r.format))
            if r.text:
                found.append((ZXING_NAMES.get(fmt, fmt), r.text))
        if found:
            return found
    except Exception:
        pass
    import cv2
    try:
        ok, texts, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(arr)
        if ok:
            found += [("QR code", t) for t in texts if t]
    except Exception:
        pass
    try:
        ok, texts, types, _ = cv2.barcode.BarcodeDetector().detectAndDecodeWithType(arr)
        if ok:
            found += [(CODE_NAMES.get(str(k).upper(), str(k)), t) for t, k in zip(texts, types) if t]
    except Exception:
        pass
    return found


def read_codes(ctx, src, sfmt, dst, d):
    import cv2
    import numpy as np
    from .images import flatten, normalize, open_image
    ctx.progress(None, "Recherche de QR codes et de codes-barres…")
    img = flatten(normalize(open_image(src, sfmt, min_side=800)))
    arr = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    found = _decode(arr)
    if not found:                                         # petits codes : on agrandit, puis niveaux de gris contrastés
        big = cv2.resize(arr, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        found = _decode(big)
        if not found:
            gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
            found = _decode(cv2.cvtColor(cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], cv2.COLOR_GRAY2BGR))
    unique = list(dict.fromkeys(found))
    if not unique:
        raise FinalError("Aucun QR code ni code-barres lisible dans cette image.")
    if len(unique) == 1:
        text = unique[0][1] + "\n"
    else:
        text = "\n\n".join(f"{kind}{colon().rstrip()}\n{value}" for kind, value in unique) + "\n"
    Path(dst).write_text(text, encoding="utf-8")
    return [dst]


# ---------------------------------------------------------------- kit d'icônes pour site web
def favicon_kit(ctx, src, sfmt, dst, d):
    from .images import normalize, open_image, square
    ctx.progress(None, "Création des icônes…")
    img = square(normalize(open_image(src, sfmt, min_side=1024)))
    files = {}
    for name, px in (("favicon-16x16.png", 16), ("favicon-32x32.png", 32), ("favicon-48x48.png", 48),
                     ("apple-touch-icon.png", 180), ("android-chrome-192x192.png", 192), ("android-chrome-512x512.png", 512)):
        buf = io.BytesIO()
        im = img.resize((px, px), Image.LANCZOS)
        if name == "apple-touch-icon.png":                  # iOS n'affiche pas la transparence
            flat = Image.new("RGBA", im.size, "#ffffff")
            flat.alpha_composite(im)
            im = flat.convert("RGB")
        im.save(buf, "PNG")
        files[name] = buf.getvalue()
    buf = io.BytesIO()
    img.save(buf, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    files["favicon.ico"] = buf.getvalue()
    files["site.webmanifest"] = json.dumps({
        "name": ctx.stem, "short_name": ctx.stem[:12], "display": "standalone", "theme_color": "#ffffff",
        "background_color": "#ffffff", "icons": [
            {"src": "/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2).encode()
    files[tr("A coller dans la balise head") + ".html"] = (
        '<link rel="icon" href="/favicon.ico" sizes="48x48">\n'
        '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">\n'
        '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">\n'
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">\n'
        '<link rel="manifest" href="/site.webmanifest">\n').encode()
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return [dst]


# ---------------------------------------------------------------- collage
def collage(ctx, items: list[tuple], dst, opts: dict) -> list[Path]:
    from .images import flatten, has_alpha, normalize, open_image
    if len(items) < 2:
        raise UserError("Ajoutez au moins deux images pour un collage.")
    bg = opts.get("bg") or "#ffffff"
    gap = int(opts.get("collage_gap") or 0)
    cover = (opts.get("collage_fit") or "cover") == "cover"
    n = len(items)
    cols = int(opts.get("collage_cols") or 0) or math.ceil(math.sqrt(n))
    cols = max(1, min(cols, n))
    rows = math.ceil(n / cols)
    cell = 900 if cols <= 3 else 700 if cols <= 5 else 520
    images = []
    for i, (path, fmt, name) in enumerate(items):
        ctx.progress(0.8 * i / n, f"Ajout de {name}…")
        im = normalize(open_image(path, fmt, min_side=cell))
        images.append(im)
    aspects = sorted(im.width / im.height for im in images)
    aspect = aspects[len(aspects) // 2] if cover else 1.0              # cellules au format le plus courant
    cw, ch = cell, max(1, round(cell / aspect))
    W, H = cols * cw + (cols + 1) * gap, rows * ch + (rows + 1) * gap
    canvas = Image.new("RGBA", (W, H), bg)
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        x, y = gap + c * (cw + gap), gap + r * (ch + gap)
        tile = ImageOps.fit(im.convert("RGBA"), (cw, ch), Image.LANCZOS) if cover else ImageOps.contain(im.convert("RGBA"), (cw, ch), Image.LANCZOS)
        canvas.alpha_composite(tile, (x + (cw - tile.width) // 2, y + (ch - tile.height) // 2))
    fmt = opts.get("collage_fmt") or "jpg"
    ctx.progress(0.95, "Enregistrement…")
    if fmt == "png":
        canvas.save(dst, "PNG", compress_level=6)
    else:
        flatten(canvas, bg).save(dst, "JPEG", quality=90, optimize=True, progressive=True)
    return [Path(dst)]
