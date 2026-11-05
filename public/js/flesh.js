// The fleshy / biomechanical screen frame around the end screen: a lumpy wet band of meat (noise + lighting
// filters), veins, chrome bolts, a neon rim on the inside edge and two googly eyes. Ugly on purpose, generated as an
// SVG for the window size so it never stretches. Visual only, nothing reads it.
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

// a point + inward normal at distance u along a rounded rect (x0,y0)-(x1,y1) with corner radius r
function perim(x0, y0, x1, y1, r) {
  const w = x1 - x0 - 2 * r, h = y1 - y0 - 2 * r, arc = (Math.PI / 2) * r;
  const segs = [w, arc, h, arc, w, arc, h, arc];
  const L = segs.reduce((a, b) => a + b, 0);
  const at = (u) => {
    u = ((u % L) + L) % L;
    let i = 0;
    while (u > segs[i]) { u -= segs[i]; i++; }
    const corner = (cx, cy, a0) => { const a = a0 + u / r; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r, -Math.cos(a), -Math.sin(a)]; };
    switch (i) {
      case 0: return [x0 + r + u, y0, 0, 1]; // top, left -> right
      case 1: return corner(x1 - r, y0 + r, -Math.PI / 2);
      case 2: return [x1, y0 + r + u, -1, 0];
      case 3: return corner(x1 - r, y1 - r, 0);
      case 4: return [x1 - r - u, y1, 0, -1];
      case 5: return corner(x0 + r, y1 - r, Math.PI / 2);
      case 6: return [x0, y1 - r - u, 1, 0];
      default: return corner(x0 + r, y0 + r, Math.PI);
    }
  };
  return { L, at };
}

