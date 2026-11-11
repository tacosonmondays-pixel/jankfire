// The soft skin look: a cheap stand-in for subsurface scattering on skin (players, zombies, your own hands). Real
// skin lets light in and back out a little red, so: the sun bleeds a warm red past the shadow line instead of
// stopping dead, and thin bits glow when the light is behind them. One extra term for the sun in the material's own
// shader (no extra passes); one shared uniform switches it, so the setting never recompiles anything.
import { jankify } from './jank.js';

export const skinU = { value: 0 }; // 0 = off, 1 = on (main.js sets it from the shader settings)
const LIT = { MeshLambertMaterial: 1, MeshPhongMaterial: 1, MeshToonMaterial: 1, MeshStandardMaterial: 1, MeshPhysicalMaterial: 1 };
const TYPES = LIT;

// patch a lit material in place (once). k = how soft (1 = skin)
export function softSkin(mat, k = 1) {
  if (!mat || !LIT[mat.type] || mat._skinOn) return mat;
  mat._skinOn = true; mat.userData.skin = k; // (.skin survives clone(): remote.js puts the look back on its copies)
  const prev = mat.onBeforeCompile, prevKey = mat.customProgramCacheKey ? mat.customProgramCacheKey() : '';
  mat.onBeforeCompile = (sh, r) => {
    if (prev) prev(sh, r);
    sh.uniforms.uSkin = skinU;
    // the sun only (the first directional light), and without its shadow: the far side of an arm is in the arm's own
    // shadow, which is exactly where the light should be leaking through
    sh.fragmentShader = 'uniform float uSkin;\n' + sh.fragmentShader.replace('#include <lights_fragment_end>', `#include <lights_fragment_end>
#if NUM_DIR_LIGHTS > 0
	if ( uSkin > 0.0 ) {
		vec3 skL = directionalLights[ 0 ].direction;
		float skN = dot( normal, skL );
		float skWrap = saturate( ( skN + 0.75 ) / 1.75 ) - saturate( skN ); // light that gets round the shadow line
		float skBack = pow( saturate( dot( geometryViewDir, - skL ) ), 2.0 ) * saturate( 0.6 - skN ); // lit from behind: it glows through
		vec3 skBlood = mix( vec3( 1.0, 0.22, 0.12 ), diffuseColor.rgb, 0.25 );
		reflectedLight.directDiffuse += uSkin * ${k.toFixed(2)} * directionalLights[ 0 ].color * skBlood * BRDF_Lambert( diffuseColor.rgb ) * ( skWrap * 1.25 + skBack * 2.0 );
	}
#endif`);
  };
  mat.customProgramCacheKey = () => prevKey + 'skin' + k;
  mat.needsUpdate = true;
  return mat;
}

// a skin copy of a shared material (models.js keeps one material per colour: a shirt the same colour must not turn to skin)
const copies = new Map();
export function skinCopy(mat) {
  if (!mat || !TYPES[mat.type]) return mat;
  if (mat._skinOn) return mat;
  if (!copies.has(mat)) { const c = jankify(mat.clone()); c.userData.shared = true; copies.set(mat, softSkin(c)); }
  return copies.get(mat);
}
