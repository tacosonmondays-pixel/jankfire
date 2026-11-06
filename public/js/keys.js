// Rebindable controls: every action the player can bind lives in ACTIONS, nowhere else.
// a binding is a KeyboardEvent.code ('KeyW', 'Space', 'ControlLeft') or a mouse button ('Mouse0' left, 'Mouse2' right,
// 'Mouse3' / 'Mouse4' the side buttons). each action has a primary and an alternate slot.
// ADDING AN ACTION = one line in ACTIONS: [id, label, group, [default, alternate], ctx?]. then react to it in main.js
// (K.matches('id', e) in pressed(), K.up('id', e) in released(), or K.isDown('id') for held stuff) and use
// K.label('id') in any hint. it shows up in SETTINGS > CONTROLS by itself and old saves get its default.
// ctx: actions in different contexts may share a key (skip-replay Space vs jump Space, vote 1 vs slot 1).
// saves keep only what the player changed (settings.binds = { v, set }), so a new default reaches everyone else.
export const GROUPS = ['Movement', 'Combat', 'Weapons', 'Items & streaks', 'Social', 'Interface'];
export const ACTIONS = [
  ['forward', 'Move forward', 'Movement', ['KeyW']],
  ['back', 'Move back', 'Movement', ['KeyS']],
  ['left', 'Strafe left', 'Movement', ['KeyA']],
  ['right', 'Strafe right', 'Movement', ['KeyD']],
  ['jump', 'Jump (hold to bhop)', 'Movement', ['Space']],
  ['sprint', 'Run', 'Movement', ['ShiftLeft', 'ShiftRight']],
  ['crouch', 'Crouch / slide / ground slam', 'Movement', ['KeyC', 'ControlLeft']],
  ['grapple', 'Grapple (hold)', 'Movement', ['KeyE', 'Mouse3']],
  ['fire', 'Fire / swing', 'Combat', ['Mouse0']],
  ['aim', 'Aim · heavy stab · pick card', 'Combat', ['Mouse2']],
  ['parry', 'Katana: parry', 'Combat', ['Mouse2'], 'katana'], // its own context: shares right click with aim, wins while the katana is out
  ['reload', 'Reload / redraw', 'Combat', ['KeyR']],
  ['use', 'Use (hold): plant · defuse · zombies buy + revive · inspect', 'Combat', ['KeyF']],
  ['slot1', 'Primary', 'Weapons', ['Digit1']],
  ['slot2', 'Secondary', 'Weapons', ['Digit2']],
  ['slot3', 'Melee', 'Weapons', ['Digit3']],
  ['slot4', 'Slot 4 (Scythe Rifle)', 'Weapons', ['Digit4']],
  ['lastSlot', 'Last weapon', 'Weapons', ['KeyQ']],
  ['item', 'Use item', 'Items & streaks', ['KeyG']],
  ['nvgFlash', 'Goggles: flash', 'Items & streaks', ['Mouse1', 'KeyN']], // night vision goggles. not H: H drops in Plant & Defuse
  ['streak1', 'Killstreak 1', 'Items & streaks', ['Digit5']],
  ['streak2', 'Killstreak 2', 'Items & streaks', ['Digit6']],
  ['streak3', 'Killstreak 3', 'Items & streaks', ['Digit7']],
  ['scythe', 'Scythe: rifle mode', 'Items & streaks', ['KeyX']],
  ['dash', 'Scythe: glitch dash (hold)', 'Items & streaks', ['KeyV']],
  ['spray', 'Spray', 'Social', ['KeyZ']],
  ['chat', 'Chat', 'Social', ['KeyT', 'Enter']],
  ['scores', 'Scoreboard (hold)', 'Interface', ['Tab']],
  ['menu', 'Pause menu', 'Interface', ['KeyB']],
  ['skip', 'Skip killcam / replay', 'Interface', ['Space', 'Enter'], 'replay'],
  ['vote1', 'Vote: option 1', 'Interface', ['Digit1'], 'vote'],
  ['vote2', 'Vote: option 2', 'Interface', ['Digit2'], 'vote'],
  ['vote3', 'Vote: option 3', 'Interface', ['Digit3'], 'vote'],
  ['vote4', 'Vote: option 4', 'Interface', ['Digit4'], 'vote'],
  // Plant & Defuse (econ.js): its own context, so B can be the buy menu there and the pause menu everywhere else
  ['buy', 'Plant & Defuse: buy menu', 'Interface', ['KeyB'], 'eco'],
  ['drop', 'Plant & Defuse: drop what you hold (+ Shift: your item)', 'Weapons', ['KeyH'], 'eco'],
  ['pause', 'Pause menu (also where B buys)', 'Interface', ['KeyP'], 'eco'],
].map(([id, label, group, def, ctx]) => ({ id, label, group, def, ctx: ctx || 'game' }));

