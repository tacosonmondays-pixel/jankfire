// Name cards: a 256x64 banner people see when you kill them (and in replays / scoreboard).
// Draw one yourself or upload a picture. Saved as a small crusty JPEG data url.
export const CW = 256, CH = 64;
const cache = new Map();

function rng(seed) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
  return () => { h += 0x6d2b79f5; let t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

// backgrounds you can start from in the editor (also used for default cards)
export const BACKGROUNDS = {
  stripes(x, c, r) { x.fillStyle = '#120818'; x.fillRect(0, 0, CW, CH); x.fillStyle = c; for (let i = -CH; i < CW; i += 18) { x.beginPath(); x.moveTo(i, CH); x.lineTo(i + 9, CH); x.lineTo(i + 9 + CH, 0); x.lineTo(i + CH, 0); x.fill(); } },
  missing(x) { for (let i = 0; i < CW / 16; i++) for (let j = 0; j < CH / 16; j++) { x.fillStyle = (i + j) % 2 ? '#ff00dc' : '#000'; x.fillRect(i * 16, j * 16, 16, 16); } },
  sunset(x) { const g = x.createLinearGradient(0, 0, 0, CH); g.addColorStop(0, '#2a0a4a'); g.addColorStop(0.55, '#ff4fd8'); g.addColorStop(1, '#ffb31a'); x.fillStyle = g; x.fillRect(0, 0, CW, CH); x.fillStyle = '#ffe14d'; x.beginPath(); x.arc(CW * 0.75, CH * 0.8, 22, 0, Math.PI * 2); x.fill(); x.fillStyle = '#1a0a2a'; for (let i = 0; i < 6; i++) x.fillRect(0, CH - 4 - i * 6, CW, 2); },
  stars(x, c, r) { x.fillStyle = '#05030f'; x.fillRect(0, 0, CW, CH); for (let i = 0; i < 90; i++) { x.fillStyle = r() < 0.2 ? c : '#fff'; const s = r() < 0.1 ? 2 : 1; x.fillRect((r() * CW) | 0, (r() * CH) | 0, s, s); } },
  flames(x) { const g = x.createLinearGradient(0, CH, 0, 0); g.addColorStop(0, '#ffe14d'); g.addColorStop(0.4, '#ff6a1a'); g.addColorStop(1, '#3a0000'); x.fillStyle = g; x.fillRect(0, 0, CW, CH); x.fillStyle = '#1a0000'; for (let i = 0; i < CW; i += 12) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i + 6, 10 + ((i * 7) % 20)); x.lineTo(i + 12, 0); x.fill(); } },
  static(x, c, r) { const im = x.createImageData(CW, CH); for (let i = 0; i < im.data.length; i += 4) { const v = (r() * 255) | 0; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; } x.putImageData(im, 0, 0); },
  grid(x, c) { x.fillStyle = '#12001f'; x.fillRect(0, 0, CW, CH); x.strokeStyle = c; x.lineWidth = 1; for (let i = 0; i <= 16; i++) { x.beginPath(); x.moveTo(CW / 2, 20); x.lineTo(i * 16 * 2 - CW / 2, CH); x.stroke(); } for (let j = 0; j < 6; j++) { const y = 20 + Math.pow(j / 6, 1.8) * 44; x.beginPath(); x.moveTo(0, y); x.lineTo(CW, y); x.stroke(); } },
  camo(x, c, r) { x.fillStyle = '#4a5a2a'; x.fillRect(0, 0, CW, CH); const cols = ['#2e3a1a', '#6a7a3a', '#3a2a1a']; for (let i = 0; i < 40; i++) { x.fillStyle = cols[i % 3]; x.beginPath(); x.ellipse(r() * CW, r() * CH, 6 + r() * 16, 4 + r() * 8, r() * 3, 0, Math.PI * 2); x.fill(); } },
  plain(x, c) { x.fillStyle = c; x.fillRect(0, 0, CW, CH); },
};

