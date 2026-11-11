"""Bureautique : LibreOffice, Calibre, tableurs (Python), présentations, PDF -> PowerPoint/Excel."""
from __future__ import annotations

import csv
import datetime
import html as htmllib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path

from .. import formats as F
from ..util import NO_WINDOW, FinalError, UserError, parse_pages, read_text_any, safe_name

# ---------------------------------------------------------------- LibreOffice
WRITER = {"pdf": "pdf:writer_pdf_Export", "docx": "docx:MS Word 2007 XML", "doc": "doc:MS Word 97",
          "odt": "odt:writer8", "rtf": "rtf:Rich Text Format", "txt": "txt:Text (encoded):UTF8",
          "html": "html:HTML (StarWriter):EmbedImages"}
CALC = {"pdf": "pdf:calc_pdf_Export", "xlsx": "xlsx:Calc MS Excel 2007 XML", "xls": "xls:MS Excel 97",
        "ods": "ods:calc8", "csv": "csv:Text - txt - csv (StarCalc):44,34,76,1", "html": "html:HTML (StarCalc)"}
IMPRESS = {"pdf": "pdf:impress_pdf_Export", "pptx": "pptx:Impress MS PowerPoint 2007 XML",
           "ppt": "ppt:MS PowerPoint 97", "odp": "odp:impress8"}


def _claim_profile(ctx):
    """Profils LibreOffice persistants (démarrage plus rapide), un par conversion simultanée."""
    base = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "Convertisseur" / "lo-profiles"
    try:
        base.mkdir(parents=True, exist_ok=True)
        import msvcrt
        for i in range(8):
            f = open(base / f"p{i}.lock", "a+b")
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                ctx.keep_alive.append(f)
                return base / f"p{i}"
            except OSError:
                f.close()
    except Exception:
        pass
    return ctx.tmp / "lo-profile"


