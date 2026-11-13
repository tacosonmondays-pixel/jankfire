// BOARD GAME NIGHT: THE KITCHEN TABLE's board graph (docs/party/DESIGN.md 2). a 36-space main loop round the edge of an
// 11 x 9 grid (clockwise from THE BOX LID, top left) and THE CREASE: 7 spaces down the fold in the middle, from fork A
// (top middle) to fork B (bottom middle). spaces: { id, k, p: [x, z], next: [ids], plate? }. next[0] is the loop,
// next[1] the crease. 6 plates are where the bakery can sit (main loop only). browser-safe, shared.
const LOOP = 'L c f c j c s c f c j c f c j c c s f c j c f c c j f c c s j f c c j c'.split(' ');
const PLATES = [3, 9, 15, 21, 27, 33];
const CREASE = 'p j p c p f p'.split(' ');
export const FORK_A = 5, FORK_B = 23, CREASE0 = 36;

function loopPos(i) { // grid cell of loop space i
  if (i <= 10) return [i, 0];
  if (i <= 18) return [10, i - 10];
  if (i <= 28) return [10 - (i - 18), 8];
  return [0, 8 - (i - 28)];
}
export const BOARD = [];
for (let i = 0; i < 36; i++) {
  const [x, y] = loopPos(i);
  BOARD.push({ id: i, k: LOOP[i], p: [x - 5, y - 4], next: [(i + 1) % 36], prev: [(i + 35) % 36], ...(PLATES.includes(i) ? { plate: 1 } : {}) });
}
for (let j = 0; j < CREASE.length; j++) {
  const id = CREASE0 + j;
  BOARD.push({ id, k: CREASE[j], p: [0, j + 1 - 4], next: [j === CREASE.length - 1 ? FORK_B : id + 1], prev: [j ? id - 1 : FORK_A], crease: 1 });
}
BOARD[FORK_A].next.push(CREASE0); // fork A: LOOP or CREASE
BOARD[FORK_B].prev.push(CREASE0 + CREASE.length - 1); // fork B only joins the paths back up
export const PLATE_IDS = PLATES.slice();
export const LID = 0;
export const N_SPACES = BOARD.length;
export const isSpace = (id) => Number.isInteger(id) && id >= 0 && id < BOARD.length;
// every space 1..n steps ahead of `from` (any branch): the wet floor sign's reach
export function aheadSet(from, n) {
  const out = new Set();
  let front = [from];
  for (let s = 0; s < n; s++) {
    const nx = [];
    for (const id of front) for (const t of BOARD[id].next) { if (!out.has(t)) { out.add(t); nx.push(t); } }
    front = nx;
  }
  out.delete(from);
  return out;
}
// loop distance between two main-loop spaces (either way round): the bakery hops at least BGN.bakeryMin away
export const loopDist = (a, b) => { const d = Math.abs(a - b) % 36; return Math.min(d, 36 - d); };
