--!strict
-- the server's fighters: every player and every test dummy, their HP (the server's number is the truth; the Humanoid
-- just shows it), deaths, kill credit, respawns, spawn picking and knockback. the rules themselves are in Rules.luau
-- (pure, tested); this wires them to Roblox. who may hurt whom, where you spawn and whether you respawn are the hub's
-- call (Matches.luau sets Fight.allow / Fight.spawnAt / Fight.holdRespawn): matches are played from the hub's pads
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats")) -- (the hat on your gun, the loadout's Hats)
local Arena = require(Shared:WaitForChild("Arena"))
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
Fight.live = true
-- the hub's hooks (Matches.luau replaces these)
Fight.allow = function(_by: Fighter?, _t: Fighter): boolean return true end
Fight.holdRespawn = function(_f: Fighter): boolean return false end
Fight.spawnAt = nil :: ((Fighter) -> (Vector3, Vector3?))?
-- the items' hooks (Utility.luau replaces these): a shield bubble dropping a hit (by = the attacker; from = where
-- damage with nobody behind it came from), a smoke cloud in a sight line (bots' eyes)
Fight.blocks = function(_by: Fighter?, _t: Fighter, _from: Vector3?): boolean return false end
Fight.smokeBlocks = function(_a: Vector3, _c: Vector3): boolean return false end
-- a reverse card: does t send this hit back to by (Utility.luau)
Fight.reflects = function(_by: Fighter, _t: Fighter): boolean return false end
-- sitting a pop quiz, or the seconds after acing one: no damage from anyone else (Utility.luau; the shove still lands,
-- web room.js hitBlocked is checked in damage(), after the knock)
Fight.invulnerable = function(_t: Fighter): boolean return false end

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
-- the server's own record of where everyone's been (the last 0.75 s, sampled 30 times a second by Combat)
Fight.trail = {} :: { [Fighter]: { { t: number, p: Vector3 } } }
-- lag: a shooter sees you where you were a ping and an interpolation step ago, so hit checks (line of sight, "was
-- it aimed at them") look back this many seconds along your trail instead of only at where you are right now
Fight.LAG = 0.6
function Fight.track(n: number)
	for _, f in Fight.all do
		local r = Fight.root(f)
		if not r or not f.alive then Fight.trail[f] = nil; continue end
		local tr = Fight.trail[f] or {}
		Fight.trail[f] = tr
		table.insert(tr, { t = n, p = r.Position })
		while #tr > 0 and tr[1].t < n - 0.75 do table.remove(tr, 1) end
	end
	for k in Fight.trail do if not table.find(Fight.all, k) then Fight.trail[k] = nil end end
end
-- how fast the server SAW you move over the last 0.3 s (flat), or nil if it hasn't watched long enough
function Fight.seenSpeed(f: Fighter): number?
	local tr = Fight.trail[f]
	if not tr or #tr < 2 then return nil end
	local d, t0 = 0, nil
	for i = 2, #tr do
		if tr[i].t < now() - 0.3 then continue end
		t0 = t0 or tr[i - 1].t
		local a, b = tr[i - 1].p, tr[i].p
		local s = Vector3.new(b.X - a.X, 0, b.Z - a.Z).Magnitude
		if s < 1.5 * Weapons.S then d += s end
	end
	local dt = if t0 then tr[#tr].t - t0 else 0
	return if dt < 0.15 then nil else d / dt
end
-- the speed allowance on range / reach: what your character claims, capped at 1.25x what the server saw (0 for the
-- first 0.25 s of a life), so a faked velocity can't stretch your reach (web room.js speedOf)
function Fight.speed(f: Fighter): number
	local r = Fight.root(f)
	if not r or now() - f.spawnT < 0.25 then return 0 end
	local seen = Fight.seenSpeed(f)
	return math.min(r.AssemblyLinearVelocity.Magnitude, 1.25 * (seen or 0))
end
-- where a parrier faces: where they looked when they opened the guard (body facing lags in third person)
function Fight.facing(f: Fighter): Vector3
	if f.parryYaw then return Vector3.new(-math.sin(f.parryYaw), 0, -math.cos(f.parryYaw)) end
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
-- where the target's feet are and were: now first, then back along the trail for Fight.LAG seconds
function Fight.path(t: Fighter): { Vector3 }
	local out = {}
	local feet = Fight.feet(t)
	if feet then table.insert(out, feet) end
	local tr = Fight.trail[t]
	if tr then
		local n = now()
		for i = #tr, 1, -1 do
			if n - tr[i].t > Fight.LAG then break end
			table.insert(out, Hitbox.feet(tr[i].p))
		end
	end
	return out
end
-- can `from` see any of the target's head, chest or feet + 1 m: where they are now, or (lag) where they were a moment
-- ago, so a hit that landed just before they reached cover still counts. the look back tries every 4th sample
-- (about every 0.13 s), so a blocked shot costs a handful of rays, not dozens
function Fight.sees(from: Vector3, t: Fighter): boolean
	local function cast(o: Vector3, d: Vector3, l: number): boolean return Fight.castMap(o, d, l) ~= nil end
	local path = Fight.path(t)
	if #path == 0 then return false end
	if Rules.sees(cast, from, path[1]) then return true end
	for i = 5, #path, 4 do
		if Rules.sees(cast, from, path[i]) then return true end
	end
	return false
end

-- ------------------------------------------------------------------ the weapon others see in your hand
local HAND_K = 3 * 1.5
-- the hub is weapons-free (owner, 2026-11-14): a player standing in the hub (Zone "hub") holds nothing; the training
-- room and matches arm you as usual. HubHolster re-runs this whenever your Zone changes
function Fight.holstered(f: Fighter): boolean
	return f.kind == "player" and (f.ref :: Player):GetAttribute("Zone") == "hub"
end
function Fight.showWeapon(f: Fighter)
	local m = Fight.model(f)
	if not m then return end
	local old = m:FindFirstChild("HeldWeapon")
	if old then old:Destroy() end
	if Fight.holstered(f) then return end
	local hand = m:FindFirstChild("RightHand") :: BasePart? or m:FindFirstChild("Right Arm") :: BasePart?
	if not hand then return end
	local w = WeaponModels.build(f.held, HAND_K)
	if not w or not w.PrimaryPart then return end
	w.Name = "HeldWeapon"
	if f.held == "katana" then WeaponModels.setKatana(w, f.kat, HAND_K) end
	if f.kind == "player" then -- its wrap (the loadout screen), so everyone sees your paint job
		local wid, md = WeaponModels.wrapFor(f.ref :: Player, f.held)
		if wid then WeaponModels.wrap(w, wid, md) end
		GunHats.attach(w, f.held, GunHats.hatFor(f.ref :: Player, f.held), HAND_K, nil, GunHats.THIRD) -- and its hat
	end
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
-- every bit of HP that really comes off someone: (victim, hp taken, by, weapon). matches count damage dealt with it
local onHurtHooks: { (Fighter, number, Fighter?, string) -> () } = {}
function Fight.onHurt(fn: (Fighter, number, Fighter?, string) -> ()) table.insert(onHurtHooks, fn) end

local function scheduleRespawn(f: Fighter)
	local delay = if f.kind == "dummy" then 3 else FFA.respawn
	task.delay(delay, function()
		if f.alive or not table.find(Fight.all, f) then return end
		if f.kind == "player" and Fight.holdRespawn(f) then return end -- in a match: you're back with the next round
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
	scheduleRespawn(v)
	for _, fn in onKillHooks do fn(info) end
end

-- the one way damage lands: knockback first (it lands even through spawn protection, like the web game), then HP.
-- a shield bubble drops the whole hit, shove and all (web hurt: bubbleBlocks before knock). from = where damage with
-- nobody behind it came from (a frag whose thrower has left). plain = straight to HP, no dome or card asked (web
-- room.js damage(): the duck's crush and its near-the-middle damage)
function Fight.hurt(t: Fighter, amt: number, by: Fighter?, wid: string, hs: boolean, kb: Vector3?, at: Vector3?, from: Vector3?, plain: boolean?): number
	if not t.alive or not Fight.allow(by, t) then return 0 end
	if not plain and Fight.blocks(by, t, from) then return 0 end
	-- a reverse card up: the whole hit goes back to whoever sent it, its shove mirrored (web hurt)
	if not plain and by and by ~= t and by.alive and Fight.reflects(by, t) then
		t, by = by, t
		if kb then kb = Vector3.new(-kb.X, kb.Y, -kb.Z) end
		local r = Fight.root(t)
		at = if r then r.Position else nil
	end
	if kb then Fight.knock(t, kb, wid) end
	-- (a shove with no damage still marks who did it, so a fall now is theirs: web hurt tags every hit)
	if by and amt <= 0 and kb then Rules.tagged(t, by, wid, now()) end
	if by and by ~= t and Fight.invulnerable(t) then return 0 end
	local done, info = Rules.damage(t, amt, by, wid, now())
	if done <= 0 and not info then return 0 end
	if done > 0 then for _, fn in onHurtHooks do fn(t, done, by, wid) end end
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
	local arena = Arena.get() -- (the Rooftop v1 or v2: workspace.Map's attribute Arena)
	local sp = arena and arena:FindFirstChild("Spawns")
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

-- after a player's spawn (Loadout.luau: tell the client its keys, hand out the Shredder)
local spawnHooks: { (Fighter) -> () } = {}
function Fight.onSpawn(fn: (Fighter) -> ()) table.insert(spawnHooks, fn) end

local spawning: { [Fighter]: boolean } = {}
function Fight.spawn(f: Fighter)
	if f.kind ~= "player" then
		Rules.spawn(f, now())
		if f.ref then Fight.byModel[f.ref] = nil; if f.ref.Parent then f.ref:Destroy() end end
		local make = Fight.makeDummy
		if make then make(f) end
		syncHp(f)
		return
	end
	local p = f.ref :: Player
	if not p.Parent or spawning[f] then return end
	-- the new body first (LoadCharacter yields), THEN alive: until then hits on the old body can't land on the new life
	spawning[f] = true
	local old = p.Character
	if old then Fight.byModel[old] = nil end
	local at, face = Fight.pickSpawn(f), nil
	if Fight.spawnAt then at, face = Fight.spawnAt(f) end
	local ok = pcall(function() p:LoadCharacter() end)
	spawning[f] = nil
	local ch = p.Character
	if not ok or not ch or not p.Parent or f.alive or not table.find(Fight.all, f) then return end
	Rules.spawn(f, now())
	-- no regen: HP is the server's
	local hs = ch:FindFirstChild("Health")
	if hs then hs:Destroy() end
	local pos = at + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)
	local look = if face and Vector3.new(face.X, 0, face.Z).Magnitude > 1e-3 then Vector3.new(face.X, 0, face.Z).Unit else nil
	ch:PivotTo(if look then CFrame.lookAt(pos, pos + look) else CFrame.new(pos))
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
	for _, fn in spawnHooks do task.spawn(fn, f) end
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

-- ------------------------------------------------------------------ the end-of-match board
-- kills high to low, then deaths low to high (MODES.md endRound). dummies aren't on it. only = just these fighters
function Fight.board(only: { Fighter }?): { { any } }
	local rows = {}
	for _, f in only or Fight.all do if f.kind == "player" then table.insert(rows, f) end end
	table.sort(rows, function(a, b)
		if a.kills ~= b.kills then return a.kills > b.kills end
		return a.deaths < b.deaths
	end)
	local out = {}
	for _, f in rows do table.insert(out, boardRow(f)) end
	return out
end

function Fight.init()
	-- (the old free-for-all clock is gone: matches are played from the hub's pads)
	MatchState:SetAttribute("Phase", "hub")
	MatchState:SetAttribute("EndsAt", nil)
	MatchState:SetAttribute("Target", nil)
	Players.CharacterAutoLoads = false
	-- spawns are picked by the server; no ForceField (spawn protection is a server check)
	for _, s in workspace:GetDescendants() do
		if s:IsA("SpawnLocation") then s.Duration = 0 end
	end
	for _, p in Players:GetPlayers() do Fight.addPlayer(p) end
	Players.PlayerAdded:Connect(Fight.addPlayer)
	Players.PlayerRemoving:Connect(Fight.removePlayer)
end

return Fight
