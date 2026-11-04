// JANKFIRE desktop app (Electron). Shows a launcher, then either:
//  - joins a server (the official online one, or any address), or
//  - runs the game server inside the app ("host on this PC") for bots, training and wifi parties.
const { app, BrowserWindow, ipcMain, Menu, shell } = require('electron');
const path = require('node:path');
const net = require('node:net');
const os = require('node:os');
const fs = require('node:fs');
const { pathToFileURL, fileURLToPath } = require('node:url');

const ROOT = path.join(__dirname, '..');
const LAUNCHER = path.join(__dirname, 'launcher.html');
let config = { officialServer: '' };
try { config = { ...config, ...JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8')) }; } catch { /* defaults */ }
if (process.env.JF_SERVER) config.officialServer = process.env.JF_SERVER;

let win = null;
let local = null; // { port, lan: [...], mod }
let starting = null;

function lanAddrs(port) {
  return Object.values(os.networkInterfaces()).flat()
    .filter((i) => i && i.family === 'IPv4' && !i.internal).map((i) => `http://${i.address}:${port}`);
}
function freePort(preferred) {
  return new Promise((resolve) => {
    const s = net.createServer();
    s.once('error', () => {
      const s2 = net.createServer();
      s2.listen(0, () => { const p = s2.address().port; s2.close(() => resolve(p)); });
    });
    s.listen(preferred, () => s.close(() => resolve(preferred)));
  });
}
async function waitUp(url, ms = 8000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    try { const r = await fetch(url); if (r.ok) return true; } catch { /* not yet */ }
    await new Promise((r) => setTimeout(r, 150));
  }
  return false;
}
function startLocalServer() {
  if (local) return Promise.resolve(local);
  if (starting) return starting;
  starting = (async () => {
    const port = await freePort(3000);
    process.env.PORT = String(port);
    // accounts made on your own PC are saved in your user folder (Supabase keys are never inside the app)
    process.env.JF_DATA_DIR = path.join(app.getPath('userData'), 'data');
    delete process.env.JF_OPEN;
    delete process.env.SUPABASE_URL;
    delete process.env.SUPABASE_SERVICE_KEY;
    const mod = await import(pathToFileURL(path.join(ROOT, 'server.js')).href);
    if (!(await waitUp(`http://127.0.0.1:${port}/health`))) throw new Error('local server did not start');
    local = { port, lan: lanAddrs(port), mod };
    return local;
  })();
  starting.catch(() => { starting = null; });
  return starting;
}

function normalize(addr) {
  let a = String(addr || '').trim();
  if (!a) throw new Error('type an address');
  if (!/^https?:\/\//i.test(a)) {
    const hostOnly = a.split('/')[0];
    const isIp = /^(\d{1,3}\.){3}\d{1,3}(:\d+)?$/.test(hostOnly) || /^localhost(:\d+)?$/i.test(hostOnly);
    a = (isIp ? 'http://' : 'https://') + a;
    if (isIp && !/:\d+$/.test(hostOnly)) a = a.replace(hostOnly, hostOnly + ':3000');
  }
  const u = new URL(a);
  if (u.protocol !== 'http:' && u.protocol !== 'https:') throw new Error('only http/https addresses');
  return u.origin;
}

// who is calling window.jf? the launcher (a file inside the app), the game page of the server this app runs
// ('host on this PC'), or any other page: the official server or an address typed into JOIN. only the app's own
// pages may start a server, pick one, see the LAN addresses or save anything; any game page may still switch
// screens, change the display mode (not saved) and quit.
function caller(e) {
  const f = e.senderFrame;
  if (!win || !f || f.parent || e.sender !== win.webContents) return 'other'; // no iframes, no other windows
  let u;
  try { u = new URL(f.url); } catch { return 'other'; }
  if (u.protocol === 'file:') {
    try { const p = path.resolve(fileURLToPath(u)); return (process.platform === 'win32' ? p.toLowerCase() === LAUNCHER.toLowerCase() : p === LAUNCHER) ? 'launcher' : 'other'; } catch { return 'other'; }
  }
  if (local && u.protocol === 'http:' && (u.hostname === 'localhost' || u.hostname === '127.0.0.1') && Number(u.port) === local.port) return 'local';
  return u.protocol === 'http:' || u.protocol === 'https:' ? 'remote' : 'other';
}
function need(e, ...kinds) { if (!kinds.includes(caller(e))) throw new Error('not allowed from this page'); }

function showLauncher(err) {
  win.setTitle('JANKFIRE');
  win.loadFile(LAUNCHER, err ? { query: { err } } : undefined);
}

function createWindow() {
  win = new BrowserWindow({
    width: 1280, height: 760, minWidth: 800, minHeight: 500, backgroundColor: '#120818', title: 'JANKFIRE',
    icon: path.join(__dirname, 'icon.png'), autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  Menu.setApplicationMenu(null);
  win.webContents.setWindowOpenHandler(({ url }) => { if (/^https?:/i.test(url)) shell.openExternal(url); return { action: 'deny' }; });
  win.webContents.on('before-input-event', (e, input) => {
    if (input.type !== 'keyDown') return;
    if (input.key === 'F11') { toggleFullscreen(true); e.preventDefault(); } // a real key press: remembered
    if (input.control && input.shift && input.key.toLowerCase() === 'i') win.webContents.toggleDevTools();
  });
  win.webContents.on('did-fail-load', (_e, _code, desc, url, isMain) => {
    if (isMain && !String(url).startsWith('file:')) showLauncher(`couldn't reach ${url} (${desc})`);
  });
  win.webContents.on('page-title-updated', (e) => e.preventDefault());
  // fullscreen changed some other way (the OS button, a page's own fullscreen): keep the mode in step.
  // leaving is always fine to remember; entering only counts for this session
  win.on('enter-full-screen', () => { if (displayMode !== 'fullscreen') { lastMode = displayMode; displayMode = 'fullscreen'; } });
  win.on('leave-full-screen', () => { if (displayMode === 'fullscreen') { displayMode = lastMode; saveDisplay(); } });
  // start in the display mode you picked last time
  const m = readDisplay();
  if (m !== 'windowed') setTimeout(() => applyDisplay(m), 50);
  showLauncher();
}

ipcMain.handle('jf:info', (e) => ({
  version: app.getVersion(), official: config.officialServer || '',
  hosting: local && ['launcher', 'local'].includes(caller(e)) ? { port: local.port, lan: local.lan } : null,
}));
ipcMain.handle('jf:host', async (e) => {
  need(e, 'launcher');
  const l = await startLocalServer();
  win.setTitle(`JANKFIRE · hosting${l.lan.length ? ' · friends join ' + l.lan[0] : ''}`);
  win.loadURL(`http://localhost:${l.port}/`);
  return { port: l.port, lan: l.lan };
});
ipcMain.handle('jf:join', async (e, addr) => {
  need(e, 'launcher');
  const url = normalize(addr);
  win.setTitle(`JANKFIRE · ${new URL(url).host}`);
  win.loadURL(url + '/');
  return url;
});
ipcMain.handle('jf:launcher', (e) => { need(e, 'launcher', 'local', 'remote'); showLauncher(); }); // CHANGE SERVER
// display mode: 'windowed' | 'maximized' (windowed fullscreen) | 'fullscreen'. remembered for next launch when
// it comes from F11 or the app's own pages; a remote page can switch it (its FULLSCREEN button) but not save it.
// every change goes through applyDisplay, so displayMode is always what the window really is.
const MODES = ['windowed', 'maximized', 'fullscreen'];
const displayFile = () => path.join(app.getPath('userData'), 'display.json');
let windowedBounds = null, displayMode = 'windowed', lastMode = 'windowed'; // lastMode: where leaving fullscreen goes back to
function readDisplay() { try { const m = JSON.parse(fs.readFileSync(displayFile(), 'utf8')).mode; return MODES.includes(m) ? m : 'windowed'; } catch { return 'windowed'; } }
function saveDisplay() { try { fs.writeFileSync(displayFile(), JSON.stringify({ mode: displayMode })); } catch { /* not important */ } }
function applyDisplay(mode) {
  if (!win) return;
  const { screen } = require('electron');
  // the normal size, taken only from a really normal window (not one that F11 or the OS made full or maximized)
  if (displayMode === 'windowed' && !win.isFullScreen() && !win.isMaximized()) windowedBounds = win.getBounds();
  if (displayMode !== 'fullscreen') lastMode = displayMode;
  displayMode = mode;
  if (mode === 'fullscreen') { win.setFullScreen(true); return; }
  win.setFullScreen(false);
  if (mode === 'maximized') { // windowed fullscreen: a normal window that fills the screen (taskbar stays)
    win.maximize();
    setTimeout(() => { if (displayMode === 'maximized' && !win.isFullScreen() && !win.isMaximized()) win.setBounds(screen.getDisplayMatching(win.getBounds()).workArea); }, 150);
  } else {
    if (win.isMaximized()) win.unmaximize();
    if (windowedBounds) win.setBounds(windowedBounds);
  }
}
function toggleFullscreen(save) { applyDisplay(displayMode === 'fullscreen' ? lastMode : 'fullscreen'); if (save) saveDisplay(); }
ipcMain.handle('jf:fullscreen', (e) => { need(e, 'launcher', 'local', 'remote'); toggleFullscreen(caller(e) !== 'remote'); return displayMode; });
ipcMain.handle('jf:display', (e, mode) => {
  need(e, 'launcher', 'local', 'remote');
  mode = MODES.includes(mode) ? mode : 'windowed';
  applyDisplay(mode);
  if (caller(e) !== 'remote') saveDisplay();
  return mode;
});
ipcMain.handle('jf:displayGet', () => displayMode);
ipcMain.handle('jf:quit', (e) => { need(e, 'launcher', 'local', 'remote'); app.quit(); });

app.on('before-quit', () => { try { if (local && local.mod.shutdown) local.mod.shutdown(); } catch { /* closing anyway */ } });
app.on('window-all-closed', () => app.quit());
app.whenReady().then(() => {
  createWindow();
  // automated smoke test: host locally, load the game, screenshot, quit
  if (process.env.JF_DESKTOP_TEST) {
    setTimeout(async () => {
      try {
        const shot = async (name) => fs.writeFileSync(path.join(process.env.JF_DESKTOP_TEST, name), (await win.webContents.capturePage()).toPNG());
        await shot('desktop_launcher.png');
        await win.webContents.executeJavaScript('window.jf.host()');
        await new Promise((r) => win.webContents.once('did-finish-load', r));
        await new Promise((r) => setTimeout(r, 3000));
        await shot('desktop_game.png');
        const r = await win.webContents.executeJavaScript('({ url: location.href, desktop: !!window.jf, title: document.title, btn: !!document.getElementById("desktopRow") && getComputedStyle(document.getElementById("desktopRow")).display })');
        const disp = {};
        for (const mode of ['maximized', 'fullscreen', 'windowed']) {
          await win.webContents.executeJavaScript(`window.jf.display('${mode}')`);
          await new Promise((res) => setTimeout(res, 600));
          const bb = win.getBounds();
          disp[mode] = { full: win.isFullScreen(), max: win.isMaximized(), w: bb.width, h: bb.height };
        }
        r.display = disp;
        fs.writeFileSync(path.join(process.env.JF_DESKTOP_TEST, 'desktop_result.json'), JSON.stringify({ ok: true, ...r, local: { port: local.port, lan: local.lan } }));
      } catch (e) {
        fs.writeFileSync(path.join(process.env.JF_DESKTOP_TEST, 'desktop_result.json'), JSON.stringify({ ok: false, error: String(e && e.stack || e) }));
      }
      app.quit();
    }, 1500);
  }
});
