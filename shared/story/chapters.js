// OVERDUE chapters for the save slot cards: every main mission (acts I-V, flashbacks too) in story order, with the
// line a slot card shows ("ACT 1 · tickets please"). the card works out where a save is from its quest progress, so
// old saves (that all say chapter 'return_to_sender') read right too, and nothing the engine writes has to change.
import { MISSIONS_ACT1 } from './content/missions/act1.js';
import { MISSIONS_ACT2 } from './content/missions/act2.js';
import { MISSIONS_ACT3 } from './content/missions/act3.js';
import { MISSIONS_ACT4 } from './content/missions/act4.js';
import { MISSIONS_ACT5 } from './content/missions/act5.js';

// the card's voice: lowercase, no commas or full stops ("TICKETS, PLEASE" -> "tickets please")
export const chapterLabel = (title) => String(title || '').toLowerCase().replace(/[,.!?]/g, '').replace(/\s+/g, ' ').trim();

export const CHAPTER_LIST = Object.entries({ ...MISSIONS_ACT1, ...MISSIONS_ACT2, ...MISSIONS_ACT3, ...MISSIONS_ACT4, ...MISSIONS_ACT5 })
  .map(([id, m]) => ({ id, act: m.act | 0, n: m.n | 0, label: chapterLabel(m.title) }))
  .sort((a, b) => a.act - b.act || a.n - b.n); // (act II's m06 comes after act I's m06)
export const CHAPTER = Object.fromEntries(CHAPTER_LIST.map((c, i) => [c.id, { ...c, i }]));
const LEGACY = { return_to_sender: 'm01_return_to_sender' }; // the one chapter saves were ever given

// where a save is: the furthest mission you've started and not finished, else the furthest you finished, else the
// first. data = a save's data ({ quests: { id: { done } } }); anything else reads as a new game. never throws
export function chapterOf(data, chapter) {
  let open = -1, done = -1;
  const q = data && typeof data === 'object' && data.quests && typeof data.quests === 'object' ? data.quests : {};
  for (const id of Object.keys(q)) {
    if (!Object.hasOwn(CHAPTER, id) || !q[id] || typeof q[id] !== 'object') continue;
    const i = CHAPTER[id].i;
    if (q[id].done) done = Math.max(done, i); else open = Math.max(open, i);
  }
  const i = open > done ? open : done;
  if (i >= 0) return CHAPTER_LIST[i];
  const c = typeof chapter === 'string' ? (Object.hasOwn(CHAPTER, chapter) ? chapter : LEGACY[chapter]) : null;
  return (c && Object.hasOwn(CHAPTER, c) && CHAPTER[c]) || CHAPTER_LIST[0];
}
