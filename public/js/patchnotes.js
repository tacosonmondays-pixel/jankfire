// PATCH NOTES: what changed, newest first, in the game's voice. Add an entry here with every update that players notice.
// The menu link shows a NEW badge until you open the page after a new entry (remembered in localStorage).
export const PATCH_NOTES = [
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
