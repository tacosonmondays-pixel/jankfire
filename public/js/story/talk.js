// OVERDUE talk (DESIGN §8.1 "Talk"): the dialogue tree with a cinematic camera. The world keeps running behind it.
// The NPC turns to you, the camera eases over your shoulder and slowly pushes in on their face (a third of the screen),
// lines type out with their babble voice and jaw, answers come up as zine buttons (1-4 or click), and their live 3D
// portrait sits beside the box. Keys: use (F) / jump / fire = next line (or finish typing), 1-4 = answer.
import * as THREE from 'three';
import { K } from '../keys.js';
import { sfx } from '../audio.js';
import { organic, organicRedraw } from '../organic.js';
import { actors, camHead, setFace, play } from './actors.js';
import { drawPortrait } from './portrait.js';
import { wantShot } from './camctl.js';

const $ = (id) => document.getElementById(id);
const SLOTS = ['slot1', 'slot2', 'slot3', 'slot4'];
let T = null, U = null, S = null, A = null, onEnd = null, eyeNow = [0, 0, 0];
const hp = new THREE.Vector3(), ev = new THREE.Vector3(), fw = new THREE.Vector3(), side = new THREE.Vector3();

function ui() {
  if (U) return U;
  const el = document.createElement('div'); el.id = 'stTalk'; el.className = 'hidden';
  el.innerHTML = '<div class="st-port"><canvas></canvas></div><div class="st-box"><div class="st-name"><b></b><span></span></div><div class="st-text"></div><div class="st-opts"></div><div class="st-keys"></div></div>';
  $('stLayer').append(el);
  U = { el, port: el.querySelector('.st-port'), cv: el.querySelector('canvas'), box: el.querySelector('.st-box'), name: el.querySelector('.st-name b'), title: el.querySelector('.st-name span'), text: el.querySelector('.st-text'), opts: el.querySelector('.st-opts'), hint: el.querySelector('.st-keys') };
  organic(U.box, { rim: 5, lumps: 4, shadow: [8, 8] }); organic(U.port, { rim: 5, lumps: 3, shadow: [6, 6] });
  return U;
}

export const talking = () => !!T;
export const talkingTo = () => (T ? T.npc : null);

// start a conversation with an actor. story = the hub (shared/story/story.js). done(T) when it ends
export function startTalk(story, actorId, node = 'start', done = null) {
  if (T) return false;
  S = story; A = actors.get(actorId); onEnd = done;
  ui();
  T = S.talk(actorId, node);
  T.typed = 0; T.shown = -1; T.age = 0; T.camT = 0;
  if (A) { A.talking = true; A.faceTarget = null; }
  document.body.classList.add('st-talk');
  U.el.classList.remove('hidden');
  sfx.click && sfx.click();
  showLine();
  return true;
}

function speakerOf(l) { return l && l.who && l.who !== 'you' ? actors.get(l.who) || A : null; }
function showLine() {
  const l = T.line();
  if (!l) { endTalk(); return; }
  T.typed = 0; T.full = l.act ? l.t.replace(/\*/g, '') : l.t;
  const who = l.who === 'you' ? null : (S.defs.npcs[l.who] || S.defs.npcs[T.npc]);
  U.name.textContent = l.act ? '' : l.who === 'you' ? 'YOU' : who ? who.name : ''; // (stage directions have no speaker)
  U.name.style.display = U.name.textContent ? '' : 'none';
  U.name.className = l.who === 'you' ? 'you' : '';
  U.title.textContent = l.act || l.who === 'you' ? '' : who ? who.title || '' : '';
  U.text.className = 'st-text' + (l.act ? ' act' : '') + (l.who === 'you' ? ' you' : '');
  U.port.classList.toggle('you', l.who === 'you');
  const sp = speakerOf(l);
  for (const a of actors.values()) a.talking = a === sp || a === A;
  if (sp) setFace(sp, l.face || T.face || 'neutral');
  if (sp && l.face === 'shock') play(sp, 'shock');
  render();
}
function render() {
  U.text.textContent = T.full.slice(0, Math.floor(T.typed));
  const typing = T.typed < T.full.length;
  U.opts.innerHTML = '';
  if (!typing && T.opts && T.i === T.lines.length - 1) T.opts.forEach((o, i) => {
    const b = document.createElement('div'); b.className = 'st-opt';
    b.innerHTML = `<i>${K.label(SLOTS[i])}</i>`; b.append(document.createTextNode(o.t));
    b.addEventListener('mousedown', (e) => { e.stopPropagation(); pick(i); });
    U.opts.append(b);
  });
  const u = `<b>${K.label('use')}</b>`;
  U.hint.innerHTML = typing ? `${u} skip` : T.opts && T.i === T.lines.length - 1 ? `pick <b>${K.label('slot1')}</b>-<b>${K.label(SLOTS[T.opts.length - 1])}</b>` : `${u} next`;
  organicRedraw(U.box);
}
function next() {
  if (!T) return;
  if (T.typed < T.full.length) { T.typed = T.full.length; render(); return; }
  if (T.opts && T.i === T.lines.length - 1) return;
  const more = T.next();
  if (!more || T.end) { endTalk(); return; }
  showLine();
}
function pick(i) {
  if (!T || T.typed < T.full.length) return;
  if (!T.choose(i)) return;
  sfx.click && sfx.click();
  if (T.end) { endTalk(); return; }
  showLine();
}
export function endTalk() {
  if (!T) return;
  const t = T; T = null;
  for (const a of actors.values()) { a.talking = false; setFace(a, 'neutral'); }
  U.el.classList.add('hidden');
  document.body.classList.remove('st-talk');
  wantShot(null);
  if (onEnd) onEnd(t);
}

