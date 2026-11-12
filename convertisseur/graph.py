"""Graphe des conversions.

Chaque arête est un convertisseur direct (FFmpeg, Pillow, MuPDF, LibreOffice, Calibre…).
Une conversion indirecte (ex. DOCX -> JPG) est un chemin : DOCX -> PDF -> JPG.
Ce module ne dépend d'aucune bibliothèque lourde : le serveur s'en sert pour lister les cibles.
"""
from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from . import formats as F

TOOL_LABELS = {
    "ffmpeg": "FFmpeg", "soffice": "LibreOffice", "calibre": "Calibre",
    "tts": "une voix de synthèse Windows", "ocr": "la reconnaissance de texte de Windows (OCR)",
    "vtracer": "le module vtracer", "pdf2docx": "le module pdf2docx", "mammoth": "le module mammoth",
    "markdown": "le module markdown", "pydocx": "le module python-docx", "pptx": "le module python-pptx",
    "openpyxl": "le module openpyxl", "xlrd": "le module xlrd", "odfpy": "le module odfpy",
    "resvg": "le module resvg", "heic": "le module pillow-heif", "heic_save": "l'encodeur HEIC",
    "avif": "l'encodeur AVIF", "whisper": "le module faster-whisper", "pysubs2": "le module pysubs2",
    "fonttools": "le module fontTools", "sevenzip": "7-Zip", "edge": "Microsoft Edge", "yaml": "le module PyYAML",
}


@dataclass(frozen=True)
class Edge:
    name: str
    srcs: frozenset
    dsts: tuple
    fn: str                                  # "module:fonction" dans convertisseur.engines
    cost: float | Callable = 1.0
    req: tuple | Callable = ()
    terminal: bool = False                   # produit plusieurs fichiers : uniquement en dernière étape
    opts: list | Callable | None = None
    first_only: bool = False                 # seulement en première étape (source réelle)

    def cost_of(self, s, d) -> float:
        return float(self.cost(s, d) if callable(self.cost) else self.cost)

    def req_of(self, s, d) -> tuple:
        return tuple(self.req(s, d) if callable(self.req) else self.req)

    def opts_of(self, s, d, last) -> list[dict]:
        if self.opts is None:
            return []
        o = self.opts(s, d, last) if callable(self.opts) else self.opts
        return [x if isinstance(x, dict) else {"id": x} for x in o]


EDGES: list[Edge] = []


def edge(name, srcs, dsts, fn, cost=1.0, req=(), terminal=False, opts=None, first_only=False):
    EDGES.append(Edge(name, frozenset(srcs), tuple(dsts), fn, cost, req, terminal, opts, first_only))


# ---------------------------------------------------------------- options par étape
def _img_req(s, d):
    r = []
    if s in F.SVG_IN:
        r.append("resvg")
    if s in F.HEIC_IN:
        r.append("heic")
    if d == "heic":
        r.append("heic_save")
    if d == "avif":
        r.append("avif")
    return r


def _img_save_opts(s, d, last):
    if not last:
        return []
    o = []
    if s in F.SVG_IN:
        o.append("svg_width")
    if d in F.LOSSY_IMAGE:
        o += ["quality", "target_kb"]
    if d == "webp":
        o.append("lossless")
    if d not in ("ico", "icns", "svg") and s not in F.SVG_IN:
        o += ["max_w", "max_h"]
    if d in F.NO_ALPHA_IMAGE:
        o.append("bg")
    return o


WM = ["wm_text", "wm_pos", "wm_size", "wm_opacity", "wm_color"]
WM_MAIN = [{"id": x, "section": ""} for x in WM]            # outil « filigrane » : réglages au premier plan
IMG_EDITS = ["img_resize", "img_ratio", "rotate", "img_adjust", *WM, "strip_meta"]
TAG_FORMATS = {"mp3", "m4a", "m4b", "m4r", "flac", "ogg", "opus", "alac"}


def _img_edit_opts(s, d, last):
    o = _img_save_opts(s, d, last)
    if last and d not in ("ico", "icns"):
        o += IMG_EDITS
    return o


