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
H.TITLE = "HOLDOUT"
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
		liedown = 84272735523225, lying = 112468296499220, shove = 126115043504756,
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
	minPlayers = 2, lobby = 20, hide = 20, hunt = 240, fightBack = 120, results = 6,
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
	{
		id = "school", source = "JankfieldHighV2A", title = "JANKFIELD HIGH", strip = { "ZM" },
		gunman = { 0, 0, 72, 0, -1 }, -- (the main entrance, facing in)
		hiders = {
			{ -82, -16, 6 }, { 10, -16, -42 }, { 10, -16, -82 }, { 58, -16, -62 }, { -28, -16, -66 }, { 4, -16, -62 },
			{ 36, -16, -62 }, { 102, -16, -62 }, { -88, 0, -65 }, { -88, 0, 16 }, { -76, 0, 72 }, { -48, 0, -72 },
			{ -16, 0, -72 }, { 16, 0, -72 }, { 48, 0, 72 }, { 52, 0, -68 }, { 83, 0, -68 }, { 121, 0, -68 },
			{ 112, 0, 12 }, { 112, 0, 76 }, { -88, 16, -61 }, { -76, 16, 72 }, { -48, 16, -72 }, { -16, 16, -72 },
			{ 16, 16, -72 }, { 0, 16, 86 }, { 48, 16, 72 }, { 52, 16, -68 }, { 102, 16, -68 }, { 112, 16, 76 },
		},
		-- the search spots for FIGHT BACK: x, y (the piece's top-ish), z, what's in it ("" = nothing)
		search = {
			{ -118, 3.6, 38, "knife" }, { -118, 3.6, 66, "" }, { -118, 3.6, 89, "pan" }, { -96.5, 3.2, 63, "" },
			{ 62.2, 19.4, 64, "knife" }, { 66, 22, 82, "" }, { 158.4, 6.5, 64, "club" }, { 146, 6.5, 94.4, "bat" },
			{ 72.5, 6.5, -87.2, "" }, { 110.5, 6.5, -87.2, "club" }, { 25.5, -12.8, -73.8, "bat" }, { -17.5, -8, -74.3, "" },
			{ -40, -12.4, -72, "" }, { 6, -12.4, -66, "pan" }, { -49.5, 2.6, -66, "" }, { 14.5, 18.6, -66, "" },
			{ -54.7, 6.5, 20, "" }, { 62.7, 6.5, -28, "" }, { 8, 22.5, -46.7, "" }, { -108, 23, 59, "" },
			{ 29.8, 20.5, 58, "" }, { -30.2, 20.5, 74, "knife" }, { 33.4, 6, 88, "" }, { -57.6, 6, -62, "" },
		},
	},	-- (stage 4: maps we already have, the spots picked from their own layouts by tools/roblox/hunt_spots.py)
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

return H
