"""Téléchargement depuis un lien (YouTube, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo…) avec yt-dlp.

Le fichier téléchargé passe ensuite par le graphe de conversion habituel (MP3, MP4, AVI, GIF, SRT…).
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from .. import formats as F
from ..util import FinalError, UserError

AUDIO_SITES = {"soundcloud", "bandcamp", "mixcloud", "audiomack", "jamendo", "radiofrance", "podbean", "spotify"}
SITE_NAMES = {"youtube": "YouTube", "youtubetab": "YouTube", "soundcloud": "SoundCloud", "soundcloudset": "SoundCloud",
              "instagram": "Instagram", "instagramstory": "Instagram", "facebook": "Facebook", "tiktok": "TikTok",
              "twitter": "X (Twitter)", "vimeo": "Vimeo", "dailymotion": "Dailymotion", "twitch": "Twitch",
              "twitchclips": "Twitch", "reddit": "Reddit", "bandcamp": "Bandcamp", "mixcloud": "Mixcloud",
              "pinterest": "Pinterest", "linkedin": "LinkedIn", "threads": "Threads", "bilibili": "Bilibili",
              "kick": "Kick", "rumble": "Rumble", "snapchat": "Snapchat", "tumblr": "Tumblr"}
AUDIO_FIRST = set(F.AUDIO_OUT) | {"txt", "srt", "vtt", "docx"}
MAX_PLAYLIST = 200


def site_name(key: str | None) -> str:
    k = (key or "").lower()
    for prefix, name in SITE_NAMES.items():
        if k == prefix or k.startswith(prefix):
            return name
    return key or "Web"


def base_options(tools: dict, cookies: str | None = None) -> dict:
    opts = {
        "quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True, "consoletitle": False,
        "compat_opts": {"no-certifi"},          # magasin de certificats de Windows (antivirus qui inspectent HTTPS)
        "socket_timeout": 30, "retries": 5, "fragment_retries": 5, "concurrent_fragment_downloads": 4,
        "windowsfilenames": True, "overwrites": True, "continuedl": False,
    }
    from ..tools import find_node
    node = find_node()
    if node:                                    # YouTube exige un moteur JavaScript pour ses signatures
        opts["js_runtimes"] = {Path(node).stem.lower(): {"path": node}}
    if tools.get("ffmpeg"):
        opts["ffmpeg_location"] = str(Path(tools["ffmpeg"]).parent)
    if cookies and cookies != "none":
        opts["cookiesfrombrowser"] = (cookies,)
    return opts


def friendly_error(e: Exception) -> str:
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(e)).replace("ERROR: ", "").strip()
    msg = re.sub(r"^\[[^\]]+\]\s*[^:\s]*:\s*", "", msg)
    low = msg.lower()
    if "unsupported url" in low:
        return "Lien non reconnu : ce site n'est pas pris en charge (ou l'adresse est incomplète)."
    if "drm" in low:
        return "Ce contenu est protégé (DRM) : il ne peut pas être téléchargé."
    if "private" in low:
        return "Ce contenu est privé."
    if "confirm your age" in low or "age-restricted" in low or "inappropriate" in low:
        return ("Contenu soumis à une limite d'âge : une connexion est nécessaire. Dans Réglages, choisissez le "
                "navigateur où vous êtes connecté.")
    if any(w in low for w in ("login", "log in", "sign in", "cookies", "rate-limit", "authentication", "empty media")):
        return ("Ce site demande d'être connecté pour ce contenu. Dans Réglages, choisissez le navigateur où vous "
                "êtes connecté pour utiliser sa session.")
    if "unavailable" in low or "not available" in low or "removed" in low or "404" in low:
        return "Contenu indisponible (supprimé, privé ou bloqué dans votre pays)."
    if any(w in low for w in ("timed out", "getaddrinfo", "connection", "network", "resolve")):
        return "Problème de connexion Internet : réessayez."
    return msg[:400] or "Téléchargement impossible."


def _item(info: dict, fallback_url: str) -> dict:
    key = info.get("extractor_key") or info.get("ie_key") or info.get("extractor")
    formats = info.get("formats") or []
    if formats:
        has_video = any((f.get("vcodec") or "none") != "none" for f in formats)
    else:
        has_video = (key or "").lower() not in AUDIO_SITES and info.get("vcodec") != "none"
    thumb = info.get("thumbnail")
    if not thumb and info.get("thumbnails"):
        thumb = (info["thumbnails"][-1] or {}).get("url")
    return {
        "url": info.get("webpage_url") or info.get("url") or fallback_url,
        "title": (info.get("title") or info.get("id") or "video").strip(),
        "duration": info.get("duration"), "width": info.get("width"), "height": info.get("height"),
        "site": site_name(key), "uploader": info.get("uploader") or info.get("channel"),
        "thumbnail": thumb, "has_video": has_video,
        "filesize": info.get("filesize") or info.get("filesize_approx"),
    }


# ---------------------------------------------------------------- Spotify
# Les morceaux Spotify sont chiffrés (DRM) : on lit leurs informations publiques (titre, artistes, durée,
# pochette) puis on cherche le même morceau sur YouTube, dont l'audio est téléchargé et converti.
SPOTIFY_RE = re.compile(r"https?://open\.spotify\.com/(?:intl-[a-z]{2}(?:-[a-z]{2,4})?/)?(?:embed/)?"
                        r"(track|album|playlist)/([A-Za-z0-9]{10,})", re.I)
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/140.0 Safari/537.36")
UNWANTED = ("live", "cover", "karaoke", "instrumental", "remix", "nightcore", "sped up", "slowed", "8d audio",
            "reverb", "acoustic", "piano", "tutorial", "reaction", "1 hour", "1 heure", "10 hours")


def is_spotify(url: str) -> bool:
    return bool(SPOTIFY_RE.match(url or ""))


def _fetch(url: str, timeout: int = 20) -> bytes:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _spotify_entity(kind: str, sid: str) -> dict:
    import json
    try:
        html = _fetch(f"https://open.spotify.com/embed/{kind}/{sid}").decode("utf-8", "replace")
    except Exception as e:
        raise FinalError(f"Spotify est inaccessible : {friendly_error(e)}")
    try:
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
        entity = json.loads(m.group(1))["props"]["pageProps"]["state"]["data"]["entity"]
    except Exception:
        entity = None
    if not entity:
        raise FinalError("Lien Spotify introuvable, privé ou réservé à certains pays.")
    return entity


def _spotify_cover(entity: dict) -> str | None:
    images = (entity.get("visualIdentity") or {}).get("image") or (entity.get("coverArt") or {}).get("sources") or []
    images = [i for i in images if i.get("url")]
    if not images:
        return None
    return max(images, key=lambda i: i.get("maxWidth") or i.get("width") or 0)["url"]


def _spotify_title(artists: str, title: str) -> str:
    return f"{artists} - {title}" if artists else title


def spotify_track(url: str) -> dict:
    """Informations d'un morceau : titre, artistes, durée (s), année, pochette."""
    m = SPOTIFY_RE.match(url)
    if not m or m.group(1).lower() != "track":
        raise FinalError("Ce lien Spotify ne désigne pas un morceau.")
    e = _spotify_entity("track", m.group(2))
    artists = ", ".join(a.get("name", "") for a in e.get("artists") or [] if a.get("name"))
    return {"title": (e.get("title") or e.get("name") or "").strip(), "artists": artists,
            "duration": (e.get("duration") or 0) / 1000 or None,
            "year": ((e.get("releaseDate") or {}).get("isoString") or "")[:4] or None,
            "cover": _spotify_cover(e)}


