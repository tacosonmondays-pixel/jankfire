--!strict
-- MODES: JANKFIRE's classic modes on the Play screen's MODES tab (roblox/docs/MODES.md: the web rules, traced to the
-- web code, and "Roblox adaptations" for what had to change). the numbers each mode plays by, the cards, and the gun
-- game's ladder pools. shared: the server runs the rules (server/Modes.luau), the clients draw the cards and the HUD
-- (client/ModeHud.client.luau). requiring it puts the cards in PlayConfig.EXTRA (PlayConfig.addMode).
-- units: 1 m = 3 studs (Weapons.S). times in seconds
local Shared = script.Parent
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))

local ModeConfig = {}
local S = 3

-- the queue (Queue.luau's free-for-all branch): a match is MIN..MAX players, parties kept whole. it goes at MAX, or
-- at MIN once the oldest in the queue has waited FILL s
ModeConfig.MIN, ModeConfig.MAX, ModeConfig.FILL = 2, 8, 15
-- from spawning in to the clock running (the arena's name, the mode's name, its rules line)
ModeConfig.READY = 4

-- web room.js ROUND.ffa / TARGETS.ffa (the Online numbers: there are no bots on Roblox)
ModeConfig.DM = { target = 20, time = 360 }
-- web modes.js GUNGAME / LADDER_POOL / rollLadder: 10 guns, then 5 silly, then 3 melee, then the knife in its spoon
-- look; the weapons that sat out the last match first. 600 s, then the highest rung (ties: kills)
ModeConfig.GUN = {
	time = 600,
	guns = { "ar", "smg", "redline", "shotgun", "minigun", "shredder", "revolver", "marbles", "sniper", "burst", "lmg", "dmr", "lever",
		"autoshot", "nailgun", "pistol", "akimbo", "sawnoff", "laser" },
	silly = { "bow", "chicken", "bloodcross", "banana", "cards", "bowling", "tennis", "cart", "snowball", "taser", "slipper" },
	melee = { "slapper", "bread", "scales", "katana" },
	take = { guns = 10, silly = 5, melee = 3 },
	last = "knife",
}
-- a ladder weapon that isn't on Roblox yet plays as the nearest one that is (the first on its list not on the ladder
-- already, else the first). the Shredder is a Tool of its own that only a spawn hands out, so a mid-life rung swap
-- can't give it: it plays as the Lawn Mower. when a weapon is ported (Roster live) it takes its own rung by itself
ModeConfig.NEAREST = {
	minigun = { "lmg", "smg" }, shredder = { "autoshot", "shotgun" }, nailgun = { "smg", "ar" }, akimbo = { "pistol", "revolver" },
	laser = { "sniper", "dmr" },
	bow = { "lever", "dmr" }, chicken = { "shotgun", "sawnoff" }, bloodcross = { "revolver", "pistol" }, banana = { "marbles", "sawnoff" },
	cards = { "burst", "pistol" }, bowling = { "autoshot", "shotgun" }, tennis = { "pistol", "marbles" }, cart = { "shotgun", "autoshot" },
	snowball = { "pistol", "revolver" }, taser = { "sawnoff", "pistol" }, slipper = { "katana" },
	slapper = { "katana" }, bread = { "katana" }, scales = { "katana" }, knife = { "katana" },
}
-- web modes.js oitc + room.js oitcShot: a Revolver hit is 999 (always kills), 1 bullet a life, 3 at most, 3 lives.
-- the kit's knife isn't on Roblox yet: the katana stands in (NEAREST.knife)
ModeConfig.OITC = { lives = 3, bullets = 1, maxBullets = 3, time = 360, kit = { "revolver", "knife" }, gun = "revolver", hit = 999 }
-- web modes.js DUCKRAIN + room.js skyDucks: deathmatch numbers, and sky ducks
ModeConfig.DUCKRAIN = {
	first = 3, everyFrom = 2.4, everyTo = 1.1, countFrom = 1.5, countTo = 3.5, near = 0.5, nearMin = 2 * S, nearMax = 14 * S,
	areaPer = 9000, sizeMin = 0.5, sizeMax = 1.8, -- (size = clamp(sqrt(floor m2 / 9000), 0.5, 1.8))
	above = 20 * S, drop = 46 * S, v0 = 6 * S, g = 22 * S, maxFall = 8, grid = 2.5 * S,
	hole = { R = 12 * S, pull = 40 * S, life = 2.6 }, -- (the blast is the duck item's own: Items.DUCK blastR / blastKb / blastDmg)
	lookR = 3.5 * S, lookY = 4 * S, credit = 6,
}

-- web modes.js TARGETS (Online) for the team modes: team deathmatch 40 team kills, tags 25 confirms, 360 s; a tag lasts
-- 30 s and is picked up within 1.9 m of your centre (feet + 0.9 m), placed 0.9 m over the floor (room.js dropTag)
ModeConfig.TDM = { target = 40, time = 360 }
ModeConfig.TAGS = { target = 25, time = 360, life = 30, grab = 1.9 * S, up = 0.9 * S, drop = 60 * S }
-- the two sides of a team mode: the duels' own (Matches TEAM_NAMES / TEAM_HEX: the pads' pink and cyan), not the web's
-- red and blue, so a side looks the same everywhere in the game
-- web modes.js spoons kit: { slots: ['knife'] (in its spoon look), noItem, noStreaks, oneHit, speedMul: 1.6 }, hookMul 1.35
ModeConfig.SPOONS = { kit = { "knife" }, speed = 1.6, hook = 1.35 }
-- web modes.js INFECT: 180 s, patient zero 6 s in (two with 8 or more fighters), 200 HP zombies with the claw
ModeConfig.INF = { time = 180, delay = 6, two = 8, hp = 200, claw = "claw", color = "#7dff4f" }
-- (20 Nov 2026: shared/TeamColors.luau's first two, the pads' and the duels' palette)
local TeamColors = require(Shared:WaitForChild("TeamColors")) :: any
ModeConfig.SIDES = { { name = TeamColors.name(1), hex = TeamColors.hex(1) }, { name = TeamColors.name(2), hex = TeamColors.hex(2) } }
-- a team mode's queue (Queue.luau's team branch): whole parties on one side each, 1-4 a side, the sides at most one
-- apart; it goes at 4v4, or once the oldest has waited FILL s with both sides filled

