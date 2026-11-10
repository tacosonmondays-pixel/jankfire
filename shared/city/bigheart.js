// THE BIG HEART (gut:big_heart): the Gut's landmark, a giant heart grown out of ~1,700 human ones on a spiral tower of
// bone (public/models/story/s_gut_heart.glb, docs/story/gut/GUT_HEART_MODEL.md). The world side of it: where it
// stands, its collision (the tower, the heart, the buttresses and every stair tread, so you can climb the rib stair
// and stand under the apex), its mark and the red light at its foot. The client draws it with its own loader
// (public/js/city/bigheart.js): the model never goes through the prop path, which would strip the ripple.
// Pure data + boxes: runs in the chunk workers and on the server, so both agree on every tread.
import { SLICE } from './slice.js';
import HB from './bigheart_boxes.js';

// model space = world space moved to (x, y, z): the heart's front faces +z (south, the border), its apex points east
export const BIG_HEART = { id: 'gut:big_heart', x: SLICE.heart.x, y: SLICE.gut.y, z: SLICE.heart.z, reach: 12, tall: 49.4, ...HB };
// a model-space point in the world
export const heartAt = (p) => [BIG_HEART.x + p[0], BIG_HEART.y + p[1], BIG_HEART.z + p[2]];
const KIND = [['mound', 'bone'], ['tower', 'bone'], ['buttresses', 'bone'], ['steps', 'bone'], ['heart', 'flesh']];

export function bigHeart(B) {
  const H = BIG_HEART;
  if (!B.touches([H.x - H.reach, H.z - H.reach, H.x + H.reach, H.z + H.reach], 24)) return;
  // a glowing bile puddle can land under the mound: its green light would shine out of the bone, so it goes
  B.out.lights = B.out.lights.filter((l) => Math.hypot(l[0] - H.x, l[2] - H.z) > 7);
  // collision only (hide): the model is the picture. the builder clips each box to the chunk
  for (const [k, mat] of KIND) for (const b of H.boxes[k]) B.add(H.x + b[0], H.y + b[1], H.z + b[2], H.x + b[3], H.y + b[4], H.z + b[5], mat, { hide: true });
  // what it lights: a deep red pool round the roots, a dimmer one under the heart for the top of the stair
  B.light(H.x, H.y + 3, H.z + 5, 0xff2038, 20, 1.1);
  B.light(H.x + 3, H.y + 24, H.z + 1, 0xff3050, 12, 0.8);
  if (B.inside(H.x, H.z)) {
    const l = heartAt(H.markers.listening_spot), t = heartAt(H.markers.stair_top);
    B.out.marks.push({ id: H.id, p: l, face: 0 }, { id: 'gut.big_heart_top', p: t }); // where you stand to look at it; the top of the rib stair
  }
}
