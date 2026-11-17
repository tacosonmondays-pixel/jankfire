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
	return { v = 1, season = Ranked.SEASON, modes = {}, past = {}, recent = {}, log = {}, fixed = {} }
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
	if not q or (q.n or 0) <= 0 then
		return { unranked = true, mode = mode, ladder = if mode == Ranked.PARTY_KEY then "party" else "duels", n = 0, need = if q then q.need else Ranked.PLACEMENTS }
	end
	local rk = Ranked.rankOf(q, if mode == Ranked.PARTY_KEY then "party" else nil)
	-- (the MMR itself never leaves the server: the screens show rank points, rp of 100 in the division)
	return {
		mode = mode, ladder = if mode == Ranked.PARTY_KEY then "party" else "duels", placed = rk.placed, name = rk.name, tier = rk.tier.id, div = rk.div, step = rk.step, rp = rk.rp,
		progress = rk.progress, n = q.n or 0, need = q.need or Ranked.PLACEMENTS, w = q.w or 0, l = q.l or 0,
	}
end

-- every ranked mode's view for a player (the Play screen's mode cards)
function RankedData.modes(p: Player): { [string]: any }
	local d = dataOf(p)
	local out = {}
	for _, m in Ranked.MODES do out[m] = RankedData.view(if d then d.modes[m] else nil, m) end
	out[Ranked.PARTY_KEY] = RankedData.view(if d then d.modes[Ranked.PARTY_KEY] else nil, Ranked.PARTY_KEY)
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

-- ------------------------------------------------------------------ restoring after a cheater (17 Nov, the owner:
-- "If someone is caught cheating give back any ranked stuff or stats!!"; the kind of restore Valorant does)
-- every ranked match goes in an index store (logStore): "m:<match key>" = its teams (user ids, stand-ins too) and each
-- real player's change { team, won, rp, mmr }; "u:<user id>" = the keys of that player's ranked matches. each player's
-- own save keeps the same per match in d.log (their history for the season).
-- RankedData.restoreFor(cheaterId, since), called by the anti-cheat session when a cheater is CONFIRMED (an owner ban
-- or confirm, never an automatic flag): for every ranked match the cheater played since `since` (default: the last
-- 14 days of this season), once per match (the record is marked restored):
--   * each player on the OTHER team who LOST gets back the RP and the MMR they lost, and the loss comes off their W/L
--   * the cheater's teammates are left alone: they didn't cheat, their result stands either way
--   * the cheater's season is voided: every mode back to the MMR it started the season at, RP and placements reset,
--     their save flagged (d.void)
-- a player online in this server gets it at once; anyone else gets a pending fix in fixStore ("r:<user id>"), taken and
-- applied on their next join (their own save is session-locked, so nothing else writes into it). with
-- PlayConfig.CROSS_SERVER on, MessagingService ("JankRankedFix") tells the server they're on to take it now.
-- the restored player sees "RANKED RATING RESTORED +N"
-- RankedData.undoRestore(uid), for a wrong catch (the anti-cheat session's UNCONFIRM / UNBAN): the accused's season
-- comes back as it was before the void. the players who got RP back keep it, and the matches stay marked restored, so a
-- later CONFIRM never pays anyone twice
local DataStoreService = game:GetService("DataStoreService")
local MessagingService = game:GetService("MessagingService")
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))
local studio = RunService:IsStudio()
local logStore: DataStore? = nil
local fixStore: DataStore? = nil
pcall(function()
	logStore = DataStoreService:GetDataStore(if studio then "JankfireRankedLog_studio" else "JankfireRankedLog_v1")
	fixStore = DataStoreService:GetDataStore(if studio then "JankfireRankedFix_studio" else "JankfireRankedFix_v1")
end)
local LOG_KEEP = 300 -- matches in a player's own log
local INDEX_DAYS = 30 -- a "u:" index keeps this long
local RESTORE_DAYS = 14

local matchRes: { [string]: { [string]: any } } = {} -- each live ranked match's results so far (leavers included)

local function idsOf(rated: any): { { number } }
	local out = {}
	for t, list in rated.teams do
		out[t] = {}
		for _, x in list do table.insert(out[t], x.id) end
	end
	return out
end

