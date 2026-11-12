"""Polices : TTF, OTF, WOFF, WOFF2 entre elles, et aperçu (PNG, PDF)."""
from __future__ import annotations

from pathlib import Path

from ..util import FinalError

SAMPLE = "Portez ce vieux whisky au juge blond qui fume. 0123456789"


def _open(path):
    from fontTools.ttLib import TTFont
    try:
        return TTFont(str(path))
    except Exception as e:
        raise FinalError(f"Police illisible : {e}")


def _otf_to_ttf(font):
    """Contours cubiques (CFF) -> quadratiques (glyf), d'après l'exemple officiel de fontTools."""
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import newTable
    order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    quads = {}
    for name in glyph_set.keys():
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        quads[name] = pen.glyph()
    font["loca"] = newTable("loca")
    font["glyf"] = glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = quads
    for tag in ("CFF ", "CFF2", "VORG"):
        if tag in font:
            del font[tag]
    glyf.compile(font)
    hmtx = font["hmtx"]
    for name, g in glyf.glyphs.items():
        if hasattr(g, "xMin"):
            hmtx[name] = (hmtx[name][0], g.xMin)
    font["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    for attr in ("maxZones",):
        setattr(maxp, attr, 1)
    for attr in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs", "maxStackElements",
                 "maxSizeOfInstructions"):
        setattr(maxp, attr, 0)
    maxp.maxComponentElements = max((len(getattr(g, "components", []) or []) for g in glyf.glyphs.values()),
                                    default=0)
    maxp.compile(font)
    post = font["post"]
    post.formatType, post.extraNames, post.mapping, post.glyphOrder = 2.0, [], {}, order
    try:
        post.compile(font)
    except OverflowError:
        post.formatType = 3
    font["head"].glyphDataFormat = 0
    font.sfntVersion = "\000\001\000\000"


def _ttf_to_otf(font):
    """Contours quadratiques (glyf) -> CFF (conversion exacte en courbes cubiques)."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    glyph_set = font.getGlyphSet()
    charstrings = {}
    for name in font.getGlyphOrder():
        pen = T2CharStringPen(font["hmtx"][name][0], glyph_set)
        glyph_set[name].draw(pen)
        charstrings[name] = pen.getCharString()
    ps_name = (font["name"].getDebugName(6) or "Police").replace(" ", "")
    full_name = font["name"].getDebugName(4) or ps_name
    for tag in ("glyf", "loca", "fpgm", "prep", "cvt ", "gasp", "hdmx", "LTSH", "VDMX"):
        if tag in font:
            del font[tag]
    fb = FontBuilder(font=font)
    fb.isTTF = False
    fb.setupCFF(ps_name, {"FullName": full_name}, charstrings, {})
    font["maxp"].tableVersion = 0x00005000
    font.sfntVersion = "OTTO"


def convert(ctx, src, sfmt, dst, d):
    ctx.progress(None, "Conversion de la police…")
    font = _open(src)
    cff = "CFF " in font or "CFF2" in font
    if d == "ttf" and cff:
        _otf_to_ttf(font)
    elif d == "otf" and not cff and "glyf" in font:
        _ttf_to_otf(font)
    font.flavor = {"woff": "woff", "woff2": "woff2"}.get(d)
    font.save(str(dst))
    return [dst]


def _as_sfnt(ctx, src) -> Path:
    """Copie TTF/OTF non compressée (les WOFF ne sont pas lus partout)."""
    font = _open(src)
    if not font.flavor:
        return Path(src)
    font.flavor = None
    out = ctx.tmp / ("police.otf" if "CFF " in font else "police.ttf")
    font.save(str(out))
    return out


def preview(ctx, src, sfmt, dst, d):
    from PIL import Image, ImageDraw, ImageFont
    plain = _as_sfnt(ctx, src)
    font = _open(plain)
    name = font["name"].getDebugName(4) or Path(src).stem
    from ..i18n import tr
    text = (ctx.opts.get("font_text") or "").strip() or tr(SAMPLE)
    sizes = [16, 24, 36, 48, 72]
    if d == "pdf":
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_font(fontname="F0", fontfile=str(plain))
        y = 70
        page.insert_text((50, y), name, fontname="helv", fontsize=20)
        y += 30
        for s in sizes:
            page.insert_textbox(pymupdf.Rect(50, y, 545, y + s * 2.6), text, fontname="F0", fontsize=s)
            y += s * 2.6 + 10
        page.insert_textbox(pymupdf.Rect(50, y, 545, y + 120), "ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz\n"
                            "àâçéèêëîïôûùüÿœæ ÀÉÈÇ  .,;:!?«»()[]{}@#&%$€", fontname="F0", fontsize=18)
        doc.save(str(dst))
        return [dst]
    width, pad = 1600, 50
    fonts = [ImageFont.truetype(str(plain), s) for s in sizes]
    head = ImageFont.truetype("arial.ttf", 30) if Path("C:/Windows/Fonts/arial.ttf").exists() else fonts[1]
    height = pad * 2 + 60 + sum(int(s * 1.6) + 20 for s in sizes) + 180
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((pad, pad), name, font=head, fill="#555")
    y = pad + 60
    for s, f in zip(sizes, fonts):
        draw.text((pad, y), text, font=f, fill="#111")
        y += int(s * 1.6) + 20
    draw.text((pad, y), "ABCDEFGHIJKLMNOPQRSTUVWXYZ  abcdefghijklmnopqrstuvwxyz", font=fonts[2], fill="#333")
    draw.text((pad, y + 70), "àâçéèêëîïôûùüÿœæ  .,;:!?«»()[]{}@#&%$€", font=fonts[2], fill="#333")
    img.save(dst)
    return [dst]
