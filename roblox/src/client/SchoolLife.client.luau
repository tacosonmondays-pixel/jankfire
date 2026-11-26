--!strict
-- SchoolLife (20 Nov 2026): Jankfield High v2's ceiling lights flicker. The owner: "make it a little darker, maybe the
-- ceiling lights flicker you know more ambiance". The kit (tools/roblox/school_models.py --variant=v2A|v2B) puts each
-- flickering group's fittings (frosted shade + small neon core) in its own model, Shell.sc_flk<group>x, and the layout
-- tags those fittings' lights (Lights.Light, attribute FlickGroup = group; WebArena reads the layout's lightGroups).
-- Each group dies on its own timer. Writes happen only on a change, a handful of parts and lights at a time, never per
-- frame (roblox/docs/PERFORMANCE.md). Nothing runs unless the player's Arena is a v2 school; the nearest copy flickers:
-- the source (workspace.Map.<name>), a match copy (Map.ArenaCopies, CopyOf = name) or a zombies game's copy (a child of
-- workspace with the map's name, at (0, 600, 24000)).
-- (26 Nov 2026, the owner on zombies: "the ambiance isnt there yet, it should be darker, with fog, not all ceiling likes
-- should work so the ones that do give a better vibe") a flickering tube buzzes now (zm_flicker, a recording, from the
-- fitting), a few groups stay dead for good, and a thin mist hangs over the floor round you: one emitter box that
-- follows you at your feet (moved twice a second, not per frame), its puffs lit by the lamps they drift under
local Players = game:GetService("Players")
local okSfx, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
local me = Players.LocalPlayer
local OFF_MAT = Enum.Material.SmoothPlastic
local NAMES = { JankfieldHighV2A = true, JankfieldHighV2B = true }
local NGROUPS = 24
local DEAD_GROUPS = { [3] = true, [9] = true, [15] = true, [20] = true } -- (gone for good: a dark fitting among the lit)

type Group = { parts: { BasePart }, cols: { Color3 }, mats: { Enum.Material }, lights: { Light }, at: Vector3? }
local current: Model? = nil
local groups: { [number]: Group } = {}

local function arenaModel(): Model?
	local name = me:GetAttribute("Arena")
	if type(name) ~= "string" or not NAMES[name] then return nil end
	local cam = workspace.CurrentCamera
	local at = if cam then cam.CFrame.Position else Vector3.zero
	local best: Model?, bestD = nil, math.huge
	local function consider(m: Instance?)
		if not m or not m:IsA("Model") then return end
		local d = (m:GetPivot().Position - at).Magnitude
		if d < bestD then best, bestD = m, d end
	end
	local map = workspace:FindFirstChild("Map")
	if map then
		consider(map:FindFirstChild(name))
		local copies = map:FindFirstChild("ArenaCopies")
		if copies then
			for _, c in copies:GetChildren() do
				if c:GetAttribute("CopyOf") == name then consider(c) end
			end
		end
	end
	consider(workspace:FindFirstChild(name))
	return if best and bestD < 1500 then best else nil
end

local function collect(m: Model)
	local out: { [number]: Group } = {}
	local function g(n: number): Group
		local x = out[n]
		if not x then x = { parts = {}, cols = {}, mats = {}, lights = {} }; out[n] = x end
		return x
	end
	local shell = m:FindFirstChild("Shell")
	if shell then
		for _, c in shell:GetChildren() do
			local n = tonumber(string.match(c.Name, "^sc_flk(%d+)x$"))
			if n then
				for _, p in c:GetDescendants() do
					if p:IsA("BasePart") then
						local x = g(n)
						table.insert(x.parts, p); table.insert(x.cols, p.Color); table.insert(x.mats, p.Material)
					end
				end
			end
		end
	end
	local lights = m:FindFirstChild("Lights")
	if lights then
		for _, a in lights:GetChildren() do
			local n = a:GetAttribute("FlickGroup")
			if type(n) == "number" then
				for _, l in a:GetChildren() do
					if l:IsA("Light") then table.insert(g(n).lights, l) end
				end
				if a:IsA("BasePart") and not g(n).at then g(n).at = a.Position end
			end
		end
	end
	return out
