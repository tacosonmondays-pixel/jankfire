-- ZFight: finds z-fighting (flicker) in a built map. Two visible surfaces that lie in the same plane, face the same way
-- and overlap fight over which one the GPU draws, so they shimmer as the camera moves. Run it after every rebuild.
--
--   local Z = require(game.ServerStorage.PolishBackup.ZFight:Clone())
--   Z.start({ workspace.Map.RooftopV3 }, { tol = 0.02 })   -- roots to scan, options (all optional)
--   repeat local s = Z.step(20) until s == "done"           -- or call Z.step(20) once per execute_luau until "done"
--   print(Z.report(40))                                     -- ranked list; Z.results() gives the table
--   Z.clear()                                               -- free the memory
--
-- Every visible BasePart (Transparency < 1) becomes world-space triangles: blocks and wedges from their size, cylinder
-- caps as 24-gons, MeshParts from their real mesh (AssetService:CreateEditableMeshAsync, cached per MeshId), so the
-- colour-merged kits (r2_*, r3_*) are checked face by face, not by their boxes. Triangles are bucketed by plane
-- (normal, offset); in each bucket, triangles of DIFFERENT parts with a DIFFERENT look (colour, material, variant,
-- texture, transparency) that face the same way, lie within `tol` studs of each other and overlap by more than
-- `minArea` square studs are a hit. Same-look overlaps are skipped: they cannot be seen. Back-to-back faces (opposite
-- normals) are not a fight either.
-- A hit is "covered" when the point just in front of it is inside another visible block (then nobody sees it).
-- Ranking: overlap area, weighted down with distance to the nearest place players stand (spawns, pads), and ceilings
-- (faces pointing down) count a little less. Unions and balls are skipped and counted.
local ZF = {}
local AS = game:GetService("AssetService")
local V = Vector3.new

local function S()
	shared.ZF_STATE = shared.ZF_STATE or {}
	return shared.ZF_STATE
end
shared.ZF_MESHES = shared.ZF_MESHES or {} -- MeshId -> { tris = { {a,b,c}... } in mesh space, c0 = bbox centre } | false

local function lookOf(p: BasePart): string
	local k = p.Color:ToHex() .. "|" .. p.Material.Name .. "|" .. p.MaterialVariant .. ("|%.2f"):format(p.Transparency)
	if p:IsA("MeshPart") then k ..= "|" .. p.TextureID end
	local sa = p:FindFirstChildWhichIsA("SurfaceAppearance")
	if sa then
		local ok, cm = pcall(function() return (sa :: any).ColorMap end)
		k ..= "|SA" .. (if ok then tostring(cm) else sa.Name)
	end
	return k
end

-- triangles of a convex solid in local space, outward-wound using the solid's centre (local origin)
local function addConvex(list, cf: CFrame, tris)
	for _, t in tris do
		local a, b, c = cf * t[1], cf * t[2], cf * t[3]
		local n = (b - a):Cross(c - a)
		if n:Dot((a + b + c) / 3 - cf.Position) < 0 then b, c = c, b end
		table.insert(list, { a, b, c })
	end
end
local function quad(t, p1, p2, p3, p4)
	table.insert(t, { p1, p2, p3 }); table.insert(t, { p1, p3, p4 })
end
local function boxTris(h: Vector3)
	local t = {}
	local x, y, z = h.X, h.Y, h.Z
	quad(t, V(x, -y, -z), V(x, y, -z), V(x, y, z), V(x, -y, z)); quad(t, V(-x, -y, -z), V(-x, y, -z), V(-x, y, z), V(-x, -y, z))
	quad(t, V(-x, y, -z), V(x, y, -z), V(x, y, z), V(-x, y, z)); quad(t, V(-x, -y, -z), V(x, -y, -z), V(x, -y, z), V(-x, -y, z))
	quad(t, V(-x, -y, z), V(x, -y, z), V(x, y, z), V(-x, y, z)); quad(t, V(-x, -y, -z), V(x, -y, -z), V(x, y, -z), V(-x, y, -z))
	return t
