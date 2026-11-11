"""Outils HTML : arbre DOM minimal, HTML -> texte / Markdown / DOCX, impression PDF (Edge ou MuPDF)."""
from __future__ import annotations

import base64
import html as htmllib
import io
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from ..util import NO_WINDOW

VOID = {"br", "img", "hr", "meta", "link", "input", "col", "area", "base", "wbr", "source", "param", "embed"}
SKIP = {"script", "style", "head", "title", "noscript", "template", "svg", "math", "object", "iframe"}
BLOCK = {"p", "div", "section", "article", "main", "header", "footer", "aside", "nav", "figure", "figcaption",
         "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "pre", "blockquote", "table", "thead", "tbody",
         "tfoot", "tr", "td", "th", "hr", "dl", "dt", "dd", "address", "center", "body", "html", "form",
         "fieldset", "details", "summary", "caption"}
AUTO_CLOSE = {"p", "li", "tr", "td", "th", "dt", "dd", "option"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.children, self.parent = tag, attrs or {}, [], parent

    def text(self) -> str:
        out = []
        for c in self.children:
            out.append(c if isinstance(c, str) else ("" if c.tag in SKIP else c.text()))
        return "".join(out)

    def find(self, tag):
        for c in self.children:
            if isinstance(c, Node):
                if c.tag == tag:
                    return c
                r = c.find(tag)
                if r is not None:
                    return r
        return None

    def find_all(self, tag, out=None):
        out = [] if out is None else out
        for c in self.children:
            if isinstance(c, Node):
                if c.tag == tag:
                    out.append(c)
                c.find_all(tag, out)
        return out


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in AUTO_CLOSE:
            n = self.cur
            while n is not self.root and n.tag not in ("ul", "ol", "table", "dl", "body", "div", "blockquote"):
                if n.tag == tag:
                    self.cur = n.parent
                    break
                n = n.parent
        node = Node(tag, {k.lower(): (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag.lower(), {k.lower(): (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)

    def handle_endtag(self, tag):
        tag = tag.lower()
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if data:
            self.cur.children.append(data)


def parse_html(text: str) -> Node:
    b = _Builder()
    b.feed(text)
    b.close()
    return b.root


def body_of(root: Node) -> Node:
    return root.find("body") or root


def title_of(root: Node, default="") -> str:
    t = root.find("title")
    if t is not None and t.text().strip():
        return t.text().strip()
    h = root.find("h1")
    return h.text().strip() if h is not None and h.text().strip() else default


# ---------------------------------------------------------------- sérialisation XHTML
def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _attr(s: str) -> str:
    return _esc(s).replace('"', "&quot;")


_SAFE_ATTRS = {"href", "src", "alt", "title", "colspan", "rowspan", "id", "class", "width", "height", "lang", "dir",
               "start", "type", "scope", "headers", "abbr", "cite", "datetime", "xml:lang"}


def serialize(node, out=None, xhtml=True) -> str:
    """Re-sérialise en XHTML bien formé (attributs filtrés, balises vides fermées)."""
    out = [] if out is None else out
    for c in node.children:
        if isinstance(c, str):
            out.append(_esc(c))
            continue
        if c.tag in SKIP or not re.fullmatch(r"[a-z][a-z0-9]*", c.tag):
            if c.tag not in SKIP:
                serialize(c, out, xhtml)
            continue
        attrs = "".join(f' {k}="{_attr(v)}"' for k, v in c.attrs.items() if k in _SAFE_ATTRS)
        if c.tag in VOID:
            out.append(f"<{c.tag}{attrs}/>" if xhtml else f"<{c.tag}{attrs}>")
        else:
            out.append(f"<{c.tag}{attrs}>")
            serialize(c, out, xhtml)
            out.append(f"</{c.tag}>")
    return "".join(out)


# ---------------------------------------------------------------- images intégrées
_DATA_URI = re.compile(r"data:([\w/+.-]+)?(;base64)?,(.*)", re.S)


def load_image_src(src: str, base_dir=None) -> tuple[bytes, str] | None:
    """Retourne (octets, type MIME) pour une URI data:, un chemin local ou file://."""
    if not src:
        return None
    m = _DATA_URI.match(src.strip())
    if m:
        mime = m.group(1) or "image/png"
        payload = m.group(3)
        try:
            data = base64.b64decode(payload) if m.group(2) else unquote(payload).encode("latin-1")
        except Exception:
            return None
        return data, mime
    if re.match(r"https?://", src, re.I):
        return None
    if src.lower().startswith("file:"):
        path = Path(unquote(urlparse(src).path.lstrip("/")))
    else:
        path = Path(unquote(src.split("#")[0].split("?")[0]))
        if not path.is_absolute() and base_dir:
            path = Path(base_dir) / path
    try:
        data = path.read_bytes()
    except Exception:
        return None
    ext = path.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "svg": "image/svg+xml",
            "webp": "image/webp", "bmp": "image/bmp"}.get(ext, "application/octet-stream")
    return data, mime


def to_data_uri(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def inline_images(root: Node, base_dir) -> None:
    for img in root.find_all("img"):
        src = img.attrs.get("src", "")
        if src and not src.startswith("data:"):
            got = load_image_src(src, base_dir)
            if got:
                img.attrs["src"] = to_data_uri(*got)


# ---------------------------------------------------------------- texte brut
def html_to_text(text: str) -> str:
    root = body_of(parse_html(text))
    out: list[str] = []

    def walk(node, pre=False):
        for c in node.children:
            if isinstance(c, str):
                out.append(c if pre else re.sub(r"\s+", " ", c))
                continue
            if c.tag in SKIP:
                continue
            if c.tag == "br":
                out.append("\n")
            elif c.tag == "li":
                out.append("\n• ")
                walk(c, pre)
            elif c.tag in ("td", "th"):
                walk(c, pre)
                out.append("\t")
            elif c.tag == "img":
                alt = c.attrs.get("alt")
                if alt:
                    out.append(f"[{alt}]")
            elif c.tag in BLOCK:
                out.append("\n\n" if c.tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote",
                                               "table", "ul", "ol") else "\n")
                walk(c, pre or c.tag == "pre")
                out.append("\n")
            else:
                walk(c, pre)

    walk(root)
    txt = "".join(out)
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n[ ]+", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip() + "\n"


# ---------------------------------------------------------------- Markdown
def html_to_markdown(text: str) -> str:
    root = body_of(parse_html(text))

    def inline(node) -> str:
        parts = []
        for c in node.children:
            if isinstance(c, str):
                parts.append(re.sub(r"\s+", " ", c).replace("*", r"\*").replace("_", r"\_"))
                continue
            t = c.tag
            if t in SKIP:
                continue
            inner = inline(c)
            if t in ("strong", "b"):
                parts.append(f"**{inner.strip()}**" if inner.strip() else "")
            elif t in ("em", "i", "cite"):
                parts.append(f"*{inner.strip()}*" if inner.strip() else "")
            elif t in ("code", "kbd", "tt", "samp"):
                parts.append(f"`{c.text()}`")
            elif t in ("s", "del", "strike"):
                parts.append(f"~~{inner.strip()}~~")
            elif t == "a":
                href = c.attrs.get("href", "")
                parts.append(f"[{inner.strip()}]({href})" if href and not href.startswith("#") else inner)
            elif t == "img":
                parts.append(f"![{c.attrs.get('alt', '')}]({c.attrs.get('src', '')})")
            elif t == "br":
                parts.append("  \n")
            elif t in BLOCK:
                parts.append(" " + inner + " ")
            else:
                parts.append(inner)
        return "".join(parts)

    def block(node, depth=0) -> list[str]:
        lines: list[str] = []
        buf: list = []

        def flush():
            if buf:
                tmp = Node("span")
                tmp.children = list(buf)
                s = inline(tmp).strip()
                if s:
                    lines.extend([s, ""])
                buf.clear()

        for c in node.children:
            if isinstance(c, str) or (c.tag not in BLOCK and c.tag not in SKIP):
                buf.append(c)
                continue
            flush()
            t = c.tag
            if t in SKIP:
                continue
            if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
                s = inline(c).strip()
                if s:
                    lines.extend(["#" * int(t[1]) + " " + s, ""])
            elif t == "p":
                s = inline(c).strip()
                if s:
                    lines.extend([s, ""])
            elif t in ("ul", "ol"):
                n = int(c.attrs.get("start") or 1) if t == "ol" else 0
                for li in [x for x in c.children if isinstance(x, Node) and x.tag == "li"]:
                    sub = Node("li")
                    sub.children = [x for x in li.children if not (isinstance(x, Node) and x.tag in ("ul", "ol"))]
                    bullet = f"{n}." if t == "ol" else "-"
                    n += 1
                    lines.append("   " * depth + f"{bullet} " + inline(sub).strip())
                    for nested in [x for x in li.children if isinstance(x, Node) and x.tag in ("ul", "ol")]:
                        holder = Node("div")
                        holder.children = [nested]
                        lines.extend(l for l in block(holder, depth + 1) if l)
                lines.append("")
            elif t == "pre":
                lines.extend(["```", c.text().rstrip("\n"), "```", ""])
            elif t == "blockquote":
                inner = block(c, depth)
                lines.extend(("> " + l) if l else ">" for l in inner)
                lines.append("")
            elif t == "hr":
                lines.extend(["---", ""])
            elif t == "table":
                rows = []
                for tr in c.find_all("tr"):
                    cells = [inline(td).strip().replace("|", r"\|") for td in tr.children
                             if isinstance(td, Node) and td.tag in ("td", "th")]
                    if cells:
                        rows.append(cells)
                if rows:
                    width = max(len(r) for r in rows)
                    rows = [r + [""] * (width - len(r)) for r in rows]
                    lines.append("| " + " | ".join(rows[0]) + " |")
                    lines.append("|" + "---|" * width)
                    for r in rows[1:]:
                        lines.append("| " + " | ".join(r) + " |")
                    lines.append("")
            elif t == "img":
                lines.extend([f"![{c.attrs.get('alt', '')}]({c.attrs.get('src', '')})", ""])
            else:
                lines.extend(block(c, depth))
        flush()
        return lines

    md = "\n".join(block(root))
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


# ---------------------------------------------------------------- DOCX
def html_to_docx(text: str, dst, base_dir=None, title=None) -> None:
    import docx
    from docx.enum.text import WD_BREAK
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    root = parse_html(text)
    body = body_of(root)
    document = docx.Document()
    if title:
        document.core_properties.title = title
    styles = {s.name for s in document.styles}

    def style_ok(name):
        return name if name in styles else None

    def add_picture(run, src):
        got = load_image_src(src, base_dir)
        if not got:
            return
        data, mime = got
        try:
            from PIL import Image
            if "svg" in mime:
                from .images import svg_render
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
                        f.write(data)
                        name = f.name
                    im = svg_render(name)
                    Path(name).unlink(missing_ok=True)
                except Exception:
                    return
            else:
                im = Image.open(io.BytesIO(data))
                im.load()
            w_px = im.width
            if im.format not in ("PNG", "JPEG", "GIF", "BMP") or "svg" in mime:
                buf = io.BytesIO()
                im.convert("RGBA").save(buf, "PNG")
                data = buf.getvalue()
            width = min(6.2, max(0.2, w_px / 96))
            run.add_picture(io.BytesIO(data), width=Inches(width))
        except Exception:
            pass

    def hr_par():
        p = document.add_paragraph()
        ppr = p._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "BFC3CC")):
            bottom.set(qn(k), v)
        bdr.append(bottom)
        ppr.append(bdr)

    def inline(node, par, fmt, pre=False):
        for c in node.children:
            if isinstance(c, str):
                s = c if pre else re.sub(r"\s+", " ", c)
                if not pre and not par.runs and not s.strip():
                    continue
                if not pre and not par.text:
                    s = s.lstrip()
                if pre:
                    lines = s.split("\n")
                    for i, line in enumerate(lines):
                        r = par.add_run(line)
                        r.font.name = "Consolas"
                        r.font.size = Pt(9.5)
                        if i < len(lines) - 1:
                            r.add_break()
                    continue
                if not s:
                    continue
                r = par.add_run(s)
                r.bold = fmt.get("b") or None
                r.italic = fmt.get("i") or None
                r.underline = fmt.get("u") or None
                if fmt.get("s"):
                    r.font.strike = True
                if fmt.get("code"):
                    r.font.name = "Consolas"
                if fmt.get("sup"):
                    r.font.superscript = True
                if fmt.get("sub"):
                    r.font.subscript = True
                if fmt.get("a"):
                    r.font.color.rgb = RGBColor(0x2B, 0x4A, 0xCB)
                    r.underline = True
                continue
            t = c.tag
            if t in SKIP:
                continue
            f = dict(fmt)
            if t in ("b", "strong"):
                f["b"] = True
            elif t in ("i", "em", "cite"):
                f["i"] = True
            elif t in ("u", "ins"):
                f["u"] = True
            elif t in ("s", "del", "strike"):
                f["s"] = True
            elif t in ("code", "kbd", "tt", "samp"):
                f["code"] = True
            elif t == "sup":
                f["sup"] = True
            elif t == "sub":
                f["sub"] = True
            elif t == "a":
                f["a"] = True
            if t == "br":
                par.add_run().add_break(WD_BREAK.LINE)
            elif t == "img":
                add_picture(par.add_run(), c.attrs.get("src", ""))
            else:
                inline(c, par, f, pre or t == "pre")

    def has_block(node):
        return any(isinstance(c, Node) and c.tag in BLOCK for c in node.children)

    def blocks(node, quote=False, depth=0):
        buf = []

        def flush():
            if buf and any((isinstance(x, str) and x.strip()) or isinstance(x, Node) for x in buf):
                p = document.add_paragraph(style=style_ok("Quote") if quote else None)
                tmp = Node("span")
                tmp.children = list(buf)
                inline(tmp, p, {})
                if not p.text.strip() and not p.runs:
                    p._p.getparent().remove(p._p)
            buf.clear()

        for c in node.children:
            if isinstance(c, str) or (c.tag not in BLOCK and c.tag not in SKIP):
                buf.append(c)
                continue
            flush()
            t = c.tag
            if t in SKIP:
                continue
            if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
                p = document.add_heading(level=min(int(t[1]), 9))
                inline(c, p, {})
            elif t == "p" or (t in ("div", "figcaption", "dt", "dd", "address", "caption", "summary")
                              and not has_block(c)):
                p = document.add_paragraph(style=style_ok("Quote") if quote else None)
                inline(c, p, {})
            elif t in ("ul", "ol"):
                base = "List Number" if t == "ol" else "List Bullet"
                name = base if depth == 0 else f"{base} {min(depth + 1, 3)}"
                for li in [x for x in c.children if isinstance(x, Node) and x.tag == "li"]:
                    p = document.add_paragraph(style=style_ok(name) or style_ok(base))
                    holder = Node("li")
                    holder.children = [x for x in li.children if not (isinstance(x, Node) and x.tag in ("ul", "ol"))]
                    inline(holder, p, {})
                    for nested in [x for x in li.children if isinstance(x, Node) and x.tag in ("ul", "ol")]:
                        wrap = Node("div")
                        wrap.children = [nested]
                        blocks(wrap, quote, depth + 1)
            elif t == "pre":
                p = document.add_paragraph()
                inline(c, p, {}, pre=True)
            elif t == "blockquote":
                blocks(c, True, depth)
            elif t == "hr":
                hr_par()
            elif t == "table":
                rows = []
                for tr in c.find_all("tr"):
                    cells = [td for td in tr.children if isinstance(td, Node) and td.tag in ("td", "th")]
                    if cells:
                        rows.append(cells)
                if rows:
                    ncols = max(len(r) for r in rows)
                    table = document.add_table(rows=len(rows), cols=ncols)
                    if style_ok("Table Grid"):
                        table.style = "Table Grid"
                    for i, r in enumerate(rows):
                        for j, td in enumerate(r):
                            cell = table.cell(i, j)
                            par = cell.paragraphs[0]
                            inline(td, par, {"b": td.tag == "th"})
                    document.add_paragraph()
            elif t == "img":
                p = document.add_paragraph()
                add_picture(p.add_run(), c.attrs.get("src", ""))
            else:
                blocks(c, quote, depth)
        flush()

    blocks(body)
    document.save(str(dst))


# ---------------------------------------------------------------- PDF
PAGE_CSS = {"a4": "A4", "letter": "letter", "a5": "A5", "legal": "legal"}

DOC_CSS = """
@page { size: %(page)s; margin: 18mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #1b1c20;
       margin: 0 auto; max-width: 820px; }
h1 { font-size: 22pt; } h2 { font-size: 17pt; } h3 { font-size: 14pt; }
h1, h2, h3, h4, h5, h6 { line-height: 1.25; margin: 1.1em 0 .45em; page-break-after: avoid; }
p { margin: 0 0 .7em; }
img { max-width: 100%%; height: auto; }
table { border-collapse: collapse; margin: .8em 0; }
th, td { border: 1px solid #c9ccd6; padding: 4px 8px; vertical-align: top; text-align: left; }
th { background: #f1f2f6; }
pre, code { font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace; font-size: 9.5pt; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #f5f6f8; padding: 10px 12px; border-radius: 6px; }
blockquote { border-left: 3px solid #c9ccd6; margin: .8em 0; padding: .1em 0 .1em 12px; color: #444; }
a { color: #2b4acb; }
hr { border: 0; border-top: 1px solid #d5d8e0; margin: 1.2em 0; }
pre.plain { background: none; padding: 0; font-size: 10pt; }
"""


def wrap_html(title: str, body: str, page_size: str = "a4", lang: str = "fr", base_href: str | None = None) -> str:
    base = f'<base href="{_attr(base_href)}">' if base_href else ""
    css = DOC_CSS % {"page": PAGE_CSS.get(page_size, "A4")}
    return (f'<!DOCTYPE html>\n<html lang="{lang}"><head><meta charset="utf-8">{base}'
            f"<title>{_esc(title)}</title><style>{css}</style></head><body>\n{body}\n</body></html>\n")


def story_pdf(html_text: str, dst, page_size="a4", base_dir=None) -> None:
    import pymupdf
    archive = pymupdf.Archive(str(base_dir)) if base_dir else None
    story = pymupdf.Story(html=html_text, archive=archive)
    writer = pymupdf.DocumentWriter(str(dst))
    rect = pymupdf.paper_rect(page_size if page_size in ("a4", "a5", "letter", "legal") else "a4")
    where = rect + (48, 54, -48, -54)
    more = 1
    while more:
        dev = writer.begin_page(rect)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()


def run_edge(ctx, args: list, output: Path, timeout: float = 120) -> bool:
    """Lance Edge sans fenêtre et attend le fichier produit.

    Edge rend la main tout de suite puis travaille en arrière-plan (et ne se ferme pas toujours) :
    on attend que le fichier soit complet, puis on ferme les processus de ce profil temporaire."""
    import time
    import uuid
    edge = ctx.tools.get("edge")
    if not edge:
        return False
    token = f"edge-{uuid.uuid4().hex[:10]}"
    profile = ctx.tmp / token
    cmd = [edge, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
           "--disable-sync", "--disable-background-networking", "--mute-audio", "--hide-scrollbars",
           f"--user-data-dir={profile}", "--virtual-time-budget=10000", *args]
    output = Path(output)
    try:
        subprocess.run(cmd, capture_output=True, timeout=60, creationflags=NO_WINDOW)
        deadline, last, stable = time.time() + timeout, -1, 0
        while time.time() < deadline:
            size = output.stat().st_size if output.exists() else -1
            if size > 0 and size == last:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            last = size
            time.sleep(0.4)
    except Exception:
        pass
    finally:
        script = (f"Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object {{ $_.CommandLine "
                  f"-like '*{token}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force "
                  f"-ErrorAction SilentlyContinue }}")
        try:
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True,
                           timeout=30, creationflags=NO_WINDOW)
        except Exception:
            pass
    return output.exists() and output.stat().st_size > 0


def print_pdf(ctx, html_path: Path, dst: Path, page_size="a4") -> None:
    """Imprime une page HTML en PDF avec Edge (mise en page fidèle), sinon avec MuPDF."""
    if run_edge(ctx, ["--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={dst}",
                      Path(html_path).resolve().as_uri()], Path(dst)) and Path(dst).stat().st_size > 200:
        return
    from ..util import read_text_any
    story_pdf(read_text_any(html_path), dst, page_size, Path(html_path).parent)
