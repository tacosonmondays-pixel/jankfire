// Body killstreaks that last until they BREAK (the Wrecking Ball and the Overdrive Rig): no timer, an HP pool of their
// own on top of the player's. Everything that hits you while you're in one comes off the pool (no headshot bonus: the
// ball has no head and the rig's is armoured; one hit can't take more than `cap`, so a frag, the bomb or a spoon can't
// pop it in one go). At 0 it breaks: a knock, you're yourself again at the HP you had. The pool also drains on its own
// (`decay` per second) so it's over in a minute even if nobody shoots it. The server owns the pool; clients only show it.
//
// Why these numbers (guns in shared/weapons.js): most guns do 100-150 damage a second (AR 110, SMG 112, LMG 120,
// minigun 150; the sawn-off 360 point blank, the burst rifle 210). A big target gets hit ~80 % of the time, so two people
// on it do ~200/s and three ~300/s:
//   ball 900  -> ~4.5 s against two, ~3 s against three
//   rig 1200  -> ~6 s against two, ~4 s against three, more while it blocks (80 % off hits from the front)
export const BODY = {
  wreckingball: { hp: 900, decay: 15, name: 'Wrecking Ball' }, // 900 / 15 = 60 s if nobody touches it
  overdrive: { hp: 1200, decay: 20, name: 'Overdrive Rig' }, // 1200 / 20 = 60 s
  cap: 120, // the most a single hit takes off a pool
  life: 65, // s: the clients' own safety timer (the decay ends it first)
  knock: 9, // m/s up when it breaks: popped out
  // what still hurts YOU (not the pool): the floor is lava, the royale zone, your own cough. (void / falling out of the
  // map kill you straight away, as before)
  bypass: ['lava', 'zone', 'cough', 'void', 'oob'],
};
export const bodyKinds = Object.keys(BODY).filter((k) => BODY[k] && BODY[k].hp);
