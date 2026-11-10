// the referee's boss on the client (story fights). the combat referee (shared/story/refsys.js + server/storyboss.js)
// owns him: HP, parts, phases, attacks, where he stands. he's a bot in its room, so here:
//   - that bot's mannequin is hidden and the story actor (the real model) stands where the referee has him
//   - your shots are tested against his real size (the body + head + staplers from c_<who>.parts.json); the referee
//     decides which part it was
//   - the boss bar (HP, the plate, the phase), a couple of callouts, and his missed staples left in the walls
// nothing here changes the fight: turn it off and he's still fought, just invisible
import * as THREE from 'three';
import { G } from '../ctx.js';
import { hud } from '../hud.js';
import { play } from './actors.js';

const fin = Number.isFinite;
const PARTS = {}; // who -> the parts file (or null while it loads / if it isn't there)
function partsOf(who) {
  if (!/^[a-z]{1,16}$/.test(who)) return null;
  if (!(who in PARTS)) { PARTS[who] = null; fetch(`/models/cast/c_${who}.parts.json`).then((r) => (r.ok ? r.json() : null)).then((j) => { PARTS[who] = j && j.parts && j.body ? j : null; }).catch(() => {}); }
  return PARTS[who];
}
// a root-space box (centre, half extents) as a world box around the bot (yaw turns it; an AABB round the turned box)
function worldBox(r, c, h, k = 1) {
  const cs = Math.cos(r.yaw), sn = Math.sin(r.yaw), x = r.pos[0] + c[0] * cs + c[2] * sn, y = r.pos[1] + c[1], z = r.pos[2] - c[0] * sn + c[2] * cs;
  const ex = (Math.abs(h[0] * cs) + Math.abs(h[2] * sn)) * k, ez = (Math.abs(h[0] * sn) + Math.abs(h[2] * cs)) * k;
  return { min: [x - ex, y - h[1], z - ez], max: [x + ex, y + h[1], z + ez] };
}

function css() {
  if (document.getElementById('stBossCss')) return;
  const s = document.createElement('style'); s.id = 'stBossCss';
  s.textContent = `#stBossBar{position:fixed;left:50%;top:14px;transform:translateX(-50%) rotate(-0.6deg);width:min(560px,70vw);z-index:40;pointer-events:none;font-family:var(--font);
    background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:6px 12px 9px;color:#fff}
  #stBossBar.hidden{display:none}
  #stBossBar .nm{display:flex;justify-content:space-between;align-items:baseline;font-weight:700;letter-spacing:1px}
  #stBossBar .nm b{color:#ffe14d;font-size:20px} #stBossBar .nm span{font-size:13px;color:#4fd8ff;text-transform:lowercase}
  #stBossBar .tr{position:relative;height:16px;margin-top:5px;background:#000;border:3px solid #000;outline:2px solid #fff}
  #stBossBar .hp,#stBossBar .ar{position:absolute;left:0;top:0;bottom:0} #stBossBar .hp{background:#ff4fd8} #stBossBar .ar{background:#ffe14d}
  #stBossBar .tk{position:absolute;top:-3px;bottom:-3px;width:3px;background:#fff;left:50%}
  #stBossBar.inv .hp,#stBossBar.inv .ar{opacity:.45}`;
  document.head.appendChild(s);
}

