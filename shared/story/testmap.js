// the story's test lot: a walled scrap yard behind the Lost & Found with the Machine standing in it. a stand-in until
// the world lane's districts stream in (WP1/WP2). TEST is plain data (the sim worker reads it without building
// any map); buildTestMap(kit) takes shared/map.js's building kit so the worker never has to import every map.
export const TEST = {
  id: 'story_test', name: 'The Lost & Found (test lot)', killY: -30,
  spawn: [0, 0.1, 6], yaw: 0,
  terminal: { p: [0, 0, -14], r: 2.6 }, // the Machine: F within r metres opens the sims (the normal PLAY menu)
  locker: { p: [6, 0, -14], r: 2.6 }, // the safehouse Locker (WP3): stash / unstash only within r metres
  clinic: { p: [-7, 0, -14], r: 2.8 }, // a Meat Mechanic's clinic chair (WP5): buy, install, uninstall implants
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
  const [lx, , lz] = TEST.locker.p; // the Locker: a dented green filing locker with a padlock
  B.add(lx - 0.8, 0, lz - 0.5, lx + 0.8, 2.2, lz + 0.4, 'mint');
  D.add(lx - 0.02, 0.2, lz + 0.4, lx + 0.02, 2.0, lz + 0.45, 'metal');
  D.add(lx + 0.15, 1.0, lz + 0.4, lx + 0.35, 1.25, lz + 0.5, 'yellow');
  const [cx, , cz] = TEST.clinic.p; // the clinic: a pink dentist chair under a striped awning, a jar of something on a stool
  B.add(cx - 0.6, 0, cz - 0.6, cx + 0.6, 0.7, cz + 0.6, 'metal');
  D.add(cx - 0.55, 0.7, cz - 0.55, cx + 0.55, 0.95, cz + 0.55, 'pink'); D.add(cx - 0.55, 0.95, cz - 0.6, cx + 0.55, 1.9, cz - 0.4, 'pink');
  for (let i = 0; i < 5; i++) D.add(cx - 1.6 + i * 0.64, 2.6, cz - 1.4, cx - 0.96 + i * 0.64, 2.75, cz + 1.2, i % 2 ? 'white' : 'pink');
  for (const sx of [-1.6, 1.6]) D.add(cx + sx - 0.05, 0, cz + 1.1, cx + sx + 0.05, 2.6, cz + 1.2, 'metal');
  D.add(cx + 1.0, 0, cz + 0.4, cx + 1.3, 0.6, cz + 0.7, 'wood'); D.add(cx + 1.02, 0.6, cz + 0.42, cx + 1.28, 0.95, cz + 0.68, 'mint');
  horizon(D, -H - 1, -H - 1, H + 1, H + 1, 900, 'dirt');
  for (let i = 0; i < 26; i++) { const rr = rng(900 + i), a = rr() * Math.PI * 2, d = 70 + rr() * 120; (rr() < 0.5 ? conifer : lollipop)(D.local(0, 0, 0), Math.cos(a) * d, Math.sin(a) * d, 5 + rr() * 4, rr); }
  return {
    name: TEST.name, size: 'story', boxes: B.boxes, deco: D.boxes, killY: TEST.killY, floorY: -2, bounds: [-H, -H, H, H],
    sky: { top: 0x5a3a6a, mid: 0xffb27a, bot: 0x2a1a20, fog: 0xd99a7a }, fogNear: 60, fogFar: 260, // a dusty pink-orange end-of-the-world dusk
    spawns: [TEST.spawn.slice()], story: true,
  };
}
