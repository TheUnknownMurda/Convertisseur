"""Catalogue : familles de formats d'entrée, formats de sortie, libellés, options et préréglages."""
from __future__ import annotations

import re

# ---------------------------------------------------------------- entrées
VIDEO_IN = {"mp4", "m4v", "mov", "qt", "mkv", "webm", "avi", "wmv", "asf", "flv", "f4v", "mpg", "mpeg", "m2v",
            "vob", "ts", "mts", "m2ts", "3gp", "3g2", "ogv", "mxf", "divx", "rm", "rmvb", "dv", "nut", "y4m", "wtv"}
AUDIO_IN = {"mp3", "wav", "wave", "flac", "ogg", "oga", "opus", "m4a", "m4b", "m4r", "aac", "wma", "aiff", "aif",
            "aifc", "amr", "awb", "ac3", "eac3", "dts", "mka", "caf", "wv", "ape", "mp2", "mpa", "weba", "au", "snd",
            "spx", "tta", "voc", "w64", "dsf", "dff", "alac", "ra"}
SVG_IN = {"svg", "svgz"}
HEIC_IN = {"heic", "heif", "hif"}
IMAGE_IN = {"png", "jpg", "jpeg", "jfif", "pjpeg", "pjp", "jpe", "webp", "bmp", "dib", "tif", "tiff", "ico", "cur",
            "avif", "tga", "icb", "vda", "vst", "psd", "jp2", "j2k", "jpf", "jpx", "j2c", "ppm", "pgm", "pbm", "pnm",
            "pcx", "dds", "icns", "qoi", "xbm", "xpm", "sgi", "rgb", "rgba", "bw", "ras", "blp", "msp", "wmf", "emf",
            "dcx", "pcd", "fits", "fit", "mpo"} | SVG_IN | HEIC_IN
ANIM_IN = {"gif", "apng", "webp_anim"}          # webp_anim : pseudo-format attribué aux WebP animés
PDF_IN = {"pdf"}
XPS_IN = {"xps", "oxps"}
WORD_IN = {"docx", "docm", "dotx", "dotm", "doc", "dot", "odt", "ott", "fodt", "rtf", "wpd", "wps", "pages", "abw",
           "zabw", "sxw", "lwp", "hwp"}
HTML_IN = {"html", "htm", "xhtml"}
TEXT_IN = {"txt", "text"}
MD_IN = {"md", "markdown"}
SHEET_IN = {"xlsx", "xlsm", "xltx", "xltm", "xls", "xlt", "xlsb", "ods", "ots", "fods", "csv", "tsv", "tab",
            "numbers", "dif", "slk"}
SLIDES_IN = {"pptx", "pptm", "potx", "potm", "ppt", "pps", "ppsx", "pot", "odp", "otp", "fodp", "key"}
EBOOK_IN = {"epub", "mobi", "azw", "azw3", "azw4", "prc", "fb2", "fbz", "cbz", "cbr", "cb7", "cbc", "lit", "pdb",
            "pml", "lrf", "tcr", "snb", "chm", "htmlz", "txtz", "rb", "djvu", "djv", "kepub"}
TABLE_IN = {"xlsx", "xlsm", "xltx", "xltm", "xls", "xlt", "ods", "ots", "csv", "tsv", "tab"}
PPTX_IN = {"pptx", "pptm", "potx", "potm", "ppsx"}
DOCX_IN = {"docx", "docm", "dotx", "dotm"}
REFLOWABLE_IN = {"epub", "mobi", "fb2", "fbz"}
COMIC_IN = {"cbz", "cbr", "cb7", "cbc"}
SUBS_IN = {"srt", "vtt", "ass", "ssa", "sbv", "ttml", "dfxp", "sub", "smi", "sami", "lrc"}
FONT_IN = {"ttf", "otf", "woff", "woff2"}
ARCHIVE_IN = {"zip", "7z", "rar", "tar", "gz", "tgz", "bz2", "tbz2", "xz", "txz", "iso", "cab", "lzh", "arj", "zst",
              "wim"}
SQLITE_IN = {"sqlite", "sqlite3", "db"}
DATA_IN = {"json", "jsonl", "ndjson", "xml", "yaml", "yml", "toml"} | SQLITE_IN
WEB_IN = {"webpage"}                            # pseudo-format : page web (lien)
TEXT_ONLY_OUT = {"txt", "md", "txtz", "tcr", "mp3", "wav", "m4a", "ogg"}

FAMILY_SETS = [
    ("video", VIDEO_IN), ("audio", AUDIO_IN), ("anim", ANIM_IN), ("image", IMAGE_IN),
    ("pdf", PDF_IN | XPS_IN), ("doc", WORD_IN | HTML_IN | TEXT_IN | MD_IN), ("sheet", SHEET_IN),
    ("slides", SLIDES_IN), ("ebook", EBOOK_IN), ("subs", SUBS_IN), ("font", FONT_IN), ("archive", ARCHIVE_IN),
    ("data", DATA_IN), ("web", WEB_IN),
]
EXT_FAMILY = {ext: fam for fam, exts in FAMILY_SETS for ext in exts}

FAMILY_LABEL = {"video": "Vidéo", "audio": "Audio", "image": "Image", "anim": "Animation", "pdf": "PDF",
                "doc": "Document", "sheet": "Tableur", "slides": "Présentation", "ebook": "Ebook",
                "subs": "Sous-titres", "font": "Police", "archive": "Archive", "data": "Données", "web": "Page web"}

# ---------------------------------------------------------------- sorties
# id -> (libellé, groupe, extension du fichier produit)
OUT: dict[str, tuple[str, str, str]] = {}


def _out(group, *items):
    for item in items:
        tid, label = item[0], item[1]
        ext = item[2] if len(item) > 2 else tid
        OUT[tid] = (label, group, ext)


