# Battle Island batch 1: Tripo text prompts (WRECKING BALL, VENDING MACHINE, TROLLEY)

The looks come from `docs/mechs/ROSTER.md`. Paste each prompt into Tripo's **text to 3D**, and the shared negative
prompt into its negative box. Every prompt is under 1,000 characters and ends with the house style words.

How to download:
- **Download each result as a GLB** and name it as shown (e.g. `wreckingball_body.glb`).
- **Put them in `docs/mechs/tripo/in/`** (or send them to the session).
- **Walkers (VENDING MACHINE): turn Tripo's auto-rig on before downloading.** With it, the cut onto the game's joints
  follows Tripo's own elbows and knees (PAPER PLANE B and NIGHT SHIFT came rigged and cut cleanly; A didn't).
- **Not walkers (WRECKING BALL, TROLLEY, every part):** no rig needed.
- **Textures:** fine on or off. Paint and the painted-metal look are added in the game's colours afterwards, so team
  colours work.
- **Text** (OUT OF ORDER, prices, stencils) is added in the game as decals, so the prompts ask for blank panels.
- **Pilots** come from the game (its own animated pilot), so the prompts ask for no figures.

## Shared negative prompt
```
realistic photo, gritty, rusty, dirty, horror, gore, text, letters, numbers, logo, watermark, signature, multiple objects, scene, ground, floor, base, pedestal, background props, people, human figure, blurry, low detail, melted shapes, fused parts, extra limbs, broken geometry, thin wires, floating parts, see-through glass, holes in the surface
```

## House style words (already at the end of every prompt)
`stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated
colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean
bevels, single object, centered, plain light grey background`

---

## WRECKING BALL (dive tank: rolls, swings on a chain, slams)

### `wreckingball_body.glb`: the ball
```
A heavy round wrecking ball mech: one big steel sphere, almost perfectly round so it can roll. A thick riveted equator band and a second band crossing over the top, both with yellow and black hazard stripes. One round porthole window on the front with a thick bolted rim and a dark tinted pane. A heavy shackle loop on top for a chain. Two stubby stabiliser feet folded flush into the lower shell. Recessed armour panels, big round rivets and a few dents all over the shell. Colours: gunmetal grey steel, yellow and black hazard stripes, orange accents, a glowing cyan ring around the window. Front view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

### `wreckingball_hook.glb`: the grapple hook (on the end of the chain)
```
A big heavy crane hook on its own: a thick curved steel hook with a spring safety latch, hanging from a chunky swivel block with a round eye on top. Yellow and black hazard stripes on the block, a worn steel hook with a polished inner curve, big bolts. Hanging straight down, front view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

### `wreckingball_link.glb`: one chain link (the game repeats it for any length)
```
One single thick oval chain link on its own, like a giant anchor chain link with a centre stud bar across the middle. Heavy dark steel with a polished wear band where links rub, chunky and solid. Standing upright, front view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

### `wreckingball_cage.glb`: the pilot's hamster wheel (spins inside, seen through the window)
```
A pilot's hamster wheel: a round running wheel made of chunky metal bars, with a small padded bucket seat and two shoulder straps fixed in the middle on a short axle, and a little control stick. Thick sturdy bars, not thin wire. Colours: chrome bars, orange padded seat, yellow straps. Side view of the wheel, the seat facing left. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

---

## VENDING MACHINE (support: coin turret, drops colas, OUT OF ORDER shield wall)

### `vending_body.glb`: the machine (a walker: auto-rig ON)
```
A tall boxy vending machine robot on two short stubby legs with big flat feet, in an A-pose, two short thick arms held slightly away from the body. The front is a big glowing panel of colourful soda cans and bottles in rows behind tinted glass. On top, a lit marquee sign box with a blank glowing panel. Its face is a coin slot and a coin return cup in a chrome panel at head height, with two round button eyes. A drink delivery flap low on the front. Rounded box corners, chunky chrome trims, side vents. Colours: cyan body, hot pink trims and marquee, white and chrome details, warm glowing drinks. Full body, front view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

### `vending_door.glb`: the front door (swings open when it dispenses)
```
The front door of a vending machine on its own: a tall flat rectangular panel with a chunky chrome frame, a long vertical chrome handle on one side and two hinges on the other, rows of colourful soda cans and bottles behind solid tinted glass, a small blank price strip under each row. Cyan and hot pink frame. Front view, flat. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

### `vending_sign.glb`: the OUT OF ORDER shield wall (the words go on in the game)
```
A wide folding warning sign used as a shield wall: a big rectangular metal sign board with a thick yellow and black hazard border and a large blank white face, standing on two fold-out A-frame legs, with a carry handle on top and a few dents. Front view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

---

## TROLLEY (speed: drifts, rams, scoops people up in the basket)

### `trolley_body.glb`: the trolley (on wheels, no rig)
```
A big shopping trolley robot on four chunky swivel caster wheels. A chrome wire basket body made of thick bars in a grid, a deep basket at the front and a fold-down child seat at the back. A bright red plastic push handle across the back at chest height with a small yellow coin lock box. A low steel chassis under the basket with a rubber bumper at the front and two small round headlights. Chunky and sturdy, thick bars, not thin wire. Colours: chrome and steel, red handle and bumper, yellow coin lock, small blue trims. No figure. Three-quarter front view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

### `trolley_basket.glb`: the basket (tips forward to dump people)
```
A deep shopping trolley basket on its own: thick chrome bars in a grid forming an open-top box that tapers toward the front, a red plastic rim around the top edge, two hinge brackets at the bottom back corners. Chunky and sturdy, not thin wire. Three-quarter front view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```

### `trolley_wheel.glb`: one caster wheel (used four times; one wobbles)
```
One single chunky swivel caster wheel on its own: a fat black rubber wheel with a red hub, held in a thick chrome fork, a round swivel plate with four bolts on top. Side view. Style: stylized hero mech for a cartoon arena shooter, chunky hard-surface shapes, readable silhouette, bright saturated colours, glossy clear-coat painted metal, chrome and brass details, panel lines, rivets, subtle edge wear, clean bevels, single object, centered, plain light grey background
```
