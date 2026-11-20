--!strict
-- THE EXPLODED VIEW'S DATA (19 Nov 2026, the owner: "make sure models can be blown up, like for guns ... not
-- destructible, like blueprint-wise, where parts get 'blown up' to see individual pieces"). A built weapon (WeaponModels.
-- build: a Root part, the kit pieces named "<node>_wz<zone>__<slot>") is sorted into its real PARTS: the receiver (the
-- core, which stays put), the barrel, the muzzle, the magazine, the stock, the grip, the bolt / slide / charging handle,
-- the sights or the scope, the cylinder, the pump, a skin's accents (each wing, halo, crown its own part) and the hat.
-- Each part gets a direction (the gun's own frame: x right, y up, the muzzle to -z), a distance and a step in the
-- order they move. Nothing is stored per gun: it is worked out from the pieces' names and where they sit, so a new gun
-- or skin gets it for free; OVERRIDE corrects one gun where the rule picks wrong. client/ExplodedView animates it.
--   local plan = GunExplode.plan(model)        -- nil for a model it can't take apart (fewer than two parts)
--   GunExplode.pose(plan, f)                   -- f(group) -> 0..1: each part that far out (0 = home)
--   GunExplode.home(plan)                      -- every piece back exactly where it was
-- the rules, in order, for a piece:
--   1. a hat (GunHats marks its parts NoWrap): the whole hat is one part, up
--   2. its node (the WrapNode attribute a build keeps, else its name) in NODE: that part
--   3. a big piece of a node not listed (over 4% of the gun's box): a part of its own, pushed away from the core
--   4. anything else (trims, rivets, marks, pins, the trigger, a lens): rides with the part whose box holds it (the
--      smallest such), else the core
local GunExplode = {}

export type Group = { name: string, parts: { BasePart }, rel: { CFrame }, dir: Vector3, dist: number, step: number,
	centre: Vector3, lo: Vector3, hi: Vector3, core: boolean, accent: boolean }
export type Plan = { model: Model, root: BasePart?, groups: { Group }, size: number, steps: number, joints: { Instance } }

-- node -> part (anything not here is sorted by rules 3 and 4)
local NODE: { [string]: string } = {
	body = "core", receiver = "core", frame = "core", lower = "core", upper = "core", housing = "core", action = "core",
	deck = "core", -- (a receiver's top deck)
	barrel = "barrel", barrels = "barrel", lmg_heat = "barrel", shroud = "barrel", tube = "barrel",
	muzzle = "muzzle", muz = "muzzle", nozzle = "muzzle", brake = "muzzle", throat = "muzzle", nose = "muzzle",
	mag = "mag", magtrack = "mag", clip = "mag", drum = "mag", shells = "mag", load = "mag",
	stock = "stock", butt = "stock",
	grip = "grip", grips = "grip", grip2 = "grip", -- (not "handle": on a gun that is a carry handle; it sorts itself)
	sight = "sight", sights = "sight", fsight = "fsight", bead = "fsight", optic = "scope", scope = "scope", rail = "rail",
	bolt = "bolt", charge = "bolt", cocker = "bolt", slide = "slide", lever = "lever",
	hammer = "hammer", lhammer = "hammer", hammerl = "hammer", hammerr = "hammer",
	cylinder = "cylinder", pump = "pump", forend = "pump", forend_iron = "pump", fore = "fore",
	guard = "guard", tguard = "tguard", shield = "shield", cover = "cover", box = "box", gauge = "gauge",
	hinge = "hinge", shell1 = "shells", shell2 = "shells", tank = "tank", water = "tank",
	-- (the Marble Shotgun's jar and its marbles, a hopper's lid: the gimmick's container lifts off whole)
	marbles_jar = "jar", funnel = "jar", lid = "jar",
	kat_blade = "blade", blade = "blade", kat_tsuka = "handle", kat_guard = "core",
	-- a skin's accents: each its own part
	rwing = "wing", lwing = "wing", wing = "wing", wings = "wing", halo = "halo", crown = "crown", bow = "bow",
	charm = "charm", ribbon = "bow", tassel = "charm",
}
-- small fittings: never a part of their own, they ride with what holds them (rule 4) however long they run
local TRIM: { [string]: boolean } = { trim = true, rivet = true, mark = true, panel = true, band = true, tape = true, cut = true,
	flute = true, inlay = true, screw = true, pin = true, nut = true, dot = true, lens = true, glint = true, trigger = true,
	stitch = true, seam = true, label = true, badge = true, sign = true }
GunExplode.TRIM = TRIM
-- the belt links of the LMG are its magazine's
local function nodePart(node: string): string?
	if string.match(node, "^belt_%d+$") then return "mag" end
	if string.match(node, "^marble_%d+$") then return "jar" end
	return NODE[node]
end
-- each part's way out (the gun's frame) and its step (1 first)
local DIR: { [string]: Vector3 } = {
	barrel = Vector3.new(0, 0, -1), muzzle = Vector3.new(0, 0, -1), blade = Vector3.new(0, 0, -1),
	mag = Vector3.new(0, -1, 0), pump = Vector3.new(0, -1, 0), fore = Vector3.new(0, -1, 0),
	guard = Vector3.new(0, -1, 0), tguard = Vector3.new(0, -1, 0), shield = Vector3.new(0, 1, 0),
	cover = Vector3.new(0, 1, 0), box = Vector3.new(0, -1, 0), gauge = Vector3.new(-1, 0, 0), tank = Vector3.new(0, 1, 0),
	jar = Vector3.new(0, 1, 0), hinge = Vector3.new(0, -0.25, -1).Unit, shells = Vector3.new(0, 1, 0.3).Unit,
	stock = Vector3.new(0, 0, 1), handle = Vector3.new(0, 0, 1),
	grip = Vector3.new(0, -1, 0.35).Unit,
	sight = Vector3.new(0, 1, 0), fsight = Vector3.new(0, 1, 0), scope = Vector3.new(0, 1, 0), rail = Vector3.new(0, 1, 0),
	slide = Vector3.new(0, 1, 0), halo = Vector3.new(0, 1, 0), crown = Vector3.new(0, 1, 0), hat = Vector3.new(0, 1, 0),
	-- (a preview shows the gun's left side three-quarters on: a part going straight out to the right hides behind it,
	-- so the bolt comes up and back, the cylinder swings out low to the left)
	bolt = Vector3.new(0, 0.8, 0.6).Unit, lever = Vector3.new(0, -1, 0.3).Unit, hammer = Vector3.new(0, 0.6, 0.8).Unit,
	cylinder = Vector3.new(-0.55, -0.85, 0).Unit,
}
local STEP: { [string]: number } = {
	hat = 1, wing = 1, halo = 1, crown = 1, bow = 1, charm = 1,
	scope = 2, sight = 2, fsight = 2, rail = 2, shield = 2, cover = 2, gauge = 2, tank = 2, jar = 2,
	mag = 3, muzzle = 3, box = 3, shells = 3,
	stock = 4, grip = 4, fore = 4, lever = 4, guard = 4, tguard = 4,
	barrel = 5, pump = 5, blade = 5, handle = 5, hinge = 5,
	bolt = 6, slide = 6, hammer = 6, cylinder = 6,
}
-- OVERRIDE[weapon id or skin id] = { [part] = { dir = Vector3?, dist = number? (x the usual), step = number? },
-- node = { [node] = part } }: one gun's corrections (empty until a gun needs one)
GunExplode.OVERRIDE = {} :: { [string]: any }
GunExplode.NODE, GunExplode.DIR, GunExplode.STEP = NODE, DIR, STEP

local function nodeOf(p: BasePart): string
	local nd = p:GetAttribute("WrapNode")
	if type(nd) == "string" then return nd end
	local n = string.lower(p.Name)
	return string.match(n, "^(.-)_wz") or n
end

-- a part's box in the root's frame
local function boxIn(ref: CFrame, p: BasePart): (Vector3, Vector3)
	local cf = ref:ToObjectSpace(p.CFrame)
	local h = p.Size / 2
	local e = Vector3.new(
		math.abs(cf.XVector.X) * h.X + math.abs(cf.YVector.X) * h.Y + math.abs(cf.ZVector.X) * h.Z,
		math.abs(cf.XVector.Y) * h.X + math.abs(cf.YVector.Y) * h.Y + math.abs(cf.ZVector.Y) * h.Z,
		math.abs(cf.XVector.Z) * h.X + math.abs(cf.YVector.Z) * h.Y + math.abs(cf.ZVector.Z) * h.Z)
	return cf.Position - e, cf.Position + e
end

local function vol(lo: Vector3, hi: Vector3): number
	local d = hi - lo
	return math.max(d.X, 1e-4) * math.max(d.Y, 1e-4) * math.max(d.Z, 1e-4)
end

local function frameOf(m: Model): (CFrame, BasePart?)
	local root = m.PrimaryPart
	if root and root.Name == "Root" then return root.CFrame, root end
	local r = m:FindFirstChild("Root")
	if r and r:IsA("BasePart") then return r.CFrame, r end
	return m:GetPivot(), nil
end

function GunExplode.plan(m: Model): Plan?
	local ref, root = frameOf(m)
	local id = m:GetAttribute("Skin") or m.Name
	local ov = (type(id) == "string" and GunExplode.OVERRIDE[id]) or GunExplode.OVERRIDE[m.Name] or {}
	local pieces: { { p: BasePart, node: string, lo: Vector3, hi: Vector3, hat: Instance? } } = {}
	local glo, ghi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, d in m:GetDescendants() do
		if not d:IsA("BasePart") or d == root or d.Name == "Root" or d.Name == "SuckField" then continue end
		if d:GetAttribute("ExplodeLine") then continue end
		local tr = d:GetAttribute("WrapTr")
		if (if type(tr) == "number" then tr else d.Transparency) >= 0.99 then continue end
		local lo, hi = boxIn(ref, d)
		local hat: Instance? = nil
		if d:GetAttribute("NoWrap") then
			-- (a hat is a model of its own on the weapon; a NoWrap piece straight in it, a skin's shade shell, is not)
			local a = d.Parent
			while a and a ~= m and not (a:IsA("Model") and a.Parent == m) do a = a.Parent end
			if a and a ~= m then hat = a end
		end
		table.insert(pieces, { p = d, node = nodeOf(d), lo = lo, hi = hi, hat = hat })
		if not hat then glo = glo:Min(lo); ghi = ghi:Max(hi) end
	end
	if #pieces < 2 or glo.X > ghi.X then return nil end
	local gsize = ghi - glo
	local L = math.max(gsize.X, gsize.Y, gsize.Z)
	local gvol = vol(glo, ghi)
	-- the named parts (rules 1-3)
	local groups: { [string]: Group } = {}
	local order: { string } = {}
	local function groupOf(name: string): Group
		local g = groups[name]
		if not g then
			g = { name = name, parts = {}, rel = {}, dir = Vector3.zero, dist = 0, step = 4, centre = Vector3.zero,
				lo = Vector3.one * math.huge, hi = -Vector3.one * math.huge, core = name == "core",
				accent = name == "hat" or string.find(name, ":", 1, true) ~= nil and string.sub(name, 1, 2) ~= "n:" }
			groups[name] = g; table.insert(order, name)
		end
		return g
	end
	local function add(g: Group, pc: any)
		table.insert(g.parts, pc.p)
		g.lo = g.lo:Min(pc.lo); g.hi = g.hi:Max(pc.hi)
	end
	-- a node's pieces together: its box (for rule 3)
	local byNode: { [string]: { any } } = {}
	for _, pc in pieces do
		if pc.hat then continue end
		local t = byNode[pc.node]
		if not t then t = {}; byNode[pc.node] = t end
		table.insert(t, pc)
	end
	local loose: { any } = {}
	for _, pc in pieces do
		if pc.hat then
			add(groupOf("hat"), pc)
			continue
		end
		local name = (ov.node and ov.node[pc.node]) or nodePart(pc.node)
		if not name and TRIM[pc.node] then
			table.insert(loose, pc)
			continue
		end
		if name then
			if name == "wing" or name == "halo" or name == "crown" or name == "bow" or name == "charm" then
				name = name .. ":" .. pc.node -- (each accent node its own part)
			end
			add(groupOf(name), pc)
		else
			local nlo, nhi = Vector3.one * math.huge, -Vector3.one * math.huge
			for _, q in byNode[pc.node] do nlo = nlo:Min(q.lo); nhi = nhi:Max(q.hi) end
			if vol(nlo, nhi) > gvol * 0.04 then add(groupOf("n:" .. pc.node), pc) else table.insert(loose, pc) end
		end
	end
	if not groups.core then
		-- (no receiver by name: the biggest part is the core)
		local best, bv = nil, -1
		for _, nm in order do
			local g = groups[nm]
			if nm ~= "hat" and vol(g.lo, g.hi) > bv then best, bv = g, vol(g.lo, g.hi) end
		end
		if best then best.core = true end
	end
	local core: Group? = groups.core
	if not core then
		for _, nm in order do if groups[nm].core then core = groups[nm] end end
	end
	-- rule 4: a small piece rides with the smallest part whose box holds its middle; only if none does, the smallest
	-- whose box grown a little does (a rivet standing just proud of its part). the boxes are the named parts' own,
	-- taken before any trim joins them, so one trim never drags the next one along
	local boxes: { [string]: { Vector3 } } = {}
	for _, nm in order do boxes[nm] = { groups[nm].lo, groups[nm].hi } end
	local function holder(c: Vector3, grow: number): Group?
		local best: Group? = nil
		local bv = math.huge
		for _, nm in order do
			local g = groups[nm]
			-- (never a hat, a skin's accent or an unnamed big part: a trim isn't theirs)
			if g.accent or string.sub(nm, 1, 2) == "n:" or not boxes[nm] then continue end
			local lo, hi = boxes[nm][1] - Vector3.one * grow, boxes[nm][2] + Vector3.one * grow
			if c.X >= lo.X and c.X <= hi.X and c.Y >= lo.Y and c.Y <= hi.Y and c.Z >= lo.Z and c.Z <= hi.Z then
				local v = vol(boxes[nm][1], boxes[nm][2])
				if v < bv then best, bv = g, v end
			end
		end
		return best
	end
	for _, pc in loose do
		local c = (pc.lo + pc.hi) / 2
		local g = holder(c, 0) or holder(c, L * 0.02) or core or groupOf("core")
		add(g, pc)
	end
	local coreC = if core then (core.lo + core.hi) / 2 else (glo + ghi) / 2
	-- the way out, how far, the step
	local list: { Group } = {}
	local maxStep = 1
	for _, nm in order do
		local g = groups[nm]
		g.centre = (g.lo + g.hi) / 2
		local base = string.match(nm, "^([%w_]+):") or nm
		local o = (ov :: any)[base] or (ov :: any)[nm] or {}
		local v = g.centre - coreC
		local dir: Vector3 = o.dir or DIR[base] or Vector3.zero
		if base == "wing" or base == "bow" or base == "charm" then
			-- (a wing goes out to its own side and up; one across the middle, straight up)
			local side = if math.abs(g.centre.X - coreC.X) > L * 0.03 then math.sign(g.centre.X - coreC.X) else 0
			dir = Vector3.new(side * 0.55, 1, 0).Unit
		end
		if dir.Magnitude < 0.5 then
			-- (by where it sits: straight along the gun's axis it leans to most, else straight away from the core)
			if v.Magnitude < L * 0.02 then dir = Vector3.new(0, 1, 0)
			else
				local a = Vector3.new(math.abs(v.X), math.abs(v.Y), math.abs(v.Z))
				local mx = math.max(a.X, a.Y, a.Z)
				if mx > v.Magnitude * 0.72 then
					dir = if mx == a.Z then Vector3.new(0, 0, math.sign(v.Z)) elseif mx == a.Y then Vector3.new(0, math.sign(v.Y), 0) else Vector3.new(math.sign(v.X), 0, 0)
				else dir = v.Unit end
			end
		end
		g.dir = dir.Unit
		local proj = math.max(0, v:Dot(g.dir))
		-- (and always clear of the core: the part's near end goes past the core's far end that way, with a gap)
		-- (along the way's main axis only: a part going up and back clears the receiver's top, not its length)
		local clear = 0
		if core and not g.core then
			local dx, dy, dz = math.abs(g.dir.X), math.abs(g.dir.Y), math.abs(g.dir.Z)
			local ax = if dx >= dy and dx >= dz then "X" elseif dy >= dz then "Y" else "Z"
			local s = (g.dir :: any)[ax]
			local gap = if s > 0 then (core.hi :: any)[ax] - (g.lo :: any)[ax] else (g.hi :: any)[ax] - (core.lo :: any)[ax]
			clear = (gap + L * 0.06) / math.max(math.abs(s), 0.3)
		end
		local d = math.max(L * 0.16 + proj * 0.4, clear)
		if base == "hat" then d = L * 0.32 elseif base == "wing" or base == "halo" or base == "crown" then d = L * 0.2 + proj * 0.4 end
		g.dist = if g.core then 0 else math.min(d, L * 0.5) * (o.dist or 1) -- (half the gun at most: it stays in the panel)
		g.step = if g.core then 0 else (o.step or STEP[base] or 4)
		maxStep = math.max(maxStep, g.step)
		for _, p in g.parts do table.insert(g.rel, ref:ToObjectSpace(p.CFrame)) end
		table.insert(list, g)
	end
	if #list < 2 then return nil end
	table.sort(list, function(a, b) if a.step ~= b.step then return a.step < b.step end return a.name < b.name end)
	return { model = m, root = root, groups = list, size = L, steps = maxStep, joints = {} }
end

-- each part f(group) of the way out (0..1, eased by the caller); the pieces follow the root wherever it is now
function GunExplode.pose(plan: Plan, f: (Group) -> number)
	local ref = if plan.root then plan.root.CFrame else plan.model:GetPivot()
	if #plan.joints == 0 then
		-- (the pieces are welded to the root: the welds let go while it is apart, GunExplode.home takes them back)
		for _, d in plan.model:GetDescendants() do
			if (d:IsA("WeldConstraint") or d:IsA("JointInstance")) and (d :: any).Enabled then
				(d :: any).Enabled = false
				table.insert(plan.joints, d)
			end
		end
	end
	for _, g in plan.groups do
		if g.core then continue end
		local off = CFrame.new(g.dir * (g.dist * f(g)))
		for i, p in g.parts do
			if p.Parent then p.CFrame = ref * off * g.rel[i] end
		end
	end
end

function GunExplode.home(plan: Plan)
	GunExplode.pose(plan, function() return 0 end)
	for _, j in plan.joints do if j.Parent then (j :: any).Enabled = true end end
	table.clear(plan.joints)
end

-- where a part's middle is at f of the way out (root space): the leader lines
function GunExplode.at(g: Group, f: number): Vector3
	return g.centre + g.dir * (g.dist * f)
end

return GunExplode
