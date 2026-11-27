--!strict
-- HOLDOUT, the one-gunman hunt mode (26 Nov 2026; roblox/docs/HUNT.md): every number the mode uses, in one place. The
-- owner: "The new gamemode will start in a new lobby ... Youll be in a house, with a backyard ... They can run around
-- interact with stuff, punch push super push. Push is funny, if you lay down look up and push you'll send people flying."
-- Shared by the server (Hunt, HuntMoves, HuntProps, HuntTravel) and the client (HuntMoves.client, HuntClient). Pure data.
local H = {}

-- ------------------------------------------------------------------ where it lives
-- nil: the house and the rounds are in this place (workspace.Map.HuntHouse). once the owner makes HOLDOUT its own place
-- in this experience, its place id goes here and HuntTravel teleports instead (DataStores, passes and products belong to
-- the experience, so everything carries over)
H.PLACE_ID = nil :: number?
H.HUB_PLACE_ID = 96891323589901 -- (the start place, for the way back once it's split)
H.HOUSE = "HuntHouse" -- (workspace.Map.<HOUSE>: the lobby, built by studio-tools/HuntBuild)
H.TITLE = "HOUSE HUNT" -- (the owner's pick, 27 Nov: the mode's on-screen name, one constant; internal ids stay "hunt")
H.HOUSE_TITLE = "THE HOUSE"

-- ------------------------------------------------------------------ the moves (studs, seconds, studs/s)
-- the server judges reach and cone from its own copy of the bodies; a knock goes through Fight.knock. damage only lands
-- on the gunman, in a round (the house hurts nobody)
H.MOVES = {
	jab = { dmg = 6, reach = 6.5, cone = 50, cd = 0.45, kb = 14, up = 6 },
	hay = { dmg = 18, wind = 0.5, maxWind = 2.5, reach = 7.0, cone = 50, cd = 0.9, kb = 35, up = 14 },
	push = { reach = 7.0, cone = 55, cd = 1.2, kb = 45, up = 12 },
	super = { hold = 0.8, reach = 8.0, cone = 55, cd = 8.0, kb = 105, up = 40 },
	-- lying on your back: the body sinks this far (Body.sink), moves at this share of a run; a push from it goes along
	-- your whole look (the up part uncapped) and x launch
	lie = { sink = 1.7, speed = 0.2, launch = 1.4, getUp = 0.5 },
	-- the server's slack on reach (a moving body, lag)
	slack = 2.5,
	-- a knock on the ball (the driveway's basketball): x this
	ball = 0.9,
}

-- ------------------------------------------------------------------ the hider's animations (mocap: the owner's Mixamo
-- clips in the vault, retargeted by tools/blender/mixamo_r15.py [--r6]; uploaded 26 Nov 2026). HuntAnims plays them.
-- idle and run replace the avatar's own (its Animate script's ids) while you're in the mode; walk, crouch and the shove's
-- final take wait on new Mixamo downloads (the avatar's own walk and CrouchPoses' crouch until then)
H.ANIMS = {
	R15 = {
		idle = 79402510903596, run = 139539319042211, haymaker = 132438005835323, jab = 123332468233314,
		liedown = 139959671656219, lying = 132632727339007, shove = 73591106098734,
	},
	R6 = {
		idle = 131309729157109, run = 94895902829568, haymaker = 109065100096930, jab = 106574595043554,
		liedown = 108959127320577, lying = 72487779516021, shove = 126115043504756, -- (R6: lying with the hips dropped: an R6 body keeps its leg height)
	},
	-- the haymaker's wind-up ends here (s): the clip waits at this pose while the punch is held, the rest plays on release
	windAt = 0.53,
}

-- ------------------------------------------------------------------ the trampoline and the beds
-- landing on a part with the attribute Trampoline (its power, 1 = the trampoline): you go back up at least base x power,
-- or your fall speed x keep if that's more; Space held as you land adds boost (a timed bounce), up to max
H.BOUNCE = { base = 42, keep = 0.92, boost = 14, max = 96, gap = 0.18 }

