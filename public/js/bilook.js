// BATTLE ISLAND's own look (the owner: "I want this to be higher quality than the base game"). Only on map
// 'battleisland'; every other map keeps the game's usual sky. This part: the sky. A painted anime noon: a deep blue
// zenith fading to a pale sea-haze horizon, a hot sun with a soft glow, flat drifting cumulus overhead and a band of
// big towering cumulus standing on the horizon, lit white on top, lavender-blue underneath, crisp edged like a
// background painting. One sphere, one shader, no textures: the same on every preset (it's a handful of noise taps
// a pixel, and Potato draws very few pixels). The sun's direction comes from the map's sun light (lighting.js), so the
// clouds are lit from where the shadows fall from. Plus the map's fog and a light colour grade (post.js) to match.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAPS } from '/shared/map.js';
import { setGrade } from './post.js';
import { biGroundLite, biGroundTime } from './biground.js';
import { biLifeMap, updateBiLife } from './bilife.js';

export const BI_SKY = {
  zen: 0x2a6fe4, mid: 0x74c0ff, hor: 0xe0f3ff, sea: 0xa8dcf2, // zenith, mid sky, horizon haze, under the horizon
  sunCol: 0xfff3d6, glow: 0xfff0c0,
  cloudLit: 0xffffff, cloudShade: 0xe2d6ee, cloudWarm: 0xffe9d6, // (the owner's refs: pastel clouds with peach-pink undersides)
  cover: 0.4, // how much of the sky overhead is cloud (0..1)
  towers: 1.0, // how tall the horizon cumulus stand
  drift: 0.004, // overhead clouds' wind (sky units / s)
  fog: 0xc8ecfa, fogNear: 140, fogFar: 1150, // aerial perspective: the far shore fades into the horizon haze
  grade: [1.16, 0.02, 1.06, 1], // saturation, warmth, contrast, on (post.js final pass; only when shaders are on)
  film: [0.3, 0.45], // a filmic curve (bright things roll off, never clip flat) and vibrance (post.js)
  // the light (the owner's refs: "vibrant", high-key): a warm bright sun and a strong blue sky fill bouncing green off the
  // grass, so shade is soft and coloured, never black
  light: { sun: 0xfff1d8, sunK: 1.06, hemi: [0xa9d6ff, 0x8fbf6a], hemiK: 1.18 },
};

