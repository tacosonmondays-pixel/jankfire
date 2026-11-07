// Client side of accounts: login / signup / logout, keeping your profile (loadout, skins, settings) in sync.
const TOKEN_KEY = 'jankfire_token';
let token = null;
try { token = localStorage.getItem(TOKEN_KEY); } catch { /* private mode */ }

export const account = {
  me: null, // { name, level, stats, profile }
  gifts: [], // gifts the server just gave this account (shared/gifts.js): main.js shows the popup, then empties it
  get token() { return token; },
  get loggedIn() { return !!(token && this.me); },
};

async function api(path, body) {
  const res = await fetch('/api/' + path, {
    method: body ? 'POST' : 'GET',
    headers: { 'content-type': 'application/json', ...(token ? { authorization: 'Bearer ' + token } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch { /* empty */ }
  if (!res.ok) throw new Error(data.error || 'request failed');
  return data;
}

function setToken(t) {
  token = t;
  try { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); } catch { /* fine */ }
}

export async function restore() {
  if (!token) return null;
  try { const r = await api('me'); account.me = r.me; if (r.gifts && r.gifts.length) account.gifts = r.gifts; return account.me; }
  catch { setToken(null); account.me = null; return null; }
}
export async function refresh() { return restore(); }

export async function login(name, pass) {
  const r = await api('login', { name, pass });
  setToken(r.token);
  account.me = r.me;
  if (r.gifts && r.gifts.length) account.gifts = r.gifts;
  return r.me;
}
export async function register(name, pass) {
  const r = await api('register', { name, pass });
  setToken(r.token);
  account.me = r.me;
  if (r.gifts && r.gifts.length) account.gifts = r.gifts;
  return r.me;
}
export function logout() { setToken(null); account.me = null; }

let saveT = null;
export function saveProfile(profile) {
  if (!account.loggedIn) return;
  clearTimeout(saveT);
  saveT = setTimeout(() => { api('profile', { profile }).catch((e) => console.warn('profile save failed', e.message)); }, 700);
}

export async function leaderboard() { return api('leaderboard'); }
