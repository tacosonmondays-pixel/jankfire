--!strict
-- the server's fighters: every player and every test dummy, their HP (the server's number is the truth; the Humanoid
-- just shows it), deaths, kill credit, respawns, spawn picking, knockback and the FFA match (first to 20 or 6 minutes).
-- the rules themselves are in Rules.luau (pure, tested); this wires them to Roblox
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local R = {
	Dmg = Remotes:WaitForChild("Dmg") :: RemoteEvent,
	Kill = Remotes:WaitForChild("Kill") :: RemoteEvent,
	Knock = Remotes:WaitForChild("Knock") :: RemoteEvent,
	Round = Remotes:WaitForChild("Round") :: RemoteEvent,
	Spawn = Remotes:WaitForChild("Spawn") :: RemoteEvent,
	Callout = Remotes:WaitForChild("Callout") :: RemoteEvent,
}
local MatchState = ReplicatedStorage:WaitForChild("Match") :: Folder

type Fighter = Rules.Fighter
local Fight = {}
Fight.byPlayer = {} :: { [Player]: Fighter }
Fight.byModel = {} :: { [Model]: Fighter }
Fight.all = {} :: { Fighter }
Fight.live = true -- the round is on (false while the end screen shows)

local FFA = Weapons.FFA
local now = os.clock

-- ------------------------------------------------------------------ helpers
function Fight.model(f: Fighter): Model?
	if f.kind == "player" then return (f.ref :: Player).Character end
	return f.ref :: Model
end
function Fight.root(f: Fighter): BasePart?
	local m = Fight.model(f)
	return m and m:FindFirstChild("HumanoidRootPart") :: BasePart?
end
function Fight.hum(f: Fighter): Humanoid?
	local m = Fight.model(f)
	return m and m:FindFirstChildOfClass("Humanoid")
end
function Fight.eye(f: Fighter): Vector3?
	local r = Fight.root(f)
	return r and r.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0)
end
function Fight.feet(f: Fighter): Vector3?
	local r = Fight.root(f)
	return r and Hitbox.feet(r.Position)
end
function Fight.speed(f: Fighter): number
	local r = Fight.root(f)
	return if r then math.min(r.AssemblyLinearVelocity.Magnitude, 150 * Weapons.S) else 0
end
function Fight.facing(f: Fighter): Vector3
	local r = Fight.root(f)
	return if r then r.CFrame.LookVector else Vector3.zAxis
end
function Fight.of(x: any): Fighter?
	if typeof(x) ~= "Instance" then return nil end
	if x:IsA("Player") then return Fight.byPlayer[x :: Player] end
	if x:IsA("Model") then return Fight.byModel[x :: Model] end
	return nil
end

