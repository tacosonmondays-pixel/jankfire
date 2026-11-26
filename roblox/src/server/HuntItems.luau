--!strict
-- HOLDOUT's traps, points and FIGHT BACK weapons (26 Nov 2026; roblox/docs/HUNT.md section 5). The owner: "Hiders can
-- also buy traps like a bear trap, some sort of spray, a taser, etc.. ... If you hide for 2ish minutes you will be given
-- a chance to fight back, you'll have the chance to find and search for weapons around the house like a kitchen knife
-- golf club etc!"
--   points: HuntConfig.POINTS (a start, a trickle while alive in the hunt, more for hits and trap catches); player
--     attribute HuntPoints
--   traps: bought with points from the trap menu (client: G), two carried (attribute HuntItems "id:uses,id:uses"),
--     used with 1 / 2. BEAR TRAP (set on the floor, springs on the gunman), PEPPER SPRAY (a cone: his view goes white),
--     TASER (one shot: StunUntil, the game's own stun), SMOKE BOMB (a cloud), MARBLES (a spill: the game's own slip),
--     DECOY (footsteps walking away from it)
--   FIGHT BACK: the map's search spots open (hold F); a find goes in your right hand (attribute HuntWeapon) and your
--     punch swings it (HuntMoves asks weaponOf)
-- Nothing here hurts anyone but the gunman, and only in the hunt (Fight.allow, HuntRound).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local Remote = Remotes:WaitForChild("Hunt") :: RemoteEvent
local SlipR = Remotes:FindFirstChild("Slip") :: RemoteEvent?
local PTS = HC.POINTS

local HuntItems = {}
local TRAP: { [string]: any } = {}
for _, t in HC.TRAPS do TRAP[t.id] = t end

type St = { points: number, items: { { id: string, uses: number } }, weapon: string?, nextAlive: number, prop: Model? }
local st: { [Player]: St } = {}
local world: { any } = {} -- (the live traps in the map: bear traps, spills, decoys, clouds)
local spots: { BasePart } = {}
local G: any = nil

local Sounds = ReplicatedStorage:FindFirstChild("JankfireSounds")
local function sfx(name: string, at: BasePart, vol: number?)
	local s = Sounds and Sounds:FindFirstChild(name)
	if not (s and s:IsA("Sound")) then return end
	local c = s:Clone()
	c.RollOffMode = Enum.RollOffMode.InverseTapered; c.RollOffMinDistance = 8; c.RollOffMaxDistance = 90
	if vol then c.Volume *= vol end
	c.Parent = at
	c:Play()
	task.delay(math.max(1.5, c.TimeLength + 0.3), function() c:Destroy() end)
end
local function part(props: { [string]: any }, parent: Instance?): Part
	local p = Instance.new("Part")
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic; p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	for k, v in props do (p :: any)[k] = v end
	if parent then p.Parent = parent end
	return p
end

local function publish(p: Player)
	local s = st[p]
	if not s then
		for _, a in { "HuntPoints", "HuntItems", "HuntWeapon" } do p:SetAttribute(a, nil) end
		return
	end
	p:SetAttribute("HuntPoints", s.points)
	local parts = {}
	for _, it in s.items do table.insert(parts, it.id .. ":" .. it.uses) end
	p:SetAttribute("HuntItems", table.concat(parts, ","))
	p:SetAttribute("HuntWeapon", s.weapon)
end
function HuntItems.score(p: Player, n: number)
	local s = st[p]
	if not s then return end
	s.points += n
	publish(p)
end

-- ------------------------------------------------------------------ the gunman (whoever the round says)
local function gunmanOf(): any
	return G and G.gunman
end
local function gunRoot(): BasePart?
	local m = gunmanOf()
	return m and m.alive and m.f.alive and Fight.root(m.f) or nil
end
local function caught(by: Player, dmg: number?)
	local m = gunmanOf()
	if not m then return end
	local bf = Fight.byPlayer[by]
	if dmg and dmg > 0 and bf then Fight.hurt(m.f, dmg, bf, "trap", false, nil) end
	HuntItems.score(by, PTS.trap)
end
local function stun(secs: number)
	local m = gunmanOf()
	if not m then return end
	local model = Fight.model(m.f)
	local hum = model and model:FindFirstChildOfClass("Humanoid")
	local until_ = workspace:GetServerTimeNow() + secs
	if m.p then m.p:SetAttribute("StunUntil", until_) end
	if hum then hum:SetAttribute("StunUntil", until_) end
	if not m.p and model then model:SetAttribute("StunUntil", until_) end
end
local function sees(from: Vector3, to: Vector3, ignore: { Instance }): boolean
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(from, to - from, params)
	if not hit then return true end
	local m = gunmanOf()
	local model = m and Fight.model(m.f)
	return model ~= nil and hit.Instance:IsDescendantOf(model)
