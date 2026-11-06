// the story's test lot: a walled scrap yard behind the Lost & Found with the Machine standing in it. a stand-in until
// the world lane's districts stream in (WP1/WP2). TEST is plain data (the sim worker reads it without building
// any map); buildTestMap(kit) takes shared/map.js's building kit so the worker never has to import every map.
export const TEST = {
  id: 'story_test', name: 'The Lost & Found (test lot)', killY: -30,
  spawn: [0, 0.1, 6], yaw: 0,
  terminal: { p: [0, 0, -14], r: 2.6 }, // the Machine: F within r metres opens the sims (the normal PLAY menu)
};

export function buildTestMap(kit) {
  const { builder, horizon, rng, lollipop, conifer } = kit;
  const B = builder(), D = builder();
  const H = 40; // half size of the lot
  B.add(-H, -2, -H, H, 0, H, 'concrete');
  for (const [x0, z0, x1, z1] of [[-H, -H - 1, H, -H], [-H, H, H, H + 1], [-H - 1, -H, -H, H], [H, -H, H + 1, H]]) B.add(x0, 0, z0, x1, 5, z1, 'brick');
  // junk to climb, slide past and grapple: crates, a ramp, a scrap tower with a ledge
  const r = rng(4417);
  for (let i = 0; i < 14; i++) {
    const x = (r() - 0.5) * 60, z = (r() - 0.5) * 60, s = 1.2 + r() * 1.6;
    if (Math.hypot(x, z - 6) < 8 || Math.hypot(x, z + 14) < 6) continue; // keep the spawn and the Machine clear
    B.box(x, s / 2, z, s, s, s, 'crate');
  }
  for (let i = 0; i < 8; i++) B.add(18 + i * 1.5, 0, -20, 19.5 + i * 1.5, 0.5 + i * 0.5, -12, 'wood'); // stepped ramp
  B.add(26, 0, -20, 32, 8, -12, 'metal');
  B.add(26, 8, -20, 32, 8.4, -12, 'hazard');
  B.add(-32, 0, 18, -24, 12, 26, 'concrete'); // a stub of tower for the grapple
  B.add(-32.5, 12, 17.5, -23.5, 12.4, 26.5, 'yellow');
  // the Machine: a tall pink vending machine, blue glass, a dispensing tray, a yellow ☺ sign on a pole
  const [mx, , mz] = TEST.terminal.p;
  B.add(mx - 0.9, 0, mz - 0.6, mx + 0.9, 2.7, mz + 0.5, 'pink');
  D.add(mx - 0.7, 0.9, mz + 0.5, mx + 0.7, 2.4, mz + 0.56, 'blue');
  D.add(mx - 0.6, 0.25, mz + 0.5, mx + 0.6, 0.6, mz + 0.75, 'metal');
  D.add(mx - 0.05, 2.7, mz - 0.1, mx + 0.05, 4.2, mz, 'metal');
  D.add(mx - 1.2, 4.2, mz - 0.12, mx + 1.2, 5.2, mz + 0.02, 'yellow');
  horizon(D, -H - 1, -H - 1, H + 1, H + 1, 900, 'dirt');
  for (let i = 0; i < 26; i++) { const rr = rng(900 + i), a = rr() * Math.PI * 2, d = 70 + rr() * 120; (rr() < 0.5 ? conifer : lollipop)(D.local(0, 0, 0), Math.cos(a) * d, Math.sin(a) * d, 5 + rr() * 4, rr); }
  return {
    name: TEST.name, size: 'story', boxes: B.boxes, deco: D.boxes, killY: TEST.killY, floorY: -2, bounds: [-H, -H, H, H],
    sky: { top: 0x5a3a6a, mid: 0xffb27a, bot: 0x2a1a20, fog: 0xd99a7a }, fogNear: 60, fogFar: 260, // a dusty pink-orange end-of-the-world dusk
    spawns: [TEST.spawn.slice()], story: true,
  };
}
