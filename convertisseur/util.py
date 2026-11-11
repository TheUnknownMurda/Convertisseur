"""Petits utilitaires partagés (noms de fichiers, temps, pages, processus)."""
from __future__ import annotations

import ctypes
import os
import re
import shutil
import subprocess
from pathlib import Path

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class UserError(Exception):
    """Erreur dont le message peut être montré tel quel à l'utilisateur."""


class FinalError(UserError):
    """Le fichier lui-même empêche la conversion (protégé, vide, sans parole…) : inutile d'essayer un autre chemin."""


def safe_name(name: str, default: str = "fichier") -> str:
    name = _INVALID.sub("_", str(name)).strip().rstrip(". ")
    if not name:
        name = default
    if name.split(".")[0].upper() in _RESERVED:
        name = "_" + name
    if len(name) > 180:
        stem, dot, ext = name.rpartition(".")
        name = (stem[: 170] + dot + ext) if dot and len(ext) < 10 else name[:180]
    return name


def unique_path(folder: Path, filename: str) -> Path:
    p = Path(folder) / filename
    if not p.exists():
        return p
    if p.suffix and not p.is_dir():
        stem, suffix = p.stem, p.suffix
    else:
        stem, suffix = (p.stem, p.suffix) if p.suffix else (p.name, "")
    i = 1
    while True:
        q = Path(folder) / f"{stem} ({i}){suffix}"
        if not q.exists():
            return q
        i += 1


def parse_time(value) -> float | None:
    """Accepte « 90 », « 1:30 », « 01:02:03.5 », « 1m30s ». Vide -> None."""
    if value is None:
        return None
    s = str(value).strip().lower().replace(",", ".")
    if not s:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = s.split(":")
    if 2 <= len(parts) <= 3 and all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        total = 0.0
        for p in parts:
            total = total * 60 + float(p)
        return total
    m = re.fullmatch(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+(?:\.\d+)?)\s*s)?", s)
    if m and any(m.groups()):
        h, mi, se = m.groups()
        return int(h or 0) * 3600 + int(mi or 0) * 60 + float(se or 0)
    raise UserError(f"Temps invalide : « {value} » (exemples : 1:30 ou 90).")


def fmt_time(sec: float) -> str:
    sec = max(0.0, float(sec))
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = sec - h * 3600 - m * 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def parse_pages(spec, count: int) -> list[int]:
    """« 1-3, 5 » -> [0, 1, 2, 4]. Vide -> toutes les pages."""
    s = (spec or "").replace(" ", "")
    if not s:
        return list(range(count))
    pages: list[int] = []
    for part in s.split(","):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)?-(\d+)?|(\d+)", part)
        if not m:
            raise UserError(f"Pages invalides : « {spec} » (exemple : 1-3, 5).")
        if m.group(3):
            a = b = int(m.group(3))
        else:
            a, b = int(m.group(1) or 1), int(m.group(2) or count)
        if a > b:
            a, b = b, a
        for p in range(max(a, 1), min(b, count) + 1):
            if p - 1 not in pages:
                pages.append(p - 1)
    if not pages:
        raise UserError(f"Aucune page valide dans « {spec} » (le document compte {count} page(s)).")
    return pages


def kill_tree(pid: int) -> None:
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True,
                       creationflags=NO_WINDOW, timeout=20)
    except Exception:
        pass


def rmtree_quiet(path) -> None:
    if path:
        shutil.rmtree(path, ignore_errors=True)


def hide_path(path) -> None:
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x02)
        except Exception:
            pass


def read_text_any(path) -> str:
    """Lit un fichier texte en devinant l'encodage (UTF-8, UTF-16, Windows-1252)."""
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", "replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", "replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", "replace")


def run(cmd, timeout=None, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], capture_output=True, timeout=timeout,
                          creationflags=NO_WINDOW, **kw)