_out("Vidéo", ("mp4", "MP4"), ("mkv", "MKV"), ("webm", "WEBM"), ("mov", "MOV"), ("avi", "AVI"), ("wmv", "WMV"),
     ("flv", "FLV"), ("m4v", "M4V"), ("mpg", "MPEG"), ("ts", "TS"), ("3gp", "3GP"), ("ogv", "OGV"))
_out("Animation", ("gif", "GIF"), ("apng", "APNG", "png"), ("webp_anim", "WEBP animé", "webp"))
_out("Audio", ("mp3", "MP3"), ("wav", "WAV"), ("flac", "FLAC"), ("ogg", "OGG"), ("opus", "OPUS"),
     ("m4a", "M4A"), ("aac", "AAC"), ("aiff", "AIFF"), ("wma", "WMA"), ("alac", "ALAC", "m4a"), ("ac3", "AC3"),
     ("mp2", "MP2"), ("amr", "AMR"), ("wv", "WavPack", "wv"), ("mka", "MKA"), ("caf", "CAF"), ("au", "AU"),
     ("m4b", "M4B (livre audio)"), ("m4r", "M4R (sonnerie)"), ("weba", "WEBA"), ("spx", "Speex", "spx"),
     ("tta", "TTA"))
_out("Image", ("png", "PNG"), ("jpg", "JPG"), ("webp", "WEBP"), ("avif", "AVIF"), ("heic", "HEIC"),
     ("bmp", "BMP"), ("tiff", "TIFF"), ("ico", "ICO"), ("tga", "TGA"), ("jp2", "JPEG 2000", "jp2"),
     ("ppm", "PPM"), ("pcx", "PCX"), ("qoi", "QOI"), ("icns", "ICNS"), ("dds", "DDS"), ("eps", "EPS"),
     ("svg", "SVG"))
_out("Document", ("pdf", "PDF"), ("docx", "DOCX"), ("doc", "DOC"), ("odt", "ODT"), ("rtf", "RTF"),
     ("txt", "TXT"), ("html", "HTML"), ("md", "Markdown", "md"))
_out("Tableur", ("xlsx", "XLSX"), ("xls", "XLS"), ("ods", "ODS"), ("csv", "CSV"), ("tsv", "TSV"),
     ("json", "JSON"))
_out("Présentation", ("pptx", "PPTX"), ("ppt", "PPT"), ("odp", "ODP"))
_out("Sous-titres", ("srt", "SRT"), ("vtt", "VTT"), ("ass", "ASS"), ("ssa", "SSA"), ("sbv", "SBV (YouTube)"),
     ("ttml", "TTML"), ("lrc", "LRC (paroles)"), ("sub", "SUB (MicroDVD)"), ("smi", "SAMI"))
_out("Police", ("ttf", "TTF"), ("otf", "OTF"), ("woff", "WOFF"), ("woff2", "WOFF2"))
_out("Archive", ("zip", "ZIP"), ("7z", "7Z"), ("tar", "TAR"), ("tgz", "TAR.GZ", "tar.gz"),
     ("folder", "Dossier (extraire)", ""))
_out("Données", ("json", "JSON"), ("yaml", "YAML"), ("xml", "XML"), ("toml", "TOML"))
_out("Document", ("pdf_small", "PDF compressé", "pdf"))
_out("Image", ("frame", "Capture", "png"))       # interne : capture vidéo / spectrogramme (jamais proposé)
_out("Ebook", ("epub", "EPUB"), ("mobi", "MOBI"), ("azw3", "AZW3"), ("fb2", "FB2"), ("lit", "LIT"), ("pdb", "PDB"),
     ("lrf", "LRF"), ("htmlz", "HTMLZ"), ("txtz", "TXTZ"), ("snb", "SNB"), ("tcr", "TCR"), ("rb", "RB"),
     ("cbz", "CBZ"))

VIDEO_OUT = ["mp4", "mkv", "webm", "mov", "avi", "wmv", "flv", "m4v", "mpg", "ts", "3gp", "ogv"]
ANIM_OUT = ["gif", "apng", "webp_anim"]
AUDIO_OUT = ["mp3", "wav", "flac", "ogg", "opus", "m4a", "aac", "aiff", "wma", "alac", "ac3", "mp2", "amr", "wv",
             "mka", "caf", "au", "m4b", "m4r", "weba", "spx", "tta"]
LOSSY_AUDIO = {"mp3", "ogg", "opus", "m4a", "aac", "wma", "ac3", "mp2", "m4b", "m4r", "weba", "mka"}
RASTER_OUT = ["png", "jpg", "webp", "avif", "heic", "gif", "bmp", "tiff", "ico", "tga", "jp2", "ppm", "pcx", "qoi",
              "icns", "dds", "eps"]
STILL_OUT = [x for x in RASTER_OUT if x != "gif"]
DOC_OUT = ["pdf", "docx", "doc", "odt", "rtf", "txt", "html", "md"]
SHEET_OUT = ["xlsx", "xls", "ods", "csv", "tsv", "html", "pdf", "md", "json", "yaml", "xml", "toml", "txt"]
SUBS_OUT = ["srt", "vtt", "ass", "ssa", "sbv", "ttml", "lrc", "sub", "smi", "txt"]
FONT_OUT = ["ttf", "otf", "woff", "woff2", "png", "pdf"]
ARCHIVE_OUT = ["zip", "7z", "tar", "tgz", "folder"]
DATA_OUT = ["json", "yaml", "xml", "toml", "csv", "xlsx", "ods", "html", "md", "txt", "pdf"]
WEB_OUT = ["pdf", "png", "jpg", "html", "md", "txt", "docx", "epub"]
SLIDES_OUT = ["pptx", "ppt", "odp", "pdf"]
EBOOK_OUT = ["epub", "mobi", "azw3", "fb2", "lit", "pdb", "lrf", "htmlz", "txtz", "snb", "tcr", "rb", "cbz"]
TTS_OUT = ["mp3", "wav", "m4a", "ogg"]
TRANSCRIPT_OUT = ["txt", "srt", "vtt", "docx"]
LOSSY_IMAGE = {"jpg", "webp", "avif", "heic", "jp2"}
NO_ALPHA_IMAGE = {"jpg", "bmp", "ppm", "pcx", "eps"}


