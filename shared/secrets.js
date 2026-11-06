// Hidden NPCs and cats. Walk up to one and press F: NPCs talk (their lines tell the lore), cats get petted.
// Kept out of shared/map.js on purpose (the maps get remade): every spot is a plain [x, y, z] on a map id, so moving
// one is a one-line change. y = the surface they sit on (the client drops them onto the box under them if it moved a
// bit). face = which way they look (radians, same as a player's yaw: 0 looks down -z).
// The server checks you're really next to one before anything counts (SECRET.reach), once per account, logged-in only.
// What you've found lives in the account's inv jsonb (inv.lore = [ids]): no new column, no supabase.sql re-run.

export const SECRET = { reach: 2.8, up: 2.4, down: 2.6, cd: 600 }; // metres sideways, metres above / below your feet, ms between tries
export const CAT_GOAL = 5; // pets that unlock the outfit. fixed on purpose: hiding more cats later never re-locks anyone

// lore chapters, in story order. each NPC tells one. `file` is the summary the LORE page shows once you've heard it
export const CHAPTERS = [
  { id: 'machine', name: 'THE MACHINE', file: 'it started as one vending machine in a mall. it never gave change. forty years of keeping the change bought the mall, the town, and then money itself. wages are containers now, because a salary is a known quantity and the shareholders hate knowing things.' },
  { id: 'merger', name: 'THE MERGER', file: '☺ CORP bought the government at an auction (it was the only bidder), then merged with everyone else. you are an employee. matches are the job, because you can lie in a spreadsheet but you cannot lie about a headshot. respawning is in the benefits package: returned mannequins from the stockroom.' },
  { id: 'void', name: 'THE VOID', file: 'everything past the licensed play area was sold to investors as premium negative space. every bad quarter they repossess a bit more ground. people who fall in are still employed. they just lose the dental.' },
  { id: 'jank', name: 'THE JANK', file: 'the physics department was downsized to one intern, forty years ago. he wrote gravity from memory on his first day. the banana and the marbles use the floor code. stopping things was a paid add-on nobody bought, so momentum never ends.' },
  { id: 'founder', name: 'THE FOUNDER', file: 'during the merger vote the founder walked across the keyboard and typed yyyyyyyyyyyy. legally, that is a yes. the founder is a cat. so is the whole board of directors, and they hide everywhere. pet them. it is how you get promoted.' },
];

