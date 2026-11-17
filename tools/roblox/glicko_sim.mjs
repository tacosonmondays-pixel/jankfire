// the ranked rating maths (Glicko-2 with a team composite, roblox/docs/MATCHMAKING.md section 4) in JS, to tune the
// constants: 5 placement wins from the start, settled players, and 2,000 players of known skill over 60 matches.
// run: node tools/roblox/glicko_sim.mjs (the Luau is src/shared/Ranked.luau; keep the two in step)
const Q = 173.7178, TAU = 0.5, EPS = 1e-6;
const g = (phi) => 1 / Math.sqrt(1 + 3 * phi * phi / (Math.PI * Math.PI));
function update(p, oppMu, oppPhi, teamMu, s, floor = 80, ceil = 350) {
  let mu = (p.r - 1500) / Q, phi = p.rd / Q, sig = p.vol;
  const tm = (teamMu - 1500) / Q, om = (oppMu - 1500) / Q, op = oppPhi / Q;
  const gg = g(op), E = 1 / (1 + Math.exp(-gg * (tm - om)));
  const v = 1 / (gg * gg * E * (1 - E));
  const delta = v * gg * (s - E);
  const a = Math.log(sig * sig);
  const f = (x) => { const ex = Math.exp(x); return ex * (delta * delta - phi * phi - v - ex) / (2 * (phi * phi + v + ex) ** 2) - (x - a) / (TAU * TAU); };
  let A = a, B;
  if (delta * delta > phi * phi + v) B = Math.log(delta * delta - phi * phi - v); else { let k = 1; while (f(a - k * TAU) < 0) k++; B = a - k * TAU; }
  let fA = f(A), fB = f(B);
  for (let i = 0; i < 100 && Math.abs(B - A) > EPS; i++) { const C = A + (A - B) * fA / (fB - fA), fC = f(C); if (fC * fB <= 0) { A = B; fA = fB; } else fA /= 2; B = C; fB = fC; }
  const sig2 = Math.exp(A / 2);
  const phiS = Math.sqrt(phi * phi + sig2 * sig2);
  let phi2 = 1 / Math.sqrt(1 / (phiS * phiS) + 1 / v);
  const mu2 = mu + phi2 * phi2 * gg * (s - E);
  phi2 = Math.min(ceil / Q, Math.max(floor / Q, phi2));
  return { r: 1500 + Q * mu2, rd: Q * phi2, vol: sig2 };
}
for (const rd0 of [350, 250, 200]) {
  let p = { r: 1500, rd: rd0, vol: 0.06 }; const seq = [];
  for (let i = 0; i < 5; i++) { const n = update(p, 1500, 80, p.r, 1); seq.push(Math.round(n.r - p.r)); p = n; }
  console.log('rd0', rd0, '5 wins vs 1500/80 ->', Math.round(p.r), 'rd', Math.round(p.rd), 'steps', seq.join(','));
  p = { r: 1500, rd: rd0, vol: 0.06 }; const s2 = [];
  for (let i = 0; i < 5; i++) { const n = update(p, p.r, 300, p.r, i % 2 ? 0 : 1); s2.push(Math.round(n.r - p.r)); p = n; }
  console.log('   alt W/L vs fellow new players ->', Math.round(p.r), 'rd', Math.round(p.rd), s2.join(','));
}
// settled player 1600 rd 60 beats 1600 rd 60
let s = { r: 1600, rd: 60, vol: 0.06 }; let n = update(s, 1600, 60, 1600, 1); console.log('settled even win', Math.round(n.r - 1600), 'rd', n.rd.toFixed(1));
n = update(s, 1800, 60, 1600, 1); console.log('settled upset win vs +200', Math.round(n.r - 1600));
n = update(s, 1400, 60, 1600, 1); console.log('settled win vs -200', Math.round(n.r - 1600));
n = update(s, 1400, 60, 1600, 0); console.log('settled loss vs -200', Math.round(n.r - 1600));
// population sim: true skills N(1500,250), 30 matches each vs random-ish nearby, see spread
function randn() { return Math.sqrt(-2 * Math.log(Math.random())) * Math.cos(2 * Math.PI * Math.random()); }
const N = 2000, pl = [];
for (let i = 0; i < N; i++) pl.push({ t: 1500 + 250 * randn(), r: 1500, rd: 250, vol: 0.06 });
for (let round = 0; round < 60; round++) {
  pl.sort((a, b) => a.r - b.r);
  for (let i = 0; i + 1 < N; i += 2) {
    const a = pl[i], b = pl[i + 1];
    const pa = 1 / (1 + 10 ** ((b.t - a.t) / 400)); // true win chance (single match, first to 5 sharpens it)
    const sa = Math.random() < pa ? 1 : 0;
    const na = update(a, b.r, b.rd, a.r, sa), nb = update(b, a.r, a.rd, b.r, 1 - sa);
    Object.assign(a, na); Object.assign(b, nb);
  }
}
const rs = pl.map((p) => p.r).sort((a, b) => a - b);
console.log('after 60: pctiles', [0.05, 0.25, 0.5, 0.75, 0.95, 0.99].map((q) => Math.round(rs[Math.floor(q * N)])).join(' '), 'avg rd', Math.round(pl.reduce((a, p) => a + p.rd, 0) / N));