def _sniff_delimiter(text: str) -> str:
    try:
        return csv.Sniffer().sniff(text[:20000], delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def lo_convert(ctx, src, sfmt, dst, d):
    soffice = ctx.tools.get("soffice")
    if not soffice:
        raise UserError("LibreOffice est nécessaire pour cette conversion.")
    family = "calc" if sfmt in F.SHEET_IN else "impress" if sfmt in F.SLIDES_IN else "writer"
    filt = {"calc": CALC, "impress": IMPRESS, "writer": WRITER}[family].get(d)
    if not filt:
        raise UserError(f"LibreOffice ne sait pas produire ce format ({d}).")
    src = Path(src)
    infilter = None
    work = ctx.tmp / f"lo_{uuid.uuid4().hex[:6]}"
    work.mkdir()
    if sfmt in F.HTML_IN and family == "writer":
        infilter = "HTML (StarWriter)"
    elif sfmt in F.TEXT_IN:
        copy = work / "texte.txt"
        copy.write_text(read_text_any(src), encoding="utf-8")
        src, infilter = copy, "Text (encoded):UTF8"
    elif sfmt in ("csv", "tsv", "tab"):
        text = read_text_any(src)
        sep = "\t" if sfmt in ("tsv", "tab") else _sniff_delimiter(text)
        copy = work / "tableau.csv"
        copy.write_text(text, encoding="utf-8")
        src, infilter = copy, f"CSV:{ord(sep)},34,76,1"
    outdir = work / "out"
    outdir.mkdir()
    profile = _claim_profile(ctx)
    cmd = [soffice, f"-env:UserInstallation={profile.resolve().as_uri()}", "--headless", "--invisible", "--nologo",
           "--nodefault", "--norestore", "--nolockcheck", "--convert-to", filt, "--outdir", str(outdir)]
    if infilter:
        cmd.append(f"--infilter={infilter}")
    cmd.append(str(src))
    ctx.progress(None, "Conversion avec LibreOffice…")
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=900, creationflags=NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise UserError("LibreOffice a mis trop de temps à répondre.")
    want = "." + F.OUT[d][2]
    produced = [p for p in outdir.iterdir() if p.suffix.lower() == want]
    if not produced or produced[0].stat().st_size == 0:
        detail = (r.stderr or r.stdout or b"").decode("utf-8", "replace").strip()[-300:]
        raise UserError("LibreOffice n'a pas pu convertir ce fichier." + (f" ({detail})" if detail else ""))
    out = produced[0]
    if d == "html":
        from .htmlconv import inline_images, parse_html, serialize
        text = read_text_any(out)
        if re.search(r'<img[^>]+src="(?!data:)', text, re.I):
            root = parse_html(text)
            inline_images(root, outdir)
            text = "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"></head>" + serialize(root, xhtml=False) + "</html>"
        Path(dst).write_text(text, encoding="utf-8")
    else:
        shutil.move(str(out), str(dst))
    return [dst]


# ---------------------------------------------------------------- Calibre
def calibre_convert(ctx, src, sfmt, dst, d):
    exe = ctx.tools.get("calibre")
    if not exe:
        raise UserError("Calibre est nécessaire pour cette conversion.")
    src = Path(src)
    if sfmt in F.MD_IN or sfmt in F.TEXT_IN:
        copy = ctx.tmp / ("source.md" if sfmt in F.MD_IN else "source.txt")
        copy.write_text(read_text_any(src), encoding="utf-8")
        src = copy
    args = [exe, str(src), str(dst)]
    if sfmt in F.MD_IN:
        args += ["--formatting-type", "markdown", "--paragraph-type", "off"]
    if d == "pdf":
        args += ["--paper-size", "a4", "--pdf-default-font-size", "16"]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
    tail = []
    ctx.progress(0.01, "Conversion avec Calibre…")
    for raw in proc.stdout:
        line = raw.decode("utf-8", "replace").strip()
        if not line:
            continue
        tail = (tail + [line])[-8:]
        m = re.match(r"^(\d+)%\s+(.*)", line)
        if m:
            ctx.progress(int(m[1]) / 100)
    rc = proc.wait()
    if rc != 0 or not Path(dst).exists() or Path(dst).stat().st_size == 0:
        raise UserError("Calibre n'a pas pu convertir ce fichier : " + " / ".join(tail[-3:])[-400:])
    return [dst]


# ---------------------------------------------------------------- tableurs : lecture
def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return v
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return int(v)
    if isinstance(v, datetime.datetime):
        return v.date().isoformat() if v.time() == datetime.time(0) else v.isoformat(sep=" ")
    if isinstance(v, (datetime.date, datetime.time)):
        return v.isoformat()
    return v


def _trim(rows):
    rows = [list(r) for r in rows]
    for r in rows:
        while r and (r[-1] is None or r[-1] == ""):
            r.pop()
    while rows and not rows[-1]:
        rows.pop()
    return rows


_NUM = re.compile(r"-?(?:0|[1-9]\d{0,14})(?:\.\d+)?")
_NUM_FR = re.compile(r"-?(?:0|[1-9]\d{0,14}),\d+")


def _typed(v, decimal_comma=False):
    if not isinstance(v, str):
        return v
    s = v.strip()
    if _NUM.fullmatch(s):
        return float(s) if "." in s else int(s)
    if decimal_comma and _NUM_FR.fullmatch(s):
        return float(s.replace(",", "."))
    return v


def read_tables(path, fmt) -> list[tuple[str, list[list]]]:
    stem = Path(path).stem
    if fmt in ("csv", "tsv", "tab"):
        text = read_text_any(path)
        sep = "\t" if fmt in ("tsv", "tab") else _sniff_delimiter(text)
        rows = [[_typed(c, sep == ";") for c in r] for r in csv.reader(io.StringIO(text), delimiter=sep)]
        return [(stem, _trim(rows))]
    if fmt in ("xlsx", "xlsm", "xltx", "xltm"):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets:
            rows = []
            for i, r in enumerate(ws.iter_rows(values_only=True)):
                if i >= 1_048_576:
                    break
                rows.append([_cell(v) for v in r])
            out.append((ws.title, _trim(rows)))
        wb.close()
        return out
    if fmt in ("xls", "xlt"):
        import xlrd
        book = xlrd.open_workbook(str(path))
        out = []
        for sh in book.sheets():
            rows = []
            for i in range(sh.nrows):
                row = []
                for c in sh.row(i):
                    if c.ctype == xlrd.XL_CELL_DATE:
                        try:
                            row.append(_cell(xlrd.xldate_as_datetime(c.value, book.datemode)))
                        except Exception:
                            row.append(c.value)
                    elif c.ctype == xlrd.XL_CELL_BOOLEAN:
                        row.append(bool(c.value))
                    else:
                        row.append(_cell(c.value))
                rows.append(row)
            out.append((sh.name, _trim(rows)))
        return out
    if fmt in ("ods", "ots"):
        from odf import teletype
        from odf.opendocument import load
        from odf.table import Table, TableRow
        doc = load(str(path))
        out = []
        for table in doc.spreadsheet.getElementsByType(Table):
            rows = []
            for row in table.getElementsByType(TableRow):
                cells = []
                for cell in row.childNodes:
                    if getattr(cell, "qname", (None, None))[1] not in ("table-cell", "covered-table-cell"):
                        continue
                    rep = int(cell.getAttribute("numbercolumnsrepeated") or 1)
                    vtype = cell.getAttribute("valuetype")
                    if vtype in ("float", "percentage", "currency"):
                        try:
                            val = _cell(float(cell.getAttribute("value")))
                        except (TypeError, ValueError):
                            val = teletype.extractText(cell)
                    elif vtype == "date":
                        val = cell.getAttribute("datevalue")
                    elif vtype == "boolean":
                        val = cell.getAttribute("booleanvalue") == "true"
                    else:
                        val = teletype.extractText(cell)
                    cells.extend([val] * (rep if val not in ("", None) else min(rep, 50)))
                rrep = int(row.getAttribute("numberrowsrepeated") or 1)
                empty = all(c in ("", None) for c in cells)
                rows.extend([list(cells) for _ in range(rrep if not empty else min(rrep, 5))])
            out.append((table.getAttribute("name") or f"Feuille{len(out) + 1}", _trim(rows)))
        return out
    raise UserError(f"Lecture de tableur non gérée : {fmt}")


# ---------------------------------------------------------------- tableurs : écriture
def _sheet_title(name, used):
    t = re.sub(r"[\[\]:*?/\\]", "_", str(name or "Feuille"))[:31] or "Feuille"
    base, i = t, 2
    while t.lower() in used:
        t = f"{base[:28]} ({i})"
        i += 1
    used.add(t.lower())
    return t


def write_xlsx(sheets, dst):
    import openpyxl
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    used = set()
    for name, rows in sheets:
        ws = wb.create_sheet(_sheet_title(name, used))
        widths = {}
        for r in rows:
            ws.append([_typed(v) for v in r])
            for j, v in enumerate(r):
                widths[j] = max(widths.get(j, 0), min(60, len(str(v))))
        if rows and all(isinstance(v, str) and v for v in rows[0]):
            for c in ws[1]:
                c.font = Font(bold=True)
        for j, w in widths.items():
            ws.column_dimensions[get_column_letter(j + 1)].width = max(8, w + 2)
    if not wb.worksheets:
        wb.create_sheet("Feuille1")
    wb.save(str(dst))


def write_ods(sheets, dst):
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableCell, TableRow
    from odf.text import P
    doc = OpenDocumentSpreadsheet()
    used = set()
    for name, rows in sheets or [("Feuille1", [])]:
        t = Table(name=_sheet_title(name, used))
        for r in rows:
            tr = TableRow()
            for v in r:
                v = _typed(v)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    tc = TableCell(valuetype="float", value=str(v))
                else:
                    tc = TableCell(valuetype="string")
                tc.addElement(P(text="" if v is None else str(v)))
                tr.addElement(tc)
            t.addElement(tr)
        doc.spreadsheet.addElement(t)
    doc.save(str(dst))


def _looks_header(rows):
    return bool(rows) and len(rows) > 1 and all(isinstance(v, str) and v.strip() for v in rows[0])


def _html_tables(sheets, title):
    from .htmlconv import wrap_html
    parts = []
    for name, rows in sheets:
        if len(sheets) > 1:
            parts.append(f"<h2>{htmllib.escape(str(name))}</h2>")
        parts.append("<table>")
        for i, r in enumerate(rows):
            tag = "th" if i == 0 and _looks_header(rows) else "td"
            parts.append("<tr>" + "".join(f"<{tag}>{htmllib.escape(str(v))}</{tag}>" for v in r) + "</tr>")
        parts.append("</table>")
    return wrap_html(title, "\n".join(parts))


def _md_tables(sheets):
    out = []
    for name, rows in sheets:
        if len(sheets) > 1:
            out += [f"## {name}", ""]
        if not rows:
            continue
        width = max(len(r) for r in rows)
        norm = [[str(v).replace("|", r"\|").replace("\n", " ") for v in r] + [""] * (width - len(r)) for r in rows]
        out.append("| " + " | ".join(norm[0]) + " |")
        out.append("|" + "---|" * width)
        out += ["| " + " | ".join(r) + " |" for r in norm[1:]]
        out.append("")
    return "\n".join(out).strip() + "\n"


def _txt_tables(sheets):
    out = []
    for name, rows in sheets:
        if len(sheets) > 1:
            out += [f"== {name} ==", ""]
        if not rows:
            continue
        width = max(len(r) for r in rows)
        norm = [[str(v) for v in r] + [""] * (width - len(r)) for r in rows]
        cols = [min(40, max(len(r[j]) for r in norm)) for j in range(width)]
        out += ["  ".join(v[:40].ljust(cols[j]) for j, v in enumerate(r)).rstrip() for r in norm]
        out.append("")
    return "\n".join(out).strip() + "\n"


def _json_tables(sheets):
    def data(rows):
        if _looks_header(rows) and len({str(v) for v in rows[0]}) == len(rows[0]):
            keys = [str(v) for v in rows[0]]
            return [{k: (r[j] if j < len(r) else "") for j, k in enumerate(keys)} for r in rows[1:]]
        return rows
    if len(sheets) == 1:
        return json.dumps(data(sheets[0][1]), ensure_ascii=False, indent=2, default=str)
    return json.dumps({str(n): data(r) for n, r in sheets}, ensure_ascii=False, indent=2, default=str)


def _write_csv(rows, target, sep):
    w = csv.writer(target, delimiter=sep, lineterminator="\r\n")
    for r in rows:
        w.writerow(["" if v is None else v for v in r])


def write_tables(sheets, dst, d, opts, title):
    dst = Path(dst)
    if d == "xlsx":
        write_xlsx(sheets, dst)
    elif d == "ods":
        write_ods(sheets, dst)
    elif d in ("csv", "tsv"):
        sep = "\t" if d == "tsv" else {"tab": "\t"}.get(opts.get("csv_sep"), opts.get("csv_sep") or ",")
        if opts.get("sheets") == "all" and len(sheets) > 1:
            out = dst.with_suffix(".zip")
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                for name, rows in sheets:
                    buf = io.StringIO()
                    _write_csv(rows, buf, sep)
                    z.writestr(f"{safe_name(str(name))}.{d}", "﻿" + buf.getvalue())
            return [out]
        with open(dst, "w", encoding="utf-8-sig", newline="") as f:
            _write_csv(sheets[0][1] if sheets else [], f, sep)
    elif d == "html":
        dst.write_text(_html_tables(sheets, title), encoding="utf-8")
    elif d == "md":
        dst.write_text(_md_tables(sheets), encoding="utf-8")
    elif d == "json":
        dst.write_text(_json_tables(sheets), encoding="utf-8")
    elif d == "txt":
        dst.write_text(_txt_tables(sheets), encoding="utf-8")
    else:
        raise UserError(f"Format de tableur non géré : {d}")
    return [dst]


def table_convert(ctx, src, sfmt, dst, d):
    ctx.progress(None, "Lecture du tableur…")
    sheets = read_tables(src, sfmt)
    if not any(rows for _, rows in sheets):
        raise FinalError("Le tableur est vide.")
    ctx.progress(None, "Écriture…")
    return write_tables(sheets, dst, d, ctx.opts, ctx.stem)


# ---------------------------------------------------------------- présentations
def _shape_texts(shapes, skip=None):
    for sh in shapes:
        if skip is not None and sh is skip:
            continue
        if sh.shape_type == 6 and hasattr(sh, "shapes"):          # groupe
            yield from _shape_texts(sh.shapes)
            continue
        if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                t = "".join(r.text for r in p.runs).strip()
                if t:
                    yield ("p", p.level, t)
        if getattr(sh, "has_table", False) and sh.has_table:
            rows = [[c.text.strip() for c in row.cells] for row in sh.table.rows]
            yield ("table", 0, rows)


def pptx_to_text(ctx, src, sfmt, dst, d):
    from pptx import Presentation
    from .htmlconv import wrap_html
    prs = Presentation(str(src))
    slides = []
    for slide in prs.slides:
        title_shape = slide.shapes.title
        title = title_shape.text.strip() if title_shape is not None and title_shape.has_text_frame else ""
        items = list(_shape_texts(slide.shapes, title_shape))
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        slides.append((title, items, notes))
    lines, html_parts = [], []
    for i, (title, items, notes) in enumerate(slides, 1):
        head = f"Diapositive {i}" + (f" : {title}" if title else "")
        if d == "md":
            lines += [f"## {head}", ""]
        elif d == "txt":
            lines += [head, "=" * len(head)]
        html_parts.append(f"<h2>{htmllib.escape(head)}</h2>")
        for kind, level, val in items:
            if kind == "p":
                lines.append(("  " * level) + ("- " if d == "md" else "• ") + val)
                html_parts.append(f'<p style="margin-left:{level * 1.5}em">• {htmllib.escape(val)}</p>')
            else:
                if d == "md" and val:
                    width = max(len(r) for r in val)
                    lines += ["", "| " + " | ".join(val[0] + [""] * (width - len(val[0]))) + " |", "|" + "---|" * width]
                    lines += ["| " + " | ".join(r + [""] * (width - len(r))) + " |" for r in val[1:]]
                else:
                    lines += ["\t".join(r) for r in val]
                html_parts.append("<table>" + "".join("<tr>" + "".join(f"<td>{htmllib.escape(c)}</td>" for c in r)
                                                      + "</tr>" for r in val) + "</table>")
        if notes:
            lines += ["", ("> " if d == "md" else "Notes : ") + notes.replace("\n", " ")]
            html_parts.append(f"<blockquote>{htmllib.escape(notes)}</blockquote>")
        lines.append("")
    if d == "html":
        Path(dst).write_text(wrap_html(ctx.stem, "\n".join(html_parts)), encoding="utf-8")
    else:
        Path(dst).write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return [dst]


def pdf_to_pptx(ctx, src, sfmt, dst, d):
    import pymupdf
    from pptx import Presentation
    from pptx.util import Emu
    doc = pymupdf.open(str(src))
    if doc.needs_pass:
        raise UserError("Ce PDF est protégé par un mot de passe.")
    pages = parse_pages(ctx.opts.get("pages"), doc.page_count)
    dpi = int(ctx.opts.get("dpi") or 150)
    first = doc[pages[0]].rect
    clamp = lambda pt: int(max(72, min(4000, pt)) * 12700)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(clamp(first.width)), Emu(clamp(first.height))
    blank = prs.slide_layouts[6]
    for i, pno in enumerate(pages):
        ctx.progress(i / len(pages), f"Page {pno + 1}/{doc.page_count}…")
        page = doc[pno]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72), alpha=False)
        slide = prs.slides.add_slide(blank)
        sw, sh = prs.slide_width, prs.slide_height
        s = min(sw / page.rect.width, sh / page.rect.height)
        w, h = int(page.rect.width * s), int(page.rect.height * s)
        slide.shapes.add_picture(io.BytesIO(pix.tobytes("png")), int((sw - w) / 2), int((sh - h) / 2), w, h)
    prs.save(str(dst))
    return [dst]


