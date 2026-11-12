// OVERDUE story mode, server side. solo story runs in the player's browser (a web worker, public/js/story/host.js),
// so all this does for solo is keep the save slots. co-op (WP10) will run the same shared/story sim in StoryRoom.
//   POST /api/story/list  -> { slots: n, table, saves: [card|null x n] }
//   POST /api/story/load  { slot } -> { save }
//   POST /api/story/save  { slot, save } -> { ok, card }
//   POST /api/story/delete { slot } -> { ok }   (wipe a slot: the picker's WIPE IT. nothing to undo)
// every request needs a signed token (Bearer). bodies are capped by readJson (64 KB) and cleaned by shared/story/save.js.
import { cleanSave, saveCard, SAVE, FALLBACK } from '../shared/story/save.js';

const lastSave = new Map(); // name_lower -> time of the last accepted save (1 per SAVE.minGap per account)
const lastWipe = new Map(); // name_lower -> time of the last wipe (a few seconds apart: it's a button, not a loop)
export const WIPE_GAP = 3000;
const MAX_ROOMS = 8; // TECH_PLAN §4: more co-op rooms than this and the city is full (try solo)

export async function storyApi(accounts, url, body, auth, send) {
  const u = await accounts.verify(auth);
  if (!u) return send(401, { error: 'log in to save your story' });
  const store = accounts.store;
  if (typeof store.getStory !== 'function') return send(503, { error: 'no story saves here' });
  const info = await store.storyInfo();
  const slotOf = (x) => (Number.isInteger(x) && x >= 0 && x < info.slots ? x : null);
  const all = await store.getStory(u.name_lower);
  const bySlot = (n) => all.find((s) => s && s.slot === n) || null;
  switch (url) {
    case '/api/story/list':
      return send(200, { slots: info.slots, table: info.table, saves: Array.from({ length: info.slots }, (_, i) => saveCard(bySlot(i))) });
    case '/api/story/load': {
      const slot = slotOf(body.slot);
      if (slot == null) return send(400, { error: 'bad slot' });
      return send(200, { save: bySlot(slot) });
    }
    case '/api/story/save': {
      const slot = slotOf(body.slot);
      if (slot == null) return send(400, { error: 'bad slot' });
      const t = Date.now();
      if (t - (lastSave.get(u.name_lower) || 0) < SAVE.minGap) return send(429, { error: 'saving too fast' });
      const r = cleanSave(body.save, { slot, prev: bySlot(slot), maxBytes: info.table ? SAVE.maxBytes : FALLBACK.maxBytes });
      if (r.error) return send(400, { error: r.error });
      r.save.t = t;
      lastSave.set(u.name_lower, t);
      if (lastSave.size > 5000) for (const [k, v] of lastSave) if (t - v > SAVE.minGap) lastSave.delete(k); // (forget old ones)
      await store.putStory(u.name_lower, slot, r.save);
      return send(200, { ok: true, card: saveCard(r.save) });
    }
    case '/api/story/delete': {
      const slot = slotOf(body.slot);
      if (slot == null) return send(400, { error: 'bad slot' });
      if (typeof store.delStory !== 'function') return send(503, { error: 'no story saves here' });
      const t = Date.now();
      if (t - (lastWipe.get(u.name_lower) || 0) < WIPE_GAP) return send(429, { error: 'wiping too fast' });
      lastWipe.set(u.name_lower, t);
      if (lastWipe.size > 5000) for (const [k, v] of lastWipe) if (t - v > WIPE_GAP) lastWipe.delete(k);
      await store.delStory(u.name_lower, slot); // (your own slots only: the account comes from the token)
      lastSave.delete(u.name_lower); // (a new game can save straight away)
      return send(200, { ok: true });
    }
    default: return send(404, { error: 'nope' });
  }
}

// co-op story room (WP10). empty for now: the class and the cap exist so the lobby/net lane has a place to grow.
export class StoryRoom {
  static rooms = new Map();
  static full() { return StoryRoom.rooms.size >= MAX_ROOMS; }
  constructor(id) {
    this.id = id;
    this.players = new Map();
    StoryRoom.rooms.set(id, this);
  }
  close() { StoryRoom.rooms.delete(this.id); }
}
