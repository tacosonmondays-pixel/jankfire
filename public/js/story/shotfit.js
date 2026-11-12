// face shots that fit the actor (shots.js closeup / extreme): which way the face really looks, and how far the body
// reaches out in front of it. pure three.js (no story modules), so tests can run it in node
import * as THREE from 'three';

// which way a face really looks: the head bone's own forward (-z), flat. a clip can turn the body away from the actor's
// yaw (Pallet Jack going down against the fridge in his last moment): a face shot set up from the yaw lands in his back
export function faceFwd(a, out) {
  const h = a.ch && a.ch.head; if (!h || !h.getWorldDirection) return false;
  h.getWorldDirection(out).negate(); out.y = 0;
  if (out.lengthSq() < 0.04) return false; // (looking straight down or up: the yaw knows better)
  out.normalize(); return true;
}
// how far the body reaches out in front of the face (a big belly, arms out front, a crouch): a face shot stands clear of
// it instead of inside it. the box's 8 corners against the facing, from the head
const bb = new THREE.Box3(), mb = new THREE.Box3(), cn = new THREE.Vector3();
export function reachOf(a, head, f) {
  if (!a.ch || !a.ch.root) return 0;
  bb.makeEmpty(); a.ch.root.updateWorldMatrix(true, true);
  a.ch.root.traverseVisible((o) => { if (!o.isMesh || !o.geometry) return; if (!o.geometry.boundingBox) o.geometry.computeBoundingBox(); bb.union(mb.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld)); }); // (what you can see: not his hidden damage pieces)
  if (bb.isEmpty()) return 0;
  let r = 0;
  for (let i = 0; i < 8; i++) { cn.set(i & 1 ? bb.max.x : bb.min.x, 0, i & 4 ? bb.max.z : bb.min.z); r = Math.max(r, (cn.x - head.x) * f.x + (cn.z - head.z) * f.z); }
  return Math.min(r, 2.5);
}
