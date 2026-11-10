// PALLET JACK's parts file, the game half: measures the dressed Blender model in the game at its real size (root scale
// 1.18, metres, root space: feet at 0, front = -z) and adds to public/models/cast/c_pallet_jack.parts.json (which the
// Blender script wrote: parts, moving, markers, states):
//   marks  { clip: { mark: seconds } }                 (repeats get numbered)
//   clips  { clip: { len, loop, next, t: [...], hips: [[x, y, z]...], fist: [...], palmL: [...], head: [...] } }  every 0.2 s + at each mark
//   props  where the things he touches go: the hand truck for pj_idle, the rail for pj_idle_eating, the load, the fridge,
//          the carrier's arms; measured from the poses
//   game   { markers: { name: [x, y, z] } } the look's markers as the game has them (should match `markers`)
// usage: node tools/blender/cast/pjparts.cjs [port]   (rerun after changing the model, the look or a clip)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PORT = process.argv[2] || 3000;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto(`http://localhost:${PORT}/`);
  const out = await pg.evaluate(async () => {
    const THREE = await import('three');
    const looks = await import('/js/story/looks.js');
    const { CLIPS } = await import('/js/story/actors.js');
    const { PJ } = await import('/js/story/palletjack.js');
    const got = await looks.loadCast(['pallet_jack'], 30000);
    PJ.fx = false; PJ.auto = false;
    const r3 = (v) => v.toArray().map((x) => +x.toFixed(3));
    let n = 0;
    const jack = (clip, t) => {
      const L = looks.buildLook('pallet_jack'), c = L.ch; c.head.rotation.z = 0;
      const a = { id: 'pjp' + n++, L, ch: c, pos: [0, 0, 0], yaw: 0, clip: null, face: L.face };
      const rig = PJ.rig(a); rig.manual = true;
      c.arm.rotation.set(0.05, 0, 0.1); c.armL.rotation.set(0.05, 0, -0.1); c.foreR.rotation.set(0.22, 0, 0); c.foreL.rotation.set(0.22, 0, 0);
      if (clip) { CLIPS[clip].f(c, t, 1); a.clip = { name: clip, t, len: 9e9 }; }
      rig.update(0, null); c.root.updateMatrixWorld(true);
      return { L, c, rig };
    };
    const J0 = jack(null, 0);
    const game = { blender: !!J0.L.blender, got, markers: {} };
    for (const [k, g] of Object.entries(J0.L.parts || {})) if (g && !g.userData.blender && !g.userData.codeOnly && k !== 'headJoint') game.markers[k] = r3(g.getWorldPosition(new THREE.Vector3()));
    const D = PJ.data.clips, marks = {}, clips = {};
    for (const [clip, C] of Object.entries(D)) {
      const cnt = {}, m = {}, seen = {};
      for (const [, k] of C.marks) cnt[k] = (cnt[k] || 0) + 1;
      for (const [t, k] of C.marks) { seen[k] = (seen[k] || 0) + 1; m[cnt[k] > 1 ? k + seen[k] : k] = t; }
      marks[clip] = m;
      const len = C.len || C.loop || C.keys[C.keys.length - 1].t || 0;
      const ts = [...new Set([...Array.from({ length: Math.round(len / 0.2) + 1 }, (_, i) => +(i * 0.2).toFixed(2)), ...Object.values(m)])].sort((x, y) => x - y);
      const row = { len: C.len, loop: C.loop, held: C.len == null && C.loop == null, t: [], hips: [], fist: [], palmL: [], head: [] };
      for (const t of ts) { const J = jack(clip, t); row.t.push(t); row.hips.push(r3(J.c.spine.getWorldPosition(new THREE.Vector3()))); row.fist.push(r3(J.rig.at('fistAt'))); row.palmL.push(r3(J.rig.at('palmL'))); row.head.push(r3(J.rig.at('eyeAt'))); }
      clips[clip] = row;
    }
    // where the things he touches go
    const props = {};
    { const J = jack('pj_idle', 0), p = J.rig.at('palmL'); props.handtruck = { clip: 'pj_idle', at: [+p.x.toFixed(3), 0, +(p.z - 0.05).toFixed(3)], yaw: 0, note: 's_handtruck.glb stands here (root space, metres): its grip is under his left palm. palm height ' + p.y.toFixed(3) + ' (the grip is at 1.17)' }; }
    { const J = jack('pj_idle_eating', 0), s = J.rig.at('seatAt'); props.seat = { clip: 'pj_idle_eating', at: r3(s), note: 'the top of the rail he sits on is here in his root space: put his root at rail - this' }; }
    { const J = jack('pj_walk_load', 1), a = J.rig.at('palmL'), b2 = J.rig.at('fistAt'); const c = a.clone().add(b2).multiplyScalar(0.5); props.load = { clip: 'pj_walk_load', at: [0, +(c.y + 0.22).toFixed(3), +(c.z - 0.1).toFixed(3)], note: 'the middle of a crate about 0.6 m across carried on his forearms' }; }
    { const J = jack('pj_dying_talk', 5), bx = new THREE.Box3(); for (const k of ['boiler', 'dmgBoilerSplit']) for (const g of (J.L.partsAll || {})[k] || []) bx.expandByObject(g); const h = J.c.spine.getWorldPosition(new THREE.Vector3());
      props.fridge = { clip: 'pj_armour_break_fall', backZ: +bx.max.z.toFixed(3), sitAt: r3(h), note: 'the fridge door is at z = backZ in the root space of where he STOOD when the clip began (he ends sat 0.59 m behind that)' }; }
    { const J = jack('pj_carried', 0); props.carry = { clip: 'pj_carried', back: r3(J.c.spine.getWorldPosition(new THREE.Vector3())), knees: r3(J.c.kneeL.getWorldPosition(new THREE.Vector3()).add(J.c.kneeR.getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5)), head: r3(J.rig.at('eyeAt')),
      note: 'root space of the pose: the carrier\'s arms go under `back` and `knees`. parent his root to the carrier and offset it so these land on their forearms' }; }
    { const J = jack('pj_dying_talk', 5); props.hand = { clip: 'pj_dying_talk', chest: r3(J.rig.at('chest')), palmL: r3(J.rig.at('palmL')), take: r3(jack('pj_dying_talk', 2.8).rig.at('palmL')), note: 'your hand: he reaches to `take`, then holds it at `chest` (his palm over it at palmL)' }; }
    return { game, marks, clips, props };
  });
  const file = path.join(__dirname, '../../../public/models/cast/c_pallet_jack.parts.json');
  const j = JSON.parse(fs.readFileSync(file, 'utf8'));
  Object.assign(j, out);
  fs.writeFileSync(file, JSON.stringify(j, null, 1));
  console.log(Object.keys(out.marks).length, 'clips | blender', out.game.blender, '| props', Object.keys(out.props).join(' '), '|', errs.join('\n') || 'no errors');
  await b.close();
})();