const VERT = `varying vec3 vDir;
void main() { vDir = normalize( position ); vec4 p = modelViewMatrix * vec4( position, 1.0 ); gl_Position = projectionMatrix * p; gl_Position.z = gl_Position.w * 0.99999; }`;
const FRAG = `uniform vec3 uZen; uniform vec3 uMid; uniform vec3 uHor; uniform vec3 uSea; uniform vec3 uSun; uniform vec3 uSunCol; uniform vec3 uGlow;
uniform vec3 uLit; uniform vec3 uShade; uniform vec3 uWarm; uniform float uCover; uniform float uTowers; uniform float uT; uniform float uOct;
varying vec3 vDir;
float h21( vec2 p ) { p = fract( p * vec2( 123.34, 456.21 ) ); p += dot( p, p + 45.32 ); return fract( p.x * p.y ); }
float vn( vec2 p ) { vec2 i = floor( p ), f = fract( p ); f = f * f * ( 3.0 - 2.0 * f );
  return mix( mix( h21( i ), h21( i + vec2( 1, 0 ) ), f.x ), mix( h21( i + vec2( 0, 1 ) ), h21( i + vec2( 1, 1 ) ), f.x ), f.y ); }
float fbm( vec2 p ) { float a = 0.5, s = 0.0; mat2 r = mat2( 0.8, 0.6, -0.6, 0.8 );
  for ( int i = 0; i < 6; i++ ) { if ( float( i ) >= uOct ) break; s += a * vn( p ); p = r * p * 2.03 + 11.7; a *= 0.5; } return s; }
// a cloud's look: d = density (0..1). lit = how much the sun side it is. crisp edge, painted bands
vec3 cloudCol( float d, float lit, float warm ) {
  float band = smoothstep( 0.35, 0.65, lit );
  vec3 c = mix( uShade, uLit, band );
  c = mix( c, uWarm, warm * band * 0.6 );
  return c;
}
void main() {
  vec3 d = normalize( vDir );
  float y = d.y;
  // the sky: zenith -> mid -> horizon haze, the sea's haze under it
  vec3 col = y > 0.0 ? mix( uHor, mix( uMid, uZen, smoothstep( 0.18, 0.9, y ) ), smoothstep( 0.0, 0.32, y ) ) : mix( uHor, uSea, smoothstep( 0.0, 0.08, -y ) );
  float sd = max( dot( d, uSun ), 0.0 );
  col += uGlow * ( pow( sd, 9.0 ) * 0.28 + pow( sd, 90.0 ) * 0.5 ); // the bright air round the sun
  // overhead: a flat cloud deck, looked up at (projected onto a plane), drifting
  if ( y > 0.015 ) {
    vec2 p = d.xz / ( y + 0.12 ) * 0.8 + vec2( uT, uT * 0.35 );
    vec2 q = vec2( fbm( p * 0.9 ), fbm( p * 0.9 + 5.2 ) ); // a warp, so the puffs curl
    float n = fbm( p * 1.4 + q * 1.3 );
    float edge = 1.0 - uCover;
    float a = smoothstep( edge, edge + 0.035, n ); // crisp painted edge
    vec2 sp = normalize( uSun.xz + 1e-4 ) * 0.22;
    float lit = clamp( 0.62 + ( n - fbm( ( p - sp ) * 1.4 + q * 1.3 ) ) * 5.0 + ( n - edge ) * 1.5, 0.0, 1.0 ); // brighter on the side toward the sun
    vec3 cc = cloudCol( n, lit, pow( sd, 4.0 ) );
    cc += uGlow * pow( sd, 24.0 ) * 0.5 * ( 1.0 - smoothstep( edge, edge + 0.25, n ) ); // silver linings near the sun
    a *= smoothstep( 0.07, 0.3, y ); // fade out low down: the horizon belongs to the towers
    col = mix( col, cc, a * 0.95 );
  }
  // the horizon: a band of towering cumulus standing on the sea
  float az = atan( d.z, d.x );
  vec2 ap = vec2( az * 2.2, 0.0 );
  float hgt = uTowers * ( 0.03 + 0.24 * pow( smoothstep( 0.3, 0.75, fbm( ap * 0.7 + 3.0 ) ), 1.5 ) + 0.03 * fbm( ap * 3.0 ) ); // where each tower's top is
  float body = fbm( vec2( az * 9.0, y * 16.0 ) ); // puffy bulges along its outline
  float top = hgt * ( 0.82 + 0.35 * body );
  if ( y > -0.01 && y < top + 0.02 ) {
    float a = smoothstep( top, top - 0.006, y ) * smoothstep( -0.01, 0.012, y ) * step( 0.004, hgt );
    float lit = clamp( ( y / max( top, 0.01 ) ) * 1.2 + ( body - 0.5 ) * 1.6 + dot( normalize( vec2( d.x, d.z ) ), normalize( uSun.xz + 1e-4 ) ) * 0.25, 0.0, 1.0 );
    vec3 cc = cloudCol( body, lit, pow( sd, 3.0 ) );
    cc = mix( cc, uHor, 0.35 * ( 1.0 - smoothstep( 0.0, 0.08, y ) ) ); // their feet are in the haze
    col = mix( col, cc, a );
  }
  // the sun's disc
  col = mix( col, uSunCol * 1.6, smoothstep( 0.9993, 0.9997, sd ) );
  gl_FragColor = vec4( col, 1.0 );
}`;

