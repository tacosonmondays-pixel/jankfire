// BOARD GAME NIGHT (docs/party/DESIGN.md): the party board mode's rules, numbers and every name players see.
// shared by the server (server/bgn.js, server/bgnbots.js) and the client (public/js/bgn*.js). browser-safe.
// every player-facing word lives in BGN_NAMES (and the name/desc fields of the tables below), so a rename is one line.

export const BGN_NAMES = {
  mode: 'BOARD GAME NIGHT', tag: 'PARTY', coupons: 'COUPONS', coupon: 'COUPON', bread: 'GOLDEN BREAD',
  board: 'THE KITCHEN TABLE', lid: 'THE BOX LID', die: 'THE FOAM DIE', host: 'THE RULES GUY', crease: 'THE CREASE',
  bakery: 'THE BAKERY', store: 'CORNER STORE', last: 'LAST CALL', toast: 'THE TOASTING', dibs: 'DIBS', tie: 'TIEBREAKER',
  loop: 'THE LOOP', sponge: 'a sponge', desc: 'roll the die, buy golden bread, minigames between turns',
  // big HUD callouts (ALL CAPS, punchy)
  call: {
    coupon: '+{n} COUPONS', fee: 'LATE FEE', jank: 'JANK!', store: "SHOP'S OPEN", spill: 'STUCK', bread: 'GOLDEN BREAD!',
    allowance: 'ALLOWANCE', duel: 'DUEL!', slip: 'SLIPPED', sign: 'WET FLOOR', mg: 'MINIGAME TIME', rent: 'RENT IS DUE',
    hung: 'HUNG JURY', last: 'LAST CALL', toast: 'TOASTED', moved: 'THE BREAD HAS MOVED', broke: 'come back with {n} coupons',
    settled: 'THEY SETTLED IT OUTSIDE', sponge: 'IT WAS A SPONGE', lasso: 'YOINK', cart: 'NO BRAKES', dibs: 'DIBS!',
    roll: 'ROLL', yourTurn: 'YOUR TURN', sd: 'SUDDEN DEATH', tie: 'TIEBREAKER',
  },
  // the rules guy, deadpan and wrong
  host: {
    intro: ["welcome to board game night. i read the rules once.", "most golden bread wins. i think.", "that's not how you play. anyway."],
    one: ['rolled a one. bold.', 'a one. the die believes in you less than i do.'],
    six: ['six. show off.', 'a six. the foam die has favourites.'],
    moved: ["the bread has moved. don't ask me how.", 'the bakery packed up. it does that.'],
    duel: ['you landed on them. that means fight. page 4.', 'two pawns, one space. violence.'],
    last: ['found the back of the box. there are more rules.', 'last call. coupon spaces pay double now. probably.'],
    afk: ['they went to the fridge. i played for them.'],
    end: ['game over. somebody clean this up.'],
  },
  // formats (end-of-round minigames)
  fmt: { ffa: '1v1v1v1', '2v2': '2v2', '3v1': 'EVERYONE VS THE LEADER', boss: '4 VS BOSS', duel: 'DUEL', tie: 'TIEBREAKER' },
  stake: { coupons: '10 COUPONS', bread: '1 GOLDEN BREAD' },
  path: ['THE LOOP', 'THE CREASE'],
};

// numbers (every one a default the owner can change). times in ms
export const BGN = {
  seats: 4, coupons: 10, rounds: 10, roundOpts: [5, 10, 15], price: 20, bagMax: 3,
  coupon: 3, fee: 3, allowance: 5, lastRounds: 3, lastMul: 2, stuckDiv: 2,
  hop: 350, dieMs: 1500, landMs: 1100, introMs: 4500, dibsMs: 4000, eventMs: 2600,
  choice: { online: 10000, offline: 30000 }, botThink: [600, 1400],
  mgIntro: 5000, mgRes: 6000, mgGrace: 6000,
  duelFrom: 4, duelFee: 10, duelCoupons: 10, botDuelMs: 3000, sudden: 20000,
  trapRounds: 3, signRange: 6, peelBack: 3, bakeryMin: 8, duckLoss: 5, duckSpaces: 3, tax: 10,
  storeStock: 3, endMs: 15000, again: 20000, rate: 6, // rate: bg messages a second, per player
  fmtW: { ffa: 40, '2v2': 25, '3v1': 20, boss: 15 },
  pay: { ffa: [10, 6, 3, 1], v2: [8, 1], v2tie: 4, v31: { one: 15, three: 5 }, boss: { win: 8, mvp: 5, lose: 2 } },
  bossOn: false, // the bosses (THE LANDLORD, THE NIGHT MANAGER) arrive in the next PR: until then no BOSS format
};

// space kinds: colour, what landing does
export const SPACE = {
  c: { name: 'COUPON', color: '#39ff14' },
  f: { name: 'LATE FEE', color: '#ff3030' },
  j: { name: 'JANK', color: '#ff00dc' },
  s: { name: 'CORNER STORE', color: '#ffe14d' },
  p: { name: 'SODA SPILL', color: '#8a5a2b' },
  b: { name: 'THE BAKERY', color: '#ffb300' },
  L: { name: 'THE BOX LID', color: '#ffffff' },
};

