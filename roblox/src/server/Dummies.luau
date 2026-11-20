--!strict
-- the training room's dummies (behind the hub's spawn), so one person can try everything: "Dummy" strafes back and
-- forth (shoot it, slice it, marble it), "Plinker" stands on its block and fires short Redline bursts at whoever's in
-- the training room (feel getting shot, practise the katana parry on real bullets), and the yellow "Stand"s just
-- stand there. they never count for score or the kill feed (like the web game's training dummies), but they do grow
-- your katana. where they stand: the hub's DummySpots
-- since 16 Nov (the owner: "an area where you can activate dummies that shoot back, that way they don't shoot into the
-- main hub area of the training"): the shooters ("Plinker", "Plinker2") stand at the far corners of the yard's live-fire
-- end and stay quiet until someone holds E at the console on its line; then for 90 s (or until the end has stood empty
-- for 8 s) they fire at whoever is inside the end, and their shots never cross the line. the end is
-- Hub.TrainingGround.LiveFire (TrainingV2): Zone (its box), LiveButton (with the Prompt), lamps (attribute Lamp), and
-- the attribute Line (the z the shots stop at). the dummies are cardboard-coloured with a ring on the chest now, the
-- shooters slate with a red one, and no name tags. since 18 Nov: rails, the practice lane and the heal pads (below)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Arena = require(Shared:WaitForChild("Arena"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local ShotR = Remotes:WaitForChild("Shot") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent

type Fighter = Rules.Fighter
local Dummies = {}
local S = Weapons.S
local list: { Fighter } = {}
type Brain = { home: Vector3, side: number, flip: number, shoot: number, slipUntil: number, span: number?, speed: number?, every: number?, lane: boolean, jumpT: number,
	armour: boolean?, healBack: number?, hurtAt: number? }
local brain: { [Fighter]: Brain } = {}
local Fight: any
local applyHitscan: any
local TAN, SLATE, LEGS = Color3.fromRGB(180, 154, 122), Color3.fromRGB(98, 102, 111), Color3.fromRGB(74, 78, 87)
local RED, PALE = Color3.fromRGB(200, 70, 60), Color3.fromRGB(236, 234, 228)
local LIGHT, HEAVY = Color3.fromRGB(214, 200, 178), Color3.fromRGB(122, 104, 86) -- (the practice lane's 50 and 300 HP dummies)
local function shooter(name: string): boolean return string.sub(name, 1, 7) == "Plinker" end

-- the practice lane (18 Nov, the owner: "can the training hub be like the overwatch training one to an extent like the
-- indoor part except for the shoot range"): the yard's side hall's three run on rails (a spot's Span: studs each way,
-- Speed: walk speed; any spot with a Span is a rail: the yard's strafer and the course's Runner too), and two consoles at
-- the lane's start set, for everyone in it, how they act (BEHAVIOUR: strafe, strafe and jump, shoot back, still) and
-- their health (HEALTH: 100, 300, 50). shoot back is the live-fire shooters' burst, at players inside the side hall only.
-- the lane is Hub.TrainingGround.Practice (TrainingV2): Zone, BehaviourButton and HealthButton (each with a Prompt),
-- Board (PracticeBoard.client paints it). heal pads anywhere in the training ground: a Model with the attributes Heal
-- (HP) and Every (s); its HealPlus parts dim while it comes back
local MODES = { "strafe", "jump", "shoot", "still" }
local MODE_TEXT = { strafe = "Strafe", jump = "Strafe and jump", shoot = "Shoot back", still = "Still" }
local CLASSES = { 100, 300, 50 }
local practice = { mode = "strafe", hp = 100 }
local pf: Instance? = nil
local pads: { { m: Model, at: Vector3, heal: number, every: number, readyAt: number } } = {}
local function laneShoots(f: Fighter): boolean
	local b = brain[f]
	return b ~= nil and b.lane and practice.mode == "shoot"
end
local function inPractice(pos: Vector3): boolean
	local z = (pf and pf:FindFirstChild("Zone")) :: BasePart?
	if not z then return false end
	local rel = z.CFrame:PointToObjectSpace(pos)
	local h = z.Size / 2
	return math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z
end

-- the live-fire end
local LIVE_FOR, EMPTY_FOR = 90, 8
local live, liveUntil, lastIn, lookAt = false, 0, 0, 0
local lf: Instance? = nil
local function liveFolder(): Instance?
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local tg = hub and hub:FindFirstChild("TrainingGround")
	return tg and tg:FindFirstChild("LiveFire")
end
local function inLive(pos: Vector3): boolean
	local z = lf and lf:FindFirstChild("Zone") :: BasePart?
	if not z then return false end
	local rel = z.CFrame:PointToObjectSpace(pos)
	local h = z.Size / 2
	return math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z
end
local function setLive(on: boolean, by: Player?)
	live = on
	liveUntil = if on then os.clock() + LIVE_FOR else 0
	lastIn = os.clock()
	local f = lf
	if not f then return end
	f:SetAttribute("Live", on)
	for _, d in f:GetDescendants() do
		if d:IsA("BasePart") and d:GetAttribute("Lamp") then
			d.Material = if on then Enum.Material.Neon else Enum.Material.SmoothPlastic
			d.Color = if on then Color3.fromRGB(255, 72, 54) elseif d.Name == "LiveButton" then Color3.fromRGB(138, 58, 51) else Color3.fromRGB(107, 74, 70)
			for _, l in d:GetChildren() do if l:IsA("Light") then l.Enabled = on end end
		elseif d:IsA("ProximityPrompt") then
			d.ActionText = if on then "Live fire off" else "Live fire on"
		end
	end
	for _, p in Players:GetPlayers() do
		if p:GetAttribute("Zone") == "training" and (p == by or inLive((p.Character and p.Character:GetPivot().Position) or Vector3.zero)) then
			CalloutR:FireClient(p, if on then "LIVE FIRE · THE TWO AT THE BACK SHOOT BACK" else "LIVE FIRE OFF", 1.8)
		end
	end
end

local folder = Instance.new("Folder")
folder.Name = "Dummies"
folder.Parent = workspace

-- a plain R15 if the engine will make one, else a box mannequin with a wrong knee (jank)
local function body(name: string, color: Color3): Model
	local ok, m = pcall(function()
		local d = Instance.new("HumanoidDescription")
		d.HeadColor, d.TorsoColor = color, color
		d.LeftArmColor, d.RightArmColor, d.LeftLegColor, d.RightLegColor = color, color, LEGS, LEGS
		return Players:CreateHumanoidModelFromDescription(d, Enum.HumanoidRigType.R15)
	end)
	if ok and m then (m :: Model).Name = name; return m :: Model end
	local mm = Instance.new("Model")
	mm.Name = name
	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"; root.Size = Vector3.new(2, 2, 1); root.Transparency = 1; root.CanCollide = false
	root.Parent = mm
	local function limb(n: string, size: Vector3, off: Vector3, col: Color3)
		local p = Instance.new("Part")
		p.Name = n; p.Size = size; p.Color = col; p.CFrame = root.CFrame * CFrame.new(off) * CFrame.Angles(0, 0, if n == "LeftLeg" then 0.2 else 0)
		local w = Instance.new("Weld"); w.Part0 = root; w.Part1 = p; w.C0 = CFrame.new(off); w.Parent = p
		p.Parent = mm
	end
	limb("UpperTorso", Vector3.new(2, 2, 1), Vector3.new(0, 0, 0), color)
	limb("Head", Vector3.new(1.2, 1.2, 1.2), Vector3.new(0, 1.6, 0), color)
	limb("LeftLeg", Vector3.new(0.9, 2, 0.9), Vector3.new(-0.5, -2, 0), Color3.fromRGB(40, 40, 50))
	limb("RightLeg", Vector3.new(0.9, 2, 0.9), Vector3.new(0.5, -2, 0), Color3.fromRGB(40, 40, 50))
	local hum = Instance.new("Humanoid"); hum.HipHeight = 2; hum.Parent = mm
	mm.PrimaryPart = root
	return mm
end

local function make(f: Fighter)
	local plinker = shooter(f.name) or laneShoots(f)
	local b0 = brain[f]
	local max = f.maxHp or Weapons.HP
	local tone = if plinker then SLATE elseif b0 and b0.lane and max > Weapons.HP then HEAVY elseif b0 and b0.lane and max < Weapons.HP then LIGHT else TAN
	local m = body(f.name, tone)
	-- a target ring on the chest (red on the shooters, so you know which ones shoot back)
	local torso = (m:FindFirstChild("UpperTorso") or m:FindFirstChild("Torso")) :: BasePart?
	if torso then
		for i, r in { { 1.7, if plinker then RED else PALE }, { 0.8, if plinker then PALE else RED } } do
			local disc = Instance.new("Part")
			disc.Name = "Ring"; disc.Shape = Enum.PartType.Cylinder; disc.Size = Vector3.new(0.12, r[1], r[1])
			disc.Color = r[2]; disc.Material = Enum.Material.SmoothPlastic; disc.CanCollide = false; disc.CanQuery = false
			disc.CanTouch = false; disc.Massless = true; disc.CastShadow = false
			disc.CFrame = torso.CFrame * CFrame.new(0, 0.15, -(torso.Size.Z / 2 + 0.04 + 0.05 * i)) * CFrame.Angles(0, math.pi / 2, 0)
			local w = Instance.new("WeldConstraint"); w.Part0 = torso; w.Part1 = disc; w.Parent = disc
			disc.Parent = m
		end
	end
	-- (20 Nov 2026, the training redo's dummy yard) an ARMOURED one (a spot's HP over 100) wears a slate plate round the
	-- ring; a HEAL-BACK one (HealBack: s after your last hit it is whole again) has a pale cross over its ring
	local bb = brain[f]
	if torso and bb and (bb.armour or bb.healBack) then
		local function bit(name: string, size: Vector3, off: CFrame, col: Color3)
			local q = Instance.new("Part")
			q.Name = name; q.Size = size; q.Color = col; q.Material = Enum.Material.SmoothPlastic
			q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.Massless = true; q.CastShadow = false
			q.CFrame = (torso :: BasePart).CFrame * off
			local w = Instance.new("WeldConstraint"); w.Part0 = torso; w.Part1 = q; w.Parent = q
			q.Parent = m
		end
		local fz = -((torso :: BasePart).Size.Z / 2 + 0.03)
		if bb.armour then
			bit("Plate", Vector3.new(2.3, 2.1, 0.12), CFrame.new(0, 0.05, fz), SLATE)
			bit("PlateRim", Vector3.new(2.5, 0.22, 0.2), CFrame.new(0, 1.12, fz), PALE)
		end
		if bb.healBack then
			bit("Cross", Vector3.new(0.7, 0.18, 0.1), CFrame.new(0, 1.05, fz - 0.1), PALE)
			bit("Cross", Vector3.new(0.18, 0.7, 0.1), CFrame.new(0, 1.05, fz - 0.1), PALE)
		end
	end
	local b = brain[f]
	local at = b.home + Vector3.new(0, Hitbox.ROOT_UP + 0.5, 0)
	m:PivotTo(CFrame.lookAt(at, at + Vector3.zAxis)) -- facing the training room's door
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.MaxHealth, hum.Health = Weapons.HP, Weapons.HP
		hum.WalkSpeed = 22 -- quick enough to slip on marbles (safe speed is 16.5)
		hum.BreakJointsOnDeath = true
		hum.DisplayName = f.name
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	end
	local hs = m:FindFirstChild("Health")
	if hs then hs:Destroy() end
	m:SetAttribute("Dummy", true)
	m.Parent = folder
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then pcall(function() root:SetNetworkOwner(nil) end) end
	f.ref = m
	Fight.byModel[m] = f
	f.held = if plinker then "redline" else "katana"
	Fight.showWeapon(f)
end

-- on marbles: feet out the way it was going, flat on its back for the slip
function Dummies.slip(f: Fighter)
	local b = brain[f]
	local hum = Fight.hum(f)
	local root = Fight.root(f)
	if not b or not hum or not root then return end
	b.slipUntil = os.clock() + Weapons.SLIP.time
	local v = root.AssemblyLinearVelocity
	local flat = Vector3.new(v.X, 0, v.Z)
	local d = if flat.Magnitude > 0.1 then flat.Unit else root.CFrame.LookVector
	hum.PlatformStand = true
	root.AssemblyLinearVelocity = v + d * (4 * S) + Vector3.new(0, Weapons.SLIP.up, 0)
	root.AssemblyAngularVelocity = Vector3.new(d.Z, 0, -d.X) * 8
end

-- the Plinker's burst: the server's own ray from its eye (a bot fires on the server, web botFire), same spread maths
local function plink(f: Fighter, lane: boolean?)
	if not lane and not live then return end
	local eye = Fight.eye(f)
	if not eye then return end
	local best, bestD = nil, 60 * S
	for _, t in Fight.all do
		-- (not someone mid-run at Cardboard Carl's: the sign there says nobody shoots back; not anyone out on the back
		-- lot behind the garage door, TheLot.server.luau)
		if t.kind == "player" and t.alive and (t.ref :: Player):GetAttribute("Zone") == "training" and not (t.ref :: Player):GetAttribute("RangeRun") and not (t.ref :: Player):GetAttribute("OnLot") then
			local c = Fight.root(t)
			-- (nor through smoke: the web game's bots can't see through it either, room.js canSee)
			if c and (if lane then inPractice(c.Position) else inLive(c.Position)) and (c.Position - eye).Magnitude < bestD and Fight.sees(eye, t) and not (Fight.smokeBlocks and Fight.smokeBlocks(eye, c.Position)) then best, bestD = t, (c.Position - eye).Magnitude end
		end
	end
	if not best then return end
	local w = Weapons.list.redline
	local root = Fight.root(f)
	if root then
		local tc = (Fight.root(best) :: BasePart).Position
		root.CFrame = CFrame.lookAt(root.Position, Vector3.new(tc.X, root.Position.Y, tc.Z))
	end
	local shots = if lane then 3 else 5
	task.spawn(function()
		for _ = 1, shots do
			if not f.alive or not best.alive or not Fight.live then return end
			local tr = Fight.root(best)
			local e = Fight.eye(f)
			if not tr or not e then return end
			local tf = Hitbox.feet(tr.Position)
			local aim = (tf + Vector3.new(0, 3.5, 0) - e).Unit
			local d = Hitbox.spreadDir(aim, (w.spread :: number) * 1 + 0.045, math.random(), math.random())
			local cap = w.range :: number
			local line = if lane then nil else lf and lf:GetAttribute("Line")
			if type(line) == "number" and d.Z > 1e-4 then cap = math.min(cap, math.max(0, (line - e.Z) / d.Z)) end -- (never past the line)
			local hitMap = Fight.castMap(e, d, cap)
			local mapT = if hitMap then (hitMap.Position - e).Magnitude else cap
			local t, head = Hitbox.ray(e, d, tf, Hitbox.distScale((tf - e).Magnitude))
			local endT = mapT
			if t and t < mapT then
				endT = t
				applyHitscan(f, best, "redline", 1, if head then 1 else 0, e)
			end
			for _, o in Players:GetPlayers() do ShotR:FireClient(o, { model = Fight.model(f), w = "redline", ends = { e + d * endT } }) end
			task.wait(1 / Weapons.fireRate(w, f.hp))
		end
	end)
end

-- (20 Nov 2026: the tutorial rooms' practice turret, Tutorials.server) a short Redline burst from f at t, through the same
-- hitscan as the shooters above, so the katana's guard and crit return, a shield bubble, a reverse card and smoke all
-- work on it as on any shooter. no zone rules here: the caller picks who
function Dummies.burst(f: Fighter, t: Fighter, shots: number)
	if not Fight or not applyHitscan then return end
	local w = Weapons.list.redline
	task.spawn(function()
		for _ = 1, shots do
			if not f.alive or not t.alive or not Fight.live then return end
			local tr = Fight.root(t)
			local e = Fight.eye(f)
			if not tr or not e then return end
			if Fight.smokeBlocks and Fight.smokeBlocks(e, tr.Position) then return end
			local tf = Hitbox.feet(tr.Position)
			local aim = (tf + Vector3.new(0, 3.5, 0) - e).Unit
			local d = Hitbox.spreadDir(aim, (w.spread :: number) + 0.03, math.random(), math.random())
			local cap = w.range :: number
			local hitMap = Fight.castMap(e, d, cap)
			local mapT = if hitMap then (hitMap.Position - e).Magnitude else cap
			local hitT, head = Hitbox.ray(e, d, tf, Hitbox.distScale((tf - e).Magnitude))
			local endT = mapT
			if hitT and hitT < mapT then
				endT = hitT
				applyHitscan(f, t, "redline", 1, if head then 1 else 0, e)
			end
			for _, o in Players:GetPlayers() do ShotR:FireClient(o, { model = Fight.model(f), w = "redline", ends = { e + d * endT } }) end
			task.wait(0.17)
		end
	end)
end

-- the practice lane's consoles and the heal pads (found again whenever the training ground is rebuilt)
local function practiceFolder(): Instance?
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local tg = hub and hub:FindFirstChild("TrainingGround")
	return tg and tg:FindFirstChild("Practice")
end
local function promptOf(name: string): ProximityPrompt?
	local b = pf and pf:FindFirstChild(name)
	local p = b and b:FindFirstChild("Prompt")
	return if p and p:IsA("ProximityPrompt") then p else nil
end
local function paintConsoles()
	local a = promptOf("BehaviourButton")
	if a then a.ObjectText = "Dummies: " .. MODE_TEXT[practice.mode]; a.ActionText = "Change" end
	local h = promptOf("HealthButton")
	if h then h.ObjectText = "Dummy health: " .. practice.hp; h.ActionText = "Change" end
end
local function respawnLane()
	for _, f in list do
		local b = brain[f]
		if b and b.lane then
			f.maxHp = if practice.hp ~= Weapons.HP then practice.hp else nil
			b.flip, b.jumpT, b.shoot = 0, 0, os.clock() + 1.5
			Fight.spawn(f)
		end
	end
end
local function nextIn<T>(t: { T }, v: T): T
	local i = table.find(t, v) or 0
	return t[i % #t + 1]
end
local function wirePractice()
	local f = practiceFolder()
	if f == pf then return end
	pf = f
	local a = promptOf("BehaviourButton")
	if a then a.Triggered:Connect(function() if pf == f then practice.mode = nextIn(MODES, practice.mode); respawnLane(); paintConsoles() end end) end
	local h = promptOf("HealthButton")
	if h then h.Triggered:Connect(function() if pf == f then practice.hp = nextIn(CLASSES, practice.hp); respawnLane(); paintConsoles() end end) end
	paintConsoles()
	table.clear(pads)
	local tg = f and f.Parent
	if tg then
		for _, m in tg:GetDescendants() do
			local heal = m:GetAttribute("Heal")
			if m:IsA("Model") and type(heal) == "number" then
				local every = m:GetAttribute("Every")
				table.insert(pads, { m = m, at = m:GetPivot().Position, heal = heal, every = if type(every) == "number" then every else 10, readyAt = 0 })
			end
		end
	end
end
local function dimPad(m: Model, used: boolean)
	m:SetAttribute("Ready", not used)
	for _, d in m:GetDescendants() do if d:IsA("BasePart") and d.Name == "HealPlus" then d.Transparency = if used then 0.8 else 0 end end
end
-- a heal pad: stand on it with less than your full health and it gives you Heal HP, then comes back after Every s
local function tickPads(n: number)
	for _, pd in pads do
		if not pd.m.Parent or n < pd.readyAt then continue end
		if pd.m:GetAttribute("Ready") == false then dimPad(pd.m, false) end
		for _, p in Players:GetPlayers() do
			local fp = Fight.of(p)
			local ch = p.Character
			local r = (ch and ch:FindFirstChild("HumanoidRootPart")) :: BasePart?
			if not fp or not fp.alive or not r then continue end
			local d = r.Position - pd.at
			if Vector3.new(d.X, 0, d.Z).Magnitude > 2.6 or d.Y < -1 or d.Y > 6 then continue end
			local max = fp.maxHp or Weapons.HP
			if fp.hp >= max then continue end
			fp.hp = math.min(max, fp.hp + pd.heal)
			Fight.syncHp(fp)
			pd.readyAt = n + pd.every
			dimPad(pd.m, true)
			break
		end
	end
end

function Dummies.tick(n: number)
	if not Fight then return end
	if n - lookAt > 2 then -- (the end can be rebuilt: find it again, wire its console)
		lookAt = n
		local f = liveFolder()
		if f ~= lf then
			lf = f
			live = false
			local b = f and f:FindFirstChild("LiveButton")
			local pr = b and b:FindFirstChild("Prompt")
			if pr and pr:IsA("ProximityPrompt") then
				pr.Triggered:Connect(function(p: Player) if lf == f then setLive(not live, p) end end)
			end
			setLive(false)
		end
		wirePractice()
	end
	tickPads(n)
	if live then
		for _, p in Players:GetPlayers() do
			local ch = p.Character
			local r = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r and inLive(r.Position) then lastIn = n; break end
		end
		if n > liveUntil or n - lastIn > EMPTY_FOR then setLive(false) end
	end
	local killY = Arena.killY() -- (the arena's: the Rooftop v1 or v2)
	for _, f in list do
		local b = brain[f]
		local hum, root = Fight.hum(f), Fight.root(f)
		if not f.alive or not hum or not root then continue end
		if root.Position.Y < (killY :: number) then Fight.void(f); continue end
		if hum.PlatformStand and n > b.slipUntil then hum.PlatformStand = false; hum:ChangeState(Enum.HumanoidStateType.GettingUp) end
		local span = b.span
		if span and not (b.lane and practice.mode == "still") and n > b.flip and not hum.PlatformStand then
			-- (a rail: to one end and back at its own speed; the yard's first strafer keeps its 1.6 s flip)
			local sp = b.speed or 22
			hum.WalkSpeed = sp
			b.side = -b.side
			b.flip = n + (b.every or (2 * span / sp + 0.35))
			hum:MoveTo(b.home + Vector3.new(b.side * span, 0, 0))
		end
		if b.lane and practice.mode == "jump" and n > b.jumpT and not hum.PlatformStand then
			b.jumpT = n + 1.2 + math.random() * 0.8
			hum.Jump = true
		end
		-- (heal-back) whole again HealBack s after the last hit
		local hb = b.healBack
		if hb and f.hp < (f.maxHp or Weapons.HP) and n - (b.hurtAt or 0) > hb then
			f.hp = f.maxHp or Weapons.HP
			if Fight.syncHp then Fight.syncHp(f) end
		end
		local lane = laneShoots(f)
		if (shooter(f.name) or lane) and n > b.shoot then
			b.shoot = n + 3
			plink(f, lane)
		end
	end
end

function Dummies.init(fight: any, apply: any)
	Fight, applyHitscan = fight, apply
	Fight.makeDummy = make
	Fight.onHurt(function(t: Fighter) local b = brain[t]; if b then b.hurtAt = os.clock() end end)
	local spots = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub") and workspace.Map.Hub:FindFirstChild("DummySpots")
	local sp = Fight.spawnPoints()
	-- (18 Nov: the yard's side hall has three more, Stand3, Stand4 and the second strafer Dummy2, only where their spots are)
	-- (20 Nov: the dummy yard's armoured and heal-back ones, only where their spots are)
	for i, name in { "Dummy", "Plinker", "Plinker2", "Stand1", "Stand2", "Stand3", "Stand4", "Dummy2", "Runner", "Armour1", "Armour2", "Heal1", "Heal2" } do
		local f = Rules.newFighter("dummy", if string.sub(name, 1, 5) == "Stand" then "Stand" else name, nil)
		local spot = spots and spots:FindFirstChild(name) :: BasePart?
		if not spot and not spots and i > 2 then continue end
		if not spot and i > 5 then continue end
		if not spot and spots and shooter(name) then continue end -- (18 Nov: the v3 rooms have no shooters; never one at a spawn point)
		local home = if spot then spot.Position else (sp[math.min(#sp, i * 2)] or Vector3.new(i * 10, 0, 0))
		local railSpan = spot and spot:GetAttribute("Span")
		local span: number? = if type(railSpan) == "number" then railSpan elseif string.sub(name, 1, 5) == "Dummy" then 4 * S else nil
		local railSpeed = spot and spot:GetAttribute("Speed")
		local lane = spot ~= nil and spot:GetAttribute("Lane") == "practice"
		local hpA = spot and spot:GetAttribute("HP")
		local hbA = spot and spot:GetAttribute("HealBack")
		brain[f] = { home = home, side = 1, flip = 0, shoot = os.clock() + 4, slipUntil = 0, span = span,
			speed = if type(railSpeed) == "number" then railSpeed else nil, every = if type(railSpan) == "number" then nil else 1.6, lane = lane, jumpT = 0,
			armour = type(hpA) == "number" and hpA > Weapons.HP, healBack = if type(hbA) == "number" then hbA else nil, hurtAt = 0 }
		if lane and practice.hp ~= Weapons.HP then f.maxHp = practice.hp end
		if type(hpA) == "number" then f.maxHp = hpA end
		table.insert(list, f)
		table.insert(Fight.all, f)
		Fight.spawn(f)
	end
	-- Studio play tests only: ServerStorage.LiveTest answers "on", "off" (the live-fire end as if the console was
	-- pressed by the first player) and "state"
	if game:GetService("RunService"):IsStudio() then
		local bf = Instance.new("BindableFunction")
		bf.Name = "LiveTest"
		bf.OnInvoke = function(op: string): any
			if op == "on" then setLive(true, Players:GetPlayers()[1]); return true
			elseif op == "off" then setLive(false, nil); return true end
			return { live = live, left = math.max(0, liveUntil - os.clock()), folder = lf ~= nil }
		end
		bf.Parent = game:GetService("ServerStorage")
		-- ServerStorage.PracticeTest: "mode" (strafe, jump, shoot, still), "hp" (100, 300, 50), "state"
		local pt = Instance.new("BindableFunction")
		pt.Name = "PracticeTest"
		pt.OnInvoke = function(op: string, v: any): any
			if op == "mode" and table.find(MODES, v) then practice.mode = v; respawnLane(); paintConsoles()
			elseif op == "hp" and table.find(CLASSES, v) then practice.hp = v; respawnLane(); paintConsoles() end
			local out = {}
			for _, f in list do
				local b = brain[f]
				local r = Fight.root(f)
				table.insert(out, { name = f.name, lane = b.lane, hp = f.hp, max = f.maxHp or Weapons.HP, at = r and r.Position, alive = f.alive })
			end
			return { mode = practice.mode, hp = practice.hp, pads = #pads, folder = pf ~= nil, dummies = out }
		end
		pt.Parent = game:GetService("ServerStorage")
	end
end

return Dummies