end

-- ------------------------------------------------------------------ the traps
local function floorAt(p: Vector3, ignore: { Instance }): Vector3?
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(p + Vector3.new(0, 2, 0), Vector3.new(0, -9, 0), params)
	return if hit then hit.Position else nil
end
local USE: { [string]: (Player, BasePart, Vector3, any) -> boolean } = {}
USE.beartrap = function(p, root, look, T)
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else root.CFrame.LookVector
	local at = floorAt(root.Position + flat * 4, { p.Character :: any, G.map:FindFirstChild("HuntPen") :: any })
	if not at then return false end
	local f = Instance.new("Model"); f.Name = "BearTrap"
	local base = part({ Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.3, 2.6, 2.6), Color = Color3.fromRGB(70, 72, 76),
		CFrame = CFrame.new(at + Vector3.new(0, 0.15, 0)) * CFrame.Angles(0, 0, math.pi / 2) }, f)
	local jaws = {}
	for s = -1, 1, 2 do
		local j = part({ Size = Vector3.new(2.4, 0.25, 0.9), Color = Color3.fromRGB(96, 98, 102),
			CFrame = CFrame.new(at + Vector3.new(0, 0.3, s * 0.8)) * CFrame.Angles(s * math.rad(60), 0, 0) }, f)
		table.insert(jaws, { j = j, s = s })
	end
	f.Parent = G.map
	table.insert(world, { kind = "beartrap", by = p, at = at, model = f, armT = os.clock() + T.arm, jaws = jaws, T = T })
	sfx("marble", base, 0.6)
	return true
end
USE.spray = function(p, root, look, T)
	local eye = root.Position + Vector3.new(0, 1.6, 0)
	Remote:FireAllClients("fx", "spray", eye, look)
	sfx("gas_hiss", root, 0.7)
	local g = gunRoot()
	if g then
		local d = g.Position - eye
		if d.Magnitude <= T.range and d.Unit:Dot(look.Unit) >= math.cos(math.rad(T.cone)) and sees(eye, g.Position, { p.Character :: any }) then
			local m = gunmanOf()
			if m and m.p then Remote:FireClient(m.p, "blind", T.blind) end
			caught(p, 0)
		end
	end
	return true
end
USE.taser = function(p, root, look, T)
	local eye = root.Position + Vector3.new(0, 1.6, 0)
	local g = gunRoot()
	local hitAt = eye + look.Unit * T.range
	if g then
		local d = g.Position - eye
		if d.Magnitude <= T.range and d.Unit:Dot(look.Unit) >= math.cos(math.rad(T.cone)) and sees(eye, g.Position, { p.Character :: any }) then
			hitAt = g.Position
			stun(T.stun)
			caught(p, 0)
			sfx("taser_arc", g, 1)
		end
	end
	Remote:FireAllClients("fx", "zap", eye, hitAt)
	sfx("taser_fire", root, 0.8)
	return true
end
USE.smoke = function(p, root, _look, T)
	local at = floorAt(root.Position, { p.Character :: any }) or root.Position
	Remote:FireAllClients("fx", "smoke", at, T.time, T.radius)
	sfx("skin_smoke_censer_cloud", root, 0.8)
	return true
end
USE.marbles = function(p, root, _look, T)
	local at = floorAt(root.Position, { p.Character :: any }) or root.Position
	local f = Instance.new("Model"); f.Name = "Marbles"
	for _ = 1, 22 do
		local a, r = math.random() * math.pi * 2, math.sqrt(math.random()) * T.radius
		part({ Shape = Enum.PartType.Ball, Size = Vector3.new(0.45, 0.45, 0.45),
			Color = ({ Color3.fromRGB(122, 150, 176), Color3.fromRGB(176, 150, 118), Color3.fromRGB(150, 170, 140) })[math.random(3)],
			CFrame = CFrame.new(at + Vector3.new(math.cos(a) * r, 0.22, math.sin(a) * r)) }, f)
	end
	f.Parent = G.map
	table.insert(world, { kind = "marbles", by = p, at = at, model = f, untilT = os.clock() + T.time, T = T, next = 0, scored = false })
	sfx("marble", root, 0.9)
	return true
end
USE.decoy = function(p, root, look, T)
	local at = floorAt(root.Position, { p.Character :: any }) or root.Position
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else root.CFrame.LookVector
	local walker = part({ Size = Vector3.new(0.6, 0.6, 0.6), Transparency = 1, CFrame = CFrame.new(at + Vector3.new(0, 0.5, 0)) }, G.map)
	table.insert(world, { kind = "decoy", by = p, at = at, model = walker, dir = flat, untilT = os.clock() + T.time, next = 0 })
	return true
end

