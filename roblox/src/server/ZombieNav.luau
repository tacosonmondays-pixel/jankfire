--!strict
-- ZOMBIES: the nav grid and the flow fields (web server/zombies.js buildNav / flow / downhill). 3-stud cells over a
-- map's ZM/NavBounds box; every floor in each column (up to 4 stacked: a basement, the ground, upstairs, a roof) found
-- by casting down; a cell is walkable if a zombie fits standing on it. links go to the 8 neighbours: at most a step up
-- or down, nothing solid in the way at knee or chest height, no cutting corners. a cell a door's shutter covers is
-- gated by that door (walkable once it's bought open). one flow field per player says how far each cell is from them
-- on foot, so every zombie just walks downhill toward whoever is closest. the map contract: roblox/docs/ZOMBIES.md
local ZombieNav = {}

local CELL = 3 -- studs (the web's 1 m)
local STEP = 1.6 -- the most a link climbs or drops (a stair step)
local HEAD = 6.5 -- head room a zombie needs over a floor
local INF = math.huge
ZombieNav.CELL = CELL

-- the 8 neighbours: di, dj, cost
local D8 = { { 1, 0, 1 }, { -1, 0, 1 }, { 0, 1, 1 }, { 0, -1, 1 }, { 1, 1, 1.414 }, { 1, -1, 1.414 }, { -1, 1, 1.414 }, { -1, -1, 1.414 } }

export type Nav = {
	x0: number, z0: number, W: number, D: number, L: number, WD: number, N: number,
	floor: { [number]: number }, -- cell (0-based l * WD + j * W + i) -> floor height (nil = no floor)
	door: { [number]: number }, -- cell -> the door index whose shutter covers it
	links: { [number]: { number } }, -- cell -> 8 neighbour cells (-1 = no link), in D8's order
	params: RaycastParams,
	cells: number, -- walkable cells, for the report
	built: number, -- seconds it took
}

local function centre(nav: Nav, c: number): (number, number)
	local col = c % nav.WD
	return nav.x0 + (col % nav.W + 0.5) * CELL, nav.z0 + (col // nav.W + 0.5) * CELL
end
ZombieNav.centre = centre

-- build the grid (yields every so often: a school is ~10k cells). skip = what the casts ignore (characters, the
-- zombies, the door shutters: their cells are gated instead)
function ZombieNav.build(bounds: BasePart, shutters: { BasePart }, skip: { Instance }): Nav
	local t0 = os.clock()
	local lo = bounds.Position - bounds.Size / 2
	local hi = bounds.Position + bounds.Size / 2
	local W, D = math.ceil(bounds.Size.X / CELL), math.ceil(bounds.Size.Z / CELL)
	local WD = W * D
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local ex = table.clone(skip)
	for _, s in shutters do table.insert(ex, s) end
	params.FilterDescendantsInstances = ex
	params.RespectCanCollide = true
	local over = OverlapParams.new()
	over.FilterType = Enum.RaycastFilterType.Exclude
	over.FilterDescendantsInstances = ex
	over.RespectCanCollide = true
	over.MaxParts = 1
	local probe = Instance.new("Part")
	probe.Name = "ZMNavProbe"; probe.Anchored = true; probe.CanCollide = false; probe.CanQuery = false; probe.CanTouch = false
	probe.Transparency = 1; probe.Size = Vector3.new(1.8, HEAD - 1.0, 1.8)
	probe.Parent = workspace
	local nav: Nav = { x0 = lo.X, z0 = lo.Z, W = W, D = D, L = 1, WD = WD, N = WD, floor = {}, door = {}, links = {}, params = params, cells = 0, built = 0 }
	-- every floor in each column, lowest first
	local cols: { [number]: { number } } = {}
	local L = 1
	local n = 0
	for j = 0, D - 1 do
		for i = 0, W - 1 do
			local x, z = lo.X + (i + 0.5) * CELL, lo.Z + (j + 0.5) * CELL
			local ys = {}
			local from = hi.Y
			for _ = 1, 8 do
				if from <= lo.Y then break end
				local h = workspace:Raycast(Vector3.new(x, from, z), Vector3.new(0, -(from - lo.Y + 2), 0), params)
				if not h then break end
				local y = h.Position.Y
				if h.Normal.Y > 0.7 then
					-- a zombie fits standing on it: nothing solid from its knees to its head (the knees: steps don't count)
					probe.CFrame = CFrame.new(x, y + 1.0 + (HEAD - 1.0) / 2, z)
					if #workspace:GetPartsInPart(probe, over) == 0 then table.insert(ys, y) end
				end
				from = y - 0.05 -- (a ray from inside a part goes straight through it: on down to the next floor)
			end
			table.sort(ys)
			if #ys > 4 then ys = { ys[#ys - 3], ys[#ys - 2], ys[#ys - 1], ys[#ys] } end
			cols[j * W + i] = ys
			if #ys > L then L = #ys end
			n += 1
			if n % 150 == 0 then task.wait() end
		end
	end
	probe:Destroy()
	nav.L, nav.N = L, WD * L
	for col, ys in cols do
		for l, y in ys do nav.floor[(l - 1) * WD + col] = y end
	end
	-- the shutters' cells (the whole cell: shutters are thinner than one)
	for c, y in nav.floor do
		local x, z = centre(nav, c)
		for di, s in shutters do
			local l = s.CFrame:PointToObjectSpace(Vector3.new(x, y + 2, z))
			local hs = s.Size / 2
			if math.abs(l.X) <= hs.X + CELL / 2 and math.abs(l.Z) <= hs.Z + CELL / 2 and l.Y >= -hs.Y - 2 and l.Y <= hs.Y then nav.door[c] = di; break end
		end
	end
	-- links: the neighbour cell (whichever floor) within a step, nothing solid between at knee and chest height
	local function stepTo(c: number, di: number, dj: number): number
		local col = c % WD
		local i, j = col % W + di, col // W + dj
		if i < 0 or j < 0 or i >= W or j >= D then return -1 end
		local y0 = nav.floor[c]
		local best, bd = -1, STEP
		for l = 0, L - 1 do
			local nc = l * WD + j * W + i
			local y = nav.floor[nc]
			if y and math.abs(y - y0) <= bd then bd = math.abs(y - y0); best = nc end
		end
		return best
	end
	local function clear(a: number, b: number): boolean
		local ax, az = centre(nav, a)
		local bx, bz = centre(nav, b)
		local ay, by = nav.floor[a], nav.floor[b]
		for _, up in { 1.4, 3.6 } do
			local o = Vector3.new(ax, ay + up, az)
			if workspace:Raycast(o, Vector3.new(bx, by + up, bz) - o, params) then return false end
		end
		return true
	end
	n = 0
	for c in nav.floor do
		local row = table.create(8, -1)
		for k, d in D8 do
			local nb = stepTo(c, d[1], d[2])
			if nb >= 0 and clear(c, nb) then row[k] = nb end
		end
		-- no cutting corners: a diagonal needs both of its sides
		for k = 5, 8 do
			if row[k] >= 0 then
				local d = D8[k]
				local sx, sz = -1, -1
				for kk = 1, 4 do
					if D8[kk][1] == d[1] and D8[kk][2] == 0 then sx = row[kk] end
					if D8[kk][1] == 0 and D8[kk][2] == d[2] then sz = row[kk] end
				end
				if sx < 0 or sz < 0 then row[k] = -1 end
			end
		end
		nav.links[c] = row
		nav.cells += 1
		n += 1
		if n % 300 == 0 then task.wait() end
	end
	nav.built = os.clock() - t0
	return nav
end

local function walkable(nav: Nav, open: { boolean }, c: number): boolean
	if not nav.floor[c] then return false end
	local d = nav.door[c]
	return d == nil or open[d] == true
end
ZombieNav.walkable = walkable

-- the cell under a position (feet): the floor it stands on (the highest not above its knees), else the nearest
function ZombieNav.cellOf(nav: Nav, p: Vector3): number
	local i, j = math.floor((p.X - nav.x0) / CELL), math.floor((p.Z - nav.z0) / CELL)
	if i < 0 or j < 0 or i >= nav.W or j >= nav.D then return -1 end
	local col = j * nav.W + i
	local best, bd, any = -1, INF, -1
	for l = 0, nav.L - 1 do
		local c = l * nav.WD + col
		local y = nav.floor[c]
		if not y then continue end
		local d = p.Y + 2.1 - y -- (how far under the knees it is)
		if d >= 0 and d < bd then bd = d; best = c end
		any = c
	end
	return if best >= 0 then best else any
end

-- a flow field: how far every cell is from `at` on foot (Dijkstra; seeded on the cells round them they can see: they
-- might be up on a table). out is reused (a table of N)
function ZombieNav.flow(nav: Nav, open: { boolean }, at: Vector3, out: { [number]: number })
	table.clear(out)
	local hc, hd = {}, {}
	local function push(c: number, d: number)
		local i = #hc + 1
		hc[i], hd[i] = c, d
		while i > 1 do
			local p = i // 2
			if hd[p] <= d then break end
			hc[i], hd[i] = hc[p], hd[p]
			i = p
		end
		hc[i], hd[i] = c, d
	end
	local function pop(): (number, number)
		local c, d = hc[1], hd[1]
		local lc, ld = hc[#hc], hd[#hd]
		hc[#hc], hd[#hd] = nil, nil
		local n = #hc
		if n > 0 then
			local i = 1
			while true do
				local k = 2 * i
				if k > n then break end
				if k + 1 <= n and hd[k + 1] < hd[k] then k += 1 end
				if hd[k] >= ld then break end
				hc[i], hd[i] = hc[k], hd[k]
				i = k
			end
			hc[i], hd[i] = lc, ld
		end
		return c, d
	end
	local ci, cj = math.floor((at.X - nav.x0) / CELL), math.floor((at.Z - nav.z0) / CELL)
	for dj = -2, 2 do
		for di = -2, 2 do
			local i, j = ci + di, cj + dj
			if i < 0 or j < 0 or i >= nav.W or j >= nav.D then continue end
			for l = 0, nav.L - 1 do
				local c = l * nav.WD + j * nav.W + i
				if not walkable(nav, open, c) then continue end
				local y = nav.floor[c]
				if nav.L > 1 and (y > at.Y + 2.4 or y < at.Y - 6.6) then continue end -- (their floor, not the one upstairs)
				local x, z = centre(nav, c)
				local dx, dz = x - at.X, z - at.Z
				local d = math.sqrt(dx * dx + dz * dz)
				if d > 6.6 then continue end
				if d > 0.9 and workspace:Raycast(Vector3.new(at.X, at.Y + 1.5, at.Z), Vector3.new(dx, 0, dz), nav.params) then continue end
				if d < (out[c] or INF) then out[c] = d; push(c, d) end
			end
		end
	end
	while #hc > 0 do
		local c, d = pop()
		if d > (out[c] or INF) + 1e-3 then continue end
		local row = nav.links[c]
		if not row then continue end
		for k, nb in row do
			if nb < 0 or not walkable(nav, open, nb) then continue end
			local nd = d + D8[k][3] * CELL
			if nd < (out[nb] or INF) then out[nb] = nd; push(nb, nd) end
		end
	end
end

-- walk downhill on a field: up to 4 cells ahead, as far as there's a straight line to it. nil at the bottom
function ZombieNav.downhill(nav: Nav, open: { boolean }, f: { [number]: number }, pos: Vector3): Vector3?
	local c = ZombieNav.cellOf(nav, pos)
	if c < 0 then return nil end
	local out: Vector3? = nil
	for s = 1, 4 do
		local nb, nd = -1, f[c] or INF
		local row = nav.links[c]
		if row and walkable(nav, open, c) then
			for _, n in row do
				if n >= 0 and walkable(nav, open, n) and (f[n] or INF) < nd then nd = f[n]; nb = n end
			end
		else
			-- knocked off the grid: any neighbour column's cell back on it
			local col = c % nav.WD
			local i0, j0 = col % nav.W, col // nav.W
			for _, d in D8 do
				local i, j = i0 + d[1], j0 + d[2]
				if i < 0 or j < 0 or i >= nav.W or j >= nav.D then continue end
				for l = 0, nav.L - 1 do
					local n = l * nav.WD + j * nav.W + i
					if walkable(nav, open, n) and (f[n] or INF) < nd then nd = f[n]; nb = n end
				end
			end
		end
		if nb < 0 then break end
		c = nb
		local x, z = centre(nav, c)
		local p = Vector3.new(x, nav.floor[c], z)
		if s > 1 then
			local dx, dz = x - pos.X, z - pos.Z
			if workspace:Raycast(Vector3.new(pos.X, pos.Y + 1.4, pos.Z), Vector3.new(dx, 0, dz), nav.params) then break end
		end
		out = p
	end
	return out
end

-- the distance on a field from a position (the cell under it, or the best neighbour + a step if it's off the grid)
function ZombieNav.dist(nav: Nav, open: { boolean }, f: { [number]: number }, pos: Vector3): number
	local c = ZombieNav.cellOf(nav, pos)
	if c < 0 then return INF end
	local d = f[c] or INF
	if d < INF then return d end
	local row = nav.links[c]
	if row then
		for k, n in row do if n >= 0 and walkable(nav, open, n) then d = math.min(d, (f[n] or INF) + D8[k][3] * CELL) end end
	end
	return d
end

return ZombieNav
