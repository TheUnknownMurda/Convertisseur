"""Détection des outils externes (FFmpeg, Edge, LibreOffice, Calibre, voix, OCR) et des modules Python."""
from __future__ import annotations

import importlib.util
import os
import sys
import re
import shutil
import subprocess
from pathlib import Path

from .util import NO_WINDOW

APP_DIR = Path(__file__).resolve().parent.parent


def _app_path(exe: str) -> str | None:
    try:
        import winreg
    except ImportError:
        return None
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as k:
                value, _ = winreg.QueryValueEx(k, None)
                value = str(value).strip('"')
                if value and Path(value).is_file():
                    return value
        except OSError:
            pass
    return None


def _program_files(*parts) -> list[Path]:
    out = []
    for var in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            out.append(Path(base, *parts))
    return out


def _first_file(paths) -> str | None:
    for p in paths:
        if p and Path(p).is_file():
            return str(Path(p))
    return None


def _winget_links(exe: str) -> str | None:
    """Programmes installés par winget (ex. FFmpeg) : raccourcis dans WinGet\\Links, même si le PATH n'est pas à jour."""
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        return None
    link = Path(base, "Microsoft", "WinGet", "Links", exe)
    if link.is_file():
        return str(link)
    return None


def find_ffmpeg() -> str | None:
    local = APP_DIR / "bin" / "ffmpeg.exe"
    if local.is_file():
        return str(local)
    p = shutil.which("ffmpeg") or _winget_links("ffmpeg.exe")
    if p:
        return p
    base = os.environ.get("LOCALAPPDATA")
    if base:                                  # paquet winget Gyan.FFmpeg sans lien
        for cand in sorted(Path(base, "Microsoft", "WinGet", "Packages").glob("Gyan.FFmpeg*/*/bin/ffmpeg.exe")):
            return str(cand)
    try:
        import imageio_ffmpeg  # optionnel
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def find_ffprobe(ffmpeg: str | None) -> str | None:
    if ffmpeg:
        cand = Path(ffmpeg).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if cand.is_file():
            return str(cand)
    return shutil.which("ffprobe")


def find_edge() -> str | None:
    return (_first_file(_program_files("Microsoft", "Edge", "Application", "msedge.exe"))
            or _app_path("msedge.exe") or shutil.which("msedge")
            or _first_file(_program_files("Google", "Chrome", "Application", "chrome.exe"))
            or _app_path("chrome.exe"))


def find_soffice() -> str | None:
    return (_first_file(_program_files("LibreOffice", "program", "soffice.exe"))
            or _app_path("soffice.exe") or shutil.which("soffice"))


def find_7zip() -> str | None:
    return (_first_file(_program_files("7-Zip", "7z.exe")) or _app_path("7zFM.exe") and
            str(Path(_app_path("7zFM.exe")).with_name("7z.exe")) or shutil.which("7z"))


def find_node() -> str | None:
    """Moteur JavaScript pour yt-dlp (YouTube) : Node.js ou Deno."""
    return (shutil.which("node") or shutil.which("deno") or _first_file(_program_files("nodejs", "node.exe"))
            or _winget_links("node.exe") or _winget_links("deno.exe"))


def find_calibre() -> str | None:
    return (_first_file(_program_files("Calibre2", "ebook-convert.exe"))
            or _first_file(_program_files("Calibre", "ebook-convert.exe"))
            or shutil.which("ebook-convert"))


def ffmpeg_version(ffmpeg: str) -> str | None:
    try:
        out = subprocess.run([ffmpeg, "-hide_banner", "-version"], capture_output=True, timeout=20,
                             creationflags=NO_WINDOW).stdout.decode("utf-8", "replace")
        m = re.search(r"ffmpeg version (\S+)", out)
        return re.split(r"[-_]", m.group(1))[0] if m else "?"
    except Exception:
        return None


def ffmpeg_encoders(ffmpeg: str) -> set[str]:
    try:
        out = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, timeout=20,
                             creationflags=NO_WINDOW).stdout.decode("utf-8", "replace")
    except Exception:
        return set()
    return set(re.findall(r"^\s*[VAS][.A-Z]{5}\s+(\S+)", out, re.M))


