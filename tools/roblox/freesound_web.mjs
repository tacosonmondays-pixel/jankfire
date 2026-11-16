// Freesound without an API key (16 Nov 2026): search freesound.org's public pages for CC0 (public domain) sounds and
// download their high-quality preview (the same public file the site's own player streams; CC0 means no
// attribution is needed, but every file is still listed in CREDITS.md so its source stays traceable).
//   node tools/roblox/freesound_web.mjs search "marbles scatter" [maxSeconds=10] [n=12]
//       -> id | title | seconds | downloads | rating | user   (most downloaded first, CC0 only)
//   node tools/roblox/freesound_web.mjs get <outDir> <id> [<id>...]
//       -> <outDir>/<id>.ogg (+ .mp3 fallback), CREDITS.md line; refuses anything whose own page isn't CC0
import fs from 'node:fs';
import path from 'node:path';

const UA = { 'User-Agent': 'Mozilla/5.0 (jankfire sound research)' };
const attr = (s, k) => { const m = new RegExp(`${k}="([^"]*)"`).exec(s); return m ? m[1] : ''; };
const unesc = (s) => s.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');

async function search(q, maxS = 10, n = 12) {
  const f = `license:"Creative Commons 0" duration:[0 TO ${maxS}]`;
  const u = `https://freesound.org/search/?q=${encodeURIComponent(q)}&f=${encodeURIComponent(f)}&s=${encodeURIComponent('Downloads (most first)')}`;
  const t = await (await fetch(u, { headers: UA })).text();
  const blocks = t.split('class="bw-search__result"').slice(1);
  const out = [];
  for (const b of blocks.slice(0, n)) {
    const p = b.slice(b.indexOf('bw-player'));
    const rating = /Average rating of ([\d.]+)/.exec(b);
    out.push({
      id: attr(p, 'data-sound-id'), title: unesc(attr(p, 'data-title')), secs: Number(attr(p, 'data-duration')),
      downloads: Number(attr(p, 'data-num-downloads')), rating: rating ? Number(rating[1]) : 0, user: attr(p, 'data-username'),
    });
  }
  return out;
}

async function get(dir, ids) {
  fs.mkdirSync(dir, { recursive: true });
  const credits = path.join(dir, 'CREDITS.md');
  for (const id of ids) {
    const r = await fetch(`https://freesound.org/s/${id}/`, { headers: UA, redirect: 'follow' });
    const t = await r.text();
    if (!/creativecommons\.org\/publicdomain\/zero/.test(t)) { console.log(`${id}: NOT CC0 on its page, skipped`); continue; }
    const lq = attr(t.slice(t.indexOf('bw-player')), 'data-ogg') || attr(t, 'data-ogg');
    if (!lq) { console.log(`${id}: no preview found`); continue; }
    const hq = lq.replace('-lq.', '-hq.');
    const a = await fetch(hq, { headers: UA });
    if (!a.ok) { console.log(`${id}: preview ${a.status}`); continue; }
    const buf = Buffer.from(await a.arrayBuffer());
    const file = path.join(dir, `${id}.ogg`);
    fs.writeFileSync(file, buf);
    const title = unesc(attr(t, 'data-title')), user = (/\/people\/([^/]+)\/sounds\//.exec(r.url) || [])[1] || attr(t, 'data-username');
    fs.appendFileSync(credits, `- ${id}.ogg: "${title}" by ${user}, ${r.url} (CC0)\n`);
    console.log(`${id}: ${buf.length} bytes  "${title}" by ${user}`);
  }
}

const [cmd, ...rest] = process.argv.slice(2);
if (cmd === 'search') {
  const res = await search(rest[0], Number(rest[1] || 10), Number(rest[2] || 12));
  for (const s of res) console.log(`${s.id} | ${s.title} | ${s.secs.toFixed(2)}s | ${s.downloads} dl | ${s.rating} | ${s.user}`);
} else if (cmd === 'get') {
  await get(rest[0], rest.slice(1));
} else {
  console.log('usage: search "<words>" [maxSeconds] [n] | get <outDir> <id>...');
}
