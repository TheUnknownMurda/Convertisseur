"""Outils PDF : découper, extraire ou supprimer des pages, pivoter, protéger, déverrouiller, filigrane,
numérotation, PDF cherchable (OCR), extraction des images, nettoyage des métadonnées."""
from __future__ import annotations

import re
import secrets
from pathlib import Path

from ..i18n import tr
from ..util import FinalError, unique_path

FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")
FONT_REGULAR = Path("C:/Windows/Fonts/arial.ttf")


def _open(src):
    import pymupdf
    try:
        doc = pymupdf.open(str(src))
    except Exception as e:
        raise FinalError(f"PDF illisible : {e}")
    if doc.needs_pass:
        raise FinalError("Ce PDF est protégé par un mot de passe : retirez-le d'abord avec l'outil « Déverrouiller un PDF ».")
    return doc


def _save(doc, dst, **kw):
    try:
        doc.subset_fonts()                       # polices ajoutées : seulement les caractères utilisés
    except Exception:
        pass
    doc.save(str(dst), garbage=3, deflate=True, **kw)


def parse_order(spec: str, count: int) -> list[int]:
    """« 3, 1-2, 8- » -> pages dans l'ordre donné (indices à partir de 0). Accepte « pair » et « impair »."""
    s = re.sub(r"\s*-\s*", "-", (spec or "").strip().lower())
    if not s:
        raise FinalError("Indiquez les pages dans les réglages (exemple : 1-3, 7, 10-).")
    out: list[int] = []
    for part in re.split(r"[,;\s]+", s):
        if not part:
            continue
        m = re.fullmatch(r"(\d*)-(\d*)", part)
        if m:
            a = int(m.group(1)) if m.group(1) else 1
            b = int(m.group(2)) if m.group(2) else count
            rng = range(a, b + 1) if a <= b else range(a, b - 1, -1)
        elif part.isdigit():
            rng = [int(part)]
        elif part in ("pair", "paires", "pairs"):
            rng = range(2, count + 1, 2)
        elif part in ("impair", "impaires", "impairs"):
            rng = range(1, count + 1, 2)
        else:
            raise FinalError(f"Pages non comprises : « {part} » (exemple : 1-3, 7, 10-).")
        out += [p - 1 for p in rng if 1 <= p <= count]
    if not out:
        raise FinalError(f"Aucune de ces pages n'existe : ce PDF en compte {count}.")
    return out


def _rgb(hex_color: str, default=(0.5, 0.5, 0.5)):
    try:
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except Exception:
        return default


def _font(doc_page, bold=True):
    """Arial de Windows (accents et symboles), sinon Helvetica intégrée."""
    path = FONT_BOLD if bold else FONT_REGULAR
    if path.is_file():
        name = "ArialB" if bold else "ArialR"
        try:
            doc_page.insert_font(fontname=name, fontfile=str(path))
            return name, path
        except Exception:
            pass
    return "helv", None


def _text_width(text, fontsize, fontfile):
    import pymupdf
    if fontfile:
        return pymupdf.Font(fontfile=str(fontfile)).text_length(text, fontsize=fontsize)
    return pymupdf.get_text_length(text, fontname="helv", fontsize=fontsize)


# ---------------------------------------------------------------- pages
def split(ctx, src, sfmt, dst, d):
    import pymupdf
    o = ctx.opts
    doc = _open(src)
    n = doc.page_count
    mode = o.get("split_mode") or "each"
    if mode == "ranges":
        spec = (o.get("split_ranges") or "").strip()
        if not spec:
            raise FinalError("Indiquez les plages dans les réglages (exemple : 1-3, 4-6, 7-).")
        groups = [parse_order(part, n) for part in re.split(r"[,;]+", spec) if part.strip()]
    else:
        size = 1 if mode == "each" else max(1, int(mode))
        groups = [list(range(i, min(i + size, n))) for i in range(0, n, size)]
    folder = unique_path(Path(dst).parent, f"{ctx.stem} {tr('(pages)')}")
    folder.mkdir(parents=True)
    width = max(2, len(str(n)))
    for gi, pages in enumerate(groups):
        ctx.progress(gi / len(groups), f"Fichier {gi + 1}/{len(groups)}…")
        part = pymupdf.open()
        for p in pages:
            part.insert_pdf(doc, from_page=p, to_page=p)
        first, last = pages[0] + 1, pages[-1] + 1
        label = (f"{tr('page')} {first:0{width}d}" if len(pages) == 1
                 else f"{tr('pages')} {first:0{width}d}-{last:0{width}d}")
        part.save(str(folder / f"{ctx.stem} - {label}.pdf"), garbage=3, deflate=True)
    return [folder]