def _pages_img_opts(s, d, last):
    o = ["dpi", "pages", "zip"]
    if d in F.LOSSY_IMAGE:
        o.append("quality")
    return o


def _audio_opts(s, d, last):
    o = []
    if d in F.LOSSY_AUDIO and d != "mka":
        o.append("a_bitrate")
    if d not in ("amr", "spx"):
        o += ["a_channels", "a_rate"]
    if s != "wav" or d != "wav":
        o += ["start", "end"]
    o += ["normalize", "fade", "trim_silence", {"id": "speed", "section": "Son"}, "denoise", "bass", "gain", "karaoke",
          "reverse"]
    if d in TAG_FORMATS:
        o += ["tag_title", "tag_artist", "tag_album", "tag_year"]
    return o + ["strip_meta"]


def _ebook_pdf_opts(s, d, last):
    return ["page_size", "font_size"] if s in F.REFLOWABLE_IN else []


def _table_req(s, d):
    r = []
    if s in ("xlsx", "xlsm", "xltx", "xltm") or d == "xlsx":
        r.append("openpyxl")
    if s in ("xls", "xlt"):
        r.append("xlrd")
    if s in ("ods", "ots") or d == "ods":
        r.append("odfpy")
    return r


def _table_opts(s, d, last):
    o = []
    if d in ("csv", "tsv"):
        o.append("sheets")
    if d == "csv":
        o.append("csv_sep")
    return o


EBOOK_FORMATS = {"epub", "mobi", "azw3", "fb2", "lit", "pdb", "lrf", "htmlz", "txtz", "snb", "tcr", "rb"}
CALIBRE_IN = {"azw", "azw3", "azw4", "cb7", "cbc", "cbr", "cbz", "chm", "djvu", "djv", "docx", "epub", "fb2", "fbz",
              "html", "htm", "xhtml", "htmlz", "kepub", "lit", "lrf", "mobi", "odt", "pdb", "pdf", "pml", "prc", "rb",
              "rtf", "snb", "tcr", "txt", "text", "md", "markdown", "txtz"}
CALIBRE_OUT = ["epub", "mobi", "azw3", "fb2", "lit", "pdb", "lrf", "htmlz", "txtz", "snb", "tcr", "rb",
               "docx", "rtf", "txt", "pdf"]

V, A, I, AN = F.VIDEO_IN, F.AUDIO_IN, F.IMAGE_IN, F.ANIM_IN

# ---------------------------------------------------------------- médias (FFmpeg)
edge("video_to_video", V, F.VIDEO_OUT, "media:video_to_video", 1, ("ffmpeg",), terminal=True,
     opts=lambda s, d, last: ["v_quality", "v_res", "start", "end", "mute"]
     + (["target_mb"] if d in ("mp4", "mkv", "mov", "m4v", "webm", "avi", "wmv", "flv", "ts") else [])
     + ["crop", "rotate", "speed", "stabilize", "fps_out", "v_play", "normalize", "denoise"]
     + (["auto_subs", "subs_style", {"id": "whisper_model", "section": "Sous-titres"},
         {"id": "whisper_lang", "section": "Sous-titres"}] if d in ("mp4", "mkv", "mov", "m4v", "webm") else [])
     + WM + ["strip_meta"])
edge("video_to_anim", V, F.ANIM_OUT, "media:video_to_anim", 1, ("ffmpeg",), terminal=True,
     opts=["fps", "anim_width", "start", "end"])
edge("to_audio", V | A, F.AUDIO_OUT, "media:to_audio", 1, ("ffmpeg",), terminal=True, opts=_audio_opts)
edge("video_frame", V, ["frame"], "media:video_frame", 1, ("ffmpeg",), opts=["frame_at"])
edge("audio_to_video", A, F.VIDEO_OUT, "media:audio_to_video", 1, ("ffmpeg",), terminal=True, opts=["v_res", "start", "end"])
edge("spectrogram", A, ["frame"], "media:spectrogram", 1, ("ffmpeg",), first_only=True)
edge("anim_to_video", AN, F.VIDEO_OUT, "media:anim_to_video", 1, ("ffmpeg",), terminal=True, opts=["v_res"])
edge("anim_to_anim", AN, F.ANIM_OUT, "media:anim_to_anim", 1, ("ffmpeg",),
     opts=[{"id": "fps", "default": "orig"}, {"id": "anim_width", "default": "orig"}])
