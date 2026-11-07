// the MR. OVERTIME rehearsal (?story=1&otpreview=1): he appears in front of you and runs his whole set on a loop, with
// a caption for each move and its marks. no damage, no fight: for checking the animation, the fx and the timing
import { ME } from '../player.js';
import { spawnActor, actors, walkTo, dropTo } from './actors.js';
import { OT, MARKS } from './overtime.js';
import { where, LAB } from './boot.js';

// [clip, seconds, what to do first, caption]
const PROGRAM = [
  ['ot_idle', 3, null, 'IDLE MENACE'],
  ['ot_staple', 1.8, null, 'STAPLE GUN · clack, clack, FIRE'],
  ['ot_stalk', 3.5, 'walkIn', 'STALK'],
  ['ot_fan', 2.5, null, 'STAPLE FAN · ten clacks, five staples'],
  ['ot_slam', 2.8, 'walkOut', 'OVERTIME SLAM · watch, crouch, jump, frozen ring'],
  ['ot_punchin', 3.0, null, 'PUNCH IN · the slot opens'],
  ['ot_flinch', 1.0, 'cracked', 'CRIT FLINCH · the clock cracks'],
  ['ot_roar', 2.6, null, 'PHASE CHANGE'],
  ['ot_plate_rip', 2.4, null, 'PLATE RIPPED OFF'],
  ['ot_coffee', 5.5, 'sparking', 'COFFEE BREAK · the heart is sparking'],
  ['ot_flinch', 1.0, 'ripped', 'HEART RIP'],
  ['ot_kneel', 3.5, null, '"RESCHEDULED" · on one knee'],
  ['ot_clockout', 5.0, null, 'CLOCK OUT'],
  ['ot_idle', 1.5, 'fresh', 'BACK ON SHIFT (the machine prints a new one)'],
];

let P = null, STAND = null, YAW = 0;
export function start() {
  if (P) return;
  // in the city: he stands in the gate (the arena's boss spot); you're 9 m south of him, the zone sign behind you
  const boss = !LAB && where('arena.boss');
  let at, yaw;
  if (boss) {
    STAND = [boss[0] + 2, boss[1], boss[2] + 9];
    ME.pos = [...STAND]; ME.vel = [0, 0, 0]; ME.yaw = Math.atan2(-(boss[0] - STAND[0]), -(boss[2] - STAND[2])); ME.pitch = 0.14; YAW = ME.yaw;
    at = [boss[0], boss[1], boss[2]]; at[1] = dropTo([at[0], boss[1] + 2, at[2]], 4);
  } else {
    const f0 = [-Math.sin(ME.yaw), -Math.cos(ME.yaw)];
    at = [ME.pos[0] + f0[0] * 13, ME.pos[1], ME.pos[2] + f0[1] * 13]; at[1] = dropTo(at, 3);
  }
  const dx = ME.pos[0] - at[0], dz = ME.pos[2] - at[2], dl = Math.hypot(dx, dz) || 1, f = [-dx / dl, -dz / dl]; // (f: from you to him)
  yaw = Math.atan2(dx, dz) + Math.PI;
  const a = spawnActor('ot_preview', { look: 'overtime', voice: { kind: 'dialtone', pitch: 0.7, rate: 0.9 }, name: 'MR. OVERTIME' }, at, yaw);
  a.lookAt = null; a.home.face = a.yaw;
  const cap = document.createElement('div'); cap.id = 'otPrev';
  cap.style.cssText = 'position:fixed;left:24px;top:64px;transform:rotate(-2deg);z-index:60;font:900 24px var(--font,sans-serif);color:#ffe14d;background:rgba(18,8,24,.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:8px 18px;pointer-events:none;text-align:center';
  document.body.append(cap);
  P = { a, i: -1, t: 0, cap, home: [...at], near: [at[0] - f[0] * 3.5, at[1], at[2] - f[1] * 3.5], marks: [] };
  OT.on((ev) => { if (ev.id !== 'ot_preview') return; P.marks.push(ev.mark.toUpperCase() + '!'); P.marks = P.marks.slice(-5); P.markT = 0.9; });
  next();
}
function next() {
  P.i = (P.i + 1) % PROGRAM.length;
  const [clip, len, pre, label] = PROGRAM[P.i], a = P.a;
  if (pre === 'walkIn') walkTo(a, [P.near], 2.2);
  if (pre === 'walkOut') { walkTo(a, [P.home], 2.6, () => { a.yaw = a.home.face; }); }
  if (pre && pre !== 'walkIn' && pre !== 'walkOut') OT.dmg(a, pre === 'fresh' ? 'fresh' : pre);
  OT.play(a, clip, { hold: CLIP_HOLD.has(clip) });
  P.t = 0; P.len = len; P.label = label; P.marks = [];
  render();
}
const CLIP_HOLD = new Set(['ot_idle', 'ot_stalk', 'ot_coffee', 'ot_kneel', 'ot_clockout']);
function render() { P.cap.innerHTML = `${P.label}<div style="font-size:18px;color:#4fd8ff;min-height:22px">${P.marks.join(' ')}</div><div style="font-size:13px;color:#fff;opacity:.7">mr. overtime rehearsal · ${P.i + 1}/${PROGRAM.length} · no damage</div>`; }
export function previewFrame(dt) {
  if (!P) return;
  if (STAND && (P.total || 0) < 1.5) { ME.pos = [...STAND]; ME.vel = [0, 0, 0]; ME.yaw = YAW; ME.pitch = 0.14; } // (the shell may still be placing you)
  P.t += dt; P.total = (P.total || 0) + dt; window.JF_OTP = { total: P.total, step: P.i, label: P.label }; // (the recorder retimes its video with this)
  if (P.markT > 0) { P.markT -= dt; render(); }
  if (P.t >= P.len) next();
}
export const previewOn = () => !!P;