def pdf_to_tables(ctx, src, sfmt, dst, d):
    import pymupdf
    doc = pymupdf.open(str(src))
    if doc.needs_pass:
        raise UserError("Ce PDF est protégé par un mot de passe.")
    pages = parse_pages(ctx.opts.get("pages"), doc.page_count)
    sheets = []
    for i, pno in enumerate(pages):
        ctx.progress(0.8 * i / len(pages), f"Recherche de tableaux, page {pno + 1}…")
        try:
            found = list(doc[pno].find_tables().tables)
        except Exception:
            found = []
        for k, tab in enumerate(found):
            rows = [["" if c is None else str(c).strip() for c in r] for r in tab.extract()]
            if any(any(c for c in r) for r in rows):
                sheets.append((f"Page {pno + 1}" + (f" ({k + 1})" if len(found) > 1 else ""), rows))
    if not sheets:
        for pno in pages:
            words = doc[pno].get_text("words")
            lines = {}
            for x0, y0, x1, y1, w, b, l, n in words:
                lines.setdefault((b, l), []).append((x0, x1, w))
            rows = []
            for key in sorted(lines):
                ws = sorted(lines[key])
                cells, cur, last_x1 = [], [], None
                for x0, x1, w in ws:
                    if last_x1 is not None and x0 - last_x1 > 12:
                        cells.append(" ".join(cur))
                        cur = []
                    cur.append(w)
                    last_x1 = x1
                if cur:
                    cells.append(" ".join(cur))
                rows.append(cells)
            if rows:
                sheets.append((f"Page {pno + 1}", rows))
    if not sheets:
        raise UserError("Aucun texte ni tableau trouvé dans ce PDF.")
    sheets = [(n, [[_typed(c) for c in r] for r in rows]) for n, rows in sheets]
    if d == "xlsx":
        write_xlsx(sheets, dst)
    else:
        with open(dst, "w", encoding="utf-8-sig", newline="") as f:
            for i, (_, rows) in enumerate(sheets):
                if i:
                    f.write("\r\n")
                _write_csv(rows, f, ",")
    return [dst]


