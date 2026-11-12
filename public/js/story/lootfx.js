// OVERDUE loot juice (WP4): a beam per rarity over every drop (taller and louder up the tiers, ☺ PREMIUM spins rays
// and sings), a comic sound per tier when loot hits the floor and when you grab it, and the item card with the
// ▲▼ stat arrows against what you're holding.
import * as THREE from 'three';
import { synth } from '../audio.js';
import { RCOL } from './bar.js';
import { statsOf, statsFor, compare, nameOf, STATS, BRANDS, MODIFIERS, LEGENDARIES } from '/shared/story/loot.js';
import { infoOf, kindOf } from '/shared/story/items.js';

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const TIER = { common: 0, rare: 1, epic: 2, legendary: 3, premium: 4 };
export const RNAME = { common: 'COMMON', rare: 'RARE', epic: 'EPIC', legendary: 'LEGENDARY', premium: '☺ PREMIUM' };

// ------------------------------------------------------------ beams
const beamGeo = new THREE.CylinderGeometry(0.06, 0.16, 1, 8, 1, true);
const rayGeo = new THREE.PlaneGeometry(0.18, 1);
export function beamFor(r) {
  const t = TIER[r] ?? 0, col = new THREE.Color(RCOL[r] || RCOL.common), g = new THREE.Group();
  const h = [2.2, 3.4, 5, 8, 12][t];
  const mat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.35 + t * 0.1, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const core = new THREE.Mesh(beamGeo, mat); core.scale.set(1 + t * 0.35, h, 1 + t * 0.35); core.position.y = h / 2; g.add(core);
  if (t >= 2) { const halo = new THREE.Mesh(beamGeo, mat.clone()); halo.material.opacity = 0.12; halo.scale.set(2 + t * 0.5, h * 0.6, 2 + t * 0.5); halo.position.y = h * 0.3; g.add(halo); }
  const rays = new THREE.Group(); // legendary + premium: spinning rays round the base, like a shrine
  if (t >= 3) for (let i = 0; i < (t === 4 ? 10 : 6); i++) {
    const m = new THREE.Mesh(rayGeo, mat.clone()); m.material.opacity = 0.3;
    m.scale.y = 1.4 + (i % 2) * 0.8; m.position.y = m.scale.y / 2 - 0.1; m.rotation.y = (i / (t === 4 ? 10 : 6)) * Math.PI; m.rotation.z = 0.5;
    const holder = new THREE.Group(); holder.rotation.y = (i / 6) * Math.PI * 2; holder.add(m); rays.add(holder);
  }
  g.add(rays);
  const mats = []; g.traverse((o) => { if (o.material) mats.push([o.material, o.material.opacity]); });
  // near: fade to a thin glow so a beam you stand in doesn't paint the whole screen
  g.userData.tick = (dt, time, dist = 99) => {
    rays.rotation.y += dt * (t === 4 ? 1.6 : 0.8);
    const near = Math.max(0.12, Math.min(1, (dist - 1.2) / 7)), pulse = 1 + Math.sin(time * (3 + t)) * 0.2;
    for (const [m, o] of mats) m.opacity = o * near * pulse;
  };
  return g;
}

// ------------------------------------------------------------ sounds (synthesized, like audio.js)
// tier: common a blip, rare a chime, epic two chimes, legendary a fanfare, ☺ PREMIUM a little choir ("aaaah")
export function lootSound(r, pos, pick) {
  const t = TIER[r] ?? 0, T = synth.tone;
  if (pick) { T('square', 660 + t * 120, 1320 + t * 240, 0.08, 0.12, pos); if (t >= 3) T('triangle', 990, 1980, 0.25, 0.1, pos, 0.06); return; }
  if (t === 0) T('triangle', 880, 900, 0.08, 0.1, pos);
  else if (t === 1) { T('sine', 1318, 1318, 0.25, 0.12, pos); T('sine', 1760, 1760, 0.3, 0.08, pos, 0.08); }
  else if (t === 2) for (const [d, f] of [[0, 1046], [0.1, 1318], [0.2, 1568], [0.32, 2093]]) T('triangle', f, f, 0.28, 0.1, pos, d);
  else if (t === 3) { for (const [d, f, l] of [[0, 523, 0.15], [0.15, 659, 0.15], [0.3, 784, 0.15], [0.46, 1046, 0.7]]) { T('square', f, f, l, 0.07, pos, d); T('sawtooth', f / 2, f / 2, l, 0.04, pos, d); } }
  else { // the choir: three voices swelling on a major chord, a bell on top
    for (const [f, d] of [[523, 0], [659, 0.04], [784, 0.08], [1046, 0.12]]) { T('sine', f, f * 1.003, 1.6, 0.07, pos, d); T('triangle', f * 2, f * 2.01, 1.3, 0.025, pos, d + 0.05); }
    T('sine', 2093, 2093, 1.2, 0.05, pos, 0.5);
  }
}

