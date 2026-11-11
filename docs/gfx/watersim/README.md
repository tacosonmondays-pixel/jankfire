# Water physics: a proof

Owner, 2026-11-11: "Like actual physics with water can we do that in j.3s or whatever we're running on?"

**Yes for the surface, no for a full fluid.** This PR is a working proof of the surface part, switched off by default:
Settings > video > "water physics (test)". Mid and Too HD only.

## What it does
A small patch of water round the camera is a real wave simulation (`public/js/watersim.js`). Anything that already
makes a splash pokes it: players and bots wading or falling in, bullets, grenades, gibs, explosions. The ripples
spread at about 5.6 m/s, bounce off the banks, rocks and pier legs, cross each other and die out. The water's light and
reflections follow them. It works on every flat water surface (ponds, pools, the sea), because the patch follows you.

## What it cannot do
- It is a surface that goes up and down. No flow, no pouring, no waterfalls, no breaking waves, no water moving from one
  pool to another, nothing floating or pushed by the waves.
- The surface mesh does not move: the ripples are in the lighting, not the silhouette. (Moving it needs a denser pond
  mesh; left out of the proof.)
- Look only. Swimming, wading speed and everything the server decides are untouched, and nothing is sent to other
  players: two people see slightly different ripples.
- Only within 14 m of you (a 28 m square). Ripples leave the square and are gone.
- Lava, goo and other liquids are not simulated.

## How it works
- 128 x 128 cells over a 28 m square (22 cm a cell). Two half-float textures, swapped each step ("ping-pong"); each step
  is one small draw. 60 steps a second by the clock, at most 3 a frame.
- The wave equation with a little damping; the banks come from the shore map `liquids.js` already bakes, so there is no
  new map data. The square moves with the camera a whole cell at a time and carries the waves with it.
- The water shader reads the height and its slope (5 texture reads a water pixel inside the square).
- If the GPU cannot draw into float textures, or anything throws, it switches itself off and the water is as before.

## Cost (headless software GL, as a floor)
- The simulation: about 0.3 to 0.35 ms a frame.
- Memory: two 128 x 128 half-float textures, about 0.26 MB.
- Draw calls: up to 3 tiny ones a frame for the steps. The water itself: no extra draws.
- Not measured: the extra shader cost on screen, anything on a real GPU.

## Can it scale to the Islands sea?
The follow-the-camera square already runs on the sea in this build (not photographed). The honest limits: 14 m reach,
and on the open sea the big swell and whitecaps hide small ripples, so it mostly shows near shores and in calm bays.
A bigger square (256 cells over 56 m) is about 4 times the simulation cost, still small; a second, coarser square for
distance is possible later. Recommendation: keep it for ponds, pools, shallows and anything near the player; do not
expect it to replace the sea's swell.

## Pictures
- `desert_pond_current.jpg`: two things dropped in the Desert pond, off (top) and on (bottom), four moments. With it
  on, a ring spreads from the drop and reaches the banks. The first "on" frame is a mis-shot (the test camera was
  elsewhere).
- `desert_pond_weaker.jpg`: the same with an earlier, weaker tuning.
- Not kept: the first, strongest tuning, which showed the ring crossing the pond and bouncing back most clearly but
  drew it as thick white bands.

## Tested / not tested
Tested (headless SwiftShader, Desert, Too HD): switches on and off, steps run (about 105 in the photo run), drops land,
no page errors, the pond with it off is unchanged.
Not tested: a real GPU, the exe, Mid specifically, the fall-back path (no float support could not be forced here),
the camera-follow carry while moving, the sea, pools on other maps, a real match (drops were made by calling the same
splash function the game uses), how it looks in motion (about 3 frames a second here), the final strength of the look
(the last tuning pass was photographed once and one frame missed).

## Could the exe have a "real" simulated tier? (feasibility only, nothing built)
Owner: "Well what if we use a potato option for browser but an actual simulated thingy for the exe version?"

**The exe is not a stronger machine than the browser.** `desktop/` is Electron: the same Chromium, the same JavaScript,
the same graphics card as a browser tab, and PLAY ONLINE loads the same site from Render. What decides what a player
can run is their graphics card and their settings, not exe versus browser. So the split should be a quality tier, with
the exe allowed to default it on.