// people without a custom card get a generated one, seeded by their name
export function defaultCard(name, color) {
  const key = name + '|' + color;
  if (cache.has(key)) return cache.get(key);
  const cv = document.createElement('canvas');
  cv.width = CW; cv.height = CH;
  const x = cv.getContext('2d');
  const r = rng(key);
  const keys = ['stripes', 'stars', 'grid', 'sunset', 'flames', 'camo'];
  BACKGROUNDS[keys[(r() * keys.length) | 0]](x, color || '#ff4fd8', r);
  x.fillStyle = 'rgba(0,0,0,0.35)';
  x.fillRect(0, CH - 22, CW, 22);
  const url = cv.toDataURL('image/jpeg', 0.8);
  cache.set(key, url);
  return url;
}

// <div class="ncard"> with the picture, the name and a little line of text
export function cardEl(url, name, sub, color) {
  const d = document.createElement('div');
  d.className = 'ncard';
  d.style.setProperty('--c', color || '#ff4fd8');
  const img = document.createElement('img');
  img.src = url;
  img.alt = '';
  const n = document.createElement('div');
  n.className = 'nc-name';
  n.textContent = name || '';
  n.style.color = color || '#fff';
  d.append(img, n);
  if (sub) { const s = document.createElement('div'); s.className = 'nc-sub'; s.textContent = sub; d.append(s); }
  return d;
}

// shrink until it fits the server limit
export function exportCard(cv) {
  for (const q of [0.8, 0.65, 0.5, 0.35, 0.2]) {
    const u = cv.toDataURL('image/jpeg', q);
    if (u.length <= 22000) return u;
  }
  return '';
}

