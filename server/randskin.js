// Random cosmetics + favourites, server half. A slot of your saved look can be 'random' (the wrap, hat, effect, skin of a
// weapon, or your kill effect): every time you spawn the server swaps it for something you own, picked from your
// favourites when you ticked "only use favourites". The look you asked for (p.skinWant, p.kfxWant) stays as sent; what
// you wear this life (p.skins, p.kfx) is the rolled one, checked against your inventory like any other pick.
import { COSMETICS, owns, achInv, ownedKill } from '../shared/cosmetics.js';

export const RAND = 'random'; // never a catalog id (checked below), passes the skin key regex
for (const t of Object.keys(COSMETICS)) if (Object.hasOwn(COSMETICS[t], RAND)) throw new Error(`cosmetic id "${RAND}" is reserved`);
const FAV_TYPES = ['finish', 'hat', 'effect', 'model', 'kill'];
const SLOT_T = ['finish', 'hat', 'effect', 'model'];
const pickOne = (a) => a[Math.floor(Math.random() * a.length)];

// favourites off the wire: { finish: [ids], ..., only: [types] }. only real catalog ids, capped
export function cleanFavs(f) {
  const out = { only: [] };
  if (!f || typeof f !== 'object' || Array.isArray(f)) return out;
  for (const t of FAV_TYPES) {
    const v = f[t];
    if (!Array.isArray(v)) continue;
    const ids = [...new Set(v.slice(0, 300).filter((id) => typeof id === 'string' && id.length <= 24 && Object.hasOwn(COSMETICS[t], id)))];
    if (ids.length) out[t] = ids;
  }
  if (Array.isArray(f.only)) out.only = FAV_TYPES.filter((t) => f.only.includes(t));
  return out;
}

// everything of a type you could roll: owned, the right weapon for skins, from favourites if that's ticked
// (favourites-only with no owned favourites falls back to all owned, so Random never comes up empty)
function pool(type, own, favs, weapon) {
  let ids = Object.keys(COSMETICS[type]).filter((id) => owns(own, type, id) && (type !== 'model' || id === 'default' || COSMETICS.model[id].weapon === weapon));
  if (favs && favs.only && favs.only.includes(type) && Array.isArray(favs[type])) {
    const f = ids.filter((id) => favs[type].includes(id));
    if (f.length) ids = f;
  }
  return ids;
}

export function rollSkins(want, inv, achs, favs, enforce) {
  const own = achInv(inv, achs), out = {};
  for (const [id, sk] of Object.entries(want || {})) {
    const s = sk.slice();
    for (let i = 0; i < 4; i++) if (s[i] === RAND) { const ids = pool(SLOT_T[i], own, favs, id); s[i] = ids.length ? pickOne(ids) : (i === 0 || i === 3 ? 'default' : 'none'); }
    out[id] = s;
  }
  return enforce(out, inv, achs); // the usual ownership check on what came out
}
export const hasRandom = (want) => Object.values(want || {}).some((sk) => sk.includes(RAND));

export function rollKfx(want, inv, favs) {
  if (want !== RAND) return ownedKill(want, inv);
  const ids = pool('kill', inv, favs);
  return ids.length ? pickOne(ids) : 'none';
}

// mixed into Room: every spawn rolls the random slots again and tells everyone (you included: your own gun shows it)
export function installRandSkin(Room, H) {
  const P = Room.prototype, orig = { resetLife: P.resetLife };
  P.rollLook = function (p, tell) {
    if (!p || p.isBot) return;
    if (p.skinWant && hasRandom(p.skinWant)) {
      p.skins = rollSkins(p.skinWant, p.inv, p.acct && p.acct.achs, p.favs, H.enforceSkins);
      if (tell) this.broadcast({ t: 'sk', id: p.id, s: p.skins });
    }
    if (p.kfxWant === RAND) p.kfx = rollKfx(RAND, p.inv, p.favs);
  };
  P.resetLife = function (p) { orig.resetLife.call(this, p); this.rollLook(p, true); };
}
