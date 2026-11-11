(() => {
  "use strict";

  const TOKEN = document.querySelector('meta[name="token"]').content;
  const $ = (s, r = document) => r.querySelector(s);
  const NF1 = new Intl.NumberFormat("fr-CA", { maximumFractionDigits: 1 });

  // ------------------------------------------------------------ icônes
  const ICONS = {
    upload: '<path d="M12 15V4"/><path d="m7 9 5-5 5 5"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
    video: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m10 9.5 4.5 2.5-4.5 2.5z" fill="currentColor"/>',
    audio: '<path d="M9 18V6l11-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
    image: '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.8"/><path d="m21 16-5-5-9 9"/>',
    anim: '<rect x="7" y="7" width="13" height="13" rx="2.5"/><path d="M4 15.5V6a2 2 0 0 1 2-2h9.5"/><path d="m12 11.5 3.5 2-3.5 2z" fill="currentColor"/>',
    pdf: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
    doc: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M8.5 12h7M8.5 15.5h7M8.5 19h4"/>',
    sheet: '<rect x="3.5" y="3.5" width="17" height="17" rx="2.5"/><path d="M3.5 9.5h17M3.5 15h17M9.5 9.5v11"/>',
    slides: '<rect x="3" y="4" width="18" height="12" rx="2.5"/><path d="M12 16v4M8 20h8"/>',
    ebook: '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5z"/><path d="M5 19.5A1.5 1.5 0 0 0 6.5 21H19v-3"/>',
    unknown: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
    subs: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M7 15h4M13 15h4M7 11h10"/>',
    font: '<path d="M5 19 10.5 5h1L17 19"/><path d="M7.5 13.5h7"/><path d="M18 19h2"/><path d="M4 19h3"/>',
    archive: '<rect x="3" y="4" width="18" height="5" rx="1.5"/><path d="M5 9v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9"/><path d="M10 13h4"/>',
    data: '<ellipse cx="12" cy="5.5" rx="7.5" ry="2.5"/><path d="M4.5 5.5v13c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5v-13"/><path d="M4.5 12c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5"/>',
    web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/>',
    star: '<path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    all: '<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>',
    combo: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    chev: '<path d="m6 9 6 6 6-6"/>',
    arrow: '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    sliders: '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    folder: '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2.5h7.5A2.5 2.5 0 0 1 21 10v7.5a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5z"/>',
    open: '<path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M19 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-12A1.5 1.5 0 0 1 4 18.5v-12A1.5 1.5 0 0 1 5.5 5H10"/>',
    check: '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.8 2.8L16.5 9.5"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5h.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/>',
    gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    grip: '<circle cx="9" cy="6" r="1.2" fill="currentColor"/><circle cx="15" cy="6" r="1.2" fill="currentColor"/><circle cx="9" cy="12" r="1.2" fill="currentColor"/><circle cx="15" cy="12" r="1.2" fill="currentColor"/><circle cx="9" cy="18" r="1.2" fill="currentColor"/><circle cx="15" cy="18" r="1.2" fill="currentColor"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12.5A1.5 1.5 0 0 0 8.5 21h7a1.5 1.5 0 0 0 1.5-1.5L18 7M9 7V4.5A1.5 1.5 0 0 1 10.5 3h3A1.5 1.5 0 0 1 15 4.5V7"/>',
    shield: '<path d="M12 3 5 6v5c0 4.5 3 8.3 7 10 4-1.7 7-5.5 7-10V6z"/><path d="m9 12 2 2 4-4"/>',
    play: '<path d="M7 4.5v15l12-7.5z"/>',
    stop: '<rect x="6" y="6" width="12" height="12" rx="2.5"/>',
    retry: '<path d="M20 11a8 8 0 0 0-14.9-4M4 4v3.5h3.5"/><path d="M4 13a8 8 0 0 0 14.9 4M20 20v-3.5h-3.5"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7L12 5"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7L12 19"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    tools: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2L4 16.8V20h3.2l5.3-5.3a4 4 0 0 0 5.2-5.4l-2.5 2.5-2.5-.5-.5-2.5z"/>',
  };
  const svg = (name, cls = "ic") =>
    `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.unknown}</svg>`;
  const icon = (name, cls) => {
    const t = document.createElement("template");
    t.innerHTML = svg(name, cls);
    return t.content.firstChild;
  };

  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "html") el.innerHTML = v;
      else if (k === "style" && typeof v === "object") {
        for (const [sk, sv] of Object.entries(v)) {
          if (sk.startsWith("--")) el.style.setProperty(sk, sv);   // variables CSS (couleurs des familles)
          else el.style[sk] = sv;
        }
      }
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
      else if (typeof v === "boolean") el[k] = v;
      else el.setAttribute(k, v);
    }
    for (const kid of kids.flat()) {
      if (kid == null || kid === false) continue;
      el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
    }
    return el;
  }

  // ------------------------------------------------------------ API
  async function api(path, body, method) {
    const init = { method: method || (body !== undefined ? "POST" : "GET"), headers: { "X-Token": TOKEN } };
    if (body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    const res = await fetch(path, init);
    let data = null;
    try { data = await res.json(); } catch { /* vide */ }
    if (!res.ok) throw new Error((data && data.error) || `Erreur ${res.status}`);
    return data;
  }

  // ------------------------------------------------------------ état
  const S = {
    presets: [], presetMap: {}, options: {}, combine: {}, groups: [], families: {}, extFamily: {},
    tools: {}, settings: {}, preset: "all", files: [], jobs: {}, combos: [],
  };
  let keySeq = 0;
  const rows = new Map();
  const KIND_ICON = { video: "video", audio: "audio", image: "image", anim: "anim", pdf: "pdf", doc: "doc", sheet: "sheet", slides: "slides", ebook: "ebook", subs: "subs", font: "font", archive: "archive", data: "data", web: "web" };
  const kc = (family) => `var(--k-${family || "unknown"})`;

  // ------------------------------------------------------------ identité visuelle
  const BASE_FAMILY = { "Vidéo": "video", "Animation": "anim", "Audio": "audio", "Image": "image", "Document": "doc", "Tableur": "sheet", "Présentation": "slides", "Sous-titres": "subs", "Police": "font", "Archive": "archive", "Données": "data", "Ebook": "ebook" };
  const GROUP_COLOR = { "Favoris": "tools", "Vidéo & audio": "video", "En ligne": "link", "Outils": "tools", "Image": "image", "PDF & documents": "pdf", "Autres formats": "data", "GIF": "anim" };
  const POPULAR = {
    video: ["mp4", "mp3", "gif", "webm", "mov", "wav", "txt"], audio: ["mp3", "wav", "flac", "m4a", "ogg", "txt"],
    image: ["jpg", "png", "webp", "pdf", "ico", "svg"], anim: ["mp4", "gif", "webm", "apng", "png"],
    pdf: ["docx", "jpg", "png", "txt", "epub", "pdf_small"], doc: ["pdf", "docx", "txt", "epub", "html", "md"],
    sheet: ["xlsx", "csv", "pdf", "json"], slides: ["pdf", "pptx", "png", "mp4"], ebook: ["epub", "pdf", "mobi", "azw3", "txt", "mp3"],
    subs: ["srt", "vtt", "ass", "txt"], font: ["woff2", "ttf", "otf", "png"], archive: ["folder", "zip", "7z"],
    data: ["csv", "xlsx", "json", "yaml"], web: ["pdf", "png", "md", "docx"],
  };
  const POPULAR_PRESETS = ["yt-mp3", "sp-mp3", "heic-jpg", "pdf-word", "video-mp3", "discord", "video-gif", "pdf-small"];
  const PREFERRED_IN = ["mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "flac", "m4a", "jpg", "png", "heic", "webp", "svg", "pdf", "docx", "doc", "odt",
    "xlsx", "csv", "pptx", "epub", "mobi", "gif", "srt", "vtt", "ass", "ttf", "otf", "woff2", "zip", "rar", "7z", "json", "xml", "sqlite"];
  const SPECTRUM = ["#ff6b8b", "#ffa94d", "#ffd43b", "#5fe0b0", "#4dabf7", "#9775fa"];
  const norm = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  function fmtFamily(id) {
    if (id === "pdf" || id === "pdf_small") return "pdf";
    if (id === "folder") return "archive";
    if (id === "webp_anim" || id === "apng" || id === "gif") return "anim";
    return S.extFamily[id] || "unknown";
  }
  const fmtName = (id) => ({ pdf_small: "PDF", folder: "DOSSIER", webp_anim: "WEBP", tgz: "TAR.GZ" }[id] || String(id).toUpperCase());
  function targetFamily(t) {
    if (!t) return null;
    if (t.id === "pdf" || t.id === "pdf_small") return "pdf";
    if (t.id === "folder") return "archive";
    return BASE_FAMILY[t.base] || fmtFamily(t.id);
  }

  /* Le symbole de l'application (forme ronde qui devient carrée), à n'importe quelle échelle. */
  function glyph(prefix, x, y, w, ht) {
    const r = ht / 2, c = ht * 0.14, sw = w * 0.062, s1 = x + w * 0.443, s2 = x + w * 0.638;
    const stops = SPECTRUM.map((col, i) => `<stop offset="${(i / (SPECTRUM.length - 1)).toFixed(2)}" stop-color="${col}"/>`).join("");
    return `<defs><linearGradient id="${prefix}-g" gradientUnits="userSpaceOnUse" x1="${x}" y1="0" x2="${x + w}" y2="0">${stops}</linearGradient>` +
      `<mask id="${prefix}-m" maskUnits="userSpaceOnUse"><rect x="${x - 4}" y="${y - 4}" width="${w + 8}" height="${ht + 8}" fill="#fff"/>` +
      `<rect x="${s1}" y="${y - 4}" width="${sw}" height="${ht + 8}" fill="#000"/><rect x="${s2}" y="${y - 4}" width="${sw}" height="${ht + 8}" fill="#000"/></mask></defs>` +
      `<path class="art-glyph" mask="url(#${prefix}-m)" fill="url(#${prefix}-g)" d="M${x + r} ${y} H${x + w - c} Q${x + w} ${y} ${x + w} ${y + c} V${y + ht - c} Q${x + w} ${y + ht} ${x + w - c} ${y + ht} H${x + r} A${r} ${r} 0 0 1 ${x + r} ${y} Z"/>`;
  }

  /* Ce qu'un outil prend en entrée et produit, pour l'illustrer : [[libellé, famille], …]. */
  function heroFlow(p) {
    if (!p || p.id === "all") {
      return { ins: [["MOV", "video"], ["HEIC", "image"], ["DOCX", "doc"], ["WAV", "audio"]], outs: [["MP4", "video"], ["JPG", "image"], ["PDF", "pdf"], ["MP3", "audio"]] };
    }
    let ins;
    if (p.link) ins = [[(p.web ? "Page web" : p.site || "Lien").toUpperCase(), p.web ? "web" : "link"]];
    else if (p.accept && p.accept.length) {
      const pick = PREFERRED_IN.filter((e) => p.accept.includes(e)).slice(0, 3);
      ins = (pick.length ? pick : p.accept.slice(0, 3)).map((e) => [fmtName(e), fmtFamily(e)]);
    } else ins = [["FICHIERS", "unknown"]];
    let t = p.target;
    if (t && typeof t === "object") t = t["*"] || Object.values(t)[0];
    let outs;
    if (p.combine && S.combine[p.combine]) {
      const ext = S.combine[p.combine].ext || t || "zip";
      outs = [[fmtName(ext), fmtFamily(ext)]];
    } else if (t === "=") outs = [["MÊME FORMAT", ins[0][1]]];
    else if (t) outs = [[fmtName(t), fmtFamily(t)]];
    else if (p.link) outs = [["MP4", "video"], ["MP3", "audio"], ["GIF", "anim"]];
    else outs = (POPULAR[p.icon] || ["pdf"]).slice(0, 3).map((x) => [fmtName(x), fmtFamily(x)]);
    return { ins, outs };
  }

  function heroArt(ins, outs, id = "hero") {
    const W = 660, H = 206, cx = W / 2, cy = H / 2, cw = 96, ch = 32, gw = 128, gh = 76;
    const ys = (n) => Array.from({ length: n }, (_, i) => cy + (i - (n - 1) / 2) * (n > 3 ? 46 : 54));
    const chip = (x, y, [label, fam], main) =>
      `<g class="art-chip${main ? " main" : ""}" style="--c:${kc(fam)}"><rect x="${x}" y="${y - ch / 2}" width="${cw}" height="${ch}" rx="10"/>` +
      `<text x="${x + cw / 2}" y="${y + 4.6}" text-anchor="middle">${escapeHtml(label)}</text></g>`;
    const wire = (d, fam, k) => `<path class="art-line" style="--c:${kc(fam)}" d="${d}"/><path class="art-flow" style="--c:${kc(fam)};animation-delay:${-k * 0.37}s" d="${d}"/>`;
    const gx0 = cx - gw / 2, gx1 = cx + gw / 2, inX = 34, outX = W - 34 - cw;
    let lines = "", chips = "";
    ys(ins.length).forEach((y, i) => {
      const x1 = inX + cw, x2 = gx0 - 4, m = (x1 + x2) / 2;
      lines += wire(`M${x1} ${y} C${m} ${y} ${m} ${cy} ${x2} ${cy}`, ins[i][1], i);
      chips += chip(inX, y, ins[i], false);
    });
    ys(outs.length).forEach((y, i) => {
      const x1 = gx1 + 4, x2 = outX, m = (x1 + x2) / 2;
      lines += wire(`M${x1} ${cy} C${m} ${cy} ${m} ${y} ${x2} ${y}`, outs[i][1], i + 2);
      chips += chip(outX, y, outs[i], outs.length === 1);
    });
    const halo = `<defs><filter id="${id}-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="20"/></filter></defs>` +
      `<ellipse class="art-halo" cx="${cx}" cy="${cy}" rx="${gw * 0.62}" ry="${gh * 0.62}" fill="url(#${id}-g)" filter="url(#${id}-blur)"/>`;
    return `<svg class="hero-art" viewBox="0 0 ${W} ${H}" role="img" aria-label="Un fichier entre, il ressort converti">${lines}${halo}${glyph(id, gx0, cy - gh / 2, gw, gh)}${chips}</svg>`;
  }

  // ------------------------------------------------------------ formats
  function fmtSize(n) {
    if (n == null) return "";
    if (n < 1024) return `${n} o`;
    if (n < 1048576) return `${NF1.format(n / 1024)} Ko`;
    if (n < 1073741824) return `${NF1.format(n / 1048576)} Mo`;
    return `${NF1.format(n / 1073741824)} Go`;
  }
  function fmtDur(s) {
    s = Math.round(s);
    const hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
    return hh ? `${hh}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}` : `${mm}:${String(ss).padStart(2, "0")}`;
  }
  function metaParts(f) {
    const m = f.meta || {};
    const parts = [];
    if (f.size != null) parts.push(fmtSize(f.size));
    if (m.duration) parts.push(fmtDur(m.duration));
    if (m.uploader) parts.push(m.uploader);
    if (m.width && m.height) parts.push(`${m.width}×${m.height}`);
    if (m.frames) parts.push(`${m.frames} images`);
    if (m.pages) parts.push(`${m.pages} page${m.pages > 1 ? "s" : ""}`);
    if (m.encrypted) parts.push("protégé");
    if (m.unreadable) parts.push("illisible ?");
    return parts;
  }
  const targetOf = (f, id = f.target) => (f.targets || []).find((t) => t.id === id);
  const targetLabel = (f) => { const t = targetOf(f); return t ? t.label : "—"; };

  // ------------------------------------------------------------ préréglages
  const currentPreset = () => S.presetMap[S.preset] || S.presets[0];
  function presetTarget(f, p = currentPreset()) {
    if (!p || !p.target) return null;
    if (p.link && !f.url) return null;
    if (p.accept && !p.accept.includes(f.ext)) return null;
    let t = p.target;
    if (typeof t === "object") t = t[f.ext] || t["*"];
    if (t === "=") t = f.ext === "jpeg" || f.ext === "jfif" ? "jpg" : (f.ext === "tif" ? "tiff" : f.ext);
    const entry = targetOf(f, t);
    return entry && entry.ok ? t : null;
  }

  // ------------------------------------------------------------ fichiers
  function applyRecord(f, rec) {
    Object.assign(f, {
      id: rec.id, name: rec.name, ext: rec.ext, fmt: rec.fmt, family: rec.family, size: rec.size, meta: rec.meta || {},
      targets: rec.targets || [], def: rec.default, source: rec.source, familyLabel: rec.family_label,
      url: rec.url || null,
    });
    if (!f.target || !targetOf(f)) {
      const pt = presetTarget(f);
      f.target = pt || rec.default || null;
      const p = currentPreset();
      if (pt && p && p.options) Object.assign(f.options, p.options);
    }
    return f;
  }
  function newItem(extra) {
    return Object.assign({ key: `f${++keySeq}`, options: {}, open: false, jobId: null, upload: null, error: null, targets: [], meta: {} }, extra);
  }
  function addRecord(rec) {
    if (S.files.some((f) => f.id === rec.id)) return;
    S.files.push(applyRecord(newItem(), rec));
  }

  function stateOf(f) {
    if (f.upload) return "uploading";
    if (f.error) return "localerror";
    const j = f.jobId && S.jobs[f.jobId];
    if (j) return j.status;
    return f.family ? "idle" : "unsupported";
  }
  const busy = (st) => st === "queued" || st === "running" || st === "uploading";

  // ------------------------------------------------------------ import
  const uploadQueue = [];
  let uploading = false;

  function extOf(name) { const i = name.lastIndexOf("."); return i > 0 ? name.slice(i + 1).toLowerCase() : ""; }

  function addLocalFiles(list) {
    const files = [...list].filter((f) => f && f.size !== undefined);
    if (!files.length) return;
    for (const file of files) {
      const ext = extOf(file.name);
      const item = newItem({ name: file.name, ext, family: S.extFamily[ext] || null, size: file.size, upload: { p: 0 }, file });
      S.files.push(item);
      uploadQueue.push(item);
    }
    render();
    pump();
  }

  async function pump() {
    if (uploading) return;
    uploading = true;
    while (uploadQueue.length) {
      const item = uploadQueue.shift();
      if (!S.files.includes(item)) continue;
      try {
        const rec = await uploadOne(item);
        item.upload = null;
        delete item.file;
        if (!S.files.includes(item)) { api("/api/files/remove", { ids: [rec.id] }).catch(() => {}); continue; }
        applyRecord(item, rec);
      } catch (e) {
        item.upload = null;
        item.error = e.message;
      }
      render();
    }
    uploading = false;
  }

  function uploadOne(item) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      item.xhr = xhr;
      xhr.open("POST", `/api/upload?name=${encodeURIComponent(item.name)}`);
      xhr.setRequestHeader("X-Token", TOKEN);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) { item.upload.p = e.loaded / e.total; updateRow(item); }
      };
      xhr.onload = () => {
        let data = null;
        try { data = JSON.parse(xhr.responseText); } catch { /* */ }
        if (xhr.status === 200 && data) resolve(data);
        else reject(new Error((data && data.error) || "Échec de l'import"));
      };
      xhr.onerror = () => reject(new Error("Échec de l'import"));
      xhr.onabort = () => reject(new Error("Import annulé"));
      xhr.send(item.file);
    });
  }

  async function addLink(raw) {
    const url = (raw || "").trim();
    if (!/^https?:\/\/\S+$/i.test(url)) { toast("Collez une adresse complète, qui commence par https://", "error"); return; }
    const ph = newItem({ name: url, ext: "", family: null, size: null, upload: { p: null, label: "Analyse du lien…" } });
    S.files.push(ph);
    render();
    try {
      const p0 = currentPreset();
      const res = await api("/api/link", { url, web: !!(p0 && p0.web) });
      let at = S.files.indexOf(ph);
      S.files = S.files.filter((x) => x !== ph);
      if (at < 0) at = S.files.length;
      let n = 0;
      for (const rec of res.files || []) {
        if (S.files.some((f) => f.id === rec.id)) continue;
        S.files.splice(at + n, 0, applyRecord(newItem(), rec));
        n++;
      }
      if (n > 1) toast(`${n} éléments ajoutés depuis la liste de lecture.`, "ok");
      if (!n) toast("Ce lien est déjà dans la liste.", "info");
    } catch (e) {
      ph.upload = null;
      ph.error = e.message;
    }
    render();
  }

  function renderLinkbar() {
    const p = currentPreset();
    $("#linkbar").hidden = !(p && (p.link || p.id === "all"));
    $("#link-input").placeholder = p && p.site
      ? `Collez un lien ${p.site}… (${p.site === "Spotify" ? "titre, album ou playlist" : "vidéo, Reel ou playlist"})`
      : "Collez un lien YouTube, Spotify, SoundCloud, Instagram, Facebook, TikTok, X, Vimeo…";
    const art = $("#link-art");
    if (p && p.link) { const { ins, outs } = heroFlow(p); art.innerHTML = heroArt(ins, outs, "link"); } else art.innerHTML = "";
  }

  let picking = false;
  async function browse() {
    if (picking) return;
    picking = true;
    try {
      const p = currentPreset();
      const res = await api("/api/pick", { accept: p && p.accept ? p.accept : null });
      if (res.unavailable) $("#file-input").click();
      else {
        (res.files || []).forEach(addRecord);
        render();
      }
    } catch (e) {
      $("#file-input").click();
    } finally {
      picking = false;
    }
  }

  async function filesFromDrop(dt) {
    const entries = [...(dt.items || [])].filter((i) => i.kind === "file").map((i) => i.webkitGetAsEntry && i.webkitGetAsEntry()).filter(Boolean);
    if (!entries.length) return [...(dt.files || [])];
    const out = [];
    const walk = async (entry) => {
      if (entry.isFile) out.push(await new Promise((res, rej) => entry.file(res, rej)));
      else if (entry.isDirectory) {
        const reader = entry.createReader();
        let batch;
        do {
          batch = await new Promise((res, rej) => reader.readEntries(res, rej));
          for (const e of batch) await walk(e);
        } while (batch.length);
      }
    };
    for (const e of entries) await walk(e);
    return out;
  }

  // ------------------------------------------------------------ conversion
  function optionSpecs(f) { const t = targetOf(f); return t && t.ok ? t.options || [] : []; }
  function optionValues(item, specs) {
    const out = {};
    for (const spec of specs) if (item.options[spec.id] !== undefined) out[spec.id] = item.options[spec.id];
    return out;
  }

  let askedNotify = false;
  function askNotify() {
    if (askedNotify) return;
    askedNotify = true;
    try { if (window.Notification && Notification.permission === "default") Notification.requestPermission(); } catch { /* */ }
  }

  async function convert(f) {
    if (!f.id || !f.target) return;
    askNotify();
    const t = targetOf(f);
    if (!t || !t.ok) { toast(t ? t.reason : "Choisissez un format de sortie.", "error"); return; }
    try {
      f.error = null;
      const job = await api("/api/convert", { mode: "single", file_ids: [f.id], target: f.target, options: optionValues(f, t.options || []) });
      S.jobs[job.id] = job;
      f.jobId = job.id;
      render();
      poll(true);
    } catch (e) {
      toast(e.message, "error");
    }
  }

  async function cancel(jobId) {
    try { S.jobs[jobId] = await api(`/api/jobs/${jobId}/cancel`, {}); render(); } catch (e) { toast(e.message, "error"); }
  }

  function convertAll() {
    let n = 0;
    for (const f of S.files) {
      const st = stateOf(f);
      if ((st === "idle" || st === "error" || st === "canceled") && targetOf(f)?.ok) { convert(f); n++; }
    }
    if (!n) toast("Rien à convertir : tout est déjà fait ou en cours.", "info");
  }

  let pollTimer = null;
  async function poll(soon) {
    if (soon) { clearTimeout(pollTimer); pollTimer = setTimeout(poll, 250); return; }
    pollTimer = null;
    try {
      const list = await api("/api/jobs");
      for (const j of list) {
        const prev = S.jobs[j.id];
        S.jobs[j.id] = j;
        if (prev && prev.status !== j.status && j.status === "done" && document.hidden) notify(j);
      }
      render();
    } catch { /* serveur arrêté ? */ }
    const active = Object.values(S.jobs).some((j) => j.status === "queued" || j.status === "running");
    if (active) pollTimer = setTimeout(poll, 450);
  }

  function notify(job) {
    try {
      if (Notification.permission === "granted") new Notification("Conversion terminée", { body: job.outputs.map((o) => o.name).join(", "), icon: "/web/icon.png" });
    } catch { /* */ }
  }

  // ------------------------------------------------------------ rendu
  function render() {
    renderList();
    renderChrome();
  }

  function renderChrome() {
    const p = currentPreset();
    const has = S.files.length > 0 || S.combos.length > 0;
    $("#list-wrap").hidden = !has;
    $("#actionbar").hidden = !has;
    $("#content").classList.toggle("link-first", !!(p && p.link));
    $("#link-art").hidden = has || !(p && p.link);
    renderDrop(has || !!(p && p.link));
    renderPopular(!has && (!p || p.id === "all"));
    const ready = S.files.filter((f) => ["idle", "error", "canceled"].includes(stateOf(f)) && targetOf(f)?.ok).length;
    const running = S.files.filter((f) => busy(stateOf(f)));
    const done = S.files.filter((f) => stateOf(f) === "done").length;
    const count = $("#count");
    count.textContent = "";
    count.append(h("span", {}, `${S.files.length} fichier${S.files.length > 1 ? "s" : ""}`));
    if (running.length) count.append(h("i", { class: "sep" }), h("span", {}, `${running.length} en cours`));
    if (done) count.append(h("i", { class: "sep" }), h("span", { class: "done" }, `${done} terminé${done > 1 ? "s" : ""}`));
    // progression d'ensemble
    const tracked = S.files.filter((f) => f.jobId || busy(stateOf(f)));
    const overall = $("#overall");
    overall.hidden = !running.length || tracked.length < 2;
    if (!overall.hidden) {
      let sum = done;
      for (const f of running) { const j = f.jobId && S.jobs[f.jobId]; sum += j && j.progress ? j.progress : 0; }
      const n = tracked.length;
      $("#overall-text").textContent = `${done} sur ${n} terminé${done > 1 ? "s" : ""}`;
      $("#overall-bar").style.width = `${Math.min(100, (sum / n) * 100)}%`;
    }
    const all = $("#btn-all");
    all.innerHTML = `${svg("play")}<span>${ready ? `Tout convertir (${ready})` : done && !running.length ? "Tout est converti" : "Tout convertir"}</span>`;
    all.disabled = !ready;
    renderCombine();
  }

  function renderDrop(compact) {
    const drop = $("#drop");
    const p = currentPreset();
    const key = `${compact}|${S.preset}|${S.files.length ? 1 : 0}`;
    if (drop.dataset.key === key) return;            // évite de reconstruire l'illustration à chaque rafraîchissement
    drop.dataset.key = key;
    drop.classList.toggle("compact", compact);
    drop.classList.toggle("hero", !compact);
    drop.textContent = "";
    if (compact) {
      drop.append(
        h("div", { class: "big", html: svg("plus") }),
        h("div", { class: "grow" },
          h("h2", {}, S.files.length ? "Ajouter d'autres fichiers" : "Ou convertir des fichiers de cet ordinateur"),
          h("p", {}, "Cliquez pour parcourir, ou glissez-les n'importe où dans la fenêtre.")),
        h("kbd", {}, "Ctrl O"),
      );
      return;
    }
    const { ins, outs } = heroFlow(p);
    const art = document.createElement("template");
    art.innerHTML = heroArt(ins, outs);
    const accept = p && p.id !== "all" && p.accept;
    let chips = null;
    if (accept) {
      chips = accept.slice(0, 16).map((e) => h("span", { style: { "--c": kc(fmtFamily(e)) } }, e.toUpperCase()));
      if (accept.length > 16) chips.push(h("span", {}, `+${accept.length - 16}`));
    }
    drop.append(...[
      art.content.firstChild,
      h("h2", {}, "Déposez vos fichiers ici"),
      h("p", { class: "lead" }, !p || p.id === "all"
        ? "Le format est reconnu tout seul et toutes les conversions possibles vous sont proposées. Les dossiers sont acceptés."
        : "Ou cliquez pour les choisir. Les dossiers sont acceptés."),
      chips ? h("div", { class: "formats" }, chips) : null,
      h("div", { class: "hero-actions" },
        h("button", { class: "btn primary", type: "button", onclick: (e) => { e.stopPropagation(); browse(); } }, icon("upload"), "Parcourir les fichiers"),
        !p || p.id === "all" ? h("button", { class: "btn", type: "button", onclick: (e) => { e.stopPropagation(); const i = $("#link-input"); i.focus(); i.scrollIntoView({ block: "center", behavior: "smooth" }); } }, icon("link"), "Coller un lien") : null,
        h("span", { class: "hint-key" }, h("kbd", {}, "Ctrl O"))),
      h("ol", { class: "steps" },
        ["Déposez vos fichiers", "Choisissez le format", "Convertissez"].map((s, i) => h("li", { style: { "--sc": SPECTRUM[i * 2] } }, h("b", {}, String(i + 1)), s))),
      h("div", { class: "privacy", html: `${svg("shield")}<span>Aucun envoi sur Internet : tout est converti sur cet ordinateur.</span>` }),
    ].filter(Boolean));
  }

  function renderPopular(show) {
    const box = $("#popular");
    box.hidden = !show;
    if (!show || box.dataset.ready) return;
    box.dataset.ready = "1";
    const items = POPULAR_PRESETS.map((id) => S.presetMap[id]).filter(Boolean);
    box.append(
      h("div", { class: "section-title" }, "Raccourcis populaires"),
      h("div", { class: "pop-grid" }, items.map((p) => {
        const { ins, outs } = heroFlow(p);
        const [a, b] = [ins[0], outs[0]];
        return h("button", { class: "pop", type: "button", title: p.desc || p.label, style: { "--sc": kc(a[1]), "--tc": kc(b[1]) }, onclick: () => selectPreset(p.id) },
          h("span", { class: "mini" }, h("span", { style: { "--c": kc(a[1]) } }, a[0]), h("i"), h("span", { style: { "--c": kc(b[1]) } }, b[0])),
          h("b", {}, p.label));
      })),
    );
  }

  function renderCombine() {
    const box = $("#combine");
    const p = currentPreset();
    const avail = [];
    for (const [mode, spec] of Object.entries(S.combine)) {
      const items = combineItems(spec);
      if (items.length < (spec.min || 2)) continue;
      if (spec.needs && !spec.needs.every((fam) => items.some((f) => f.family === fam))) continue;
      avail.push({ mode, spec, n: items.length });
    }
    const key = `${S.preset}|${avail.map((a) => `${a.mode}:${a.n}`).join(",")}`;
    if (box.dataset.key === key) return;
    box.dataset.key = key;
    box.textContent = "";
    if (!avail.length) return;
    const featured = avail.find((a) => p && p.combine === a.mode);
    const btn = (a, primary) => h("button", {
      class: `btn ${primary ? "primary" : ""} sm`, type: "button", title: `${a.spec.label} avec ${a.n} fichiers, dans l'ordre de la liste`,
      onclick: () => openCombine(a.mode),
    }, icon("combo"), `${a.spec.button} (${a.n})`);
    if (featured) box.append(btn(featured, true));
    const rest = avail.filter((a) => a !== featured);
    if (rest.length === 1 && !featured) box.append(btn(rest[0], false));
    else if (rest.length) {
      box.append(h("button", { class: "btn sm", type: "button", title: "Assembler plusieurs fichiers de la liste en un seul", onclick: (e) => openCombineMenu(e.currentTarget, rest) },
        icon("combo"), featured ? "Autres assemblages" : `Assembler… (${rest.length})`, icon("chev")));
    }
  }

  function openCombineMenu(anchor, list) {
    closePicker();
    const pop = h("div", { class: "picker menu", role: "menu" },
      h("div", { class: "menu-title" }, "Assembler les fichiers de la liste"),
      list.map((a) => h("button", { class: "menu-item", type: "button", role: "menuitem", onclick: () => { closePicker(); openCombine(a.mode); } },
        h("span", { class: "dot", style: { "--kc": "var(--k-combo)" }, html: svg("combo") }),
        h("span", { class: "grow" }, h("b", {}, a.spec.button), h("small", {}, `${a.n} fichiers, dans l'ordre de la liste`)))));
    pop.addEventListener("keydown", (e) => { if (e.key === "Escape") { closePicker(); anchor.focus(); } });
    document.body.append(pop);
    const rect = anchor.getBoundingClientRect();
    pop.style.left = `${Math.max(12, Math.min(rect.left, window.innerWidth - pop.offsetWidth - 12))}px`;
    pop.style.bottom = `${window.innerHeight - rect.top + 8}px`;
    pickerEl = pop;
    setTimeout(() => document.addEventListener("mousedown", outsidePicker, true), 0);
    pop.querySelector(".menu-item")?.focus();
  }

  function combineItems(spec) {
    return S.files.filter((f) => f.id && !f.url && (spec.families === "*" || spec.families.includes(f.family)));
  }

  function renderList() {
    const list = $("#list");
    const wanted = [...S.combos.map((c) => ({ key: `c:${c.jobId}`, c })), ...S.files.map((f) => ({ key: `f:${f.key}`, f }))];
    const keys = new Set(wanted.map((w) => w.key));
    for (const [k, el] of rows) if (!keys.has(k)) { el.remove(); rows.delete(k); }
    let prev = null;
    for (const w of wanted) {
      let el = rows.get(w.key);
      if (!el) { el = w.c ? buildCombo(w.c) : buildRow(w.f); rows.set(w.key, el); }
      if (w.c) updateCombo(w.c, el); else updateRow(w.f, el);
      const next = prev ? prev.nextSibling : list.firstChild;
      if (next !== el) list.insertBefore(el, next);
      prev = el;
    }
  }

  function buildRow(f) {
    const el = h("article", { class: "row fresh", onanimationend: (e) => { if (e.target === el) el.classList.remove("fresh"); } });
    const r = {};
    r.grip = h("span", { class: "grip", title: "Glisser pour réordonner", html: svg("grip") });
    r.thumb = h("div", { class: "thumb" });
    r.name = h("div", { class: "name" });
    r.meta = h("div", { class: "meta" });
    r.src = h("span", { class: "fmt" });
    r.wire = h("span", { class: "wire" }, h("span", { class: "spark" }));
    r.target = h("button", { class: "target-btn", type: "button", title: "Choisir le format de sortie", onclick: (e) => openPicker(e.currentTarget, f.targets, f.target, (id) => setTarget(f, id), null, f.family) });
    r.opt = h("button", { class: "opt-btn", type: "button", title: "Réglages de cette conversion", onclick: () => { f.open = !f.open; updateRow(f); } }, icon("sliders"), h("span", { class: "lbl" }, "Réglages"));
    r.go = h("button", { class: "btn primary go", type: "button" });
    r.remove = h("button", { class: "icon-btn", type: "button", title: "Retirer de la liste", onclick: () => removeItem(f) }, icon("x"));
    r.opts = h("div", { class: "opts", hidden: true });
    r.status = h("div", { class: "status-line" });
    r.bar = h("div", { class: "bar" }, h("i"));
    el.append(
      h("div", { class: "row-main" }, r.grip, r.thumb, h("div", { class: "info" }, r.name, r.meta),
        h("div", { class: "to flow" }, r.src, r.wire, r.target, r.opt),
        h("div", { class: "actions" }, r.go, r.remove)),
      r.opts, r.status, r.bar,
    );
    el._r = r;
    el._f = f;
    setupReorder(el, f);
    return el;
  }

  function updateRow(f, el = rows.get(`f:${f.key}`)) {
    if (!el) return;
    const r = el._r;
    const st = stateOf(f);
    const job = f.jobId ? S.jobs[f.jobId] : null;
    el.dataset.state = st;
    el.style.setProperty("--kc", kc(f.url ? "link" : f.family));

    // vignette
    if (f.id && r.thumb.dataset.id !== f.id) {
      r.thumb.dataset.id = f.id;
      r.thumb.innerHTML = svg(KIND_ICON[f.family] || "unknown");
      if (["video", "audio", "image", "anim", "pdf"].includes(f.family) || ["epub", "mobi", "fb2", "cbz"].includes(f.ext)) {
        const img = new Image();
        img.alt = "";
        img.onload = () => { if (img.naturalWidth) { r.thumb.textContent = ""; r.thumb.append(img); } };
        img.src = `/api/thumb/${f.id}?t=${encodeURIComponent(TOKEN)}`;
      }
    } else if (!f.id && !r.thumb.firstChild) {
      r.thumb.innerHTML = svg(KIND_ICON[f.family] || "unknown");
    }

    r.name.textContent = f.url ? f.name.replace(/\.(mp4|m4a)$/i, "") : f.name;
    r.name.title = f.source || f.name;
    const kind = f.url ? (f.meta && f.meta.site ? f.meta.site : "Lien") : (f.familyLabel || S.families[f.family] || "");
    r.meta.textContent = "";
    [kind, ...metaParts(f)].filter(Boolean).forEach((part, i) => {
      if (i) r.meta.append(h("i", { class: "sep" }));
      r.meta.append(i ? h("span", {}, part) : h("span", { class: "kind-tag" }, part));
    });

    const t = targetOf(f);
    el.style.setProperty("--tc", t ? kc(targetFamily(t)) : "var(--line-2)");
    r.src.textContent = f.url ? (f.meta && f.meta.site ? f.meta.site : "Lien") : (f.ext || "?").toUpperCase();
    r.src.title = f.url ? "Contenu en ligne" : (f.familyLabel || "");
    const via = t && t.via ? t.via : [];
    const viaKey = via.join(">");
    if (r.wire.dataset.via !== viaKey) {
      r.wire.dataset.via = viaKey;
      r.wire.querySelectorAll(".node").forEach((n) => n.remove());
      via.forEach((step, i) => r.wire.append(h("span", { class: "node", title: `Étape intermédiaire : ${fmtName(step)}`, style: { left: `${((i + 1) / (via.length + 1)) * 100}%` } })));
    }
    r.wire.title = via.length ? `Passe par ${via.map(fmtName).join(" → ")}` : "Conversion directe";
    r.target.disabled = !f.targets.length || busy(st);
    r.target.innerHTML = f.targets.length
      ? `<span><span class="tg">en</span><span class="tl">${escapeHtml(t ? t.label : "Choisir…")}</span></span>${svg("chev")}`
      : `<small>${st === "uploading" ? "Import…" : "Aucune sortie"}</small>`;
    const specs = optionSpecs(f);
    r.opt.hidden = !t;                       // même sans réglage : le panneau permet d'enregistrer un favori
    r.opt.classList.toggle("on", !!(f.open && t));
    const changed = specs.filter((s) => f.options[s.id] !== undefined && f.options[s.id] !== specDefault(s)).length;
    r.opt.querySelector(".badge")?.remove();
    if (changed) r.opt.append(h("span", { class: "badge" }, changed));

    // options
    const optKey = `${f.target}|${specs.map((s) => s.id).join(",")}`;
    if (f.open && t) {
      if (r.opts.dataset.key !== optKey) { r.opts.dataset.key = optKey; r.opts.textContent = ""; r.opts.append(...specs.map((s) => field(f, s))); if (!specs.length) r.opts.append(h("div", { class: "hint" }, "Aucun réglage pour cette sortie.")); appendHint(r.opts, t); r.opts.append(h("div", { class: "hint" }, h("button", { class: "btn sm ghost", type: "button", onclick: () => saveFavorite(f) }, icon("star"), "Enregistrer ces réglages en favori"))); }
      r.opts.hidden = false;
    } else r.opts.hidden = true;

    // bouton principal
    r.go.onclick = null;
    if (st === "queued" || st === "running") {
      r.go.className = "btn go";
      r.go.innerHTML = `${svg("stop")}<span>Annuler</span>`;
      r.go.disabled = false;
      r.go.onclick = () => cancel(f.jobId);
    } else {
      r.go.className = "btn primary go";
      r.go.innerHTML = `${svg(st === "error" ? "retry" : "play")}<span>${st === "error" ? "Réessayer" : "Convertir"}</span>`;
      r.go.disabled = st === "uploading" || st === "unsupported" || !t || !t.ok;
      r.go.title = t && !t.ok ? t.reason : "";
      r.go.onclick = () => convert(f);
    }

    // statut + progression
    renderStatus(r, st, f, job);
  }

  function renderStatus(r, st, f, job) {
    const line = r.status;
    line.textContent = "";
    let show = true;
    let progress = null;
    if (st === "uploading") {
      progress = f.upload.p;
      line.append(h("span", { class: "spin" }), h("span", {}, f.upload.label || `Import… ${Math.round((f.upload.p || 0) * 100)} %`));
    } else if (st === "localerror") {
      line.append(h("span", { class: "err", html: `${svg("alert")}<span>${escapeHtml(f.error)}</span>` }));
    } else if (st === "unsupported") {
      line.append(h("span", { class: "muted" }, "Format non reconnu : aucune conversion disponible pour ce type de fichier."));
    } else if (st === "queued") {
      progress = 0;
      line.append(h("span", { class: "spin" }), h("span", { class: "muted" }, "En attente d'un emplacement libre…"));
    } else if (st === "running") {
      progress = job.progress;
      line.append(h("span", { class: "spin" }), job.progress != null ? h("span", { class: "pct" }, `${Math.round(job.progress * 100)} %`) : null,
        h("span", {}, job.message || "Conversion…"));
    } else if (st === "done" && job) {
      line.append(h("div", { class: "result" }, resultParts(job, f)));
    } else if (st === "error" && job) {
      line.append(h("span", { class: "err", html: `${svg("alert")}<span>${escapeHtml(job.error || "Échec de la conversion.")}</span>` }));
    } else if (st === "canceled") {
      line.append(h("span", { class: "muted" }, "Conversion annulée."));
    } else {
      const t = targetOf(f);
      if (f.url) {
        line.append(h("span", { class: "muted" }, `Sera téléchargé depuis ${(f.meta && f.meta.site) || "le site"} puis converti${t ? ` en ${t.label}` : ""}.`));
      } else if (t && t.via && t.via.length) {
        const steps = [f.ext, ...t.via].map(fmtName);
        const route = h("span", { class: "route" }, `En ${t.via.length + 1} étapes :`);
        steps.forEach((s) => route.append(h("span", {}, s), icon("arrow")));
        route.append(h("span", {}, t.label));
        line.append(route);
      } else show = false;
    }
    line.classList.toggle("show", show);
    const bar = r.bar;
    bar.classList.toggle("indet", progress === null && (st === "running" || st === "uploading"));
    bar.firstChild.style.width = progress == null ? (st === "running" ? "30%" : "0") : `${Math.max(2, progress * 100)}%`;
    bar.style.visibility = busy(st) ? "visible" : "hidden";
  }

  const SAME_KIND = { video: "Vidéo", audio: "Audio", image: "Image", anim: "Animation", pdf: "Document", doc: "Document" };
  function resultParts(job, f) {
    const srcSize = f && f.size;
    const t = f && f.targets ? targetOf(f, job.target) : null;
    const comparable = t && SAME_KIND[f.family] && SAME_KIND[f.family] === t.base;
    const parts = [];
    const outs = job.outputs || [];
    if (!outs.length) return [h("span", { class: "ok", html: `${svg("check")}<span>Terminé</span>` })];
    const o = outs[0];
    parts.push(h("span", { class: "ok", html: svg("check") }));
    parts.push(h("span", { class: "file", title: o.path }, o.name));
    if (o.is_dir) parts.push(h("span", { class: "muted" }, `dossier · ${o.count} fichier${o.count > 1 ? "s" : ""} · ${fmtSize(o.size)}`));
    else {
      parts.push(h("span", { class: "muted" }, fmtSize(o.size)));
      if (comparable && srcSize && o.size && job.mode === "single") {
        const pct = Math.round((o.size / srcSize - 1) * 100);
        if (pct <= -1) parts.push(h("span", { class: "delta down", title: "Gain de taille par rapport à l'original" }, `−${Math.abs(pct)} %`));
      }
    }
    parts.push(h("span", { class: "spacer" }));
    parts.push(h("button", { class: "btn sm", type: "button", onclick: () => api("/api/open", { job_id: job.id, index: 0 }).catch((e) => toast(e.message, "error")) }, icon("open"), "Ouvrir"));
    parts.push(h("button", { class: "btn sm ghost", type: "button", onclick: () => api("/api/reveal", { job_id: job.id, index: 0 }).catch((e) => toast(e.message, "error")) }, icon("folder"), "Afficher dans le dossier"));
    return parts;
  }

  function appendHint(box, t) {
    if (t && t.via && t.via.length) {
      box.append(h("div", { class: "hint" }, `Passe par : ${t.via.map((x) => x.toUpperCase()).join(" → ")}`));
    }
  }

  function specDefault(spec) {
    const d = { ...S.options[spec.id], ...spec };
    return d.default;
  }

  function field(item, spec) {
    const d = { ...S.options[spec.id], ...spec };
    const val = item.options[spec.id] !== undefined ? item.options[spec.id] : d.default;
    const set = (v) => { item.options[spec.id] = v; if (item.key) updateRow(item); };
    if (d.type === "checkbox") {
      return h("label", { class: "check" }, h("input", { type: "checkbox", checked: !!val, onchange: (e) => set(e.target.checked) }), h("span", {}, d.label));
    }
    let input;
    if (d.type === "select") {
      input = h("select", { onchange: (e) => set(e.target.value) }, d.choices.map(([v, l]) => h("option", { value: v }, l)));
      input.value = String(val ?? "");
    } else if (d.type === "range") {
      const out = h("output", {}, String(val));
      const range = h("input", { type: "range", min: d.min, max: d.max, value: val, oninput: (e) => { out.textContent = e.target.value; item.options[spec.id] = Number(e.target.value); }, onchange: (e) => set(Number(e.target.value)) });
      input = h("div", { class: "range" }, range, out);
    } else if (d.type === "number") {
      input = h("input", { type: "number", min: d.min, max: d.max, placeholder: d.placeholder || "", value: val ?? "", onchange: (e) => set(e.target.value === "" ? null : Number(e.target.value)) });
    } else if (d.type === "color") {
      input = h("input", { type: "color", value: val || "#ffffff", onchange: (e) => set(e.target.value) });
    } else {
      input = h("input", { type: "text", placeholder: d.placeholder || "", value: val ?? "", onchange: (e) => set(e.target.value) });
    }
    return h("label", { class: "field" }, h("span", {}, d.label), input);
  }

  function setTarget(f, id) {
    f.target = id;
    render();
  }

  function removeItem(f) {
    if (f.xhr && f.upload) f.xhr.abort();
    const st = stateOf(f);
    if ((st === "queued" || st === "running") && f.jobId) cancel(f.jobId);
    S.files = S.files.filter((x) => x !== f);
    if (f.id) api("/api/files/remove", { ids: [f.id] }).catch(() => {});
    render();
  }

  function clearList() {
    const keep = S.files.filter((f) => busy(stateOf(f)));
    const gone = S.files.filter((f) => !keep.includes(f));
    if (gone.length) api("/api/files/remove", { ids: gone.filter((f) => f.id).map((f) => f.id) }).catch(() => {});
    S.files = keep;
    S.combos = S.combos.filter((c) => { const j = S.jobs[c.jobId]; return j && (j.status === "queued" || j.status === "running"); });
    render();
    if (keep.length) toast("Les conversions en cours ont été conservées.", "info");
  }

  // ------------------------------------------------------------ réordonner
  let dragKey = null;
  function setupReorder(el, f) {
    el._r.grip.addEventListener("mousedown", () => { el.draggable = true; });
    el.addEventListener("dragstart", (e) => {
      if (!el.draggable) return;
      dragKey = f.key;
      el.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/x-convertisseur", f.key);
    });
    el.addEventListener("dragend", () => { el.draggable = false; dragKey = null; el.classList.remove("dragging"); clearDropMarks(); });
    el.addEventListener("dragover", (e) => {
      if (!dragKey || dragKey === f.key) return;
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      const after = e.clientY > rect.top + rect.height / 2;
      clearDropMarks();
      el.classList.add(after ? "drop-after" : "drop-before");
    });
    el.addEventListener("drop", (e) => {
      if (!dragKey) return;
      e.preventDefault();
      e.stopPropagation();
      const moving = S.files.find((x) => x.key === dragKey);
      if (!moving || moving === f) return;
      const after = el.classList.contains("drop-after");
      S.files = S.files.filter((x) => x !== moving);
      const idx = S.files.indexOf(f) + (after ? 1 : 0);
      S.files.splice(idx, 0, moving);
      clearDropMarks();
      render();
    });
  }
  function clearDropMarks() { document.querySelectorAll(".drop-before,.drop-after").forEach((x) => x.classList.remove("drop-before", "drop-after")); }

  // ------------------------------------------------------------ assemblages
  function openCombine(mode) {
    const spec = S.combine[mode];
    const items = combineItems(spec);
    const holder = { options: {} };
    const fields = spec.options.map((o) => field(holder, o));
    modal(spec.label, [
      h("p", {}, `${items.length} fichiers seront assemblés dans l'ordre de la liste. Glissez les lignes (poignée à gauche) pour changer l'ordre.`),
      h("div", { class: "opts", style: { padding: "0", border: "0", background: "none" } }, fields),
    ], [
      { label: "Annuler" },
      {
        label: "Créer", primary: true, run: async () => {
          try {
            const job = await api("/api/convert", { mode, file_ids: items.map((f) => f.id), options: holder.options });
            S.jobs[job.id] = job;
            S.combos.unshift({ jobId: job.id, mode, count: items.length });
            render();
            poll(true);
          } catch (e) { toast(e.message, "error"); return false; }
        },
      },
    ]);
  }

  function buildCombo(c) {
    const el = h("article", { class: "row" });
    const r = {};
    r.thumb = h("div", { class: "thumb", html: svg("combo") });
    r.name = h("div", { class: "name" });
    r.meta = h("div", { class: "meta" });
    r.go = h("button", { class: "btn go", type: "button" });
    r.remove = h("button", { class: "icon-btn", type: "button", title: "Retirer", onclick: () => { S.combos = S.combos.filter((x) => x !== c); render(); } }, icon("x"));
    r.status = h("div", { class: "status-line" });
    r.bar = h("div", { class: "bar" }, h("i"));
    el.append(h("div", { class: "row-main" }, h("span"), r.thumb, h("div", { class: "info" }, r.name, r.meta), h("div"), h("div", { class: "actions" }, r.go, r.remove)), r.status, r.bar);
    el.style.setProperty("--kc", "var(--k-combo)");
    el.style.setProperty("--tc", "var(--k-combo)");
    el._r = r;
    return el;
  }

  function updateCombo(c, el) {
    const r = el._r;
    const job = S.jobs[c.jobId];
    const st = job ? job.status : "queued";
    el.dataset.state = st;
    r.name.textContent = S.combine[c.mode].label;
    r.meta.textContent = `${c.count} fichiers · ${job && job.names ? job.names.slice(0, 3).join(", ") + (job.names.length > 3 ? "…" : "") : ""}`;
    r.go.hidden = !(st === "queued" || st === "running");
    r.go.innerHTML = `${svg("stop")}<span>Annuler</span>`;
    r.go.onclick = () => cancel(c.jobId);
    renderStatus(r, st, { size: null, targets: [] }, job);
  }

  // ------------------------------------------------------------ sélecteur de format
  let pickerEl = null;
  function closePicker() {
    if (!pickerEl) return;
    pickerEl.remove();
    pickerEl = null;
    document.removeEventListener("mousedown", outsidePicker, true);
  }
  function outsidePicker(e) { if (pickerEl && !pickerEl.contains(e.target)) closePicker(); }

  function openPicker(anchor, targets, current, onPick, footer, family) {
    closePicker();
    const search = h("input", { class: "picker-search", type: "search", placeholder: "Rechercher un format… (ex. mp3, pdf, jpg)", "aria-label": "Rechercher un format" });
    const body = h("div", { class: "picker-body" });
    const pop = h("div", { class: "picker", role: "dialog", "aria-label": "Format de sortie" }, h("div", { class: "picker-top", html: svg("search") }), body);
    pop.firstChild.append(search);
    pop.append(h("div", { class: "picker-foot" }, footer || h("span", {}, h("kbd", {}, "↑↓"), "naviguer ", h("kbd", {}, "Entrée"), "choisir ", h("kbd", {}, "Échap"), "fermer")));
    const chip = (t) => h("button", {
      type: "button", class: `chip${t.id === current ? " on" : ""}${t.ok ? "" : " off"}`, disabled: !t.ok, style: { "--tc": kc(targetFamily(t)) },
      title: t.ok ? (t.via && t.via.length ? `${t.label} — passe par ${t.via.map(fmtName).join(" → ")}` : t.label) : t.reason,
      onclick: () => { closePicker(); onPick(t.id); },
    }, t.label);
    const draw = () => {
      const words = norm(search.value.trim()).split(/\s+/).filter(Boolean);
      body.textContent = "";
      const groups = new Map();
      for (const t of targets) {
        const hay = norm(`${t.label} ${t.id} ${t.ext} ${t.group}`);
        if (words.length && !words.every((w) => hay.includes(w))) continue;
        if (!groups.has(t.group)) groups.set(t.group, []);
        groups.get(t.group).push(t);
      }
      if (!groups.size) { body.append(h("div", { class: "picker-empty" }, "Aucun format ne correspond.")); return; }
      const popular = !words.length && family && POPULAR[family]
        ? POPULAR[family].map((id) => targets.find((t) => t.id === id && t.ok)).filter(Boolean) : [];
      if (popular.length >= 3) {
        body.append(h("div", { class: "picker-group pop-head" }, h("i"), "Les plus utilisés"), h("div", { class: "picker-grid" }, popular.map(chip)));
      }
      for (const [g, list] of groups) {
        body.append(h("div", { class: "picker-group", style: { "--gc": kc(targetFamily(list[0])) } }, h("i"), g));
        body.append(h("div", { class: "picker-grid" }, list.map(chip)));
      }
    };
    const chips = () => [...body.querySelectorAll(".chip:not(.off)")];
    search.addEventListener("input", draw);
    pop.addEventListener("keydown", (e) => {
      const list = chips();
      const i = list.indexOf(document.activeElement);
      if (e.key === "Escape") { e.preventDefault(); closePicker(); anchor.focus(); return; }
      if (e.key === "Enter" && document.activeElement === search) { e.preventDefault(); (list.find((c) => c.classList.contains("on")) && !search.value ? list.find((c) => c.classList.contains("on")) : list[0])?.click(); return; }
      if (!["ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"].includes(e.key) || !list.length) return;
      if (document.activeElement === search && (e.key === "ArrowLeft" || e.key === "ArrowRight")) return;
      e.preventDefault();
      const step = e.key === "ArrowDown" || e.key === "ArrowRight" ? 1 : -1;
      if (i < 0) { (step > 0 ? list[0] : list[list.length - 1]).focus(); return; }
      const next = i + step;
      if (next < 0) search.focus(); else list[Math.min(next, list.length - 1)].focus();
    });
    draw();
    document.body.append(pop);
    const rect = anchor.getBoundingClientRect();
    const width = Math.min(470, window.innerWidth - 24);
    const left = Math.max(12, Math.min(rect.right - width, window.innerWidth - width - 12));
    const below = window.innerHeight - rect.bottom - 16;
    const above = rect.top - 16;
    if (below >= 300 || below >= above) {
      pop.style.top = `${rect.bottom + 6}px`;
      pop.style.maxHeight = `${Math.max(220, below)}px`;
    } else {
      pop.style.bottom = `${window.innerHeight - rect.top + 6}px`;
      pop.style.maxHeight = `${Math.max(220, above)}px`;
    }
    pop.style.left = `${left}px`;
    pickerEl = pop;
    setTimeout(() => document.addEventListener("mousedown", outsidePicker, true), 0);
    search.focus();
    body.querySelector(".chip.on")?.scrollIntoView({ block: "nearest" });
  }

  function openBulk(anchor) {
    const map = new Map();
    for (const f of S.files) {
      if (busy(stateOf(f))) continue;
      for (const t of f.targets || []) {
        const cur = map.get(t.id);
        if (!cur) map.set(t.id, { ...t, n: t.ok ? 1 : 0 });
        else if (t.ok) { cur.n++; cur.ok = true; }
      }
    }
    if (!map.size) { toast("Aucun fichier prêt.", "info"); return; }
    const order = new Map(S.groups.map((g, i) => [g, i]));
    const targets = [...map.values()].map((t) => ({ ...t, group: t.base || t.group, label: `${t.label}${t.n && t.n < S.files.length ? ` (${t.n})` : ""}` }));
    targets.sort((a, b) => (order.get(a.group) ?? 99) - (order.get(b.group) ?? 99));
    openPicker(anchor, targets, null, (id) => {
      let n = 0;
      for (const f of S.files) if (!busy(stateOf(f)) && targetOf(f, id)?.ok) { f.target = id; n++; }
      render();
      toast(`${n} fichier${n > 1 ? "s" : ""} réglé${n > 1 ? "s" : ""} sur ${map.get(id).label}.`, "ok");
    }, "Le nombre entre parenthèses indique combien de fichiers acceptent ce format.");
  }

  // ------------------------------------------------------------ fenêtres, notifications
  function modal(title, body, actions) {
    const back = h("div", { class: "modal-back" });
    const close = () => { back.remove(); document.removeEventListener("keydown", onKey); };
    const onKey = (e) => { if (e.key === "Escape") close(); };
    const footer = h("footer", {}, actions.map((a) => h("button", {
      class: `btn ${a.primary ? "primary" : ""}`, type: "button",
      onclick: async () => { if (a.run) { const r = await a.run(); if (r === false) return; } close(); },
    }, a.label)));
    const box = h("div", { class: "modal", role: "dialog", "aria-modal": "true" },
      h("header", {}, h("h3", {}, title), h("button", { class: "icon-btn", type: "button", title: "Fermer", onclick: close }, icon("x"))),
      h("div", { class: "body" }, body), footer);
    back.append(box);
    back.addEventListener("mousedown", (e) => { if (e.target === back) close(); });
    document.addEventListener("keydown", onKey);
    document.body.append(back);
    return close;
  }

  function toast(msg, kind = "info") {
    const el = h("div", { class: `toast ${kind}`, html: `${svg(kind === "ok" ? "check" : kind === "error" ? "alert" : "info")}<span></span>` });
    el.querySelector("span").textContent = msg;
    $("#toasts").append(el);
    setTimeout(() => el.remove(), kind === "error" ? 7000 : 3800);
  }

  function escapeHtml(s) { return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

  // ------------------------------------------------------------ réglages
  function openSettings() {
    const s = { ...S.settings };
    const path = h("div", { class: "path", title: s.output_dir }, s.output_dir);
    const T = S.tools;
    const toolRow = (ok, label, note) => h("div", { class: ok ? "" : "off" }, h("i"), h("span", {}, label), note ? h("small", {}, note) : null);
    modal("Réglages", [
      h("div", { class: "setting" }, h("span", {}, "Dossier d'enregistrement"),
        h("div", { class: "path-row" }, path,
          h("button", {
            class: "btn sm", type: "button", onclick: async () => {
              const r = await api("/api/pick-folder", {});
              if (r.path) { s.output_dir = r.path; path.textContent = r.path; path.title = r.path; }
              else if (r.unavailable) toast("Sélecteur de dossier indisponible.", "error");
            },
          }, "Changer…"))),
      h("label", { class: "check" }, h("input", { type: "checkbox", checked: !!s.next_to_source, onchange: (e) => { s.next_to_source = e.target.checked; } }),
        h("span", {}, "Enregistrer à côté du fichier d'origine (fichiers choisis avec « Parcourir »)")),
      h("label", { class: "check" }, h("input", { type: "checkbox", checked: !!s.open_folder, onchange: (e) => { s.open_folder = e.target.checked; } }),
        h("span", {}, "Ouvrir le dossier à la fin de chaque conversion")),
      h("label", { class: "check" }, h("input", { type: "checkbox", disabled: !T.gpu, checked: !!s.gpu && !!T.gpu, onchange: (e) => { s.gpu = e.target.checked; } }),
        h("span", {}, T.gpu ? `Accélération matérielle : vidéos (${T.gpu})${T.whisper_gpu ? " et transcription (CUDA)" : ""}` : "Accélération matérielle (aucune carte compatible détectée)")),
      h("label", { class: "field" }, h("span", {}, "Conversions simultanées"),
        (() => { const sel = h("select", { onchange: (e) => { s.parallel = Number(e.target.value); } }, [1, 2, 3, 4].map((n) => h("option", { value: n }, String(n)))); sel.value = String(s.parallel); return sel; })()),
      h("label", { class: "field" }, h("span", {}, "Session du navigateur pour les sites qui exigent une connexion (Instagram, Facebook…)"),
        (() => {
          const sel = h("select", { onchange: (e) => { s.cookies = e.target.value; } }, [
            ["none", "Aucune (contenus publics seulement)"], ["firefox", "Firefox"], ["edge", "Microsoft Edge"],
            ["chrome", "Google Chrome"], ["brave", "Brave"], ["opera", "Opera"], ["vivaldi", "Vivaldi"],
          ].map(([v, l]) => h("option", { value: v }, l)));
          sel.value = s.cookies || "none";
          return sel;
        })()),
      h("div", { class: "setting" }, h("span", {}, "Module de téléchargement"),
        h("div", { class: "path-row" },
          h("div", { class: "path", style: { direction: "ltr" } }, T.ytdlp ? `yt-dlp ${T.ytdlp}` : "yt-dlp non installé"),
          h("button", {
            class: "btn sm", type: "button", onclick: async (e) => {
              const b = e.currentTarget;
              b.disabled = true;
              b.textContent = "Mise à jour…";
              try { const r = await api("/api/update-ytdlp", {}); S.tools.ytdlp = r.version; toast(`yt-dlp est à jour (${r.version}).`, "ok"); }
              catch (err) { toast(err.message, "error"); }
              b.disabled = false;
              b.textContent = "Mettre à jour";
            },
          }, "Mettre à jour"))),
      h("div", { class: "setting" }, h("span", {}, "Moteurs installés"),
        h("div", { class: "tool-list" },
          toolRow(!!T.ffmpeg, `FFmpeg ${T.ffmpeg || ""}`, "vidéo, audio, GIF"),
          toolRow(!!T.libreoffice, "LibreOffice", "DOC, ODT, RTF, XLS, PPT…"),
          toolRow(!!T.calibre, "Calibre", "MOBI, AZW3, FB2, LIT…"),
          toolRow(!!T.edge, "Microsoft Edge", "mise en page HTML → PDF"),
          toolRow(!!T.sevenzip, "7-Zip", "archives RAR, 7Z, ISO…"),
          toolRow(!!T.ytdlp, `yt-dlp ${T.ytdlp || ""}`, T.js_runtime ? "téléchargement YouTube, SoundCloud, Instagram, Facebook…" : "installez Node.js pour YouTube"),
          toolRow(T.voices && T.voices.length, "Voix Windows", T.voices && T.voices.length ? T.voices.join(", ") : "lecture vocale"),
          toolRow(!!T.ocr, "OCR Windows", T.ocr ? `reconnaissance de texte (${T.ocr})` : "reconnaissance de texte"),
          toolRow(!!T.whisper, "Whisper", T.whisper ? `transcription de la parole (${T.whisper_gpu ? "carte NVIDIA" : "processeur"})${T.whisper_models && T.whisper_models.length ? ` — modèle(s) : ${T.whisper_models.join(", ")}` : " — modèle téléchargé au 1er usage"}` : "transcription de la parole"))),
      h("div", { class: "setting" }, h("span", {}, "Raccourcis"),
        h("div", { class: "path-row" }, h("button", {
          class: "btn sm", type: "button", onclick: async () => {
            try { await api("/api/shortcut", {}); toast("Raccourci « Convertisseur » créé sur le Bureau (vous pouvez y glisser des fichiers).", "ok"); } catch (e) { toast(e.message, "error"); }
          },
        }, icon("link"), "Raccourci sur le Bureau"), h("button", {
          class: "btn sm", type: "button", onclick: async () => {
            try { await api("/api/sendto", {}); toast("Ajouté au menu clic droit → « Envoyer vers » de l'Explorateur.", "ok"); } catch (e) { toast(e.message, "error"); }
          },
        }, icon("link"), "Menu « Envoyer vers »"))),
    ], [
      { label: "Annuler" },
      {
        label: "Enregistrer", primary: true, run: async () => {
          try { S.settings = await api("/api/settings", s); toast("Réglages enregistrés.", "ok"); } catch (e) { toast(e.message, "error"); return false; }
        },
      },
    ]);
  }

  // ------------------------------------------------------------ historique
  async function openHistory() {
    let items = [];
    try { items = await api("/api/history"); } catch (e) { toast(e.message, "error"); return; }
    const fmt = new Intl.DateTimeFormat("fr-CA", { dateStyle: "medium", timeStyle: "short" });
    const famOfName = (n) => fmtFamily(extOf(n || ""));
    const list = items.length ? items.map((e) => h("div", { class: "hist" },
      h("span", { class: "dot", style: { "--kc": kc(famOfName(e.outputs[0] && e.outputs[0].name)) }, html: svg(KIND_ICON[famOfName(e.outputs[0] && e.outputs[0].name)] || "unknown") }),
      h("div", { class: "hist-main" },
        h("b", {}, e.outputs.map((o) => o.name).join(", ") || "—"),
        h("small", {}, `${fmt.format(new Date(e.date * 1000))} · ${e.target} · depuis ${e.names.slice(0, 2).join(", ")}${e.names.length > 2 ? "…" : ""}`)),
      e.outputs[0] && e.outputs[0].exists ? h("div", { class: "hist-actions" },
        h("button", { class: "btn sm", type: "button", onclick: () => api("/api/history/open", { path: e.outputs[0].path }).catch((x) => toast(x.message, "error")) }, icon("open"), "Ouvrir"),
        h("button", { class: "btn sm ghost", type: "button", onclick: () => api("/api/history/open", { path: e.outputs[0].path, reveal: true }).catch((x) => toast(x.message, "error")) }, icon("folder"))) : h("small", { class: "muted" }, "déplacé ou supprimé"))) : [h("p", {}, "Aucune conversion pour l'instant.")];
    modal("Historique des conversions", [h("div", { class: "hist-list" }, list)], [
      { label: "Effacer l'historique", run: async () => { await api("/api/history/clear", {}); toast("Historique effacé.", "ok"); } },
      { label: "Fermer", primary: true },
    ]);
  }

  // ------------------------------------------------------------ barre latérale
  function favoritePresets() {
    return (S.settings.favorites || []).map((fav) => ({
      id: `fav-${fav.id}`, group: "Favoris", label: fav.label, icon: "star", target: fav.target, options: fav.options,
      accept: null, title: `Favori : ${fav.label}`, desc: `Règle les fichiers compatibles sur ${fav.targetLabel || fav.target.toUpperCase()} avec vos réglages enregistrés.`, fav: fav.id,
    }));
  }

  async function saveFavorite(f) {
    const t = targetOf(f);
    if (!t) return;
    const input = h("input", { type: "text", value: `${(f.ext || "").toUpperCase()} → ${t.label}`, style: { width: "100%", height: "36px", padding: "0 10px", borderRadius: "9px", border: "1px solid var(--border)", background: "var(--panel-2)" } });
    modal("Nouveau favori", [h("p", {}, "Nom du favori (il apparaîtra dans la barre latérale) :"), input], [
      { label: "Annuler" },
      {
        label: "Enregistrer", primary: true, run: async () => {
          const fav = { id: Math.random().toString(36).slice(2, 9), label: input.value.trim() || t.label, target: f.target, targetLabel: t.label, options: optionValues(f, t.options || []) };
          try {
            S.settings = await api("/api/settings", { favorites: [...(S.settings.favorites || []), fav] });
            refreshPresets();
            toast(`Favori « ${fav.label} » ajouté.`, "ok");
          } catch (e) { toast(e.message, "error"); return false; }
        },
      },
    ]);
    setTimeout(() => input.select(), 50);
  }

  async function deleteFavorite(id) {
    S.settings = await api("/api/settings", { favorites: (S.settings.favorites || []).filter((x) => x.id !== id) });
    if (S.preset === `fav-${id}`) S.preset = "all";
    refreshPresets();
  }

  function refreshPresets() {
    S.presets = [...S.basePresets.slice(0, 1), ...favoritePresets(), ...S.basePresets.slice(1)];
    S.presetMap = Object.fromEntries(S.presets.map((p) => [p.id, p]));
    renderNav();
    selectPreset(S.preset);
  }

  // groupes repliables + recherche d'outils
  let navQuery = "";
  let navOpen = null;
  function saveNavOpen() { try { localStorage.setItem("navOpen", JSON.stringify([...navOpen])); } catch { /* */ } }
  function presetMatches(p, words) {
    const hay = norm(`${p.label} ${p.group || ""} ${p.title || ""} ${p.site || ""} ${typeof p.target === "string" ? p.target : ""} ${(p.accept || []).slice(0, 12).join(" ")}`);
    return words.every((w) => hay.includes(w));
  }
  function highlight(label, words) {
    if (!words.length) return escapeHtml(label);
    const chars = [...label];
    const flat = [], map = [];
    chars.forEach((c, i) => { for (const n of norm(c)) { flat.push(n); map.push(i); } });
    const mark = new Array(chars.length).fill(false);
    const s = flat.join("");
    for (const w of words) {
      let at = s.indexOf(w);
      while (at >= 0) { for (let k = at; k < at + w.length; k++) mark[map[k]] = true; at = s.indexOf(w, at + w.length); }
    }
    let out = "", open = false;
    chars.forEach((c, i) => {
      if (mark[i] && !open) { out += "<mark>"; open = true; }
      if (!mark[i] && open) { out += "</mark>"; open = false; }
      out += escapeHtml(c);
    });
    return out + (open ? "</mark>" : "");
  }
  function navItem(p, words) {
    const home = p.id === "all";
    return h("button", {
      class: `nav-item${home ? " home" : ""}${p.id === S.preset ? " active" : ""}`, type: "button", "data-id": p.id, title: p.desc || p.label,
      onclick: () => { selectPreset(p.id); document.body.classList.remove("nav-open"); },
    },
      h("span", { class: "dot", style: { "--kc": home || p.icon === "star" ? "var(--k-tools)" : kc(p.icon) }, html: svg(p.icon) }),
      home ? h("span", { class: "grow" }, h("b", {}, p.label), h("small", {}, "Le format est reconnu tout seul"))
        : h("span", { class: "grow", html: highlight(p.label, words) }),
      p.fav ? h("span", { class: "fav-del", title: "Supprimer ce favori", html: svg("x"), onclick: (e) => { e.stopPropagation(); deleteFavorite(p.fav); } }) : null);
  }
  function renderNav() {
    const nav = $("#nav");
    nav.textContent = "";
    const words = norm(navQuery.trim()).split(/\s+/).filter(Boolean);
    if (!navOpen) {
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem("navOpen") || "null"); } catch { /* */ }
      navOpen = new Set(Array.isArray(saved) ? saved : ["Favoris"]);
    }
    const groups = [];
    for (const p of S.presets) {
      let g = groups.find((x) => x.name === (p.group || ""));
      if (!g) groups.push(g = { name: p.group || "", items: [] });
      g.items.push(p);
    }
    let shown = 0;
    for (const g of groups) {
      const items = words.length ? g.items.filter((p) => presetMatches(p, words)) : g.items;
      if (!items.length) continue;
      shown += items.length;
      if (!g.name) { items.forEach((p) => nav.append(navItem(p, words))); continue; }
      const open = words.length > 0 || navOpen.has(g.name);
      const box = h("div", { class: `nav-group${open ? "" : " closed"}` });
      box.append(
        h("button", {
          class: "nav-group-head", type: "button", "aria-expanded": String(open), style: { "--gc": kc(GROUP_COLOR[g.name] || "tools") },
          onclick: () => {
            if (words.length) return;
            const nowOpen = box.classList.toggle("closed") === false;
            if (nowOpen) navOpen.add(g.name); else navOpen.delete(g.name);
            box.firstChild.setAttribute("aria-expanded", String(nowOpen));
            saveNavOpen();
          },
        }, h("span", { class: "gdot" }), g.name, h("span", { class: "num" }, String(items.length)), icon("chev", "ic chev")),
        h("div", { class: "nav-items" }, items.map((p) => navItem(p, words))),
      );
      nav.append(box);
    }
    if (!shown) nav.append(h("div", { class: "nav-empty" }, "Aucun outil ne correspond.", h("br"), h("small", {}, "« Tous les fichiers » accepte tout.")));
  }

  function selectPreset(id) {
    S.preset = S.presetMap[id] ? id : "all";
    try { localStorage.setItem("preset", S.preset); } catch { /* */ }
    history.replaceState(null, "", `#${S.preset}`);
    const p = currentPreset();
    if (navOpen && p.group && !navOpen.has(p.group)) { navOpen.add(p.group); saveNavOpen(); }
    if (navQuery) { navQuery = ""; $("#nav-search").value = ""; }
    renderNav();
    renderLinkbar();
    $("#eyebrow").textContent = p.id === "all" ? "Atelier universel" : (p.group || "Outil");
    $("#title").textContent = p.title || p.label;
    $("#desc").textContent = p.desc || "";
    const input = $("#file-input");
    input.accept = p.accept ? p.accept.map((e) => `.${e}`).join(",") : "";
    for (const f of S.files) {
      if (busy(stateOf(f)) || !f.id) continue;
      const t = presetTarget(f, p);
      if (t) {
        f.target = t;
        if (p.options) Object.assign(f.options, p.options);
      }
    }
    render();
  }

  function renderTools() {
    const T = S.tools;
    const box = $("#tools");
    box.textContent = "";
    const pill = (ok, label, title) => h("span", { class: `tool${ok ? "" : " off"}`, title }, h("i"), label);
    box.append(
      pill(!!T.ffmpeg, "FFmpeg", T.ffmpeg ? `FFmpeg ${T.ffmpeg}` : "FFmpeg introuvable"),
      pill(!!T.libreoffice, "LibreOffice", T.libreoffice ? "Documents Office" : "Non installé"),
      pill(!!T.calibre, "Calibre", T.calibre ? "Ebooks" : "Non installé"),
    );
    if (T.gpu) box.append(pill(true, "GPU", T.gpu));
  }

  // ------------------------------------------------------------ démarrage
  function bindUi() {
    $("#btn-settings").innerHTML = `${svg("gear")}<span>Réglages</span>`;
    $("#btn-settings").onclick = openSettings;
    $("#btn-folder").innerHTML = `${svg("folder")}<span>Dossier de sortie</span>`;
    $("#btn-folder").title = "Ouvrir le dossier où sont enregistrés les fichiers convertis";
    $("#btn-history").title = "Historique des conversions";
    $("#btn-folder").onclick = () => api("/api/open-folder", {}).catch((e) => toast(e.message, "error"));
    $("#btn-history").innerHTML = `${svg("clock")}<span>Historique</span>`;
    $("#btn-history").onclick = openHistory;
    $("#btn-bulk").innerHTML = `${svg("sliders")}<span>Tout convertir en…</span>`;
    $("#btn-bulk").onclick = (e) => openBulk(e.currentTarget);
    $("#btn-clear").innerHTML = `${svg("trash")}<span>Vider la liste</span>`;
    $("#btn-clear").onclick = clearList;
    $("#btn-all").onclick = convertAll;
    $("#drag-glyph").innerHTML = `<svg viewBox="0 0 120 72" aria-hidden="true">${glyph("drag", 2, 2, 116, 68)}</svg>`;
    $("#link-icon").innerHTML = svg("link");
    $("#search-icon").innerHTML = svg("search");
    $("#btn-menu").innerHTML = svg("menu");
    $("#btn-menu").onclick = () => document.body.classList.toggle("nav-open");
    $("#scrim").onclick = () => document.body.classList.remove("nav-open");
    const navSearch = $("#nav-search");
    navSearch.addEventListener("input", () => { navQuery = navSearch.value; renderNav(); });
    navSearch.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const items = [...document.querySelectorAll("#nav .nav-item")];
        const best = items.find((b) => b.querySelector("mark")) || items[0];   // priorité au nom qui correspond
        if (best) best.click();
        navSearch.blur();
      }
      if (e.key === "Escape") { navSearch.value = ""; navQuery = ""; renderNav(); navSearch.blur(); }
      if (e.key === "ArrowDown") { e.preventDefault(); $("#nav .nav-item")?.focus(); }
    });
    $("#link-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const input = $("#link-input");
      addLink(input.value);
      input.value = "";
    });
    window.addEventListener("paste", (e) => {
      const t = e.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      const text = ((e.clipboardData && e.clipboardData.getData("text")) || "").trim();
      if (/^https?:\/\/\S+$/i.test(text)) { e.preventDefault(); addLink(text); }
    });
    const drop = $("#drop");
    drop.addEventListener("click", browse);
    drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); browse(); } });
    $("#file-input").addEventListener("change", (e) => { addLocalFiles(e.target.files); e.target.value = ""; });

    let depth = 0;
    const hasFiles = (e) => [...(e.dataTransfer?.types || [])].includes("Files");
    window.addEventListener("dragenter", (e) => { if (!hasFiles(e)) return; e.preventDefault(); depth++; document.body.classList.add("dragging"); });
    window.addEventListener("dragover", (e) => { if (!hasFiles(e)) return; e.preventDefault(); e.dataTransfer.dropEffect = "copy"; });
    window.addEventListener("dragleave", (e) => { if (!hasFiles(e)) return; depth = Math.max(0, depth - 1); if (!depth) document.body.classList.remove("dragging"); });
    window.addEventListener("drop", async (e) => {
      if (!hasFiles(e)) return;
      e.preventDefault();
      depth = 0;
      document.body.classList.remove("dragging");
      addLocalFiles(await filesFromDrop(e.dataTransfer));
    });
    window.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.key.toLowerCase() === "o") { e.preventDefault(); browse(); }
      if (e.ctrlKey && e.key === "Enter") { e.preventDefault(); convertAll(); }
      if (e.ctrlKey && e.key.toLowerCase() === "k") { e.preventDefault(); document.body.classList.add("nav-open"); navSearch.focus(); navSearch.select(); }
    });
    window.addEventListener("resize", closePicker);
    $("#content").addEventListener("scroll", closePicker, { passive: true });
    window.addEventListener("beforeunload", (e) => {
      if (Object.values(S.jobs).some((j) => j.status === "running" || j.status === "queued")) { e.preventDefault(); e.returnValue = ""; }
    });
    window.addEventListener("pagehide", () => { try { navigator.sendBeacon(`/api/bye?t=${encodeURIComponent(TOKEN)}`); } catch { /* */ } });
    setInterval(() => api("/api/heartbeat", {}).catch(() => {}), 30000);
    setInterval(async () => {                      // fichiers reçus par « Envoyer vers » ou le raccourci
      try {
        const res = await api("/api/inbox");
        if (res.files && res.files.length) {
          res.files.forEach(addRecord);
          render();
          toast(`${res.files.length} fichier${res.files.length > 1 ? "s" : ""} ajouté${res.files.length > 1 ? "s" : ""}.`, "ok");
        }
      } catch { /* */ }
    }, 2500);
  }

  async function init() {
    bindUi();
    let st;
    try { st = await api("/api/state"); } catch (e) { toast(`Serveur injoignable : ${e.message}`, "error"); return; }
    Object.assign(S, {
      presets: st.presets, options: st.options, combine: st.combine, groups: st.groups, families: st.families,
      extFamily: st.ext_family, tools: st.tools, settings: st.settings,
    });
    S.presetMap = Object.fromEntries(S.presets.map((p) => [p.id, p]));
    for (const j of st.jobs) S.jobs[j.id] = j;
    S.basePresets = S.presets;
    S.presets = [...S.basePresets.slice(0, 1), ...favoritePresets(), ...S.basePresets.slice(1)];
    S.presetMap = Object.fromEntries(S.presets.map((p) => [p.id, p]));
    for (const rec of st.files) addRecord(rec);
    const lastJob = {};
    for (const j of st.jobs.sort((a, b) => a.created - b.created)) {
      if (j.mode === "single") lastJob[j.file_ids[0]] = j.id;
      else S.combos.unshift({ jobId: j.id, mode: j.mode, count: j.file_ids.length });
    }
    for (const f of S.files) if (lastJob[f.id]) { f.jobId = lastJob[f.id]; const j = S.jobs[f.jobId]; if (j.target) f.target = j.target; }
    renderNav();
    renderTools();
    let saved = location.hash.slice(1);
    if (!S.presetMap[saved]) { try { saved = localStorage.getItem("preset") || "all"; } catch { saved = "all"; } }
    selectPreset(saved);
    poll();
  }

  init();
})();
