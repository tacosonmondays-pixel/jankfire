--!strict
-- VICTORY SPOTS: proposes and places each arena's "Victory" model (the victory scene's own spot in the map, 27 Nov 2026,
-- the owner: "the victory screen will depend on the map! itll be a preloaded scene just placing our characters in!").
-- Run in Studio Edit as a ModuleScript: require(it).run({ "RooftopV3", ... }, opts) -> report lines.
-- How a spot is found: a team's spawn area (TeamSpawns "att", else "def") is open floor with the map's edge behind it.
-- The one in front stands at the spawns' middle, facing the arena's middle; teammates in a loose V behind; the lenses
-- (RISE close-up, WIDE group, both in front, looking back at them) sit at the same places relative to the one in front
-- as THE RISER's. Floors and walls are found by rays (the floors take queries: spawns are placed by the same ray in a
-- match). Boxes are no use here: the kit maps are big MeshParts whose boxes cover whole areas (memory roblox-clip-check),
-- and decorations don't take queries, so EVERY spot is judged by a photo too (roblox/docs/VICTORY.md), and moved by hand
-- where the photo says so. opts.dry = report only; opts.replace = replace a spot already placed (otherwise kept).
-- The model is invisible and out of play: Transparency 1, nothing collides, queries or touches.
local M = {}

-- (by the held lens's angles, 27 Nov: the first teammate (a 2v2's only one) to the right, then the left, then back
-- centre-right, so nobody stands on the line from WideB to the one in front)
M.MATES = { Vector3.new(3.8, 0, -2.7), Vector3.new(-4.8, 0, -2.2), Vector3.new(1.6, 0, -5.8) }
-- lens keys in the one-in-front's frame (+Z toward the lens, +X the lens's right; y above their floor)
M.LENS = {
	RiseA = { Vector3.new(2.6, 0.8, 3.9), Vector3.new(0, 1.9, 0), 50 },
	RiseB = { Vector3.new(2.9, 4.4, 5.5), Vector3.new(0, 4.3, 0), 42 },
	WideA = { Vector3.new(-6.5, 3.0, 22), Vector3.new(1.0, 3.0, -2.0), 38 },
	WideB = { Vector3.new(4.6, 3.6, 16), Vector3.new(3.3, 3.2, -2.0), 36 },
}

local function params(arena: Instance): RaycastParams
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	rp.FilterDescendantsInstances = { arena }
	return rp
end
local function floorAt(rp: RaycastParams, x: number, z: number, fromY: number): number?
	local hit = workspace:Raycast(Vector3.new(x, fromY + 4, z), Vector3.new(0, -16, 0), rp)
	return if hit then hit.Position.Y else nil
end