edge("image_to_video", I, F.VIDEO_OUT, "media:image_to_video", 1,
     lambda s, d: ["ffmpeg", *[r for r in _img_req(s, "png")]], terminal=True, opts=["still_dur"])
edge("pdf_to_video", ["pdf"], ["mp4"], "media:pdf_to_video", 1.5, ("ffmpeg",), terminal=True, opts=["slide_dur", "pages"])

# ---------------------------------------------------------------- images (Pillow, resvg, vtracer)
edge("image_to_image", I, F.RASTER_OUT, "images:convert_image", 1, _img_req, opts=_img_edit_opts)
# Une capture (image d'une vidéo, spectrogramme) ne mène qu'à une image, un SVG ou un PDF d'une page.
edge("frame_to_image", ["frame"], F.RASTER_OUT, "images:convert_image", 1, terminal=True, opts=_img_save_opts)
edge("frame_to_svg", ["frame"], ["svg"], "images:vectorize", 1.5, ("vtracer",), terminal=True, opts=["svg_preset"])
edge("frame_to_pdf", ["frame"], ["pdf"], "images:image_to_pdf", 1, terminal=True, opts=["img_page"])
edge("anim_to_image", AN, F.STILL_OUT, "images:anim_to_image", 1, lambda s, d: _img_req("png", d),
     opts=lambda s, d, last: (["frames"] if last else []) + _img_save_opts(s, d, last))
edge("vectorize", I - F.SVG_IN, ["svg"], "images:vectorize", 1.5,
     lambda s, d: ["vtracer", *_img_req(s, "png")], opts=["svg_preset"])
edge("image_to_pdf", I | AN, ["pdf"], "images:image_to_pdf", 1, lambda s, d: _img_req(s, "png"), opts=["img_page"])
edge("cbz_to_images", ["cbz"], F.RASTER_OUT, "images:cbz_to_images", 0.5, terminal=True,
     opts=lambda s, d, last: ["zip"] + (["quality"] if d in F.LOSSY_IMAGE else []))
edge("image_to_docx", I, ["docx"], "office:image_to_docx", 1, lambda s, d: ["pydocx", *_img_req(s, "png")],
     first_only=True)
edge("image_to_pptx", I, ["pptx"], "office:image_to_pptx", 1, lambda s, d: ["pptx", *_img_req(s, "png")],
     first_only=True)
edge("ocr", I, ["txt"], "ocr:image_to_text", 1.0, lambda s, d: ["ocr", *_img_req(s, "png")], first_only=True)
edge("transcribe", V | A, ["txt", "srt", "vtt"], "transcription:transcribe", 3, ("whisper",), first_only=True,
     opts=lambda s, d, last: ((["subs_mode"] if d in ("srt", "vtt") and s in V else [])
                              + ["whisper_model", "whisper_lang", "whisper_translate"]))

# ---------------------------------------------------------------- PDF (MuPDF, pdf2docx)
edge("pdf_to_docx", ["pdf"], ["docx"], "pdfdoc:pdf_to_docx", 1.5, ("pdf2docx",), opts=["pages"])
edge("pdf_to_text", ["pdf"], ["txt", "md", "html"], "pdfdoc:pdf_to_text",
     lambda s, d: 2.0 if d == "html" else 1.0, opts=["pages"])
edge("pdf_to_images", ["pdf"], F.RASTER_OUT + ["svg"], "pdfdoc:pdf_to_images", 1, terminal=True,
     opts=_pages_img_opts)
