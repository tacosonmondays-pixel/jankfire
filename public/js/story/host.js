// WorkerSocket: a stand-in WebSocket backed by the solo story worker (simworker.js), handed to net.connect so the
// normal game client plays story mode with no server room. same surface net.js uses: readyState, send, close,
// onopen / onmessage / onclose.
export class WorkerSocket {
  constructor(save) {
    this.readyState = 0;
    this.onopen = this.onmessage = this.onclose = null;
    this.w = new Worker(new URL('./simworker.js', import.meta.url), { type: 'module' });
    this.w.onmessage = (e) => {
      if (this.readyState === 0 && e.data === '{"t":"__open"}') { this.readyState = 1; if (this.onopen) this.onopen(); return; }
      if (this.readyState === 1 && this.onmessage) this.onmessage({ data: e.data });
    };
    this.w.onerror = (e) => { console.error('story worker:', e.message || e); this.close(true); };
    this.w.postMessage({ init: save || null });
  }
  send(s) { if (this.readyState === 1) this.w.postMessage(s); }
  close(crashed) {
    if (this.readyState === 3) return;
    this.readyState = 3;
    this.w.terminate();
    if (this.onclose) this.onclose({ code: crashed ? 1011 : 1000 });
  }
}
