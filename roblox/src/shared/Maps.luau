--!strict
-- the maps in the place (Workspace.Map: Rooftop at the origin, the Range 20000 studs east). each map Model carries
-- MapId, KillY, Bounds (x range), BoundsZ (z range), Offset and its sky (tools/roblox/convert.mjs). server and client
local Maps = {}

function Maps.byId(id: string): Model?
	local root = workspace:FindFirstChild("Map")
	if not root then return nil end
	for _, m in root:GetChildren() do
		if m:IsA("Model") and m:GetAttribute("MapId") == id then return m end
	end
	return nil
end

-- the map a point is over (the nearest one by its play area), or nil if there are none
function Maps.at(pos: Vector3): Model?
	local root = workspace:FindFirstChild("Map")
	if not root then return nil end
	local best, bestD = nil, math.huge
	for _, m in root:GetChildren() do
		if not m:IsA("Model") then continue end
		local bx, bz = m:GetAttribute("Bounds"), m:GetAttribute("BoundsZ")
		if typeof(bx) ~= "Vector3" or typeof(bz) ~= "Vector3" then continue end
		local dx = math.max(bx.X - pos.X, 0, pos.X - bx.Y)
		local dz = math.max(bz.X - pos.Z, 0, pos.Z - bz.Y)
		local d = dx + dz
		if d < bestD then best, bestD = m, d end
	end
	return best
end

-- how low you can fall where you are before it's "into the smog"
function Maps.killY(pos: Vector3): number
	local m = Maps.at(pos)
	local k = m and m:GetAttribute("KillY")
	return if type(k) == "number" then k else -485
end

-- a map's spawn points (feet)
function Maps.spawns(m: Model?): { Vector3 }
	local out = {}
	local sp = m and m:FindFirstChild("Spawns")
	if sp then
		for _, s in sp:GetChildren() do
			if s:IsA("BasePart") then table.insert(out, s.Position + Vector3.new(0, 0.1, 0)) end
		end
	end
	return out
end

return Maps