let frames = 0;
export function fleshFrame(W, H) {
  seed = 7 + ((W * 31 + H) % 1000); // same window = same lumps
  const P = `fl${++frames}-`; // the menu and the end screen each have a frame on the page: their svg ids must not collide
  const T = Math.round(Math.max(12, Math.min(26, Math.min(W, H) * 0.022)));
  const P = perim(T, T, W - T, H - T, T * 2.2);
  const bumps = Array.from({ length: 7 }, () => ({ u: rnd() * P.L, w: 40 + rnd() * 90, a: 6 + rnd() * 10 }));
  const off = (u) => {
    let o = Math.sin(u / 41) * 3 + Math.sin(u / 13 + 1.7) * 1.6 + Math.sin(u / 97 + 4) * 3;
    for (const b of bumps) { let d = Math.abs(u - b.u); d = Math.min(d, P.L - d); o += b.a * Math.exp(-(d * d) / (2 * b.w * b.w)); }
    return o;
  };
  let inner = '';
  const step = 14;
  for (let u = 0; u <= P.L; u += step) {
    const [x, y, nx, ny] = P.at(u), o = off(u);
    inner += `${u ? 'L' : 'M'}${(x + nx * o).toFixed(1)} ${(y + ny * o).toFixed(1)}`;
  }
  inner += 'Z';
  const band = `M0 0H${W}V${H}H0Z${inner}`;
  // veins: little branching squiggles that live inside the band
  let veins = '';
  for (let i = 0; i < 26; i++) {
    const u = rnd() * P.L, [x, y, nx, ny] = P.at(u), tx = -ny, ty = nx, len = 30 + rnd() * 70;
    const d0 = -T * 0.5 + rnd() * T * 0.6;
    const p = (k, wob) => [x + tx * len * k + nx * (d0 + wob), y + ty * len * k + ny * (d0 + wob)];
    const a = p(0, 0), b = p(0.35, (rnd() - 0.5) * T * 0.7), c = p(0.7, (rnd() - 0.5) * T * 0.7), d = p(1, (rnd() - 0.5) * T * 0.5);
    veins += `<path d="M${a[0].toFixed(1)} ${a[1].toFixed(1)}C${b[0].toFixed(1)} ${b[1].toFixed(1)} ${c[0].toFixed(1)} ${c[1].toFixed(1)} ${d[0].toFixed(1)} ${d[1].toFixed(1)}" stroke-width="${(1 + rnd() * 2.2).toFixed(1)}"/>`;
  }
  // chrome bolts screwed into the meat, a pair of googly eyes up top
  let bolts = '';
  const boltAt = (x, y, r) => { bolts += `<g transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${Math.round(rnd() * 90)})"><circle r="${r}" fill="url(#${P}chrome)" stroke="#120818" stroke-width="2"/><path d="M${-r * 0.55} 0H${r * 0.55}M0 ${-r * 0.55}V${r * 0.55}" stroke="#3a3a48" stroke-width="2"/></g>`; };
  const br = Math.max(5, T * 0.32);
  for (const [x, y] of [[T * 0.75, T * 0.75], [W - T * 0.75, T * 0.75], [T * 0.75, H - T * 0.75], [W - T * 0.75, H - T * 0.75]]) boltAt(x, y, br * 1.25);
  for (let x = 240; x < W - 200; x += 260 + rnd() * 120) { boltAt(x, T * 0.45, br); boltAt(x + 60, H - T * 0.45, br); }
  for (let y = 200; y < H - 160; y += 240 + rnd() * 100) { boltAt(T * 0.45, y, br); boltAt(W - T * 0.45, y + 50, br); }
  const eye = (x, y, r, d) => `<g class="eye" transform="translate(${x} ${y})"><circle r="${r}" fill="#fff" stroke="#120818" stroke-width="3"/><circle class="pupil" style="animation-delay:${d}s" cx="${r * 0.2}" cy="${r * 0.25}" r="${r * 0.48}" fill="#120818"/><circle cx="${-r * 0.35}" cy="${-r * 0.35}" r="${r * 0.18}" fill="#fff" opacity=".9"/></g>`;
  const er = Math.max(10, T * 0.85);
  const eyes = eye(W * 0.5 - er * 1.15, T * 0.55, er, 0) + eye(W * 0.5 + er * 1.15, T * 0.55, er * 0.82, 0.37);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" aria-hidden="true">
  <defs>
    <linearGradient id="${P}meat" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e2667a"/><stop offset=".45" stop-color="#b8304e"/><stop offset=".7" stop-color="#d4507a"/><stop offset="1" stop-color="#8a1838"/></linearGradient>
    <radialGradient id="${P}chrome" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#ffffff"/><stop offset=".35" stop-color="#c8ccd6"/><stop offset=".7" stop-color="#6a6e7c"/><stop offset="1" stop-color="#e8ecf4"/></radialGradient>
    <filter id="${P}wet" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency=".035 .06" numOctaves="3" seed="4" result="n"/>
      <feDiffuseLighting in="n" surfaceScale="5" lighting-color="#ffc8d0" result="lit"><feDistantLight azimuth="235" elevation="48"/></feDiffuseLighting>
      <feComposite in="lit" in2="SourceGraphic" operator="arithmetic" k1="1.15" k2="0" k3="0" k4="0" result="tex"/>
      <feSpecularLighting in="n" surfaceScale="6" specularConstant=".9" specularExponent="22" lighting-color="#fff" result="spec"><feDistantLight azimuth="235" elevation="52"/></feSpecularLighting>
      <feComposite in="spec" in2="SourceAlpha" operator="in" result="spec2"/>
      <feComposite in="tex" in2="spec2" operator="arithmetic" k1="0" k2="1" k3=".55" k4="0" result="all"/>
      <feComposite in="all" in2="SourceAlpha" operator="in"/>
    </filter>
    <filter id="${P}glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5"/></filter>
    <clipPath id="${P}bandclip"><path d="${band}" clip-rule="evenodd"/></clipPath>
  </defs>
  <path d="${inner}" fill="none" stroke="#000" stroke-opacity=".55" stroke-width="${T * 1.6}" filter="url(#${P}glow)"/>
  <path d="${band}" fill="url(#${P}meat)" fill-rule="evenodd" filter="url(#${P}wet)"/>
  <g clip-path="url(#${P}bandclip)" fill="none" stroke="#5a1a6a" stroke-opacity=".7" stroke-linecap="round">${veins}</g>
  <path d="${inner}" fill="none" stroke="#ff4fd8" stroke-width="7" filter="url(#${P}glow)"/>
  <path d="${inner}" fill="none" stroke="#120818" stroke-width="4"/>
  <path d="${inner}" fill="none" stroke="#ff4fd8" stroke-width="2.2"/>
  <path d="${inner}" fill="none" stroke="#ffe14d" stroke-width="0.9" stroke-dasharray="2 10" opacity=".9"/>
  ${bolts}${eyes}
</svg>`;
}