// gift: what they hand over the first time (a cosmetic, or a container: { roll: 'crate' | 'bag' | 'box' }).
// if you already own the cosmetic you get `or` instead. gift: null = they only talk.
// lines: dialogue nodes. say = lines shown one at a time; opts = [button text, next node]; no opts = the chat ends.
// the `end` node is where every chat finishes: `got` is said the first time (the gift line), `again` on later visits
export const SECRETS = {
  // ---------------------------------------------------------------- NPCs
  gary: {
    kind: 'npc', map: 'warehouse', p: [55.2, 0.12, -10.4], face: Math.PI, chapter: 'merger', look: 'gary',
    name: 'GARY', title: 'regional manager (the region is this room)', where: 'somewhere in the Warehouse', gift: null,
    lines: {
      start: { say: ['oh. a visitor. nobody comes to the site office. that is why i picked it.', 'i\'m gary. regional manager. the region is this room.'],
        opts: [['what happened to the world?', 'merger'], ['why does everyone fight?', 'kpi'], ['bye gary', 'bye']] },
      merger: { say: ['the merger. ☺ CORP bought the government at an auction. it was the only bidder. the government brought snacks.', 'then it merged with everyone else. you didn\'t sign anything? you breathed near a form. that counts now.', 'so we\'re all employees. me, you, the bots. the bots got better benefits.'],
        opts: [['and the fighting?', 'kpi'], ['that\'s bleak', 'bleak']] },
      bleak: { say: ['it\'s fine. i\'ve been fine for nineteen years.', 'i get one day off a year. it\'s always during a match.'], opts: [['why the fighting though?', 'kpi'], ['i have to go', 'bye']] },
      kpi: { say: ['productivity. we tried spreadsheets. people lied in the spreadsheets.', 'you can\'t lie about a headshot. so the job is matches now. kills are the only honest KPI.', 'dying is covered by the benefits package. you respawn in a body from the stockroom. returned mannequins. that\'s why your knee bends wrong.'],
        opts: [['can i have something?', 'end'], ['thanks gary', 'bye']] },
      bye: { say: ['close the door on your way out.', 'there\'s no door. close it anyway.'] },
      end: { got: ['i\'d love to give you something. the gift budget got restructured into a smaller gift budget. then into a firm handshake.', '*he shakes your hand. it\'s limp.*'], again: ['still no gift budget. it\'s in a meeting. so am i.'] },
    },
  },
  dale: {
    kind: 'npc', map: 'suburb', p: [-75.2, 1.1, -49.0], face: 0, chapter: 'machine', look: 'dale', // on the corner store's loading dock, the machine against the stockroom wall
    name: 'DALE', title: 'vending machine guy', where: 'somewhere in Suburb', gift: { roll: 'box' },
    lines: {
      start: { say: ['careful. she bites.', 'that\'s a Jank Cola machine. i\'m the guy who fixes them. been fixing this one since tuesday. not sure which tuesday.'],
        opts: [['what is ☺ CORP?', 'corp'], ['why do we get paid in containers?', 'pay'], ['can i get a cola?', 'cola']] },
      corp: { say: ['☺ CORP started as one of these. one vending machine, in a mall. it sold cola and it never gave change.', 'it kept the change for forty years. compound interest. it bought the mall. then the town. then the idea of money.', 'now it\'s everywhere and i fix it. it doesn\'t thank me. i don\'t thank it either. it works.'],
        opts: [['and the containers?', 'pay'], ['respect', 'end']] },
      pay: { say: ['the machine stopped taking money. money was too predictable. the shareholders hate knowing things.', 'so wages are containers now. crates, duffel bags, boxes. could be a legendary. could be a spray that says L.', 'that\'s the whole economy. the surprise. you\'re welcome.'],
        opts: [['where did it all start?', 'corp'], ['cool. bye', 'end']] },
      cola: { say: ['the cola\'s 0% water now. i don\'t know what it is. i don\'t ask.', '*he hits the machine with a wrench. something falls out.*'], opts: [['...is that for me?', 'end']] },
      end: { got: ['here. it fell out while i was hitting her. don\'t tell anyone.'], again: ['one per customer. she counts. she always counts.'] },
    },
  },
  janitor: {
    kind: 'npc', map: 'backrooms', p: [-77, -4.5, -5.6], face: Math.PI, chapter: 'void', look: 'janitor',
    name: 'THE JANITOR', title: 'has seen things', where: 'somewhere deep in the Backrooms', gift: { type: 'grapple', id: 'plunger', or: { roll: 'bag' } },
    lines: {
      start: { say: ['*squeak. squeak.*', 'careful. floor\'s wet. it\'s a pool. i mop it anyway. job\'s a job.'],
        opts: [['what\'s past the edge of the map?', 'void'], ['you look like you\'ve seen things', 'seen'], ['how long have you been down here?', 'long']] },
      void: { say: ['the edge? ☺ CORP sold it. everything past the licensed play area. "premium negative space". investors love it.', 'every bad quarter they repossess a bit more ground. i mop right up to the edge. every night it\'s a little closer.', 'i had a house out there. now it\'s a premium feature.'],
        opts: [['what happens if you fall in?', 'fall'], ['that\'s rough', 'end']] },
      fall: { say: ['you\'re still employed. you just lose the dental.', 'some of them wave. don\'t wave back. it gets them excited.'], opts: [['ok', 'end']] },
      seen: { say: ['i\'ve seen a man t-bag so hard he exploded. i mopped him up.', 'i\'ve seen the board of directors. little furry executives. they sleep on everything.', 'don\'t tell them i said furry.'],
        opts: [['what\'s past the edge?', 'void'], ['noted', 'end']] },
      long: { say: ['since the carpet had a colour. you could pick it, back then.', 'i picked beige. look how that turned out.'], opts: [['what\'s past the edge?', 'void'], ['bye', 'end']] },
      end: { got: ['take this. my plunger. it sticks to anything.', 'don\'t ask where it\'s been. i know where it\'s been.'], again: ['*squeak. squeak.* the floor\'s still wet.'] },
    },
  },
  smiles: {
    kind: 'npc', map: 'skyline', p: [-60, 65.6, -80], face: -Math.PI / 2, chapter: 'founder', look: 'smiles', sit: true, // up the building site's crane, on the jib, looking at the Spire
    name: 'MR. SMILES', title: 'mascot (retired)', where: 'somewhere very high in Skyline', gift: { type: 'kill', id: 'balloon', or: { roll: 'bag' } },
    lines: {
      start: { say: ['oh! a fan! nobody climbs up here. that\'s the point of up here.', 'i used to be the mascot. Mr. Smiles. the big happy face of ☺ CORP. now i\'m a guy in a hot suit on a crane.'],
        opts: [['who runs ☺ CORP?', 'founder'], ['why did you retire?', 'retire'], ['take the head off', 'head']] },
      retire: { say: ['they made fun mandatory. if fun is mandatory it\'s a job. if it\'s a job it isn\'t fun.', 'i did the maths. the maths broke me.'], opts: [['who runs it now?', 'founder']] },
      head: { say: ['no.', 'there\'s nothing under there anymore. it\'s smiles all the way down.'], opts: [['ok... who runs ☺ CORP?', 'founder']] },
      founder: { say: ['nobody\'s seen the founder. that\'s the official line. the plaque just says OUR FOUNDER.', 'i\'ve seen the founder. i was in the room for the merger vote. the founder walked across the keyboard.', 'it typed yyyyyyyyyyyy. legally that\'s a yes.', 'the founder is a cat.'],
        opts: [['a CAT??', 'board']] },
      board: { say: ['the whole board of directors is cats. they hide all over the place. shelves. car roofs. awnings. boxes, mostly.', 'find them and pet them. that\'s how you get promoted.', 'the board has a dress code for its favourite staff. ears. tail. a maid dress. don\'t ask me. i just wear the face.'],
        opts: [['i will pet the board', 'end']] },
      end: { got: ['here. my balloons. anyone you get floats away.', 'last fun thing i own. take care of it.'], again: ['go pet the board. they\'re waiting. they\'re always waiting.'] },
    },
  },
  todd: {
    kind: 'npc', map: 'islands', p: [2.6, 42.8, -2.4], face: -0.6, chapter: 'jank', look: 'todd',
    name: 'TODD', title: 'intern (year 40)', where: 'somewhere above the Islands', gift: { roll: 'crate' },
    lines: {
      start: { say: ['oh hey! sorry, i\'m on a deadline. the deadline was in 1986.', 'i\'m todd. i\'m the intern. i\'m also the whole physics department. they downsized it to me.'],
        opts: [['why is everything so janky?', 'jank'], ['why does momentum never stop?', 'mom'], ['40 years as an intern?', 'intern']] },
      jank: { say: ['i wrote gravity on my first day. from memory. i was nervous.', 'the bananas? i copied the floor code onto the banana. then onto the marbles. same code. that\'s why you slip.', 'this purple and black square is where i ran out of textures. i\'m patching it. with hope.'],
        opts: [['and momentum?', 'mom'], ['good luck todd', 'end']] },
      mom: { say: ['stopping things was a paid add-on. we never bought it. so things just keep going.', 'if you grapple fast enough you can leave the quarter. please don\'t. accounting gets weird.'],
        opts: [['why is it all so janky?', 'jank'], ['got it', 'end']] },
      intern: { say: ['unpaid! well. paid in exposure. it\'s very exposed up here. it\'s windy.', 'my lanyard says INTERN. the lanyard is also an intern.'], opts: [['why the jank?', 'jank'], ['bye todd', 'end']] },
      end: { got: ['oh! take this crate. it\'s from my onboarding kit. i never opened it. i was scared.'], again: ['back to work. the floor isn\'t going to code itself. it is, actually. badly.'] },
    },
  },
  // ---------------------------------------------------------------- the board of directors (cats)
  cat_biscuit: { kind: 'cat', map: 'warehouse', p: [14.78, 7.05, 9.45], face: 0, name: 'BISCUIT', title: 'chief financial officer', where: 'Warehouse', pose: 'loaf', coat: 'tabby' },
  cat_beans: { kind: 'cat', map: 'suburb', p: [76.55, 1.6, 31.45], face: 2.4, // on a prize pumpkin in the community garden
    name: 'BEANS', title: 'vp of sitting', where: 'Suburb', pose: 'lie', coat: 'tux' },
  cat_gravy: { kind: 'cat', map: 'rooftop', p: [-3.5, 0.45, 4.0], face: 0, // on the sofa in the penthouse lounge, chairing (sitting)
    name: 'PRINCESS GRAVY', title: 'chair of the board', where: 'Rooftop', pose: 'sit', coat: 'cream' },
  cat_meatloaf: { kind: 'cat', map: 'bazaar', p: [-45, 8.0, 37], face: 0, // on the tea table up on the tea house roof (synergy is a nap)
    name: 'MEATLOAF', title: 'head of synergy', where: 'Bazaar', pose: 'side', coat: 'grey' },
  cat_gremlin: { kind: 'cat', map: 'desert', p: [-44.1, 0.9, -23.0], face: Math.PI, // in the bank vault, on the gold (legal is handling it)
    name: 'GREMLIN', title: 'head of legal', where: 'Desert', pose: 'box', coat: 'calico' },
};
export const SECRET_IDS = Object.keys(SECRETS);
export const NPC_IDS = SECRET_IDS.filter((k) => SECRETS[k].kind === 'npc');
export const CAT_IDS = SECRET_IDS.filter((k) => SECRETS[k].kind === 'cat');
export const secretsOn = (mapId) => SECRET_IDS.filter((k) => SECRETS[k].map === mapId);
// everything you've found, from the account's inventory (unknown or removed ids drop out)
export function loreOf(inv) { return new Set(inv && Array.isArray(inv.lore) ? inv.lore.filter((k) => typeof k === 'string' && Object.hasOwn(SECRETS, k)) : []); }
export const catsOf = (inv) => [...loreOf(inv)].filter((k) => SECRETS[k].kind === 'cat').length;
// where Plant & Defuse rounds are on, nobody's around (no interactions mid-round)
export const secretsOff = (game) => game === 'bomb';
// can someone standing at pos (feet) reach the secret? a cylinder: sideways reach, a bit up and down
export function canReach(pos, id, slack = 0) {
  const s = Object.hasOwn(SECRETS, id) && SECRETS[id];
  if (!s || !Array.isArray(pos)) return false;
  const dy = s.p[1] - pos[1];
  return Math.hypot(pos[0] - s.p[0], pos[2] - s.p[2]) < SECRET.reach + slack && dy < SECRET.up + slack && dy > -SECRET.down - slack;
}
