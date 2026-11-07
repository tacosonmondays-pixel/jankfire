// Gifts from the management: free containers for every account, given once each. A new gift is one line here.
// id: recorded in the account's inv.gifts when claimed (so never twice). rolls: containers by kind (shared/cosmetics.js
// CONTAINERS). until: after this, nobody new can claim it (accounts claim on their next login / visit while it runs).
export const GIFTS = [
  { id: 'g20261107', title: 'THE MANAGEMENT FEELS GENEROUS', rolls: { crate: 30, bag: 25, box: 70 }, until: '2026-12-07T00:00:00Z' },
];
export const GIFT_IDS = new Set(GIFTS.map((g) => g.id));
export function activeGifts(now = Date.now()) { return GIFTS.filter((g) => !g.until || now < Date.parse(g.until)); }
// the ones this account hasn't had yet. inv.gifts holds the ids it has
export function giftsDue(inv, now = Date.now()) {
  const had = inv && Array.isArray(inv.gifts) ? inv.gifts : [];
  return activeGifts(now).filter((g) => !had.includes(g.id));
}
// the most containers one batch open takes (OPEN ALL asks for min(owned, this))
export const ROLL_BATCH_MAX = 100;
