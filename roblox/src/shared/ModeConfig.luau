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

-- the cards (PlayConfig.addMode): id, name, the card's rules line. kind = which rules run it. all four are free for all
-- (ffa: Queue packs whole parties, every player their own side)
ModeConfig.LIST = {
	{ id = "gun", kind = "gun", name = "GUN GAME", sub = "19 weapons · a kill moves you up · the last rung wins",
		rule = "a kill moves you up · a melee death knocks you down" },
	{ id = "oitc", kind = "oitc", name = "ONE IN THE CHAMBER", sub = "1 bullet, any hit kills · 3 lives · last one standing",
		rule = "a kill gives a bullet · 3 lives" },
	{ id = "duckrain", kind = "dm", name = "DUCK RAIN", sub = "free for all · ducks fall as black holes · first to 20",
		rule = "watch for the shadows · first to 20" },
	{ id = "rand", kind = "dm", name = "RANDOMIZER", sub = "free for all · a random loadout every life · first to 20",
		rule = "a random loadout every life · first to 20" },
}
ModeConfig.byId = {} :: { [string]: any }
for _, m in ModeConfig.LIST do
	ModeConfig.byId[m.id] = m
	-- (teams x size keep a queue without the free-for-all branch from ever forming one: 8 x 4 = 32 seats)
	PlayConfig.addMode({ id = m.id, name = m.name, sub = m.sub, teams = ModeConfig.MAX, size = PlayConfig.PARTY_MAX, ffa = true,
		min = ModeConfig.MIN, max = ModeConfig.MAX, fill = ModeConfig.FILL, pad = "modes" })
end

return ModeConfig