edge("pdf_to_epub", ["pdf"], ["epub"], "pdfdoc:pdf_to_epub", 0.9, opts=["pages"])
edge("pdf_to_cbz", ["pdf"], ["cbz"], "pdfdoc:pdf_to_cbz", 1, opts=["dpi", "pages"])
edge("pdf_to_pptx", ["pdf"], ["pptx"], "office:pdf_to_pptx", 1.2, ("pptx",), opts=["dpi", "pages"])
edge("pdf_to_tables", ["pdf"], ["xlsx", "csv"], "office:pdf_to_tables", 1.5, ("openpyxl",), opts=["pages"])
edge("mupdf_to_pdf", F.XPS_IN | {"epub", "mobi", "fb2", "fbz", "cbz"}, ["pdf"], "pdfdoc:mupdf_to_pdf", 1.5,
     opts=_ebook_pdf_opts)

# ---------------------------------------------------------------- texte, HTML, Markdown, EPUB
HTML = F.HTML_IN
edge("docx_to_text", F.DOCX_IN, ["html", "txt", "md"], "textdoc:docx_to", 1, ("mammoth",))
edge("md_to_html", F.MD_IN, ["html"], "textdoc:md_to_html", 0.5, ("markdown",))
edge("txt_to_html", F.TEXT_IN, ["html"], "textdoc:txt_to_html", 0.5)
edge("txt_to_docx", F.TEXT_IN, ["docx"], "textdoc:txt_to_docx", 1, ("pydocx",))
edge("html_to_txt", HTML, ["txt"], "textdoc:html_to_txt", 0.5)
edge("html_to_md", HTML, ["md"], "textdoc:html_to_md", 0.5)
edge("html_to_docx", HTML, ["docx"], "textdoc:html_to_docx", 1.2, ("pydocx",))
edge("html_to_pdf", HTML, ["pdf"], "textdoc:html_to_pdf", 1.2, opts=["page_size"])
edge("html_to_epub", HTML, ["epub"], "textdoc:html_to_epub", 1.2)
edge("epub_to_html", ["epub"], ["html"], "textdoc:epub_to_html", 1.5)
edge("tts", F.TEXT_IN, ["wav"], "tts:text_to_wav", 2, ("tts",), opts=["voice", "tts_rate"])

# ---------------------------------------------------------------- LibreOffice
WRITER_SRC = F.WORD_IN | F.TEXT_IN | HTML
edge("lo_writer", WRITER_SRC, ["pdf", "docx", "doc", "odt", "rtf", "txt", "html"], "office:lo_convert", 2,
     ("soffice",))
edge("lo_calc", F.SHEET_IN, ["pdf", "xlsx", "xls", "ods", "csv", "html"], "office:lo_convert", 2, ("soffice",))
edge("lo_impress", F.SLIDES_IN, ["pdf", "pptx", "ppt", "odp"], "office:lo_convert", 2, ("soffice",))

# ---------------------------------------------------------------- tableurs et présentations (Python)
edge("table", F.TABLE_IN, ["xlsx", "ods", "csv", "tsv", "html", "md", "json", "txt"], "office:table_convert", 1,
     _table_req, opts=_table_opts)
edge("pptx_to_text", F.PPTX_IN, ["txt", "md", "html"], "office:pptx_to_text", 1, ("pptx",))

# ---------------------------------------------------------------- Calibre
edge("calibre", CALIBRE_IN, CALIBRE_OUT, "office:calibre_convert",
     lambda s, d: 1.0 if d in EBOOK_FORMATS else (5.0 if s == "pdf" else (2.5 if d in ("docx", "rtf", "txt") else 3.0)),
     ("calibre",))

# ---------------------------------------------------------------- sous-titres, polices, archives, données, web
edge("subs_convert", F.SUBS_IN, F.SUBS_OUT, "subs:convert", 1, ("pysubs2",))
edge("font_convert", F.FONT_IN, ["ttf", "otf", "woff", "woff2"], "fonts:convert", 1, ("fonttools",))
edge("font_preview", F.FONT_IN, ["png", "pdf"], "fonts:preview", 1, ("fonttools",), terminal=True, first_only=True,
     opts=["font_text"])
edge("archive_convert", F.ARCHIVE_IN, F.ARCHIVE_OUT, "archives:convert", 1, terminal=True,
     req=lambda s, d: [] if (s in {"zip", "tar", "tgz", "gz", "bz2", "tbz2", "xz", "txz"} and d != "7z")
     else ["sevenzip"])