def _uniq(*lists):
    seen, out = set(), []
    for lst in lists:
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
    return out


OFFERS = {
    "video": _uniq(VIDEO_OUT, ANIM_OUT, AUDIO_OUT, STILL_OUT, ["svg", "pdf"], TRANSCRIPT_OUT),
    "audio": _uniq(AUDIO_OUT, VIDEO_OUT, ["png", "jpg"], TRANSCRIPT_OUT),
    "anim": _uniq(ANIM_OUT, VIDEO_OUT, STILL_OUT, ["svg", "pdf"]),
    "image": _uniq(RASTER_OUT, ["svg", "pdf"], VIDEO_OUT, ["txt", "docx", "odt", "pptx", "odp"]),
    "pdf": _uniq(["pdf", "pdf_small", "docx", "doc", "odt", "rtf", "txt", "html", "md"], EBOOK_OUT, RASTER_OUT, ["svg"],
                 ["pptx", "ppt", "odp"], ["xlsx", "xls", "ods", "csv"], ["mp4"], TTS_OUT),
    "doc": _uniq(DOC_OUT, EBOOK_OUT, RASTER_OUT, ["svg"], TTS_OUT),
    "sheet": _uniq(SHEET_OUT, RASTER_OUT, ["svg"]),
    "slides": _uniq(SLIDES_OUT, RASTER_OUT, ["svg"], ["mp4"], ["txt", "md", "html"]),
    "ebook": _uniq(EBOOK_OUT, DOC_OUT, RASTER_OUT, ["svg"], TTS_OUT),
    "subs": SUBS_OUT + ["docx", "pdf"],
    "font": FONT_OUT,
    "archive": ARCHIVE_OUT,
    "data": DATA_OUT,
    "web": WEB_OUT,
}
SAME_FORMAT_OK = {"video", "audio", "image", "anim"}   # ré-encoder / redimensionner dans le même format

PAGED = {"pdf", "doc", "sheet", "slides", "ebook"}


def context_group(family: str, target: str) -> str:
    """Nom du groupe affiché dans le sélecteur, selon la source."""
    group = OUT[target][1]
    if family == "image" and target == "gif":
        return "Image"
    if group == "Image":
        if family == "video":
            return "Image (capture)"
        if family == "audio":
            return "Image (spectrogramme)"
        if family == "anim":
            return "Image (1re image)"
        if family in PAGED:
            return "Image (une par page)"
    if group == "Vidéo":
        if family == "audio":
            return "Vidéo (pochette ou onde)"
        if family == "image":
            return "Vidéo (image fixe)"
        if family in ("pdf", "slides"):
            return "Vidéo (diaporama)"
    if group == "Audio" and family in ("pdf", "doc", "ebook"):
        return "Audio (lecture vocale)"
    if family == "image" and target == "txt":
        return "Texte (reconnaissance OCR)"
    if family == "image" and group in ("Document", "Présentation"):
        return group + " (image intégrée)"
    if family == "video" and target == "pdf":
        return "Document (capture)"
    if family in ("video", "audio") and target in ("txt", "docx"):
        return "Texte (transcription de la parole)"
    if family == "anim" and target == "pdf":
        return "Document (une page par image)"
    if family == "font" and target in ("png", "pdf"):
        return "Aperçu de la police"
    if family == "web" and target in ("png", "jpg"):
        return "Capture de la page"
    if family == "subs" and target in ("txt", "docx", "pdf"):
        return "Texte des dialogues"
    return group


GROUP_ORDER = ["Vidéo", "Animation", "Audio", "Image", "Document", "Sous-titres", "Données", "Tableur", "Présentation",
               "Ebook", "Police", "Archive"]
PRIMARY_GROUP = {"video": "Vidéo", "audio": "Audio", "image": "Image", "anim": "Animation", "pdf": "Document",
                 "doc": "Document", "sheet": "Tableur", "slides": "Présentation", "ebook": "Ebook",
                 "subs": "Sous-titres", "font": "Police", "archive": "Archive", "data": "Données", "web": "Document"}

