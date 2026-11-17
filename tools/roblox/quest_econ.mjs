// the daily quests + weekly track economy, simulated (roblox/docs/QUESTS.md, "The numbers").
// run: node tools/roblox/quest_econ.mjs [players] [weeks]
// the numbers below are Shared.QuestData's (roblox/src/shared/QuestData.luau): keep the two the same.
// every player rolls 3 quests a day (one easy, one medium, one hard), one free reroll, and finishes each with the
// chance their kind of player has. a finished quest pays its Brass and its weekly points at once; the weekly bar pays
// its steps as they're reached and starts again on Monday 00:00 UTC.
const TIERS = {
  easy: { brass: 30, pts: 1 },
  medium: { brass: 50, pts: 2 },
  hard: { brass: 80, pts: 3 },
};
const STEPS = [ // weekly points -> reward
  { at: 3, brass: 75 },
  { at: 6, tix: 1 },
  { at: 10, brass: 100 },
  { at: 15, tix: 1 },
  { at: 21, brass: 150 },
  { at: 28, tix: 1 },
  { at: 34, brass: 200 },
  { at: 40, tix: 2 },
];
const PRICES = { // what the shop asks (Brass never buys a Crate)
  crate: { tix: 12 },
  bag: { tix: 6, brass: 2500 },
  spray: { tix: 3, brass: 1000 },
};

// kinds of player: chance to play on a given day, and to finish each tier's quest on a day they play. the reroll
// swaps the quest they're least likely to finish (the hard one) for another hard one: a small lift (REROLL_LIFT)
const REROLL_LIFT = 0.1;
const KINDS = {
  casual: { play: 2 / 7, easy: 0.85, medium: 0.45, hard: 0.12 },
  regular: { play: 0.65, easy: 0.95, medium: 0.75, hard: 0.4 },
  grinder: { play: 1, easy: 1, medium: 1, hard: 0.95 },
};

// VIP players also claim the VIP daily reward (Trisangle in the VIP room, the shop session's VipDailyData.TABLE, one
// claim a day) on the days they play. its odds as the shop session gave them on 17 Nov, with the main session's
// decision the same day: the Crate at 1% (was 2%), the freed 1% to the Spray Can (the 1% of daily-only items
// left out): Brass through Quests.giveBrass (capped at 300 a day), or a container straight into stock
const VIP_DAILY = [
  { brass: 40, w: 0.424 }, { brass: 100, w: 0.273 }, { brass: 250, w: 0.111 },
  { box: 'spray', w: 0.131 }, { box: 'bag', w: 0.051 }, { box: 'crate', w: 0.01 },
];
function vipDaily() {
  let r = rand() * VIP_DAILY.reduce((a, e) => a + e.w, 0);
  for (const e of VIP_DAILY) { if (r < e.w) return e; r -= e.w; }
  return VIP_DAILY[0];
}

let seed = 12345;
const rand = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };

function simulate(kind, weeks, vip) {
  const k = KINDS[kind];
  let brass = 0, tix = 0, quests = 0, days = 0, played = 0;
  const boxes = { spray: 0, bag: 0, crate: 0 }; // (VIP daily containers)
  let firstCrate = null, firstSprayB = null, firstBag = null;
  const fullWeeks = [];
  for (let w = 0; w < weeks; w++) {
    let pts = 0;
    let stepI = 0;
    for (let d = 0; d < 7; d++) {
      days++;
      if (rand() < k.play) {
        played++;
        if (vip) { const e = vipDaily(); if (e.brass) brass += e.brass; else boxes[e.box]++; }
        for (const t of ['easy', 'medium', 'hard']) {
          const p = Math.min(1, k[t] + (t === 'hard' ? REROLL_LIFT * (1 - k[t]) : 0));
          if (rand() < p) {
            quests++;
            brass += TIERS[t].brass;
            pts += TIERS[t].pts;
          }
        }
        while (stepI < STEPS.length && pts >= STEPS[stepI].at) {
          brass += STEPS[stepI].brass || 0;
          tix += STEPS[stepI].tix || 0;
          stepI++;
        }
      }
      if (firstCrate === null && tix >= PRICES.crate.tix) firstCrate = days;
      if (firstSprayB === null && brass >= PRICES.spray.brass) firstSprayB = days;
      if (firstBag === null && brass >= PRICES.bag.brass) firstBag = days;
    }
    fullWeeks.push(stepI === STEPS.length ? 1 : 0);
  }
  return { brass, tix, quests, days, played, boxes, firstCrate, firstSprayB, firstBag, full: fullWeeks.reduce((a, b) => a + b, 0) / weeks };
}

