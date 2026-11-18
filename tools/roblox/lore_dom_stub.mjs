// just enough DOM for the web's model code in Node. canvas 2D contexts record their first full-size fill (the panel's
// background colour), which the dump uses as the flat colour of a canvas-textured panel
globalThis.__canvases = [];
function ctx2d(canvas) {
  const st = { fillStyle: '#000', canvas };
  const fns = {
    fillRect(x, y, w, h) { if (!canvas.bg && w >= canvas.width * 0.9 && h >= canvas.height * 0.9) canvas.bg = String(st.fillStyle); if (!canvas.first) canvas.first = String(st.fillStyle); },
    fill() { if (!canvas.first) canvas.first = String(st.fillStyle); },
    measureText: () => ({ width: 10 }),
    createImageData: (w, h) => ({ width: w || 1, height: h || 1, data: new Uint8ClampedArray((w || 1) * (h || 1) * 4) }),
    getImageData: (x, y, w, h) => ({ width: w || 1, height: h || 1, data: new Uint8ClampedArray((w || 1) * (h || 1) * 4) }),
    createLinearGradient: () => ({ addColorStop() {} }), createRadialGradient: () => ({ addColorStop() {} }), createPattern: () => ({}),
  };
  return new Proxy(st, { get: (t, k) => (k in fns ? fns[k] : k in t ? t[k] : () => {}), set: (t, k, v) => { t[k] = v; return true; } });
}
function el(tag) {
  const e = { tagName: tag, width: 64, height: 64, style: {}, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } }, dataset: {}, addEventListener() {}, removeEventListener() {}, append() {}, appendChild() {}, prepend() {}, remove() {}, setAttribute() {}, getAttribute() { return null; }, querySelector() { return null; }, querySelectorAll() { return []; }, children: [], toDataURL() { return ''; } };
  if (tag === 'canvas') { let c; e.getContext = () => (c ||= ctx2d(e)); globalThis.__canvases.push(e); } else e.getContext = () => ctx2d(e);
  return e;
}
globalThis.document = { createElement: el, createElementNS: (ns, t) => el(t), getElementById: () => null, querySelector: () => null, querySelectorAll: () => [], body: el('body'), head: el('head'), addEventListener() {}, documentElement: el('html'), fonts: { load: async () => {}, ready: Promise.resolve() } };
globalThis.window = globalThis; globalThis.self = globalThis;
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {};
globalThis.innerWidth = 1280; globalThis.innerHeight = 720; globalThis.devicePixelRatio = 1;
globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} }; globalThis.sessionStorage = globalThis.localStorage;
globalThis.requestAnimationFrame = () => 0;
globalThis.Image = class { constructor() { this.width = 1; this.height = 1; } set src(v) {} };
globalThis.AudioContext = class {}; globalThis.fetch = async () => ({ ok: false, json: async () => ({}), arrayBuffer: async () => new ArrayBuffer(0) });
globalThis.location = { search: '', hash: '', href: 'http://x/', origin: 'http://x', pathname: '/' };
globalThis.matchMedia = () => ({ matches: false, addEventListener() {} });
// a fixed seed: the paperwork's tilt, the jank, Todd's paper balls come out the same every run
let seed = 12345; Math.random = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
