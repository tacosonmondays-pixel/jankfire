--!strict
-- the hub (Workspace.Map.Hub: THE LANES, a bowling alley) and its queue pads, Rivals-style. you spawn in the hub; the red
-- door in its west wall is the way to the training room (its dummies shoot back in there, nowhere else). on the pads in
-- front, one on each lane's approach: stand on a
-- side; when every side is full a 3 s countdown runs, then everyone on it goes to the arena for a match (that pad's
-- next one in the rotation, workspace.Map's ArenaPool: Arena.luau; its name is the first banner):
-- rounds of one life each, last team standing takes the round, first to Matches.WIN rounds wins, then back to the hub.
-- a round nobody wins outright (time up, or the last ones go down together) goes to whoever dealt the most damage in
-- it, then whoever has the most HP left, then a coin flip (nobody shot anybody): there are no draws
-- matches run side by side (16 Nov 2026, more pads in the hub, the way big duel games do it): every live match has its
-- own "site", the picked arena itself when no other match is in it, else a copy of it far out along x
-- (Arena.copyOffset). a pad takes its site when its countdown starts (so a copy has reached every screen before anyone
-- lands in it) and gives it back Matches.CLEAR s after its players are home: a copy is then cleared, its water too
-- (JankWater). at most Matches.MAX_LIVE sites at once (no streaming: a v2 copy is ~4,600 parts on every screen); past
-- that a full pad waits ("ALL ARENAS BUSY") and the pad that filled first goes first.
-- other players can't hurt you in the hub or the training room; in a match only the other teams can
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

-- the arenas (the Rooftop v1, v2 or v3), the rotation (workspace.Map's ArenaPool) and where copies go
local Arena = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Arena"))
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
Matches.CLEAR = 3 -- s after a match's players are back in the hub, its site is free again (a copy is cleared)
Matches.MAX_LIVE = 6 -- sites in use at once (live matches and counting-down pads; the arenas themselves count)

local TEAM_NAMES = { "PINK", "CYAN", "YELLOW" }
local TEAM_HEX = { "#ff4fd8", "#37d6ff", "#ffe14d" }

type Fighter = any
-- where a match is played: an arena under workspace.Map, or a copy of one in Map.ArenaCopies
type Site = { name: string, model: Model, copy: boolean, slot: number }
type Match = {
	id: number, mode: string, teams: { { Player } }, wins: { number }, round: number,
	phase: string, -- "ready" (spawned, not live yet) | "live" | "between" | "over"
	roundEnds: number, pad: Model, fighters: { Fighter },
	dmg: { number }, -- damage each team dealt to the others this round
	arena: string, -- the arena's name ("RooftopV2"): its banner and its light
	site: Site, -- where it is played: that arena, or a copy of it
	on: boolean, -- false once its players are back in the hub
	ghost: number?, -- (Studio tests only: a match with nobody in it, over at this os.clock(): Matches.test)
}

local Fight: any
local hub: Instance
local live: { Match } = {} -- the matches being played, oldest first
local inMatch: { [Player]: { m: Match, team: number } } = {}
local lastZone: { [Player]: string } = {}
-- a full pad's countdown and the site it holds (lost: when the pad stopped being full, if it has)
local padCount: { [Model]: { at: number, site: Site, arena: string, lost: number? } } = {}
local fullSince: { [Model]: number } = {} -- when each full pad filled (the first to fill gets the next free site)
local lastArena: { [Model]: string } = {} -- each pad's last arena (none yet after a server starts: the first pick is random)
local padLast: { [Model]: Match } = {} -- each pad's latest match (its sign shows it)
local busy: { [Model]: boolean } = {} -- the sites in use
local copySlots: { [string]: { [number]: Model } } = {} -- each arena's copies by slot (Arena.copyOffset)
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
	-- the playground (a secret, off through the training hall): its own zone, so its own look, and weapons work there
	local pz = hub:FindFirstChild("PlaygroundZone") :: BasePart?
	if root and pz and inside(pz, root.Position, 4) then return "playground" end
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

-- ------------------------------------------------------------------ sites (an arena, or a copy, per live match)
local function sitesInUse(): number
	local n = 0
	for _ in busy do n += 1 end
	return n
end
local function maxLive(): number
	-- (test knob: a TestMaxLive attribute on this module, set on the running server, lowers the cap in a playtest)
	local t = script:GetAttribute("TestMaxLive")
	return if type(t) == "number" then t else Matches.MAX_LIVE
end
local function copiesFolder(): Instance
	local map = workspace:WaitForChild("Map")
	local f = map:FindFirstChild("ArenaCopies")
	if not f then
		f = Instance.new("Folder")
		f.Name = "ArenaCopies"
		f.Parent = map -- (inside Map: the map-only raycasts, Fight.castMap and the clients', see the copies)
	end
	return f :: Instance
end
-- a site in arena `name`: the arena itself if no match is in it, else a new copy. nil at the cap, or when the arena
-- isn't built or can't be copied (v1)
local function claimSite(name: string): Site?
	if sitesInUse() >= maxLive() then return nil end
	local map = workspace:FindFirstChild("Map")
	local arena = map and map:FindFirstChild(name)
	if not arena or not arena:IsA("Model") then return nil end
	if not busy[arena] then
		busy[arena] = true
		return { name = name, model = arena, copy = false, slot = 0 }
	end
	if Arena.NO_COPY[name] then return nil end
	local slots = copySlots[name] or {}
	copySlots[name] = slots
	local k = 1
	while slots[k] do k += 1 end
	local c = arena:Clone()
	local off = Arena.copyOffset(k)
	c:PivotTo(arena:GetPivot() + off) -- (before it is parented: JankWater fills the pool where the copy lands)
	local cx = arena:GetAttribute("CentreX")
	c:SetAttribute("CentreX", (if type(cx) == "number" then cx else 0) + off.X)
	c:SetAttribute("CopyOf", name)
	c.Name = ("%s_copy%d"):format(name, k)
	c.Parent = copiesFolder()
	slots[k] = c
	busy[c] = true
	return { name = name, model = c, copy = true, slot = k }
end
local function releaseSite(s: Site)
	if not busy[s.model] then return end
	busy[s.model] = nil
	if s.copy then
		local slots = copySlots[s.name]
		if slots and slots[s.slot] == s.model then slots[s.slot] = nil end
		s.model:Destroy()
	end
end

-- the site's spawns per team: attackers' end, defenders' end, and (1v1v1) the middle
local function teamSpawns(m: Match, team: number): { CFrame }
	local roof = m.site.model
	local cx = Arena.centreX(roof)
	local out = {}
	local ts = roof:FindFirstChild("TeamSpawns")
	local want = if team == 1 then "att" elseif team == 2 then "def" else nil
	if ts and want then
		for _, s in ts:GetChildren() do
			if s:IsA("BasePart") and s.Name == want then table.insert(out, CFrame.lookAt(s.Position, Vector3.new(cx, s.Position.Y, s.Position.Z))) end
		end
	else
		local sp = roof:FindFirstChild("Spawns")
		for _, n in { "Spawn11", "Spawn18", "Spawn14", "Spawn12", "Spawn13" } do
			local s = sp and sp:FindFirstChild(n) :: BasePart?
			if s then table.insert(out, CFrame.lookAt(s.Position + Vector3.new(0, 0.1, 0), Vector3.new(s.Position.X + 1, s.Position.Y, s.Position.Z))) end
		end
	end
	if #out == 0 then table.insert(out, CFrame.new(roof:GetPivot().Position + Vector3.new(team * 30, 5, 0))) end
	return out
end

-- the fall line under a player: their match's site's, else the default arena's (Main's "into the smog")
function Matches.killY(p: Player): number
	local im = inMatch[p]
	return Arena.killY(if im then im.m.site.model else nil)
end

local function spawnAt(f: Fighter): (Vector3, Vector3?)
	local p = f.ref :: Player
	local im = inMatch[p]
	if im then
		local list = teamSpawns(im.m, im.team)
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
		p:SetAttribute("Team", nil); p:SetAttribute("MatchHud", nil); p:SetAttribute("RoundEnds", nil); p:SetAttribute("Arena", nil)
		RoundR:FireClient(p, { hub = true })
		local f = Fight.byPlayer[p]
		if f then f.alive = false; task.spawn(Fight.spawn, f) end
	end)
	for p, im in inMatch do if im.m == m then inMatch[p] = nil end end
	m.on = false
	local i = table.find(live, m)
	if i then table.remove(live, i) end
	if padLast[m.pad] == m then padLast[m.pad] = nil end
	-- the site goes back once everyone is out of it (a copy is cleared)
	task.delay(Matches.CLEAR, releaseSite, m.site)
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
	if not m.on or m.phase == "over" then return end
	if m.ghost then -- (a Studio test's empty match: over when its time is up)
		if os.clock() >= m.ghost then endMatch(m, nil) end
		return
	end
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
	task.delay(Matches.BETWEEN, function() if m.on and m.phase == "between" then startRound(m) end end)
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
	-- the first round opens on the arena's name (Arena.title: "ROOFTOP: SKYLINE"), then the round line, both on the
	-- HUD's announcer line
	local first = m.round == 1
	task.delay(0.6, function()
		if not m.on then return end
		if first then callAll(m, Arena.title(m.arena), 1.1) end
		task.delay(if first then 1.2 else 0, function()
			if not m.on then return end
			each(m, function(p, t) CalloutR:FireClient(p, ("ROUND %d · you're %s"):format(m.round, TEAM_NAMES[t]), if first then 1.05 else 1.6) end)
		end)
	end)
	task.delay(Matches.READY, function()
		if not m.on or m.phase ~= "ready" then return end
		m.phase = "live"
		-- (test knob: a TestRoundTime attribute on this module, set on the running server, shortens rounds in a playtest)
		m.roundEnds = os.clock() + ((script:GetAttribute("TestRoundTime") :: number?) or Matches.ROUND_TIME)
		setHud(m)
		each(m, function(p) RoundR:FireClient(p, { start = true }) end)
	end)
end

-- `site` is the one the pad took when its countdown started (in arena `arena`, the pad's pick from the rotation)
local function startMatch(pad: Model, sides: { { Player } }, site: Site, arena: string): Match
	nextId += 1
	local teams = {}
	for t, list in sides do teams[t] = table.clone(list) end
	local wins = {}
	for t = 1, #teams do wins[t] = 0 end
	lastArena[pad] = arena
	local m: Match = { id = nextId, mode = pad:GetAttribute("Mode") :: string, teams = teams, wins = wins, round = 0, phase = "ready", roundEnds = 0, pad = pad, fighters = {}, dmg = {}, arena = arena, site = site, on = true }
	table.insert(live, m)
	padLast[pad] = m
	each(m, function(p, t)
		inMatch[p] = { m = m, team = t }
		p:SetAttribute("Team", t)
		p:SetAttribute("Arena", arena) -- (their screen's light follows it: HubLife)
		local f = Fight.byPlayer[p]
		if f then
			table.insert(m.fighters, f)
			f.kills, f.deaths, f.kat = 0, 0, 0
			p:SetAttribute("Kills", 0); p:SetAttribute("Deaths", 0); p:SetAttribute("Kat", 0)
		end
	end)
	startRound(m)
	return m
end

-- the pad's next arena: the next one in the rotation for this pad (never its last one twice running), else "Arena"
local function nextArena(pad: Model): string
	return Arena.pick(Arena.pool(), lastArena[pad], math.random) or Arena.name()
end

-- ------------------------------------------------------------------ the pads
-- a pad's two lines go on every label in it named Status and Sub (the Lanes' boards have two faces, so two of each;
-- the old pads had one). found once per pad
local padLabels: { [Model]: { status: { TextLabel }, sub: { TextLabel } } } = {}
local function padSign(pad: Model, status: string, sub: string)
	local l = padLabels[pad]
	if not l then
		l = { status = {}, sub = {} }
		for _, d in pad:GetDescendants() do
			if d:IsA("TextLabel") then
				if d.Name == "Status" then table.insert(l.status, d) elseif d.Name == "Sub" then table.insert(l.sub, d) end
			end
		end
		padLabels[pad] = l
	end
	for _, s in l.status do if s.Text ~= status then s.Text = status end end
	for _, b in l.sub do if b.Text ~= sub then b.Text = sub end end
end

local function padStep()
	local pads = hub:FindFirstChild("QueuePads")
	if not pads then return end
	-- a pad taken out of the hub gives back the site it held
	for pad, c in padCount do
		if pad.Parent ~= pads then padCount[pad] = nil; releaseSite(c.site) end
	end
	for pad in fullSince do if pad.Parent ~= pads then fullSince[pad] = nil end end
	local claimed: { [Player]: boolean } = {}
	local seen: { [Model]: { sides: { { Player } }, counts: string, full: boolean } } = {}
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
		-- the slot rings light up as people step on. (an empty slot is 0.55 see-through unless it says otherwise: the Lanes'
		-- place lights have Off = 1, so an empty place is the dark socket under the light and a taken one is lit)
		for _, r in pad:GetChildren() do
			if r.Name == "Slot" and r:IsA("BasePart") then
				local t, s = r:GetAttribute("Team") :: number, r:GetAttribute("Slot") :: number
				local off = r:GetAttribute("Off")
				local want = if sides[t] and #sides[t] >= s then 0 else (if type(off) == "number" then off else 0.55)
				if r.Transparency ~= want then r.Transparency = want end
			end
		end
		seen[pad] = { sides = sides, counts = table.concat(counts, "   vs   "), full = full }
		local c = padCount[pad]
		if full then
			fullSince[pad] = fullSince[pad] or os.clock()
			if c and c.lost then c.lost = nil; c.at = os.clock() + Matches.COUNTDOWN end -- (back on: the count starts again)
		else
			fullSince[pad] = nil
			-- someone stepped off: the count stops, and the site goes back if nobody steps on again within 1.5 s (so a
			-- foot on the edge doesn't clear a copy and make it again)
			if c then
				c.lost = c.lost or os.clock()
				if os.clock() - (c.lost :: number) > 1.5 then padCount[pad] = nil; releaseSite(c.site) end
			end
		end
	end
	-- full pads with no site yet take one in the order they filled. the first that can't get one (the cap) stops the
	-- line: nobody jumps ahead of a pad that filled before them
	local line: { Model } = {}
	for pad, s in seen do if s.full and not padCount[pad] then table.insert(line, pad) end end
	table.sort(line, function(a, b) return fullSince[a] < fullSince[b] end)
	local waiting: { [Model]: number } = {}
	for _, pad in line do
		if next(waiting) == nil then
			local arena = nextArena(pad)
			local site = claimSite(arena)
			if site then padCount[pad] = { at = os.clock() + Matches.COUNTDOWN, site = site, arena = arena }; continue end
		end
		local n = 0
		for _ in waiting do n += 1 end
		waiting[pad] = n -- (how many pads are ahead of it)
	end
	for pad, s in seen do
		local sub = "step on a side to queue"
		local c = padCount[pad]
		if s.full then
			if not c then
				local ahead = waiting[pad] or 0
				sub = if ahead == 0 then "ALL ARENAS BUSY · you're next" else ("ALL ARENAS BUSY · %d ahead of you"):format(ahead)
			elseif os.clock() >= c.at then
				padCount[pad] = nil
				fullSince[pad] = nil
				startMatch(pad, s.sides, c.site, c.arena)
				sub = "GO!"
			else
				sub = ("STARTING IN %d"):format(math.ceil(c.at - os.clock()))
			end
		else
			local m = padLast[pad]
			if m and m.on then sub = "match on · " .. hudText(m):gsub("<[^>]+>", "") end
		end
		padSign(pad, s.counts, sub)
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
		for _, m in table.clone(live) do checkRound(m) end
	end)
	-- (Studio play tests only, like TestHook's JankTest: ServerStorage.JankMatchTest reaches the running server)
	if RunService:IsStudio() then
		local old = ServerStorage:FindFirstChild("JankMatchTest")
		if old then old:Destroy() end
		local fn = Instance.new("BindableFunction")
		fn.Name = "JankMatchTest"
		fn.OnInvoke = function(op: string, a: any, b: any, c: any): any return Matches.test(op, a, b, c) end
		fn.Parent = ServerStorage
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankMatchTest)
-- a play test has one player, so it can't fill two pads at once. "ghost" starts a match with nobody in it (pad name,
-- arena name or nil for the pad's next, seconds it lasts): it takes a site like any match, runs its rounds and ends
-- the normal way. "state" reads the live matches, the sites in use, the copies and the pads' countdowns
function Matches.test(op: string, a: any, b: any, c: any): any
	if not RunService:IsStudio() then return nil end
	if op == "ghost" then
		local pads = hub:FindFirstChild("QueuePads")
		local pad = pads and pads:FindFirstChild(tostring(a))
		if not pad or not pad:IsA("Model") then return nil end
		local arena = if type(b) == "string" then b else nextArena(pad)
		local site = claimSite(arena)
		if not site then return { refused = arena, inUse = sitesInUse(), cap = maxLive() } end
		local sides = {}
		for t = 1, (pad:GetAttribute("Teams") :: number) do sides[t] = {} end
		local m = startMatch(pad, sides, site, arena)
		m.ghost = os.clock() + (if type(c) == "number" then c else 30)
		local sp = {}
		for t = 1, #sides do
			sp[t] = {}
			for _, cf in teamSpawns(m, t) do table.insert(sp[t], cf.Position) end
		end
		return { id = m.id, arena = arena, site = site.model:GetFullName(), copy = site.copy, pivot = site.model:GetPivot().Position, killY = Arena.killY(site.model), centreX = Arena.centreX(site.model), spawns = sp }
	elseif op == "state" then
		local out = { live = {}, sites = {}, pads = {}, inMatch = 0, cap = maxLive() }
		for _, m in live do
			local n = 0
			each(m, function() n += 1 end)
			table.insert(out.live, { id = m.id, pad = m.pad.Name, arena = m.arena, site = m.site.model.Name, copy = m.site.copy, phase = m.phase, round = m.round, players = n, ghost = m.ghost ~= nil })
		end
		for model in busy do table.insert(out.sites, model:GetFullName()) end
		for pad, cd in padCount do out.pads[pad.Name] = { arena = cd.arena, site = cd.site.model.Name, left = cd.at - os.clock() } end
		for _ in inMatch do out.inMatch += 1 end
		local map = workspace:FindFirstChild("Map")
		local f = map and map:FindFirstChild("ArenaCopies")
		out.copies = if f then #f:GetChildren() else 0
		local slots = 0
		for _, list in copySlots do for _ in list do slots += 1 end end
		out.copySlots = slots
		return out
	end
	return nil
end

return Matches
