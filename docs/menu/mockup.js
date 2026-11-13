// HUB / LOBBY mockups, drawn inside the real game page (its fonts, mode art, map thumbs, characters).
// window.__mock(view): 'hub' | 'pub' | 'priv' | 'friends'
import * as THREE from 'three';
import { buildCharacter } from '/js/models.js';
import { modeThumb } from '/js/modeart.js';
import { DEFAULT_LOOK } from '/shared/looks.js';

const css = `
#mk{position:fixed;inset:0;z-index:9999;font-family:var(--font);color:#fff;pointer-events:none}
#mk *{box-sizing:border-box}
#mk .pan{background:rgba(18,8,24,.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:12px 14px}
#mk .tag{display:inline-block;background:#ff4fd8;color:#120818;font-weight:900;letter-spacing:3px;font-size:13px;padding:2px 10px;transform:rotate(-2deg);box-shadow:3px 3px 0 #120818}
#mk .ybtn{background:#ffe14d;color:#120818;border:4px solid #000;box-shadow:6px 6px 0 #ff4fd8;font:900 30px var(--font);letter-spacing:2px;padding:10px 26px;transform:rotate(-1.5deg)}
#mk .wbtn{background:#fff;color:#120818;border:3px solid #000;box-shadow:4px 4px 0 #ff4fd8;font:700 15px var(--font);padding:5px 12px}
#mk .pbar .wbtn,#mk .pbar .rbtn{font-size:13px;padding:4px 9px}
#mk .rbtn{background:#ff3030;color:#fff;border:3px solid #000;box-shadow:4px 4px 0 #120818;font:700 15px var(--font);padding:5px 12px}
#mk .title{font:900 52px var(--font);color:#ffe14d;text-shadow:4px 4px 0 #ff00dc,7px 7px 0 #120818;letter-spacing:2px;transform:rotate(-1deg)}
#mk .cards{position:absolute;right:28px;top:168px;width:520px;display:grid;grid-template-columns:1fr 1fr;gap:16px}
#mk .card{position:relative;height:118px;background:rgba(18,8,24,.94);border:4px solid var(--c);box-shadow:7px 7px 0 #120818;display:flex;gap:10px;padding:8px;transform:rotate(var(--r,0deg))}
#mk .card .mthumb{width:112px;height:94px;flex:none;border:3px solid #000;overflow:hidden;background:var(--b)}
#mk .card .mthumb img{width:100%;height:100%;object-fit:cover;image-rendering:pixelated}
#mk .card b{font-size:21px;color:var(--c);line-height:1;display:block;margin-top:4px}
#mk .card span{font-size:12px;color:#e8dcef;display:block;margin-top:5px;line-height:1.2}
#mk .card i{position:absolute;right:8px;bottom:6px;font-style:normal;font-size:12px;font-weight:700;color:#7dff4f}
#mk .card .new{position:absolute;right:-8px;top:-12px;background:#7dff4f;color:#120818;font-weight:900;font-size:12px;padding:1px 7px;border:2px solid #000;transform:rotate(6deg)}
#mk .card.soon{opacity:.55;filter:saturate(.4)}
#mk .card.sel{outline:4px solid #ffe14d;outline-offset:3px}
#mk .pbar{position:absolute;left:330px;right:568px;bottom:20px;display:flex;flex-direction:column;gap:8px}
#mk .row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#mk .code{font:900 26px var(--font);letter-spacing:6px;color:#4fd8ff;background:#000;padding:2px 10px;border:2px dashed #4fd8ff}
#mk .nm{position:absolute;transform:translate(-50%,0);text-align:center;font-weight:900;font-size:15px;text-shadow:2px 2px 0 #000;white-space:nowrap}
#mk .nm small{display:block;font-size:11px;color:#ffe14d;font-weight:700}
#mk .nm .rd{display:inline-block;margin-top:3px;background:#7dff4f;color:#120818;font-size:11px;padding:0 6px;border:2px solid #000}
#mk .nm .nr{display:inline-block;margin-top:3px;background:#3a3a44;color:#ccc;font-size:11px;padding:0 6px;border:2px solid #000}
#mk .slot{position:absolute;transform:translate(-50%,0);width:96px;height:150px;border:3px dashed rgba(255,79,216,.6);display:flex;align-items:center;justify-content:center;text-align:center;font-weight:900;color:#ff9ad5;font-size:13px;background:rgba(18,8,24,.4)}
#mk .seg{display:flex;border:3px solid #000;box-shadow:4px 4px 0 #ff4fd8}
#mk .seg div{padding:6px 16px;font-weight:900;font-size:18px;background:#2a1430;color:#aaa}
#mk .seg div.on{background:#ffe14d;color:#120818}
#mk .set{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:2px dashed rgba(255,79,216,.35);font-size:15px}
#mk .set:last-child{border:0}
#mk .set em{font-style:normal;font-weight:900;color:#4fd8ff}
#mk .tog{width:46px;height:22px;border:3px solid #000;background:#7dff4f;position:relative}
#mk .tog:after{content:'';position:absolute;right:2px;top:2px;width:13px;height:12px;background:#120818}
#mk .tog.off{background:#3a3a44}#mk .tog.off:after{left:2px;right:auto;background:#888}
#mk .slider{width:120px;height:10px;background:#3a3a44;border:2px solid #000;position:relative}
#mk .slider b{position:absolute;left:0;top:0;bottom:0;background:#ff4fd8}
#mk .lead{font-size:12px;color:#ffe14d}
#mk .fr{display:flex;align-items:center;gap:8px;padding:7px 4px;border-bottom:2px dashed rgba(79,216,255,.3)}
#mk .dot{width:12px;height:12px;border:2px solid #000;flex:none}
#mk .fr b{font-size:16px;display:block}#mk .fr small{font-size:12px;color:#c8bcd8;display:block}
#mk .fr .sp{flex:1}
#mk .map{border:3px solid #000;width:100%;height:120px;object-fit:cover;display:block}
#mk .tabs{display:flex;gap:6px;margin-bottom:8px}#mk .tabs div{padding:3px 12px;font-weight:900;border:3px solid #000;background:#2a1430;color:#aaa}#mk .tabs div.on{background:#4fd8ff;color:#120818}
#mk input{font:700 15px var(--font);border:3px solid #000;padding:4px 8px;width:170px}
#mk .toast{position:absolute;left:36%;top:18px;transform:translateX(-50%) rotate(-1deg);display:flex;gap:12px;align-items:center}
#mk .note{position:absolute;font:700 13px var(--font);color:#120818;background:#ffe14d;border:2px solid #000;padding:3px 8px;transform:rotate(2deg);box-shadow:3px 3px 0 #000;max-width:230px}
`;
const looks = [
  { color: '#ff4fd8', look: { ...DEFAULT_LOOK, hair: 'mohawk', hairColor: '#ff4fd8', top: 'hoodie', topColor: '#ffe14d', bottom: 'pants', bottomColor: '#2a4a8a', head: 'none' } },
  { color: '#4fd8ff', look: { ...DEFAULT_LOOK, hair: 'long', hairColor: '#d9b45a', top: 'jacket', topColor: '#4fd8ff', bottom: 'skirt', bottomColor: '#1a1a1a', build: 'f', skin: '#c68642' } },
  { color: '#7dff4f', look: { ...DEFAULT_LOOK, hair: 'short', top: 'suit', topColor: '#3a3a44', bottom: 'pants', bottomColor: '#3a3a44', bigHead: 2, skin: '#ffdbac' } },
  { color: '#ffe14d', look: { ...DEFAULT_LOOK, hair: 'spiky', hairColor: '#7dff4f', top: 'tee', topColor: '#ff7a1a', bottom: 'cargo', bottomColor: '#8a5a2b', fat: 2, skin: '#8d5524' } },
];
const NAMES = [['taco', 'LEADER'], ['bigwes', 'lvl 31'], ['soupman', 'lvl 7'], ['grandma_420', 'guest']];

