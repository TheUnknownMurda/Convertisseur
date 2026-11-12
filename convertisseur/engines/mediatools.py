"""Outils vidéo et audio : fond flou vertical, filigrane, lecture inversée, planche d'aperçu, extraction
d'images, découpage en morceaux, logo, nouvelle bande-son, pochette."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..i18n import tr
from ..util import FinalError, UserError, fmt_time, unique_path
from .media import (CONTAINER, COPY_RULES, EVEN, _readable, _scale, _trim, aenc, probe_media, run_ffmpeg,
                    venc)

BLUR_TARGETS = {"9:16b": (9, 16), "1:1b": (1, 1)}
WM_RATIO = {"small": 0.045, "medium": 0.07, "large": 0.11}
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")


def blur_fill(info, mode, rotate=None) -> str | None:
    """Format vertical ou carré : la vidéo entière au centre, sur un fond flou d'elle-même."""
    if mode not in BLUR_TARGETS:
        return None
    w, h = info.get("width") or 1280, info.get("height") or 720
    if rotate in ("cw", "ccw"):
        w, h = h, w
    big = max(w, h) >= 1280
    if BLUR_TARGETS[mode] == (9, 16):
        W, H = (1080, 1920) if big else (720, 1280)
    else:
        W = H = 1080 if big else 720
    return (f"split=2[cvbg][cvfg];[cvbg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=20:2,eq=brightness=-0.05[cvb];[cvfg]scale={W}:{H}:force_original_aspect_ratio=decrease[cvf];"
            f"[cvb][cvf]overlay=(W-w)/2:(H-h)/2,setsar=1")


def _font_copy(ctx) -> str:
    """Police copiée à côté (chemin relatif) : évite d'échapper « C: » dans les filtres FFmpeg."""
    if FONT_BOLD.is_file():
        target = ctx.tmp / "police.ttf"
        if not target.exists():
            shutil.copyfile(FONT_BOLD, target)
        return "fontfile=police.ttf:"
    return ""


def drawtext(ctx, o) -> str | None:
    text = (o.get("wm_text") or "").strip()
    if not text:
        return None
    (ctx.tmp / "filigrane.txt").write_text(text, encoding="utf-8")
    ratio = WM_RATIO.get(o.get("wm_size") or "medium", 0.07)
    alpha = max(0.05, min(1.0, (o.get("wm_opacity") or 25) / 100))
    color = (o.get("wm_color") or "#808080").lstrip("#")
    m = "h*0.03"
    x, y = {"br": (f"w-tw-{m}", f"h-th-{m}"), "bl": (m, f"h-th-{m}"), "tr": (f"w-tw-{m}", m), "tl": (m, m),
            "top": ("(w-tw)/2", m), "bottom": ("(w-tw)/2", f"h-th-{m}")}.get(o.get("wm_pos") or "",
                                                                           ("(w-tw)/2", "(h-th)/2"))
    return (f"drawtext={_font_copy(ctx)}textfile=filigrane.txt:fontsize=h*{ratio}:fontcolor=0x{color}@{alpha:.2f}:"
            f"borderw=2:bordercolor=black@{alpha * 0.6:.2f}:x={x}:y={y}")


def play_effect(ctx, src, dst, t, info, head, tail, dur):
    """Lecture à l'envers ou aller-retour (boomerang)."""
    o = ctx.opts
    if dur and dur > 180:
        raise FinalError("La lecture inversée est limitée à 3 minutes : réglez « Début » et « Fin » sur un extrait.")
    mode = o.get("v_play")
    scale = _scale(info, o.get("v_res"))
    pre = (scale + "," if scale else "") + EVEN
    sound = info["has_audio"] and not o.get("mute")
    if mode == "reverse":
        graph = [f"[0:v]{pre},reverse,format=yuv420p[v]"] + (["[0:a]areverse[a]"] if sound else [])
        total = dur
    else:
        graph = [f"[0:v]{pre},split[f][r0];[r0]reverse[r];[f][r]concat=n=2:v=1:a=0,format=yuv420p[v]"]
        if sound:
            graph.append("[0:a]asplit[af][ar0];[ar0]areverse[ar];[af][ar]concat=n=2:v=0:a=1[a]")
        total = dur * 2 if dur else None
    args = [*head, "-i", src, *tail, "-filter_complex", ";".join(graph), "-map", "[v]",
            *venc(t, "high", None, info.get("fps"))]
    args += (["-map", "[a]", *aenc(t, "high")] if sound else ["-an"]) + CONTAINER.get(t, []) + [dst]
    run_ffmpeg(ctx, args, total, "Inversion de la vidéo…")
    return [dst]


