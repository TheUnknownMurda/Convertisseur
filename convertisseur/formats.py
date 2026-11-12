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

FAMILY_LABEL = {"file": "Fichier", "video": "Vidéo", "audio": "Audio", "image": "Image", "anim": "Animation", "pdf": "PDF",
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
_out("Outils PDF", ("pdf_small", "Compresser le PDF", "pdf"), ("pdf_split", "Diviser (un fichier par page)", ""),
     ("pdf_pages", "Extraire ou supprimer des pages", "pdf"), ("pdf_rotate", "Pivoter les pages", "pdf"),
     ("pdf_protect", "Protéger par mot de passe", "pdf"), ("pdf_unlock", "Retirer le mot de passe", "pdf"),
     ("pdf_watermark", "Ajouter un filigrane", "pdf"), ("pdf_number", "Numéroter les pages", "pdf"),
     ("pdf_ocr", "Rendre le texte cherchable (OCR)", "pdf"), ("pdf_images", "Extraire les images", ""),
     ("pdf_clean", "Supprimer les métadonnées", "pdf"))
_out("Outils image", ("img_nobg", "Supprimer l'arrière-plan (PNG)", "png"),
     ("qr_read", "Lire un QR code ou un code-barres", "txt"), ("favicon", "Kit d'icônes pour site web (ZIP)", "zip"))
_out("Outils vidéo", ("contact_sheet", "Planche d'aperçu (JPG)", "jpg"), ("video_frames", "Extraire des images (ZIP)", "zip"),
     ("media_split", "Découper en morceaux", ""))
_out("Outils fichier", ("hash", "Empreintes (SHA-256, MD5…)", "txt"), ("info", "Rapport d'informations (TXT)", "txt"),
     ("protect", "Archive protégée par mot de passe", "7z"), ("split_vol", "Découper en volumes (7-Zip)", ""))
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
PDF_TOOLS = ["pdf_split", "pdf_pages", "pdf_rotate", "pdf_protect", "pdf_unlock", "pdf_watermark", "pdf_number",
             "pdf_ocr", "pdf_images", "pdf_clean"]
FILE_TOOLS = ["hash", "info", "protect", "split_vol"]
OFFERS["pdf"] = OFFERS["pdf"] + PDF_TOOLS
OFFERS["image"] = OFFERS["image"] + ["img_nobg", "qr_read", "favicon"]
OFFERS["video"] = OFFERS["video"] + ["contact_sheet", "video_frames", "media_split"]
OFFERS["audio"] = OFFERS["audio"] + ["media_split"]
for _fam in list(OFFERS):
    if _fam != "web":
        OFFERS[_fam] = OFFERS[_fam] + FILE_TOOLS
OFFERS["file"] = list(FILE_TOOLS)
# Cibles d'outils : proposées même si l'extension de sortie est celle d'origine ; suffixe du fichier produit.
SUFFIX = {"pdf_small": "compressé", "pdf_pages": "pages", "pdf_rotate": "pivoté", "pdf_protect": "protégé",
          "pdf_unlock": "déverrouillé", "pdf_watermark": "filigrane", "pdf_number": "numéroté", "pdf_ocr": "cherchable",
          "pdf_clean": "nettoyé", "img_nobg": "détouré", "qr_read": "contenu", "favicon": "icônes",
          "contact_sheet": "aperçu", "video_frames": "images", "hash": "empreintes", "info": "infos"}
SPECIAL = set(SUFFIX) | {"pdf_split", "pdf_images", "media_split", "protect", "split_vol"}
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
    if target == "media_split" and family == "audio":
        return "Outils audio"
    return group


GROUP_ORDER = ["Vidéo", "Animation", "Audio", "Image", "Document", "Sous-titres", "Données", "Tableur", "Présentation",
               "Ebook", "Police", "Archive", "Outils PDF", "Outils image", "Outils vidéo", "Outils audio", "Outils fichier"]
PRIMARY_GROUP = {"video": "Vidéo", "audio": "Audio", "image": "Image", "anim": "Animation", "pdf": "Document",
                 "doc": "Document", "sheet": "Tableur", "slides": "Présentation", "ebook": "Ebook",
                 "subs": "Sous-titres", "font": "Police", "archive": "Archive", "data": "Données", "web": "Document",
                 "file": "Outils fichier"}

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
    "auto_subs": {"type": "select", "label": "Sous-titres automatiques (Whisper)", "default": "no", "section": "Sous-titres", "choices": [
        ["no", "Non"], ["burn", "Incrustés (toujours visibles)"], ["soft", "Intégrés (désactivables)"]]},
    "subs_burn": {"type": "select", "label": "Sous-titres", "default": "burn", "choices": [
        ["burn", "Incrustés (toujours visibles)"], ["soft", "Intégrés (désactivables)"]]},
    "subs_style": {"type": "select", "label": "Taille des sous-titres incrustés", "default": "medium", "section": "Sous-titres", "choices": [
        ["small", "Petits"], ["medium", "Moyens"], ["large", "Grands"]]},
    "target_mb": {"type": "select", "label": "Taille maximale", "default": "", "choices": [
        ["", "Aucune limite"], ["8", "8 Mo"], ["10", "10 Mo (Discord)"], ["25", "25 Mo"],
        ["50", "50 Mo (Discord Nitro Basic)"], ["100", "100 Mo"], ["500", "500 Mo (Discord Nitro)"]]},
    "target_kb": {"type": "number", "label": "Taille max (Ko)", "placeholder": "aucune", "min": 5, "max": 200000},
    "normalize": {"type": "checkbox", "label": "Normaliser le volume", "default": False, "section": "Son"},
    "fade": {"type": "select", "label": "Fondu début/fin", "default": "0", "section": "Son", "choices": [
        ["0", "Aucun"], ["1", "1 s"], ["2", "2 s"], ["5", "5 s"]]},
    "trim_silence": {"type": "checkbox", "label": "Couper les silences (début et fin)", "default": False, "section": "Son"},
    "speed": {"type": "select", "label": "Vitesse", "default": "1", "section": "Retouches", "choices": [
        ["0.5", "0,5×"], ["0.75", "0,75×"], ["1", "Normale"], ["1.25", "1,25×"], ["1.5", "1,5×"], ["2", "2×"]]},
    "rotate": {"type": "select", "label": "Rotation", "default": "none", "section": "Retouches", "choices": [
        ["none", "Aucune"], ["cw", "90° à droite"], ["ccw", "90° à gauche"], ["180", "180°"],
        ["hflip", "Miroir horizontal"], ["vflip", "Miroir vertical"]]},
    "crop": {"type": "select", "label": "Recadrage", "default": "none", "section": "Retouches", "choices": [
        ["none", "Aucun"], ["auto", "Auto (bandes noires)"], ["1:1", "Carré 1:1"], ["9:16", "Vertical 9:16"],
        ["16:9", "Paysage 16:9"], ["4:5", "Portrait 4:5"], ["4:3", "4:3"],
        ["9:16b", "Vertical 9:16 sur fond flou (Reels, TikTok, Shorts)"], ["1:1b", "Carré sur fond flou"]]},
    "stabilize": {"type": "checkbox", "label": "Stabiliser l'image (plus lent)", "default": False, "section": "Retouches"},
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
    # retouches d'image et de vidéo
    "img_resize": {"type": "select", "label": "Taille", "default": "none", "section": "Retouches", "choices": [
        ["none", "Taille d'origine"], ["75%", "75 %"], ["50%", "50 %"], ["25%", "25 %"], ["x2", "Agrandir ×2"],
        ["x4", "Agrandir ×4"], ["3840", "3840 px (4K)"], ["1920", "1920 px (Full HD)"], ["1280", "1280 px"],
        ["1080", "1080 px"], ["800", "800 px"], ["512", "512 px"], ["256", "256 px"]]},
    "img_ratio": {"type": "select", "label": "Recadrer (proportions)", "default": "none", "section": "Retouches", "choices": [
        ["none", "Aucun"], ["1:1", "Carré 1:1"], ["4:5", "Portrait 4:5 (Instagram)"], ["16:9", "Paysage 16:9"],
        ["9:16", "Vertical 9:16 (stories)"], ["4:3", "4:3"], ["3:2", "3:2 (photo)"], ["2:3", "2:3"]]},
    "img_adjust": {"type": "select", "label": "Filtre", "default": "none", "section": "Retouches", "choices": [
        ["none", "Aucun"], ["bw", "Noir et blanc"], ["sepia", "Sépia"], ["contrast", "Contraste automatique"],
        ["sharpen", "Plus net"], ["blur", "Flou"], ["invert", "Négatif"]]},
    "fps_out": {"type": "select", "label": "Images par seconde", "default": "orig", "section": "Retouches", "choices": [
        ["orig", "Originales"], ["60", "60"], ["30", "30"], ["25", "25"], ["24", "24 (cinéma)"], ["15", "15"], ["10", "10"]]},
    "v_play": {"type": "select", "label": "Lecture", "default": "normal", "section": "Retouches", "choices": [
        ["normal", "Normale"], ["reverse", "À l'envers"], ["boomerang", "Aller-retour (boomerang)"]]},
    # effets sonores
    "denoise": {"type": "checkbox", "label": "Réduire le bruit de fond", "default": False, "section": "Son"},
    "bass": {"type": "select", "label": "Basses", "default": "0", "section": "Son", "choices": [
        ["0", "Normales"], ["6", "Renforcées"], ["12", "Très renforcées"]]},
    "gain": {"type": "select", "label": "Volume", "default": "0", "section": "Son", "choices": [
        ["0", "Inchangé"], ["3", "+3 dB"], ["6", "+6 dB"], ["10", "+10 dB"], ["-3", "−3 dB"], ["-6", "−6 dB"],
        ["-12", "−12 dB"]]},
    "karaoke": {"type": "checkbox", "label": "Retirer la voix (karaoké, approximatif)", "default": False, "section": "Son"},
    "reverse": {"type": "checkbox", "label": "Lire à l'envers", "default": False, "section": "Son"},
    # filigrane
    "wm_text": {"type": "text", "label": "Texte du filigrane", "placeholder": "ex. © Mon nom, CONFIDENTIEL", "section": "Filigrane"},
    "wm_pos": {"type": "select", "label": "Position", "default": "diagonal", "section": "Filigrane", "choices": [
        ["diagonal", "En diagonale"], ["tiled", "Répété partout"], ["center", "Au centre"], ["top", "En haut"],
        ["bottom", "En bas"], ["tl", "En haut à gauche"], ["tr", "En haut à droite"], ["bl", "En bas à gauche"],
        ["br", "En bas à droite"]]},
    "wm_size": {"type": "select", "label": "Taille du texte", "default": "medium", "section": "Filigrane", "choices": [
        ["small", "Petite"], ["medium", "Moyenne"], ["large", "Grande"]]},
    "wm_opacity": {"type": "range", "label": "Opacité (%)", "default": 25, "min": 5, "max": 100, "section": "Filigrane"},
    "wm_color": {"type": "color", "label": "Couleur", "default": "#808080", "section": "Filigrane"},
    # étiquettes audio et confidentialité
    "tag_title": {"type": "text", "label": "Titre", "placeholder": "inchangé", "section": "Étiquettes"},
    "tag_artist": {"type": "text", "label": "Artiste", "placeholder": "inchangé", "section": "Étiquettes"},
    "tag_album": {"type": "text", "label": "Album", "placeholder": "inchangé", "section": "Étiquettes"},
    "tag_year": {"type": "text", "label": "Année", "placeholder": "ex. 2026", "section": "Étiquettes"},
    "strip_meta": {"type": "checkbox", "label": "Supprimer les métadonnées (auteur, appareil, position GPS…)",
                   "default": False, "section": "Confidentialité"},
    # outils PDF
    "split_mode": {"type": "select", "label": "Découpage", "default": "each", "choices": [
        ["each", "Une page par fichier"], ["2", "Par groupes de 2 pages"], ["5", "Par groupes de 5 pages"],
        ["10", "Par groupes de 10 pages"], ["ranges", "Selon les plages ci-contre"]]},
    "split_ranges": {"type": "text", "label": "Plages (une par fichier)", "placeholder": "ex. 1-3, 4-6, 7-"},
    "pages_mode": {"type": "select", "label": "Action", "default": "keep", "choices": [
        ["keep", "Garder ces pages (dans cet ordre)"], ["remove", "Supprimer ces pages"]]},
    "pdf_angle": {"type": "select", "label": "Rotation", "default": "90", "choices": [
        ["90", "90° à droite"], ["270", "90° à gauche"], ["180", "180°"]]},
    "password": {"type": "password", "label": "Mot de passe", "placeholder": "à choisir"},
    "pdf_restrict": {"type": "checkbox", "label": "Interdire aussi l'impression, la copie et la modification", "default": False},
    "num_fmt": {"type": "select", "label": "Format", "default": "n", "choices": [
        ["n", "1, 2, 3…"], ["page", "Page 1"], ["of", "1 / 10"], ["page_of", "Page 1 sur 10"]]},
    "num_pos": {"type": "select", "label": "Position", "default": "bc", "choices": [
        ["bc", "En bas au centre"], ["br", "En bas à droite"], ["bl", "En bas à gauche"], ["tc", "En haut au centre"],
        ["tr", "En haut à droite"], ["tl", "En haut à gauche"]]},
    "num_start": {"type": "number", "label": "Premier numéro", "default": 1, "min": 0, "max": 99999},
    "ocr_lang": {"type": "select", "label": "Langue du texte", "default": "auto", "choices": [
        ["auto", "Langue de Windows"], ["fr", "Français"], ["en", "Anglais"], ["es", "Espagnol"], ["de", "Allemand"],
        ["it", "Italien"], ["pt", "Portugais"]]},
    # outils image
    "nobg_model": {"type": "select", "label": "Qualité du détourage", "default": "precise", "choices": [
        ["precise", "Précis (modèle de 175 Mo, téléchargé une fois)"], ["fast", "Rapide (modèle de 5 Mo)"]]},
    "nobg_crop": {"type": "checkbox", "label": "Recadrer sur le sujet", "default": False},
    "nobg_bg": {"type": "select", "label": "Fond", "default": "none", "choices": [
        ["none", "Transparent"], ["white", "Blanc"], ["black", "Noir"]]},
    # outils vidéo
    "sheet_grid": {"type": "select", "label": "Grille", "default": "4x4", "choices": [
        ["3x3", "3 × 3 (9 images)"], ["4x4", "4 × 4 (16 images)"], ["5x5", "5 × 5 (25 images)"], ["4x6", "4 × 6 (24 images)"]]},
    "frames_rate": {"type": "select", "label": "Images", "default": "1", "choices": [
        ["1", "1 par seconde"], ["2", "2 par seconde"], ["5", "5 par seconde"], ["10", "10 par seconde"],
        ["all", "Toutes"]]},
    "split_len": {"type": "select", "label": "Durée de chaque morceau", "default": "5m", "choices": [
        ["15s", "15 secondes (stories)"], ["30s", "30 secondes"], ["60s", "1 minute"], ["5m", "5 minutes"],
        ["10m", "10 minutes"], ["15m", "15 minutes"], ["30m", "30 minutes"], ["60m", "1 heure"]]},
    # outils fichier
    "vol_size": {"type": "select", "label": "Taille de chaque partie", "default": "25", "choices": [
        ["5", "5 Mo"], ["10", "10 Mo"], ["25", "25 Mo (pièce jointe)"], ["100", "100 Mo"], ["700", "700 Mo (CD)"],
        ["4000", "4 Go (clé FAT32)"]]},
    # assemblages
    "collage_cols": {"type": "select", "label": "Colonnes", "default": "0", "choices": [
        ["0", "Automatique"], ["2", "2"], ["3", "3"], ["4", "4"], ["5", "5"], ["6", "6"]]},
    "collage_gap": {"type": "select", "label": "Espacement", "default": "16", "choices": [
        ["0", "Aucun"], ["8", "Fin"], ["16", "Moyen"], ["32", "Large"]]},
    "collage_fit": {"type": "select", "label": "Ajustement", "default": "cover", "choices": [
        ["cover", "Remplir les cases (recadré)"], ["contain", "Images entières"]]},
    "collage_fmt": {"type": "select", "label": "Format", "default": "jpg", "choices": [["jpg", "JPG"], ["png", "PNG"]]},
    "logo_pos": {"type": "select", "label": "Position du logo", "default": "br", "choices": [
        ["br", "En bas à droite"], ["bl", "En bas à gauche"], ["tr", "En haut à droite"], ["tl", "En haut à gauche"],
        ["center", "Au centre"]]},
    "logo_size": {"type": "select", "label": "Taille du logo", "default": "medium", "choices": [
        ["small", "Petit"], ["medium", "Moyen"], ["large", "Grand"]]},
    "logo_opacity": {"type": "range", "label": "Opacité (%)", "default": 90, "min": 10, "max": 100},
    "soundtrack_mode": {"type": "select", "label": "Bande-son", "default": "replace", "choices": [
        ["replace", "Remplacer le son d'origine"], ["mix", "Mélanger avec le son d'origine"]]},
    "rename_pattern": {"type": "text", "label": "Modèle de nom", "default": "Fichier {n}",
                       "placeholder": "{n} numéro · {nom} nom d'origine · {date} date"},
    "rename_start": {"type": "number", "label": "Premier numéro", "default": 1, "min": 0, "max": 999999},
    "rename_digits": {"type": "select", "label": "Chiffres", "default": "0", "choices": [
        ["0", "Automatique"], ["2", "01"], ["3", "001"], ["4", "0001"]]},
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
    # Outils PDF
    {"id": "pdf-merge", "group": "Outils PDF", "label": "Fusionner des PDF", "icon": "pdf", "accept": ["pdf", "@image"],
     "combine": "combine_pdf", "desc": "Ajoutez plusieurs PDF (et des images), puis « Fusionner en PDF » : dans l'ordre de la liste."},
    {"id": "pdf-split", "group": "Outils PDF", "label": "Diviser un PDF", "icon": "pdf", "accept": ["pdf"],
     "target": "pdf_split", "open": True, "desc": "Un fichier par page, par groupes de pages ou selon vos plages."},
    {"id": "pdf-extract", "group": "Outils PDF", "label": "Extraire des pages", "icon": "pdf", "accept": ["pdf"],
     "target": "pdf_pages", "options": {"pages_mode": "keep"}, "open": True,
     "desc": "Gardez seulement les pages choisies, dans l'ordre de votre choix (ex. 3, 1-2, 8-)."},
    {"id": "pdf-remove", "group": "Outils PDF", "label": "Supprimer des pages", "icon": "pdf", "accept": ["pdf"],
     "target": "pdf_pages", "options": {"pages_mode": "remove"}, "open": True, "desc": "Retirez des pages d'un PDF."},
    {"id": "pdf-rotate", "group": "Outils PDF", "label": "Pivoter un PDF", "icon": "pdf", "accept": ["pdf"],
     "target": "pdf_rotate", "open": True, "desc": "Faites pivoter toutes les pages ou seulement certaines."},
    {"id": "pdf-protect", "group": "Outils PDF", "label": "Protéger un PDF", "icon": "lock", "accept": ["pdf"],
     "target": "pdf_protect", "open": True, "desc": "Mot de passe à l'ouverture (chiffrement AES-256), restrictions possibles."},
    {"id": "pdf-unlock", "group": "Outils PDF", "label": "Déverrouiller un PDF", "icon": "unlock", "accept": ["pdf"],
     "target": "pdf_unlock", "open": True, "desc": "Retirez le mot de passe d'un PDF dont vous connaissez le mot de passe."},
    {"id": "pdf-watermark", "group": "Outils PDF", "label": "Filigrane sur un PDF", "icon": "stamp", "accept": ["pdf"],
     "target": "pdf_watermark", "open": True, "desc": "Texte en diagonale, répété ou dans un coin, avec l'opacité choisie."},
    {"id": "pdf-number", "group": "Outils PDF", "label": "Numéroter les pages", "icon": "pdf", "accept": ["pdf"],
     "target": "pdf_number", "open": True, "desc": "Ajoutez « 1, 2, 3… » ou « Page 1 sur 10 » sur chaque page."},
    {"id": "pdf-ocr", "group": "Outils PDF", "label": "PDF cherchable (OCR)", "icon": "search", "accept": ["pdf"],
     "target": "pdf_ocr", "desc": "Rend le texte des documents scannés sélectionnable et cherchable (reconnaissance de Windows)."},
    {"id": "pdf-images", "group": "Outils PDF", "label": "Extraire les images", "icon": "image", "accept": ["pdf"],
     "target": "pdf_images", "desc": "Récupère les images contenues dans un PDF, dans leur qualité d'origine."},
    {"id": "pdf-small", "group": "Outils PDF", "label": "Compresser un PDF", "icon": "pdf", "accept": ["pdf"],
     "target": "pdf_small", "desc": "Allège un PDF (images recompressées, polices réduites)."},
    # Outils image
    {"id": "img-nobg", "group": "Outils image", "label": "Supprimer l'arrière-plan", "icon": "image", "accept": ["@image"],
     "target": "img_nobg", "desc": "Détourage automatique par intelligence artificielle, sur cet ordinateur : PNG transparent."},
    {"id": "img-resize", "group": "Outils image", "label": "Redimensionner", "icon": "image", "accept": ["@image"],
     "target": "=", "open": "Retouches", "desc": "Changez la taille (50 %, 1920 px, agrandissement ×2…), dans le même format."},
    {"id": "img-crop", "group": "Outils image", "label": "Recadrer", "icon": "image", "accept": ["@image"],
     "target": "=", "options": {"img_ratio": "1:1"}, "open": "Retouches",
     "desc": "Carré, 4:5 Instagram, 16:9, 9:16 stories… recadrage centré."},
    {"id": "img-rotate", "group": "Outils image", "label": "Pivoter ou retourner", "icon": "image", "accept": ["@image"],
     "target": "=", "options": {"rotate": "cw"}, "open": "Retouches", "desc": "Rotation de 90°, 180° ou effet miroir."},
    {"id": "img-filter", "group": "Outils image", "label": "Noir et blanc et filtres", "icon": "image",
     "accept": ["@image"], "target": "=", "options": {"img_adjust": "bw"}, "open": "Retouches",
     "desc": "Noir et blanc, sépia, contraste automatique, netteté, flou, négatif."},
    {"id": "img-watermark", "group": "Outils image", "label": "Filigrane sur des images", "icon": "stamp",
     "accept": ["@image"], "target": "=", "options": {"wm_pos": "br"}, "open": "Filigrane",
     "desc": "Signez vos photos : texte dans un coin, en diagonale ou répété."},
    {"id": "img-upscale", "group": "Outils image", "label": "Agrandir une image", "icon": "image", "accept": ["@image"],
     "target": "=", "options": {"img_resize": "x2"}, "open": "Retouches", "desc": "Agrandissement ×2 ou ×4 avec netteté."},
    {"id": "img-small", "group": "Outils image", "label": "Compresser une image", "icon": "image",
     "accept": ["jpg", "jpeg", "jfif", "webp", "avif", "heic", "png", "bmp", "tiff", "tif"],
     "target": {"png": "webp", "bmp": "jpg", "tiff": "jpg", "tif": "jpg", "heic": "jpg", "*": "="},
     "options": {"quality": 75}, "desc": "Allège les images (qualité 75, ou taille maximale en Ko dans les options)."},
    {"id": "img-exif", "group": "Outils image", "label": "Retirer les données EXIF / GPS", "icon": "shield",
     "accept": ["@image"], "target": "=", "options": {"strip_meta": True},
     "desc": "Supprime l'appareil, la date et la position GPS avant de partager une photo."},
    {"id": "img-collage", "group": "Outils image", "label": "Créer un collage", "icon": "grid", "accept": ["@image"],
     "combine": "combine_collage", "desc": "Assemblez plusieurs images en une grille (colonnes, espacement, fond)."},
    {"id": "img-qr", "group": "Outils image", "label": "Lire un QR code", "icon": "qr", "accept": ["@image"],
     "target": "qr_read", "desc": "Lit les QR codes, codes-barres, Data Matrix et PDF417 d'une image ou d'une capture."},
    {"id": "img-favicon", "group": "Outils image", "label": "Kit d'icônes (favicon)", "icon": "image",
     "accept": ["@image"], "target": "favicon",
     "desc": "Toutes les icônes d'un site web (favicon.ico, Apple, Android) et le code à coller."},
    # Outils vidéo
    {"id": "discord", "group": "Outils vidéo", "label": "Compresser pour Discord", "icon": "video", "accept": ["@video"],
     "target": "mp4", "options": {"target_mb": "10"},
     "desc": "Vidéo en MP4 de 10 Mo maximum (taille réglable dans les options : 25, 50, 500 Mo…)."},
    {"id": "vid-cut", "group": "Outils vidéo", "label": "Couper une vidéo", "icon": "scissors", "accept": ["@video"],
     "target": "=", "open": True, "desc": "Gardez un extrait : indiquez le début et la fin."},
    {"id": "vid-vertical", "group": "Outils vidéo", "label": "Format vertical (Reels, TikTok)", "icon": "video",
     "accept": ["@video"], "target": "mp4", "options": {"crop": "9:16b"},
     "desc": "La vidéo entière en 9:16, sur un fond flou d'elle-même, prête pour Reels, TikTok et Shorts."},
    {"id": "vid-crop", "group": "Outils vidéo", "label": "Recadrer une vidéo", "icon": "video", "accept": ["@video"],
     "target": "=", "options": {"crop": "1:1"}, "open": "Retouches", "desc": "Carré, 9:16, 16:9, bandes noires retirées…"},
    {"id": "vid-rotate", "group": "Outils vidéo", "label": "Pivoter une vidéo", "icon": "video", "accept": ["@video"],
     "target": "=", "options": {"rotate": "cw"}, "open": "Retouches", "desc": "Rotation de 90°, 180° ou effet miroir."},
    {"id": "vid-speed", "group": "Outils vidéo", "label": "Accélérer ou ralentir", "icon": "video", "accept": ["@video"],
     "target": "=", "options": {"speed": "2"}, "open": "Retouches", "desc": "De 0,5× à 2×, son compris."},
    {"id": "vid-reverse", "group": "Outils vidéo", "label": "Inverser ou boomerang", "icon": "retry",
     "accept": ["@video"], "target": "mp4", "options": {"v_play": "boomerang"}, "open": "Retouches",
     "desc": "Lecture à l'envers ou aller-retour (extraits de 3 minutes au plus)."},
    {"id": "vid-stabilize", "group": "Outils vidéo", "label": "Stabiliser une vidéo", "icon": "video",
     "accept": ["@video"], "target": "mp4", "options": {"stabilize": True}, "desc": "Corrige les tremblements d'une vidéo filmée à la main."},
    {"id": "vid-watermark", "group": "Outils vidéo", "label": "Filigrane sur une vidéo", "icon": "stamp",
     "accept": ["@video"], "target": "mp4", "options": {"wm_pos": "br", "wm_opacity": 60}, "open": "Filigrane",
     "desc": "Ajoutez votre nom ou une mention dans un coin de la vidéo."},
    {"id": "vid-logo", "group": "Outils vidéo", "label": "Ajouter un logo", "icon": "image",
     "accept": ["@video", "@image"], "combine": "combine_logo",
     "desc": "Ajoutez une vidéo et une image (PNG transparent idéalement), puis « Ajouter le logo »."},
    {"id": "vid-soundtrack", "group": "Outils vidéo", "label": "Remplacer la bande-son", "icon": "audio",
     "accept": ["@video", "@audio"], "combine": "combine_soundtrack",
     "desc": "Ajoutez une vidéo et une musique : remplacez ou mélangez le son d'origine."},
    {"id": "vid-mute", "group": "Outils vidéo", "label": "Retirer le son", "icon": "video", "accept": ["@video"],
     "target": "=", "options": {"mute": True}, "desc": "Une vidéo muette, dans le même format."},
    {"id": "auto-subs", "group": "Outils vidéo", "label": "Sous-titres automatiques", "icon": "subs", "accept": ["@video"],
     "target": "mp4", "options": {"auto_subs": "burn"},
     "desc": "La parole est transcrite (Whisper) puis incrustée dans la vidéo."},
    {"id": "add-subs", "group": "Outils vidéo", "label": "Ajouter des sous-titres", "icon": "subs",
     "accept": ["@video", "@subs"], "combine": "combine_subs",
     "desc": "Ajoutez une vidéo et un fichier SRT, VTT ou ASS, puis « Ajouter les sous-titres »."},
    {"id": "vid-sheet", "group": "Outils vidéo", "label": "Planche d'aperçu", "icon": "grid", "accept": ["@video"],
     "target": "contact_sheet", "desc": "Une image qui résume la vidéo : 9 à 25 vignettes avec leur minutage."},
    {"id": "vid-frames", "group": "Outils vidéo", "label": "Extraire des images", "icon": "image", "accept": ["@video"],
     "target": "video_frames", "open": True, "desc": "Les images de la vidéo en JPG (1 par seconde, ou toutes), dans un ZIP."},
    {"id": "vid-split", "group": "Outils vidéo", "label": "Découper en segments", "icon": "scissors",
     "accept": ["@video"], "target": "media_split", "open": True,
     "desc": "Des morceaux de 15 s, 1 min, 10 min… sans réencodage (stories, envoi par messagerie)."},
    {"id": "concat", "group": "Outils vidéo", "label": "Fusionner vidéos ou audios", "icon": "video",
     "accept": ["@video", "@audio"], "combine": "combine_concat",
     "desc": "Mettez plusieurs vidéos ou audios bout à bout (dans l'ordre de la liste)."},
    # Outils audio
    {"id": "aud-cut", "group": "Outils audio", "label": "Couper un audio", "icon": "scissors", "accept": ["@audio"],
     "target": "=", "open": True, "desc": "Gardez un extrait : indiquez le début et la fin."},
    {"id": "normalize", "group": "Outils audio", "label": "Normaliser le volume", "icon": "audio",
     "accept": ["@audio", "@video"], "target": "=", "options": {"normalize": True},
     "desc": "Volume homogène (norme EBU R128), dans le même format."},
    {"id": "aud-volume", "group": "Outils audio", "label": "Augmenter le volume", "icon": "audio", "accept": ["@audio"],
     "target": "=", "options": {"gain": "6"}, "open": "Son", "desc": "De −12 à +10 dB, sans saturation."},
    {"id": "aud-denoise", "group": "Outils audio", "label": "Réduire le bruit", "icon": "audio", "accept": ["@audio", "@video"],
     "target": "=", "options": {"denoise": True}, "desc": "Atténue le souffle et le bruit de fond d'un enregistrement."},
    {"id": "aud-bass", "group": "Outils audio", "label": "Renforcer les basses", "icon": "audio", "accept": ["@audio"],
     "target": "=", "options": {"bass": "6"}, "open": "Son", "desc": "Des basses plus présentes, sans saturation."},
    {"id": "aud-speed", "group": "Outils audio", "label": "Accélérer ou ralentir", "icon": "audio", "accept": ["@audio"],
     "target": "=", "options": {"speed": "1.25"}, "open": "Son", "desc": "De 0,5× à 2×, sans changer la hauteur de la voix."},
    {"id": "aud-karaoke", "group": "Outils audio", "label": "Retirer la voix (karaoké)", "icon": "audio",
     "accept": ["@audio"], "target": "=", "options": {"karaoke": True},
     "desc": "Atténue la voix enregistrée au centre (résultat variable selon le mixage)."},
    {"id": "aud-reverse", "group": "Outils audio", "label": "Inverser un audio", "icon": "retry", "accept": ["@audio"],
     "target": "=", "options": {"reverse": True}, "desc": "Lecture à l'envers."},
    {"id": "aud-tags", "group": "Outils audio", "label": "Modifier les tags", "icon": "audio", "accept": ["@audio"],
     "target": {"mp3": "mp3", "m4a": "m4a", "flac": "flac", "ogg": "ogg", "opus": "opus", "*": "mp3"},
     "open": "Étiquettes", "desc": "Titre, artiste, album et année d'un morceau."},
    {"id": "aud-cover", "group": "Outils audio", "label": "Ajouter une pochette", "icon": "image",
     "accept": ["@audio", "@image"], "combine": "combine_cover",
     "desc": "Ajoutez un audio et une image, puis « Ajouter la pochette » (sans réencodage)."},
    {"id": "aud-split", "group": "Outils audio", "label": "Découper en morceaux", "icon": "scissors",
     "accept": ["@audio"], "target": "media_split", "open": True, "desc": "Des morceaux de durée fixe, sans réencodage."},
    {"id": "aud-ringtone", "group": "Outils audio", "label": "Sonnerie iPhone", "icon": "audio",
     "accept": ["@audio", "@video"], "target": "m4r", "open": True,
     "desc": "Un extrait de 40 secondes au plus, au format M4R des iPhone."},
    # Outils fichiers
    {"id": "file-info", "group": "Outils fichiers", "label": "Informations détaillées", "icon": "info",
     "target": "info", "desc": "Tout sur un fichier : codecs, résolution, EXIF et GPS, pages, auteur, contenu d'archive, empreintes."},
    {"id": "file-hash", "group": "Outils fichiers", "label": "Empreintes (SHA-256, MD5)", "icon": "hash",
     "target": "hash", "desc": "Vérifiez qu'un fichier n'a pas été modifié ou qu'un téléchargement est complet."},
    {"id": "file-protect", "group": "Outils fichiers", "label": "Protéger par mot de passe", "icon": "lock",
     "target": "protect", "open": True,
     "desc": "Archive 7Z ou ZIP chiffrée en AES-256. Pour tout regrouper : « Compresser en ZIP » avec un mot de passe."},
    {"id": "file-split", "group": "Outils fichiers", "label": "Découper un gros fichier", "icon": "scissors",
     "target": "split_vol", "open": True, "desc": "En parties de 25 Mo, 100 Mo, 4 Go… à rassembler avec 7-Zip."},
    {"id": "file-clean", "group": "Outils fichiers", "label": "Nettoyer les métadonnées", "icon": "shield",
     "accept": ["@image", "@video", "@audio", "pdf"], "target": {"pdf": "pdf_clean", "*": "="},
     "options": {"strip_meta": True}, "desc": "Retire auteur, appareil, position GPS et commentaires avant de partager."},
    {"id": "file-rename", "group": "Outils fichiers", "label": "Renommer en lot", "icon": "edit",
     "combine": "combine_rename", "desc": "Des copies renommées selon un modèle : « Vacances {date} - {n} »…"},
    {"id": "file-hashes", "group": "Outils fichiers", "label": "Empreintes d'un lot", "icon": "hash",
     "combine": "combine_hash", "desc": "Un seul fichier texte avec l'empreinte SHA-256 et MD5 de chaque fichier."},
    {"id": "zip", "group": "Outils fichiers", "label": "Compresser en ZIP", "icon": "archive", "combine": "combine_zip",
     "desc": "Ajoutez plusieurs fichiers puis « Compresser en ZIP » (mot de passe possible)."},
    {"id": "extract", "group": "Outils fichiers", "label": "Extraire une archive", "icon": "archive", "accept": ["@archive"],
     "target": "folder", "desc": "ZIP, RAR, 7Z, TAR, ISO… extraits dans un dossier."},
    # Créer
    {"id": "make-qr", "group": "Créer", "label": "Créer un QR code", "icon": "qr", "panel": "qr",
     "desc": "Lien, texte, Wi-Fi, contact, e-mail, SMS ou téléphone : en PNG, SVG ou PDF, aux couleurs voulues."},
    {"id": "make-barcode", "group": "Créer", "label": "Créer un code-barres", "icon": "barcode", "panel": "barcode",
     "desc": "EAN-13, UPC-A, Code 128, Code 39, ISBN… en PNG ou SVG."},
    {"id": "make-tts", "group": "Créer", "label": "Lire un texte à voix haute", "icon": "audio", "panel": "tts",
     "desc": "Tapez ou collez un texte : il est lu par une voix de Windows et enregistré en MP3."},
    {"id": "make-screen", "group": "Créer", "label": "Enregistrer l'écran", "icon": "record", "panel": "screen",
     "desc": "Une vidéo MP4 de votre écran, avec le son de votre micro si vous le souhaitez."},
    {"id": "make-mic", "group": "Créer", "label": "Enregistrer le micro", "icon": "mic", "panel": "mic",
     "desc": "Un enregistrement audio MP3 depuis le micro de votre choix."},
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
                    "options": [{"id": "zip_fmt"}, {"id": "password", "label": "Mot de passe (facultatif)",
                                                    "placeholder": "aucun"}], "ext": "zip"},
    "combine_collage": {"label": "Créer un collage", "button": "Créer un collage", "families": ["image"],
                        "options": [{"id": "collage_cols"}, {"id": "collage_gap"}, {"id": "collage_fit"}, {"id": "bg"},
                                    {"id": "collage_fmt"}], "ext": "jpg"},
    "combine_logo": {"label": "Ajouter le logo à la vidéo", "button": "Ajouter le logo", "families": ["video", "image"],
                     "needs": ["video", "image"], "options": [{"id": "logo_pos"}, {"id": "logo_size"},
                                                              {"id": "logo_opacity"}], "ext": "mp4"},
    "combine_soundtrack": {"label": "Remplacer la bande-son", "button": "Remplacer la bande-son",
                           "families": ["video", "audio"], "needs": ["video", "audio"],
                           "options": [{"id": "soundtrack_mode"}], "ext": "mp4"},
    "combine_cover": {"label": "Ajouter la pochette", "button": "Ajouter la pochette", "families": ["audio", "image"],
                      "needs": ["audio", "image"], "options": [], "ext": "mp3"},
    "combine_rename": {"label": "Renommer en lot (copies)", "button": "Renommer en lot", "families": "*", "min": 1,
                       "options": [{"id": "rename_pattern"}, {"id": "rename_start"}, {"id": "rename_digits"}], "ext": ""},
    "combine_hash": {"label": "Empreintes de tous les fichiers", "button": "Empreintes du lot", "families": "*",
                     "options": [], "ext": "txt"},
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