-- the player's own log line for a match (rate() calls this)
local function logMatch(p: Player, d: any, m: any, team: number, won: boolean, res: any)
	local teams = idsOf(m.rated)
	local mates, foes = {}, {}
	for t, ids in teams do
		for _, id in ids do
			if t == team and not m.ffa then if id ~= p.UserId then table.insert(mates, id) end elseif id ~= p.UserId then table.insert(foes, id) end
		end
	end
	d.log = d.log or {}
	table.insert(d.log, 1, { k = m.key, t = os.time(), mode = m.rated.rkey or m.rated.mode, played = m.rated.mode, team = team, mates = mates, foes = foes,
		rp = res.delta, mmr = res.mmrDelta, won = won, place = res.place, of = res.of, season = d.season })
	while #d.log > LOG_KEEP do table.remove(d.log) end
	local key = tostring(m.key)
	matchRes[key] = matchRes[key] or {}
	matchRes[key][tostring(p.UserId)] = { team = team, won = won, rp = res.delta, mmr = res.mmrDelta, placed = res.delta == nil, place = res.place }
end

-- after a ranked match: its record and every player's index line (in the background, retried by the store)
local function writeIndex(m: any)
	local store = logStore
	if not store or type(m.key) ~= "string" then return end
	local key = m.key :: string
	local rec = { ffa = m.ffa == true, t = os.time(), mode = m.rated.rkey or m.rated.mode, played = m.rated.mode, season = Ranked.SEASON, teams = idsOf(m.rated), res = matchRes[key] or {} }
	matchRes[key] = nil
	pcall(function() (store :: DataStore):SetAsync("m:" .. key, rec) end)
	local cut = os.time() - INDEX_DAYS * 86400
	for t, ids in rec.teams do
		for _, id in ids do
			pcall(function()
				(store :: DataStore):UpdateAsync("u:" .. id, function(old: any)
					local list = {}
					for _, e in (if type(old) == "table" then old else {}) do if type(e) == "table" and (e.t or 0) >= cut then table.insert(list, e) end end
					table.insert(list, { k = key, t = rec.t, team = t })
					while #list > LOG_KEEP do table.remove(list, 1) end
					return list
				end)
			end)
		end
	end
end

-- a voided season: every mode back to where it started, no placements, no RP; the save says so
local function voidSeason(d: any)
	-- (kept, so a wrong catch can be undone: RankedData.undoRestore)
	local keep = {}
	for mode, q in d.modes do if type(q) == "table" then keep[mode] = table.clone(q) end end
	d.voidBackup = { season = d.season, modes = keep }
	for mode, q in d.modes do
		if type(q) == "table" then
			local s0 = tonumber(q.s0) or Ranked.START.r
			local f = Ranked.fresh()
			f.r, f.s0 = s0, s0
			d.modes[mode] = f
		end
	end
	d.void = { t = os.time(), season = d.season }
end

-- apply fixes to a loaded save: { k, mode, rp, mmr, season } refunds, { void = true } and { unvoid = true } (each key once)
local function apply(p: Player, fixes: { any })
	local d = dataOf(p)
	if not d then return end
	d.fixed = d.fixed or {}
	local total, any = 0, false
	for _, fx in fixes do
		if type(fx) ~= "table" or type(fx.k) ~= "string" or d.fixed[fx.k] then continue end
		d.fixed[fx.k] = os.time()
		if fx.void then
			voidSeason(d)
		elseif fx.unvoid then
			-- a wrong catch: the season as it was before the void (matches played since the void are dropped with it), and
			-- a later CONFIRM can void it again
			local b = d.voidBackup
			if d.void and type(b) == "table" and b.season == d.season and type(b.modes) == "table" then d.modes = b.modes end
			d.void, d.voidBackup = nil, nil
			d.fixed[("void:%d:%d"):format(p.UserId, d.season)] = nil
			any = true
		elseif fx.season == d.season and type(fx.mode) == "string" then
			local q = d.modes[fx.mode]
			if type(q) == "table" then
				local rp = math.max(0, tonumber(fx.rp) or 0)
				if q.placed and rp > 0 then
					q.lp = (if type(q.lp) == "number" then q.lp else Ranked.ladderOf(q.r)) + rp
					total += rp
				end
				q.r += math.max(0, tonumber(fx.mmr) or 0)
				q.l = math.max(0, (q.l or 0) - 1)
				any = true
				for _, e in d.log or {} do if e.k == fx.k then e.restored = true end end
			end
		end
	end
	local s = st[p]
	if s and s.prof then s.prof.dirty = true end
	publish(p)
	RankedData.topWrite(p) -- (a refund moves them on the global lists; a void takes them off)
	if (any or total > 0) and push then
		(push :: any)(p, { t = "toast", text = if total > 0 then ("RANKED RATING RESTORED +%d"):format(total) else "RANKED RATING RESTORED", refresh = true })
	end
