// streaming hitches walking out to the Gut (the owner: "as you go out and especially the gut area, the map gets super
// choppy"): a model that just loaded used to compile all its shaders and upload all its textures on the one frame it
// first showed (150-250 ms), and a crowd walking into view cloned 20 people in one frame. now (public/js/city/stream.js
// warm()/warmStep(), crowd.js):
//   a new model warms up a frame at a time: at most one new shader compile or one first-use check a frame, textures
//   ~3 ms of them a frame; a crowd person's model goes ahead of the props waiting (a missing crowd shows more)
//   models whose shaders are already compiled cost no frames; with no renderer nothing waits (the city testbed)
//   a props rebuild waits for a prop model that's still warming (it would draw it cold), but never more than a second
//   the crowd: a new crowd model warms before its first person spawns, then at most 2 new people a frame
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { register } from 'node:module';
import * as THREE from 'three';

const ROOT = new URL('../../', import.meta.url);
const js = (s) => 'data:text/javascript,' + encodeURIComponent(s);
const THREE_URL = import.meta.resolve('three');
// stream.js and crowd.js for real; what they pull in for drawing the city is stood in for
const STUB = {
  './props.js': js(`import * as THREE from ${JSON.stringify(THREE_URL)}; export const buildPropGroup = () => { globalThis.__rebuilds = (globalThis.__rebuilds || 0) + 1; return new THREE.Group(); }; export const freeProps = () => {}; export const onPropModel = (f) => { globalThis.__onProp = f; }; export const propModel = (id) => globalThis.__models[id];`),
  './propcode.js': js(''),
  './weather.js': js('export class Weather { update() { return 0; } fog() {} dispose() {} }'),
  './mats.js': js(`import * as THREE from ${JSON.stringify(THREE_URL)}; export const NL = 4; export const cityUniforms = { uTime: { value: 0 }, uBeat: { value: 0 }, uNight: { value: 0 }, uHaze: { value: new THREE.Color() }, uLP: { value: [] }, uLC: { value: [] } }; export const cityMaterials = () => ({});`),
  'three/addons/loaders/GLTFLoader.js': js(`import * as THREE from ${JSON.stringify(THREE_URL)};
export class GLTFLoader { load(url, ok) { const s = new THREE.Group(); for (const n of ['hips', 'head']) { const m = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial({ name: url + n })); m.name = n; s.add(m); } ok({ scene: s }); } }`),
};
register(js(`const STUB = ${JSON.stringify(STUB)}, ROOT = ${JSON.stringify(ROOT.href)};
export async function resolve(s, c, next) {
  const from = c.parentURL || '';
  if (/public\\/js\\/city\\/(stream|crowd)\\.js$/.test(from) && STUB[s]) return { url: STUB[s], shortCircuit: true };
  if (s.startsWith('/shared/')) return next(ROOT + s.slice(1), c);
  return next(s, c);
}`));
globalThis.fetch = async () => ({ json: async () => ['s_local_tiedye', 's_local_cook', 's_local_scooter'] });
const { CityStream, drawKind } = await import('../../public/js/city/stream.js');
const { Crowd } = await import('../../public/js/city/crowd.js');