# ---------------------------------------------------------------- image -> Word / PowerPoint
def _image_file(ctx, src, sfmt):
    from PIL import Image
    from .images import JPEG_EXT, to_png
    if sfmt in JPEG_EXT:
        try:
            with Image.open(src) as im:
                if im.getexif().get(0x0112, 1) in (None, 1) and im.mode in ("RGB", "L"):
                    return Path(src), im.size
        except Exception:
            pass
    png = to_png(src, sfmt, ctx.tmp / "image.png", max_side=4000)
    with Image.open(png) as im:
        return png, im.size


def image_to_docx(ctx, src, sfmt, dst, d):
    import docx
    from docx.enum.section import WD_ORIENT
    from docx.shared import Emu
    path, (w, h) = _image_file(ctx, src, sfmt)
    document = docx.Document()
    sec = document.sections[0]
    if w > h:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    avail_w = sec.page_width - sec.left_margin - sec.right_margin
    avail_h = sec.page_height - sec.top_margin - sec.bottom_margin
    nat_w, nat_h = w / 96 * 914400, h / 96 * 914400
    s = min(1.0, avail_w / nat_w, avail_h / nat_h)
    document.add_picture(str(path), width=Emu(int(nat_w * s)))
    document.save(str(dst))
    return [dst]


def image_to_pptx(ctx, src, sfmt, dst, d):
    from pptx import Presentation
    from pptx.util import Emu
    path, (w, h) = _image_file(ctx, src, sfmt)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    sw, sh = prs.slide_width, prs.slide_height
    s = min(sw / w, sh / h)
    pw, ph = int(w * s), int(h * s)
    slide.shapes.add_picture(str(path), int((sw - pw) / 2), int((sh - ph) / 2), pw, ph)
    prs.save(str(dst))
    return [dst]
