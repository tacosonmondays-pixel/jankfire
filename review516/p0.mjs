import { mk, snap } from './h.mjs';
const { room, human } = mk('bots');
console.log('map', room.cfg.map);
const p = human('p'); const b = room.addBot({});
p.pos = [0, 0.1, 0]; p.spawnT = 0; p.w = 'ar'; b.pos = [0, 0.1, -6];
room.handle(p, { t: 'hit', to: b.id, w: 'ar', n: 1, h: 1, d: [0, 0, -1] });
console.log('bot hp', b.hp);
process.exit(0);
