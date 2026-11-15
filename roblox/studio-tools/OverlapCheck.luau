-- edit-time overlap check for the hub (run from the command bar: print(require(game.ServerStorage.PolishBackup.OverlapCheck).run())).
-- every scenery model/part gets an oriented box (its own yaw); prop pairs are tested with the separating-axis test,
-- props against keep-out zones (doors, hallways, walkways, spawns, markers, launch columns), props against walls with
-- GetPartsInPart, and the building is checked for leaks (rays out of every room must hit it)
local OC = {}
local V = Vector3.new
local SHRINK = 0.12
local FLOOR = { Arrow = 1, EdgeLine = 1, Accent = 1, FloorRing = 1, FloorDash = 1, FloorDisc = 1, Carpet = 1, Hazard = 1, BrickSkin = 1, DustMotes = 1, HoloBeam = 1, Bunting = 1, Light = 1, FloorGrate = 1 }
-- (Column and Girder: the training hall's steel. a girder sits on its columns and runs into both side walls on purpose)
local FRAME = { Arch = 1, BlastDoor = 1, Portal = 1, HallRib = 1, Dome = 1, RingBalcony = 1, Pilaster = 1, Column = 1, Girder = 1 }
local ROUND = { Stage = { r = 14.8, top = 249 }, LightRing = { r = 15, top = 1e9 } } -- round things: radius tests

local function kindOf(inst)
	local n = inst.Name
	if FLOOR[n] then return "floor" end
	if FRAME[n] then return "frame" end
	if ROUND[n] then return "round" end
	if n == "FakePad5v5" then return "pad" end
	if inst:IsA("BasePart") then return "deco" end
	return "prop"
end
local function obb(inst)
	if inst:IsA("Model") then
		local ref = inst:FindFirstChildWhichIsA("BasePart", true)
		local rot = if ref then CFrame.fromOrientation(0, math.rad(ref.Orientation.Y), 0) else CFrame.identity
		local old = inst.WorldPivot
		inst.WorldPivot = CFrame.new(inst:GetPivot().Position) * rot
		local cf, sz = inst:GetBoundingBox()
		inst.WorldPivot = old
		return cf, sz
	end
	return inst.CFrame, inst.Size
end
local function sat(a, b)
	local A = { a.cf.RightVector, a.cf.UpVector, a.cf.LookVector }
	local B = { b.cf.RightVector, b.cf.UpVector, b.cf.LookVector }
	local T = b.cf.Position - a.cf.Position
	local ha, hb = { a.half.X, a.half.Y, a.half.Z }, { b.half.X, b.half.Y, b.half.Z }
	local tests = { A[1], A[2], A[3], B[1], B[2], B[3] }
	for i = 1, 3 do for j = 1, 3 do local c = A[i]:Cross(B[j]); if c.Magnitude > 1e-4 then table.insert(tests, c.Unit) end end end
	for _, L in tests do
		local ra = ha[1] * math.abs(A[1]:Dot(L)) + ha[2] * math.abs(A[2]:Dot(L)) + ha[3] * math.abs(A[3]:Dot(L))
		local rb = hb[1] * math.abs(B[1]:Dot(L)) + hb[2] * math.abs(B[2]:Dot(L)) + hb[3] * math.abs(B[3]:Dot(L))
		if math.abs(T:Dot(L)) > ra + rb then return false end
	end
	return true
end
local function zone(n, a, b) return { name = n, cf = CFrame.new((a + b) / 2), half = (b - a) / 2 } end

function OC.run(): string
	local hub = workspace.Map.Hub
	-- the hub is THE LANES now (2026-11-15): its keep-clear test lives with its builder. what follows was written for the
	-- round hub, which is put away in PolishBackup.HubArchive.Rotunda, and only runs if that one is the hub again
	if hub:FindFirstChild("Lanes") then return (require(game.ServerStorage.PolishBackup.HubLab:Clone()) :: any).check() end
	local tg = hub.TrainingGround
	local O = hub:GetAttribute("Origin") :: Vector3 -- (0, 240, -8000)
	local C = O + V(0, 0, -36) -- the rotunda's centre
	local function R(v) return v + V(0, 0, O.Z + 8000) end -- zones below are written for Origin z -8000
	local items = {}
	local function collect(folder, path)
		for _, c in folder:GetChildren() do
			if c:IsA("Folder") then if c.Name ~= "Accents" and c.Name ~= "FillLights" then collect(c, path .. "/" .. c.Name) end
			elseif c:IsA("Model") or (c:IsA("BasePart") and c.Transparency < 1) then
				local cf, sz = obb(c)
				table.insert(items, { name = path .. "/" .. c.Name, cf = cf, half = sz / 2 - V(SHRINK, SHRINK, SHRINK), kind = kindOf(c), round = ROUND[c.Name] })
			end
		end
	end
	collect(hub.Scenery, "Hub"); collect(tg.Scenery, "Training")
	for _, pad in hub.QueuePads:GetChildren() do
		if pad:FindFirstChild("PadModel") then local cf, sz = obb(pad.PadModel); table.insert(items, { name = "pad " .. pad.Name, cf = cf, half = sz / 2, kind = "pad" }) end
	end
	local zones = {
		zone("rotunda N door", R(V(-7, 240.2, -8008.5)), R(V(7, 257, -8005))), zone("rotunda S door", R(V(-7, 240.2, -8067)), R(V(7, 257, -8063.5))),
		zone("rotunda W door", R(V(-30.5, 240.2, -8043)), R(V(-27, 257, -8029))), zone("rotunda E door", R(V(27, 240.2, -8043)), R(V(30.5, 257, -8029))),
		zone("N hallway", R(V(-6.4, 240.2, -8005)), R(V(6.4, 249, -7975))), zone("S hallway", R(V(-8, 240.2, -8085)), R(V(8, 249, -8066))),
		zone("W hallway", R(V(-59, 240.2, -8040)), R(V(-29, 249, -8032))), zone("E hallway", R(V(29, 240.2, -8040)), R(V(59, 249, -8032))),
		zone("lounge door", R(V(-50, 240.2, -8029)), R(V(-40, 249, -8024.5))), zone("depot door", R(V(-62, 240.2, -8043)), R(V(-58, 249, -8029))),
		zone("gym door", R(V(58, 240.2, -8043)), R(V(62, 249, -8029))), zone("corridor walkway", R(V(-12.8, 240.2, -7973)), R(V(12.8, 262, -7882))),
		zone("laser door approach", R(V(-7, 240.2, -8089)), R(V(7, 254, -8080))), zone("training door approach", R(V(-7, 240.2, -8126)), R(V(7, 254, -8105.4))),
	}
	for _, s in hub.HubSpawns:GetChildren() do local z = zone("HubSpawn", s.Position - V(1.2, 0, 1.2), s.Position + V(1.2, 6, 1.2)); z.stageOK = true; table.insert(zones, z) end
	for _, s in hub.TrainSpawns:GetChildren() do table.insert(zones, zone("TrainSpawn", s.Position - V(1.2, 0.5, 1.2), s.Position + V(1.2, 6, 1.2))) end
	for _, s in hub.Doors.HubArrive:GetChildren() do table.insert(zones, zone("HubArrive", s.Position - V(1.2, 0, 1.2), s.Position + V(1.2, 6, 1.2))) end
	for _, s in hub.DummySpots:GetChildren() do table.insert(zones, zone("DummySpot " .. s.Name, s.Position - V(2, 0, 2), s.Position + V(2, 7, 2))) end
	for _, p in hub.Build:GetChildren() do if p.Name == "BalconyPad" then table.insert(zones, zone("launch column", p.Position - V(3.6, -0.4, 3.6), p.Position + V(3.6, 20, 3.6))) end end
	local issues = {}
	local function roundHit(rd, centre, it)
		local p = it.cf.Position
		local flat = V(p.X - centre.X, 0, p.Z - centre.Z)
		return flat.Magnitude - math.max(it.half.X, it.half.Z) < rd.r and p.Y - it.half.Y < rd.top
	end
	for i = 1, #items do
		local a = items[i]
		for j = i + 1, #items do
			local b = items[j]
			if a.kind == "floor" or b.kind == "floor" or (a.kind == "frame" and b.kind == "frame") then continue end
			if a.kind == "deco" and b.kind == "deco" then continue end
			if a.name:find("Dome") or a.name:find("RingBalcony") or b.name:find("Dome") or b.name:find("RingBalcony") then continue end
			-- the training hall's mezzanine: things stand under it and on it by design (checked by hand when it was built)
			if a.name:find("Mezzanine") or b.name:find("Mezzanine") then continue end
			-- the rotunda's four big screens hang across pairs of piers: they touch them on purpose
			if (a.name:find("Frame$") and b.name:find("Pilaster")) or (b.name:find("Frame$") and a.name:find("Pilaster")) then continue end
			if a.name:find("Railing$") and b.name:find("Railing$") then continue end
			if a.kind == "round" or b.kind == "round" then
				local r, o = if a.kind == "round" then a else b, if a.kind == "round" then b else a
				if o.kind == "round" or o.name:find("Logo") or o.name:find("Halo") then continue end
				if r.name:find("LightRing") then
					-- the ring itself is a band at r 14 (+-0.8), from its top down 10.6
					local p = o.cf.Position; local d = V(p.X - r.cf.Position.X, 0, p.Z - r.cf.Position.Z).Magnitude
					if math.abs(d - 14) < 0.8 + math.max(o.half.X, o.half.Z) and p.Y + o.half.Y > r.cf.Position.Y - r.half.Y then table.insert(issues, o.name .. "  x  LightRing") end
				elseif roundHit(r.round, r.cf.Position, o) then table.insert(issues, o.name .. "  x  " .. r.name) end
				continue
			end
			if sat(a, b) then table.insert(issues, a.name .. "  x  " .. b.name) end
		end
		if a.kind == "prop" or a.kind == "deco" then
			for _, z in zones do if sat(a, z) then table.insert(issues, a.name .. "  in  " .. z.name) end end
		end
	end
	local params = OverlapParams.new(); params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { hub.Build.Shell, tg.Shell }
	local q = Instance.new("Part"); q.Anchored = true; q.CanCollide = false; q.Transparency = 1; q.Parent = workspace
	for _, a in items do
		if a.kind == "prop" then
			q.Size = a.half * 2; q.CFrame = a.cf
			for _, w in workspace:GetPartsInPart(q, params) do
				if w.Name ~= "Floor" and w.Name ~= "CorridorFloor" then table.insert(issues, a.name .. "  into  " .. w.Name); break end
			end
		end
	end
	q:Destroy()
	local rooms = { { "rotunda", C + V(0, 30, 0) }, { "dome", C + V(0, 56, 0) }, { "N hall", R(V(0, 250, -7990)) }, { "S hall", R(V(0, 250, -8078)) },
		{ "W hall", R(V(-44, 250, -8036)) }, { "E hall", R(V(44, 250, -8036)) }, { "lounge", R(V(-45, 250, -8015)) }, { "depot", R(V(-80, 250, -8032)) },
		{ "gym", R(V(80, 250, -8032)) }, { "corridor", R(V(0, 258, -7921)) }, { "training", R(V(0, 255, -8206)) }, { "balcony", R(V(-18, 265, -8018)) } }
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { hub.Build, tg.Shell, tg.ToHubDoor }
	local leaks = 0
	for _, r in rooms do
		for x = -1, 1 do for y = -1, 1 do for z = -1, 1 do
			if not (x == 0 and y == 0 and z == 0) and not workspace:Raycast(r[2], V(x, y, z).Unit * 600, rp) then
				leaks += 1; table.insert(issues, "LEAK " .. r[1] .. " toward " .. tostring(V(x, y, z)))
			end
		end end end
	end
	local msg = #items .. " items, " .. #issues .. " issues, leaks " .. leaks
	game.ServerStorage.PolishBackup:SetAttribute("LastOverlapCheck", msg)
	return msg .. "\n" .. table.concat(issues, "\n")
end

return OC
