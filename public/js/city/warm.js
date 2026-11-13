// Load time (owner: "the loading takes forever"): the city's startup, started early. While you're still on the menus
// (story mode on), the chunk workers start up (each one imports the whole city generator, which takes seconds) and
// build the chunks round where you'll appear into their own caches, and the city's code is fetched. NEW GAME then
// finds its first pass ready instead of waiting on all of that. The chunks are the same ones it would build (same
// seeds), so nothing about the city or its collision changes, only when the work happens.
//   warmCity(spots)   spots: [[x, z], ...] world points you might start at (the new game's spawn, your saves)
//   takeWarm(n, url)  stream.js: the warm workers, if there are n of that kind (else null: it makes its own)
// (no imports: the workers start the moment this runs, and they work out the chunks round each spot themselves)

let pool = null, poolUrl = '';
export function warmCity(city, spots, n = 2, url = '/js/city/chunkworker.js') {
  if (!pool && typeof Worker !== 'undefined') {
    pool = Array.from({ length: n }, () => new Worker(url, { type: 'module' })); poolUrl = url;
    for (const w of pool) w.postMessage({ op: 'warm', city, spots }); // (both: the streamer asks them in turn, each has its own cache)
  }
  import('./ingame.js').catch(() => { /* fetched again when the map needs it */ }); // (the city's code: its module graph is nine levels deep)
}
export function takeWarm(n, url) {
  if (!pool || pool.length !== n || poolUrl !== url) return null;
  const p = pool; pool = null; return p;
}
