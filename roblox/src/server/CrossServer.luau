--!strict
-- CROSS SERVER: the Play queue across servers (roblox/docs/MATCHMAKING.md section 6). OFF: PlayConfig.CROSS_SERVER is
-- false, and none of this has ever run. teleports and reserved servers don't work in Studio Play solo, so it waits
-- for the place to be published and tested with real players. with the switch off, CrossServer.init does nothing.
--   * a party that finds no match in its own server for HANDOFF s offers a ticket: one entry in a MemoryStore sorted map
--     per queue ("jf_q_ranked:2v2"), sort key = its rating, expiring unless renewed while it searches
--   * one server at a time is the matchmaker (a lock in a MemoryStore hash map, renewed every LOCK_RENEW s). it reads
--     every queue map, forms matches with Queue.form (the same rules as in one server), reserves a server for each
--     (TeleportService:ReserveServer) and writes each ticket's result: { code, team, match }
--   * each server reads its own tickets' results and teleports those parties to the match server, with teleport data
--     { match, team, mode, ranked, rated } (seen by the client: nothing secret in it)
--   * a match server (game.PrivateServerId ~= "" and players arriving with match data) waits up to ARRIVE s for
--     everyone, starts the match through Matches.startQueued, and after it sends everyone back to a public server with
--     their party in the teleport data
--   * an invite to a friend in another server: MessagingService topic "jf_invite" { to, fromName, job }. accepting
--     teleports you to the inviter's server (TeleportToPlaceInstance with its JobId)
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

local JOB = if game.JobId ~= "" then game.JobId else ("studio-" .. HttpService:GenerateGUID(false))
local Matches: any
local onArrive: ((Player, any) -> ())? = nil

function CrossServer.enabled(): boolean
	return PlayConfig.CROSS_SERVER == true
end

local function map(key: string): MemoryStoreSortedMap
	return MemoryStoreService:GetSortedMap("jf_q_" .. key)
end
local results = function(): MemoryStoreHashMap return MemoryStoreService:GetHashMap("jf_results") end
local lockMap = function(): MemoryStoreHashMap return MemoryStoreService:GetHashMap("jf_mm") end

-- ------------------------------------------------------------------ tickets (any server)
-- offer an entry that has searched here for HANDOFF s. members = { { id, r, rd } }
function CrossServer.offer(e: any, members: { any }): string?
	if not CrossServer.enabled() then return nil end
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

local function matchmake()
	for _, mode in PlayConfig.MODES do
		for _, ranked in { false, true } do
			if ranked and not mode.ranked then continue end
			local key = Queue.key(mode.id, ranked)
			local ok, items = pcall(function() return map(key):GetRangeAsync(Enum.SortDirection.Ascending, 100) end)
			if not ok or type(items) ~= "table" then continue end
			local es = {}
			for _, it in items do
				local v = it.value
				table.insert(es, { key = key, mode = mode.id, ranked = ranked, since = os.clock() - (os.time() - (v.since or os.time())),
					size = v.size, rating = v.rating, owner = { id = it.key, v = v }, state = "search" })
			end
			for _ = 1, 4 do
				local teams = Queue.form(es, mode.id, ranked, os.clock())
				if not teams then break end
				local okR, code = pcall(function() return (TeleportService:ReserveServer(game.PlaceId)) end)
				if not okR then break end
				local matchId = HttpService:GenerateGUID(false)
				local rated = { mode = mode.id, teams = {} }
				for t, list in teams do
					rated.teams[t] = {}
					for _, e in list do for _, m in e.owner.v.members do table.insert(rated.teams[t], m) end end
				end
				for t, list in teams do
					for _, e in list do
						e.state = "found"
						pcall(function() results():SetAsync(e.owner.id, { code = code, team = t, match = matchId, mode = mode.id, ranked = ranked, rated = rated }, 120) end)
						pcall(function() map(key):RemoveAsync(e.owner.id) end)
					end
				end
			end
		end
	end
