// npm run check-supabase  ->  tells you if Supabase is set up right for JANKFIRE accounts.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
if (fs.existsSync(path.join(ROOT, '.env'))) process.loadEnvFile(path.join(ROOT, '.env'));
const url = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
const key = process.env.SUPABASE_SERVICE_KEY || '';
const H = (extra) => ({ apikey: key, ...(key.startsWith('sb_') ? {} : { Authorization: `Bearer ${key}` }), ...extra });
const say = (ok, msg) => console.log(`${ok ? '  OK  ' : '  !!  '} ${msg}`);

console.log('\nChecking Supabase for JANKFIRE...\n');
if (!url || !key) {
  say(false, 'SUPABASE_URL / SUPABASE_SERVICE_KEY are not set. Copy .env.example to .env and fill it in.');
  process.exit(1);
}
if (!/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(url)) say(false, `SUPABASE_URL looks odd: ${url} (expected https://<id>.supabase.co). Trying anyway.`);
if (key.startsWith('sb_publishable_') || /"role":"anon"/.test(Buffer.from((key.split('.')[1] || ''), 'base64').toString())) {
  say(false, 'That looks like the anon/publishable key. Use the secret key instead (Project Settings -> API Keys -> Secret keys, starts with sb_secret_), or the legacy service_role key.');
  process.exit(1);
}
try {
  const res = await fetch(`${url}/rest/v1/jf_users?select=name_lower&limit=1`, { headers: H() });
  const body = await res.text();
  if (res.ok) {
    say(true, 'connected, and the jf_users table exists');
    const count = await fetch(`${url}/rest/v1/jf_users?select=name_lower`, { headers: H({ Prefer: 'count=exact', Range: '0-0' }) });
    say(true, `accounts so far: ${(count.headers.get('content-range') || '?/?').split('/')[1]}`);
    // columns added after the first release: without them those stats can't be saved
    const cols = await fetch(`${url}/rest/v1/jf_users?select=airborne,wings_old,sniper_feats&limit=1`, { headers: H() });
    if (!cols.ok) { say(false, 'the jf_users table is missing newer columns (airborne + wings_old for Never Landed, sniper_feats for Sniper Royalty). Run supabase.sql again in the SQL Editor: it adds them and keeps every account.'); process.exit(1); }
    console.log('\nAll good. Start the server and accounts will be saved in Supabase.\n');
  } else if (res.status === 401 || res.status === 403) {
    say(false, `Supabase rejected the key (${res.status}). Re-copy the secret key (sb_secret_...) from Project Settings -> API Keys.`);
  } else if (body.includes('jf_users') || res.status === 404) {
    say(false, 'Connected, but the jf_users table is missing. Run supabase.sql in the Supabase SQL Editor.');
  } else {
    say(false, `Unexpected answer ${res.status}: ${body.slice(0, 200)}`);
  }
} catch (e) {
  say(false, `Could not reach ${url}: ${e.message}`);
}
