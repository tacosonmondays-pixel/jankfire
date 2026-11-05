// End-of-match vote: pick the MODE first, then the MAP for it. Shared so the client's clock and the server agree.
import { GAMES, GAME_ORDER, mapsFor } from './modes.js';

export const VOTE = { mode: 11000, map: 9000, reveal: 3000, cards: 4, botMin: 1200, botMax: 7000 };
export const voteTotal = () => VOTE.mode + VOTE.map + VOTE.reveal;
// the daily EVENT mode: always one of the mode cards (tagged EVENT), and the main menu's event card advertises it.
// rotates at midnight UTC so everyone online sees the same one
export const EVENT_POOL = ['duckrain', 'spoons', 'lava', 'oitc', 'gun', 'inf', 'rand'];
export function eventGame(t = Date.now()) {
  const pool = EVENT_POOL.filter((g) => GAMES[g]);
  return pool[Math.floor(t / 86400000) % pool.length];
}
const shuffle = (a, rnd) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
// 4 mode cards: the event, plus 3 others (never all free-for-all or all teams when there's a choice). every mode on a
// card has at least one map it can be played on
export function modeCards(maps, order, cur, rnd = Math.random) {
  const ok = GAME_ORDER.filter((g) => mapsFor(g, maps, order).length);
  const ev = eventGame();
  const out = ok.includes(ev) ? [ev] : [];
  const rest = shuffle(ok.filter((g) => g !== ev && g !== cur), rnd);
  if (cur && ok.includes(cur) && cur !== ev) rest.push(cur); // the mode you just played only if there's nothing else
  for (const g of rest) {
    if (out.length >= VOTE.cards) break;
    const same = out.every((x) => !!GAMES[x].teams === !!GAMES[g].teams);
    if (out.length === VOTE.cards - 1 && same && rest.some((x) => !out.includes(x) && !!GAMES[x].teams !== !!GAMES[g].teams)) continue; // keep a mix of teams + free for all
    out.push(g);
  }
  for (const g of rest) if (out.length < VOTE.cards && !out.includes(g)) out.push(g);
  return shuffle(out, rnd).map((g) => ({ game: g, event: g === ev ? 1 : 0 }));
}
// up to 4 map cards for the mode that won (the map you just played goes last in line)
export function mapCards(game, maps, order, cur, rnd = Math.random) {
  const ok = shuffle(mapsFor(game, maps, order), rnd);
  ok.sort((a, b) => (a === cur) - (b === cur));
  return ok.slice(0, VOTE.cards).sort(() => rnd() - 0.5).map((m) => ({ map: m }));
}
// humans decide. bots only break ties (and decide if no human voted). then it's random
export function tally(n, votes, isBot) {
  const h = new Array(n).fill(0), b = new Array(n).fill(0);
  for (const [id, i] of votes) if (i >= 0 && i < n) (isBot(id) ? b : h)[i]++;
  return { h, b };
}
export function winner(n, votes, isBot, rnd = Math.random) {
  const { h, b } = tally(n, votes, isBot);
  let best = [];
  for (let i = 0; i < n; i++) {
    if (!best.length) { best = [i]; continue; }
    const j = best[0], d = h[i] - h[j] || b[i] - b[j];
    if (d > 0) best = [i]; else if (d === 0) best.push(i);
  }
  return best[Math.floor(rnd() * best.length)];
}