def spotify_items(url: str) -> list[dict]:
    """Un élément par morceau (titre, album ou playlist publics)."""
    kind, sid = SPOTIFY_RE.match(url).groups()
    kind = kind.lower()
    e = _spotify_entity(kind, sid)
    if kind == "track":
        artists = ", ".join(a.get("name", "") for a in e.get("artists") or [] if a.get("name"))
        title = (e.get("title") or e.get("name") or "").strip()
        tracks = [(sid, title, artists, e.get("duration"), _spotify_cover(e))]
    else:
        cover = _spotify_cover(e) if kind == "album" else None      # une playlist n'a pas la pochette de chaque titre
        tracks = [(t["uri"].split(":")[-1], (t.get("title") or "").strip(), (t.get("subtitle") or "").strip(),
                   t.get("duration"), cover)
                  for t in e.get("trackList") or [] if str(t.get("uri", "")).startswith("spotify:track:")]
    if not tracks:
        raise FinalError("Aucun morceau lisible dans ce lien Spotify.")
    return [{"url": f"https://open.spotify.com/track/{tid}", "title": _spotify_title(artists, title),
             "duration": (dur or 0) / 1000 or None, "width": None, "height": None, "site": "Spotify",
             "uploader": artists or None, "thumbnail": cover, "has_video": False, "filesize": None}
            for tid, title, artists, dur, cover in tracks[:MAX_PLAYLIST]]


