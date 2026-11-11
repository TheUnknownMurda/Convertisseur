"""Sous-titres : SRT, VTT, ASS, SSA, SBV, TTML, LRC, SUB (MicroDVD), SAMI <-> les uns vers les autres et TXT."""
from __future__ import annotations

import re
from pathlib import Path

from ..util import FinalError, read_text_any

PYSUBS = {"srt": "srt", "vtt": "vtt", "ass": "ass", "ssa": "ssa", "ttml": "ttml", "dfxp": "ttml", "sub": "microdvd",
          "smi": "sami", "sami": "sami"}


def _ms(h, m, s, frac="0") -> int:
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int((frac + "000")[:3])


def _parse_sbv(text):
    import pysubs2
    subs = pysubs2.SSAFile()
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        m = re.match(r"(\d+):(\d+):(\d+)\.(\d+),(\d+):(\d+):(\d+)\.(\d+)", lines[0].strip()) if lines else None
        if m and len(lines) > 1:
            subs.append(pysubs2.SSAEvent(start=_ms(*m.groups()[:4]), end=_ms(*m.groups()[4:]),
                                         text="\\N".join(lines[1:])))
    return subs


def _parse_lrc(text):
    import pysubs2
    times = []
    for line in text.splitlines():
        stamps = re.findall(r"\[(\d+):(\d+)(?:[.:](\d+))?\]", line)
        words = re.sub(r"\[[^\]]*\]", "", line).strip()
        for mm, ss, ff in stamps:
            times.append((_ms(0, mm, ss, ff or "0"), words))
    times.sort()
    subs = pysubs2.SSAFile()
    for i, (start, words) in enumerate(times):
        if not words:
            continue
        end = times[i + 1][0] if i + 1 < len(times) else start + 4000
        subs.append(pysubs2.SSAEvent(start=start, end=max(end, start + 500), text=words))
    return subs


def load(path, fmt):
    import pysubs2
    text = read_text_any(path).replace("\r\n", "\n")
    if fmt == "sbv":
        return _parse_sbv(text)
    if fmt == "lrc":
        return _parse_lrc(text)
    try:
        return pysubs2.SSAFile.from_string(text, format_=PYSUBS.get(fmt), fps=25)
    except Exception:
        try:
            return pysubs2.SSAFile.from_string(text, fps=25)
        except Exception as e:
            raise FinalError(f"Sous-titres illisibles : {e}")


def _clock(ms: int, sep=".") -> str:
    ms = max(0, int(ms))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h}:{m:02d}:{s:02d}{sep}{ms:03d}"


def convert(ctx, src, sfmt, dst, d):
    subs = load(src, sfmt)
    events = [e for e in subs.events if not e.is_comment and e.plaintext.strip()]
    if not events:
        raise FinalError("Aucun sous-titre trouvé dans ce fichier.")
    dst = Path(dst)
    if d == "txt":
        dst.write_text("\n".join(e.plaintext.replace("\n", " ").strip() for e in events) + "\n", encoding="utf-8")
    elif d == "sbv":
        dst.write_text("\n".join(f"{_clock(e.start)},{_clock(e.end)}\n{e.plaintext.strip()}\n" for e in events),
                       encoding="utf-8")
    elif d == "lrc":
        lines = []
        for e in events:
            m, s = divmod(e.start / 1000, 60)
            lines.append(f"[{int(m):02d}:{s:05.2f}]{e.plaintext.replace(chr(10), ' ').strip()}")
        dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif d == "smi":                              # SAMI : écrit à la main (non géré par pysubs2)
        import html
        body = []
        for e in events:
            text = "<br>".join(html.escape(line) for line in e.plaintext.splitlines())
            body.append(f"<SYNC Start={e.start}><P Class=FRCC>{text}</P></SYNC>")
            body.append(f"<SYNC Start={e.end}><P Class=FRCC>&nbsp;</P></SYNC>")
        dst.write_text("<SAMI>\n<HEAD><TITLE></TITLE><STYLE TYPE=\"text/css\"><!--\nP { font-family: Arial; "
                       "text-align: center; }\n.FRCC { Name: Français; lang: fr-CA; }\n--></STYLE></HEAD>\n<BODY>\n"
                       + "\n".join(body) + "\n</BODY>\n</SAMI>\n", encoding="utf-8")
    else:
        subs.events = events
        subs.save(str(dst), format_=PYSUBS[d], fps=25, encoding="utf-8")
    return [dst]


def to_srt(src, sfmt, dst) -> Path:
    """Convertit n'importe quels sous-titres en SRT (pour l'incrustation dans une vidéo)."""
    subs = load(src, sfmt)
    subs.save(str(dst), format_="srt", encoding="utf-8")
    return Path(dst)