def pages(ctx, src, sfmt, dst, d):
    o = ctx.opts
    doc = _open(src)
    n = doc.page_count
    chosen = parse_order(o.get("pages"), n)
    if (o.get("pages_mode") or "keep") == "remove":
        drop = set(chosen)
        keep = [i for i in range(n) if i not in drop]
        if not keep:
            raise FinalError("Toutes les pages seraient supprimées.")
    else:
        keep = chosen
    ctx.progress(None, f"{len(keep)} page(s) conservée(s)…")
    doc.select(keep)
    _save(doc, dst)
    return [dst]


def rotate(ctx, src, sfmt, dst, d):
    o = ctx.opts
    doc = _open(src)
    angle = int(o.get("pdf_angle") or 90)
    targets = set(parse_order(o.get("pages"), doc.page_count)) if (o.get("pages") or "").strip() else range(doc.page_count)
    for i in targets:
        page = doc[i]
        page.set_rotation((page.rotation + angle) % 360)
    _save(doc, dst)
    return [dst]


# ---------------------------------------------------------------- sécurité
def protect(ctx, src, sfmt, dst, d):
    import pymupdf
    o = ctx.opts
    password = (o.get("password") or "").strip()
    if not password:
        raise FinalError("Indiquez un mot de passe dans les réglages.")
    doc = _open(src)
    full = (pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_MODIFY | pymupdf.PDF_PERM_COPY | pymupdf.PDF_PERM_ANNOTATE
            | pymupdf.PDF_PERM_FORM | pymupdf.PDF_PERM_ACCESSIBILITY | pymupdf.PDF_PERM_ASSEMBLE | pymupdf.PDF_PERM_PRINT_HQ)
    restrict = bool(o.get("pdf_restrict"))
    perms = pymupdf.PDF_PERM_ACCESSIBILITY if restrict else full
    owner = secrets.token_urlsafe(24) if restrict else password   # restrictions : mot de passe propriétaire secret
    ctx.progress(None, "Chiffrement AES-256…")
    _save(doc, dst, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=owner, permissions=perms)
    return [dst]


def unlock(ctx, src, sfmt, dst, d):
    import pymupdf
    try:
        doc = pymupdf.open(str(src))
    except Exception as e:
        raise FinalError(f"PDF illisible : {e}")
    if doc.needs_pass:
        password = (ctx.opts.get("password") or "").strip()
        if not password:
            raise FinalError("Indiquez le mot de passe du PDF dans les réglages.")
        if not doc.authenticate(password):
            raise FinalError("Mot de passe incorrect.")
    elif not doc.is_encrypted:
        raise FinalError("Ce PDF n'est pas protégé : il n'y a rien à retirer.")
    doc.save(str(dst), encryption=pymupdf.PDF_ENCRYPT_NONE, garbage=3, deflate=True)
    return [dst]


def clean(ctx, src, sfmt, dst, d):
    doc = _open(src)
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    _save(doc, dst)
    return [dst]


# ---------------------------------------------------------------- annotations
WM_SIZES = {"small": 0.06, "medium": 0.1, "large": 0.15}


