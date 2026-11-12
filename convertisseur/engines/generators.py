"""Générateurs : QR codes (texte, lien, Wi-Fi, contact, e-mail, SMS, téléphone) et codes-barres."""
from __future__ import annotations

import base64
import re
import urllib.parse
from pathlib import Path

from ..i18n import tr
from ..util import UserError, safe_name, unique_path

QR_SCALE = {"small": 6, "medium": 10, "large": 16}
BARCODES = {"code128": "Code 128", "ean13": "EAN-13", "ean8": "EAN-8", "upca": "UPC-A", "code39": "Code 39",
            "isbn13": "ISBN-13", "itf": "ITF", "codabar": "Codabar"}


def _wifi_escape(value: str) -> str:
    return re.sub(r'([\\;,:"])', r"\\\1", value or "")


def qr_payload(p: dict) -> tuple[str, str]:
    """(données encodées, libellé pour le nom de fichier)."""
    kind = p.get("kind") or "text"
    if kind == "wifi":
        ssid = (p.get("ssid") or "").strip()
        if not ssid:
            raise UserError("Indiquez le nom du réseau Wi-Fi.")
        sec = p.get("security") or "WPA"
        pwd = "" if sec == "nopass" else _wifi_escape(p.get("password") or "")
        hidden = "true" if p.get("hidden") else "false"
        return f"WIFI:T:{sec};S:{_wifi_escape(ssid)};P:{pwd};H:{hidden};;", f"Wi-Fi {ssid}"
    if kind == "contact":
        import segno.helpers
        first, last = (p.get("first") or "").strip(), (p.get("last") or "").strip()
        if not (first or last):
            raise UserError("Indiquez au moins un nom.")
        data = segno.helpers.make_vcard_data(
            name=f"{last};{first}", displayname=f"{first} {last}".strip(), email=p.get("email") or None,
            phone=p.get("phone") or None, org=p.get("org") or None, url=p.get("url") or None)
        return data, f"Contact {first} {last}".strip()
    if kind == "email":
        addr = (p.get("email") or "").strip()
        if not addr:
            raise UserError("Indiquez l'adresse e-mail.")
        query = urllib.parse.urlencode({k: v for k, v in (("subject", p.get("subject")), ("body", p.get("body"))) if v},
                                       quote_via=urllib.parse.quote)
        return f"mailto:{addr}" + (f"?{query}" if query else ""), f"E-mail {addr}"
    if kind == "sms":
        num = re.sub(r"[^\d+]", "", p.get("phone") or "")
        if not num:
            raise UserError("Indiquez le numéro de téléphone.")
        return f"SMSTO:{num}:{p.get('message') or ''}", f"SMS {num}"
    if kind == "phone":
        num = re.sub(r"[^\d+]", "", p.get("phone") or "")
        if not num:
            raise UserError("Indiquez le numéro de téléphone.")
        return f"tel:{num}", tr(f"Téléphone {num}")
    text = (p.get("text") or "").strip()
    if not text:
        raise UserError("Saisissez le texte ou le lien à encoder.")
    label = re.sub(r"^https?://(www\.)?", "", text).split("?")[0].strip("/")[:40] or tr("texte")
    return text, label


def make_qr(p: dict, out_dir: Path) -> Path:
    import segno
    data, label = qr_payload(p)
    fmt = p.get("format") if p.get("format") in ("png", "svg", "pdf") else "png"
    dark = p.get("color") if re.fullmatch(r"#[0-9a-fA-F]{6}", p.get("color") or "") else "#000000"
    light = None if p.get("transparent") else (p.get("bg") if re.fullmatch(r"#[0-9a-fA-F]{6}", p.get("bg") or "") else "#ffffff")
    try:
        qr = segno.make(data, error=p.get("ecc") if p.get("ecc") in ("l", "m", "q", "h") else "m", micro=False)
    except Exception as e:
        raise UserError(f"Texte trop long pour un QR code : {e}")
    path = unique_path(Path(out_dir), safe_name(f"QR code - {label}") + f".{fmt}")
    qr.save(str(path), scale=QR_SCALE.get(p.get("size") or "medium", 10), border=4, dark=dark, light=light)
    return path


def make_barcode(p: dict, out_dir: Path) -> Path:
    from barcode import get_barcode_class
    from barcode.writer import ImageWriter, SVGWriter
    kind = p.get("kind") if p.get("kind") in BARCODES else "code128"
    data = re.sub(r"\s+", "", p.get("data") or "") if kind != "code128" else (p.get("data") or "").strip()
    if not data:
        raise UserError("Saisissez le contenu du code-barres.")
    fmt = "svg" if p.get("format") == "svg" else "png"
    try:
        code = get_barcode_class(kind)(data, writer=SVGWriter() if fmt == "svg" else ImageWriter())
    except Exception as e:
        hints = {"ean13": "12 ou 13 chiffres", "ean8": "7 ou 8 chiffres", "upca": "11 ou 12 chiffres",
                 "isbn13": "un ISBN commençant par 978 ou 979", "itf": "un nombre pair de chiffres",
                 "code39": "des majuscules, chiffres et - . $ / + % espace"}
        raise UserError(f"Contenu invalide pour un code {BARCODES[kind]}" + (f" ({hints[kind]})" if kind in hints else "")
                        + f" : {e}")
    base = unique_path(Path(out_dir), safe_name(f"{tr('Code-barres')} {BARCODES[kind]} - {data}") + f".{fmt}")
    options = {"module_height": 15.0, "font_size": 10, "text_distance": 5.0, "quiet_zone": 6.5}
    if fmt == "png":
        options["dpi"] = 300
    saved = code.save(str(base.with_suffix("")), options=options)
    return Path(saved)


def preview(path: Path) -> str | None:
    """Aperçu en data URL pour l'interface."""
    ext = path.suffix.lower()
    mime = {".png": "image/png", ".svg": "image/svg+xml"}.get(ext)
    if not mime or path.stat().st_size > 4_000_000:
        return None
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
