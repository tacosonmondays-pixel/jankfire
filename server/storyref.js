// story rooms (OVERDUE): the game's real rules for story fights. shared/story/refsys.js runs one in the story's web
// worker (the solo referee); co-op will run the same thing here. what a story room changes from a match:
//   - no rounds, votes or auto bots: the story spawns who's there (room.storySpawn)
//   - enemies have a story kind: sk = { kind, max, side, tags, npc, boss }. the room's HP stays 0..100 like everyone
//     else's (all the weapon rules assume it), the kind's own pool is scaled onto it, and the real numbers go out
//   - sides instead of teams: the same side doesn't hurt or hunt itself (you and your allies are side 'you')
//   - enemies stay down when they die (refsys clears the body); you respawn as usual (the Machine dispenses you)
//   - every hit and kill is reported through room.onStory(ev) with the real numbers
import { WEAPONS } from '../shared/weapons.js';

export const STORY_SIDE = 'you';
const sideOf = (p) => (p.sk ? p.sk.side || 'enemy' : STORY_SIDE);

export function installStoryRef(Room) {
  const P = Room.prototype;
  const damage0 = P.damage, kill0 = P.kill, friendly0 = P.friendly;
  P.damage = function (t, amt, attacker, w, hs, from) {
    if (this.mode !== 'story') return damage0.call(this, t, amt, attacker, w, hs, from);
    const sk = t.sk, k = sk ? 100 / sk.max : 1; // a 400 HP brute takes a quarter of each hit off its 100
    const hp0 = t.hp, ok = damage0.call(this, t, amt > 0 ? amt * k : amt, attacker, w, hs, from);
    if (ok && t.hp < hp0 && this.onStory) this.onStory({ type: 'hit', t, by: attacker, w, dmg: (hp0 - Math.max(0, t.hp)) / k, head: !!hs });
    return ok;
  };
  P.kill = function (t, attacker, w) {
    const was = t.alive, r = kill0.call(this, t, attacker, w);
    if (this.mode === 'story' && was && !t.alive) {
      if (t.sk) t.respawnAt = t.minRespawnAt = Infinity; // story enemies stay down
      if (this.onStory) this.onStory({ type: 'kill', t, by: attacker, w });
    }
    return r;
  };
  P.friendly = function (a, b) {
    if (this.mode !== 'story') return friendly0.call(this, a, b);
    return !!a && !!b && a !== b && sideOf(a) === sideOf(b);
  };
  // a story enemy: def { kind, name, hp, w, side, tags, npc, color, skins } at pos. returns the room player
  P.storySpawn = function (def, pos) {
    const b = this.addBot({ pos });
    b.sk = { kind: def.kind, max: Math.max(1, def.hp || 100), side: def.side || 'enemy', tags: def.tags || [], npc: def.npc || '', boss: !!def.boss };
    if (def.name) b.name = def.name;
    if (def.w && Object.hasOwn(WEAPONS, def.w)) { b.w = def.w; b.ai.ammo = WEAPONS[def.w].mag || 1; }
    if (def.color) b.color = def.color;
    if (def.skins) b.skins = def.skins;
    this.sendLoadout(b);
    this.broadcast({ t: 'pj', ...this.info(b) }); // (again: the story name / gun / look replace the bot's own)
    return b;
  };
  P.storyDespawn = function (b) {
    if (b && this.players.get(b.id) === b) this.remove(b); // (its projectiles, ropes etc. go with it)
  };
}
