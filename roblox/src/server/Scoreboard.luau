--!strict
-- THE MATCH SCOREBOARD's server side (21 Nov 2026, the owner: "when you press tab in match I want it to pull upa
-- coreboard"). The client (client/Scoreboard.client.luau, drawn by client/ScoreboardUI.luau) asks through the remote
-- JankfireRemotes.Scoreboard ("board") about once a second while it is open; the answer is the asker's own match:
--   { mode, ranked, ffa, cols = { "K", "D", "A", "DMG" } (or a classic mode's own two), teams = { { t, name, wins,
--     rows = { { name, uid, v = { numbers in cols order }, ping, rank = a RankedData view (ranked only), empty } } } } }
-- kills and deaths are the fighters' own (Matches zeroes them at the start); damage dealt to the other sides and assists
-- (you hurt them in the ASSIST s before someone else killed them, as weapon mastery counts one) are counted here, per
-- match, from Fight's hurt and kill hooks. A classic mode's board and columns are its rules' own (Modes.luau), as on its
-- end screen. Ping is Roblox's own measure of the player's round trip. Works the same on a cross-server match server.
-- Studio only: ServerStorage.JankBoardTest (BindableFunction):
--   ("fake", player, { { name, team, k, d, a, dmg, ping }, ... })  pretend players filling the empty seats of the
--                                                                    player's match (photos of a full board)
--   ("board", player)                                                the board the player would get
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")

local Scoreboard = {}
Scoreboard.ASSIST = 10 -- s (Shared.Mastery's ASSIST_WINDOW)

local Matches: any = nil
local Fight: any = nil
local RankedData: any = nil
local TeamColors = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("TeamColors")) :: any

type Tally = { dmg: { [Player]: number }, ast: { [Player]: number } }
local tallies: { [any]: Tally } = setmetatable({}, { __mode = "k" }) :: any
local hurtBy: { [any]: { [Player]: number } } = setmetatable({}, { __mode = "k" }) :: any -- victim fighter -> attacker -> when
local fakes: { [any]: { any } } = setmetatable({}, { __mode = "k" }) :: any -- (Studio tests)

local function tally(m: any): Tally
	local t = tallies[m]
	if not t then t = { dmg = {}, ast = {} }; tallies[m] = t end
	return t
end
local function teamIn(m: any, p: Player): number?
	for t, list in m.teams do if table.find(list, p) then return t end end
	return nil
end

-- ------------------------------------------------------------------ the counts
local function onHurt(v: any, hp: number, by: any?)
	if not by or by == v or by.kind ~= "player" or v.kind ~= "player" or type(hp) ~= "number" or hp <= 0 then return end
	local a, b = by.ref :: Player, v.ref :: Player
	local m = Matches.raw(a)
	if not m or Matches.raw(b) ~= m then return end
	local ta, tb = teamIn(m, a), teamIn(m, b)
	if not ta or ta == tb then return end
	local t = tally(m)
	t.dmg[a] = (t.dmg[a] or 0) + hp
	local hb = hurtBy[v] or {}
	hurtBy[v] = hb
	hb[a] = os.clock()
end
local function onKill(info: any)
	local v, k = info.v, info.k
	if not v then return end
	local hb = hurtBy[v]
	hurtBy[v] = nil
	if not hb or v.kind ~= "player" then return end
	local m = Matches.raw(v.ref)
	if not m then return end
	local killer = if k and k.kind == "player" then k.ref else nil
	local tv = teamIn(m, v.ref)
	local t = tally(m)
	for a, at in hb do
		if a ~= killer and os.clock() - at <= Scoreboard.ASSIST and Matches.raw(a) == m and teamIn(m, a) ~= tv then
			t.ast[a] = (t.ast[a] or 0) + 1
		end
	end
end

-- ------------------------------------------------------------------ the board
local function pingOf(p: Player): number?
	local ok, s = pcall(function() return p:GetNetworkPing() end)
	return if ok and type(s) == "number" then math.floor(s * 1000 + 0.5) else nil
end
local function rankOf(m: any, p: Player): any?
	if not m.ranked or not RankedData then return nil end
	local ok, views = pcall(RankedData.modes, p)
	if not ok or type(views) ~= "table" then return nil end
	return views[m.mode] or views.party
end
local function nameOf(p: Player): string
	local f = Fight.byPlayer[p]
	return if f and type(f.name) == "string" then f.name else p.DisplayName
end