-- ------------------------------------------------------------------ search spots and the weapons
local function weld(prop: Model, hand: BasePart)
	for _, d in prop:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = false; d.Massless = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		end
	end
	local grip = prop.PrimaryPart :: BasePart
	local w = Instance.new("Weld")
	w.Part0 = hand; w.Part1 = grip
	w.C0 = CFrame.new(0, -0.55, 0) * CFrame.Angles(math.rad(90), 0, 0) -- (the long axis, +Z, out of the fist)
	w.Parent = grip
end
local function makeProp(id: string): Model
	local m = Instance.new("Model"); m.Name = "HuntWeapon"
	local STEEL, DARK, WOOD = Color3.fromRGB(176, 182, 188), Color3.fromRGB(46, 44, 42), Color3.fromRGB(176, 136, 92)
	local function b(size: Vector3, off: CFrame, col: Color3, shape: Enum.PartType?): Part
		local p = part({ Size = size, Color = col, CFrame = off }, m)
		if shape then p.Shape = shape end
		return p
	end
	local grip: Part
	if id == "knife" then
		grip = b(Vector3.new(0.3, 0.3, 1.3), CFrame.new(0, 0, 0.3), DARK)
		b(Vector3.new(0.08, 0.5, 1.9), CFrame.new(0, 0.05, 1.9), STEEL)
	elseif id == "pan" then
		grip = b(Vector3.new(0.25, 0.25, 2.2), CFrame.new(0, 0, 0.6), DARK)
		b(Vector3.new(0.35, 2.4, 2.4), CFrame.new(0, 0, 2.9) * CFrame.Angles(0, 0, math.pi / 2), Color3.fromRGB(58, 60, 64), Enum.PartType.Cylinder)
	elseif id == "club" then
		grip = b(Vector3.new(0.22, 0.22, 1.4), CFrame.new(0, 0, 0.3), DARK)
		b(Vector3.new(0.14, 0.14, 3.6), CFrame.new(0, 0, 2.7), STEEL)
		b(Vector3.new(0.45, 0.7, 1.0), CFrame.new(0, -0.15, 4.6), STEEL)
	else
		grip = b(Vector3.new(0.28, 0.28, 1.4), CFrame.new(0, 0, 0.3), Color3.fromRGB(70, 60, 54))
		b(Vector3.new(0.45, 0.45, 1.4), CFrame.new(0, 0, 1.6), WOOD)
		b(Vector3.new(0.62, 0.62, 2.0), CFrame.new(0, 0, 3.2), WOOD)
	end
	m.PrimaryPart = grip
	return m
end
local function equip(p: Player, id: string)
	local s = st[p]
	if not s then return end
	if s.prop then s.prop:Destroy(); s.prop = nil end
	s.weapon = id
	local ch = p.Character
	local hand = ch and (ch:FindFirstChild("RightHand") or ch:FindFirstChild("Right Arm")) :: BasePart?
	if hand then
		local prop = makeProp(id)
		prop:PivotTo(hand.CFrame)
		prop.Parent = ch
		weld(prop, hand)
		s.prop = prop
	end
	publish(p)
end
function HuntItems.weaponOf(p: Player): any
	local s = st[p]
	return if s and s.weapon then HC.WEAPONS[s.weapon] else nil
end

local function makeSpots(g: any)
	spots = {}
	local def = g.def
	local folder = Instance.new("Folder"); folder.Name = "HuntSearch"; folder.Parent = g.map
	for _, sp in (def.search or {}) do
		local at = (g.origin * CFrame.new(sp[1], sp[2], sp[3])).Position
		local pt = part({ Size = Vector3.new(2, 2, 2), Transparency = 1, CFrame = CFrame.new(at) }, folder)
		pt:SetAttribute("Holds", sp[4])
		local pr = Instance.new("ProximityPrompt")
		pr.ActionText = "SEARCH"; pr.ObjectText = ""; pr.HoldDuration = HC.WEAPONS.search
		pr.KeyboardKeyCode = Enum.KeyCode.F; pr.GamepadKeyCode = Enum.KeyCode.ButtonX
		pr.MaxActivationDistance = 8; pr.RequiresLineOfSight = false; pr.Enabled = false
		pr.Parent = pt
		pr.Triggered:Connect(function(who: Player)
			if not G or not G.fightOn or pt:GetAttribute("Searched") then return end
			local m = G.byF[Fight.byPlayer[who]]
			if not m or m.role ~= "hider" or not m.alive then return end
			pt:SetAttribute("Searched", true)
			pr.Enabled = false
			local holds = pt:GetAttribute("Holds")
			if type(holds) == "string" and holds ~= "" and HC.WEAPONS[holds] then
				equip(who, holds)
				Remote:FireClient(who, "found", holds)
			else
				Remote:FireClient(who, "found", "")
			end
		end)
		table.insert(spots, pt)
	end
end

