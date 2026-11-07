// Bot flair: their outfits (server/botlook.js), their chat (server/botlines.js) and a spray on the wall after a big play.
// Chat is rate-limited per room (one bot line every ~6-8 s at most) and per bot, with a chance roll and a personality on
// top, so it reads like people and never floods. Bot lines go out as normal { t: 'chat', id } messages: clients that
// turned "bot chatter" off drop them (public/js/main.js).
import { botLook, botSkins, hashStr, rng } from './botlook.js';
import { LINES, PERSONAS, PERSONA_IDS, REPLY } from './botlines.js';
import { WEAPONS } from '../shared/weapons.js';
import { COSMETICS, SPRAY } from '../shared/cosmetics.js';
import { raycast, PH } from '../shared/physics.js';

// test knobs come from server.js (JF_BOTCHAT_*): gap = ms between bot lines in a room, all = skip the chance roll
export const BOTCHAT = { gap: [6000, 8000], botCd: 20000, all: false, delay: [500, 1600] };
const GOOFY = new Set(['chicken', 'bowling', 'banana', 'tennis', 'cart', 'marbles', 'cig', 'blower', 'cards', 'popper', 'reverse', 'duck', 'snowball', 'bread', 'slipper', 'slapper', 'scales', 'water', 'remote', 'lasso', 'shredder', 'bloodcross', 'nailgun']);
const DUMB = new Set(['void', 'car', 'carboom', 'lava', 'duck', 'cough', 'tbag', 'frag', 'pit', 'shredder']);
const SPRAYS = Object.keys(COSMETICS.spray);
const BIG = new Set(['multi', 'clutch', 'noscope', 'far', 'revenge']);
const pick = (a) => a[Math.floor(Math.random() * a.length)];
const between = ([a, b]) => a + Math.random() * (b - a);
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const r2 = (x) => Math.round(x * 100) / 100;
const plain = (n) => String(n || '').replace(/ \[bot\]$/, '');

