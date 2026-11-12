// teams with parties in them (server/party.js): a party stays on one side. parties go first, the biggest first, each
// onto the side with fewer people; then everyone else fills in evenly (humans before bots, as before)
export function teamPlan(list) {
  const t = new Map(), c = { 1: 0, 2: 0 }, groups = new Map();
  for (const p of list) if (p.party && !p.isBot) { if (!groups.has(p.party)) groups.set(p.party, []); groups.get(p.party).push(p); }
  for (const g of [...groups.values()].filter((g) => g.length > 1).sort((a, b) => b.length - a.length)) { const s = c[1] <= c[2] ? 1 : 2; for (const p of g) { t.set(p, s); c[s]++; } }
  for (const p of list) if (!t.has(p)) { const s = c[1] <= c[2] ? 1 : 2; t.set(p, s); c[s]++; }
  return t;
}
