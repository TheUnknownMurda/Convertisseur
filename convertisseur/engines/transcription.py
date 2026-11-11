"""Transcription de la parole (audio/vidéo -> TXT, SRT, VTT) avec Whisper (faster-whisper), en local.

Le modèle choisi est téléchargé une seule fois dans le dossier « modeles\\whisper » de l'application,
puis tout fonctionne hors ligne. Les sous-titres déjà intégrés à une vidéo sont extraits directement.
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from ..util import NO_WINDOW, FinalError, UserError

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

MODEL_DIR = Path(__file__).resolve().parents[2] / "modeles" / "whisper"   # voyage avec l'application
MODEL_BYTES = {"tiny": 75e6, "base": 145e6, "small": 484e6, "medium": 1.53e9, "large-v3-turbo": 1.62e9}
TEXT_SUBS = {"subrip", "ass", "ssa", "mov_text", "webvtt", "text"}
# Phrases que Whisper « invente » parfois sur du silence (sous-titres de films ayant servi à l'entraînement).
HALLUCINATIONS = re.compile(
    r"(amara\.org|sous-titr(es|age) (réalisés?|fait|par)|merci d'avoir regardé|abonnez-vous|"
    r"thanks? for watching|subtitles by|please subscribe)", re.I)


def repo_dir(name: str) -> Path:
    from faster_whisper.utils import _MODELS
    repo = _MODELS.get(name, name)
    return MODEL_DIR / ("models--" + repo.replace("/", "--"))


def downloaded_models() -> list[str]:
    try:
        return [n for n in MODEL_BYTES if any(repo_dir(n).glob("snapshots/*/model.bin"))]
    except Exception:
        return []


# Bibliothèques NVIDIA (cuBLAS 12, cuDNN 9) : installées dans un dossier au chemin court, car Windows refuse
# de charger des DLL dont le chemin dépasse 260 caractères.
CUDA_HOME = Path(os.environ.get("PROGRAMDATA") or r"C:\ProgramData") / "Convertisseur" / "cuda"


def cuda_library_dirs() -> list[str] | None:
    dirs = [d for d in os.environ.get("PATH", "").split(os.pathsep) if d]
    for base in (CUDA_HOME, Path(sys.prefix) / "Lib" / "site-packages"):
        dirs += glob.glob(str(base / "nvidia" / "*" / "bin"))
    found = {}
    for need in ("cublas64_12.dll", "cublasLt64_12.dll", "cudnn64_9.dll"):
        for d in dirs:
            if os.path.isfile(os.path.join(d, need)):
                found[need] = d
                break
    return sorted(set(found.values())) if len(found) == 3 else None


def cuda_available() -> bool:
    """Vrai si une carte NVIDIA et les bibliothèques CUDA nécessaires sont présentes."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() < 1:
            return False
    except Exception:
        return False
    return cuda_library_dirs() is not None


def _cuda_ready() -> bool:
    if not cuda_available():
        return False
    for d in cuda_library_dirs() or []:
        try:
            os.add_dll_directory(d)
        except OSError:
            pass
        if d not in os.environ.get("PATH", ""):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
    return True


RUNTIME_HOME = CUDA_HOME.parent / "runtime"     # copie d'onnxruntime au chemin court (voir CUDA_HOME)


def _vad_available() -> bool:
    """Le détecteur de parole (Silero) dépend d'onnxruntime, dont les DLL refusent les chemins trop longs."""
    try:
        import onnxruntime  # noqa: F401
        return True
    except Exception:
        pass
    if not (RUNTIME_HOME / "onnxruntime").is_dir():
        return False
    for name in [m for m in sys.modules if m == "onnxruntime" or m.startswith("onnxruntime.")]:
        del sys.modules[name]
    if str(RUNTIME_HOME) not in sys.path:
        sys.path.insert(0, str(RUNTIME_HOME))
    try:
        import onnxruntime  # noqa: F401,F811
        return True
    except Exception:
        return False


def _folder_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def ensure_model(ctx, name: str, span=(0.05, 0.3)) -> str:
    """Chemin local du modèle, téléchargé (une seule fois) si nécessaire."""
    from faster_whisper.utils import download_model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        path = download_model(name, local_files_only=True, cache_dir=str(MODEL_DIR))
    except Exception:
        expected = MODEL_BYTES.get(name, 5e8)
        label = f"{expected / 1e9:.1f} Go".replace(".", ",") if expected >= 1e9 else f"{expected / 1e6:.0f} Mo"
        ctx.progress(span[0], f"Téléchargement du modèle « {name} » ({label}, une seule fois)…")
        stop = threading.Event()
        folder = repo_dir(name)
        base = _folder_size(folder) if folder.exists() else 0

        def watch():
            while not stop.wait(0.7):
                done = (_folder_size(folder) - base) if folder.exists() else 0
                ctx.progress(span[0] + (span[1] - span[0]) * min(0.99, done / expected))
        t = threading.Thread(target=watch, daemon=True)
        t.start()
        try:
            path = download_model(name, cache_dir=str(MODEL_DIR))
        except Exception as e:
            raise FinalError(f"Impossible de télécharger le modèle de transcription « {name} » "
                            f"(connexion Internet requise la première fois) : {e}")
        finally:
            stop.set()
    return path


def make_model(path: str, where: str):
    from faster_whisper import WhisperModel
    if where == "GPU":
        return WhisperModel(path, device="cuda", compute_type="float16")
    return WhisperModel(path, device="cpu", compute_type="int8", cpu_threads=max(4, (os.cpu_count() or 8) - 2))