end

-- ------------------------------------------------------------------ moving players
-- send a party's players to a match server
function CrossServer.send(players: { Player }, res: any, party: any)
	local opts = Instance.new("TeleportOptions")
	opts.ReservedServerAccessCode = res.code
	opts:SetTeleportData({ match = res.match, team = res.team, mode = res.mode, ranked = res.ranked, rated = res.rated, party = party })
	local ok, err = pcall(function() TeleportService:TeleportAsync(game.PlaceId, players, opts) end)
	if not ok then warn("[jankfire] cross-server teleport failed: " .. tostring(err)) end
end

-- the match server's side: who has arrived for which match; start once all are in or ARRIVE s have passed
local arrivals: { [string]: { data: any, players: { [number]: { Player } }, t0: number, started: boolean } } = {}
local function arrived(p: Player, data: any)
	if type(data) ~= "table" or type(data.match) ~= "string" then return end
	local a = arrivals[data.match]
	if not a then
		a = { data = data, players = {}, t0 = os.clock(), started = false }
		arrivals[data.match] = a
	end
	local team = math.clamp(tonumber(data.team) or 1, 1, 4)
	a.players[team] = a.players[team] or {}
	table.insert(a.players[team], p)
	if onArrive then (onArrive :: any)(p, data) end
end
local function startArrived()
	for id, a in arrivals do
		if a.started then continue end
		local need, have = 0, 0
		for _, list in a.data.rated.teams do need += #list end
		for _, list in a.players do have += #list end
		if have >= need or os.clock() - a.t0 > CrossServer.ARRIVE then
			a.started = true
			local cfg = PlayConfig.byId[a.data.mode]
			local sides = {}
			for t = 1, #a.data.rated.teams do sides[t] = a.players[t] or {} end
			if cfg then Matches.startQueued(cfg.pad, sides, { queue = "cross:" .. id, ranked = a.data.ranked == true, rated = a.data.rated }) end
		end
	end
end

-- after a cross-server match: everyone back to a public server, their party in the data
local function backHome(m: any)
	if type(m.queue) ~= "string" or string.sub(m.queue, 1, 6) ~= "cross:" then return end
	task.delay((Matches.AFTER or 7) + 0.5, function()
		local all = {}
		for _, list in m.teams do for _, p in list do if p.Parent then table.insert(all, p) end end end
		if #all == 0 then return end
		local opts = Instance.new("TeleportOptions")
		opts:SetTeleportData({ back = true })
		pcall(function() TeleportService:TeleportAsync(game.PlaceId, all, opts) end)
	end)
end

-- ------------------------------------------------------------------ invites across servers
function CrossServer.invite(toUserId: number, fromName: string)
	pcall(function() MessagingService:PublishAsync("jf_invite", { to = toUserId, fromName = fromName, job = JOB }) end)
end

function CrossServer.init(matches: any, hooks: { onInvite: ((Player, any) -> ())?, onArrive: ((Player, any) -> ())? })
	if not CrossServer.enabled() or RunService:IsStudio() then return end
	Matches = matches
	onArrive = hooks.onArrive
	Matches.onEnd(backHome)
	Players.PlayerAdded:Connect(function(p)
		local jd = p:GetJoinData()
		if jd and jd.TeleportData then arrived(p, jd.TeleportData) end
	end)
	pcall(function()
		MessagingService:SubscribeAsync("jf_invite", function(msg)
			local d = msg.Data
			if type(d) ~= "table" then return end
			local p = Players:GetPlayerByUserId(tonumber(d.to) or 0)
			if p and hooks.onInvite then (hooks.onInvite :: any)(p, d) end
		end)
	end)
	task.spawn(function()
		while true do
			if holdLock() then pcall(matchmake) end
			pcall(startArrived)
			task.wait(CrossServer.LOCK_RENEW)
		end
	end)
end

return CrossServer
