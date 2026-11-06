// Mode stuff you can see: bomb sites (A / B markers you see through walls), the bomb, who carries it,
// dropped tags, the team score bar and the objective line on the HUD.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAPS } from '/shared/map.js';
import { TEAMS, GAMES, BOMB, siteAt, canDefuse } from '/shared/modes.js';
import { M } from './models.js';
import { K } from './keys.js';

const $ = (id) => document.getElementById(id);
let sites = [], bomb = null, carrierMark = null, mapId = null;
const tags = new Map();

function textSprite(text, color, px = 0.05) {
  const c = document.createElement('canvas'); c.width = 64; c.height = 64;
  const x = c.getContext('2d');
  x.fillStyle = 'rgba(0,0,0,0.55)'; x.beginPath(); x.arc(32, 32, 28, 0, Math.PI * 2); x.fill();
  x.strokeStyle = color; x.lineWidth = 5; x.stroke();
  x.fillStyle = color; x.font = 'bold 38px "Comic Neue", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(text, 32, 34);
  const tex = new THREE.CanvasTexture(c); tex.magFilter = THREE.NearestFilter;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, sizeAttenuation: false, transparent: true, fog: false }));
  s.scale.set(px, px, 1);
  s.renderOrder = 20;
  return s;
}

export function setupObjectives(id) {
  if (id === mapId) return;
  mapId = id;
  for (const s of sites) G.scene.remove(s.sprite, s.ring);
  sites = [];
  const map = MAPS[id];
  for (const st of (map && map.sites) || []) {
    const cx = (st.min[0] + st.max[0]) / 2, cz = (st.min[2] + st.max[2]) / 2;
    const sprite = textSprite(st.id, '#ffe14d');
    sprite.position.set(cx, st.min[1] + 4.5, cz);
    // painted outline on the floor so you know when you're in
    const w = st.max[0] - st.min[0], d = st.max[2] - st.min[2];
    const ring = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(w, 0.05, d)), new THREE.LineBasicMaterial({ color: 0xffe14d, fog: false }));
    ring.position.set(cx, st.min[1] + 0.06, cz);
    G.scene.add(sprite, ring);
    sites.push({ id: st.id, sprite, ring });
  }
}

function bombMesh() {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.26, 0.32), M(0x3a3f2a)));
  const dyn = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.3, 0.12), M(0xc02020));
  for (const x of [-0.16, 0, 0.16]) { const d2 = dyn.clone(); d2.position.set(x, 0.05, 0); g.add(d2); }
  const light = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.08, 0.08), M(0xff2020, true));
  light.position.set(0, 0.24, 0.1);
  g.add(light);
  g.userData.light = light;
  const mark = textSprite('!', '#ff3030', 0.04);
  mark.position.y = 1.6;
  g.add(mark);
  return g;
}

export function addTag(id, p, team) {
  const g = new THREE.Group();
  const col = new THREE.Color(TEAMS[team] ? TEAMS[team].color : '#ffffff').getHex();
  const plate = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.5, 0.05), M(col, true));
  const edge = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.56, 0.03), M(0xffffff, true));
  g.add(edge, plate);
  g.position.set(p[0], p[1], p[2]);
  g.userData.base = p[1];
  G.scene.add(g);
  tags.set(id, g);
}
export function removeTag(id) { const g = tags.get(id); if (g) { G.scene.remove(g); tags.delete(id); } }
export function clearTags() { for (const g of tags.values()) G.scene.remove(g); tags.clear(); }

// am I in a spot where F plants / defuses?
export function canUse(r, myPos) {
  const b = r && r.bomb;
  if (!b || r.game !== 'bomb' || b.ph === 'done') return false;
  if (b.ph === 'live' && b.carrier === G.myId) return !!siteAt(MAPS[G.cfg.map], myPos);
  // the server's rule (a cylinder: a bomb up on a prop is defused from the floor), so F never inspects where bots defuse
  if (b.ph === 'planted' && G.myTeam && G.myTeam !== b.att && b.p) return canDefuse(myPos, b.p);
  return false;
}

