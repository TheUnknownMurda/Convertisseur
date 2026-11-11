"""Conversions audio / vidéo / animation avec FFmpeg."""
from __future__ import annotations

import json
import re
import subprocess
import threading
from collections import deque
from pathlib import Path

from ..tools import gpu_args
from ..util import NO_WINDOW, FinalError, UserError, fmt_time, parse_time


class FFmpegError(UserError):
    pass


# ---------------------------------------------------------------- analyse
def probe_media(tools: dict, path) -> dict:
    info = {"duration": None, "width": None, "height": None, "vcodec": None, "acodec": None, "has_video": False,
            "has_audio": False, "attached_pic": False, "fps": None, "channels": None, "audio_streams": 0}
    ffprobe = tools.get("ffprobe")
    if ffprobe:
        try:
            r = subprocess.run([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                                str(path)], capture_output=True, timeout=60, creationflags=NO_WINDOW)
            data = json.loads(r.stdout.decode("utf-8", "replace") or "{}")
        except Exception:
            data = {}
        try:
            info["duration"] = float(data.get("format", {}).get("duration"))
        except (TypeError, ValueError):
            pass
        for s in data.get("streams", []):
            kind = s.get("codec_type")
            if kind == "video":
                if (s.get("disposition") or {}).get("attached_pic"):
                    info["attached_pic"] = True
                    continue
                if info["has_video"]:
                    continue
                info["has_video"] = True
                info["vcodec"] = s.get("codec_name")
                info["hdr"] = s.get("color_transfer") in ("smpte2084", "arib-std-b67")
                w, h = s.get("width"), s.get("height")
                rot = 0
                for sd in s.get("side_data_list") or []:
                    if "rotation" in sd:
                        try:
                            rot = int(float(sd["rotation"]))
                        except (TypeError, ValueError):
                            pass
                if not rot:
                    try:
                        rot = int(float((s.get("tags") or {}).get("rotate", 0) or 0))
                    except (TypeError, ValueError):
                        rot = 0
                if w and h and abs(rot) % 180 == 90:
                    w, h = h, w
                info["width"], info["height"] = w, h
                fr = s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/0"
                try:
                    n, d = fr.split("/")
                    info["fps"] = round(float(n) / float(d), 3) if float(d) else None
                except (ValueError, ZeroDivisionError):
                    pass
                if info["duration"] is None:
                    try:
                        info["duration"] = float(s.get("duration"))
                    except (TypeError, ValueError):
                        pass
            elif kind == "audio":
                info["audio_streams"] += 1
                if not info["has_audio"]:
                    info["has_audio"] = True
                    info["acodec"] = s.get("codec_name")
                    info["channels"] = s.get("channels")
                    info["layout_unknown"] = s.get("channel_layout") in (None, "", "unknown")
                    if info["duration"] is None:
                        try:
                            info["duration"] = float(s.get("duration"))
                        except (TypeError, ValueError):
                            pass
        return info
    ffmpeg = tools.get("ffmpeg")
    if not ffmpeg:
        return info
    try:
        err = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, timeout=60,
                             creationflags=NO_WINDOW).stderr.decode("utf-8", "replace")
    except Exception:
        return info
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", err)
    if m:
        info["duration"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    for line in err.splitlines():
        if "Video:" in line and not info["has_video"]:
            if "attached pic" in line:
                info["attached_pic"] = True
                continue
            info["has_video"] = True
            mm = re.search(r"Video: (\w+)", line)
            info["vcodec"] = mm and mm[1]
            mm = re.search(r", (\d{2,5})x(\d{2,5})", line)
            if mm:
                info["width"], info["height"] = int(mm[1]), int(mm[2])
            mm = re.search(r"([\d.]+) fps", line)
            if mm:
                info["fps"] = float(mm[1])
        elif "Audio:" in line:
            info["audio_streams"] += 1
            if not info["has_audio"]:
                info["has_audio"] = True
                mm = re.search(r"Audio: (\w+)", line)
                info["acodec"] = mm and mm[1]
                mm = re.search(r", (\d+) channels", line)          # « 2 channels » = disposition inconnue
                if mm:
                    info["channels"], info["layout_unknown"] = int(mm[1]), True
    return info


# ---------------------------------------------------------------- exécution
def run_ffmpeg(ctx, args, duration=None, msg=None, span=(0.0, 1.0), timeout=None, cwd=None) -> None:
    ffmpeg = ctx.tools.get("ffmpeg")
    if not ffmpeg:
        raise UserError("FFmpeg est introuvable.")
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-y", "-loglevel", "error", "-progress", "pipe:1", "-nostats",
           *[str(a) for a in args]]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NO_WINDOW,
                            cwd=str(cwd) if cwd else None)
    errors: deque = deque(maxlen=40)

    def drain():
        for raw in proc.stderr:
            errors.append(raw.decode("utf-8", "replace").rstrip())

    t = threading.Thread(target=drain, daemon=True)
    t.start()
    a, b = span
    ctx.progress(a, msg)
    for raw in proc.stdout:
        line = raw.decode("utf-8", "replace").strip()
        if duration and line.startswith(("out_time_us=", "out_time_ms=")):
            v = line.split("=", 1)[1]
            if v.lstrip("-").isdigit():
                frac = max(0.0, min(1.0, int(v) / 1e6 / duration))
                ctx.progress(a + (b - a) * frac)
        elif line == "progress=end":
            ctx.progress(b)
    rc = proc.wait(timeout)
    t.join(2)
    if rc != 0:
        lines = [l for l in errors if l.strip()]
        detail = "\n".join(lines[-6:])[-700:]
        raise FFmpegError("FFmpeg a échoué : " + (detail or f"code {rc}"))


