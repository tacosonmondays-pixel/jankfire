--!strict
-- RANKED DATA: every player's ranked ratings (Shared.Ranked has the maths), saved per player in its own session-locked
-- store through Profiles.luau (the loot and stats saves' layer): "JankfireRanked_v1", key "u<userId>". Studio Play tests
-- use "JankfireRanked_studio" instead, so a test match never reaches a live rating. no other system's store is touched.
--   data = { v = 1, season, modes = { ["2v2"] = Rating }, past = { [season] = { [mode] = peak } }, recent = { last 10 } }
-- after a ranked match (Matches.onEnd, m.ranked): each real player is updated as one Glicko-2 period against the other
-- team's composite (m.rated holds everyone's rating at the start, stand-ins too), and is sent the result (PlayPush
-- { t = "ranked", ... }) for the end screen and the lobby. leaving a ranked match before its end is a loss, applied the
-- moment you leave.
-- the player card (Stats.cardExtra) gets `ranked` = the player's best mode as a view RankedStyle draws.
-- player attribute RankedBest = "GOLD II" / "PLACEMENTS 2/5" / "UNRANKED" (for lists and nametags).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Ranked = require(Shared:WaitForChild("Ranked"))
local Profiles = require(script.Parent:WaitForChild("Profiles"))

local RankedData = {}
local RECENT = 10

local function template(): any
	return { v = 1, season = Ranked.SEASON, modes = {}, past = {}, recent = {} }
end
local store = Profiles.new(if RunService:IsStudio() then "JankfireRanked_studio" else "JankfireRanked_v1", template)

type State = { p: Player, prof: Profiles.Profile?, ready: boolean, done: { [number]: boolean } } -- done: match ids already rated
local st: { [Player]: State } = {}
local push: ((Player, any) -> ())? = nil -- (PlayServer: PlayPush:FireClient)
local Matches: any

local function dataOf(p: Player): any
	local s = st[p]
	return if s and s.prof then s.prof.data else nil
end

-- the stored rating for a mode, made fresh if there is none (and idle days turned into rd)
local function ratingOf(d: any, mode: string): Ranked.Rating
	local q = d.modes[mode]
	if type(q) ~= "table" or type(q.r) ~= "number" then
		q = Ranked.fresh()
		d.modes[mode] = q
	end
	return q
end

-- the view of one rating that the screens draw (RankedStyle): the rank, tier and division, placements
function RankedData.view(q: Ranked.Rating?, mode: string?): any
	if not q or (q.n or 0) <= 0 then return { unranked = true, mode = mode, n = 0, need = if q then q.need else Ranked.PLACEMENTS } end
	local rk = Ranked.rankOf(q)
	return {
		mode = mode, r = rk.r, placed = rk.placed, name = rk.name, tier = rk.tier and rk.tier.id, div = rk.div, step = rk.step,
		lo = if rk.lo == -math.huge then nil else rk.lo, hi = rk.hi, progress = rk.progress, n = q.n or 0, need = q.need or Ranked.PLACEMENTS,
		w = q.w or 0, l = q.l or 0, peak = math.floor((q.peak or 0) + 0.5),
	}
end

-- every ranked mode's view for a player (the Play screen's mode cards)
function RankedData.modes(p: Player): { [string]: any }
	local d = dataOf(p)
	local out = {}
	for _, m in Ranked.MODES do out[m] = RankedData.view(if d then d.modes[m] else nil, m) end
	return out
end

-- the player's best mode as a view (the card), or an unranked view
function RankedData.summary(p: Player): any
	local d = dataOf(p)
	if not d then return { unranked = true } end
	local mode, q = Ranked.best(d.modes)
	if not mode then return { unranked = true } end
	local v = RankedData.view(q, mode)
	v.season = d.season
	v.card = true -- (RankedStyle.label adds the mode on the card)
	return v
end

-- (r, rd) for a player in a mode: what the queue matches on and m.rated records
function RankedData.rating(p: Player, mode: string): (number, number, boolean)
	local d = dataOf(p)
	if not d then return Ranked.START.r, Ranked.START.rd, false end
	local q = d.modes[mode]
	if type(q) ~= "table" then return Ranked.START.r, Ranked.START.rd, false end
	local idleDays = if (q.last or 0) > 0 then (os.time() - (q.last :: number)) / 86400 else 0
	return q.r, Ranked.idle(q, idleDays), q.placed == true
end

function RankedData.ready(p: Player): boolean
	local s = st[p]
	return s ~= nil and s.ready
end

local function publish(p: Player)
	if not p.Parent then return end
	local v = RankedData.summary(p)
	local label = if v.unranked then "UNRANKED" else v.name
	if p:GetAttribute("RankedBest") ~= label then p:SetAttribute("RankedBest", label) end
end

