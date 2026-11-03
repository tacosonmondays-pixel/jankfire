const handlers = {};

export const net = {
  ws: null,
  open: false,
  on(t, fn) { handlers[t] = fn; },
  send(o) { if (this.ws && this.ws.readyState === 1) this.ws.send(JSON.stringify(o)); },
  connect(hello, onClose) {
    const url = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';
    const ws = this.ws = new WebSocket(url);
    ws.onopen = () => { this.open = true; this.send({ t: 'join', ...hello }); };
    ws.onmessage = (e) => {
      if (ws !== this.ws) return;
      let m;
      try { m = JSON.parse(e.data); } catch { return; }
      const h = handlers[m.t];
      if (h) h(m);
    };
    ws.onclose = () => { if (ws !== this.ws) return; this.open = false; if (onClose) onClose(); };
  },
  // leave on purpose (quit to menu): no "disconnected" callback
  close() {
    const ws = this.ws;
    this.ws = null;
    this.open = false;
    if (ws) try { ws.close(); } catch { /* already gone */ }
  },
};
