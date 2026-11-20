--!strict
-- where a loot container stands: the floor under a point, for LootOpening (your own opening, a batch's row) and for
-- Loot.luau (the spot others see). the owner, 16 Nov: "make sure the stuff doesnt clip through the ground".
-- the traps, all met in the hub:
--   * your feet: HipHeight is not where the feet are with this game's movement (1.2 studs off in the hub), so the feet
--     are measured from the foot parts themselves;
--   * floors rays can't see: many floor pieces are CanQuery off. a ray that ends far from the feet (a hole, a ceiling)
--     is not trusted; then the floor is where the feet are;
--   * thin decorative tops over the floor a ray hits, in ANOTHER folder: the hub's dais (Shell.Dais, 241.20) wears
--     Scenery.DaisTop / SpawnRing / DaisInner, round discs up to 0.12 studs higher. so after the ray, the container
--     stands on the highest visible piece that covers the point (discs tested as discs) within half a stud over the hit,
--     looked for among everything under the hit part's grandparent (cached a few seconds).
local F = {}

local function lowest(p: BasePart): number
	local cf, sz = p.CFrame, p.Size
	return cf.Position.Y - (math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z) / 2
end
local function highest(p: BasePart): number
	local cf, sz = p.CFrame, p.Size
	return cf.Position.Y + (math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z) / 2
end

-- the lowest point of a character's feet (nil: no character)
function F.feet(ch: Model?): number?
	if not ch then return nil end
	local low = math.huge
	for _, n in { "LeftFoot", "RightFoot", "Left Leg", "Right Leg" } do
		local p = ch:FindFirstChild(n)
		if p and p:IsA("BasePart") then low = math.min(low, lowest(p)) end
	end
	if low < math.huge then return low end
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch:FindFirstChildOfClass("Humanoid")
	return if root then root.Position.Y - root.Size.Y / 2 - (if hum then hum.HipHeight else 2) else nil
end

-- does this part cover the point (x, z) from above? a cylinder is tested as its round face (a flat disc stands with its
-- axis, local X, upright), anything else as its box
local function covers(d: BasePart, x: number, z: number): boolean
	local p = d.CFrame:PointToObjectSpace(Vector3.new(x, d.Position.Y, z))
	if d:IsA("Part") and d.Shape == Enum.PartType.Cylinder then
		local up = math.abs(d.CFrame.RightVector.Y) > 0.9 -- (the disc lies flat)
		if up then
			local r = math.min(d.Size.Y, d.Size.Z) / 2
			return p.Y * p.Y + p.Z * p.Z <= r * r
		end
	end
	local sz = d.Size
	return math.abs(p.X) <= sz.X / 2 and math.abs(p.Z) <= sz.Z / 2
end

-- the pieces rays can't see under a scope (cached for a few seconds: a batch asks ten times in a row)
local cache: { [Instance]: { t: number, parts: { BasePart } } } = {}
local function hidden(scope: Instance): { BasePart }
	local c = cache[scope]
	if c and os.clock() - c.t < 4 then return c.parts end
	local list = {}
	for _, d in scope:GetDescendants() do
		if d:IsA("BasePart") and not d.CanQuery and d.Transparency < 0.99 then table.insert(list, d) end
	end
	cache[scope] = { t = os.clock(), parts = list }
	return list
end

-- the floor's height under `at` (feetY: the opener's feet; ignore: what the ray must not hit, e.g. the character), and
-- whether a ray found a floor there at all (false: a drop, or something over the spot; the height is then your feet's)
function F.at(at: Vector3, feetY: number, ignore: { Instance }): (number, boolean)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local down = workspace:Raycast(Vector3.new(at.X, feetY + 3, at.Z), Vector3.new(0, -8, 0), params)
	if not down or down.Position.Y < feetY - 1.5 or down.Position.Y > feetY + 2.5 then return feetY, false end
	local y = down.Position.Y
	local scope: Instance? = down.Instance.Parent
	if scope and scope.Parent and scope.Parent ~= workspace and scope.Parent ~= game then scope = scope.Parent end
	if scope then
		for _, d in hidden(scope) do
			local top = highest(d)
			if top > y and top <= down.Position.Y + 0.5 and covers(d, at.X, at.Z) then y = top end
		end
	end
	return y, true
end

-- ---------------------------------------------------------------- how big they are, where they stand
-- the owner, 16 Nov: "can the bags be larger? I think they're small or get small when you open multiple, instead could
-- they open around you to compensate that". so every container is shown bigger than its model (crate and bag up to
-- about your waist, the can a head taller than them), and several at once are NOT shrunk into a row: they stand round
-- you at full size, a half ring in front for five, a full ring for ten, as wide as they need.
F.SIZE = { crate = 1.25, bag = 1.4, spray = 1.1 }
-- each one's room at size 1 when it's OPEN (tools/roblox/loot_models.py): its width (x), how far it reaches in front of
-- its pivot and behind it (the crate's lid swings up and back; the bag's flaps fold out both sides; the can's cap lands
-- beside it), its open height, its shut height
local ROOM = {
	crate = { w = 4.04, front = 1.44, back = 2.3, h = 4.4, shut = 2.39 },
	bag = { w = 3.98, front = 1.8, back = 1.8, h = 2.1, shut = 2.0 },
	spray = { w = 2.3, front = 0.64, back = 1.25, h = 3.6, shut = 3.56 },
}
-- (every Spray Can, the spray sets' too: "spraycosmic" and the rest, LootTable.SPRAY_SETS, has the first can's size and room)
for _, t in { F.SIZE, ROOM } :: { any } do
	setmetatable(t, { __index = function(self: any, k: any): any
		return if type(k) == "string" and string.sub(k, 1, 5) == "spray" then rawget(self, "spray") else nil
	end })
