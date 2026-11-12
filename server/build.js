// versioned code URLs (load times: the owner's #1 complaint). the page's ~550 scripts were all served no-cache, so every
// visit asked the server about every one again, a round trip each, 4-8 imports deep. now the pages name the code under
// /v/<build>/..., the browser keeps those for good (immutable) and the next visit asks about none of them.
//   <build>: a hash of every code file's path, size and mtime (public, shared, the three.js version). a deploy gives a
//            new build and new URLs, so a fresh page never gets an old script. (a tab left open across a deploy that
//            lazily imports something then gets the new file, as it did before: an old build's URL isn't immutable.)
//            in production it's worked out once at boot; locally it's checked again at most every 2 s (your edits)
//   pages:   each .html gets its import map, module scripts and stylesheets pointed at /v/<build>/, and a
//            <link rel=modulepreload> for every module its scripts import up front (fetched in parallel, not 4-8
//            round trips deep). "/js/" and "/shared/" are in the import map too, so an import('/js/x.js') from anywhere
//            on the page gets the same module the page has
//   /v/<b>/: the file at the rest of the path. code that's in the hash (.js .css .json, not in the media folders) is
//            immutable when <b> is the current build, an old build's code gets the normal headers, and anything not in
//            the hash (models, music, json in the media folders) is sent to its own unversioned address
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import { sendStatic } from './static.js';

const CODE = new Set(['.js', '.mjs', '.css', '.json']);
const SKIP = new Set(['models', 'music', 'sounds', 'fonts', 'icons', 'img', 'textures', 'node_modules', '.git']); // (big media folders: no code in them, not worth the stat walk)
const IMMUTABLE = 'public, max-age=31536000, immutable';

