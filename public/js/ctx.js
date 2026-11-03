// Shared mutable game context. Yes it's a global. No, I will not be taking questions.
export const G = {
  myId: 0, myName: '', myColor: '#fff', joined: false,
  names: new Map(),      // id -> {name, color}
  remotes: new Map(),    // id -> Remote
  projs: new Map(),      // id -> projectile visual
  peels: new Map(),      // id -> peel mesh
  offset: 0, offsetInit: false, ping: 0,
  kills: 0, deaths: 0, shake: 0,
  mode: 'ffa', cfg: { map: 'islands', hip: 'normal', bots: 5, diff: 'normal' },
  gibs: [], holes: new Map(), skins: new Map(), skinFxWorld: null, skinFxVM: null,
  renderer: null, scene: null, camera: null, vmScene: null, vmCamera: null,
  settings: {
    name: '', jank: 1, sens: 1.2, adsSens: 1, vol: 0.5, fov: 95, swapAim: false, toggleAim: false,
    blood: true, shake: true, fovKick: true, showFps: false, skins: {}, killcam: true, showCards: true, card: '', kfx: 'none',
  },
};