def _readable(info):
    if not info["has_video"] and not info["has_audio"] and not info["attached_pic"]:
        raise FinalError("Fichier illisible ou corrompu : aucun flux audio ou vidéo reconnu.")


def _trim(opts, info):
    start = parse_time(opts.get("start"))
    end = parse_time(opts.get("end"))
    total = info.get("duration")
    if start and total and start >= total:
        raise UserError("Le début est après la fin du fichier.")
    if end is not None and start is not None and end <= start:
        raise UserError("La fin doit être après le début.")
    head = ["-ss", fmt_time(start)] if start else []
    tail = ["-t", fmt_time(end - (start or 0))] if end is not None else []
    if end is not None:
        dur = end - (start or 0)
        if total:
            dur = min(dur, total - (start or 0))
    else:
        dur = (total - (start or 0)) if total else None
    return head, tail, dur


EVEN = "scale=trunc(iw/2)*2:trunc(ih/2)*2"
CRF = {"high": 18, "medium": 23, "low": 28}
GPU_Q = {"nvenc": {"high": 19, "medium": 24, "low": 30}, "qsv": {"high": 20, "medium": 25, "low": 31},
         "amf": {"high": 20, "medium": 25, "low": 31}}
VP9 = {"high": 28, "medium": 33, "low": 40}
QSCALE = {"high": 3, "medium": 5, "low": 8}
THEORA = {"high": 8, "medium": 6, "low": 4}
H264_TARGETS = {"mp4", "m4v", "mov", "mkv", "flv", "ts", "3gp"}
MPEG_RATES = [(24000 / 1001, "24000/1001"), (24, "24"), (25, "25"), (30000 / 1001, "30000/1001"), (30, "30"),
              (50, "50"), (60000 / 1001, "60000/1001"), (60, "60")]

COPY_RULES = {
    "mp4": ({"h264", "hevc", "av1", "mpeg4"}, {"aac", "mp3", "ac3", "eac3", "alac"}),
    "m4v": ({"h264", "hevc", "mpeg4"}, {"aac", "ac3", "alac"}),
    "mov": ({"h264", "hevc", "mpeg4", "prores", "mjpeg"}, {"aac", "mp3", "alac", "pcm_s16le", "pcm_s24le", "ac3"}),
    "mkv": (None, None),
    "webm": ({"vp8", "vp9", "av1"}, {"opus", "vorbis"}),
    "flv": ({"h264", "flv1"}, {"aac", "mp3"}),
    "ts": ({"h264", "hevc", "mpeg2video", "mpeg1video"}, {"aac", "mp3", "ac3", "mp2", "eac3"}),
    "mpg": ({"mpeg1video", "mpeg2video"}, {"mp2", "mp3", "ac3"}),
    "3gp": ({"h264", "h263", "mpeg4"}, {"aac", "amr_nb", "amr_wb"}),
    "ogv": ({"theora", "vp8"}, {"vorbis", "opus", "flac"}),
    "avi": ({"mpeg4", "msmpeg4v3", "mjpeg"}, {"mp3", "ac3", "pcm_s16le"}),
    "wmv": ({"wmv1", "wmv2", "wmv3", "vc1"}, {"wmav1", "wmav2"}),
}
CONTAINER = {"mp4": ["-movflags", "+faststart"], "m4v": ["-f", "mp4", "-movflags", "+faststart"],
             "mov": ["-movflags", "+faststart"], "3gp": ["-movflags", "+faststart"], "mpg": ["-f", "vob"]}


def _mpeg_rate(fps):
    if not fps:
        return "25"
    return min(MPEG_RATES, key=lambda r: abs(r[0] - fps))[1]


def venc(t, q, gpu=None, fps=None, alpha=False):
    if t in H264_TARGETS:
        if gpu and t != "3gp":
            args = gpu_args(gpu, GPU_Q[gpu][q]) + ["-pix_fmt", "yuv420p"]
        else:
            args = ["-c:v", "libx264", "-preset", "medium", "-crf", str(CRF[q]), "-pix_fmt", "yuv420p"]
        if t == "3gp":
            args += ["-profile:v", "baseline"]
        return args
    if t == "webm":
        return ["-c:v", "libvpx-vp9", "-crf", str(VP9[q]), "-b:v", "0", "-row-mt", "1", "-deadline", "good",
                "-cpu-used", "4", "-pix_fmt", "yuva420p" if alpha else "yuv420p"]
    if t == "avi":
        return ["-c:v", "mpeg4", "-vtag", "XVID", "-q:v", str(QSCALE[q]), "-pix_fmt", "yuv420p"]
    if t == "wmv":
        return ["-c:v", "wmv2", "-q:v", str(QSCALE[q]), "-pix_fmt", "yuv420p"]
    if t == "mpg":
        return ["-c:v", "mpeg2video", "-q:v", str(QSCALE[q]), "-pix_fmt", "yuv420p", "-r", _mpeg_rate(fps)]
    if t == "ogv":
        return ["-c:v", "libtheora", "-q:v", str(THEORA[q]), "-pix_fmt", "yuv420p"]
    raise UserError(f"Format vidéo non géré : {t}")


