// The world's zones, walked in and out of: a reach event when you step into one, leave when you step out. A step that
// starts while you're already standing in its place (m04's "go to the sunset wall" when you're at the Sunset Wall) has
// its zones forgotten, so the next frame counts you as arriving: otherwise it would wait for you to walk out and back in.
// Used by public/js/story/boot.js every frame; tested in tests/story/arrive.test.mjs.
export class ZoneTracker {
  constructor() { this.in = new Set(); }
  // inside: the zone ids you're in this frame -> [{ type: 'reach' | 'leave', zone }]
  update(inside) {
    const out = [];
    for (const z of inside) if (!this.in.has(z)) { this.in.add(z); out.push({ type: 'reach', zone: z }); }
    for (const z of [...this.in]) if (!inside.has(z)) { this.in.delete(z); out.push({ type: 'leave', zone: z }); }
    return out;
  }
  forget(zones) { for (const z of zones) this.in.delete(z); }
  clear() { this.in.clear(); }
  has(z) { return this.in.has(z); }
}
// the zones a quest step waits for you to reach (reach / escort / a delivery's reach): defs = the engine's defs
export function stepZones(defs, quest, step) {
  const q = defs.quests[quest], s = q && q.steps.find((x) => x.id === step);
  if (!s) return [];
  return (s.goals || (s.goal ? [s.goal] : [])).filter((g) => g && (g.type === 'reach' || g.type === 'escort') && g.zone).map((g) => g.zone);
}
