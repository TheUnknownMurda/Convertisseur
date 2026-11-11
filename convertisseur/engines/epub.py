"""Lecture et écriture d'EPUB (EPUB 3 avec table des matières NCX pour la compatibilité EPUB 2)."""
from __future__ import annotations

import datetime
import posixpath
import re
import uuid
import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from .htmlconv import Node, _attr, _esc, load_image_src, parse_html, body_of, serialize, to_data_uri

CSS = """body { font-family: serif; line-height: 1.5; margin: 0 4%; }
h1, h2, h3 { line-height: 1.25; text-align: left; }
img { max-width: 100%; height: auto; }
table { border-collapse: collapse; } td, th { border: 1px solid #999; padding: 2px 6px; }
pre { white-space: pre-wrap; font-size: .9em; }
p { margin: 0 0 .6em; }
"""

MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml",
        "webp": "image/webp", "bmp": "image/bmp"}
EXT_OF = {v: k for k, v in MIME.items() if k != "jpeg"}


def _xhtml(title, body, lang):
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" '
            f'xml:lang="{lang}">\n<head><meta charset="utf-8"/><title>{_esc(title)}</title>'
            '<link rel="stylesheet" type="text/css" href="style.css"/></head>\n'
            f"<body>\n{body}\n</body>\n</html>\n")


def _well_formed(fragment: str) -> bool:
    try:
        ET.fromstring(f"<div>{fragment}</div>")
        return True
    except ET.ParseError:
        return False


class EpubImages:
    """Extrait les images intégrées (data:) d'un fragment HTML vers des fichiers de l'EPUB."""

    def __init__(self):
        self.files: dict[str, tuple[bytes, str]] = {}

    def add(self, data: bytes, mime: str) -> str:
        ext = EXT_OF.get(mime, "png")
        if mime not in MIME.values() or mime in ("image/webp", "image/bmp"):
            try:
                import io
                from PIL import Image
                im = Image.open(io.BytesIO(data))
                buf = io.BytesIO()
                im.convert("RGBA").save(buf, "PNG")
                data, mime, ext = buf.getvalue(), "image/png", "png"
            except Exception:
                pass
        name = f"img{len(self.files) + 1:04d}.{ext}"
        self.files[name] = (data, mime)
        return name

    def fix(self, root: Node, base_dir=None) -> None:
        for img in root.find_all("img"):
            got = load_image_src(img.attrs.get("src", ""), base_dir)
            if got:
                img.attrs["src"] = "images/" + self.add(*got)
            else:
                img.attrs.pop("src", None)
                img.tag = "span"


def fragment_from_html(html_text: str, images: EpubImages, base_dir=None) -> str:
    root = body_of(parse_html(html_text))
    images.fix(root, base_dir)
    frag = serialize(root)
    if not _well_formed(frag):
        text = root.text()
        frag = "".join(f"<p>{_esc(p.strip())}</p>" for p in re.split(r"\n\s*\n", text) if p.strip())
    return frag