edge("data_convert", F.DATA_IN, ["json", "yaml", "xml", "toml", "csv", "xlsx", "ods", "html", "md", "txt"],
     "data:convert", 1, lambda s, d: (["yaml"] if "yaml" in (s, d) or s == "yml" else [])
     + (["openpyxl"] if d == "xlsx" else []) + (["odfpy"] if d == "ods" else []), opts=_table_opts)
edge("table_to_data", F.TABLE_IN, ["yaml", "xml", "toml"], "data:from_table", 1,
     lambda s, d: (["yaml"] if d == "yaml" else []) + _table_req(s, d))
edge("web_capture", F.WEB_IN, ["pdf", "png", "jpg", "html"], "web:capture", 1, ("edge",), first_only=True,
     opts=lambda s, d, last: ["page_size"] if d == "pdf" else (["web_width"] if d in ("png", "jpg") else []))
edge("pdf_compress", ["pdf"], ["pdf_small"], "pdfdoc:compress", 1, terminal=True, opts=["pdf_quality"])

# ---------------------------------------------------------------- outils PDF, image, vidéo, audio
PDF = ["pdf"]
edge("pdf_split", PDF, ["pdf_split"], "pdftools:split", 1, terminal=True, first_only=True,
     opts=["split_mode", "split_ranges"])
edge("pdf_pages", PDF, ["pdf_pages"], "pdftools:pages", 1, terminal=True, first_only=True,
     opts=["pages_mode", {"id": "pages", "placeholder": "ex. 1-3, 7, 10-"}])
edge("pdf_rotate", PDF, ["pdf_rotate"], "pdftools:rotate", 1, terminal=True, first_only=True,
     opts=["pdf_angle", {"id": "pages", "placeholder": "toutes"}])
edge("pdf_protect", PDF, ["pdf_protect"], "pdftools:protect", 1, terminal=True, first_only=True,
     opts=["password", "pdf_restrict"])
edge("pdf_unlock", PDF, ["pdf_unlock"], "pdftools:unlock", 1, terminal=True, first_only=True,
     opts=[{"id": "password", "placeholder": "celui du PDF"}])
edge("pdf_watermark", PDF, ["pdf_watermark"], "pdftools:watermark", 1, terminal=True, first_only=True, opts=WM_MAIN)
edge("pdf_number", PDF, ["pdf_number"], "pdftools:number", 1, terminal=True, first_only=True,
     opts=["num_fmt", "num_pos", "num_start"])
edge("pdf_ocr", PDF, ["pdf_ocr"], "pdftools:ocr", 2, ("ocr",), terminal=True, first_only=True, opts=["ocr_lang"])
edge("pdf_images", PDF, ["pdf_images"], "pdftools:images", 1, terminal=True, first_only=True)
edge("pdf_clean", PDF, ["pdf_clean"], "pdftools:clean", 1, terminal=True, first_only=True)
edge("img_nobg", I, ["img_nobg"], "imagetools:remove_background", 2, lambda s, d: _img_req(s, "png"), terminal=True,
     first_only=True, opts=["nobg_model", "nobg_crop", "nobg_bg"])
edge("qr_read", I, ["qr_read"], "imagetools:read_codes", 1, lambda s, d: _img_req(s, "png"), terminal=True,
     first_only=True)
edge("favicon", I, ["favicon"], "imagetools:favicon_kit", 1, lambda s, d: _img_req(s, "png"), terminal=True,
     first_only=True)
edge("contact_sheet", V, ["contact_sheet"], "mediatools:contact_sheet", 1, ("ffmpeg",), terminal=True,
     first_only=True, opts=["sheet_grid"])
edge("video_frames", V, ["video_frames"], "mediatools:video_frames", 1, ("ffmpeg",), terminal=True,
     first_only=True, opts=["frames_rate", "start", "end"])
edge("media_split", V | A, ["media_split"], "mediatools:media_split", 1, ("ffmpeg",), terminal=True,
     first_only=True, opts=["split_len"])