// fileOf(url) -> the file a url is served from (server.js ROUTES), or null
export function makeBuild(ROOT, fileOf, { every = process.env.RENDER || process.env.NODE_ENV === 'production' ? Infinity : 2000 } = {}) { // (production: the files never change under a running server)
  const B = { id: '', at: 0, html: new Map() };
  function walk(dir, h) {
    let es; try { es = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    es.sort((a, b) => (a.name < b.name ? -1 : 1));
    for (const e of es) {
      const f = path.join(dir, e.name);
      if (e.isDirectory()) { if (!SKIP.has(e.name)) walk(f, h); continue; }
      if (!CODE.has(path.extname(e.name)) && path.extname(e.name) !== '.html') continue;
      try { const st = fs.statSync(f); h.update(`${path.relative(ROOT, f)}|${st.size}|${Math.floor(st.mtimeMs)}\n`); } catch { /* gone */ }
    }
  }
  B.now = () => {
    if (B.id && Date.now() - B.at < every) return B.id;
    const h = crypto.createHash('sha1');
    walk(path.join(ROOT, 'public'), h); walk(path.join(ROOT, 'shared'), h);
    try { h.update(fs.readFileSync(path.join(ROOT, 'node_modules/three/package.json'))); } catch { /* no three */ }
    const id = h.digest('hex').slice(0, 10);
    if (id !== B.id) B.html.clear();
    B.id = id; B.at = Date.now();
    return id;
  };

  // the modules a script imports up front (import / export ... from, and bare imports; not import()), breadth first
  const MAP0 = { three: '/vendor/three/build/three.module.js', 'three/addons/': '/vendor/three/examples/jsm/' };
  const STATIC = /(?:^|[\n;])[ \t]*(?:import|export)\s*(?:[\w*{}\s,$]*?\s*from\s*)?['"]([^'"\n]+)['"]/g;
  function resolve(spec, from, map) {
    if (spec.startsWith('./') || spec.startsWith('../')) return path.posix.resolve(path.posix.dirname(from), spec);
    if (spec.startsWith('/')) return spec;
    if (Object.hasOwn(map, spec)) return map[spec];
    for (const k of Object.keys(map)) if (k.endsWith('/') && spec.startsWith(k)) return map[k] + spec.slice(k.length);
    return null;
  }
  function graph(entries, map) {
    const seen = new Set(), out = [], q = [...entries];
    while (q.length && out.length < 1500) {
      const u = q.shift();
      if (seen.has(u) || !/\.m?js$/.test(u)) continue;
      seen.add(u);
      const f = fileOf(u);
      let src; try { src = fs.readFileSync(f, 'utf8'); } catch { continue; }
      out.push(u);
      for (const m of src.matchAll(STATIC)) { const r = resolve(m[1], u, map); if (r && !seen.has(r)) q.push(r); }
    }
    return out;
  }
  // a page, pointed at the build
  function rewrite(src, id) {
    const v = `/v/${id}`;
    let map = { ...MAP0 };
    src = src.replace(/<script type="importmap">([\s\S]*?)<\/script>/, (all, json) => {
      let im = {}; try { im = JSON.parse(json); } catch { return all; }
      map = { ...MAP0, ...(im.imports || {}) };
      const imports = {};
      for (const [k, u] of Object.entries(map)) imports[k] = typeof u === 'string' && u.startsWith('/') ? v + u : u;
      for (const p of ['/js/', '/shared/', '/vendor/']) imports[p] ??= v + p;
      return `<script type="importmap">\n${JSON.stringify({ ...im, imports })}\n</script>`;
    });
    const mods = [];
    src = src.replace(/<script([^>]*?)\ssrc="(\/[^"]+\.m?js)"/g, (all, attrs, u) => { if (/type="module"/.test(attrs)) mods.push(u); return `<script${attrs} src="${v}${u}"`; });
    src = src.replace(/<link rel="stylesheet" href="(\/[^"]+\.css)"/g, (all, u) => `<link rel="stylesheet" href="${v}${u}"`);
    const pre = graph(mods, map).filter((u) => !mods.includes(u)).map((u) => `<link rel="modulepreload" href="${v}${u}">`).join('\n');
    return pre ? src.replace('</head>', `${pre}\n</head>`) : src;
  }
  // a page: rewritten once per build and file version, gzipped, an ETag of its own (always rechecked: no-cache)
  B.sendHtml = (req, res, file, st) => {
    const id = B.now(), key = `${file}|${st.size}|${Math.floor(st.mtimeMs)}`;
    let c = B.html.get(key);
    if (!c) {
      let src; try { src = fs.readFileSync(file, 'utf8'); } catch { res.writeHead(404).end('404'); return; }
      const body = Buffer.from(rewrite(src, id));
      c = { body, gz: zlib.gzipSync(body, { level: 6 }), tag: `W/"${id}-${crypto.createHash('sha1').update(body).digest('hex').slice(0, 12)}"` };
      B.html.set(key, c);
    }
    const head = { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-cache', etag: c.tag, vary: 'Accept-Encoding' };
    const inm = req.headers['if-none-match'];
    if (typeof inm === 'string' && inm.split(',').some((t) => t.trim() === c.tag)) { res.writeHead(304, head).end(); return; }
    const zip = /\bgzip\b/.test(String(req.headers['accept-encoding'] || ''));
    const body = zip ? c.gz : c.body;
    res.writeHead(200, { ...head, ...(zip ? { 'content-encoding': 'gzip' } : {}), 'content-length': body.length });
    res.end(req.method === 'HEAD' ? undefined : body);
  };
  // /v/<build>/<path>: the file at /<path>, kept for good when it's this build's code
  B.sendVersioned = (req, res, url, type) => {
    const m = /^\/v\/([0-9a-f]{6,16})(\/.*)$/.exec(url);
    if (!m) { res.writeHead(404).end('404'); return; }
    const file = fileOf(m[2]);
    if (!file) { res.writeHead(404).end('404'); return; }
    fs.stat(file, (err, st) => {
      if (err || !st.isFile()) { res.writeHead(404).end('404'); return; }
      const ext = path.extname(file), rel = path.relative(ROOT, file).split(path.sep), hashed = CODE.has(ext) && (rel[0] === 'node_modules' || !rel.some((d) => SKIP.has(d))); // (three.js: its version is in the hash)
      if (!hashed) { res.writeHead(302, { location: m[2] + (req.url.includes('?') ? req.url.slice(req.url.indexOf('?')) : ''), 'cache-control': 'no-cache' }).end(); return; } // (not in the build id: its own address, cached the way it always is)
      if (m[1] === B.now()) { const wh = res.writeHead.bind(res); res.writeHead = (code, h) => wh(code, { ...h, 'cache-control': IMMUTABLE }); }
      sendStatic(req, res, file, st, ext, type(ext));
    });
  };
  return B;
}