export function installBotFlair(Room, knobs = {}) {
  Object.assign(BOTCHAT, knobs);
  Object.assign(Room.prototype, {
    // a fresh bot's look, weapon skins and personality. same name in the same room = same bot
    botDress(b) {
      this.botSalt ??= (Math.random() * 2 ** 31) | 0;
      const seed = (hashStr(b.name) ^ this.botSalt) >>> 0, { look, preset } = botLook(seed);
      b.look = look; b.preset = preset;
      b.skins = botSkins(seed, Object.keys(WEAPONS));
      b.persona = preset === 'corpo' ? 'corpo' : PERSONA_IDS[Math.floor(rng(seed ^ 0x9e3779b9)() * PERSONA_IDS.length)];
    },
    // one chat line from a bot, if the dice, its cooldown and the room's cooldown all say yes. true = it'll say it
    botSay(b, ev, vars = {}, chance = 1, reply = false) {
      const n = Date.now(), pool = LINES[ev];
      if (!pool || !b || !b.isBot || (b.ai && b.ai.dummy) || (this.zm && !b.zmh) || this.players.get(b.id) !== b) return false; // zombies: only the squad's bots talk
      const per = PERSONAS[b.persona] || PERSONAS.polite;
      if (!BOTCHAT.all && Math.random() > chance * per.talk) return false;
      // the room's gap (6-8 s). an answer to a person only needs 4 s since the last bot line, so bots don't ignore you
      if (reply ? n - (this.bcLast || 0) < Math.min(4000, BOTCHAT.gap[0]) : n < (this.bcNext || 0) || n < (b.bcT || 0)) return false;
      const list = pool[b.persona] && Math.random() < 0.55 ? pool[b.persona] : pool.any;
      const m = pick(list).replace(/\{v\}/g, plain(vars.v) || 'you').replace(/\{w\}/g, vars.w || 'that');
      this.bcNext = n + between(BOTCHAT.gap); this.bcLast = n; b.bcT = n + BOTCHAT.botCd;
      setTimeout(() => { try { if (this.players.get(b.id) === b) this.broadcast({ t: 'chat', id: b.id, m }); } catch (e) { console.error('botchat', e); } }, between(BOTCHAT.delay)); // a beat later, like typing
      return true;
    },
    // a kill happened (server.js kill()): bots brag about cool ones, and sometimes cope when they die
    botBrag(killer, t, w, via, ctx = {}) {
      if (this.zm || this.mode === 'training') return;
      const wid = via || w, wd = WEAPONS[wid];
      if (!killer || killer === t) { // nobody to blame: the void, a car, lava, their own knees
        if (t.isBot && (DUMB.has(wid) || killer === t)) this.botSay(t, 'dumb', {}, 0.45);
        return;
      }
      if (killer.isBot && !(killer.ai && killer.ai.dummy)) {
        const n = Date.now(), d = dist3(killer.pos, t.pos);
        killer.bcKills = (killer.bcKills || []).filter((x) => n - x < 4500); killer.bcKills.push(n);
        const air = t.isBot ? t.onGround === false : !raycast([t.pos[0], t.pos[1] + 0.2, t.pos[2]], [0, -1, 0], 1.6, this.boxes);
        let ev = 'kill', ch = 0.08;
        if (ctx.clutch) ev = 'clutch', ch = 0.95;
        else if (killer.bcKills.length >= 3 || (killer.bcKills.length === 2 && !t.isBot)) ev = 'multi', ch = 0.6; // two bots in a crowd isn't news: three is, or two with a person in it
        else if (ctx.rev) ev = 'revenge', ch = 0.5;
        else if (wd && wd.slot === 'melee') ev = 'melee', ch = 0.35;
        else if (wid === 'sniper' && !t.isBot) ev = 'noscope', ch = 0.55; // bots never scope in: every bot sniper kill is a no-scope
        else if (d > 45 && w !== 'void' && wd && (wd.slot === 'primary' || wd.slot === 'secondary')) ev = 'far', ch = 0.45; // (not someone knocked flying off the map)
        else if (t.g) ev = 'grapple', ch = 0.5;
        else if (air) ev = 'air', ch = 0.35;
        else if (GOOFY.has(wid)) ev = 'goofy', ch = 0.3;
        else if (t.lastHs) ev = 'head', ch = 0.2;
        if (t.isBot) ch *= BIG.has(ev) ? 0.5 : 0.25; // bots roasting bots: less of it, humans are the audience (and replies need the slot)
        if (this.botSay(killer, ev, { v: t.name, w: wd ? wd.name.toLowerCase() : wid }, ch) && BIG.has(ev) && Math.random() < 0.6) setTimeout(() => { try { this.botSpray(killer); } catch (e) { console.error('botspray', e); } }, 700);
      }
      if (t.isBot && !killer.isBot) this.botSay(t, 'died', {}, 0.1 * ((PERSONAS[t.persona] || {}).salt || 1));
    },
    // Plant & Defuse: this kill wiped their team and the killer is the last one standing on theirs
    botClutch(k, t) {
      if (this.game !== 'bomb' || !k || k === t || !k.isBot || !k.team || k.team === t.team) return false;
      const alive = this.fighters().filter((p) => p.alive);
      return !alive.some((p) => p.team === t.team) && alive.filter((p) => p.team === k.team).length === 1 && this.fighters().filter((p) => p.team === k.team).length >= 2;
    },
    // a human said something: a bot might answer (the one that last killed them, else one they named, else anyone)
    botReply(p, text) {
      if (p.isBot || this.zm) return;
      const hit = REPLY.find(([re]) => re.test(text));
      const bots = [...this.players.values()].filter((b) => b.isBot && !(b.ai && b.ai.dummy));
      if (!bots.length) return;
      const low = text.toLowerCase(), named = bots.find((b) => low.includes(plain(b.name).toLowerCase()));
      if (!hit && !named) return;
      const chatty = bots.filter((x) => x.persona !== 'silent');
      const b = (p.lastKiller && bots.find((x) => x.id === p.lastKiller && hit && hit[1] !== 'hi')) || named || pick(chatty.length ? chatty : bots);
      this.botSay(b, hit ? hit[1] : 'hi', { v: p.name }, hit ? 0.7 : 0.45, true);
    },
    // a big play: paint a spray on the wall in front (or the floor), like a player would with Z
    botSpray(b) {
      const n = Date.now();
      if (!b || !b.alive || n - (b.sprayT || 0) < SPRAY.cd * 1000 || this.players.get(b.id) !== b) return;
      const e = [b.pos[0], b.pos[1] + PH.eye, b.pos[2]], y = b.yaw || 0;
      const h = raycast(e, [-Math.sin(y), 0, -Math.cos(y)], SPRAY.reach, this.boxes) || raycast(e, [0, -1, 0], SPRAY.reach, this.boxes);
      if (!h || !h.normal || !h.box) return;
      const nm = h.normal.map((v) => Math.round(v)), k = nm.findIndex((v) => v !== 0);
      if (k < 0 || nm.filter((v) => v !== 0).length !== 1) return;
      const pt = h.point.map(r2);
      pt[k] = nm[k] > 0 ? h.box.max[k] : h.box.min[k];
      b.sprayT = n;
      if (this.sprayMap !== this.cfg.map) { this.sprays.clear(); this.sprayMap = this.cfg.map; }
      const TAU = Math.PI * 2, s = { id: b.id, s: pick(SPRAYS), p: pt, n: nm, r: k === 1 ? r2(((y % TAU) + TAU) % TAU) : 0 };
      this.sprays.delete(b.id); this.sprays.set(b.id, s);
      while (this.sprays.size > SPRAY.max) this.sprays.delete(this.sprays.keys().next().value);
      this.broadcast({ t: 'spray', ...s });
    },
  });
}
