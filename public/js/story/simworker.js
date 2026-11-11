// the solo story "server": shared/story/sim.js in a web worker (TECH_PLAN §4). the page talks to it through
// host.js's WorkerSocket exactly like a WebSocket: json strings both ways. the first message is { init: save }.
import { createSim } from '/shared/story/sim.js';
import { cleanSave } from '/shared/story/save.js';
import '/shared/story/enginesys.js'; // the story engine's state rides along in the save (WP8)
import '/shared/story/invsys.js'; // the Tote Bag + quick bar (WP3)
import '/shared/story/bodysys.js'; // implants, HYPE, coupons (WP5)
import '/shared/story/carsys.js'; // story cars (WP7)
import '/shared/story/solohost.js'; // the card deck's hand and other server-side bits solo needs
import '/shared/story/refsys.js'; // the combat referee: the game's room code, in here (shared/story/refsys.js)
import '/shared/story/encsys.js'; // Act I encounters: groups of enemies for the set pieces (rigs, interns, dogs)

let sim = null, last = 0;
const send = (o) => postMessage(JSON.stringify(o));
onmessage = (e) => {
  if (!sim) {
    const d = e.data || {}, r = d.init ? cleanSave(d.init, { slot: d.init.slot | 0 }) : {};
    sim = createSim({ send, save: r.save || null });
    sim.raw = (s) => postMessage(s); // the referee's room messages are json already
    sim.dev = d.dev === true; // ?storydev=1 (tests): the dev 'give'
    if (r.save && Number.isFinite(d.init.playtime)) sim.save.playtime = d.init.playtime;
    last = performance.now();
    setInterval(() => { const n = performance.now(); sim.tick(Math.min(0.25, (n - last) / 1000)); last = n; }, 50); // 20 Hz, like the rooms
    postMessage('{"t":"__open"}');
    return;
  }
  let m;
  try { m = typeof e.data === 'string' ? JSON.parse(e.data) : null; } catch { return; }
  sim.msg(m);
};