-- ------------------------------------------------------------------ a finished match
-- rate one player in a finished (or left) match. rated = m.rated: { mode, teams = { { { id, r, rd } } } }
local function rate(p: Player, m: any, team: number, won: boolean): any?
	local s = st[p]
	local d = dataOf(p)
	if not s or not d or s.done[m.id] then return nil end
	local rated = m.rated
	if type(rated) ~= "table" or type(rated.teams) ~= "table" or not rated.teams[team] then return nil end
	s.done[m.id] = true
	local mine = rated.teams[team]
	-- every other team is one composite opponent (1v1v1 is never ranked, so this is the other team)
	local opp = {}
	for t, list in rated.teams do
		if t ~= team then for _, x in list do table.insert(opp, x) end end
	end
	local teamR = Ranked.team(mine)
	local oppR, oppRd = Ranked.team(opp)
	local q = ratingOf(d, rated.mode)
	-- (the rd as it stands after idle days, so coming back after a break moves you faster again)
	if (q.last or 0) > 0 then q.rd = Ranked.idle(q, (os.time() - (q.last :: number)) / 86400) end
	local res = Ranked.apply(q, teamR, oppR, oppRd, won, os.time())
	res.mode = rated.mode
	res.rank = RankedData.view(q, rated.mode)
	res.season = d.season
	table.insert(d.recent, 1, { t = os.time(), mode = rated.mode, r0 = res.before, r1 = res.after, res = if won then "W" else "L" })
	while #d.recent > RECENT do table.remove(d.recent) end
	if s.prof then s.prof.dirty = true end
	publish(p)
	return res
end

-- who is in a ranked match right now (our own record: Matches forgets a leaver before we hear they left)
local inRanked: { [Player]: { m: any, team: number } } = {}
local function onStart(m: any)
	if not m.ranked then return end
	for t, list in m.teams do for _, p in list do inRanked[p] = { m = m, team = t } end end
end

local function onEnd(m: any, winner: number?)
	if not m.ranked or type(m.rated) ~= "table" then return end
	for p, im in inRanked do if im.m == m then inRanked[p] = nil end end
	for t, list in m.teams do
		for _, p in list do
			if p.Parent then
				local res = rate(p, m, t, winner == t)
				if res and push then (push :: any)(p, { t = "ranked", result = res }) end
			end
		end
	end
end

-- ------------------------------------------------------------------ players
local function seasonCheck(d: any)
	if (tonumber(d.season) or 0) >= Ranked.SEASON then return end
	local old = tonumber(d.season) or 0
	d.past[tostring(old)] = {}
	for mode, q in d.modes do
		if type(q) == "table" and type(q.r) == "number" then
			d.past[tostring(old)][mode] = math.floor((q.peak or q.r) + 0.5)
			d.modes[mode] = Ranked.seasonReset(q)
		end
	end
	d.season = Ranked.SEASON
end

local function join(p: Player)
	local s: State = { p = p, prof = nil, ready = false, done = {} }
	st[p] = s
	p:SetAttribute("RankedBest", "UNRANKED")
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	s.prof = prof
	seasonCheck(prof.data)
	s.ready = true
	publish(p)
	prof.onLost.Event:Connect(function() warn("[jankfire] ranked: " .. p.Name .. "'s save was opened elsewhere") end)
end

local function leave(p: Player)
	local s = st[p]
	if not s then return end
	-- leaving a ranked match before its end: a loss, now
	local im = inRanked[p]
	inRanked[p] = nil
	if im and im.m.phase ~= "over" then pcall(rate, p, im.m, im.team, false) end
	st[p] = nil
	if s.prof then Profiles.release(store, s.prof) end
end

function RankedData.init(matches: any, stats: any?, pushFn: (Player, any) -> ())
	Matches = matches
	push = pushFn
	Matches.onStart(onStart)
	Matches.onEnd(onEnd)
	if stats and type(stats.cardExtra) == "function" then
		stats.cardExtra(function(target: Player, _viewer: Player?, card: any)
			card.ranked = RankedData.summary(target)
		end)
	end
	Players.PlayerAdded:Connect(function(p) task.spawn(join, p) end)
	for _, p in Players:GetPlayers() do task.spawn(join, p) end
	Players.PlayerRemoving:Connect(leave)
end

-- ------------------------------------------------------------------ Studio tests (PlayServer's JankPlayTest)
function RankedData.test(op: string, p: Player?, a: any, b: any): any
	if not RunService:IsStudio() then return nil end
	local d = if p then dataOf(p) else nil
	if op == "ranked" then
		if not d then return { ready = false } end
		return { ready = true, store = store.name, season = d.season, modes = d.modes, views = RankedData.modes(p :: Player), best = RankedData.summary(p :: Player), recent = d.recent }
	elseif op == "setranked" and d and type(a) == "string" and type(b) == "table" then
		local q = ratingOf(d, a)
		for _, k in { "r", "rd", "vol", "n", "w", "l", "need" } do if type(b[k]) == "number" then (q :: any)[k] = b[k] end end
		if type(b.placed) == "boolean" then q.placed = b.placed end
		local s = st[p :: Player]
		if s and s.prof then s.prof.dirty = true end
		publish(p :: Player)
		return RankedData.view(q, a)
	elseif op == "resetranked" and d then
		d.modes, d.past, d.recent, d.season = {}, {}, {}, Ranked.SEASON
		local s = st[p :: Player]
		if s and s.prof then s.prof.dirty = true end
		publish(p :: Player)
		return true
	end
	return nil
end

return RankedData
