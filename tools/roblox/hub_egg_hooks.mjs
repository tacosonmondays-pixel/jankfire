// hub_egg_dump.mjs's loader: the web game's bare imports in Node. 'three' and 'three/addons/' from a local three 0.170.0
// (the web's version; env THREE_DIR, its folder with a trailing slash), '/shared/...' from the web repo (env WEB_DIR)
import { pathToFileURL } from 'node:url';
const THREE_DIR = process.env.THREE_DIR || 'C:/Users/soup2/Downloads/jankfire/jankfire/node_modules/three/';
const WEB = process.env.WEB_DIR || 'D:/Robloxd/jankfire/';
export async function resolve(spec, ctx, next) {
  if (spec === 'three') return { url: pathToFileURL(THREE_DIR + 'build/three.module.js').href, shortCircuit: true };
  if (spec.startsWith('three/addons/')) return { url: pathToFileURL(THREE_DIR + 'examples/jsm/' + spec.slice(13)).href, shortCircuit: true };
  if (spec.startsWith('/shared/')) return { url: pathToFileURL(WEB + spec.slice(1)).href, shortCircuit: true };
  return next(spec, ctx);
}