**1. Can a real particle fluid run next to our renderer?**
- What it is: tens of thousands of particles that really flow, splash, pour and pile up (methods called PBF or
  MLS-MPM), drawn as a smooth liquid surface.
- It needs WebGPU compute to be worth doing. Published WebGPU demos report roughly 70,000 to 100,000 particles in real
  time on laptop integrated graphics and more on a mid-range card (author-reported, not independently benchmarked). For
  a pond splash, a puddle, blood or the shredder we would want 5,000 to 30,000, which is inside that.
- A WebGL2 version (transform feedback, textures as particle storage) is possible but much weaker: neighbour search is
  awkward and slow there. A few thousand particles at best. Not recommended.
- Our renderer is WebGL (three.js `WebGLRenderer`). Two ways to add WebGPU:
  - **A second, WebGPU canvas just for the fluid**, laid over or under the game canvas. The simulation is easy to
    isolate this way. The hard part is making the liquid sit correctly in the 3D scene: it cannot see the game's depth
    buffer, so walls and players would not hide it properly without copying depth across every frame (slow, or a frame
    late). Fine for a liquid in an open spot (a pond, the shredder pit seen from above), wrong for anything that needs
    to go behind things.
  - **Move the whole game to three.js `WebGPURenderer`.** Then fluid and world share one renderer. But the three.js
    manual says custom `ShaderMaterial`s and `onBeforeCompile` patches are not supported there and must be rewritten as
    node materials. This game is built on those: the vertex snap on every material, the liquids, flames, wraps, haze,
    soft skin, the post pass. That is a rewrite of the look of the whole game, plus retesting every preset. Weeks, not a
    side task, and WebGPU is still not everywhere (it falls back to WebGL2, where compute does not exist).
- Cost at Too HD, as an estimate only: a few ms a frame on a mid-range card for 20,000 particles plus the surface
  drawing; unusable on integrated graphics next to the rest of the game; zero on machines without WebGPU because it
  would not run.
- Gameplay: like the heightfield, it would have to be look only. Synchronising a particle fluid between players is not
  realistic, so it must never block, push or hurt anyone.

**2. What can the Electron wrapper do that a tab cannot?**
- Turn WebGPU on with a command-line switch where Chromium has it off by default, and pin a known Chromium version.
  Real, but small: current Chromium already has WebGPU on Windows.
- No background throttling, a fixed window, the discrete GPU asked for by default (`force_high_performance_gpu`).
  Useful for frame rate in general, nothing to do with fluids.
- A native addon (C++ fluid on the CPU or CUDA) is possible in the exe only. Not worth it: results still have to cross
  into the web page to be drawn, it only helps exe players, and it is a second codebase to build per platform.
- Since PLAY ONLINE loads the same site, anything exe-only still has to live in the site's code behind a "this is the
  exe" check. So the exe gains a default and a flag, not a capability.

**3. Recommended tiers**
| tier | who gets it | water |
|---|---|---|
| Potato, Crusty | default for most players | the shader water we have |
| Mid, Too HD | by quality preset, once the proof is tuned | + the heightfield ripples in this PR |
| SIMULATED (optional, later) | a switch, default off in the browser, could default on in the exe when a WebGPU card is found | + a small particle fluid for hero moments only: the shredder pit, one fountain or pond, blood pools |

Recommendation: ship the heightfield as the "real water" for Mid and Too HD. Treat SIMULATED as its own project: start
with a stand-alone WebGPU test page (one pool, 20,000 particles, the second-canvas approach) to get real numbers on the
owner's machine before deciding anything. Do not migrate the renderer for it.

Sources: WebGPU particle fluid demo and its reported particle counts, https://github.com/matsuoka-601/webgpu-ocean and
https://tympanus.net/codrops/2025/02/26/webgpu-fluid-simulations-high-performance-real-time-rendering/ ; three.js
manual on what `WebGPURenderer` does not support, https://threejs.org/manual/en/webgpurenderer . The Electron points are
from general knowledge of Electron and were not looked up for this note.
