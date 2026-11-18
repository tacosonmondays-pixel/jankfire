--!nocheck
-- THE ROTUNDA: the game's real hub since 2026-11-15, and its edit-time builder. the owner, about the bowling centre
-- (HubLab's "centre"): "I like the aspect and design buyt bolowing doesnt make sense for the game you know, keep it as a
-- hub we can use but lets rework the first rework"; asked which hub they meant: "it had a duck lounge, a big like circle
-- thing in the center with the branching paths leading into the rivals like pads that I said were a bit too on the nose".
-- so: the first round hub's plan (a round domed middle, a ring balcony, short halls that each frame the next room, a
-- small warm duck lounge), built in the bowling centre's look (slate shell, dark piers with light strips, a cream ring
-- with one pink line, wood dado, plain heavy lettering), as the ground-floor lobby of the arena. the pads are five open
-- lifts up to the arena, on an arc behind the round room's northern piers: one opening and one floor line per lift.
-- no pad corridor, no runway, no blast door.
-- HOLOGRAMS (owner, 16 Nov: "in the hub can the center gun thingy cycle your loadout but hologram style? we also need
-- holograms like in rivals with bundle sets that float and people can look at and interact with"): the builder only
-- leaves their places, B.holo: an invisible drum tagged HubHolo the size of the space a hologram may fill (attributes
-- Holo = "loadout" / "bundle", Slot, Radius, Height, Base = how far under its middle its lens is, Color = the palette's
-- accent). StarterPlayerScripts.HubHolo draws them on each player's screen: over the platform your own loadout in
-- turn, on the showroom's four plinths (the south wall either side of the lounge) the shop's bundles. R.check tests
-- the sight lines and keep-clear zones against those drums as if they were solid.
--   usage (Studio's command bar, Edit):
--     local R = require(game.ServerStorage.PolishBackup.HubRotunda:Clone()); print(R.build("live")); print(R.check())
--   R.build("stage")   a copy to look at, under workspace.Map.HubStage at R.STAGE (its pads are for show)
--   R.compare()        one copy of each palette side by side (R.COMPARE), to photograph; R.unstage() takes them away
--   R.build("live")    the real hub: Hub.Rotunda (Shell, Scenery, Collision), its five pads in Hub.QueuePads, spawn markers
--                      in Hub.HubSpawns (in the lounge since 18 Nov), where the training hall's door lands you in Hub.Doors.HubArrive, the training
--                      gate's trigger in Hub.Doors. each of those is marked Built = "Rotunda". it takes the bowling
--                      centre away first (Hub.Lanes and everything marked Built = "HubLab")
--   R.check()          keep-clear zones, leaks, sight lines (from where you come onto the platform: pads, boards, the
--                      name, every door's name; one thing inside each room; from every spawn point in the lounge: the
--                      first look, R.FIRST_LOOK), the walk from the spawn to every pad, the regulars' ways
--   R.switch("lanes")  the bowling centre back (HubLab builds it; HubLab's own build also takes the Rotunda away, so
--                      HubLab's usage line alone does the same). R.switch("rotunda") = build("live") and check
-- a build wipes and remakes the hub: change the builder, never the built parts. the rooms are in three part modules
-- beside this one (R.PARTS); each returns function(B, R) and builds with the helpers below.
-- coordinates: the middle of the round room's floor is the origin. a FRAME is a bearing from that middle (0 = north,
-- the way you look when you spawn; 90 = east) and things are placed in it by x (to the right as you look outward), y
-- (up) and d (how far out from the middle). `face` is the way a thing's front looks in its frame: 0 = at the middle,
-- 180 = outward, 90 = to the right, -90 = to the left.
local R = {}
local hub = workspace.Map.Hub
local lib = game.ServerStorage.JankfireMeshes
local PB = game.ServerStorage.PolishBackup
local SP, Neon = Enum.Material.SmoothPlastic, Enum.Material.Neon

R.ROOM = "Rotunda" -- its folder in workspace.Map.Hub
R.MARK = "Rotunda" -- the Built attribute on what the server finds by name
-- every hub building's folder in Map.Hub and Built mark (a build takes all of them away first: one hub at a time). the
-- hotel plaza is HubPlaza's (18 Nov), the bowling centre HubLab's
R.HUB_FOLDERS, R.HUB_MARKS = { "Rotunda", "Lanes", "Plaza" }, { "Rotunda", "HubLab", "Plaza" }
R.SITE = Vector3.new(-200, 240, -10000) -- the hub's site (the bowling centre's too: only one of them is built at a time)
R.STAGE = Vector3.new(200, 240, -10000)
R.PARTS = { "HubRotundaCentre", "HubRotundaLifts", "HubRotundaRooms" }
R.PUSH = 61 -- (counts the pushes from the repo into Studio while the builder was being written)
-- the hub's own prop kit (tools/roblox/rotunda_props.py, one upload): chunky pieces that replaced the weakest old bc_
-- props on 16 Nov (owner: "some of the props dont look super like rivals ones!"). R.importProps() brings them into
-- JankfireMeshes; R.prop(new, old) places the new one if it is there, else the old
R.PROPS = 94371006780646 -- (the kit's Model asset: rk_planter, rk_punchbag, rk_tyres, rk_coffeetable, rk_lockers, rk_dumbbells, rk_bench)
-- the round room: 14 sides, 28 from the middle to a wall's face, walls and piers 3.4 thick, the ring balcony 14 up and
-- 5.5 deep. side i is at bearing i * 360 / 14; R.OPEN says which sides are ways out
R.N, R.A, R.WALL, R.RING_Y, R.RING_IN = 14, 28, 3.4, 14, 19.5
-- (18 Nov, the owner: "maybe make the hub larger and extend the size of the balcony so its not as cramped up there?". the
-- balcony ring's inner edge came in from 22.5 to 19.5: 8.5 deep in the round room's units, 12.75 studs at R.HALL_K 1.5,
-- from 7.4. over the two jump pads (sides 3 and 11) it keeps its old edge, R.RING_IN_JUMP: a notch the throw lands in)
R.RING_IN_JUMP = 22.5
-- the FOCUS: the point on the platform, 6 south of the middle, that the spawn points stand round and that the five
-- lifts fan out from. each lift bay lies along the line from the focus through the middle of its opening, so from
-- where you appear every lift is framed by its own two piers (from the room's own middle they would be too far round
-- to the sides to be in a first look)
R.FOCUS = 6
-- (sides 6 and 8, "arcade": since 18 Nov the two arches either side of the lounge's, three round arches in a row onto
-- the big lounge where you spawn)
R.OPEN = { [0] = "lift", [1] = "lift", [2] = "lift", [12] = "lift", [13] = "lift", [4] = "gym", [6] = "arcade", [7] = "lounge", [8] = "arcade", [10] = "armory" }
-- THE SPAWN LOUNGE (18 Nov 2026, the owner: "Can the current lounge be turned into a part of a larger lounge where players
-- will now spawn making the central [room] feel more spacious!!"). the small lounge is now the middle bay of a lounge as
-- wide as the round room, open onto it through the three arches (sides 6, 7, 8): its walls and hall gone, it and the VIP
-- room behind it moved R.LOUNGE_S further out, its low ceiling kept as a timber canopy over it. you appear on a round rug
-- on the lounge's front floor, facing the arches (Hub.HubSpawns: the same markers as before, only where they stand
-- changed). HubRotundaRooms builds it. LOUNGE_X = half its width inside, LOUNGE_H = its ceiling
R.LOUNGE_S, R.LOUNGE_X, R.LOUNGE_H = 8, 28, 16
-- THE HOTEL PLAZA (18 Nov 2026; the owner, after a square plaza for the whole hub was planned: "keep the old circular
-- look though for the hub, lounge free rein", so the round room stays the hub's heart and the hotel is the lounge wing.
-- before that, the owner: "can you try remodelling the hub lounge into like a hotel plaza? rn a lot of
-- your extensions just look like well extensions, it doesnt look very natural"). R.LOUNGE_STYLE = "plaza": the lounge,
-- its timber bay and the VIP box behind it become one building round a covered courtyard, in the round room's own
-- language (its piers floor to cornice, the balcony's band, the gallery's windows, its cornice) turned inside out: the
-- round room's three south faces are the courtyard's north side (its arches the way in, a balcony over the middle one,
-- a bay window over each side one: the west one is the hub egg's nook), and three facades of hotel rooms over arcades
-- close the rest (dark windows, balconies); a lit coffered ceiling over it all. in the arcades: the showroom (west),
-- seats and the games corner (east), the reception and the VIP door (south). in the courtyard: the spawn rug, a
-- fountain with the duck over it, big trees, two ring chandeliers. "lounge" = the spawn lounge as it was (place v810)
R.LOUNGE_STYLE = script:GetAttribute("LoungeStyle") or "plaza" -- ("lounge": the spawn lounge of place v810. R.switch("plaza" | "lounge") builds either live, from a copy of this module with the attribute set)
-- the plaza's plan, in the lounge's frame (side 7: x to the west, d out) and Hub v2 numbers like everything here: X =
-- the courtyard's half width (the side facades' faces), D = the south facade's face, BACK = the face of the south
-- arcade's back wall (the VIP door's), OUT = the side arcades' outer walls' faces, WALL = a facade's thickness, BEAM =
-- the arcades' ceilings (the openings' head), ROOF = the courtyard's lit ceiling, PIERS_D = the side facades' piers
-- (their d; one more at each corner), PIERS_X = the south facade's (its x either side; and the corners)
R.PLAZA = { X = 19, D = 69.2, BACK = 78.2, OUT = 28, WALL = 1.6, BEAM = 12, ROOF = 28.6, PIERS_D = { 27.5, 41.17, 55.17 }, PIERS_X = { 6.33 } }
-- the jump pads' lit ring (18 Nov: the way up made obvious): its radius, a little outside the pad's own rim
R.JUMP_GLOW = 4
-- the hub egg's hiding place (18 Nov; the egg is training-v2's, Map.Hub.HubEgg): the gallery window over this side is an
-- opening { half its width, its sill, its head } into a little room on the lounge's roof (HubRotundaCentre)
-- (dropped 18 Nov: the lore NPCs, the mannequin too, now appear only in their code cutscene, so the nook went with the
-- lobby's two bay blocks. R.EGG_SIDE = 8 builds it again)
R.EGG_SIDE, R.EGG_NICHE = nil, { 2.3, 17, 23.4 }
R.FOUNTAIN_DUCK_TURN = 0 -- (the lobby fountain's duck: degrees about its own axis, so its face looks north at the arches)
-- the fountain's trickle (18 Nov: a looped recording from Roblox's licensed library, Pro Sound Effects; nil: none)
R.FOUNTAIN_TRICKLE = "rbxassetid://110264836521979" -- (freesound 676173, CC0: a small fountain, close, made to loop; roblox/assets/sounds/fountain_trickle.ogg)
R.FOUNTAIN_TRICKLE_VOL = 0.35
-- where you appear: { x, d } in the lounge's frame (side 7: x to the right as you look out of the round room, d out)
R.SPAWNS = if R.LOUNGE_STYLE == "plaza"
	then { { -3.6, 42.8 }, { -1.2, 42.8 }, { 1.2, 42.8 }, { 3.6, 42.8 }, { -3.6, 45.2 }, { -1.2, 45.2 }, { 1.2, 45.2 }, { 3.6, 45.2 } } -- (in the courtyard, the middle arch straight ahead)
	else { { -3.6, 39.2 }, { -1.2, 39.2 }, { 1.2, 39.2 }, { 3.6, 39.2 }, { -3.6, 41.6 }, { -1.2, 41.6 }, { 1.2, 41.6 }, { 3.6, 41.6 } } -- (far enough back that the first look takes in all three arches)
-- where the lifts must all be framed from: the platform's south edge, where you come out onto it from the lounge (the
-- spawn rows stood here until 18 Nov). { x, d } in the north frame, on the platform's top
-- where the lounge's own things (the duck, the showroom's bundles) must show from: the front of the spawn rug, { x, d } in
-- the lounge's frame, the eye 5.2 up
R.LOUNGE_LOOK = if R.LOUNGE_STYLE == "plaza" then { 0, 47 } else { 0, 34 } -- (the plaza: the rug's south half, the fountain ahead)
R.PLATFORM_LOOK = { { -2.4, -8.4 }, { -0.8, -8.4 }, { 0.8, -8.4 }, { 2.4, -8.4 }, { -2.4, -9.9 }, { -0.8, -9.9 }, { 0.8, -9.9 }, { 2.4, -9.9 } }
local TEAM = { "ff4fd8", "37d6ff", "ffe14d" } -- the teams' colours, in Matches' order
R.TEAM = TEAM
-- the five modes, left to right as you spawn: its side of the round room, and its pad's width and depth
R.MODES = {
	{ id = "1v1", title = "1V1", kind = "DUEL", teams = 2, size = 1, side = 12, w = 12.4, dp = 9.6 },
	{ id = "1v1v1", title = "1V1V1", kind = "THREE-WAY", teams = 3, size = 1, side = 13, w = 15.6, dp = 9.6 },
	{ id = "2v2", title = "2V2", kind = "DUOS", teams = 2, size = 2, side = 0, w = 13.6, dp = 11 },
	{ id = "3v3", title = "3V3", kind = "TRIOS", teams = 2, size = 3, side = 1, w = 14.4, dp = 11.2 },
	{ id = "4v4", title = "4V4", kind = "SQUADS", teams = 2, size = 4, side = 2, w = 15.6, dp = 11.2 },
}
-- THE SECOND FLOOR (HubRotundaLifts). the owner, 16 Nov: "can you try to create a second floor of pads above the current
-- one", then "we dont need stairs or escalators, we already have the jump pads". so: over the lift ring, at the
-- balcony's height, a crescent hall with seven more pads round its outer wall, each with its board on the wall behind
-- it. the jump pads (sides 3 and 11) throw you onto the balcony beside a doorway into it; there is one off the balcony
-- over each of the four outer lifts. the way back down is the balcony's gap over each jump pad.
R.UP_Y = 14.04 -- the second floor's top (the balcony's floor)
R.UP_ROOF = 27.45 -- its ceiling (the round room's wall top)
R.UP_OUT = 76 -- the face of its outer wall, from the focus (66.6 until 18 Nov: the bigger hall, roomier upstairs)
R.UP_PITCH = 17.5 -- degrees between its pads, seen from the focus (14.5 until 18 Nov: about three times the floor between two)
R.UP_END = 64 -- the second floor's end walls, degrees from the focus's north (it reaches past the lift fan's ends, R.endBearing)
R.UP_SIZE = { ["1v1"] = { 10, 8 }, ["2v2"] = { 12, 9 }, ["3v3"] = { 13.6, 10 } }
-- its pads left to right: name (= its PadId), mode (R.MODES index)
R.UPPER = {
	{ name = "1v1_u1", mode = 1 }, { name = "2v2_u1", mode = 3 }, { name = "1v1_u2", mode = 1 }, { name = "3v3_u1", mode = 4 },
	{ name = "1v1_u3", mode = 1 }, { name = "2v2_u2", mode = 3 }, { name = "1v1_u4", mode = 1 },
}
R.UP_DOORS = { [12] = true, [13] = true, [1] = true, [2] = true } -- the round room's sides with a doorway off the balcony into it
-- THE GYM (side 4, HubRotundaRooms), only for looks since the second floor (no pads, no hall behind it): push 37's
-- locker room with the ring centred on the door's axis
R.GYM_BOX = { 20, 74, 18 } -- half its width, its far wall's d, its height
R.GYM_RING = 58.5 -- the ring's middle, on the door's axis
-- THE REGULARS: the owner's friends about the hub in their own avatars (owner, 16 Nov: "Can you put these two as NPCs
-- somewhere?", "This one too"). B.npc leaves their places, HubNPCs.server builds them at server start (a saved copy in
-- ServerStorage.JankfireNPCs if the avatar call fails). who = the label over them, user = their Roblox username. their
-- purposes (owner, 17 Nov: "Dune is the quests guy, maybe Frisk does one. Maybe Looticus the shop? ... I want to give
-- them purposes"): role = the word after their name over them; prompt = { its action, the attribute it carries, its
-- value }: the panel's own client opens on that attribute (ShopOpen: ShopClient; QuestsOpen: QuestClient; RankedBoard:
-- the ranked leaderboard, "duels" or "party"). idle / extra / extraStand / walk: their clips (MX below; a seated one's
-- hips levelled about the clip's own middle, as Roblox's own sit has them, so they don't sink into the sofas; walk only
-- for an avatar with none of its own). every = { min, max } seconds between the one-shots. Trisangle's prompt is the
-- shop's VipDaily's
-- getting up and sitting down (owner, 17 Nov: "When they stand make sure they don't stand in their seats like clipped
-- into it! Idk how you would do it but make them leaving their seat natural?"): rise / settle = the two clips (motion
-- capture; uploaded with their hips kept still: HubNPCs moves the body along the hips' own path). they stand up onto a
-- seat's Stand point, R.NPC_STAND in front of it (clear of the cushion by more than half a body), take a step out to
-- its approach before they turn, and sit down from the Stand point with their back to the seat. R.check sweeps a body
-- (R.NPC_BODY: across, tall, deep; its feet R.NPC_LIFT over the floor, so rugs and sills don't count) along every way
-- they walk, every R.NPC_STEP studs, and stands one on every point they stop at. across, each regular's own width
-- (R.NPCS width: their hands at rest; walking, the hands swing to the front and back). what counts is what can be seen:
-- the invisible collision boxes round the kit (a sofa's, a rail's) are bigger than the things and don't show
R.NPC_STAND = 1.9 -- (the sofas reach 1.1 in front of their seat points; a body is 1.2 deep)
R.NPC_BODY = Vector3.new(3.8, 5.2, 1.2) -- (5.2 tall, 1.2 deep; across: each regular's own width, R.NPCS width, at the hands)
R.NPC_LIFT = 0.35
R.NPC_STEP = 0.5
-- the clips (owner, 17 Nov: "also the animations seem really stiff.."; then Mixamo motion capture the owner approved, put
-- onto R15 by my own retarget (the scratchpad's mixamo\retarget.py; the FBX stay in the vault, Assets\mixamo-17nov) and
-- set side by side with the live clips and the generated takes (four standing up, two sitting down; PORT-PLAN
-- section 32): the mocap won every slot. each with its
-- length in seconds where the server times something by it. one seated glance serves Trisangle and Looticus
local MX = {
	rise = "rbxassetid://117955942892612", settle = "rbxassetid://97331327036036", -- (2.27 s, 2.23 s; uploaded with the hips kept still)
	trisIdle = "rbxassetid://122668447841808", look = "rbxassetid://114005193645149", -- (legs swinging on a high perch; a glance to the side, 4 s)
	lootIdle = "rbxassetid://81991323034085", stretch = "rbxassetid://75542542460583", -- (breathing, seated; an arm stretch standing, 8.87 s)
	duneIdle = "rbxassetid://90791386511358", shift = "rbxassetid://86800381172094", -- (breathing, standing; a weight shift, 9.43 s)
	friskIdle = "rbxassetid://132599545925485", -- (looking around)
}
local GEN_WALK = "rbxassetid://135619112265836" -- (generated; only for an avatar with no walk of its own)
R.NPCS = {
	Looticus = { user = "roblox_user_4547551380", id = 4547551380, pose = "sit", role = "SHOP", prompt = { "Shop", "ShopOpen", "tab:containers" }, moves = "teleport", width = 4, idle = MX.lootIdle, extra = MX.look, extraLen = 4, extraStand = MX.stretch, extraStandLen = 8.9, every = { 15, 30 }, rise = MX.rise, riseLen = 2.27, settle = MX.settle, settleLen = 2.23 }, -- on the lounge's sofa; now and then up, a puff, and he is on another seat or by the arcade or the fridge
	Dune = { user = "Doonamei", id = 56917496, pose = "stand", role = "QUESTS", prompt = { "Quests", "QuestsOpen", true }, badge = "QuestNews", moves = "pingpong", width = 3.9, idle = MX.duneIdle, extra = MX.shift, extraLen = 9.4, every = { 20, 40 }, walk = GEN_WALK }, -- in the gym, walking round three sides of the ring and back
	Frisk1636 = { user = "BruhFrisk1636", id = 5028123368, pose = "stand", role = "RANKED", prompt = { "Ranked", "RankedBoard", "duels" }, moves = "pingpong", width = 3.2, idle = MX.friskIdle, walk = GEN_WALK }, -- on the balcony over the lifts, moving between four spots on the rail, looking down
	Trisangle = { user = "Xxxglowingstarlightx", id = 2321239144, pose = "sit", vipDaily = true, role = "DAILY REWARD", moves = "seats", width = 3.4, moveEvery = { 45, 90 }, idle = MX.trisIdle, extra = MX.look, extraLen = 4, every = { 12, 25 }, walk = GEN_WALK, rise = MX.rise, riseLen = 2.27, settle = MX.settle, settleLen = 2.23 }, -- in the VIP room, on a sofa (owner, 16 Nov: "Can you put this person inside the VIP room")
}
-- the paint. one palette is one switch (R.PALETTE); every palette paints the same build. the owner on the round hubs C to
-- G (16 Nov): "I like how it looked, I think with the new diesgn principles building somelike like it could be cool,
-- less colorfuil, maybe keep some color obviously, idk tryh different thing". so three treatments, photographed side by
-- side (R.compare), one picked as the default and the others kept here:
--   "arena"  calm slate and cream, near-monochrome: one pink line (the ring, the rail), yellow words over the lifts
--   "glow"   the cosy rotunda (E) made sober: a darker shell where the light does the work, the pink ring kept, a cyan
--            line to every lift and cyan words over them: a restrained version of the old neon pair
--   "warm"   warm stone, brass and timber: one amber accent instead of the pink, amber lines and words
-- keys (doorGlow and halo are optional: the glow palette's lit door lines and the ring over the name): shell/shell2 walls, pier/pier2 piers and frames, cream/creamHi the ring, rails and ribs, wood/band the dado and
-- the line over it, dome, floor/floor2, deck/padBase the lift decks, bay the shafts' back walls, plate the signs' plates,
-- accent the rail line, glow the platform's ring, ray the floor lines, dim the gallery's lit panels, word the words over
-- the lifts, train the training word, pale the words over the rooms, strip/panel/sky/light/warm the lights, brick/beam
-- /carpet the lounge, gymWall/gymFloor the gym, edge the pads' rims. remap repaints the kit's props (the colour in a
-- piece's name = its new colour): nothing near-black, nothing loud
R.PALETTE = "glow" -- (picked on 16 Nov from the three side by side: the closest to how the round hubs C to G looked, calmer)
local ARENA = {
	tint = "neutral",
	shell = "5e6672", shell2 = "68707c", pier = "3f4753", pier2 = "4a5260", cream = "ddd8cd", creamHi = "ece8df",
	wood = "bfae92", band = "62808a", dome = "767d86", floor = "6b7078", floor2 = "5a5f68", deck = "4f5863", padBase = "4f5863", bay = "78808c",
	plate = "2e3140", accent = "ff4fd8", glow = "ff4fd8", ray = "c9b660", dim = "858a92", word = "ffd84a", train = "7dff4f", pale = "f1ede2",
	strip = "f4f8ff", panel = "9a9fa8", sky = "8e9298", light = "f1f1ee", warm = "ffe2b8", brick = "a98b7c", beam = "8f7558", edge = "9a9fa8",
	carpet = "67635f", gymWall = "c4c0b6", gymFloor = "5a6069",
	flat = true, -- (brick, wood and crate grain become flat colour: "flat colours, no noisy textures", and round 1's judge)
	remap = { ["37d6ff"] = "86a9b3", ffe14d = "dccf9a", ["7dff4f"] = "9dbb93", ff9a1f = "cfa57c", ff4fd8 = "b7879f", ff4fd9 = "b7879f",
		["17141f"] = "3f4753", ["2e3140"] = "3f4753", ["2a2d38"] = "3f4753", ["120818"] = "3a414c", ["1b1b20"] = "3f4753", ["1a1824"] = "3f4753",
		["2a2c3e"] = "4a5260", ["26242e"] = "3f4753", ["1f2a3a"] = "3f4753", ["3b2a52"] = "e4ddcf", c8262e = "a8605c", ff2a3a = "c9605e", b44fff = "8f84a8",
		["3a3f4a"] = "566070", d6dbe3 = "b9bec8", ["5b6478"] = "566070", a4aab8 = "c9c5bb", ["8fe6ff"] = "a9c6cf", bfe9ff = "b9d0d6" },
}
local function over(base, t, remap)
	local p = table.clone(base)
	for k, v in t do p[k] = v end
	p.remap = table.clone(base.remap)
	for k, v in remap or {} do p.remap[k] = v end
	return p
end
R.PALETTES = {
	arena = ARENA,
	glow = over(ARENA, {
		-- (round 1's judge, 16 Nov: "the team colours leak into the building, so the pads don't stand out" and "the piers are
		-- near-black". so the pink, cyan and yellow are left to the pads and their boards; the building has ONE accent, a soft
		-- aqua, on the platform's ring, the floor lines, the lit strips and the ring over the showpiece; the piers are a
		-- mid slate, paler than the walls; floor, walls, piers and dome are four clearly different values)
		shell = "535a66", shell2 = "5c636f", pier = "68707c", pier2 = "747c88", cream = "b3aea4", creamHi = "c4bfb5",
		wood = "a48f6c", band = "6c6862", dome = "727a86", floor = "41464f", floor2 = "393e46", deck = "3a3f48", padBase = "3a3f48", bay = "6a727e",
		-- (round 2's judge, 16 Nov: teal had become a second base colour. so the aqua is kept to the floor lines and the
		-- platform's ring; the wall band, the gallery's panels and the ring overhead go neutral, the training word white)
		plate = "262a34", accent = "b3aea4", glow = "6fc9c9", ray = "4c8a8e", dim = "6a6e74", word = "e8eef2", pale = "e8eef2", strip = "d8eef2", panel = "8e98a2", sky = "7f8a96",
		train = "e8eef2", bayWash = "fff1dc", padCalm = 0.18,
		light = "e8f0f4", edge = "8e98a2", carpet = "4f4846", gymWall = "c9bfae", gymFloor = "4c515a",
		brick = "80746e", beam = "6b5a4c", -- (the lounge: flat brick under its warm lamps read salmon; a warm taupe and darker timber)
		doorGlow = "5fbcbf", halo = "d8eef2", -- (a line on every threshold; the ring over the showpiece)
	}, { f4f8ff = "d8eef2", ["17141f"] = "434a55", ["2e3140"] = "434a55", ["2a2d38"] = "434a55", ["1b1b20"] = "434a55", ["1a1824"] = "434a55",
		["26242e"] = "434a55", ["1f2a3a"] = "434a55", ["2a2c3e"] = "4c535e", ["5b6478"] = "5a616d", ["3a3f4a"] = "5a616d", a4aab8 = "b3aea4" }),
	warm = over(ARENA, {
		shell = "6b625b", shell2 = "746a62", pier = "463d37", pier2 = "51473f", cream = "e2d4bc", creamHi = "eee3cf",
		wood = "c49f72", band = "8c5f45", dome = "7b7068", floor = "6e665f", floor2 = "5e5751", deck = "4e4741", padBase = "4e4741", bay = "7d736a",
		plate = "2f2a28", accent = "e0a040", glow = "f0a646", ray = "d4a35c", dim = "958676", word = "ffcf7a", pale = "f5ecdc", strip = "ffe6c4",
		panel = "a89a88", sky = "a3968a", light = "fff0dc", warm = "ffd7a0", edge = "a89a88", carpet = "6b5446", gymWall = "d6c8b2", gymFloor = "625a54",
	}, { f4f8ff = "ffe6c4", ["37d6ff"] = "a9b39f", ff4fd8 = "c4977a", ff4fd9 = "c4977a", ["17141f"] = "463d37", ["2e3140"] = "463d37", ["2a2d38"] = "463d37",
		["120818"] = "463d37", ["1b1b20"] = "463d37", ["1a1824"] = "463d37", ["26242e"] = "463d37", ["1f2a3a"] = "463d37", ["2a2c3e"] = "51473f",
		["3b2a52"] = "eee3cf", d6dbe3 = "c8bba8", a4aab8 = "d2c3ab", ["5b6478"] = "6a5f57", ["3a3f4a"] = "5e544c", ["8fe6ff"] = "c9c2b0", bfe9ff = "d6cdb9" }),
}
-- side by side, to photograph: { palette, its site }. R.compare() builds one staging copy of each
R.COMPARE = { { "arena", Vector3.new(200, 240, -10000) }, { "glow", Vector3.new(600, 240, -10000) }, { "warm", Vector3.new(1000, 240, -10000) } }

-- HUB V3 (18 Nov 2026, the owner: "can you do hub v3? its the current one just more spacious one of my friends said it
-- felt too cramped"). the same Rotunda, everything in it, through ONE scale rule applied to the finished build:
--   the plan   every place and every footprint K times as far from the round room's middle (K = 1.35: the room 56
--              across becomes 75.6; walks, halls, doorways, rooms and the gaps between things all 35% wider)
--   the height a map H of heights over the floor: { old, new } breakpoints, straight between them. the bands people
--              use keep their size (the ground floor up to 9.5, the second floor's first 9.5) and only the air over
--              them grows: the balcony and the second floor 14.04 -> 18, its ceiling (the wall top) 27.45 -> 35, the
--              dome over it 30% taller
--   what keeps its size (people-sized things): seats keep their depth (sofas, armchairs, benches get longer), the
--              props and display guns keep their size and stand where their place went (R.WARP_MODE), plants and the
--              jump pads grow with the plan, the regulars, markers and lamps move (lamps reach K times as far)
-- R.VERSION says what R.build("live") makes: 3 = Hub v3, 2 = the Rotunda as it was (the spare: R.switch("rotunda"))
-- the whole hub's scale in plan (Hub v3: 1.35; since 18 Nov, the owner's "make the hub larger", 1.5). heights keep their
-- band map, R.V3.H. TUNABLE: change it and rebuild; every place the builders and the check take from the warp follows
R.HALL_K = 1.5
R.V3 = { K = R.HALL_K, H = { { 0, 0 }, { 9.5, 9.5 }, { 14.04, 18 }, { 23.5, 27.46 }, { 27.45, 35 }, { 41.3, 53 } } }
R.VERSION = 3
-- how a kit model takes the warp: "stretch" (its footprint K times, its height by H: the structural kit that must meet
-- walls and lids, and the jump pads: wider, not taller), "seat" (longer, not deeper or taller: people sit in it),
-- "uniform" (K times all over: plants, bigger things for a bigger room), anything else "rigid" (its own size, moved)
R.WARP_MODE = { hb_pier = "stretch", hb_rail = "stretch", hb_screen = "stretch", bc_halo = "stretch", hb_portal = "stretch",
	rk_lockers = "stretch", bc_lockers = "stretch", rk_coffeetable = "stretch", bc_coffeetable = "stretch", bc_holoprojector = "stretch",
	bc_sofa = "seat", bc_armchair = "seat", rk_bench = "seat", bc_bench = "seat",
	bc_jumppad = "stretch", rk_planter = "uniform", bc_plantbig = "uniform" }
-- heights over the floor through a warp's H (straight past the last breakpoint)
local function hmap(H, y)
	if y <= H[1][1] then return y + (H[1][2] - H[1][1]) end
	for i = 1, #H - 1 do
		local a, b = H[i], H[i + 1]
		if y <= b[1] then return a[2] + (y - a[1]) * (b[2] - a[2]) / (b[1] - a[1]) end
	end
	local a, b = H[#H - 1], H[#H]
	return b[2] + (y - b[1]) * (b[2] - a[2]) / (b[1] - a[1])
end
R.hmap = hmap
-- a world point through a warp about the round room's middle O (nil warp: the point itself)
function R.warpPoint(Wp, O, v)
	if not Wp then return v end
	local d = v - O
	return O + Vector3.new(d.X * Wp.K, hmap(Wp.H, d.Y), d.Z * Wp.K)
end
-- the warp a built hub was made with (its Version attribute)
function R.warpOf(room)
	return if room and room:GetAttribute("Version") == 3 then R.V3 else nil
end
-- the warp on one finished part: its middle and its three axes' ends through the warp (a box stays a box when its axes
-- are level or upright, as nearly all are; a tilted one, a dome panel or a rib, keeps its ends on the warped points),
-- the attachments in it moved with its faces, its lights reaching K times as far
local function warpPart(Wp, O, p)
	local cf, s = p.CFrame, p.Size
	local c = cf.Position
	local ax = { cf.XVector, cf.YVector, cf.ZVector }
	local half = { s.X / 2, s.Y / 2, s.Z / 2 }
	local ey = 0
	for i = 1, 3 do ey += math.abs(ax[i].Y) * half[i] end
	local lo, hi = hmap(Wp.H, c.Y - ey - O.Y), hmap(Wp.H, c.Y + ey - O.Y)
	local mid = Vector3.new(O.X + (c.X - O.X) * Wp.K, O.Y + (lo + hi) / 2, O.Z + (c.Z - O.Z) * Wp.K)
	local dirs, ext = {}, {}
	for i = 1, 3 do
		local u, e = ax[i], half[i]
		if math.abs(u.Y) < 1e-3 then dirs[i], ext[i] = u, e * Wp.K
		elseif math.abs(u.Y) > 0.999 then dirs[i], ext[i] = u, e * (hi - lo) / math.max(2 * ey, 1e-6)
		else
			local w = R.warpPoint(Wp, O, c + u * e) - R.warpPoint(Wp, O, c - u * e)
			dirs[i], ext[i] = w.Unit, w.Magnitude / 2
		end
	end
	-- (a tilted part: the longest axis kept, the others squared to it)
	local order = { 1, 2, 3 }
	table.sort(order, function(a, b) return ext[a] > ext[b] end)
	local a1 = dirs[order[1]]
	local a2 = dirs[order[2]] - a1 * dirs[order[2]]:Dot(a1)
	if a2.Magnitude < 1e-4 then a2 = dirs[order[3]] - a1 * dirs[order[3]]:Dot(a1) end
	a2 = a2.Unit
	local a3 = a1:Cross(a2)
	if a3:Dot(dirs[order[3]]) < 0 then a3 = -a3 end
	local new = {}
	new[order[1]], new[order[2]], new[order[3]] = a1, a2, a3
	-- (keep the frame right-handed: X cross Y = Z)
	if new[1]:Cross(new[2]):Dot(new[3]) < 0 then new[3] = -new[3] end
	local ns = Vector3.new(math.max(ext[1] * 2, 0.02), math.max(ext[2] * 2, 0.02), math.max(ext[3] * 2, 0.02))
	for _, a in p:GetChildren() do
		if a:IsA("Attachment") then
			local q = a.Position
			a.Position = Vector3.new(q.X * ns.X / math.max(s.X, 1e-6), q.Y * ns.Y / math.max(s.Y, 1e-6), q.Z * ns.Z / math.max(s.Z, 1e-6))
		elseif a:IsA("Light") then a.Range = math.min(a.Range * Wp.K, 60) end
	end
	p.Size = ns
	p.CFrame = CFrame.fromMatrix(mid, new[1], new[2], new[3])
end
-- a part that keeps its size and only moves (markers, the regulars' places and points, lamp spots)
local function movePart(Wp, O, p)
	local c = p.Position
	p.CFrame = CFrame.new(R.warpPoint(Wp, O, c)) * p.CFrame.Rotation
	for _, l in p:GetChildren() do if l:IsA("Light") then l.Range = math.min(l.Range * Wp.K, 60) end end
end
-- a thrown body's flight: launched up at vy from the floor, how long until it comes down onto a floor y over the launch
local function flight(vy, y, g)
	local disc = vy * vy - 2 * g * y
	return (vy + math.sqrt(math.max(disc, 0))) / g
end
-- the attributes that hold world points, vectors or heights, through the warp
local POINT_ATTR = { Door = true, Out = true, Approach = true, Aisle = true, Stand = true, Center = true }
local function warpAttrs(Wp, O, inst)
	local top0 = inst:GetAttribute("Top")
	for name, v in inst:GetAttributes() do
		if POINT_ATTR[name] and typeof(v) == "Vector3" then inst:SetAttribute(name, R.warpPoint(Wp, O, v))
		elseif name == "Slide" and typeof(v) == "Vector3" then inst:SetAttribute(name, Vector3.new(v.X * Wp.K, v.Y, v.Z * Wp.K))
		elseif name == "Top" and type(v) == "number" then inst:SetAttribute(name, O.Y + hmap(Wp.H, v - O.Y))
		-- (the gate's roll-up door, GateKit: each slat's shut place is where it now stands; the door rolls up as much
		-- further as its top went up)
		elseif name == "Shut" and typeof(v) == "CFrame" and inst:IsA("BasePart") then inst:SetAttribute(name, inst.CFrame)
		elseif name == "Lift" and type(v) == "number" and type(top0) == "number" then
			inst:SetAttribute(name, v + hmap(Wp.H, top0 - O.Y) - (top0 - O.Y))
		end
	end
end
-- the whole warp over a finished build: every part of the room and of the pads, markers and triggers it made (extras),
-- except the kit models and guns B.put and B.gun already placed through it (attribute Warped)
function R.applyWarp(Wp, O, root, extras)
	local CS = game:GetService("CollectionService")
	local list = {}
	for _, top in { root, table.unpack(extras) } do
		table.insert(list, top)
		for _, d in top:GetDescendants() do table.insert(list, d) end
	end
	local skip = {}
	for _, d in list do if d:GetAttribute("Warped") then skip[d] = true end end
	local function skipped(d)
		local q = d
		while q do if skip[q] then return true end; q = q.Parent end
		return false
	end
	local holo = {}
	for _, d in list do
		if skipped(d) then continue end
		if d:IsA("BasePart") then
			local rigid = CS:HasTag(d, "HubNPC") or CS:HasTag(d, "NPCPoint") or d.Name == "LampSpot" or d.Name == "HubSpawn" or d.Name == "Arrive"
			if d:GetAttribute("HoloEnvelope") then holo[d] = { mid = d.Position.Y, base = d:GetAttribute("Base") or 0 } end
			if rigid then movePart(Wp, O, d) else warpPart(Wp, O, d) end
		end
		warpAttrs(Wp, O, d)
		if d:IsA("Model") and d.PrimaryPart == nil then
			-- (a model's own pivot, which HubLife turns things about: moved with it)
			local pv = d.WorldPivot
			d.WorldPivot = CFrame.new(R.warpPoint(Wp, O, pv.Position)) * pv.Rotation
		end
	end
	-- the holograms' drums: their radius with the plan, their height and their lens with the height map
	for p, h in holo do
		p:SetAttribute("Radius", (p:GetAttribute("Radius") or 1) * Wp.K)
		p:SetAttribute("Height", p.Size.X)
		local lens = O.Y + hmap(Wp.H, h.mid - h.base - O.Y)
		p:SetAttribute("Base", if h.base > 0 then p.Position.Y - lens else 0)
	end
	-- the jump pads' throws: as high over the new balcony as they were over the old, as far out in the new plan
	for _, d in list do
		if d.Name == "JumpPadTop" and typeof(d:GetAttribute("Pad")) == "Vector3" then
			local v = d:GetAttribute("Pad") :: Vector3
			local g = workspace.Gravity
			local up0, up1 = R.UP_Y, hmap(Wp.H, R.UP_Y)
			local vy = math.sqrt(v.Y * v.Y + 2 * g * (up1 - up0))
			local t0, t1 = flight(v.Y, up0, g), flight(vy, up1, g)
			local flat = Vector3.new(v.X, 0, v.Z) * (Wp.K * t0 / t1)
			d:SetAttribute("Pad", Vector3.new(flat.X, vy, flat.Z))
		end
	end
end

local function folderIn(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder"); f.Name = name; f.Parent = parent end
	return f
end
local function hexOf(name) return name:match("_(%x%x%x%x%x%x)$") end

-- where a build's pieces are: the real hub's own folders, or the staging copy's (its Game folder)
function R.prop(new, old) return if lib:FindFirstChild(new) then new else old end
function R.propScale(new, sNew, sOld) return if lib:FindFirstChild(new) then sNew else sOld end
-- the prop kit into ServerStorage.JankfireMeshes, split by the pieces' names ("<model><n>__<kind>_<hex>"), each model's
-- pivot the file's own frame (its footprint's middle on the floor)
function R.importProps(id)
	id = id or R.PROPS
	local ok, container = pcall(function() return game:GetService("InsertService"):LoadAsset(id) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	local MAT = { plastic = SP, neon = Neon }
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = Color3.fromHex(h); d.TextureID = ""
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind ~= "neon"
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	local names = {}
	for name, parts in groups do
		local m = Instance.new("Model")
		m.Name = name
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", id); m:SetAttribute("Kit", "rotunda")
		local old = lib:FindFirstChild(name)
		if old then old:Destroy() end
		m.Parent = lib
		local _, size = m:GetBoundingBox()
		table.insert(names, ("%s %d (%.1f x %.1f x %.1f)"):format(name, #parts, size.X, size.Y, size.Z))
	end
	container:Destroy()
	table.sort(names)
	return #names .. " models" .. (if bad > 0 then ", " .. bad .. " pieces with no name rule" else "") .. "\n  " .. table.concat(names, "\n  ")
end

function R.places(stage) --(stage = the name of a staging copy's folder in workspace.Map; nil = the live hub, else HubStage)
	if not stage then
		local room = hub:FindFirstChild(R.ROOM)
		if room then
			return { live = true, O = R.SITE, room = room, pads = hub:FindFirstChild("QueuePads"), spawns = hub:FindFirstChild("HubSpawns"), arrive = hub.Doors:FindFirstChild("HubArrive"), doors = hub.Doors }
		end
		stage = "HubStage"
	end
	local st = workspace.Map:FindFirstChild(stage)
	local room = st and st:FindFirstChild(R.ROOM)
	local g = room and room:FindFirstChild("Game")
	if not g then return nil end
	return { live = false, O = room:GetAttribute("At") or R.STAGE, room = room, pads = g.QueuePads, spawns = g.HubSpawns, arrive = g.HubArrive, doors = g.Doors }
end
function R.frame(O, bearing, d, z0) return CFrame.new(O + Vector3.new(0, 0, z0 or 0)) * CFrame.Angles(0, -math.rad(bearing), 0) * CFrame.new(0, 0, -(d or 0)) end
-- the bearing, from the focus, of the middle of a side's opening; and how far from the focus a line at that bearing
-- crosses a circle r round the room's middle
function R.liftBearing(side)
	local b, r = math.rad(side * 360 / R.N), R.A + R.WALL / 2
	return math.deg(math.atan2(r * math.sin(b), r * math.cos(b) + R.FOCUS))
end
-- the lift ring's end walls: this many degrees either side of north, from the focus (half a bay past the outer lifts)
function R.endBearing()
	local b5 = R.liftBearing(2)
	return b5 + (b5 - R.liftBearing(12)) / 8
end
function R.reach(bearing, r)
	local b = math.rad(bearing)
	return R.FOCUS * math.cos(b) + math.sqrt(r * r - (R.FOCUS * math.sin(b)) ^ 2)
end

function R.new(live, opts)
	opts = opts or {}
	local pname = if R.PALETTES[opts.palette or R.PALETTE] then opts.palette or R.PALETTE else "arena"
	local P = table.clone(R.PALETTES[pname])
	P.name = pname
	local O = if live then R.SITE else opts.at or R.STAGE
	local stageName = opts.stage or "HubStage"
	-- (opts.version: 3 = Hub v3, through R.V3; 2 = the Rotunda as it was. default R.VERSION. 18 Nov: another building
	-- can use these helpers too, the hotel plaza, HubPlaza: opts.room = its folder's name, opts.mark = the Built
	-- attribute on its pads and markers, opts.version anything but 3 = no warp)
	local version = opts.version or R.VERSION
	local ROOM, MARK = opts.room or R.ROOM, opts.mark or R.MARK
	local B = { live = live, O = O, P = P, G = { ghost = true }, count = 0, lamps = 0, shadows = 0, missing = {},
		version = version, warp = if version == 3 then R.V3 else nil, extra = {}, room = ROOM, builtMark = MARK } -- (not "mark": B.mark is B.rigid's)
	if live then
		for _, n in R.HUB_FOLDERS do local old = hub:FindFirstChild(n); if old then old:Destroy() end end
		for _, f in { folderIn(hub, "QueuePads"), folderIn(hub, "HubSpawns"), folderIn(hub.Doors, "HubArrive"), hub.Doors } do
			for _, c in f:GetChildren() do local b = c:GetAttribute("Built"); if b and table.find(R.HUB_MARKS, b) then c:Destroy() end end
		end
	else
		local stage = workspace.Map:FindFirstChild(stageName); if stage then stage:Destroy() end
	end
	local root = Instance.new("Folder"); root.Name = ROOM
	for _, n in { "Shell", "Scenery", "Collision" } do local f = Instance.new("Folder"); f.Name = n; f.Parent = root end
	B.root = root
	if live then
		B.pads, B.spawnFolder, B.arriveFolder, B.doors = hub.QueuePads, hub.HubSpawns, hub.Doors.HubArrive, hub.Doors
	else
		local g = Instance.new("Folder"); g.Name = "Game"; g.Parent = root
		B.pads, B.spawnFolder, B.arriveFolder, B.doors = folderIn(g, "QueuePads"), folderIn(g, "HubSpawns"), folderIn(g, "HubArrive"), folderIn(g, "Doors")
	end
	function B.fr(bearing, d) return R.frame(O, bearing, d) end
	function B.lf(bearing) return R.frame(O, bearing, 0, R.FOCUS) end -- a frame from the focus
	function B.side(i) return R.frame(O, i * 360 / R.N, 0) end
	function B.wid(r) return 2 * r * math.tan(math.pi / R.N) end -- a side's width, r from the middle

	-- a plain block: x0..x1 across, y0..y1 up, d0..d1 out. o.rot turns it about its own middle, o.ghost = seen but not
	-- felt (paint, trim), o.nc = no collision only
	function B.box(F, folder, name, x0, x1, y0, y1, d0, d1, hex, mat, o)
		o = o or {}
		local p = Instance.new(if o.wedge then "WedgePart" else "Part")
		p.Name = name; p.Anchored = true
		p.Size = Vector3.new(math.max(math.abs(x1 - x0), 0.05), math.max(math.abs(y1 - y0), 0.05), math.max(math.abs(d1 - d0), 0.05))
		p.CFrame = F * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, -(d0 + d1) / 2) * (o.rot or CFrame.identity)
		if P.flat and (mat == Enum.Material.Wood or mat == Enum.Material.Brick) then mat = SP end
		p.Color = Color3.fromHex(hex); p.Material = mat or SP
		p.Transparency = o.tr or 0
		if o.ghost then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end
		if o.nc then p.CanCollide = false end
		if o.noShadow or o.ghost then p.CastShadow = false end
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		if B.mark then p:SetAttribute("Warped", true) end -- (made in world studs inside B.rigid: the warp leaves it be)
		p.Parent = root[folder]
		B.count += 1
		return p
	end
	-- a disc or drum standing on its flat
	function B.cyl(F, folder, name, x, y0, y1, d, dia, hex, mat, o)
		local p = B.box(F, folder, name, x - dia / 2, x + dia / 2, y0, y1, d - dia / 2, d + dia / 2, hex, mat, o)
		p.Shape = Enum.PartType.Cylinder; p.Size = Vector3.new(math.max(y1 - y0, 0.05), dia, dia)
		p.CFrame = F * CFrame.new(x, (y0 + y1) / 2, -d) * CFrame.Angles(0, 0, math.pi / 2)
		return p
	end
	-- a slab w wide and t thick running from (dA, yA) to (dB, yB): dome panels, ribs, sloped soffits
	function B.bar(F, folder, name, x, w, t, dA, yA, dB, yB, hex, mat, o)
		local len = math.sqrt((dB - dA) ^ 2 + (yB - yA) ^ 2)
		local p = B.box(F, folder, name, x - w / 2, x + w / 2, 0, t, 0, len, hex, mat, o)
		p.CFrame = F * CFrame.new(x, (yA + yB) / 2, -(dA + dB) / 2) * CFrame.Angles(math.atan2(yB - yA, dB - dA), 0, 0)
		return p
	end
	-- a block d0..d1 deep and t thick running across a frame from (xA, yA) to (xB, yB): arch stones, cut corners
	function B.spar(F, folder, name, d0, d1, t, xA, yA, xB, yB, hex, mat, o)
		local len = math.sqrt((xB - xA) ^ 2 + (yB - yA) ^ 2)
		local p = B.box(F, folder, name, 0, len, 0, t, d0, d1, hex, mat, o)
		p.CFrame = F * CFrame.new((xA + xB) / 2, (yA + yB) / 2, -(d0 + d1) / 2) * CFrame.Angles(0, 0, math.atan2(yB - yA, xB - xA))
		return p
	end

	local boxSrc = hub.TrainingGround.PropCollision:FindFirstChild("RangeCounterBox")
	function B.solid(name, size, cf)
		local b
		if boxSrc then b = boxSrc:Clone() else b = Instance.new("Part"); b.Transparency = 1; b.Anchored = true; b.CanTouch = false end
		b.Name = name; b.Size = size; b.CFrame = cf; b.Parent = root.Collision
		return b
	end

	-- a model from the kit. (x, y, d) is the middle of its footprint on the floor it stands on (o.seat = "top": y is its
	-- top; "centre": its middle); o.back: the point its back goes against. o.scale, o.stretch = Vector3 (across, up,
	-- front to back; after the scale), o.color = { oldHex = newHex } (else the palette's remap), o.solid = true (its own
	-- box), a Vector3 (a box that size standing where it stands) or a list of { sx, sy, sz, ox, oy, oz }
	function B.put(F, tmpl, name, x, y, d, face, o)
		o = o or {}
		local t = lib:FindFirstChild(tmpl)
		if not t then B.missing[tmpl] = (B.missing[tmpl] or 0) + 1; return nil end
		local m = t:Clone(); m.Name = name or tmpl
		local Wp = B.warp
		local mode = Wp and (o.warp or R.WARP_MODE[tmpl] or "rigid")
		local scale = o.scale
		if mode == "uniform" then scale = (scale or 1) * Wp.K end
		if scale and math.abs(scale - 1) > 0.005 then m:ScaleTo(scale) end
		local bcf, sz = m:GetBoundingBox()
		local st = o.stretch or Vector3.one
		local full = sz * st
		local a = math.rad(face or 0)
		local at = Vector3.new(x, y, -d)
		local backAt = nil
		if o.back then backAt = at; at += Vector3.new(math.sin(a), 0, math.cos(a)) * (full.Z / 2) end
		local cy = if o.seat == "top" then y - full.Y / 2 elseif o.seat == "centre" then y else y + full.Y / 2
		local cf = F * CFrame.new(at.X, cy, at.Z) * CFrame.Angles(0, a, 0)
		-- (Hub v3: the model through the warp as its mode says, R.WARP_MODE. its own solid boxes too: marked Warped, the
		-- post-pass leaves them alone)
		local solidK = Vector3.one
		if Wp then
			local H = Wp.H
			local base0, top0 = cy - full.Y / 2, cy + full.Y / 2
			if mode == "stretch" then
				solidK = Vector3.new(Wp.K, (hmap(H, top0) - hmap(H, base0)) / math.max(full.Y, 1e-6), Wp.K)
			elseif mode == "seat" then
				solidK = Vector3.new(Wp.K, 1, 1)
			end
			st = st * solidK
			if mode == "uniform" then solidK = Vector3.one * Wp.K end
			local nf = sz * st
			local ny
			if mode == "stretch" then ny = hmap(H, base0) + nf.Y / 2
			elseif o.seat == "top" then ny = hmap(H, top0) - nf.Y / 2
			elseif o.seat == "centre" then ny = hmap(H, cy)
			else ny = hmap(H, base0) + nf.Y / 2 end
			local wc = F * Vector3.new(at.X, 0, at.Z)
			local pc
			if backAt then -- (set against a wall: its back stays on the wall)
				local wb = F * Vector3.new(backAt.X, 0, backAt.Z)
				pc = R.warpPoint(Wp, B.O, wb) + (wc - wb) * (if mode == "stretch" then Wp.K else 1)
			else
				pc = R.warpPoint(Wp, B.O, wc)
			end
			cf = CFrame.new(pc.X, B.O.Y + ny, pc.Z) * F.Rotation * CFrame.Angles(0, a, 0)
			full = nf
			if st ~= Vector3.one then o = table.clone(o); o.stretch = st end
			m:SetAttribute("Warped", true)
		end
		m:PivotTo(cf * m:GetPivot():ToObjectSpace(bcf):Inverse())
		for _, p in m:GetDescendants() do
			if not p:IsA("BasePart") then continue end
			p.Anchored = true
			if o.stretch then
				local rel = cf:ToObjectSpace(p.CFrame)
				local function f(v) return math.abs(v.X) * st.X + math.abs(v.Y) * st.Y + math.abs(v.Z) * st.Z end
				p.Size = Vector3.new(p.Size.X * f(rel.RightVector), p.Size.Y * f(rel.UpVector), p.Size.Z * f(rel.LookVector))
				p.CFrame = cf * CFrame.new(rel.Position * st) * rel.Rotation
			end
			local key = hexOf(p.Name)
			local new = key and ((o.color and o.color[key]) or (not o.raw and P.remap[key]))
			if new then p.Color = Color3.fromHex(new) end
			if not o.keepMat and (p.Material == Enum.Material.Metal or p.Material == Enum.Material.Fabric or p.Material == Enum.Material.Rubber or p.Material == Enum.Material.DiamondPlate
				or (P.flat and (p.Material == Enum.Material.Wood or p.Material == Enum.Material.Brick))) then p.Material = SP end
			if o.noShadow then p.CastShadow = false end
		end
		m.Parent = root.Scenery
		local base = cf * CFrame.new(0, -full.Y / 2, 0)
		local k = solidK
		if typeof(o.solid) == "table" then
			for i, b in o.solid do
				local bx = B.solid((name or tmpl) .. "Box" .. i, Vector3.new(b[1], b[2], b[3]) * k, base * CFrame.new((b[4] or 0) * k.X, (b[5] or b[2] / 2) * k.Y, (b[6] or 0) * k.Z))
				if Wp then bx:SetAttribute("Warped", true) end
			end
		elseif o.solid then
			local s = if typeof(o.solid) == "Vector3" then o.solid * k else full
			local bx = B.solid((name or tmpl) .. "Box", s, base * CFrame.new(0, s.Y / 2, 0))
			if Wp then bx:SetAttribute("Warped", true) end
		end
		B.count += 1
		return m, full, cf
	end

	-- one of the game's own weapon models as a display piece, `len` studs long, its middle at (x, y, d) in F. yaw 0 =
	-- its length across F (seen side-on from the middle), -90 or 90 = its length along F's d. no collision, no shadow,
	-- nothing that runs or sounds. its pivot is its middle, so HubLife can turn it in place (tag HubSpin)
	function B.gun(F, wname, len, x, y, d, yaw, name, k) -- (k: a scale shared by every gun on show, instead of fitting each to len)
		local src = game.ReplicatedStorage:FindFirstChild("JankfireWeapons")
		local t = src and src:FindFirstChild(wname)
		if not t then B.missing[wname] = (B.missing[wname] or 0) + 1; return nil end
		local g = t:Clone(); g.Name = name or ("Gun_" .. wname)
		local Tags = game:GetService("CollectionService")
		for _, tag in Tags:GetTags(g) do Tags:RemoveTag(g, tag) end
		for _, q in g:GetDescendants() do
			if q:IsA("BasePart") then q.Anchored = true; q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.CastShadow = false
			elseif q:IsA("LuaSourceContainer") or q:IsA("Sound") or q:IsA("ParticleEmitter") or q:IsA("Light") or q:IsA("Beam") or q:IsA("Trail") then q:Destroy() end
		end
		local _, sz = g:GetBoundingBox()
		g:ScaleTo(g:GetScale() * (k or (len / math.max(sz.Z, 0.01))))
		local bcf = g:GetBoundingBox()
		local at = F * CFrame.new(x, y, -d) * CFrame.Angles(0, math.rad(90 + (yaw or 0)), 0)
		if B.warp then -- (Hub v3: a gun keeps its size and goes where its place went)
			at = CFrame.new(R.warpPoint(B.warp, B.O, at.Position)) * at.Rotation
			g:SetAttribute("Warped", true)
		end
		g:PivotTo(at * g:GetPivot():ToObjectSpace(bcf):Inverse())
		g.PrimaryPart = nil; g.WorldPivot = at
		g.Parent = root.Scenery
		B.count += 1
		return g
	end

	-- words on a plate. lines = { { text, hex, "B" (heavy) or "S", share of the height }, ... } top to bottom. o.both =
	-- the same on the back, o.clear = no plate, o.flush = (x, y, d) is the face the words are on, o.plate = its colour
	function B.text(F, name, lines, w, h, x, y, d, face, o)
		o = o or {}
		local thick = o.thick or 0.3
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Size = Vector3.new(w, h, thick)
		p.Color = Color3.fromHex(o.plate or P.plate); p.Material = SP
		p.Transparency = if o.clear then 1 else 0
		local a = math.rad(face or 0)
		local at = Vector3.new(x, y, -d)
		if o.flush then at -= Vector3.new(math.sin(a), 0, math.cos(a)) * (thick / 2) end
		p.CFrame = F * CFrame.new(at) * CFrame.Angles(0, a + math.pi, 0) * (o.rot or CFrame.identity)
		local sides = { Enum.NormalId.Front }
		if o.both then table.insert(sides, Enum.NormalId.Back) end
		for _, sd in sides do
			local total, tallest = 0, 0
			for _, ln in lines do total += ln[4]; tallest = math.max(tallest, ln[4]) end
			local k = 0.92 / math.max(total, 0.01)
			local g = Instance.new("SurfaceGui")
			g.Name = "Gui"; g.Face = sd; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			g.PixelsPerStud = math.min(o.pps or 30, math.max(8, math.floor(100 / math.max(tallest * k * h, 0.01))))
			g.LightInfluence = 0
			local yAt = 0.04
			for i, ln in lines do
				local t = Instance.new("TextLabel")
				t.Name = "Line" .. i; t.BackgroundTransparency = 1; t.TextScaled = true; t.RichText = o.rich or false
				t.Text = ln[1]; t.TextColor3 = Color3.fromHex(ln[2] or "ffffff")
				t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", if ln[3] == "S" then Enum.FontWeight.SemiBold else Enum.FontWeight.Heavy)
				t.Size = UDim2.new(0.94, 0, ln[4] * k, 0); t.Position = UDim2.new(0.03, 0, yAt, 0)
				t.Parent = g
				yAt += ln[4] * k
			end
			g.Parent = p
		end
		p.Parent = root.Scenery
		B.count += 1
		return p
	end

	-- a real light at a point. o.spot (o.angle, o.face), o.shadows (at most about 11 of those in the hub)
	function B.lamp(F, x, y, d, range, bright, hex, o)
		o = o or {}
		local p = Instance.new("Part")
		p.Name = "LampSpot"; p.Size = Vector3.new(1, 0.2, 1); p.Transparency = 1; p.Anchored = true
		p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.CFrame = F * CFrame.new(x, y, -d)
		local l = Instance.new(if o.spot then "SpotLight" else "PointLight")
		l.Range = range; l.Brightness = bright; l.Color = Color3.fromHex(hex or P.light); l.Shadows = o.shadows or false
		if o.spot then l.Face = o.face or Enum.NormalId.Bottom; l.Angle = o.angle or 120 end
		l.Parent = p
		if B.mark then p:SetAttribute("Warped", true) end
		p.Parent = root.Scenery
		B.lamps += 1
		if l.Shadows then B.shadows += 1 end
		return p
	end
	-- a hologram's place (see the top): its middle at (x, y, d), r across from its axis, h tall. o.base = how far under
	-- its middle the lens it rises from is (0 = no beam), o.slot = which bundle, o.prompt = a ProximityPrompt on it
	function B.holo(F, name, kind, x, y, d, r, h, o)
		o = o or {}
		local p = B.cyl(F, "Scenery", name, x, y - h / 2, y + h / 2, d, 2 * r, P.glow, nil, { ghost = true, tr = 1 })
		p:SetAttribute("Holo", kind); p:SetAttribute("HoloEnvelope", true)
		p:SetAttribute("Radius", r); p:SetAttribute("Height", h); p:SetAttribute("Base", o.base or 0)
		p:SetAttribute("Color", P.holo or P.glow)
		if o.slot then p:SetAttribute("Slot", o.slot) end
		if o.offer then p:SetAttribute("Offer", o.offer) end -- (one offer only: "vip" = the VIP pack's things)
		if o.prompt then
			local pr = Instance.new("ProximityPrompt")
			pr.Name = "BundlePrompt"; pr.ActionText = o.prompt; pr.ObjectText = "Bundle"
			pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
			pr.MaxActivationDistance = 10; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
			pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
			pr.Parent = p
		end
		game:GetService("CollectionService"):AddTag(p, "HubHolo")
		return p
	end
	-- a regular's place (R.NPCS): at (x, y, d), turned yaw degrees from F's -Z (the way they face). "sit": a Seat at about
	-- the cushion's height (HubNPCs.server sets it on the cushion with a ray); "stand": a marker on the floor. tagged HubNPC
	function B.npc(F, who, x, y, d, yaw)
		local info = R.NPCS[who]
		if not info then return nil end
		local p = Instance.new(if info.pose == "sit" then "Seat" else "Part")
		p.Name = "Regular_" .. who .. "_Place"; p.Size = Vector3.new(2, 0.2, 2)
		p.CFrame = F * CFrame.new(x, y + 0.1, -d) * CFrame.Angles(0, math.rad(yaw or 0), 0)
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1; p.CastShadow = false
		if p:IsA("Seat") then p.Disabled = true end -- (HubNPCs.server opens it for its regular only)
		p:SetAttribute("Who", who); p:SetAttribute("User", info.user); p:SetAttribute("Pose", info.pose)
		if info.vipDaily then p:SetAttribute("VipDaily", true) end -- (the shop's VipDaily puts the VIP daily reward's prompt on this spot)
		-- (their idle and the one-shot now and then: HubNPCs plays them; made with Studio's prompt-to-animation tool)
		if info.role then p:SetAttribute("Role", info.role) end
		if info.badge then p:SetAttribute("Badge", info.badge) end -- (a player attribute: while it is true for you, a dot after their name)
		if info.prompt then -- (one style for all four: E, no hold, 8 studs, at chest height)
			local at = Instance.new("Attachment"); at.Name = "PromptAt"; at.Position = Vector3.new(0, if info.pose == "sit" then 1.4 else 3.2, 0); at.Parent = p
			local pr = Instance.new("ProximityPrompt")
			pr.Name = info.prompt[1] .. "Prompt" -- (ShopPrompt, QuestsPrompt, RankedPrompt: as the shop's VipDailyPrompt)
			pr.ActionText = info.prompt[1]; pr.ObjectText = who
			pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
			pr.MaxActivationDistance = 8; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
			pr:SetAttribute(info.prompt[2], info.prompt[3])
			pr.Parent = at
		end
		if info.idle then p:SetAttribute("Idle", info.idle) end
		if info.walk then p:SetAttribute("Walk", info.walk) end
		-- (how they move about: HubNPCs reads Moves and walks or jumps between their points, B.npcPoint)
		if info.moves then p:SetAttribute("Moves", info.moves) end
		if info.moveEvery then p:SetAttribute("MoveEvery", Vector2.new(info.moveEvery[1], info.moveEvery[2])) end
		if info.extra then p:SetAttribute("Extra", info.extra); p:SetAttribute("ExtraLen", info.extraLen or 4) end -- (a one-shot while they keep still: a seated one's while seated)
		if info.extraStand then p:SetAttribute("ExtraStand", info.extraStand); p:SetAttribute("ExtraStandLen", info.extraStandLen or 4) end -- (a seated one's while standing somewhere)
		if info.every then p:SetAttribute("ExtraEvery", Vector2.new(info.every[1], info.every[2])) end
		if info.rise then -- (standing up from a seat, sitting down on one, each with its length)
			p:SetAttribute("Rise", info.rise); p:SetAttribute("RiseLen", info.riseLen or 2)
			p:SetAttribute("Settle", info.settle); p:SetAttribute("SettleLen", info.settleLen or 2.5)
		end
		if info.id then p:SetAttribute("UserId", info.id) end
		if info.width then p:SetAttribute("Width", info.width) end -- (R.check's body across, for them)
		p.Parent = root.Scenery
		game:GetService("CollectionService"):AddTag(p, "HubNPC")
		return p
	end
	-- one of a regular's points (HubNPCs walks or jumps them between these): index 1 is where they start (their place);
	-- kind "seat" / "spot" / "stop" (pause there) / "via" (walk on through); pose "sit" / "stand"; (x, y, d) and yaw as
	-- for B.npc (a seat point stands where a Seat would, so the way they sit on it carries over). o.pause = { min, max }
	-- seconds; o.approach / o.aisle = world points on the floor a seat is reached by. a seat's Stand: where they stand up
	-- to and sit down from, R.NPC_STAND in front of it (o.stand: another world point)
	function B.npcPoint(F, who, index, kind, pose, x, y, d, yaw, o)
		o = o or {}
		local p = Instance.new("Part")
		p.Name = ("NPCPoint_%s_%d"):format(who, index); p.Size = Vector3.new(2, 0.2, 2)
		p.CFrame = F * CFrame.new(x, y + 0.1, -d) * CFrame.Angles(0, math.rad(yaw or 0), 0)
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1; p.CastShadow = false
		p:SetAttribute("Who", who); p:SetAttribute("Index", index); p:SetAttribute("Kind", kind); p:SetAttribute("Pose", pose)
		if o.pause then p:SetAttribute("Pause", Vector2.new(o.pause[1], o.pause[2])) end
		if o.approach then p:SetAttribute("Approach", o.approach) end
		if o.aisle then p:SetAttribute("Aisle", o.aisle) end
		if pose == "sit" then p:SetAttribute("Stand", o.stand or p.CFrame * Vector3.new(0, 0, -R.NPC_STAND)) end
		p.Parent = root.Scenery
		game:GetService("CollectionService"):AddTag(p, "NPCPoint")
		return p
	end
	-- a white light panel let into a ceiling whose underside is y: w across, l deep. o.hex = its colour
	function B.panel(F, x, y, d, w, l, o)
		o = o or {}
		B.box(F, "Scenery", "PanelHousing", x - w / 2 - 0.35, x + w / 2 + 0.35, y - 0.45, y + 0.05, d - l / 2 - 0.35, d + l / 2 + 0.35, P.pier, nil, B.G)
		return B.box(F, "Scenery", "LightPanel", x - w / 2, x + w / 2, y - 0.55, y - 0.4, d - l / 2, d + l / 2, o.hex or P.panel, Neon, B.G)
	end
	-- a kit piece's face that lies on another's (the flicker finder's hits inside a kit model, 18 Nov): the part made `by`
	-- thinner along its most upright axis, about its middle, or keeping its bottom where it is (keep = "bottom")
	function B.unseam(p, by, keep)
		if not (p and p:IsA("BasePart")) then return end
		local cf = p.CFrame
		local ys = { math.abs(cf.XVector.Y), math.abs(cf.YVector.Y), math.abs(cf.ZVector.Y) }
		local k = if ys[1] >= ys[2] and ys[1] >= ys[3] then 1 elseif ys[2] >= ys[3] then 2 else 3
		p.Size -= Vector3.new(if k == 1 then by else 0, if k == 2 then by else 0, if k == 3 then by else 0)
		if keep == "bottom" then p.CFrame = cf - Vector3.new(0, by / 2, 0) end
	end
	-- paint on a floor whose top is y
	function B.paint(F, name, x0, x1, y, d0, d1, hex, lift)
		return B.box(F, "Scenery", name, x0, x1, y + (lift or 0.03), y + (lift or 0.03) + 0.03, d0, d1, hex, nil, B.G)
	end
	-- a thing made in WORLD studs (18 Nov: the arches seen from the lounge, which the warp's stretch of heights over 9.5
	-- had made faceted): fn(Fl) builds it in Fl, a frame at its place on the floor (x, d in F, turned yaw degrees). in
	-- Hub v3 its place goes through the warp but its parts keep their shape (marked Warped)
	function B.rigid(F, x, d, yaw, fn)
		local at = F * Vector3.new(x, 0, -d)
		if B.warp then at = R.warpPoint(B.warp, O, at) end
		local Fl = CFrame.new(at) * F.Rotation * CFrame.Angles(0, math.rad(yaw or 0), 0)
		local was = B.mark
		B.mark = B.warp ~= nil
		fn(Fl)
		B.mark = was
	end
	-- a ball: its middle at (x, y, d) in F, dia across (inside B.rigid: world studs)
	function B.ball(F, folder, name, x, y, d, dia, hex, mat, o)
		local p = B.box(F, folder, name, x - dia / 2, x + dia / 2, y - dia / 2, y + dia / 2, d - dia / 2, d + dia / 2, hex, mat, o)
		p.Shape = Enum.PartType.Ball
		return p
	end

	-- a queue pad: a dark base, the team plates side by side (pink on the left as you face outward, the way the counts
	-- on its board read), each plate's face glowing in its team's colour (owner, 17 Nov: "can we try removing the circles
	-- on the pads and then make them glow?"): a thin neon Glow over the plate with a soft light, which PadGlow.client
	-- breathes slowly while the side is open and brightens while someone stands on it. no circles: a place for everybody
	-- is still a Slot, the marker Matches switches (Off = 1: clear while the place is empty; it says on a screen that
	-- the side is taken), now a speck inside the plate that never shows. y = the top of the deck it lies on
	function B.pad(F, md, x, y, d)
		local m = Instance.new("Model"); m.Name = md.name or md.id
		m:SetAttribute("Mode", md.id); m:SetAttribute("Teams", md.teams); m:SetAttribute("Size", md.size)
		-- (several pads share a mode since the duel hall: PadId tells them apart, Bank says where it stands)
		m:SetAttribute("PadId", m.Name); m:SetAttribute("Bank", md.bank or "lifts")
		m:SetAttribute(if live then "Built" else "ForShow", if live then MARK else true)
		local function plate(pn, cx, cd, sx, sd, hex, mat, yy, th)
			local p = Instance.new("Part")
			p.Name = pn; p.Anchored = true; p.Size = Vector3.new(sx, th, sd)
			p.CFrame = F * CFrame.new(x + cx, y + yy, -(d + cd))
			p.Color = Color3.fromHex(hex); p.Material = mat or SP
			p.CanCollide = false; p.CastShadow = false; p.TopSurface = Enum.SurfaceType.Smooth; p.Parent = m
			return p
		end
		plate("Base", 0, 0, md.w, md.dp, P.padBase, nil, 0.04, 0.08)
		local n = md.teams
		local pw, pd = (md.w - 1.2 - (n - 1) * 0.8) / n, md.dp - 1.2
		local cols = if md.size >= 4 then 2 else 1
		local rows = math.ceil(md.size / cols)
		for i = 1, n do
			local cx = -(md.w - 1.2) / 2 + pw / 2 + (i - 1) * (pw + 0.8)
			local s = plate("Side" .. i, cx, 0, pw, pd, TEAM[i], nil, 0.12, 0.14)
			-- (the plate itself a deep shade of the team's colour; the light is the Glow's)
			s.Color = Color3.fromHex(TEAM[i]):Lerp(Color3.fromHex("1c1f26"), 0.55)
			s:SetAttribute("Team", i)
			local g = plate("Glow", cx, 0, pw - 0.5, pd - 0.5, TEAM[i], Neon, 0.24, 0.04) -- (its top 0.07 over the plate's: no flicker)
			g.CanQuery = false; g.CanTouch = false; g.Transparency = 0.78 -- (open: dim; PadGlow.client lights it when taken)
			g:SetAttribute("Team", i)
			local gl = Instance.new("PointLight")
			gl.Color = Color3.fromHex(TEAM[i]); gl.Range = 7; gl.Brightness = 0.12; gl.Shadows = false
			gl.Parent = g
			for sl = 1, md.size do
				local c, r = (sl - 1) % cols, math.floor((sl - 1) / cols)
				local ox = if cols == 1 then 0 else (c - 0.5) * (pw / 2)
				local od = pd * (0.5 - (r + 0.5) / rows)
				local q = Instance.new("Part") -- (Matches' place marker: a speck inside the plate, seen by no one)
				q.Name = "Slot"; q.Anchored = true; q.Size = Vector3.new(0.05, 0.05, 0.05)
				q.CFrame = F * CFrame.new(x + cx + ox, y + 0.12, -(d + od))
				q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.CastShadow = false
				q.Color = Color3.fromHex(TEAM[i]); q.Transparency = 1
				q:SetAttribute("Team", i); q:SetAttribute("Slot", sl); q:SetAttribute("Off", 1)
				q.Parent = m
			end
		end
		for _, e in { { 0, md.dp / 2 - 0.2, md.w, 0.4 }, { 0, -md.dp / 2 + 0.2, md.w, 0.4 }, { md.w / 2 - 0.2, 0, 0.4, md.dp }, { -md.w / 2 + 0.2, 0, 0.4, md.dp } } do
			plate("Edge", e[1], e[2], e[3], e[4], P.edge, Neon, 0.14, 0.1)
		end
		m.Parent = B.pads
		if live then table.insert(B.extra, m) end -- (outside the room's folder: the warp's post-pass is told of it)
		B.count += 1
		return m
	end
	-- a pad's board, in the pad's model as its Sign: the mode, its kind, and the two lines Matches writes every 0.15 s
	-- on every label named Status and Sub in the pad (who is waiting, in the teams' colours; what happens next)
	function B.board(pad, F, md, w, h, x, y, d, face, o)
		o = o or {}
		local counts = {}
		for t = 1, md.teams do table.insert(counts, ('<font color="#%s">0/%d</font>'):format(TEAM[t], md.size)) end
		local p = B.text(F, "Sign", { { md.title, P.pale, "B", 0.3 }, { md.kind, "c8cdd6", "S", 0.13 }, { table.concat(counts, "   vs   "), "ffffff", "B", 0.33 }, { "step on a side to queue", "c8c8dc", "S", 0.15 } },
			w, h, x, y, d, face, { thick = o.thick or 0.4, plate = o.plate or "20232e", pps = 46, both = o.both })
		for _, g in p:GetChildren() do
			if g:IsA("SurfaceGui") then g.Line3.Name = "Status"; g.Status.RichText = true; g.Line4.Name = "Sub" end
		end
		p.Parent = pad
		return p
	end

	-- where you appear: list of { x, d } in the north frame, standing on a floor y up. each looks north
	local function marker(name, x, y, d, lookBearing, folder)
		local p = Instance.new("Part")
		p.Name = name; p.Size = Vector3.new(2, 0.2, 2); p.Transparency = 1; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		local at = B.fr(0) * Vector3.new(x, y + 0.1, -d)
		local f = B.fr(lookBearing).LookVector
		p.CFrame = CFrame.lookAt(at, at + f)
		if live then p:SetAttribute("Built", MARK); table.insert(B.extra, p) end
		p.Parent = folder
		return p
	end
	function B.spawns(list, y) for _, s in list do marker("HubSpawn", s[1], y, s[2], 0, B.spawnFolder) end end
	-- where the training hall's door lands you: F's own x, d; you look the way `face` says
	function B.arrive(F, list, y, lookBearing)
		for _, s in list do
			local w = F * Vector3.new(s[1], 0, -s[2])
			local l = B.fr(0):PointToObjectSpace(w)
			marker("Arrive", l.X, y, -l.Z, lookBearing, B.arriveFolder)
		end
	end
	-- a box you walk into to be taken somewhere: land = a marker folder in Hub.Doors, or "@TrainSpawns"
	function B.trigger(F, name, x0, x1, y0, y1, d0, d1, land, say)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.Transparency = 1; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Size = Vector3.new(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(d1 - d0))
		p.CFrame = F * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, -(d0 + d1) / 2)
		p:SetAttribute("Land", land); p:SetAttribute("Say", say)
		if live then p:SetAttribute("Built", MARK); table.insert(B.extra, p) end
		p.Parent = B.doors
		return p
	end
	-- a jump pad (Move throws you off any part with a Pad attribute: its launch velocity). vel = (to the right, up, outward)
	function B.jump(F, x, y, d, face, vel, scale)
		scale = scale or 0.8
		B.put(F, "bc_jumppad", "JumpPad", x, y, d, face, { scale = scale, color = { ff4fd8 = P.pier2, ["37d6ff"] = P.pier2, ffe14d = P.ray, d6dbe3 = P.pier2 } })
		local h = 4.2 * scale * 0.8
		local jp = B.box(F, "Scenery", "JumpPadTop", x - h, x + h, y, y + 0.5 * scale, d - h, d + h, P.pier, nil, { tr = 1 })
		jp:SetAttribute("Pad", F:VectorToWorldSpace(Vector3.new(vel.X, vel.Y, -vel.Z)))
		return jp
	end

	function B.done()
		for _, p in root:GetDescendants() do if p:IsA("BasePart") then p.Anchored = true end end
		-- (Hub v3: the whole build through the warp, R.V3, before it goes into the place)
		if B.warp then R.applyWarp(B.warp, O, root, B.extra) end
		root:SetAttribute("Version", B.version)
		root:SetAttribute("Palette", P.name); root:SetAttribute("Live", live); root:SetAttribute("At", O)
		local home = if live then hub else folderIn(workspace.Map, stageName)
		if live then
			hub:SetAttribute("Origin", O) -- (Matches: the fall line is 60 under this, the last-ditch spawn point 3 over it)
			local look = game.ReplicatedStorage.Jankfire:FindFirstChild("HubLook")
			if look then look:SetAttribute("HubTint", P.tint) end
		end
		-- (into the place in pieces: one write of the whole hub can stall Studio)
		local kids = root:GetChildren()
		for _, f in kids do f.Parent = nil end
		root.Parent = home
		for _, f in kids do f.Parent = root; task.wait() end
		local parts = 0
		for _, p in root:GetDescendants() do if p:IsA("BasePart") then parts += 1 end end
		local miss = {}
		for k, n in B.missing do table.insert(miss, k .. " x" .. n) end
		return ("%s v%d (%s) built %s at (%d, %d, %d): %d things, %d parts, %d lamps, %d with shadows%s"):format(ROOM, B.version, P.name, if live then "LIVE" else "as a staging copy", O.X, O.Y, O.Z,
			#root:GetDescendants(), parts, B.lamps, B.shadows, if #miss > 0 then "  MISSING: " .. table.concat(miss, ", ") else "")
	end
	return B
end

-- mode "live" or "stage"; opts (both optional) = { palette = a key of R.PALETTES, at = a staging copy's site, stage =
-- its folder's name in workspace.Map }
function R.build(mode, opts)
	local live = mode == "live"
	local parts = {}
	for _, n in R.PARTS do
		local src = PB:FindFirstChild(n)
		if not src then return "no " .. n .. " in PolishBackup: nothing built" end
		local m = src:Clone(); local fn = require(m); m:Destroy()
		table.insert(parts, fn)
	end
	local B = R.new(live, opts)
	for _, fn in parts do fn(B, R); task.wait() end
	return B.done()
end

-- one staging copy of every palette in R.COMPARE, side by side, each checked
function R.compare()
	local out = {}
	for _, c in R.COMPARE do
		local name = "HubStage_" .. c[1]
		table.insert(out, R.build("stage", { palette = c[1], at = c[2], stage = name }))
		table.insert(out, (R.check(name):match("^[^\n]+")))
	end
	return table.concat(out, "\n")
end

-- the bowling centre back, or the Rotunda: "v3" = Hub v3 (the live hub since 18 Nov), "rotunda" = the Rotunda as it
-- was before (the spare, like the bowling centre); anything else = R.VERSION's
function R.switch(which)
	if which == "plaza" or which == "lounge" then -- (the lounge wing as the hotel plaza or as the spawn lounge, 18 Nov)
		local m = PB.HubRotunda:Clone(); m:SetAttribute("LoungeStyle", which); local R2 = require(m); m:Destroy()
		return R2.build("live") .. "\n" .. R2.check()
	end
	if which == "lanes" then
		local m = PB.HubLab:Clone(); local L = require(m); m:Destroy()
		return "the bowling centre: " .. tostring(L.build("Hub3_Lanes")) .. "\n" .. L.check()
	end
	local version = if which == "rotunda" or which == "v2" then 2 elseif which == "v3" then 3 else nil
	return R.build("live", { version = version }) .. "\n" .. R.check()
end

-- what the other edit-time tools had to learn about this hub, once (2026-11-15). safe to run again: each edit is made
-- only if its old text is still there, exactly once, and the script still parses afterwards.
--   HubLab        its build takes the Rotunda and everything marked Built = "Rotunda" away, so the bowling centre comes
--                 back with HubLab's own usage line
--   OverlapCheck  run() hands over to R.check() while the Rotunda is the hub
--   StudioExport  the four builder modules are in its list of helpers
-- it also takes the staging copy away (workspace.Map.HubStage)
function R.install()
	local out = {}
	local function edit(script, pairs)
		local s = script.Source
		for _, pr in pairs do
			local a, b = pr[1], pr[2]
			local i = s:find(a, 1, true)
			if not i then
				table.insert(out, script.Name .. (if s:find(b, 1, true) then ": already done" else ": OLD TEXT NOT FOUND: " .. a:sub(1, 60)))
				return
			end
			if s:find(a, i + 1, true) then table.insert(out, script.Name .. ": old text is there twice: " .. a:sub(1, 60)); return end
			s = s:sub(1, i - 1) .. b .. s:sub(i + #a)
		end
		local f, err = loadstring(s)
		if not f then table.insert(out, script.Name .. ": would not parse: " .. tostring(err)); return end
		script.Source = s
		table.insert(out, script.Name .. ": edited, " .. #s .. " characters")
	end
	edit(PB.HubLab, {
		{ 'local old = hub:FindFirstChild(L.ROOM); if old then old:Destroy() end\n\t\tH.padFolder',
			'for _, n in { L.ROOM, "Rotunda" } do local old = hub:FindFirstChild(n); if old then old:Destroy() end end -- ("Rotunda": the other hub, built by HubRotunda. only one of the two stands at a time)\n\t\tH.padFolder' },
		{ 'for _, c in f:GetChildren() do if c:GetAttribute("Built") == "HubLab" then c:Destroy() end end',
			'for _, c in f:GetChildren() do local b = c:GetAttribute("Built"); if b == "HubLab" or b == "Rotunda" then c:Destroy() end end' },
	})
	edit(PB.OverlapCheck, {
		{ 'if hub:FindFirstChild("Lanes") then return (require(game.ServerStorage.PolishBackup.HubLab:Clone()) :: any).check() end',
			'if hub:FindFirstChild("Rotunda") then return (require(game.ServerStorage.PolishBackup.HubRotunda:Clone()) :: any).check() end\n\tif hub:FindFirstChild("Lanes") then return (require(game.ServerStorage.PolishBackup.HubLab:Clone()) :: any).check() end' },
	})
	edit(PB.StudioExport, {
		{ '"StudioExport", "HubLab", "KitImport",', '"StudioExport", "HubLab", "HubRotunda", "HubRotundaCentre", "HubRotundaLifts", "HubRotundaRooms", "KitImport",' },
	})
	return table.concat(out, "\n") .. "\n" .. R.unstage() .. "\n" .. R.status()
end
-- every staging copy away (the folders in workspace.Map whose names start with HubStage)
function R.unstage()
	local n = 0
	for _, c in workspace.Map:GetChildren() do if c.Name:sub(1, 8) == "HubStage" then c:Destroy(); n += 1 end end
	return n .. " staging copies removed"
end
-- one line on what stands where
function R.status()
	local n = {}
	table.insert(n, "hub: " .. (if hub:FindFirstChild(R.ROOM) then "the Rotunda" elseif hub:FindFirstChild("Lanes") then "the bowling centre" else "NONE"))
	for _, name in { "QueuePads", "HubSpawns" } do local f = hub:FindFirstChild(name); table.insert(n, name .. " " .. (if f then #f:GetChildren() else 0)) end
	local arr = hub.Doors:FindFirstChild("HubArrive")
	table.insert(n, "HubArrive " .. (if arr then #arr:GetChildren() else 0))
	local doors = {}
	for _, d in hub.Doors:GetChildren() do if d:GetAttribute("Land") then table.insert(doors, d.Name) end end
	table.insert(n, "door triggers: " .. table.concat(doors, " "))
	local live = hub:FindFirstChild(R.ROOM)
	if live then table.insert(n, "palette " .. tostring(live:GetAttribute("Palette")) .. ", Live " .. tostring(live:GetAttribute("Live"))) end
	local st = 0
	for _, c in workspace.Map:GetChildren() do if c.Name:sub(1, 8) == "HubStage" then st += 1 end end
	table.insert(n, "staging copies " .. st)
	table.insert(n, "Lighting.Previewing " .. tostring(game.Lighting:GetAttribute("Previewing")))
	table.insert(n, "HubTint " .. tostring(game.ReplicatedStorage.Jankfire.HubLook:GetAttribute("HubTint")))
	local calm, all = 0, 0
	local ws = game.ReplicatedStorage:FindFirstChild("JankfireWeapons")
	for _, w in (if ws then ws:GetChildren() else {}) do all += 1; if w:GetAttribute("Paint") == "calm" then calm += 1 end end
	table.insert(n, ("weapons in the calm paint %d of %d"):format(calm, all))
	return table.concat(n, ", ")
end

-- ------------------------------------------------------------------ the check
-- walks that must stay clear, 0.4 to 8 over their floor: { what, bearing, x0, x1, d0, d1, floor y }
R.WALKS = {}
-- from where the leak test looks out in 26 directions: { bearing, x, y, d }
R.LEAKS = {}
-- spots other sessions keep their things in, outside the Rotunda's folders (their things are never checked here): nothing
-- the builder makes may stand in them. Hub v3 only (world numbers): { what, its middle on the floor from the hub's site,
-- its size; it starts 0.4 over the floor }
R.KEEP = {
	-- (Dumpling's box went on 18 Nov: the lore NPCs, Dumpling too, appear only in their code cutscene now, never in the world)
}
-- what must show from every spawn point besides the pads' plates and boards: { what, its name in Scenery }
R.SIGHTS = { { "the name on the gallery over the middle lift", "GalleryName" } }
-- the overlap test: kit models set into walls, lids or floors on purpose are left out; parts are shrunk by this much first
R.STRUCTURE = { Pier = true, Rail = true, DomeRing = true, Bezel = true, TrainingPortal = true, WallLight = true, DropLight = true, CrownDuck = true, HoloProjector = true, HoloDuck = true }
R.OVERLAP_GAP = 0.06
local STEP = 360 / R.N
local GYM, LOUNGE, ARM = 4 * STEP, 7 * STEP, 10 * STEP
R.DECK0, R.DECK1 = 49.8, 62.6 -- a lift's deck, from the focus: its front and the face of the wall behind it
for _, md in R.MODES do
	local b = R.liftBearing(md.side)
	table.insert(R.WALKS, { "the way from the platform to the " .. md.title .. " lift", b, -4.2, 4.2, R.reach(b, 14), R.DECK0 - 0.2, 0, R.FOCUS })
	table.insert(R.WALKS, { "the walk in front of the " .. md.title .. " lift", b, -5, 5, R.reach(b, 33.2), R.DECK0 - 0.2, 0, R.FOCUS })
	table.insert(R.LEAKS, { b, 0, 6, 43, R.FOCUS }); table.insert(R.LEAKS, { b, 0, 10, 56, R.FOCUS })
	table.insert(R.SIGHTS, { md.title .. " over its way in", "Way_" .. md.id })
end
-- (the lounge's three arches: from the platform's foot out through each into the lounge, and its front floor to the spawn rug)
local PLAZA = R.LOUNGE_STYLE == "plaza"
for _, w in { { "the way through the lounge's middle arch", LOUNGE, -4.2, 4.2, 14, if PLAZA then 40 else 34, 0 }, { "the way through the east arch", 6 * STEP, -4.2, 4.2, 15, if PLAZA then 31 else 34, 0 },
	{ "the way through the west arch", 8 * STEP, -4.2, 4.2, 15, if PLAZA then 31 else 34, 0 }, { "the way to the gym", GYM, -4.5, 4.5, 14, 44.5, 0 },
	if R.EGG_SIDE then { "the hub egg's nook over the west arch", 8 * STEP, -3, 3, 31.6, 37.2, 17 } else nil, -- (kept clear for training-v2's egg, Map.Hub.HubEgg: R.EGG_NICHE)
	{ "the gym's aisle south of the ring", GYM, 10.6, 13.2, 47.8, 70, 0 }, { "the gym's aisle north of the ring", GYM, -15.8, -10.6, 48, 68, 0 },
	-- (since the armory's makeover, 18 Nov: a row of open cases either side of the aisle, |x| 4.75..7.25, the aisle clear
	-- between them to the gate, and a lane down each side between the cases and the walls)
	{ "the way to the training gate", ARM, -4.2, 4.2, 14, 60.4, 0 }, { "the armory's aisle", ARM, -4.5, 4.5, 40.2, 60.4, 0 },
	{ "the armory's west lane", ARM, -10.3, -7.5, 41.6, 60.4, 0 },
	{ "the armory's east lane", ARM, 7.5, 9.5, 41.6, 60.4, 0 } } do table.insert(R.WALKS, w) end
local LS = R.LOUNGE_S
for _, p in { { 0, 0, 8, 0 }, { 0, 0, 22, 0 }, { 0, 0, 18, 25 }, { 180, 0, 18, 25 }, { 8 * STEP, 0, 20, 34 },
	{ GYM, 0, 6, 35 }, { GYM, 0, 9, 50 }, { GYM, 0, 9, 70 }, { ARM, 0, 6, 34 }, { ARM, 0, 6, 50 } } do table.insert(R.LEAKS, p) end
if PLAZA then -- (the courtyard low and high, each arcade, the VIP room behind the south one)
	local V = R.PLAZA.BACK + 2 -- (the VIP room's near wall's face)
	for _, p in { { LOUNGE, 0, 6, 34 }, { LOUNGE, 0, 6, 52 }, { LOUNGE, 0, 20, 50 }, { LOUNGE, 0, 26, 64 }, { LOUNGE, -12, 22, 40 }, { LOUNGE, 12, 22, 40 }, { LOUNGE, -15, 8, 66 }, { LOUNGE, 15, 8, 66 },
		{ LOUNGE, -13, 14, 31 }, { LOUNGE, 13, 14, 31 }, { LOUNGE, -24, 6, 34 }, { LOUNGE, 24, 6, 34 }, { LOUNGE, -24, 9, 62 }, { LOUNGE, 24, 9, 62 }, { LOUNGE, -12, 6, 74 }, { LOUNGE, 12, 9, 74 },
		{ LOUNGE, 0, 5, V + 8 }, { LOUNGE, 6, 8, V + 14 } } do table.insert(R.LEAKS, p) end
else
	for _, p in { { LOUNGE, 0, 6, 34 }, { LOUNGE, 0, 6, 50 + LS }, { LOUNGE, 0, 5, 70 + LS }, { LOUNGE, 6, 8, 76 + LS },
		{ LOUNGE, -22, 8, 40 }, { LOUNGE, 22, 8, 40 }, { LOUNGE, -22, 12, 62 }, { LOUNGE, 22, 12, 62 }, { LOUNGE, -24, 6, 29 }, { LOUNGE, 24, 6, 29 }, { LOUNGE, -13, 14, 31 }, { LOUNGE, 13, 14, 31 } } do table.insert(R.LEAKS, p) end
end
-- (w[3]: true = a thing in a room, looked for from the middle of the platform only; "lounge" = in the lounge, looked
-- for from the front of the spawn rug, R.LOUNGE_LOOK)
for _, w in { { "TRAINING over the armory's hatch", "Way_training" }, { "GYM over its door", "Way_gym" }, { "LOUNGE over its arch", "Way_lounge" },
	if PLAZA then { "the duck on the plaza's fountain", "FountainDuck", "lounge" } else { "the duck in the lounge", "HoloDuck", "lounge" },
	{ "the training gate at the armory's far end", "TrainingPortal", true }, { "the target at the gym's far end", "Target", true } } do table.insert(R.SIGHTS, w) end
-- what every spawn point must show on the first look out of the lounge (any one of each group's parts, by name in
-- Scenery or a pad): the way to the pads and the way up
-- (a group's second field may name several parts, "A|B": any one of them will do. 18 Nov, the owner: "I dont like the
-- pillar of light from the teleporter", so the jump pads' light column is gone; from the spawn the pads' ring and the
-- UPSTAIRS boards are behind the piers, so the way up there is the lit doorways)
R.FIRST_LOOK = { { "the name over the middle lift", "GalleryName" }, { "a lit doorway into the second floor", "UpperGlowHead" },
	{ "the 2V2 lift's pad", "pad:2v2" } }
-- the second floor: its walk stays clear; inside it no ray gets out
do
	local UY = R.UP_Y
	for i, u in R.UPPER do
		local b = (i - (#R.UPPER + 1) / 2) * R.UP_PITCH
		local dp = R.UP_SIZE[R.MODES[u.mode].id][2]
		table.insert(R.WALKS, { "the second floor's walk in front of pad " .. u.name, b, -3.5, 3.5, R.reach(b, R.A + R.WALL + 1.5), R.UP_OUT - 1.2 - dp - 0.3, UY, R.FOCUS })
		table.insert(R.LEAKS, { b, 0, UY + 6, 46, R.FOCUS }); table.insert(R.LEAKS, { b, 0, UY + 10, 62, R.FOCUS })
	end
end
-- (the bundles: 3 on side 9 by the arches, 1, 2 and 4 in the lounge's showroom)
for _, k in { 1, 2, 4 } do table.insert(R.SIGHTS, { "the bundle hologram on plinth " .. k, "HoloBundle" .. k, "lounge" }) end
table.insert(R.SIGHTS, { "the bundle hologram on plinth 3", "HoloBundle3", true })

local function obb(cfA, hA, cfB, hB)
	local A = { cfA.RightVector, cfA.UpVector, cfA.LookVector }
	local Bx = { cfB.RightVector, cfB.UpVector, cfB.LookVector }
	local a, b = { hA.X, hA.Y, hA.Z }, { hB.X, hB.Y, hB.Z }
	local T = cfB.Position - cfA.Position
	local function sep(ax)
		local ra, rb = 0, 0
		for i = 1, 3 do ra += a[i] * math.abs(A[i]:Dot(ax)); rb += b[i] * math.abs(Bx[i]:Dot(ax)) end
		return math.abs(T:Dot(ax)) > ra + rb - 0.05
	end
	for i = 1, 3 do if sep(A[i]) or sep(Bx[i]) then return false end end
	for i = 1, 3 do for j = 1, 3 do local c = A[i]:Cross(Bx[j]); if c.Magnitude > 1e-4 and sep(c.Unit) then return false end end end
	return true
end

function R.check(stage)
	local W = R.places(stage)
	if not W then return "no " .. R.ROOM .. " in Map.Hub or Map.HubStage: build it first" end
	local room, O = W.room, W.O
	-- (Hub v3: the check's own places, written for the Rotunda's plan, through the same warp as the build)
	local Wp = R.warpOf(room)
	local KK = if Wp then Wp.K else 1
	local function WP(v) return R.warpPoint(Wp, O, v) end
	local function HY(y) return if Wp then hmap(Wp.H, y) else y end
	local zones = {}
	local function zone(what, cf, half) table.insert(zones, { what = what, cf = cf, half = half }) end
	for _, f in { W.spawns, W.arrive } do
		for _, s in f:GetChildren() do
			if s:GetAttribute("Built") == R.MARK or not W.live then
				local p = s.Position
				zone(("%s at (%.1f, %.1f)"):format(s.Name, p.X - O.X, p.Z - O.Z), CFrame.new(p.X, p.Y - 0.1 + 4.2, p.Z), Vector3.new(4, 3.8, 4))
			end
		end
	end
	-- (the middle of the spawn points, on the floor: the spawn rug in the lounge since 18 Nov)
	local spawnMid, nS = Vector3.zero, 0
	for _, s in W.spawns:GetChildren() do
		if W.live and s:GetAttribute("Built") ~= R.MARK then continue end
		spawnMid += s.Position - Vector3.new(0, 0.1, 0); nS += 1
	end
	spawnMid = if nS > 0 then spawnMid / nS else O
	local pads = {}
	for _, pad in W.pads:GetChildren() do
		if pad:IsA("Model") and (pad:GetAttribute("Built") == R.MARK or not W.live) then
			table.insert(pads, pad)
			local b = pad:FindFirstChild("Base")
			if b then zone("pad " .. pad.Name, b.CFrame * CFrame.new(0, 4.2, 0), Vector3.new(b.Size.X / 2, 3.8, b.Size.Z / 2)) end
		end
	end
	for _, w in R.WALKS do
		local fr = R.frame(O, w[2], 0, w[8])
		local mid = WP(fr * Vector3.new((w[3] + w[4]) / 2, w[7] or 0, -(w[5] + w[6]) / 2))
		zone(w[1], CFrame.new(mid + Vector3.new(0, 4.2, 0)) * fr.Rotation, Vector3.new(math.abs(w[4] - w[3]) / 2 * KK, 3.8, math.abs(w[6] - w[5]) / 2 * KK))
	end
	if Wp then for _, k in R.KEEP do zone(k[1], CFrame.new(O + k[2] + Vector3.new(0, 0.4 + k[3].Y / 2, 0)), k[3] / 2) end end
	local issues, seen, looked = {}, {}, 0
	local game_ = room:FindFirstChild("Game")
	for _, p in room:GetDescendants() do
		-- (a thing counts if you can see it or bump into it: lamp points and markers do not)
		if not p:IsA("BasePart") or (p.Transparency >= 1 and not p.CanCollide and not (p:GetAttribute("HoloEnvelope") and p:GetAttribute("Holo") ~= "loadout")) or (game_ and p:IsDescendantOf(game_)) then continue end
		looked += 1
		local round = p:IsA("Part") and p.Shape == Enum.PartType.Cylinder
		for _, z in zones do
			local hit = obb(p.CFrame, p.Size / 2, z.cf, z.half)
			-- (a drum standing on its flat is round: how far its axis is from the zone's box decides)
			if hit and round and math.abs(p.CFrame.RightVector.Y) > 0.99 then
				local c = z.cf:PointToObjectSpace(p.Position)
				local dx, dz = math.max(math.abs(c.X) - z.half.X, 0), math.max(math.abs(c.Z) - z.half.Z, 0)
				hit = dx * dx + dz * dz < (p.Size.Y / 2 - 0.05) ^ 2
			end
			if hit then
				local top = p
				while top.Parent and top.Parent.Parent ~= room do top = top.Parent end
				local line = ("%s/%s  in  %s"):format(top.Parent and top.Parent.Name or "?", top.Name, z.what)
				if not seen[line] then seen[line] = true; table.insert(issues, line) end
			end
		end
	end
	-- props through props (the owner's play-test, 16 Nov: an SMG through a case, the katana through an ammo box): every
	-- pair of kit models and display guns in Scenery, part against part, each part shrunk by R.OVERLAP_GAP so things
	-- that only touch pass. the structural kit set into walls and lids on purpose (R.STRUCTURE) is left out
	local props = {}
	for _, m in room.Scenery:GetChildren() do
		if not m:IsA("Model") or R.STRUCTURE[m.Name] then continue end
		local parts = {}
		for _, p in m:GetDescendants() do if p:IsA("BasePart") and p.Transparency < 0.95 then table.insert(parts, p) end end
		if #parts > 0 then local cf, sz = m:GetBoundingBox(); table.insert(props, { m = m, parts = parts, cf = cf, half = sz / 2 }) end
	end
	local g = R.OVERLAP_GAP
	local function shrunk(p) return Vector3.new(math.max(p.Size.X / 2 - g, 0.01), math.max(p.Size.Y / 2 - g, 0.01), math.max(p.Size.Z / 2 - g, 0.01)) end
	local overlaps = 0
	for i = 1, #props do
		for j = i + 1, #props do
			local a, b = props[i], props[j]
			if not obb(a.cf, a.half, b.cf, b.half) then continue end
			local hit = nil
			for _, p in a.parts do
				for _, q in b.parts do
					if obb(p.CFrame, shrunk(p), q.CFrame, shrunk(q)) then hit = { p, q }; break end
				end
				if hit then break end
			end
			if hit then
				overlaps += 1
				local at = hit[1].Position - O
				table.insert(issues, ("OVERLAP: %s (%s) goes into %s (%s) near (%.1f, %.1f, %.1f)"):format(a.m.Name, hit[1].Name, b.m.Name, hit[2].Name, at.X, at.Y, at.Z))
			end
		end
	end
	-- the route (the main session, 16 Nov: "a fresh spawn reaches every pad on both floors using the jump pads"): a body
	-- is swept from the spawn rows to the front of every pad and onto it. to a lift: past the projector and straight out
	-- through its opening. to the second floor: to the jump pad on the pad's side; then the throw (the pad's velocity under
	-- the place's gravity, until the body lands: it must land on the balcony); then along the balcony to the doorway over
	-- the outer lift, through it, and along the upper walk. anything solid in the way, a throw that lands anywhere else,
	-- or a waypoint with no floor under it, is a problem
	local routes = 0
	local landings = {} -- (where each jump pad lands you: the sight test below looks for the doorway from there)
	do
		local rp2 = RaycastParams.new(); rp2.FilterType = Enum.RaycastFilterType.Include; rp2.FilterDescendantsInstances = { room }; rp2.RespectCanCollide = true
		local BODY, LIFT = Vector3.new(1.8, 3, 1.8), 2.8 -- (walking: its middle 2.8 over the floor, so it clears kerbs and steps)
		local FULL = Vector3.new(1.8, 4.6, 1.8) -- (thrown: the whole body, feet to head)
		local function lf(b, x, y, d) return WP(R.frame(O, b, 0, R.FOCUS) * Vector3.new(x, y, -d)) end
		local function mf(b, x, y, d) return WP(R.frame(O, b, 0) * Vector3.new(x, y, -d)) end
		local UY, ST = R.UP_Y, 360 / R.N
		-- (from the middle of the spawn points, in the lounge since 18 Nov, out through the middle arch to TA, then on)
		local start = spawnMid
		local TA = mf(180, 0, 0, 25)
		local nUp = #R.UPPER
		local function upBearing(i) return (i - (nUp + 1) / 2) * R.UP_PITCH end
		-- each jump pad's throw, once
		local land, padAt = {}, {}
		for _, jp in room.Scenery:GetChildren() do
			if jp.Name ~= "JumpPadTop" or typeof(jp:GetAttribute("Pad")) ~= "Vector3" then continue end
			local side = if R.frame(O, 0, 0):PointToObjectSpace(jp.Position).X >= 0 then 1 else -1 -- (1: east, side 3)
			local name = if side > 0 then "3" else "11"
			padAt[side] = Vector3.new(jp.Position.X, O.Y, jp.Position.Z)
			local v = jp:GetAttribute("Pad") :: Vector3
			local p = jp.Position + Vector3.new(0, jp.Size.Y / 2 + FULL.Y / 2 + 0.05, 0)
			local g = Vector3.new(0, -workspace.Gravity, 0)
			local dt, hit = 1 / 30, nil
			for _ = 1, 150 do
				local nv = v + g * dt
				local step = (v + nv) / 2 * dt
				hit = workspace:Blockcast(CFrame.new(p), FULL, step, rp2)
				if hit and hit.Normal.Y <= 0.7 then -- (a wall: it stops you going sideways, you slide down it)
					v = Vector3.new(0, v.Y, 0); hit = nil; continue
				end
				if hit then break end
				p += step; v = nv
			end
			if hit and hit.Normal.Y > 0.7 then
				local at = hit.Position
				local r = Vector3.new(at.X - O.X, 0, at.Z - O.Z).Magnitude
				if math.abs(at.Y - (O.Y + HY(UY))) < 0.6 and r > R.RING_IN * KK - 0.5 and r < R.A * KK then
					land[side] = at
					table.insert(landings, at)
				else
					table.insert(issues, ("ROUTE: the jump pad on side %s lands you at (%.1f, %.1f, %.1f), not on the balcony"):format(name, at.X - O.X, at.Y - O.Y, at.Z - O.Z))
				end
			else
				table.insert(issues, ("ROUTE: the jump pad on side %s throws you into %s"):format(name, if hit then hit.Instance.Name else "nothing"))
			end
		end
		local function walk(pts, what)
			for k = 1, #pts - 1 do
				local A, Bp = pts[k] + Vector3.new(0, LIFT, 0), pts[k + 1] + Vector3.new(0, LIFT, 0)
				local hit = workspace:Blockcast(CFrame.lookAt(A, Bp), BODY, Bp - A, rp2)
				if hit then
					table.insert(issues, ("ROUTE: the walk to pad %s is blocked at step %d by %s near (%.1f, %.1f, %.1f)"):format(what, k, hit.Instance.Name, hit.Position.X - O.X, hit.Position.Y - O.Y, hit.Position.Z - O.Z))
					return false
				end
				if not workspace:Raycast(pts[k + 1] + Vector3.new(0, 3, 0), Vector3.new(0, -5, 0), rp2) then
					table.insert(issues, ("ROUTE: no floor under the walk to pad %s at step %d"):format(what, k + 1))
					return false
				end
			end
			return true
		end
		for _, pad in pads do
			local base = pad:FindFirstChild("Base")
			if not base then continue end
			local fy = base.Position.Y - 0.08
			local fr = base.CFrame * Vector3.new(0, 0, base.Size.Z / 2 + 2.5)
			local front = Vector3.new(fr.X, fy, fr.Z)
			local onto = Vector3.new(base.Position.X, fy, base.Position.Z)
			routes += 1
			if pad:GetAttribute("Bank") == "upper" then
				local idx = 0
				for i, u in R.UPPER do if u.name == pad.Name then idx = i end end
				local s = if idx >= (nUp + 1) / 2 then 1 else -1 -- (the middle pad and the east ones: the east jump pad)
				local L, J = land[s], padAt[s]
				if not L or not J then continue end -- (the throw's problem is listed already)
				if not walk({ start, TA, J }, pad.Name) then continue end
				local pts = { L, mf(s * 2.5 * ST, 0, UY, 25.3), mf(s * 2 * ST, 0, UY, 25.3), mf(s * 2 * ST, 0, UY, 31), lf(s * R.liftBearing(2), 0, UY, 40) }
				for i = if s > 0 then nUp else 1, idx, -s do table.insert(pts, lf(upBearing(i), 0, UY, 47)) end
				table.insert(pts, front); table.insert(pts, onto)
				walk(pts, pad.Name)
			else
				local rel = CFrame.new(WP(R.frame(O, 0, 0, R.FOCUS).Position)):PointToObjectSpace(front)
				local b = math.deg(math.atan2(rel.X, -rel.Z))
				walk({ start, TA, mf(0, if b >= 0 then 7 else -7, 1.24, 0), lf(b, 0, 0, R.reach(b, R.A + R.WALL + 3)), front, onto }, pad.Name)
			end
		end
	end
	-- sight: from the eye over every spawn marker (4.7 over it) the middle of every pad's plates, three points across
	-- every board and everything in R.SIGHTS must show. anything you can see counts as in the way, solid or not; a
	-- part is tested as its own box, turned as it is turned
	local blockers = {}
	for _, f in { room, W.pads } do
		for _, q in f:GetDescendants() do
			if q:IsA("BasePart") and (q.Transparency < 0.5 or (q:GetAttribute("HoloEnvelope") and q:GetAttribute("Holo") ~= "loadout")) then -- (a bundle hologram's drum: what may stand there. the loadout hologram over the platform is see-through and walk-through: it hides nothing)
				local cf, h = q.CFrame, q.Size / 2
				local r, u, l = cf.RightVector, cf.UpVector, cf.LookVector
				local e = Vector3.new(math.abs(r.X) * h.X + math.abs(u.X) * h.Y + math.abs(l.X) * h.Z, math.abs(r.Y) * h.X + math.abs(u.Y) * h.Y + math.abs(l.Y) * h.Z, math.abs(r.Z) * h.X + math.abs(u.Z) * h.Y + math.abs(l.Z) * h.Z)
				table.insert(blockers, { p = q, lo = cf.Position - e, hi = cf.Position + e, round = q:IsA("Part") and q.Shape == Enum.PartType.Cylinder })
			end
		end
	end
	local function hidden(a, b, target, fam)
		local dv = b - a
		local len = dv.Magnitude
		local lo, hi = a:Min(b), a:Max(b)
		fam = fam or (if target.Parent:IsA("Model") then target.Parent else nil)
		for _, k in blockers do
			if k.p ~= target and not (fam and k.p:IsDescendantOf(fam)) and not (k.hi.X < lo.X or k.lo.X > hi.X or k.hi.Y < lo.Y or k.lo.Y > hi.Y or k.hi.Z < lo.Z or k.lo.Z > hi.Z) then
				local cf, h = k.p.CFrame, k.p.Size / 2
				for t = 1, len - 1, 0.25 do -- (not the first stud or the last)
					local q = cf:PointToObjectSpace(a + dv * (t / len))
					if math.abs(q.X) < h.X and math.abs(q.Y) < h.Y and math.abs(q.Z) < h.Z and (not k.round or q.Y * q.Y + q.Z * q.Z < h.Y * h.Y) then return k.p end
				end
			end
		end
		return nil
	end
	local targets = {}
	for _, pad in pads do
		if pad:GetAttribute("Bank") ~= "lifts" then continue end -- (the second floor's pads are behind the balcony: not seen from the spawn)
		for _, c in pad:GetChildren() do
			if c:IsA("BasePart") and c.Name:sub(1, 4) == "Side" then table.insert(targets, { "pad " .. pad.Name .. "'s " .. c.Name, c, c.Position, pad }) end
		end
		local sign = pad:FindFirstChild("Sign")
		if sign then for _, k in { -0.3, 0, 0.3 } do table.insert(targets, { "the board of " .. pad.Name, sign, sign.Position + sign.CFrame.RightVector * (sign.Size.X * k), pad }) end end
	end
	local inside = {} -- (looked for from the middle of the platform only: a room is not seen into from every spawn point)
	local insideL = {} -- (the lounge's: from the middle of the spawn rug)
	for _, w in R.SIGHTS do
		local q, fam = room.Scenery:FindFirstChild(w[2]), nil
		if q and q:IsA("Model") then fam = q; q = q.PrimaryPart or q:FindFirstChildWhichIsA("BasePart", true) end
		if q then table.insert(if w[3] == "lounge" then insideL elseif w[3] then inside else targets, { w[1], q, if fam then fam:GetBoundingBox().Position else q.Position, fam }) else table.insert(issues, "SIGHT: nothing called " .. w[2] .. " to look for") end
	end
	local sights, lines, shut, spawnN = {}, 0, 0, 0
	-- (where each jump pad lands you: the nearest doorway into the second floor must show from there)
	for _, L in landings do
		local best, bd = nil, math.huge
		for _, q in room.Scenery:GetChildren() do
			if q.Name == "UpperHead" and (q.Position - L).Magnitude < bd then best, bd = q, (q.Position - L).Magnitude end
		end
		if best then
			lines += 1
			local inward = Vector3.new(O.X - L.X, 0, O.Z - L.Z).Unit * 1.5 * KK -- (a step off the wall, where you stand up)
			local by = hidden(L + inward + Vector3.new(0, 4.7, 0), best.Position, best)
			if by then shut += 1; table.insert(sights, ("SIGHT: %s hides the doorway into the second floor from where a jump pad lands you"):format(by.Name)) end
		else table.insert(issues, "SIGHT: no doorway into the second floor near where a jump pad lands you") end
	end
	for _, t in inside do
		lines += 1
		local by = hidden(O + Vector3.new(0, 5.9, 0), t[3], t[2], t[4])
		if by then shut += 1; table.insert(sights, ("SIGHT: %s hides %s from the middle of the platform"):format(by.Name, t[1])) end
	end
	for _, t in insideL do
		lines += 1
		local by = hidden(WP(R.frame(O, 180, 0) * Vector3.new(R.LOUNGE_LOOK[1], 5.2, -R.LOUNGE_LOOK[2])), t[3], t[2], t[4])
		if by then shut += 1; table.insert(sights, ("SIGHT: %s hides %s from the front of the spawn rug"):format(by.Name, t[1])) end
	end
	-- the lifts' pads and boards, the name and every way out's word: from where you come out onto the platform (they were
	-- tested from the spawn points while those stood there)
	for _, lp in R.PLATFORM_LOOK do
		local eye = WP(R.frame(O, 0, 0) * Vector3.new(lp[1], 1.3, -lp[2])) + Vector3.new(0, 4.7, 0)
		for _, t in targets do
			lines += 1
			local by = hidden(eye, t[3], t[2], t[4])
			if by then
				shut += 1
				local line = ("SIGHT: %s hides %s from the platform at (%.1f, %.1f)"):format(by.Name, t[1], eye.X - O.X, eye.Z - O.Z)
				if not seen[line] then seen[line] = true; table.insert(sights, line) end
			end
		end
	end
	-- the first look from every spawn point (18 Nov, the main session: "from the new spawn, take one look round. The way up
	-- and the pads upstairs should be obvious within a few seconds"): one of each R.FIRST_LOOK group must show
	local groups = {}
	for _, g in R.FIRST_LOOK do
		local list = {}
		local padId = g[2]:match("^pad:(.+)$")
		if padId then
			for _, pad in pads do
				if pad.Name ~= padId then continue end
				for _, c in pad:GetChildren() do if c:IsA("BasePart") and c.Name:sub(1, 4) == "Side" then table.insert(list, { c, c.Position, pad }) end end
			end
		else
			local names = {}
			for n in g[2]:gmatch("[^|]+") do names[n] = true end
			for _, q in room.Scenery:GetChildren() do if names[q.Name] and q:IsA("BasePart") then table.insert(list, { q, q.Position, nil }) end end
		end
		if #list == 0 then table.insert(issues, "SIGHT: nothing called " .. g[2] .. " for the first look") end
		table.insert(groups, { g[1], list })
	end
	for _, s in W.spawns:GetChildren() do
		if W.live and s:GetAttribute("Built") ~= R.MARK then continue end
		spawnN += 1
		local eye = s.Position + Vector3.new(0, 4.7, 0)
		for _, g in groups do
			if #g[2] == 0 then continue end
			lines += 1
			local ok, by = false, nil
			for _, c in g[2] do
				local h = hidden(eye, c[2], c[1], c[3])
				if not h then ok = true; break end
				by = by or h
			end
			if not ok then
				shut += 1
				table.insert(sights, ("SIGHT: from the spawn point at (%.1f, %.1f) no %s shows (%s in the way)"):format(s.Position.X - O.X, s.Position.Z - O.Z, g[1], if by then by.Name else "?"))
			end
		end
	end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { room.Shell }
	local leaks = 0
	for _, from in R.LEAKS do
		local at = WP(R.frame(O, from[1], 0, from[5]) * Vector3.new(from[2], from[3], -from[4]))
		for x = -1, 1 do for y = -1, 1 do for z = -1, 1 do
			if not (x == 0 and y == 0 and z == 0) and not workspace:Raycast(at, Vector3.new(x, y, z).Unit * 500, rp) then
				leaks += 1; table.insert(issues, ("LEAK from bearing %.0f, x %.0f, y %.0f, d %.0f toward (%d, %d, %d)"):format(from[1], from[2], from[3], from[4], x, y, z))
			end
		end end end
	end
	local shadows, lamps = 0, 0
	for _, l in room:GetDescendants() do if l:IsA("Light") then lamps += 1; if l.Shadows then shadows += 1 end end end
	if shadows > 11 then table.insert(issues, ("LAMPS: %d cast shadows (11 is the limit)"):format(shadows)) end
	if spawnN < 8 then table.insert(issues, ("SPAWNS: %d spawn markers (8 wanted)"):format(spawnN)) end
	if #pads ~= #R.MODES + #R.UPPER then table.insert(issues, ("PADS: %d pads (%d wanted)"):format(#pads, #R.MODES + #R.UPPER)) end
	-- the regulars' ways (the owner, 17 Nov: "When they stand make sure they don't stand in their seats like clipped into
	-- it!"): a body (R.NPC_BODY, its feet R.NPC_LIFT over the floor) stood on every point they stop at (a seat's Stand,
	-- facing the way the seat does) and swept every R.NPC_STEP along every way they walk, the same ways HubNPCs walks
	-- them: seat to seat by the Stand, the Approach, the Aisles and the place's Door (straight along the front of a sofa
	-- when both seats share an aisle); a loop's or a rail's points in order. anything seen or solid in it is a problem
	local npcWays, npcBoxes = 0, 0
	do
		local CS = game:GetService("CollectionService")
		local BODY, LIFT, STEP = R.NPC_BODY, R.NPC_LIFT, R.NPC_STEP
		local places, pts = {}, {}
		for _, q in room.Scenery:GetChildren() do
			local who = q:GetAttribute("Who")
			if type(who) ~= "string" then continue end
			if CS:HasTag(q, "HubNPC") then places[who] = q
			elseif CS:HasTag(q, "NPCPoint") then pts[who] = pts[who] or {}; table.insert(pts[who], q) end
		end
		local things = {}
		for _, q in room:GetDescendants() do
			if not q:IsA("BasePart") or q.Transparency >= 0.95 or CS:HasTag(q, "HubNPC") or CS:HasTag(q, "NPCPoint") then continue end
			local cf, h = q.CFrame, q.Size / 2
			local r, u, l = cf.RightVector, cf.UpVector, cf.LookVector
			local e = Vector3.new(math.abs(r.X) * h.X + math.abs(u.X) * h.Y + math.abs(l.X) * h.Z, math.abs(r.Y) * h.X + math.abs(u.Y) * h.Y + math.abs(l.Y) * h.Z, math.abs(r.Z) * h.X + math.abs(u.Z) * h.Y + math.abs(l.Z) * h.Z)
			table.insert(things, { p = q, lo = cf.Position - e, hi = cf.Position + e, round = q:IsA("Part") and q.Shape == Enum.PartType.Cylinder and math.abs(r.Y) > 0.99 })
		end
		local rp3 = RaycastParams.new(); rp3.FilterType = Enum.RaycastFilterType.Include; rp3.FilterDescendantsInstances = { room }; rp3.RespectCanCollide = false
		local half = BODY / 2
		local reach = Vector3.new(half.X + half.Z, half.Y, half.X + half.Z)
		local function body(at, dir, what)
			npcBoxes += 1
			local reach = Vector3.new(half.X + half.Z, half.Y, half.X + half.Z)
			local hit = workspace:Raycast(at + Vector3.new(0, 4, 0), Vector3.new(0, -9, 0), rp3)
			if not hit then
				table.insert(issues, ("REGULAR: no floor under %s at (%.1f, %.1f, %.1f)"):format(what, at.X - O.X, at.Y - O.Y, at.Z - O.Z))
				return false
			end
			local c = Vector3.new(at.X, hit.Position.Y + LIFT + half.Y, at.Z)
			local flat = Vector3.new(dir.X, 0, dir.Z)
			local cf = CFrame.lookAt(c, c + (if flat.Magnitude > 1e-3 then flat else Vector3.new(0, 0, -1)))
			local lo, hi = c - reach, c + reach
			for _, k in things do
				if k.hi.X < lo.X or k.lo.X > hi.X or k.hi.Y < lo.Y or k.lo.Y > hi.Y or k.hi.Z < lo.Z or k.lo.Z > hi.Z then continue end
				local into = obb(cf, half, k.p.CFrame, k.p.Size / 2)
				if into and k.round then -- (a drum on its flat: how far its axis is from the body decides)
					local q = k.p.CFrame:PointToObjectSpace(c)
					into = math.sqrt(q.Y * q.Y + q.Z * q.Z) < k.p.Size.Y / 2 + math.min(half.X, half.Z)
				end
				if into then
					table.insert(issues, ("REGULAR: %s goes through %s near (%.1f, %.1f, %.1f)"):format(what, k.p.Name, c.X - O.X, hit.Position.Y - O.Y, c.Z - O.Z))
					return false
				end
			end
			return true
		end
		local function way(list, what)
			npcWays += 1
			for k = 1, #list - 1 do
				local a, b = list[k], list[k + 1]
				local d = Vector3.new(b.X - a.X, 0, b.Z - a.Z)
				local steps = math.max(1, math.ceil(d.Magnitude / STEP))
				for i = (if k == 1 then 0 else 1), steps do
					if not body(a + (b - a) * (i / steps), d, what) then return end
				end
			end
		end
		local function standOf(p) local s = p:GetAttribute("Stand"); return if typeof(s) == "Vector3" then s else p.Position end
		for who, list in pts do
			table.sort(list, function(a, b) return (a:GetAttribute("Index") or 0) < (b:GetAttribute("Index") or 0) end)
			local place = places[who]
			local mode = place and place:GetAttribute("Moves")
			local w = place and place:GetAttribute("Width")
			half = Vector3.new((if type(w) == "number" then w else BODY.X) / 2, BODY.Y / 2, BODY.Z / 2)
			for _, p in list do
				if p:GetAttribute("Kind") ~= "via" then body(standOf(p), p.CFrame.LookVector, ("%s standing at their point %d"):format(who, p:GetAttribute("Index") or 0)) end
			end
			if mode == "seats" then
				for _, a in list do
					for _, b in list do
						if a == b then continue end
						local w = { standOf(a), a:GetAttribute("Approach") }
						if a:GetAttribute("Aisle") ~= b:GetAttribute("Aisle") then
							table.insert(w, a:GetAttribute("Aisle")); table.insert(w, place:GetAttribute("Door")); table.insert(w, b:GetAttribute("Aisle"))
						end
						table.insert(w, b:GetAttribute("Approach")); table.insert(w, standOf(b))
						local ok = true
						for i = 1, #w do if typeof(w[i]) ~= "Vector3" then ok = false end end
						if ok then way(w, ("%s's walk from seat %d to seat %d"):format(who, a:GetAttribute("Index"), b:GetAttribute("Index")))
						else table.insert(issues, ("REGULAR: %s's seats %d and %d have no full way between them"):format(who, a:GetAttribute("Index"), b:GetAttribute("Index"))) end
					end
				end
			elseif mode == "loop" or mode == "pingpong" then
				local w = {}
				for _, p in list do table.insert(w, p.Position) end
				if mode == "loop" then table.insert(w, list[1].Position) end
				way(w, ("%s's %s"):format(who, if mode == "loop" then "loop" else "walk along the rail"))
			end
		end
	end
	local problems = #issues
	for _, line in sights do table.insert(issues, line) end
	local msg = ("%s (%s): %d keep-clear zones, %d parts looked at, %d problems, leaks %d, sight lines %d, hidden %d, props %d, overlaps %d, lamps %d (%d with shadows), pads %d, walked to %d, regulars' ways %d (%d body boxes)"):format(
		R.ROOM, if W.live then "live" else "staging copy", #zones, looked, problems + #sights, leaks, lines, shut, #props, overlaps, lamps, shadows, #pads, routes, npcWays, npcBoxes)
	if W.live then PB:SetAttribute("LastOverlapCheck", msg) end
	if #issues > 40 then local n = #issues; issues = table.move(issues, 1, 40, 1, {}); table.insert(issues, ("... and %d more"):format(n - 40)) end
	return msg .. (if #issues > 0 then "\n" .. table.concat(issues, "\n") else "")
end

-- camera spots for pictures: name = { eye, looking at }, each { bearing, x, y, d }. R.view(name) gives world points
R.VIEWS = {
	-- (18 Nov: spawn = from the spawn rug out through the arches; lounge_spawn = the lounge from the rug; upstairs = the way
	-- up from the rug; jump = a jump pad and its board from the round room)
	spawn = { { LOUNGE, 0, 5.9, 40.4 }, { 0, 0, 8, 30 } }, lounge_spawn = { { LOUNGE, 0, 6.4, 33.2 }, { LOUNGE, 0, 3.6, 62 } }, upstairs = { { LOUNGE, 0, 5.9, 40.4 }, { 0, 0, 17, 27 } },
	lounge_wide = { { LOUNGE, -25.5, 10, 30 }, { LOUNGE, 10, 2.5, 58 } }, lounge_wide2 = { { LOUNGE, 25.5, 10, 30 }, { LOUNGE, -10, 2.5, 58 } },
	jump = { { 180, 4, 5.9, 18 }, { 3 * STEP, 0, 12, 24 } }, platform = { { 0, 0, 5.9, -9 }, { 0, 0, 7, 50 } },
	centre = { { 180, 0, 8, 23 }, { 0, 0, 11, 20 } }, dome = { { 180, 0, 3.5, 15 }, { 0, 0, 30, 3 } },
	balcony = { { 180, 0, 19.2, 25 }, { 0, 0, 9, 32 } }, lifts = { { 334.3, 0, 5.2, 34.5 }, { 22, 0, 8, 52 } }, lift = { { 0, 0, 6, 33 }, { 0, 0, 9, 56 } },
	back = { { 0, 0, 5.5, 41 }, { 180, 0, 9, 30 } }, lounge_door = { { 0, 0, 5.9, 3 }, { 180, 0, 5, 46 + LS } }, lounge = { { 180, 6.5, 5.6, 39.5 + LS }, { 180, -3, 4.2, 52 + LS } },
	gym_door = { { GYM + 180, 0, 5.9, 4 }, { GYM, 0, 6.5, 70 } }, gym = { { GYM, -1, 5.9, 39.5 }, { GYM, 3, 3.5, 66 } },
	gym_back = { { GYM, 12, 9, 70 }, { GYM, -6, 3, 46 } },
	training_door = { { ARM + 180, 0, 5.9, 4 }, { ARM, 0, 5.5, 60 } }, armory = { { ARM, 8.5, 6, 39.5 }, { ARM, -7, 5.5, 58 } },
	holo = { { 180, 0, 5.94, 9 }, { 0, 0, 6, 0 } }, holo_across = { { 90, 0, 5.4, 24 }, { 0, 0, 6, 0 } }, showroom = { { LOUNGE, 8, 6.2, 40 }, { LOUNGE, 26, 4.6, 50 } },
	plinth = { { 9 * STEP, -5, 5.6, 15.5 }, { 9 * STEP, 0, 4.8, 25 } }, arches = { { 0, 0, 7, 8 }, { 180, 0, 6, 32 } },
	-- (18 Nov, the plaza: the same spots for both builds, under the old lounge's ceiling, for the before / after sheet.
	-- pz_spawn = the first look from the spawn; pz_back = turned round; pz_wide = the courtyard from its north-east
	-- corner; pz_join = the round room's south faces from the courtyard; pz_facade = the west facade and its arcade;
	-- pz_up = the facades and the ceiling from the rug)
	pz_spawn = { { LOUNGE, 0, 5.9, 44 }, { 0, 0, 8, 30 } }, pz_back = { { LOUNGE, 0, 6.4, 37 }, { LOUNGE, 0, 4, 76 } },
	pz_wide = { { LOUNGE, -17, 13, 33 }, { LOUNGE, 9, 3, 66 } }, pz_join = { { LOUNGE, 7, 8, 62 }, { LOUNGE, -2, 11, 30 } },
	pz_facade = { { LOUNGE, -13, 6, 46 }, { LOUNGE, 19, 12, 56 } }, pz_up = { { LOUNGE, 2, 5.6, 50 }, { LOUNGE, -8, 24, 66 } },
}
-- every view as "name x y z x y z" lines, for the screen capture tool
function R.views()
	local out = {}
	for name in R.VIEWS do
		local a, b = R.view(name)
		if a then table.insert(out, ("%s %.1f %.1f %.1f %.1f %.1f %.1f"):format(name, a.X, a.Y, a.Z, b.X, b.Y, b.Z)) end
	end
	table.sort(out)
	return table.concat(out, "\n")
end
function R.view(name)
	local W = R.places()
	local v = R.VIEWS[name]
	if not W or not v then return nil end
	local Wp = R.warpOf(W.room)
	local a = R.warpPoint(Wp, W.O, R.frame(W.O, v[1][1]) * Vector3.new(v[1][2], v[1][3], -v[1][4]))
	local b = R.warpPoint(Wp, W.O, R.frame(W.O, v[2][1]) * Vector3.new(v[2][2], v[2][3], -v[2][4]))
	return a, b
end

return R
