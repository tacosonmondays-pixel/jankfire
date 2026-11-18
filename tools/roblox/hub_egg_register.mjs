// node --import ./tools/roblox/hub_egg_register.mjs tools/roblox/hub_egg_dump.mjs <out.json>  (see hub_egg_dump.mjs)
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
register('./hub_egg_hooks.mjs', pathToFileURL(import.meta.filename));
