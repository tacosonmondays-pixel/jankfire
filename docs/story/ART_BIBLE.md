# OVERDUE art bible

How story mode looks: a **post-apocalyptic, surreal** city sixty-one years after a nuclear war the companies started.
Greater Jankburg is grown on the war's dead, the people at the bottom are the fallout-born **Off-Spec**, and the
companies that ended the world still run their districts from the rubble. It builds on the game's existing look (chunky low-poly, bright saturated colours, glossy
bevelled Blender models, the pink/yellow/cyan comic UI, render presets from Potato to Too HD) and adds the owner's
references: **rubbery claymation puppets, uncanny faces, bold patterns, pastel and fleshy palettes, stacked surreal
architecture.** The references are the vibe; no character, costume or set is copied from them.

Companion docs: [DESIGN.md](DESIGN.md) · [TECH_PLAN.md](TECH_PLAN.md) · [SLICE_PLAN.md](SLICE_PLAN.md)

---

## 1. The three kinds of people

The city mixes three body types on purpose. The contrast is the joke and the horror.

| type | who | proportions | read |
|---|---|---|---|
| **Mannequins** | the player, Corp workers, shoppers, suburb families, crowd extras | the game's existing jointed mannequin (1.8 m, ~1 : 7.5 heads), ball joints, built-in jank (random tilt, a wrong knee) | "returned product" |
| **Normals** | survivors, scavengers, shopkeepers, raiders, ☺ CORP arcology staff, cops' faces under helmets, the old pre-war survivors (Auntie Spreadsheet, Dale) | chunky low-poly humans in scavenged clothes, 1 : 6 heads, simple faces (dot eyes, a mouth line), boxy hands | "the people trying to get through the day" |
| **Puppets (the Off-Spec)** | the fallout-born generations and the rich who bought Regrowth to stay young: faction characters, quest givers, bosses (the Family, the jesters, the Gut Choir, Lumps, Wee Gordo) | **exaggerated**: head 1 : 2.5 to 1 : 3.5 of the body, or a tiny head on a giant body; hands either tiny or enormous; never "normal" | "a claymation nightmare that loves you" |

### Puppet proportion rules
- **Why they look like this:** the Off-Spec are three generations born after the fallout and Regrowth. The rich got
  their own version: the Family and the company bosses bought Regrowth treatments to live forever, and it stretched
  their faces into grins. Mutation is never the joke (DESIGN §7.1): the designs are bold and stylised, and the
  characters are people first.
- **One thing is huge, one thing is tiny.** Every puppet gets one oversized feature and one undersized one: Pip
  Grinsworth (huge horned head, tiny praying hands), Long Larry (long body, droopy nose to his chest, tiny feet), Lumps
  (gigantic veiny forearms, small head, tiny legs), Wee Gordo (huge sagging lipped face, hunched tiny body), Don
  Grinaldi (huge face, huge hands, a tiny waist).
- **Silhouette first:** every puppet must be recognisable as a black shape at 30 m. Test with a flat-black render.
- **Gameplay hitboxes stay boxes** (head, body, legs as today). A giant head gets a bigger head box, so headshots on
  puppets are generous. That's a feature.
- **Heights:** small puppets 1.2-1.5 m, normal 1.7-2.0 m, big 2.4-3.0 m, bosses 4-12 m.

### Faces
- **Puppet faces** are the signature. Big glassy eyes (green, yellow, red-rimmed), long hooked or droopy noses, wide
  lipped mouths. Teeth are always a feature: a row of tiny needle teeth, or a few big yellow tombstones, never
  realistic teeth.
- **The grin**: every puppet can stretch its mouth wider than its head (a blend shape or a scaled jaw bone). Used in
  cutscenes and boss intros.
- **Rig for faces:** a jaw bone (mouth open/close, babble flap), two eye bones (look-at), two eyelid bones (blinks),
  two brow bones, and one "stretch" bone that pulls the mouth corners. Max 8 face bones. No blend shapes on crowd NPCs;
  heroes and bosses may have up to 4 shape keys (grin, frown, squash, scream).
