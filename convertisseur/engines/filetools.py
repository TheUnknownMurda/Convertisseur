"""Outils pour tous les fichiers : empreintes (SHA-256, MD5…), rapport d'informations, archive protégée par
mot de passe, découpage en volumes, renommage en lot."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from .. import i18n
from ..i18n import colon, dec, tr
from ..util import NO_WINDOW, FinalError, UserError, safe_name, unique_path

ALGOS = (("MD5", "md5"), ("SHA-1", "sha1"), ("SHA-256", "sha256"), ("SHA-512", "sha512"))


def _size(n: int) -> str:
    exact = f"{n:,}".replace(",", " " if i18n.LANG == "fr" else ",")
    return i18n.size(n) + (f" ({exact} {tr('octets')})" if n >= 1024 else "")


def digests(ctx, path: Path, span=(0.0, 1.0)) -> dict[str, str]:
    hashers = {name: hashlib.new(algo) for name, algo in ALGOS}
    total = max(1, path.stat().st_size)
    done = 0
    a, b = span
    with open(path, "rb") as f:
        while True:
            chunk = f.read(4 << 20)
            if not chunk:
                break
            for h in hashers.values():
                h.update(chunk)
            done += len(chunk)
            ctx.progress(a + (b - a) * done / total, "Calcul des empreintes…")
    return {name: h.hexdigest() for name, h in hashers.items()}


def hash_file(ctx, src, sfmt, dst, d):
    src = Path(src)
    sums = digests(ctx, src)
    labels = [tr("Fichier"), tr("Taille")]
    w = max(len(x) for x in labels)
    lines = [f"{labels[0]:<{w}}{colon()}{src.name}", f"{labels[1]:<{w}}{colon()}{_size(src.stat().st_size)}", ""]
    lines += [f"{name:<8}: {value}" for name, value in sums.items()]
    Path(dst).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [dst]


def combine_hash(ctx, items, dst_dir: Path) -> list[Path]:
    dst = dst_dir / f"{ctx.stem} {tr('(empreintes)')}.txt"
    lines_256, lines_md5 = [tr("# SHA-256 (vérifiable avec : certutil -hashfile NOM SHA256)")], ["", "# MD5"]
    for i, (path, _, name) in enumerate(items):
        sums = digests(ctx, Path(path), (i / len(items), (i + 1) / len(items)))
        lines_256.append(f"{sums['SHA-256']} *{name}")
        lines_md5.append(f"{sums['MD5']} *{name}")
    dst.write_text("\n".join(lines_256 + lines_md5) + "\n", encoding="utf-8")
    return [dst]


# ---------------------------------------------------------------- rapport d'informations
def _media_section(ctx, path) -> list[str]:
    ffprobe = ctx.tools.get("ffprobe")
    if not ffprobe:
        return []
    try:
        r = subprocess.run([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                           capture_output=True, timeout=60, creationflags=NO_WINDOW)
        data = json.loads(r.stdout.decode("utf-8", "replace") or "{}")
    except Exception:
        return []
    fmt = data.get("format") or {}
    out = ["", "— Média —"]
    if fmt.get("format_long_name"):
        out.append(f"Conteneur : {fmt['format_long_name']}")
    try:
        sec = float(fmt.get("duration"))
        out.append(dec(f"Durée : {int(sec // 3600)}:{int(sec % 3600 // 60):02d}:{sec % 60:05.2f}"))
    except (TypeError, ValueError):
        pass
    if fmt.get("bit_rate"):
        out.append(f"Débit total : {int(fmt['bit_rate']) // 1000} kb/s")
    for s in data.get("streams") or []:
        kind = s.get("codec_type")
        lang = (s.get("tags") or {}).get("language")
        extra = f" ({lang})" if lang and lang != "und" else ""
        if kind == "video":
            if (s.get("disposition") or {}).get("attached_pic"):
                out.append(f"Pochette : {s.get('codec_name')}, {s.get('width')}×{s.get('height')}")
                continue
            fr = s.get("avg_frame_rate") or "0/1"
            try:
                n, dd = fr.split("/")
                fps = dec(f", {float(n) / float(dd):.3g} ") + tr("im/s") if float(dd) else ""
            except (ValueError, ZeroDivisionError):
                fps = ""
            hdr = ", HDR" if s.get("color_transfer") in ("smpte2084", "arib-std-b67") else ""
            br = f", {int(s['bit_rate']) // 1000} kb/s" if s.get("bit_rate") else ""
            out.append(f"Vidéo{extra} : {s.get('codec_long_name') or s.get('codec_name')}, "
                       f"{s.get('width')}×{s.get('height')}{fps}{br}{hdr}")
        elif kind == "audio":
            rate = dec(f", {int(s['sample_rate']) / 1000:g} kHz") if s.get("sample_rate") else ""
            br = f", {int(s['bit_rate']) // 1000} kb/s" if s.get("bit_rate") else ""
            ch = s.get("channels")
            chans = tr({1: "mono", 2: "stéréo"}.get(ch, f"{ch} canaux" if ch else "canaux inconnus"))
            out.append(f"Audio{extra} : {s.get('codec_long_name') or s.get('codec_name')}, {chans}{rate}{br}")
        elif kind == "subtitle":
            out.append(f"Sous-titres{extra} : {s.get('codec_name')}")
    tags = fmt.get("tags") or {}
    for key in ("title", "artist", "album", "date", "genre", "comment", "encoder", "creation_time"):
        if tags.get(key):
            out.append(f"{key.capitalize()} : {tags[key]}")
    return out


EXIF_NAMES = {0x010F: "Fabricant", 0x0110: "Appareil", 0x0131: "Logiciel", 0x0132: "Date", 0x013B: "Auteur",
              0x8298: "Copyright"}


def _image_section(path) -> list[str]:
    try:
        from PIL import Image, ExifTags
        from .images import _heif
        if Path(path).suffix.lower() in (".heic", ".heif", ".hif"):
            _heif()
        with Image.open(path) as im:
            out = ["", "— Image —", f"Format : {im.format}", f"Dimensions : {im.width} × {im.height} pixels",
                   f"Mode de couleur : {im.mode}"]
            dpi = im.info.get("dpi")
            if dpi:
                out.append(f"Résolution : {round(dpi[0])} {tr('ppp')}")
            if getattr(im, "n_frames", 1) > 1:
                out.append(f"Images (animation) : {im.n_frames}")
            if im.info.get("icc_profile"):
                out.append("Profil de couleur : oui")
            exif = im.getexif()
            for tag, label in EXIF_NAMES.items():
                if exif.get(tag):
                    out.append(f"{label} : {str(exif[tag]).strip()}")
            sub = exif.get_ifd(ExifTags.IFD.Exif)
            if sub.get(0x9003):
                out.append(f"Prise de vue : {sub[0x9003]}")
            gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
            if gps:
                def deg(v, ref):
                    d, m, s = (float(x) for x in v)
                    val = d + m / 60 + s / 3600
                    return -val if ref in ("S", "W") else val
                try:
                    lat, lon = deg(gps[2], gps.get(1)), deg(gps[4], gps.get(3))
                    out.append(f"Position GPS : {lat:.5f}, {lon:.5f}  ← retirée par l'outil « Nettoyer les métadonnées »")
                except Exception:
                    out.append("Position GPS : présente")
            return out
    except Exception:
        return []


def _pdf_section(path) -> list[str]:
    try:
        import pymupdf
        doc = pymupdf.open(str(path))
    except Exception:
        return []
    out = ["", "— PDF —"]
    if doc.needs_pass:
        return out + ["Protégé par un mot de passe : contenu illisible sans lui."]
    meta = doc.metadata or {}
    out.append(f"Pages : {doc.page_count}")
    if doc.page_count:
        r = doc[0].rect
        out.append(f"Format de la 1re page : {r.width * 25.4 / 72:.0f} × {r.height * 25.4 / 72:.0f} mm")
    out.append(f"Version : {meta.get('format') or '?'}")
    for key, label in (("title", "Titre"), ("author", "Auteur"), ("subject", "Sujet"), ("keywords", "Mots-clés"),
                       ("creator", "Créé avec"), ("producer", "Produit par"), ("creationDate", "Créé le"),
                       ("modDate", "Modifié le")):
        if meta.get(key):
            out.append(f"{label} : {meta[key]}")
    if doc.is_encrypted:
        out.append("Chiffré : oui (ouverture libre, restrictions possibles)")
    text = sum(len(p.get_text("text").strip()) for p in doc)
    out.append("Texte sélectionnable : " + ("oui" if text > 20 else "non (document scanné ? → « PDF cherchable »)"))
    return out


def _office_section(path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as z:
            core = z.read("docProps/core.xml").decode("utf-8", "replace")
    except Exception:
        return []
    out = ["", "— Document Office —"]
    for tag, label in (("dc:title", "Titre"), ("dc:creator", "Auteur"), ("cp:lastModifiedBy", "Modifié par"),
                       ("dcterms:created", "Créé le"), ("dcterms:modified", "Modifié le"), ("cp:revision", "Révision")):
        m = re.search(rf"<{tag}[^>]*>([^<]*)</{tag}>", core)
        if m and m.group(1).strip():
            out.append(f"{label} : {m.group(1).strip()}")
    return out


def _archive_section(ctx, path) -> list[str]:
    names = []
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                names = [i.filename for i in z.infolist() if not i.is_dir()]
        elif ctx.tools.get("sevenzip"):
            r = subprocess.run([ctx.tools["sevenzip"], "l", "-slt", "-p-", str(path)], capture_output=True,
                               timeout=120, creationflags=NO_WINDOW)
            text = r.stdout.decode("utf-8", "replace")
            names = [m.group(1) for m in re.finditer(r"^Path = (.+)$", text, re.M)][1:]
    except Exception:
        return []
    if not names:
        return []
    out = ["", "— Archive —", f"Fichiers : {len(names)}"]
    out += [f"  {n}" for n in names[:60]]
    if len(names) > 60:
        out.append(f"  … et {len(names) - 60} autres")
    return out


def info_file(ctx, src, sfmt, dst, d):
    from .. import formats as F
    src = Path(src)
    st = src.stat()
    family = F.EXT_FAMILY.get(sfmt) or F.EXT_FAMILY.get(src.suffix.lower().lstrip("."))
    when = lambda t: dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"Rapport d'informations — {src.name}", "=" * 60, f"Taille : {_size(st.st_size)}",
             f"Type : {tr(F.FAMILY_LABEL.get(family, 'Fichier'))} ({src.suffix.lower() or tr('sans extension')})",
             f"Créé le : {when(st.st_ctime)}", f"Modifié le : {when(st.st_mtime)}"]
    ctx.progress(0.1, "Analyse du fichier…")
    if family in ("video", "audio", "anim"):
        lines += _media_section(ctx, src)
    if family in ("image", "anim"):
        lines += _image_section(src)
    if family == "pdf" or src.suffix.lower() == ".pdf":
        lines += _pdf_section(src)
    if src.suffix.lower() in (".docx", ".xlsx", ".pptx", ".docm", ".xlsm", ".pptm", ".dotx", ".potx", ".xltx"):
        lines += _office_section(src)
    if family == "archive":
        lines += _archive_section(ctx, src)
    sums = digests(ctx, src, (0.3, 1.0))
    lines += ["", "— Empreintes —"] + [f"{k:<8}: {v}" for k, v in sums.items()]
    lines = [i18n.report_line(line) for line in lines]
    Path(dst).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [dst]


# ---------------------------------------------------------------- archive protégée, volumes
def _7z(ctx, args, what):
    from .archives import _run7z
    if not ctx.tools.get("sevenzip"):
        raise UserError("7-Zip est nécessaire pour cet outil.")
    _run7z(ctx, args, what)


def protected_archive(ctx, files: list[Path], dst: Path, password: str, kind: str) -> Path:
    if not password:
        raise FinalError("Indiquez un mot de passe dans les réglages.")
    lst = ctx.tmp / "liste.txt"
    lst.write_text("\n".join(str(f) for f in files), encoding="utf-8")
    crypto = ["-t7z", "-mhe=on"] if kind == "7z" else ["-tzip", "-mem=AES256"]
    _7z(ctx, ["a", *crypto, "-mx=5", f"-p{password}", "-scsUTF-8", str(dst), f"@{lst}"], "Chiffrement…")
    return dst


def protect(ctx, src, sfmt, dst, d):
    o = ctx.opts
    kind = o.get("zip_fmt") or "7z"
    dst = Path(dst).with_name(f"{ctx.stem} {tr('(protégé)')}.{kind}")
    return [protected_archive(ctx, [Path(src)], dst, (o.get("password") or "").strip(), kind)]


VOLUME_MB = {"5": 5, "10": 10, "25": 25, "100": 100, "700": 700, "4000": 4000}


def split_volumes(ctx, src, sfmt, dst, d):
    src = Path(src)
    mb = VOLUME_MB.get(ctx.opts.get("vol_size") or "25", 25)
    if src.stat().st_size <= mb * (1 << 20):
        raise FinalError(f"Le fichier fait moins de {mb} Mo : il n'y a rien à découper.")
    folder = unique_path(Path(dst).parent, f"{ctx.stem} {tr('(volumes)')}")
    folder.mkdir(parents=True)
    _7z(ctx, ["a", "-t7z", "-mx=1", f"-v{mb}m", str(folder / f"{safe_name(src.name)}.7z"), str(src)],
        "Découpage en volumes…")
    (folder / f"{tr('LISEZ-MOI')}.txt").write_text(
        tr("Pour reconstituer le fichier : gardez toutes les parties dans le même dossier, puis ouvrez la "
           "première (.7z.001) avec 7-Zip et choisissez « Extraire ».") + "\n", encoding="utf-8")
    return [folder]


# ---------------------------------------------------------------- renommage en lot
def combine_rename(ctx, items, dst_dir: Path) -> list[Path]:
    o = ctx.opts
    pattern = (o.get("rename_pattern") or "").strip() or "{nom}"
    pattern = pattern.replace("{name}", "{nom}").replace("{time}", "{heure}")   # noms anglais acceptés
    if "{" not in pattern and len(items) > 1:
        pattern += " {n}"                          # sinon tous les fichiers auraient le même nom
    start = int(o.get("rename_start") or 1)
    digits = max(len(str(start + len(items) - 1)), int(o.get("rename_digits") or 0) or 0)
    folder = unique_path(dst_dir, tr("Fichiers renommés"))
    folder.mkdir(parents=True)
    for i, (path, _, name) in enumerate(items):
        p = Path(path)
        stamp = dt.datetime.fromtimestamp(p.stat().st_mtime)
        new = (pattern.replace("{n}", str(start + i).zfill(digits)).replace("{nom}", Path(name).stem)
               .replace("{date}", stamp.strftime("%Y-%m-%d")).replace("{heure}", stamp.strftime("%H-%M-%S")))
        target = unique_path(folder, safe_name(new) + Path(name).suffix.lower())
        shutil.copy2(p, target)
        ctx.progress((i + 1) / len(items), f"{i + 1}/{len(items)} : {target.name}")
    return [folder]
