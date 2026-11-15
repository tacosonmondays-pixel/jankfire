--!nocheck
-- edit-time tool (2026-11-14): swaps the hub's thin old pieces for the chunky hb_* kit, in place.
-- each scenery Model keeps its name, its place in the tree and everything that isn't a mesh (screens, sign boards,
-- lamp parts with their lights); only its mesh parts change. the old mesh parts go to PolishBackup.HubV5, each bundle
-- tagged with where it came from. a Model that has been done carries the attribute Reskin, so running twice is safe.
-- usage: local R = require(game.ServerStorage.PolishBackup.HubReskin:Clone()); print(R.run())
local R = {}
local lib = game.ServerStorage.JankfireMeshes
local backup = game.ServerStorage.PolishBackup
local hub = workspace.Map.Hub
local C = Vector3.new(0, 240, -8036) + ((hub:GetAttribute("Origin") or Vector3.new(0, 240, -8000)) - Vector3.new(0, 240, -8000))

-- old library mesh -> what replaces it, and how it is seated
--   seat: bottom / top / centre (which height of the old piece the new one keeps)
--   back = true: the piece stands against a wall; its flat back keeps the old back plane, its front faces the room
--   wide: the new model's own width, when it is scaled to the old piece's width
R.MAP = {
	bc_pilaster = { to = "hb_pier", seat = "bottom", back = true, towardCentre = true },
	bc_portal = { to = "hb_portal", seat = "bottom" },
	bc_railing = { to = "hb_rail", seat = "bottom" },
	bc_ringbalcony = { to = "hb_ring", seat = "top", flat = true },
	bc_screenframe = { to = "hb_screen", seat = "centre", wide = 24.6 },
	bc_hangsign = { to = "hb_hangsign", seat = "bottom", drop = 0.15 },
	bc_arch = { to = "hb_arch", seat = "bottom" },
	bc_hallrib = { to = "hb_rib", seat = "bottom" },
	bc_downlight = { to = "hb_panel", seat = "top", flat = true },
	bc_pendantlong = { to = "hb_droplight", seat = "top", rod = true },
	bc_pendantmid = { to = "hb_droplight", seat = "top", rod = true },
	bc_pendant = { to = "hb_droplight", seat = "top", rod = true },
	bc_ceilbar = { to = "hb_bar", seat = "top" },
	bc_sconce = { to = "hb_walllight", seat = "centre", back = true },
	bc_wallpanel = { to = "hb_slab", seat = "centre", back = true, wide = 7.0 },
	p_vending = { to = "hb_vending", seat = "bottom", back = true },
}
local VEND = { "ff4fd8", "37d6ff", "ffe14d" }

-- the box round a model's own mesh parts, in its pivot frame
local function meshBox(m)
	local piv = m:GetPivot()
	local lo, hi = Vector3.new(1e9, 1e9, 1e9), Vector3.new(-1e9, -1e9, -1e9)
	local n = 0
	for _, d in m:GetDescendants() do
		if d:IsA("MeshPart") then
			n += 1
			local s = d.Size / 2
			for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
				local p = piv:PointToObjectSpace(d.CFrame:PointToWorldSpace(Vector3.new(s.X * sx, s.Y * sy, s.Z * sz)))
				lo = lo:Min(p); hi = hi:Max(p)
			end end end
		end
	end
	if n == 0 then return nil end
	return piv * CFrame.new((lo + hi) / 2), hi - lo
end

-- which library mesh a model is a copy of (nil if it holds other models that hold the meshes: we want the innermost)
local byMesh
local function sourceOf(m)
	if not byMesh then
		byMesh = {}
		for _, t in lib:GetChildren() do
			if R.MAP[t.Name] then for _, mp in t:GetDescendants() do if mp:IsA("MeshPart") then byMesh[mp.MeshId] = t.Name end end end
		end
	end
	-- the meshes are direct children, or sit one wrapper Model down ("..._Node")
	local first
	for _, c in m:GetChildren() do
		if c:IsA("MeshPart") then first = c; break end
		if c:IsA("Model") then
			local kids = c:GetChildren()
			local mp = c:FindFirstChildWhichIsA("MeshPart")
			if mp and not c:FindFirstChildWhichIsA("Model") then first = mp; break end
		end
	end
	return first and byMesh[first.MeshId] or nil
end

local shellParams
local function frontOf(cf, size, spec)
	local p = cf.Position
	if spec.towardCentre then
		local d = Vector3.new(C.X - p.X, 0, C.Z - p.Z)
		return d.Unit, true
	end
	if not shellParams then
		shellParams = RaycastParams.new(); shellParams.FilterType = Enum.RaycastFilterType.Include
		shellParams.FilterDescendantsInstances = { hub.Build.Shell }
	end
	local z = cf.LookVector -- (-Z of the old piece)
	z = Vector3.new(z.X, 0, z.Z).Unit
	local a = workspace:Raycast(p, z * 14, shellParams)
	local b = workspace:Raycast(p, -z * 14, shellParams)
	local da, db = a and a.Distance or 1e9, b and b.Distance or 1e9
	if da == 1e9 and db == 1e9 then return z, false end
	-- the nearer wall is behind it
	return if da < db then -z else z, true
end

