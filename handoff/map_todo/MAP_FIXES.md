# Map fixes requested by the player (saved for later, after update 2)

Asked 2026-11-04. Do these as one map pass on top of the integrated update 2 (so they include Backrooms,
update 1's Bazaar fixes and the bot walk graph). Original designs only: "like Nuketown" means a compact,
symmetric two-houses-across-a-street suburb in that spirit, not a copy of its layout, props or branding.

## Shared: out-of-bounds warning
- Per-map play bounds. Leave them and a big pop-up appears: "RETURN TO THE MAP 3... 2... 1...".
  Come back in time and it clears; stay out and you die (server-enforced, credited as a fall/void death).
- Used by Suburb and Warehouse (and anywhere else a map now has a big walkable outside).

## Suburb: bigger, more Nuketown-like
- Scale it up so it plays like a compact two-house cul-de-sac (houses facing across a street,
  yards, fences, cars and a bus or truck down the middle as cover, sightlines down the street, flanks round the backs).
- The "ugly cliff" on every side goes. Instead, a flat extended platform (lawns, road) runs out a long way,
  then a ring of trees as the border. Past the playable edge -> the out-of-bounds countdown.

## Skyline
- There's still a void at the bottom. Add a street level far below the towers (road, cars, street lights) so falling
  lands you on something / you see a city floor, not a void (falling still kills).
- A bridge "just ends" in mid-air (screenshot skyline_bridge_end.png, left side): make it connect to something or end
  properly (railing, a cut-off barrier, a landing).

## Rooftop
- Same as Skyline: a street far below instead of the void (falling still kills).

## Warehouse
- More props inside: forklifts, pallets (stacked, some with boxes), more shelving rows.
- Outside: a fenced perimeter yard and a city skyline in the distance.
- Going too far out -> the out-of-bounds countdown, then death.

## Bazaar
- "Weird spacing in the map": there are visible gaps/seams between pieces (screenshot bazaar_gap.png: a dark
  vertical slot between floor tiles, top middle). Find and close the gaps between boxes across the whole map.

## Check while there
- Screenshot skyline_bridge_end.png shows the pause panel running off the right edge. It may just be a crop,
  but check the pause menu at small window sizes.