end
local function wedgeTris(h: Vector3)
	-- Roblox wedge: full bottom and back (+Z) faces, the slope rises from the front-bottom edge to the back-top edge
	local t = {}
	local x, y, z = h.X, h.Y, h.Z
	quad(t, V(-x, -y, -z), V(x, -y, -z), V(x, -y, z), V(-x, -y, z))
	quad(t, V(-x, -y, z), V(x, -y, z), V(x, y, z), V(-x, y, z))
	quad(t, V(-x, -y, -z), V(x, -y, -z), V(x, y, z), V(-x, y, z))
	table.insert(t, { V(x, -y, -z), V(x, -y, z), V(x, y, z) }); table.insert(t, { V(-x, -y, -z), V(-x, -y, z), V(-x, y, z) })
	return t
end
local function cylinderCaps(h: Vector3)
	local t, r, N = {}, math.min(h.Y, h.Z), 24
	for _, sx in { -1, 1 } do
		for i = 0, N - 1 do
			local a0, a1 = i / N * math.pi * 2, (i + 1) / N * math.pi * 2
			table.insert(t, { V(sx * h.X, 0, 0), V(sx * h.X, math.cos(a0) * r, math.sin(a0) * r), V(sx * h.X, math.cos(a1) * r, math.sin(a1) * r) })
		end
	end
	return t
end

local function meshTris(p: MeshPart)
	local id = p.MeshId
	local cached = shared.ZF_MESHES[id]
	if cached ~= nil then return cached end
	local ok, em = pcall(function() return AS:CreateEditableMeshAsync(Content.fromUri(id)) end)
	if not ok or not em then shared.ZF_MESHES[id] = false; return false end
	local mn, mx = V(1e9, 1e9, 1e9), V(-1e9, -1e9, -1e9)
	for _, v in em:GetVertices() do local q = em:GetPosition(v); mn = mn:Min(q); mx = mx:Max(q) end
	local tris = {}
	local pos = {}
	for _, v in em:GetVertices() do pos[v] = em:GetPosition(v) end
	local vol = 0
	for _, f in em:GetFaces() do
		local vs = em:GetFaceVertices(f)
		if #vs == 3 then
			local a, b, c = pos[vs[1]], pos[vs[2]], pos[vs[3]]
			vol += a:Dot(b:Cross(c))
			table.insert(tris, { a, b, c })
		end
	end
	em:Destroy()
	-- winding: the kits are closed solids, so the signed volume says which way the faces turn; flip all if inward
	if vol < 0 then for _, t in tris do t[2], t[3] = t[3], t[2] end end
	local rec = { tris = tris, c0 = (mn + mx) / 2, size = mx - mn }
	shared.ZF_MESHES[id] = rec
	return rec
end

local function partTris(p: BasePart)
	local list = {}
	local h = p.Size / 2
	if p:IsA("MeshPart") then
		local rec = meshTris(p)
		if not rec then return nil, "mesh failed" end
		local sz = rec.size
		local sc = V(if sz.X > 1e-6 then p.Size.X / sz.X else 1, if sz.Y > 1e-6 then p.Size.Y / sz.Y else 1, if sz.Z > 1e-6 then p.Size.Z / sz.Z else 1)
		local cf, c0 = p.CFrame, rec.c0
		for _, t in rec.tris do
			table.insert(list, { cf * ((t[1] - c0) * sc), cf * ((t[2] - c0) * sc), cf * ((t[3] - c0) * sc) })
		end
		return list
	elseif p:IsA("WedgePart") then
		addConvex(list, p.CFrame, wedgeTris(h)); return list
	elseif p:IsA("Part") then
		local sh = p.Shape
		if sh == Enum.PartType.Block then addConvex(list, p.CFrame, boxTris(h)); return list end
		if sh == Enum.PartType.Wedge then addConvex(list, p.CFrame, wedgeTris(h)); return list end
		if sh == Enum.PartType.Cylinder then addConvex(list, p.CFrame, cylinderCaps(h)); return list end
		return nil, "shape " .. sh.Name
	end
	return nil, p.ClassName
end

local function isWalkPoint(d: Instance): boolean
	if not d:IsA("BasePart") then return false end
	local n = d.Name
	return d:IsA("SpawnLocation") or n:find("Spawn") ~= nil or n:find("Pad") ~= nil or n:find("Arrive") ~= nil
end