def _run(ctx, model, samples, lang, translate, vad, where, duration):
    """Transcrit entièrement (le générateur est consommé ici) et renvoie les répliques retenues."""
    t0 = time.monotonic()
    segments, tinfo = model.transcribe(
        samples, language=None if lang == "auto" else lang, task="translate" if translate else "transcribe",
        beam_size=5, vad_filter=vad, condition_on_previous_text=False)
    total = tinfo.duration or duration or 0
    detected = f", langue : {tinfo.language}" if lang == "auto" and tinfo.language else ""
    cues = []
    for seg in segments:
        text = seg.text.strip()
        if not text or (HALLUCINATIONS.search(text) and seg.no_speech_prob > 0.2):
            continue
        # Silence, bruit, bip ou musique : Whisper y « entend » parfois un mot (« You », « Merci »…).
        nsp, lp = seg.no_speech_prob, seg.avg_logprob
        if nsp > 0.6 or lp < -1.0 or (nsp > 0.3 and lp < -0.7) or (nsp > 0.3 and len(text.split()) <= 2):
            continue
        cues.append((seg.start, seg.end, text))
        if total:
            speed = seg.end / max(0.1, time.monotonic() - t0)
            ctx.progress(0.3 + 0.7 * min(1.0, seg.end / total),
                         f"Transcription ({where}{detected}) — {speed:.0f}× le temps réel…" if speed >= 10 else
                         f"Transcription ({where}{detected}) — {speed:.1f}× le temps réel…")
    return cues


def _ts(sec: float, sep: str) -> str:
    ms = int(round(max(0.0, sec) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def write_subtitles(cues: list[tuple[float, float, str]], dst: Path, kind: str) -> None:
    if kind == "srt":
        body = "\n".join(f"{i}\n{_ts(a, ',')} --> {_ts(b, ',')}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1))
    else:
        body = "WEBVTT\n\n" + "\n".join(f"{_ts(a, '.')} --> {_ts(b, '.')}\n{t}\n" for a, b, t in cues)
    dst.write_text(body, encoding="utf-8")


def write_text(cues: list[tuple[float, float, str]], dst: Path) -> None:
    paragraphs, cur, last_end = [], [], None
    for a, b, t in cues:
        if cur and last_end is not None and a - last_end > 2.0:
            paragraphs.append(" ".join(cur))
            cur = []
        cur.append(t)
        last_end = b
    if cur:
        paragraphs.append(" ".join(cur))
    dst.write_text("\n\n".join(paragraphs).strip() + "\n", encoding="utf-8")


def _embedded_subtitle_index(ctx, src) -> int | None:
    ffprobe = ctx.tools.get("ffprobe")
    if not ffprobe:
        return None
    try:
        r = subprocess.run([ffprobe, "-v", "error", "-select_streams", "s", "-show_entries", "stream=index,codec_name",
                            "-of", "csv=p=0", str(src)], capture_output=True, timeout=60, creationflags=NO_WINDOW)
    except Exception:
        return None
    for n, line in enumerate(r.stdout.decode("utf-8", "replace").splitlines()):
        parts = line.strip().split(",")
        if len(parts) >= 2 and parts[1] in TEXT_SUBS:
            return n
    return None


def transcribe(ctx, src, sfmt, dst, d):
    from .media import probe_media, run_ffmpeg
    o = ctx.opts
    dst = Path(dst)
    if d in ("srt", "vtt") and (o.get("subs_mode") or "auto") == "auto":
        idx = _embedded_subtitle_index(ctx, src)
        if idx is not None:
            run_ffmpeg(ctx, ["-i", src, "-map", f"0:s:{idx}", "-c:s", "srt" if d == "srt" else "webvtt", dst], None,
                       "Extraction des sous-titres intégrés…")
            return [dst]
    info = probe_media(ctx.tools, src)
    if not info["has_audio"]:
        raise FinalError("Ce fichier ne contient aucune piste audio à transcrire.")
    duration = info.get("duration")
    wav = ctx.tmp / "parole.wav"
    run_ffmpeg(ctx, ["-i", src, "-vn", "-sn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav], duration,
               "Préparation de l'audio…", (0.0, 0.05))
    path = ensure_model(ctx, o.get("whisper_model") or "small")
    lang = o.get("whisper_lang") or "auto"
    vad = _vad_available()
    # L'audio est passé déjà décodé (16 kHz mono) : pas de dépendance au décodage de PyAV.
    import wave
    import numpy as np
    with wave.open(str(wav), "rb") as w:
        samples = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if samples.size < 1600:
        raise FinalError("L'audio est trop court pour être transcrit.")
    devices = (["GPU"] if ctx.gpu and _cuda_ready() else []) + ["processeur"]
    cues = []
    for where in devices:
        ctx.progress(0.3, f"Chargement du modèle ({where})…")
        try:
            model = make_model(path, where)
            cues = _run(ctx, model, samples, lang, o.get("whisper_translate"), vad, where, duration)
            break
        except FinalError:
            raise
        except Exception as e:
            if where == devices[-1]:
                raise
            print(f"GPU indisponible pour la transcription : {e}", file=sys.stderr)
            ctx.progress(0.3, "Carte graphique indisponible : passage au processeur…")
    if not cues:
        raise FinalError("Aucune parole reconnue dans ce fichier.")
    if d == "txt":
        write_text(cues, dst)
    else:
        write_subtitles(cues, dst, d)
    return [dst]
