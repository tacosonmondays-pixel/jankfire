--!strict
-- CROSS SERVER: the Play queue across servers (roblox/docs/MATCHMAKING.md section 6). ON since 17 Nov 2026 (the owner:
-- "can you also enable cross matchmaking"), with PlayConfig.CROSS_SERVER. Real teleports and reserved servers can't run
-- in Studio, so the live check waits for the owner's publish (the doc lists what to check).
--   * a party that finds no match in its own server for HANDOFF s also offers a ticket, and keeps searching at home
--     (Party.luau's crossTick): one entry in a MemoryStore sorted map per queue ("jf_q_ranked:2v2"), sort key = its
--     rating, expiring unless renewed while it searches. whichever finds a match first wins; a party matched at home
--     takes its ticket back
--   * one server at a time is the matchmaker (a lock in a MemoryStore hash map, renewed every LOCK_RENEW s). it reads
--     the duel queues and QUICKPLAY's, forms matches with Queue.form (the same rules as in one server), reserves a
--     server for each (TeleportService:ReserveServer) and writes each ticket's result: { code, team, match, mode,
--     ranked, rated }. a QUICKPLAY match can't vote across servers: the matchmaker draws its mode (PlayConfig.
--     QUICK_WEIGHT, a team mode only when the parties split into two sides) and the map is the rotation's
--   * each server reads its own tickets' results and teleports those parties to the match server, with teleport data
--     { match, team, mode, ranked, rated } (seen by the client: nothing secret in it). a teleport that fails (an error
--     now, TeleportInitFailed later, or the players simply still here AWAY s on) puts the party back in its own
--     server's queue with a note: Party.luau
--   * a match server (players arriving with match data) waits up to ARRIVE s for everyone, starts the match (a duel
--     through Matches.startQueued, a classic mode through its own start), and after it sends everyone back to a public
--     server. a side that never arrives, or a match that won't start, sends everyone back at once with a note, so
--     nobody is left in an empty private server
--   * an invite to a friend in another server: MessagingService topic "jf_invite" { to, fromName, job }
--   * any memory store call that fails is skipped: the party simply searches at home
-- Studio: its own map names ("jfs_" in place of "jf_"), so a play test never touches the live queues; nothing runs
-- unless a test switches it on: CrossServer.test below (PlayServer's JankPlayTest "cross...")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local TeleportService = game:GetService("TeleportService")
local MessagingService = game:GetService("MessagingService")
local MemoryStoreService = game:GetService("MemoryStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))
local Queue = require(script.Parent:WaitForChild("Queue"))

local CrossServer = {}
CrossServer.HANDOFF = 20 -- s of searching in this server before a ticket goes out
CrossServer.TICKET_TTL = 30 -- s a ticket lives without renewal
CrossServer.LOCK_RENEW = 5
CrossServer.ARRIVE = 30 -- s a match server waits for its players
CrossServer.AWAY = 20 -- s a party sent to a match server may still be here before it searches at home again

local STUDIO = RunService:IsStudio()
local NS = if STUDIO then "jfs_" else "jf_"
local JOB = if game.JobId ~= "" then game.JobId else ("studio-" .. HttpService:GenerateGUID(false))
local Matches: any
local hooks: any = {}
local studioOn = false -- (Studio: a test switched it on)

function CrossServer.enabled(): boolean
	return PlayConfig.CROSS_SERVER == true
end
-- (Party.luau) does this server take part right now? live: when the switch is on. Studio: only in a test
function CrossServer.active(): boolean
	return CrossServer.enabled() and (not STUDIO or studioOn)
end

local function map(key: string): MemoryStoreSortedMap
	return MemoryStoreService:GetSortedMap(NS .. "q_" .. key)
end
local results = function(): MemoryStoreHashMap return MemoryStoreService:GetHashMap(NS .. "results") end
local lockMap = function(): MemoryStoreHashMap return MemoryStoreService:GetHashMap(NS .. "mm") end

-- the queues that go across servers: every duel, and QUICKPLAY. (a PARTY card pick, filled from quickplay, stays in
-- its own server)
function CrossServer.crossable(mode: string): boolean
	local m: any = PlayConfig.byId[mode]
	return m ~= nil and (mode == PlayConfig.QUICKPLAY or m.ladder ~= "party")
end

-- ------------------------------------------------------------------ tickets (any server)
-- offer an entry that has searched here for HANDOFF s. members = { { id, r, rd } }
function CrossServer.offer(e: any, members: { any }): string?
	if not CrossServer.active() then return nil end
	local id = HttpService:GenerateGUID(false)
	local ok = pcall(function()
		map(e.key):SetAsync(id, { job = JOB, size = e.size, rating = e.rating, since = os.time(), members = members }, CrossServer.TICKET_TTL, e.rating)
	end)
	return if ok then id else nil
end
function CrossServer.renew(key: string, id: string, e: any, members: { any })
	pcall(function()
		map(key):SetAsync(id, { job = JOB, size = e.size, rating = e.rating, since = os.time(), members = members }, CrossServer.TICKET_TTL, e.rating)
	end)
end
function CrossServer.withdraw(key: string, id: string)
	pcall(function() map(key):RemoveAsync(id) end)
end
-- this server's ticket's result, once the matchmaker has written one: { code, team, match, mode, ranked, rated }
function CrossServer.result(id: string): any?
	local ok, v = pcall(function() return results():GetAsync(id) end)
	return if ok then v else nil
end

-- ------------------------------------------------------------------ the matchmaker (one server at a time)
local function holdLock(): boolean
	local mine = false
	pcall(function()
		lockMap():UpdateAsync("lock", function(old: any)
			if old == nil or old.job == JOB or os.time() - (old.t or 0) > CrossServer.LOCK_RENEW * 3 then
				mine = true
				return { job = JOB, t = os.time() }
			end
			mine = false
			return nil
		end, CrossServer.LOCK_RENEW * 4)
	end)
	return mine
end

-- QUICKPLAY across servers: the mode the matchmaker draws for the parties it formed, and the sides for it (a team
-- mode: the parties split into two; anything else: each party its own side, as at home)
local function quickPick(teams: { { any } }): (string?, { { any } }?)
	local es = {}
	for _, list in teams do for _, e in list do table.insert(es, e) end end
	local n = 0
	for _, e in es do n += e.size end
	local fits: { { id: string, teams: { { any } } } } = {}
	for _, m in PlayConfig.classic() do
		local lo, hi = PlayConfig.counts(m.id)
		if n >= lo and n <= hi then
			if (m :: any).sides == 2 then
				local split = Queue.split(es :: any, PlayConfig.PARTY_MAX)
				if split then table.insert(fits, { id = m.id, teams = split :: any }) end
			else
				table.insert(fits, { id = m.id, teams = teams })
			end
		end
	end
	if #fits == 0 then return nil, nil end
	local sum = 0
	for _, f in fits do sum += PlayConfig.QUICK_WEIGHT[f.id] or 1 end
	local r = math.random() * sum
	for _, f in fits do
		r -= PlayConfig.QUICK_WEIGHT[f.id] or 1
		if r <= 0 then return f.id, f.teams end
	end
	return fits[#fits].id, fits[#fits].teams
end

-- one pass over every queue. reserve(): a reserved server's access code (Studio tests pass a stand-in)
local function matchmake(reserve: () -> string?): { any }
	local made = {}
	local keys: { { key: string, mode: string, ranked: boolean } } = {}
	for _, mode in PlayConfig.MODES do
		table.insert(keys, { key = Queue.key(mode.id, false), mode = mode.id, ranked = false })
		if mode.ranked then table.insert(keys, { key = Queue.key(mode.id, true), mode = mode.id, ranked = true }) end
	end
	table.insert(keys, { key = Queue.key(PlayConfig.QUICKPLAY, false), mode = PlayConfig.QUICKPLAY, ranked = false })
	table.insert(keys, { key = Queue.key(PlayConfig.QUICKPLAY, true), mode = PlayConfig.QUICKPLAY, ranked = true })
	for _, k in keys do
		local key, ranked = k.key, k.ranked
		local ok, items = pcall(function() return map(key):GetRangeAsync(Enum.SortDirection.Ascending, 100) end)
		if not ok or type(items) ~= "table" or #items == 0 then continue end
		local es = {}
		for _, it in items do
			local v = it.value
			if type(v) ~= "table" then continue end
			table.insert(es, { key = key, mode = k.mode, ranked = ranked, since = os.clock() - (os.time() - (v.since or os.time())),
				size = v.size, rating = v.rating, owner = { id = it.key, v = v }, state = "search" })
		end
		for _ = 1, 4 do
			local teams = Queue.form(es :: any, k.mode, ranked, os.clock())
			if not teams then break end
			local modeId = k.mode
			if modeId == PlayConfig.QUICKPLAY then
				local pickId, sides = quickPick(teams :: any)
				if not pickId or not sides then
					-- (nothing fits that head-count: they stay in their queues, out of this pass)
					for _, list in teams do for _, e in list do (e :: any).state = "found" end end
					continue
				end
				modeId, teams = pickId, sides :: any
			end
			local code = reserve()
			if not code then break end
			local matchId = HttpService:GenerateGUID(false)
			local rated = { mode = modeId, rkey = PlayConfig.ratingKey(modeId), teams = {} }
			local n = 0
			for t, list in teams do
				rated.teams[t] = {}
				for _, e in list do
					n += 1
					for _, m in (e :: any).owner.v.members do table.insert(rated.teams[t], m) end
				end
			end
			-- (one party alone is never rated: friends could farm each other)
			local isRanked = ranked and n >= 2
			-- (the match server reads the match from here, not from the teleport data, which passes through clients)
			pcall(function() results():SetAsync("m:" .. matchId, { mode = modeId, ranked = isRanked, rated = rated }, 300) end)
			for t, list in teams do
				for _, e in list do
					(e :: any).state = "found"
					local tid = (e :: any).owner.id
					pcall(function() results():SetAsync(tid, { code = code, team = t, match = matchId, mode = modeId, ranked = isRanked, rated = rated }, 120) end)
					pcall(function() map(key):RemoveAsync(tid) end)
				end
			end
			table.insert(made, { match = matchId, mode = modeId, ranked = isRanked, sides = #teams, entries = n })
		end
	end
	return made
end

-- ------------------------------------------------------------------ moving players
-- send a party's players to a match server. true = the teleport is on its way (it can still fail later:
-- TeleportInitFailed, hooks.onTeleportFailed)
function CrossServer.send(players: { Player }, res: any, party: any): (boolean, string?)
	if STUDIO then return false, "Studio has no teleports" end
	local opts = Instance.new("TeleportOptions")
	opts.ReservedServerAccessCode = res.code
	opts:SetTeleportData({ match = res.match, team = res.team, mode = res.mode, ranked = res.ranked, rated = res.rated, party = party })
	local ok, err = pcall(function() TeleportService:TeleportAsync(game.PlaceId, players, opts) end)
	if not ok then warn("[jankfire] cross-server teleport failed: " .. tostring(err)) end
	return ok, if ok then nil else tostring(err)
end

-- back to a public server (after a match, or when one can't be played), a few tries
local function sendHome(list: { Player }, note: string?)
	local all = {}
	for _, p in list do if p.Parent then table.insert(all, p) end end
	if #all == 0 then return end
	if note and hooks.notify then for _, p in all do pcall(hooks.notify, p, note) end end
	if STUDIO then return end
	task.spawn(function()
		for try = 1, 3 do
			local left = {}
			for _, p in all do if p.Parent then table.insert(left, p) end end
			if #left == 0 then return end
			local opts = Instance.new("TeleportOptions")
			opts:SetTeleportData({ back = true })
			local ok = pcall(function() TeleportService:TeleportAsync(game.PlaceId, left, opts) end)
			task.wait(if ok then 15 else 3 * try)
		end
	end)
end

-- the match server's side: who has arrived for which match; start once all are in or ARRIVE s have passed
type Arrival = { data: any, players: { [number]: { Player } }, t0: number, started: boolean }
local arrivals: { [string]: Arrival } = {}
local function arrived(p: Player, data: any)
	if type(data) ~= "table" or type(data.match) ~= "string" then return end
	-- (teleport data passes through the player's client: only the match id is taken from it. the mode, the sides and
	-- the ratings are the matchmaker's own record, and the side is the one this player is listed on)
	local id = data.match
	local a = arrivals[id]
	if not a then
		local ok, rec = pcall(function() return results():GetAsync("m:" .. id) end)
		if not ok or type(rec) ~= "table" or type(rec.rated) ~= "table" or type(rec.rated.teams) ~= "table" then
			sendHome({ p }, "that match is gone: back to a public server")
			return
		end
		a = arrivals[id] -- (another arrival may have made it while this one waited)
		if not a then
			a = { data = rec, players = {}, t0 = os.clock(), started = false }
			arrivals[id] = a
		end
	end
	local arr = a :: Arrival
	local team: number? = nil
	for t, list in arr.data.rated.teams do
		for _, m in list do if m.id == p.UserId then team = t end end
	end
	if not team or arr.started then
		sendHome({ p }, if arr.started then "that match has started: back to a public server" else "you're not in that match: back to a public server")
		return
	end
	arr.players[team] = arr.players[team] or {}
	table.insert(arr.players[team], p)
	if hooks.onArrive then pcall(hooks.onArrive, p, arr.data) end
end
local function everyone(a: Arrival): { Player }
	local out = {}
	for _, list in a.players do for _, p in list do table.insert(out, p) end end
	return out
end
local function startArrived(): { any }
	local out = {}
	for id, a in arrivals do
		if a.started then continue end
		local need, have = 0, 0
		for _, list in a.data.rated.teams do need += #list end
		for _, list in a.players do for _, p in list do if p.Parent then have += 1 end end end
		if have < need and os.clock() - a.t0 <= CrossServer.ARRIVE then continue end
		a.started = true
		local cfg: any = PlayConfig.byId[a.data.mode]
		local sides = {}
		local missing = false
		for t = 1, #a.data.rated.teams do
			local list = {}
			for _, p in a.players[t] or {} do if p.Parent then table.insert(list, p) end end
			sides[t] = list
			if #list == 0 then missing = true end
		end
		local m, why = nil, nil
		if not cfg then
			why = "unknown mode"
		elseif missing then
			why = "a side never arrived"
		else
			local opts = { queue = "cross:" .. id, ranked = a.data.ranked == true, rated = a.data.rated }
			local okS, r1, r2 = pcall(function()
				if type(cfg.start) == "function" then return cfg.start(sides, opts) end
				return Matches.startQueued(cfg.pad, sides, opts)
			end)
			if okS then m, why = r1, r2 else why = tostring(r1) end
		end
		table.insert(out, { match = id, started = m ~= nil, why = why })
		if not m then sendHome(everyone(a), "the match couldn't start: back to a public server") end
		task.delay(300, function() arrivals[id] = nil end)
	end
	return out
end

-- after a cross-server match: everyone back to a public server
local function backHome(m: any)
	if type(m.queue) ~= "string" or string.sub(m.queue, 1, 6) ~= "cross:" then return end
	task.delay((Matches.AFTER or 7) + 0.5, function()
		local all = {}
		for _, list in m.teams do for _, p in list do table.insert(all, p) end end
		sendHome(all, nil)
	end)
end

-- ------------------------------------------------------------------ invites across servers
function CrossServer.invite(toUserId: number, fromName: string)
	if not CrossServer.active() then return end
	pcall(function() MessagingService:PublishAsync("jf_invite", { to = toUserId, fromName = fromName, job = JOB }) end)
end

-- hooks = { onInvite?, onArrive?, onTeleportFailed? (Player) -> (), notify? (Player, text) -> () }
function CrossServer.init(matches: any, h: any)
	Matches = matches
	hooks = h or {}
	if not CrossServer.enabled() or STUDIO then return end
	Matches.onEnd(backHome)
	local function joined(p: Player)
		local jd = p:GetJoinData()
		if jd and jd.TeleportData then arrived(p, jd.TeleportData) end
	end
	Players.PlayerAdded:Connect(joined)
	for _, p in Players:GetPlayers() do task.spawn(joined, p) end
	TeleportService.TeleportInitFailed:Connect(function(p: Player, result: Enum.TeleportResult, msg: string)
		warn(("[jankfire] cross-server teleport of %s failed: %s %s"):format(p.Name, tostring(result), tostring(msg)))
		if hooks.onTeleportFailed then pcall(hooks.onTeleportFailed, p) end
	end)
	pcall(function()
		MessagingService:SubscribeAsync("jf_invite", function(msg)
			local d = msg.Data
			if type(d) ~= "table" then return end
			local p = Players:GetPlayerByUserId(tonumber(d.to) or 0)
			if p and hooks.onInvite then pcall(hooks.onInvite, p, d) end
		end)
	end)
	task.spawn(function()
		while true do
			if holdLock() then pcall(matchmake, function(): string?
				local ok, code = pcall(function() return (TeleportService:ReserveServer(game.PlaceId)) end)
				return if ok then code else nil
			end) end
			pcall(startArrived)
			task.wait(CrossServer.LOCK_RENEW)
		end
	end)
end

-- ------------------------------------------------------------------ Studio tests (PlayServer's JankPlayTest "cross...")
--   ("on") / ("off")              this server takes part (Studio maps "jfs_", no teleports: a send fails, which is the
--                                 fall-back to test)
--   ("handoff", secs)             how long a party searches at home before its ticket goes out
--   ("ticket", key, size, rating) a ticket from "another server" in queue key ("casual:1v1")
--   ("peek", key)                 the tickets in that queue
--   ("mm")                        one matchmaker pass, with stand-in reserved-server codes; what it made
--   ("result", ticketId)          a ticket's result
--   ("arrive", player, data)      that player arrives as if teleported with data; ("start") the arrivals' check now,
--                                 ARRIVE taken as passed
function CrossServer.test(op: string, a: any, b: any, c: any): any
	if not STUDIO then return nil end
	if op == "on" then studioOn = true; return CrossServer.active()
	elseif op == "off" then studioOn = false; return false
	elseif op == "handoff" then CrossServer.HANDOFF = tonumber(a) or 20; return CrossServer.HANDOFF
	elseif op == "ticket" then
		local id = "stand-" .. HttpService:GenerateGUID(false)
		local r = tonumber(c) or 1500
		local ok, err = pcall(function()
			map(tostring(a)):SetAsync(id, { job = "studio-other", size = tonumber(b) or 1, rating = r, since = os.time(),
				members = { { id = -900 - math.random(99), r = r, rd = 90 } } }, CrossServer.TICKET_TTL, r)
		end)
		return { ok = ok, id = id, err = if ok then nil else tostring(err) }
	elseif op == "peek" then
		local ok, items = pcall(function() return map(tostring(a)):GetRangeAsync(Enum.SortDirection.Ascending, 100) end)
		if not ok then return { err = tostring(items) } end
		local out = {}
		for _, it in items do table.insert(out, { id = it.key, job = it.value and it.value.job, size = it.value and it.value.size }) end
		return out
	elseif op == "mm" then
		local n = 0
		local ok, made = pcall(matchmake, function(): string? n += 1; return "studio-code-" .. n end)
		return if ok then made else { err = tostring(made) }
	elseif op == "result" then
		return CrossServer.result(tostring(a))
	elseif op == "arrive" and typeof(a) == "Instance" and a:IsA("Player") then
		arrived(a, b)
		return true
	elseif op == "start" then
		for _, x in arrivals do x.t0 = -math.huge end
		return startArrived()
	end
	return nil
end

return CrossServer