local function swap(m, src, spec, hold, log)
	local cf, size = meshBox(m)
	if not cf then return false end
	local tmpl = lib:FindFirstChild(spec.to)
	if not tmpl then log.missing[spec.to] = true; return false end
	local new = tmpl:Clone()
	local scale = 1
	if spec.wide then scale = size.X / spec.wide end
	if spec.rod then scale = math.clamp(math.max(size.X, size.Z) / 1.8, 0.6, 1) end
	if math.abs(scale - 1) > 0.01 then new:ScaleTo(scale) end
	local _, ns = new:GetBoundingBox()
	-- where the new one goes
	local pos = cf.Position
	local rot = cf.Rotation
	if spec.flat then rot = CFrame.identity end
	if spec.back then
		local f, sure = frontOf(cf, size, spec)
		if not sure then log.unsure += 1 end
		local backPlane = pos - f * (size.Z / 2)
		pos = backPlane + f * (ns.Z / 2)
		rot = CFrame.lookAt(Vector3.zero, -f).Rotation -- the new piece's +Z (its front) looks along f
	end
	local y = pos.Y
	if spec.seat == "bottom" then y = cf.Position.Y - size.Y / 2 + ns.Y / 2 - (spec.drop or 0)
	elseif spec.seat == "top" then y = cf.Position.Y + size.Y / 2 - ns.Y / 2 end
	if spec.rod then y = cf.Position.Y + size.Y / 2 - ns.Y / 2 end
	new:PivotTo(CFrame.new(pos.X, y, pos.Z) * rot)
	-- a hanging lamp: stretch the rod so the shade ends where the old lamp ended
	if spec.rod then
		local want = size.Y
		local extra = want - ns.Y
		for _, p in new:GetChildren() do
			if p.Name:find("17141f") then
				p.Size = Vector3.new(p.Size.X, math.max(0.2, p.Size.Y + extra), p.Size.Z)
				p.CFrame = p.CFrame - Vector3.new(0, extra / 2, 0)
			elseif not p.Name:find("3a3d4a") then
				p.CFrame = p.CFrame - Vector3.new(0, extra, 0)
			end
		end
	end
	-- the old meshes out (lights that hung on them are kept for the new lens)
	local bundle = Instance.new("Model")
	bundle.Name = m.Name
	bundle:SetAttribute("From", m:GetFullName())
	local lights = {}
	for _, c in m:GetChildren() do
		local isMesh = c:IsA("MeshPart") or (c:IsA("Model") and c:FindFirstChildWhichIsA("MeshPart") and not c:FindFirstChildWhichIsA("Model"))
		if isMesh then
			for _, d in c:GetDescendants() do if d:IsA("Light") or d:IsA("Attachment") then table.insert(lights, d) end end
			if c:IsA("MeshPart") then for _, d in c:GetChildren() do if d:IsA("Light") then table.insert(lights, d) end end end
		end
	end
	local lens, firstPart
	for _, p in new:GetChildren() do
		if p:IsA("BasePart") then
			firstPart = firstPart or p
			if p.Material == Enum.Material.Neon and not lens then lens = p end
		end
	end
	for _, l in lights do if l:IsA("Light") then l.Parent = lens or firstPart end end
	for _, c in m:GetChildren() do
		local isMesh = c:IsA("MeshPart") or (c:IsA("Model") and c:FindFirstChildWhichIsA("MeshPart") and not c:FindFirstChildWhichIsA("Model"))
		if isMesh then c.Parent = bundle end
	end
	bundle.Parent = hold
	for _, p in new:GetChildren() do p.Parent = m end
	new:Destroy()
	m:SetAttribute("Reskin", spec.to)
	return true
end

function R.run(only)
	local hold = backup:FindFirstChild("HubV5")
	if not hold then hold = Instance.new("Folder"); hold.Name = "HubV5"; hold.Parent = backup end
	local log = { done = {}, missing = {}, unsure = 0 }
	local list = {}
	for _, d in hub:GetDescendants() do
		if d:IsA("Model") and not d:GetAttribute("Reskin") and not d:IsDescendantOf(hub.TrainingGround) and not d:IsDescendantOf(hub.Playground) then
			local src = sourceOf(d)
			if src and R.MAP[src] and (not only or only[src]) then table.insert(list, { d, src }) end
		end
	end
	local vend = 0
	for i, it in list do
		local m, src = it[1], it[2]
		-- (a wrapper or an inner model whose parent was just done is in the backup by now: leave it)
		if m:IsDescendantOf(hub) and not m:GetAttribute("Reskin") and swap(m, src, R.MAP[src], hold, log) then
			log.done[src] = (log.done[src] or 0) + 1
			if src == "p_vending" then
				vend += 1
				for _, p in m:GetChildren() do if p:IsA("BasePart") and p.Name:find("plastic_ff4fd8") then p.Color = Color3.fromHex(VEND[(vend - 1) % #VEND + 1]) end end
			end
		end
		if i % 25 == 0 then task.wait() end
	end
	local rows = {}
	for k, v in log.done do table.insert(rows, k .. " x" .. v) end
	table.sort(rows)
	local miss = {}
	for k in log.missing do table.insert(miss, k) end
	return ("swapped: %s | front guessed for %d | missing templates: %s"):format(table.concat(rows, ", "), log.unsure, table.concat(miss, ","))
end

return R