- **Mannequin faces** stay blank (the game's existing look), with a painted smile for Corp staff.
- **Normals** get flat painted faces with one or two features modelled (a nose, ears).

### Skin and materials
- **Rubbery skin:** glossy but soft. Roughness 0.35-0.5, a faint clear coat, a warm rim light added in the shader
  (fake subsurface: the rim is redder than the skin). Skin colours are fleshy and pastel: pink-orange, lilac, mint,
  butter yellow, peach, pale blue-grey. Never photoreal.
- **Speckle:** a 64-128 px speckle/pore texture multiplied over the vertex colour (pink-orange skin with darker
  freckles, like the reference's rubbery creature).
- **Veins:** painted as vertex colour lines plus a small bump texture on the forearms and foreheads of the big guys.
- **Flesh (the Gut, organs, cores):** wet look. Roughness 0.2, high spec, a tiny "wet" normal noise, colours raw pink
  `#ff6f91`, liver `#8a2a4a`, fat `#ffd27a`, bile `#a6e22e`, bruise `#5b3a8f`. Slowly pulsing vertex animation
  (sin-wave inflate along the normal) on walls and organs.
- **Plastic (Corp):** the opposite: white and cyan, roughness 0.15, perfect, a faint grid texture, no grime.
- **Cloth:** flat colours with bold patterns (below) in a small tiled texture, roughness 0.8.
- **Metal and chrome:** the existing glossy bevelled weapon look (chrome, brass, candy paint).

## 2. Patterns

Bold patterns do a lot of the character work. Each is a tiny tiling texture (32-128 px, nearest-neighbour in Potato).

| pattern | where | colours |
|---|---|---|
| **Checkerboard** | the mafia's restaurants and floors, jester trousers, Pip's suit | red/blue/black floor tiles, red/white, black/white |
| **Pinstripe** | the Fazzoletti Family's suits, Pinstripe awnings | red/white, black/grey, cream/brown |
| **Tie-dye** | The Bottom: tees, banners, sofa-cars | pink/yellow/teal swirls |
| **Ribbing** | the Gut's tunnel walls, intestine streets | pink with darker ridges |
| **Grid / spreadsheet** | Corp Hill floors, office carpet, Auntie's dress | white/cyan, grey/blue |
| **Price tags / barcodes** | the Checkout | yellow/black, white/red |
| **Digits** | Number Works | yellow/black with big 7s and 13s |
| **Gingham / argyle** | Evergreen Acres (picnic blankets, sweaters, curtains) | pastel green/white, pink/blue |
| **Wallpaper damask** | the Lates (yellowed, peeling into flesh) | mustard/beige |
| **Halftone dots** | the cutscene comic panels, UI | pink/black, yellow/black |

## 3. Palettes per district

Base game palette stays the UI: hot pink `#ff4fd8` / `#ff00dc`, yellow `#ffe14d`, cyan `#4fd8ff`, toxic green
`#39ff14`, red `#ff3030` on near-black. Each district has its own world palette, sky, fog and light.

| district | key colours | sky / fog / light |
|---|---|---|
| **The Bottom** | pastel pink `#ffb3c7`, yellow `#ffe58a`, teal `#5fd3c6`, mint, tie-dye accents | a dark violet sky `#2a1840` with string lights; warm low lamps; light haze |
| **The Gut** | raw pink, liver, fat yellow, bile green, bone white | a red-brown "sky" (it's a ceiling of tissue in places), thick pink fog, a heartbeat-pulsing ambient |
| **Pinstripe** | blood red, cream, marble white, gold, black | a stormy grey-violet sky, candle-warm interiors, pink stucco rooms |
| **The Checkout** | yellow, red, white, neon pink | always golden-hour inside the dome, white fluorescent interiors |
| **Corp Hill** | white, cyan `#4fd8ff`, chrome, a single ☺ yellow | a clean blue sky, crisp hard sun, no fog (they paid for it) |
| **Chrome Gristle** | magenta, cyan, black, raw-meat red | always night, rain, neon bloom, wet reflective floor |
| **Number Works** | yellow `#ffe14d`, black, rust orange | smoggy yellow haze, sodium lights |
| **Evergreen Acres** | lawn green, sky blue, pastel house colours | a perfect sitcom-blue sky, perfect sun, a little too saturated |
| **The Lates** | mustard, beige, fluorescent white, a pink rot creeping in | no sky (a ceiling), buzzing fluorescent light, a faint yellow fog |
| **The Margins** | dark pine green, grey, void black with a gloss | dusk purple sky, heavy fog, the void reflects nothing |
| **Hot zones** (blast sites, fallen digits) | glassed black-green, ash grey, toxic green `#39ff14` glow | a sickly green sky, ash snow, glow from below |
| **The Commute** | sun-bleached tarmac, rust orange, faded car paint, paper white | dusty orange sky, paper storms (white confetti fog), long shadows |

## 4. Architecture and props per district

### Ruin rules (the whole city is after the end of the world)
- **Every district is a ruin with a ruler.** Start from the pre-apocalypse building (the sims' look), then break it in
  that district's way: the Stampede flattened things (crushed cars, trampled shopfronts), the Gut grew over things
  (flesh on brick), the digits fell on things (a giant 4 through a roof), the void ate things (clean black cuts).
- **Then repair it in the ruler's style.** Companies patch with branding (fresh logos and SALE banners on cracked
  concrete, ☺ CORP's bleach-white plastic panels); groups patch with scrap (office furniture, shopping carts, car
  doors, vending machines, tarps in tie-dye).
- **Readable decay, not mud.** Ruins stay bright and saturated: pastel concrete, candy rust, glossy flesh. Grime is a
  small texture, never a brown filter over everything.
- **Scavenger props everywhere:** barricades of filing cabinets and office chairs, cart walls, burning ☺buck barrels,
  scrap lean-tos, dead traffic jams, hand-painted signs in the lowercase voice ("no interns", "soup 2 coupons").
- **The war is in everything:** blast shadows burned onto walls, glassed craters, ash drifts, wrecked war machines in
  division colours (a ☺ CORP tank, a Big Value supply mech), fallen glowing digits, the void's clean black cuts, and
  under it all the corpse-city (bone in the bricks, roots that are veins).
- **Corp Hill is the exception:** a perfect clean bubble, with a bleach line on the road where the rubble ends.

General city rules (the game's existing map rules): **big readable blocks**, scenery all around (never a void, except
the Margins where the void is the point), streets wide enough for cars and grapple swings, everything climbable
somehow. Collisions stay boxes. Buildings are **modular kits** on a 2 m grid (walls, windows, doors, corners, roofs,
balconies), so districts can be assembled from code like Jankburg's `build()`.

| district | architecture | signature props |
|---|---|---|
| **The Bottom** | stacked pastel cube houses climbing a rubble hill, built from shipping containers, dead vending machines and fallen ☺ signs; every roof is someone's floor, external stairs, rebar sticking out | the Machine, washing lines, wok satellite dishes, sofas, fridges, scooters, plastic chairs, string lights, a sofa-car |
| **The Gut** | Gristle & Sons' old office campus grown over with skin (the logo still visible under it); rib arches; intestine tubes as streets; sphincter doors; lungs between buildings | teeth cobbles, vein cables, eyeballs in gutters, stomach-dogs, organ cores in jars, a tongue door |
| **Pinstripe** | gothic stone mansions, marble halls, arched windows, pink stucco restaurant interiors with checkerboard floors | velvet ropes, gold medallions, bocce balls, meatballs (huge), spaghetti, chandeliers, marionette strings from the sky |
| **The Checkout** | a cracked, half-collapsed mall dome over streets, trampled shopfronts from the Stampede, escalators between levels, shopfronts, a food court plaza | shopping carts, mannequins in windows, SALE banners, fountains with coins, kiosks, a cart mountain |
| **Corp Hill** | the clean bubble: white glass towers, the ☺ Spire, perfect lawns, clocks on every corner, open-plan offices inside | public clocks, punch-clocks, water coolers, office chairs, filing cabinets, LED schedule boards |
| **Chrome Gristle** | narrow neon lanes, overhanging signs, back-alley clinics, butcher curtains | neon sign letters, surgical chairs, organ jars, noodle carts, arcade cabinets |
| **Number Works** | factory yards, conveyor bridges, smokestacks, a building-sized calculator, fallen digits stuck in roofs and roads | giant digits, presses, pallets, forklifts (existing), number balls (existing `p_numball`) |
| **Evergreen Acres** | identical pastel houses, picket fences, cul-de-sacs, behind a sandbag wall painted like a hedge | sprinklers, trampolines, BBQs, mailboxes, garden gnomes, identical cars |
| **The Lates** | repeating yellow offices, car parks, a clock tower with no hands | waiting-room chairs, water-stained ceiling tiles, photocopiers, flickering lights |
| **The Margins** | pine forest, crumbling roads ending in void, half-eaten houses | Vacancy Holdings SOLD signs, foreclosure notices, gnomes (the Walkers' stakes), PREMIUM NEGATIVE SPACE billboards, a lifeguard tower |

## 5. Building it in the Blender pipeline

Same pipeline as the weapons and props (`tools/blender/`, models from code in headless Blender, `.glb` into
`public/models/`, turnaround sheets in `tools/blender/sheets/`, the code model is the fallback). New pieces:

### Look rules
- **Low-poly, PS1-leaning, glossy.** Flat shading on hard props, smooth shading on skin and flesh. Bevels on every
  box edge (1-2 segments) so the gloss catches.
- **Vertex colour first.** Most colour is vertex colour (one merged mesh per object, like `public/js/cars.js`); small
  tiling textures only for patterns, speckle, grime and labels. Textures are 64-256 px, nearest-filtered in Potato.
- **Rubbery shading** is a shared material: `MeshStandardMaterial` with low roughness plus an `onBeforeCompile` rim
  term (one shader, all skin). Flesh adds the pulse in the vertex shader.
- **Outlines** on other players and on puppet NPCs within 30 m (the game's existing outlines).
- **Crusty textures:** the `tex_noise` / `tex_canvas` helpers in `lib.py` for grime, plus a new `tex_speckle` and
  `tex_rib` (tissue ridges) and pattern makers (`tex_check`, `tex_pinstripe`, `tex_tiedye`).
- **Part names:** keep the existing conventions (`_wzA` / `_wzB` / `_wzN` wrap zones on weapons). Characters add
  bone names from the shared rig (below), props tag `_col` for their collision box size hint and `_lod1` for the
  simpler mesh.

### Characters
- **One shared humanoid rig** for mannequins and normals (the existing mannequin rig and `anim.js` clips), so every
  walk, run, sit, talk, ragdoll and dance plays on everyone.
- **Puppet rig** = the same skeleton with different bone lengths plus the face bones (§1). Clips retarget by bone name
  with per-character scale, so a puppet with tiny legs still uses the walk (it just waddles; good).
- **Bosses** get their own rigs and clips.
- **Animation** gets max effort (the owner's quality bar): pose sheets and turnarounds for every character, clips
  checked as frame contact sheets in the game. Puppets move with squash and stretch, overshoot and a slight
  stop-motion step (play clips at 12 fps on puppets for the claymation feel, optional per character).

### Triangle and texture budgets
| asset | tris (LOD0) | LOD1 | bones | textures |
|---|---|---|---|---|
| player mannequin + outfit | 3,000-5,000 | 1,500 | existing rig | existing |
| hero puppet (quest giver, faction lead) | 4,000-7,000 | 2,000 | rig + 8 face | 1 × 256 px pattern + speckle |
| normal NPC | 1,500-2,500 | 700 | shared rig | vertex colour + 1 × 64 px |
| crowd extra | 600-1,000 | 300 / impostor | shared rig | vertex colour only |
| boss | 8,000-15,000 | 4,000 | own rig ≤ 64 | 2 × 256 px |
| small prop (chair, jar, sign) | 50-600 | merged / none | — | vertex colour |
| big prop (car, fountain, cart pile) | 1,500-4,000 | 600 | — | 1 × 128 px |
| building module (wall/window/door piece) | 50-400 | — (merged per chunk) | — | district atlas 256 px |
| landmark (Spire, Big Stomach, Villa) | 6,000-15,000 | 2,000 + impostor | — | 2 × 256 px |
| weapon (viewmodel) | existing (2,000-8,000) | — | — | existing |

On screen at once (Too HD): ~600k tris; Potato: ~150k. Each district's atlas set is ≤ 4 MB of textures.

## 6. The first 30 assets to model

In slice order (what the vertical slice needs first). **P** = prop, **C** = character, **B** = building kit, **V** =
vehicle, **L** = landmark.

| # | asset | type | district | notes |
|---|---|---|---|---|
| 1 | **Bottom house kit** (stacked cube house: walls, windows, doors, roof-floor, external stairs, balcony) | B | Bottom | pastel vertex colours per instance, 2 m grid |
| 2 | **Washing line + socks** | P | Bottom | doubles as a grapple rail |
| 3 | **Wok satellite dish** | P | Bottom | |
| 4 | **Lost & Found depot + the Machine** | L | Bottom | the hub, a ruined returns depot; the Machine is the original ☺ vending machine, hero-quality (glowing glass with a tiny sim world inside, a tray you get dispensed from) |
| 5 | **Auntie Spreadsheet** | C | Bottom | old normal (85, pre-war), grid dress, crayon behind her ear, huge glasses, an old ☺ CORP auditor's badge |
| 6 | **Lumps** | C | Bottom | small head, gigantic veiny forearms, gold rings, tie-dye tee, sunglasses |
| 7 | **Wee Gordo** | C | Bottom | huge sagging lipped face, spiky hair, pink sweater, hunched |
| 8 | **Bottom local (normal) ×3 variants** | C | Bottom | tie-dye, scooter kid, cook |
| 9 | **Sofa-car** | V | Bottom | a drivable car body with a sofa on top |
| 10 | **Gut tunnel kit** (intestine tube street pieces: straight, bend, junction, ramp) | B | Gut | ribbed, pulsing |
| 11 | **Rib arch** | P | Gut | spans an avenue |
| 12 | **Lung trampoline** | P | Gut | inflate/deflate animation |
| 13 | **Overgrown shopfront** (a launderette with skin and a tongue door) | B | Gut | |
| 14 | **Teeth cobbles + vein cables + gutter eyeballs** (scatter set) | P | Gut | instanced |
| 15 | **The Big Stomach** | L | Gut | acid-lake crater, boss arena |
| 16 | **Gut Choir singer** | C | Gut | robed puppet, stretched smile, ×2 variants |
| 17 | **Stomach-dog** | C | Gut | an ambient creature |
| 18 | **Meat Mechanic + clinic chair** | C+P | Gut border | many arms, butcher apron |
| 19 | **MR. OVERTIME** | C | (nemesis) | 4.5 m, punch-clock chest, stapler arms, own rig, max effort |
| 20 | **Cracked Punch-Clock core** | P | — | the first organ core (pickup + installed look on the player's chest) |
| 21 | **Organ core set: Second Stomach, Deposit Gland** | P | — | pickups + installed looks |
| 22 | **Implant looks: Pigeon Eyes, Spring Knees** | P | — | attach to the mannequin |
| 23 | **Punctuality Officer** | C | Corp | mannequin cop: whistle, clipboard, peaked cap |
| 24 | **Timekeeping cruiser** | V | Corp | white/cyan cop car based on the saloon in `cars.js`, clock-face light bar |
| 25 | **Unpaid raider** ×2 variants | C | Commute | interns in office-chair and filing-cabinet armour, lanyards, a traffic-cone helmet |
| 26 | **Late Desk** | P | all | the pay-your-fees kiosk |
| 27 | **Safehouse props** (bed, locker, wardrobe, garage door) | P | all | |
| 28 | **Loot crate + rarity beam** | P | all | colour per rarity, ☺ PREMIUM gets a pink choir glow |
| 29 | **Ruin kit** (rubble piles, broken walls, fallen ☺ sign, dead-car shells from `cars.js` models, filing-cabinet barricade, ☺buck fire barrel, a broken district clock) | P | all | instanced scatter |
| 30 | **Gut border gate** (the place the Bottom turns into the Gut, flesh creeping over pastel houses) | L | Bottom/Gut | the first nemesis arena |

After the slice: Pinstripe (Don Grinaldi, Pip Grinsworth, Long Larry, the Villa, marionette strings), the Checkout
(the Cart Mother, mall kit), Corp Hill (the Spire, office kit), and so on, district by district.