// a renderer that counts: compile() makes a program for each material it hasn't seen, initTexture() uploads one
function fakeRenderer() {
  const props = new WeakMap(), R = { info: { programs: [] }, log: [], uploaded: new Set() };
  R.properties = { get: (m) => { if (!props.has(m)) props.set(m, {}); return props.get(m); } };
  R.compile = (o) => o.traverse((q) => { if (!q.material) return; const p = R.properties.get(q.material); if (p.currentProgram) return;
    const pr = { name: q.material.name, getUniforms: () => { R.log.push('check ' + pr.name); return {}; } }; p.currentProgram = pr; R.info.programs.push(pr); R.log.push('compile ' + pr.name); });
  R.initTexture = (t) => { R.uploaded.add(t); R.log.push('upload ' + t.name); };
  let rt = null; R.getRenderTarget = () => rt; R.setRenderTarget = (t) => { rt = t; }; R.compileTargets = [];
  const c0 = R.compile; R.compile = (o) => { R.compileTargets.push(rt); c0(o); };
  return R;
}
// a CityStream with only what warm()/warmStep()/updateProps() use (no workers, no scene)
function stream(renderer) {
  const S = Object.create(CityStream.prototype);
  Object.assign(S, { renderer, warmQ: [], drawnTo: { canvas: 0, rt: -1e9 }, warmRT: null, scene: new THREE.Scene(), time: 0, cam: new THREE.Vector3(), R: { props: 100, propsHi: 30 }, props: { group: null, key: 'old', t: 0, n: 0 }, root: new THREE.Group() });
  return S;
}
const mesh = (name, tex = []) => { const m = new THREE.MeshStandardMaterial({ name }); for (const [k, t] of tex) { m[k] = new THREE.Texture(); m[k].name = t; } return new THREE.Mesh(new THREE.BoxGeometry(), m); };
const cam = new THREE.PerspectiveCamera();

test('a new model warms up a frame at a time: one compile, one check or one texture a frame, then done', () => {
  const R = fakeRenderer(), S = stream(R);
  let done = 0;
  S.warm([mesh('skin', [['map', 'skin.png'], ['normalMap', 'skin_n.png']]), mesh('robe', [['map', 'robe.png']])], () => done++);
  const frames = [];
  for (let f = 0; f < 20 && !done; f++) { const n = R.log.length; S.warmStep(cam); frames.push(R.log.slice(n)); }
  assert.equal(done, 1, 'done fires once the queue drains');
  for (const fr of frames) assert.ok(fr.filter((x) => !x.startsWith('upload')).length <= 1, `at most one compile or check a frame (got ${JSON.stringify(fr)})`);
  const steps = frames.flat();
  assert.deepEqual(steps.filter((s) => s.startsWith('compile')), ['compile skin', 'compile robe']);
  assert.ok(steps.indexOf('check skin') === steps.indexOf('compile skin') + 1, 'a shader is checked the frame after it compiled');
  assert.deepEqual(steps.filter((s) => s.startsWith('upload')).sort(), ['upload robe.png', 'upload skin.png', 'upload skin_n.png']);
  assert.ok(frames.length <= 5, `2 compiles + 2 checks, the textures within a frame's budget (${frames.length} frames)`);
});

test('a warm-up compiles for each kind of place the scene was drawn to lately (canvas, a target), then rebinds the old one', () => {
  const R = fakeRenderer(), S = stream(R);
  S.time = 100; S.drawnTo = { canvas: 99, rt: -1e9 };
  S.warm([mesh('a')], () => {}); S.warmStep(cam);
  assert.deepEqual(R.compileTargets, [null], 'drawn to the canvas only: compiled for the canvas');
  for (let i = 0; i < 10 && S.warmQ.length; i++) S.warmStep(cam); // (finish a)
  R.compileTargets.length = 0; S.drawnTo = { canvas: 99, rt: 95 }; // (post off, but a talk portrait drew the scene into a target)
  S.warm([mesh('b')], () => {}); S.warmStep(cam);
  assert.equal(R.compileTargets.length, 1, 'one kind on the first frame');
  for (let i = 0; i < 3; i++) S.warmStep(cam);
  assert.equal(R.compileTargets.length, 2, 'both kinds compiled, a frame each');
  assert.ok(R.compileTargets[1] && R.compileTargets[1].isWebGLRenderTarget && R.compileTargets[1].width === 1, 'the target kind with a 1 x 1 of its own');
  assert.equal(R.getRenderTarget(), null, 'and the canvas is bound again after');
  for (let i = 0; i < 10 && S.warmQ.length; i++) S.warmStep(cam); // (finish b)
  R.compileTargets.length = 0; S.time = 200; S.drawnTo = { canvas: -1e9, rt: 199 }; // (post on: only targets)
  S.warm([mesh('c')], () => {}); S.warmStep(cam);
  assert.ok(R.compileTargets.length === 1 && R.compileTargets[0], 'post on: the target kind only');
});