def _plain(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _match_score(entry: dict, track: dict) -> float:
    """Plus c'est haut, plus la vidéo YouTube ressemble au morceau Spotify (durée, titre, artiste)."""
    title, chan = _plain(entry.get("title") or ""), _plain(entry.get("channel") or entry.get("uploader") or "")
    want = _plain(track["title"])
    score = 0.0
    if entry.get("duration") and track.get("duration"):
        diff = abs(entry["duration"] - track["duration"])
        score += 30 if diff <= 3 else 18 if diff <= 8 else 6 if diff <= 15 else -40 if diff > 30 else -10
    words = [w for w in want.split() if len(w) > 1] or want.split()
    if words:
        score += 30 * sum(w in title for w in words) / len(words)
    first_artist = _plain(track["artists"].split(",")[0]) if track.get("artists") else ""
    if first_artist and (first_artist in chan or first_artist in title):
        score += 15
    if chan.endswith(" topic"):                  # chaîne « Artiste - Topic » : l'audio officiel
        score += 12
    for bad in UNWANTED:
        if bad in title and bad not in want:
            score -= 25
    return score


def spotify_match(tools: dict, track: dict, cookies: str | None = None) -> str:
    """Adresse de la vidéo YouTube la plus proche du morceau."""
    import yt_dlp
    query = f'{track["artists"].split(",")[0] if track.get("artists") else ""} {track["title"]}'.strip()
    opts = base_options(tools, cookies) | {"extract_flat": True, "skip_download": True, "noplaylist": False}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            found = ydl.extract_info(f"ytsearch8:{query}", download=False) or {}
    except Exception as e:
        raise FinalError(f"Recherche sur YouTube impossible : {friendly_error(e)}")
    entries = [e for e in found.get("entries") or [] if e and e.get("id")]
    if not entries:
        raise FinalError(f"Morceau introuvable sur YouTube : {query}")
    best = max(entries, key=lambda e: _match_score(e, track))
    return best.get("url") or f"https://www.youtube.com/watch?v={best['id']}"


def write_cover(path, cover: bytes) -> None:
    """Pochette (JPEG) intégrée au fichier audio : MP3, M4A, FLAC, OGG, OPUS. Lève une erreur si impossible."""
    import base64
    import mutagen
    ext = Path(path).suffix.lower()
    if ext == ".mp3":
        from mutagen.id3 import APIC, ID3, ID3NoHeaderError
        try:
            id3 = ID3(str(path))
        except ID3NoHeaderError:
            id3 = ID3()
        id3.delall("APIC")
        id3.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover))
        id3.save(str(path), v2_version=3)
    elif ext in (".m4a", ".m4b", ".m4r", ".mp4", ".alac"):
        from mutagen.mp4 import MP4, MP4Cover
        m4 = MP4(str(path))
        m4["covr"] = [MP4Cover(cover, imageformat=MP4Cover.FORMAT_JPEG)]
        m4.save()
    elif ext in (".flac", ".ogg", ".opus"):
        from mutagen.flac import FLAC, Picture
        pic = Picture()
        pic.type, pic.mime, pic.data = 3, "image/jpeg", cover
        if ext == ".flac":
            fl = FLAC(str(path))
            fl.clear_pictures()
            fl.add_picture(pic)
            fl.save()
        else:
            og = mutagen.File(str(path))
            og["metadata_block_picture"] = [base64.b64encode(pic.write()).decode("ascii")]
            og.save()
    else:
        raise UserError("Ce format audio ne peut pas contenir de pochette.")


def write_tags(path, tags: dict, cover: bytes | None = None) -> None:
    """Titre, artiste, album, année et pochette dans le fichier audio final (MP3, M4A, FLAC, OGG, OPUS)."""
    try:
        import mutagen
        f = mutagen.File(str(path), easy=True)
        if f is None:
            return
        if f.tags is None:
            f.add_tags()
        for key in ("title", "artist", "album", "date"):
            if tags.get(key):
                f[key] = [str(tags[key])]
        f.save()
        if cover:
            write_cover(path, cover)
    except Exception:
        pass                                     # les étiquettes sont un bonus : la conversion reste valide


