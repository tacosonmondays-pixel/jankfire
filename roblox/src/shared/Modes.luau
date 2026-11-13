--!strict
-- the game modes and the end-of-match vote (roblox/docs/MODES.md: GAMES, TARGETS, ROUND, VOTE, shared/vote.js).
-- every quick-play mode is listed; only the ones ported to Roblox (`ported`) reach the vote, so a new mode slots in by
-- flipping its flag. pure functions: the tests run them outside Roblox
local Modes = {}

export type Game = { id: string, name: string, teams: boolean, ported: boolean, quick: boolean, desc: string }

Modes.GAMES = {
	dm = { id = "dm", name = "Deathmatch", teams = false, ported = true, quick = true, desc = "everyone for themselves. first to the kill limit." },
	tdm = { id = "tdm", name = "Team Deathmatch", teams = true, ported = false, quick = true, desc = "red vs blue. every kill is a point." },
	tags = { id = "tags", name = "Tags", teams = true, ported = false, quick = true, desc = "kills drop dog tags. grab them." },
	rand = { id = "rand", name = "Randomizer", teams = false, ported = false, quick = true, desc = "a random loadout every life." },
	gun = { id = "gun", name = "Gun Game", teams = false, ported = false, quick = true, desc = "one weapon at a time. the spoon wins." },
	inf = { id = "inf", name = "Infection", teams = true, ported = false, quick = true, desc = "someone turns. then everyone does." },
	spoons = { id = "spoons", name = "Spoons & Grapples", teams = false, ported = false, quick = true, desc = "spoons only. one hit kills." },
	duckrain = { id = "duckrain", name = "Duck Rain", teams = false, ported = false, quick = true, desc = "it's raining black holes." },
	lava = { id = "lava", name = "Floor Is Lava", teams = false, ported = false, quick = true, desc = "the floor burns. stay up." },
	oitc = { id = "oitc", name = "One in the Chamber", teams = false, ported = false, quick = true, desc = "one bullet. three lives." },
} :: { [string]: Game }
-- the order cards are offered in (shared/modes.js GAME_ORDER)
Modes.ORDER = { "dm", "tdm", "tags", "rand", "gun", "inf", "spoons", "duckrain", "lava", "oitc" }
-- the daily EVENT mode, rotating at midnight UTC
Modes.EVENTS = { "duckrain", "spoons", "lava", "oitc", "gun", "inf", "rand" }
-- which maps each mode can use (the Range is never on the list)
Modes.MAPS = {
	rooftop = { id = "rooftop", name = "Rooftop", desc = "neon roofs over the smog. mind the gap." },
} :: { [string]: { id: string, name: string, desc: string } }
Modes.MAP_ORDER = { "rooftop" }

-- the vote's timings, seconds (shared/vote.js VOTE: mode 11 s, map 9 s, reveal 3 s, 4 cards). a stage with one card
-- just shows it for `single` s; once every human has voted it closes `early` s later; bots vote 1.2-7 s in
Modes.VOTE = { mode = 11, map = 9, reveal = 3, cards = 4, single = 2, early = 2.5, botMin = 1.2, botMax = 7 }

-- kill limit + clock: an Online room (people only) vs a room with bots (room.js ROUND, modes.js TARGETS)
function Modes.limits(game: string, withBots: boolean): (number, number)
	if game == "tdm" then return if withBots then 30 else 40, if withBots then 300 else 360 end
	if game == "tags" then return if withBots then 20 else 25, if withBots then 300 else 360 end
	return if withBots then 15 else 20, if withBots then 300 else 360
end

function Modes.eventFor(day: number): string
	return Modes.EVENTS[day % #Modes.EVENTS + 1]
end

local function ported(id: string): boolean
	local g = Modes.GAMES[id]
	return g ~= nil and g.ported and g.quick
end

-- stage 1: up to 4 mode cards. the daily event is always one (if ported), team and FFA modes are mixed when both
-- exist, and the mode just played only comes back if there's nothing else
function Modes.modeCards(last: string?, day: number, rand: () -> number): { string }
	local pool = {}
	for _, id in Modes.ORDER do if ported(id) and id ~= last then table.insert(pool, id) end end
	if #pool == 0 and last and ported(last) then table.insert(pool, last) end
	local cards = {}
	local ev = Modes.eventFor(day)
	if table.find(pool, ev) then table.insert(cards, ev) end
	-- shuffle the rest, then take a team one and an FFA one first so both kinds show
	local rest = {}
	for _, id in pool do if id ~= ev then table.insert(rest, id) end end
	for i = #rest, 2, -1 do local j = math.floor(rand() * i) + 1; rest[i], rest[j] = rest[j], rest[i] end
	local function takeOne(teams: boolean)
		if #cards >= Modes.VOTE.cards then return end
		for i, id in rest do
			if Modes.GAMES[id].teams == teams then table.insert(cards, id); table.remove(rest, i); return end
		end
	end
	local hasTeams, hasFfa = false, false
	for _, id in cards do if Modes.GAMES[id].teams then hasTeams = true else hasFfa = true end end
	if not hasTeams then takeOne(true) end
	if not hasFfa then takeOne(false) end
	for _, id in rest do if #cards < Modes.VOTE.cards then table.insert(cards, id) end end
	return cards
end

-- stage 2: up to 4 maps for the mode; the map just played goes last in line
function Modes.mapCards(game: string, last: string?): { string }
	local _ = game
	local cards = {}
	for _, id in Modes.MAP_ORDER do if id ~= last then table.insert(cards, id) end end
	if last and Modes.MAPS[last] then table.insert(cards, last) end
	while #cards > Modes.VOTE.cards do table.remove(cards) end
	return cards
end

-- the winner of a stage: humans decide; bots' votes only break a tie between the cards humans tied on; still tied =
-- the first of them (random pick is the caller's, by shuffling). votes: { [voter]: cardIndex }
function Modes.tally(n: number, humans: { [any]: number }, bots: { [any]: number }): number
	local hc, bc = table.create(n, 0), table.create(n, 0)
	for _, i in humans do if hc[i] then hc[i] += 1 end end
	for _, i in bots do if bc[i] then bc[i] += 1 end end
	local best = -1
	for i = 1, n do best = math.max(best, hc[i]) end
	local tied = {}
	for i = 1, n do if hc[i] == best then table.insert(tied, i) end end
	local win, wb = tied[1], -1
	for _, i in tied do if bc[i] > wb then win, wb = i, bc[i] end end
	return win
end

-- when a stage closes: its full time, or `early` s after every human has voted (whichever is first)
function Modes.closeAt(start: number, dur: number, allVotedAt: number?): number
	if allVotedAt then return math.min(start + dur, allVotedAt + Modes.VOTE.early) end
	return start + dur
end

return Modes
