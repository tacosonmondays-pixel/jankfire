// Killstreak looks (shared/cosmetics.js STREAK_SKINS / STREAK_LOOKS): what a streak looks like for whoever used it.
// A look is a skin slot keyed by the streak's id, [wrap, 'none', 'none', model, wrap mode], checked by the server like
// a weapon skin and sent to everyone in the player info, so other players and killcams see it too.
// Where they show: the wrecking ball's shell (wreck.js), the giant duck's black hole (the duck that circles it), Chicken
// Strike's falling birds, the Overdrive Rig's plates (a wrap), and every streak's icon (itemicons.js). Models are lazy
// x_<skin>.glb files (tools/blender/make_streakskins.py); until one lands the default stands in.
import * as THREE from 'three';
import { G } from './ctx.js';
import { COSMETICS, isStreakLook, STREAK_LOOKS } from '/shared/cosmetics.js';
import { authored, nodeIn, whenGlb } from './glbkit.js';
import { applySkin } from './skins.js';

// someone's look for a streak (me: what I wear, rolled randoms and all), or null. owner = a player id, 'me', or a skins
// table itself (a remote's r.skins: killcam replays have their own copies of the players)
export function lookOf(owner, id) {
  const r = typeof owner === 'number' && G.remotes && G.remotes.get(owner);
  const t = owner && typeof owner === 'object' ? owner : owner === G.myId || owner === 'me' ? G.equipped : (r && r.skins) || (G.skins && G.skins.get(owner));
  const sk = t && t[id];
  return Array.isArray(sk) && isStreakLook(id) ? sk : null;
}
// the model in a look, if it belongs to that streak ('default' otherwise)
export function modelOf(sk, id) {
  const m = sk && sk[3];
  return typeof m === 'string' && Object.hasOwn(COSMETICS.model, m) && COSMETICS.model[m].weapon === id ? m : 'default';
}
// its wrap, all over (streak models have no wrap zones): the glowing bits keep their glow
export function paintLook(g, sk) {
  if (sk && typeof sk[0] === 'string' && sk[0] !== 'default') applySkin(g, [sk[0], 'none', 'none', 'default', 'full']);
  return g;
}
// the Golden Duck: the rubber duck in solid gold (no file of its own)
const GOLD = new THREE.MeshPhysicalMaterial({ color: 0xffc83a, metalness: 0.55, roughness: 0.28, clearcoat: 0.8, emissive: 0x6a4400 }); // (half metal: reads as gold even where there's no reflection to show)
function goldDuck() {
  const b = authored('pj_duck');
  if (!b) return null;
  b.obj.traverse((o) => { if (o.isMesh && !(o.material && o.material.name === 'pd_black')) o.material = GOLD; });
  b.obj.scale.setScalar(2.2);
  return b.obj;
}
// a look's own model, or null (not one / not here yet: the caller keeps the default)
export function lookModel(model) {
  if (!model || model === 'default') return null;
  if (model === 'duck_gold') return goldDuck();
  const b = authored('x_' + model);
  return b ? b.obj : null;
}
// the files a set of streak looks needs: yours (your loadout's streaks) or another player's whole skins table, so their
// disco ball / drones are already here when they use it (the wrecking ball's look needs the Blender ball under it too)
export function lookFiles(streaks, owner = 'me') {
  const out = [];
  for (const id of streaks || []) {
    const m = modelOf(lookOf(owner, id), id);
    if (m === 'duck_gold') out.push('pj_duck'); else if (m !== 'default') out.push('x_' + m);
    if (m !== 'default' && id === 'wreckingball') out.push('x_wreck');
  }
  return out;
}
export const lookFilesOf = (skins) => lookFiles(STREAK_LOOKS, skins && typeof skins === 'object' ? skins : null);

// ------------------------------------------------------------ in the world
// the giant duck's hole (models.js buildHole): its circling duck becomes your look's model, in your wrap
export function dressHole(mesh, owner) {
  const sk = lookOf(owner, 'giantduck');
  if (!sk || !mesh.userData.orbit || mesh.userData.dressed) return;
  const md = modelOf(sk, 'giantduck'), alt = lookModel(md);
  if (md !== 'default' && !alt) { whenGlb([md === 'duck_gold' ? 'pj_duck' : 'x_' + md], () => { if (mesh.parent) dressHole(mesh, owner); }); return; } // its model is still coming: dress it when it lands
  mesh.userData.dressed = true;
  const orbit = mesh.userData.orbit, duck = orbit.children[0];
  if (alt) {
    const g = new THREE.Group(); g.add(alt);
    g.position.copy(duck.position); g.rotation.copy(duck.rotation);
    const bx = new THREE.Box3().setFromObject(duck), want = bx.getSize(new THREE.Vector3()), have = new THREE.Box3().setFromObject(alt).getSize(new THREE.Vector3());
    alt.scale.multiplyScalar(Math.max(want.x, want.y, want.z, 0.5) / Math.max(have.x, have.y, have.z, 0.01)); // the same size as the duck it stands in for
    orbit.remove(duck); orbit.add(g);
    paintLook(g, sk);
  } else paintLook(duck, sk);
}
// a Chicken Strike bird for that player's look, or null (the normal chicken)
export function strikeBird(owner) {
  const sk = lookOf(owner, 'chickenstrike');
  if (!sk) return null;
  const alt = lookModel(modelOf(sk, 'chickenstrike'));
  if (!alt) return null;
  const g = new THREE.Group(); g.add(alt);
  return paintLook(g, sk);
}
// the wrecking ball's shell: the Blender ball keeps its chain stub, viewing slot and face; its steel shell goes
const SHELL = new Set(['ball_steel', 'ball_accent', 'ball_rivet', 'ball_strap', 'ball_sign']);
export function wreckShell(ball, sk) {
  const alt = lookModel(modelOf(sk, 'wreckingball'));
  if (alt) {
    for (const n of SHELL) { const o = nodeIn(ball, n); if (o) o.removeFromParent(); }
    ball.add(alt);
    paintLook(alt, sk);
  } else if (sk) { const s = nodeIn(ball, 'ball_steel'); if (s) paintLook(s, sk); }
}
