// WorkerSocket: a stand-in WebSocket backed by the solo story worker (simworker.js), handed to net.connect so the
// normal game client plays story mode with no server room. same surface net.js uses: readyState, send, close,
// onopen / onmessage / onclose.
// load time: the sim's worker takes seconds to start (it imports the whole game's rules, every map with them), so one
// is started while you're on the menus (warmSim) and NEW GAME hands it the save. a used one is never reused
let spare = null;
export function warmSim() { if (!spare && typeof Worker !== 'undefined') spare = new Worker(new URL('./simworker.js', import.meta.url), { type: 'module' }); }

export class WorkerSocket {
  constructor(save) {
    this.readyState = 0;
    this.onopen = this.onmessage = this.onclose = null;
    this.w = spare || new Worker(new URL('./simworker.js', import.meta.url), { type: 'module' }); spare = null;
    this.w.onmessage = (e) => {
      if (this.readyState === 0 && e.data === '{"t":"__open"}') { this.readyState = 1; if (this.onopen) this.onopen(); return; }
      if (this.readyState === 1 && this.onmessage) this.onmessage({ data: e.data });
    };
    this.w.onerror = (e) => { console.error('story worker:', e.message || e); this.close(true); };
    let dev = false;
    try { dev = new URLSearchParams(location.search).get('storydev') === '1'; } catch { /* no url */ }
    this.w.postMessage({ init: save || null, dev });
  }
  send(s) { if (this.readyState === 1) this.w.postMessage(s); }
  close(crashed) {
    if (this.readyState === 3) return;
    this.readyState = 3;
    this.w.terminate();
    if (this.onclose) this.onclose({ code: crashed ? 1011 : 1000 });
  }
}