-- the solid map only (the city's look-only boxes are CanQuery = false), for line of sight and the marbles
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
function Fight.castMap(o: Vector3, d: Vector3, len: number): RaycastResult?
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	mapParams.FilterDescendantsInstances = { map }
	return workspace:Raycast(o, d * len, mapParams)
end
-- can `from` see any of the target's head, chest or feet + 1 m
function Fight.sees(from: Vector3, t: Fighter): boolean
	local feet = Fight.feet(t)
	if not feet then return false end
	return Rules.sees(function(o, d, l) return Fight.castMap(o, d, l) ~= nil end, from, feet)
end

-- ------------------------------------------------------------------ the weapon others see in your hand
local HAND_K = 3 * 1.5
function Fight.showWeapon(f: Fighter)
	local m = Fight.model(f)
	if not m then return end
	local old = m:FindFirstChild("HeldWeapon")
	if old then old:Destroy() end
	local hand = m:FindFirstChild("RightHand") :: BasePart? or m:FindFirstChild("Right Arm") :: BasePart?
	if not hand then return end
	local w = WeaponModels.build(f.held, HAND_K)
	if not w or not w.PrimaryPart then return end
	w.Name = "HeldWeapon"
	if f.held == "katana" then WeaponModels.setKatana(w, f.kat, HAND_K) end
	local grip = w.PrimaryPart:FindFirstChild("Grip") :: Attachment?
	local off = if grip then grip.Position else Vector3.zero
	-- in the fist, pointing where the forearm points (the arm is raised to the aim by the client's animation)
	w:PivotTo(hand.CFrame * CFrame.new(0, -hand.Size.Y * 0.35, 0) * CFrame.Angles(-math.pi / 2, 0, 0) * CFrame.new(-off))
	local weld = Instance.new("WeldConstraint")
	weld.Name = "HandWeld"; weld.Part0 = hand; weld.Part1 = w.PrimaryPart; weld.Parent = w.PrimaryPart
	w:SetAttribute("Weapon", f.held)
	w.Parent = m
end

-- ------------------------------------------------------------------ hp, knockback, kills
local function syncHp(f: Fighter)
	local hum = Fight.hum(f)
	if hum then
		hum.MaxHealth = Weapons.HP
		hum.Health = math.max(0, f.hp)
	end
	if f.kind == "player" then (f.ref :: Player):SetAttribute("Hp", math.max(0, math.ceil(f.hp))) end
end
Fight.syncHp = syncHp

-- knockback (studs/s): a player's own client moves them, so it goes to their client; a dummy is the server's
function Fight.knock(t: Fighter, v: Vector3, wid: string)
	if v.Magnitude < 1e-3 then return end
	if t.kind == "player" then
		R.Knock:FireClient(t.ref :: Player, v, wid)
	else
		local r = Fight.root(t)
		if r then r.AssemblyLinearVelocity += v end
	end
end

local function boardRow(f: Fighter): { any }
	return { f.name, f.kills, f.deaths, if f.kind == "player" then (f.ref :: Player).UserId else 0 }
end

local onKillHooks: { (Rules.KillInfo) -> () } = {}
function Fight.onKill(fn: (Rules.KillInfo) -> ()) table.insert(onKillHooks, fn) end

local function scheduleRespawn(f: Fighter)
	local delay = if f.kind == "dummy" then 3 else FFA.respawn
	task.delay(delay, function()
		if f.alive or not table.find(Fight.all, f) then return end
		if not Fight.live and f.kind == "player" then return end -- the end screen: everyone spawns with the next round
		Fight.spawn(f)
	end)
end

-- a death: the body flies apart with the hit (jank), the feed, the katana, the score
function Fight.died(info: Rules.KillInfo, vel: Vector3?)
	local v = info.v
	syncHp(v)
	local hum = Fight.hum(v)
	if hum and hum.Health > 0 then hum.Health = 0 end
	local m = Fight.model(v)
	if m and vel then
		task.defer(function()
			for _, p in m:GetDescendants() do
				if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
					p.AssemblyLinearVelocity = vel * 0.6 + Vector3.new(math.random() * 20 - 10, math.random() * 18, math.random() * 20 - 10)
					p.AssemblyAngularVelocity = Vector3.new(math.random() * 20 - 10, math.random() * 20 - 10, math.random() * 20 - 10)
				end
			end
		end)
	end
	local k = info.k
	if k and k.kind == "player" then
		local kp = k.ref :: Player
		kp:SetAttribute("Kat", k.kat)
		kp:SetAttribute("Kills", k.kills)
		local km = Fight.model(k)
		if km then km:SetAttribute("Kat", k.kat) end
		if (info.w == "katana" or info.w == "parry") and k.held == "katana" then Fight.showWeapon(k) end
	end
	if v.kind == "player" then
		local vp = v.ref :: Player
		vp:SetAttribute("Kat", 0); vp:SetAttribute("Deaths", v.deaths)
	end
	-- the feed (dummies never show in it, like the web game: the killer just gets "dummy down")
	R.Kill:FireAllClients({
		k = if k then k.name else nil, kid = if k and k.kind == "player" then (k.ref :: Player).UserId else nil,
		v = v.name, vid = if v.kind == "player" then (v.ref :: Player).UserId else nil, dummy = v.kind == "dummy",
		w = info.w, via = info.via, kat = if k then k.kat else nil,
	})
	for _, fn in onKillHooks do fn(info) end
	scheduleRespawn(v)
	Fight.checkWin()
end

-- the one way damage lands: knockback first (it lands even through spawn protection, like the web game), then HP
function Fight.hurt(t: Fighter, amt: number, by: Fighter?, wid: string, hs: boolean, kb: Vector3?, at: Vector3?): number
	if not Fight.live or not t.alive then return 0 end
	if kb then Fight.knock(t, kb, wid) end
	local done, info = Rules.damage(t, amt, by, wid, now())
	if done <= 0 and not info then return 0 end
	syncHp(t)
	R.Dmg:FireAllClients({
		to = if t.kind == "player" then (t.ref :: Player).UserId else nil, model = Fight.model(t),
		from = if by and by.kind == "player" then (by.ref :: Player).UserId else nil,
		a = math.floor(math.min(amt, 999) + 0.5), w = wid, hs = hs, ko = info ~= nil, at = at,
	})
	if info then Fight.died(info, if kb then kb else Vector3.new(0, 20, 0)) end
	return done
end

-- the street: "into the smog". whoever shoved you in the last 10 s gets it
function Fight.void(f: Fighter)
	if not f.alive then return end
	local info = Rules.kill(f, nil, "void", now())
	Fight.died(info, nil)
end

-- ------------------------------------------------------------------ spawning
local function spawnPoints(): { Vector3 }
	local out = {}
	local map = workspace:FindFirstChild("Map")
	local sp = map and map:FindFirstChild("Spawns", true)
	if sp then
		for _, s in sp:GetChildren() do
			if s:IsA("BasePart") then table.insert(out, s.Position + Vector3.new(0, 0.1, 0)) end
		end
	end
	if #out == 0 then table.insert(out, Vector3.new(0, 5, 0)) end
	return out
end
Fight.spawnPoints = spawnPoints

-- the spawn farthest from the nearest living enemy, plus a random 0-45 studs (MODES.md pickSpawn)
function Fight.pickSpawn(f: Fighter): Vector3
	local best, bestScore = nil, -math.huge
	for _, p in spawnPoints() do
		local near = 1e6
		for _, o in Fight.all do
			if o ~= f and o.alive and o.kind == "player" then
				local ft = Fight.feet(o)
				if ft then near = math.min(near, (ft - p).Magnitude) end
			end
		end
		local score = near + math.random() * 15 * Weapons.S
		if score > bestScore then best, bestScore = p, score end
	end
	return best :: Vector3
end

function Fight.spawn(f: Fighter)
	if f.kind ~= "player" then
		Rules.spawn(f, now())
		if f.ref and f.ref.Parent then f.ref:Destroy() end
		local make = Fight.makeDummy
		if make then make(f) end
		syncHp(f)
		return
	end
	local p = f.ref :: Player
	if not p.Parent then return end
	Rules.spawn(f, now())
	local at = Fight.pickSpawn(f)
	p:LoadCharacter()
	local ch = p.Character
	if not ch then return end
	-- no regen: HP is the server's
	local hs = ch:FindFirstChild("Health")
	if hs then hs:Destroy() end
	ch:PivotTo(CFrame.new(at + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)))
	R.Spawn:FireClient(p, at)
	syncHp(f)
	p:SetAttribute("Kat", 0)
	Fight.showWeapon(f)
	local hum = ch:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.BreakJointsOnDeath = true
		hum.Died:Connect(function()
			-- reset (Esc > Reset) or the engine: counts as a fall (whoever tagged you gets it)
			if f.alive and Fight.model(f) == ch then Fight.void(f) end
		end)
	end
end

-- ------------------------------------------------------------------ players
function Fight.addPlayer(p: Player): Fighter
	local f = Rules.newFighter("player", p.DisplayName, p)
	Fight.byPlayer[p] = f
	table.insert(Fight.all, f)
	p:SetAttribute("Kills", 0); p:SetAttribute("Deaths", 0); p:SetAttribute("Kat", 0)
	p.CharacterAdded:Connect(function(ch)
		Fight.byModel[ch] = f
		ch.AncestryChanged:Connect(function()
			if not ch.Parent and Fight.byModel[ch] == f then Fight.byModel[ch] = nil end
		end)
	end)
	task.defer(Fight.spawn, f)
	return f
end
function Fight.removePlayer(p: Player)
	local f = Fight.byPlayer[p]
	if not f then return end
	Fight.byPlayer[p] = nil
	local i = table.find(Fight.all, f)
	if i then table.remove(Fight.all, i) end
end

-- ------------------------------------------------------------------ the FFA match
local function setMatch(phase: string, endsAt: number)
	MatchState:SetAttribute("Phase", phase)
	MatchState:SetAttribute("EndsAt", endsAt)
	MatchState:SetAttribute("Target", FFA.kills)
end

-- the board: kills high to low, then deaths low to high (MODES.md endRound). dummies aren't on it
function Fight.board(): { { any } }
	local rows = {}
	for _, f in Fight.all do if f.kind == "player" then table.insert(rows, f) end end
	table.sort(rows, function(a, b)
		if a.kills ~= b.kills then return a.kills > b.kills end
		return a.deaths < b.deaths
	end)
	local out = {}
	for _, f in rows do table.insert(out, boardRow(f)) end
	return out
end

function Fight.startRound()
	Fight.live = true
	for _, f in Fight.all do
		f.kills, f.deaths, f.kat = 0, 0, 0
		if f.kind == "player" then
			local p = f.ref :: Player
			p:SetAttribute("Kills", 0); p:SetAttribute("Deaths", 0); p:SetAttribute("Kat", 0)
		end
	end
	setMatch("live", workspace:GetServerTimeNow() + FFA.time)
	for _, f in Fight.all do Fight.spawn(f) end
	R.Round:FireAllClients({ start = true, target = FFA.kills })
end

function Fight.endRound()
	if not Fight.live then return end
	Fight.live = false
	local board = Fight.board()
	local top = board[1]
	local winner = if top and top[2] >= 1 then top[1] else nil -- needs at least one kill
	setMatch("over", workspace:GetServerTimeNow() + FFA.over)
	R.Round:FireAllClients({ over = true, winner = winner, winnerId = if top and winner then top[4] else nil, board = board, next = FFA.over })
	task.delay(FFA.over, Fight.startRound)
end

function Fight.checkWin()
	if not Fight.live then return end
	for _, f in Fight.all do
		if f.kind == "player" and f.kills >= FFA.kills then Fight.endRound(); return end
	end
	local ends = MatchState:GetAttribute("EndsAt")
	if typeof(ends) == "number" and workspace:GetServerTimeNow() >= ends then Fight.endRound() end
end

function Fight.init()
	setMatch("live", workspace:GetServerTimeNow() + FFA.time)
	Players.CharacterAutoLoads = false
	-- spawns are picked by the server; no ForceField (spawn protection is a server check)
	for _, s in workspace:GetDescendants() do
		if s:IsA("SpawnLocation") then s.Duration = 0 end
	end
	for _, p in Players:GetPlayers() do Fight.addPlayer(p) end
	Players.PlayerAdded:Connect(Fight.addPlayer)
	Players.PlayerRemoving:Connect(Fight.removePlayer)
	task.spawn(function()
		while true do
			task.wait(0.5)
			Fight.checkWin()
		end
	end)
end

return Fight
