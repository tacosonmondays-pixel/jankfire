// Pop Quiz (item, G): a calculator you throw. Whoever it hits is frozen with a maths question ('quiz'); the server
// picks it and marks it ('quizx'). Here: the exam paper on your screen (keys 1-4), the giant calculator hovering in front
// of whoever is sitting it with the sum on its screen (everyone can read it), the bell, the ticking, the gold star.
import * as THREE from 'three';
import { QUIZ } from '/shared/weapons.js';
import { G } from './ctx.js';
import { ME, releaseHook } from './player.js';
import { W } from './weapons.js';
import { net } from './net.js';
import { calculator, lcdTexture } from './gearmodels.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { RP, RP_HOOKS, recordEv } from './replay.js';

const quizzes = new Map(); // victim id -> Q (live)
const ghostQ = new Map(); // the same in a replay
const golds = new Map(); // id -> until: the gold star over someone who aced it (nothing can hurt them)
const nameOf = (id) => (G.names.get(id) || {}).name || '???';
let mineQ = null, lastWrong = null;

// the sign over their head, so everyone else can read the sum too (the calculator faces them)
function signTex() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 176;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.userData.write = (top, big, col = '#111') => {
    const x = c.getContext('2d');
    x.clearRect(0, 0, 512, 176);
    x.fillStyle = '#4fd8ff'; x.fillRect(16, 16, 486, 130); // hard offset shadow
    x.fillStyle = '#ffffff'; x.fillRect(4, 4, 486, 130); x.lineWidth = 8; x.strokeStyle = '#111'; x.strokeRect(4, 4, 486, 130);
    x.beginPath(); x.moveTo(220, 134); x.lineTo(256, 172); x.lineTo(280, 134); x.closePath(); x.fillStyle = '#fff'; x.fill(); x.stroke(); // the speech tail
    x.fillStyle = '#ff4fd8'; x.font = 'bold 30px sans-serif'; x.textAlign = 'center'; x.fillText(top, 247, 44);
    let fs = 64; x.font = `bold ${fs}px sans-serif`; while (x.measureText(big).width > 460 && fs > 30) { fs -= 4; x.font = `bold ${fs}px sans-serif`; }
    x.fillStyle = col; x.fillText(big, 247, 112);
    t.needsUpdate = true;
  };
  return t;
}
function makeQ(m, scene) {
  const lcd = lcdTexture([`${m.q} = ?`, 'POP QUIZ']);
  const calc = calculator(lcd);
  calc.scale.setScalar(4.6); // about 1.4 m tall
  scene.add(calc);
  const st = signTex();
  const sign = new THREE.Sprite(new THREE.SpriteMaterial({ map: st, depthTest: false, transparent: true, fog: false }));
  sign.scale.set(3.4, 1.17, 1); sign.renderOrder = 9; sign.center.set(0.5, 0);
  scene.add(sign);
  const now = performance.now();
  return { id: m.id, by: m.by, q: m.q, a: m.a, born: now, until: now + m.left, lcd, calc, sign, st, sec: -1, done: 0, res: null, scene };
}
function dropQ(map, id) {
  const Q = map.get(id);
  if (!Q) return;
  map.delete(id);
  Q.scene.remove(Q.calc); Q.scene.remove(Q.sign);
  Q.lcd.dispose(); Q.st.dispose(); Q.sign.material.dispose();
  Q.calc.traverse((o) => { if (o.isMesh && o.material && o.material.map === Q.lcd) o.material.dispose(); });
}
// where a quiz hovers: in front of their face, facing them (a ghost / remote, or you)
function place(Q, pos, yaw, now) {
  const ahead = Q.id === G.myId && !RP.active ? 1.7 : 1.05, f = [-Math.sin(yaw), -Math.cos(yaw)];
  const bob = Math.sin(now * 0.003 + Q.id) * 0.05;
  Q.calc.position.set(pos[0] + f[0] * ahead, pos[1] + (Q.id === G.myId && !RP.active ? 1.25 : 1.55) + bob, pos[2] + f[1] * ahead);
  Q.calc.rotation.set(-0.12 + Math.sin(now * 0.0021) * 0.04, yaw + Math.PI, Math.sin(now * 0.0017 + Q.id) * 0.06);
}

