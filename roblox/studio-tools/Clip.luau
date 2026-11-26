--!nonstrict
-- the clipping checker (26 Nov 2026, the owner: "make sure props dont blick entrances unless entended, make sure
-- propls dont clip into walls or other objkects and props ... the door the slides up leading to the portal isnt properly
-- attatched and the door goes over the the frrame, like clips through it"). ServerStorage.PolishBackup.Clip, run from
-- Studio's command bar (or execute_luau, Edit) on any area: training, a hub, the zombies school.
--
--   local C = require(game.ServerStorage.PolishBackup.Clip:Clone())
--   print(C.run(workspace.Map.Hub.TrainingGround, { doorways = { ... } }))
--
-- Three passes, each a short list with positions (doc: roblox/docs/CLIP-CHECK.md):
--   1. PROPS: a prop (any part of a Model, or a builder part whose name says it is furniture: Bench, Desk, Console,
--      Crate, Seat, Table, Counter, Cradle, Barrel) sunk into another visible part deeper than opts.tol (0.15).
--   2. DOORS: every moving door (a model whose parts carry Shut CFrames: TrainingDoors.client's rollers with Lift and
--      Top, hinged doors with Hinge and Swing) is swept from shut to open in 12 steps. A shown slat must not cut through
--      anything outside its door (sliding wholly into a wall or housing is fine: that is where it goes), and a shown
--      slat's part more than opts.rollZone (1.2, a slat's height: where it rolls in) above the door's Top must be
--      hidden inside something (else it "shows above its frame").
--   3. DOORWAYS: a player's box (2.2 wide, 5 tall, 2 deep, feet 0.2 over the floor) pushed through each doorway
--      (opts.doorways = { { name, at = Vector3 on the floor, dir = Vector3 along the way through, len = 6 } }, and by
--      default every moving door's Center) must meet nothing collidable but the door itself.
-- Left out on purpose (intended overlaps): two parts of one model; invisible parts; glass and see-through parts (0.3+);
-- thin decals and lines (under 0.12, not collidable); trim the builder sets into walls (names with Nose, Lip, Cap,
-- Trim, Frame, Jamb, Head, Reveal, Housing, Bracket, Mount, Plinth, Foot, Base, Collar, Band, Glow, Light, Panel,
-- Line, Word, Plate, Sign, Lens, Hook); kit frames (models named Portal, Frame, Gate, Lamp, Post, Parapet, Crown);
-- a prop standing in a floor or the ground (its middle above the floor's top), or on a floor line; two builder pieces
-- of the same name (a run's joint); trees and rocks in each other or the ground; portal voids and triggers in a
-- doorway; anything whose full name has one of opts.ignore's words.
-- Depth = how far one reaches into the other: exact for two boxes (the separating axes); a mesh is checked by its own
-- triangles (EditableMesh, read once per mesh); a union, wedge or cylinder by its real shape (a box probe). A depth
-- marked [box guess] came from bounding boxes only (both sides odd shapes): worth a look, not proof.
local Clip = {}

local AS = game:GetService("AssetService")

local PROP_NAMES = { "Bench", "Desk", "Console", "Crate", "Seat", "Table", "Counter", "Cradle", "Barrel" }
local SET_IN = { "Nose", "Lip", "Cap", "Trim", "Frame", "Jamb", "Head", "Reveal", "Housing", "Bracket", "Mount", "Plinth", "Foot", "Base",
	"Collar", "Band", "Glow", "Light", "Panel", "Line", "Word", "Plate", "Sign", "Lens", "Hook" }
local KIT_FRAMES = { "Portal", "Frame", "Gate", "Lamp", "Post", "Parapet", "Crown" }
local GROUND = { "Ridge", "Berm", "Floor", "Ground", "Mound", "Grass", "Lawn", "Dirt", "Soil", "Sand", "Hill", "Terrain", "Slope", "Turf", "Gravel" }
local NATURAL = { "Tree", "Pine", "Bush", "Hedge", "Leaf", "Leaves", "Foliage", "Canopy", "Rock", "Boulder", "Shrub", "Fern", "Flower", "Plant", "Ivy", "Vine" }
local NOT_A_WALL = { "Void", "Trigger", "Zone", "Touch", "Sensor" }

local V3 = Vector3.new

local function has(name: string, list: { string }): boolean
	for _, w in list do if string.find(name, w, 1, true) then return true end end
	return false
end

-- how deep two oriented boxes overlap (0 if they don't): the least overlap over the 15 separating axes
local function depth(a: CFrame, sa: Vector3, b: CFrame, sb: Vector3): number
	local axA = { a.RightVector, a.UpVector, a.LookVector }
	local axB = { b.RightVector, b.UpVector, b.LookVector }
	local ha, hb = sa / 2, sb / 2
	local ea, eb = { ha.X, ha.Y, ha.Z }, { hb.X, hb.Y, hb.Z }
	local d = b.Position - a.Position
	local best = math.huge
	local function test(n: Vector3)
		local m = n.Magnitude
		if m < 1e-6 then return true end
		n = n / m
		local ra = ea[1] * math.abs(axA[1]:Dot(n)) + ea[2] * math.abs(axA[2]:Dot(n)) + ea[3] * math.abs(axA[3]:Dot(n))
		local rb = eb[1] * math.abs(axB[1]:Dot(n)) + eb[2] * math.abs(axB[2]:Dot(n)) + eb[3] * math.abs(axB[3]:Dot(n))
		local o = ra + rb - math.abs(d:Dot(n))
		if o <= 0 then return false end
		if o < best then best = o end
		return true
	end
	for i = 1, 3 do if not test(axA[i]) then return 0 end end
	for i = 1, 3 do if not test(axB[i]) then return 0 end end
	for i = 1, 3 do for j = 1, 3 do if not test(axA[i]:Cross(axB[j])) then return 0 end end end
	return best
end
Clip.depth = depth

-- a box's half reach along a unit axis
local function reach(cf: CFrame, s: Vector3, n: Vector3): number
	return (s.X * math.abs(cf.RightVector:Dot(n)) + s.Y * math.abs(cf.UpVector:Dot(n)) + s.Z * math.abs(cf.LookVector:Dot(n))) / 2
end

local function visible(p: BasePart): boolean
	return p.Transparency < 0.95 and p.LocalTransparencyModifier < 0.95
end
local function seeThrough(p: BasePart): boolean
	return p.Transparency >= 0.3 or p.Material == Enum.Material.Glass or p.Material == Enum.Material.ForceField
end
local function thinDecal(p: BasePart): boolean
	local s = p.Size
	return not p.CanCollide and math.min(s.X, s.Y, s.Z) <= 0.12
end
local function isBox(p: BasePart): boolean
	return p:IsA("Part") and p.Shape == Enum.PartType.Block
end

-- the prop a part belongs to: its outermost Model under root that is a piece, not a container (under 400 things; a
-- kit model's pieces may sit in models of their own, and they are one prop)
local sizeOf = {}
local function modelOf(p: Instance, root: Instance): Model?
	local a, best = p.Parent, nil
	while a and a ~= root do
		if a:IsA("Model") then
			local n = sizeOf[a]
			if not n then n = #a:GetDescendants(); sizeOf[a] = n end
			if n >= 400 then break end
			best = a
		end
		a = a.Parent
	end
	return best
end

local function where(v: Vector3): string return ("(%.1f, %.1f, %.1f)"):format(v.X, v.Y, v.Z) end
-- the point of box (cf, s) nearest to v
local function nearest(cf: CFrame, s: Vector3, v: Vector3): Vector3
	local l = cf:PointToObjectSpace(v)
	local h = s / 2
	return cf * V3(math.clamp(l.X, -h.X, h.X), math.clamp(l.Y, -h.Y, h.Y), math.clamp(l.Z, -h.Z, h.Z))
end

-- ---------------------------------------------------------------- real shapes
-- a mesh's triangles, as corners in its own box scaled to 1 (so a part's corner = part.CFrame * (c * part.Size));
-- read once per mesh id; false when the mesh can't be read
local triCache = {}
local function meshTris(mp: Instance)
	if not mp:IsA("MeshPart") then return false end
	local id = mp.MeshId
	if triCache[id] ~= nil then return triCache[id] end
	triCache[id] = false
	local ok, em = pcall(function()
		return AS:CreateEditableMeshAsync(Content.fromUri(id)) -- (as ZFight reads them)
	end)
	if not ok or not em then return false end
	local pts = {}
	local mn, mx = V3(math.huge, math.huge, math.huge), V3(-math.huge, -math.huge, -math.huge)
	local ok2 = pcall(function()
		for _, f in em:GetFaces() do
			local vs = em:GetFaceVertices(f)
			if #vs >= 3 then
				for i = 1, 3 do
					local v = em:GetPosition(vs[i])
					table.insert(pts, v); mn = mn:Min(v); mx = mx:Max(v)
				end
			end
		end
	end)
	pcall(function() em:Destroy() end)
	if not ok2 or #pts == 0 then return false end
	local c, e = (mn + mx) / 2, mx - mn
	e = V3(math.max(e.X, 1e-4), math.max(e.Y, 1e-4), math.max(e.Z, 1e-4))
	for i, v in pts do pts[i] = (v - c) / e end
	triCache[id] = pts
	return pts
end

-- does the triangle (a, b, c, in the box's own space) touch the box of half size h? (the 13 separating axes)
local function triBox(h: Vector3, v0: Vector3, v1: Vector3, v2: Vector3): boolean
	if math.min(v0.X, v1.X, v2.X) > h.X or math.max(v0.X, v1.X, v2.X) < -h.X then return false end
	if math.min(v0.Y, v1.Y, v2.Y) > h.Y or math.max(v0.Y, v1.Y, v2.Y) < -h.Y then return false end
	if math.min(v0.Z, v1.Z, v2.Z) > h.Z or math.max(v0.Z, v1.Z, v2.Z) < -h.Z then return false end
	local function sep(ax: Vector3): boolean
		local p0, p1, p2 = v0:Dot(ax), v1:Dot(ax), v2:Dot(ax)
		local r = h.X * math.abs(ax.X) + h.Y * math.abs(ax.Y) + h.Z * math.abs(ax.Z)
		return math.max(p0, p1, p2) < -r or math.min(p0, p1, p2) > r
	end
	for _, e in { v1 - v0, v2 - v1, v0 - v2 } do
		if sep(V3(0, -e.Z, e.Y)) or sep(V3(e.Z, 0, -e.X)) or sep(V3(-e.Y, e.X, 0)) then return false end
	end
	return not sep((v1 - v0):Cross(v2 - v1))
end

-- how far a mesh (pts at cfm, size sm) reaches into a box (cfb, sb), beyond tol: 0 if not past tol
local function meshDepth(pts, cfm: CFrame, sm: Vector3, cfb: CFrame, sb: Vector3, tol: number): number
	local rel = cfb:ToObjectSpace(cfm)
	local function shrunk(s: number): Vector3
		local h = sb / 2
		return V3(math.max(h.X - s, 0.005), math.max(h.Y - s, 0.005), math.max(h.Z - s, 0.005))
	end
	local h = shrunk(tol)
	local hit = {}
	for i = 1, #pts - 2, 3 do
		local a, b, c = rel * (pts[i] * sm), rel * (pts[i + 1] * sm), rel * (pts[i + 2] * sm)
		if triBox(h, a, b, c) then table.insert(hit, { a, b, c }) end
	end
	if #hit == 0 then return 0 end
	local lo, hi = tol, math.min(sb.X, sb.Y, sb.Z) / 2
	for _ = 1, 6 do
		local mid = (lo + hi) / 2
		local hm, keep = shrunk(mid), {}
		for _, t in hit do if triBox(hm, t[1], t[2], t[3]) then table.insert(keep, t) end end
		if #keep > 0 then lo = mid; hit = keep else hi = mid end
	end
	return math.max(lo, tol + 0.01)
end

-- how far a part's real shape (q, where it stands) reaches into a box (cfb, sb), beyond tol: a shrinking probe box
local probe: Part? = nil
local opProbe = OverlapParams.new(); opProbe.FilterType = Enum.RaycastFilterType.Include; opProbe.RespectCanCollide = false
local function probeDepth(cfb: CFrame, sb: Vector3, q: BasePart, tol: number): number
	if not probe then
		local p = Instance.new("Part")
		p.Name = "ClipProbe"; p.Anchored = true; p.CanCollide = false; p.CanTouch = false; p.CanQuery = false
		p.Transparency = 1; p.Parent = workspace
		probe = p
	end
	local pr = probe :: Part
	opProbe.FilterDescendantsInstances = { q }
	local function touches(s: number): boolean
		pr.Size = V3(math.max(sb.X - 2 * s, 0.01), math.max(sb.Y - 2 * s, 0.01), math.max(sb.Z - 2 * s, 0.01))
		pr.CFrame = cfb
		return #workspace:GetPartsInPart(pr, opProbe) > 0
	end
	if not touches(tol) then return 0 end
	local lo, hi = tol, math.min(sb.X, sb.Y, sb.Z) / 2
	for _ = 1, 6 do
		local mid = (lo + hi) / 2
		if touches(mid) then lo = mid else hi = mid end
	end
	return math.max(lo, tol + 0.01)
end

-- how deep a (at cfa, size sa: it may be a door slat on its way, not where it stands) and b (where it stands) overlap,
-- by their real shapes where they can be read; the second result says when it is only a bounding-box guess
local function overlap(a: BasePart, cfa: CFrame, sa: Vector3, b: BasePart, tol: number): (number, boolean)
	local cfb, sb = b.CFrame, b.Size
	local aBox, bBox = isBox(a), isBox(b)
	if aBox and bBox then return depth(cfa, sa, cfb, sb), false end
	local ta, tb = (not aBox) and meshTris(a), (not bBox) and meshTris(b)
	local aHere = (cfa.Position - a.Position).Magnitude < 1e-3
	if aBox then
		if tb then return meshDepth(tb, cfb, sb, cfa, sa, tol), false end
		return probeDepth(cfa, sa, b, tol), false
	end
	if bBox then
		if ta then return meshDepth(ta, cfa, sa, cfb, sb, tol), false end
		if aHere then return probeDepth(cfb, sb, a, tol), false end
		return depth(cfa, sa, cfb, sb), true
	end
	-- two odd shapes: each one's triangles in the other's box, where there are triangles
	if ta and tb then return math.min(meshDepth(ta, cfa, sa, cfb, sb, tol), meshDepth(tb, cfb, sb, cfa, sa, tol)), false end
	if ta then return meshDepth(ta, cfa, sa, cfb, sb, tol), true end
	if tb then return meshDepth(tb, cfb, sb, cfa, sa, tol), true end
	return depth(cfa, sa, cfb, sb), true
end
Clip.overlap = overlap

-- is the point inside something solid to the eye (opaque, visible, not part of 'door')?
local opPt = OverlapParams.new(); opPt.FilterType = Enum.RaycastFilterType.Include; opPt.RespectCanCollide = false
local function covered(pt: Vector3, door: Instance, doorParts): boolean
	for _, q in workspace:GetPartBoundsInBox(CFrame.new(pt), V3(0.02, 0.02, 0.02), opPt) do
		if doorParts[q] == door or not visible(q) or seeThrough(q) or thinDecal(q) then continue end
		if isBox(q) then
			local l = q.CFrame:PointToObjectSpace(pt)
			local h = q.Size / 2
			if math.abs(l.X) <= h.X + 1e-3 and math.abs(l.Y) <= h.Y + 1e-3 and math.abs(l.Z) <= h.Z + 1e-3 then return true end
		elseif probeDepth(CFrame.new(pt), V3(0.04, 0.04, 0.04), q, 0) > 0 then
			return true
		end
	end
	return false
end

-- the doors in the area: rollers and hinged doors (TrainingDoors.client's attributes)
local function doorsIn(root: Instance)
	local rollers, hinged = {}, {}
	local seen = {}
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") and typeof(d:GetAttribute("Shut")) == "CFrame" then
			local m = d.Parent
			while m and m ~= root and not (m:GetAttribute("Lift") ~= nil or m:GetAttribute("Hinge") ~= nil or m:GetAttribute("Center") ~= nil) do m = m.Parent end
			if m and m ~= root and not seen[m] then
				seen[m] = true
				local slats = {}
				for _, s in m:GetDescendants() do
					if s:IsA("BasePart") and typeof(s:GetAttribute("Shut")) == "CFrame" then table.insert(slats, s) end
				end
				if typeof(m:GetAttribute("Hinge")) == "CFrame" then table.insert(hinged, { m = m, leaf = slats })
				else table.insert(rollers, { m = m, slats = slats }) end
			end
		end
	end
	return rollers, hinged
end

function Clip.run(root: Instance, opts): string
	opts = opts or {}
	local tol = opts.tol or 0.15
	local out = {}
	local t0 = os.clock()
	-- (spatial queries skip CanQuery-off parts, and many props are: on for the scan, back after)
	local was = {}
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") and not d.CanQuery then was[d] = true; d.CanQuery = true end
	end
	local ok, res = pcall(Clip.scan, root, opts, tol, out)
	for d in was do if d.Parent then d.CanQuery = false end end
	if probe then probe:Destroy(); probe = nil end
	if not ok then return "clip check FAILED: " .. tostring(res) end
	table.insert(out, ("(%.1f s)"):format(os.clock() - t0))
	return table.concat(out, "\n")
end

function Clip.scan(root: Instance, opts, tol: number, out)
	local ignore = opts.ignore or {}
	local function ignored(x: Instance): boolean return #ignore > 0 and has(x:GetFullName(), ignore) end
	opPt.FilterDescendantsInstances = { root }
	local doorParts = {}
	local rollers, hinged = doorsIn(root)
	for _, r in rollers do for _, d in r.m:GetDescendants() do if d:IsA("BasePart") then doorParts[d] = r.m end end end
	for _, h in hinged do for _, d in h.m:GetDescendants() do if d:IsA("BasePart") then doorParts[d] = h.m end end end
	local guesses = 0

	-- 1. props
	local op = OverlapParams.new(); op.FilterType = Enum.RaycastFilterType.Include; op.FilterDescendantsInstances = { root }; op.RespectCanCollide = false
	local props, nProps = {}, 0
	for _, p in root:GetDescendants() do
		if p:IsA("BasePart") and visible(p) and not seeThrough(p) and not thinDecal(p) and not doorParts[p] and not ignored(p) then
			local m = modelOf(p, root)
			local isProp = (m ~= nil and not has(m.Name, KIT_FRAMES)) or (m == nil and has(p.Name, PROP_NAMES) and not has(p.Name, SET_IN))
			if isProp then props[p] = m or p; nProps += 1 end
		end
	end
	local done = {}
	for p, owner in props do
		local pNat = has(owner.Name, NATURAL) or has(p.Name, NATURAL)
		for _, q in workspace:GetPartsInPart(p, op) do
			if q == p or not visible(q) or seeThrough(q) or thinDecal(q) or doorParts[q] or ignored(q) then continue end
			local qo = props[q]
			if qo == owner then continue end
			if not qo and has(q.Name, SET_IN) and q.Size.Magnitude < p.Size.Magnitude then continue end -- (trim the prop sits against)
			if owner == p and qo == q and p.Name == q.Name then continue end -- (two pieces of one builder run: a joint)
			-- a prop standing in a floor or the ground: its middle above the floor's top and over the floor (or over a
			-- ground piece's middle)
			local ry, rx, rz = reach(q.CFrame, q.Size, Vector3.yAxis), reach(q.CFrame, q.Size, Vector3.xAxis), reach(q.CFrame, q.Size, Vector3.zAxis)
			local over = math.abs(p.Position.X - q.Position.X) <= rx and math.abs(p.Position.Z - q.Position.Z) <= rz
			local flat = ry < 0.5 * math.min(rx, rz)
			if (over or ry <= 0.15) and flat and p.Position.Y > q.Position.Y + ry - 0.05 then continue end -- (on a floor, or on a line or mat on it)
			if over and has(q.Name, GROUND) and p.Position.Y > q.Position.Y then continue end
			local qNat = has((qo or q).Name, NATURAL) or has(q.Name, NATURAL)
			if pNat and (qNat or has(q.Name, GROUND)) then continue end
			local key = if qo then (if tostring(owner) < tostring(qo) then tostring(owner) .. "|" .. tostring(qo) else tostring(qo) .. "|" .. tostring(owner)) else tostring(owner) .. "|" .. q:GetFullName()
			if done[key] and done[key].d >= depth(p.CFrame, p.Size, q.CFrame, q.Size) then continue end -- (can't beat what's found)
			local dd, guess = overlap(p, p.CFrame, p.Size, q, tol)
			if dd > tol and (not done[key] or dd > done[key].d) then
				done[key] = { d = dd, a = owner, b = qo or q, at = nearest(q.CFrame, q.Size, p.Position), guess = guess }
			end
		end
	end
	local hits = {}
	for _, h in done do table.insert(hits, h) end
	table.sort(hits, function(a, b) return a.d > b.d end)
	table.insert(out, ("PROPS: %d props, %d sunk deeper than %.2f"):format(nProps, #hits, tol))
	for i = 1, math.min(#hits, opts.max or 40) do
		local h = hits[i]
		if h.guess then guesses += 1 end
		table.insert(out, ("  CLIP %.2f deep: %s into %s at %s%s"):format(h.d, h.a:GetFullName(), h.b:GetFullName(), where(h.at), if h.guess then " [box guess]" else ""))
	end

	-- 2. doors
	local opD = OverlapParams.new(); opD.FilterType = Enum.RaycastFilterType.Include; opD.FilterDescendantsInstances = { root }; opD.RespectCanCollide = false
	local nDoor, doorHits = 0, {}
	local function note(key: string, h)
		if not doorHits[key] or h.d > doorHits[key].d then doorHits[key] = h end
	end
	local function sweepPart(door: Instance, part: BasePart, cf: CFrame, stage: string)
		local L = cf.LookVector
		for _, q in workspace:GetPartBoundsInBox(cf, part.Size, opD) do
			if doorParts[q] == door or not visible(q) or seeThrough(q) or thinDecal(q) or ignored(q) then continue end
			-- sliding wholly into a wall or a housing (the wall covers the slat's whole thickness) is where it goes
			local c = (q.Position - cf.Position):Dot(L)
			local rq, rs = reach(q.CFrame, q.Size, L), part.Size.Z / 2
			if c - rq <= -rs + 0.02 and c + rq >= rs - 0.02 then continue end
			local dd, guess = overlap(part, cf, part.Size, q, tol)
			if dd > tol then
				note(door:GetFullName() .. "|" .. q:GetFullName(), { d = dd, door = door, what = ("passes %.2f into %s"):format(dd, q:GetFullName()), stage = stage, at = nearest(cf, part.Size, q.Position), guess = guess })
			end
		end
	end
	for _, r in rollers do
		nDoor += 1
		local lift = r.m:GetAttribute("Lift"); lift = if type(lift) == "number" then lift else 10
		local top = r.m:GetAttribute("Top"); top = if type(top) == "number" then top else math.huge
		for k = 0, 12 do
			local u = k / 12
			local stage = ("%d%% open"):format(math.floor(u * 100))
			for _, s in r.slats do
				local cf = s:GetAttribute("Shut") + V3(0, u * lift, 0)
				local hy = reach(cf, s.Size, Vector3.yAxis)
				if cf.Y - hy > top then continue end -- (hidden from here up)
				sweepPart(r.m, s, cf, stage)
				-- its part above Top must be hidden inside something
				if cf.Y + hy > top + 0.1 then
					local worst = 0
					local wpt = nil
					for _, fx in { -0.45, -0.25, 0, 0.25, 0.45 } do
						local y = top + 0.1
						while y <= cf.Y + hy - 0.02 do
							local l = cf:PointToObjectSpace(V3(cf.X, y, cf.Z))
							local pt = cf * V3(fx * s.Size.X, l.Y, 0)
							if not covered(pt, r.m, doorParts) and y - top > worst then worst = y - top; wpt = pt end
							y += 0.4
						end
					end
					if wpt and worst > (opts.rollZone or 1.2) then -- (a slat's own height over Top is where it rolls in)
						note(r.m:GetFullName() .. "|show|" .. s.Name, { d = worst, door = r.m, what = ("shows %.2f above its frame (%s, nothing hides it)"):format(worst, s.Name), stage = stage, at = wpt })
					end
				end
			end
		end
	end
	for _, h in hinged do
		nDoor += 1
		local hinge = h.m:GetAttribute("Hinge"); local sw = h.m:GetAttribute("Swing"); sw = if type(sw) == "number" then sw else -math.pi / 2
		for k = 0, 12 do
			local a = sw * k / 12
			for _, s in h.leaf do
				local rel = hinge:ToObjectSpace(s:GetAttribute("Shut"))
				sweepPart(h.m, s, hinge * CFrame.Angles(0, a, 0) * rel, ("%d%% swung"):format(math.floor(k / 12 * 100)))
			end
		end
	end
	local dh = {}
	for _, h in doorHits do table.insert(dh, h) end
	table.sort(dh, function(a, b) return a.d > b.d end)
	table.insert(out, ("DOORS: %d moving doors, %d clip on their way"):format(nDoor, #dh))
	for i = 1, math.min(#dh, opts.max or 40) do
		local h = dh[i]
		if h.guess then guesses += 1 end
		table.insert(out, ("  DOOR %s %s at %s (%s)%s"):format(h.door:GetFullName(), h.what, where(h.at), h.stage, if h.guess then " [box guess]" else ""))
	end

	-- 3. doorways
	local ways = {}
	for _, w in opts.doorways or {} do table.insert(ways, w) end
	if opts.autoDoors ~= false then
		for _, r in rollers do
			local c = r.m:GetAttribute("Center")
			if typeof(c) == "Vector3" and r.slats[1] then
				table.insert(ways, { name = r.m:GetFullName(), at = c, dir = r.slats[1]:GetAttribute("Shut").LookVector, len = 6, door = r.m })
			end
		end
		for _, h in hinged do
			local c = h.m:GetAttribute("Center")
			if typeof(c) == "Vector3" and h.leaf[1] then
				table.insert(ways, { name = h.m:GetFullName(), at = c, dir = h.leaf[1]:GetAttribute("Shut").LookVector, len = 6, door = h.m })
			end
		end
	end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { root }; rp.RespectCanCollide = true
	local opW = OverlapParams.new(); opW.FilterType = Enum.RaycastFilterType.Include; opW.FilterDescendantsInstances = { root }; opW.RespectCanCollide = true
	local BODY = V3(2.2, 5, 2)
	local blocked = {}
	for _, w in ways do
		local dir = V3(w.dir.X, 0, w.dir.Z)
		dir = if dir.Magnitude > 0.01 then dir.Unit else V3(0, 0, 1)
		local fh = workspace:Raycast(w.at + V3(0, 3, 0), V3(0, -12, 0), rp)
		local floorY = if fh then fh.Position.Y else w.at.Y
		local len = w.len or 6
		local worst = nil
		for t = -len / 2, len / 2, 0.5 do
			local c = V3(w.at.X, floorY + 0.2 + 2.5, w.at.Z) + dir * t
			local cf = CFrame.lookAt(c, c + dir)
			for _, q in workspace:GetPartBoundsInBox(cf, BODY, opW) do
				if (w.door and q:IsDescendantOf(w.door)) or q.Name == "DoorBlock" or q.Name == "EggBlock" or has(q.Name, NOT_A_WALL) or ignored(q) then continue end
				if not q.CanCollide then continue end
				-- (a body is stopped by the real collision shape: boxes exactly, anything else by the probe)
				local dd = if isBox(q) then depth(cf, BODY, q.CFrame, q.Size) else probeDepth(cf, BODY, q, 0.1)
				if dd > 0.1 and (not worst or dd > worst.d) then worst = { d = dd, q = q, at = c } end
			end
		end
		if worst then table.insert(blocked, { w = w, hit = worst }) end
	end
	table.insert(out, ("DOORWAYS: %d checked, %d blocked"):format(#ways, #blocked))
	for _, b in blocked do
		table.insert(out, ("  BLOCKED %s by %s (%.2f deep) at %s"):format(b.w.name or "?", b.hit.q:GetFullName(), b.hit.d, where(b.hit.at)))
	end
	local unread = 0
	for _, v in triCache do if v == false then unread += 1 end end
	if guesses > 0 or unread > 0 then table.insert(out, ("(%d meshes could not be read; %d lines are box guesses)"):format(unread, guesses)) end
end

return Clip