# ---------------------------------------------------------------- options
# type : select | checkbox | range | number | text | time | color
OPTIONS: dict[str, dict] = {
    "v_quality": {"type": "select", "label": "Qualité", "default": "orig", "choices": [
        ["orig", "Originale (rapide si possible)"], ["high", "Haute"], ["medium", "Moyenne"],
        ["low", "Basse (fichier léger)"]]},
    "v_res": {"type": "select", "label": "Résolution", "default": "orig", "choices": [
        ["orig", "Originale"], ["2160", "2160p (4K)"], ["1440", "1440p"], ["1080", "1080p"], ["720", "720p"],
        ["480", "480p"], ["360", "360p"], ["240", "240p"]]},
    "mute": {"type": "checkbox", "label": "Retirer le son", "default": False},
    "start": {"type": "time", "label": "Début", "placeholder": "0:00"},
    "end": {"type": "time", "label": "Fin", "placeholder": "jusqu'à la fin"},
    "a_bitrate": {"type": "select", "label": "Débit", "default": "192", "choices": [
        ["320", "320 kb/s"], ["256", "256 kb/s"], ["192", "192 kb/s"], ["160", "160 kb/s"], ["128", "128 kb/s"],
        ["96", "96 kb/s"], ["64", "64 kb/s"]]},
    "a_channels": {"type": "select", "label": "Canaux", "default": "auto", "choices": [
        ["auto", "Originaux"], ["2", "Stéréo"], ["1", "Mono"]]},
    "a_rate": {"type": "select", "label": "Fréquence", "default": "auto", "choices": [
        ["auto", "Originale"], ["48000", "48 kHz"], ["44100", "44,1 kHz"], ["32000", "32 kHz"],
        ["22050", "22,05 kHz"], ["16000", "16 kHz"]]},
    "fps": {"type": "select", "label": "Images par seconde", "default": "15", "choices": [
        ["orig", "Originales"], ["30", "30"], ["25", "25"], ["20", "20"], ["15", "15"], ["12", "12"], ["10", "10"],
        ["8", "8"], ["5", "5"]]},
    "anim_width": {"type": "select", "label": "Largeur", "default": "480", "choices": [
        ["orig", "Originale"], ["1280", "1280 px"], ["1024", "1024 px"], ["800", "800 px"], ["640", "640 px"],
        ["480", "480 px"], ["360", "360 px"], ["320", "320 px"], ["240", "240 px"]]},
    "loop": {"type": "checkbox", "label": "Lecture en boucle", "default": True},
    "frame_at": {"type": "time", "label": "Moment de la capture", "placeholder": "auto (10 %)"},
    "frames": {"type": "select", "label": "Images", "default": "first", "choices": [
        ["first", "Première image"], ["all", "Toutes les images (ZIP)"]]},
    "quality": {"type": "range", "label": "Qualité", "default": 90, "min": 1, "max": 100},
    "lossless": {"type": "checkbox", "label": "Sans perte", "default": False},
    "max_w": {"type": "number", "label": "Largeur max (px)", "placeholder": "originale", "min": 1, "max": 30000},
    "max_h": {"type": "number", "label": "Hauteur max (px)", "placeholder": "originale", "min": 1, "max": 30000},
    "bg": {"type": "color", "label": "Fond (transparence)", "default": "#ffffff"},
    "svg_width": {"type": "number", "label": "Largeur de rendu (px)", "placeholder": "auto", "min": 1, "max": 20000},
    "svg_preset": {"type": "select", "label": "Style", "default": "logo", "choices": [
        ["logo", "Logo / illustration"], ["poster", "Affiche (aplats de couleur)"], ["photo", "Photo (détaillé)"],
        ["bw", "Noir et blanc"]]},
    "dpi": {"type": "select", "label": "Résolution", "default": "150", "choices": [
        ["72", "72 ppp"], ["96", "96 ppp"], ["150", "150 ppp"], ["200", "200 ppp"], ["300", "300 ppp (impression)"],
        ["600", "600 ppp"]]},
    "pages": {"type": "text", "label": "Pages", "placeholder": "toutes (ex. 1-3, 5)"},
    "zip": {"type": "checkbox", "label": "Regrouper en ZIP (sinon : un dossier)", "default": False},
    "page_size": {"type": "select", "label": "Format de page", "default": "a4", "choices": [
        ["a4", "A4"], ["letter", "Lettre US"], ["a5", "A5"], ["legal", "Légal US"]]},
    "font_size": {"type": "select", "label": "Taille du texte", "default": "11", "choices": [
        ["9", "9 pt"], ["10", "10 pt"], ["11", "11 pt"], ["12", "12 pt"], ["14", "14 pt"], ["16", "16 pt"],
        ["18", "18 pt"]]},
    "img_page": {"type": "select", "label": "Page", "default": "a4", "choices": [
        ["a4", "A4 (orientation auto)"], ["letter", "Lettre US (orientation auto)"], ["fit", "Taille de l'image"]]},
    "still_dur": {"type": "number", "label": "Durée (secondes)", "default": 5, "min": 1, "max": 36000},
    "slide_dur": {"type": "number", "label": "Durée par page (s)", "default": 5, "min": 1, "max": 3600},
    "frame_ms": {"type": "number", "label": "Durée par image (ms)", "default": 500, "min": 20, "max": 60000},
    "voice": {"type": "select", "label": "Voix", "default": "auto", "choices": [["auto", "Automatique (selon la langue)"]]},
    "tts_rate": {"type": "select", "label": "Vitesse", "default": "0", "choices": [
        ["-4", "Lente"], ["-2", "Posée"], ["0", "Normale"], ["2", "Rapide"], ["4", "Très rapide"]]},
    "whisper_model": {"type": "select", "label": "Modèle (téléchargé au 1er usage)", "default": "small", "choices": [
        ["tiny", "Très rapide (75 Mo)"], ["base", "Rapide (145 Mo)"], ["small", "Équilibré (485 Mo)"],
        ["medium", "Précis (1,5 Go)"], ["large-v3-turbo", "Très précis (1,6 Go)"]]},
    "whisper_lang": {"type": "select", "label": "Langue parlée", "default": "auto", "choices": [
        ["auto", "Détection automatique"], ["fr", "Français"], ["en", "Anglais"], ["es", "Espagnol"],
        ["de", "Allemand"], ["it", "Italien"], ["pt", "Portugais"], ["nl", "Néerlandais"], ["ar", "Arabe"],
        ["zh", "Chinois"], ["ja", "Japonais"], ["ko", "Coréen"], ["ru", "Russe"], ["pl", "Polonais"],
        ["tr", "Turc"], ["uk", "Ukrainien"]]},
    "whisper_translate": {"type": "checkbox", "label": "Traduire en anglais", "default": False},
    "subs_mode": {"type": "select", "label": "Source des sous-titres", "default": "auto", "choices": [
        ["auto", "Sous-titres intégrés s'il y en a, sinon transcription"], ["transcribe", "Toujours transcrire la parole"]]},
    "auto_subs": {"type": "select", "label": "Sous-titres automatiques (Whisper)", "default": "no", "choices": [
        ["no", "Non"], ["burn", "Incrustés (toujours visibles)"], ["soft", "Intégrés (désactivables)"]]},
    "subs_burn": {"type": "select", "label": "Sous-titres", "default": "burn", "choices": [
        ["burn", "Incrustés (toujours visibles)"], ["soft", "Intégrés (désactivables)"]]},
    "subs_style": {"type": "select", "label": "Taille des sous-titres incrustés", "default": "medium", "choices": [
        ["small", "Petits"], ["medium", "Moyens"], ["large", "Grands"]]},
    "target_mb": {"type": "select", "label": "Taille maximale", "default": "", "choices": [
        ["", "Aucune limite"], ["8", "8 Mo"], ["10", "10 Mo (Discord)"], ["25", "25 Mo"],
        ["50", "50 Mo (Discord Nitro Basic)"], ["100", "100 Mo"], ["500", "500 Mo (Discord Nitro)"]]},
    "target_kb": {"type": "number", "label": "Taille max (Ko)", "placeholder": "aucune", "min": 5, "max": 200000},
    "normalize": {"type": "checkbox", "label": "Normaliser le volume", "default": False},
    "fade": {"type": "select", "label": "Fondu début/fin", "default": "0", "choices": [
        ["0", "Aucun"], ["1", "1 s"], ["2", "2 s"], ["5", "5 s"]]},
    "trim_silence": {"type": "checkbox", "label": "Couper les silences (début et fin)", "default": False},
    "speed": {"type": "select", "label": "Vitesse", "default": "1", "choices": [
        ["0.5", "0,5×"], ["0.75", "0,75×"], ["1", "Normale"], ["1.25", "1,25×"], ["1.5", "1,5×"], ["2", "2×"]]},
    "rotate": {"type": "select", "label": "Rotation", "default": "none", "choices": [
        ["none", "Aucune"], ["cw", "90° à droite"], ["ccw", "90° à gauche"], ["180", "180°"],
        ["hflip", "Miroir horizontal"], ["vflip", "Miroir vertical"]]},
    "crop": {"type": "select", "label": "Recadrage", "default": "none", "choices": [
        ["none", "Aucun"], ["auto", "Auto (bandes noires)"], ["1:1", "Carré 1:1"], ["9:16", "Vertical 9:16"],
        ["16:9", "Paysage 16:9"], ["4:5", "Portrait 4:5"], ["4:3", "4:3"]]},
    "stabilize": {"type": "checkbox", "label": "Stabiliser l'image (plus lent)", "default": False},
    "concat_fmt": {"type": "select", "label": "Format", "default": "auto", "choices": [
        ["auto", "Auto (MP4 s'il y a de la vidéo, sinon MP3)"], ["mp4", "MP4"], ["mkv", "MKV"], ["mp3", "MP3"],
        ["m4a", "M4A"], ["wav", "WAV"], ["flac", "FLAC"]]},
    "zip_fmt": {"type": "select", "label": "Format de l'archive", "default": "zip", "choices": [
        ["zip", "ZIP"], ["7z", "7Z (plus compact)"]]},
    "pdf_quality": {"type": "select", "label": "Niveau", "default": "ebook", "choices": [
        ["screen", "Écran (très léger, 72 ppp)"], ["ebook", "Équilibré (150 ppp)"], ["print", "Impression (300 ppp)"]]},
    "web_width": {"type": "select", "label": "Largeur de la page", "default": "1366", "choices": [
        ["1920", "1920 px"], ["1366", "1366 px"], ["1024", "1024 px"], ["390", "Mobile (390 px)"]]},
    "font_text": {"type": "text", "label": "Texte d'aperçu", "placeholder": "Portez ce vieux whisky au juge blond qui fume"},
    "csv_sep": {"type": "select", "label": "Séparateur", "default": ",", "choices": [
        [",", "Virgule ( , )"], [";", "Point-virgule ( ; )"], ["tab", "Tabulation"]]},
    "sheets": {"type": "select", "label": "Feuilles", "default": "first", "choices": [
        ["first", "Première feuille"], ["all", "Toutes (un fichier par feuille, ZIP)"]]},
}


