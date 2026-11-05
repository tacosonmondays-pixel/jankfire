// Chunky toy-like icons + colours for every game mode (end-of-match vote cards, the menu's event card).
// Plain SVG strings, drawn for JANKFIRE: thick black outlines, flat fills, one glossy highlight.
const K = 'stroke="#120818" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"';
const shine = (x, y, rx, ry, r = -25) => `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="#fff" opacity=".55" transform="rotate(${r} ${x} ${y})"/>`;
const ICONS = {
  dm: `<circle cx="50" cy="50" r="30" fill="#ff4f6a" ${K}/><circle cx="50" cy="50" r="17" fill="#fff" ${K}/><circle cx="50" cy="50" r="6" fill="#ff4f6a" ${K}/>
    <path d="M50 8v22M50 70v22M8 50h22M70 50h22" ${K} stroke-width="7"/>${shine(38, 33, 9, 4)}`,
  tdm: `<path d="M14 22l28-6v34c0 17-12 26-28 32z" fill="#ff4f4f" ${K}/><path d="M86 22l-28-6v34c0 17 12 26 28 32z" fill="#4fa8ff" ${K}/>
    <path d="M40 74l20-48M60 74l-20-48" ${K} stroke-width="6"/>${shine(24, 32, 6, 3, -70)}${shine(76, 32, 6, 3, 70)}`,
  tags: `<path d="M50 6c-6 10-6 16 0 22" fill="none" ${K} stroke-dasharray="1 7"/><rect x="26" y="26" width="48" height="64" rx="14" fill="#d8dde6" ${K}/>
    <circle cx="50" cy="38" r="5" fill="#120818"/><path d="M36 58h28M36 70h20" ${K}/>${shine(40, 44, 8, 3, -60)}`,
  bomb: `<circle cx="44" cy="58" r="30" fill="#2a2a38" ${K}/><rect x="52" y="22" width="16" height="14" rx="3" fill="#8a8a9a" ${K} transform="rotate(35 60 29)"/>
    <path d="M66 22c6-8 12-10 18-6" fill="none" ${K}/><path d="M84 8l3 8 8 2-7 4 1 8-6-5-7 3 3-8-5-6 8 1z" fill="#ffe14d" ${K} stroke-width="3"/>${shine(32, 46, 9, 5)}`,
  rand: `<rect x="20" y="20" width="60" height="60" rx="12" fill="#fff" ${K} transform="rotate(12 50 50)"/>
    <g fill="#ff4fd8" transform="rotate(12 50 50)"><circle cx="35" cy="35" r="6"/><circle cx="50" cy="50" r="6"/><circle cx="65" cy="65" r="6"/><circle cx="65" cy="35" r="6"/><circle cx="35" cy="65" r="6"/></g>`,
  gun: `<path d="M22 92V14M78 92V14" ${K} stroke-width="7"/><path d="M22 30h56M22 50h56M22 70h56" ${K}/>
    <path d="M50 8l14 16h-8v14h-12V24h-8z" fill="#ffe14d" ${K} stroke-width="4"/>`,
  inf: `<path d="M50 14c22 0 34 16 34 34 0 20-14 36-34 36S16 68 16 48c0-18 12-34 34-34z" fill="#7dff4f" ${K}/>
    <path d="M30 40l12 10M42 40L30 50M58 40l12 10M70 40L58 50" ${K}/><path d="M32 66c6-6 30-6 36 0" fill="none" ${K}/><path d="M40 64v6M50 63v7M60 64v6" ${K} stroke-width="3"/>${shine(34, 26, 9, 4)}`,
  spoons: `<ellipse cx="50" cy="30" rx="18" ry="22" fill="#d8dde6" ${K}/><path d="M50 52v40" ${K} stroke-width="12"/><path d="M50 52v40" stroke="#d8dde6" stroke-width="4" stroke-linecap="round"/>
    ${shine(43, 22, 6, 9, 15)}`,
  duckrain: `<path d="M20 60c0-14 12-22 26-18 2-14 12-22 22-20 12 2 16 16 10 26l12 2c-2 6-8 8-14 8 2 16-10 26-28 26-18 0-28-10-28-24z" fill="#ffe14d" ${K}/>
    <circle cx="66" cy="36" r="4" fill="#120818"/><path d="M80 48l12 2c-2 6-8 8-14 8" fill="#ff9a3c" ${K} stroke-width="4"/>${shine(36, 56, 10, 4)}
    <path d="M14 14l4 10M34 6l4 10M86 76l4 10" ${K} stroke="#4fd8ff" stroke-width="4"/>`,
  lava: `<path d="M50 6c6 18 26 24 26 48 0 18-12 32-26 32S24 72 24 54c0-12 8-18 10-28 6 8 6 14 6 14s4-18 10-34z" fill="#ff5a1a" ${K}/>
    <path d="M50 44c4 10 12 12 12 24 0 8-6 14-12 14s-12-6-12-14c0-8 6-12 12-24z" fill="#ffe14d" ${K} stroke-width="4"/>`,
  oitc: `<rect x="38" y="38" width="24" height="52" rx="3" fill="#e0a040" ${K}/><path d="M38 38c0-20 6-30 12-32 6 2 12 12 12 32z" fill="#c8ccd2" ${K}/>
    <path d="M38 80h24" ${K}/>${shine(45, 22, 3, 8, 10)}<text x="78" y="34" font-size="26" font-weight="700" fill="#ff4fd8" stroke="#120818" stroke-width="2" font-family="Comic Neue, Comic Sans MS, cursive">1</text>`,
};
// card colours: [background top, bottom]. unknown future modes get a pink default and their initials
const COLORS = {
  dm: ['#ff7a9a', '#b0103a'], tdm: ['#9a7dff', '#3a1a9a'], tags: ['#4fffb0', '#0a7a5a'], bomb: ['#ffb04f', '#9a3a0a'],
  rand: ['#ff9ad5', '#a0106a'], gun: ['#ffe14d', '#a07a00'], inf: ['#9aff4f', '#2a6a0a'], spoons: ['#c8f0ff', '#3a7aa0'],
  duckrain: ['#7ad8ff', '#1a5aa0'], lava: ['#ff7a3a', '#7a0a0a'], oitc: ['#e0c080', '#5a3a1a'],
};
export function modeColors(g) { return COLORS[g] || ['#ff4fd8', '#5a0a4a']; }
export function modeIcon(g, name = '') {
  const body = ICONS[g] || `<text x="50" y="64" text-anchor="middle" font-size="40" font-weight="700" fill="#fff" stroke="#120818" stroke-width="3" font-family="Comic Neue, Comic Sans MS, cursive">${String(name).replace(/[^A-Za-z ]/g, '').split(' ').map((w) => w[0] || '').join('').slice(0, 2).toUpperCase() || '?'}</text>`;
  return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${body}</svg>`;
}
// a card thumbnail: the mode's colours, a loud pattern, the icon big in the middle
export function modeThumb(g, name) {
  const [a, b] = modeColors(g);
  const d = document.createElement('div');
  d.className = 'mthumb';
  d.style.setProperty('--a', a); d.style.setProperty('--b', b);
  d.innerHTML = modeIcon(g, name);
  return d;
}
