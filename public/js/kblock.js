// browser shortcuts vs the game. crouch is Left Ctrl too, so crouch-walking forward is Ctrl+W, which closes the tab
// (the last tab: the whole of Chrome). a page can't block that, but in real fullscreen the Keyboard Lock api hands
// those keys to the game instead. so: while you're playing in fullscreen, lock the keys browser shortcuts ride on;
// let go on the menu, pause, chat and leaving fullscreen. Esc is never locked (it still exits fullscreen as usual).
// windowed, it can't be locked: the first Ctrl crouch shows a one-time tip instead. the exe has no menu, so
// Ctrl+W never did anything there: none of this runs in it. (story mode also asks "Leave site?": story/main.js)
import { G } from './ctx.js';
import { K } from './keys.js';
import { hud } from './hud.js';

// Ctrl+W/Q/T/N/Tab/1-9 and Ctrl+Shift+W/Q/T/N: close, quit, new tab or window, switch tabs. (R, H, J, S, D... the
// page can already stop: main.js preventDefaults every bound key)
const KEYS = ['KeyW', 'KeyQ', 'KeyT', 'KeyN', 'Tab', ...Array.from({ length: 9 }, (_, i) => 'Digit' + (i + 1))];
const desktop = () => !!(window.jf && window.jf.desktop);
let locked = false, busy = false;
// main.js, every frame: want = in a game, playing (menu, pause and chat closed)
export function kbLock(want) {
  const kb = navigator.keyboard;
  if (!kb || !kb.lock || desktop()) return;
  want = !!want && !!document.fullscreenElement;
  if (want === locked || busy) return;
  if (want) { busy = true; kb.lock(KEYS).then(() => { locked = true; }, () => {}).finally(() => { busy = false; }); }
  else { try { kb.unlock(); } catch { /* fine */ } locked = false; }
}
export const kbLocked = () => locked;
document.addEventListener('fullscreenchange', () => { if (!document.fullscreenElement && locked) kbLock(false); }); // (the browser drops the lock itself)

// the tip: the first time you crouch on Ctrl in a windowed browser game
const TIP = 'jfCtrlTip';
addEventListener('keydown', (e) => {
  if (e.repeat || !/^Control/.test(e.code) || !G.joined || locked || desktop() || !K.matches('crouch', e)) return;
  try { if (localStorage.getItem(TIP)) return; localStorage.setItem(TIP, '1'); } catch { return; }
  hud.msg('tip: ctrl+w closes the browser tab. crouch on C, or go fullscreen', 5);
});
