// End-of-match medals (server awards them in server/match.js, the end screen draws them). Deadpan corporate voice.
// c = medal colour, g = the glyph on it
export const MEDALS = {
  first: { name: 'FIRST BLOOD', desc: 'opened the meeting with a kill', c: '#ff3b5c', g: '1' },
  untouch: { name: 'UNTOUCHABLE', desc: '3+ kills and zero deaths. legally immortal', c: '#4fd8ff', g: '∅' },
  hs: { name: 'HEAD OF HR', desc: '3+ headshot kills', c: '#ffe14d', g: '◎' },
  multi2: { name: 'TWO FOR ONE', desc: 'a double kill', c: '#ff9a3c', g: '×2' },
  multi3: { name: 'BULK DISCOUNT', desc: '3+ kills in 8 seconds', c: '#ff4fd8', g: '×3' },
  streak: { name: 'ON A TEAR', desc: '5 kills without dying', c: '#b07dff', g: '5' },
  fast: { name: 'OVER THE LIMIT', desc: 'a kill at 200+ km/h', c: '#7dff4f', g: '»' },
  far: { name: 'LONG DISTANCE CALL', desc: 'a kill from 60 m+', c: '#4fffb0', g: '⌖' },
  void: { name: 'WASTE DISPOSAL', desc: 'knocked someone into the void', c: '#9a7dff', g: '▼' },
  revenge: { name: 'FILED A COMPLAINT', desc: 'killed whoever killed you', c: '#ff6a4f', g: '!' },
  melee: { name: 'HANDS-ON MANAGER', desc: '3+ melee kills', c: '#e0a060', g: '✊' },
  feeder: { name: 'ORGAN DONOR', desc: 'died the most. your organs have been leased', c: '#c86a7a', g: '♥' },
  mvp: { name: 'EMPLOYEE OF THE MONTH', desc: 'top score in the lobby', c: '#ffd21a', g: '★' },
  pacifist: { name: 'CONSCIENTIOUS OBJECTOR', desc: 'no kills, no deaths. what were you doing', c: '#a8a8b0', g: '☮' },
};
