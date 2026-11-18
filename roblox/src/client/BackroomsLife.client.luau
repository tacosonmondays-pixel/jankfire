--!strict
-- BackroomsLife (18 Nov 2026): in the Backrooms the dying ceiling panels flicker, as in the web map (its ceilflick
-- rooms). The kit (tools/roblox/backrooms_models.py) puts them in their own models, Shell.br_flickA and Shell.br_flickB
-- (one or two MeshParts each), so each group dies on its own timer. Writes happen only on a change (a few a second over
-- at most four MeshParts), never per frame (roblox/docs/PERFORMANCE.md). Nothing runs unless the player's arena is the
-- Backrooms; in a match copy (Map.ArenaCopies, "Backrooms_copyN", the same Arena name) the nearest copy flickers.
local Players = game:GetService("Players")
local me = Players.LocalPlayer
local OFF_COL, OFF_MAT = Color3.fromHex("b6af9d"), Enum.Material.SmoothPlastic

local function arenaModel(): Model?
	local name = me:GetAttribute("Arena")
	if type(name) ~= "string" or name ~= "Backrooms" then return nil end
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
	consider(map:FindFirstChild(name))
	local copies = map:FindFirstChild("ArenaCopies")
	if copies then
		for _, c in copies:GetChildren() do
			if c:GetAttribute("CopyOf") == name then consider(c) end
		end
	end
	return if best and bestD < 1500 then best else nil
end

local function parts(m: Model, group: string): { MeshPart }
	local out = {}
	local shell = m:FindFirstChild("Shell")
	local g = shell and shell:FindFirstChild("br_flick" .. group)
	if g then for _, p in g:GetDescendants() do if p:IsA("MeshPart") then table.insert(out, p) end end end
	return out
end

local function setOn(ps: { MeshPart }, on: boolean, col: Color3, mat: Enum.Material)
	for _, p in ps do
		p.Material = if on then mat else OFF_MAT
		p.Color = if on then col else OFF_COL
	end
end

for _, group in { "A", "B" } do
	task.spawn(function()
		local col: Color3?, mat: Enum.Material? = nil, nil
		while true do
			task.wait(0.6 + math.random() * 3.4)
			local m = arenaModel()
			if not m then task.wait(2); continue end
			local ps = parts(m, group)
			if #ps == 0 then continue end
			-- (the lit look, read once while it's lit: a blink always ends lit)
			if not col then col, mat = ps[1].Color, ps[1].Material end
			if ps[1].Material == OFF_MAT then setOn(ps, true, col :: Color3, mat :: Enum.Material) end
			for _ = 1, (if math.random() < 0.35 then 2 else 1) do
				setOn(ps, false, col :: Color3, mat :: Enum.Material)
				task.wait(0.05 + math.random() * 0.2)
				setOn(ps, true, col :: Color3, mat :: Enum.Material)
				task.wait(0.06 + math.random() * 0.1)
			end
		end
	end)
end
