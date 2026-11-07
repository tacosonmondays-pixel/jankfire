// the server files a browser may load: the game-room code (server/room.js and the server/ modules it imports), so the
// story's solo referee can run the real rules in a web worker. worked out once at boot by following room.js's imports;
// nothing else under server/ (store, accounts, static, the http side) is ever served.
import fs from 'node:fs';
import path from 'node:path';

export function browsableServer(root) {
  const dir = path.join(root, 'server'), ok = new Set();
  const walk = (file) => {
    if (ok.has(file) || !file.startsWith(dir + path.sep) || !file.endsWith('.js')) return;
    let real = '', src = '';
    try { real = fs.realpathSync(file); src = fs.readFileSync(real, 'utf8'); } catch { return; }
    if (real !== file || !fs.lstatSync(file).isFile()) return; // a symlink (or anything odd) is never followed
    ok.add(file);
    for (const m of src.matchAll(/^\s*import\s+(?:[^'"]*?from\s+)?['"](\.{1,2}\/[^'"]+)['"]/gm)) walk(path.resolve(path.dirname(file), m[1]));
  };
  walk(path.join(dir, 'room.js'));
  for (const no of ['store.js', 'accounts.js', 'static.js', 'browsable.js', 'story.js']) ok.delete(path.join(dir, no)); // (never, even if imported one day)
  // the url's path (already decoded, no query) must name one of those files exactly: no listing, no ../, no other files
  const serve = (url) => { const f = path.normalize(path.join(dir, url.slice('/server/'.length))); return ok.has(f) ? f : null; };
  serve.files = () => [...ok].map((f) => path.relative(dir, f)).sort();
  return serve;
}