end

local function buzz(x: Group)
	local at = x.at
	local cam = workspace.CurrentCamera
	if not at or not cam or not okSfx or (cam.CFrame.Position - at).Magnitude > 70 then return end
	pcall((Sfx :: any).play, "zm_flicker", at)
end

local function setOn(x: Group, on: boolean)
	for i, p in x.parts do
		local mat = x.mats[i]
		if mat == Enum.Material.Neon then
			p.Material = if on then mat else OFF_MAT
			p.Color = if on then x.cols[i] else x.cols[i]:Lerp(Color3.new(0, 0, 0), 0.55)
		end
	end
	for _, l in x.lights do l.Enabled = on end
end

-- one watcher: which school (if any) is ours, and its groups (read once per model, while everything's lit)
task.spawn(function()
	while true do
		local m = arenaModel()
		if m ~= current then
			for _, x in groups do setOn(x, true) end
			current = m
			groups = if m then collect(m) else {}
			for n, x in groups do if DEAD_GROUPS[n] then setOn(x, false) end end
		end
		task.wait(2)
	end
end)

-- the mist: faint puffs low over the floor in a box round you (lit by whatever lamp they're under: LightInfluence 1)
do
	local box = Instance.new("Part")
	box.Name = "SchoolMist"
	box.Anchored, box.CanCollide, box.CanQuery, box.CanTouch, box.CastShadow = true, false, false, false, false
	box.Transparency = 1
	box.Size = Vector3.new(76, 1.6, 76)
	local pe = Instance.new("ParticleEmitter")
	pe.Shape = Enum.ParticleEmitterShape.Box
	pe.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
	pe.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	pe.Texture = "rbxasset://textures/particles/smoke_main.dds"
	pe.Color = ColorSequence.new(Color3.fromRGB(150, 160, 178))
	pe.LightEmission = 0
	pe.LightInfluence = 1
	pe.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 7), NumberSequenceKeypoint.new(1, 13) })
	pe.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.86),
		NumberSequenceKeypoint.new(0.7, 0.88), NumberSequenceKeypoint.new(1, 1) })
	pe.Lifetime = NumberRange.new(7, 11)
	pe.Rate = 9
	pe.Speed = NumberRange.new(0.2, 0.7)
	pe.SpreadAngle = Vector2.new(180, 8)
	pe.Rotation = NumberRange.new(0, 360)
	pe.RotSpeed = NumberRange.new(-6, 6)
	pe.Acceleration = Vector3.new(0, 0.05, 0)
	pe.LockedToPart = false
	pe.Enabled = false
	pe.Parent = box
	task.spawn(function()
		while true do
			local ch = me.Character
			local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			local on = current ~= nil and root ~= nil and current:IsDescendantOf(workspace)
			if on and root then
				if box.Parent ~= workspace then box.Parent = workspace end
				box.CFrame = CFrame.new(root.Position - Vector3.new(0, 2.3, 0)) -- (the puffs start a knee deep: their middles over the floor)
			end
			if pe.Enabled ~= on then pe.Enabled = on; if not on then pe:Clear() end end
			task.wait(0.5)
		end
	end)
end

for n = 1, NGROUPS do
	task.spawn(function()
		task.wait(math.random() * 4)
		while true do
			task.wait(2 + math.random() * 6)
			local x = groups[n]
			if not x or current == nil or DEAD_GROUPS[n] then continue end
			buzz(x)
			if math.random() < 0.15 then
				-- a dying tube: a rapid stutter, a dark spell, back on
				for _ = 1, math.random(5, 9) do
					setOn(x, false); task.wait(0.03 + math.random() * 0.08)
					setOn(x, true); task.wait(0.03 + math.random() * 0.1)
				end
				setOn(x, false); task.wait(0.6 + math.random() * 1.6)
				setOn(x, true)
			else
				for _ = 1, math.random(1, 3) do
					setOn(x, false); task.wait(0.04 + math.random() * 0.16)
					setOn(x, true); task.wait(0.05 + math.random() * 0.12)
				end
			end
		end
	end)
end