function ZF.start(roots: { Instance }, opts: any?): string
	local o = opts or {}
	local st = S()
	table.clear(st)
	st.tol = o.tol or 0.02
	st.minArea = o.minArea or 0.01
	st.skipName = o.skipName -- optional Lua pattern: parts whose full name matches are ignored
	st.parts, st.looks, st.queue, st.walk = {}, {}, {}, {}
	st.buckets = {}
	st.skipped = {}
	st.minY = o.minY -- optional: hits below this height are "unseen" (under a city's ground plates, say)
	st.tris = 0
	st.phase = "fetch"
	st.qi = 1
	st.fetch, st.fi, st.inflight = {}, 1, 0
	for _, r in roots do
		for _, d in r:GetDescendants() do
			if d:IsA("BasePart") and d.Transparency < 1 and not d:IsA("Terrain") then
				if not (st.skipName and d:GetFullName():find(st.skipName)) then table.insert(st.queue, d) end
			end
			if isWalkPoint(d) then table.insert(st.walk, (d :: BasePart).Position) end
		end
	end
	local seen = {}
	for _, p in st.queue do
		if p:IsA("MeshPart") and shared.ZF_MESHES[p.MeshId] == nil and not seen[p.MeshId] then seen[p.MeshId] = true; table.insert(st.fetch, p) end
	end
	st.roots = {}
	for _, r in roots do table.insert(st.roots, r:GetFullName()) end
	return ("queued %d parts, %d walk points"):format(#st.queue, #st.walk)
end

local function bucketKey(n: Vector3, d: number, step: number): (string, number)
	return math.round(n.X * 20) .. "," .. math.round(n.Y * 20) .. "," .. math.round(n.Z * 20), math.floor(d / step)
end

local function collectOne(st, p: BasePart)
	local list, why = partTris(p)
	if not list then
		st.skipped[why] = (st.skipped[why] or 0) + 1
		return
	end
	local pi = #st.parts + 1
	st.parts[pi] = p
	st.looks[pi] = lookOf(p)
	local minA2 = st.minArea * 2
	for _, t in list do
		local a, b, c = t[1], t[2], t[3]
		local cr = (b - a):Cross(c - a)
		local m = cr.Magnitude
		if m >= minA2 then
			local n = cr / m
			local d = n:Dot(a)
			local nk, dk = bucketKey(n, d, 0.1)
			local nb = st.buckets[nk]
			if not nb then nb = {}; st.buckets[nk] = nb end
			local bl = nb[dk]
			if not bl then bl = {}; nb[dk] = bl end
			table.insert(bl, { a, b, c, n, d, pi, a:Min(b):Min(c), a:Max(b):Max(c) })
			st.tris += 1
		end
	end
end

-- area of triangle B clipped by triangle A, both projected on A's plane
local function overlap(A, B): (number, Vector3?)
	local o = A[1]
	local u = (A[2] - o).Unit
	local w = A[4]:Cross(u)
	local function pr(p) local q = p - o; return { u:Dot(q), w:Dot(q) } end
	local clip = { pr(A[1]), pr(A[2]), pr(A[3]) }
	local poly = { pr(B[1]), pr(B[2]), pr(B[3]) }
	for i = 1, 3 do
		local p1, p2 = clip[i], clip[i % 3 + 1]
		local ex, ey = p2[1] - p1[1], p2[2] - p1[2]
		local function side(q) return ex * (q[2] - p1[2]) - ey * (q[1] - p1[1]) end
		local out = {}
		local n = #poly
		if n == 0 then return 0 end
		for j = 1, n do
			local cur, nxt = poly[j], poly[j % n + 1]
			local sc, sn = side(cur), side(nxt)
			if sc >= -1e-7 then table.insert(out, cur) end
			if (sc >= -1e-7) ~= (sn >= -1e-7) then
				local tt = sc / (sc - sn)
				table.insert(out, { cur[1] + (nxt[1] - cur[1]) * tt, cur[2] + (nxt[2] - cur[2]) * tt })
			end
		end
		poly = out
	end
	local n = #poly
	if n < 3 then return 0 end
	local ar, cx, cy = 0, 0, 0
	for j = 1, n do
		local p, q = poly[j], poly[j % n + 1]
		local cr = p[1] * q[2] - q[1] * p[2]
		ar += cr; cx += (p[1] + q[1]) * cr; cy += (p[2] + q[2]) * cr
	end
	if math.abs(ar) < 1e-9 then return 0 end
	cx /= 3 * ar; cy /= 3 * ar
	return math.abs(ar) / 2, o + u * cx + w * cy
end

local function compareLists(st, L1, L2, same: boolean)
	local tol = st.tol
	local looks = st.looks
	-- one list sorted by min X, swept: a pair is only tested while their X ranges can still meet. with two buckets,
	-- only pairs that take one triangle from each are tested (the bucket's own pairs are done by its own work item)
	local L, tag = {}, {}
	for _, t in L1 do table.insert(L, t); tag[t] = 1 end
	if not same then for _, t in L2 do table.insert(L, t); tag[t] = 2 end end
	table.sort(L, function(x, y) return x[7].X < y[7].X end)
	for i = 1, #L do
		local A = L[i]
		local la = looks[A[6]]
		local ta = tag[A]
		local amin, amax = A[7] - V(tol, tol, tol), A[8] + V(tol, tol, tol)
		for j = i + 1, #L do
			local B = L[j]
			if B[7].X > amax.X then break end
			if B[6] ~= A[6] and looks[B[6]] ~= la and (same or tag[B] ~= ta) then
				local bmin, bmax = B[7], B[8]
				if bmin.X <= amax.X and bmax.X >= amin.X and bmin.Y <= amax.Y and bmax.Y >= amin.Y and bmin.Z <= amax.Z and bmax.Z >= amin.Z
					and A[4]:Dot(B[4]) > 0.999 then
					local n = A[4]
					local g = math.max(math.abs(n:Dot(B[1] - A[1])), math.abs(n:Dot(B[2] - A[1])), math.abs(n:Dot(B[3] - A[1])))
					if g <= tol then
						local ar, c = overlap(A, B)
						if ar > 1e-4 then
							local pa, pb = math.min(A[6], B[6]), math.max(A[6], B[6])
							local key = pa .. ":" .. pb .. ":" .. math.round(n.X * 20) .. "," .. math.round(n.Y * 20) .. "," .. math.round(n.Z * 20)
							local r = st.hits[key]
							if not r then r = { a = pa, b = pb, n = n, area = 0, c = V(), gap = 0, best = 0 }; st.hits[key] = r end
							r.area += ar
							r.c += (c :: Vector3) * ar
							r.gap = math.max(r.gap, g)
							if ar > r.best then r.best = ar; r.pt = c end
						end
					end
				end
			end
		end
	end
end

local function insideVisibleBlock(st, pt: Vector3, except: { [BasePart]: boolean }): BasePart?
	for _, q in workspace:GetPartBoundsInRadius(pt, 0.01) do
		if not except[q] and q.Transparency < 0.05 and q:IsA("Part") and q.Shape == Enum.PartType.Block then
			local lp = q.CFrame:PointToObjectSpace(pt)
			local h = q.Size / 2
			if math.abs(lp.X) < h.X and math.abs(lp.Y) < h.Y and math.abs(lp.Z) < h.Z then return q end
		end
	end
	return nil
end

function ZF.step(budget: number?): string
	local st = S()
	if not st.phase then return "not started" end
	local t0 = os.clock()
	local limit = budget or 20
	local slice = os.clock()
	local function tick()
		if os.clock() - slice > 0.1 then task.wait(); slice = os.clock() end
		return os.clock() - t0 < limit
	end
	-- meshes download one by one in about 0.4 s each, so fetch them 24 at a time first (each is cached by MeshId)
	if st.phase == "fetch" then
		while st.fi <= #st.fetch or st.inflight > 0 do
			while st.fi <= #st.fetch and st.inflight < 24 do
				local p = st.fetch[st.fi]
				st.fi += 1
				st.inflight += 1
				task.spawn(function() pcall(meshTris, p); st.inflight -= 1 end)
			end
			task.wait()
			if os.clock() - t0 > limit then return ("fetch %d/%d meshes"):format(st.fi - 1 - st.inflight, #st.fetch) end
		end
		st.phase = "collect"
	end
	if st.phase == "collect" then
		while st.qi <= #st.queue do
			collectOne(st, st.queue[st.qi])
			st.qi += 1
			if not tick() then return ("collect %d/%d parts, %d tris"):format(st.qi - 1, #st.queue, st.tris) end
		end
		st.phase = "pair"
		st.hits = {}
		st.work = {}
		for nk, nb in st.buckets do
			for dk, bl in nb do
				table.insert(st.work, { bl, bl, true })
				local nx = nb[dk + 1]
				if nx then table.insert(st.work, { bl, nx, false }) end
			end
		end
		st.wi = 1
	end
	if st.phase == "pair" then
		while st.wi <= #st.work do
			local w = st.work[st.wi]
			-- quick out: a bucket pair with only one look cannot fight
			local L1, L2 = w[1], w[2]
			local first, mixed = st.looks[L1[1][6]], false
			for _, t in L1 do if st.looks[t[6]] ~= first then mixed = true; break end end
			if not mixed and not w[3] then for _, t in L2 do if st.looks[t[6]] ~= first then mixed = true; break end end end
			if mixed then compareLists(st, L1, L2, w[3]) end
			st.wi += 1
			if not tick() then return ("pair %d/%d buckets"):format(st.wi - 1, #st.work) end
		end
		st.phase = "rank"
	end
	if st.phase == "rank" then
		local res = {}
		local lowWalk = math.huge
		for _, w in st.walk do lowWalk = math.min(lowWalk, w.Y) end
		for _, r in st.hits do
			if r.area >= st.minArea then
				local A, B = st.parts[r.a], st.parts[r.b]
				r.c /= r.area
				local probe = (r.pt or r.c) + r.n * 0.04
				local cov = insideVisibleBlock(st, probe, { [A] = true, [B] = true })
				local dist = math.huge
				for _, w in st.walk do dist = math.min(dist, (w - r.c).Magnitude) end
				if #st.walk == 0 then dist = 0 end
				local face = if r.n.Y > 0.7 then 1 elseif r.n.Y < -0.7 then 0.6 else 1
				-- unseen: a face pointing down from below where anyone stands, or under the given floor (minY)
				local unseen = (r.n.Y < -0.7 and r.c.Y < lowWalk - 3) or (st.minY ~= nil and r.c.Y < st.minY)
				r.covered = if cov then cov:GetFullName() elseif unseen then "unseen" else nil
				r.dist = dist
				r.score = if r.covered then 0 else r.area * face / (1 + dist / 40)
				r.A, r.B = A, B
				table.insert(res, r)
			end
		end
		table.sort(res, function(x, y) if x.score ~= y.score then return x.score > y.score end return x.area > y.area end)
		st.results = res
		st.buckets, st.work, st.hits, st.queue = nil, nil, nil, nil
		st.phase = "done"
	end
	return st.phase
end

local function short(p: Instance): string
	local s = p:GetFullName():gsub("^Workspace%.Map%.", "")
	return s
end

function ZF.results()
	return S().results or {}
end

function ZF.counts(): string
	local st = S()
	local vis, cov = 0, 0
	for _, r in st.results or {} do if r.covered then cov += 1 else vis += 1 end end
	local sk = {}
	for k, v in st.skipped or {} do table.insert(sk, k .. " " .. v) end
	return ("%s: %d parts, %d tris, %d visible hits, %d covered or unseen%s"):format(table.concat(st.roots or {}, "+"), #(st.parts or {}), st.tris or 0, vis, cov,
		if #sk > 0 then " (skipped: " .. table.concat(sk, ", ") .. ")" else "")
end

function ZF.report(n: number?): string
	local st = S()
	if st.phase ~= "done" then return "not done: " .. tostring(st.phase) end
	local lines = { ZF.counts() }
	for i, r in st.results do
		if i > (n or 40) then break end
		local A, B = r.A, r.B
		table.insert(lines, ("%2d %s%.2f sq studs, n(%.1f,%.1f,%.1f) gap %.3f, %dst from play, at (%.1f,%.1f,%.1f)\n     %s [%s %s]\n  vs %s [%s %s]"):format(
			i, if r.covered == "unseen" then "UNSEEN " elseif r.covered then "COVERED " else "", r.area, r.n.X, r.n.Y, r.n.Z, r.gap, math.floor(r.dist), r.c.X, r.c.Y, r.c.Z,
			short(A), A.Color:ToHex(), A.Material.Name, short(B), B.Color:ToHex(), B.Material.Name))
	end
	return table.concat(lines, "\n")
end

-- one call does it all (for small areas); bigger areas: start + step + report across calls
function ZF.run(roots: { Instance }, opts: any?): string
	ZF.start(roots, opts)
	while ZF.step(1e9) ~= "done" do end
	return ZF.report((opts and opts.top) or 40)
end

function ZF.clear()
	shared.ZF_STATE = nil
	shared.ZF_MESHES = {}
end

return ZF