def build_epub(dst, title: str, author: str, chapters: list[tuple[str, str]], images: EpubImages,
               cover: tuple[bytes, str] | None = None, lang: str = "fr") -> None:
    uid = f"urn:uuid:{uuid.uuid4()}"
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    title = title or "Sans titre"
    manifest, spine, nav_items, ncx_points = [], [], [], []
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0" encoding="utf-8"?>\n<container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
                   '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                   '</rootfiles></container>')
        z.writestr("OEBPS/style.css", CSS)
        manifest.append('<item id="css" href="style.css" media-type="text/css"/>')
        if cover:
            data, mime = cover
            ext = EXT_OF.get(mime, "jpg")
            z.writestr(f"OEBPS/images/cover.{ext}", data)
            manifest.append(f'<item id="cover-image" href="images/cover.{ext}" media-type="{mime}" '
                            'properties="cover-image"/>')
            z.writestr("OEBPS/cover.xhtml", _xhtml(title, f'<div style="text-align:center"><img src="images/cover.'
                                                         f'{ext}" alt="{_attr(title)}"/></div>', lang))
            manifest.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
            spine.append('<itemref idref="cover" linear="yes"/>')
        for i, (ctitle, body) in enumerate(chapters, 1):
            fname = f"chap{i:03d}.xhtml"
            z.writestr(f"OEBPS/{fname}", _xhtml(ctitle or title, body, lang))
            manifest.append(f'<item id="c{i}" href="{fname}" media-type="application/xhtml+xml"/>')
            spine.append(f'<itemref idref="c{i}"/>')
            label = _esc(ctitle or f"Chapitre {i}")
            nav_items.append(f'<li><a href="{fname}">{label}</a></li>')
            ncx_points.append(f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{label}</text></navLabel>'
                              f'<content src="{fname}"/></navPoint>')
        for name, (data, mime) in images.files.items():
            z.writestr(f"OEBPS/images/{name}", data)
            manifest.append(f'<item id="i_{name.replace(".", "_")}" href="images/{name}" media-type="{mime}"/>')
        nav = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" '
               f'xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}"><head><meta charset="utf-8"/>'
               f'<title>{_esc(title)}</title></head><body><nav epub:type="toc" id="toc"><h1>Table des matières</h1>'
               f'<ol>{"".join(nav_items)}</ol></nav></body></html>')
        z.writestr("OEBPS/nav.xhtml", nav)
        manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
        ncx = ('<?xml version="1.0" encoding="utf-8"?>\n<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" '
               f'version="2005-1"><head><meta name="dtb:uid" content="{uid}"/></head><docTitle><text>{_esc(title)}'
               f'</text></docTitle><navMap>{"".join(ncx_points)}</navMap></ncx>')
        z.writestr("OEBPS/toc.ncx", ncx)
        manifest.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        cover_meta = '<meta name="cover" content="cover-image"/>' if cover else ""
        opf = ('<?xml version="1.0" encoding="utf-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" '
               'version="3.0" unique-identifier="uid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
               f'<dc:identifier id="uid">{uid}</dc:identifier><dc:title>{_esc(title)}</dc:title>'
               f'<dc:creator>{_esc(author or "Inconnu")}</dc:creator><dc:language>{lang}</dc:language>'
               f'<meta property="dcterms:modified">{now}</meta>{cover_meta}</metadata>'
               f'<manifest>{"".join(manifest)}</manifest><spine toc="ncx">{"".join(spine)}</spine></package>')
        z.writestr("OEBPS/content.opf", opf)


# ---------------------------------------------------------------- lecture
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_epub_html(path) -> tuple[str, str, str]:
    """Rassemble le contenu d'un EPUB (ordre de lecture) en une page HTML autonome.

    Retourne (titre, auteur, html)."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        container = ET.fromstring(z.read("META-INF/container.xml"))
        opf_path = next(el.get("full-path") for el in container.iter() if _local(el.tag) == "rootfile")
        opf = ET.fromstring(z.read(opf_path))
        base = posixpath.dirname(opf_path)
        title = author = ""
        manifest, spine = {}, []
        for el in opf.iter():
            tag = _local(el.tag)
            if tag == "title" and not title:
                title = (el.text or "").strip()
            elif tag == "creator" and not author:
                author = (el.text or "").strip()
            elif tag == "item":
                manifest[el.get("id")] = (el.get("href"), el.get("media-type", ""))
            elif tag == "itemref":
                spine.append(el.get("idref"))
        parts = []
        for idref in spine:
            href, mt = manifest.get(idref, (None, ""))
            if not href or "html" not in mt:
                continue
            item_path = posixpath.normpath(posixpath.join(base, unquote(href)))
            if item_path not in names:
                continue
            raw = z.read(item_path).decode("utf-8", "replace")
            root = body_of(parse_html(raw))
            item_dir = posixpath.dirname(item_path)
            for img in root.find_all("img") + root.find_all("image"):
                src = img.attrs.get("src") or img.attrs.get("xlink:href") or img.attrs.get("href") or ""
                ip = posixpath.normpath(posixpath.join(item_dir, unquote(src)))
                if ip in names:
                    ext = ip.rsplit(".", 1)[-1].lower()
                    img.tag = "img"
                    img.attrs = {"src": to_data_uri(z.read(ip), MIME.get(ext, "image/png")),
                                 "alt": img.attrs.get("alt", "")}
            for svg in root.find_all("svg"):
                imgs = [i for i in svg.find_all("img")]
                if imgs:
                    svg.tag, svg.attrs, svg.children = "div", {}, imgs
            for a in root.find_all("a"):
                href2 = a.attrs.get("href", "")
                if href2 and not re.match(r"[a-z]+:", href2):
                    a.attrs.pop("href", None)
            parts.append(f"<section>{serialize(root, xhtml=False)}</section>")
    from .htmlconv import wrap_html
    return title, author, wrap_html(title or Path(path).stem, "\n".join(parts))
