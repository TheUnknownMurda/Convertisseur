"""Lecture vocale (texte -> WAV) avec les voix de synthèse intégrées à Windows."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ..util import NO_WINDOW, FinalError, UserError, read_text_any

SCRIPT = r"""
param([string]$inPath, [string]$outPath, [string]$voice, [int]$rate)
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($voice) { try { $s.SelectVoice($voice) } catch { } }
$s.Rate = $rate
$s.SetOutputToWaveFile($outPath)
$text = [IO.File]::ReadAllText($inPath, [Text.Encoding]::UTF8)
$parts = [regex]::Split($text, "(?:\r?\n[ \t]*){2,}") | Where-Object { $_.Trim() -ne "" }
$n = @($parts).Count
$i = 0
foreach ($p in $parts) {
  $s.Speak($p)
  $i++
  [Console]::Out.WriteLine("PROGRESS $i/$n")
  [Console]::Out.Flush()
}
$s.Dispose()
"""

FR_WORDS = re.compile(r"\b(le|la|les|des|une|est|et|que|pour|dans|avec|pas|sur|vous|nous|qui|ce|du)\b", re.I)
EN_WORDS = re.compile(r"\b(the|and|is|of|to|that|for|with|you|not|this|are|was|it|on|be)\b", re.I)


def pick_voice(text: str, voices: list[dict], wanted: str | None) -> str:
    if wanted and wanted != "auto":
        return wanted
    fr, en = len(FR_WORDS.findall(text[:20000])), len(EN_WORDS.findall(text[:20000]))
    lang = "fr" if fr >= en else "en"
    for v in voices:
        if v["culture"].lower().startswith(lang):
            return v["name"]
    return voices[0]["name"] if voices else ""


def text_to_wav(ctx, src, sfmt, dst, d):
    text = read_text_any(src).strip()
    if not text:
        raise FinalError("Aucun texte à lire dans ce fichier.")
    clean = ctx.tmp / "lecture.txt"
    clean.write_text(text, encoding="utf-8")
    script = ctx.tmp / "lecture.ps1"
    script.write_text(SCRIPT, encoding="utf-8-sig")
    voice = pick_voice(text, ctx.tools.get("voices") or [], ctx.opts.get("voice"))
    rate = max(-10, min(10, int(ctx.opts.get("tts_rate") or 0)))
    ctx.progress(0.01, f"Lecture vocale ({voice or 'voix par défaut'})…")
    proc = subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                             str(script), "-inPath", str(clean), "-outPath", str(dst), "-voice", voice,
                             "-rate", str(rate)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=NO_WINDOW)
    for raw in proc.stdout:
        m = re.match(r"PROGRESS (\d+)/(\d+)", raw.decode("utf-8", "replace").strip())
        if m:
            ctx.progress(int(m[1]) / max(1, int(m[2])))
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0 or not Path(dst).exists() or Path(dst).stat().st_size < 100:
        raise UserError("La synthèse vocale a échoué. " + err.strip()[-300:])
    return [dst]
