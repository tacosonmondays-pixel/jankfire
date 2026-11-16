# What the web game's effects are, in numbers (for the critic)

Units are metres (Roblox: 1 m = 3 studs). Source lines in `public/js/`.

- **Muzzle flash** (`weapons.js:114-145`, first person only in the web game): a crisp 16-point star, white core, pale
  yellow #fff2a0, orange #ff9a1a tips fading out; 0.24 m across (x1.6 on shotgun, sniper, autoshot, dmr) plus two thin
  flame planes along the barrel, 0.4 x 0.14 m; a new random roll and a 0.8-1.4 size every frame; on for 0.05 s (0.035 s
  on guns over 8 shots a second: AR, SMG, Hat Trick, Belt Sander). No light, no smoke off your own gun.
- **Tracer** (`fx.js:261`, `weapons.js:870`): a straight solid line from the muzzle to where the shot ended, pale yellow
  #fff0a0 (own colours: sniper pink #ff4fd8 0.09 m thick, Second Opinion purple 0.06 m, Hat Trick blue, Revolver gold,
  pistol pale blue, Yeehaw pink, Half a Shotgun orange), 0.045 m thick, opacity fading straight to nothing over 0.2 s
  (0.03 m and 0.07 s on the fast guns). Shotguns draw one per pellet.
- **Someone else's shot** (`flipbook.js` muzzlePuff): the tracer plus a small grey smoke puff off the muzzle,
  0.22 -> 0.85 m, 0.55-0.8 s, half see-through, drifting along the shot.
- **Bullet impact** (`fx.js:268`): 10 small squares, grey-green #999988 turning dark grey #444444, sprayed off the wall
  along its normal at about 4 m/s (+-3), falling (gravity 12), 0.15 -> 0.08 m, gone in 0.5 s. Sparks off metal.
- **Frag explosion** (`fx.js:240`, `flipbook.js` boomSprite; radius 7.5 m): a white pop (a sphere 0.5 -> 4.25 m round in
  0.08 s), a baked fireball flipbook (about 18 -> 25 m across over 1.5 s: white-hot burst, orange, then dark rolling
  smoke) with 3 smaller ones off-centre, dark soot puffs from 0.65 s rising for 2.6-4.2 s, 22 hot sparks, 25 white
  feathers drifting down, a camera shake.
- **Smoke bomb** (`flipbook.js` softCloud; radius 6.5 m, 10 s): soft grey puffs filling a low wide cloud (0.4-3.8 m up,
  mostly low), each 3.3 -> 6-7.6 m across, 24 a second after a first 26, thick enough to hide a player.

Allowed on top in Roblox (asked for by the owner: richer, layered effects, a serious finish): a short light flash at the
muzzle and the blast; a bullet hole and a small dust puff at impacts; on the frag a ring racing across the floor, the
floor's dust, dark shards, slow cinders and a scorch mark. The web game's colours stay; nothing more colourful.