# Outils valables pour n'importe quel fichier (« * »), appliqués au fichier d'origine.
edge("hash", ["*"], ["hash"], "filetools:hash_file", 0.5, terminal=True, first_only=True)
edge("info", ["*"], ["info"], "filetools:info_file", 0.5, terminal=True, first_only=True)
edge("protect", ["*"], ["protect"], "filetools:protect", 1, ("sevenzip",), terminal=True, first_only=True,
     opts=["password", {"id": "zip_fmt", "default": "7z"}])
edge("split_vol", ["*"], ["split_vol"], "filetools:split_volumes", 1, ("sevenzip",), terminal=True, first_only=True,
     opts=["vol_size"])

# ---------------------------------------------------------------- recherche de chemins
EDGE_BY_NAME = {e.name: e for e in EDGES}
_INDEX: dict[str, list[Edge]] = defaultdict(list)
_ANY: list[Edge] = []
for _e in EDGES:
    if "*" in _e.srcs:
        _ANY.append(_e)
        continue
    for _s in _e.srcs:
        _INDEX[_s].append(_e)

# Pénalité pour les formats intermédiaires peu naturels (évite p. ex. vidéo -> GIF -> JPG).
INTERMEDIATE = {"frame": 0.0, "png": 0.0, "pdf": 0.8, "html": 0.1, "txt": 1.5, "wav": 0.0, "docx": 0.05, "epub": 0.5,
                "xlsx": 0.0, "pptx": 0.05, "md": 1.5}


def _dijkstra(src, dst, tools, banned, all_tools, max_len=5):
    heap = [(0.0, 0, src, ())]
    done = set()
    n = 0
    while heap:
        cost, _, fmt, path = heapq.heappop(heap)
        if fmt == dst and path:
            return cost, list(path)
        if path:
            if fmt in done:
                continue
            done.add(fmt)
            if EDGE_BY_NAME[path[-1][0]].terminal or len(path) >= max_len:
                continue
        seen = {src, *(p[2] for p in path)}
        for e in (_INDEX.get(fmt, []) + _ANY if not path else _INDEX.get(fmt, ())):
            if e.first_only and path:
                continue
            for d in e.dsts:
                if (e.name, fmt, d) in banned or (e.name, fmt) in banned:
                    continue
                if d != dst and (d in seen or e.terminal):
                    continue
                if not all_tools and not all(tools.get(r) for r in e.req_of(fmt, d)):
                    continue
                step = e.cost_of(fmt, d) + (0.0 if d == dst else INTERMEDIATE.get(d, 0.6))
                n += 1
                heapq.heappush(heap, (cost + step, n, d, path + ((e.name, fmt, d),)))
    return None


# Étapes qui changent la nature du contenu : un chemin de secours doit garder exactement les mêmes.
SEMANTIC = {"font_preview", "web_capture", "archive_convert", "pdf_compress", "pdf_split", "pdf_pages", "pdf_rotate",
            "pdf_protect", "pdf_unlock", "pdf_watermark", "pdf_number", "pdf_ocr", "pdf_images", "pdf_clean", "img_nobg",
            "qr_read", "favicon", "contact_sheet", "video_frames", "media_split", "hash", "info", "protect", "split_vol", "transcribe", "tts", "ocr", "spectrogram", "video_frame", "audio_to_video", "image_to_video",
            "pdf_to_video", "frame_to_image", "frame_to_svg", "frame_to_pdf", "image_to_docx", "image_to_pptx",
            "anim_to_image", "pdf_to_images", "cbz_to_images", "pdf_to_cbz", "pdf_to_pptx", "pdf_to_tables",
            "vectorize", "image_to_pdf"}


def _signature(path):
    return frozenset(name for name, _, _ in path if name in SEMANTIC)


def find_paths(src: str, dst: str, tools: dict, k: int = 3, all_tools: bool = False) -> list[list[tuple]]:
    """Jusqu'à k chemins (du moins coûteux au plus coûteux) pour aller de src à dst."""
    best = _dijkstra(src, dst, tools, set(), all_tools)
    if not best:
        return []
    found = [best]
    sig = _signature(best[1])
    for step in best[1]:
        alt = _dijkstra(src, dst, tools, {(step[0], step[1])}, all_tools)
        if alt and _signature(alt[1]) == sig and all(alt[1] != f[1] for f in found):
            found.append(alt)
    found.sort(key=lambda x: x[0])
    return [f[1] for f in found[:k]]


