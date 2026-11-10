// PATCH NOTES: what changed, newest first, in the game's voice. Add an entry here with every update that players notice.
// The menu link shows a NEW badge until you open the page after a new entry (remembered in localStorage).
export const PATCH_NOTES = [
  { v: '7.1', date: '2026-11-10', title: 'LESS SMALL PRINT', items: [
    'PLANT & DEFUSE: the spammiest guns fire slower there (and only there). SMG 16 -> 13 shots a second, Belt Sander 12 -> 10, Lefty & Righty 9 -> 7.5 per hand, and the Sniper takes 1.33 s between shots instead of 1.1. aim more, hose less.',
    'captions that said what the button already said are gone: under CUSTOMIZE and CONTAINERS, on the mode pickers, in customize and in settings.',
    'a weapon\'s description shows the first time you hold it, not every time you press 1. gun game and infection stopped repeating their own name under their own name.',
  ] },
  { v: '7.0', date: '2026-11-10', title: 'AD SUPPORTED', items: [
    'new item: the LAPTOP. press G to open it at someone and their screen fills with pop-up ads for 7 seconds. they close them with the number on each ad. some ads ask ARE YOU SURE?. nobody in front of it: NO SIGNAL, and you keep the charge. a reverse card sends the ads back.',
    'bots carry laptops too. a bot reading ads aims worse. so do you.',
    'GUN GAME rolls a new ladder every match: 10 guns, 5 silly ones, 3 melee, then the spoon. weapons that sat out the last match go first. 16 more weapons can show up (shopping cart cannon, taser, slipper, big laser pointer...).',
    'CHARACTER has a joke body row: head size, butt size, and Mannequin / Male / Female builds. everyone sees it. looks only: your hitbox did not get bigger. nice try. some bots turn up with one too.',
    'bots finally learned to throw cards. they used to reach the card deck in gun game and just stand there holding it. forever.',
  ] },
  { v: '6.9', date: '2026-11-10', title: 'HONEST CHEATING', items: [
    'SPINBOT no longer grabs your camera. look around freely: every shot goes to whoever is closest to your crosshair (a green LOCKED diamond shows who). nobody near your crosshair, nobody gets shot.',
    'the spinbot leaves your own side alone now: teammates, and in zombies your squad (people and bots).',
    'the party popper works in zombies: it shoves zombies back like it shoves everyone else.',
  ] },
  { v: '6.8', date: '2026-11-07', title: 'SPRAY RANGE', items: [
    'TRAINING has a SPRAY RANGE now: a wall left of the firing line with a head ring 10 m out. step onto the sand and the plant & defuse guns kick like they do in P&D. hold fire, pull down, and the last spray\'s holes stay on the wall in hot pink. the rest of training is as dumb as ever.',
    'the little first-person spectate box in royale sits under the stats now instead of on top of them.',
  ] },
  { v: '6.7', date: '2026-11-07', title: 'LEARN YOUR SPRAY', items: [
    'plant & defuse sprays are learnable now: every auto gun climbs straight up, then sways left-right-left at the top, the SAME way every time. pull down against it and it stays on a head. running or jumping still sprays everywhere.',
    'online plant & defuse lobbies fill the empty slots with bots, so it\'s always 5v5.',
    'spectating no longer crashes when the player you watch pulls out a knife while aiming. the little first-person box sits lower so it doesn\'t cover the royale stats.',
  ] },
  { v: '6.6', date: '2026-11-07', title: 'THE SQUAD', items: [
    'ZOMBIES is always a squad of 4 now: bots fill the empty slots. when someone joins, a bot clocks out (with a few words in chat), and when someone leaves, a bot comes back. you can start zombies alone with 3 bots.',
    'squad bots actually play: they shoot, buy doors and guns, nail planks back on, grab drops, flip the power and revive you (people first).',
    'zombies show up in the end-of-match highlight now (it used to look like everyone died to nothing). and no kill effects in zombies: they just die like zombies.',
  ] },
  { v: '6.5', date: '2026-11-07', title: 'THE MANAGEMENT FEELS GENEROUS', items: [
    'every account gets +30 CRATES, +25 DUFFEL BAGS and +70 BOXES. log in and they\'re waiting (once per account, until dec 7).',
    'CONTAINERS: open them in bulk with x5, x10 or ALL. they all rattle and pop at once, the loot lands rarest first, and you can equip straight from the results. skip if you\'re impatient.',
  ] },
  { v: '6.4', date: '2026-11-07', title: 'WATER IS WET NOW', items: [
    'real water everywhere: waves sized to the pool or sea, a swell on the open sea, foam where it meets the shore, sky reflections, sun sparkles, and light wobbling on pool floors.',
    'splashes when anything hits water (you, bots, gibs, grenades, bullets, explosions). shallow water slows you down and goes shlp shlp. falling in the sea still means sleeping with the fishes.',
    'lava actually flows now: a cracking crust drifting over the glow, bubbles that pop into embers (islands volcano + floor is lava).',
    'fire actually burns: animated flames, smoke and embers with a flickering light on burning cars and the oil rig flare. platform has an oil slick, the bazaar dye vats are real dye.',
  ] },
  { v: '6.3', date: '2026-11-07', title: 'TACTICAL MODE (ALLEGEDLY)', items: [
    'PLANT & DEFUSE is 5v5 now. bots fill the empty spots, and a real player takes a bot\'s place. matches are 15 rounds at most: first to 8, sides swap after round 7, 7-7 goes to a decider.',
    'P&D gunplay works like a proper tactical shooter: the first shot standing still is near-perfect, every shot after it blooms, and each gun has its own spray pattern. tap and burst, don\'t hold.',
    'moving ruins your aim. walking is shaky, running sprays everywhere and jumping is a prayer. stop, then shoot.',
    'damage depends on where you hit: the AR one-taps heads up close, the DMR one-taps heads anywhere, the sniper one-shots bodies, shotguns only work close up. the crosshair shows your spread (settings can hide it), and hit markers show head / body / legs.',
    'dead in P&D? you spectate through your teammate\'s own eyes now. when spectating anywhere else, a little first-person box in the corner shows what they see.',
    'the gunplay changes are only in plant & defuse. everywhere else is still chaos.',
  ] },
  { v: '6.2', date: '2026-11-07', title: 'WHO\'S THE BEST AT WHAT', items: [
    'the LEADERBOARD has tabs now: OVERALL, QUICK PLAY, PLANT & DEFUSE, ZOMBIES and JANK ROYALE, each with its own boards.',
    'plant & defuse: rounds won, plants, defuses, clutches, combat score per round, headshot %. zombies: highest round, zombies killed, revives, planks nailed, credits spent, cheat machine rolls. royale: wins, top 3s, kills, damage, longest kill.',
    'real matches and accounts only. the per-mode boards start counting from today, so go take the #1 spots while they say "nobody yet".',
  ] },
  { v: '6.1', date: '2026-11-06', title: 'BOARD UP THE WINDOWS', items: [
    'ZOMBIES hurt less: a claw does 15 in round 1 (it was 40), going up 1 a round. after a claw lands nothing else can claw you for a split second, and an arrow shows where it came from.',
    'every window in the Dead Mall has 6 planks of mall junk nailed over it. zombies rip them off before they climb in. hold F near a window to nail them back (+10 a plank, first 20 a round).',
    'dead zombies sometimes drop power-ups for the whole team: any killstreak, plus TIP JAR (+400), RESTOCK (full ammo) and CLEAN-UP ON AISLE 5 (every zombie pops).',
    'THE CHEAT MACHINE: an arcade cabinet in the Arcade, once the power is on. pay, pull the lever, get 15-30 s of ONE AND DONE, TAX FRAUD, BOTTOMLESS MAG, ZOOMIES, BRAIN FREEZE, BIG HEAD MODE, VAMPIRE TEETH or BOUNCY CASTLE.',
    'CUSTOMIZE > LOADOUT has QUICK PLAY and ZOMBIES tabs. for zombies pick your start pistol, the G item you bring and a passive (Quick Hands, Trust Fund, Stubborn, Handyman, Lucky Foot, Thick Skin, Coupon Book, Second Wind).',
  ] },
  { v: '6.0', date: '2026-11-06', title: 'SERIOUS BUSINESS (MOSTLY)', items: [
    'PLANT & DEFUSE got a tight, CS-style shop: real guns only. 4 sidearms, 2 SMGs, 2 shotguns, 3 rifles, a DMR, the sniper and an LMG. you start with Plan B and a knife. bananas, bread and the other gimmicks stay home for this one.',
    'P&D utility is just three things now: night vision goggles (the flash), the smoke bomb and the frag. kill rewards, win money and loss bonuses work like you\'d expect. bots buy like real people (eco, force, full buy) and flash you mid-fight.',
    'JANK ROYALE: TAB opens your backpack. swap guns, drop stuff, use heals, keep walking. the full scoreboard moved to L.',
    'royale: no more night vision goggles anywhere. and the grapple has 2 charges now, 8 s each. no more infinite swinging. the ring by your crosshair shows them.',
  ] },
  { v: '5.9', date: '2026-11-06', title: 'DRESS YOUR KILLSTREAKS', items: [
    'killstreaks have looks now. CUSTOMIZE > KILLSTREAKS: every streak takes a wrap, and most get new models.',
    'wrecking ball: bowling ball, meatball, disco ball. giant duck: pool flamingo, robo duck, golden duck. chicken strike: pigeon raid, drone strike. moon boots: heelys, rocket sneakers, clown shoes. spinbot: halo, anime aura. spy satellite: pizza dish, cctv blimp.',
    'everyone else sees your look too. getting flattened by a disco ball is a lifestyle.',
  ] },
  { v: '5.8', date: '2026-11-06', title: 'SAT-NAV (MOSTLY RIGHT)', items: [
    'a minimap on every map and every mode (top left). it shows you, your team, the plant sites and the bomb. enemies blip red when they shoot, except in plant & defuse, where you have to actually listen. a spy satellite still shows everyone.',
    'settings > minimap: on/off, S/M/L, and turn with you or north up. royale keeps its own zone map, which now follows the same settings.',
    'bots dress themselves now. every bot rolls its own outfit, hair, accessories and weapon skins, and some show up as a corpo suit, a rat king, a mall cop, a delivery guy or a maid assassin. same bot, same fit, all match.',
    'bots talk. they brag after a cool kill, cope after a dumb death, and answer gg / ez / noob. each one has a personality (tryhard, polite, unhinged, corpo, or silent). settings > bot chatter turns them off.',
  ] },
  { v: '5.7', date: '2026-11-06', title: 'NO MORE OLD MODELS', items: [
    'CUSTOMIZE loads the real Blender models first: what you\'re looking at downloads first, the rest after, and a tile shows static until its model lands instead of flashing the old blocky one. on a slow connection the skin strip went from about 88 s to 11 s.',
    'the game downloads a lot less: models come compressed, and coming back later only fetches what changed.',
    'killstreak and item pictures are 3D now (moon boots, satellite, spinbot, medkit, shield bubble and friends), all lit the same way.',
  ] },
  { v: '5.6', date: '2026-11-06', title: 'THE STAFF ENTRANCE', items: [
    'the home screen\'s side menu got rebuilt as one thing instead of four different ideas glued together: fleshy plaques, each with a little 3D prop in a socket.',
    'CUSTOMIZE shows your own equipped gun, CONTAINERS is a crate that hops when you have some to open (with a count badge).',
    'leaderboard, settings, guide, lore and patch notes all match now (trophy, cog, guide book, a board-of-directors cat, clipboard). install app is a small link at the bottom.',
  ] },
  { v: '5.5', date: '2026-11-06', title: 'PLATFORM, REBUILT', items: [
    'PLATFORM is not a flat slab any more: it\'s GLUG OIL\'s offshore rig. a grated cellar deck over the sea, a main deck of pipes and containers, a drill floor under a 30 m derrick, living quarters with a galley and bunks, a helideck with a chopper on top, cranes, a flare boom, and THE SNACK RUN supply boat tied up below.',
    'Platform has its own Plant & Defuse version, the Snack Attack: the crew defends the rig, SLURP OIL raiders attack from a riser platform. A is the drill floor, B is the cellar wellbay.',
    'that\'s every map remade. thanks for falling off all of them.',
  ] },
  { v: '5.4', date: '2026-11-06', title: 'ISLANDS, REBUILT', items: [
    'ISLANDS got rebuilt from scratch: Mount Kaboom in the middle (a tiki village, a lava crater and a human cannonball pad), the Soggy Biscuit shipwreck with a crow\'s nest, a climbable lighthouse, Fort Splinter and Skull Rock, joined by rope bridges, a pier and sandbars.',
    'shallows round every beach, so you fall in the sea a lot less (the old Islands lost most deaths to falls). if you do go in, you sleep with the fishes.',
    'Islands has its own Plant & Defuse version: the Treasure Tour. tourists attack, pirates defend; A is the wreck, B is the lighthouse.',
    'fixed: an AFK bomb carrier could stall a Plant & Defuse round. bots that fall in the sea grapple back to land.',
  ] },
  { v: '5.3', date: '2026-11-06', title: 'SKYLINE, REBUILT', items: [
    'SKYLINE got rebuilt from scratch: towers above the dusk city, joined by sky bridges and cranes, with a rooftop park, a putt-putt course, a long neon corridor and helipads.',
    'Skyline has its own Plant & Defuse version now: A is the helipad, B is the observatory.',
    'fixed: the Plant & Defuse versions of Suburb, Desert, Bazaar, Rooftop and Skyline now get their own map\'s lighting instead of the default.',
  ] },
  { v: '5.2', date: '2026-11-06', title: 'TIDY MENU', items: [
    'the home menu is cleaner: CUSTOMIZE, CONTAINERS and LEADERBOARD on the left, a row of small buttons for settings, the guide, lore and patch notes, and PLAY on the right.',
    'your character stands in the middle in 3D holding your gun. click them for CHARACTER, click the gun for LOADOUT.',
    'CUSTOMIZE is one place now, with tabs for LOADOUT (pick weapons, your item and 3 killstreaks), WEAPONS (skins, wraps, charms, effects, finishers), CHARACTER (outfits) and GRAPPLE & SPRAY.',
    'the pause menu is just resume, customize, match settings, settings and quit.',
    'containers are 3D now: they rattle while the strip spins and burst open when you get your item. item icons come from the real models.',
  ] },
  { v: '5.1', date: '2026-11-06', title: 'LIGHTS ON', items: [
    'fixed: leaving the Dead Mall no longer steals the next map\'s lighting (the Scary Forest came out lit like a sunny day).',
    'REAL SHADOWS: the sun casts shadows from buildings, props and players now, and they follow you around the map.',
    'every map got its own lighting mood with coloured bounce light. neon signs and lamps throw little pools of light, and corners and overhangs get darker.',
    'your hands and gun get darker in the shade and pick up the map\'s light. on Too HD the Scary Forest flashlights cast shadows.',
    'new setting: Settings > Shadows (auto / off / low / med / high). auto follows your graphics preset: off on Potato, high on Too HD. if your frame rate drops, turn it down.',
  ] },
  { v: '5.0', date: '2026-11-06', title: 'THE LOCKER, REDONE', items: [
    'NEW CUSTOMIZE SCREEN: your weapons down the left, the one you picked huge in the middle (drag to spin it), its stats and your numbers with it on the right, and tabs along the bottom: SKIN, WRAP, CHARM, EFFECT, FINISHER.',
    'open a tab for a strip of tiles with a search box and filters. hover one to try it on the gun, click to equip.',
    'RANDOM: pick it in any tab and you get a random one you own every time you spawn.',
    'FAVOURITES: heart the ones you like (saved to your account), then tick "only use favourites" so Random only picks from those.',
    'every weapon has a mastery bar and shows its damage, fire rate, mag, reload and range. grapples and sprays are still under GRAPPLE + SPRAY.',
  ] },
  { v: '4.9', date: '2026-11-06', title: 'ROOFTOP, REBUILT', items: [
    'ROOFTOP got rebuilt from scratch: a block of rooftops over the city, joined by stair bridges and sky bridges, with a penthouse bar, a rooftop pool deck, a helipad and billboards. it has its own Plant & Defuse version too.',
    'the city below Rooftop and Skyline stopped flickering (stacked neon strips were fighting each other).',
    'bots on rooftop maps stop jumping off the edge.',
  ] },
  { v: '4.8', date: '2026-11-06', title: 'BLENDER ROUND 3', items: [
    'the zombie claw, the lasso (+ the Garden Hose skin), the Bubble Wand, the wrecking ball, the laser pointer, the instant camera, the Pop Quiz calculator and the night vision goggles all got real glossy models.',
    'THE OVERDRIVE RIG got rebuilt: hydraulics, chrome stacks, BONK and HUGS on the knuckles, a bobblehead on the dash. the missiles say RETURN TO SENDER.',
    'you can watch your instant camera photo develop now (the right way up). other people\'s night vision goggles flip up over their forehead instead of through their chin.',
    'fixed: the Scary Forest, Dead Mall, Jankburg and Suburb (Plant & Defuse) had no picture on their vote cards.',
  ] },
  { v: '4.7', date: '2026-11-06', title: 'UNTIL IT BREAKS', items: [
    'the WRECKING BALL and the OVERDRIVE RIG have no timer any more: they last until they break. the ball has 900 HP, the rig 1200 armour, and both drain slowly so they end on their own after about a minute.',
    'shots hit the ball or the rig, not you. no headshot bonus, and no single hit takes more than 120. lava, the zone and the void still get you.',
    'when it breaks you get knocked up out of the wreckage at your own HP. the kill feed says who BROKE it (it isn\'t a kill), and they get a shout.',
    'your own health bar for it in the HUD, and a bar over everyone else\'s.',
  ] },
  { v: '4.6', date: '2026-11-06', title: 'REMODEL', items: [
    'SUBURB, DESERT and BAZAAR got rebuilt from scratch, and each one has its own Plant & Defuse layout now (like Warehouse).',
    'SUBURB: two rows of houses you can go inside, a park with a playground in the middle, a canal with a boardwalk, a Mega-Mart, traffic, and a forest round the edge.',
    'DESERT: a western main street with a hotel and saloon, a water tower, an oasis, a railway with a mine tunnel, and a wall round the town. Plant & Defuse plays DRY GULCH, the payroll job.',
    'BAZAAR: rebuilt market streets with stalls, rooftops and new lanes, plus its own Plant & Defuse version.',
    'the Warehouse shredder is animated now, and the Backrooms pool water stopped shimmering.',
    'some hidden people and cats moved house with the remodel. go find them again.',
  ] },
  { v: '4.5', date: '2026-11-06', title: 'NEW HANDS WHO DIS', items: [
    'NEW HANDS on everything: chunky low-poly PS1 hands with real fingers that wrap round grips, triggers and handles, in your skin tone with your sleeve colour. no more tan boxes.',
    'the katana and knives got snappier: a wind-up, a whippy cut with a longer smear, a springy settle. knives flip and get caught, the katana twirls on inspect. hit timing hasn\'t changed.',
    'akimbo gets a real left hand, and so do reloads and the card deck.',
  ] },
  { v: '4.4', date: '2026-11-06', title: 'COSMETICS PACK 2', items: [
    '"too epic to skip" killcams are only for the sniper, Second Opinion and the revolver now. epic kills with anything else still count, but you can skip them.',
    'THE SPOON IS A KNIFE NOW. one weapon, not two: Gun Game\'s last rung is the knife in the spoon look (first kill with the spoon still wins), Spoons & Grapples is knives in the spoon look with one-hit kills. the Ladle became a knife skin and you keep it if you had it.',
    '27 NEW SKINS: Keytar (AR), Label Maker (SMG), Brolly (shotgun), Pool Cue (sniper), Take A Number (Hat Trick), Leaf Shredder (Belt Sander), Fountain Pen (Second Opinion), Cap Gun (Yeehaw), Weed Whacker (Lawn Mower), Calculator (Plan B), Walkie Talkies (Lefty & Righty), Pepper Mills (Half a Shotgun), Business Cards, Squirt Flower + Hose Nozzle (water pistol), Bug Zapper (taser), Game Pad (TV remote), Cordless Drill (revolver), Cat Laser, Baguette + Neon Tube katanas, Pizza Cutter, Keycard and Frozen Fish knives, Sliced Loaf, Flip-Flop.',
    '37 NEW WRAPS (102 total): a camo family, Brushed Steel, Damascus, Anodized Ti, Verdigris, Kitchen Granite, Marble, Jade, Amethyst Geode, Wood Burl, Moss, Sprinkles, Watermelon, Sushi, Memphis 90s, Bowling Alley, Arcade Carpet, Checkered Flag, Jersey, Barcode, QR Code, Organ Donor, Loaded Dice, Number Soup, Candy Corn, Ugly Sweater.',
    'animated legendaries: Opal, Lava Lamp, Vaporwave, Nebula, Aurora, Black Hole, Market Crash and Neon Hex.',
  ] },
  { v: '4.3', date: '2026-11-06', title: 'HOTFIX: EVICTION CANCELLED', items: [
    'fixed: after a Jank Royale match, every other mode stayed in battle royale (the EVICTION NOTICE, the zone and royale loot rules followed you into quick play and everything else).',
    'Quick Play\'s vote no longer offers Plant & Defuse, Jank Royale or Zombies. they have their own cards and lobbies now.',
    'Jank Royale only plays on Jankburg, the big city.',
    'fixed: night vision goggles vanished after both flashes in Jank Royale and Plant & Defuse. now only the flashes run out; the goggles stay on your face.',
    'fixed: the Blood Cross shoots again (the rifle pack mistook it for a burst rifle with no ammo).',
    'BACKROOMS: every doorway goes up to the ceiling now, so you can bhop and grapple through without smacking your head on the frame.',
  ] },
  { v: '4.2', date: '2026-11-06', title: 'LEGS DAY', items: [
    'everyone moves properly now: real strides for walk, run and sprint (feet stay planted), leaning and arm pumping, and a silly zooming pose past sprint speed.',
    'strafing and backpedalling read sideways and backwards. jumps have a wind-up, a tuck, a landing squash (bigger the further you fell), and bhop chains look rhythmic.',
    'MARBLE SLIPS are a proper pratfall: feet fly out, flat on your back with the gun in the air, kicking, then you get back up.',
    'Plant & Defuse slow walk is a sneaky tiptoe. crouch walking, sliding and hanging off a grapple got matched up.',
    'fixed: most players\' knees bent backwards (it was meant to be a rare jank quirk). now only the cursed ones do.',
    'your own gun bobs with your footsteps and stumbles when you slip (calmer with Screen Shake off).',
  ] },
  { v: '4.1', date: '2026-11-06', title: 'HOLD IT RIGHT', items: [
    'THE KATANA IS HELD LIKE A KATANA: two hands on the grip, big two-handed cuts both ways, an iai draw, a proper inspect (with a blood flick) and a two-handed parry. other players see both hands on it too. the timing hasn\'t changed.',
    'THE BUTTERFLY KNIFE does real flips now: the handles swing round the pivot, with fan, rollover and aerial tricks.',
    'melee fixes: the knife, spoon, slapper and karambit stabs no longer point the blade away from you, and bread got its own draw.',
    'EVERY GUN HAS A RELOAD: mag swaps on the AR and SMG, shell by shell on the shotgun, bolt work on the sniper, a speedloader on the revolver.',
    'the silly ones: a jerry can for the Redline, a tiny arm shoving the minigun belt in, a little hammer for the nail gun, a bag of marbles tipped into the jar, soul shells for the reaper rifle and a juice box for the water pistol.',
    'reloads now end exactly when the ammo refills, at any framerate.',
  ] },
  { v: '4.0', date: '2026-11-06', title: 'THE WRAP PACK', items: [
    '48 NEW WRAPS (65 total). commons come in every colour: Cherry Pop, Tangerine, Lemon Drop, Lime, Mint, Pool Tile, Sky, Navy, Grape Soda, Hot Magenta, Cream, Matte Black, Fridge White, Bubblegum, Creamsicle, Ketchup & Mustard, Hazard Stripes, Hi-Vis.',
    'PORCELAIN: Grandma\'s China, Crackle Glaze, and the legendary Kintsugi (gold in the cracks).',
    'JAPANESE: Seigaiha, Asanoha, Shibori, Washi Paper, Sakura Storm, Koi Pond, Big Wave, Urushi Maki-e, and the legendary Tokyo Night.',
    'AND THEN IT GOT WEIRD: Bubble Wrap, Swiss Cheese, Denim, Dad Plaid, Receipt, Pizza, Leopard, Zebra, Stained Glass, Circuit Board, CRT, Spreadsheet, Corporate Memo, Holo Foil, Liquid Chrome, Datamosh, Meat Suit and ☺ CORP.',
    'every legendary moves. all of them work on every gun in normal, reverse and full.',
    'they drop from boxes. the locker\'s wrap list has rarity and owned filters and a search box now.',
  ] },
  { v: '3.9', date: '2026-11-06', title: 'PICK YOUR POISON', items: [
    'NEW MENU: ONLINE and WITH BOTS. both open four cards: QUICK PLAY, PLANT & DEFUSE, JANK ROYALE and ZOMBIES, and each card shows how many real people are in it right now.',
    'ONLINE is real players only. no bots, ever. Plant & Defuse and Jank Royale need 2 players to start, Zombies 1.',
    'LOBBIES for Plant & Defuse, Jank Royale and Zombies: run around in a warm-up (nothing counts) while a 60 s countdown ticks. press Y (rebindable) to READY UP. everyone ready = 5 seconds.',
    'once a match starts it\'s locked. anyone who picks that mode after gets a fresh lobby. after the match, a quick 10 s lobby keeps your group together.',
    'QUICK PLAY has no lobby: drop in anytime. with bots you take a bot\'s place. WITH BOTS > CUSTOM is the old setup screen (any mode, map, bots, difficulty).',
  ] },
  { v: '3.8', date: '2026-11-06', title: 'FRESHLY MODELLED', items: [
    'BLENDER ROUND 2: the cigarette and cigar, card deck (and the cards you throw), Reverse and Skip cards, leaf blower, snowball, popper, rubber duck, bread, spoon, slipper, Hand Slapper, the bow and its arrows and the Scythe Rifle all got real glossy models.',
    'all 29 weapon skins got remade too. the Spoon knife skin is a proper tablespoon now.',
    'knives and katanas got the same gloss, so they read as polished steel.',
    'the Zombies wall boards hang the real models.',
    'fixed: chrome showed up black in the hotbar, the locker and the menu.',
  ] },
  { v: '3.7', date: '2026-11-06', title: 'LAW & DISORDER', items: [
    'NEW ITEM: SPEED TRAP. hold G to point a radar gun at people. over 100 km/h they get SLOW DOWN 3.. 2.. 1. slow down and it\'s a warning, keep speeding and it\'s JAIL (a cage drops on them for 3.5 s). over 200 is jail on the spot.',
    'WATER PISTOL: soaks people for 4 s. soaked = slower and slidey, and it puts out fire.',
    'TASER: a 1 s stun that chains through everyone soaked nearby. bring a friend with a water pistol.',
    'TV REMOTE: left click PAUSES someone for 1.2 s (their momentum comes back after). aim to REWIND them 2 s back to where they were.',
    'all four are in Plant & Defuse, the three secondaries are in the Zombies crate, and bots use them.',
    'fixed: melee weapons swing on left click again (a stray comment ate it in the rifle pack update).',
  ] },
  { v: '3.6', date: '2026-11-06', title: 'SIDEARMS', items: [
    'PLAN B: a plain semi-auto pistol. for when everything else is empty.',
    'LEFTY & RIGHTY: two machine pistols. left click fires the left one, your aim key fires the right one. each hand has its own mag and reloads on its own.',
    'HALF A SHOTGUN: a sawed-off with two shells. point blank it deletes people, knocks them back, and the kick hops you off the floor.',
    'all three are Jank Royale floor loot, in the Zombies crate (with wall ammo) and in Plant & Defuse with their own spray patterns.',
  ] },
  { v: '3.5', date: '2026-11-06', title: 'HARDWARE STORE', items: [
    'NAIL GUN: fires nails, fast. land six in a row and they get nailed to the wall behind them like a poster. the nails stay in the walls.',
    'TENNIS BALL LAUNCHER: fuzzy balls bounce up to 5 times and hit 30% harder every bounce. bank it round a corner for a BANK SHOT.',
    'SHOPPING CART CANNON: fires a shopping cart that runs people over. it stays parked as cover, or walk up and hop in (your use key) to ride it.',
    'all three are in Plant & Defuse and the Zombies mystery crate. each comes with a skin.',
    'fixed: in Plant & Defuse, slow walking with the lasso out made it spin (and spinning it made your footsteps silent).',
  ] },
  { v: '3.4', date: '2026-11-06', title: 'THE RIFLE PACK', items: [
    'HAT TRICK: a burst rifle. three rounds a pull. land all three on one person for a BURST!',
    'BELT SANDER: an LMG with a 100-round belt you can watch run out and a barrel that glows the longer you hold it. slow to aim, slow to reload.',
    'SECOND OPINION: a marksman rifle. two to the body or one to the head. quick-scope it for a little extra.',
    'YEEHAW: lever-action. crank after every shot, and every hit on the same person stings more. spin-cocks on reload, obviously.',
    'LAWN MOWER: an automatic shotgun with a box mag. less per shot than the pump, but it never stops.',
    'all five are in Plant & Defuse (with their own spray patterns), the Zombies mystery crate, and three of them hang on the Dead Mall walls.',
  ] },
  { v: '3.3', date: '2026-11-06', title: 'YEEHAW', items: [
    'NEW SECONDARY: THE LASSO. hold fire to spin the loop, let go to throw it. catch someone and they dangle off your rope.',
    'reel them in or let the rope out with the mouse wheel (or R / F, rebindable). swing them round, walk backwards, flick: click to let go and they fly. walls and floors hurt.',
    'caught? mash jump or a move key to wriggle free.',
    'in Plant & Defuse it costs 1100 for 10 throws. not in Jank Royale or Zombies. bots use it too.',
  ] },
  { v: '3.2', date: '2026-11-06', title: 'THE BOARD WILL SEE YOU NOW', items: [
    'HIDDEN PEOPLE: five ☺ CORP employees are hiding around the maps. walk up and press your use key to talk. they know how things got like this, and some of them have something for you.',
    'every chapter of lore you find goes on the new LORE page in the menu.',
    'THE BOARD OF DIRECTORS: five cats are hidden on five maps. pet all of them for the BOARD APPROVED achievement: Cat Ears, a Cat Tail and the Maid Dress.',
    'hint: not everyone is on the ground. bring a grapple.',
  ] },
  { v: '3.1', date: '2026-11-06', title: 'PLANT & DEFUSE, BUT TACTICAL', items: [
    'PLANT & DEFUSE ONLY: no enemy outlines and no nametags. you find people the old way.',
    'hold SHIFT (your sprint key) to slow walk: half speed, and nobody hears your footsteps. moving wrecks your aim, so stand still (or crouch) to shoot straight.',
    'guns kick in their own recoil patterns now. learn them.',
    'gimmick weapons (slippers and friends) have limited ammo here, and the strong stuff got nerfed. buy with B, drop with H (both rebindable in Settings > Key bindings).',
    'PLAY WITH BOTS: players who join take a bot\'s place. ONLINE rooms are players only now.',
    'bots plant, hold the sites properly and defuse. defenders no longer wander into the attackers\' spawn on Bazaar.',
  ] },
  { v: '3.0', date: '2026-11-06', title: 'ZOMBIES', items: [
    'NEW MODE: ZOMBIES. co-op against endless rounds of the undead on a new map, the DEAD MALL. pick it in BOTS (Game: Zombies) or vote for it online.',
    'start with 500 credits, a Revolver and a knife. hits and kills pay, headshots and knife kills pay more. hold your use key on a roller shutter to open an area, on a wall gun to buy it (or its ammo), or on the mystery crate for a random gun.',
    'find the power switch in the Loading Dock: lights on, and the JANK COLA machine works (zombies hit you half as hard). a friend goes down? hold use on them to revive. everyone down = game over.',
    'KEY BINDINGS: Settings > Key bindings. rebind every action to a key or a mouse button, with a second slot for each. new: Katana parry (right click) and Goggles flash (middle mouse or N, off H).',
    'the guide, the vote cards and every prompt show your own keys.',
  ] },
  { v: '2.9', date: '2026-11-06', title: 'THE SCARY FOREST', items: [
    'NEW MAP: SCARY FOREST. a pine forest at night, in the fog, by a lake. cabins, a dirt road and not much light.',
    'the TALL GUY FROM HR lives here. he only moves when nobody is looking at him. staring at him fills your screen with static. if he reaches you, you get transferred.',
    'night vision goggles cut through the fog, so you can spot him from further away.',
    'tall guy from HR can be set to off, rare, on or lots in the match setup.',
  ] },
  { v: '2.8', date: '2026-11-06', title: 'JANK ROYALE', items: [
    'NEW MODE: JANK ROYALE. ride the JANK AIR blimp, jump, glide down under an umbrella, loot the floor, stay in the zone. last idiot standing wins.',
    'LOOT: guns with real ammo in 5 rarities (Rare and up have light beams), gadgets, Jank Cola and Medkits (H), and armour: Cardboard Plate, Bin Lid Vest, Riot Fridge. F picks up or swaps.',
    'NEW MAP: JANKBURG, a whole walled city. Liberal Lane (liberal helpings), Pronoun Park (no names, only pronouns), Overdraft Heights (negative gravity), Number Works, Neon Market and Corp Hill each bend a rule while you are inside.',
    'TWISTS: Return to Sender (die early and get mailed back once), a glowing kill-leader bounty, a zone wall that shoves, supply crates from the blimp and loot goblins that run off with Epics.',
    'bots play it: they drop somewhere sensible, loot, heal, pick the right gun for the range, third-party fights and rotate with the zone.',
  ] },
  { v: '2.7', date: '2026-11-06', title: 'THE REAL PLACES UPDATE', items: [
    'TRAFFIC: cars, vans, buses and trucks drive the roads on Suburb, Warehouse, Desert and the city under Skyline and Rooftop. a slow bump shoves you, a fast one sends you flying. two cars crashing explode. shove someone into a car and it is your kill. off in Plant & Defuse.',
    'SMARTY PANTS: answer 3 Pop Quiz questions right to unlock the achievement, the Big Glasses and the Overalls (the first locked pants).',
    'MAP PASS: every map sits in a real place now, with scenery out to the horizon instead of a platform in the void.',
    'SKYLINE + ROOFTOP: a whole city far below the towers, in the haze. the roads run on into the city.',
    'WAREHOUSE: remade, with racks, forklifts and pallets inside, a fenced yard, machinery outside the gate and a wood round the fence. Plant & Defuse gets its own Warehouse with three lanes.',
    'SUBURB sits in a forest now. the BACKROOMS have higher ceilings. DESERT, BAZAAR and the rest got scenery and fixes (stairs, spawns, flickering floors).',
    'RETURN TO THE MAP: leave the play area and you get 3.. 2.. 1.. to come back, then BYE. whoever pushed you out gets the kill.',
    'the void is lower on every map, so falls last longer.',
  ] },
  { v: '2.6', date: '2026-11-06', title: 'THE TACTICAL UPDATE', items: [
    'fixed: getting flashed and then dying (or respawning) no longer snaps your hearing back. the ringing runs its course and fades out.',
    'OVERDRIVE RIG: a tap of SPACE now jumps about 6 m straight up with a heavy landing. E fires boot + back thrusters (3 charges, refill fast) that work in the air. the quickhack moved to R.',
    'PLANT & DEFUSE got an economy: earn money for kills, wins and plants, then spend it in the BUY PHASE (B). guns, armour (Padded Vest, Vest + Bucket), defuse pliers, frags, smokes and every item.',
    'lose a round and you get a loss bonus. drop guns for your team (H), pick them up (E). a fresh kit after a death, your bought gear if you live.',
    'BOTS PLAY IT AS A TEAM: they buy by the economy (eco / force / full), group up and execute a site with smokes and frags, plant safe, hold, rotate, retake together, defuse with pliers and save when the round is lost.',
  ] },
  { v: '2.5', date: '2026-11-06', title: 'THE LOUD UPDATE', items: [
    'MUSIC: 6 original gabber / hard tek tracks plus Untitled. Jank Cola Rave, Spoon Fight Tekno, Rubber Duck Hardcore, Hung Jury Hardcore, Banana Peel Acid, Wrecking Ball Warm-Up.',
    'music on the menu, a new song every match, and the end-of-match music under the vote. it ducks for the play of the round and killcams.',
    'SETTINGS > AUDIO: music volume, music in matches, match music volume, and a separate switch for competitive (off by default in Online and Plant & Defuse).',
  ] },
  { v: '2.4', date: '2026-11-06', title: 'THE GADGET UPDATE', items: [
    'BIG LASER POINTER: a new primary. hold to charge, let go to fire a thick beam that goes through people. tap for a weak one.',
    'INSTANT CAMERA: G takes a photo of where you stand. G again prints it as a frame. walk into the frame and you are back where you took it (so can anyone else).',
    'POP QUIZ: throw a calculator. whoever it hits freezes and gets a maths question. wrong or too slow and they die. right and they get a buff and a few seconds of invulnerability.',
    'NIGHT VISION GOGGLES: G puts them on, the dark goes green and people glow. middle click (or N) flashes everyone you can see. flashbangs hurt you more while you wear them.',
    'the Spoon is gone from the loadout: it is a knife skin now. Gun Game\'s last rung and Spoons & Grapples still hand you one.',
  ] },
  { v: '2.3', date: '2026-11-06', title: 'THE OVERDRIVE UPDATE', items: [
    'NEW KILLSTREAK: the OVERDRIVE RIG. become a scrap-built exo-frame: rocket punch, block, grapple quickhack, homing missiles, crater leaps. bots use it too.',
    'NEW MENU + END SCREEN: the whole UI went organic. the end of a match plays the play of the round, then you vote the mode, then the map.',
    '/skip: hate this mode? type /skip in chat. more than half the room has to agree (alone it is instant).',
    'GLOSSY GUNS: 11 guns rebuilt in Blender with real sights, plus props on Suburb and Warehouse (cars, a bus, forklifts, racks, number balls).',
    'TWO-TONE WRAPS: wraps paint part of the weapon now. NORMAL = handle, REVERSE = blade / barrel, FULL = the old look.',
    'BLAST ZONE: a new legendary kill effect. knocked clean off the screen, with a burst of colour.',
    'SPOON: a new epic knife skin. it is a spoon. it still stabs.',
    'CIGARETTE: hold it into TOO MUCH and you cough a cloud of smoke instead of fire. everyone sees you cough.',
    'THE CLASSIC GRAPPLE IS BACK: the hard pull and the big grapple jump from update 1.',
    'MARBLES: the Marble Shotgun finally leaves marbles on the floor that make people slip. crouch-walk to cross.',
    'SNIPER ROYALTY is 3 boxes now: a long shot, a quick-scope OR a no-scope, and a headshot. old progress counts.',
    'LOCKER: hover anything (skins, wraps, hats, outfits) to try it on, locked or not. copy-to-every-weapon starts unticked.',
    'the play of the round can no longer be skipped. witness greatness.',
    'Duck Rain ducks fall straight down now, so you can dodge them. only a thrown duck homes in.',
    'fixed: pausing and resuming in Infection told you you were infected again.',
  ] },
  { v: '2.0', date: '2026-11-05', title: 'UPDATE 2', items: [
    'NEW GEAR: Bubble Wand, Scales of Justice, Shredder, Blood Cross, Golden Sniper (earn it with Sniper Royalty), Runner Jacket.',
    'NEW KILLSTREAK: the Wrecking Ball. roll, chain-swing, ram, slam.',
    'NEW MODES: Gun Game, Infection, Spoons & Grapples, Duck Rain, Floor Is Lava, One in the Chamber.',
    'NEW MAP: the Backrooms.',
    'revolver twirl + fan the hammer, katana parry, no-scope hype, headshot DINK / TONK, homing slippers, sprays (Z), grapple skins.',
    'EPIC kills can not be skipped. Never Landed: finish a match without touching the ground.',
  ] },
  { v: '1.2', date: '2026-11-04', title: 'UPDATE 1.2', items: [
    'the sleep arrow knocks you flat for 4 s, and everyone sees it.',
    'Training: your 3 picked killstreaks are always ready (a used one comes back 3 s after it runs out).',
  ] },
  { v: '1.1', date: '2026-11-04', title: 'UPDATE 1.1', items: [
    'sniper knockback is back (the minigun and the sniper are the only guns that shove).',
    'killcam fixes: the victim stays put until the killing shot, then explodes.',
  ] },
  { v: '1.0', date: '2026-11-04', title: 'UPDATE 1', items: [
    'weapon feel pass, new guns: Marble Shotgun and Redline. one hotbar, corner killstreaks.',
    'rebuilt knife and katana models. sniper headshots kill, revolver headshots do 96.',
    '74 fixes and a crash-proof server.',
  ] },
];
const SEEN = 'jf_patch_seen';
export const patchUnseen = () => { try { return localStorage.getItem(SEEN) !== PATCH_NOTES[0].v; } catch { return false; } };
export function markPatchSeen() { try { localStorage.setItem(SEEN, PATCH_NOTES[0].v); } catch { /* private mode */ } }
export function renderPatchNotes(el) {
  el.innerHTML = '';
  PATCH_NOTES.forEach((n, i) => {
    const card = document.createElement('section'); card.className = 'pn' + (i === 0 ? ' latest' : '');
    const h = document.createElement('header');
    const tag = document.createElement('b'); tag.className = 'pnv'; tag.textContent = 'v' + n.v;
    const t = document.createElement('h3'); t.textContent = n.title;
    const d = document.createElement('span'); d.className = 'pnd'; d.textContent = n.date;
    h.append(tag, t, d);
    const ul = document.createElement('ul');
    for (const it of n.items) {
      const li = document.createElement('li');
      const m = /^([A-Z0-9 /&'.:+-]{3,}?):\s(.*)$/.exec(it); // "BIG THING: the rest" gets a bold lead-in
      if (m) { const b = document.createElement('b'); b.textContent = m[1] + ': '; li.append(b, m[2]); } else li.textContent = it;
      ul.append(li);
    }
    card.append(h, ul);
    el.append(card);
  });
}
