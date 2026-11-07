// First-person spectating for Plant & Defuse (owner, 2026-11-07: "in defuse mode the spectate should only be in first
// person"). You see through the watched player's eyes: their gun in their hands with their skin, aiming down sights
// (their AIM flag), the scope on a scoped gun, a kick on every shot they fire, a swing on every melee swing, a dip while
// they reload (a gun that stops firing with an empty-ish mag), their crosshair, and a SPECTATING bar. Their view angles
// are smoothed so a 20 Hz snapshot stream doesn't judder. Everything here is the client's own drawing.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { WEAPONS, FLAGS } from '/shared/weapons.js';
import { PH } from '/shared/physics.js';
import { buildWeapon, freeTree } from './models.js';
import { gunHand } from './hands.js';
import { specVMKit } from './weapons.js';

const $ = (id) => document.getElementById(id);
const S = { id: 0, yaw: 0, pitch: 0, snap: true, root: null, cur: null, cache: new Map(), kick: 0, swing: 0, aim: 0, bar: null, on: false, scoped: false, lastShot: 0 };
const wrapA = (a) => { while (a > Math.PI) a -= Math.PI * 2; while (a < -Math.PI) a += Math.PI * 2; return a; };

// their shots and swings: a kick / a swing on the gun in "your" hands
net.tap((m) => {
  if (!S.on || m.t !== 'fx' || m.id !== S.id) return;
  if (m.k === 'shot') { const n = performance.now(); S.burst = (n - S.lastShot < 600 ? S.burst || 0 : 0) + 1; S.kick = Math.min(1.4, S.kick + 1); S.lastShot = n; }
  else if (m.k === 'swing') S.swing = 1;
});

function model(id, skin) {
  const key = id + JSON.stringify(skin || '');
  if (S.cache.has(key)) return S.cache.get(key);
  const cfg = specVMKit.pose(id);
  if (!cfg) return null;
  const wrap = new THREE.Group(), g = buildWeapon(id, skin);
  g.scale.setScalar(cfg.s);
  wrap.add(g);
  const hand = gunHand(id, cfg, g, g.userData.model);
  wrap.add(hand);
  if (g.userData.bare) { hand.visible = false; g.add(g.userData.bare); }
  const m = { id, wrap, g, cfg };
  if (S.cache.size > 8) { for (const [k, v] of S.cache) { if (v !== S.cur) { S.root.remove(v.wrap); freeTree(v.wrap); S.cache.delete(k); break; } } }
  S.cache.set(key, m);
  S.root.add(wrap);
  return m;
}

function bar(r) {
  if (!S.bar) {
    const b = S.bar = document.createElement('div');
    b.id = 'specFP';
    b.innerHTML = '<b>SPECTATING</b><span class="n"></span><span class="s"></span>';
    $('hud').append(b);
    const st = document.createElement('style');
    st.textContent = `#specFP { position: absolute; left: 50%; bottom: 112px; transform: translateX(-50%) rotate(-1deg); background: rgba(18,8,24,0.92); border: 4px solid #ff4fd8; box-shadow: 6px 6px 0 #4fd8ff; padding: 4px 14px; font: bold 17px var(--font); color: #fff; display: none; white-space: nowrap; pointer-events: none; }
#specFP b { color: #ffe14d; margin-right: 10px; letter-spacing: 1px; } #specFP .n { margin-right: 12px; } #specFP .s { color: #ccc; font-size: 14px; }
body.spec-fp #specFP { display: block; } body.spec-fp #ecoSpec { top: auto; bottom: 64px; }`;
    document.head.append(st);
  }
  const w = WEAPONS[r.w], money = G.eco && G.eco.money ? G.eco.money.get(r.id) : null;
  const n = S.bar.querySelector('.n'), s = S.bar.querySelector('.s');
  if (n.textContent !== r.name) { n.textContent = r.name; n.style.color = r.color || '#fff'; }
  const txt = `${Math.max(0, Math.round(r.hp))} HP · ${w ? w.name : '?'}${money != null ? ` · $${money}` : ''}`;
  if (s.textContent !== txt) s.textContent = txt;
}