end

-- take this player's pending fixes out of the store and apply them (on join, or when another server says so)
local function pull(p: Player)
	local store = fixStore
	if not store or not dataOf(p) then return end
	local got: { any } = {}
	local ok = pcall(function()
		(store :: DataStore):UpdateAsync("r:" .. p.UserId, function(old: any)
			got = if type(old) == "table" then old else {}
			if #got == 0 then return nil end
			return {}
		end)
	end)
	if ok and #got > 0 then apply(p, got) end
end

-- a fix for one player: now if they're here, else waiting in the store (and a word to their server)
local function deliver(uid: number, fx: any, forceStore: boolean?): boolean
	local p = Players:GetPlayerByUserId(uid)
	if p and dataOf(p) and not forceStore then apply(p, { fx }); return true end
	local store = fixStore
	if not store then return false end
	pcall(function()
		(store :: DataStore):UpdateAsync("r:" .. uid, function(old: any)
			local list = if type(old) == "table" then old else {}
			for _, e in list do if type(e) == "table" and e.k == fx.k then return nil end end
			table.insert(list, fx)
			return list
		end)
	end)
	if PlayConfig.CROSS_SERVER and not studio then
		pcall(function() MessagingService:PublishAsync("JankRankedFix", { u = uid }) end)
	end
	return false
end

-- the anti-cheat session's call when a cheater is CONFIRMED. since = os.time() seconds (nil / 0: the last 14 days).
-- returns { ok, matches, victims, now, queued } or { ok = false, why }. safe to call again: each match restores once
function RankedData.restoreFor(cheaterId: number, since: number?, forceStore: boolean?): any
	local store = logStore
	if type(cheaterId) ~= "number" then return { ok = false, why = "no user id" } end
	if not store then return { ok = false, why = "no DataStore here" } end
	local from = if type(since) == "number" and since > 0 then since else os.time() - RESTORE_DAYS * 86400
	local okI, idx = pcall(function() return (store :: DataStore):GetAsync("u:" .. cheaterId) end)
	if not okI then return { ok = false, why = "couldn't read the match index: " .. tostring(idx) } end
	local out = { ok = true, matches = 0, victims = 0, now = 0, queued = 0 }
	local here: { [Player]: { any } } = {} -- (players in this server: all their fixes at once, so one notice with the total)
	for _, e in (if type(idx) == "table" then idx else {}) do
		if type(e) ~= "table" or (e.t or 0) < from or type(e.k) ~= "string" then continue end
		local rec: any = nil
		pcall(function()
			(store :: DataStore):UpdateAsync("m:" .. e.k, function(old: any)
				rec = nil
				if type(old) ~= "table" or old.restored then return nil end
				old.restored = { by = cheaterId, t = os.time() }
				rec = old
				return old
			end)
		end)
		if not rec or rec.season ~= Ranked.SEASON then continue end
		out.matches += 1
		local cteam = e.team
		for uidS, r in rec.res or {} do
			local uid = tonumber(uidS)
			local lostTo = if rec.ffa then ((type(r.rp) == "number" and r.rp < 0) or (type(r.mmr) == "number" and r.mmr < 0)) else (r.team ~= cteam and r.won == false)
			if uid and uid ~= cheaterId and lostTo then
				local fx = { k = e.k, mode = rec.mode, season = rec.season, by = cheaterId, t = os.time(),
					rp = if type(r.rp) == "number" and r.rp < 0 then -r.rp else 0, mmr = if type(r.mmr) == "number" and r.mmr < 0 then -r.mmr else 0 }
				out.victims += 1
				local p = Players:GetPlayerByUserId(uid)
				if p and dataOf(p) and not forceStore then
					here[p] = here[p] or {}
					table.insert(here[p], fx)
					out.now += 1
				elseif deliver(uid, fx, true) then out.now += 1 else out.queued += 1 end
			end
		end
	end
	for p, list in here do apply(p, list) end
	-- the cheater's own season, voided (now if they're here, else on their next join)
	deliver(cheaterId, { k = ("void:%d:%d"):format(cheaterId, Ranked.SEASON), void = true, season = Ranked.SEASON, t = os.time() }, forceStore)
	return out
