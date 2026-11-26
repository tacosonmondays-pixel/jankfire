# The clipping check (`PolishBackup.Clip`)

On 26 Nov 2026 the owner asked for four things, in both the hub and the training area:

- props must not block entrances unless that is intended;
- props must not clip into walls, other objects or other props;
- the roll-up door to the portal must sit in its frame and slide up into the wall, not through the frame;
- "find stuff like that!"

`ServerStorage.PolishBackup.Clip` finds these. It works on any area (training, any hub, the zombies school) and prints
a short list with positions. Its source is [`studio-tools/Clip.luau`](../studio-tools/Clip.luau). It sits beside the
flicker check, `PolishBackup.ZFight`.

## Running it

Run it in Edit mode, from the command bar or `execute_luau` (datamodel `Edit`):

```lua
local C = require(game.ServerStorage.PolishBackup.Clip:Clone())
print(C.run(workspace.Map.Hub, {
	doorways = {
		{ name = "pad room door", at = Vector3.new(0, 240, -8000), dir = Vector3.new(0, 0, -1), len = 8 },
	},
}))
```

- **`root`**: the area to check. Pass a folder or model: everything under it is checked against everything else under
  it. Pass the area itself, not the whole `workspace.Map`; a bigger root is slower and mixes areas.
- **Options:**

| Option | Default | What it does |
|---|---|---|
| `tol` | 0.15 | How deep (studs) an overlap must be to count. |
| `doorways` | none | Ways a player must get through: `{ name, at = a point on the floor in the opening, dir = the way through, len = how far to sweep }`. |
| `autoDoors` | true | Also checks every moving door's own opening (its `Center` attribute). |
| `ignore` | none | Words; a part whose full name contains one is left out (for overlaps an area means to have). |
| `rollZone` | 1.2 | How far a door slat may show above the door's `Top` (where it rolls in). |
| `max` | 40 | The most lines per list. |

- **Training:** `T.clip(stage)` in `TrainingV2` runs it on the training ground with its doorways (`T.DOORWAYS`, set
  by `TrainingCompound` for v5). `T.check(stage)` includes it, after the floor-gap check:

```lua
local T = require(game.ServerStorage.PolishBackup.TrainingV2:Clone())
print(T.clip(false)) -- the live build; T.clip(true) checks the staging copy
```

- **One pair:** `C.overlap(a, cfa, sa, b, tol)` measures how deep part `a` (placed at `cfa` with size `sa`, which may
  not be where `a` stands) and part `b` overlap, by real shape. For two plain boxes, `C.depth(cfa, sa, cfb, sb)`.
- **Time:** training v5 (about 900 props, 4 moving doors, 15 doorways) takes a few seconds. The first run in a
  session is slower, because it reads each mesh's triangles once.

## What it prints

```
PROPS: 812 props, 3 sunk deeper than 0.15
  CLIP 0.70 deep: Map.Hub.TrainingGround.LotScenery.Beacon into ...FieldWallE at (25.5, 272.6, -8279.5)
DOORS: 4 moving doors, 1 clip on their way
  DOOR ...LotShell.EggDoor shows 7.95 above its frame (EggSheet, nothing hides it) at (-304.0, 286.5, -8249.2) (91% open)
DOORWAYS: 15 checked, 0 blocked
(4.2 s)
```

Each line names both parts by full name and gives a world position on the part that was hit, near the prop.

## The three passes

1. **PROPS.** A prop is either of these:
   - any part inside a Model (the nearest Model with fewer than 400 things in it; the whole model counts as one
     prop);
   - a builder part named like furniture: Bench, Desk, Console, Crate, Seat, Table, Counter, Cradle, Barrel.

   The pass reports a prop sunk into another visible part deeper than `tol`.
2. **DOORS.** Every moving door is swept from shut to open in 12 steps. That covers TrainingDoors.client's rollers
   (slats with a `Shut` CFrame, and `Lift` and `Top` on the model) and hinged doors (`Hinge` and `Swing`). At each
   step, two things are checked:
   - **A shown slat must not cut through anything outside its door.** A slat that slides wholly into a wall or a
     housing is fine: when the wall covers the slat's whole thickness, that is where the slat goes.
   - **Any part of a shown slat more than `rollZone` above `Top` must be inside something solid.** If it isn't, the
     line says the door "shows above its frame". This is the owner's "the door goes over the frame".
3. **DOORWAYS.** A player's box (2.2 wide, 5 tall, 2 deep, feet 0.2 over the floor) is pushed through each doorway.
   It must meet nothing collidable except the door itself, the door's unseen blocks (`DoorBlock`, `EggBlock`), and
   portal voids and triggers.

## Left out on purpose

These are intended overlaps, so the list stays short and real:

- two parts of one model;
- invisible parts (solids, guards, triggers, zones);
- glass and see-through parts (transparency 0.3 or more): things inside a display case;
- thin decals and lines (0.12 or thinner, not collidable);
- trim set into walls, by name: Nose, Lip, Cap, Trim, Frame, Jamb, Head, Reveal, Housing, Bracket, Mount, Plinth,
  Foot, Base, Collar, Band, Glow, Light, Panel, Line, Word, Plate, Sign, Lens, Hook;
