--!strict
-- ForestLife (18 Nov 2026): the Spooky Forest's night, as the web map had it.
--   * flashlights: while you are in the Forest, every player in the Forest carries a beam from the head (a SpotLight
--     made here, on this client only, so everyone sees everyone's beam; gone when you leave)
--   * the radio mast's red lights and the broken-down car's hazards blink (the kit's glow pieces fo_glow*__neon_ff5a46
--     and fo_glow*__neon_ffa448, tools/roblox/forest_models.py): one write per change, a few a second, never per frame
-- Nothing runs unless your own arena is the Forest. A match copy (Map.ArenaCopies, "Forest_copyN") shares the Arena name:
-- the nearest one blinks.
local Players = game:GetService("Players")
local me = Players.LocalPlayer
local ARENA = "Forest"
local BEAM = "ForestBeam"

local function inForest(p: Player): boolean
	return p:GetAttribute("Arena") == ARENA
end

-- ------------------------------------------------------------ flashlights
local function setBeam(p: Player, on: boolean)
	local ch = p.Character
	local head = ch and ch:FindFirstChild("Head")
	if not head or not head:IsA("BasePart") then return end
	local l = head:FindFirstChild(BEAM)
	if on and not l then
		local s = Instance.new("SpotLight")
		s.Name = BEAM
		s.Face = Enum.NormalId.Front
		s.Angle = 38; s.Range = 60; s.Brightness = 1.6
		s.Color = Color3.fromRGB(255, 244, 222)
		s.Shadows = false
		s.Parent = head
	elseif not on and l then
		l:Destroy()
	end
end

local function sweep()
	local mine = inForest(me)
	for _, p in Players:GetPlayers() do setBeam(p, mine and inForest(p)) end
end

task.spawn(function()
	while true do
		sweep()
		task.wait(0.5)
	end
end)

-- ------------------------------------------------------------ blinking lamps
local function arenaModel(): Model?
	if not inForest(me) then return nil end
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	local cam = workspace.CurrentCamera
	local at = if cam then cam.CFrame.Position else Vector3.zero
	local best: Model?, bestD = nil, math.huge
	local function consider(m: Instance?)
		if not m or not m:IsA("Model") then return end
		local d = (m:GetPivot().Position - at).Magnitude
		if d < bestD then best, bestD = m, d end
	end
	consider(map:FindFirstChild(ARENA))
	local copies = map:FindFirstChild("ArenaCopies")
	if copies then
		for _, c in copies:GetChildren() do
			if c:GetAttribute("CopyOf") == ARENA then consider(c) end
		end
	end
	return if best and bestD < 1500 then best else nil
end

local function lamps(m: Model, hex: string): { BasePart }
	local out = {}
	local shell = m:FindFirstChild("Shell")
	if not shell then return out end
	for _, d in shell:GetDescendants() do
		if d:IsA("BasePart") and string.find(d.Name, "__neon_" .. hex, 1, true) then table.insert(out, d) end
	end
	return out
end

local DIM = Color3.fromRGB(70, 46, 44)
local function blinker(hex: string, period: number, onFor: number)
	task.spawn(function()
		local cache: { [Model]: { BasePart } } = {}
		local lit: { [BasePart]: Color3 } = {}
		while true do
			local m = arenaModel()
			if not m then task.wait(2); continue end
			local ps = cache[m] or lamps(m, hex)
			cache[m] = ps
			for _, p in ps do
				if not lit[p] then lit[p] = p.Color end
				p.Material = Enum.Material.Neon; p.Color = lit[p]
			end
			task.wait(onFor)
			for _, p in ps do
				p.Material = Enum.Material.SmoothPlastic; p.Color = DIM
			end
			task.wait(period - onFor)
		end
	end)
end
blinker("ff5a46", 1.2, 0.45)   -- the mast's red lights
blinker("ffa448", 0.6, 0.3)    -- the car's hazards