const BY = Object.assign(Object.create(null), Object.fromEntries(ACTIONS.map((a) => [a.id, a]))); // no prototype: a save key like 'toString' is just unknown
{ // dev check for the one-line adds: a repeated id or two defaults on one key in one context would both fire
  const seen = new Set();
  for (const a of ACTIONS) {
    if (seen.has('id|' + a.id)) console.warn('keys.js: duplicate action id', a.id);
    seen.add('id|' + a.id);
    for (const c of a.def) { if (seen.has(a.ctx + '|' + c)) console.warn('keys.js: two default bindings on', c, 'in', a.ctx); seen.add(a.ctx + '|' + c); }
  }
}
const RESERVED = new Set(['Escape']); // pointer lock / pause: never bindable
const okCode = (c) => typeof c === 'string' && c.length > 0 && c.length <= 32 && /^[A-Za-z0-9]+$/.test(c) && !RESERVED.has(c);
const mac = typeof navigator !== 'undefined' && /Mac/.test(navigator.platform || '');
const NAMES = {
  Space: 'Space', Enter: 'Enter', Tab: 'Tab', Backspace: 'Backspace', CapsLock: 'Caps Lock', Delete: 'Delete', Insert: 'Insert',
  ShiftLeft: 'Left Shift', ShiftRight: 'Right Shift', ControlLeft: 'Left Ctrl', ControlRight: 'Right Ctrl',
  AltLeft: mac ? 'Left Option' : 'Left Alt', AltRight: mac ? 'Right Option' : 'Right Alt',
  MetaLeft: mac ? 'Left Cmd' : 'Left Win', MetaRight: mac ? 'Right Cmd' : 'Right Win', ContextMenu: 'Menu key',
  ArrowUp: 'Up', ArrowDown: 'Down', ArrowLeft: 'Left', ArrowRight: 'Right', PageUp: 'Page Up', PageDown: 'Page Down', Home: 'Home', End: 'End',
  Backquote: '`', Minus: '-', Equal: '=', BracketLeft: '[', BracketRight: ']', Backslash: '\\', IntlBackslash: '\\',
  Semicolon: ';', Quote: "'", Comma: ',', Period: '.', Slash: '/',
  NumpadEnter: 'Num Enter', NumpadAdd: 'Num +', NumpadSubtract: 'Num -', NumpadMultiply: 'Num *', NumpadDivide: 'Num /', NumpadDecimal: 'Num .',
  Mouse0: 'LMB', Mouse1: 'MMB', Mouse2: 'RMB', Mouse3: 'Mouse 4', Mouse4: 'Mouse 5',
};
let layout = null; // the real letters on this keyboard (AZERTY etc.), when the browser will say
try { if (navigator.keyboard && navigator.keyboard.getLayoutMap) navigator.keyboard.getLayoutMap().then((m) => { layout = m; changed(); }).catch(() => {}); } catch { /* not allowed here */ }

let set = {};    // what the player changed: id -> [primary, alternate] (null = empty)
let eff = {};    // what's actually bound right now: overrides, else defaults nobody else took
let store = null;
const subs = [];
const down = new Set();     // codes held right now
const held = new Map();     // code -> actions it pressed (so a rebind or a menu mid-hold still releases them)
let lastUp = { code: '', acts: new Set() };

