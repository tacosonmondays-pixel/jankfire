# The fill light on the held gun

Added 16 Nov 2026, place version 280. Code: `roblox/src/client/Viewmodel.luau` (`FILL`, `fillOn`, `fillReach`, and
the block after `VM.props` in `VM.update`); `Arsenal.client.luau` passes `hidden = gone`.

**Why:** judges 5, 6 and 7 found every gun near-black in first person. The side you see (the top and the left) faces
away from the hall's lamps. Lightening the paint twice moved those pixels only 0 to 6 levels.

**What it is:** a SpotLight on an Attachment on the gun's root, with no part, so nothing of it shows. It sits up and
to the left of the gun's middle, a little toward you, in camera space. So it stays put while the gun sways, kicks or
turns in a reload. It is aimed at that middle: angle 80, brightness 1.2, colour 255,247,238. Its reach (`Range`)
ends just past the gun's far side (2.2 studs for the Revolver, 4.5 for the Assault Rifle).

- **It does not reach the world.** In the open, nothing is in range. Up against a wall, cover or another player,
  five rays a frame cut the reach to the first visible thing in the cone. Invisible blockers are skipped.
- **It goes out** whenever the viewmodel is hidden: third person, the scope, a menu, or holstered.
- **It also lights your hands.**
- **Not covered:** the Shredder is a Tool, not a viewmodel, so it has no fill light.

**Measured** with a fixed camera in the training hall, light at 0 then at 1.2 (`fill-light-sheet.jpg`,
`fill-light-revolver-full.jpg`, `fill-light-wall.jpg`):

| | gun pixels, mean | gun pixels, darkest tenth | world left of the gun | wall past the muzzle |
|---|---|---|---|---|
| Revolver | 29 -> 56 | 4 -> 24 | 0.37 | 1.38 (a dummy walking) |
| Assault Rifle | 32 -> 64 | 5 -> 30 | 0.37 | 0.57 |
| Shotgun | 25 -> 49 | 4 -> 26 | 0.31 | 0.98 (a dummy walking) |
| Assault Rifle, 3 studs from a wall | 33 -> 65 | 8 -> 28 | 0.24 | 0.14 |

Levels are 0 to 255. The world columns are mean change. Brightness 1.6 was also tried: it turns the Revolver's
steel cylinder near-white, so 1.2 was kept. To change the look, change the one `FILL` table.
