-- The grapple heads into the place (roblox/docs/GRAPPLES.md). Run from Studio (execute_luau, Edit), e.g. as
-- ServerStorage.PolishBackup.GrappleImport (not yet in studio.project.json) or pasted into an unparented ModuleScript:
--
--   local G = require(<this module>:Clone())
--   G.build(nil, true)   -- a DRY run: loads every upload, builds each head, reports its size and frame check, keeps nothing
--   G.build()            -- builds ReplicatedStorage.JankfireGrapples.<id> for all eight (or G.build({ "laser" }))
--   G.check()            -- every head there, its pivot the bite, its box where the file says
--
-- The uploads come from tools/roblox/grapple_heads.py, one per head, turned for Roblox (rbxglb): they land in the HEAD
-- FRAME at 1 stud per file unit. Pieces arrive as MeshParts named "<id>_<node>__<look>" (the name rides on the Model
-- round each one) at their box centres, unrotated. Each head becomes a Model named by its id: pivot = the bite (the
-- file's origin, identity rotation: -Z into the wall, +Y up), each piece a MeshPart named by its node, painted from its
-- look code (p = SmoothPlastic, n = Neon, g = SmoothPlastic see-through: two hex digits of opacity follow the colour),
-- anchored, no collision / query / touch, attributes Tail (studs back from the bite where the rope ties on) and Asset.
-- shared/GrappleLook.luau clones them onto the ropes; Flair.grappleReady reads whether one is there.
local G = {}

G.ASSETS = {
	rope = 113932793511930, chain = 109288193353572, candy = 110813247615068, plunger = 82089190964520,
	vine = 85954939445069, laser = 79595434254565, sticky = 90493771144036, rainbow = 73499289204214,
}
-- per head, from grapples.json (head frame, studs): the file's box, the tie, each piece's box centre (mid: a MeshPart
-- lands at its box centre, so these catch a wrong turn, which the box alone would not)
G.INFO = {
	rope = { lo = { -0.5728, -0.3613, 0 }, hi = { 0.5728, 0.6502, 1.634 }, tail = 1.5,
		mid = { crown = { 0, 0, 0.67 }, body = { 0, 0.1444, 0.8459 }, lash = { 0, 0, 1.04 } } },
	chain = { lo = { -0.4618, -0.4618, -0.0179 }, hi = { 0.4618, 0.4618, 1.326 }, tail = 1.28,
		mid = { dark = { 0, 0, 0.615 }, body = { 0, 0, 0.6541 } } },
	candy = { lo = { -0.125, -0.125, 0.0001 }, hi = { 0.125, 0.7039, 1.745 }, tail = 1.6,
		mid = { stripe = { 0, 0.2879, 0.8745 }, cane = { 0, 0.2894, 0.8726 } } },
	plunger = { lo = { -0.478, -0.478, 0.0193 }, hi = { 0.478, 0.478, 1.735 }, tail = 1.7,
		mid = { cup = { 0, 0, 0.225 }, rim = { 0, 0, 0.2596 }, handle = { 0, 0, 1.03 }, knob = { 0, 0, 1.64 } } },
	vine = { lo = { -0.4768, -0.6317, 0.0023 }, hi = { 0.5479, 0.6317, 1.44 }, tail = 1.44,
		mid = { knot = { 0, 0, 0.13 }, wood = { 0, 0, 0.7211 }, vine = { 0, 0, 1.064 }, leaf = { 0.0356, 0.0184, 1.18 } } },
	laser = { lo = { -0.3182, -0.36, -0.0157 }, hi = { 0.3182, 0.3438, 1.255 }, tail = 1.22,
		mid = { glow = { 0, 0, 0.6437 }, face = { 0, 0, 0.2 }, body = { 0, 0, 0.7 }, fin = { 0, -0.0081, 0.5809 } } },
	sticky = { lo = { -0.4003, -0.0673, 0.0142 }, hi = { 0.5135, 1.1049, 0.4883 }, tail = 0.42,
		mid = { hand = { 0.0566, 0.5188, 0.2513 } } },
	rainbow = { lo = { -0.5992, -0.5187, 0.01 }, hi = { 0.5992, 0.63, 0.39 }, tail = 0.33,
		mid = { star = { 0, 0.0556, 0.2 } } },
}
G.ORDER = { "rope", "chain", "candy", "plunger", "vine", "laser", "sticky", "rainbow" }

local function v3(t: { number }): Vector3 return Vector3.new(t[1], t[2], t[3]) end

local function look(p: BasePart, code: string)
	local kind, hex, alpha = string.sub(code, 1, 1), string.sub(code, 2, 7), string.sub(code, 8, 9)
	p.Color = Color3.fromHex(hex)
	p.Material = if kind == "n" then Enum.Material.Neon else Enum.Material.SmoothPlastic
	p.Reflectance = if kind == "g" then 0.12 else 0
	p.Transparency = if kind == "g" and #alpha == 2 then 1 - (tonumber(alpha, 16) or 255) / 255 else 0
	p.CastShadow = kind == "p"
	if p:IsA("MeshPart") then p.TextureID = "" end
	for _, c in p:GetChildren() do if c:IsA("SurfaceAppearance") then c:Destroy() end end
end

local function lib(): Folder
	local f = game.ReplicatedStorage:FindFirstChild("JankfireGrapples")
	if not f then
		f = Instance.new("Folder")
		f.Name = "JankfireGrapples"
		f.Parent = game.ReplicatedStorage
	end
	return f :: Folder
end

-- one head from its upload -> a Model in the head frame at the world origin (not parented)
local function head(id: string): (Model?, string)
	local asset, info = G.ASSETS[id], G.INFO[id]
	if not asset or not info then return nil, id .. ": unknown" end
	local ok, res = pcall(function() return game:GetService("InsertService"):LoadAsset(asset) end)
	if not ok then return nil, id .. ": load failed: " .. tostring(res) end
	local parts: { BasePart } = {}
	for _, d in res:GetDescendants() do
		if d:IsA("BasePart") then
			local nm = if d.Parent and d.Parent ~= res and d.Parent:IsA("Model") then d.Parent.Name else d.Name
			d:SetAttribute("Piece", nm)
			table.insert(parts, d)
		end
	end
	if #parts == 0 then res:Destroy(); return nil, id .. ": no parts" end
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, p in parts do lo = lo:Min(p.Position - p.Size / 2); hi = hi:Max(p.Position + p.Size / 2) end
	local flo, fhi = v3(info.lo), v3(info.hi)
	local origin = (lo + hi) / 2 - (flo + fhi) / 2 -- (where the file's origin, the bite, landed)
	local m = Instance.new("Model")
	m.Name = id
	local big: BasePart? = nil
	for _, p in parts do
		local nm = p:GetAttribute("Piece") :: string
		local node, code = string.match(nm, "^%a+_(.-)__(%w+)$")
		local c = p:Clone()
		for _, x in c:GetChildren() do if not x:IsA("SurfaceAppearance") then x:Destroy() end end
		c.Name = node or nm
		c:SetAttribute("Piece", nil)
		c:SetAttribute("Look", code)
		if code then look(c, code) end
		c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.Massless = true
		pcall(function() (c :: any).CollisionFidelity = Enum.CollisionFidelity.Box end)
		c.CFrame = CFrame.new(p.Position - origin)
		c.Parent = m
		if not big or c.Size.Magnitude > (big :: BasePart).Size.Magnitude then big = c end
	end
	res:Destroy()
	m.PrimaryPart = big
	-- (with a PrimaryPart the model's pivot is that part's own, so its PivotOffset carries the bite: GetPivot() = identity)
	if big then (big :: BasePart).PivotOffset = (big :: BasePart).CFrame:Inverse() end
	m.WorldPivot = CFrame.identity
	m:SetAttribute("Tail", info.tail)
	m:SetAttribute("Asset", asset)
	-- the frame check: every piece's centre against the file's (a wrong turn moves them; the box alone would not show it)
	local err = 0
	for _, p in m:GetChildren() do
		local want = p:IsA("BasePart") and info.mid[p.Name]
		if want then err = math.max(err, (p.Position - v3(want)).Magnitude) end
	end
	local _, size = m:GetBoundingBox()
	return m, ("%s: %d pieces, %.2f x %.2f x %.2f studs, pieces off by %.3f%s"):format(id, #parts, size.X, size.Y, size.Z,
		err, if err > 0.02 then "  <-- CHECK THE TURN" else "")
end

-- build the heads into ReplicatedStorage.JankfireGrapples (dry = report only, nothing kept)
function G.build(ids: { string }?, dry: boolean?): string
	local out = {}
	for _, id in ids or G.ORDER do
		local m, msg = head(id)
		table.insert(out, msg)
		if m then
			if dry then
				m:Destroy()
			else
				local f = lib()
				local old = f:FindFirstChild(id)
				if old then old:Destroy() end
				m.Parent = f
			end
		end
	end
	return table.concat(out, "\n")
end

function G.check(): string
	local f = game.ReplicatedStorage:FindFirstChild("JankfireGrapples")
	if not f then return "no ReplicatedStorage.JankfireGrapples" end
	local out = {}
	for _, id in G.ORDER do
		local m = f:FindFirstChild(id)
		if not m or not m:IsA("Model") then table.insert(out, id .. ": MISSING"); continue end
		local info = G.INFO[id]
		local pv = m:GetPivot()
		local n, bad, err = 0, 0, 0
		for _, p in m:GetDescendants() do
			if p:IsA("BasePart") then
				n += 1
				if p.CanCollide or p.CanQuery or p.CanTouch or not p.Anchored then bad += 1 end
				local want = info.mid[p.Name]
				if want then err = math.max(err, (pv:PointToObjectSpace(p.Position) - v3(want)).Magnitude) end
			end
		end
		table.insert(out, ("%s: %d parts, tail %s, pieces off by %.3f%s%s"):format(id, n, tostring(m:GetAttribute("Tail")), err,
			if bad > 0 then ", " .. bad .. " parts collide/query/touch or loose" else "", if err > 0.02 then "  <-- CHECK" else ""))
	end
	return table.concat(out, "\n")
end

return G