// ------------------------------------------------------------ the exam paper (you)
let el = null;
const CSS = `
#quizPanel { position: absolute; left: 50%; bottom: 13%; width: min(560px, 92vw); transform: translateX(-50%) rotate(-1.2deg); z-index: 8;
  background: rgba(18,8,24,0.94); border: 4px solid #ff4fd8; box-shadow: 8px 8px 0 #4fd8ff; padding: 14px 18px 16px; display: none;
  font-family: var(--font, sans-serif); color: #fff; pointer-events: auto; }
#quizPanel.on { display: block; animation: quizIn 0.25s cubic-bezier(.2,1.6,.4,1); }
@keyframes quizIn { from { transform: translateX(-50%) rotate(-6deg) scale(0.4); } }
#quizPanel h2 { margin: 0; font-size: 30px; color: #ffe14d; text-shadow: 3px 3px 0 #000; transform: rotate(-2deg); display: inline-block; }
#quizPanel .sub { float: right; font-size: 14px; color: #ff9ad5; margin-top: 10px; }
#quizPanel .q { font-size: 46px; font-weight: 700; text-align: center; margin: 6px 0 10px; letter-spacing: 1px; }
#quizPanel .opts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
#quizPanel button { font: 700 26px var(--font, sans-serif); background: #fff; color: #111; border: 3px solid #000; box-shadow: 4px 4px 0 #ff4fd8;
  padding: 8px 10px; text-align: left; cursor: pointer; }
#quizPanel button kbd { display: inline-block; min-width: 26px; margin-right: 10px; padding: 0 6px; background: #ffe14d; border: 2px solid #000; font: 700 18px var(--font, sans-serif); text-align: center; }
#quizPanel button.pick { background: #ffe14d; }
#quizPanel button.right { background: #39ff14; }
#quizPanel button.wrong { background: #ff3030; color: #fff; }
#quizPanel .bar { height: 12px; margin-top: 12px; border: 3px solid #000; background: #2a1830; }
#quizPanel .bar i { display: block; height: 100%; background: #ffe14d; }
#quizPanel.hurry .bar i { background: #ff3030; }
#quizPanel .verdict { text-align: center; font-size: 40px; font-weight: 700; margin-top: 8px; display: none; text-shadow: 3px 3px 0 #000; }
body.replaying #quizPanel { display: none !important; }`;
function panel() {
  if (el) return el;
  const st = document.createElement('style'); st.textContent = CSS; document.head.append(st);
  el = document.createElement('div'); el.id = 'quizPanel';
  el.innerHTML = '<h2>POP QUIZ!</h2><span class="sub">wrong answer = death. no pressure.</span><div class="q"></div><div class="opts"></div><div class="bar"><i></i></div><div class="verdict"></div>';
  document.body.append(el);
  return el;
}
function showPanel(Q) {
  const p = panel();
  p.querySelector('.q').textContent = `${Q.q} = ?`;
  const opts = p.querySelector('.opts'); opts.innerHTML = '';
  Q.a.forEach((v, i) => {
    const b = document.createElement('button');
    b.innerHTML = `<kbd>${i + 1}</kbd>`; b.append(String(v));
    b.addEventListener('mousedown', (e) => { e.stopPropagation(); answer(i); });
    opts.append(b);
  });
  p.querySelector('.verdict').style.display = 'none';
  p.classList.remove('hurry');
  p.classList.add('on');
}
function answer(i) {
  const Q = mineQ;
  if (!Q || Q.picked != null || !ME.alive) return;
  Q.picked = i;
  net.send({ t: 'ans', i });
  el.querySelectorAll('button')[i].classList.add('pick');
  sfx.click();
}
// keys 1-4 (and the numpad) answer while you're sitting one. true = that key was ours
export function quizKey(e) {
  if (!mineQ || mineQ.res) return false;
  const m = /^(?:Digit|Numpad)([1-4])$/.exec(e.code);
  if (!m) return /^(?:Digit|Numpad)[0-9]$/.test(e.code); // other number keys do nothing either (no weapon swaps mid-exam)
  if (!e.repeat) answer(Number(m[1]) - 1);
  return true;
}

