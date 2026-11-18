// the web's models.js, with buildCharacter's joints given names (so the dump can tell which piece moves with which)
export * from 'file:///C:/Users/soup2/jankfire-port/public/js/models.js';
import { buildCharacter as bc } from 'file:///C:/Users/soup2/jankfire-port/public/js/models.js';
export function buildCharacter(c, l) {
  const ch = bc(c, l);
  for (const k of ['root', 'body', 'head', 'arm', 'armL', 'legL', 'legR', 'kneeL', 'kneeR', 'slot']) if (ch[k]) ch[k].name = k;
  return ch;
}