- kit frames in their walls (models named Portal, Frame, Gate, Lamp, Post, Parapet, Crown);
- a prop standing in a floor or the ground, when its middle is above the floor's top and over the floor;
- trees, bushes and rocks in each other or in the ground.

A prop sunk into the *side* of a raised floor or platform is still reported.

## How deep is measured

- **Two boxes:** exact, from the 15 separating axes.
- **A mesh:** measured against its own triangles, read once per mesh id with `AssetService:CreateEditableMeshAsync`. A
  mesh's bounding box covers its openings, so a frame around a door would otherwise always hit the door.
- **A union, wedge or cylinder:** measured by its real collision shape, with a shrinking probe box.
- **[box guess]:** when neither side can be read, the line ends with `[box guess]`. That depth comes from bounding
  boxes only: look at the spot before fixing it.
- **Unread meshes:** the last line says how many meshes could not be read (they fall back to the probe).

## Traps

- **CanQuery.** Spatial queries skip parts with CanQuery off, and most builder props have it off. The check turns it on
  for every part under `root` while it runs and puts it back after, even if the check fails.
- **Edit mode only.** Run it from the command bar or Edit. It changes CanQuery and makes a probe part for a moment.
- **Bounding boxes versus shapes.** `GetPartBoundsInBox` returns bounding boxes, not shapes. Every hit is measured
  again by shape before it is listed.
- **A door's `Top`.** It is the height where TrainingDoors.client hides a slat: once the slat's bottom is above `Top`,
  it is gone. A tall sheet that rides with the slats stays shown until its bottom passes `Top`. That is how the egg
  door's dark sheet stood 8 studs over its frame.

## Training v5, 26 Nov

| | v1 of the check | v2, before the fixes | v2, after the fixes |
|---|---|---|---|
| Props sunk | 33 (most false: drums, shelves, trees in berms, mesh boxes) | 13 | 0 |
| Doors clipping | 6 | 1 (the egg door's sheet, 8.1 over its frame) | 0 |
| Doorways blocked | 1 (`GateVoid`, a portal void) | 0 | 0 |

After the fixes (place version 1400): `T.check` reports the hall sealed with 0 leaks and nothing within 0.6 of an eye.

**Play test.** With the key from `LotTest` "setkey", the egg door rolled up all the way (9.0 of 9.0) as the player came
near, and every slat and the sheet were hidden. The ring at the end of the room took the player to the playground. The
key was put back afterwards.

**Photos.** The before/after sheet `training_clip_fixes_v1400.jpg` is in the shared notes folder. It shows the egg door,
the hub gate at 0, 42 and 100% open, the shelf and the rail.

v2's 13 props before the fixes:

- **Basement:** crates in the pipe brackets (1.2) and in the pipes (0.79).
- **The yard's beacons:** in the field's east wall (0.68) and in the target tower's corner (0.29).
- **The firing line's counter:** over the range rail and its posts (0.45).
- **The garage's roller boxes:** in the bay light and the garage frame (0.2 to 0.28).
- **Three joins of 0.16 to 0.18:** two counter rim pieces, the jump pad's own pieces, and a container and a barrier on a floor line. v2.1 leaves these out: same-name builder runs, kit models as one prop, props on a thin floor line.

Fixed in the builders:

- **The egg door** (`TrainingCompound` `T.TOPD3`, `TrainingV2` `topRoom` flush mode). It is now set in the course's
  south wall:
  - its slats roll up inside the wall;
  - the dark sheet behind them goes up into the wall over the opening;
  - the room runs through the wall and 5.5 studs behind it, boxed in.

  It used to stand 6 studs out from the wall on a collar.
- **The basement shelf** (`TrainingLot`). Its posts and top crates ran into the ceiling pipes and their brackets.
- **The range rail** (`TrainingV2` `range`). It ran through the firing line's counter.
- **The yard's KEEP CLEAR panel and its beacons** (`TrainingLot`, with `T.LOT_YARD` from `TrainingCompound`). They now
  fit between the garage frame and the v5 yard walls.
- **The garage's roller boxes** (`TrainingLot`). Each moved 0.3 off the garage frame; the bay-side box also sits 0.5
  lower, clear under the bay's first light bar.
- **Every gate's roll-up door** (`GateKit`, used by training and every hub). Over the head there is now a
  `ShutterHousing` roller box (`GateKit.HOUSING`: x ±4.5, from H to H+1.3, d 0.45 to 1.45), and the slats roll up into
  it. A slat shows at most 0.95 over the head before it hides. The hub builders leave a slot for the box: HubKit's
  armory wall does since push 180.
  - Where a gate stands free with only the hb_portal kit frame round it (training's HubGate, the Classic Rotunda's),
    the frame head's back reaches 0.2-0.28 into the box's lower edge. The box sits seated in the head and nothing
    shows (photo from below on the sheet), so it stays.
  - `run` does not report this, because neither side counts as a prop. It was found by testing a stand-in box with
    `C.overlap` at every gate tagged `Shutter`.
