-- step 3a tests: the match core (MODES.md batch 1). limits, the vote's cards and tally, rooms (the match vs the Range),
-- loadouts and the weapon picker, infinite ammo, spawn picking, the bot brain's decisions. called from tests/run.luau
local fs = require("@lune/fs")
local roblox = require("@lune/roblox")
local V3 = roblox.Vector3

return function(T: any)
	local check, near, load = T.check, T.near, T.load
	local Weapons = load("src/shared/Weapons.luau", {})
	local Modes = load("src/shared/Modes.luau", {})
	local Rules = load("src/server/Rules.luau", { Weapons = Weapons })
	local Brain = load("src/server/BotBrain.luau", { Weapons = Weapons })
	local S = Weapons.S

	-- ------------------------------------------------------------ limits
	local k, t = Modes.limits("dm", false)
	local kb, tb = Modes.limits("dm", true)
	check(k == 20 and t == 360 and kb == 15 and tb == 300, "Deathmatch: 20 kills / 6 min with people only, 15 / 5 min with bots")
	local tk = Modes.limits("tdm", true)
	check(tk == 30, "(Team Deathmatch's numbers are ready for later: 30 with bots)")

	-- ------------------------------------------------------------ the vote's cards
	check(#Modes.modeCards("dm", 0, function() return 0.5 end) == 1, "only Deathmatch is ported: one mode card (the mode you just played, since there's nothing else)")
	check(Modes.modeCards("dm", 0, math.random)[1] == "dm", "and it's Deathmatch")
	local saved = {}
	for _, id in { "tdm", "tags", "rand", "gun", "spoons", "duckrain" } do saved[id] = Modes.GAMES[id].ported; Modes.GAMES[id].ported = true end
	local okMix, okLast, okEvent, okCount = true, true, true, true
	for day = 0, 13 do
		local cards = Modes.modeCards("dm", day, math.random)
		local teams, ffa = false, false
		for _, id in cards do if Modes.GAMES[id].teams then teams = true else ffa = true end; if id == "dm" then okLast = false end end
		if not (teams and ffa) then okMix = false end
		if #cards ~= 4 then okCount = false end
		local ev = Modes.eventFor(day)
		if Modes.GAMES[ev].ported and cards[1] ~= ev then okEvent = false end
	end
	check(okCount, "with more modes ported: 4 mode cards")
	check(okMix, "always a mix of team and FFA modes")
	check(okLast, "the mode just played doesn't come back while there are others")
	check(okEvent, "the daily event mode is always a card (when it's ported)")
	for id, v in saved do Modes.GAMES[id].ported = v end
	check(Modes.eventFor(0) == "duckrain" and Modes.eventFor(1) == "spoons" and Modes.eventFor(7) == "duckrain", "the daily event rotates through 7 modes")
	local mc = Modes.mapCards("dm", "rooftop")
	check(#mc == 1 and mc[1] == "rooftop", "maps: Rooftop (the Range is never on the vote)")
	check(Modes.VOTE.mode == 11 and Modes.VOTE.map == 9 and Modes.VOTE.reveal == 3 and Modes.VOTE.cards == 4, "vote timings: 11 s mode, 9 s map, 3 s reveal, 4 cards")

	-- ------------------------------------------------------------ the tally: people decide, bots only break ties
	check(Modes.tally(3, { a = 2, b = 2, c = 1 }, { x = 1, y = 1, z = 1 }) == 2, "people's votes win over any number of bot votes")
	check(Modes.tally(3, { a = 1, b = 3 }, { x = 3 }) == 3, "a tie between people is broken by the bots")
	check(Modes.tally(3, {}, { x = 2, y = 2, z = 1 }) == 2, "nobody voted: the bots decide")
	check(Modes.tally(4, {}, {}) == 1, "no votes at all: the first card")
	check(Modes.tally(2, { a = 9 }, {}) == 1, "a bad card number is ignored")
	check(Modes.closeAt(100, 11, nil) == 111 and near(Modes.closeAt(100, 11, 103), 105.5, 1e-9) and Modes.closeAt(100, 11, 110) == 111, "a stage closes on its timer, or 2.5 s after everyone voted")

	-- ------------------------------------------------------------ rooms, loadouts, the Range
	local function fighter(kind: string?, room: string?): any
		local f = Rules.newFighter(kind or "player", "p", nil)
		f.room = room or "ffa"
		Rules.spawn(f, 0)
		return f
	end
	local eye = V3.new(0, 4.8, 0)
	do
		local f = fighter()
		check(Rules.setLoadout(f, { "redline", "marbles", "katana" }) == nil, "loadout: one weapon per slot")
		check(Rules.setLoadout(f, { "marbles", "redline", "katana" }) ~= nil, "refused: weapons in the wrong slots")
		check(Rules.setLoadout(f, { "redline", "marbles" }) ~= nil and Rules.setLoadout(f, { "redline", "marbles", "sniper" }) ~= nil and Rules.setLoadout(f, "redline") ~= nil, "refused: too few, unknown weapons, garbage")
		check(Rules.equip(f, "parry", 1) ~= nil, "refused: equipping a hidden weapon (the parry's kill credit)")
	end
	do -- the Range: infinite ammo, nothing scores, it can't touch the match
		local f = fighter("player", "training")
		local ok = 0
		for i = 1, 80 do if Rules.fire(f, "redline", i * 0.2, eye, eye) == nil then ok += 1 end end
		check(ok == 80 and f.ammo.redline.mag == 40, "the Range: infinite ammo (80 shots, the mag never drops)")
		local g = fighter("player", "ffa")
		local done = Rules.damage(g, 50, f, "redline", 10)
		check(done == 0 and g.hp == 100, "the Range can't hurt the match (different rooms)")
		check(Rules.hit(f, g, "redline", 1, 0, 10, { dist = 10, speedF = 0, speedT = 0, los = true }) == "not in your room", "refused: a hit from the Range on someone in the match")
		Rules.equip(f, "katana", 11); Rules.swing(f, "katana", 12)
		check(Rules.meleeHit(f, g, "katana", 12.1, { dist = 5, look = V3.new(0, 0, -1), to = V3.new(0, 0, -5), los = true, speedF = 0, speedT = 0 }) == "not in your room", "refused: a katana hit across rooms")
		local d = fighter("dummy", "training")
		Rules.damage(d, 200, f, "katana", 20)
		check(f.kills == 0 and f.kat == 1, "a Range kill doesn't score, but the katana still grows (a test bench)")
		local h = fighter("player", "training")
		Rules.damage(h, 200, f, "redline", 30)
		check(f.kills == 0, "killing another person on the Range doesn't score either")
	end
	do -- spawn picking: the spot farthest from the nearest enemy (+ a random 0-45 studs)
		local pts = { V3.new(0, 0, 0), V3.new(100, 0, 0), V3.new(300, 0, 0) }
		local p = Rules.pickSpawn(pts, { V3.new(280, 0, 0), V3.new(10, 0, 0) }, function() return 0 end)
		check(p == pts[2], "pickSpawn: the spot farthest from its nearest enemy")
		local q = Rules.pickSpawn(pts, {}, function() return 0 end)
		check(q ~= nil, "pickSpawn with nobody around still picks one")
		local wins = {}
		for i = 1, 30 do local r = Rules.pickSpawn(pts, { V3.new(200, 0, 0) }, function() return (i % 10) / 10 end); wins[r] = true end
		check(wins[pts[1]] and not wins[pts[2]], "the random part (0-45 studs) can't beat a 100-stud difference")
	end

	-- ------------------------------------------------------------ the bot brain
	do
		check(Brain.weapon(5, "redline", 0) == "katana" and Brain.weapon(20, "redline", 0) == "marbles" and Brain.weapon(80, "redline", 0) == "redline", "bots pick the weapon for the range: katana up close, marbles mid, Redline far")
		check(Brain.weapon(12, "katana", 0) == "katana" and Brain.weapon(12, "marbles", 0) == "marbles", "a little give at the boundary (no flicking back and forth)")
		check(Brain.weapon(24, "marbles", 10) == "katana" and Brain.weapon(24, "marbles", 0) == "marbles", "a long katana (10 kills) fights from further away")
		local lo, hi = Brain.pref("marbles", 0)
		local lo2, hi2 = Brain.pref("redline", 0)
		local _, hik = Brain.pref("katana", 0)
		check(lo == 4.5 and hi == 12 and lo2 == 21 and hi2 == 66 and near(hik, 8.4 * 0.7, 1e-9), "preferred range: marbles 1.5-4 m, guns 7-22 m, melee right in (web botThink)")
		local a, b = { f = "a" }, { f = "b" }
		a.dist, a.vis, b.dist, b.vis = 40, false, 90, true
		check(Brain.target({ a, b }).f == "b", "a target it can see at 90 beats one behind a wall at 40 (x2.5)")
		a.vis = true
		check(Brain.target({ a, b }).f == "a", "the nearest of the ones it can see")
		check(Brain.target({}) == nil, "nobody: no target")
		local to = V3.new(0, 0, -100)
		local w1 = Brain.wish(to, 100, true, 21, 66, 1, false)
		check(w1.Z < 0 and math.abs(w1.X) > 0.3, "too far: walk in, strafing")
		local w2 = Brain.wish(V3.new(0, 0, -10), 10, true, 21, 66, 1, false)
		check(w2.Z > 0, "too close with a gun: back off")
		local w3 = Brain.wish(V3.new(0, 0, -30), 30, false, 21, 66, 1, false)
		check(w3.Z < 0, "out of sight: go find them")
		local w4 = Brain.wish(V3.new(0, 0, -20), 20, true, 0, 5.9, 1, true)
		check(math.abs(w4.X) < 1e-6 and w4.Z < 0, "with the katana: straight in, no circling")
		check(not Brain.canFire(false, 5, 0, 10, "redline", 0), "bots never fire at someone they can't see (no wallhacks)")
		check(not Brain.canFire(true, 0.1, 0, 10, "redline", 0) and Brain.canFire(true, 0.5, 0.1, 10, "redline", 0), "they react after 0.35 s, then fire when on target")
		check(not Brain.canFire(true, 1, 0.5, 10, "redline", 0), "not while turned away")
		check(Brain.canFire(true, 0, 0.4, 8, "katana", 0) and not Brain.canFire(true, 0, 0.4, 12, "katana", 0), "swing when in reach")
		check(Brain.wantHook(true, 0, true, 30) == "save" and Brain.wantHook(false, 100, false, 0) == "cross" and Brain.wantHook(true, 100, false, 0) == nil and Brain.wantHook(false, 400, false, 0) == nil, "grapple: out of the smog, across a gap in range, not otherwise")
		check(Brain.parryChance(true, true, "blade") > Brain.parryChance(true, true, "gun") and Brain.parryChance(true, false, "gun") == 0 and Brain.parryChance(false, true, "gun") == 0, "parry sometimes: more often against a blade, only with the katana out and ready")
		check(Brain.wanted(0, 6) == 6 and Brain.wanted(2, 6) == 4 and Brain.wanted(9, 6) == 0, "bots fill the seats: 6 seats, every person takes a bot's")
	end

	-- ------------------------------------------------------------ the Range in the place
	local parts = fs.isFile("build/Range.model.json") and require("@lune/serde").decode("json", fs.readFile("build/Range.model.json"))
	if parts then
		local a = parts.Properties.Attributes.Attributes
		check(a.MapId.String == "range" and a.Offset.Vector3[1] == 20000 and near(a.KillY.Float64, -180, 1e-6), "the Range sits 20000 studs east of Rooftop, kill height -180")
		local dummies, spawns = 0, 0
		for _, c in parts.Children do
			if c.Name == "Dummies" then dummies = #c.Children end
			if c.Name == "Spawns" then spawns = #c.Children; check(c.Children[1].Properties.CFrame.CFrame.position[1] > 19000, "Range spawns moved with it") end
		end
		check(dummies == 8 and spawns == 3, ("the Range: 8 dummy spots, 3 spawns (%d, %d)"):format(dummies, spawns))
		local _ = S
	end
end