def aenc(t, q):
    br = {"high": 192, "medium": 160, "low": 128}[q]
    if t == "webm":
        return ["-c:a", "libopus", "-b:a", f"{ {'high': 160, 'medium': 128, 'low': 96}[q] }k"]
    if t == "ogv":
        return ["-c:a", "libvorbis", "-q:a", {"high": "6", "medium": "4", "low": "2"}[q]]
    if t == "avi":
        return ["-c:a", "libmp3lame", "-b:a", f"{br}k"]
    if t == "wmv":
        return ["-c:a", "wmav2", "-b:a", f"{br}k", "-ar", "44100"]
    if t == "mpg":
        return ["-c:a", "mp2", "-b:a", f"{br}k", "-ar", "48000"]
    if t in ("3gp", "flv"):
        return ["-c:a", "aac", "-b:a", "128k" if t == "3gp" else f"{br}k", "-ar", "44100"]
    return ["-c:a", "aac", "-b:a", f"{br}k"]


def _scale(info, res):
    if res in (None, "", "orig"):
        return None
    target = int(res)
    w, h = info.get("width"), info.get("height")
    if w and h:
        if min(w, h) <= target:
            return None
        return f"scale=-2:{target}" if w >= h else f"scale={target}:-2"
    return f"scale=-2:{target}"


# ---------------------------------------------------------------- vidéo -> vidéo
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
SUB_SIZE = {"small": 14, "medium": 18, "large": 24}
RATIOS = {"1:1": 1.0, "9:16": 9 / 16, "16:9": 16 / 9, "4:5": 4 / 5, "4:3": 4 / 3}


def _atempo(speed: float) -> list[str]:
    out, s = [], speed
    while s > 2.0:
        out.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        out.append("atempo=0.5")
        s /= 0.5
    out.append(f"atempo={s:.4f}")
    return out


STD_LAYOUT = {1: "mono", 2: "stereo", 3: "2.1", 4: "quad", 5: "5.0", 6: "5.1", 7: "6.1", 8: "7.1"}


def layout_fix(info) -> list[str]:
    """Piste sans disposition de canaux (ex. Speex « 2 channels ») : l'encodeur AAC la refuse, on la nomme."""
    lay = STD_LAYOUT.get(info.get("channels") or 0)
    return [f"channelmap=channel_layout={lay}"] if info.get("layout_unknown") and lay else []


def audio_filters(o, duration=None) -> list[str]:
    af = []
    speed = float(o.get("speed") or 1)
    if o.get("trim_silence"):
        cut = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.25"
        af += [cut, "areverse", cut, "areverse"]
    if speed != 1:
        af += _atempo(speed)
    if o.get("normalize"):
        af.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    fade = float(o.get("fade") or 0)
    if fade:
        af += [f"afade=t=in:d={fade}", "areverse", f"afade=t=in:d={fade}", "areverse"]
    return af