def watermark(ctx, src, sfmt, dst, d):
    import pymupdf
    o = ctx.opts
    doc = _open(src)
    text = (o.get("wm_text") or "").strip() or tr("CONFIDENTIEL")
    opacity = max(0.03, min(1.0, (o.get("wm_opacity") or 25) / 100))
    color = _rgb(o.get("wm_color") or "#808080")
    pos = o.get("wm_pos") or "diagonal"
    ratio = WM_SIZES.get(o.get("wm_size") or "medium", 0.1)
    for i, page in enumerate(doc):
        ctx.progress(i / doc.page_count, f"Page {i + 1}/{doc.page_count}…")
        fontname, fontfile = _font(page)
        r = page.rect                                    # page telle qu'affichée
        fs = max(8.0, min(r.width, r.height) * ratio)
        tw = _text_width(text, fs, fontfile)
        if pos in ("diagonal", "tiled") and tw > 0.9 * (r.width ** 2 + r.height ** 2) ** 0.5:
            fs *= 0.9 * (r.width ** 2 + r.height ** 2) ** 0.5 / tw
            tw = _text_width(text, fs, fontfile)
        elif pos not in ("diagonal", "tiled") and tw > r.width * 0.9:
            fs *= r.width * 0.9 / tw
            tw = _text_width(text, fs, fontfile)
        margin = max(18, fs * 0.6)
        spots = []
        angle = 0
        if pos == "diagonal":
            angle = 45 if r.width < r.height else 30
            spots = [(r.width / 2, r.height / 2)]
        elif pos == "tiled":
            angle = 30
            step_x, step_y = tw * 1.4 + fs, fs * 4
            y = step_y / 2
            row = 0
            while y < r.height + step_y:
                x = (step_x / 2) * (row % 2)
                while x < r.width + step_x:
                    spots.append((x, y))
                    x += step_x
                y += step_y
                row += 1
        else:
            x = {"tl": margin + tw / 2, "bl": margin + tw / 2, "tr": r.width - margin - tw / 2,
                 "br": r.width - margin - tw / 2}.get(pos, r.width / 2)
            y = {"tl": margin + fs / 2, "tr": margin + fs / 2, "top": margin + fs / 2,
                 "bl": r.height - margin - fs / 2, "br": r.height - margin - fs / 2,
                 "bottom": r.height - margin - fs / 2}.get(pos, r.height / 2)
            spots = [(x, y)]
        for cx, cy in spots:
            center = pymupdf.Point(cx, cy) * page.derotation_matrix   # coordonnées de la page non pivotée
            start = pymupdf.Point(center.x - tw / 2, center.y + fs * 0.35)
            mat = pymupdf.Matrix(angle + page.rotation if angle else page.rotation)
            page.insert_text(start, text, fontsize=fs, fontname=fontname, color=color,
                             fill_opacity=opacity, stroke_opacity=opacity, morph=(center, mat), overlay=True)
    _save(doc, dst)
    return [dst]


NUM_FORMATS = {"n": "{n}", "page": "Page {n}", "of": "{n} / {total}", "page_of": "Page {n} sur {total}"}


def number(ctx, src, sfmt, dst, d):
    import pymupdf
    o = ctx.opts
    doc = _open(src)
    start = int(o.get("num_start") or 1)
    total = start + doc.page_count - 1
    template = tr(NUM_FORMATS.get(o.get("num_fmt") or "n", "{n}"))
    pos = o.get("num_pos") or "bc"
    for i, page in enumerate(doc):
        fontname, fontfile = _font(page, bold=False)
        r = page.rect
        fs = max(8.0, min(13.0, r.width / 50))
        label = template.format(n=start + i, total=total)
        tw = _text_width(label, fs, fontfile)
        margin = max(20.0, r.height * 0.03)
        x = {"bl": margin, "tl": margin, "br": r.width - margin - tw, "tr": r.width - margin - tw}.get(pos, (r.width - tw) / 2)
        y = margin + fs if pos in ("tl", "tc", "tr") else r.height - margin
        point = pymupdf.Point(x, y) * page.derotation_matrix
        page.insert_text(point, label, fontsize=fs, fontname=fontname, color=(0.25, 0.25, 0.25),
                         rotate=page.rotation, overlay=True)
    _save(doc, dst)
    return [dst]