-- the cards (PlayConfig.addMode): id, name, the card's rules line. kind = which rules run it. ffa = free for all (Queue
-- packs whole parties, every player their own side); sides = 2: a team mode
ModeConfig.LIST = {
	{ id = "gun", kind = "gun", name = "GUN GAME", sub = "19 weapons · a kill moves you up · the last rung wins",
		rule = "a kill moves you up · a melee death knocks you down" },
	{ id = "oitc", kind = "oitc", name = "ONE IN THE CHAMBER", sub = "1 bullet, any hit kills · 3 lives · last one standing",
		rule = "a kill gives a bullet · 3 lives" },
	{ id = "duckrain", kind = "dm", name = "DUCK RAIN", sub = "free for all · ducks fall as black holes · first to 20",
		rule = "watch for the shadows · first to 20" },
	{ id = "rand", kind = "dm", name = "RANDOMIZER", sub = "free for all · a random loadout every life · first to 20",
		rule = "a random loadout every life · first to 20" },
	{ id = "spoons", kind = "spoons", name = "SPOONS & GRAPPLES", sub = "spoons only, one hit kills · the grapple pulls harder · first to 20",
		rule = "one hit kills · you run faster · the grapple pulls harder" },
	{ id = "tdm", kind = "tdm", sides = 2, name = "TEAM DEATHMATCH", sub = "two teams · every kill scores · first to 40",
		rule = "every kill scores for your team · first to 40" },
	{ id = "tags", kind = "tags", sides = 2, name = "TAGS", sub = "two teams · grab enemy tags to score · first to 25",
		rule = "grab enemy tags to score · grab your team's to deny" },
	{ id = "inf", kind = "inf", name = "INFECTION", sub = "someone turns 6 s in · the zombies' kills turn · survive 3 minutes",
		rule = "survive 3 minutes · a zombie's kill turns you" },
}
ModeConfig.byId = {} :: { [string]: any }
for _, m in ModeConfig.LIST do
	ModeConfig.byId[m.id] = m
	if m.sides == 2 then
		-- (a queue without the team branch would need a full 4v4 to form one)
		PlayConfig.addMode({ id = m.id, name = m.name, sub = m.sub, teams = 2, size = PlayConfig.PARTY_MAX, sides = 2,
			fill = ModeConfig.FILL, pad = "modes" })
	else
		-- (teams x size keep a queue without the free-for-all branch from ever forming one: 8 x 4 = 32 seats)
		PlayConfig.addMode({ id = m.id, name = m.name, sub = m.sub, teams = ModeConfig.MAX, size = PlayConfig.PARTY_MAX, ffa = true,
			min = ModeConfig.MIN, max = ModeConfig.MAX, fill = ModeConfig.FILL, pad = "modes" })
	end
end

return ModeConfig
