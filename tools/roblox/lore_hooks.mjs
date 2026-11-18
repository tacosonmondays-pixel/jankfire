import { pathToFileURL } from 'node:url';
const THREE_DIR = process.env.THREE_DIR || 'C:/Users/soup2/Downloads/jankfire/jankfire/node_modules/three/';
const WEB = process.env.WEB_DIR || 'C:/Users/soup2/jankfire-port/';
const HERE = new URL('.', import.meta.url).href;
export async function resolve(spec, ctx, next) {
  if (spec === 'three') return { url: pathToFileURL(THREE_DIR + 'build/three.module.js').href, shortCircuit: true };
  if (spec.startsWith('three/addons/')) return { url: pathToFileURL(THREE_DIR + 'examples/jsm/' + spec.slice(13)).href, shortCircuit: true };
  if (spec.startsWith('/shared/')) return { url: pathToFileURL(WEB + spec.slice(1)).href, shortCircuit: true };
  if (spec === './audio.js' || spec.endsWith('/audio.js')) return { url: HERE + 'lore_stub_audio.mjs', shortCircuit: true };
  if (spec === './models.js' && ctx.parentURL && ctx.parentURL.endsWith('/lorenpcs.js')) return { url: HERE + 'lore_models_shim.mjs', shortCircuit: true };
  return next(spec, ctx);
}