function el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
let ren = null;
// the party stood in a row (CoD style). xs: screen x centres (fraction), returns their screen feet points
function lineup(root, n, cx, gap, scale) {
  const cv = el('canvas'); cv.style.cssText = `position:absolute;left:0;top:0;width:100%;height:100%`;
  root.append(cv);
  const W = innerWidth, H = innerHeight, D = 9;
  ren = new THREE.WebGLRenderer({ canvas: cv, alpha: true, antialias: true }); ren.setSize(W, H, false); ren.setPixelRatio(1);
  const sc = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, W / H, 0.1, 100);
  cam.position.set(0, 1.3, D); cam.lookAt(0, 0.6, 0);
  sc.add(new THREE.HemisphereLight(0xffe8ff, 0x3a2040, 1.7)); const d = new THREE.DirectionalLight(0xffffff, 2.2); d.position.set(2, 4, 5); sc.add(d);
  const half = Math.tan(15 * Math.PI / 180) * D * (W / H), x0 = (cx * 2 - 1) * half;
  const out = [];
  for (let i = 0; i < n; i++) {
    const off = i - (n - 1) / 2, x = x0 + off * gap;
    const g = new THREE.Group(); g.position.set(x, 0, -Math.abs(off) * 0.4);
    const C = buildCharacter(looks[i].color, looks[i].look), ch = C.root; ch.rotation.y = Math.PI + off * -0.22 + (i % 2 ? 0.12 : -0.06);
    if (C.arm) C.arm.rotation.x = -1.35 - (i % 2) * 0.15; if (C.armL) C.armL.rotation.x = -1.4 + (i === 1 ? 0.9 : 0);
    ch.updateMatrixWorld(true); const bx = new THREE.Box3().setFromObject(ch), k = (1.8 * scale) / Math.max(0.5, bx.max.y - bx.min.y); ch.scale.setScalar(k); ch.position.y = -bx.min.y * k;
    g.add(ch);
    const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.56, 0.16, 10), new THREE.MeshLambertMaterial({ color: i === 0 ? 0xffe14d : 0xff4fd8 })); pl.position.y = -0.08; g.add(pl);
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(0.58, 0.58, 0.05, 10), new THREE.MeshLambertMaterial({ color: 0x120818 })); rim.position.y = -0.17; g.add(rim);
    sc.add(g);
    g.updateMatrixWorld(true); const top = new THREE.Box3().setFromObject(ch).max.y;
    const v = new THREE.Vector3(x, top + 0.12, g.position.z).project(cam);
    out.push([(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]);
  }
  ren.render(sc, cam);
  return out;
}

