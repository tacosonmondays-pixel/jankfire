--!strict
-- THE VICTORY SCENE's server side (27 Nov 2026, shared/VictoryData.luau has the why; plan: side-session-notes
-- .../victory-scene/PLAN.md). At every match's end (Matches.onEnd) everyone in the match gets one message on
-- JankfireRemotes.Victory:
--   { t = "scene", id, scene (play the default scene), cine (a finisher's cinematic plays instead: wait for it), len,
--     winner (team, nil = nobody), youWon, team (yours), mode, classic, ranked, arena, wins = { per team },
--     board = Scoreboard.board (the Tab board's own counts: K/D/A/DMG or a classic mode's two columns),
--     stage = { { uid, name, emote, front } } (the winning side best first: the one in front, then up to V.MATES),
--     front = uid, spot = the map's own victory spot (world CFrames, nil = THE RISER: VictoryScene's fallback set),
--     finisher = { by, vs, fid } when one plays }
-- ONE RANKING (V.better: kills, damage, assists, fewest deaths, the lower UserId; classic modes their own result order
-- first) picks the one in front, the teammates, and the cinematic: the best-ranked winner with a scene finisher
-- equipped plays theirs against the enemy side's best (the owner: "the person who did the best has theirs play against
-- the enemy best because weapon finishers are usualy duels"), through FinisherServer's Matches.endFinisher (pick /
-- play, the finishers session's). Players who left are skipped: the next best takes the place.
-- The end screen (Matches.endScreen, the client's stats card) waits on m.finisherUntil: with no cinematic this sets it
-- to the scene's length (+ slack) and brings it in when every viewer has reported the scene done or skipped
-- ({ t = "done" } back on the same remote). A cinematic's hold is FinisherServer's own. Nobody goes home mid-scene:
-- backToHub and CrossServer.backHome come after the end screen.
-- THE MAP'S SPOT: a Model named "Victory" anywhere inside the arena (a copy carries it): Parts Hero, Mate1-3 (floor
-- points, LookVector = facing), lens keys RiseA, RiseB, WideA, WideB (+ optional LoseA, LoseB, Hold): Position = the
-- lens, LookVector = where it looks, attribute Fov; optional Lights (switched on on screen during the scene).
-- Studio only: ServerStorage.JankVictoryTest (BindableFunction):
--   ("fake", player, { { name, look = userId, mine = bool, k, d, a, dmg, emote }, ... })  pretend players in the
--       player's next match end: ranked with everyone, on the stage when their side wins, on the card's board. their
--       bodies are built from `look` (Players:CreateHumanoidModelFromUserId) into ReplicatedStorage.JankVictoryLooks
--   ("clear", player)   ("state")   the last message's summary and the live holds   ("spot", arenaName) the spot read
--   ("pick", player)   the finisher FinisherServer says this player would bring (Matches.endFinisher.pick)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")

