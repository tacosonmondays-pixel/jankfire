// Hand-cut fleshy slabs behind the UI's panels, cards and buttons (the owner: "the ui looks really flat, make it more
// organic"). organic(el, opts) puts an svg under el's content: a lumpy outline seeded per element (so it holds still),
// the zine's hard offset shadow cut to the same shape, a dark bumpy fill (text stays readable on it), a wet fleshy rim,
// a few veins, rivets and surgical staples, and fleshy sockets around pictures (opts.holes, clipped to match).
// Colours come from CSS variables on el (--rim, --fill, --shd, --band), so :hover / .mine just restyle; the shape is
// only redrawn when el's size changes (one shared ResizeObserver).
import { perim } from './flesh.js';

let ids = 0;
const NS = 'http://www.w3.org/2000/svg';
const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver((list) => { for (const e of list) draw(e.target); }) : null;
const rng = (seed) => () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

const live = new Set();
let calls = 0;
export function organic(el, o = {}) {
  if (!el) return el;
  if (++calls % 24 === 0) for (const e of live) if (e._orgDrawn && !e.isConnected) { live.delete(e); if (ro) ro.unobserve(e); } // only ones already drawn: a new card is still detached while it's built
  live.add(el);
  el._org = { pad: 9, ...o };
  if (!el.dataset.orgSeed) el.dataset.orgSeed = String(1 + Math.floor(Math.random() * 2e9));
  el.classList.add('org');
  if (ro) ro.observe(el); else requestAnimationFrame(() => draw(el));
  return el;
}

// redraw now (contents with sockets were rebuilt but the size may not have changed)
export function organicRedraw(el) { if (el && el._org) { delete el.dataset.orgSize; draw(el); } }

// a lumpy outline around a w x h box at (x0, y0): almost-square corners, hand-cut jitter, a few soft lumps and bites
function outline(w, h, x0, y0, o, rnd) {
  const P = perim(x0, y0, x0 + w, y0 + h, Math.max(1, Math.min(o.corner ?? 4, w / 3, h / 3)));
  const step = Math.max(4, o.step || (Math.min(w, h) < 70 ? 5 : 8));
  const ph = [rnd() * 6.28, rnd() * 6.28];
  const wob = o.wob ?? 1.5, la = o.lumpA ?? 3.2;
  const lumps = Array.from({ length: o.lumps ?? 3 }, () => ({ u: rnd() * P.L, w: 8 + rnd() * 24, a: (rnd() < 0.72 ? 1 : -0.7) * (1 + rnd() * la) }));
  let d = '';
  for (let u = 0, i = 0; u < P.L; u += step, i++) {
    const [x, y, nx, ny] = P.at(u);
    let off = Math.sin(u / 23 + ph[0]) * wob * 0.6 + Math.sin(u / 7.3 + ph[1]) * wob * 0.3 + (rnd() - 0.5) * wob * 0.6;
    for (const b of lumps) { let q = Math.abs(u - b.u); q = Math.min(q, P.L - q); off += b.a * Math.exp(-(q * q) / (2 * b.w * b.w)); }
    d += `${i ? 'L' : 'M'}${(x - nx * off).toFixed(1)} ${(y - ny * off).toFixed(1)}`; // perim's normal points in: out is minus
  }
  return { d: d + 'Z', P };
}