function hubCards(root, sel) {
  const C = [['qp', 'dm', 'QUICK PLAY', 'drop in, vote the next mode', '#ff4f6a', '14 playing'], ['bomb', 'bomb', 'PLANT & DEFUSE', '5v5. plant it, defuse it, buy guns', '#ffb04f', '9 playing'],
    ['br', 'br', 'JANK ROYALE', 'blimp, umbrella, loot. last one standing', '#4fd8ff', '22 playing'], ['zm', 'zm', 'ZOMBIES', 'you + 3 vs endless rounds. buy doors', '#39ff14', '3 playing'],
    ['isle', 'br', 'BATTLE ISLAND', 'squads of 3. mech heroes. go down, get picked up', '#ff4fd8', '6 playing'], ['tr', 'gun', 'TRAINING', 'dummies + infinite ammo. no judgement', '#ffe14d', 'solo or party'],
  ];
  const g = el('div', 'cards');
  C.forEach(([k, art, n, d, c, live], i) => {
    const cd = el('div', 'card' + (k === sel ? ' sel' : '')); cd.style.setProperty('--c', c); cd.style.setProperty('--r', (i % 3 - 1) * 0.6 + 'deg');
    cd.append(modeThumb(art, n)); const t = el('div'); t.append(el('b', null, n), el('span', null, d)); cd.append(t, el('i', null, '● ' + live));
    if (k === 'isle') cd.append(el('div', 'new', 'MECHS'));
    g.append(cd);
  });
  const st = el('div', 'card soon'); st.style.cssText = 'grid-column:1/3;height:60px;--c:#b07dff'; st.append(el('div', null, '<b>STORY: OVERDUE</b><span>coming to the hub. you still owe us.</span>')); g.append(st);
  root.append(g);
}

function partyBar(root, n, extra) {
  const p = el('div', 'pbar');
  const a = el('div', 'pan'); a.style.padding = '8px 10px'; a.innerHTML = `<div class="row" style="justify-content:space-between"><span class="tag">PARTY ${n}/6</span><span class="row"><span style="font-size:12px;color:#c8bcd8">code</span><span class="code" style="font-size:20px">JNK4Q</span></span></div>
    <div class="row" style="margin-top:8px;gap:6px"><button class="wbtn">INVITE</button><button class="wbtn">JOIN CODE</button><button class="wbtn">FRIENDS <b style="color:#ff00dc">2 ON</b></button><button class="rbtn">LEAVE</button></div>${extra || ''}`;
  p.append(a); root.append(p);
}

function names(root, pts, ready) {
  pts.forEach(([x, y], i) => {
    const n = el('div', 'nm'); n.style.left = x + 'px'; n.style.top = (y - (ready ? 118 : 98)) + 'px';
    n.innerHTML = `${i === 0 ? '👑 ' : ''}${NAMES[i][0]}<small>${NAMES[i][1]}</small>` + (ready ? (ready[i] ? '<span class="rd">READY</span>' : '<span class="nr">not ready</span>') : '');
    root.append(n);
  });
}