_WHISPER_BASE = [list(c) for c in OPTIONS["whisper_model"]["choices"]]


def set_whisper_choices(downloaded: list[str]) -> None:
    OPTIONS["whisper_model"]["choices"] = [[v, l + (" — déjà téléchargé" if v in downloaded else "")]
                                           for v, l in _WHISPER_BASE]


def set_voice_choices(voices: list[dict]) -> None:
    choices = [["auto", "Automatique (selon la langue)"]]
    for v in voices:
        choices.append([v["name"], f'{v["name"]} ({v["culture"]})'])
    OPTIONS["voice"]["choices"] = choices


def clean_options(specs: list[dict], raw: dict | None) -> dict:
    """Valide et complète les options reçues du client selon les définitions."""
    raw = raw or {}
    out = {}
    for spec in specs:
        oid = spec["id"]
        d = {**OPTIONS[oid], **spec}
        v = raw.get(oid, d.get("default"))
        t = d["type"]
        if t == "select":
            allowed = {c[0] for c in d["choices"]}
            v = str(v) if str(v) in allowed else d.get("default")
        elif t == "checkbox":
            v = bool(v)
        elif t in ("range", "number"):
            try:
                v = None if v in (None, "") else int(float(v))
            except (TypeError, ValueError):
                v = d.get("default")
            if v is not None:
                v = max(d.get("min", v), min(d.get("max", v), v))
        elif t == "color":
            v = v if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v) else d.get("default", "#ffffff")
        else:
            v = str(v or "").strip()[:200]
        out[oid] = v
    return out