function Scoreboard.board(p: Player): any?
	local m = Matches.raw(p)
	if not m then return nil end
	local t = tally(m)
	local rules = m.rules
	local cols: { string } = { "K", "D", "A", "DMG" }
	local byUid: { [number]: { any } } = {}
	if rules then
		local okC, c = pcall(rules.cols, m)
		cols = if okC and type(c) == "table" then c else { "KILLS", "DEATHS" }
		local okB, rows = pcall(rules.board, m)
		if okB and type(rows) == "table" then
			for _, r in rows do if type(r[4]) == "number" then byUid[r[4]] = { r[2], r[3] } end end
		end
	end
	local size = tonumber(string.match(tostring(m.mode), "^(%d+)v")) or 0
	local most = 0
	for _, list in m.teams do most = math.max(most, #list) end
	-- (free-for-all: one list. every side of one (1V1V1, a four-way), or a classic mode that puts everyone on one side)
	local ffa = #m.teams <= 1 or (#m.teams >= 3 and most <= 1 and size <= 1)
	local teams = {}
	local fk = fakes[m] or {}
	for ti, list in m.teams do
		local name = TeamColors.name(ti)
		if rules and rules.label then
			local okL, l = pcall(rules.label, m, ti)
			if okL and type(l) == "string" then name = l end
		end
		local rows = {}
		for _, q in list do
			if not q.Parent then continue end
			local f = Fight.byPlayer[q]
			local v
			if rules then
				local r = byUid[q.UserId]
				v = if r then { r[1], r[2] } else { f and f.kills or 0, f and f.deaths or 0 }
			else
				v = { f and f.kills or 0, f and f.deaths or 0, t.ast[q] or 0, math.floor((t.dmg[q] or 0) + 0.5) }
			end
			table.insert(rows, { name = nameOf(q), uid = q.UserId, v = v, ping = pingOf(q), rank = rankOf(m, q) })
		end
		-- (Studio tests: pretend players in this side's empty seats)
		for _, x in fk do
			if x.team == ti then
				table.insert(rows, { name = x.name, uid = 0, v = if rules then { x.k or 0, x.d or 0 } else { x.k or 0, x.d or 0, x.a or 0, x.dmg or 0 }, ping = x.ping, rank = if m.ranked then { unranked = true, ladder = "duels" } else nil })
			end
		end
		-- the empty seats of a side whose players left (not a classic mode's: it has no seats)
		if not rules then for _ = #rows + 1, size do table.insert(rows, { empty = true }) end end
		table.insert(teams, { t = ti, name = name, wins = m.wins and m.wins[ti] or 0, rows = rows })
	end
	return { mode = string.upper(tostring(m.mode)), ranked = m.ranked == true, ffa = ffa, cols = cols, round = m.round, teams = teams }
end

-- ------------------------------------------------------------------ init
function Scoreboard.init(fight: any, matches: any, rankedData: any?)
	Fight, Matches, RankedData = fight, matches, rankedData
	Fight.onHurt(onHurt)
	Fight.onKill(onKill)
	local remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
	local fn = remotes:FindFirstChild("Scoreboard") :: RemoteFunction?
	if not fn then
		local r = Instance.new("RemoteFunction")
		r.Name = "Scoreboard"
		r.Parent = remotes
		fn = r
	end
	local last: { [Player]: number } = {}
	;(fn :: RemoteFunction).OnServerInvoke = function(p: Player, op: unknown): any
		if op ~= "board" then return nil end
		local n = os.clock()
		if last[p] and n - last[p] < 0.25 then return false end -- (the client asks once a second; too soon: false, it keeps what it shows)
		last[p] = n
		local ok, res = pcall(Scoreboard.board, p)
		if not ok then warn("[jankfire] scoreboard: " .. tostring(res)); return nil end
		return res
	end
	Players.PlayerRemoving:Connect(function(p) last[p] = nil end)
	if RunService:IsStudio() then
		local old = ServerStorage:FindFirstChild("JankBoardTest")
		if old then old:Destroy() end
		local t = Instance.new("BindableFunction")
		t.Name = "JankBoardTest"
		t.OnInvoke = function(op: string, a: any, b: any): any
			if op == "fake" and typeof(a) == "Instance" and a:IsA("Player") then
				local m = Matches.raw(a)
				if not m then return "not in a match" end
				fakes[m] = if type(b) == "table" then b else nil
				return true
			elseif op == "board" and typeof(a) == "Instance" and a:IsA("Player") then
				return Scoreboard.board(a)
			end
			return nil
		end
		t.Parent = ServerStorage
	end
end

return Scoreboard
