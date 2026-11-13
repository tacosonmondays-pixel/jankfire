--!strict
-- two test dummies so one person can try everything: "Dummy" strafes back and forth (shoot it, slice it, marble it),
-- "Plinker" stands still and fires short Redline bursts at the nearest player it can see (so you can feel getting
-- shot, and practise the katana parry on real bullets). they never count for score or the kill feed (like the web
-- game's training dummies), but they do grow your katana. bots proper (MODES.md bot brain) come with the match core
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local ShotR = Remotes:WaitForChild("Shot") :: RemoteEvent

type Fighter = Rules.Fighter
local Dummies = {}
local S = Weapons.S
local list: { Fighter } = {}
local brain: { [Fighter]: { home: Vector3, side: number, flip: number, shoot: number, slipUntil: number } } = {}
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

local function make(f: Fighter)
	local plinker = f.name == "Plinker"
	local m = body(f.name, if plinker then Color3.fromRGB(255, 59, 59) else Color3.fromRGB(255, 225, 77))
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
		if t.kind == "player" and t.alive then
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
	local map = workspace:FindFirstChild("Map")
	local m1 = map and map:FindFirstChildWhichIsA("Model")
	local killY = (m1 and m1:GetAttribute("KillY")) or -485
	for _, f in list do
		local b = brain[f]
		local hum, root = Fight.hum(f), Fight.root(f)
		if not f.alive or not hum or not root then continue end
		if root.Position.Y < (killY :: number) then Fight.void(f); continue end
		if hum.PlatformStand and n > b.slipUntil then hum.PlatformStand = false; hum:ChangeState(Enum.HumanoidStateType.GettingUp) end
		if f.name == "Dummy" and n > b.flip and not hum.PlatformStand then
			b.flip = n + 1.6; b.side = -b.side
			hum:MoveTo(b.home + Vector3.new(b.side * 4 * S, 0, 0))
		elseif f.name == "Plinker" and n > b.shoot then
			b.shoot = n + 3
			plink(f)
		end
	end
end

function Dummies.init(fight: any, apply: any)
	Fight, applyHitscan = fight, apply
	Fight.makeDummy = make
	local sp = Fight.spawnPoints()
	for i, name in { "Dummy", "Plinker" } do
		local f = Rules.newFighter("dummy", name, nil)
		local home = sp[math.min(#sp, i * 2)] or Vector3.new(i * 10, 0, 0)
		brain[f] = { home = home, side = 1, flip = 0, shoot = os.clock() + 4, slipUntil = 0 }
		table.insert(list, f)
		table.insert(Fight.all, f)
		Fight.spawn(f)
	end
end

return Dummies
