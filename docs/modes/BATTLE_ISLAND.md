# BATTLE ISLAND: the mode (design, not built yet)

Owner: "can we make anew mode thats a battle island like actual island shaped off rip, also blender props immediately
instead of code blocks, and a ton like 12 new mechs ... it can be like a hero shooter!"

Every number here is a default the owner can change.

## The shape: squads, pilots, mechs
A squad royale on one real island. You pick a **mech hero** in the lobby, drop in on foot as its pilot, and earn your mech
mid-match. It is Jank Royale (server/royale.js: blimp, drop, loot, zone, placements, bots) with MECH DROP (server/mech.js)
built into the loop.

1. **Lobby.** Squads of 3, up to 6 squads (18 players), with bots filling the gaps. Each player picks one of the 14 mech
   heroes (ROSTER.md). A squad can't double-pick a hero, so you get team comps.
2. **Drop.** The blimp crosses the island (about 200 m up, a random line), you jump, and the umbrella opens (all of this is Jank Royale's).
3. **On foot.** You're the pilot with a sidearm, loot guns, armour, Jank Cola and **energy cells**. You're weak on purpose:
   pilots hide and run.
4. **Mech meter.** It fills from time (about 90 s from empty on its own), energy cells (+20% each), damage you deal and
   kills (+25%). At 100% press the streak key: your hero drops at your crosshair (MECH DROP's call, marker and shockwave)
   and you climb in. The meter shows in the HUD with a big **MECH READY** callout.
5. **In the mech.** You play your hero's kit until its armour breaks. **EJECT**: you're flung out on foot, the mech pops,
   and the meter restarts at 25% (you keep a head start). Your squad can **revive** a downed pilot (hold F for 4 s); a
   squad is out when every pilot is down.
6. **Zone.** It shrinks in 5 rings over about 12 minutes. The last ring sits on the island's middle, so the finale is a
   mech brawl. Outside the zone, mechs take armour damage and pilots take HP damage.
7. **Win.** Last squad standing. Placements, XP and medals use Jank Royale's.

Why this shape: it's the mech-arena formula the owner asked about, it reuses two systems we already have and test, and
the meter makes every match swing from scrappy pilot fights to big mech fights.

## Second option: ISLAND ARENA (6v6, quick)
The same island and heroes, but you spawn in your mech. It's 6v6 team deathmatch on a cut-down middle of the island:
respawn as the pilot, with the meter at 60%. First to 30 mech kills. It's cheap to add after the royale (the same
pieces, no zone or loot), and good for bots-only rooms and short sessions. **Recommend building it second.**

## Bots
Bots pick a hero that fills a gap in their squad's roles, loot and pick up cells, call their mech as soon as the meter
is full and they're near a fight, and use each hero's kit through a small per-hero plan (like mechBotStep). Squad bots
stick within about 25 m of a human teammate and revive them.

## The island (the map session builds it, agreed with it)
- **Size and shape:** about 560 x 460 m of land, with sea out to about 800 m and a few small islets. The coastline has a
  harbour bay (south), a lagoon behind a reef (east), cliffs (north-west), a central ridge 45-60 m high with the radio
  tower, a river down to the lagoon, beaches and dunes.
- **Blender props from day one.** Collision stays boxes.
- **9 POIs:** Port Jankton (harbour town, biggest), The All-Inclusive (resort), Dead Air (radio tower, landmark), Return to
  Sender (wrecked cargo ship), Scrap Mart (mech hangar and scrapyard), Ancient Temple (Probably), Wrong Way Point
  (lighthouse), Moo-Tel Farm, The Big Hole (quarry). Plus a 12 m ring road and cross roads.
- **Mech scale:** streets 14 m or wider, bridges 10 m, big doorways 7 x 6 m, a mech-walkable route through most POIs.
  Small buildings stay pilot-sized, as cover for people on foot.
- **Loot:** about 400 spots (30-60 per POI plus scatter), 3-6 energy-cell spots per POI, grapple points on everything tall.
- **What the mode needs placed:**
  - Each POI gets an id, a centre and a radius (for the HUD, callouts and bots).
  - Each POI needs at least one open-sky flat area 12 m across or more, because mechs drop from the sky.
  - Energy-cell spots tagged apart from loot.
  - No vehicles, parked mechs or supply drops in v1.
- **Water:**
  - Reef flats and shallows (up to about 1.5 m deep) are walkable for pilots and mechs, at 60% speed.
  - Deep water is the sea kill ("into the sea"), like the void.
- **Zone:** 5 rings over about 12 minutes. It never ends in the sea. The final ring is at least 40 m across, on land flat
  enough for mechs, and leans toward the middle (Dead Air / Scrap Mart).
- **No district rule-bends in v1.** We keep it readable; a POI gimmick or two can come later.

## Server and safety
- **New code:** squads, the mech meter, picking a hero, and revives.
- **Reused:** royale.js and mech.js.
- **Rules as before:** the server owns the meter, every hit, the call, the zone damage and revives. Every message is
  validated and rate-limited. A hero's kit is data in shared/heroes.js plus its server judging, so each new hero is
  additive.
- **Testing:** each build PR gets a ws test pass, a bots game, a Too HD clip, and the reviewer's attack pass before merge
  (as for #310).

## Build order (step 2, after the owner OKs it)
1. **Squads in royale:** team spawns, shared placement, revives, the squad HUD.
2. **The mech meter and hero pick:** with PAPER PLANE and NIGHT SHIFT, so the full loop plays on the current royale map.
3. **The island map:** the map session's PR, wired in.
4. **The heroes, in batches of 3 or 4 per PR:** the art session does the models from the owner's Tripo meshes; code
   stand-ins come first.
5. **ISLAND ARENA.**
