import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
register('./lore_hooks.mjs', pathToFileURL(import.meta.filename));