const fmt = (ms) => { const s = Math.ceil(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };

export function updateObjectives(dt, now, r, myPos) {
  const game = r && r.game;
  const isBomb = game === 'bomb' && r.bomb;
  for (const s of sites) { s.sprite.visible = !!isBomb; s.ring.visible = !!isBomb; }
  // the bomb on the floor (dropped or planted)
  const bp = isBomb && (r.bomb.p || r.bomb.drop);
  if (bp) {
    if (!bomb) { bomb = bombMesh(); G.scene.add(bomb); }
    bomb.visible = true;
    bomb.position.set(bp[0], bp[1] + 0.13, bp[2]);
    const planted = r.bomb.ph === 'planted';
    const rate = planted ? 2 + (1 - r.bomb.left / (BOMB.fuse * 1000)) * 10 : 1;
    bomb.userData.light.visible = Math.sin(now * 0.006 * rate) > 0;
    bomb.rotation.y = planted ? 0 : now * 0.002;
  } else if (bomb) bomb.visible = false;
  // who has it (only your team sees, if you're attacking)
  const car = isBomb && r.bomb.carrier && r.bomb.carrier !== G.myId && G.myTeam === r.bomb.att ? G.remotes.get(r.bomb.carrier) : null;
  if (car) {
    if (!carrierMark) { carrierMark = textSprite('B', '#ff3030', 0.035); G.scene.add(carrierMark); }
    carrierMark.visible = true;
    carrierMark.position.set(car.pos[0], car.pos[1] + 3.3, car.pos[2]);
  } else if (carrierMark) carrierMark.visible = false;
  for (const g of tags.values()) { g.rotation.y += dt * 3; g.position.y = g.userData.base + Math.sin(now * 0.004 + g.id) * 0.15; }

  // ---- HUD: team score + objective line
  const bar = $('teamBar'), obj = $('objective');
  const teams = r && GAMES[game] && GAMES[game].teams;
  bar.classList.toggle('hidden', !teams);
  if (teams) {
    const sc = isBomb ? r.bomb.wins : r.sc || [0, 0];
    bar.children[0].textContent = `${TEAMS[1].name} ${sc[0]}`;
    bar.children[2].textContent = `${sc[1]} ${TEAMS[2].name}`;
    bar.children[0].classList.toggle('mine', G.myTeam === 1);
    bar.children[2].classList.toggle('mine', G.myTeam === 2);
    bar.children[1].textContent = isBomb ? `ROUND ${r.bomb.n} · ${G.myTeam === r.bomb.att ? 'ATTACK' : 'DEFEND'}` : `${GAMES[game].name.toUpperCase()} · to ${r.target}${r.over ? '' : ' · ' + fmt(r.left)}`;
  }
  let line = '';
  if (isBomb) {
    const b = r.bomb, att = G.myTeam === b.att;
    if (b.ph === 'planted') line = `BOMB PLANTED AT ${b.site} · ${fmt(b.left)}${att ? ' · guard it' : ` · DEFUSE IT (hold ${K.label('use')} at the bomb)`}`;
    else if (b.ph === 'done') line = '';
    else if (b.carrier === G.myId) line = `YOU HAVE THE BOMB · get to A or B · hold ${K.label('use')} to plant · ${fmt(b.left)}`;
    else if (b.drop) line = att ? `BOMB DROPPED · go pick it up · ${fmt(b.left)}` : `they dropped the bomb · ${fmt(b.left)}`;
    else line = att ? `plant the bomb at A or B · ${fmt(b.left)}` : `stop them planting at A or B · ${fmt(b.left)}`;
    if (b.act && b.act.by !== G.myId) line += b.act.k === 'plant' ? ' · THEY ARE PLANTING' : ' · DEFUSING!';
  } else if (game === 'tags' && teams) line = 'grab enemy tags to score · grab your team\'s to deny';
  if (obj.textContent !== line) obj.textContent = line;
}
