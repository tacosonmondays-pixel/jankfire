--!strict
-- the Range's test dummies (Training): one on every dummy spot of the map (shared/map.js range.dummies), some sliding
-- side to side, back 0.7 s after they die. plus "Plinker" at the back, who fires short Redline bursts at whoever's
-- training in sight, so you can feel getting shot and practise the katana parry on real bullets. they never score and
-- never show in the kill feed (like the web game's dummies), but they do grow your katana
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Maps = require(Shared:WaitForChild("Maps"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local ShotR = Remotes:WaitForChild("Shot") :: RemoteEvent

type Fighter = Rules.Fighter
local Dummies = {}
local S = Weapons.S
local list: { Fighter } = {}
local brain: { [Fighter]: { home: Vector3, side: number, flip: number, shoot: number, slipUntil: number, move: number } } = {}
local Fight: any
local applyHitscan: any

local folder = Instance.new("Folder")
folder.Name = "Dummies"
folder.Parent = workspace

-- a plain R15 if the engine will make one, else a box mannequin with a wrong knee (jank)
local function body(name: string, color: Color3): Model
	local ok, m = pcall(function()
		local d = Instance.new("HumanoidDescription")
		d.HeadColor, d.TorsoColor = color, color
		d.LeftArmColor, d.RightArmColor, d.LeftLegColor, d.RightLegColor = color, color, Color3.fromRGB(40, 40, 50), Color3.fromRGB(40, 40, 50)
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

Dummies.body = body

local function make(f: Fighter, _at: Vector3?)
	local plinker = f.name == "Plinker"
	local m = body(f.name, if plinker then Color3.fromRGB(255, 59, 59) else Color3.fromRGB(255, 225, 77))
	if not table.find(Fight.all, f) or (f.ref and f.ref.Parent) then m:Destroy(); return end -- (body() can yield)
	local b = brain[f]
	m:PivotTo(CFrame.new(b.home + Vector3.new(0, Hitbox.ROOT_UP + 0.5, 0)))
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.MaxHealth, hum.Health = Weapons.HP, Weapons.HP
		hum.WalkSpeed = 22 -- quick enough to slip on marbles (safe speed is 16.5)
		hum.BreakJointsOnDeath = true
		hum.DisplayName = f.name
	end
	local hs = m:FindFirstChild("Health")
	if hs then hs:Destroy() end
	m:SetAttribute("Dummy", true)
	if hum then hum.NameDisplayDistance = 40 end
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
local function plink(f: Fighter)
	local eye = Fight.eye(f)
	if not eye then return end
	local best, bestD = nil, 60 * S
	for _, t in Fight.all do
		if t.kind == "player" and t.alive and t.room == "training" then
			local c = Fight.root(t)
			if c and (c.Position - eye).Magnitude < bestD and Fight.sees(eye, t) then best, bestD = t, (c.Position - eye).Magnitude end
		end
	end
	if not best then return end
	local w = Weapons.list.redline
	local root = Fight.root(f)
	if root then
		local tc = (Fight.root(best) :: BasePart).Position
		root.CFrame = CFrame.lookAt(root.Position, Vector3.new(tc.X, root.Position.Y, tc.Z))
	end
	local shots = 5
	task.spawn(function()
		for _ = 1, shots do
			if not f.alive or not best.alive or not Fight.live then return end
			local tr = Fight.root(best)
			local e = Fight.eye(f)
			if not tr or not e then return end
			local tf = Hitbox.feet(tr.Position)
			local aim = (tf + Vector3.new(0, 3.5, 0) - e).Unit
			local d = Hitbox.spreadDir(aim, (w.spread :: number) * 1 + 0.045, math.random(), math.random())
			local hitMap = Fight.castMap(e, d, w.range)
			local mapT = if hitMap then (hitMap.Position - e).Magnitude else w.range
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

function Dummies.tick(n: number)
	if not Fight then return end
	for _, f in list do
		local b = brain[f]
		local hum, root = Fight.hum(f), Fight.root(f)
		if not f.alive or not hum or not root then continue end
		if root.Position.Y < Maps.killY(root.Position) then Fight.void(f); continue end
		if hum.PlatformStand and n > b.slipUntil then hum.PlatformStand = false; hum:ChangeState(Enum.HumanoidStateType.GettingUp) end
		if b.move > 0 and n > b.flip and not hum.PlatformStand then -- slides side to side (map.js dummies[].move)
			b.flip = n + math.max(0.8, b.move / 12); b.side = -b.side
			hum:MoveTo(b.home + Vector3.new(b.side * b.move, 0, 0))
		elseif f.name == "Plinker" and n > b.shoot then
			b.shoot = n + 3
			plink(f)
		end
	end
end

function Dummies.init(fight: any, apply: any)
	Fight, applyHitscan = fight, apply
	Fight.makeDummy = make
	local range = Maps.byId("range")
	local spots = range and range:FindFirstChild("Dummies")
	local homes: { { p: Vector3, move: number } } = {}
	if spots then
		for _, d in spots:GetChildren() do
			if d:IsA("BasePart") then
				local mv = d:GetAttribute("Move")
				table.insert(homes, { p = d.Position, move = if type(mv) == "number" then mv else 0 })
			end
		end
	end
	table.sort(homes, function(a, b) return a.p.Z > b.p.Z end)
	-- Plinker: at the back of the range, 60 m out, facing the firing line
	local off = range and range:GetAttribute("Offset")
	local base = if typeof(off) == "Vector3" then off else Vector3.new(20000, 0, 0)
	table.insert(homes, { p = base + Vector3.new(14 * S, 0, -60 * S), move = 0 })
	for i, h in homes do
		local plinker = i == #homes
		local f = Rules.newFighter("dummy", if plinker then "Plinker" else "Dummy", nil)
		f.room = "training"
		brain[f] = { home = h.p, side = 1, flip = 0, shoot = os.clock() + 4, slipUntil = 0, move = h.move }
		table.insert(list, f)
		table.insert(Fight.all, f)
		Fight.spawn(f)
	end
end

return Dummies
