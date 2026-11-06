// static files, cheaper: an ETag so a returning player's browser gets "304 not modified" instead of 30 MB again
// (the models used to come down in full on every visit), and gzip for text + .glb (packed models still shrink ~40%).
// gzipped copies are kept in memory (capped), made once per file version.
import fs from 'node:fs';
import zlib from 'node:zlib';

const ZIP = new Set(['.glb', '.js', '.css', '.html', '.json', '.svg', '.webmanifest', '.wav']);
const gz = new Map(); // file -> { tag, buf | promise }
let gzBytes = 0;
const GZ_CAP = 64 * 1024 * 1024;

function gzipOf(file, tag) {
  const c = gz.get(file);
  if (c && c.tag === tag) return c.p;
  if (c && c.buf) gzBytes -= c.buf.length;
  const e = { tag, buf: null, p: null };
  e.p = new Promise((res) => fs.readFile(file, (err, raw) => {
    if (err) { gz.delete(file); res(null); return; }
    zlib.gzip(raw, { level: 6 }, (err2, buf) => {
      if (err2) { gz.delete(file); res(null); return; }
      if (gzBytes + buf.length > GZ_CAP) { gz.delete(file); res(buf); return; } // over the cap: send it, don't keep it
      e.buf = buf; gzBytes += buf.length; res(buf);
    });
  }));
  gz.set(file, e);
  return e.p;
}

export function sendStatic(req, res, file, st, ext, type) {
  const tag = `W/"${st.size.toString(36)}-${Math.floor(st.mtimeMs).toString(36)}"`;
  const head = { 'content-type': type, 'cache-control': 'no-cache', etag: tag, 'last-modified': st.mtime.toUTCString() };
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