// corner store items: they change the board, never your stats. used before your roll, one a turn
export const BGN_ITEMS = {
  peel: { name: 'BANANA PEEL', cost: 5, desc: 'drop it on your space. the next pawn through slips back 3. hard bananas, soft landing.', color: '#ffe14d' },
  sign: { name: 'WET FLOOR SIGN', cost: 6, desc: 'put it up to 6 spaces ahead. the next pawn to get there has to stop. legally.', color: '#ffb04f', to: 'space' },
  cart: { name: 'SHOPPING CART', cost: 8, desc: "roll the die twice and ride. you can't stop at shops or the bakery. carts don't have brakes.", color: '#4fd8ff' },
  fake: { name: 'FAKE BREAD', cost: 10, desc: 'turn any COUPON space into a fake bakery. whoever buys there pays you and gets a sponge.', color: '#ffb300', to: 'space' },
  lasso: { name: 'LASSO', cost: 12, desc: "yank any pawn onto your space. that's a duel.", color: '#ff4fd8', to: 'seat' },
};
export const BGN_ITEM_ORDER = ['peel', 'sign', 'cart', 'fake', 'lasso'];

// jank spaces: the rules guy spins a wheel (never the same one twice in a row)
export const BGN_JANK = {
  marbles: { name: 'MARBLES!', desc: 'every pawn slides 1-3 spaces. no duels from sliding.' },
  ducks: { name: 'DUCKS INBOUND', desc: '3 spaces get a duck. pawns there lose 5 coupons.' },
  tax: { name: 'AUDITED', desc: 'the richest seat pays the poorest 10.' },
  misread: { name: 'HE MISREAD IT', desc: 'the bakery moves. right now.' },
  swap: { name: 'SWAP MEET', desc: 'you swap places with a random pawn.' },
};
export const BGN_JANK_ORDER = ['marbles', 'ducks', 'tax', 'misread', 'swap'];

// last call: last place picks one for the rest of the game
export const BGN_HOUSE = [
  { id: 'cheap', name: 'CHEAP BREAD', desc: 'golden bread costs 10.' },
  { id: 'nofees', name: 'NO MORE FEES', desc: 'every LATE FEE is a JANK now.' },
  { id: 'rush', name: 'BOSS RUSH', desc: 'the next minigame is a BOSS. (no boss yet: everyone vs the leader instead)' },
];

// the minigames: existing modes on small maps with a short clock. fmts: where it can come up (duel = 1v1).
// target: the kill / point limit (0 = the mode's own end). lives / ladder: per-room knobs (server/bgn.js)
export const BGN_MINIS = {
  brawl: { n: 1, name: 'CRATE BRAWL', game: 'dm', map: 'crate', time: 60, target: 10, fmts: ['ffa', 'duel'], rule: 'most kills wins. it is a box. fight in the box.' },
  spoons: { n: 2, name: 'SPOON FIGHT', game: 'spoons', map: 'crate', time: 60, target: 10, fmts: ['ffa', 'duel', '2v2', 'tie'], rule: 'spoons only, one hit kills. most kills wins (team kills in 2v2).' },
  hotfloor: { n: 3, name: 'HOT FLOOR', game: 'lava', map: 'platform', time: 75, target: 10, fmts: ['ffa', 'duel'], rule: 'the floor is lava. most kills wins. lava deaths count against you.' },
  ducks: { n: 4, name: 'DUCK DODGE', game: 'duckrain', map: 'rooftop', time: 60, target: 10, fmts: ['ffa'], rule: 'ducks fall from the sky. most kills wins. look up.' },
  meat: { n: 5, name: 'MYSTERY MEAT', game: 'rand', map: 'crate', time: 60, target: 10, fmts: ['ffa', 'duel'], rule: 'a random loadout every life. most kills wins.' },
  oneshot: { n: 6, name: 'ONE-SHOT WONDER', game: 'oitc', map: 'crate', time: 90, target: 0, lives: 2, fmts: ['ffa', 'duel'], rule: 'one bullet, any hit kills. 2 lives. last one standing.' },
  ladder: { n: 7, name: 'SPEED LADDER', game: 'gun', map: 'crate', time: 90, target: 0, ladder: 6, fmts: ['ffa', 'duel'], rule: 'six guns. a kill moves you up. first spoon kill wins.' },
  rvb: { n: 8, name: 'RED VS BLUE', game: 'tdm', map: 'platform', time: 75, target: 15, fmts: ['2v2'], rule: 'red vs blue. team kills win.' },
  tagsale: { n: 9, name: 'TAG SALE', game: 'tags', map: 'platform', time: 75, target: 10, fmts: ['2v2'], rule: 'kills drop tags. grab the other team\'s. most tags wins.' },
  leader: { n: 10, name: 'EVERYONE VS THE LEADER', game: 'inf', map: 'rooftop', time: 60, target: 0, fmts: ['3v1'], rule: 'the leader is patient zero. turn all three to win. three: survive.' },
};
export const BGN_MINI_ORDER = Object.keys(BGN_MINIS);
export const BGN_FMTS = ['ffa', '2v2', '3v1', 'boss'];

// a little seeded rng (mulberry32) for JF_BGN_SEED: same seed, same game
export function bgnRng(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
// "+{n} COUPONS" -> "+3 COUPONS"
export const bgnFill = (s, v) => String(s).replace(/\{(\w+)\}/g, (_, k) => (v && v[k] != null ? v[k] : ''));