function rebuild() {
  const taken = new Set();
  for (const id in set) for (const c of set[id]) if (c) taken.add(BY[id].ctx + '|' + c);
  eff = {};
  for (const a of ACTIONS) eff[a.id] = set[a.id] ? set[a.id].slice() : [0, 1].map((i) => (a.def[i] && !taken.has(a.ctx + '|' + a.def[i]) ? a.def[i] : null));
}
function changed(rebound) { for (const f of subs) { try { f(!!rebound); } catch (e) { console.error(e); } } }
function commit() {
  for (const id in set) if (set[id][0] === (BY[id].def[0] || null) && set[id][1] === (BY[id].def[1] || null)) delete set[id]; // back to default: forget it
  rebuild();
  if (store) store.binds = { v: 1, set: JSON.parse(JSON.stringify(set)) };
  changed(true);
}
const codeOf = (e) => (!e ? '' : e.type && e.type.startsWith('mouse') ? 'Mouse' + e.button : e.code || '');
const ids = (x) => (Array.isArray(x) ? x : [x]);

export const K = {
  // read settings.binds (or the old 'right click grapples' checkbox) and keep writing changes back there
  attach(s) {
    store = null; set = {};
    const b = s && s.binds;
    try {
      if (b && typeof b === 'object' && b.v > 1) { rebuild(); store = s; changed(true); return; } // a newer build's save: play on defaults, leave it alone until a key changes
      if (b && typeof b === 'object' && b.v === 1 && b.set && typeof b.set === 'object') {
        const used = new Set();
        for (const [id, v] of Object.entries(b.set)) {
          if (!BY[id] || !Array.isArray(v)) continue; // an action that's gone: ignore it
          set[id] = [0, 1].map((i) => {
            const c = okCode(v[i]) && !used.has(BY[id].ctx + '|' + v[i]) ? v[i] : null; // a broken save can't double-bind a key
            if (c) used.add(BY[id].ctx + '|' + c);
            return c;
          });
        }
      }
      rebuild();
    } catch (e) { console.error('keys.js: bad save, using defaults', e); set = {}; rebuild(); }
    store = s;
    // the old checkbox (also from a profile synced by an old client): a preset, E aims and right click grapples
    if (s && s.swapAim) { s.swapAim = false; if (!set.aim && !set.grapple) { K.set('grapple', 0, 'Mouse2'); K.set('aim', 0, 'KeyE'); return; } }
    commit();
  },
  onChange(fn) { subs.push(fn); }, // fn(rebound): false when only the key names changed (keyboard layout)
  get(id) { return (eff[id] || [null, null]).slice(); },
  isDefault(id) { return !set[id]; },
  // bind one slot; a key another action in the same context had gets swapped: that action takes this slot's old key
  set(id, slot, code) {
    const a = BY[id];
    if (!a || (code != null && !okCode(code))) return null;
    const cur = eff[id].slice(), old = cur[slot];
    let moved = null;
    if (code) {
      for (const b of ACTIONS) {
        if (b.id === id || b.ctx !== a.ctx) continue;
        const j = eff[b.id].indexOf(code);
        if (j < 0) continue;
        const nb = eff[b.id].slice();
        nb[j] = old && !nb.includes(old) ? old : null;
        set[b.id] = nb; eff[b.id] = nb;
        moved = { id: b.id, label: b.label, to: nb[j] };
      }
      const k = cur.indexOf(code);
      if (k >= 0 && k !== slot) cur[k] = old; // it was this action's other slot: swap the two
    }
    cur[slot] = code || null;
    set[id] = cur;
    commit();
    return moved;
  },
  reset(id) { const a = BY[id], moved = []; if (!a) return moved; for (const i of [0, 1]) { const m = K.set(id, i, a.def[i] || null); if (m) moved.push(m); } return moved; },
  resetAll() { set = {}; commit(); },
  // does this key / mouse event trigger the action (or any of a list)?
  matches(x, e) { const c = codeOf(e); return !!c && ids(x).some((id) => eff[id] && eff[id].includes(c)); },
  // a release: true when this code is bound to it or was what pressed it
  up(x, e) { const c = codeOf(e); return ids(x).some((id) => (lastUp.code === c && lastUp.acts.has(id)) || (eff[id] && !!c && eff[id].includes(c))); },
  isDown(id) { return !!eff[id] && eff[id].some((c) => c && down.has(c)); },
  bound(e) { const c = codeOf(e); return !!c && ACTIONS.some((a) => eff[a.id].includes(c)); },
  clear() { down.clear(); held.clear(); },
  codeOf,
  reserved: (c) => RESERVED.has(c),
  codeLabel(c) {
    if (!c) return 'unbound';
    if (layout && /^Key|^(Backquote|Minus|Equal|Bracket|Backslash|Semicolon|Quote|Comma|Period|Slash)/.test(c)) { const k = layout.get(c); if (k && k.trim()) return k.toUpperCase(); }
    if (NAMES[c]) return NAMES[c];
    if (/^Key[A-Z]$/.test(c)) return c.slice(3);
    if (/^Digit\d$/.test(c)) return c.slice(5);
    if (/^Numpad\d$/.test(c)) return 'Num ' + c.slice(6);
    if (/^Mouse\d+$/.test(c)) return 'Mouse ' + (Number(c.slice(5)) + 1);
    return c;
  },
  // the key to show in a hint: the primary, or the alternate when the primary is empty
  label(id, fallback) { if (!eff[id]) return fallback != null ? fallback : id; const b = eff[id]; return K.codeLabel(b[0] || b[1]); },
  labels(id) { const b = (eff[id] || []).filter(Boolean); return b.length ? b.map(K.codeLabel).join(' / ') : 'unbound'; },
  // shared text (weapon / streak / mode descriptions) is written for the default keys: swap in the player's
  hint(text) {
    if (typeof text !== 'string') return text;
    // an unbound action keeps the default wording ('unbound parries' reads worse than a stale key)
    const r = (re, id, f) => { if (!K.get(id).some(Boolean) || K.label(id) === K.codeLabel(BY[id].def[0])) return; text = text.replace(re, f || (() => K.label(id))); };
    r(/\b[Rr]ight click(?= (to )?parr)/g, 'parry'); // before aim: the katana's right click is the parry key
    r(/\b[Rr]ight click\b/g, 'aim');
    r(/\b[Ll]eft click\b/g, 'fire');
    r(/\b[Mm]iddle click(?= flashes)/g, 'nvgFlash');
    r(/\bR(?= redraws)/g, 'reload');
    r(/\bX(?=:| turns| to flip)/g, 'scythe');
    r(/\b([Hh]old) V\b/g, 'dash', (m, h) => `${h} ${K.label('dash')}`);
    r(/\(E,/g, 'grapple', () => `(${K.label('grapple')},`);
    r(/\bW(?= pumps)/g, 'forward');
    r(/\b([Hh]old) F\b/g, 'use', (m, h) => `${h} ${K.label('use')}`);
    return text;
  },
  // keys typed into chat or any text box never reach the game
  typing(e) {
    const t = e && e.target;
    if (!t || !t.tagName) return false;
    if (t.isContentEditable || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT') return true;
    return t.tagName === 'INPUT' && !/^(checkbox|radio|range|button|submit|reset|color|file)$/i.test(t.type || '');
  },
};

// held-key tracking runs first (capture), for every key and button, so isDown and releases stay right
if (typeof addEventListener === 'function') {
  const press = (e) => {
    if (K.typing(e)) return;
    const c = codeOf(e);
    if (!c) return;
    down.add(c);
    const acts = held.get(c) || new Set();
    for (const a of ACTIONS) if (eff[a.id].includes(c)) acts.add(a.id);
    held.set(c, acts);
  };
  const release = (e) => {
    const c = codeOf(e);
    down.delete(c);
    lastUp = { code: c, acts: held.get(c) || new Set() };
    held.delete(c);
  };
  addEventListener('keydown', press, true);
  addEventListener('mousedown', press, true);
  addEventListener('keyup', release, true);
  addEventListener('mouseup', release, true);
  // the side buttons mean back / forward to the browser (and Electron): never let them navigate away from the game
  for (const t of ['mousedown', 'mouseup', 'auxclick']) addEventListener(t, (e) => { if (e.button === 3 || e.button === 4) e.preventDefault(); }, true);
  addEventListener('blur', () => K.clear());
}
