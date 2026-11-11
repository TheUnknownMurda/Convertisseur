"""Conversions de documents texte : DOCX (mammoth), Markdown, TXT, HTML, EPUB."""
from __future__ import annotations

import html as htmllib
import re
from pathlib import Path

from ..util import UserError, read_text_any
from .htmlconv import (Node, body_of, html_to_docx as _html_to_docx, html_to_markdown, html_to_text, inline_images,
                       parse_html, print_pdf, serialize, title_of, wrap_html)

STYLE_MAP = """
p[style-name='Title'] => h1.title:fresh
p[style-name='Titre'] => h1.title:fresh
p[style-name='Subtitle'] => h2.subtitle:fresh
p[style-name='Sous-titre'] => h2.subtitle:fresh
p[style-name='Quote'] => blockquote:fresh
p[style-name='Citation'] => blockquote:fresh
"""


def _page(ctx):
    return ctx.opts.get("page_size") or "a4"


def docx_to(ctx, src, sfmt, dst, d):
    import mammoth
    ctx.progress(None, "Lecture du document Word…")
    with open(src, "rb") as f:
        if d == "txt":
            text = mammoth.extract_raw_text(f).value
            Path(dst).write_text(re.sub(r"\n{3,}", "\n\n", text).strip() + "\n", encoding="utf-8")
            return [dst]
        body = mammoth.convert_to_html(f, style_map=STYLE_MAP).value
    if d == "md":
        Path(dst).write_text(html_to_markdown(body), encoding="utf-8")
    else:
        title = title_of(parse_html(body), ctx.stem)
        Path(dst).write_text(wrap_html(title, body, _page(ctx)), encoding="utf-8")
    return [dst]


def md_to_html(ctx, src, sfmt, dst, d):
    import markdown
    text = read_text_any(src)
    body = markdown.markdown(text, extensions=["extra", "sane_lists", "toc"], output_format="html")
    root = parse_html(body)
    inline_images(root, Path(src).parent)
    body = serialize(root, xhtml=False)
    Path(dst).write_text(wrap_html(title_of(root, ctx.stem), body, _page(ctx)), encoding="utf-8")
    return [dst]


def txt_to_html(ctx, src, sfmt, dst, d):
    text = read_text_any(src)
    body = f'<pre class="plain">{htmllib.escape(text)}</pre>'
    Path(dst).write_text(wrap_html(ctx.stem, body, _page(ctx)), encoding="utf-8")
    return [dst]


def txt_to_docx(ctx, src, sfmt, dst, d):
    import docx
    from docx.shared import Pt
    text = read_text_any(src)
    document = docx.Document()
    style = document.styles["Normal"]
    style.paragraph_format.space_after = Pt(0)
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(str(dst))
    return [dst]


def html_to_txt(ctx, src, sfmt, dst, d):
    Path(dst).write_text(html_to_text(read_text_any(src)), encoding="utf-8")
    return [dst]


def html_to_md(ctx, src, sfmt, dst, d):
    Path(dst).write_text(html_to_markdown(read_text_any(src)), encoding="utf-8")
    return [dst]


def html_to_docx(ctx, src, sfmt, dst, d):
    ctx.progress(None, "Création du document Word…")
    text = read_text_any(src)
    _html_to_docx(text, dst, base_dir=Path(src).parent, title=title_of(parse_html(text), ctx.stem))
    return [dst]


def html_to_pdf(ctx, src, sfmt, dst, d):
    ctx.progress(None, "Mise en page du PDF…")
    print_pdf(ctx, Path(src), Path(dst), _page(ctx))
    if not Path(dst).exists():
        raise UserError("La création du PDF a échoué.")
    return [dst]


def _flatten_blocks(body: Node) -> list:
    nodes = [c for c in body.children if not (isinstance(c, str) and not c.strip())]
    while len(nodes) == 1 and isinstance(nodes[0], Node) and nodes[0].tag in ("div", "article", "main"):
        nodes = [c for c in nodes[0].children if not (isinstance(c, str) and not c.strip())]
    return nodes


def html_to_epub(ctx, src, sfmt, dst, d):
    from .epub import EpubImages, build_epub, fragment_from_html
    text = read_text_any(src)
    root = parse_html(text)
    title = title_of(root, ctx.stem)
    blocks = _flatten_blocks(body_of(root))
    sections = [b for b in blocks if isinstance(b, Node) and b.tag == "section"]
    groups: list[tuple[str, list]] = []
    if len(sections) >= 2 and len(sections) == len([b for b in blocks if isinstance(b, Node)]):
        for s in sections:
            h = s.find("h1") or s.find("h2") or s.find("h3")
            groups.append((h.text().strip() if h is not None else "", [s]))
    else:
        level = next((lv for lv in ("h1", "h2") if sum(1 for b in blocks if isinstance(b, Node)
                                                       and b.tag == lv) >= 2), None)
        cur_title, cur = title, []
        for b in blocks:
            if level and isinstance(b, Node) and b.tag == level and cur:
                groups.append((cur_title, cur))
                cur_title, cur = b.text().strip() or title, []
            elif level and isinstance(b, Node) and b.tag == level:
                cur_title = b.text().strip() or title
            cur.append(b)
        if cur:
            groups.append((cur_title, cur))
    images = EpubImages()
    chapters = []
    for i, (ctitle, nodes) in enumerate(groups):
        holder = Node("body")
        holder.children = nodes
        frag = fragment_from_html(serialize(holder, xhtml=False), images, Path(src).parent)
        chapters.append((ctitle or f"Chapitre {i + 1}", frag))
        ctx.progress((i + 1) / len(groups))
    build_epub(dst, title, "", chapters or [(title, "<p></p>")], images)
    return [dst]


def epub_to_html(ctx, src, sfmt, dst, d):
    from .epub import read_epub_html
    ctx.progress(None, "Lecture de l'EPUB…")
    _, _, page = read_epub_html(src)
    Path(dst).write_text(page, encoding="utf-8")
    return [dst]
