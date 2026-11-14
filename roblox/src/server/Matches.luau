--!strict
-- the hub (Workspace.Map.Hub) and its queue pads, Rivals-style. you spawn in the hub; walk back through the door behind
-- the spawn for the training room (its dummies shoot back in there, nowhere else). on the pads in front: stand on a
-- side; when every side is full a 3 s countdown runs, then everyone on it goes to the Rooftop arena for a match:
-- rounds of one life each, last team standing takes the round, first to Matches.WIN rounds wins, then back to the hub.
-- a round nobody wins outright (time up, or the last ones go down together) goes to whoever dealt the most damage in
-- it, then whoever has the most HP left, then a coin flip (nobody shot anybody): there are no draws
-- there's one arena, so one match at a time: a full pad waits for it ("ARENA BUSY").
-- other players can't hurt you in the hub or the training room; in a match only the other teams can
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local RoundR = Remotes:WaitForChild("Round") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent

local Matches = {}
Matches.WIN = 5 -- round wins that take the match
Matches.ROUND_TIME = 120 -- s; time up = the most damage dealt takes it (then HP left, then a coin flip)
Matches.COUNTDOWN = 3 -- s on a full pad before you go
Matches.READY = 3 -- s from spawning in to the round going live (no damage till then)
Matches.BETWEEN = 3 -- s between rounds
Matches.AFTER = 7 -- s on the end screen, then back to the hub

local TEAM_NAMES = { "PINK", "CYAN", "YELLOW" }
local TEAM_HEX = { "#ff4fd8", "#37d6ff", "#ffe14d" }

type Fighter = any
type Match = {
	id: number, mode: string, teams: { { Player } }, wins: { number }, round: number,
	phase: string, -- "ready" (spawned, not live yet) | "live" | "between" | "over"
	roundEnds: number, pad: Model, fighters: { Fighter },
	dmg: { number }, -- damage each team dealt to the others this round
}

local Fight: any
local hub: Instance
local current: Match? = nil
local inMatch: { [Player]: { m: Match, team: number } } = {}
local lastZone: { [Player]: string } = {}
local padCount: { [Model]: number? } = {} -- when a full pad's countdown ends
local nextId = 0

-- ------------------------------------------------------------------ where you are
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then return nil end
	return ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
end
local function inside(part: BasePart, pos: Vector3, up: number): boolean
	local rel = part.CFrame:PointToObjectSpace(pos)
	local h = part.Size / 2
	return math.abs(rel.X) <= h.X + 0.5 and math.abs(rel.Z) <= h.Z + 0.5 and rel.Y > -h.Y - 1 and rel.Y < h.Y + up
end
function Matches.zoneOf(p: Player): string
	if inMatch[p] then return "match" end
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local tz = hub:FindFirstChild("TrainingZone") :: BasePart?
	if root and tz and inside(tz, root.Position, 4) then return "training" end
	return "hub"
end

-- ------------------------------------------------------------------ the hooks Fight asks
-- may `by` hurt `t`? (nil / yourself = a fall: always)
function Matches.allow(by: Fighter?, t: Fighter): boolean
	if not by or by == t then return true end
	if t.kind == "dummy" then return true end -- anyone can hit a dummy
	local tp = t.ref :: Player
	if by.kind == "dummy" then return Matches.zoneOf(tp) == "training" end -- the dummies only shoot back in their room
	local a, b = inMatch[by.ref :: Player], inMatch[tp]
	return a ~= nil and b ~= nil and a.m == b.m and a.m.phase == "live" and a.team ~= b.team
end

local function markers(name: string): { BasePart }
	local f = hub:FindFirstChild(name)
	local out = {}
	if f then for _, c in f:GetChildren() do if c:IsA("BasePart") then table.insert(out, c) end end end
	return out
end

-- the arena's spawns per team: attackers' end, defenders' end, and (1v1v1) the middle
local function teamSpawns(team: number): { CFrame }
	local map = workspace:FindFirstChild("Map")
	local roof = map and map:FindFirstChild("Rooftop")
	local out = {}
	if roof then
		local ts = roof:FindFirstChild("TeamSpawns")
		local want = if team == 1 then "att" elseif team == 2 then "def" else nil
		if ts and want then
			for _, s in ts:GetChildren() do
				if s:IsA("BasePart") and s.Name == want then table.insert(out, CFrame.lookAt(s.Position, Vector3.new(0, s.Position.Y, s.Position.Z))) end
			end
		else
			local sp = roof:FindFirstChild("Spawns")
			for _, n in { "Spawn11", "Spawn18", "Spawn14", "Spawn12", "Spawn13" } do
				local s = sp and sp:FindFirstChild(n) :: BasePart?
				if s then table.insert(out, CFrame.lookAt(s.Position + Vector3.new(0, 0.1, 0), Vector3.new(s.Position.X + 1, s.Position.Y, s.Position.Z))) end
			end
		end
	end
	if #out == 0 then table.insert(out, CFrame.new(team * 30, 5, 0)) end
	return out
