# Performance (Roblox)

The owner, 16 Nov 2026, playing in Studio: "I think the hologram is super laggy?? something lags really badly in the
training hub". This page covers what was slow, how it was measured, what changed, and how to measure again.

## The cause: the old training mirror (37 ms a frame)

In the owner's own Play test, standing in training at (-65, 243, -8313): **9.5 to 12 fps, an 84 ms frame, of which
40 ms was render CPU** (`Stats.RenderCPUFrameTime`). Heartbeat (0.2 ms) and physics (1.1 ms) were small.

To prove the cause, the old mirror was rebuilt Play-only in training, as it was before training's push 27 and
Hologram v447:
- a full 1.8x clone of the avatar, with its layered clothing and the idle animation playing;
- a new CFrame every frame;
- Neon plus 6 scanline `Texture`s on each of its 48 parts (288 Textures);
- **every part's Transparency and Color, and every Texture's Transparency and OffsetStudsV, written every frame**.

| training, Studio Play (60 fps cap) | fps | render CPU |
|---|---|---|
| new mirror (still statue, plain Neon) | 60 | 6.3 ms |
| no mirror | 60 | 6.2 ms |
| old clone, plain (layered clothing, animation, moving) | 60 | 6.0 ms |
| **old mirror, full (with the per-frame writes)** | **22** | **43.1 ms** |
| old mirror, per-frame writes stopped | 60 | 6.1 ms |

So the lag was the per-frame property writes on hundreds of Textures and parts. Each write makes the renderer redo
that object. Layered clothing, the playing animation and the moving root cost nothing measurable.

**Already fixed before this pass, by the owners:**
- Training push 27 (TrainingDoors): the mirror is a still statue. Layered clothing, tools and joints are gone, it
  is posed once and anchored, and it is rebuilt only when your character or appearance changes.
- Hologram v447 (VFX, commit 1bd5519): no Texture objects. The `lines` look is ForceField material. Parts are
  written only during the build-in and scan-out, and only when a value changes.

**Rule for every client effect:** never write properties on many instances every frame. Write once; animate with
the GPU (materials, Beams, ParticleEmitters, a Highlight); or write only when the value really changes, and only
for what is near and on screen.

## The rest of the frame, measured (training, after the mirror fix)

Each suspect was switched off on the client, one at a time, 2 s per sample:

| change | render CPU |
|---|---|
| baseline | 6.2 ms |
| the three Rooftops and Map.Models out of the client's world | 3.9 ms |
| plus the hub's Rotunda and Playground (only training left) | 3.7 ms |
| every light in the place off | 6.0 ms |
| every light's shadows off | 6.2 ms |
| `Lighting.GlobalShadows` off | 5.8 ms |

On this PC, lights and shadows cost almost nothing. The geometry of the far maps costs about 2.5 ms. That is now
removed by ZoneCull (below). No lamp budget is needed. Keep shadow-casting lights where they are (hub 9, training 5,
`R.check` caps the hub at 11).

## ZoneCull: each client draws only where you are

`StarterPlayerScripts.Jankfire.ZoneCull` (`roblox/src/client/ZoneCull.client.luau`).

- **Pieces.** Every child of `workspace.Map` with 200 or more parts (Rooftop, Models, RooftopV2, RooftopV3), every
  such child of `Map.Hub` (Rotunda, Playground, TrainingGround) and every match copy in `Map.ArenaCopies`. Small
  folders always stay: spawns, doors, zones, queue pads, barriers.
- **Hiding.** A piece is moved, on this client only, to `ReplicatedStorage.ZoneCullHidden`, which is not drawn.
  This happens once neither your character nor your camera has been within 250 + 60 studs of its box for 1 s.
- **Showing.** A piece comes back the same frame your character or camera is within 250 studs of its box. The check
  runs in PreSimulation, so a teleport lands on a floor, and in PreRender. In a match, the arena named by your
  `Arena` attribute also stays.
- **The server.** It keeps the real map, so hits, matches, spawns and other players are untouched. Its changes to a
  hidden piece still arrive. A rebuild that swaps in a new instance is picked up within 2 s.
- **Switch.** Set the `workspace` attribute `ZoneCull` to `false` to show everything, in Edit or on one client. The
  script's own attribute `Hidden` lists what is hidden now.
- **For script writers.** A hidden piece is missing from `workspace`:
  - TrainingDoors' `trainingGround()` returns nil while TrainingGround is hidden, and rescans within 2 s of its return.
  - GunHatsClient's racks also look in `ZoneCullHidden`.
  - HubHolo's holograms are already off outside the hub.
  - Anything new that finds map parts by path, or keeps a list of them, must cope with the piece being away.
- **Teleport test, 16 Nov.** Training → Rooftop v3 → hub → back lot. Each target piece was back on the arrival frame,
  with no drop in the root's height. The hide list was right at each stop.
- **Match in a copy, 16 Nov.** Ghost matches held RooftopV2 and RooftopV3, then a real match was started with the
  player in it (`JankMatchTest` "ghost" with the player), so it went to `ArenaCopies.RooftopV2_copy1`.
  - Inside it, the copy was drawn (4,301 parts) and the floor below was the copy's. Photo:
    `roblox/docs/perf/match-copy-zonecull.jpg`.
  - Back in the hub after the match, the Rotunda was back, everything else was hidden, and the copy the server
    destroyed was gone from `ZoneCullHidden` as well (the server's Destroy reaches a hidden piece, a few seconds
    after you leave).
  - A small saving is still possible: in a copy, the original arena stays drawn, because it is kept by the `Arena`
    attribute's name. That rule could be skipped while your body is inside another piece.
- **Network ownership.** Unanchored map parts are NPCs anchored at the root, so a hidden floor can't drop them. Dummy
  debris belongs to whoever is near it, and anyone that close has training drawn.