export function makeBossRef({ actorOf, busy }) {
  const R = { cur: null, stuck: [] };
  let bar = null;
  const el = (cls, tag = 'div') => { const d = document.createElement(tag); if (cls) d.className = cls; return d; };
  function showBar() {
    const c = R.cur;
    if (!bar) { css(); bar = el('hidden'); bar.id = 'stBossBar'; const nm = el('nm'); nm.append(el('', 'b'), el('', 'span')); const tr = el('tr'); tr.append(el('hp'), el('ar'), el('tk')); bar.append(nm, tr); document.body.appendChild(bar); }
    bar.classList.toggle('hidden', !c);
    if (!c) return;
    const hp = Math.max(0, Math.min(1, c.hp / c.max)), he = Math.max(0, Math.min(1, c.health / c.max));
    bar.querySelector('b').textContent = c.name; bar.querySelector('span').textContent = c.phase;
    bar.querySelector('.hp').style.width = `${Math.min(hp, he) * 100}%`;
    const ar = bar.querySelector('.ar'); ar.style.left = `${he * 100}%`; ar.style.width = `${Math.max(0, hp - he) * 100}%`; // the plate: the yellow end of the bar
    bar.classList.toggle('inv', !!c.inv);
  }
  // the room's bot for him: never drawn (the actor is his body), and as big as he really is when you shoot
  function adopt(r) {
    const c = R.cur; if (r.stBoss) return; r.stBoss = true;
    const upd = r.update.bind(r);
    r.update = (...a) => { upd(...a); r.ch.root.visible = false; if (r.shadow) r.shadow.visible = false; if (r.marker) r.marker.visible = false; };
    const plain = r.hitboxes.bind(r);
    r.hitboxes = () => {
      const P = partsOf(c.who); if (!P) return plain();
      const out = [worldBox(r, P.body.c, [P.body.r, P.body.h / 2, P.body.r], 0.85)];
      for (const k of ['head', 'gunR', 'gunL']) if (P.parts[k]) out.push(worldBox(r, P.parts[k].c, P.parts[k].h));
      return out;
    };
  }
  R.tick = (dt) => {
    for (let i = R.stuck.length - 1; i >= 0; i--) { const s = R.stuck[i]; if ((s.t -= dt) <= 0) { G.scene.remove(s.m); R.stuck.splice(i, 1); } }
    const c = R.cur; if (!c) return;
    const r = G.remotes.get(c.pid), a = actorOf(c.id); if (!r) return;
    adopt(r);
    if (!a || !fin(r.pos[0]) || (busy && busy())) return; // (a cutscene has him: it puts him where it wants)
    a.pos[0] = r.pos[0]; a.pos[1] = r.pos[1]; a.pos[2] = r.pos[2]; a.yaw = r.yaw; a.home.p = [...r.pos]; a.home.face = r.yaw; a.path = null; a.hidden = false;
    // between attacks: walking or waiting (his clips; an attack / a phase pose is left alone)
    const want = Math.hypot(r.vel[0], r.vel[2]) > 0.6 ? 'ot_stalk' : 'ot_idle', cl = a.clip;
    if (!cl || ((cl.name === 'ot_stalk' || cl.name === 'ot_idle') && cl.name !== want && !c.inv)) play(a, want, { hold: true });
  };
  // the referee's events, before the fight hooks get them
  R.combat = (ev) => {
    const c = R.cur; if (!c || ev.boss !== c.id) return;
    if (ev.type === 'hit' && fin(ev.hp)) c.hp = ev.hp;
    if (ev.type === 'phase') { c.inv = !!ev.invuln; if (typeof ev.name === 'string' && ev.name) c.phase = ev.name.slice(0, 40); }
    if (ev.type === 'part' && ev.state === 'plate_off') hud.msg('PLATE OFF. HIT THE CLOCK.', 2.2, 'brag');
    if (ev.type === 'kill') { c.hp = 0; hud.msg('RESCHEDULED', 2.6, 'brag'); }
    if (ev.type === 'fx' && ev.k === 'staple' && Array.isArray(ev.at) && ev.at.length === 3 && ev.at.every(fin)) stick(ev.at, Array.isArray(ev.n) && ev.n.length === 3 && ev.n.every(fin) ? ev.n : [0, 1, 0]);
    showBar();
  };
  // a staple that missed, left in the wall (walls take a grapple anyway: this is the "aim here")
  const mat = new THREE.MeshStandardMaterial({ color: 0xffe14d, emissive: 0xffa020, emissiveIntensity: 0.5, metalness: 0.6, roughness: 0.3 }), geo = new THREE.BoxGeometry(1, 1, 1);
  function stick(at, n) {
    const g = new THREE.Group();
    for (const [w, h, x, y] of [[0.9, 0.12, 0, 0], [0.12, 0.5, -0.4, -0.22], [0.12, 0.5, 0.4, -0.22]]) { const b = new THREE.Mesh(geo, mat); b.scale.set(w, 0.12, h); b.position.set(x, 0, y); g.add(b); }
    g.position.set(at[0] + n[0] * 0.25, at[1] + n[1] * 0.25, at[2] + n[2] * 0.25);
    g.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, -1), new THREE.Vector3(n[0], n[1], n[2]).normalize()); g.rotateZ(Math.random() * 6);
    G.scene.add(g); R.stuck.push({ m: g, t: 40 });
    while (R.stuck.length > 24) G.scene.remove(R.stuck.shift().m);
  }
  if (G.story && G.story.on) G.story.on('boss', (m) => {
    if (!m || typeof m.id !== 'string' || !/^[a-z0-9_]{1,40}$/.test(m.id)) return;
    if (m.on === true && fin(m.pid) && fin(m.hp) && fin(m.max) && m.max > 0) R.cur = { id: m.id, pid: m.pid, hp: m.hp, max: m.max, health: fin(m.health) ? m.health : m.max, who: typeof m.who === 'string' ? m.who : '', name: typeof m.name === 'string' ? m.name.slice(0, 24) : 'BOSS', phase: typeof m.phase === 'string' ? m.phase.slice(0, 40) : '', inv: false };
    else if (R.cur && R.cur.id === m.id) R.cur = null;
    if (R.cur) partsOf(R.cur.who);
    showBar();
  });
  return R;
}
