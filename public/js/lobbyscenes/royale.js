// JANK ROYALE's lobby: the blimp's launch deck (docs/menu/LOBBY_SCENES.md). your party lined up at the railing, the
// pink envelope overhead, a big sky, chunky clouds drifting past below, the island far off down there, confetti. a
// line-up (no walking): everyone idles, READY does a little hop, the camera sways like a blimp.
import * as THREE from 'three';

export function build(L) {
  const S = L.cur().scene, root = new THREE.Group(); S.add(root);
  const potato = L.potato();
  S.background = new THREE.Color(0x9ab8ff);
  S.fog = new THREE.Fog(0xf0c8e8, 120, 520);
  const flat = (o) => { o.castShadow = false; return o; };
  // ---- the sky: a gradient dome, the sea, the island, clouds
  const sky = new THREE.Mesh(new THREE.SphereGeometry(500, 20, 12), L.tex(new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    vertexShader: 'varying vec3 p; void main(){ p = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'varying vec3 p; void main(){ float h = normalize(p).y; vec3 lo = vec3(1.0, 0.74, 0.86), hi = vec3(0.32, 0.6, 1.0); gl_FragColor = vec4(mix(lo, hi, smoothstep(-0.08, 0.5, h)), 1.0); }' })));
  sky.userData.lsSee = true; root.add(sky);
  const sea = new THREE.Mesh(new THREE.CircleGeometry(480, 32), L.mat(0x2a8adf, 0.3, 0.1)); sea.rotation.x = -Math.PI / 2; sea.position.y = -40; root.add(sea);
  const isle = new THREE.Group(); isle.position.set(-50, -40, -260); root.add(isle);
  flat(L.cyl(isle, 62, 70, 4, L.mat(0xf2dc9a, 0.9), 0, 1, 0, 11)); // the beach
  flat(L.cyl(isle, 50, 58, 8, L.mat(0x5fcf4f, 0.9), 0, 6, 0, 11));
  const mt = new THREE.Mesh(new THREE.ConeGeometry(22, 34, 7), L.mat(0x7a6a8a, 0.9)); mt.position.set(-12, 26, -10); isle.add(mt);
  const city = L.mat(0xff9ad5, 0.6); for (let i = 0; i < 9; i++) flat(L.box(isle, 6, 8 + (i * 7) % 14, 6, i % 2 ? city : L.mat(0xffe14d, 0.6), 14 + (i % 3) * 9, 12, 8 + Math.floor(i / 3) * 9));
  const clouds = [];
  const puff = L.mat(0xffffff, 1);
  for (let i = 0; i < (potato ? 10 : 24); i++) {
    const c = new THREE.Group(), a = (i / 24) * Math.PI * 2, r = 40 + (i % 5) * 22;
    c.position.set(Math.sin(a) * r, -10 - (i % 4) * 7, Math.cos(a) * r - 40);
    for (let k = 0; k < 5; k++) { const s = new THREE.Mesh(new THREE.IcosahedronGeometry(3 + ((i * 7 + k * 3) % 5) * 0.7, 0), puff); s.position.set((k - 2) * 3.2, (k % 2) * 1.4, (k % 3) * 1.2); c.add(s); }
    root.add(c); clouds.push(c);
  }
  // ---- the deck: planks, a pink railing at the edge (the drop behind it), the gondola's side walls, the envelope overhead
  const deck = L.mat(0xb07a4a, 0.75); deck.map = L.speck(0xb07a4a, 6, true);
  L.box(root, 12, 0.3, 9, deck, 0, -0.15, 1.5).castShadow = false;
  const rail = L.mat(0xff4fd8, 0.35, 0.2);
  L.box(root, 12, 0.1, 0.1, rail, 0, 1.05, -2.95); for (let x = -5.8; x <= 5.81; x += 1.16) L.box(root, 0.08, 1.05, 0.08, rail, x, 0.52, -2.95);
  L.box(root, 12, 0.08, 0.08, rail, 0, 0.55, -2.95);
  const tape = L.mat(0xffffff, 0.6); tape.map = L.stripes(20); flat(L.box(root, 12, 0.02, 0.3, tape, 0, 0.012, -2.6));
  const gond = L.mat(0xf6f2e6, 0.4, 0.2);
  for (const x of [-6.6, 6.6]) { L.box(root, 1.2, 4, 9, gond, x, 1.7, 1.5); L.box(root, 1.25, 0.25, 9.05, L.mat(0xffe14d, 0.4), x, 3.5, 1.5); }
  for (const x of [-6.0, 6.0]) for (const z of [-0.5, 2.5]) { const w = L.box(root, 0.06, 1.1, 1.4, L.mat(0x4fd8ff, 0.1, 0.6), x, 2.2, z); w.castShadow = false; }
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(3, 0.45), L.basic(0xffffff, { map: L.label('GATE 7 · NO REFUNDS', { w: 512, h: 80 }) })); sign.position.set(-5.98, 2.9, 1.5); sign.rotation.y = Math.PI / 2; root.add(sign);
  const jump = new THREE.Mesh(new THREE.PlaneGeometry(3, 0.45), L.basic(0xffffff, { map: L.label('JUMP WHEN THE LIGHT IS GREEN', { bg: '#120818', fg: '#7dff4f', w: 512, h: 80 }) })); jump.position.set(5.98, 2.9, 1.5); jump.rotation.y = -Math.PI / 2; root.add(jump);
  const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), L.basic(0xff3030)); lamp.position.set(5.95, 3.35, 0.2); root.add(lamp);
  const pole = L.box(root, 0.05, 2.6, 0.05, L.mat(0x222222), 5.4, 2.3, -2.9); pole.castShadow = false;
  const flag = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.6, 6, 1), L.mat(0xffe14d, 0.6)); flag.material.side = THREE.DoubleSide; flag.position.set(5.92, 3.3, -2.9); root.add(flag);
  const fpos = flag.geometry.attributes.position, fx0 = Float32Array.from(fpos.array);
  const env = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 14), L.mat(0xff4fd8, 0.3, 0.1)); env.scale.set(9, 6, 22); env.position.set(0, 9.6, 4); root.add(env);
  const band = new THREE.Mesh(new THREE.CylinderGeometry(1.004, 1.004, 0.1, 24, 1, true), L.mat(0xffe14d, 0.4)); band.rotation.z = Math.PI / 2; band.scale.set(6.05, 9.05, 22.05); band.position.copy(env.position); root.add(band);
  for (const x of [-5, 5]) { const c = L.cyl(root, 0.04, 0.04, 6.2, L.mat(0x333333), x, 5.4, -0.5, 4); c.rotation.z = x * 0.03; c.castShadow = false; } // the cables up to the envelope
  // ---- lights: bright noon, a pink bounce off the envelope
  S.add(new THREE.HemisphereLight(0xffffff, 0xffc0e0, 1.5));
  const sun = new THREE.DirectionalLight(0xfff4dd, 2.3); sun.position.set(6, 12, 9); sun.target.position.set(0, 0, -1); S.add(sun, sun.target);
  if (L.shadows()) { sun.castShadow = true; sun.shadow.mapSize.set(potato ? 512 : 2048, potato ? 512 : 2048); Object.assign(sun.shadow.camera, { left: -8, right: 8, top: 8, bottom: -5, near: 1, far: 40 }); sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.03; }
  // ---- confetti: one instanced mesh, drifting down through the frame and round again
  const N = potato ? 0 : 220, cols = [0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f], P = [];
  const conf = N ? new THREE.InstancedMesh(new THREE.PlaneGeometry(0.07, 0.12), L.basic(0xffffff, { side: THREE.DoubleSide }), N) : null;
  if (conf) { for (let i = 0; i < N; i++) { P.push([(Math.random() - 0.5) * 12, Math.random() * 6, (Math.random() - 0.5) * 7 + 0.5, Math.random() * 6]); conf.setColorAt(i, new THREE.Color(cols[i % 4])); } conf.userData.lsSee = true; conf.frustumCulled = false; root.add(conf); }
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), v = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  // where your party stands: in a row at the railing, you in the middle (up to 6; fill 4: a squad)
  const spots = [{ x: 0, z: -1.5, ry: 0 }, { x: -1.05, z: -1.85, ry: 0.12 }, { x: 1.05, z: -1.85, ry: -0.12 }, { x: -2.1, z: -2.2, ry: 0.22 }, { x: 2.1, z: -2.2, ry: -0.22 }, { x: 0, z: -2.5, ry: 0 }];
  return {
    spots, fill: 4, inviteH: 1.3,
    focus: { at: new THREE.Vector3(0, 1.2, -1.6), top: new THREE.Vector3(0, 2.5, -1.8), bot: new THREE.Vector3(0, 0, -1.2), w: 4.4, min: 5, dir: new THREE.Vector3(0, 0.12, 1).normalize(), fov: 40, drift: 0.04, bob: 0.01 }, // (the outer two may stand half behind a panel: the middle three fill the stage)
    inviteSpot(wrap) { wrap.userData.lsPick = 'invite'; const m = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 1.8, 10, 1, true), L.basic(0x4fd8ff, { transparent: true, opacity: 0.15, depthWrite: false, side: THREE.DoubleSide })); m.position.y = 0.9; wrap.add(m); },
    update(dt, t) {
      for (const c of clouds) { c.position.x += dt * 2.2; if (c.position.x > 140) c.position.x = -140; }
      lamp.material.color.setHex(Math.sin(t * 0.7) > 0.6 ? 0x39ff14 : 0xff3030); // (green, now and then. nobody jumps)
      for (let i = 0; i < fpos.count; i++) { const x = fx0[i * 3]; fpos.setZ(i, Math.sin(t * 6 + x * 5) * 0.08 * (x + 0.5)); } fpos.needsUpdate = true;
      if (conf) {
        for (let i = 0; i < N; i++) { const p = P[i], y = ((p[1] - t * 0.55) % 6 + 6) % 6; e.set(t * 3 + p[3], t * 2 + i, 0); q.setFromEuler(e); v.set(p[0] + Math.sin(t + p[3]) * 0.3, y, p[2]); m4.compose(v, q, one); conf.setMatrixAt(i, m4); }
        conf.instanceMatrix.needsUpdate = true;
      }
    },
    info: () => ({ clouds: clouds.length, confetti: N }),
  };
}
