// BATTLE ISLAND squads with parties in them (server/party.js sets p.party): a party lands together. parties go first,
// the biggest first, each into the first squad with room for all of it (a party bigger than a squad spills into a
// second one, in squad-sized chunks); then everyone else fills the gaps in order (people before bots, as before).
// with no parties this is the old fill: squad 1 first, then 2, ...
export function islePlan(list, size) {
  const sq = new Map(), n = [], groups = new Map();
  const put = (ps) => { let s = n.findIndex((c) => c + ps.length <= size); if (s < 0) { n.push(0); s = n.length - 1; } n[s] += ps.length; for (const p of ps) sq.set(p, s + 1); };
  for (const p of list) if (typeof p.party === 'string' && !p.isBot) { if (!groups.has(p.party)) groups.set(p.party, []); groups.get(p.party).push(p); }
  for (const g of [...groups.values()].filter((g) => g.length > 1).sort((a, b) => b.length - a.length)) for (let i = 0; i < g.length; i += size) put(g.slice(i, i + size));
  for (const p of list) if (!sq.has(p)) put([p]);
  return sq;
}

// a late boarder from a party: the squad a partymate is already in, if it has room. the first of the party in: a squad
// with room for the whole party (the ones here + the tickets not used yet), else -1 (a new squad, so they land
// together). 0 = no party, or a party of one: the usual pick
export function islePartySquad(room, p, size) {
  if (typeof p.party !== 'string' || p.isBot) return 0;
  const c = new Map(), live = new Set(), I = room.br.isle;
  for (const o of room.fighters()) if (o !== p && o.sq && room.isleIn(o)) { c.set(o.sq, (c.get(o.sq) || 0) + 1); if (o.alive && o.br && !o.br.out && !I.sqOut.has(o.sq)) live.add(o.sq); }
  let need = 1;
  for (const o of room.fighters()) if (o !== p && o.party === p.party) { if (o.sq && room.isleIn(o)) { if (live.has(o.sq) && c.get(o.sq) < size) return o.sq; } else need++; }
  if (room.tickets instanceof Map) for (const t of room.tickets.values()) if (t && t.party === p.party && t.until > Date.now()) need++;
  if (need < 2) return 0;
  need = Math.min(need, size);
  let best = 0, bn = -1;
  for (const [s, n] of c) if (live.has(s) && n + need <= size && n > bn) { bn = n; best = s; }
  return best || -1;
}
