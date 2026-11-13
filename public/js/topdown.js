// the royale maps' top-down pictures (baked by tools/topdown.cjs into public/maps/topdown/<map>.jpg + .json): a real
// render of the map from straight above with the POI names on it. topdownFor(id) starts loading on the first ask and
// returns { img, ext, names } once the picture is in (null until then, or for a map that has none)
const TD = new Map(); // id -> { state: 'loading' | 'ok' | 'none', img, ext, names }
export const TOPDOWN_MAPS = ['jankburg', 'battleisland'];
export function topdownFor(id) {
  if (!TOPDOWN_MAPS.includes(id)) return null;
  let t = TD.get(id);
  if (!t) {
    t = { state: 'loading', img: null, ext: null, names: false };
    TD.set(id, t);
    fetch(`/maps/topdown/${id}.json`).then((r) => (r.ok ? r.json() : null)).then((j) => {
      if (!j || !Array.isArray(j.ext) || j.ext.length !== 4 || !j.ext.every(Number.isFinite)) { t.state = 'none'; return; }
      const img = new Image();
      img.onload = () => { t.img = img; t.ext = j.ext; t.names = !!j.names; t.state = 'ok'; };
      img.onerror = () => { t.state = 'none'; };
      img.src = `/maps/topdown/${id}.jpg`;
    }).catch(() => { t.state = 'none'; });
  }
  return t.state === 'ok' ? t : null;
}