-- ------------------------------------------------------------------ the house's props
H.PROPS = {
	doorOpen = 0.32, doorReach = 7.5, doorShut = 3.0, -- (a door swings open as you walk into it, shuts this long after)
	tap = 4.0, -- (a tap runs this long)
	fridge = 4.0,
	rollup = 1.6, -- (the garage door's travel)
	ballHome = 12.0, -- (the ball goes home this long after it leaves the lot)
}

-- the store tables' prompts (ShopClient: a prompt's ShopOpen opens the shop on that tab or offer). VIP, coins, cases:
-- the store's own items only (THE ROBUX RULE, roblox/docs/MONEY.md)
H.TABLES = {
	vip = { label = "VIP", open = "tab:bundles" }, -- (the VIP pass is the wide tile at the top of BUNDLES)
	coins = { label = "COINS", open = "tab:coins" },
	cases = { label = "CASES", open = "tab:containers" },
}

-- ------------------------------------------------------------------ the round (stage 2)
H.ROUND = {
	minPlayers = 2, lobby = 20, hide = 16, hunt = 240, fightBack = 120, results = 6, -- (hide = the gunman's intro, 27 Nov)
	gunmanHp = 250, hiderHp = 100,
	-- where a round's copy of its map goes: SITE + (GAP * k, 0, 0) for game k = 0, 1, 2
	site = Vector3.new(0, 300, -96000), gap = 7000,
	-- the gunman waits out the hide in a sealed dark room this far over the copy's pivot
	pen = Vector3.new(0, 140, 0),
}

-- the gunman's gun: one of the main game's real guns at random (the owner: "a random gun from ar to sniper to shotgun")
H.GUNS = { "ar", "smg", "shotgun", "sniper", "burst", "lmg", "dmr", "lever", "autoshot" }

-- his passives: two of these at random each round. Names are labels (no-flavour-text); `say` is the plain line under it
H.PASSIVES = {
	{ id = "pulse", name = "PULSE", say = "hiders near him show through walls for a moment", every = 25, range = 60, show = 1.5 },
	{ id = "tracks", name = "TRACKS", say = "running hiders leave footprints he can see", fresh = 3.0 },
	{ id = "thick", name = "THICK SKIN", say = "+100 health", hp = 100 },
	{ id = "firm", name = "FIRM STANCE", say = "shoves move him half as far", knock = 0.5 },
}

-- the maps a round plays on: a map already in the place (workspace.Map.<source>), copied for the round, plus where
-- people stand in it (local to the map's pivot). strip = folders taken out of the copy (the zombies' shutters)
H.MAPS = {
	-- (27 Nov, main: no schools, churches, malls or offices of desks, nothing that reads as a real-world attack site: homes,
	-- mansions, backrooms, parks, warehouses. Jankfield High is out of this list for good.) the maps below: spots picked by
	-- tools/roblox/hunt_spots.py from each map's own layout (the house: --y=-2,13.5, its floors only); the house's
	-- weapons placed by hand where they belong (the kitchen's knives and pan, the garage's club, the toy chest's bat)
	{
		id = "house", source = "HuntHouse", title = "THE HOUSE", strip = { "Hunt" }, -- (the copy: no doors, exit, tables)
		outside = { 0, -1.5, 70, 0, -1 }, -- (the gunman's intro ends here: the front walk, facing the front door)
		gunman = { 3, 0, -21, 0, -1 },
		hiders = {
			{ 93, -1.5, -145 }, { -43, -1.5, 69 }, { -77, -1.5, -149 }, { 55, 13, -19 }, { -55, 13, -37 }, { 99, -1, 37 },
			{ -7, 0, 1 }, { 41, 0, 35 }, { 105, -1.5, -21 }, { -77, -1.5, -75 }, { -77, -1.5, 27 }, { -23, 13, 37 },
			{ -19, -1, -49 }, { 17, 13, -53 }, { -51, 0, -7 }, { 21, 13, 9 }, { 27, 0, -29 }, { 67, -1, 9 },
			{ -29, 13, -1 }, { -1, 0, 35 }, { -3, 13, -27 }, { 51, 13, 17 }, { 47, 13, -49 }, { -53, 13, 35 },
		},
		search = {
			{ 55.5, 5.6, -32, "knife" }, { 55.5, 5.6, -20, "pan" }, { 80.5, 2.0, -8.2, "club" }, { 55.5, 16.2, -36, "bat" },
			{ 34, 5.6, -18, "knife" }, { 100, 2.4, 0, "bat" }, { 73, 1.5, -147, "" }, { 101, 1.5, -127, "" },
			{ -19, 16, 19, "" }, { -51, 3, 11, "" }, { -19, 16, -15, "" }, { 7, 16, 19, "" },
			{ -21, 16, -33, "" }, { 47, 16, -33, "" }, { 53, 16, 1, "" }, { 31, 16, -49, "" },
		},
	},
	{
		id = "backrooms", source = "Backrooms", title = "THE BACKROOMS",
		gunman = { 1, -0.2, 1, 0, -1 },
		hiders = {
			{ -237, 0, -237 }, { 233, 0, 233 }, { -237, -0.2, 235 }, { 233, 0, -235 }, { -101, -0.2, -1 }, { 137, -0.2, -3 },
			{ -3, 0, -235 }, { 3, 0, 211 }, { -223, -13.5, -79 }, { -235, -13.5, 91 }, { 127, 0, -141 }, { 235, 0, 93 },
			{ 105, -0.2, 125 }, { -103, 0, 133 }, { -103, 0, -151 }, { 235, 0, -79 }, { 9, 0, -123 }, { 125, 0, 237 },
			{ -7, -0.2, 99 }, { -211, -0.2, 7 }, { -137, 0, 235 }, { 127, 0, -237 }, { -111, -0.2, -237 }, { 225, -0.2, 5 },
		},
		search = {
			{ 175, 2.9, 173, "knife" }, { -145, 3, 65, "pan" }, { 221, 3, -157, "club" }, { -191, 3, -173, "bat" },
			{ -147, -10.5, -79, "knife" }, { 103, 2.9, -69, "bat" }, { -69, 2.9, 211, "" }, { 165, 3, 77, "" },
			{ 41, 3, 151, "" }, { 43, 3, -185, "" }, { -163, -10.5, 163, "" }, { -55, 3, -195, "" },
			{ -65, 3, -99, "" }, { -41, 3, 153, "" }, { 63, 3, 231, "" }, { 235, 3, 159, "" },
		},
	},
	{
		id = "suburb", source = "SuburbV2", title = "SUBURB",
		gunman = { 0, 0, 2, 0, -1 },
		hiders = {
			{ -148, 0, -104 }, { 148, 0, 104 }, { -74, 0, 104 }, { 82, 0, -104 }, { -38, 0, -36 }, { 30, 0, 56 },
			{ -164, 0, 44 }, { 164, 0, -46 }, { 8, 14, -100 }, { 66, 0, -18 }, { -64, 3.2, 30 }, { 80, 0, 104 },
			{ -80, 0, -104 }, { -146, 0, 104 }, { 80, 12, 48 }, { 162, 0, 44 }, { 144, 0, -104 }, { -164, 0, -46 },
			{ -6, 0, 104 }, { -82, 12, -48 }, { 36, 0, -66 }, { -28, 0, -102 }, { -24, 0, 54 }, { 80, 12, -48 },
		},
		search = {
			{ 36, 3, 100, "knife" }, { -8, 3, -64, "pan" }, { -40, 3, 100, "club" }, { 42, 3, -102, "bat" },
			{ 14, 3, -40, "knife" }, { -66, 3, -20, "bat" }, { -80, 3, 58, "" }, { -36, 3, -72, "" },
			{ 4, 3, 68, "" }, { 42, 3, -38, "" }, { 56, 3, 48, "" }, { -42, 3, 38, "" },
			{ -58, 6.2, -48, "" }, { -14, 3, -42, "" }, { 14, 3, 40, "" }, { 14, 3, -62, "" },
		},
	},
}

-- ------------------------------------------------------------------ stage 3: the hiders' points, traps and weapons
-- points: a hider starts with `start`, earns `alive` every `every` s alive in the hunt, `punch` / `push` for each one that
-- lands on the gunman, `trap` when one of their traps gets him. two traps carried at once
H.POINTS = { start = 10, every = 3, alive = 1, punch = 5, push = 8, trap = 20, carry = 2 }
H.TRAPS = {
	{ id = "beartrap", name = "BEAR TRAP", cost = 30, say = "set on the floor: holds him 3 s, 20 damage", hold = 3, dmg = 20, arm = 1.0, reach = 2.8 },
	{ id = "spray", name = "PEPPER SPRAY", cost = 25, say = "3 puffs: his view goes white for 3 s", uses = 3, range = 12, cone = 35, blind = 3 },
	{ id = "taser", name = "TASER", cost = 40, say = "one shot: he can't move or shoot for 2 s", range = 18, cone = 12, stun = 2 },
	{ id = "smoke", name = "SMOKE BOMB", cost = 20, say = "a cloud that hides everyone in it for 8 s", radius = 14, time = 8 },
	{ id = "marbles", name = "MARBLES", cost = 15, say = "a spill he slips on, 10 s", radius = 7, time = 10 },
	{ id = "decoy", name = "DECOY", cost = 20, say = "footsteps that walk away from it, 10 s", time = 10 },
}
-- the FIGHT BACK weapons (a search spot's find): held in your right hand, swung with the punch (the server judges it)
H.WEAPONS = {
	knife = { name = "KITCHEN KNIFE", dmg = 35, reach = 6.5, cone = 45, cd = 0.45, kb = 10, up = 4 },
	pan = { name = "FRYING PAN", dmg = 40, reach = 7.0, cone = 50, cd = 0.7, kb = 40, up = 14 },
	club = { name = "GOLF CLUB", dmg = 45, reach = 8.5, cone = 45, cd = 0.8, kb = 25, up = 10 },
	bat = { name = "BASEBALL BAT", dmg = 50, reach = 7.5, cone = 50, cd = 0.9, kb = 30, up = 10 },
	search = 1.5, -- (s held to search a spot)
}

-- ------------------------------------------------------------------ the gunman's intro (owner, 27 Nov; HUNT.md section 11)
-- a cinematic on the gunman's screen only, as long as the hide (ROUND.hide): his room, the build, the snap, outside, the
-- turn. Two rooms on the same beats (the owner: "we can try both"): A their bedroom (a PC screen's light), B an attic
-- (an old TV's static). set = "A", "B" or "both" (each round the other one). Each map's `outside` = where he comes in
-- (x, y, z, facing x, z; local to the map); a map without one lets him out at its `gunman` spot as before
H.INTRO = {
	on = true,
	set = "both",
	kit = "JankfireHuntIntro", -- (ReplicatedStorage: hiA_room, hiA_props, hiB_room, hiB_props, hi_mask; HuntBuild.importIntro)
	outsideLead = 4.6, -- (s before the hunt: he stands at the map's outside spot for the last two beats, held still)
	-- mocap (the vault's Mixamo clips, mixamo_r15.py; R15 and R6). calm = ANIMS idle
	anims = {
		R15 = { crazy = 136466865725956, nod = 130020646585198, shake = 116523207869437, snap = 84828717533144, look = 108845709130342 },
		R6 = { crazy = 86292029421586, nod = 78893331405051, shake = 137563690783496, snap = 130441780593124, look = 95541089023402 },
	},
	static = { 72310839769760, 86008837872701, 122572333792473, 98994588240705 }, -- (B's screen: soft grey noise, nothing readable)
	-- recordings only, no voices (Sfx names; a missing one stays silent)
	sounds = { drone = "intro_drone", buzz = "zm_flicker", heart = "intro_heart", hit = "boom", air = "intro_air", hiss = "intro_hiss" },
}

return H
