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
local MapCards = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("MapCards")) -- (the pads' map vote)
local RankedDraft = require(script.Parent:WaitForChild("RankedDraft")) -- (ranked: the draft's bans, the loadout switches)
local Hitbox = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Hitbox")) -- (a spawn's root height, as Fight.spawn puts it)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local RoundR = Remotes:WaitForChild("Round") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent

local Matches = {}
Matches.WIN = 5 -- round wins that take the match
Matches.ROUND_TIME = 120 -- s; time up = the most damage dealt takes it (then HP left, then a coin flip)
Matches.COUNTDOWN = 3 -- s on a full pad before you go
Matches.PAD_VOTE = 8 -- s a pad's group votes on its map in a map room (18 Nov, the owner; MapRooms.luau, the stages below)
Matches.READY = 3 -- s from spawning in to the round going live (no damage till then): the shortest count after a break
Matches.READY_FIRST = 20 -- (round 1: the loadout window before the first round. 17 Nov, the owner; 20 s since 18 Nov)
Matches.WINDOW = 15 -- s the loadout window runs between rounds: the break, then the count held at your spawn (18 Nov)
Matches.GO = 3 -- s from everyone locked in (READY) to the round going live: the window shuts early (18 Nov)
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
	id: number, key: string, -- (key: unique across servers and restarts, "<server>-<id>-<os.time>": per-match records in Stats and RankedData)
	mode: string, teams: { { Player } }, wins: { number }, round: number,
	phase: string, -- "ready" (spawned, not live yet) | "live" | "between" | "over"
	roundEnds: number, pad: Model, fighters: { Fighter },
	dmg: { number }, -- damage each team dealt to the others this round
	arena: string, -- the arena's name ("RooftopV2"): its banner and its light
	site: Site, -- where it is played: that arena, or a copy of it
	on: boolean, -- false once its players are back in the hub
	ghost: number?, -- (Studio tests only: a match with nobody in it, over at this os.clock(): Matches.test)
	ghostWin: number?, -- (and the team that wins it then; nil = nobody)
	queue: string?, -- (the Play queue's matches: its queue key, "ranked:2v2"; nil = a pad match)
	ranked: boolean?, -- (a ranked match: RankedData rates it at the end)
	rated: any?, -- (everyone's rating when it started, stand-ins too: RankedData)
	quick: boolean?, -- (a QUICKPLAY match: the grapple's auto-lock, shared/HookCharges.AUTO)
	private: boolean?, -- (a party alone, Party.luau: counts for nothing, like a dev match: Stats, Quests)
	rules: any?, -- (a classic mode's match, Matches.startMode: Modes.luau runs its spawns, respawns, clock, HUD, board and end)
	ms: any?, -- (and keeps its state here)
	liveAt: number?, -- (the os.clock() the next round goes live: the loadout window shuts then, LoadoutWindow)
	tok: number?, -- (the go-live that's still wanted: an early start makes the one before it stale)
	locked: boolean?, -- (everyone locked in: the window is shut early, the GO count runs)
	ready: { [Player]: boolean }?, -- who has locked in their set this window (READY)
	standIns: { { team: number, ready: boolean } }?, -- (Studio tests: pretend players in the ready count)
}

local Fight: any
local hub: Instance
local live: { Match } = {} -- the matches being played, oldest first
local inMatch: { [Player]: { m: Match, team: number } } = {}
local lastZone: { [Player]: string } = {}
-- a full pad's countdown and the site it holds (lost: when the pad stopped being full, if it has)
local padCount: { [Model]: { at: number, site: Site, arena: string, lost: number? } } = {}
local fullSince: { [Model]: number } = {} -- when each full pad filled (the first to fill gets the next free site)
-- (QuickJoin.luau) the pads as the last step saw them: pad -> { sides = { { Player } }, full = boolean }
local padView: { [Model]: any } = {}
local staged: { [Player]: any } = {} -- (in a map room, voting on the map: the stages below padSign)
function Matches.padView(): { [Model]: any } return padView end
local lastArena: { [Model]: string } = {} -- each pad's last arena (none yet after a server starts: the first pick is random)
local padLast: { [Model]: Match } = {} -- each pad's latest match (its sign shows it)
local busy: { [Model]: boolean } = {} -- the sites in use
local copySlots: { [string]: { [number]: Model } } = {} -- each arena's copies by slot (Arena.copyOffset)
local nextId = 0
-- (the first 8 of the JobId, or a random tag in Studio where the JobId is "": a match key never repeats across servers)
local SERVER_TAG = if game.JobId ~= "" then string.sub(game.JobId, 1, 8) else ("st" .. string.format("%06x", math.random(0, 0xffffff)))

-- other modules follow the matches (Stats.luau): one starting (its teams of players), a round won, the end. each hook
-- runs in its own thread, so a slip in one can't stop a match
local hooks: { [string]: { (...any) -> () } } = { start = {}, round = {}, finish = {} }
function Matches.onStart(fn: (Match) -> ()) table.insert(hooks.start, fn) end
function Matches.onRound(fn: (Match, number) -> ()) table.insert(hooks.round, fn) end -- (the match, the team that took it)
function Matches.onEnd(fn: (Match, number?) -> ()) table.insert(hooks.finish, fn) end -- (the match, the winning team)
local function fire(list: { (...any) -> () }, ...: any) for _, fn in list do task.spawn(fn, ...) end end
-- the match a player is in, or nil: { id, mode, arena, team, phase }
function Matches.matchOf(p: Player): { id: number, key: string, mode: string, arena: string, team: number, phase: string, ranked: boolean, queue: string? }?
	local im = inMatch[p]
	if not im then return nil end
	return { id = im.m.id, key = im.m.key, mode = im.m.mode, arena = im.m.arena, team = im.team, phase = im.m.phase, ranked = im.m.ranked == true, queue = im.m.queue }
end
-- (OwnerDev.server) may the owner's dev weapons hurt this player out of a match
Matches.devHit = nil :: ((Player, Player) -> boolean)?
-- (Party.luau) where a player who is not in a match respawns instead of the hub: their private lobby's plinth, or nil
Matches.homeOf = nil :: ((Player) -> CFrame?)?
-- (Recorder.luau) at a match's end: hold it for a replay? { wait = s on the end screen, total = s until home, label }
Matches.afterHook = nil :: ((any) -> any?)?
-- (Modes.luau) the match itself a player is in, or nil
function Matches.raw(p: Player): any?
	local im = inMatch[p]
	return if im then im.m else nil
end

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
	if staged[p] then return "staging" end -- (a map room: server/MapRooms.luau)
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local tz = hub:FindFirstChild("TrainingZone") :: BasePart?
	if root and tz and inside(tz, root.Position, 4) then return "training" end
	-- the playground (a secret, off through the training hall): its own zone, so its own look, and weapons work there
	local pz = hub:FindFirstChild("PlaygroundZone") :: BasePart?
	if root and pz and inside(pz, root.Position, 4) then return "playground" end
	return "hub"
end
-- (19 Nov 2026, the owner: "dont let player be able to use grapple or gadgets before round starts") not yet GO: in a
-- match that isn't live (the countdown and loadout window, between rounds, the end screen) or in a map room. the grapple,
-- yank and reel (Main.server) and the gadgets (Utility) are refused before anything is spent; RoundLock on the player
-- (the heartbeat below) tells the clients
function Matches.roundLocked(p: Player): boolean
	if staged[p] then return true end
	local im = inMatch[p]
	return im ~= nil and im.m.phase ~= "live"
end

-- ------------------------------------------------------------------ the hooks Fight asks
-- may `by` hurt `t`? (nil / yourself = a fall: always)
function Matches.allow(by: Fighter?, t: Fighter): boolean
	if not by or by == t then return true end
	if t.kind == "dummy" then return true end -- anyone can hit a dummy
	local tp = t.ref :: Player
	if by.kind == "dummy" then return Matches.zoneOf(tp) == "training" end -- the dummies only shoot back in their room
	-- (the owner's dev weapons, out of a match: anyone else out of one too. it counts for nothing: Fight.devKill)
	if Matches.devHit and by.kind == "player" and (Matches.devHit :: any)(by.ref :: Player, tp) then return true end
	local a, b = inMatch[by.ref :: Player], inMatch[tp]
	-- (a classic mode can have sides of its own: infection's survivors and zombies, Modes.luau)
	if a and b and a.m == b.m and a.m.rules and a.m.rules.allow then return a.m.phase == "live" and a.m.rules.allow(a.m, by, t, a.team ~= b.team) end
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
-- which end a team spawns at this round (18 Nov 2026, the owner: "rotate spawns"): the sides swap every round, so nobody
-- keeps a better end. round 1 is a random side (a shift drawn once a match); after it, two teams swap ends each round
-- and a 1v1v1 moves one spawn group round. 1 = the "att" spawns, 2 = "def", 3 = "mid". a classic mode keeps its own
-- spawning (Modes.luau). everything that puts a body on its round spawn asks teamSpawns, so it follows
local function sideOf(m: Match, team: number): number
	local n = math.max(1, #m.teams)
	local mm = m :: any
	if mm.spawnShift == nil then mm.spawnShift = math.random(0, n - 1) end
	return (team - 1 + mm.spawnShift + math.max(0, m.round - 1)) % n + 1
end
local function teamSpawns(m: Match, team: number): { CFrame }
	local roof = m.site.model
	local cx = Arena.centreX(roof)
	local out = {}
	local ts = roof:FindFirstChild("TeamSpawns")
	-- (a 1v1v1's third side: the arena's "mid" team spawns, facing its middle; the ported web maps have them, 17 Nov)
	local side = sideOf(m, team)
	local want = if side == 1 then "att" elseif side == 2 then "def" else "mid"
	local mid = roof:GetPivot().Position
	if ts then
		for _, s in ts:GetChildren() do
			if s:IsA("BasePart") and s.Name == want then
				local toward = if want == "mid" then Vector3.new(mid.X, s.Position.Y, mid.Z) else Vector3.new(cx, s.Position.Y, s.Position.Z)
				local f = s:GetAttribute("Face") -- (a spawn's own heading, 17 Nov: a galley spawn looks at its door, not its wall)
				if typeof(f) == "Vector3" and Vector3.new(f.X, 0, f.Z).Magnitude > 0.01 then toward = s.Position + Vector3.new(f.X, 0, f.Z) end
				if (toward - s.Position).Magnitude > 0.1 then table.insert(out, CFrame.lookAt(s.Position, toward)) else table.insert(out, CFrame.new(s.Position)) end
			end
		end
	end
	if #out == 0 and (want == "mid" or not ts) then
		local sp = roof:FindFirstChild("Spawns")
		for _, n in { "Spawn11", "Spawn18", "Spawn14", "Spawn12", "Spawn13" } do
			local s = sp and sp:FindFirstChild(n) :: BasePart?
			if s then table.insert(out, CFrame.lookAt(s.Position + Vector3.new(0, 0.1, 0), Vector3.new(s.Position.X + 1, s.Position.Y, s.Position.Z))) end
		end
	end
	if #out == 0 then table.insert(out, CFrame.new(roof:GetPivot().Position + Vector3.new(side * 30, 5, 0))) end
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
	if im and im.m.rules then return im.m.rules.spawnAt(im.m, p) end -- (a classic mode: Modes.luau picks)
	if im then
		local list = teamSpawns(im.m, im.team)
		local i = table.find(im.m.teams[im.team], p) or 1
		local cf = list[(i - 1) % #list + 1]
		return cf.Position, cf.LookVector
	end
	local home = Matches.homeOf and Matches.homeOf(p)
	if home then return home.Position, home.LookVector end
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
	return ("%s · ROUND %d · %s"):format(if m.ranked then "RANKED " .. m.mode else m.mode, m.round, table.concat(score, " – "))
end
local function each(m: Match, fn: (Player, number) -> ())
	for t, list in m.teams do for _, p in list do if p.Parent then fn(p, t) end end end
end
local function setHud(m: Match)
	if m.rules then m.rules.setHud(m); return end -- (a classic mode: each player's own line, Modes.luau)
	local txt = hudText(m)
	-- (the loadout window, 17 Nov, the owner: "allow us to change weapons before first round and between rounds". the
	-- countdown before a round and the break between rounds; the server time it shuts. Loadout.luau takes picks while
	-- it is set and puts them in your hands, client/MatchLoadout.luau opens on it)
	local win = if (m.phase == "ready" or m.phase == "between") and m.liveAt and not m.locked then workspace:GetServerTimeNow() + math.max(0, (m.liveAt :: number) - os.clock()) else nil
	each(m, function(p) p:SetAttribute("MatchHud", txt); p:SetAttribute("RoundEnds", if m.phase == "live" then workspace:GetServerTimeNow() + (m.roundEnds - os.clock()) else nil); p:SetAttribute("LoadoutWindow", win) end)
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
local startRound: (Match, boolean?) -> ()

-- ------------------------------------------------------------------ READY (18 Nov, the owner: "give more time for
-- loadouts! until move people lock in their set once both are ready"). the loadout window is longer (READY_FIRST before
-- round 1, WINDOW between rounds) and you're held at your spawn while the round counts in. READY (MatchLoadout, the
-- MatchReady remote) locks your set for the round; once everyone still in the match has, the window shuts early and the
-- round goes live GO s later. whoever doesn't lock in keeps what they had; a leaver holds nobody up. every round-based
-- match, casual and ranked; a classic mode has no window. ReadyTeams on each player: per team, "1" / "0" a player
-- ("1,0|0"); LoadoutReady: you're locked in
local function readyBoard(m: Match): string
	local parts = {}
	for t, list in m.teams do
		local marks = {}
		for _, p in list do if p.Parent then table.insert(marks, if m.ready and m.ready[p] then "1" else "0") end end
		for _, s in m.standIns or {} do if s.team == t then table.insert(marks, if s.ready then "1" else "0") end end
		parts[t] = table.concat(marks, ",")
	end
	return table.concat(parts, "|")
end
local function pushReady(m: Match)
	local board = if (m.phase == "ready" or m.phase == "between") and not m.rules then readyBoard(m) else nil
	each(m, function(p)
		p:SetAttribute("ReadyTeams", board)
		p:SetAttribute("LoadoutReady", if board and m.ready and m.ready[p] then true else nil)
	end)
end
local function allReady(m: Match): boolean
	local n = 0
	for _, list in m.teams do
		for _, p in list do
			if p.Parent and inMatch[p] then
				n += 1
				if not (m.ready and m.ready[p]) then return false end
			end
		end
	end
	for _, s in m.standIns or {} do if not s.ready then return false end end
	return n > 0
end
local goLive: (Match, number) -> ()
-- everyone's in: the window shuts now and the round goes live GO s later (from the break: the round starts now)
local function checkReady(m: Match)
	if not m.on or m.rules or m.locked or not (m.phase == "ready" or m.phase == "between") then return end
	if not allReady(m) then return end
	if m.phase == "between" then
		if m.wins and m.round > 0 then for _, w in m.wins do if w >= Matches.WIN then return end end end -- (the match is won)
		startRound(m, true)
		return
	end
	if (m.liveAt or 0) - os.clock() <= Matches.GO then return end -- (the count is shorter than that already)
	m.locked = true
	m.liveAt = os.clock() + Matches.GO
	m.tok = (m.tok or 0) + 1
	setHud(m)
	pushReady(m)
	callAll(m, "ALL READY", 1.2)
	task.delay(Matches.GO, goLive, m, m.tok)
end
function Matches.ready(p: Player): (boolean, string?)
	local im = inMatch[p]
	if not im then return false, "not in a match" end
	local m = im.m
	if m.rules then return false, "this mode keeps its own weapons" end
	if m.locked or not (m.phase == "ready" or m.phase == "between") then return false, "the round is starting" end
	local r = m.ready or {}
	m.ready = r
	if r[p] then return true, nil end
	r[p] = true
	pushReady(m)
	checkReady(m)
	return true, nil
end
-- held at your round spawn while the round counts in (18 Nov, the owner: "make sure to lock position at the start of
-- round because I was moving around after round ended and when round started I got a head start forward because it
-- carried my momentum"). every body, the round's winners' too, is a fresh one Fight.spawn puts on its spawn (startRound);
-- the step it's there (alive again) it's put back exactly on the spot (a TeleportT stamp first: the anti-cheat starts
-- afresh there), stopped and anchored. SpawnHold on each player tells Move.client to keep no speed and build none.
-- the round goes live: stopped again, let go, SpawnHold off. (until 18 Nov a body was anchored 0.6 s after it appeared,
-- time to sprint a few studs off the spot first.) an anchored body doesn't move: the anti-cheat sees nothing to judge
-- (standing ON the floor under the spawn mark, found by a ray with every body left out: let go, the first frames are
-- on the ground and run, not a short fall. was the spawn's own +0.2 studs over standing height until 18 Nov)
local floorParams = RaycastParams.new()
floorParams.FilterType = Enum.RaycastFilterType.Exclude
floorParams.RespectCanCollide = true
local function spawnSpot(m: Match, p: Player, team: number, root: BasePart?, hum: Humanoid?): CFrame?
	local list = teamSpawns(m, team)
	if #list == 0 then return nil end
	local i = table.find(m.teams[team], p) or 1
	local cf = list[(i - 1) % #list + 1]
	local y = cf.Position.Y + Hitbox.ROOT_UP + 0.2
	local bodies = {}
	for _, q in Players:GetPlayers() do if q.Character then table.insert(bodies, q.Character) end end
	floorParams.FilterDescendantsInstances = bodies
	local hit = workspace:Raycast(cf.Position + Vector3.new(0, 4, 0), Vector3.new(0, -14, 0), floorParams)
	if hit and root and hum then
		local stand = root.Size.Y / 2 + (if hum.RigType == Enum.HumanoidRigType.R15 then hum.HipHeight else 2)
		y = hit.Position.Y + stand
	end
	local pos = Vector3.new(cf.Position.X, y, cf.Position.Z)
	local look = Vector3.new(cf.LookVector.X, 0, cf.LookVector.Z)
	return if look.Magnitude > 1e-3 then CFrame.lookAt(pos, pos + look.Unit) else CFrame.new(pos)
end
local function holdSpawns(m: Match, round: number)
	local held: { [BasePart]: boolean } = {}
	local function live(): boolean return m.on and m.round == round and m.phase == "ready" end
	each(m, function(p) p:SetAttribute("SpawnHold", true) end)
	while live() do
		each(m, function(p, t)
			local ch = p.Character
			local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			local hum = ch and ch:FindFirstChildOfClass("Humanoid")
			local f = Fight.byPlayer[p]
			if not root or not hum or hum.Health <= 0 or held[root] or not f or not f.alive then return end
			local spot = spawnSpot(m, p, t, root, hum)
			if spot and (root.Position - spot.Position).Magnitude > 0.05 then
				p:SetAttribute("TeleportT", os.clock())
				local body = ch :: Model
				body:PivotTo(spot)
			end
			root.AssemblyLinearVelocity = Vector3.zero
			root.AssemblyAngularVelocity = Vector3.zero
			root.Anchored = true
			held[root] = true
		end)
		RunService.Heartbeat:Wait()
	end
	for root in held do
		if root.Parent then root.AssemblyLinearVelocity = Vector3.zero; root.Anchored = false end
	end
	each(m, function(p) p:SetAttribute("SpawnHold", nil) end)
end

local function backToHub(m: Match)
	if m.rules then m.rules.home(m) end -- (a classic mode: its marks come off first)
	each(m, function(p)
		RankedDraft.stop(p)
		inMatch[p] = nil
		lastZone[p] = "hub"
		p:SetAttribute("Team", nil); p:SetAttribute("MatchHud", nil); p:SetAttribute("RoundEnds", nil); p:SetAttribute("Arena", nil); p:SetAttribute("LoadoutWindow", nil)
		p:SetAttribute("ReadyTeams", nil); p:SetAttribute("LoadoutReady", nil); p:SetAttribute("SpawnHold", nil)
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
	fire(hooks.finish, m, winner)
	setHud(m)
	local board = if m.rules then m.rules.board(m) else Fight.board(m.fighters)
	local name = if winner then (if m.rules then m.rules.label(m, winner) else teamLabel(m, winner)) else nil
	local cols = if m.rules then m.rules.cols(m) else nil -- (the board's two number columns, nil: KILLS, DEATHS)
	-- (Recorder.luau) a match with a play of the match stays on the end screen for after.wait s, then everyone watches
	-- it, then home after after.total s
	local after = if Matches.afterHook then Matches.afterHook(m) else nil
	each(m, function(p, t)
		local home = Matches.homeOf and Matches.homeOf(p)
		RoundR:FireClient(p, { over = true, winner = name, youWon = winner == t, board = board, next = if after then after.wait else Matches.AFTER,
			nextLabel = if after then after.label elseif home then "back to the lobby in %d" else "back to the hub in %d", ranked = m.ranked == true,
			cols = cols, mode = if m.rules then m.mode else nil })
	end)
	task.delay(if after then after.total else Matches.AFTER, backToHub, m)
end
Matches.finish = endMatch -- (Modes.luau: a classic mode's end, winner = the team that takes it or nil)

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
	if m.rules then m.rules.check(m); return end -- (a classic mode: its clock, leavers and win, Modes.luau)
	if m.ghost then -- (a Studio test's empty match: over when its time is up)
		if os.clock() >= m.ghost then endMatch(m, m.ghostWin) end
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
	m.liveAt = os.clock() + Matches.WINDOW -- (the break, then the count at your spawn: the loadout window)
	m.wins[winner] += 1
	fire(hooks.round, m, winner)
	setHud(m)
	pushReady(m)
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

startRound = function(m: Match, early: boolean?)
	m.round += 1
	m.phase = "ready"
	if m.ranked then
		local ps = {}
		each(m, function(p) table.insert(ps, p) end)
		RankedDraft.round(m.key, ps, m.round) -- (a switch counts from round 2's window on)
	end
	-- (the loadout window: READY_FIRST before round 1, the rest of WINDOW after a break; everyone ready already: GO)
	local ready = if early then Matches.GO elseif m.round == 1 then Matches.READY_FIRST else math.max(Matches.READY, Matches.WINDOW - Matches.BETWEEN)
	m.liveAt = os.clock() + ready
	m.locked = if early then true else nil
	m.tok = (m.tok or 0) + 1
	local tok = m.tok
	for t = 1, #m.teams do m.dmg[t] = 0 end
	setHud(m)
	pushReady(m)
	if early then callAll(m, "ALL READY", 1.2) end
	-- a fresh body for everyone at their end (alive or not), held there till the round goes live
	each(m, function(p)
		local f = Fight.byPlayer[p]
		if f then f.alive = false; task.spawn(Fight.spawn, f) end
	end)
	task.spawn(holdSpawns, m, m.round)
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
	task.delay(ready, goLive, m, tok)
end
goLive = function(m: Match, tok: number)
	if not m.on or m.phase ~= "ready" or m.tok ~= tok then return end
	m.phase = "live"
	m.locked = nil
	m.ready = nil
	-- (test knob: a TestRoundTime attribute on this module, set on the running server, shortens rounds in a playtest)
	m.roundEnds = os.clock() + ((script:GetAttribute("TestRoundTime") :: number?) or Matches.ROUND_TIME)
	setHud(m)
	pushReady(m)
	each(m, function(p) RoundR:FireClient(p, { start = true }) end)
end

-- `site` is the one the pad took when its countdown started (in arena `arena`, the pad's pick from the rotation)
local function startMatch(pad: Model, sides: { { Player } }, site: Site, arena: string, opts: any?): Match
	nextId += 1
	local teams = {}
	for t, list in sides do teams[t] = table.clone(list) end
	local wins = {}
	for t = 1, #teams do wins[t] = 0 end
	lastArena[pad] = arena
	local m: Match = { id = nextId, key = SERVER_TAG .. "-" .. nextId .. "-" .. os.time(), mode = if opts and opts.mode then opts.mode else pad:GetAttribute("Mode") :: string, teams = teams, wins = wins, round = 0, phase = "ready", roundEnds = 0, pad = pad, fighters = {}, dmg = {}, arena = arena, site = site, on = true,
		queue = if opts then opts.queue else nil, ranked = if opts then opts.ranked == true else nil, rated = if opts then opts.rated else nil,
		rules = if opts then opts.rules else nil, private = if opts and opts.private == true then true else nil,
		quick = if opts and opts.quick == true then true else nil }
	table.insert(live, m)
	if not m.queue then padLast[pad] = m end -- (a Play-queue match isn't the pad's: its sign keeps its own)
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
	-- (a ranked match: the draft's bans hold for it, and loadout switches are counted: RankedDraft.luau)
	if m.ranked then
		local ps = {}
		each(m, function(p) table.insert(ps, p) end)
		RankedDraft.start(m.key, ps, if opts then opts.bans else nil)
	end
	fire(hooks.start, m)
	if m.rules then m.rules.begin(m) else startRound(m) end
	return m
end

-- the pad's next arena: the next one in the rotation for this pad (never its last one twice running), else "Arena".
-- only arenas that take the pad's team size (an arena's MaxTeam: Arena.pool)
local function nextArena(pad: Model): string
	local mode = pad:GetAttribute("Mode")
	local size = if type(mode) == "string" then tonumber(string.match(mode, "^(%d+)")) else nil
	return Arena.pick(Arena.pool(size), lastArena[pad], math.random) or Arena.name()
end

-- (Party.luau, the Play queue) a match the queue found: the pad of that mode (the one by the lifts first) gives its
-- rules and its arena rotation, and a site is claimed now, like a pad's countdown does. returns the match, or nil and
-- why ("busy": every site is in use; the queue tries again). opts = { queue, ranked, rated, hold?, holdWin? }; hold
-- (Studio tests only) holds the match like a ghost match: it ends after hold s with team holdWin taking it
function Matches.startQueued(padMode: string, sides: { { Player } }, opts: any): (Match?, string?)
	local pads = hub:FindFirstChild("QueuePads")
	local pad: Model? = nil
	if pads then
		for _, c in pads:GetChildren() do
			if c:IsA("Model") and c:GetAttribute("Mode") == padMode and (pad == nil or c:GetAttribute("Bank") == "lifts") then pad = c end
		end
	end
	if not pad then return nil, "no pad plays " .. padMode end
	for _, list in sides do for _, p in list do if inMatch[p] then return nil, "in a match" end end end
	-- (opts.arena: the map its players picked, the leader's or a vote's. one that can't be had now, while there's room
	-- for a match, gives way to the rotation's)
	local arena = if type(opts.arena) == "string" then opts.arena else nextArena(pad)
	local site = claimSite(arena)
	if not site and type(opts.arena) == "string" and sitesInUse() < maxLive() then
		arena = nextArena(pad)
		site = claimSite(arena)
	end
	if not site then return nil, "busy" end
	local m = startMatch(pad, sides, site, arena, opts)
	if opts.hold and RunService:IsStudio() then
		m.ghost = os.clock() + opts.hold
		m.ghostWin = opts.holdWin
	end
	return m, nil
end

-- (Modes.luau) a classic mode's match: sides = one list of players per side (a free-for-all: one each; a ghost side of a
-- Studio test: empty), opts as startQueued's plus rules (Modes.luau's: it runs the match) and mode (its id, "gun"). the
-- arena comes from the whole rotation through a pad of its own (no queue pad's rotation moves). the match, or nil and why
local modePad: Model? = nil
function Matches.startMode(sides: { { Player } }, opts: any): (Match?, string?)
	for _, list in sides do for _, p in list do if inMatch[p] then return nil, "in a match" end end end
	if not modePad then
		local mp = Instance.new("Model")
		mp.Name = "ModesPad"
		mp:SetAttribute("Mode", "modes")
		modePad = mp
	end
	local pad = modePad :: Model
	local arena = if type(opts.arena) == "string" then opts.arena else nextArena(pad)
	local site = claimSite(arena)
	if not site and type(opts.arena) == "string" and sitesInUse() < maxLive() then
		arena = nextArena(pad)
		site = claimSite(arena)
	end
	if not site then return nil, "busy" end
	return startMatch(pad, sides, site, arena, opts), nil
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

-- ------------------------------------------------------------------ the pads' map vote, in a room of its own (18 Nov 2026,
-- the owner: "map select for pads please", then "map select should happen after pads itll spawn you in liek a void
-- area where the map options appear then itll bring you to said map"). a full pad counts down Matches.COUNTDOWN s as
-- before, then its group goes to a MAP ROOM of its own (server/MapRooms.luau: a dark platform in a void, three big map
-- displays with a plate in front of each) and the pad is free for the next group at once.
--   the vote: Matches.PAD_VOTE s on the three maps (the site the pad holds is one of them, two more from the rotation
--   for the pad's size, never the pad's last arena). a vote is the card on your screen (client/QuickVoteUI.luau: keys
--   1-3 or a tap; PlayPush { t = "padvote" }, the Play remote's "padvote" through Party.ops) or standing on a display's
--   plate. most votes wins; a tie, or no votes at all, is drawn.
--   the pick: the winner's site takes the held one's place (if it can't be had right now, the held map is played, and
--   the displays show that), shown PICK_SHOW s, then the match starts the usual way: everyone respawns at that arena's
--   spawns.
--   leavers: out of the game, or into another match, they leave the room; a side with nobody left sends the rest back to
--   the hub with a note, and the site goes back.
-- the room is the "staging" zone (Matches.zoneOf): its own dark look (HubLook "void", client_root/HubLife), no damage
-- (nobody there is in a match). every move into it stamps the anti-cheat's TeleportT, and the client turns its camera to
-- the displays (the Spawn remote, Body.luau). pads are casual: a ranked match never comes from a pad
local MapRooms = require(script.Parent:WaitForChild("MapRooms"))
local Hitbox = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Hitbox"))
local PICK_SHOW = 1.5
-- (a pad's stage holds its pad and site; a match server's (Matches.voteRoom, CrossServer.luau) has neither: go(map)
-- starts its match and cancel(note) runs when a whole side has left)
type Stage = { pad: Model?, sides: { { Player } }, site: Site?, arena: string, room: any, options: { string },
	votes: { [number]: string }, ends: number, map: string?, at: number?, test: boolean, shown: { [Player]: boolean }, dirty: boolean,
	go: ((string, any?) -> ())?, cancel: ((string) -> ())?,
	draft: any? } -- (a ranked draft's own state: Matches.draftRoom below)
local stages: { Stage } = {}
local testFill: { [Model]: Player } = {} -- (Studio: Matches.test "padfill")
local pushR: RemoteEvent? = nil
local spawnR: RemoteEvent? = nil
local function remote(name: string): RemoteEvent?
	local r = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	return r and r:FindFirstChild(name) :: RemoteEvent?
end
local function padPush(p: Player, msg: any)
	pushR = pushR or remote("PlayPush")
	if pushR and p.Parent then (pushR :: RemoteEvent):FireClient(p, msg) end
end
local function padCard(id: string): any return { id = id, title = Arena.title(id), thumb = MapCards.thumb(id) } end
local function stageCards(st: Stage): { any }
	local out = {}
	for _, id in st.options do table.insert(out, padCard(id)) end
	return out
end
local function each2(st: Stage, fn: (Player) -> ())
	for _, list in st.sides do for _, p in list do fn(p) end end
end
-- into the room: on its spot, facing the displays (a server move: TeleportT first; the client turns its camera)
local function moveTo(p: Player, spot: CFrame, look: Vector3)
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not root then return end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	if hum and hum.SeatPart then
		local weld = hum.SeatPart:FindFirstChild("SeatWeld")
		if weld then weld:Destroy() end
	end
	p:SetAttribute("TeleportT", os.clock())
	root.AssemblyLinearVelocity = Vector3.zero
	local pos = spot.Position + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)
	;(ch :: Model):PivotTo(CFrame.lookAt(pos, pos + look))
	spawnR = spawnR or remote("Spawn")
	if spawnR then (spawnR :: RemoteEvent):FireClient(p, spot.Position, look) end
end
-- the vote on everyone's screen as it stands; anyone who left the room sees it go
local function stageSync(st: Stage, gone: boolean?)
	local now: { [Player]: boolean } = {}
	if not gone then
		local view = { options = stageCards(st), ends = workspace:GetServerTimeNow() + math.max(0, st.ends - os.clock()), counts = MapCards.counts(st.votes) }
		local map = if st.map then padCard(st.map) else nil
		each2(st, function(p)
			now[p] = true
			if st.dirty or not st.shown[p] then
				if st.draft then padPush(p, (Matches :: any).draftView(st, p))
				else padPush(p, { t = "padvote", vote = { options = view.options, ends = view.ends, counts = view.counts, mine = st.votes[p.UserId] }, map = map }) end
			end
		end)
	end
	for p in st.shown do if not now[p] then padPush(p, { t = "padvote" }) end end
	st.shown = now
end
local function stageEnd(st: Stage)
	local i = table.find(stages, st)
	if i then table.remove(stages, i) end
	each2(st, function(p) if staged[p] == st then staged[p] = nil end end)
	for p in st.shown do if staged[p] == st then staged[p] = nil end end
	stageSync(st, true)
	local room = st.room
	task.delay(4, function() MapRooms.release(room) end) -- (after everyone has gone: the new bodies come first)
end
-- a whole side gone: the rest back to the hub, the site back
local function stageCancel(st: Stage, note: string)
	stageEnd(st)
	if st.site then releaseSite(st.site) end
	each2(st, function(p)
		if not st.cancel then padPush(p, { t = "toast", text = note }) end -- (a match server's cancel says its own)
		local f = Fight.byPlayer[p]
		if f and p.Parent then f.alive = false; task.spawn(Fight.spawn, f) end -- (a fresh body at the hub's spawns)
	end)
	if st.cancel then task.spawn(st.cancel, note) end
end
-- the vote's clock ran out: its pick, and that arena's site in place of the held one if it can be had
local function stageSettle(st: Stage)
	if st.map then return end
	local want = MapCards.result(st.options, st.votes) or st.arena
	if not st.site then
		st.arena = want -- (a match server's room: no site held, its go() starts the match on the pick)
	elseif want ~= st.arena then
		-- (the held site goes back first, so the cap counts it free; if the winner can't be had, the held map is taken again)
		local held = st.site :: Site
		releaseSite(held)
		local site = claimSite(want)
		if site then st.site, st.arena = site, want else st.site = claimSite(st.arena) or held end
	end
	st.map = st.arena
	st.at = os.clock() + ((script:GetAttribute("TestPickShow") :: number?) or PICK_SHOW) -- (test knob: longer, for a photo)
	st.dirty = true
end
-- to the arena: the match starts the usual way (everyone respawns at its spawns)
local function stageGo(st: Stage)
	stageEnd(st)
	if st.go then task.spawn(st.go, st.arena); return end
	local m = startMatch(st.pad :: Model, st.sides, st.site :: Site, st.arena)
	if st.test then m.ghost = os.clock() + 25 end -- (a test fill: held like a ghost match)
end
-- into the room: everyone on a spot, facing the displays, and the vote on its way
local function stageIn(st: Stage, sides: { { Player } })
	local room = st.room
	local k = 0
	for t, list in sides do
		st.sides[t] = {}
		for _, p in list do
			table.insert(st.sides[t], p)
			staged[p] = st
			k += 1
			moveTo(p, room.spots[(k - 1) % #room.spots + 1], room.look)
		end
	end
	table.insert(stages, st)
	MapRooms.show(room, stageCards(st), {}, nil)
end
-- a full pad's countdown is over: its group to a map room (no room to be had: straight to the match, as before)
local function stageStart(pad: Model, sides: { { Player } }, site: Site, arena: string): Match?
	local test = testFill[pad] ~= nil
	testFill[pad] = nil
	local room = MapRooms.claim()
	if not room then return startMatch(pad, sides, site, arena) end
	local sz = pad:GetAttribute("Size")
	local rest = {}
	for _, id in Arena.pool(if type(sz) == "number" then sz else nil) do if id ~= arena then table.insert(rest, id) end end
	local options = { arena }
	for _, id in MapCards.offer(rest, lastArena[pad], 2) do table.insert(options, id) end
	for i = #options, 2, -1 do local j = math.random(i); options[i], options[j] = options[j], options[i] end -- (the held one anywhere)
	local st: Stage = { pad = pad, sides = {}, site = site, arena = arena, room = room, options = options, votes = {},
		ends = os.clock() + ((script:GetAttribute("TestPadVote") :: number?) or Matches.PAD_VOTE), test = test, shown = {}, dirty = true }
	stageIn(st, sides)
	return nil
end
-- (CrossServer.luau, a match server: 18 Nov 2026, the owner's "custom matchmaking for queue outside of pads") everyone
-- the cross-server matchmaker sent here has arrived: the same map room and vote as a pad's, on three maps from the
-- rotation for teamSize (nil: any). go(map) starts the match once the pick has shown; cancel(note) if a whole side
-- leaves the room. false = no room or no maps (the caller starts straight away on the rotation). test: a Studio test
-- whose other side is a ghost (an empty side doesn't cancel it)
function Matches.voteRoom(sides: { { Player } }, teamSize: number?, go: (string) -> (), cancel: (string) -> (), test: boolean?): boolean
	local options = MapCards.offer(Arena.pool(teamSize), nil, 3)
	if #options == 0 then return false end
	local room = MapRooms.claim()
	if not room then return false end
	local st: Stage = { sides = {}, arena = options[1], room = room, options = options, votes = {},
		ends = os.clock() + ((script:GetAttribute("TestPadVote") :: number?) or Matches.PAD_VOTE), test = test == true, shown = {}, dirty = true,
		go = go, cancel = cancel }
	stageIn(st, sides)
	return true
end
-- (19 Nov 2026, the owner: "weapon ban at the start of match along with map select and banning maps too"; RankedDraft.luau)
-- a ranked match's draft in a map room, before it starts: each side bans a live primary (WBAN s: the side's most votes,
-- a tie drawn, none no ban), then one of three maps from the rotation for teamSize (MBAN s, the cards or the plates);
-- the map left is played (two left: drawn), shown SHOW s with the bans, then go(map, bans). cancel(note): a whole side
-- left the room. false = no room or no maps (start without it). test: a Studio test with a ghost side
local Roster = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Roster")) :: any
local MX: any = Matches -- (the draft's pieces stageSync, stageStep and padVote call, above)
function Matches.draftRoom(sides: { { Player } }, teamSize: number?, go: (string, { string }) -> (), cancel: (string) -> (), test: boolean?): boolean
	if not RankedDraft.ON then return false end
	local options = MapCards.offer(Arena.pool(teamSize), nil, 3)
	if #options == 0 then return false end
	local room = MapRooms.claim()
	if not room then return false end
	local wopts = {}
	for _, e in Roster.list do if e.slot == "primary" and e.live then table.insert(wopts, e.id) end end
	local side = {}
	for t, list in sides do for _, p in list do side[p.UserId] = t end end
	local st: Stage = { sides = {}, arena = options[1], room = room, options = options, votes = {},
		ends = os.clock() + ((script:GetAttribute("TestDraft") :: number?) or RankedDraft.WBAN), test = test == true, shown = {}, dirty = true,
		go = go :: any, cancel = cancel,
		draft = { phase = "wban", wopts = wopts, wvotes = {}, side = side, wbans = {}, mbans = {} } }
	stageIn(st, sides)
	return true
end
-- a player's view of a draft: the phase's cards, the clock, their side's votes, their own vote, the bans so far
MX.draftView = function(st: Stage, p: Player): any
	local d = st.draft
	local mySide = d.side[p.UserId]
	local function sideCounts(votes: { [number]: string }): { [string]: number }
		local out = {}
		for uid, id in votes do if d.side[uid] == mySide then out[id] = (out[id] or 0) + 1 end end
		return out
	end
	local ends = workspace:GetServerTimeNow() + math.max(0, st.ends - os.clock())
	local banned = {}
	for _, id in d.wbans do local e = Roster.byId[id]; table.insert(banned, if e then e.name else id) end
	if d.phase == "wban" then
		local opts = {}
		for _, id in d.wopts do local e = Roster.byId[id]; table.insert(opts, { id = id, title = if e then e.name else id }) end
		return { t = "padvote", kind = "wban", vote = { options = opts, ends = ends, counts = sideCounts(d.wvotes), mine = d.wvotes[p.UserId] } }
	end
	return { t = "padvote", kind = "mban", vote = { options = stageCards(st), ends = ends, counts = sideCounts(st.votes), mine = st.votes[p.UserId] },
		map = if st.map then padCard(st.map) else nil, banned = banned, mbanned = d.mbans }
end
MX.draftVote = function(st: Stage, p: Player, id: any): (boolean, string?)
	local d = st.draft
	if type(id) ~= "string" then return false, "?" end
	if d.phase == "wban" and os.clock() < st.ends and table.find(d.wopts, id) then
		d.wvotes[p.UserId] = id
		st.dirty = true
		return true, nil
	elseif d.phase == "mban" and os.clock() < st.ends and table.find(st.options, id) then
		st.votes[p.UserId] = id
		st.dirty = true
		return true, nil
	end
	return false, "not now"
end
-- each side's pick out of a set of votes (RankedDraft.top), one per side, no repeats
local function sideBans(st: Stage, votes: { [number]: string }, options: { string }): { string }
	local d = st.draft
	local out = {}
	for t = 1, #st.sides do
		local sv = {}
		for uid, id in votes do if d.side[uid] == t then sv[uid] = id end end
		local b = RankedDraft.top(sv, options)
		if b and not table.find(out, b) then table.insert(out, b) end
	end
	return out
end
MX.draftStep = function(st: Stage)
	local d = st.draft
	local t = os.clock()
	if d.phase == "mban" then
		-- standing on a display's plate is a ban for its map
		each2(st, function(p)
			local root = rootOf(p)
			local i = if root then MapRooms.plateAt(st.room, root.Position) else nil
			local id = if i then st.options[i] else nil
			if id and st.votes[p.UserId] ~= id then st.votes[p.UserId] = id; st.dirty = true end
		end)
	end
	if d.phase == "wban" and t >= st.ends then
		d.wbans = sideBans(st, d.wvotes, d.wopts)
		d.phase = "mban"
		st.ends = t + ((script:GetAttribute("TestDraft") :: number?) or RankedDraft.MBAN)
		st.dirty = true
	elseif d.phase == "mban" and t >= st.ends then
		d.mbans = sideBans(st, st.votes, st.options)
		local left = {}
		for _, id in st.options do if not table.find(d.mbans, id) then table.insert(left, id) end end
		if #left == 0 then left = table.clone(st.options) end
		st.map = left[math.random(#left)]
		st.arena = st.map :: string
		d.phase = "show"
		st.at = t + RankedDraft.SHOW
		st.dirty = true
	elseif d.phase == "show" and st.at and t >= st.at then
		stageEnd(st)
		if st.go then task.spawn(st.go :: any, st.arena, d.wbans) end
		return
	end
	if st.dirty then MapRooms.show(st.room, stageCards(st), MapCards.counts(st.votes), st.map) end
	stageSync(st)
	st.dirty = false
end
-- every padStep: leavers, the plates, the clock
local function stageStep()
	for _, st in table.clone(stages) do
		for _, list in st.sides do
			for k = #list, 1, -1 do
				local p = list[k]
				if not p.Parent or inMatch[p] or staged[p] ~= st then
					table.remove(list, k)
					if staged[p] == st then staged[p] = nil end
					st.dirty = true
				end
			end
		end
		local empty = false
		for _, list in st.sides do if #list == 0 then empty = true end end
		local anyone = false
		each2(st, function() anyone = true end)
		if not anyone or (empty and not st.test) then
			stageCancel(st, "the other side left: back to the hub")
			continue
		end
		if st.draft then (Matches :: any).draftStep(st); continue end -- (a ranked draft: its own phases, below)
		if not st.map then
			-- standing on a display's plate is a vote for it
			each2(st, function(p)
				local root = rootOf(p)
				local i = if root then MapRooms.plateAt(st.room, root.Position) else nil
				local id = if i then st.options[i] else nil
				if id and st.votes[p.UserId] ~= id then st.votes[p.UserId] = id; st.dirty = true end
			end)
			if os.clock() >= st.ends then stageSettle(st) end
		elseif st.at and os.clock() >= st.at then
			stageGo(st)
			continue
		end
		if st.dirty then MapRooms.show(st.room, stageCards(st), MapCards.counts(st.votes), st.map) end
		stageSync(st)
		st.dirty = false
	end
end
-- (Party.ops.padvote) a vote from a player in a map room
function Matches.padVote(p: Player, id: any): (boolean, string?)
	local st = staged[p]
	if not st then return false, "no map vote for you right now" end
	if st.draft then return (Matches :: any).draftVote(st, p, id) end
	if st.map or os.clock() >= st.ends then return false, "the map is picked" end
	if type(id) ~= "string" or not table.find(st.options, id) then return false, "not one of the three" end
	st.votes[p.UserId] = id
	st.dirty = true
	return true, nil
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
			if inMatch[p] or claimed[p] or staged[p] then continue end
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
		-- (Studio: a test fills the pad with one player, Matches.test "padfill")
		local tf = testFill[pad]
		if tf and (not tf.Parent or inMatch[tf]) then testFill[pad] = nil; tf = nil end
		if tf then
			for t = 1, teams do
				local i = table.find(sides[t], tf)
				if i then table.remove(sides[t], i) end
			end
			table.insert(sides[1], 1, tf)
			claimed[tf] = true
		end
		local full = true
		local counts = {}
		for t = 1, teams do
			if #sides[t] < size and not tf then full = false end
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
				stageStart(pad, s.sides, c.site, c.arena) -- (to a map room to vote on the map, then the match)
				sub = "GO!"
			else
				sub = ("MAP VOTE IN %d"):format(math.ceil(c.at - os.clock()))
			end
		else
			local m = padLast[pad]
			if m and m.on then sub = "match on · " .. hudText(m):gsub("<[^>]+>", "") end
		end
		padSign(pad, s.counts, sub)
	end
	padView = seen
	stageStep() -- (the map rooms: leavers, plates, clocks)
end

-- (OwnerDev.server: the owner's jail and red card in a match) take a player out of their match as if they'd left it:
-- off their team, their match marks off, the round and READY go on without them. the match has been flagged dev by
-- then, so nothing in it counts. their body stays where it is (the jail moves it). true if they were in one
function Matches.pull(p: Player): boolean
	local im = inMatch[p]
	if not im then return false end
	local m = im.m
	RankedDraft.stop(p)
	inMatch[p] = nil
	lastZone[p] = "hub"
	local list = m.teams[im.team]
	local i = list and table.find(list, p)
	if i then table.remove(list, i) end
	p:SetAttribute("Team", nil); p:SetAttribute("MatchHud", nil); p:SetAttribute("RoundEnds", nil); p:SetAttribute("Arena", nil); p:SetAttribute("LoadoutWindow", nil)
	p:SetAttribute("ReadyTeams", nil); p:SetAttribute("LoadoutReady", nil); p:SetAttribute("SpawnHold", nil)
	RoundR:FireClient(p, { hub = true })
	task.defer(checkRound, m)
	task.defer(function() pushReady(m); checkReady(m) end)
	return true
end

-- ------------------------------------------------------------------ wiring
function Matches.init(fight: any)
	Fight = fight
	hub = workspace:WaitForChild("Map"):WaitForChild("Hub")
	Fight.allow = Matches.allow
	Fight.spawnAt = spawnAt
	Fight.holdRespawn = function(f: Fighter): boolean
		local p = f.ref :: Player
		local im = inMatch[p]
		if im and im.m.rules then return im.m.rules.holdRespawn(im.m, f) end -- (a classic mode: you respawn, Modes.luau)
		return im ~= nil
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
			task.defer(function() pushReady(im.m); checkReady(im.m) end) -- (a leaver holds nobody up)
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
			-- (RoundLock: the grapple, the yank, the reel and the gadgets wait for GO. QuickMatch: QUICKPLAY's auto-lock)
			local lock = if Matches.roundLocked(p) then true else nil
			if p:GetAttribute("RoundLock") ~= lock then p:SetAttribute("RoundLock", lock) end
			local imq = inMatch[p]
			local quick = if imq and imq.m.quick and not imq.m.ranked then true else nil
			if p:GetAttribute("QuickMatch") ~= quick then p:SetAttribute("QuickMatch", quick) end
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
	-- READY: the client's lock-in (MatchLoadout)
	local rr = Remotes:FindFirstChild("MatchReady") or Instance.new("RemoteFunction")
	rr.Name = "MatchReady"
	;(rr :: RemoteFunction).OnServerInvoke = function(p: Player)
		local ok, why = Matches.ready(p)
		return { ok = ok, why = why }
	end
	rr.Parent = Remotes
	-- (Studio play tests only, like TestHook's JankTest: ServerStorage.JankMatchTest reaches the running server)
	if RunService:IsStudio() then
		local old = ServerStorage:FindFirstChild("JankMatchTest")
		if old then old:Destroy() end
		local fn = Instance.new("BindableFunction")
		fn.Name = "JankMatchTest"
		fn.OnInvoke = function(op: string, a: any, b: any, c: any, d: any, e: any): any return Matches.test(op, a, b, c, d, e) end
		fn.Parent = ServerStorage
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankMatchTest)
-- a play test has one player, so it can't fill two pads at once. "ghost" starts a match with nobody in it (pad name,
-- arena name or nil for the pad's next, seconds it lasts): it takes a site like any match, runs its rounds and ends
-- the normal way. with a player as the 4th argument that player plays it alone on team 1 (the stats test), and the
-- 5th is the team that wins when its time is up. "state" reads the live matches, the sites in use, the copies and
-- the pads' countdowns
function Matches.test(op: string, a: any, b: any, c: any, d: any, e: any): any
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
		if typeof(d) == "Instance" and d:IsA("Player") then sides[1] = { d } end
		local m = startMatch(pad, sides, site, arena)
		m.ghost = os.clock() + (if type(c) == "number" then c else 30)
		m.ghostWin = if type(e) == "number" then e else nil
		local sp = {}
		for t = 1, #sides do
			sp[t] = {}
			for _, cf in teamSpawns(m, t) do table.insert(sp[t], cf.Position) end
		end
		return { id = m.id, arena = arena, site = site.model:GetFullName(), copy = site.copy, pivot = site.model:GetPivot().Position, killY = Arena.killY(site.model), centreX = Arena.centreX(site.model), spawns = sp }
	elseif op == "padfill" then
		-- (the pads' map vote alone: pad a counts as full with player b on side 1; its match is held like a ghost match)
		local pads = hub:FindFirstChild("QueuePads")
		local pad = pads and pads:FindFirstChild(tostring(a))
		if not pad or not pad:IsA("Model") or typeof(b) ~= "Instance" or not b:IsA("Player") then return false end
		testFill[pad] = b :: Player
		return true
	elseif op == "padvotefor" then
		-- (a stand-in's vote in the map room pad a sent: voter id b for map c)
		for _, st in stages do
			if (if st.pad then st.pad.Name else "cross") == tostring(a) and not st.map and table.find(st.options, tostring(c)) then
				st.votes[tonumber(b) or -1] = tostring(c)
				st.dirty = true
				return true
			end
		end
		return false
	elseif op == "padstate" then
		-- (every map room: its pad, the held arena, the cards, the votes, the pick, the seconds to go)
		local out = {}
		for _, st in stages do
			local n = 0
			each2(st, function() n += 1 end)
			table.insert(out, { pad = if st.pad then st.pad.Name else "cross", arena = st.arena, options = st.options, counts = MapCards.counts(st.votes), map = st.map,
				left = st.ends - os.clock(), players = n, room = st.room.model:GetFullName() })
		end
		return out
	elseif op == "between" then
		-- (the loadout window test: player a's match as if its round had just been won; the next round starts b s later)
		local im = if typeof(a) == "Instance" then inMatch[a :: Player] else nil
		if not im then return nil end
		local m = im.m
		local wait = tonumber(b) or Matches.BETWEEN
		m.phase = "between"
		m.liveAt = os.clock() + wait + Matches.READY
		setHud(m)
		task.delay(wait, function() if m.on and m.phase == "between" then startRound(m) end end)
		return { round = m.round, opensFor = wait + Matches.READY }
	elseif op == "standin" then
		-- (the READY test: a pretend player in player a's match on team b (2), ready c; with d = its index, sets that one's
		-- ready to c instead. answers the board)
		local im = if typeof(a) == "Instance" then inMatch[a :: Player] else nil
		if not im then return nil end
		local m = im.m
		local list = m.standIns or {}
		m.standIns = list
		if type(d) == "number" and list[d] then list[d].ready = c == true
		else table.insert(list, { team = tonumber(b) or 2, ready = c == true }) end
		pushReady(m)
		checkReady(m)
		return { n = #list, board = readyBoard(m), phase = m.phase, locked = m.locked == true, liveIn = (m.liveAt or 0) - os.clock() }
	elseif op == "queued" then
		-- (a Play-queue match, ranked if b, player a alone on team 1, held c s like a ghost match)
		if typeof(a) ~= "Instance" then return nil end
		local m2, why = Matches.startQueued("1v1", { { a :: Player }, {} }, { queue = (if b then "ranked" else "casual") .. ":1v1", ranked = b == true, hold = tonumber(c) or 60 })
		return { ok = m2 ~= nil, why = why, ranked = m2 ~= nil and m2.ranked == true, arena = m2 and m2.arena }
	elseif op == "state" then
		local out = { live = {}, sites = {}, pads = {}, inMatch = 0, cap = maxLive() }
		for _, m in live do
			local n = 0
			each(m, function() n += 1 end)
			table.insert(out.live, { id = m.id, pad = m.pad.Name, arena = m.arena, site = m.site.model.Name, copy = m.site.copy, phase = m.phase, round = m.round, players = n, ghost = m.ghost ~= nil, private = m.private == true, ranked = m.ranked == true })
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