def _autocrop(ctx, src, head) -> str | None:
    ffmpeg = ctx.tools["ffmpeg"]
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", *head, "-i", str(src), "-t", "60", "-vf", "cropdetect=24:2:0",
                            "-f", "null", "-"], capture_output=True, timeout=300, creationflags=NO_WINDOW)
    except Exception:
        return None
    found = re.findall(r"crop=(\d+:\d+:\d+:\d+)", r.stderr.decode("utf-8", "replace"))
    if not found:
        return None
    best = max(set(found[len(found) // 3:] or found), key=found.count)
    return f"crop={best}"


def _crop(ctx, src, head, info, mode) -> str | None:
    if mode in (None, "", "none"):
        return None
    if mode == "auto":
        return _autocrop(ctx, src, head)
    w, h = info.get("width"), info.get("height")
    r = RATIOS.get(mode)
    if not (w and h and r):
        return None
    cw, ch = min(w, round(h * r)), min(h, round(w / r))
    return f"crop={cw - cw % 2}:{ch - ch % 2}"


ROTATE = {"cw": "transpose=1", "ccw": "transpose=2", "180": "transpose=1,transpose=1", "hflip": "hflip",
          "vflip": "vflip"}


def _subs_track(ctx, src, sfmt):
    """Sous-titres automatiques : transcription Whisper vers ctx.tmp/sous.srt."""
    from .transcription import transcribe
    saved, span = dict(ctx.opts), ctx._span
    a, b = span
    ctx._span = (a, a + (b - a) * 0.45)
    ctx.opts = {**saved, "subs_mode": "transcribe"}
    try:
        transcribe(ctx, src, sfmt, ctx.tmp / "sous.srt", "srt")
    finally:
        ctx.opts, ctx._span = saved, (a + (b - a) * 0.45, b)
    return ctx.tmp / "sous.srt"


def _two_pass_bitrate(info, dur, target_mb, audio_kbps):
    total_kbps = target_mb * 8 * 1024 * 0.96 / max(dur or 1, 1)
    return max(60, int(total_kbps - audio_kbps))


def video_to_video(ctx, src, sfmt, dst, t, subs_file=None, subs_mode=None):
    o = ctx.opts
    info = probe_media(ctx.tools, src)
    _readable(info)
    if not info["has_video"]:
        raise FinalError("Aucune piste vidéo dans ce fichier.")
    head, tail, dur = _trim(o, info)
    quality = o.get("v_quality") or "orig"
    q = "high" if quality == "orig" else quality
    mute = bool(o.get("mute"))
    speed = float(o.get("speed") or 1)
    target_mb = int(o.get("target_mb") or 0)
    auto_subs = o.get("auto_subs") or "no"
    if subs_file is None and auto_subs != "no":
        subs_file, subs_mode = _subs_track(ctx, src, sfmt), auto_subs
    burn = subs_file is not None and subs_mode == "burn"
    soft = subs_file is not None and subs_mode == "soft"
    out_dur = (dur / speed) if dur else None

    vf = []
    crop = _crop(ctx, src, head, info, o.get("crop"))
    if crop:
        vf.append(crop)
    if ROTATE.get(o.get("rotate") or ""):
        vf.append(ROTATE[o["rotate"]])
    if o.get("stabilize"):
        ctx.progress(None, "Analyse des tremblements…")
        run_ffmpeg(ctx, [*head, "-i", src, *tail, "-vf", "vidstabdetect=shakiness=6:accuracy=15:result=mouvements.trf",
                         "-f", "null", "-"], dur, "Analyse des tremblements…", cwd=ctx.tmp)
        vf.append("vidstabtransform=input=mouvements.trf:zoom=0:smoothing=12,unsharp=5:5:0.6:3:3:0.3")
    if speed != 1:
        vf.append(f"setpts=PTS/{speed}")
    res = o.get("v_res")
    if target_mb and out_dur and (not res or res == "orig"):
        kbps = _two_pass_bitrate(info, out_dur, target_mb, 96)
        short = min(info.get("width") or 1920, info.get("height") or 1080)
        for limit, need in ((1080, 2500), (720, 1200), (480, 600), (360, 300), (240, 0)):
            if short > limit and kbps < need:
                res = str(limit)
            elif short > limit:
                break
    scale = _scale(info, res)
    if info.get("hdr"):
        vf.append(TONEMAP)
    if scale:
        vf.append(scale)
    if burn:
        size = SUB_SIZE.get(o.get("subs_style") or "medium", 18)
        vf.append(f"subtitles=sous_incrustes.srt:force_style='FontName=Arial,FontSize={size},Outline=2,"
                  f"Shadow=0,BorderStyle=1,MarginV=24'")
    af = [] if mute else audio_filters(o, dur)

    vrule, arule = COPY_RULES.get(t, (set(), set()))
    plain = quality == "orig" and not vf and not target_mb
    can_vcopy = plain and (vrule is None or info["vcodec"] in vrule)
    can_acopy = quality == "orig" and not af and not target_mb and (arule is None or info["acodec"] in arule)
    multi_audio = t in ("mkv", "mp4", "mov", "webm", "ts", "m4v")
    if burn:
        Path(ctx.tmp / "sous_incrustes.srt").write_bytes(Path(subs_file).read_bytes())

    def common_tail():
        a = []
        if soft:
            a += ["-map", "1:0", "-c:s", {"mkv": "srt", "webm": "webvtt"}.get(t, "mov_text"),
                  "-metadata:s:s:0", "language=fre"]
        else:
            a += ["-sn"]
        return a + ["-dn", "-map_metadata", "0", *CONTAINER.get(t, [])]

    def inputs():
        a = [*head, "-i", src]
        if soft:
            a += ["-i", subs_file]
        return a + tail

    def build(vcopy, acopy, gpu, extra_v=None, out=None, audio=True):
        a = [*inputs(), "-map", "0:v:0"]
        if audio and not mute and info["has_audio"]:
            a += ["-map", "0:a?" if multi_audio else "0:a:0"]
        if vcopy:
            a += ["-c:v", "copy"]
            if t in ("mp4", "mov", "m4v") and info["vcodec"] == "hevc":
                a += ["-tag:v", "hvc1"]
        else:
            a += extra_v or venc(t, q, gpu, info.get("fps"))
            a += ["-vf", ",".join(vf + ["format=yuv420p" if vf else EVEN])]
        if not audio or mute or not info["has_audio"]:
            a += ["-an"]
        elif acopy:
            a += ["-c:a", "copy"]
        else:
            a += aenc(t, q) if not target_mb else (["-c:a", "libopus", "-b:a", "96k"] if t == "webm"
                                                     else ["-c:a", "aac", "-b:a", "96k"])
            chain = (layout_fix(info) if info["audio_streams"] <= 1 else []) + af
            if chain:
                a += ["-af", ",".join(chain)]
        return a + common_tail() + [out or dst]

    if target_mb:                                   # deux passes : taille finale maîtrisée
        kbps = _two_pass_bitrate(info, out_dur, target_mb, 96 if info["has_audio"] and not mute else 0)
        if t == "webm":
            v = ["-c:v", "libvpx-vp9", "-b:v", f"{kbps}k", "-row-mt", "1", "-deadline", "good", "-cpu-used", "4",
                 "-pix_fmt", "yuv420p"]
        elif t in H264_TARGETS:
            v = ["-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p"]
        else:
            v = venc(t, "medium", None, info.get("fps"))[:2] + ["-b:v", f"{kbps}k", "-pix_fmt", "yuv420p"]
        if t == "webm" or t in H264_TARGETS:
            log = ctx.tmp / "passe"
            first = [*head, "-i", src, *tail, "-map", "0:v:0", *v, "-pass", "1", "-passlogfile", log,
                     "-vf", ",".join(vf + ["format=yuv420p" if vf else EVEN]), "-an", "-sn", "-f", "null", "NUL"]
            run_ffmpeg(ctx, first, out_dur, "Compression (passe 1/2)…", (0.0, 0.5), cwd=ctx.tmp)
            run_ffmpeg(ctx, build(False, False, None, v + ["-pass", "2", "-passlogfile", log]), out_dur,
                       "Compression (passe 2/2)…", (0.5, 1.0), cwd=ctx.tmp)
        else:
            run_ffmpeg(ctx, build(False, False, None, v), out_dur, "Compression…", cwd=ctx.tmp)
        return [dst]

    gpu = ctx.gpu if t in H264_TARGETS and t != "3gp" else None
    attempts = []
    if can_vcopy or can_acopy:
        attempts.append((can_vcopy, can_acopy, gpu))
    attempts.append((False, False, gpu))
    if gpu:
        attempts.append((False, False, None))
    last_error = None
    for vcopy, acopy, g in attempts:
        msg = "Remuxage rapide (sans réencodage)…" if vcopy else (
            f"Encodage vidéo ({'GPU' if g else 'processeur'})…")
        try:
            run_ffmpeg(ctx, build(vcopy, acopy, g), out_dur, msg, cwd=ctx.tmp)
            return [dst]
        except FFmpegError as e:
            last_error = e
    raise last_error


def add_subtitles(ctx, items, out_dir: Path) -> list[Path]:
    """Assemblage : une vidéo + un fichier de sous-titres -> vidéo sous-titrée."""
    from .subs import to_srt
    from .. import formats as F
    video = next((x for x in items if x[1] in F.VIDEO_IN), None)
    subs = next((x for x in items if x[1] in F.SUBS_IN), None)
    if not video or not subs:
        raise FinalError("Ajoutez une vidéo et un fichier de sous-titres.")
    srt = to_srt(subs[0], subs[1], ctx.tmp / "sous_source.srt")
    mode = ctx.opts.get("subs_burn") or "burn"
    ext = "mkv" if (mode == "soft" and Path(video[2]).suffix.lower() == ".mkv") else "mp4"
    ctx.stem = Path(video[2]).stem
    dst = ctx.stage_dir() / f"{ctx.stem} (sous-titres).{ext}"
    return video_to_video(ctx, Path(video[0]), video[1], dst, ext, subs_file=srt, subs_mode=mode)


def concat(ctx, items, out_dir: Path) -> list[Path]:
    """Assemblage : plusieurs vidéos ou audios bout à bout."""
    infos = [probe_media(ctx.tools, p) for p, _, _ in items]
    for (p, _, name), info in zip(items, infos):
        if not info["has_video"] and not info["has_audio"]:
            raise FinalError(f"« {name} » est illisible.")
    has_video = any(i["has_video"] for i in infos)
    fmt = ctx.opts.get("concat_fmt") or "auto"
    if fmt == "auto":
        fmt = "mp4" if has_video else "mp3"
    video_out = fmt in ("mp4", "mkv")
    dst = ctx.stage_dir() / f"{ctx.stem} (fusion).{fmt}"
    ref = next((i for i in infos if i["has_video"]), None)
    W, H = ((ref["width"] or 1280) // 2 * 2, (ref["height"] or 720) // 2 * 2) if ref else (1280, 720)
    args, graph, n = [], [], 0
    total = 0.0
    for idx, ((p, _, _), info) in enumerate(zip(items, infos)):
        args += ["-i", str(p)]
    extra = len(items)
    for idx, info in enumerate(infos):
        d = info.get("duration") or 0
        total += d
        if video_out:
            if info["has_video"]:
                graph.append(f"[{idx}:v:0]scale={W}:{H}:force_original_aspect_ratio=decrease,"
                             f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{idx}]")
            else:
                args += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", f"color=c=black:s={W}x{H}:r=30"]
                graph.append(f"[{extra}:v]format=yuv420p,setsar=1[v{idx}]")
                extra += 1
        if info["has_audio"]:
            fix = "".join(f + "," for f in layout_fix(info))
            graph.append(f"[{idx}:a:0]{fix}aresample=48000,aformat=channel_layouts=stereo[a{idx}]")
        else:
            args += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            graph.append(f"[{extra}:a]anull[a{idx}]")
            extra += 1
    pairs = "".join((f"[v{i}][a{i}]" if video_out else f"[a{i}]") for i in range(len(items)))
    graph.append(f"{pairs}concat=n={len(items)}:v={1 if video_out else 0}:a=1" + ("[v][a]" if video_out else "[a]"))
    args += ["-filter_complex", ";".join(graph)]
    if video_out:
        args += ["-map", "[v]", "-map", "[a]", *venc(fmt, "high", ctx.gpu, 30), *aenc(fmt, "high"),
                 *CONTAINER.get(fmt, [])]
    else:
        args += ["-map", "[a]", *_acodec(fmt, 192, None)]
    run_ffmpeg(ctx, args + [dst], total or None, "Fusion…")
    return [dst]


# ---------------------------------------------------------------- vers animation
def _anim_chain(fps, width, info):
    chain = []
    if fps and fps != "orig":
        chain.append(f"fps={fps}")
    if width and width != "orig":
        w = int(width)
        if not info.get("width") or w < info["width"]:
            chain.append(f"scale={w}:-1:flags=lanczos")
    return chain


def _make_gif(ctx, src, dst, chain, head, tail, dur, stats="diff", dither="bayer:bayer_scale=5", loop=True,
              input_args=()):
    base = ",".join(chain) if chain else "null"
    palette = ctx.tmp / "palette.png"
    run_ffmpeg(ctx, [*input_args, *head, "-i", src, *tail, "-vf", f"{base},palettegen=stats_mode={stats}",
                     "-frames:v", "1", "-update", "1", palette], dur, "Analyse des couleurs…", (0.0, 0.3))
    run_ffmpeg(ctx, [*input_args, *head, "-i", src, *tail, "-i", palette, "-lavfi",
                     f"{base}[x];[x][1:v]paletteuse=dither={dither}:diff_mode=rectangle",
                     "-loop", "0" if loop else "-1", dst], dur, "Création du GIF…", (0.3, 1.0))


def video_to_anim(ctx, src, sfmt, dst, t):
    o = ctx.opts
    info = probe_media(ctx.tools, src)
    _readable(info)
    if not info["has_video"]:
        raise FinalError("Aucune piste vidéo dans ce fichier.")
    head, tail, dur = _trim(o, info)
    chain = _anim_chain(o.get("fps", "15"), o.get("anim_width", "480"), info)
    if t == "gif":
        _make_gif(ctx, src, dst, chain, head, tail, dur)
    elif t == "apng":
        vf = ["-vf", ",".join(chain)] if chain else []
        run_ffmpeg(ctx, [*head, "-i", src, *tail, *vf, "-an", "-plays", "0", "-f", "apng", dst], dur,
                   "Création de l'APNG…")
    else:
        vf = ["-vf", ",".join(chain)] if chain else []
        run_ffmpeg(ctx, [*head, "-i", src, *tail, *vf, "-an", "-c:v", "libwebp_anim", "-lossless", "0",
                         "-q:v", "75", "-loop", "0", dst], dur, "Création du WEBP animé…")
    return [dst]


def _decodable_anim(ctx, src, sfmt):
    """FFmpeg ne lit pas les WebP animés : on les convertit d'abord en APNG avec Pillow."""
    if sfmt != "webp_anim":
        return src
    from PIL import Image, ImageSequence
    img = Image.open(src)
    frames, durations = [], []
    for frame in ImageSequence.Iterator(img):
        frames.append(frame.convert("RGBA"))
        durations.append(max(10, int(frame.info.get("duration", img.info.get("duration", 100)) or 100)))
    out = ctx.tmp / "anim_source.png"
    frames[0].save(out, "PNG", save_all=True, append_images=frames[1:], duration=durations, loop=0,
                   disposal=0, blend=0)
    return out


def anim_to_anim(ctx, src, sfmt, dst, t):
    o = ctx.opts
    src = _decodable_anim(ctx, src, sfmt)
    info = probe_media(ctx.tools, src)
    _readable(info)
    chain = _anim_chain(o.get("fps", "orig"), o.get("anim_width", "orig"), info)
    dur = info.get("duration")
    if t == "gif":
        _make_gif(ctx, src, dst, chain, [], [], dur, stats="full", dither="sierra2_4a")
    elif t == "apng":
        vf = ["-vf", ",".join(chain)] if chain else []
        run_ffmpeg(ctx, ["-i", src, *vf, "-plays", "0", "-f", "apng", dst], dur, "Création de l'APNG…")
    else:
        vf = ["-vf", ",".join(chain)] if chain else []
        run_ffmpeg(ctx, ["-i", src, *vf, "-c:v", "libwebp_anim", "-lossless", "0", "-q:v", "80", "-loop", "0",
                         dst], dur, "Création du WEBP animé…")
    return [dst]


def anim_to_video(ctx, src, sfmt, dst, t):
    src = _decodable_anim(ctx, src, sfmt)
    info = probe_media(ctx.tools, src)
    _readable(info)
    scale = _scale(info, ctx.opts.get("v_res"))
    alpha = t == "webm"
    vf = (scale + "," if scale else "") + EVEN
    args = ["-i", src, *venc(t, "high", None, info.get("fps") or 25, alpha=alpha), "-vf", vf, "-an",
            *CONTAINER.get(t, []), dst]
    run_ffmpeg(ctx, args, info.get("duration"), "Encodage vidéo…")
    return [dst]


# ---------------------------------------------------------------- vers audio
def _acodec(t, br, info):
    if t == "mp3":
        return ["-c:a", "libmp3lame", "-b:a", f"{br}k"]
    if t == "wav":
        return ["-c:a", "pcm_s16le"]
    if t == "flac":
        return ["-c:a", "flac"]
    if t == "ogg":   # qualité VBR : valable quelle que soit la fréquence d'échantillonnage
        q = {320: 9, 256: 8, 192: 6, 160: 5, 128: 4, 96: 2, 64: 0}.get(br, 6)
        return ["-c:a", "libvorbis", "-q:a", str(q)]
    if t in ("opus", "weba"):
        return ["-c:a", "libopus", "-b:a", f"{min(br, 256)}k"] + (["-f", "webm"] if t == "weba" else [])
    if t in ("m4a", "m4b", "m4r"):
        return ["-c:a", "aac", "-b:a", f"{br}k"] + (["-f", "ipod"] if t != "m4a" else [])
    if t == "aac":
        return ["-c:a", "aac", "-b:a", f"{br}k", "-f", "adts"]
    if t == "aiff":
        return ["-c:a", "pcm_s16be"]
    if t == "wma":
        return ["-c:a", "wmav2", "-b:a", f"{min(br, 192)}k", "-ar", "44100"]
    if t == "alac":
        return ["-c:a", "alac", "-f", "ipod"]
    if t == "ac3":
        return ["-c:a", "ac3", "-b:a", f"{max(br, 96)}k"]
    if t == "mp2":
        return ["-c:a", "mp2", "-b:a", f"{min(br, 384)}k"]
    if t == "amr":
        return ["-c:a", "libopencore_amrnb", "-ar", "8000", "-ac", "1", "-b:a", "12.2k"]
    if t == "wv":
        return ["-c:a", "wavpack"]
    if t == "mka":
        return ["-c:a", "copy"]
    if t == "caf":
        return ["-c:a", "alac"]
    if t == "au":
        return ["-c:a", "pcm_s16be"]
    if t == "spx":
        return ["-c:a", "libspeex", "-ar", "32000", "-f", "ogg"]
    if t == "tta":
        return ["-c:a", "tta"]
    raise UserError(f"Format audio non géré : {t}")


FIXED_RATE = {"amr", "spx", "wma"}
OPUS_RATES = {"48000", "24000", "16000", "12000", "8000"}


def to_audio(ctx, src, sfmt, dst, t):
    o = ctx.opts
    info = probe_media(ctx.tools, src)
    _readable(info)
    if not info["has_audio"]:
        raise FinalError("Ce fichier ne contient aucune piste audio.")
    head, tail, dur = _trim(o, info)
    if t == "m4r" and not tail:
        tail = ["-t", "40"]
        dur = min(dur or 40, 40)
    br = int(o.get("a_bitrate") or 192)
    channels = o.get("a_channels", "auto")
    rate = o.get("a_rate", "auto")
    if t == "mp2" and rate not in ("48000", "44100", "32000"):
        rate = "44100"          # MP2 : fréquences basses incompatibles avec les débits usuels
    cover_ok = info["attached_pic"] and t in ("mp3", "flac", "m4a", "alac", "m4b")
    af = audio_filters(o, dur)
    if af and dur:
        dur = dur / float(o.get("speed") or 1)

    def build(cover, codec):
        a = [*head, "-i", src, *tail, "-map", "0:a:0"]
        if cover:
            a += ["-map", "0:v:0", "-c:v", "copy", "-disposition:v:0", "attached_pic"]
        else:
            a += ["-vn"]
        a += ["-sn", "-dn", *codec]
        chain = ([] if "copy" in codec else layout_fix(info)) + af
        if chain:
            a += ["-af", ",".join(chain)]
        if channels in ("1", "2") and t not in ("amr",):
            a += ["-ac", channels]
        if rate != "auto" and t not in FIXED_RATE and (t not in ("opus", "weba") or rate in OPUS_RATES):
            a += ["-ar", rate]
        if t == "mp3":
            a += ["-id3v2_version", "3"]
        if t in ("m4a", "m4b", "m4r", "alac"):
            a += ["-movflags", "+faststart"]
        return a + [dst]

    attempts = []
    codec = _acodec(t, br, info)
    if af and t == "mka":                        # la copie directe est incompatible avec les filtres
        codec = ["-c:a", "libopus", "-b:a", f"{min(br, 256)}k"]
    if cover_ok:
        attempts.append(build(True, codec))
    attempts.append(build(False, codec))
    if t == "mka":
        attempts.append(build(False, ["-c:a", "libopus", "-b:a", f"{min(br, 256)}k"]))
    last = None
    for args in attempts:
        try:
            run_ffmpeg(ctx, args, dur, "Conversion audio…")
            return [dst]
        except FFmpegError as e:
            last = e
    raise last


# ---------------------------------------------------------------- captures, spectres, vidéos fixes
def video_frame(ctx, src, sfmt, dst, t):
    info = probe_media(ctx.tools, src)
    _readable(info)
    at = parse_time(ctx.opts.get("frame_at"))
    if at is None:
        at = (info.get("duration") or 0) * 0.1
    if info.get("duration") and at >= info["duration"]:
        at = max(0.0, info["duration"] - 0.1)
    run_ffmpeg(ctx, ["-ss", fmt_time(at), "-i", src, "-frames:v", "1", "-update", "1", "-an", dst], None,
               "Capture de l'image…")
    if not Path(dst).exists():
        run_ffmpeg(ctx, ["-i", src, "-frames:v", "1", "-update", "1", "-an", dst], None, "Capture de l'image…")
    return [dst]


def spectrogram(ctx, src, sfmt, dst, t):
    info = probe_media(ctx.tools, src)
    _readable(info)
    if not info["has_audio"]:
        raise FinalError("Ce fichier ne contient aucune piste audio.")
    run_ffmpeg(ctx, ["-i", src, "-lavfi", "showspectrumpic=s=1600x800:legend=1:color=magma:scale=log:fscale=log",
                     "-frames:v", "1", "-update", "1", dst], None, "Calcul du spectrogramme…")
    return [dst]


RES_SIZE = {"2160": (3840, 2160), "1440": (2560, 1440), "1080": (1920, 1080), "720": (1280, 720),
            "480": (854, 480), "360": (640, 360), "240": (426, 240)}


def audio_to_video(ctx, src, sfmt, dst, t):
    o = ctx.opts
    info = probe_media(ctx.tools, src)
    _readable(info)
    if not info["has_audio"]:
        raise FinalError("Ce fichier ne contient aucune piste audio.")
    head, tail, dur = _trim(o, info)
    W, H = RES_SIZE.get(o.get("v_res") or "720", (1280, 720))
    v = venc(t, "medium", None, 25)
    a = aenc(t, "high")
    limit = ["-t", f"{dur:.3f}"] if dur and not tail else []      # garantit la fin du traitement
    fix = ",".join(layout_fix(info))
    if info["attached_pic"]:
        cover = ctx.tmp / "pochette.png"
        run_ffmpeg(ctx, ["-i", src, "-an", "-map", "0:v:0", "-frames:v", "1", "-update", "1", cover], None,
                   "Extraction de la pochette…")
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
              "format=yuv420p")
        args = ["-loop", "1", "-framerate", "2", "-i", cover, *head, "-i", src, *tail, "-map", "0:v", "-map",
                "1:a", *v, "-vf", vf, "-r", "2" if t != "mpg" else "25", *a, *(["-af", fix] if fix else []), "-shortest", *limit,
                *CONTAINER.get(t, []), dst]
        if "libx264" in v:
            args[args.index("libx264") + 1:args.index("libx264") + 1] = ["-tune", "stillimage"]
    else:
        # asplit : un seul consommateur de la piste audio (sinon FFmpeg peut se bloquer avec -shortest)
        bg_len = f":d={dur:.3f}" if dur else ""
        graph = (f"[0:a]{fix + ',' if fix else ''}asplit=2[a1][a2];color=c=0x14161f:s={W}x{H}:r=25{bg_len}[bg];"
                 f"[a1]showwaves=s={W}x{H // 2}:mode=cline:rate=25:colors=0x8b7cff[w];"
                 f"[bg][w]overlay=0:{H // 4}:shortest=1,format=yuv420p[v]")
        args = [*head, "-i", src, *tail, "-filter_complex", graph, "-map", "[v]", "-map", "[a2]", *v, *a,
                "-shortest", *limit, *CONTAINER.get(t, []), dst]
    run_ffmpeg(ctx, args, dur, "Création de la vidéo…")
    return [dst]


def image_to_video(ctx, src, sfmt, dst, t):
    from .images import to_png
    still = to_png(src, sfmt, ctx.tmp / "image_fixe.png", max_side=3840)
    seconds = max(1, int(ctx.opts.get("still_dur") or 5))
    v = venc(t, "high", None, 25)
    if "libx264" in v:
        v[v.index("libx264") + 1:v.index("libx264") + 1] = ["-tune", "stillimage"]
    args = ["-loop", "1", "-framerate", "25", "-t", str(seconds), "-i", still, *v, "-vf", EVEN + ",format=yuv420p",
            "-r", "25", "-an", *CONTAINER.get(t, []), dst]
    run_ffmpeg(ctx, args, seconds, "Création de la vidéo…")
    return [dst]


def slideshow(ctx, frames: list[Path], dst, seconds: float, t="mp4", size=(1920, 1080)):
    """Assemble des images (déjà numérotées) en diaporama vidéo."""
    W, H = size
    folder = frames[0].parent
    v = venc(t, "high", None, 25)
    if "libx264" in v:
        v[v.index("libx264") + 1:v.index("libx264") + 1] = ["-tune", "stillimage"]
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=white,"
          "format=yuv420p")
    args = ["-framerate", f"1/{seconds}", "-i", folder / "f%05d.png", *v, "-vf", vf, "-r", "25", "-an",
            *CONTAINER.get(t, []), dst]
    run_ffmpeg(ctx, args, seconds * len(frames), "Création du diaporama…", (0.5, 1.0))


def pdf_to_video(ctx, src, sfmt, dst, t):
    import pymupdf
    from ..util import parse_pages
    doc = pymupdf.open(src)
    if doc.needs_pass:
        raise UserError("Ce PDF est protégé par un mot de passe.")
    pages = parse_pages(ctx.opts.get("pages"), doc.page_count)
    folder = ctx.tmp / "pages"
    folder.mkdir(exist_ok=True)
    frames = []
    for i, pno in enumerate(pages):
        page = doc[pno]
        zoom = min(1920 / page.rect.width, 1080 / page.rect.height)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        f = folder / f"f{i + 1:05d}.png"
        pix.save(str(f))
        frames.append(f)
        ctx.progress(0.5 * (i + 1) / len(pages), f"Rendu de la page {pno + 1}…")
    slideshow(ctx, frames, dst, max(1, int(ctx.opts.get("slide_dur") or 5)), t)
    return [dst]
