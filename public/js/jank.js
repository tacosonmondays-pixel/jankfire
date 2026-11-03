// PS1-style vertex snapping. Makes everything wobble like it was rendered on a toaster.
import * as THREE from 'three';

export const jankUniforms = { uSnap: { value: new THREE.Vector2(160, 120) } };

export function jankify(mat) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uSnap = jankUniforms.uSnap;
    sh.vertexShader = 'uniform vec2 uSnap;\n' + sh.vertexShader.replace(
      '#include <project_vertex>',
      `#include <project_vertex>
      vec4 jsnap = gl_Position;
      jsnap.xyz /= jsnap.w;
      jsnap.xy = floor(jsnap.xy * uSnap + 0.5) / uSnap;
      jsnap.xyz *= jsnap.w;
      gl_Position = jsnap;`,
    );
  };
  return mat;
}