| Studio Play, render CPU | cull off | cull on |
|---|---|---|
| training | 6.3 ms | 4.0 ms |
| back lot | 6.3 ms | 3.9 ms |
| hub | 6.8 ms | 4.2 ms |

## Films: nothing pops in (CullKeep, CineKit.prewarm)

The owner, 27 Nov: "Things pop in because it renders as the clip plays". A film's lens cuts to places your body isn't,
so the map piece it shows could still be put aside by ZoneCull, and meshes and pictures nobody has drawn yet load while
the shot plays.

- **The keep hook.** `client/CullKeep.luau` holds asks: `CullKeep.keep(key, { names = {...}, points = {...}, seconds = n })`,
  `CullKeep.release(key)`. ZoneCull keeps a piece an ask names, or one within its margin of an ask's point (exactly
  like the camera rule), and brings it back the frame the ask arrives. `CullKeep.pieces(points, names)` gives the pieces
  those keep (ZoneCull fills in the lookup).
- **`CineKit.prewarm(shots, opts) -> warm`** yields at most `opts.timeout` (default 4 s). Run it before the film: under
  a black lead, an open, a sting, a countdown, a loading moment; never as a frozen screen mid-film. It
  1. turns every shot's camera spot and look point (u = 0, 0.5 and 1) plus `opts.points` into a keep;
  2. waits two frames for ZoneCull, then runs `ContentProvider:PreloadAsync` on everything those pieces and `opts.sets`
     use: meshes, textures, SurfaceAppearances, decals, clothes, sounds, animations, particles, beams, images (one
     instance per asset id), plus `opts.anims` and `opts.sounds` ids;
  3. returns `warm = { ok, waited, assets, pieces, release() }`.
  `opts.keep = false` loads the assets only (the pieces are looked up, hidden or not, but nothing is brought back or
  kept drawn): for loading well ahead, as ZOMBIES does from the moment a party picks the mode.
  Hand it to `CineKit.play(shots, { pre = warm })` and play releases it at stop, or call `warm.release()` yourself.
- **Mesh detail.** A game script can't change `RenderFidelity` ("Cannot change SolidModel RenderFidelity during
  Run-Time"). Set a film's hero meshes to Precise in Edit, on the kit. The zombies helicopters are Precise.
- **Fetched is not drawn (finishers, 27 Nov).** A mesh is only built for drawing once it is in the workspace.
  Preloading fetches the asset, but a clone made on a film's first frame still pops in.
  - The case: Tidecrest's katana and sheath were placed, and fetched (`GetAssetFetchStatus` Success), from frame 1. They
    were cloned into the workspace on that frame and showed up 5-7 frames into the first shot, with the preload and
    without it. The set, built ahead and parked, never had the problem.
  - The rule: during the prewarm, before the first frame, park every film object in the workspace (out of view: the
    warm stage, under the set's floor), and let the film take those copies (`FinisherPro` `parkKit`).
  - A second run in the same session hides the problem, because the meshes are built by then. Check the first film of a
    fresh Play.
- **Broken surfaces show up as pop-in too.** "Failed to upload TexturePack ... Referenced Asset 9 is NOT found" means a
  SurfaceAppearance names a glTF texture index that was never uploaded (the zombies helicopters' glow pieces, fixed by
  pointing their emissive mask at the glow atlas). Studio's output lists every one at load.
- **Checked, 27 Nov (zombies, Studio, frames at 30 fps):**
  - the keep: from the hub, with the school's original put aside, a prewarm on it brought it back (385 assets, 0.98 s)
    and it went away again 1 s after the release;
  - the news intro: 1.4 s black lead, 1,566 assets, 5 pieces, every cut clean;
  - the extraction film: the prewarm runs at the call (509 assets, 0.32 s, 90 s ahead) and the helicopter is sharp
    from the film's first frame. Before, it was drawn as the shot started and its texture came in blurry over 6 frames.
  - Before/after clip: `roblox/docs/perf/popin-before-after-27nov.mp4`.
  The frame check: `tools/roblox/popscan.py` lists the frames where one part of the picture jumps (a cut, a flash, a
  pop-in); look at the ones that aren't cuts.

## Before and after

| | fps | frame | render CPU |
|---|---|---|---|
| training, owner's test, before | 9.5 to 12 | 84 ms | 40 ms |
| training, now | 60 (Studio's cap) | 16.7 ms | 4.0 ms |
| back lot / hub, now | 60 | 16.7 ms | 3.9 / 4.2 ms |

Studio Play runs the server and the client in one process, and an unfocused Studio window throttles, so a real
client will do better than these numbers. Compare the relative costs, not the absolute ones.

## How to measure

In a Play test, from the Client datamodel (`execute_luau`):

```lua
local RS, S = game:GetService("RunService"), game:GetService("Stats")
local n, sum, rc = 0, 0, 0
local c = RS.RenderStepped:Connect(function(dt) n += 1; sum += dt; rc += S.RenderCPUFrameTime end)
task.wait(2); c:Disconnect()
return string.format("fps=%.1f rcpu=%.1f ms", n / sum, rc / n * 1000)
```

- **Isolating a suspect.** Switch it off on the client, measure again, then put it back. For example: reparent a map
  piece to a folder in ReplicatedStorage; set `Enabled = false` on lights; park `MirrorSpot` (`Parent = nil`) and the
  mirror drops itself.
- **More stats.** `Stats.PerformanceStats` (CPU, GPU, Memory) and `Stats.RenderBreakdown` (tris and draws per pass)
  can also be read.
- **Rebuilding something old Play-only.** Do it the way the old mirror was rebuilt above: it proves a cause without
  touching the place.
