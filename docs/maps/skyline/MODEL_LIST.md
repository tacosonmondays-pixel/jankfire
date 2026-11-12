# Skyline: what still needs modelling

Walk-through on 2026-11-11 (main at `1f85a6d`; still true on `d5dca9d`): Skyline and Skyline S&D in the real game at Too HD (jank 3), shots from
both team ends, every rooftop set piece, the Spire, the bridges, a high overview and the street below
(`walk_sheet.jpg` next to this file), plus `tools/blender/inventory_maps.mjs`. Box counts are what that script still
finds drawn as boxes (skyline 5984 + 354, skyline_sd 5644 + 264). Only the south tower (the `tenement` arch model) and
the generic props (water towers, AC units, billboards, crates, barrels, jersey barriers, lollipop trees) are Blender
models so far.

What reads worst in the walk-through: the Spire is a dark blue box with pixel holes, every tower is one 160 m textured
box, the stair-bridges are grey staircases of boxes, and the big set pieces (the cola can, the crane, the observatory
dome, the choppers) are stacked rectangles.

Ranked by what players see most: landmarks and objectives first, then buildings, then props and scenery.
**Collision** = whether the boxes you bump into change (default no: visual only, the boxes stay for physics, bots and hits).

| # | What | Where | Now | Plan | Collision | Size |
|---|---|---|---|---|---|---|
| 1 | **The Spire**: the hub's glass shaft, its sniper nest, the mast, the hub deck, the C tower's body | centre (both maps; S&D at z -19, 4 floors) | glassblock boxes, windows as square holes, an 18 m box mast | **new model** (arch): a blue glass curtain wall on chrome mullions with spandrel bands, framed window openings, a crown round the nest, a lattice mast with rings and a red beacon, the deck's planters and benches; the C tower body below as a glass curtain wall | no | shaft 12 x 22 x 12 m, mast 18 m, deck 26 x 26 m, body 160 m |
| 2 | **The Jank Cola can** + vending machines | N tower (S&D: the crashers' spawn) | four turned slabs in an octagon, two chrome bands; vending machines are plain red / blue boxes | **new model**: a real 330 ml can at 9 m (domed base, necked shoulder, double-seam rim, stay-on tab, printed JANK COLA wrap, condensation beads), glossy candy red; the vending boxes tagged as the existing `p_vending` prop | no | 6 x 9 x 6 m can, 4 machines |
| 3 | **The tower crane** (Mr. Smiles sits on its jib) | NW building site (team end) | hazard-striped box mast, a slab jib, box counterweights, a box hook | **new model**: hammerhead tower crane from a real flat-top reference: lattice mast sections, slewing ring, operator cab, lattice jib and counter-jib with walkways, concrete counterweight blocks, trolley, hook block on its cable, tie bars | no | 32 m mast, 64 m jib |
| 4 | **The tower bodies** + parapets and cornices (8 of 9 towers; 9 on S&D) | every tower | one textured box per tower (office / tenement / concrete), down 160 m to the street | **new models** (arch, like the tenement): an office curtain-wall tower with window bands, corner piers, setback cornice and parapet cap (the kit's `fac_office` is already made, unused); a raw concrete one for the building site; `tenement` reused for E / NE. Shared kit with Rooftop (same `roofTop()`) | no | 26-30 m square x 160 m, x8 |
| 5 | **Stair-bridges** between the towers | 8 on Skyline, 14 on S&D | concrete box steps, plate rails (600 / 414 boxes) | **new model** (arch over the step boxes): steel stair bridges: side stringers, chequer-plate treads with nosings, posts, handrail and mid-rail, landings, lights underneath | no | 4 m wide, 20-45 m long |
| 6 | **Helicopters** (news chopper, helipad chopper) | W news roof, SW helipad (S&D: A site) | boxes in the shape of a chopper (2 per map) | **place the existing model**: `p_heli` (JANK NEWS 7) is built and never placed; wrap `chopper()` in `propOf('heli')`, livery from the map's colour | no | 12 m |
| 7 | **The observatory** | NE high roof (S&D: **B site**) | white box drum, five stacked boxes as a dome, a bar telescope | **new model**: ribbed drum, hemispherical dome on its ring rail with the slit open and shutter up, a refractor on an equatorial mount poking out, door, sign | no | 12 x 9 x 12 m |
| 8 | **The helipad kit**: control booth, fuel tanks, windsock, pad lights, S&D fuel cart | SW high roof (S&D: **A site**) | boxes | **new models**: a prefab booth with tinted glass, AC and an antenna; a striped windsock on its mast; a fuel bowser cart; edge lights on the pad | no | booth 3.6 m, cart 2 x 5 m |
| 9 | **Glass tube bridges** (N, S) and **girder bridges** (E, W) | hub to the ring | slabs: a deck, glass-block walls, a flat roof | **new model** (arch): an arched glass tunnel on steel ribs; a Warren-truss girder bridge with neon along the chords | no | 4 m wide, 45 m long, x4 |
| 10 | **Putt Putt Palace**: windmill, clown head, course walls | E roof | box windmill with plank sails, a cube clown face, plank walls | **new models**: a Dutch-style mini golf windmill with lattice sails, a big fibreglass clown head (mouth open, nose, wig), brick-edged felt lanes, flags | no | windmill 3 x 5.6 m, clown 3 m |
| 11 | **News studio**: uplink dish, studio lights, JANK NEWS 24 board | W roof | box dish, box lights | **new models**: a satellite uplink dish (parabola, feed horn, az-el mount), fresnel studio lights on stands, the sign frame | no | dish 6 m |
| 12 | **The greenhouse** + solar panels | SE low roof (team end) | steel posts and flat glass panes, box beds | **new model**: a Venlo glasshouse (sawtooth glass roof, aluminium frame, door), planted beds, tilted PV panels on frames | no | 14 x 3.8 x 14 m |
| 13 | **The rooftop garden**: gazebo, fountain, benches | S roof (on the tenement) | posts and two slabs, marble boxes | **new models**: an octagonal gazebo, a tiered fountain, park benches | no | gazebo 5 m |
| 14 | **The building site**: steel columns, beam stacks, site hut | NW low roof (team end) | box columns, box stacks, a red box hut | **new models**: steel I-beam columns with base plates and rebar, I-beam stacks on dunnage, a portacabin site office | no | 9 columns, hut 5 x 3 m |
| 15 | **Grapple bait**: window washers' platforms, gold blocks | tower faces, over the gaps | flat metal slabs, floating gold slabs | **new models**: a BMU gondola cradle with rails and its cables up to the roof; gold bars strapped on a slung pallet | no | 6 x 1.6 m, 4 x 4 m |
| 16 | **S&D set pieces**: ☺ CORP flag frame, machine rooms, B lift house, ticket kiosk, coin telescopes, radio mast, roof vents, privacy walls | S&D | boxes | **new models** (small batch): coin-op binocular viewers, a ticket kiosk, a lattice radio mast with dishes, a lift motor house, roof vents | no | small |
| 17 | **Neon crowns and cables** round the towers | all towers | glowing boxes (`cityDress()`) | **remodel** with item 4 (neon tube channels on the cornice) | no | |
| 18 | **The city below and beyond** (render only) | street 160 m down, the city to the fog | 4,700 boxes on each map (`streetLevel()`, `cityBeyond()`, far `tower()`s) | **new kit**: a few instanced far-building and shopfront types (fewer draw calls too). Shared with Rooftop: do it with that map's session | no | far |

## Not Skyline's own (for the coordinator)
- **Box clouds**: the pink-white boxes floating over every daytime map come from `public/js/world.js` (`cloudMat`). They
  are the first thing you see looking up on Skyline. A global fix.
- **Cone mountains** with white stripes ring the city maps' horizon (`public/js/scenery.js`, city theme). A city sits in
  a plain, not under Alps: worth a city-theme horizon.

## Order of work
1, 2, 3, 6 first (the landmarks you see from every spawn, and one cheap win), then 7 and 8 (the S&D sites), then 4 and
5 (the biggest box counts players walk past), then the set pieces. One landmark, or a small batch of related props, per
branch `claude/map-skyline-<thing>`.