window.__mock = (view) => {
  document.getElementById('mk')?.remove();
  const st = document.getElementById('mkcss') || document.head.appendChild(Object.assign(document.createElement('style'), { id: 'mkcss' })); st.textContent = css;
  const R = el('div'); R.id = 'mk'; document.body.append(R);
  const home = document.getElementById('scr-main');
  for (const s of ['.home-right', '.home-hero', '#homeEvent', '#homeStrip', '#status']) { const e = home.querySelector(s); if (e) e.style.visibility = 'hidden'; }
  for (const e of document.querySelectorAll('.mo, #multibox, #preview')) e.style.display = 'none';
  const W = innerWidth;
  if (view === 'hub' || view === 'friends') {
    if (view === 'hub') for (const e of home.querySelectorAll('.home-left')) e.style.visibility = 'visible';
    else for (const e of home.querySelectorAll('.home-left')) e.style.visibility = 'hidden';
    const pts = lineup(R, 3, view === 'hub' ? 0.405 : 0.35, 1.05, 0.62);
    names(R, pts);
    const sl = el('div', 'slot', '+<br>INVITE'); sl.style.left = (pts[2][0] + (pts[2][0] - pts[1][0])) + 'px'; sl.style.top = (pts[2][1] + 10) + 'px'; sl.style.height = '120px'; sl.style.width = '80px'; R.append(sl);
    if (view === 'hub') {
      hubCards(R);
      partyBar(R, 3);
      const n1 = el('div', 'note', 'the hub: pick a mode card, it opens that mode\'s lobby. your party always stands in the middle'); n1.style.cssText += 'right:36px;top:118px;max-width:480px;'; R.append(n1);
    } else {
      const f = el('div', 'pan'); f.style.cssText = 'position:absolute;right:28px;top:24px;width:440px;bottom:24px;';
      f.innerHTML = `<div class="row" style="justify-content:space-between"><span class="tag">FRIENDS</span><button class="wbtn">X</button></div>
      <div class="tabs" style="margin-top:12px"><div class="on">FRIENDS 5</div><div>REQUESTS <b style="color:#ff00dc">2</b></div></div>
      <div class="row"><input value="add by username..." style="color:#888"><button class="wbtn">ADD</button></div>
      <div style="margin-top:8px">
       <div class="fr"><span class="dot" style="background:#7dff4f"></span><div><b>bigwes</b><small>in your party</small></div><span class="sp"></span><button class="wbtn" style="opacity:.5">IN PARTY</button></div>
       <div class="fr"><span class="dot" style="background:#ffe14d"></span><div><b>noodle_arms</b><small>in lobby: ZOMBIES (2/4)</small></div><span class="sp"></span><button class="wbtn">INVITE</button><button class="wbtn">JOIN</button></div>
       <div class="fr"><span class="dot" style="background:#ff4f6a"></span><div><b>xX_bread_Xx</b><small>in match: JANK ROYALE · 14 left</small></div><span class="sp"></span><button class="wbtn">INVITE</button></div>
       <div class="fr"><span class="dot" style="background:#4fd8ff"></span><div><b>meatloaf_fan</b><small>in the menu</small></div><span class="sp"></span><button class="wbtn">INVITE</button><button class="wbtn">JOIN</button></div>
       <div class="fr" style="opacity:.5"><span class="dot" style="background:#555"></span><div><b>tax_evader</b><small>offline · 3 days ago</small></div><span class="sp"></span></div>
      </div>
      <div style="margin-top:12px" class="tag">REQUESTS</div>
      <div class="fr"><span class="dot" style="background:#7dff4f"></span><div><b>spoon_lord</b><small>wants to be friends</small></div><span class="sp"></span><button class="wbtn" style="background:#7dff4f">ACCEPT</button><button class="rbtn">NAH</button></div>
      <div style="font-size:12px;color:#c8bcd8;margin-top:10px">friends need an account. guests can still join a party with its code.</div>`;
      R.append(f);
      partyBar(R, 3);
      R.querySelector('.pbar').style.cssText += 'left:330px;right:520px;';
      const t = el('div', 'pan toast'); t.innerHTML = `<span class="tag">INVITE</span><b>noodle_arms</b> wants you in their party (ZOMBIES)<button class="ybtn" style="font-size:16px;padding:4px 12px">JOIN</button><button class="wbtn">NAH</button>`; R.append(t);
    }
    return 'ok';
  }
  // a mode lobby (public or private)
  for (const e of home.querySelectorAll('.home-left, .home-logo, #acctBar')) e.style.visibility = 'hidden';
  const priv = view === 'priv';
  const head = el('div'); head.style.cssText = 'position:absolute;left:28px;top:20px;display:flex;gap:16px;align-items:center';
  head.innerHTML = `<button class="wbtn" style="font-size:18px">&lt; HUB</button><div class="title">PLANT &amp; DEFUSE</div><div style="font-size:14px;color:#e8dcef;max-width:260px">5v5. attackers plant, defenders defuse. buy guns between rounds</div>`;
  R.append(head);
  const pts = lineup(R, 4, 0.5, 1.15, 0.8);
  names(R, pts, priv ? [1, 1, 0, 1] : [1, 1, 1, 0]);
  const L = el('div', 'pan'); L.style.cssText = 'position:absolute;left:28px;top:118px;width:300px;';
  if (!priv) L.innerHTML = `<span class="tag">MATCH</span><div class="seg" style="margin:12px 0"><div class="on">PUBLIC</div><div>PRIVATE</div></div>
    <div class="set">your party plays as<em>ONE TEAM</em></div>
    <div class="set">map<em>VOTED</em></div>
    <div class="set">fill with bots after<em>30 s</em></div>
    <div class="set">warm up while we look<span class="tog"></span></div>
    <div class="set">region<em>AUTO</em></div>
    <div class="lead" style="margin-top:6px">only the leader (taco) can change these</div>`;
  else L.innerHTML = `<span class="tag">MATCH</span><div class="seg" style="margin:12px 0"><div>PUBLIC</div><div class="on">PRIVATE</div></div>
    <div class="set">bots<span class="tog"></span></div>
    <div class="set">bot count<span class="row"><span class="slider"><b style="width:50%"></b></span><em>6</em></span></div>
    <div class="set">difficulty<em>&lt; HARD &gt;</em></div>
    <div class="set">rounds to win<em>&lt; 7 &gt;</em></div>
    <div class="set">buy time<em>&lt; 15 s &gt;</em></div>
    <div class="set">teams<em>&lt; PARTY vs BOTS &gt;</em></div>
    <div class="set">friends can join<span class="tog off"></span></div>`;
  R.append(L);
  const M = el('div', 'pan'); M.style.cssText = 'position:absolute;right:28px;top:118px;width:300px;';
  if (!priv) M.innerHTML = `<span class="tag">FINDING A MATCH</span><div style="font:900 44px var(--font);color:#4fd8ff;margin:8px 0">0:12</div>
    <div class="set">players found<em>7 / 10</em></div><div class="set">your party<em>4</em></div><div class="set">bots fill in<em>0:18</em></div>
    <div style="font-size:13px;color:#c8bcd8;margin-top:6px">the map is voted when everyone's in. warming up in the deathmatch arena meanwhile.</div>`;
  else M.innerHTML = `<span class="tag">MAP</span><img class="map" src="/thumbs/bazaar_sd.jpg" style="margin-top:10px"><div class="row" style="justify-content:space-between;margin-top:8px"><button class="wbtn">&lt;</button><b style="font-size:20px">BAZAAR</b><button class="wbtn">&gt;</button></div>
    <div class="row" style="margin-top:8px;gap:6px">${['warehouse_sd', 'suburb_sd', 'desert_sd', 'rooftop_sd'].map((m) => `<img src="/thumbs/${m}.jpg" style="width:62px;height:40px;object-fit:cover;border:2px solid #000">`).join('')}</div>
    <div class="set" style="margin-top:6px">random map<span class="tog off"></span></div>`;
  R.append(M);
  const B = el('div'); B.style.cssText = 'position:absolute;left:50%;bottom:26px;transform:translateX(-50%);display:flex;gap:18px;align-items:center';
  B.innerHTML = priv ? `<button class="wbtn">INVITE</button><button class="ybtn">START MATCH</button><div style="font-size:13px;width:150px">3/4 ready. starts when you press it</div>`
    : `<button class="wbtn">INVITE</button><button class="ybtn" style="background:#ff4fd8;color:#fff;box-shadow:6px 6px 0 #ffe14d">CANCEL SEARCH</button><div style="font-size:13px;width:150px">party code <b class="code" style="font-size:16px">JNK4Q</b></div>`;
  R.append(B);
  const n1 = el('div', 'note', priv ? 'PRIVATE: the leader picks the map, bots and rules. only the party (or friends, if allowed) gets in' : 'PUBLIC: FIND MATCH queues the whole party; you land together on one team. bots fill empty seats after the timer');
  n1.style.cssText += priv ? 'left:360px;top:120px;' : 'right:350px;top:120px;'; R.append(n1);
  return 'ok';
};
