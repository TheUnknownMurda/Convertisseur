"""Reconnaissance de texte (OCR) avec le moteur intégré à Windows (Windows.Media.Ocr)."""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..util import NO_WINDOW, FinalError, UserError

SCRIPT = r"""
param([string]$path, [string]$lang)
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) {
  $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = $null
foreach ($l in [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages) {
  if ($lang -and $l.LanguageTag.StartsWith($lang)) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($l); break }
}
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
if (-not $engine) { [Console]::Error.WriteLine("NOENGINE"); exit 3 }
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
foreach ($line in $result.Lines) { [Console]::Out.WriteLine($line.Text) }
"""


def _prepare(src, sfmt, dst) -> Path:
    from PIL import Image
    from .images import flatten, normalize, open_image
    img = flatten(normalize(open_image(src, sfmt, min_side=1600)))
    longest = max(img.size)
    if longest > 4000:
        img.thumbnail((4000, 4000), Image.LANCZOS)
    elif longest < 1200:
        s = 1200 / longest
        img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    img.save(dst, "PNG")
    return Path(dst)


def ocr_image_file(ctx, png: Path, lang: str = "fr") -> str:
    script = ctx.tmp / "ocr.ps1"
    if not script.exists():
        script.write_text(SCRIPT, encoding="utf-8-sig")
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                        str(script), "-path", str(Path(png).resolve()), "-lang", lang],
                       capture_output=True, timeout=300, creationflags=NO_WINDOW)
    if r.returncode != 0:
        raise UserError("La reconnaissance de texte a échoué : " +
                        r.stderr.decode("utf-8", "replace").strip()[-300:])
    return r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")


def image_to_text(ctx, src, sfmt, dst, d):
    ctx.progress(None, "Reconnaissance du texte…")
    png = _prepare(src, sfmt, ctx.tmp / "ocr_source.png")
    text = ocr_image_file(ctx, png).strip()
    if not text:
        raise FinalError("Aucun texte reconnu dans cette image.")
    Path(dst).write_text(text + "\n", encoding="utf-8")
    return [dst]