local Jankfire = script.Parent
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local V = require(Shared:WaitForChild("VictoryData")) :: any
local Matches = require(Jankfire:WaitForChild("Matches")) :: any
local Scoreboard = require(Jankfire:WaitForChild("Scoreboard")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local remote = Remotes:FindFirstChild("Victory") :: RemoteEvent?
if not remote then
	local r = Instance.new("RemoteEvent")
	r.Name = "Victory"
	r.Parent = Remotes
	remote = r
end
local R = remote :: RemoteEvent

-- the match-end cinematic is ours to call now (FinisherServer's old match-winning-kill cut stays off while this is set)
if V.ON then Matches.victoryLive = true end
task.spawn(function()
	local fm = Jankfire:WaitForChild("FinisherVictory", 60)
	if fm and fm:IsA("ModuleScript") and V.ON then
		local ok, FV = pcall(require, fm)
		if ok and type(FV) == "table" then (FV :: any).ON = true end
	end
end)

local watching: { [any]: { [Player]: boolean } } = setmetatable({}, { __mode = "k" }) :: any
local fakes: { [Player]: { any } } = {} -- (Studio tests)
local last: any = nil -- (Studio tests: the last message's summary)

local function teamOf(m: any, p: Player): number?
	for t, list in m.teams do if table.find(list, p) then return t end end
	return nil
end
local function everyone(m: any): { Player }
	local out = {}
	for _, list in m.teams do for _, p in list do if p.Parent then table.insert(out, p) end end end
	return out
end

-- the board's rows by uid, numbers named: { uid, name, k, d, a, dmg, team }
local function rowsOf(board: any): { [number]: any }
	local out = {}
	if type(board) ~= "table" or type(board.teams) ~= "table" then return out end
	local cols = board.cols or {}
	local kda = cols[1] == "K" and cols[4] == "DMG"
	for _, side in board.teams do
		for _, r in side.rows or {} do
			if type(r.uid) == "number" and r.uid ~= 0 and type(r.v) == "table" then
				out[r.uid] = { uid = r.uid, name = r.name, team = side.t,
					k = tonumber(r.v[1]) or 0, d = tonumber(r.v[2]) or 0,
					a = if kda then tonumber(r.v[3]) or 0 else 0, dmg = if kda then tonumber(r.v[4]) or 0 else 0 }
			end
		end
	end
	return out
end

-- everyone still here, split into the winning side and the rest, each best first: { uid, name, p?, k, d, a, dmg, order? }
local function sidesOf(m: any, winner: number?, rows: { [number]: any }, fk: { any }): ({ any }, { any })
	local won, lost = {}, {}
	local order: { [Player]: number } = {}
	local firstPlace: { [Player]: boolean } = {}
	if m.rules and type(m.results) == "table" then
		for i, r in m.results do
			if typeof(r.player) == "Instance" then
				order[r.player] = i
				if r.place == 1 then firstPlace[r.player] = true end
			end
		end
	end
	for t, list in m.teams do
		for _, p in list do
			if not p.Parent then continue end
			local r = rows[p.UserId] or {}
			local row = { uid = p.UserId, name = r.name or p.DisplayName, p = p, k = r.k or 0, d = r.d or 0, a = r.a or 0, dmg = r.dmg or 0,
				order = order[p] }
			local isWin = winner ~= nil and (if m.rules and next(firstPlace) then firstPlace[p] == true else t == winner)
			table.insert(if isWin then won else lost, row)
		end
	end
	-- (Studio tests: pretend players, ranked with everyone; no Player, so never a finisher's killer or victim)
	for _, x in fk do
		local ownerWon = false
		for _, w in won do if w.p == x.owner then ownerWon = true end end
		local mine = x.mine ~= false
		local row = { uid = x.look, name = x.name, emote = x.emote, k = x.k or 0, d = x.d or 0, a = x.a or 0, dmg = x.dmg or 0, fake = true }
		if winner ~= nil and mine == ownerWon then table.insert(won, row) else table.insert(lost, row) end
	end
	return V.rank(won), V.rank(lost)
end

-- the map's own victory spot, in world space (nil: the client uses THE RISER)
local function lens(v: Instance, name: string): any?
	local p = v:FindFirstChild(name)
	if not (p and p:IsA("BasePart")) then return nil end
	return { at = p.Position, look = p.Position + p.CFrame.LookVector * 30, fov = tonumber(p:GetAttribute("Fov")) or 40 }
end
local function spotIn(site: Instance?): any?
	local v = site and site:FindFirstChild("Victory", true)
	if not (v and v:IsA("Model")) then return nil end
	local function floor(name: string): CFrame?
		local p = v:FindFirstChild(name)
		if not (p and p:IsA("BasePart")) then return nil end
		return p.CFrame * CFrame.new(0, -p.Size.Y / 2, 0)
	end
	local hero = floor("Hero")
	local s: any = { hero = hero, mates = {}, rise = { lens(v, "RiseA"), lens(v, "RiseB") }, wide = { lens(v, "WideA"), lens(v, "WideB") },
		hold = lens(v, "Hold"), lose = { lens(v, "LoseA"), lens(v, "LoseB") }, lights = v:FindFirstChild("Lights") }
	if not hero or not (s.rise[1] and s.rise[2] and s.wide[1] and s.wide[2]) then return nil end
	for i = 1, 3 do
		local c = floor("Mate" .. i)
		if c then table.insert(s.mates, c) end
	end
	if not (s.lose[1] and s.lose[2]) then s.lose = nil end
	return s
end

-- the hold: the end screen comes when every viewer is done, or at the cap
local function release(m: any)
	watching[m] = nil
	if m.victoryHold and type(m.finisherUntil) == "number" then m.finisherUntil = math.min(m.finisherUntil, os.clock() + 0.3) end
end

local function onEnd(m: any, winner: number?)
	if not V.ON then return end
	local t0 = os.clock()
	-- the hold goes on NOW (Matches.endMatch starts waiting on it right after its hooks): the default scene's length,
	-- unless a finisher's hold is already on (FinisherServer's old cut, before Matches.victoryLive reached it)
	local held = false
	if winner and not (type(m.finisherUntil) == "number" and m.finisherUntil > t0) then
		m.finisherUntil = t0 + V.LEN + V.SLACK
		m.victoryHold = true
		held = true
	end
	-- the rest after every other end hook has run
	task.defer(function()
		local all = everyone(m)
		if #all == 0 then return end
		local okB, board = pcall(Scoreboard.board, all[1])
		if not okB or type(board) ~= "table" then board = nil end
		-- (Studio tests: pretend players on the board)
		local fk = {}
		for _, p in all do
			for _, x in fakes[p] or {} do
				local y = table.clone(x); y.owner = p
				table.insert(fk, y)
				if board then
					local t = teamOf(m, p) or 1
					local side = if x.mine ~= false then t else (if t == 1 then 2 else 1)
					for _, s in board.teams do
						if s.t == side then table.insert(s.rows, { name = x.name, uid = x.look, v = { x.k or 0, x.d or 0, x.a or 0, x.dmg or 0 } }) end
					end
				end
			end
		end
		local rows = rowsOf(board)
		local won, lost = sidesOf(m, winner, rows, fk)
		-- the cinematic: the best winner with a scene finisher, against the enemy's best still here
		local cine, finisher = false, nil
		local EF = Matches.endFinisher
		if winner and type(EF) == "table" and type(EF.pick) == "function" and type(EF.play) == "function" then
			for _, w in won do
				if not w.p or not w.p.Parent then continue end
				local okP, fid = pcall(EF.pick, w.p, m)
				if not okP or not fid then continue end
				local tries = 0
				for _, l in lost do
					if not l.p or not l.p.Parent then continue end
					tries += 1
					local okPlay, ok, why = pcall(EF.play, m, w.p, l.p)
					print(("[jankfire] Victory: finisher %s, %s vs %s: %s (%s)"):format(tostring(fid), w.p.Name, l.p.Name, tostring(okPlay and ok), tostring(why)))
					if okPlay and ok then cine = true; finisher = { by = w.uid, vs = l.uid, fid = fid }; break end
					if tries >= 2 then break end
				end
				break -- (the best winner with one: theirs or nothing)
			end
		end
		-- (belt and braces: FinisherServer's old match-winning-kill cut, if it still ran)
		if not cine and type(m.finisherFrom) == "number" and t0 - m.finisherFrom < V.CINE_WINDOW then cine = true end
		if cine and held then m.victoryHold = nil end -- (the cinematic's hold took over: its viewers' reports end it)
		local stage = {}
		for i, w in won do
			if i > 1 + V.MATES then break end
			table.insert(stage, { uid = w.uid, name = w.name, front = i == 1 or nil,
				emote = w.emote or (w.p and V.emoteOf(w.p:GetAttribute("Emotes"))) or nil })
		end
		local scene = winner ~= nil and not cine and #stage > 0
		if not scene and not cine and m.victoryHold then
			m.victoryHold = nil
			m.finisherUntil = math.min(m.finisherUntil or 0, os.clock() + 0.1) -- (a draw or nobody to show: the card at once)
		end
		local spot = spotIn(m.site and m.site.model)
		local wins = {}
		for t, n in m.wins or {} do wins[t] = n end
		local msg = {
			t = "scene", id = m.id, scene = scene, cine = cine, len = V.LEN, winner = winner, mode = tostring(m.mode or ""),
			classic = m.rules ~= nil, ranked = m.ranked == true, arena = tostring(m.arena or ""), wins = wins, board = board,
			stage = stage, front = if stage[1] then stage[1].uid else nil, spot = spot, finisher = finisher,
			ffa = m.ffa == true or (board and board.ffa) or nil,
		}
		local set = {}
		for _, p in all do
			local mm = table.clone(msg)
			mm.team = teamOf(m, p)
			mm.youWon = winner ~= nil and mm.team == winner
			if m.rules and type(m.places) == "table" and mm.team then mm.youWon = m.places[mm.team] == 1 and winner ~= nil end
			R:FireClient(p, mm)
			if scene then set[p] = true end
		end
		if scene and m.victoryHold then watching[m] = set end
		last = { id = m.id, mode = msg.mode, winner = winner, scene = scene, cine = cine, finisher = finisher, front = msg.front,
			stage = #stage, spot = spot ~= nil, hold = if type(m.finisherUntil) == "number" then m.finisherUntil - os.clock() else nil, at = os.clock() }
		print(("[jankfire] Victory: match %s %s, winner %s, front %s, %d on stage, %s, hold %.1f s"):format(tostring(m.id),
			if cine then "cinematic" elseif scene then "scene" else "card only", tostring(winner), tostring(msg.front), #stage,
			if spot then "map spot" else "the riser", (m.finisherUntil or os.clock()) - os.clock()))
	end)
end
Matches.onEnd(onEnd)

R.OnServerEvent:Connect(function(p: Player, msg: any)
	if type(msg) ~= "table" or msg.t ~= "done" then return end
	for m, set in watching do
		if set[p] then
			set[p] = nil
			if next(set) == nil then release(m) end
		end
	end
end)
Players.PlayerRemoving:Connect(function(p)
	fakes[p] = nil
	for m, set in watching do
		set[p] = nil
		if next(set) == nil then release(m) end
	end
end)

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankVictoryTest)
if RunService:IsStudio() then
	local old = ServerStorage:FindFirstChild("JankVictoryTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankVictoryTest"
	local function looks(): Folder
		local f = ReplicatedStorage:FindFirstChild("JankVictoryLooks") :: Folder?
		if not f then
			local n = Instance.new("Folder")
			n.Name = "JankVictoryLooks"
			n.Parent = ReplicatedStorage
			f = n
		end
		return f :: Folder
	end
	fn.OnInvoke = function(op: string, a: any, b: any): any
		if op == "fake" and typeof(a) == "Instance" and a:IsA("Player") and type(b) == "table" then
			local list = {}
			for _, x in b do
				if type(x) == "table" and type(x.look) == "number" then
					table.insert(list, x)
					local folder = looks()
					if not folder:FindFirstChild(tostring(x.look)) then
						local ok, model = pcall(function() return Players:CreateHumanoidModelFromUserId(x.look) end)
						if ok and model then
							model.Name = tostring(x.look)
							model.Archivable = true
							model.Parent = folder
						else
							warn("[jankfire] victory test: no look for " .. tostring(x.look) .. ": " .. tostring(model))
						end
					end
				end
			end
			fakes[a] = list
			return "ok " .. #list
		elseif op == "clear" and typeof(a) == "Instance" then
			fakes[a :: Player] = nil
			return "cleared"
		elseif op == "pick" and typeof(a) == "Instance" and a:IsA("Player") then
			-- (the finisher this player would bring at a match end: FinisherServer's own answer)
			local EF = Matches.endFinisher
			if type(EF) ~= "table" then return "no Matches.endFinisher" end
			local ok, fid, skin, w = pcall(EF.pick, a, Matches.raw(a))
			return { ok = ok, fid = fid, skin = skin, w = w }
		elseif op == "spot" then
			local map = workspace:FindFirstChild("Map")
			local s = spotIn(map and map:FindFirstChild(tostring(a)))
			return if s then { hero = s.hero, mates = #s.mates, lose = s.lose ~= nil, lights = s.lights ~= nil } else "no spot"
		elseif op == "state" then
			local holds = {}
			for m, set in watching do
				local n = 0
				for _ in set do n += 1 end
				table.insert(holds, { id = m.id, viewers = n, left = (m.finisherUntil or 0) - os.clock() })
			end
			return { last = last, holds = holds, on = V.ON, victoryLive = Matches.victoryLive, endFinisher = type(Matches.endFinisher) == "table" }
		end
		return "ops: fake, clear, pick, spot, state"
	end
	fn.Parent = ServerStorage
end
