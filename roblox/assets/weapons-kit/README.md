# The weapons kit: part names (the contract)

The owner, 19 Nov 2026, after the exploded view: "Breaking down weapons will help with improving the model making
future skins and creating proper animations right". So every kit gun is made of its **real parts**, each one a
**node** with a name everyone shares:
- **reload animators** (weapons-port: `Reloads.luau`, `Weapons.luau` `mdl.parts`, `GunParts`; hold-hands: the off
  hand) move parts by these names;
- **skin makers** paint and swap by part;
- the **BREAKDOWN** view (`shared/GunExplode.luau`, `client/ExplodedView.luau`) takes the gun apart by them.

The table the exporter checks is `tools/roblox/gun_parts_contract.py`. This page is the same list for people.

## Names

A piece is named `<node>_wz<zone>__<slot>`. The node is the part, the zone is what a wrap paints (A, B, or N for trim),
and the slot is the colour. A part can have several pieces, one per colour.

| Node | The part |
|---|---|
| `body` | the receiver / frame: the core every other part fits to (stays put in the breakdown) |
| `barrel` | the barrel, its shroud and gas block, and the brake when that isn't a part of its own |
| `barrels` | the Minigun's spinning cluster |
| `muzzle` | a muzzle device that comes off on its own |
| `mag` | the magazine: box, curved, drum, the nail strip; the LMG's box |
| `belt_00` .. `belt_11` | the LMG's belt links |
| `charge` | the charging handle |
| `bolt` | a hand-worked bolt, or a visible bolt carrier |
| `cocker` | a small gun's charging tab (Lefty & Righty) |
| `slide` | a pistol's slide |
| `cylinder` | a revolver's cylinder |
| `hammer` | the hammer; `lhammer` = the lever gun's; `hammerl` / `hammerr` = a double's two |
| `pump` | a pump action's sliding fore-end; the Water Pistol's pump |
| `lever` | a lever action's lever |
| `hinge` | a break action's barrels and hinge (they tip open); `shell1`, `shell2` its shells |
| `cover` | a feed cover / dust cover that opens |
| `box` | the Minigun's ammo box |
| `tank` | a water tank |
| `stock` | the stock / butt |
| `grip` | the pistol grip (with its trigger area when that is one piece) |
| `fore` | a fixed fore-end or fore-grip |
| `guard` | a handguard; `tguard` = the trigger guard when both exist |
| `sight` | the rear sight; `fsight` = the front post (`bead` on a shotgun) |
| `rail` | a top rail |
| `scope` | a scope or optic (its `lens` rides with it) |
| `trim`, `rivet`, `mark`, `panel`, `dot`, `lens` | small fittings: they ride with whatever part holds them |

**Moving parts** (what reloads and handling move): `mag`, `charge`, `bolt`, `cocker`, `slide`, `cylinder`, `hammer`,
`lhammer`, `hammerl`, `hammerr`, `pump`, `lever`, `hinge`, `shell1`, `shell2`, `cover`, `box`, `barrels`,
`belt_*`, `kat_blade`, `needle`, `jar`.

## What each kind of gun must have

| Kind | Guns | Parts of its own |
|---|---|---|
| rifle (mag + charging handle) | AR, SMG, Burst, DMR, Auto Shotgun, Redline | body, barrel, mag, charge, grip, sights (sight / fsight / scope / rail) |
| bolt action | Sniper | body, barrel, bolt, mag, stock, scope or sight |
| pump | Shotgun | body, barrel, pump, stock, sights |
| lever action | Lever Rifle | body, barrel, lever, lhammer, stock, sight |
| revolver | Revolver | body, barrel, cylinder, hammer, grip, sight |
| pistol | Pistol | body, slide, mag, grip |
| break action | Sawed-Off | body, hinge, hammerl, hammerr, shell1, shell2, grip |
| belt-fed | LMG | body, barrel, mag, cover, grip, stock |
| minigun | Minigun | body, barrels, box, grip |
| nail gun | Nail Gun | body, mag, grip |
| water | Water Pistol | body, tank, pump, grip |
| twin | Lefty & Righty | body, mag, cocker, grip |
| katana | Katana | kat_blade, kat_guard, kat_tsuka |

Gimmick and premium weapons (the Marble Shotgun's jar, the Chicken Rocket, the Tennis launcher, the Scythe's two forms,
the melee props) keep their own logic: no contract beyond their own moving parts.

## Skins

A skin (`w_<gun>@<skin>`) must keep its base gun's part names and the places of the parts that move. It must have
every moving node the base has, each with its middle within 2 cm of the base's. Then its reloads and BREAKDOWN work
with no extra work.

`export_weapons.py --kit` checks every file it exports and prints `PART CONTRACT <name> ok`, or what is missing or
moved (a note, not a stop). `python tools/roblox/gun_parts_contract.py` checks everything already in
`export_report.json`.

## Splitting a base gun into its parts

When a builder keeps two real parts in one piece (brake ports in the rail's trim piece, a barrel in the frame), the
base gun is split at export by `tools/roblox/gun_explode_split.py`. That cuts the piece into its solids and gives each
solid the part it sits on. The zone and slot don't change, so the look and the wraps are the same. The builders aren't
touched, so every skin built on them stays as it was.

Done so far:
- AR, Sniper, Shotgun, Revolver (place version 1064).
- The Redline's new charging handle (installing).

The other guns come in batches. Known: the DMR has no grip of its own yet.