def probe_link(tools: dict, url: str, cookies: str | None = None) -> list[dict]:
    """Analyse un lien : un élément par vidéo (plusieurs pour une playlist)."""
    if is_spotify(url):
        return spotify_items(url)
    if re.match(r"https?://open\.spotify\.com/", url, re.I) and not re.search(r"/(episode|show)/", url):
        raise FinalError("Collez le lien d'un titre, d'un album ou d'une playlist Spotify (bouton Partager → Copier le lien).")
    import yt_dlp
    opts = base_options(tools, cookies) | {"extract_flat": "in_playlist", "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise FinalError(friendly_error(e))
    if not info:
        raise FinalError("Rien à télécharger à cette adresse.")
    if info.get("_type") in ("playlist", "multi_video"):
        entries = [e for e in (info.get("entries") or []) if e][:MAX_PLAYLIST]
        if not entries:
            raise FinalError("Cette liste de lecture est vide.")
        items = []
        for e in entries:
            it = _item(e, e.get("url") or url)
            it["site"] = it["site"] if it["site"] != "Web" else site_name(info.get("extractor_key"))
            items.append(it)
        return items
    return [_item(info, url)]


def download(ctx, url: str, target: str, span=(0.0, 1.0)) -> Path:
    import yt_dlp
    o = ctx.opts
    if is_spotify(url):                          # morceau Spotify : même titre retrouvé sur YouTube
        ctx.progress(span[0], "Lecture du morceau Spotify…")
        track = spotify_track(url)
        ctx.progress(span[0], f"Recherche de « {track['title']} » sur YouTube…")
        url = spotify_match(ctx.tools, track, ctx.spec.get("cookies"))
        ctx.tags = {"title": track["title"], "artist": track["artists"], "date": track.get("year")}
        if track.get("cover"):
            try:
                ctx.cover = _fetch(track["cover"])
            except Exception:
                ctx.cover = None
    audio_only = target in AUDIO_FIRST
    height = o.get("v_res") if o.get("v_res") not in (None, "", "orig") else None
    h = f"[height<={height}]" if height else ""
    mp4_like = target in ("mp4", "m4v", "mov", "3gp")
    if audio_only:
        fmt = "bestaudio/best"
    elif mp4_like:
        fmt = (f"bv*{h}[ext=mp4][vcodec^=avc1]+ba[ext=m4a]/bv*{h}[ext=mp4]+ba[ext=m4a]/b{h}[ext=mp4]/"
               f"bv*{h}+ba/b{h}/bv*+ba/b")
    else:
        fmt = f"bv*{h}+ba/b{h}/bv*+ba/b"
    a, b = span
    state = {"index": 0, "parts": 1}

    def hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            frac = (done / total) if total else 0.0
            weights = [0.85, 0.15] if state["parts"] == 2 else [1.0]
            i = min(state["index"], len(weights) - 1)
            overall = sum(weights[:i]) + weights[i] * min(1.0, frac)
            speed = d.get("speed")
            label = f"Téléchargement… {done / 1e6:.1f} Mo" + (f" / {total / 1e6:.1f} Mo" if total else "")
            if speed:
                label += f" — {speed / 1e6:.1f} Mo/s"
            ctx.progress(a + (b - a) * 0.97 * overall, label.replace(".", ","))
        elif d.get("status") == "finished":
            state["index"] += 1

    def pp_hook(d):
        if d.get("status") == "started" and d.get("postprocessor") in ("Merger", "FFmpegMerger"):
            ctx.progress(a + (b - a) * 0.97, "Assemblage de l'image et du son…")

    opts = base_options(ctx.tools, ctx.spec.get("cookies")) | {
        "format": fmt, "outtmpl": str(ctx.tmp / "telechargement.%(ext)s"),
        "merge_output_format": "mp4" if (mp4_like and not audio_only) else "mkv",
        "progress_hooks": [hook], "postprocessor_hooks": [pp_hook],
    }
    ctx.progress(a, "Connexion au site…")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get("_type") in ("playlist", "multi_video"):
                raise FinalError("Ce lien est une liste de lecture : ajoutez-le avec « Ajouter » pour obtenir un "
                                 "élément par vidéo.")
            state["parts"] = len(info.get("requested_formats") or []) or 1
            ydl.process_ie_result(info, download=True)
    except UserError:
        raise
    except Exception as e:
        raise FinalError(friendly_error(e))
    files = [p for p in ctx.tmp.glob("telechargement.*") if p.suffix not in (".part", ".ytdl", ".temp")]
    if not files:
        raise FinalError("Le téléchargement n'a produit aucun fichier.")
    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    ctx.progress(b, "Téléchargement terminé.")
    return files[0]
