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
