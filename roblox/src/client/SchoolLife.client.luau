--!strict
-- SchoolLife (20 Nov 2026): Jankfield High v2's ceiling lights flicker. The owner: "make it a little darker, maybe the
-- ceiling lights flicker you know more ambiance". The kit (tools/roblox/school_models.py --variant=v2A|v2B) puts each
-- flickering group's fittings (frosted shade + small neon core) in its own model, Shell.sc_flk<group>x, and the layout
-- tags those fittings' lights (Lights.Light, attribute FlickGroup = group; WebArena reads the layout's lightGroups).
-- Each group dies on its own timer. Writes happen only on a change, a handful of parts and lights at a time, never per
-- frame (roblox/docs/PERFORMANCE.md). Nothing runs unless the player's Arena is a v2 school; the nearest copy flickers:
-- the source (workspace.Map.<name>), a match copy (Map.ArenaCopies, CopyOf = name) or a zombies game's copy (a child of
-- workspace with the map's name, at (0, 600, 24000)).
local Players = game:GetService("Players")
local me = Players.LocalPlayer
local OFF_MAT = Enum.Material.SmoothPlastic
local NAMES = { JankfieldHighV2A = true, JankfieldHighV2B = true }
local NGROUPS = 24

type Group = { parts: { BasePart }, cols: { Color3 }, mats: { Enum.Material }, lights: { Light } }
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
			end
		end
	end
	return out
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
		end
		task.wait(2)
	end
end)

for n = 1, NGROUPS do
	task.spawn(function()
		task.wait(math.random() * 4)
		while true do
			task.wait(2 + math.random() * 6)
			local x = groups[n]
			if not x or current == nil then continue end
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