def path_options(path: list[tuple]) -> list[dict]:
    seen, out = set(), []
    for i, (name, s, d) in enumerate(path):
        for spec in EDGE_BY_NAME[name].opts_of(s, d, i == len(path) - 1):
            if spec["id"] not in seen:
                seen.add(spec["id"])
                out.append(spec)
    return out


def missing_tools(path: list[tuple], tools: dict) -> list[str]:
    miss = []
    for name, s, d in path:
        for r in EDGE_BY_NAME[name].req_of(s, d):
            if not tools.get(r) and r not in miss:
                miss.append(r)
    return miss


_CACHE: dict = {}


def targets_for(fmt: str, ext: str, family: str, tools: dict) -> list[dict]:
    """Toutes les cibles proposées pour un fichier, avec disponibilité, raison, options et chemin."""
    key = (fmt, ext, family, tuple(sorted((k, bool(v)) for k, v in tools.items() if not isinstance(v, list))))
    if key in _CACHE:
        return _CACHE[key]
    out = []
    for t in F.OFFERS.get(family, []):
        label, _, out_ext = F.OUT[t]
        if out_ext == ext and family not in F.SAME_FORMAT_OK and t not in F.SPECIAL:
            continue
        if t == "pdf" and family == "pdf" and ext == "pdf":
            continue
        if t == "svg" and ext in F.SVG_IN:
            continue
        if ext in F.COMIC_IN and t in F.TEXT_ONLY_OUT:
            continue
        paths = find_paths(fmt, t, tools)
        entry = {"id": t, "label": label, "group": F.context_group(family, t), "ext": out_ext,
                 "base": "Image" if (family == "image" and t == "gif") else F.OUT[t][1]}
        if paths:
            entry.update(ok=True, reason=None, options=path_options(paths[0]),
                         via=[s[2] for s in paths[0][:-1]])
        else:
            ideal = find_paths(fmt, t, tools, k=1, all_tools=True)
            if not ideal:
                continue
            miss = missing_tools(ideal[0], tools)
            entry.update(ok=False, options=[], via=[],
                         reason="Nécessite " + ", ".join(TOOL_LABELS.get(m, m) for m in miss) + ".")
        out.append(entry)
    order = {g: i for i, g in enumerate(F.GROUP_ORDER)}
    primary = F.PRIMARY_GROUP.get(family)

    def base(e):
        return "Image" if family == "image" and e["id"] == "gif" else F.OUT[e["id"]][1]
    out.sort(key=lambda e: (0 if base(e) == primary else 1, order.get(base(e), 99)))
    _CACHE[key] = out
    return out


def default_target(family: str, ext: str, targets: list[dict]) -> str | None:
    pref = {
        "video": "mp3" if ext in ("mp4", "m4v") else "mp4",
        "audio": "wav" if ext == "mp3" else "mp3",
        "anim": "mp4" if ext == "gif" else "gif",
        "image": {"png": "jpg", "jpg": "png", "jpeg": "png", "heic": "jpg", "heif": "jpg", "svg": "png",
                  "svgz": "png", "webp": "png", "avif": "png", "jfif": "png"}.get(ext, "png"),
        "pdf": "docx" if ext == "pdf" else "pdf",
        "doc": "pdf",
        "sheet": "xlsx" if ext in ("csv", "tsv", "xls", "ods") else "pdf",
        "slides": "pdf",
        "ebook": "pdf" if ext in ("epub", "cbz", "cbr") else "epub",
        "subs": "vtt" if ext == "srt" else "srt",
        "font": "woff2" if ext in ("ttf", "otf") else "ttf",
        "archive": "folder",
        "data": "csv" if ext in ("json", "jsonl", "ndjson") else ("xlsx" if ext in ("sqlite", "sqlite3", "db") else "json"),
        "web": "pdf",
        "file": "info",
    }.get(family)
    ok = [t["id"] for t in targets if t["ok"]]
    if pref in ok:
        return pref
    return ok[0] if ok else None
