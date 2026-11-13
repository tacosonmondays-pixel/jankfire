// static files, cheaper: an ETag so a returning player's browser gets "304 not modified" instead of 30 MB again
// (the models used to come down in full on every visit), and gzip for text + .glb (packed models still shrink ~40%).
// gzipped copies are kept in memory (capped), made once per file version.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';

const ZIP = new Set(['.glb', '.js', '.css', '.html', '.json', '.svg', '.webmanifest', '.wav']);
// fonts and music: a returning player's browser shows its copy at once and checks for a newer one behind it
// (stale-while-revalidate). they don't change with art PRs. models, pictures and code stay no-cache + ETag (a 304 is
// cheap): new models and textures ship many times a day, and new code next to a stale .glb could break
const MEDIA = new Set(['.ogg', '.mp3', '.woff2', '.woff', '.ttf']);
const gz = new Map(); // file -> { tag, buf | promise }
let gzBytes = 0;
const GZ_CAP = 32 * 1024 * 1024; // (the models are ~12 MB gzipped, the scripts a few: fits, and leaves room on a 512 MB box)

// past the memory cap, gzipped copies go to a temp folder instead of being made again for every request (the game's
// models alone are bigger than the cap: a story player used to wait on re-gzipping most of 19 MB on a small box)
const DISK = path.join(os.tmpdir(), 'jf-gz');
let diskOk = true;
try { fs.mkdirSync(DISK, { recursive: true }); } catch { diskOk = false; }
const diskName = (file, tag) => path.join(DISK, crypto.createHash('sha1').update(file + '\n' + tag).digest('hex') + '.gz');
function gzipOf(file, tag) {
  const c = gz.get(file);
  if (c && c.tag === tag) return c.p;
  if (c && c.buf) gzBytes -= c.buf.length;
  const e = { tag, buf: null, p: null };
  const keep = (buf) => { if (gzBytes + buf.length > GZ_CAP) { gz.delete(file); return; } e.buf = buf; gzBytes += buf.length; }; // over the cap: the disk copy serves it next time
  const make = (res) => fs.readFile(file, (err, raw) => {
    if (err) { gz.delete(file); res(null); return; }
    zlib.gzip(raw, { level: 6 }, (err2, buf) => {
      if (err2) { gz.delete(file); res(null); return; }
      keep(buf); res(buf);
      if (diskOk) { const f = diskName(file, tag), t = f + '.' + process.pid + '.tmp'; fs.writeFile(t, buf, (we) => { if (we) { fs.unlink(t, () => {}); return; } fs.rename(t, f, () => {}); }); } // (whole files only: written aside, then renamed)
    });
  });
  e.p = new Promise((res) => {
    if (!diskOk) { make(res); return; }
    fs.readFile(diskName(file, tag), (err, buf) => { if (err || !buf.length) { make(res); return; } keep(buf); res(buf); });
  });
  gz.set(file, e);
  return e.p;
}

export function sendStatic(req, res, file, st, ext, type) {
  const tag = `W/"${st.size.toString(36)}-${Math.floor(st.mtimeMs).toString(36)}"`;
  const head = { 'content-type': type, 'cache-control': MEDIA.has(ext) ? 'max-age=0, stale-while-revalidate=604800' : 'no-cache', etag: tag, 'last-modified': st.mtime.toUTCString() };
  if (ZIP.has(ext)) head.vary = 'Accept-Encoding';
  const inm = req.headers['if-none-match'];
  if (typeof inm === 'string' && inm.split(',').some((t) => t.trim() === tag)) { res.writeHead(304, head).end(); return; }
  const ae = req.headers['accept-encoding'];
  if (ZIP.has(ext) && st.size > 1024 && typeof ae === 'string' && /\bgzip\b/.test(ae)) {
    gzipOf(file, tag).then((buf) => {
      if (!buf) { res.writeHead(404).end('404'); return; }
      res.writeHead(200, { ...head, 'content-encoding': 'gzip', 'content-length': buf.length });
      res.end(req.method === 'HEAD' ? undefined : buf);
    });
    return;
  }
  res.writeHead(200, { ...head, 'content-length': st.size });
  if (req.method === 'HEAD') { res.end(); return; }
  fs.createReadStream(file).on('error', () => res.destroy()).pipe(res);
}