// ------------------------------------------------------------ server messages
export function onQuiz(m) {
  recordEv(m);
  dropQ(quizzes, m.id);
  const Q = makeQ(m, G.scene);
  quizzes.set(m.id, Q);
  const r = G.remotes.get(m.id);
  if (m.id === G.myId) {
    mineQ = Q;
    ME.quizUntil = Q.until;
    releaseHook();
    Object.assign(W, { held: false, aimHeld: false, dashHeld: false, draw: 0, charge: 0, exhale: 0, pendingSwing: 0, pendingThrow: 0 });
    showPanel(Q);
    sfx.calcBonk(); sfx.quizBell();
    G.shake = Math.max(G.shake, 0.4);
  } else {
    sfx.calcBonk(r ? r.pos : null);
    if (m.by === G.myId) hud.msg(`POP QUIZ FOR ${nameOf(m.id)}`, 1.4, 'brag');
  }
  if (r) fx.spray([r.pos[0], r.pos[1] + 1.8, r.pos[2]], 24, [0x7fffd4, 0xffffff, 0xffe14d], 5, 1, 0.1, 6, 1);
}
export function onQuizEnd(m) {
  recordEv(m);
  const Q = quizzes.get(m.id);
  if (Q) result(Q, m);
  if (m.id === G.myId) {
    ME.quizUntil = 0;
    if (mineQ && !m.gone) {
      const bs = el.querySelectorAll('button');
      if (m.c >= 0 && bs[m.c]) bs[m.c].classList.add('right');
      if (m.i >= 0 && m.i !== m.c && bs[m.i]) bs[m.i].classList.add('wrong');
      const v = el.querySelector('.verdict');
      v.style.display = 'block';
      v.textContent = m.ok ? 'GOLD STAR! ★' : m.i < 0 ? 'PENS DOWN. TOO SLOW.' : 'WRONG.';
      v.style.color = m.ok ? '#ffe14d' : '#ff3030';
      if (!m.ok) lastWrong = { q: mineQ.q, a: mineQ.a[m.c] };
      setTimeout(() => { if (!mineQ || mineQ === Q) el.classList.remove('on'); }, m.ok ? 900 : 1400);
    } else if (el) el.classList.remove('on');
    mineQ = null;
    if (m.ok) {
      ME.fastUntil = performance.now() + QUIZ.fastT * 1000;
      hud.msg('GOLD STAR! ★ NOTHING CAN HURT YOU', 1.8, 'brag');
      hud.flash(0.5, 0.25);
    }
  }
  if (m.ok && !m.gone) golds.set(m.id, performance.now() + QUIZ.invuln * 1000);
}
function result(Q, m) {
  Q.res = m;
  Q.done = performance.now();
  Q.lcd.userData.write(m.gone ? ['', ''] : m.ok ? ['CORRECT', '★ GOLD STAR'] : m.i < 0 ? ['TIME UP', `ANS = ${Q.a[m.c]}`] : ['WRONG', `ANS = ${Q.a[m.c]}`]);
  if (!m.gone) Q.st.userData.write(m.ok ? 'CORRECT!' : m.i < 0 ? 'TOO SLOW' : `WRONG (said ${Q.a[m.i]})`, m.ok ? '★ GOLD STAR ★' : `${Q.q} = ${Q.a[m.c]}`, m.ok ? '#e0a800' : '#ff3030');
  const p = Q.calc.position.toArray();
  if (m.gone) return;
  if (m.ok) { sfx.quizRight(Q.id === G.myId ? null : p); fx.spray(p, 40, [0xffe14d, 0xffffff, 0xffc83a], 7, 1.3, 0.12, 6, 1.2); }
  else sfx.quizWrong(Q.id === G.myId ? null : p);
}
// the death line: "you failed the pop quiz (it was 56)"
export function quizDeath() { const w = lastWrong; lastWrong = null; return w ? `you failed the pop quiz. ${w.q} = ${w.a}.` : 'you failed the pop quiz'; }