# ---------------------------------------------------------------- préréglages (barre latérale)
PRESETS = [
    {"id": "all", "label": "Tous les fichiers", "icon": "all", "title": "Convertisseur universel",
     "desc": "Vidéo, audio, image, PDF, document, tableur, présentation, ebook, sous-titres, police, archive ou données : déposez n'importe quel fichier, ou collez un lien."},
    # Vidéo & audio
    {"id": "video", "group": "Vidéo & audio", "label": "Convertisseur vidéo", "icon": "video", "accept": ["@video"],
     "desc": "MP4, MKV, WEBM, MOV, AVI, WMV… changez de format, de résolution, coupez ou compressez."},
    {"id": "audio", "group": "Vidéo & audio", "label": "Convertisseur audio", "icon": "audio", "accept": ["@audio"],
     "desc": "MP3, WAV, FLAC, OGG, M4A, OPUS… dans tous les sens, avec le débit de votre choix."},
    {"id": "mp3", "group": "Vidéo & audio", "label": "Convertisseur MP3", "icon": "audio",
     "accept": ["@audio", "@video"], "target": "mp3", "desc": "N'importe quel audio ou vidéo en MP3."},
    {"id": "mp4-mp3", "group": "Vidéo & audio", "label": "MP4 → MP3", "icon": "audio", "accept": ["mp4", "m4v"],
     "target": "mp3", "desc": "Extraire la bande-son d'une vidéo MP4."},
    {"id": "video-mp3", "group": "Vidéo & audio", "label": "Vidéo → MP3", "icon": "audio", "accept": ["@video"],
     "target": "mp3", "desc": "Extraire l'audio de n'importe quelle vidéo."},
    {"id": "mp4", "group": "Vidéo & audio", "label": "Convertisseur MP4", "icon": "video",
     "accept": ["@video", "@anim"], "target": "mp4", "desc": "Tout en MP4 (H.264 + AAC), lisible partout."},
    {"id": "mov-mp4", "group": "Vidéo & audio", "label": "MOV → MP4", "icon": "video", "accept": ["mov", "qt"],
     "target": "mp4", "desc": "Vidéos d'iPhone ou de QuickTime en MP4 (sans perte quand c'est possible)."},
    {"id": "transcribe", "group": "Vidéo & audio", "label": "Audio → texte", "icon": "audio",
     "accept": ["@audio", "@video"], "target": "txt",
     "desc": "Transcrivez la parole d'un audio ou d'une vidéo en texte, sur cet ordinateur (Whisper)."},
    {"id": "subtitles", "group": "Vidéo & audio", "label": "Vidéo → sous-titres", "icon": "video",
     "accept": ["@video", "@audio"], "target": "srt",
     "desc": "Créez des sous-titres SRT ou VTT par reconnaissance de la parole, ou extrayez ceux intégrés à la vidéo."},
    {"id": "mp3-ogg", "group": "Vidéo & audio", "label": "MP3 → OGG", "icon": "audio", "accept": ["mp3"],
     "target": "ogg", "desc": "MP3 en OGG Vorbis."},
    # En ligne (téléchargement par lien, conversion locale)
    {"id": "link", "group": "En ligne", "label": "Depuis un lien", "icon": "link", "link": True,
     "title": "Télécharger depuis un lien",
     "desc": "Collez un lien YouTube, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo… puis choisissez le format."},
    {"id": "yt-mp3", "group": "En ligne", "label": "YouTube → MP3", "icon": "audio", "link": True, "site": "YouTube",
     "target": "mp3", "desc": "Collez un lien YouTube (vidéo ou playlist) pour récupérer l'audio en MP3."},
    {"id": "yt-mp4", "group": "En ligne", "label": "YouTube → MP4", "icon": "video", "link": True, "site": "YouTube",
     "target": "mp4", "desc": "Collez un lien YouTube pour récupérer la vidéo en MP4 (résolution au choix dans les options)."},
    {"id": "sc-mp3", "group": "En ligne", "label": "SoundCloud → MP3", "icon": "audio", "link": True,
     "site": "SoundCloud", "target": "mp3", "desc": "Collez un lien SoundCloud (titre ou playlist) pour le récupérer en MP3."},
    {"id": "sp-mp3", "group": "En ligne", "label": "Spotify → MP3", "icon": "audio", "link": True,
     "site": "Spotify", "target": "mp3",
     "desc": "Collez un lien Spotify (titre, album ou playlist) : chaque morceau est retrouvé sur YouTube, "
             "converti en MP3 avec son titre, son artiste et sa pochette."},
    {"id": "ig-mp4", "group": "En ligne", "label": "Instagram → MP4", "icon": "video", "link": True,
     "site": "Instagram", "target": "mp4", "desc": "Collez le lien d'un Reel ou d'une vidéo Instagram."},
    {"id": "fb-mp4", "group": "En ligne", "label": "Facebook → MP4", "icon": "video", "link": True,
     "site": "Facebook", "target": "mp4", "desc": "Collez le lien d'une vidéo ou d'un Reel Facebook."},
    {"id": "tt-mp4", "group": "En ligne", "label": "TikTok → MP4", "icon": "video", "link": True, "site": "TikTok",
     "target": "mp4", "desc": "Collez le lien d'une vidéo TikTok."},
    {"id": "x-mp4", "group": "En ligne", "label": "X (Twitter) → MP4", "icon": "video", "link": True,
     "site": "X", "target": "mp4", "desc": "Collez le lien d'un message X (Twitter) contenant une vidéo."},
    {"id": "web-pdf", "group": "En ligne", "label": "Page web → PDF", "icon": "web", "link": True, "web": True,
     "target": "pdf", "desc": "Collez l'adresse d'une page web pour l'enregistrer en PDF, en image ou en Markdown."},
    # Outils
    {"id": "discord", "group": "Outils", "label": "Compresser pour Discord", "icon": "video", "accept": ["@video"],
     "target": "mp4", "options": {"target_mb": "10"},
     "desc": "Vidéo en MP4 de 10 Mo maximum (taille réglable dans les options : 25, 50, 500 Mo…)."},
    {"id": "auto-subs", "group": "Outils", "label": "Sous-titres automatiques", "icon": "subs", "accept": ["@video"],
     "target": "mp4", "options": {"auto_subs": "burn"},
     "desc": "La parole est transcrite (Whisper) puis incrustée dans la vidéo."},
    {"id": "normalize", "group": "Outils", "label": "Normaliser le volume", "icon": "audio",
     "accept": ["@audio", "@video"], "target": "=", "options": {"normalize": True},
     "desc": "Volume homogène (norme EBU R128), dans le même format."},
    {"id": "pdf-small", "group": "Outils", "label": "Compresser un PDF", "icon": "pdf", "accept": ["pdf"],
     "target": "pdf_small", "desc": "Allège un PDF (images recompressées, polices réduites)."},
    {"id": "img-small", "group": "Outils", "label": "Compresser une image", "icon": "image",
     "accept": ["jpg", "jpeg", "jfif", "webp", "avif", "heic", "png", "bmp", "tiff", "tif"],
     "target": {"png": "webp", "bmp": "jpg", "tiff": "jpg", "tif": "jpg", "heic": "jpg", "*": "="},
     "options": {"quality": 75}, "desc": "Allège les images (qualité 75, ou taille maximale en Ko dans les options)."},
    {"id": "extract", "group": "Outils", "label": "Extraire une archive", "icon": "archive", "accept": ["@archive"],
     "target": "folder", "desc": "ZIP, RAR, 7Z, TAR, ISO… extraits dans un dossier."},
    {"id": "zip", "group": "Outils", "label": "Compresser en ZIP", "icon": "archive", "combine": "combine_zip",
     "desc": "Ajoutez plusieurs fichiers puis « Compresser en ZIP »."},
    {"id": "concat", "group": "Outils", "label": "Fusionner vidéos ou audios", "icon": "video",
     "accept": ["@video", "@audio"], "combine": "combine_concat",
     "desc": "Mettez plusieurs vidéos ou audios bout à bout (dans l'ordre de la liste)."},
    {"id": "add-subs", "group": "Outils", "label": "Ajouter des sous-titres", "icon": "subs",
     "accept": ["@video", "@subs"], "combine": "combine_subs",
     "desc": "Ajoutez une vidéo et un fichier SRT, VTT ou ASS, puis « Ajouter les sous-titres »."},
    # Image
    {"id": "image", "group": "Image", "label": "Convertisseur d'images", "icon": "image", "accept": ["@image"],
     "desc": "PNG, JPG, WEBP, HEIC, AVIF, TIFF, ICO, SVG… redimensionnez et compressez au passage."},
    {"id": "webp-png", "group": "Image", "label": "WEBP → PNG", "icon": "image", "accept": ["webp"],
     "target": "png", "desc": "Images WEBP en PNG."},
    {"id": "jfif-png", "group": "Image", "label": "JFIF → PNG", "icon": "image", "accept": ["jfif"],
     "target": "png", "desc": "Images JFIF en PNG."},
    {"id": "png-svg", "group": "Image", "label": "PNG → SVG", "icon": "image", "accept": ["png"],
     "target": "svg", "desc": "Vectorisez une image : idéal pour les logos et les illustrations."},
    {"id": "heic-jpg", "group": "Image", "label": "HEIC → JPG", "icon": "image", "accept": ["heic", "heif"],
     "target": "jpg", "desc": "Photos d'iPhone (HEIC) en JPG."},
    {"id": "heic-png", "group": "Image", "label": "HEIC → PNG", "icon": "image", "accept": ["heic", "heif"],
     "target": "png", "desc": "Photos d'iPhone (HEIC) en PNG."},
    {"id": "webp-jpg", "group": "Image", "label": "WEBP → JPG", "icon": "image", "accept": ["webp"],
     "target": "jpg", "desc": "Images WEBP en JPG."},
    {"id": "svg", "group": "Image", "label": "Convertisseur SVG", "icon": "image", "accept": ["svg", "@image"],
     "target": {"svg": "png", "svgz": "png", "*": "svg"},
     "desc": "SVG vers PNG, JPG, PDF… ou n'importe quelle image vers SVG."},
    # PDF & documents
    {"id": "pdf", "group": "PDF & documents", "label": "Convertisseur PDF", "icon": "pdf",
     "accept": ["pdf", "@doc", "@image", "@ebook", "@sheet", "@slides"], "target": {"pdf": "docx", "*": "pdf"},
     "desc": "Tout vers PDF, et PDF vers Word, images, EPUB, Excel, PowerPoint…"},
    {"id": "document", "group": "PDF & documents", "label": "Convertisseur de documents", "icon": "doc",
     "accept": ["@doc", "pdf"], "desc": "DOCX, DOC, ODT, RTF, TXT, Markdown, HTML, PDF… dans tous les sens."},
    {"id": "sheet", "group": "PDF & documents", "label": "Convertisseur de tableurs", "icon": "sheet",
     "accept": ["@sheet"], "desc": "XLSX, XLS, ODS, CSV, TSV, JSON, PDF…"},
    {"id": "slides", "group": "PDF & documents", "label": "Convertisseur de présentations", "icon": "slides",
     "accept": ["@slides"], "desc": "PPTX, PPT, ODP vers PDF, images, vidéo ou texte."},
    {"id": "ebook", "group": "PDF & documents", "label": "Convertisseur d'ebooks", "icon": "ebook",
     "accept": ["@ebook", "pdf"], "target": {"pdf": "epub", "epub": "pdf", "*": "epub"},
     "desc": "EPUB, MOBI, AZW3, FB2, PDF… pour toutes les liseuses."},
    {"id": "pdf-word", "group": "PDF & documents", "label": "PDF → Word", "icon": "pdf", "accept": ["pdf"],
     "target": "docx", "desc": "PDF en document Word modifiable (DOCX)."},
    {"id": "pdf-jpg", "group": "PDF & documents", "label": "PDF → JPG", "icon": "pdf", "accept": ["pdf"],
     "target": "jpg", "desc": "Une image JPG par page."},
    {"id": "pdf-epub", "group": "PDF & documents", "label": "PDF → EPUB", "icon": "ebook", "accept": ["pdf"],
     "target": "epub", "desc": "PDF en livre numérique EPUB."},
    {"id": "epub-pdf", "group": "PDF & documents", "label": "EPUB → PDF", "icon": "ebook", "accept": ["epub"],
     "target": "pdf", "desc": "Livre numérique EPUB en PDF."},
    {"id": "heic-pdf", "group": "PDF & documents", "label": "HEIC → PDF", "icon": "pdf", "accept": ["heic", "heif"],
     "target": "pdf", "desc": "Photos HEIC en PDF (une par fichier, ou fusionnées)."},
    {"id": "docx-pdf", "group": "PDF & documents", "label": "DOCX → PDF", "icon": "doc", "accept": ["docx"],
     "target": "pdf", "desc": "Documents Word en PDF, mise en page conservée."},
    {"id": "jpg-pdf", "group": "PDF & documents", "label": "JPG → PDF", "icon": "pdf",
     "accept": ["jpg", "jpeg", "jfif"], "target": "pdf", "combine": "combine_pdf",
     "desc": "Images JPG en PDF : un fichier par image, ou toutes fusionnées."},
    # Autres formats
    {"id": "subs", "group": "Autres formats", "label": "Sous-titres", "icon": "subs", "accept": ["@subs"],
     "desc": "SRT, VTT, ASS, SSA, SBV, TTML, LRC, SUB, SAMI dans tous les sens."},
    {"id": "fonts", "group": "Autres formats", "label": "Polices", "icon": "font", "accept": ["@font"],
     "desc": "TTF, OTF, WOFF, WOFF2 entre elles, et aperçu en PNG ou PDF."},
    {"id": "archives", "group": "Autres formats", "label": "Archives", "icon": "archive", "accept": ["@archive"],
     "desc": "ZIP, 7Z, RAR, TAR, GZ, ISO… vers ZIP, 7Z, TAR.GZ ou un dossier."},
    {"id": "data", "group": "Autres formats", "label": "Données", "icon": "data", "accept": ["@data"],
     "desc": "JSON, YAML, XML, TOML, SQLite vers CSV, Excel, HTML… et inversement."},
    # GIF
    {"id": "video-gif", "group": "GIF", "label": "Vidéo → GIF", "icon": "anim", "accept": ["@video"],
     "target": "gif", "desc": "Transformez un extrait vidéo en GIF animé."},
    {"id": "mp4-gif", "group": "GIF", "label": "MP4 → GIF", "icon": "anim", "accept": ["mp4", "m4v"],
     "target": "gif", "desc": "MP4 en GIF animé."},
    {"id": "webm-gif", "group": "GIF", "label": "WEBM → GIF", "icon": "anim", "accept": ["webm"],
     "target": "gif", "desc": "WEBM en GIF animé."},
    {"id": "apng-gif", "group": "GIF", "label": "APNG → GIF", "icon": "anim", "accept": ["apng", "png"],
     "target": "gif", "desc": "PNG animé (APNG) en GIF."},
    {"id": "gif-mp4", "group": "GIF", "label": "GIF → MP4", "icon": "video", "accept": ["gif"],
     "target": "mp4", "desc": "GIF en vidéo MP4 (beaucoup plus léger)."},
    {"id": "gif-apng", "group": "GIF", "label": "GIF → APNG", "icon": "anim", "accept": ["gif"],
     "target": "apng", "desc": "GIF en PNG animé (APNG), en couleurs complètes."},
    {"id": "image-gif", "group": "GIF", "label": "Images → GIF", "icon": "anim", "accept": ["@image"],
     "target": "gif", "combine": "combine_gif", "desc": "Assemblez plusieurs images en un GIF animé."},
    {"id": "mov-gif", "group": "GIF", "label": "MOV → GIF", "icon": "anim", "accept": ["mov", "qt"],
     "target": "gif", "desc": "MOV en GIF animé."},
    {"id": "avi-gif", "group": "GIF", "label": "AVI → GIF", "icon": "anim", "accept": ["avi"],
     "target": "gif", "desc": "AVI en GIF animé."},
]