def contact_sheet(ctx, src, sfmt, dst, d):
    """Planche d'aperçu : une grille d'images prises à intervalles réguliers, avec leur minutage."""
    info = probe_media(ctx.tools, src)
    _readable(info)
    if not info["has_video"]:
        raise FinalError("Aucune image dans ce fichier.")
    dur = info.get("duration") or 0
    if dur <= 0:
        raise FinalError("Durée inconnue : impossible de répartir les images.")
    cols, rows = (int(x) for x in (ctx.opts.get("sheet_grid") or "4x4").split("x"))
    step = dur / (cols * rows)
    width = 480 if cols <= 4 else 360
    offset = step / 2
    stamp = "%{pts\\:hms\\:" + f"{offset:.3f}" + "}"
    label = (f",drawtext={_font_copy(ctx)}text='{stamp}':fontsize={max(14, width // 22)}:"
             "fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=4:x=8:y=h-th-8")
    vf = f"fps=1/{step:.4f},scale={width}:-2{label},tile={cols}x{rows}:padding=6:margin=10:color=0x16171c"
    run_ffmpeg(ctx, ["-ss", fmt_time(offset), "-i", src, "-vf", vf, "-frames:v", "1", "-q:v", "3", "-update", "1",
                     dst], dur, "Création de la planche d'aperçu…", cwd=ctx.tmp)
    if not Path(dst).exists():
        raise FinalError("La planche n'a pas pu être créée.")
    return [dst]


def video_frames(ctx, src, sfmt, dst, d):
    """Images extraites (JPG) à la cadence choisie, regroupées dans un ZIP."""
    import zipfile
    o = ctx.opts
    info = probe_media(ctx.tools, src)
    _readable(info)
    if not info["has_video"]:
        raise FinalError("Aucune image dans ce fichier.")
    head, tail, dur = _trim(o, info)
    rate = o.get("frames_rate") or "1"
    per_s = (info.get("fps") or 25) if rate == "all" else float(rate)
    if dur and dur * per_s > 3000:
        raise FinalError(f"Cela ferait environ {int(dur * per_s)} images : choisissez moins d'images par seconde, "
                         "ou un extrait (Début et Fin).")
    out = ctx.tmp / "images"
    out.mkdir(exist_ok=True)
    vf = [] if rate == "all" else ["-vf", f"fps={rate}"]
    run_ffmpeg(ctx, [*head, "-i", src, *tail, *vf, "-q:v", "2", str(out / "image_%05d.jpg")], dur,
               "Extraction des images…", (0.0, 0.9))
    files = sorted(out.glob("image_*.jpg"))
    if not files:
        raise FinalError("Aucune image n'a pu être extraite.")
    ctx.progress(0.92, f"Création du ZIP ({len(files)} images)…")
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as z:
        for f in files:
            z.write(f, f.name)
    return [dst]


SPLIT_LEN = {"15s": 15, "30s": 30, "60s": 60, "5m": 300, "10m": 600, "15m": 900, "30m": 1800, "60m": 3600}


def media_split(ctx, src, sfmt, dst, d):
    """Morceaux de durée fixe, sans réencodage (coupes sur les images clés pour la vidéo)."""
    info = probe_media(ctx.tools, src)
    _readable(info)
    seg = SPLIT_LEN.get(ctx.opts.get("split_len") or "5m", 300)
    dur = info.get("duration") or 0
    if dur and dur <= seg * 1.02:
        raise FinalError("Le fichier est plus court qu'un morceau : il n'y a rien à découper.")
    ext = Path(src).suffix.lower() or (".mp4" if info["has_video"] else ".mp3")
    folder = unique_path(Path(dst).parent, f"{ctx.stem} {tr('(morceaux)')}")
    folder.mkdir(parents=True)
    stem = ctx.stem.replace("%", "%%")
    maps = ["-map", "0:v:0", "-map", "0:a?"] if info["has_video"] else ["-map", "0:a:0", "-vn"]
    run_ffmpeg(ctx, ["-i", src, *maps, "-c", "copy", "-f", "segment", "-segment_time", str(seg),
                     "-segment_start_number", "1", "-reset_timestamps", "1",
                     str(folder / f"{stem} - {tr('partie')} %03d{ext}")], dur, "Découpage…")
    if not any(folder.iterdir()):
        folder.rmdir()
        raise FinalError("Le découpage n'a produit aucun fichier.")
    return [folder]


def _pick(items, exts, exclude=None):
    return next((x for x in items if x[1] in exts and x is not exclude), None)