// ------------------------------------------------------------ every frame
let tick = -1;
function stepQ(map, now, who, isReplay) {
  for (const [id, Q] of map) {
    const r = who(id);
    if (Q.done && now - Q.done > 900) { dropQ(map, id); continue; }
    if (!Q.done && now > Q.until + 1500) { dropQ(map, id); continue; } // lost the mark (left, round reset)
    const pos = id === G.myId && !isReplay ? ME.pos : r && r.pos, yaw = id === G.myId && !isReplay ? ME.yaw : r && r.yaw;
    if (!pos) { Q.calc.visible = false; continue; }
    place(Q, pos, yaw, now);
    Q.calc.visible = isReplay || !RP.active;
    const ds = (r && r.distScale) || 1;
    Q.sign.position.set(pos[0], pos[1] + 2.75 * ds, pos[2]);
    Q.sign.scale.set(3.4 * Math.max(1, ds * 0.8), 1.17 * Math.max(1, ds * 0.8), 1);
    Q.sign.visible = (isReplay || !RP.active) && (isReplay || id !== G.myId); // you have the exam paper
    if (!Q.done) {
      const sec = Math.max(0, Math.ceil((Q.until - now) / 1000));
      if (sec !== Q.sec) { Q.sec = sec; Q.lcd.userData.write([`${Q.q} = ?`, `POP QUIZ  ${sec}s`]); Q.st.userData.write(`POP QUIZ · ${nameOf(id)} · ${sec}s`, `${Q.q} = ?`); }
      if (r && Math.random() < 0.05) fx.spray([r.pos[0], r.pos[1] + 2.4, r.pos[2]], 1, [0x9fe8ff], 1, 0.4, 0.06, -2, 0.6); // sweating
    } else { // marked: it spins off and shrinks away
      const k = (now - Q.done) / 900;
      if (k > 0.45) { Q.calc.scale.setScalar(4.6 * Math.max(0.01, 1 - (k - 0.45) / 0.55)); Q.calc.rotation.y += (k - 0.45) * 12; }
    }
  }
}
const gTex = {};
function goldStar() {
  if (gTex.t) return gTex.t;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d');
  x.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + (i * Math.PI) / 5, r = i % 2 ? 13 : 30; x.lineTo(32 + Math.cos(a) * r, 33 + Math.sin(a) * r); } x.closePath();
  x.fillStyle = '#ffe14d'; x.fill(); x.lineWidth = 4; x.strokeStyle = '#000'; x.stroke();
  return (gTex.t = new THREE.CanvasTexture(c));
}
const stars = new Map();
export function updateQuiz(dt, now) {
  if (!G.joined) { for (const id of [...quizzes.keys()]) dropQ(quizzes, id); if (el) el.classList.remove('on'); mineQ = null; ME.quizUntil = 0; return; }
  stepQ(quizzes, now, (id) => G.remotes.get(id), false);
  if (mineQ) {
    if (!ME.alive) { mineQ = null; el.classList.remove('on'); ME.quizUntil = 0; }
    else {
      W.held = false; W.aimHeld = false;
      const left = Math.max(0, mineQ.until - now) / 1000;
      el.querySelector('.bar i').style.width = (left / QUIZ.time) * 100 + '%';
      el.classList.toggle('hurry', left < 2);
      const t = Math.ceil(left * (left < 2 ? 4 : 1));
      if (t !== tick) { tick = t; if (left > 0) sfx.quizTick(left < 2); }
    }
  }
  if (now < (ME.fastUntil || 0) && ME.alive) ME.speedMul = (ME.speedMul || 1) * QUIZ.fast;
  // gold stars over whoever aced one (while nothing can hurt them)
  for (const [id, until] of golds) {
    let s = stars.get(id);
    const r = id === G.myId ? null : G.remotes.get(id);
    if (now > until || (r && !r.alive) || (id !== G.myId && !r)) { if (s) { G.scene.remove(s); s.material.dispose(); stars.delete(id); } golds.delete(id); continue; }
    if (!r) continue; // yours: the HUD said so
    if (!s) { s = new THREE.Sprite(new THREE.SpriteMaterial({ map: goldStar(), depthTest: false, transparent: true })); s.renderOrder = 9; G.scene.add(s); stars.set(id, s); }
    s.position.set(r.pos[0], r.pos[1] + 2.9 + Math.sin(now * 0.006) * 0.1, r.pos[2]); s.scale.setScalar(0.7 + Math.sin(now * 0.012) * 0.08);
    s.material.rotation = Math.sin(now * 0.004) * 0.3;
    s.visible = !RP.active;
    if (Math.random() < dt * 14) fx.spray([r.pos[0] + (Math.random() - 0.5), r.pos[1] + 1 + Math.random() * 1.2, r.pos[2] + (Math.random() - 0.5)], 1, [0xffe14d, 0xffffff], 1, 0.5, 0.08, -1, 0.5);
  }
}
export function quizReset() { for (const id of [...quizzes.keys()]) dropQ(quizzes, id); golds.clear(); for (const s of stars.values()) G.scene.remove(s); stars.clear(); if (el) el.classList.remove('on'); mineQ = null; ME.quizUntil = 0; ME.fastUntil = 0; }

// ------------------------------------------------------------ replays: the giant calculator over the ghost, the mark
RP_HOOKS.push({
  ev(m, ghosts) {
    if (m.t === 'quiz') { dropQ(ghostQ, m.id); ghostQ.set(m.id, makeQ(m, G.scene)); sfx.calcBonk(); return true; }
    if (m.t === 'quizx') { const Q = ghostQ.get(m.id); if (Q) result(Q, m); return true; }
    return false;
  },
  pre(m, ghosts, s, t0) {
    if (m.t === 'quiz' && s + m.left > t0) { dropQ(ghostQ, m.id); const Q = makeQ({ ...m, left: s + m.left - t0 }, G.scene); ghostQ.set(m.id, Q); }
    if (m.t === 'quizx') dropQ(ghostQ, m.id);
  },
  step(t, ghosts) { stepQ(ghostQ, performance.now(), (id) => ghosts.get(id), true); },
  stop() { for (const id of [...ghostQ.keys()]) dropQ(ghostQ, id); },
  preroll(ev, t0) { return ev.filter((e) => e.s < t0 && e.s > t0 - 8000 && (e.m.t === 'quiz' || e.m.t === 'quizx')); },
});