COMBINE = {
    "combine_pdf": {"label": "Fusionner en un PDF", "button": "Fusionner en PDF", "families": ["image", "anim", "pdf"],
                    "options": [{"id": "img_page"}], "ext": "pdf"},
    "combine_gif": {"label": "Créer un GIF animé", "button": "Créer un GIF animé", "families": ["image"],
                    "options": [{"id": "frame_ms"}, {"id": "anim_width", "default": "orig"}, {"id": "loop"}],
                    "ext": "gif"},
    "combine_video": {"label": "Créer un diaporama vidéo", "button": "Diaporama MP4", "families": ["image"],
                      "options": [{"id": "slide_dur", "default": 3}], "ext": "mp4"},
    "combine_concat": {"label": "Fusionner bout à bout", "button": "Fusionner vidéo/audio",
                       "families": ["video", "audio"], "options": [{"id": "concat_fmt"}], "ext": "mp4"},
    "combine_subs": {"label": "Ajouter les sous-titres à la vidéo", "button": "Ajouter les sous-titres",
                     "families": ["video", "subs"], "needs": ["video", "subs"], "min": 2,
                     "options": [{"id": "subs_burn"}, {"id": "subs_style"}], "ext": "mp4"},
    "combine_zip": {"label": "Compresser en une archive", "button": "Compresser en ZIP", "families": "*",
                    "options": [{"id": "zip_fmt"}], "ext": "zip"},
}


def expand_accept(accept) -> list[str] | None:
    if not accept:
        return None
    out = []
    for a in accept:
        if a.startswith("@"):
            out += sorted(e for e, f in EXT_FAMILY.items() if f == a[1:] and e != "webp_anim")
        else:
            out.append(a)
    return sorted(set(out))


def presets_for_client() -> list[dict]:
    return [{**p, "accept": expand_accept(p.get("accept"))} for p in PRESETS]