end
local GAP = 0.6 -- (between two containers side by side)

-- a container's room at its shown size times k: width, front, back, open height, shut height
function F.room(kind: string, k: number?): (number, number, number, number, number)
	local r = ROOM[kind] or ROOM.crate
	local s = (F.SIZE[kind] or 1) * (k or 1)
	return r.w * s, r.front * s, r.back * s, r.h * s, r.shut * s
end

-- a solid thing: one you'd walk into, or one you can see (not the invisible zones and prompts all over the hub)
local function solid(p: BasePart): boolean
	return p.CanCollide or p.Transparency < 0.5
end
-- a ray that only stops at solid things (it looks through the rest)
local function ray(from: Vector3, to: Vector3, ignore: { Instance }): RaycastResult?
	local list = table.clone(ignore)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	for _ = 1, 6 do
		params.FilterDescendantsInstances = list
		local hit = workspace:Raycast(from, to - from, params)
		if not hit or solid(hit.Instance) then return hit end
		table.insert(list, hit.Instance)
	end
	return nil
end
F.ray = ray

-- one container on the floor at angle `a` (radians, + turns left from `flat`) and `r` studs out from `c` (your feet's
-- middle), facing you, turned `twist` more; nil when that spot won't do: nothing solid may stand in its open room, nothing
-- solid between you and it, and a floor under it (not a drop, not a table top)
local function spotAt(c: Vector3, feetY: number, flat: Vector3, a: number, r: number, kind: string, k: number, twist: number,
	ignore: { Instance }, op: OverlapParams, needFloor: boolean): CFrame?
	local w, front, back, h = F.room(kind, k)
	local dir = CFrame.fromAxisAngle(Vector3.yAxis, a):VectorToWorldSpace(flat)
	local p = c + dir * r
	local y, found = F.at(p, feetY, ignore)
	if needFloor and not found then return nil end
	local g = Vector3.new(p.X, y, p.Z)
	local cf = CFrame.lookAt(g, g - dir) * CFrame.Angles(0, twist, 0)
	-- (its room, from a little over its floor, so the floor itself and the pads on it don't count)
	local room = cf * CFrame.new(0, 0.4 + h / 2, (back - front) / 2)
	for _, q in workspace:GetPartBoundsInBox(room, Vector3.new(w + 0.2, h, front + back + 0.2), op) do
		if solid(q) then return nil end
	end
	-- (and you can see it from where you stand: no wall between, at knee and at chest height)
	for _, up in { 1.0, 2.6 } do
		local from = Vector3.new(c.X, feetY + up, c.Z)
		for _, side in { 0, -1, 1 } do
			local to = (cf * CFrame.new(side * w / 2, 0, 0)).Position
			to = Vector3.new(to.X, y + math.min(up, h * 0.8), to.Z)
			if ray(from, to, ignore) then return nil end
			if up > 2 then break end -- (the corners only at knee height)
		end
	end
	return cf
end

-- the footprint of a container standing at cf (an oriented rectangle on the floor, GAP/2 bigger all round)
type Rect = { c: Vector3, x: Vector3, z: Vector3, hx: number, hz: number }
local function rectOf(cf: CFrame, w: number, front: number, back: number): Rect
	local mid = (cf * CFrame.new(0, 0, (back - front) / 2)).Position
	return { c = Vector3.new(mid.X, 0, mid.Z), x = cf.RightVector, z = cf.LookVector, hx = w / 2 + GAP / 2, hz = (front + back) / 2 + GAP / 2 }
end
local function overlaps(a: Rect, b: Rect): boolean
	local d = b.c - a.c
	for _, ax in { a.x, a.z, b.x, b.z } do
		local axis = Vector3.new(ax.X, 0, ax.Z)
		if axis.Magnitude > 1e-4 then
			axis = axis.Unit
			local ra = a.hx * math.abs(a.x:Dot(axis)) + a.hz * math.abs(a.z:Dot(axis))
			local rb = b.hx * math.abs(b.x:Dot(axis)) + b.hz * math.abs(b.z:Dot(axis))
			if math.abs(d:Dot(axis)) > ra + rb then return false end
		end
	end
	return true
end

-- where n containers of `kind` stand round a player: { cfs = floor CFrames (pivot = the middle of the bottom face, facing
-- the player) in the order they open (left to right for a half ring, clockwise from straight ahead for a ring), k = how
-- much smaller than F.SIZE they had to be (1 = not at all) }. one goes ahead of you (a little turned); five in a half
-- ring in front; ten in a ring all round. every spot is tested (spotAt): a blocked one comes in closer, or moves round
-- to the nearest free angle without touching the others; when they still don't all fit (a cupboard), all of them are
-- made smaller, down to 60%; past that they may touch. `at` moves the middle (a test). the server uses the same
-- function for what others see (Loot.luau), so they see the same ring
function F.layout(ch: Model, flat: Vector3, kind: string, n: number, at: Vector3?): { cfs: { CFrame }, k: number }
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local feetY = F.feet(ch) or (if root then root.Position.Y - 3 else 0)
	local mid = at or (if root then root.Position else Vector3.zero)
	local c = Vector3.new(mid.X, feetY, mid.Z)
	flat = Vector3.new(flat.X, 0, flat.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local ignore: { Instance } = {}
	for _, pl in game:GetService("Players"):GetPlayers() do if pl.Character then table.insert(ignore, pl.Character) end end
	if not table.find(ignore, ch) then table.insert(ignore, ch) end
	local op = OverlapParams.new()
	op.FilterType = Enum.RaycastFilterType.Exclude
	local skip = table.clone(ignore)
	table.insert(skip, workspace.Terrain)
	op.FilterDescendantsInstances = skip
	n = math.max(1, n)
	-- the plan: the angles (from straight ahead) and the radius they'd like
	local step = if n == 1 then 0 elseif n <= 5 then math.rad(45) else 2 * math.pi / n
	local twist = if n == 1 then math.rad(-20) else 0
	local plan = { 0 }
	for i = 1, n - 1 do table.insert(plan, (if i % 2 == 1 then 1 else -1) * math.ceil(i / 2) * step) end
	local function wanted(k: number): (number, number)
		local w, front = F.room(kind, k)
		local rmin = front + 1.7 -- (clear of you)
		if n == 1 then return math.max(rmin, 5.8 + front), rmin end
		return math.max(6.5, rmin, front + (w + GAP + 0.2) / (2 * math.sin(step / 2))), rmin
	end

	local function try(k: number, needFloor: boolean, final: boolean): { CFrame }?
		local R0, rmin = wanted(k)
		local w, front, back = F.room(kind, k)
		local memo: { [number]: any } = {}
		-- the farthest free spot at this angle, R0 first, coming in toward you
		local function best(a: number): { r: number, cf: CFrame }?
			local key = math.floor((a % (2 * math.pi)) * 1000 + 0.5) % 6283
			local m = memo[key]
			if m ~= nil then return if m == false then nil else m end
			local r = R0
			while r >= rmin - 1e-3 do
				local cf = spotAt(c, feetY, flat, a, r, kind, k, twist, ignore, op, needFloor)
				if cf then memo[key] = { r = r, cf = cf }; return memo[key] end
				r -= 0.75
			end
			memo[key] = false
			return nil
		end
		local placed: { { a: number, cf: CFrame, rect: Rect } } = {}
		for _, a0 in plan do
			local got = nil
			-- (the planned angle, then round from it both ways in 6 degree steps; one container only looks in front)
			local reach = if n == 1 then math.rad(90) else math.pi
			local da = 0
			while da <= reach + 1e-3 and not got do
				for _, sgn in (if da == 0 then { 1 } else { 1, -1 }) do
					local a = a0 + sgn * da
					local s = best(a)
					if s then
						local rect = rectOf(s.cf, w, front, back)
						local clear = true
						for _, o in placed do if overlaps(rect, o.rect) then clear = false; break end end
						if clear then got = { a = a, cf = s.cf, rect = rect }; break end
					end
				end
				da += math.rad(6)
			end
			if not got then
				if not final then return nil end
				-- (nowhere left: its planned angle, as near as it can, touching or not)
				local s = best(a0)
				local cf = if s then s.cf else spotAt(c, feetY, flat, a0, rmin, kind, k, twist, ignore, op, false)
				if not cf then
					local dir = CFrame.fromAxisAngle(Vector3.yAxis, a0):VectorToWorldSpace(flat)
					local g = c + dir * rmin
					cf = CFrame.lookAt(g, g - dir)
				end
				got = { a = a0, cf = cf :: CFrame, rect = rectOf(cf :: CFrame, w, front, back) }
			end
			table.insert(placed, got)
		end
		-- the order they open in
		local function key(a: number): number
			if n <= 5 then return -a end
			local v = (-a) % (2 * math.pi)
			return if v > 2 * math.pi - 1e-3 then 0 else v
		end
		table.sort(placed, function(p, q) return key(p.a) < key(q.a) end)
		local out = {}
		for i, p in placed do out[i] = p.cf end
		return out
	end

	for _, needFloor in { true, false } do
		local k = 1
		while k >= 0.6 - 1e-3 do
			local cfs = try(k, needFloor, false)
			if cfs then return { cfs = cfs, k = k } end
			k *= 0.85
		end
	end
	return { cfs = try(0.6, false, true) :: { CFrame }, k = 0.6 }
end

return F