function draw(el) {
  const o = el._org;
  if (!o) return;
  if (!el.isConnected) { if (el._orgDrawn) { live.delete(el); if (ro) ro.unobserve(el); } return; }
  const w = el.offsetWidth, h = el.offsetHeight;
  if (w < 4 || h < 4) return;
  if (getComputedStyle(el).position === 'static') el.style.position = 'relative'; // the slab is positioned against its host, not some ancestor
  const key = `${w}x${h}`;
  if (el.dataset.orgSize === key && el.querySelector(':scope > .org-bg')) return;
  el.dataset.orgSize = key;
  const rnd = rng(Number(el.dataset.orgSeed) || 7);
  const pad = o.pad, [sx, sy] = o.shadow || [7, 7], rimW = o.rim ?? 5;
  const bl = el.clientLeft, bt = el.clientTop; // abs children sit on the padding box: the svg starts this much further out
  const W = w + pad * 2 + Math.max(0, sx), H = h + pad * 2 + Math.max(0, sy);
  const id = `og${++ids}-`;
  const body = outline(w, h, pad, pad, o, rnd).d;
  let defs = `<clipPath id="${id}c"><path d="${body}"/></clipPath>`;
  let art = '';
  if (o.tex !== false) {
    const s = Math.floor(rnd() * 999);
    defs += `<filter id="${id}b" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="${o.bf || 0.03}" numOctaves="3" seed="${s}" result="n"/>
      <feDiffuseLighting in="n" surfaceScale="2" lighting-color="#fff" result="l"><feDistantLight azimuth="235" elevation="57"/></feDiffuseLighting><feComposite in="l" in2="SourceAlpha" operator="in"/></filter>
      <filter id="${id}w" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".04 .055" numOctaves="2" seed="${s + 1}" result="n"/>
      <feDiffuseLighting in="n" surfaceScale="3.2" lighting-color="#fff" result="l"><feDistantLight azimuth="235" elevation="50"/></feDiffuseLighting>
      <feComposite in="l" in2="SourceGraphic" operator="arithmetic" k1="1.18" k2="0" k3="0" k4="0" result="t"/>
      <feSpecularLighting in="n" surfaceScale="4" specularConstant=".55" specularExponent="28" lighting-color="#fff" result="sp"><feDistantLight azimuth="235" elevation="55"/></feSpecularLighting>
      <feComposite in="sp" in2="SourceAlpha" operator="in" result="sp2"/><feComposite in="t" in2="sp2" operator="arithmetic" k1="0" k2="1" k3=".6" k4="0" result="a"/>
      <feComposite in="a" in2="SourceAlpha" operator="in"/></filter>`;
  }
  // bands (a header strip or a side strip in --band), clipped to the body
  if (o.band) art += `<rect x="0" y="0" width="${W}" height="${pad + o.band}" style="fill:var(--band, var(--rim))" clip-path="url(#${id}c)"/>`;
  if (o.bandL) art += `<rect x="0" y="0" width="${pad + o.bandL}" height="${H}" style="fill:var(--band, var(--rim))" clip-path="url(#${id}c)"/>`;
  if (o.tex !== false) art += `<path d="${body}" fill="#fff" opacity="${o.texA ?? 0.07}" filter="url(#${id}b)"/>`;
  // depth: the slab is thick and puffy, lit from the top left (an inner light edge there, a shaded one bottom right)
  if (o.bevel ?? o.tex !== false) art += `<g clip-path="url(#${id}c)" fill="none" stroke-width="6"><path d="${body}" transform="translate(3 3)" stroke="#fff" opacity=".13"/><path d="${body}" transform="translate(-3 -3)" stroke="#000" opacity=".38"/></g>`;
  // veins under the skin: a couple of thin wobbly lines near the rim
  if (o.bits !== false && o.veins !== false && w > 90 && h > 60) {
    // only up the left and right sides, where there's no text, and never more than ~40% of the height
    const x0 = pad + rimW + 3, y0 = pad + rimW + 3, iw = w - 2 * rimW - 6, ih = h - 2 * rimW - 6;
    const P = perim(x0, y0, x0 + iw, y0 + ih, 2);
    let v = '';
    for (let k = 0; k < 2; k++) {
      const right = (k + Math.floor(rnd() * 2)) % 2 === 0, side0 = right ? iw + Math.PI : 2 * iw + ih + 3 * Math.PI; // perim's segment starts (corner r = 2)
      const len = ih * (0.18 + rnd() * 0.22), u0 = side0 + ih * (0.08 + rnd() * 0.5), ph = rnd() * 6;
      let p = '';
      let mid = null;
      for (let t = 0; t <= len; t += 6) {
        const [x, y, nx, ny] = P.at(u0 + t), dd = 1.5 + Math.sin(t / 9 + ph) * 1.6, X = x + nx * dd, Y = y + ny * dd;
        p += `${t ? 'L' : 'M'}${X.toFixed(1)} ${Y.toFixed(1)}`;
        if (!mid && t >= len * 0.45) mid = [X, Y, nx, ny];
      }
      if (mid) { const [X, Y, nx, ny] = mid, bl2 = 5 + rnd() * 6; p += `M${X.toFixed(1)} ${Y.toFixed(1)}Q${(X + nx * bl2 * 0.6 + (rnd() - 0.5) * 8).toFixed(1)} ${(Y + ny * bl2 * 0.6 + (rnd() - 0.5) * 8).toFixed(1)} ${(X + nx * bl2).toFixed(1)} ${(Y + ny * bl2).toFixed(1)}`; } // a branch
      v += `<path d="${p}" fill="none" style="stroke:var(--rim)" stroke-width="${(1.1 + rnd() * 0.8).toFixed(1)}" stroke-linecap="round" opacity=".55"/>`;
    }
    art += `<g clip-path="url(#${id}c)">${v}</g>`;
  }
  // the rim: an ink edge, then the fleshy band on it
  const wet = o.wet ?? o.tex !== false;
  const dash = Array.from({ length: 6 }, () => Math.round(4 + rnd() * 22)).join(' ');
  const rim = `<path d="${body}" fill="none" stroke="#000" stroke-width="${rimW + 3.5}" stroke-linejoin="round"/>
    <path d="${body}" fill="none" style="stroke:var(--rim)" stroke-width="${rimW}" stroke-linejoin="round" ${wet ? `filter="url(#${id}w)"` : ''}/>
    ${wet ? `<path d="${body}" transform="translate(-1 -1.2)" fill="none" stroke="#fff" stroke-width="1.3" stroke-dasharray="${dash}" stroke-linecap="round" opacity=".45"/>` : ''}`;
  // sockets: each picture sits in a fleshy hole. the picture is clipped to a lumpy edge, the ring is the same shape a
  // few px bigger (so it shows around the picture, not under it). layout offsets, so rotated cards line up too
  let sockets = '';
  for (const hole of o.holes || []) {
    if (!hole || !hole.isConnected) continue;
    let x = 0, y = 0, n = hole;
    while (n && n !== el) { x += n.offsetLeft + (n !== hole ? n.clientLeft : 0); y += n.offsetTop + (n !== hole ? n.clientTop : 0); n = n.offsetParent; }
    const hw = hole.offsetWidth, hh = hole.offsetHeight;
    if (n !== el || hw < 8 || hh < 8) continue;
    const hs = outline(hw, hh, 0, 0, { wob: 1.1, lumps: 2, lumpA: 1.6, corner: 3, step: 6 }, rnd).d;
    hole.style.clipPath = `path('${hs}')`;
    const kx = (hw + 7) / hw, ky = (hh + 7) / hh, cx = hw / 2, cy = hh / 2;
    sockets += `<g transform="translate(${(pad + bl + x).toFixed(1)} ${(pad + bt + y).toFixed(1)}) translate(${cx} ${cy}) scale(${kx.toFixed(4)} ${ky.toFixed(4)}) translate(${-cx} ${-cy})">
      <path d="${hs}" fill="#000" stroke="#000" stroke-width="5" vector-effect="non-scaling-stroke"/>
      <path d="${hs}" fill="none" style="stroke:var(--rim)" stroke-width="2" vector-effect="non-scaling-stroke" opacity=".9"/></g>`;
  }
  // hardware: two rivets, a surgical staple or two across the rim
  let hw = '';
  if (o.bits !== false && w > 60 && h > 40) {
    const corners = [[pad + rimW + 5, pad + rimW + 5], [pad + w - rimW - 5, pad + rimW + 5], [pad + w - rimW - 5, pad + h - rimW - 5], [pad + rimW + 5, pad + h - rimW - 5]];
    const a = Math.floor(rnd() * 4), b = (a + 1 + Math.floor(rnd() * 3)) % 4;
    for (const i of o.rivets || [a, b]) { const [x, y] = corners[i]; hw += `<circle cx="${x}" cy="${y}" r="3.3" fill="#c8ccd6" stroke="#000" stroke-width="1.6"/><circle cx="${x - 1}" cy="${y - 1}" r="1" fill="#fff"/>`; }
    if (w > 160) { // a pair of surgical staples closing a seam in the rim, seen from above: a bar across, a hole each end
      const P = perim(pad, pad, pad + w, pad + h, 2), u = P.L * (0.15 + rnd() * 0.7), L = rimW + 8;
      for (const du of [-4, 4]) {
        const [x, y, nx, ny] = P.at(u + du), a1 = [x - nx * L * 0.5, y - ny * L * 0.5], a2 = [x + nx * L * 0.5, y + ny * L * 0.5];
        const d = `M${a1[0].toFixed(1)} ${a1[1].toFixed(1)}L${a2[0].toFixed(1)} ${a2[1].toFixed(1)}`;
        hw += `<circle cx="${a1[0].toFixed(1)}" cy="${a1[1].toFixed(1)}" r="2.1" fill="#3a0010"/><circle cx="${a2[0].toFixed(1)}" cy="${a2[1].toFixed(1)}" r="2.1" fill="#3a0010"/>
          <path d="${d}" stroke="#000" stroke-width="3.6" stroke-linecap="round"/><path d="${d}" stroke="#e4e8f0" stroke-width="1.6" stroke-linecap="round"/>`;
      }
    }
  }
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('class', 'org-bg');
  svg.setAttribute('width', W); svg.setAttribute('height', H);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('aria-hidden', 'true');
  svg.style.left = `${-pad - bl}px`; svg.style.top = `${-pad - bt}px`;
  svg.innerHTML = `<defs>${defs}</defs>
    <path d="${body}" transform="translate(${sx} ${sy})" style="fill:var(--shd)"/>
    <path d="${body}" style="fill:var(--fill)"/>${art}${rim}${sockets}${hw}`;
  const old = el.querySelector(':scope > .org-bg');
  if (old) old.replaceWith(svg); else el.prepend(svg);
  el._orgDrawn = true;
}