// main.js (via econ.js econCam): put the camera in r's eyes. true = it did
export function specFP(cam, dt, id) {
  const r = id && G.remotes.get(id);
  if (!r || !r.alive) { specFPOff(); return false; }
  if (!S.root) { S.root = new THREE.Group(); G.vmScene.add(S.root); }
  if (id !== S.id || !S.on) { S.id = id; S.snap = true; S.kick = 0; S.swing = 0; S.aim = 0; }
  S.on = true;
  document.body.classList.add('spec-fp');
  // their eyes, smoothed (the snapshots come in at 20 Hz; the remote already interpolates, this takes the last jitter out)
  if (S.snap) { S.yaw = r.yaw; S.pitch = r.pitch; S.snap = false; }
  const k = Math.min(1, dt * 22);
  S.yaw += wrapA(r.yaw - S.yaw) * k; S.pitch += (r.pitch - S.pitch) * k;
  const crouch = (r.f & FLAGS.CROUCH) ? 1.05 : PH.eye;
  cam.position.set(r.pos[0], r.pos[1] + crouch, r.pos[2]);
  cam.rotation.set(S.pitch - S.kick * 0.012, S.yaw, 0);
  r.ch.root.visible = false; if (r.shadow) r.shadow.visible = false; if (r.tag) r.tag.visible = false; // (you're inside them)
  // aiming: their AIM flag, eased like your own
  const w = WEAPONS[r.w] || {};
  const aiming = !!(r.f & FLAGS.AIM) && !!w.ads;
  S.aim = aiming ? Math.min(1, S.aim + dt * 7) : Math.max(0, S.aim - dt * 8);
  const zoom = w.ads ? 1 + (w.ads.zoom - 1) * S.aim : 1, fov = (G.settings.fov || 90) / zoom;
  if (Math.abs(cam.fov - fov) > 0.05) { cam.fov = fov; cam.updateProjectionMatrix(); }
  const scoped = !!(w.ads && w.ads.scope && S.aim > 0.85);
  $('scope').classList.toggle('on', scoped); $('crosshair').style.display = scoped ? 'none' : '';
  S.scoped = scoped;
  // their gun in your hands
  const skin = (G.skins.get(id) || {})[r.w];
  const m = r.w && model(r.w, skin);
  for (const v of S.cache.values()) v.wrap.visible = v === m && !scoped;
  S.cur = m;
  specVMKit.own(false);
  if (m) {
    const c = m.cfg, now = performance.now();
    S.kick = Math.max(0, S.kick - dt * 6); S.swing = Math.max(0, S.swing - dt * 3.5);
    let px = c.p[0] + Math.sin(now * 0.0013) * 0.0025, py = c.p[1] + Math.sin(now * 0.0021) * 0.0018, pz = c.p[2];
    let rx = c.r[0], ry = c.r[1], rz = c.r[2];
    if (S.aim > 0) { const a = S.aim * S.aim * (3 - 2 * S.aim), t = specVMKit.ads(r.w, m.g); px += (t[0] - px) * a; py += (t[1] - py) * a; pz += (t[2] - pz) * a; rx += (0 - rx) * a; ry += (0 - ry) * a; rz += ((t[3] || 0) - rz) * a; }
    const ra = 1 - S.aim * 0.6;
    pz += S.kick * 0.04 * ra; rx += S.kick * 0.12 * ra;
    if (S.swing > 0) { const s = Math.sin(S.swing * Math.PI); px -= s * 0.12; py += s * 0.05; ry += s * 0.9; rz += s * 0.5; } // a melee swing across
    // a reload dip: a mag gun that hasn't fired for a moment right after a long burst reads as a reload (no reload event goes out)
    const quiet = now - S.lastShot;
    if (w.mag && quiet > 250 && quiet < 1700 && S.kick === 0 && (r.f & FLAGS.FIRE) === 0 && S.burst > (w.mag * 0.7)) { const kk = Math.sin(((quiet - 250) / 1450) * Math.PI); py -= kk * 0.12; rx -= kk * 0.6; rz += kk * 0.4; }
    m.wrap.position.set(px, py, pz); m.wrap.rotation.set(rx, ry, rz);
  }
  bar(r);
  return true;
}
export function specFPOff() {
  if (!S.on) return;
  S.on = false;
  document.body.classList.remove('spec-fp');
  for (const v of S.cache.values()) v.wrap.visible = false;
  specVMKit.own(true);
  if (S.scoped) { $('scope').classList.remove('on'); $('crosshair').style.display = ''; S.scoped = false; }
  const r = G.remotes.get(S.id);
  if (r && r.tag) r.tag.visible = true;
}
export const specFPOn = () => S.on;