const U = {
  uZen: { value: new THREE.Color() }, uMid: { value: new THREE.Color() }, uHor: { value: new THREE.Color() }, uSea: { value: new THREE.Color() },
  uSun: { value: new THREE.Vector3(0.4, 0.7, -0.5).normalize() }, uSunCol: { value: new THREE.Color() }, uGlow: { value: new THREE.Color() },
  uLit: { value: new THREE.Color() }, uShade: { value: new THREE.Color() }, uWarm: { value: new THREE.Color() },
  uCover: { value: 0.45 }, uTowers: { value: 0.5 }, uT: { value: 0 }, uOct: { value: 6 },
};
let dome = null, on = false, hidden = [], sunLight = null;
function make() {
  const m = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms: U, side: THREE.BackSide, depthWrite: false, depthTest: true, fog: false });
  dome = new THREE.Mesh(new THREE.SphereGeometry(880, 48, 24), m);
  dome.frustumCulled = false; dome.renderOrder = -10; dome.name = 'biSky';
  return dome;
}
function paint() {
  const S = BI_SKY;
  U.uZen.value.setHex(S.zen); U.uMid.value.setHex(S.mid); U.uHor.value.setHex(S.hor); U.uSea.value.setHex(S.sea);
  U.uSunCol.value.setHex(S.sunCol); U.uGlow.value.setHex(S.glow);
  U.uLit.value.setHex(S.cloudLit); U.uShade.value.setHex(S.cloudShade); U.uWarm.value.setHex(S.cloudWarm);
  U.uCover.value = S.cover; U.uTowers.value = S.towers;
}

// world.js, after a map is in (and lighting.js has aimed the sun): hide: the usual sky sphere, sun cube, box clouds
export function biLookMap(id, hide) {
  for (const o of hidden) o.visible = true; // (the last map's: back as they were)
  hidden = [];
  on = id === 'battleisland';
  if (dome) dome.visible = on;
  setGrade(on ? BI_SKY.grade : null, on ? BI_SKY.film : null);
  biLifeMap(on, on ? MAPS[id] : null); // (only asks for the island's def when it's the island: building it is not free)
  if (!on) return;
  if (!dome) G.scene.add(make());
  paint();
  for (const o of hide) if (o && o.visible) { o.visible = false; hidden.push(o); }
  sunLight = null;
  G.scene.traverse((o) => { if (!sunLight && o.isDirectionalLight && o.castShadow !== undefined && o.parent === G.scene) sunLight = o; });
  const Lt = BI_SKY.light, hemi = G.scene.children.find((o) => o.isHemisphereLight); // (after lighting.js's mood: on top of it)
  if (sunLight && Lt) { sunLight.color.setHex(Lt.sun); sunLight.intensity *= Lt.sunK; }
  if (hemi && Lt) { hemi.color.setHex(Lt.hemi[0]); hemi.groundColor.setHex(Lt.hemi[1]); hemi.intensity *= Lt.hemiK; }
  const f = G.scene.fog; f.color.setHex(BI_SKY.fog); f.near = BI_SKY.fogNear; f.far = BI_SKY.fogFar;
  U.uOct.value = (G.settings && G.settings.jank) === 0 ? 4 : 6; // (Potato: fewer layers of detail, it can't show them anyway)
}
const _d = new THREE.Vector3();
export const biSkyU = () => (on ? U : null); // (weather.js greys these for a rainy frame and puts them back after)
export function updateBiLook(dt) {
  if (!on || !dome) return;
  if (G.camera) dome.position.copy(G.camera.position);
  U.uT.value += dt * BI_SKY.drift;
  biGroundLite((G.settings && G.settings.jank) === 0); // Potato: the ground's simple mode
  biGroundTime(performance.now() / 1000 % 3600); // the shore's foam and caustics move
  updateBiLife(dt); // tufts, flowers, gulls, boats, swaying palms (bilife.js)
  if (sunLight) { _d.copy(sunLight.position).sub(sunLight.target.position); if (_d.lengthSq() > 1e-6) U.uSun.value.copy(_d.normalize()); }
}
export const biLookOn = () => on;
