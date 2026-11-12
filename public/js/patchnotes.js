// PATCH NOTES: what changed, newest first, in the game's voice. Add an entry here with every update that players notice.
// The menu link shows a NEW badge until you open the page after a new entry (remembered in localStorage).
export const PATCH_NOTES = [
  { v: '11.3', date: '2026-11-12', title: 'MAY CONTAIN NUMBERS', items: [
    'jankburg: number works got its factory back. brick smokestacks with blinking red lights, rusty vats of glowing green soup (may contain numbers), and chrome pipes on steel legs.',
  ] },
  { v: '11.2', date: '2026-11-12', title: 'GLINT', items: [
    'RAY-TRACED LOOK: props, buildings, mechs and your gun now reflect the world around them, with a sun glint on shiny paint and chrome. they pick up the bounced light too, so they stop looking flat. bounce light and soft shadows got stronger and now cover all of jankburg.',
  ] },
  { v: '11.1', date: '2026-11-12', title: 'SO DID THE CORNER', items: [
    'jankburg: the houses got walls, windows, stairs and real roofs. the streets got rearranged a bit while we were at it. your favourite corner might have moved. so did the corner.',
  ] },
  { v: '11.0', date: '2026-11-12', title: 'BEEP BEEP', items: [
    'your own mech can\'t squash you any more. stand on your own circle and it goes BEEP BEEP and bonks you out of the way, then you can climb straight in. your squad gets bonked too. enemies still get flattened.',
    'zombies (and every death): body parts and gibs don\'t hang in mid-air any more. they fall, bounce, settle on the floor and fade.',
    'zombies: the grappling hook has charges now, like jank royale. two ropes, one comes back every 8 seconds. the ring by your crosshair shows them.',
  ] },
  { v: '10.9', date: '2026-11-12', title: 'LOADS LIKE IT MEANS IT', items: [
    'the game loads a lot faster the second time you open it: your browser keeps this version\'s code instead of asking for 300 files again. an update still gets you the new stuff straight away.',
  ] },
  { v: '10.8', date: '2026-11-12', title: 'PLEASE REMAIN SEATED', items: [
    'jankburg: the cathedral of shareholder value got pews, a real bell and an organ made of servers. the sermon is a quarterly earnings call. please remain seated.',
  ] },
  { v: '10.7', date: '2026-11-12', title: 'NOBODY HAS EVER LEFT', items: [
    'jankburg: jankcorp hq is a real skyscraper now. glass setbacks, a revolving door, gold letters and a lit crown. the lights are on in some offices. they are always on. nobody has ever left.',
  ] },
  { v: '10.6', date: '2026-11-12', title: 'PUTT INTO ITS MOUTH', items: [
    'skyline: the skyscrapers are real buildings now. brick tenements with fire escapes, office towers with chrome fins, lit offices and neon blade signs.',
    'skyline: the bridges off the spire got steel. portal frames on the glass tubes, big blue trusses under the open ones. the sky stairs are proper steel stairs with handrails and neon. still 160 m of air underneath.',
    'skyline: putt putt palace got a real windmill and a giant clown head. putt into its mouth. you can\'t.',
  ] },
  { v: '10.5', date: '2026-11-12', title: 'SHINY', items: [
    'RAY-TRACED LOOK now has reflections: glass towers, office windows, wet roads and chrome reflect the world around you. its own checkbox in settings > video > shaders.',
  ] },
  { v: '10.4', date: '2026-11-12', title: 'NOBODY TOUCH THE TRAIN', items: [
    'crate: the playroom is full of real toys now. crayons that are actually round, a ball that is actually a ball, a bed, and a train set nobody is allowed to touch.',
  ] },
  { v: '10.3', date: '2026-11-12', title: 'HAVE A NICE DAY', items: [
    'jankburg: the city gates got toll booths, boom barriers and big name plates. the toll is your dignity. have a nice day.',
    'warehouse plant & defuse: the defenders spawn behind a real office block now. lit windows, a staff entrance, a NO LOITERING sign nobody reads.',
    'zombies: the mystery crate is a real crate now (glowing ??? and a padlock nobody locked), and the power switch is a big copper knife switch you get to SLAM up. works in all three zombies maps.',
    'suburb: the playground got rebuilt by professionals (the hoa). the slide is an actual slide now. read the rules.',
  ] },
  { v: '10.2', date: '2026-11-12', title: 'RAY-TRACED (ISH)', items: [
    'new shader level: RAY-TRACED LOOK (settings > video > shaders). sunlight bounces off the ground and walls onto everything around it, and corners and contact spots get soft shadows. on by default on too hd, opt-in on mid. potato stays potato.',
    'battle island\'s grass got deeper, sunnier and blotchier. in a good way.',
    'in a mech, the wrecking ball or the overdrive rig, your normal weapon bar gets out of the way, then pops back when you hop out.',
    'jankburg: the firewall\'s towers got windows, a STAFF ONLY door and a smiley the size of a bus. the jump pads still work. security is watching (badly).',
  ] },
  { v: '10.1', date: '2026-11-12', title: 'THE SHED GOT DRESSED', items: [
    'warehouse: the hall is a real depot now. pink trim, roller doors, numbered docks, yellow girders and lamps that look like lamps. same walls, same windows to get shot through.',
    'battle island: your party lands in the same squad. a party bigger than a squad splits into full squads. friends who join late go to your squad.',
    'platform: the wellheads on b site are dressed up as christmas trees. star, tinsel, fairy lights, a santa hat. still full of oil.',
    'skyline: the helipad got its gear. JET A-1 tanks, a flight-ops shack, a windsock, and a fuel truck parked on a site.',
  ] },
  { v: '10.0', date: '2026-11-12', title: 'ASKS FIRST', items: [
    'closing or reloading the tab mid-match now asks first, in every mode. the exe closes normally.',
    'battle island and training got their own pictures in the mode picker. the dummy is very excited about the target on its chest.',
  ] },
  { v: '9.9', date: '2026-11-12', title: 'IT SAW THAT', items: [
    'crate: the tower is real toy blocks now. carved wooden faces, chunky letters, it spells JANK if you fall far enough. the middle block is a shape sorter.',
    'skyline: the observatory got a real dome and a real telescope. b site has never looked so scientific.',
    'skyline: JANK NEWS 7 is parked on the helipads. it saw that.',
  ] },
  { v: '9.8', date: '2026-11-12', title: 'BRING FRIENDS', items: [
    'PARTIES. your code\'s under ONLINE / OFFLINE. send it to your friends, they type it in, you all stand there looking cool. the leader picks the match and drags everyone in. same team, obviously. kicking is allowed.',
    'ctrl+w can\'t close the game any more in fullscreen (crouch is left ctrl too, oops). windowed, you get a tip once.',
    'backrooms: the walls are real now. wallpaper seams, skirting boards, outlets nobody uses, a thermostat set to "yes", damp creeping up from the carpet and paper peeling off the top. it\'s worse.',
    'platform: the oil derrick is a real lattice tower now. crown, beacon, top drive, a little platform halfway up, and the GLUG OIL sign.',
  ] },
  { v: '9.7', date: '2026-11-12', title: 'HE OWNED ALL OF THIS', items: [
    'suburb: the founder\'s statue got an upgrade. granite plinth, brass plaque, tulips, and the founder himself as a shiny toy bust. he has a monocle now. a pigeon has opinions about his hat.',
    'smoother edges on mid and too hd (with shaders on). less shimmer on thin lines and far-away stuff. potato stays crunchy.',
  ] },
  { v: '9.6.1', date: '2026-11-12', title: 'SWIM NORMAL', items: [
    'fixed: swimming out to sea made the camera glitchy (things right in front of you blinked in and out). the sea counts as the floor again.',
  ] },
  { v: '9.6', date: '2026-11-12', title: 'LEAVING THE PRODUCT', items: [
    'jankburg: the firewall got a real wall. precast concrete, pink neon, cameras, a walkable top with a yellow line. it says FIRE WALL on it now so you know which one it is. you are now leaving the product.',
  ] },
  { v: '9.5', date: '2026-11-12', title: 'SHAKE BEFORE THROWING', items: [
    'skyline: the giant jank cola can is an actual can now. candy red, condensation, a pink ring pull. 0% real cola. shake before throwing.',
    'skyline: the building-site crane is a real crane now. lattice, cab, counterweights, a big red hook. mr. smiles says the view hasn\'t changed.',
    'offline matches got simpler: pick the map and how many bots. how hard they try and how wobbly your hipfire is are no longer your problem.',
  ] },
  { v: '9.4', date: '2026-11-12', title: 'IT MEANS IT', items: [
    'islands: mount kaboom finally looks like it means it. smoke you can see from the beach, lava that glows, a lava pool in the crater (still a pit. don\'t), stripy rock and a little jungle round its feet.',
  ] },
  { v: '9.3', date: '2026-11-12', title: 'STOP FLICKERING', items: [
    'roads, sidewalks and crossings stopped flickering when you look down from up high (the blimp, gliding, tall buildings). jankburg looks like a city again instead of static.',
  ] },
  { v: '9.2', date: '2026-11-12', title: 'DO NOT FEED IT', items: [
    'jankburg: the smiling fountain got a glow-up. glossy smiley face, one eye wandering, a grin spitting water into a marble pool full of coins. it\'s still smiling. it\'s always smiling. do not feed it.',
    'training got a real firing line: a proper range bench with earmuffs and spent brass, actual sandbags (one says SAND?), and signs telling you how far you\'re missing by.',
  ] },
  { v: '9.1', date: '2026-11-12', title: 'FRONT DOOR', items: [
    'new main menu. it\'s you in the middle and two buttons: ONLINE or OFFLINE. then pick your mode along the top. TRAINING and the old menu (CLASSIC) are still under the buttons.',
    'OFFLINE is your own match: pick the map, the bots, how many, how hard they try. nobody else gets in. that\'s the point.',
    'skyline: the spire got a glow-up. a real glass tower now, chrome fins, lit offices, neon rings and a radio mast with a blinking red light. still can\'t climb the spikes.',
    'mechs make noises when they show off now: glints, vent hisses, flare whoomphs, sparks, and a pop when you eject.',
  ] },
  { v: '9.0', date: '2026-11-12', title: 'ISLAND TIME (BETA)', items: [
    'NEW (BETA): BATTLE ISLAND. squads of 3 in the royale. get knocked down instead of dying, and hold F to pick your squadmates back up. through a wall doesn\'t count.',
    'on the blimp, pick your mech hero: PAPER PLANE or NIGHT SHIFT. fill your MECH METER (time, damage, kills, green batteries on the floor), then press 5 to drop your mech on your crosshair. not into the sea.',
    'how to play: With Bots > CUSTOM > BATTLE ISLAND (BETA). the island itself is still being built, so it\'s on jankburg for now. more heroes coming.',
  ] },
  { v: '8.9', date: '2026-11-12', title: 'HEAVY METAL', items: [
    'both MECH DROP mechs got brand new bodies, V horns and all. painted metal now, not plastic: clear coat, rivets, chipped edges, gold horns.',
    'mechs land like heroes now: superhero landing, a beat, then a pose. night shift stabs the floor. paper plane does a hand on the hip.',
    'rim light, ink outlines, hotter glows, contrails, landing dust and sparks. plus stickers. one of them says POWERED BY BREAD.',
  ] },
  { v: '8.8', date: '2026-11-12', title: 'GET IN THE ROBOT', items: [
    'new killstreak: MECH DROP (9 kills). aim at the floor, a giant mech falls out of the sky onto the red circle, press F and climb in. don\'t stand on the red circle.',
    'PAPER PLANE: hovers, fires a 12-pencil missile swarm, sends a paper crane to peck people, lunges to heal and folds into a jet. NIGHT SHIFT: box-cutter sword, a shield that says PLEASE HOLD, ground slams, and TRIPLE SHIFT. its hits clock people out.',
    'hop out whenever you like. when the armour\'s about to go, hit EJECT. the bots have figured out mechs too. sorry.',
  ] },
  { v: '8.7', date: '2026-11-12', title: 'MIND THE LAVA', items: [
    'islands plant & defuse: mount kaboom is a real volcano now. run straight up it, hide behind boulders on the way, and don\'t fall in the glowing bit.',
    'islands: the rope bridges and boardwalks got rebuilt. worn planks, posts, rope rails, stilts in the sea. same bridges, less sad.',
  ] },
  { v: '8.6', date: '2026-11-12', title: 'STILL SPLINTERY', items: [
    'islands: fort splinter got renovated. real weathered stone, moss, battlements, arrow slits, a round corner tower, a covered well. same walls to hide behind. still splintery.',
  ] },
  { v: '8.5', date: '2026-11-11', title: 'HOT ROCKS', items: [
    'islands plant & defuse: the volcano stopped being a pile of black boxes. big basalt columns, lava pouring down the sides, steam, and comfier stairs up the middle.',
  ] },
  { v: '8.4', date: '2026-11-11', title: 'MIND THE STEP', items: [
    'the lighthouse finally got real stairs: a proper iron stair wrapped round the tower, little steps you just stroll up, rails so you don\'t eat sand. the bots found them too.',
  ] },
  { v: '8.3', date: '2026-11-11', title: 'FANCY DRESS', items: [
    '12 NEW COSTUMES in character > clothes > costumes. free for everyone: lifeguard, hot dog guy, budget wizard, referee, grandma, homemade astronaut, tourist, chef, gym bro and pyjamas. one of them is a sausage.',
    'the chicken mascot comes from the new POULTRY IN MOTION achievement: 25 chicken rocket kills. blowing someone off the map with a chicken counts. the bin knight comes from SWORN PROTECTOR: 50 melee kills.',
    'skull rock\'s mouth goes down a throat now. ribs and everything. its spine is made of actual vertebrae. you can walk under it. don\'t.',
    'the lighthouse is a real lighthouse now. eight sides, a glowing lamp room, a balcony you can actually fall off. you can\'t, there\'s a railing.',
    'the soggy biscuit got rebuilt plank by plank. it has a proper rubber duck now. still wrecked.',
    'gun hats and grapple hooks got rebuilt in blender. the cowboy hat has a crease now. the rainbow star is puffy. the plunger still works. we don\'t know why.',
  ] },
  { v: '8.2', date: '2026-11-11', title: 'BOOM, SKULL', items: [
    'explosions are actual fireballs now. a flash, then black smoke rolling over the fire, then it hangs around. guns puff smoke. fires smoke properly. potato keeps its squares.',
    'explosions lost the weird see-through yellow bubble. flash, then straight into the fireball.',
    'SKULL ROCK is an actual skull now. walk in through its teeth, sit in its eyes, climb its spine to the top. the treasure is still gone.',
    'the office stapler, ball machine and basket case skins got rebuilt in blender. the basket has a price tag. it says stolen.',
    'every old top and bottom got re-sewn. real collars, cuffs, pockets, zips and hems. the runner jacket is now a huge hi-vis bomber with a little running guy on the back.',
  ] },
  { v: '8.1', date: '2026-11-11', title: 'INTAKE', items: [
    'the shredder got rebuilt in blender. a big yellow funnel, a cage of red teeth, a turbine down the throat. the wood chipper skin has wheels now. it still eats people.',
    'the blood cross hand got rebuilt in blender too. jointed mannequin fingers, veins, a cuff button. shadow cross glows violet. every weapon in the game is a proper model now.',
    'TEST: settings > video > "water physics (test)". ripples that actually spread and bounce off the bank when you wade, shoot or blow up the water. mid and too hd, off unless you turn it on. try the desert pond.',
    'PLANT & DEFUSE: your guns come back full every round. mags topped up, reserve restocked, no reload. dying still costs you the gun.',
  ] },
  { v: '8.0', date: '2026-11-11', title: 'ACTUAL FIRE', items: [
    'fire is fire now. a real rendered flame with a white-hot middle, on everything that burns, burning people included. potato keeps the cartoon one.',
    'prefer the cartoon flame? settings > video > "real smoke, fire + splashes" turns it back.',
  ] },
  { v: '7.9', date: '2026-11-11', title: 'SHARP OBJECTS', items: [
    'knives got rebuilt in blender. real bevels, real rivets, the butterfly still flips. stab responsibly.',
    'the katana got rebuilt in blender. real hamon, real cord wrap. still grows when you feed it.',
    'the scales of justice got rebuilt in blender too. polished brass, a heart in one pan, a feather in the other. kangaroo court is a baby toy with a kangaroo judge on top. it still convicts.',
    'JANKBURG: the dirt outside the firewall grew hills. the shacks and the plastic orchard sit on real ground now. also: trees stopped teleporting you onto their heads.',
    'the sea round islands and the rig has real wave detail now (mid and too hd). ponds are still ponds.',
  ] },
  { v: '7.8', date: '2026-11-11', title: 'SHINY', items: [
    'SHADERS in settings: bloom (neon and lava actually glow), soft skin (light leaks through your mannequin like a real boy) and punchy colours. pick a level or mix your own. potato and crusty stay off unless you ask; mid and too hd get a bit by default.',
    'if the shaders break on your machine they switch themselves off and say so. SHADERS BROKE. SHADERS OFF.',
    'if the map ever goes pitch black the game repaints it by itself now. type /gfx in chat for a nerd readout to screenshot if your graphics look cursed.',
  ] },
  { v: '7.7', date: '2026-11-11', title: 'DRESS CODE', items: [
    'COSTUMES. character > clothes has whole outfits now, one click each: corpo, rat king, mall cop, delivery guy and more. the bots have been wearing them for weeks. your turn.',
    'click a costume again for another take on it. the maid and night shift ones want their achievements first.',
  ] },
  { v: '7.6', date: '2026-11-11', title: 'KABOOM, PROPERLY', items: [
    'MOUNT KABOOM is an actual volcano now. bigger, craggy, cliffs and gullies, a lava channel down to the beach. walk up it, grapple it, fall in it. bots know the way up. (plant & defuse keeps the stairs.)',
    'the world got furnished. real trees, street and yard stuff, market stalls, and traffic that looks like traffic: eight cars, a bus, a semi, a box truck.',
    'rocks stopped being clones. every one is its own shape now, with little ones lying about.',
    'bow: full draw to the body is 70 now, down from 85. headshots still delete people.',
    'ZOMBIES: the school and the hospital got real furniture. lunch tables, lockers, hospital beds, an x-ray machine. the boxes have been let go.',
    'ZOMBIES: and then more of it. the hospital and the school are less empty. more beds. more desks. somewhere to hide behind.',
  ] },
  { v: '7.5', date: '2026-11-11', title: 'COME ON IN, THE WATER IS FINE', items: [
    'ISLANDS: the sea stopped being instant death. float, paddle to the next island, climb out. no diving, nobody hides under the waves.',
    'swim off the map and you get the RETURN TO THE MAP countdown, then you sleep with the fishes. same on Islands Plant & Defuse.',
    'bots float too. they used to drown constantly. now they have to be shot like everyone else.',
    'ZOMBIES: squad bots learned what stairs are for. they buy the upstairs shutters now, and they can find the power switch on every map.',
    'PLANT & DEFUSE: the better bots check a corner before they walk past it. stop, aim where your head would be, step out, step back. bad bots still just walk in.',
  ] },
  { v: '7.4', date: '2026-11-10', title: 'GROUND FLOOR, AND ANOTHER FLOOR', items: [
    'two new zombies maps, both with an upstairs: JANKFIELD HIGH and SECOND OPINION GENERAL. take the stairs. or the ramp. it is a ramp, legally.',
    'each map has its own zombies. students, teachers, lunch ladies. patients, nurses, surgeons. the surgeon brought paddles.',
    'DESERT has actual ground now: hills, hollows and two dry washes between the buildings. streets and buildings stay level, cacti ride the bumps.',
    'the oasis is a real pond: wade in, the sand drops away, you float. hold crouch to dive and hide on the bottom.',
    'more maps got real ground: grassy dunes on ISLANDS, sand drifts in the BAZAAR, a lumpy FOREST floor, and lawns that roll a bit in SUBURB.',
    'water everywhere got finer ripples and stops flickering.',
  ] },
  { v: '7.3', date: '2026-11-10', title: 'LIMBS OPTIONAL', items: [
    'ZOMBIES come apart now. shoot an arm or a leg enough and it pops off, still twitching. +10 a limb.',
    'no legs: it drags itself along the floor, slow, and can\'t get you on a crate. one leg: it hops. no arms: it headbutts you for half and is useless at planks.',
    'the zombies are proper mannequins now: smooth plastic, ball joints, blank egg heads. limbs pop off at the joint, peg and all.',
    'four new zombies. CHONK (round 5+): huge, slow, pops when it dies and takes the crowd with it. stand back or slip in it. ANKLE BITERS (round 3+): tiny, fast, three at a time. HARD HATS (round 4+): headshots dink off the hat until it flies off. THE SCREAMER (round 6+): shrieks and every zombie near it speeds up. shoot it first.',
    'ZOMBIES: the WARRANTY VOIDER is in the loading dock. hold F with a gun out, the stamp comes down, the gun comes back stronger. three goes a gun. from the second it picks up a side effect nobody tested: ZAPPY, TOASTY, FROSTY, BOINGY or TIPPY.',
    'four more colas, one in every wing: LEG DAY (run faster), DEEP POCKETS (more ammo), THIRD HAND (three guns), GET UP JUICE (get back up by yourself, once). three at a time. go down and they\'re gone.',
    'ZOMBIES: every fifth round is a BOSS ROUND. THE FLOOR MANAGER calls meetings (ankle biters, everyone speeds up) and charges at you. THE MASCOT jumps on you and the floor ripples. long HP bar, no one-shots. drop it and everyone gets paid.',
    'SUBURB got real houses: gables, awnings, porches, three kinds of house, and the store has a sign and a giant slush cup. the south tower on Skyline got fire escapes. same walls to hide behind, they just look like somebody lives there.',
    'DESERT\'s adobe huts got the same treatment as the suburb: plastered walls, roof beams poking out, a doorway you would actually duck through. same cover as before.',
    'rocks are rocks now. the boulders and far formations on Desert, Bazaar and Scary Forest are proper lumpy stone instead of red bricks. they block bullets exactly like before.',
    'the SMOKE BOMB is real smoke now: a thick soft cloud instead of grey squares. things that fall in water make a crown and foam rings. settings > video has other smoke styles (comic puffs, kenney, wispy) and the old squares if you miss them.',
  ] },
  { v: '7.2', date: '2026-11-10', title: 'THUMBS', items: [
    'JANKFIRE runs on phones and tablets now. open it in your phone\'s browser, turn it sideways, go.',
    'touch controls: a stick on the left, drag the right side to look, and big loud buttons for FIRE, JUMP, SLIDE, HOOK, AIM and friends. tap the hotbar to swap guns, tap your item and killstreaks to use them, tap the ammo to reload.',
    'aim assist for touch players: your look slows down near an enemy and the crosshair gets a small tug toward their body. enemies only, no walls, no snapping. SETTINGS > touch sets how much, or turns it off.',
    'SETTINGS > touch: look sens, button size, button see-through-ness, and a left-handed swap.',
    'auto fire for touch players: point at an enemy and the gun goes off by itself after a blink. snipers only when scoped, knives only in reach, never at friends or through walls. the green AUTO button turns it off. FIRE still works.',
    'phones and tablets cap how many pixels they draw and use cheaper shadows, so your pocket stays a pocket and not a hand warmer.',
    'touch: tap a pop-up ad to close it, the scythe gets RIFLE and DASH buttons, tap to spectate when you are dead, and hints finally say FIRE instead of LMB.',
    'hold your phone upright and the game asks you to stop.',
  ] },
  { v: '7.1', date: '2026-11-10', title: 'PITS HAVE BOTTOMS', items: [
    'MOUNT KABOOM got deeper. you don\'t stand in the lava any more, you sink into it. slowly. grapple out before it reaches your chin.',
    'MOUNT KABOOM is not a hot tub. fall down the volcano on Islands and you land in lava: it burns you the whole time you stand in it, keeps burning for a moment after you climb out, and if it finishes you the crater coughs your bits back up. grapple out fast or get EXTRA CRISPY.',
    'the sea drowns you properly now. deep water holds you up for a second while you sink (grapple out!), and you are gone when your head goes under, instead of dropping through the sea bed. same on the oil rig.',
    'long falls end where the ground is: the Desert canyon ends in the river (SPLOOSH), the rooftops end on the street (SPLAT). no more dying in mid air.',
    'bots know the volcano is hot and walk round it.',
    'plant & defuse bots are a real lobby now: some are cracked, some are having a day. good ones tap heads, stop to shoot and hold angles. bad ones run at you jumping. nobody hits harder.',
    'CHARACTER got four more shape sliders: chest, arms, belly, legs. and tabs, so you can see the mannequin while you ruin it. hitboxes still the same.',
    'blood cross never runs dry: out of blood it fires THIN BLOOD, weak but free. the bow draws faster and hits harder. every card you play throws cards now, and a spade is always a fan of six.',
    'the gadgets (speed trap, goggles, laptop, pop quiz, camera, bubble wand) take about twice as long to come back, and dying doesn\'t refill them. pop quiz stores two now.',
    'the scales of justice can hold court at range: right click opens a ring of light under someone, and a second later the pillar comes down. weaker than a swing, 10 s recharge, and you can just walk out of it. most people don\'t.',
    'RESET button in the pause menu (and a bindable key). respawn without hunting for a cliff. if someone hurt you first, they get the kill. training, co-op and quick play only.',
  ] },
  { v: '7.0', date: '2026-11-10', title: 'AD SUPPORTED', items: [
    'new item: the LAPTOP. press G to open it at someone and their screen fills with pop-up ads for 7 seconds. they close them with the number on each ad. some ads ask ARE YOU SURE?. nobody in front of it: NO SIGNAL, and you keep the charge. a reverse card sends the ads back.',
    'bots carry laptops too. a bot reading ads aims worse. so do you.',
    'GUN GAME rolls a new ladder every match: 10 guns, 5 silly ones, 3 melee, then the spoon. weapons that sat out the last match go first. 16 more weapons can show up (shopping cart cannon, taser, slipper, big laser pointer...).',
    'CHARACTER has a joke body row: head size, butt size, and Mannequin / Male / Female builds. everyone sees it. looks only: your hitbox did not get bigger. nice try. some bots turn up with one too.',
    'plant & defuse: the SMG, Belt Sander, Lefty & Righty and the Sniper fire slower there. aim more, hose less.',
    'menus talk less. a pile of captions that explained the obvious got deleted.',
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