// ------------------------------------------------------------ the item card (comic arrows against what you hold)
export function lootCard(it, vs) {
  const c = el('div', 'st-lcard'); // (not st-card: story.css's chapter title card has that name, and its centring and slam pulled this one up under the quest panel)
  if (!it) return c;
  const i = infoOf(it) || { name: it.b, desc: '' };
  c.style.borderColor = RCOL[it.r] || RCOL.common;
  const isW = kindOf(it.b) === 'gun' || kindOf(it.b) === 'melee';
  c.append(el('em', 'st-rar', RNAME[it.r] || it.r), el('b', 'st-cname', isW ? nameOf(it) : i.name));
  c.querySelector('.st-rar').style.background = RCOL[it.r] || RCOL.common;
  if (it.br && BRANDS[it.br]) c.append(el('div', 'st-brand', `${BRANDS[it.br].name} · ${BRANDS[it.br].flavour}`));
  if (it.lg && LEGENDARIES[it.lg]) c.append(el('div', 'st-quirk', LEGENDARIES[it.lg].quirk), el('div', 'st-flav', `"${LEGENDARIES[it.lg].flavour}"`));
  for (const m of it.m || []) if (MODIFIERS[m]) c.append(el('div', 'st-mod', `${MODIFIERS[m].name}: ${MODIFIERS[m].effect}`));
  if (isW) {
    const rows = el('div', 'st-stats'), s = statsOf(it), cmp = vs && (kindOf(vs.b) === 'gun' || kindOf(vs.b) === 'melee') ? compare(vs, it) : null;
    const show = statsFor(it.b);
    STATS.forEach(([k, label, dir], j) => {
      if (!show.includes(k)) return;
      const pct = Math.round(((dir > 0 ? s[k] : 1 / s[k]) - 1) * 100);
      const row = el('div', 'st-srow');
      row.append(el('span', null, label), el('span', 'st-sv', `${pct >= 0 ? '+' : ''}${pct}%`));
      if (cmp && !cmp[j].same) { const a = el('i', cmp[j].up ? 'st-up' : 'st-dn', cmp[j].up ? '▲' : '▼'); row.append(a); }
      rows.append(row);
    });
    c.append(rows);
    if (s.part) c.append(el('div', 'st-mod', `extra part: ${s.part}`));
    if (vs && cmp) c.append(el('div', 'st-vs', `vs your ${nameOf(vs)}`));
  } else if (i.desc) c.append(el('div', 'st-flav', i.desc));
  return c;
}
export const LOOT_CSS = `
.st-lcard{font-family:var(--font);background:rgba(18,8,24,.94);border:4px solid #7dff4f;box-shadow:6px 6px 0 #4fd8ff;color:#fff;padding:10px 12px;width:290px;transform:rotate(-1.5deg)}
.st-rar{display:inline-block;font-style:normal;font-weight:700;color:#000;border:2px solid #000;padding:0 8px;transform:rotate(-3deg);box-shadow:2px 2px 0 #000}
.st-cname{display:block;font-size:20px;margin:6px 0 2px;color:#ffe14d;text-transform:uppercase}
.st-brand{font-size:12px;color:#4fd8ff;margin-bottom:4px}.st-quirk{font-size:13px;color:#ff4fd8;margin:2px 0}.st-flav{font-size:13px;opacity:.85;font-style:italic}
.st-mod{font-size:13px;color:#7dff4f}.st-stats{margin-top:6px;border-top:2px dashed #ff4fd8;padding-top:4px}
.st-srow{display:grid;grid-template-columns:1fr 54px 18px;font-size:14px}.st-sv{text-align:right}
.st-up{color:#39ff14;font-style:normal;font-weight:700;text-align:right}.st-dn{color:#ff3030;font-style:normal;font-weight:700;text-align:right}
.st-vs{font-size:11px;opacity:.7;margin-top:4px}
.st-bagcard{position:fixed;right:max(8px,calc(50% - 690px));top:12%;z-index:61;pointer-events:none}
.st-lootcard{position:fixed;left:min(calc(50% + 120px),calc(100% - 314px));top:max(40%,176px);z-index:21;pointer-events:none}.st-lootcard.hidden{display:none}
`;