test('a crowd model goes ahead of waiting props, behind the one under way', () => {
  const R = fakeRenderer(), S = stream(R);
  for (const n of ['p1', 'p2', 'p3']) S.warm([mesh(n)], () => {}, true);
  S.warm([mesh('person')], () => {}, false, true);
  assert.deepEqual(S.warmQ.map((w) => w.objs[0].material.name), ['p1', 'person', 'p2', 'p3']);
});

test("post.js's target counts as the canvas (it poses as XR with sRGB output: the same shaders); a plain target doesn't", () => {
  const r = { outputColorSpace: THREE.SRGBColorSpace };
  const post = new THREE.WebGLRenderTarget(4, 4); post.isXRRenderTarget = true; post.texture.colorSpace = THREE.SRGBColorSpace;
  assert.equal(drawKind(r, null), 'canvas');
  assert.equal(drawKind(r, post), 'canvas', "post.js's target");
  assert.equal(drawKind(r, new THREE.WebGLRenderTarget(4, 4)), 'rt', 'a talk portrait, photo mode, the picture-in-picture');
});

test('already-compiled shaders cost no frames; no renderer means nothing waits', () => {
  const R = fakeRenderer(), S = stream(R), a = mesh('shared');
  R.compile(a); R.log.length = 0;
  let done = 0;
  S.warm([new THREE.Mesh(new THREE.BoxGeometry(), a.material), new THREE.Mesh(new THREE.BoxGeometry(), a.material)], () => done++);
  S.warmStep(cam);
  assert.equal(done, 1, 'a model whose programs are cached is ready on the first step');
  assert.deepEqual(R.log, [], 'and nothing was compiled again');
  const S2 = stream(null); let d2 = 0;
  S2.warm([mesh('x')], () => d2++);
  assert.equal(d2, 1, 'no renderer (the city testbed): done straight away');
});

test('a props rebuild waits for a prop model that is still warming, but never more than a second', () => {
  const R = fakeRenderer(), S = stream(R);
  globalThis.__rebuilds = 0;
  const want = [{ id: 'c1', d: 10, packed: { prop: [0, 0, 0, 0, 0, 1, 0], ids: ['lung'] } }];
  S.warm([mesh('lung_flesh'), mesh('lung_vein')], () => {}, true);
  S.time = 0.5; S.props.t = 0.1; S.updateProps(want);
  assert.equal(globalThis.__rebuilds, 0, 'held while the prop warms');
  S.time = 1.2; S.updateProps(want);
  assert.equal(globalThis.__rebuilds, 1, 'a second after the last rebuild it goes anyway (props never stall)');
  S.warmQ.length = 0; S.time = 2; S.props.key = 'old'; S.props.t = 1.5; S.updateProps(want);
  assert.equal(globalThis.__rebuilds, 2, 'nothing warming: rebuilds as before');
});

test('the crowd: a new model warms before anyone spawns, then at most 2 new people a frame', async () => {
  const R = fakeRenderer(), S = stream(R), C = new Crowd(new THREE.Scene());
  C.warm = (objs, done) => S.warm(objs, done);
  await new Promise((r) => setTimeout(r, 10)); // (the model list fetch)
  const marks = Array.from({ length: 12 }, (_, i) => ({ id: 'crowd', kind: 'cook', p: [i * 2, 0, 5] }));
  const cam = new THREE.Vector3(0, 0, 0), counts = [];
  for (let f = 0; f < 20; f++) { C.update(marks, cam, 1 / 60); S.warmStep(cam); counts.push(C.live.size); }
  const first = counts.findIndex((n) => n > 0);
  assert.ok(first >= 2, `nobody spawns until the model's shaders are warm (first spawn on frame ${first})`);
  assert.ok(R.log.some((s) => s.startsWith('compile')), 'the crowd model was compiled ahead');
  for (let i = 1; i < counts.length; i++) assert.ok(counts[i] - counts[i - 1] <= 2, `at most 2 new people a frame (${counts.join(',')})`);
  assert.equal(counts[counts.length - 1], 12, 'everyone is there in the end');
});
