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
-- (owner, 27 Nov: "Push is a light push that ragdolls the enemy or other survivors, super push is the same but like the
-- handslapper and punch ragdolls and stuns you can't untagdoll for a few seconds ... Cooldown shouldn't be crazy long but
-- also not short enough where you can chain all three") each landed move ragdolls its target for `rag` s (HuntRagdoll);
-- the get-up button works after `min` s. A punch (jab or haymaker) that lands costs `cd`, a miss `whiff`. After any
-- move every move waits `lock` s; someone just up can't be downed again for RAGDOLL.immune s
H.MOVES = {
	jab = { dmg = 6, reach = 6.5, cone = 50, cd = 0.45, kb = 14, up = 6 },
	hay = { dmg = 18, wind = 0.5, maxWind = 2.5, reach = 7.0, cone = 50, cd = 0.9, kb = 35, up = 14 },
	punch = { cd = 6.0, whiff = 1.2, rag = 3.0, min = 2.5 },
	push = { reach = 7.0, cone = 55, cd = 3.0, kb = 45, up = 12, rag = 1.0, min = 0.5 },
	super = { hold = 0.8, reach = 8.0, cone = 55, cd = 10.0, kb = 105, up = 40, rag = 2.0, min = 1.0 },
	lock = 1.0,
	-- lying on your back: the body sinks this far (Body.sink), moves at this share of a run; a push from it goes along
	-- your whole look (the up part uncapped) and x launch
	lie = { sink = 1.7, speed = 0.2, launch = 1.4, getUp = 0.5 },
	-- the server's slack on reach (a moving body, lag)
	slack = 2.5,
	-- a knock on the ball (the driveway's basketball): x this
	ball = 0.9,
}

-- the ragdoll (HuntRagdoll): immune s after getting up; the get-up (the vault's Mixamo Getting Up, mixamo_r15.py) plays
-- at riseSpeed and takes riseTime s, no moving till it's done
H.RAGDOLL = { immune = 2.0, riseTime = 1.5, riseSpeed = 1.8, getUp = { R15 = 139465552509277, R6 = 139224766499388 } }

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
	minPlayers = 2, lobby = 20, hide = 18, hunt = 240, fightBack = 120, results = 6, -- (hide = the gunman's intro: 18 s since the owner's look-round and slow push in, 27 Nov)
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
	{ id = "pulse", name = "PULSE", say = "survivors near him show through walls for a moment", every = 25, range = 60, show = 1.5 },
	{ id = "tracks", name = "TRACKS", say = "running survivors leave footprints he can see", fresh = 3.0 },
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
		-- the win films (27 Nov): his walk in from the front door, looking into the living room, toward the dining room, then
		-- on to the fireplace (eye height 5.6); the survivors' regroup in the hall (x, y, z, facing yaw degrees)
		outroWalk = { path = { { -4, 5.6, 37 }, { -5, 5.6, 29 }, { -10, 5.6, 24 }, { -18, 5.6, 25 } },  -- (owner: "walk forward more")
			looks = { { -30, 4.5, 33 }, { -36, 4.0, 13 }, { -46, 4.2, 32 }, { -52, 4.0, 16 } } },        -- (and slower looks round)
		outroGroup = { -2, 0, 14, 180 },
		tables = { 82, -1, 56, 180 }, -- (the item tables: on the driveway in front of the garage, facing the street)
		outroGroupWalk = { from = { -1, 0, 20 }, to = { -1, 0, 38.5 } }, -- (owner on v6: "walking out toward the door": up the hall to the front door)
		outroDoor = { -3.5, 3.5, 41, 0, 9.8 }, -- (the front doorway: x from, x to, z, floor, height: two leaves swing out as she nears it)
		-- the wreck along his walk (main, 27 Nov: "start the walk with destroyed place"): { piece, x, y, z, yaw, pitch, roll }
		-- in degrees (yaw first, then the tip). No blood, no bodies: things knocked over, a frame askew, a door off its hinge
		outroWreck = {
			{ "hiW_chair", -7, 1.15, 31, 30, 0, 90 }, { "hiW_lamp", -18, 1.2, 27, 70, 90, 0 }, { "hiW_armchair", -26, 1.6, 22, 200, -90, 0 },
			{ "hiW_cushion", -16, 0, 20, 30, 0, 0 }, { "hiW_cushion", -22, 0, 30, 110, 0, 8 }, { "hiW_cushion", -6, 0, 23, 200, 0, 0 },
			{ "hiW_paper", -9, 0.02, 27, 10, 0, 0 }, { "hiW_paper", -10.5, 0.02, 25, 55, 0, 0 }, { "hiW_paper", -6.5, 0.02, 29, 120, 0, 0 },
			{ "hiW_paper", -14, 0.02, 23, 80, 0, 0 }, { "hiW_paper", -19, 0.02, 25, 15, 0, 0 }, { "hiW_paper", -11, 0.02, 30, 160, 0, 0 },
			{ "hiW_frame", -36, 6.5, 39.8, 180, 0, 14 }, { "hiW_door", -10.6, 0, 35.5, 90, -10, 0 },
		},
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
H.POINTS = { start = 40, every = 3, alive = 1, punch = 5, push = 8, trap = 20, carry = 2 } -- (on screen: CASH, $)
H.TRAPS = {
	{ id = "beartrap", name = "BEAR TRAP", cost = 30, say = "set on the floor: holds him 3 s, 20 damage", hold = 3, dmg = 20, arm = 1.0, reach = 2.8 },
	{ id = "spray", name = "PEPPER SPRAY", cost = 25, say = "3 puffs: his view goes white for 3 s", uses = 3, range = 12, cone = 35, blind = 3 },
	{ id = "taser", name = "TASER", cost = 40, say = "one shot: he can't move or shoot for 2 s", range = 18, cone = 12, stun = 2, shop = false }, -- (the tables only)
	{ id = "smoke", name = "SMOKE BOMB", cost = 20, say = "a cloud that hides everyone in it for 8 s", radius = 14, time = 8 },
	{ id = "marbles", name = "MARBLES", cost = 15, say = "a spill he slips on, 10 s", radius = 7, time = 10 },
	{ id = "decoy", name = "DECOY", cost = 20, say = "footsteps that walk away from it, 10 s", time = 10 },
	-- the tables' own (not in the trap menu): shop = false
	{ id = "bandage", name = "BANDAGES", cost = 0, say = "+25 health a use", uses = 3, heal = 25, shop = false },
	{ id = "medkit", name = "MEDKIT", cost = 40, say = "back to full health over 2.5 s", heal = 100, time = 2.5, shop = false },
	{ id = "propgun", name = "PROP GUN", cost = 40, say = "aim at furniture: become it; moving fast, attacking or a hit breaks it", range = 30, breakSpeed = 9, shop = false },
}
-- the item tables (owner, 27 Nov): outside by the garage (a map's `tables` = { x, y, z, yaw }; else its first hider spot),
-- every survivor starts in front of them and takes ONE before the hunter is let out (the hide). Paid ones cost the
-- round's cash (POINTS.start buys exactly one); never coins, never Robux (THE ROBUX RULE). `weapon` = held in the hand
H.PICKS = {
	on = true,
	-- (main on v1545: big things you can tell apart, on short tables) the kit table at tableScale, two items a table at
	-- itemScale (an item's own scale / yaw on top), gap studs between tables
	tableScale = 0.7, itemScale = 1.6, gap = 2.6,
	items = {
		{ id = "bandage", name = "BANDAGES", price = 0 },
		{ id = "bat", name = "BASEBALL BAT", price = 0, weapon = "bat", scale = 0.75, yaw = 28 },
		{ id = "spray", name = "PEPPER SPRAY", price = 0 },
		{ id = "beartrap", name = "BEAR TRAP", price = 0 },
		{ id = "medkit", name = "MEDKIT", price = 40 },
		{ id = "taser", name = "TASER", price = 40 },
		{ id = "propgun", name = "PROP GUN", price = 40 },
	},
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
	set = "A", -- (owner, 27 Nov: the gunman's intro is room A, the bedroom; B the attic is the hiders' win film's)
	kit = "JankfireHuntIntro", -- (ReplicatedStorage: hiA_room, hiA_props, hiB_room, hiB_props; HuntBuild.importIntro)
	outsideLead = 8.8, -- (s before the hunt: he stands at the map's outside spot from the cut outside (beats.outside), held still)
	-- mocap (the vault's Mixamo clips, mixamo_r15.py; R15 and R6). calm = ANIMS idle
	anims = {
		-- (snap, owner 27 Nov: "I wanted to be staring straight up": the vault's Victory Idle 3, frames 15-29, the face
		-- 74 deg up and square to the hips; the old snap, a boxing head hit, peaked twisted 133 deg off them)
		-- (snapTop: the same face-up with the arms left unkeyed: v13's raised fist covered her face from above; the
		-- full one stays for outside, where her hands come down slowly)
		R15 = { crazy = 136466865725956, nod = 130020646585198, shake = 116523207869437, snap = 99336910488698, look = 108845709130342, snapTop = 123559013651150 },
		R6 = { crazy = 86292029421586, nod = 78893331405051, shake = 137563690783496, snap = 110975607602455, look = 95541089023402, snapTop = 131306120175253 },
	},
	static = { 72310839769760, 86008837872701, 122572333792473, 98994588240705 }, -- (B's screen: soft grey noise, nothing readable)
	-- recordings only, no voices. the owner's order (27 Nov): the room's hum (PC fans, a fridge), a heartbeat getting
	-- louder and faster, then peace: birds outside. a table is a Roblox library id (Pro Sound Effects / APM, under the
	-- EFFECTS volume) with its level and an optional slice; a string is the game's own library by name (Sfx)
	sounds = {
		-- (owner, 27 Nov: "it's missing that fridge hum and fans... static... birds... heartbeat": all were there, far too quiet:
		-- hum -33 dB, heartbeat peaks -15, birds -38 in the recording; all raised about 9-10 dB)
		hum = { id = 9125446564, vol = 0.5 },                          -- (PSE: Command Room Tone, Deep Air Conditioning Hum 2)
		heart = { id = 9043365842, vol = 0.6 },                        -- (APM, Epic Score: HEARTBEAT 02 96BPM; sped up, pitch held)
		birds = { id = 9116969466, vol = 10 },                         -- (PSE: Morning Birds 2, active chirping: a quiet recording)
		burst = { id = 9126097362, vol = 0.7, region = { 0.0, 0.7 } }, -- (Television Static: a burst on the cut outside; v11 -3 dB peak)
		hiss = { id = 9126097362, vol = 0.35, region = { 3.0, 8.0 } }, -- (PSE: Television Static, constant: room B's TV)
		buzz = "zm_flicker", hit = "boom",
	},
	-- the heartbeat's build: from `from` (s on the 16 s beats) to the snap it goes from rate[1] to rate[2] times its
	-- 96 BPM and from gain[1] to gain[2] of its level, while the hum ducks to `duck` of its own
	heart = { from = 2.6, rate = { 0.85, 1.85 }, gain = { 0.12, 1.0 }, duck = 0.35 },
	-- the owner's grade (27 Nov): muted colour ("not that grey!! I just wanted muted colors"; v1460's -0.82 was near
	-- grey) over the whole film, lifting with the bars as the lens goes into first person
	grade = { saturation = -0.45, contrast = -0.05, brightness = 0.01, tint = Color3.fromRGB(240, 243, 247), blur = 0.75 },
	-- the film's beats, s on an 18 s hide (k scales them to the real one). 27 Nov (owner): the room's opening trimmed,
	-- a look round outside as his hands come down, a hold behind him and a slow push into first person
	beats = { push = 1.6, profile = 2.8, build = 4.0, behind = 5.0, dutch = 5.9, face = 6.8, rush = 7.6, snap = 8.3,
		outside = 9.7, around = 10.8, swing = 13.4, hold = 15.4, enter = 16.2, bars = 16.4 }, -- (the top-down snap held 1.4 s; v15: the smooth push again)
	-- (owner on v11: "why is she still shakey or bouncy?": the breathing idle swayed her hips 19 cm and the 11 s look round
	-- was squeezed into 2.6 s, 4x its speed) the look round now plays a 3.7 s slice at `look` x, over the idle at `idle` x
	calm = { idle = 0.3, look = 1.35 },
	-- the look round's clip (upper body, R15 and R6: the vault's Mixamo Frisk Look Around, mixamo_r15.py --upper); the
	-- relaxed stand his hands come down into is ANIMS idle
	lookAround = { R15 = 104585605452755, R6 = 116576022390941 }, -- (07_frisk_look_around frames 21-131: right, then left)
	-- (main, 27 Nov: a dressed-up avatar's close-ups were a white jumble of frills) whatever he wears between the lens
	-- and the face (or hands) fades to `fade`, and anything within `near` studs of the lens
	lens = { fade = 0.92, near = 0.35 }, -- (owner on v11: "her hair is like invisible or clear?": only what the lens is inside fades)
	-- the hit-stop on the snap: `at` s after it starts, his body holds for `len` s while the lens kicks
	hitstop = { at = 0.17, len = 0.35 }, -- (as the face lands straight up after the whip: a held beat)
}

-- the round's win films (the owner, 27 Nov: "it was just a game you were playing"; HuntOutro.client): everyone in the
-- round sees the winners' film (len s), then the results card. Beats on an 11 s film: the house until the glitch, the
-- static, the pull back out of the screen, the reveal. Stand-in mocap from the vault until the Mixamo list lands
-- (MIXAMO-CLIPS-NEEDED: Sitting, Typing, Sitting Clap, High Five): seated breathing, seated arm stretch, upper-body
-- clapping / cheering / fist pump (mixamo_r15.py --upper). sitDrop: how far the seated clip drops the hips below the root
H.OUTRO = {
	on = true,
	len = 13, -- (owner, 27 Nov: a longer walk, slower looks)
	beats = { glitch = 5.8, pull = 6.3, reveal = 8.9 }, -- (main on v8: the pull out ran long in the dark: 2.6 s now)
	-- (main on v8: the pull out read near black on a phone) a soft fill rides with the lens from the pull, down to `reveal`
	fill = { brightness = 0.7, range = 14, reveal = 0.2 },
	-- the survivors' walk through her eyes (owner, 27 Nov: "Hiders winning can it be first person like how the hunters
	-- is?"): { s, yaw (deg, + = left), pitch (deg) } keys on her view: nervous glances, a pause, one look back over her
	-- shoulder at the friends trailing (about 1 s), then forward again
	-- (owner on v6: "the turns should be smoother!!": fewer, longer turns, smootherstep, the door straight ahead at the end)
	hiderLooks = { { 0, 0, -3 }, { 0.9, 0, -3 }, { 2.1, -150, -6 }, { 2.7, -150, -6 }, { 3.9, 0, -3 }, { 4.3, 12, -2 },
		{ 4.8, 0, -1 }, { 5.6, 0, 0 } },
	doorAt = 4.5, -- (s: the front door swings open, daylight spills in)
	hitstop = 0.2,
	sitDrop = { R15 = 1.2, R6 = 1.4 }, sitBack = 0.2, -- (then each sitter's hips are fitted onto the seat: HuntOutro)
	walk = { R15 = 507777826, R6 = 180426354 }, walkSpeed = 0.55, -- (Roblox's own walks, slowed: the survivors' walk)
	stretchSpeed = 0.75, -- (owner: "make them stand up slower it's too snappy")
	-- the survivors' walk (owner on v4: "one should lead and the other should lag behind it shouldn't be synchronized!
	-- Also she doesn't look scared at all!!"): she leads at `pace` studs/s (uneven by `uneven`), hunched with her arms in
	-- (the vault's Hit Stomach held, over Roblox's walk slowed) and glancing round (the look round on her head alone); the
	-- rest trail `back` studs behind and `side` across, each on their own walk speed and step phase, one stopping for a
	-- look back (`pauseAt` s, for `pauseLen`) then hurrying (`hurry` x) to catch up
	scared = { hunch = { R15 = 119535704799687, R6 = 105073434259680 }, glance = { R15 = 119056755652281, R6 = 115269372937672 },
		hunchWeight = 0.85, walkSpeed = 0.45, pace = 3.0, uneven = 0.12 }, -- (to the door by the static)
	group = {
		{ side = 0, back = 0, speed = 0.4, phase = 0 },
		{ side = -1.4, back = 2.8, speed = 0.5, phase = 0.37 }, -- (v6, first person: the nearest filled the look back)
		{ side = 1.8, back = 4.6, speed = 0.47, phase = 0.71, pauseAt = 1.7, pauseLen = 0.9, hurry = 1.5 },
		{ side = -0.5, back = 6.2, speed = 0.53, phase = 0.18 },
	},
	anims = {
		R15 = { sit = 123982609501233, stretch = 124144468077269, clap = 119842197482812, cheer = 99464849720944, pump = 82176434072280 },
		R6 = { sit = 91069648707561, stretch = 86402846376882, clap = 72835829513855, cheer = 134314727808662, pump = 114524043495459 },
	},
	-- recordings only, no voices (Pro Sound Effects); claps are single hand claps, each at one friend (never a crowd)
	sounds = {
		house = { id = 9116969466, vol = 6 },                          -- (Morning Birds 2: outside, through the walls; v5: -48 dB, silent)
		houseTone = { id = 9125446564, vol = 0.3 },                    -- (the house's own quiet room tone under it)
		heart = { id = 9043365842, vol = 0.45 },                       -- (the survivors' walk: the intro's heartbeat, under it)
		burst = { id = 9126097362, vol = 1.1, region = { 0.0, 0.7 } },  -- (Television Static: the switch-on burst; v5 peaked -17)
		hum = { id = 9125446564, vol = 0.5 },                          -- (room A: the PC's fans; the intro's hum)
		hiss = { id = 9126097362, vol = 0.4, region = { 3.0, 8.0 } },  -- (room B: the TV's static; v3: -44 dB)
		keys = { id = 9113142993, vol = 1.0 },                         -- (Apple Keyboard 28: keys)
		-- (v4 recording: the pads and claps together peaked -0.1 dB, all halved)
		pad = { id = 9119719128, vol = 0.5 },                          -- (Switches: buttons on a video controller)
		creak = { id = 9116257140, vol = 0.6 },                        -- (Leather Sofa 4: body movement)
		claps = { { id = 9114763105, vol = 0.25 }, { id = 9114762817, vol = 0.25 }, { id = 9114763106, vol = 0.25 }, { id = 9114762823, vol = 0.25 } },
	},
}

-- the hiders' intro (owner, 27 Nov: "if you get survivor you get a small cinematic of your character walking scared in
-- the map?.. and then it says survive!! You can skip it!! It'll be short regardless"; HuntHiderIntro.client): len s on
-- each hider's own screen as the round starts, added to the hide (HuntRound) so it costs no hiding time. Their own body
-- walks scared up to their spot (Roblox's walk slowed + the intro's look round), then SURVIVE in A's hero type with a
-- hit, and the lens glides back to the game's camera. Skip: Space, B, a tap
H.HIDER_INTRO = {
	on = false, -- (owner, 27 Nov: "scratch that no cinematic for survivor!! When you load in, it'll tell you survivor")
	len = 5,
	title = 1.6, -- (s of SURVIVE at the end; it fades over the last `home` s, then a cut to the game's camera)
	home = 0.35,
	walkFrom = 7, walkSpeed = 0.45, -- (studs behind their spot they start; the walk's speed)
	-- recordings only: the intro's heartbeat a little quicker and under its level, the game's own impact on the word
	sounds = {
		heart = { id = 9043365842, vol = 0.45, speed = 1.15 },
		hit = "boom", hitVol = 0.5, -- (v1: the boom peaked -1.7 dB)
	},
}

-- the survivors' role card (owner, 27 Nov: "no cinematic for survivor!! When you load in, it'll tell you survivor!!"):
-- SURVIVOR in A's hero type hits in with the game's own impact as they land in the round, holds, fades. It never stops
-- them moving and costs no hiding time. (HuntHiderIntro.client)
H.ROLE_CARD = { on = true, word = "SURVIVOR", delay = 0.35, hold = 1.7, fade = 0.5, hit = "boom", hitVol = 0.5 }

return H