// ------------------------------------------------------------ editor
export function initCardEditor({ get, save, toast }) {
  const $ = (id) => document.getElementById(id);
  const cv = $('ncCanvas');
  const x = cv.getContext('2d', { willReadFrequently: true });
  let tool = 'brush', color = '#ffe14d', size = 3, down = false, lastP = null;
  const undo = [];
  const PALETTE = ['#000000', '#ffffff', '#ff4fd8', '#4fd8ff', '#ffe14d', '#7dff4f', '#ff7a1a', '#b07dff', '#ff3030', '#3a3a44', '#8a5a2b', '#0a57c2'];

  function snapshot() { undo.push(x.getImageData(0, 0, CW, CH)); if (undo.length > 25) undo.shift(); }
  function load(url) {
    x.fillStyle = '#120818'; x.fillRect(0, 0, CW, CH);
    if (!url) { BACKGROUNDS.stripes(x, '#ff4fd8', rng('x')); return; }
    const img = new Image();
    img.onload = () => x.drawImage(img, 0, 0, CW, CH);
    img.src = url;
  }
  function pos(e) {
    const b = cv.getBoundingClientRect();
    return [((e.clientX - b.left) / b.width) * CW, ((e.clientY - b.top) / b.height) * CH];
  }
  function dot(p) {
    x.fillStyle = tool === 'erase' ? '#000000' : color;
    if (tool === 'spray') {
      for (let i = 0; i < size * 3; i++) { const a = Math.random() * 6.28, rr = Math.random() * size * 2.5; x.fillRect((p[0] + Math.cos(a) * rr) | 0, (p[1] + Math.sin(a) * rr) | 0, 1, 1); }
      return;
    }
    const s = Math.max(1, size);
    x.fillRect(Math.round(p[0] - s / 2), Math.round(p[1] - s / 2), s, s);
  }
  function line(a, b) {
    const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1])));
    for (let i = 0; i <= n; i++) dot([a[0] + ((b[0] - a[0]) * i) / n, a[1] + ((b[1] - a[1]) * i) / n]);
  }
  function fill(p) {
    const im = x.getImageData(0, 0, CW, CH), d = im.data;
    const sx = p[0] | 0, sy = p[1] | 0, i0 = (sy * CW + sx) * 4;
    const t = [d[i0], d[i0 + 1], d[i0 + 2]];
    const c = [parseInt(color.slice(1, 3), 16), parseInt(color.slice(3, 5), 16), parseInt(color.slice(5, 7), 16)];
    const near = (i) => Math.abs(d[i] - t[0]) + Math.abs(d[i + 1] - t[1]) + Math.abs(d[i + 2] - t[2]) < 60;
    if (Math.abs(t[0] - c[0]) + Math.abs(t[1] - c[1]) + Math.abs(t[2] - c[2]) < 3) return;
    const seen = new Uint8Array(CW * CH), st = [[sx, sy]];
    while (st.length) {
      const [px, py] = st.pop();
      if (px < 0 || py < 0 || px >= CW || py >= CH) continue;
      const k = py * CW + px;
      if (seen[k]) continue;
      seen[k] = 1;
      const i = k * 4;
      if (!near(i)) continue;
      d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = 255;
      st.push([px + 1, py], [px - 1, py], [px, py + 1], [px, py - 1]);
    }
    x.putImageData(im, 0, 0);
  }
  function stamp(p) {
    const text = $('ncText').value.trim();
    if (!text) { toast('type something in the text box first'); return; }
    const fs = 6 + size * 3;
    x.font = `bold ${fs}px "Comic Neue", sans-serif`;
    x.textBaseline = 'middle';
    x.lineWidth = Math.max(2, fs / 6);
    x.strokeStyle = '#000';
    x.strokeText(text, p[0], p[1]);
    x.fillStyle = color;
    x.fillText(text, p[0], p[1]);
  }

  cv.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    cv.setPointerCapture(e.pointerId);
    snapshot();
    const p = pos(e);
    if (tool === 'fill') { fill(p); return; }
    if (tool === 'text') { stamp(p); return; }
    down = true; lastP = p; dot(p);
  });
  cv.addEventListener('pointermove', (e) => { if (!down) return; const p = pos(e); line(lastP, p); lastP = p; });
  addEventListener('pointerup', () => { down = false; });

  const tools = document.querySelectorAll('#ncTools [data-tool]');
  for (const b of tools) b.addEventListener('click', () => { tool = b.dataset.tool; for (const o of tools) o.classList.toggle('on', o === b); });
  $('ncSize').addEventListener('input', () => { size = Number($('ncSize').value); });
  $('ncColor').addEventListener('input', () => { color = $('ncColor').value; });
  const pal = $('ncPalette');
  for (const c of PALETTE) {
    const b = document.createElement('button');
    b.className = 'swatch'; b.style.background = c; b.title = c;
    b.addEventListener('click', () => { color = c; $('ncColor').value = c; });
    pal.append(b);
  }
  const bgs = $('ncBgs');
  for (const k of Object.keys(BACKGROUNDS)) {
    const b = document.createElement('button');
    b.className = 'chip'; b.textContent = k;
    b.addEventListener('click', () => { snapshot(); BACKGROUNDS[k](x, color, rng(k + Math.random())); });
    bgs.append(b);
  }
  $('ncUpload').addEventListener('click', () => $('ncFile').click());
  $('ncFile').addEventListener('change', () => {
    const f = $('ncFile').files[0];
    $('ncFile').value = '';
    if (!f) return;
    if (!f.type.startsWith('image/')) { toast('that is not a picture'); return; }
    if (f.size > 15 * 1024 * 1024) { toast('picture too big (15 MB max)'); return; }
    const url = URL.createObjectURL(f);
    const img = new Image();
    img.onload = () => {
      snapshot();
      // crop to fill the banner
      const k = Math.max(CW / img.width, CH / img.height);
      const w = img.width * k, h = img.height * k;
      x.fillStyle = '#000'; x.fillRect(0, 0, CW, CH);
      x.drawImage(img, (CW - w) / 2, (CH - h) / 2, w, h);
      URL.revokeObjectURL(url);
      toast('uploaded. draw on it if you want, then SAVE');
    };
    img.onerror = () => { URL.revokeObjectURL(url); toast("couldn't read that picture"); };
    img.src = url;
  });
  $('ncUndo').addEventListener('click', () => { const u = undo.pop(); if (u) x.putImageData(u, 0, 0); });
  $('ncClear').addEventListener('click', () => { snapshot(); x.fillStyle = '#000'; x.fillRect(0, 0, CW, CH); });
  $('ncReset').addEventListener('click', () => { save(''); toast('back to the generated card'); });
  $('ncSave').addEventListener('click', () => {
    const url = exportCard(cv);
    if (!url) { toast("card too detailed to save, simplify it"); return; }
    save(url);
    toast('name card saved');
  });
  return { open() { undo.length = 0; load(get()); } };
}