-- a candidate at a spawn side (or at a given floor point and facing): the parts' CFrames and fovs, or nil and why
function M.propose(arena: Model, side: string, scale: number, at: Vector3?, face: Vector3?): (any?, string?)
	local rp = params(arena)
	local c: Vector3
	if at then
		c = at
	else
		local ts = arena:FindFirstChild("TeamSpawns")
		local pts = {}
		if ts then for _, s in ts:GetChildren() do if s:IsA("BasePart") and s.Name == side then table.insert(pts, s.Position) end end end
		if #pts == 0 then return nil, "no " .. side .. " spawns" end
		c = Vector3.zero
		for _, p in pts do c += p end
		c /= #pts
	end
	local facing: Vector3
	if face then
		facing = Vector3.new(face.X, 0, face.Z)
	else
		local mid = arena:GetPivot().Position
		local cx = arena:GetAttribute("CentreX")
		local toward = if type(cx) == "number" then Vector3.new(cx, c.Y, c.Z) else Vector3.new(mid.X, c.Y, mid.Z)
		facing = Vector3.new(toward.X - c.X, 0, toward.Z - c.Z)
	end
	if facing.Magnitude < 0.5 then facing = Vector3.new(0, 0, 1) end
	facing = facing.Unit
	local fy = floorAt(rp, c.X, c.Z, c.Y)
	if not fy then return nil, side .. ": no floor under it" end
	local hero = CFrame.lookAt(Vector3.new(c.X, fy, c.Z), Vector3.new(c.X, fy, c.Z) + facing)
	local F = CFrame.lookAt(hero.Position, hero.Position - facing) -- (+Z = facing: toward the lens)
	local out: any = { Hero = hero, side = side }
	for i, off in M.MATES do
		local p = F:PointToWorldSpace(off)
		local my = floorAt(rp, p.X, p.Z, fy)
		if my and math.abs(my - fy) < 2.5 then out["Mate" .. i] = CFrame.lookAt(Vector3.new(p.X, my, p.Z), Vector3.new(p.X, my, p.Z) + facing) end
	end
	local head = hero.Position + Vector3.new(0, 4.6, 0)
	for name, k in M.LENS do
		local off = k[1]
		local s = if string.sub(name, 1, 4) == "Wide" then scale else 1
		local lensAt = F:PointToWorldSpace(Vector3.new(off.X * s, off.Y, off.Z * s))
		local look = F:PointToWorldSpace(k[2])
		-- (an invisible wall - a walled arena's "Solid" box - blocks a ray but not the view: look past it)
		local skip = {}
		local hit = workspace:Raycast(head, lensAt - head, rp)
		while hit and hit.Instance.Transparency >= 0.95 and #skip < 8 do
			table.insert(skip, hit.Instance)
			local rp2 = RaycastParams.new()
			rp2.FilterType = Enum.RaycastFilterType.Exclude
			local ex = table.clone(skip)
			for _, c in workspace:GetChildren() do if c ~= arena and c.Name ~= "Map" then table.insert(ex, c) end end
			for _, c in (arena.Parent :: Instance):GetChildren() do if c ~= arena then table.insert(ex, c) end end
			rp2.FilterDescendantsInstances = ex
			hit = workspace:Raycast(head, lensAt - head, rp2)
		end
		if hit then return nil, ("%s x%.2f: %s blocked by %s"):format(side, s, name, hit.Instance.Name) end
		out[name] = CFrame.lookAt(lensAt, look)
		-- (the wide lenses frame ~13 studs of height at the one in front at any distance: a lens that had to come in
		-- widens instead of framing tight - 27 Nov, RooftopV2's at 75%)
		out[name .. "Fov"] = if s ~= 1 or string.sub(name, 1, 4) == "Wide"
			then math.clamp(math.deg(2 * math.atan(6.5 / (lensAt - (hero.Position + Vector3.new(0, 3, 0))).Magnitude)), 30, 62)
			else k[3]
	end
	return out, nil
end

function M.place(arena: Model, s: any)
	local old = arena:FindFirstChild("Victory")
	if old then old:Destroy() end
	local v = Instance.new("Model")
	v.Name = "Victory"
	local function part(name: string, cf: CFrame, size: Vector3, fov: number?)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Transparency = 1; p.Size = size; p.CFrame = cf
		if fov then p:SetAttribute("Fov", fov) end
		p.Parent = v
	end
	part("Hero", s.Hero * CFrame.new(0, 0.1, 0), Vector3.new(2, 0.2, 2))
	for i = 1, 3 do if s["Mate" .. i] then part("Mate" .. i, s["Mate" .. i] * CFrame.new(0, 0.1, 0), Vector3.new(2, 0.2, 2)) end end
	for name in M.LENS do part(name, s[name], Vector3.new(0.4, 0.4, 0.8), s[name .. "Fov"]) end
	v:SetAttribute("Made", "VictorySpots, side " .. tostring(s.side))
	v.Parent = arena
	return v
end

function M.run(names: { string }, opts: any?): { string }
	local map = workspace:FindFirstChild("Map")
	local out = {}
	for _, n in names do
		local arena = map and map:FindFirstChild(n)
		if not (arena and arena:IsA("Model")) then table.insert(out, n .. ": no arena"); continue end
		if arena:FindFirstChild("Victory") and not (opts and opts.replace) then table.insert(out, n .. ": spot already there (kept)"); continue end
		local got, whys = nil, {}
		for _, side in { "att", "def" } do
			for _, sc in { 1, 0.75, 0.55 } do
				local s, why = M.propose(arena, side, sc)
				if s then got = s; got.scale = sc; break end
				table.insert(whys, why)
			end
			if got then break end
		end
		if got then
			if not (opts and opts.dry) then M.place(arena, got) end
			local mates = 0
			for i = 1, 3 do if got["Mate" .. i] then mates += 1 end end
			table.insert(out, ("%s: %s, side %s, wide x%.2f, %d mate slots"):format(n, if opts and opts.dry then "would place" else "placed", got.side, got.scale, mates))
		else
			table.insert(out, n .. ": NO SPOT (" .. table.concat(whys, " | ") .. ")")
		end
		task.wait()
	end
	return out
end

return M