end

local function spawnAt(f: Fighter): (Vector3, Vector3?)
	local p = f.ref :: Player
	local im = inMatch[p]
	if im then
		local list = teamSpawns(im.team)
		local i = table.find(im.m.teams[im.team], p) or 1
		local cf = list[(i - 1) % #list + 1]
		return cf.Position, cf.LookVector
	end
	local list = markers(if lastZone[p] == "training" then "TrainSpawns" else "HubSpawns")
	if #list == 0 then list = markers("HubSpawns") end
	if #list == 0 then return (hub:GetAttribute("Origin") :: Vector3) + Vector3.new(0, 3, 0), nil end
	local s = list[math.random(#list)]
	return s.Position, s.CFrame.LookVector
end

-- ------------------------------------------------------------------ the HUD line (the client draws it)
local function hudText(m: Match): string
	local score = {}
	for t = 1, #m.teams do table.insert(score, ('<font color="%s">%d</font>'):format(TEAM_HEX[t], m.wins[t])) end
	return ("%s · ROUND %d · %s"):format(m.mode, m.round, table.concat(score, " – "))
end
local function each(m: Match, fn: (Player, number) -> ())
	for t, list in m.teams do for _, p in list do if p.Parent then fn(p, t) end end end
end
local function setHud(m: Match)
	local txt = hudText(m)
	each(m, function(p) p:SetAttribute("MatchHud", txt); p:SetAttribute("RoundEnds", if m.phase == "live" then workspace:GetServerTimeNow() + (m.roundEnds - os.clock()) else nil) end)
end
local function callAll(m: Match, text: string, dur: number)
	each(m, function(p) CalloutR:FireClient(p, text, dur) end)
end
local function teamLabel(m: Match, t: number): string
	-- a 1-person team is that person; a bigger one is its colour
	local list = m.teams[t]
	if #list == 1 and list[1].Parent then return list[1].DisplayName end
	return TEAM_NAMES[t]
end

-- ------------------------------------------------------------------ rounds
local startRound: (Match) -> ()

local function backToHub(m: Match)
	each(m, function(p)
		inMatch[p] = nil
		lastZone[p] = "hub"
		p:SetAttribute("Team", nil); p:SetAttribute("MatchHud", nil); p:SetAttribute("RoundEnds", nil)
		RoundR:FireClient(p, { hub = true })
		local f = Fight.byPlayer[p]
		if f then f.alive = false; task.spawn(Fight.spawn, f) end
	end)
	for p, im in inMatch do if im.m == m then inMatch[p] = nil end end
	if current == m then current = nil end
end

local function endMatch(m: Match, winner: number?)
	if m.phase == "over" then return end
	m.phase = "over"
	setHud(m)
	local board = Fight.board(m.fighters)
	local name = if winner then teamLabel(m, winner) else nil
	each(m, function(p, t)
		RoundR:FireClient(p, { over = true, winner = name, youWon = winner == t, board = board, next = Matches.AFTER, nextLabel = "back to the hub in %d" })
	end)
	task.delay(Matches.AFTER, backToHub, m)
end

-- teams with someone still standing
local function standing(m: Match): { number }
	local out = {}
	for t, list in m.teams do
		for _, p in list do
			local f = Fight.byPlayer[p]
			if f and f.alive and p.Parent then table.insert(out, t); break end
		end
	end
	return out
end

local function teamsLeft(m: Match): { number }
	local out = {}
	for t, list in m.teams do
		for _, p in list do if p.Parent and inMatch[p] then table.insert(out, t); break end end
	end
	return out
end

-- who takes a round nobody won outright, out of `cands` (team numbers): the most damage dealt, then the most HP left,
-- then a coin flip. returns the team and how it was decided ("damage" | "hp" | "coin"). pure, so it can be tested
function Matches.pickWinner(cands: { number }, dmg: { number }, hp: { number }, rand: (number) -> number): (number, string)
	local best, top = {}, -1
	for _, t in cands do
		local d = dmg[t] or 0
		if d > top then top, best = d, { t } elseif d == top then table.insert(best, t) end
	end
	if #best == 1 then return best[1], "damage" end
	local hpBest, hpTop = {}, -1
	for _, t in best do
		local h = hp[t] or 0
		if h > hpTop then hpTop, hpBest = h, { t } elseif h == hpTop then table.insert(hpBest, t) end
	end
	if #hpBest == 1 then return hpBest[1], "hp" end
	return hpBest[rand(#hpBest)], "coin"
end

local function checkRound(m: Match)
	if current ~= m or m.phase == "over" then return end
	-- everyone else left: the last team in wins outright
	local left = teamsLeft(m)
	if #left <= 1 then endMatch(m, left[1]); return end
	if m.phase ~= "live" then return end
	local alive = standing(m)
	local timeUp = os.clock() >= m.roundEnds
	if #alive > 1 and not timeUp then return end
	local winner: number
	local how = "kill"
	if #alive == 1 then
		winner = alive[1]
	else -- time up with several standing, or the last ones went down together: no draws
		local cands = if #alive > 1 then alive else left
		local hp = {}
		for _, t in cands do
			local s = 0
			for _, p in m.teams[t] do local f = Fight.byPlayer[p]; if f and f.alive then s += math.max(0, f.hp) end end
			hp[t] = s
		end
		winner, how = Matches.pickWinner(cands, m.dmg, hp, math.random)
	end
	m.phase = "between"
	m.wins[winner] += 1
	setHud(m)
	if m.wins[winner] >= Matches.WIN then
		callAll(m, teamLabel(m, winner) .. " WINS THE MATCH", 2)
		task.delay(1.2, endMatch, m, winner)
		return
	end
	local name = teamLabel(m, winner)
	local head = if timeUp then "TIME" else "DOUBLE KO"
	local shot = false
	for _, d in m.dmg do if d > 0 then shot = true end end
	callAll(m, if how == "kill" then name .. " TAKES THE ROUND"
		elseif how == "damage" then ("%s · %s DID MORE DAMAGE"):format(head, name)
		elseif how == "hp" then ("%s · %s HAS MORE HP"):format(head, name)
		elseif shot then ("DEAD EVEN · COIN FLIP · %s"):format(name)
		else ("NOBODY SHOT · COIN FLIP · %s"):format(name), 2.2)
	task.delay(Matches.BETWEEN, function() if current == m and m.phase == "between" then startRound(m) end end)
end

startRound = function(m: Match)
	m.round += 1
	m.phase = "ready"
	for t = 1, #m.teams do m.dmg[t] = 0 end
	setHud(m)
	-- a fresh body for everyone at their end (alive or not)
	each(m, function(p)
		local f = Fight.byPlayer[p]
		if f then f.alive = false; task.spawn(Fight.spawn, f) end
	end)
	task.delay(0.6, function()
		if current ~= m then return end
		each(m, function(p, t) CalloutR:FireClient(p, ("ROUND %d · you're %s"):format(m.round, TEAM_NAMES[t]), 1.6) end)
	end)
	task.delay(Matches.READY, function()
		if current ~= m or m.phase ~= "ready" then return end
		m.phase = "live"
		-- (test knob: a TestRoundTime attribute on this module, set on the running server, shortens rounds in a playtest)
		m.roundEnds = os.clock() + ((script:GetAttribute("TestRoundTime") :: number?) or Matches.ROUND_TIME)
		setHud(m)
		each(m, function(p) RoundR:FireClient(p, { start = true }) end)
	end)
end

local function startMatch(pad: Model, sides: { { Player } })
	nextId += 1
	local teams = {}
	for t, list in sides do teams[t] = table.clone(list) end
	local wins = {}
	for t = 1, #teams do wins[t] = 0 end
	local m: Match = { id = nextId, mode = pad:GetAttribute("Mode") :: string, teams = teams, wins = wins, round = 0, phase = "ready", roundEnds = 0, pad = pad, fighters = {}, dmg = {} }
	current = m
	each(m, function(p, t)
		inMatch[p] = { m = m, team = t }
		p:SetAttribute("Team", t)
		local f = Fight.byPlayer[p]
		if f then
			table.insert(m.fighters, f)
			f.kills, f.deaths, f.kat = 0, 0, 0
			p:SetAttribute("Kills", 0); p:SetAttribute("Deaths", 0); p:SetAttribute("Kat", 0)
		end
	end)
	startRound(m)
end

-- ------------------------------------------------------------------ the pads
local function padSign(pad: Model, status: string, sub: string)
	local sign = pad:FindFirstChild("Sign")
	local gui = sign and sign:FindFirstChild("Gui")
	if not gui then return end
	local s, b = gui:FindFirstChild("Status") :: TextLabel?, gui:FindFirstChild("Sub") :: TextLabel?
	if s and s.Text ~= status then s.Text = status end
	if b and b.Text ~= sub then b.Text = sub end
end

local function padStep()
	local pads = hub:FindFirstChild("QueuePads")
	if not pads then return end
	local claimed: { [Player]: boolean } = {}
	for _, pad in pads:GetChildren() do
		if not pad:IsA("Model") then continue end
		local teams, size = pad:GetAttribute("Teams") :: number, pad:GetAttribute("Size") :: number
		local sides: { { Player } } = {}
		for t = 1, teams do sides[t] = {} end
		for _, p in Players:GetPlayers() do
			if inMatch[p] or claimed[p] then continue end
			local root = rootOf(p)
			if not root then continue end
			for t = 1, teams do
				local side = pad:FindFirstChild("Side" .. t) :: BasePart?
				if side and inside(side, root.Position, 8) then
					claimed[p] = true
					if #sides[t] < size then table.insert(sides[t], p) end
					break
				end
			end
		end
		local full = true
		local counts = {}
		for t = 1, teams do
			if #sides[t] < size then full = false end
			table.insert(counts, ('<font color="%s">%d/%d</font>'):format(TEAM_HEX[t], #sides[t], size))
		end
		-- the slot rings light up as people step on
		for _, r in pad:GetChildren() do
			if r.Name == "Slot" and r:IsA("BasePart") then
				local t, s = r:GetAttribute("Team") :: number, r:GetAttribute("Slot") :: number
				local want = if sides[t] and #sides[t] >= s then 0 else 0.55
				if r.Transparency ~= want then r.Transparency = want end
			end
		end
		local sub = "step on a side to queue"
		if full then
			if current then
				padCount[pad] = nil
				sub = "ARENA BUSY · you're next"
			else
				local at = padCount[pad] or (os.clock() + Matches.COUNTDOWN)
				padCount[pad] = at
				if os.clock() >= at then
					padCount[pad] = nil
					startMatch(pad, sides)
					sub = "GO!"
				else
					sub = ("STARTING IN %d"):format(math.ceil(at - os.clock()))
				end
			end
		else
			padCount[pad] = nil
			if current and current.pad == pad then sub = "match on · " .. hudText(current):gsub("<[^>]+>", "") end
		end
		padSign(pad, table.concat(counts, "   vs   "), sub)
	end
end

-- ------------------------------------------------------------------ wiring
function Matches.init(fight: any)
	Fight = fight
	hub = workspace:WaitForChild("Map"):WaitForChild("Hub")
	Fight.allow = Matches.allow
	Fight.spawnAt = spawnAt
	Fight.holdRespawn = function(f: Fighter): boolean
		local p = f.ref :: Player
		return inMatch[p] ~= nil
	end
	Fight.onKill(function(info)
		local v = info.v
		if v.kind ~= "player" then return end
		local im = inMatch[v.ref :: Player]
		if im then task.defer(checkRound, im.m) end
	end)
	-- damage dealt to the other teams in a live round (what decides a round nobody wins outright)
	Fight.onHurt(function(t, done, by)
		if not by or by == t or by.kind ~= "player" or t.kind ~= "player" then return end
		local a, b = inMatch[by.ref :: Player], inMatch[t.ref :: Player]
		if a and b and a.m == b.m and a.team ~= b.team and a.m.phase == "live" then
			a.m.dmg[a.team] = (a.m.dmg[a.team] or 0) + done
		end
	end)
	Players.PlayerRemoving:Connect(function(p)
		local im = inMatch[p]
		inMatch[p] = nil
		lastZone[p] = nil
		if im then
			local list = im.m.teams[im.team]
			local i = table.find(list, p)
			if i then table.remove(list, i) end
			task.defer(checkRound, im.m)
		end
	end)
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 0.15 then return end
		acc = 0
		for _, p in Players:GetPlayers() do
			local z = Matches.zoneOf(p)
			if p:GetAttribute("Zone") ~= z then p:SetAttribute("Zone", z) end
			local f = Fight.byPlayer[p]
			if f and f.alive and z ~= "match" then
				lastZone[p] = z
				-- out of the hub somehow (a fling through a gap): straight back
				local root = rootOf(p)
				local origin = hub:GetAttribute("Origin") :: Vector3
				if root and origin and root.Position.Y < origin.Y - 60 then Fight.void(f) end
			end
		end
		padStep()
		if current then checkRound(current) end
	end)
end

return Matches
