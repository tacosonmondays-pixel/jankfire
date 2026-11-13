// Card Deck: the numbers behind the thrown cards' looks, and the tiny pool they live in (no three.js here, so node tests can
// load it). all of this is drawing only: the server's card (WEAPONS.card: r, speed, damage) is never read or changed here.

// drawn ~1.6x the old 0.18 x 0.26 card (the size the 0.26 hit radius was picked for), with a little paper thickness
export const CARD_W = 0.29, CARD_H = 0.42, CARD_T = 0.014, CARD_R = 0.03; // (R: the rounded corners)
// a suit's glow (spades and clubs are black ink, which can't glow: they get the game's neon instead)
export const GLOW = { s: 0x4fd8ff, c: 0x39ff14, h: 0xff3050, d: 0xffe14d, j: 0xb07dff };
export const SUIT_KEYS = ['s', 'c', 'h', 'd', 'j'];
// pool caps: cards in flight, cards stuck in walls, suit symbols puffing off a hit. Potato keeps fewer stuck and for less time
export const CAPS = { fly: 72, stuck: 36, stuckPotato: 12, puff: 48 };
export const STICK_S = 5, STICK_S_POTATO = 2.5; // how long a stuck card stays (s), then it pops away
export const TRAIL = { len: 7, w: 0.2, lenPotato: 3, wPotato: 0.1 }; // the glowing trail behind a card in flight (m)

// a fixed-size pool: take() hands out a free item, makes a new one while under the cap, and once full recycles the oldest
// one in use (onSteal tidies it first). give() puts one back. items are made once and reused: nothing is made per shot
export class Pool {
  constructor(cap, make, onSteal = null) { this.cap = cap; this.make = make; this.onSteal = onSteal; this.free = []; this.live = []; this.made = 0; }
  take() {
    let it = this.free.pop();
    if (!it && this.made < this.cap) it = this.make(this.made++);
    if (!it) { it = this.live.shift(); if (this.onSteal) this.onSteal(it); } // full: the oldest goes
    this.live.push(it);
    return it;
  }
  give(it) {
    const i = this.live.indexOf(it);
    if (i < 0) return false;
    this.live.splice(i, 1); this.free.push(it);
    return true;
  }
  // over a (smaller) cap, e.g. Potato's: hand back the oldest until it fits
  trim(cap, onDrop) { while (this.live.length > cap) { const it = this.live[0]; if (onDrop) onDrop(it); this.give(it); } }
  clear(onDrop) { while (this.live.length) { const it = this.live[0]; if (onDrop) onDrop(it); this.give(it); } }
}

// which suit a freshly thrown card belongs to: the owner's last played card ('fx' k:'card' arrives just before its 'ps'
// messages, in the same server tick). nothing recent (a bot's flick, a late joiner): spades
export function suitFor(last, owner, now, win = 400) {
  const l = last.get(owner);
  return l && now - l.t < win ? l.suit : 's';
}