export function talkKey(e) {
  if (!T) return false;
  const n = SLOTS.findIndex((s) => K.matches(s, e));
  if (n >= 0) { if (!e.repeat) pick(n); return true; }
  if (T.opts && T.opts.length === 1 && T.i === T.lines.length - 1 && T.typed >= T.full.length && (K.matches('fire', e) || K.matches('use', e))) { if (!e.repeat) pick(0); return true; } // a one-button prompt ([FIRE], [TAKE]): your own trigger does it
  if (K.matches('use', e) || K.matches('jump', e) || K.matches('fire', e)) { if (!e.repeat) next(); return true; }
  if (K.matches('menu', e)) { endTalk(); return false; }
  return true; // nothing else happens mid-conversation (no shooting the person you're talking to)
}

// every frame: type the line out (the voice blips per letter), the camera, the portrait
export function talkFrame(dt, now, eye) {
  if (!T) return;
  eyeNow = eye;
  T.age += dt; T.camT += dt;
  const l = T.line();
  if (l && T.typed < T.full.length) {
    const before = Math.floor(T.typed);
    T.typed = Math.min(T.full.length, T.typed + dt * (l.act ? 70 : 42));
    const sp = speakerOf(l);
    for (let i = before; i < Math.floor(T.typed); i++) if (sp && !l.act) sp.voice.blip(T.full[i], i, T.full);
    render();
  }
  if (A) A.lookAt = eye;
  // the shot: over your shoulder, pushing in on whoever's talking
  const sp = speakerOf(l) || A;
  if (sp) {
    camHead(sp, hp); // (eased between a puppet's 12 fps poses: the talk cam doesn't judder with them)
    const s = sp.ch.root.scale.y;
    ev.set(eye[0], eye[1], eye[2]);
    fw.copy(hp).sub(ev); fw.y = 0; const d = Math.max(0.6, fw.length()); fw.normalize();
    side.set(-fw.z, 0, fw.x);
    const cam = (T.cam || 'closeup'), push = Math.min(1, T.camT / 9);
    const pos = new THREE.Vector3(), look = new THREE.Vector3();
    if (cam === 'wide') { pos.copy(ev).addScaledVector(fw, -1.4).addScaledVector(side, 1.2); pos.y = hp.y + 0.5; look.copy(hp).addScaledVector(side, -0.3); }
    else if (cam === 'low') { pos.copy(hp).addScaledVector(fw, -Math.min(d, 2.2)).addScaledVector(side, 0.5); pos.y = hp.y - 1.0 * s; look.copy(hp); }
    else { // closeup: your shoulder, the face on the right third
      const dist = (1.55 - push * 0.3) * Math.max(1, s * 0.85) + (sp.L.look === 'gordo' ? 0.5 : 0);
      pos.copy(hp).addScaledVector(fw, -dist).addScaledVector(side, -0.42 * Math.max(1, s * 0.7)); pos.y = hp.y + 0.05 - (hp.y - eye[1]) * 0.25;
      look.copy(hp).addScaledVector(side, -0.28 * Math.max(1, s * 0.6)); look.y -= 0.06 * s;
    }
    wantShot({ pos, look, fov: cam === 'wide' ? 55 : 42, follow: 4 });
    if (sp !== T.portFor || Math.floor(T.age * 15) !== T.portF) { T.portFor = sp; T.portF = Math.floor(T.age * 15); drawPortrait(sp, U.cv); }
  }
}