end

-- a wrong catch (UNCONFIRM / UNBAN): the accused's voided season back as it was (now if they're here, else on their
-- next join; a void still waiting in the store is applied first, then undone). returns { ok, now } or { ok = false, why }
function RankedData.undoRestore(uid: number, forceStore: boolean?): any
	if type(uid) ~= "number" then return { ok = false, why = "no user id" } end
	local t = os.time()
	local here = deliver(uid, { k = ("unvoid:%d:%d:%d"):format(uid, Ranked.SEASON, t), unvoid = true, season = Ranked.SEASON, t = t }, forceStore)
	if not here and not fixStore then return { ok = false, why = "no DataStore here" } end
	return { ok = true, now = here }
end

-- ------------------------------------------------------------------ the leaderboard
-- (17 Nov: the hub's RANKED regular, Frisk1636, opens it, and so does the Play screen's LEADERBOARD.) this server's
-- placed players by rank points on each ladder (the duels: each player's best mode), the viewer's own ranks, the
-- season and its end. with PlayConfig.CROSS_SERVER on, also a global top 100 per ladder from an OrderedDataStore of rank
-- points: written after every rated match and every restore (a voided season drops out), read at most once a minute
-- per server. that part is OFF and untested until the place is published
local TOP_N = 100
local UserService = game:GetService("UserService")
local function lpOf(q: any): number
	return math.max(0, math.floor(if type(q.lp) == "number" then q.lp else Ranked.ladderOf(q.r)))
end
local topStores: { [string]: OrderedDataStore } = {}
local function topStore(ladder: string): OrderedDataStore?
	if topStores[ladder] then return topStores[ladder] end
	local ok, s = pcall(function()
		return DataStoreService:GetOrderedDataStore(("JankfireRankedTop%s_s%d_%s"):format(if studio then "_studio" else "_v1", Ranked.SEASON, ladder))
	end)
	if ok and s then topStores[ladder] = s; return s end
	return nil
end
-- this player's place on the global lists (their best duels mode, and Party Ranked), or off them when not placed
function RankedData.topWrite(p: Player)
	if not PlayConfig.CROSS_SERVER then return end
	local d = dataOf(p)
	if not d then return end
	local uid = tostring(p.UserId)
	local _, q = Ranked.best(d.modes)
	local pq = d.modes[Ranked.PARTY_KEY]
	local want = {
		duels = if q and q.placed then lpOf(q) else false,
		party = if type(pq) == "table" and pq.placed then lpOf(pq) else false,
	}
	task.spawn(function()
		for ladder, v in want do
			local s = topStore(ladder)
			if s then pcall(function() if v then s:SetAsync(uid, v) else s:RemoveAsync(uid) end end) end
		end
	end)
end
local topCache: { [string]: { t: number, rows: { any } } } = {}
local topBusy: { [string]: boolean } = {}
local function globalTop(ladder: string): { any }?
	if not PlayConfig.CROSS_SERVER then return nil end
	local c = topCache[ladder]
	if (c and os.clock() - c.t < 60) or topBusy[ladder] then return if c then c.rows else nil end
	local s = topStore(ladder)
	if not s then return nil end
	topBusy[ladder] = true
	local ok, page = pcall(function() return (s :: OrderedDataStore):GetSortedAsync(false, TOP_N):GetCurrentPage() end)
	if ok and type(page) == "table" then
		local ids = {}
		for _, e in page do local id = tonumber(e.key); if id then table.insert(ids, id) end end
		local who: { [number]: any } = {}
		pcall(function() for _, u in UserService:GetUserInfosByUserIdsAsync(ids) do who[u.Id] = u end end)
		local rows = {}
		for _, e in page do
			local id = tonumber(e.key)
			local u = if id then who[id] else nil
			local q = { placed = true, lp = tonumber(e.value) or 0, n = Ranked.PLACEMENTS, r = Ranked.START.r }
			table.insert(rows, { id = id, name = if u then u.DisplayName else "?", user = if u then u.Username else nil,
				v = RankedData.view(q :: any, if ladder == "party" then Ranked.PARTY_KEY else nil) })
		end
		c = { t = os.clock(), rows = rows }
		topCache[ladder] = c
	end
	topBusy[ladder] = nil
	return if c then c.rows else nil
end

-- what the leaderboard panel shows. global = also the global lists (only with CROSS_SERVER on)
function RankedData.board(viewer: Player, global: boolean?): any
	local lists = { duels = {}, party = {} }
	for _, p in Players:GetPlayers() do
		local d = dataOf(p)
		if not d then continue end
		local mode, q = Ranked.best(d.modes)
		if mode and q and q.placed then
			table.insert(lists.duels, { id = p.UserId, name = p.DisplayName, user = p.Name, lp = lpOf(q), v = RankedData.view(q, mode) })
		end
		local pq = d.modes[Ranked.PARTY_KEY]
		if type(pq) == "table" and pq.placed then
			table.insert(lists.party, { id = p.UserId, name = p.DisplayName, user = p.Name, lp = lpOf(pq), v = RankedData.view(pq, Ranked.PARTY_KEY) })
		end
	end
	for _, list in lists do
		table.sort(list, function(a, b) if a.lp ~= b.lp then return a.lp > b.lp end return a.name < b.name end)
		for i = #list, TOP_N + 1, -1 do list[i] = nil end
	end
	local views = RankedData.modes(viewer)
	return {
		ok = true,
		season = { n = Ranked.SEASON, name = Ranked.SEASON_NAME, ends = Ranked.SEASON_ENDS, now = os.time() },
		duels = lists.duels, party = lists.party,
		me = { duels = RankedData.summary(viewer), party = views[Ranked.PARTY_KEY], modes = views },
		cross = PlayConfig.CROSS_SERVER,
		global = if global and PlayConfig.CROSS_SERVER then { duels = globalTop("duels"), party = globalTop("party") } else nil,
	}
end

-- ------------------------------------------------------------------ a finished match
-- rate one player in a finished (or left) match. rated = m.rated: { mode, teams = { { { id, r, rd } } } }
-- an FFA match (the classic modes, m.ffa): where this player finished among how many, and every other player as an
-- opponent beaten (placed below), lost to (above) or tied. a leaver finishes last
local function ffaGame(m: any, p: Player, team: number, left: boolean?): (number, number, { any })
	local byId = {}
	local all = 0
	for _, list in m.rated.teams do for _, x in list do byId[x.id] = x; all += 1 end end
	local results = if type(m.results) == "table" then m.results else {}
	local n = math.max(all, #results)
	local place = if left then n elseif type(m.places) == "table" and m.places[team] then m.places[team] else n
	local opps = {}
	local seen = {}
	for _, r in results do
		if r.id ~= p.UserId and type(r.place) == "number" then
			local x = byId[r.id] or { r = Ranked.START.r, rd = Ranked.START.rd }
			table.insert(opps, { r = x.r, rd = x.rd, s = if left then 0 elseif place < r.place then 1 elseif place > r.place then 0 else 0.5 })
			seen[r.id] = true
		end
	end
	for id, x in byId do
		if id ~= p.UserId and not seen[id] then table.insert(opps, { r = x.r, rd = x.rd, s = if left then 0 else 0.5 }) end
	end
	return place, n, opps
end

local function rate(p: Player, m: any, team: number, won: boolean, left: boolean?): any?
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
	local key = rated.rkey or rated.mode -- ("party" for every classic mode: one Party Ranked rating)
	local q = ratingOf(d, key)
	-- (the rd as it stands after idle days, so coming back after a break moves you faster again)
	if (q.last or 0) > 0 then q.rd = Ranked.idle(q, (os.time() - (q.last :: number)) / 86400) end
	local res
	if m.ffa then
		local place, n, opps = ffaGame(m, p, team, left)
		res = Ranked.applyFfa(q, place, n, opps, os.time())
		won = place == 1
	else
		res = Ranked.apply(q, teamR, oppR, oppRd, won, os.time())
	end
	res.mode = rated.mode
	pcall(logMatch, p, d, m, team, won, res) -- (its line in the season's log and the match's record, for a cheat restore)
	res.rank = RankedData.view(q, key)
	-- (what the card animates from; the Rank tables carry the hidden MMR, so they stay here)
	local rb = res.rankBefore
	res.prev = { tier = rb.tier.id, div = rb.div, rp = rb.rp, step = rb.step, placed = rb.placed }
	res.rankBefore, res.rankAfter = nil, nil
	res.season = d.season
	table.insert(d.recent, 1, { t = os.time(), mode = rated.mode, rp = res.delta, mmr = res.mmrDelta, res = if won then "W" else "L" })
	while #d.recent > RECENT do table.remove(d.recent) end
	if s.prof then s.prof.dirty = true end
	publish(p)
	RankedData.topWrite(p)
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
	task.spawn(writeIndex, m) -- (the match's record and everyone's index line: RankedData.restoreFor reads them)
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
	d.log, d.fixed, d.void, d.voidBackup = {}, {}, nil, nil -- (a new season: a new log)
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
	-- (fixes waiting from a cheat restore while they were away: a moment after joining, so the notice reaches their screen)
	task.delay(3, function() if st[p] == s then pcall(pull, p) end end)
	prof.onLost.Event:Connect(function() warn("[jankfire] ranked: " .. p.Name .. "'s save was opened elsewhere") end)
end

local function leave(p: Player)
	local s = st[p]
	if not s then return end
	-- leaving a ranked match before its end: a loss, now
	local im = inRanked[p]
	inRanked[p] = nil
	if im and im.m.phase ~= "over" then pcall(rate, p, im.m, im.team, false, true) end
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
			-- (Party Ranked too, when they have played it: the card shows it as a smaller second badge)
			local d = dataOf(target)
			local q = d and d.modes[Ranked.PARTY_KEY]
			if q and (q.n or 0) > 0 then
				local v = RankedData.view(q, Ranked.PARTY_KEY)
				v.card = true
				card.partyRanked = v
			end
		end)
	end
	Players.PlayerAdded:Connect(function(p) task.spawn(join, p) end)
	for _, p in Players:GetPlayers() do task.spawn(join, p) end
	Players.PlayerRemoving:Connect(leave)
	-- (PlayConfig.CROSS_SERVER only, untested until publish: a restore in another server tells this one to take a
	-- player's fixes now)
	if PlayConfig.CROSS_SERVER and not studio then
		pcall(function()
			MessagingService:SubscribeAsync("JankRankedFix", function(msg: any)
				local u = type(msg.Data) == "table" and tonumber(msg.Data.u)
				local p = u and Players:GetPlayerByUserId(u)
				if p then task.spawn(pull, p) end
			end)
		end)
	end
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
		for _, k in { "r", "rd", "vol", "n", "w", "l", "need", "lp" } do if type(b[k]) == "number" then (q :: any)[k] = b[k] end end
		if type(b.placed) == "boolean" then q.placed = b.placed end
		local s = st[p :: Player]
		if s and s.prof then s.prof.dirty = true end
		publish(p :: Player)
		return RankedData.view(q, a)
	elseif op == "restore" then
		-- (p here is the cheater's user id; a = since; b = true: queue every fix in the store, even for players here)
		return RankedData.restoreFor(p :: any, a, b == true)
	elseif op == "unrestore" then
		-- (p here is the accused's user id; a = true: through the store, even if they're here)
		return RankedData.undoRestore(p :: any, a == true)
	elseif op == "fixes" and fixStore then
		local ok, v = pcall(function() return (fixStore :: DataStore):GetAsync("r:" .. tostring(p)) end)
		return if ok then v else tostring(v)
	elseif op == "pull" and d then
		pull(p :: Player)
		return true
	elseif op == "log" and d then
		return { log = d.log, fixed = d.fixed, void = d.void, backup = d.voidBackup ~= nil }
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
