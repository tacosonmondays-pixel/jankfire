--!strict
-- THE ARCADE CABINET, the server's half (shared/MiniGames.luau). the game itself runs on the player's own screen
-- (MiniArcade.client); the server only knows when a run started, shows its score on the cabinet while it runs, and
-- keeps the per-server high scores, after a sanity check (a score no hand could have made in that time is dropped)
-- the cabinet's attributes: Live (the running score) and Wave, while someone plays. the board is the MiniGames
-- folder's attribute ArcadeBoard: JSON { { n = name, s = score, w = wave } } best first, shared by every cabinet
-- from the client: { op = "start" }, { op = "live", score, wave }, { op = "over", score, wave, kills }
-- back to the client: ("arcade", { op = "rank", rank, best }) after a run (rank nil: not on the board)
-- the ALL-TIME board (the owner, 19 Nov: "add a leaderboard option"): each player's best run, kept in an
-- OrderedDataStore (a Studio test writes to its own store, never the live one), its top ALL_TIME read every
-- ALL_EVERY s into the folder's attribute ArcadeAllTime: JSON { { n = name, s = score } } best first. only a run that
-- passed the sanity check below is written, and only when it beats that player's own best. no rewards
local HttpService = game:GetService("HttpService")
local DataStoreService = game:GetService("DataStoreService")
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

local Arcade = {}
local board: { { n: string, s: number, w: number, u: number } } = {}
local ALL_TIME, ALL_EVERY = 10, 60
local allStore: OrderedDataStore? = nil
pcall(function()
	allStore = DataStoreService:GetOrderedDataStore(if RunService:IsStudio() then "JankArcadeBest_studio" else "JankArcadeBest")
end)
local names: { [number]: string } = {}
local allFolder: Instance? = nil
local function nameOf(uid: number): string
	if names[uid] then return names[uid] end
	local p = Players:GetPlayerByUserId(uid)
	if p then names[uid] = p.DisplayName; return p.DisplayName end
	local ok, n = pcall(function() return Players:GetNameFromUserIdAsync(uid) end)
	names[uid] = if ok and type(n) == "string" then n else "?"
	return names[uid]
end
local function readAllTime()
	local store = allStore
	local f = allFolder
	if not store or not f then return end
	local ok, pages = pcall(function() return store:GetSortedAsync(false, ALL_TIME) end)
	if not ok or not pages then return end
	local out = {}
	for _, e in (pages :: DataStorePages):GetCurrentPage() do
		local uid = tonumber(e.key)
		if uid then table.insert(out, { n = nameOf(uid), s = e.value }) end
	end
	f:SetAttribute("ArcadeAllTime", HttpService:JSONEncode(out))
end
local function saveBest(p: Player, s: number)
	local store = allStore
	if not store then return end
	task.spawn(function()
		pcall(function()
			store:UpdateAsync(tostring(p.UserId), function(old: any): any
				if type(old) == "number" and old >= s then return nil end -- (no change: their best stands)
				return math.floor(s)
			end)
		end)
		readAllTime()
	end)
end

local function publishBoard(T: any)
	local f = T.model.Parent
	if f then f:SetAttribute("ArcadeBoard", HttpService:JSONEncode(board)) end
end

function Arcade.setup(T: any, ctx: any)
	T.g = { run = nil }
	publishBoard(T)
	if not allFolder then
		allFolder = T.model.Parent
		task.spawn(function()
			while allFolder and (allFolder :: Instance).Parent do
				readAllTime()
				task.wait(ALL_EVERY)
			end
		end)
	end
end
function Arcade.canReplaceBot(_T: any): boolean return false end
function Arcade.joined(T: any, _side: string, _p: Player, _ctx: any)
	T.g.run = nil
	T.model:SetAttribute("Live", nil)
	T.model:SetAttribute("Wave", nil)
end
function Arcade.left(T: any, _side: string, _who: any, _ctx: any)
	T.g.run = nil
	T.model:SetAttribute("Live", nil)
	T.model:SetAttribute("Wave", nil)
end

local function num(v: any): number?
	if type(v) ~= "number" or v ~= v or v < 0 or v > 1e9 then return nil end
	return math.floor(v)
end

function Arcade.msg(T: any, p: Player, _side: string, d: any, ctx: any)
	local G = T.g
	local A = ctx.MG.ARCADE
	if d.op == "start" then
		G.run = { t0 = os.clock(), live = 0 }
		T.model:SetAttribute("Live", 0)
		T.model:SetAttribute("Wave", 1)
	elseif d.op == "live" then
		local run = G.run
		if not run or os.clock() - run.live < A.LIVE_EVERY * 0.6 then return end
		run.live = os.clock()
		local s, w = num(d.score), num(d.wave)
		if s then T.model:SetAttribute("Live", s) end
		if w then T.model:SetAttribute("Wave", w) end
	elseif d.op == "over" then
		local run = G.run
		G.run = nil
		T.model:SetAttribute("Live", nil)
		T.model:SetAttribute("Wave", nil)
		if not run then return end
		local s, w, k = num(d.score), num(d.wave), num(d.kills)
		if not s or not w or not k then return end
		local dur = os.clock() - run.t0
		-- what a person could have done in that time
		local okKills = k <= dur * A.MAX_KILLS_PER_S + 4
		local okScore = s <= k * A.MAX_PER_KILL + A.WAVE_BONUS * w * (w + 1) / 2 + 500
		local okWave = w <= k / 2 + 2
		if not (okKills and okScore and okWave) then
			warn(("[MiniArcade] dropped %s's run: %d in %.0f s (%d kills, wave %d)"):format(p.Name, s, dur, k, w))
			ctx.send(p, "arcade", { op = "rank", rank = nil, best = if board[1] then board[1].s else 0 })
			return
		end
		local rank: number? = nil
		if s > 0 then
			-- one line per player: their best
			local mine: number? = nil
			for i, e in board do if e.u == p.UserId then mine = i; break end end
			if mine and board[mine].s >= s then
				rank = nil
			else
				if mine then table.remove(board, mine) end
				local e = { n = p.DisplayName, s = s, w = w, u = p.UserId }
				local at = #board + 1
				for i, x in board do if s > x.s then at = i; break end end
				if at <= A.BOARD then
					table.insert(board, at, e)
					while #board > A.BOARD do table.remove(board) end
					rank = at
				end
			end
		end
		publishBoard(T)
		if s > 0 then saveBest(p, s) end -- (the all-time board: only if it beats their own best)
		ctx.send(p, "arcade", { op = "rank", rank = rank, best = if board[1] then board[1].s else 0 })
	end
end

function Arcade.step(_T: any, _dt: number, _ctx: any) end

return Arcade