# Encodeurs matériels H.264 : nom -> (codec, arguments, libellé). {q} = niveau de qualité.
GPU_ENCODERS = {
    "nvenc": ("h264_nvenc", ["-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "{q}", "-b:v", "0"], "NVIDIA NVENC"),
    "qsv": ("h264_qsv", ["-preset", "medium", "-global_quality", "{q}"], "Intel Quick Sync"),
    "amf": ("h264_amf", ["-quality", "balanced", "-rc", "cqp", "-qp_i", "{q}", "-qp_p", "{q}", "-qp_b", "{q}"], "AMD AMF"),
}


def gpu_args(name: str, q: int) -> list[str]:
    codec, args, _ = GPU_ENCODERS[name]
    return ["-c:v", codec, *[a.replace("{q}", str(q)) for a in args]]


def detect_gpu(ffmpeg: str | None) -> str | None:
    if not ffmpeg:
        return None
    encoders = ffmpeg_encoders(ffmpeg)
    for name, (codec, _, _) in GPU_ENCODERS.items():
        if codec not in encoders:
            continue
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
               "testsrc2=size=320x240:rate=25:duration=0.4", "-pix_fmt", "yuv420p",
               *gpu_args(name, 23), "-f", "null", "-"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=40, creationflags=NO_WINDOW)
        except Exception:
            continue
        if r.returncode == 0:
            return name
    return None


_PS_VOICES = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              "$s.GetInstalledVoices() | Where-Object { $_.Enabled } | ForEach-Object { $_.VoiceInfo.Culture.Name + '|' + $_.VoiceInfo.Name }")

_PS_OCR = ("$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]; "
           "$e = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages(); "
           "if ($e) { 'OK ' + $e.RecognizerLanguage.LanguageTag } else { 'NONE' }")


def _powershell(script: str, timeout=40) -> str:
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                           capture_output=True, timeout=timeout, creationflags=NO_WINDOW)
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""
    except Exception:
        return ""


def detect_voices() -> list[dict]:
    voices = []
    for line in _powershell(_PS_VOICES).splitlines():
        if "|" in line:
            culture, name = line.strip().split("|", 1)
            voices.append({"culture": culture, "name": name})
    return voices


def detect_ocr() -> str | None:
    out = _powershell(_PS_OCR).strip()
    return out[3:].strip() if out.startswith("OK") else None


def ytdlp_version(fresh: bool = False) -> str | None:
    if fresh:   # nouveau processus : la version installée a pu changer depuis le démarrage
        try:
            exe = sys.executable.replace("pythonw.exe", "python.exe")
            out = subprocess.run([exe, "-c", "import importlib.metadata as m; print(m.version('yt-dlp'))"],
                                 capture_output=True, timeout=60, creationflags=NO_WINDOW)
            return out.stdout.decode().strip() or None
        except Exception:
            return None
    try:
        import importlib.metadata
        return importlib.metadata.version("yt-dlp")
    except Exception:
        return None


def python_features() -> dict:
    spec = importlib.util.find_spec
    f = {k: spec(m) is not None for k, m in {
        "pdf2docx": "pdf2docx", "mammoth": "mammoth", "markdown": "markdown", "vtracer": "vtracer",
        "resvg": "resvg_py", "pydocx": "docx", "openpyxl": "openpyxl", "xlrd": "xlrd", "odfpy": "odf",
        "pptx": "pptx", "heic": "pillow_heif", "whisper": "faster_whisper", "pysubs2": "pysubs2",
        "fonttools": "fontTools", "yaml": "yaml"}.items()}
    f["ytdlp_version"] = ytdlp_version()
    f["heic_save"] = False
    if f["heic"]:
        try:
            import pillow_heif
            f["heic_save"] = bool(pillow_heif.libheif_info().get("HEIF"))
        except Exception:
            f["heic"] = False
    try:
        from PIL import features
        f["avif"] = bool(features.check("avif"))
    except Exception:
        f["avif"] = False
    return f


def detect_basic() -> dict:
    """Détection rapide (sans test GPU, voix ni OCR)."""
    ffmpeg = find_ffmpeg()
    d = {
        "ffmpeg": ffmpeg,
        "ffprobe": find_ffprobe(ffmpeg),
        "ffmpeg_version": ffmpeg_version(ffmpeg) if ffmpeg else None,
        "edge": find_edge(),
        "soffice": find_soffice(),
        "calibre": find_calibre(),
        "sevenzip": find_7zip(),
        "gpu": None, "tts": False, "voices": [], "ocr": None,
    }
    d.update(python_features())
    return d


def detect_slow(d: dict) -> dict:
    """Détections lentes (quelques secondes) : GPU, voix de synthèse, OCR Windows."""
    d = dict(d)
    d["gpu"] = detect_gpu(d.get("ffmpeg"))
    d["voices"] = detect_voices()
    d["tts"] = bool(d["voices"])
    d["ocr"] = detect_ocr()
    return d


def known_folder(guid: str, fallback: str) -> Path:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
            value, _ = winreg.QueryValueEx(k, guid)
            p = Path(os.path.expandvars(value))
            if p.is_dir():
                return p
    except Exception:
        pass
    p = Path.home() / fallback
    return p if p.is_dir() else Path.home()


def downloads_dir() -> Path:
    return known_folder("{374DE290-123F-4565-9164-39C4925E467B}", "Downloads")


def desktop_dir() -> Path:
    return known_folder("Desktop", "Desktop")
