// OVERDUE story conditions: tiny expression strings over the story state, compiled once (no eval, so content can't
// run code). e.g. '!q.sauce.done && (flag.metChoir || standing.bottom >= 5)'.
// names: flag.X (or a bare X) · var.X · q.ID.done / .failed / .active / .step / .n · standing.X · met.NPC · seen.SCENE
// · codex.ID · has.ITEM (asks the host). ops: ! && || == != < <= > >= ( ) and numbers / 'strings' / true / false.
const cache = new Map();

function lex(s) {
  const T = [], re = /\s*(&&|\|\||==|!=|<=|>=|[!<>()]|-?\d+(?:\.\d+)?|'[^']*'|[A-Za-z_][\w.:-]*)/y;
  let i = 0;
  while (i < s.length) {
    re.lastIndex = i;
    const m = re.exec(s);
    if (!m) { if (/^\s*$/.test(s.slice(i))) break; throw new Error(`story cond: can't read "${s}" at ${i}`); }
    T.push(m[1]); i = re.lastIndex;
  }
  return T;
}

// a name -> its value in the state. h = host hooks (has(item))
export function lookup(st, name, h) {
  if (name === 'true') return true;
  if (name === 'false') return false;
  const p = name.split('.');
  switch (p[0]) {
    case 'flag': return !!st.flags[p.slice(1).join('.')];
    case 'var': return st.vars[p.slice(1).join('.')] ?? 0;
    case 'standing': return st.standing[p[1]] ?? 0;
    case 'met': return !!st.met[p[1]];
    case 'seen': return !!st.seen[p[1]];
    case 'codex': return !!st.codex[p.slice(1).join('.')];
    case 'said': return !!(st.said && st.said[p.slice(1).join('.')]); // said.lumps.soup: heard that node
    case 'has': return !!(h && h.has && h.has(p.slice(1).join('.')));
    case 'q': {
      const q = st.quests[p[1]], k = p[2] || 'active';
      if (k === 'done') return !!(q && q.done);
      if (k === 'failed') return !!(q && q.failed);
      if (k === 'active') return !!(q && !q.done && !q.failed);
      if (k === 'started') return !!q;
      if (k === 'step') return q && !q.done ? q.step : '';
      if (k === 'n') return q ? (q.n || []).reduce((a, b) => a + b, 0) : 0;
      if (k === 'at') return !!(q && !q.done && q.step === p[3]); // q.sauce.at.drive: on that step right now
      return false;
    }
    default: return !!st.flags[name]; // a bare word is a flag
  }
}

function parse(T) {
  let i = 0;
  const peek = () => T[i], eat = (t) => { if (T[i] !== t) throw new Error(`story cond: wanted ${t}, got ${T[i]}`); i++; };
  const or = () => { let a = and(); while (peek() === '||') { i++; const l = a, r = and(); a = (s, h) => l(s, h) || r(s, h); } return a; };
  const and = () => { let a = not(); while (peek() === '&&') { i++; const l = a, r = not(); a = (s, h) => l(s, h) && r(s, h); } return a; };
  const not = () => { if (peek() === '!') { i++; const a = not(); return (s, h) => !a(s, h); } return cmp(); };
  const cmp = () => {
    const a = atom(), op = peek();
    if (!['==', '!=', '<', '<=', '>', '>='].includes(op)) return a;
    i++;
    const b = atom();
    return {
      '==': (s, h) => a(s, h) == b(s, h), '!=': (s, h) => a(s, h) != b(s, h), // (loose on purpose: 'drive' == q.x.step)
      '<': (s, h) => a(s, h) < b(s, h), '<=': (s, h) => a(s, h) <= b(s, h), '>': (s, h) => a(s, h) > b(s, h), '>=': (s, h) => a(s, h) >= b(s, h),
    }[op];
  };
  const atom = () => {
    const t = T[i++];
    if (t === undefined) throw new Error('story cond: ended early');
    if (t === '(') { const a = or(); eat(')'); return a; }
    if (/^-?\d/.test(t)) { const v = Number(t); return () => v; }
    if (t[0] === "'") { const v = t.slice(1, -1); return () => v; }
    return (s, h) => lookup(s, t, h);
  };
  const f = or();
  if (i < T.length) throw new Error(`story cond: left over "${T.slice(i).join(' ')}"`);
  return f;
}

export function compile(src) {
  if (src == null || src === '') return () => true;
  if (typeof src === 'function') return src;
  if (Array.isArray(src)) { const fs = src.map(compile); return (s, h) => fs.every((f) => f(s, h)); } // a list = all of them
  let f = cache.get(src);
  if (!f) { f = parse(lex(String(src))); cache.set(src, f); }
  return f;
}
export const test = (src, st, h) => !!compile(src)(st, h);