function mean(xs) { const v = xs.filter((x) => x !== null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; }
function median(xs) { const v = xs.filter((x) => x !== null).sort((a, b) => a - b); return v.length ? v[Math.floor(v.length / 2)] : null; }

const N = Number(process.argv[2]) || 5000;
const WEEKS = Number(process.argv[3]) || 52;
const fmt = (x, d = 1) => (x === null ? 'never' : x.toFixed(d));
console.log(`${N} players of each kind, ${WEEKS} weeks\n`);
console.log('kind        days played/wk  quests/day  Brass/day  tickets/wk  full weeks    days/Spray Can     days/Duffel   days/Crate (all)  first Crate (median day)');
for (const [kind, vip] of Object.keys(KINDS).flatMap((k) => [[k, false], [k, true]])) {
  const runs = [];
  for (let i = 0; i < N; i++) runs.push(simulate(kind, WEEKS, vip));
  const days = WEEKS * 7;
  const brassDay = mean(runs.map((r) => r.brass / days));
  const tixWk = mean(runs.map((r) => r.tix / WEEKS));
  const qDay = mean(runs.map((r) => r.quests / days));
  const playedWk = mean(runs.map((r) => r.played / WEEKS));
  const full = mean(runs.map((r) => r.full));
  const perDay = (k) => mean(runs.map((r) => r.boxes[k] / days));
  // containers a day from every source: Brass (Spray Can / Duffel Bag prices), tickets (Crate), the VIP daily itself
  const sprayDay = brassDay / PRICES.spray.brass + perDay('spray');
  const bagDay = brassDay / PRICES.bag.brass + perDay('bag');
  const crateDay = tixWk / 7 / PRICES.crate.tix + perDay('crate');
  console.log(
    `${(kind + (vip ? '+VIP' : '')).padEnd(11)} ${fmt(playedWk).padStart(14)}  ${fmt(qDay, 2).padStart(10)}  ${fmt(brassDay, 0).padStart(9)}  ${fmt(tixWk, 2).padStart(10)}  ${(fmt(full * 100, 0) + '%').padStart(10)}` +
    `  ${fmt(1 / sprayDay).padStart(17)}  ${fmt(1 / bagDay).padStart(15)}  ${fmt(1 / crateDay).padStart(19)}  ${String(median(runs.map((r) => r.firstCrate)) ?? 'never').padStart(24)}`,
  );
}
const maxPts = 7 * (TIERS.easy.pts + TIERS.medium.pts + TIERS.hard.pts);
const maxBrass = 7 * (TIERS.easy.brass + TIERS.medium.brass + TIERS.hard.brass) + STEPS.reduce((a, s) => a + (s.brass || 0), 0);
const maxTix = STEPS.reduce((a, s) => a + (s.tix || 0), 0);
console.log(`\nthe most a week can give: ${maxPts} points (the bar fills at ${STEPS[STEPS.length - 1].at}), ${maxBrass} Brass, ${maxTix} Crate Tickets`);
console.log(`so at best: a Crate every ${(PRICES.crate.tix / maxTix).toFixed(1)} weeks, a Spray Can every ${(PRICES.spray.brass / (maxBrass / 7)).toFixed(1)} days on Brass`);
