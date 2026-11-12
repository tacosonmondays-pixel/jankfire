// The map editor's menu button (editor.html). Owner/dev only for now: hidden unless this browser was let in, by opening
// the game with ?editor=1 (?editor=0 locks it again) or by typing "editor" on the main menu (works in the exe too).
// The editor only changes what this browser draws and saves a file: nothing it does reaches the server or a match.
const KEY = 'jfEditor';
const on = () => { try { return localStorage.getItem(KEY) === '1'; } catch { return false; } };
const set = (v) => { try { if (v) localStorage.setItem(KEY, '1'); else localStorage.removeItem(KEY); } catch { /* private mode: the URL flag still works this once */ } };
try { const q = new URLSearchParams(location.search).get('editor'); if (q === '1') set(true); else if (q === '0') set(false); } catch { /* fine */ }
function button() {
  let b = document.getElementById('navEditor');
  const want = on() && !window.JF_TOUCH; // (it needs a keyboard and a mouse)
  if (!want) { if (b) b.remove(); return; }
  if (b) return;
  const row = document.querySelector('#menu .nav-sec');
  if (!row) return;
  b = document.createElement('button');
  b.className = 'hnav sec hicon'; b.id = 'navEditor'; b.title = 'map editor: fly round any map, move and delete props (only in this browser)';
  b.innerHTML = '<span class="ni"><img alt=""></span><b>MAP EDITOR</b>';
  let n = 0; const ico = setInterval(() => { // (the menu's icons are rendered after load: borrow the cog's picture)
    const src = document.querySelector('[data-go="settings"] .ni img'), im = b.querySelector('.ni img');
    if (src && src.src && im) { im.src = src.src; clearInterval(ico); } else if (++n > 40) clearInterval(ico);
  }, 400);
  b.addEventListener('click', () => { location.href = '/editor.html'; });
  row.append(b);
}
let typed = '';
addEventListener('keydown', (e) => {
  if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
  if (document.pointerLockElement) return; // (only on the menus, not mid-match)
  if (!/^Key[A-Z]$/.test(e.code)) return;
  typed = (typed + e.code.slice(3).toLowerCase()).slice(-6);
  if (typed === 'editor') { set(!on()); typed = ''; button(); }
});
button();
addEventListener('load', button);
