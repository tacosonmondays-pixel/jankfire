// loads .env before the game rooms read their knobs (server/room.js). moved out of server.js as is
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
// secrets like SUPABASE_SERVICE_KEY can live in a .env file next to server.js (never commit it, never ship it in the exe)
try { if (fs.existsSync(path.join(ROOT, '.env'))) process.loadEnvFile(path.join(ROOT, '.env')); } catch (e) { console.warn('could not read .env:', e.message); }
