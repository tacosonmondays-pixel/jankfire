// PATCH NOTES: what changed, newest first, in the game's voice. Add an entry here with every update that players notice.
// The menu link shows a NEW badge until you open the page after a new entry (remembered in localStorage).
export const PATCH_NOTES = [
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
