--!strict
-- weapon unlocks (18 Nov 2026, the owner: "weapons are unlocked via level progression, some weapons are Robux exclusive
-- but free for now for everyone"). doc: docs/PROGRESSION.md, with the level table.
-- the level is the one Stats keeps already (Ranks.levelOf(xp): the Level attribute; XP from kills +20, rounds won +50,
-- 2 a minute of match time). a weapon opens at its LEVEL below; level 1 is a whole starter kit.
-- ROBUX: a few signature weapons are Robux exclusives. while WEAPONS_ROBUX_FREE is on, everyone has them at any level
-- (the loadout says FREE FOR NOW). switched off, they need their game pass: the ids below are placeholders for the owner
-- to fill in once they've made the passes (nothing here creates a product or sets a price).
-- nobody loses anything: WeaponsKept (Loadout.luau, once per player) keeps whatever a player already used or carried
-- when unlocks came in, whatever their level; UnlockAll (the owner, and Studio by default) opens everything.
-- the same rules run on the server (Loadout refuses a pick) and the clients (the locks shown), from the player's
-- attributes: Level (Stats), WeaponsKept, UnlockAll (Loadout), all set by the server.
local Unlocks = {}

Unlocks.WEAPONS_ROBUX_FREE = true -- (the owner's switch, like Config.LOOT_FREE. off: the passes below are needed)

-- weapon id -> the level it opens at (not listed: level 1). the weapons not on Roblox yet have one ready for the day
-- they go live
Unlocks.LEVEL = {
	-- level 1, the starter kit
	ar = 1, smg = 1, shotgun = 1, pistol = 1, katana = 1, frag = 1,
	-- the standard guns early
	revolver = 2, smoke = 2,
	burst = 3, knife = 3, medkit = 3,
	sniper = 4, popper = 4,
	sawnoff = 5, bubble = 5,
	lmg = 6, duck = 6, snowball = 6,
	dmr = 7, slapper = 7,
	lever = 8, wand = 8,
	marbles = 9, camera = 9, slipper = 9,
	-- the specials and the fun ones later
	redline = 10, reverse = 10,
	autoshot = 12, quiz = 12, bow = 12,
	tennis = 13,
	bread = 14, nvg = 14, scythe = 14, -- (the Scythe: the owner asked for it, 18 Nov, and main for a mid-high level)
	banana = 15, taser = 15,
	water = 16, radar = 16,
	cig = 17,
	nailgun = 18, laptop = 18,
	blower = 19,
	shredder = 20,
	bloodcross = 21, bowling = 22, remote = 23, scales = 24,
	-- not on Roblox yet (18 Nov, place version 870): their levels wait for the day they go live
	cards = 11, lasso = 20, cart = 25,
} :: { [string]: number }

-- the Robux exclusives: { pass = the game pass id (0: not made yet) }. a pass of 0 blocks nobody while the switch above
-- is on; keep it on until every live one here has its real pass, or that weapon is locked for everyone (bar kept/UnlockAll)
Unlocks.ROBUX = {
	minigun = { pass = 0 },
	laser = { pass = 0 }, -- Big Laser Pointer
	chicken = { pass = 0 }, -- Chicken Rocket
	akimbo = { pass = 0 }, -- Lefty & Righty (not on Roblox yet: it waits for its two-gun view)
} :: { [string]: { pass: number } }

function Unlocks.level(wid: string): number
	if Unlocks.ROBUX[wid] then return 1 end
	return Unlocks.LEVEL[wid] or 1
end
function Unlocks.robux(wid: string): boolean return Unlocks.ROBUX[wid] ~= nil end

-- may a player with this level, kept set and dev unlock carry it? (false, "LEVEL 7") / (false, "ROBUX")
function Unlocks.check(wid: string, level: number, kept: { [string]: boolean }?, all: boolean?, ownsPass: boolean?): (boolean, string?)
	if all then return true, nil end
	if kept and kept[wid] then return true, nil end
	if Unlocks.ROBUX[wid] then
		if Unlocks.WEAPONS_ROBUX_FREE or ownsPass then return true, nil end
		return false, "ROBUX"
	end
	local need = Unlocks.level(wid)
	if level >= need then return true, nil end
	return false, "LEVEL " .. need
end

-- the same from a player's attributes (Level, WeaponsKept, UnlockAll: the server's). a Robux pass is the server's to
-- check once passes exist (RobuxOwned: "minigun,laser")
function Unlocks.kept(p: Player): { [string]: boolean }
	local out = {}
	local s = p:GetAttribute("WeaponsKept")
	if type(s) == "string" then for id in string.gmatch(s, "[^,]+") do out[id] = true end end
	return out
end
function Unlocks.forPlayer(p: Player, wid: string): (boolean, string?)
	local lv = p:GetAttribute("Level")
	local owned = p:GetAttribute("RobuxOwned")
	local owns = type(owned) == "string" and table.find(string.split(owned, ","), wid) ~= nil
	return Unlocks.check(wid, if type(lv) == "number" then lv else 1, Unlocks.kept(p), p:GetAttribute("UnlockAll") == true, owns)
end

-- the weapons that open at exactly this level, roster order (the level-up toast): the live ones, or all with every = true
function Unlocks.at(level: number, roster: any, every: boolean?): { any }
	local out = {}
	for _, e in roster.list do
		if (every or e.live) and not Unlocks.ROBUX[e.id] and (Unlocks.LEVEL[e.id] or 1) == level then table.insert(out, e) end
	end
	return out
end

return Unlocks