def combine_logo(ctx, items, out_dir) -> list[Path]:
    from .. import formats as F
    from .images import to_png
    video, logo = _pick(items, F.VIDEO_IN), _pick(items, F.IMAGE_IN)
    if not video or not logo:
        raise UserError("Ajoutez une vidéo et une image (le logo).")
    o = ctx.opts
    info = probe_media(ctx.tools, video[0])
    _readable(info)
    ctx.stem = Path(video[2]).stem
    png = to_png(logo[0], logo[1], ctx.tmp / "logo.png", max_side=2000)
    vw, vh = info.get("width") or 1280, info.get("height") or 720
    ratio = {"small": 0.12, "medium": 0.18, "large": 0.28}.get(o.get("logo_size") or "medium", 0.18)
    lw = max(16, int(vw * ratio) // 2 * 2)
    m = max(8, int(min(vw, vh) * 0.03))
    x, y = {"br": (f"W-w-{m}", f"H-h-{m}"), "bl": (str(m), f"H-h-{m}"), "tr": (f"W-w-{m}", str(m)),
            "tl": (str(m), str(m))}.get(o.get("logo_pos") or "br", ("(W-w)/2", "(H-h)/2"))
    alpha = max(0.05, min(1.0, (o.get("logo_opacity") or 90) / 100))
    graph = (f"[1:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={alpha:.2f}[lg];"
             f"[0:v][lg]overlay={x}:{y}:format=auto:shortest=1,{EVEN},format=yuv420p[v]")
    dst = ctx.stage_dir() / f"{ctx.stem} {tr('(logo)')}.mp4"
    args = ["-i", video[0], "-loop", "1", "-i", png, "-filter_complex", graph, "-map", "[v]", "-map", "0:a?",
            *venc("mp4", "high", ctx.gpu, info.get("fps")), *aenc("mp4", "high"), *CONTAINER["mp4"], dst]
    run_ffmpeg(ctx, args, info.get("duration"), "Ajout du logo…")
    return [dst]


def combine_soundtrack(ctx, items, out_dir) -> list[Path]:
    from .. import formats as F
    video = _pick(items, F.VIDEO_IN)
    audio = _pick(items, F.AUDIO_IN) or _pick(items, F.VIDEO_IN, exclude=video)
    if not video or not audio:
        raise UserError("Ajoutez une vidéo et un fichier audio (la nouvelle bande-son).")
    vinfo, ainfo = probe_media(ctx.tools, video[0]), probe_media(ctx.tools, audio[0])
    _readable(vinfo)
    if not ainfo["has_audio"]:
        raise UserError(f"« {audio[2]} » ne contient pas de son.")
    ctx.stem = Path(video[2]).stem
    vdur = vinfo.get("duration")
    if (ctx.opts.get("soundtrack_mode") or "replace") == "mix" and vinfo["has_audio"]:
        graph = "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2:weights=1 0.8[a]"
    else:
        graph = "[1:a]apad[a]"
    vcopy = vinfo.get("vcodec") in COPY_RULES["mp4"][0] and not vinfo.get("hdr")
    vcodec = ["-c:v", "copy"] if vcopy else venc("mp4", "high", ctx.gpu, vinfo.get("fps"))
    dst = ctx.stage_dir() / f"{ctx.stem} {tr('(bande-son)')}.mp4"
    args = ["-i", video[0], "-i", audio[0], "-filter_complex", graph, "-map", "0:v:0", "-map", "[a]", *vcodec,
            *aenc("mp4", "high"), *(["-t", f"{vdur:.3f}"] if vdur else ["-shortest"]), *CONTAINER["mp4"], dst]
    run_ffmpeg(ctx, args, vdur, "Remplacement de la bande-son…")
    return [dst]


COVER_EXT = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus"}
LOSSLESS_EXT = {".wav", ".wave", ".aiff", ".aif", ".aifc", ".wv", ".tta", ".caf", ".au"}


def combine_cover(ctx, items, out_dir) -> list[Path]:
    """Pochette ajoutée à un fichier audio (sans réencodage quand le format la prend en charge)."""
    import io
    from PIL import Image
    from .. import formats as F
    from .download import write_cover
    from .images import flatten, normalize, open_image
    audio, image = _pick(items, F.AUDIO_IN), _pick(items, F.IMAGE_IN)
    if not audio or not image:
        raise UserError("Ajoutez un fichier audio et une image (la pochette).")
    ctx.stem = Path(audio[2]).stem
    ext = Path(audio[0]).suffix.lower()
    if ext in COVER_EXT:
        dst = ctx.stage_dir() / f"{ctx.stem} {tr('(pochette)')}{ext}"
        shutil.copyfile(audio[0], dst)
    else:                                             # WAV, AIFF… : FLAC sans perte ; autres : MP3
        lossless = ext in LOSSLESS_EXT
        dst = ctx.stage_dir() / f"{ctx.stem} {tr('(pochette)')}.{'flac' if lossless else 'mp3'}"
        codec = ["-c:a", "flac"] if lossless else ["-c:a", "libmp3lame", "-b:a", "256k", "-id3v2_version", "3"]
        run_ffmpeg(ctx, ["-i", audio[0], "-map", "0:a:0", "-vn", *codec, dst],
                   probe_media(ctx.tools, audio[0]).get("duration"), "Préparation de l'audio…")
    img = flatten(normalize(open_image(image[0], image[1])))
    img.thumbnail((1200, 1200), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=90)
    write_cover(dst, buf.getvalue())
    return [dst]