-- ------------------------------------------------------------------ the round's calls (HuntRound)
function HuntItems.onStart(g: any)
	G = g
	world = {}
	for _, m in g.members do
		if m.p and m.role == "hider" then
			st[m.p] = { points = PTS.start, items = {}, weapon = nil, nextAlive = 0, prop = nil }
			publish(m.p)
		end
	end
	makeSpots(g)
end
function HuntItems.onFightBack(_g: any)
	for _, pt in spots do
		local pr = pt:FindFirstChildOfClass("ProximityPrompt")
		if pr and not pt:GetAttribute("Searched") then pr.Enabled = true end
	end
end
function HuntItems.onEnd(_g: any)
	for p, s in st do
		if s.prop then s.prop:Destroy() end
		st[p] = nil
		publish(p)
	end
	world = {}; spots = {}; G = nil
end
function HuntItems.tick(g: any, dt: number)
	local t = os.clock()
	-- points for staying alive in the hunt
	if g.phase == "hunt" then
		for _, m in g.members do
			local s = m.p and st[m.p]
			if s and m.alive and t >= s.nextAlive then
				if s.nextAlive > 0 then s.points += PTS.alive; publish(m.p) end
				s.nextAlive = t + PTS.every
			end
		end
	end
	local g0 = gunRoot()
	for i = #world, 1, -1 do
		local w = world[i]
		if w.kind == "beartrap" then
			if not w.sprung and t >= w.armT and g0 and (Vector3.new(g0.Position.X, 0, g0.Position.Z) - Vector3.new(w.at.X, 0, w.at.Z)).Magnitude <= w.T.reach
				and math.abs(g0.Position.Y - 2.9 - w.at.Y) < 3 then
				w.sprung = true
				for _, j in w.jaws do TweenService:Create(j.j, TweenInfo.new(0.08), { CFrame = CFrame.new(w.at + Vector3.new(0, 0.6, j.s * 0.25)) * CFrame.Angles(j.s * math.rad(10), 0, 0) }):Play() end
				stun(w.T.hold)
				caught(w.by, w.T.dmg)
				sfx("ropesnap", w.model.PrimaryPart or w.model:FindFirstChildWhichIsA("BasePart") :: BasePart, 1.2)
				task.delay(w.T.hold + 0.5, function() if w.model.Parent then w.model:Destroy() end end)
				table.remove(world, i)
			end
		elseif w.kind == "marbles" then
			if t >= w.untilT then w.model:Destroy(); table.remove(world, i); continue end
			if g0 and t >= w.next and (Vector3.new(g0.Position.X, 0, g0.Position.Z) - Vector3.new(w.at.X, 0, w.at.Z)).Magnitude <= w.T.radius
				and math.abs(g0.Position.Y - 2.9 - w.at.Y) < 3 then
				w.next = t + 2.0
				local m = gunmanOf()
				if m and m.p and SlipR then SlipR:FireClient(m.p, "marbles") end
				if not w.scored then w.scored = true; caught(w.by, 0) end
			end
		elseif w.kind == "decoy" then
			if t >= w.untilT then w.model:Destroy(); table.remove(world, i); continue end
			-- it walks away from where it was dropped, a stride every 0.42 s, a step sound each stride
			w.model.CFrame += w.dir * 2.4 * math.min(dt, 0.25) / 0.42
			if t >= w.next then
				w.next = t + 0.42
				sfx("step_hard", w.model, 1.1)
			end
		end
	end
end

-- ------------------------------------------------------------------ the client's asks
function HuntItems.handle(p: Player, op: string, a: any, b: any): boolean
	if op ~= "buy" and op ~= "use" then return false end
	local g = G
	local s = st[p]
	if not g or not s or g.phase ~= "hunt" then return true end
	local m = g.byF[Fight.byPlayer[p]]
	if not m or not m.alive or m.role ~= "hider" then return true end
	if op == "buy" then
		local T = TRAP[a]
		if not T or s.points < T.cost or #s.items >= PTS.carry then return true end
		s.points -= T.cost
		table.insert(s.items, { id = T.id, uses = T.uses or 1 })
		publish(p)
	else
		local slot = tonumber(a)
		local it = slot and s.items[slot]
		if not it then return true end
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not root then return true end
		local look = if typeof(b) == "Vector3" and b.Magnitude > 0.1 and b.Magnitude < 2 then b.Unit else root.CFrame.LookVector
		local fn = USE[it.id]
		if fn and fn(p, root, look, TRAP[it.id]) then
			it.uses -= 1
			if it.uses <= 0 then table.remove(s.items, slot) end
			publish(p)
		end
	end
	return true
end

Players.PlayerRemoving:Connect(function(p) local s = st[p]; if s and s.prop then s.prop:Destroy() end; st[p] = nil end)

return HuntItems
