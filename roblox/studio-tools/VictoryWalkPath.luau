--!strict
-- VICTORY WALK PATH: turns an arena's victory spot into a WALK spot (27 Nov 2026, the owner for the Spooky Forest: "make
-- them walk in the forest scared as the screen distorts"). Run in Studio Edit as a ModuleScript:
--   require(it).run("Forest", { len = 7, step = 5, points = 7 }) -> report
-- From the arena's present spot (its Hero: open floor at a team's spawns, facing the arena's middle) it tries
-- headings 0, +-15, +-30 ... 180 degrees off that facing and takes the first whose points all have floor under them
-- (a ray down: an invisible floor counts - the Forest's ground is an invisible Solid part) and a clear walk between
-- them at knee, chest and head height, and room either side for the huddle (rays across). It tries first with invisible
-- parts as walls (the Forest's tree trunks are invisible Solid boxes), then without (an arena's invisible boundary).
-- The old spot is kept as VictoryPose; the new Victory model has Kind "walk", Len, and Path1..PathN on the floor (each
-- facing along the path). Forest: heading +0, 7 points, 30 studs (27 Nov, v1458).
local M = {}

local function solidHit(arena: Instance, from: Vector3, dir: Vector3, keepInvisible: boolean?): RaycastResult?
	local skip = {}
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	rp.FilterDescendantsInstances = { arena }
	local hit = workspace:Raycast(from, dir, rp)
	while hit and not keepInvisible and hit.Instance.Transparency >= 0.95 and #skip < 8 do
		table.insert(skip, hit.Instance)
		local r2 = RaycastParams.new()
		r2.FilterType = Enum.RaycastFilterType.Exclude
		local ex = table.clone(skip)
		for _, c in workspace:GetChildren() do if c.Name ~= "Map" then table.insert(ex, c) end end
		for _, c in (arena.Parent :: Instance):GetChildren() do if c ~= arena then table.insert(ex, c) end end
		r2.FilterDescendantsInstances = ex
		hit = workspace:Raycast(from, dir, r2)
	end
	return hit
end

function M.run(name: string, opts: any?): string
	local o = opts or {}
	local arena = workspace.Map:FindFirstChild(name)
	if not arena then return "no arena " .. name end
	local old = arena:FindFirstChild("Victory") or arena:FindFirstChild("VictoryPose")
	if old and old:GetAttribute("Kind") == "walk" then return "already a walk spot: " .. tostring(old:GetAttribute("Made")) end
	local hero = old and old:FindFirstChild("Hero") :: BasePart?
	if not hero then return "no spot to start from" end
	local start = hero.Position - Vector3.new(0, hero.Size.Y / 2, 0)
	local face = Vector3.new(hero.CFrame.LookVector.X, 0, hero.CFrame.LookVector.Z).Unit
	local step, n = o.step or 5, o.points or 7
	local tried = {}
	for _, strict in { true, false } do
	for _, deg in { 0, 15, -15, 30, -30, 45, -45, 60, -60, 90, -90, 120, -120, 150, -150, 180 } do
		local d = CFrame.Angles(0, math.rad(deg), 0):VectorToWorldSpace(face)
		local right = d:Cross(Vector3.yAxis)
		local pts = {}
		local why: string? = nil
		local prev = start
		for k = 0, n - 1 do
			local p = start + d * (k * step)
			local down = solidHit(arena, p + Vector3.new(0, 6, 0), Vector3.new(0, -14, 0), true)
			if not down then why = ("no floor at %d"):format(k); break end
			p = Vector3.new(p.X, down.Position.Y, p.Z)
			if math.abs(p.Y - prev.Y) > 2.5 then why = ("a step at %d"):format(k); break end
			if k > 0 then
				for _, h in { 1.2, 3.2, 5 } do
					local a = prev + Vector3.new(0, h, 0)
					local hit = solidHit(arena, a, (p + Vector3.new(0, h, 0)) - a, strict)
					if hit then why = ("blocked at %d by %s"):format(k, hit.Instance.Name); break end
				end
				if why then break end
				for _, side in { -1, 1 } do
					local a = p + Vector3.new(0, 3, 0)
					local hit = solidHit(arena, a, right * side * 2.6, strict)
					if hit then why = ("narrow at %d (%s)"):format(k, hit.Instance.Name); break end
				end
				if why then break end
			end
			table.insert(pts, p)
			prev = p
		end
		if not why then
			if old then old.Name = "VictoryPose" end
			local v = Instance.new("Model")
			v.Name = "Victory"
			v:SetAttribute("Kind", "walk")
			v:SetAttribute("Len", o.len or 7)
			v:SetAttribute("Made", ("VictoryWalkPath, heading %+d deg%s"):format(deg, if strict then "" else ", invisible walls skipped"))
			for i, p in pts do
				local part = Instance.new("Part")
				part.Name = "Path" .. i; part.Anchored = true; part.CanCollide = false; part.CanQuery = false; part.CanTouch = false
				part.CastShadow = false; part.Transparency = 1; part.Size = Vector3.new(2, 0.2, 2)
				part.CFrame = CFrame.lookAt(p, p + d) * CFrame.new(0, 0.1, 0)
				part.Parent = v
			end
			v.Parent = arena
			return ("placed: heading %+d deg (strict %s), %d points from %s, %.0f studs"):format(deg, tostring(strict), #pts, tostring(start), (n - 1) * step)
		end
		table.insert(tried, ("%s%+d: %s"):format(if strict then "S" else "L", deg, tostring(why)))
	end
	end
	return "NO PATH: " .. table.concat(tried, " | ")
end

return M