# ---------------------------------------------------------------- extraction
def images(ctx, src, sfmt, dst, d):
    import pymupdf
    doc = _open(src)
    folder = unique_path(Path(dst).parent, f"{ctx.stem} {tr('(images)')}")
    folder.mkdir(parents=True)
    seen, count = set(), 0
    for pno, page in enumerate(doc):
        ctx.progress(pno / doc.page_count, f"Page {pno + 1}/{doc.page_count}…")
        for img in page.get_images(full=True):
            xref, smask = img[0], img[1]
            if xref in seen:
                continue
            seen.add(xref)
            try:
                info = doc.extract_image(xref)
            except Exception:
                continue
            if not info or info.get("width", 0) < 24 or info.get("height", 0) < 24:
                continue                         # pastilles et puces décoratives
            count += 1
            base = folder / f"{tr('page')} {pno + 1:03d} - {tr('image')} {count:03d}"
            try:
                if smask:                        # transparence : on recompose en PNG
                    pix = pymupdf.Pixmap(doc, xref)
                    if pix.n - pix.alpha >= 4:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    pix = pymupdf.Pixmap(pix, pymupdf.Pixmap(doc, smask))
                    pix.save(str(base.with_suffix(".png")))
                elif info.get("ext") in ("jpeg", "jpg", "png", "jpx", "jp2"):
                    ext = {"jpeg": "jpg", "jpx": "jp2"}.get(info["ext"], info["ext"])
                    base.with_suffix(f".{ext}").write_bytes(info["image"])
                else:
                    pix = pymupdf.Pixmap(doc, xref)
                    if pix.n - pix.alpha >= 4:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    pix.save(str(base.with_suffix(".png")))
            except Exception:
                count -= 1
    if not count:
        folder.rmdir()
        raise FinalError("Ce PDF ne contient aucune image à extraire.")
    return [folder]


# ---------------------------------------------------------------- OCR
def ocr(ctx, src, sfmt, dst, d):
    """Ajoute un calque de texte invisible (reconnaissance de Windows) aux pages scannées."""
    import pymupdf
    from .ocr import ocr_words
    doc = _open(src)
    lang = o_lang = ctx.opts.get("ocr_lang") or "auto"
    lang = "" if o_lang == "auto" else lang
    todo = [i for i, p in enumerate(doc) if len(p.get_text("text").strip()) < 20]
    if not todo:
        raise FinalError("Ce PDF contient déjà du texte sélectionnable : rien à reconnaître.")
    dpi = 250
    pngs = []
    for k, i in enumerate(todo):
        ctx.progress(0.25 * k / len(todo), f"Préparation de la page {i + 1}/{doc.page_count}…")
        png = ctx.tmp / f"ocr_page_{i + 1:04d}.png"
        doc[i].get_pixmap(dpi=dpi, alpha=False).save(str(png))
        pngs.append(png)
    ctx.progress(0.3, f"Reconnaissance du texte ({len(todo)} page(s))…")
    results = ocr_words(ctx, pngs, lang)
    found = 0
    scale = 72 / dpi
    for k, (i, words) in enumerate(zip(todo, results)):
        page = doc[i]
        fontname, fontfile = _font(page, bold=False)
        for x, y, w, h, text in words:
            rect = pymupdf.Rect(x * scale, y * scale, (x + w) * scale, (y + h) * scale)
            if rect.is_empty or not text.strip():
                continue
            fs = max(2.0, rect.height * 0.85)
            tw = _text_width(text, fs, fontfile) or 1
            base = pymupdf.Point(rect.x0, rect.y1 - rect.height * 0.18) * page.derotation_matrix
            stretch = pymupdf.Matrix(rect.width / tw, 1) * pymupdf.Matrix(page.rotation)
            page.insert_text(base, text, fontsize=fs, fontname=fontname, render_mode=3,
                             morph=(base, stretch), overlay=True)
            found += 1
        ctx.progress(0.3 + 0.65 * (k + 1) / len(todo), f"Page {i + 1}/{doc.page_count}…")
    if not found:
        raise FinalError("Aucun texte n'a été reconnu dans les pages scannées.")
    _save(doc, dst)
    return [dst]
