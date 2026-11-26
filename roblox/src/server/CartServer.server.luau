--!strict
-- weapons batch E: the Shopping Cart Cannon (WEAPONS.md "Shopping Cart Cannon"; traced spec weapons-batchE-spec.md,
-- web server/primaries.js + shared/physics.js stepCart). the cart is the SERVER's: an anchored model it flies, rolls and
-- parks itself (box casts against the map, a 0.6 m step-up, wall bounce, friction, a drop's speed carried on), that runs
-- people over (min(80, 3 x speed) and a shove along it, once a person every 0.7 s) and, parked, is solid cover (in the
-- map, so shots, projectiles and players stop on it). 25 s each, 3 a player, 6 a server.
-- riding (Cart remote "ride" id / "off" v): anyone on top of a cart that isn't flying hops in; their client drives it
-- (CartRide.client), the server keeps the real cart under their feet with a speed check and ploughs with their credit
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CartR = Remotes:FindFirstChild("Cart") :: RemoteEvent?
if not CartR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Cart"
	r.Parent = Remotes
	CartR = r
end

local S = Weapons.S
local now = os.clock
type Fighter = Rules.Fighter

local CART = {
	L = 0.95 * S, W = 0.6 * S, H = 1.0 * S, grav = 26 * S, fric = 6 * S, wallBounce = 0.35, restSp = 0.5 * S, restT = 0.25,
	dropBoost = 0.35, dropMin = 6 * S, step = 0.6 * S, life = 25, perPlayer = 3, perServer = 6,
	-- (26 Nov 2026, flying players) pad 0.12 -> 0.35 m: a cart grazing someone in the air still runs them over
	minSp = 4 * S, maxDmg = 80, dmgPerSp = 3, kbPerSp = 1.3, kbUp = 7 * S, pad = 0.35 * S, hitCd = 0.7, slow = 0.75,
	ownerSafe = 0.4, ownerSafeFly = 0.8, reach = 1.7 * S, upTol = 1.3 * S, maxRideIn = 14 * S, maxSp = 26 * S, leave = 3.5 * S,
}

type Cart = {
	id: number, owner: Fighter, p: Vector3, v: Vector3, yaw: number, state: string, t0: number, rest: number,
	rider: Fighter?, hitT: { [Fighter]: number }, model: Model, box: BasePart, ground: boolean,
}
local carts: { Cart } = {}
local nextId = 0

-- ------------------------------------------------------------------ the model: the kit's (w_pj_cart, metres) or a stand-in
local function folder(): Instance
	local map = workspace:FindFirstChild("Map") or workspace
	local f = map:FindFirstChild("JankfireCarts")
	if not f then
		f = Instance.new("Folder")
		f.Name = "JankfireCarts"
		f.Parent = map
	end
	return f :: Instance
end
local function build(id: number): (Model, BasePart)
	local m = Instance.new("Model")
	m.Name = "Cart" .. id
	-- the solid box (what stops shots and people when it's parked): the cart's own size, its bottom at the origin
	local box = Instance.new("Part")
	box.Name = "Box"
	box.Size = Vector3.new(CART.W, CART.H, CART.L)
	box.Transparency = 1
	box.Anchored = true; box.CanCollide = false; box.CanQuery = false; box.CanTouch = false; box.CastShadow = false
	box.Parent = m
	m.PrimaryPart = box
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
	local t = lib and lib:FindFirstChild("w_pj_cart")
	if t and t:IsA("Model") then
		local k = t:Clone()
		k:ScaleTo(k:GetScale() * S)
		for _, d in k:GetDescendants() do
			if d:IsA("BasePart") then d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true end
		end
		-- (the kit's origin is the floor under the middle: lift it so it sits on the box's bottom)
		k:PivotTo(box.CFrame * CFrame.new(0, -CART.H / 2, 0))
		for _, d in k:GetDescendants() do
			if d:IsA("BasePart") then
				local w = Instance.new("WeldConstraint"); w.Part0 = box; w.Part1 = d; w.Parent = d
			end
		end
		k.Parent = m
	else
		-- a stand-in basket on wheels
		local function bit(size: Vector3, off: Vector3, color: Color3)
			local p = Instance.new("Part")
			p.Size = size; p.Color = color; p.Material = Enum.Material.Metal
			p.Anchored = false; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
			p.CFrame = box.CFrame * CFrame.new(off)
			local w = Instance.new("WeldConstraint"); w.Part0 = box; w.Part1 = p; w.Parent = p
			p.Parent = m
		end
		local grey, accent = Color3.fromRGB(150, 155, 162), Color3.fromRGB(155, 92, 255)
		bit(Vector3.new(CART.W, 0.08 * S, CART.L), Vector3.new(0, -0.1 * S, 0), grey)
		bit(Vector3.new(0.04 * S, 0.5 * S, CART.L), Vector3.new(-CART.W / 2, 0.15 * S, 0), grey)
		bit(Vector3.new(0.04 * S, 0.5 * S, CART.L), Vector3.new(CART.W / 2, 0.15 * S, 0), grey)
		bit(Vector3.new(CART.W, 0.5 * S, 0.04 * S), Vector3.new(0, 0.15 * S, -CART.L / 2), grey)
		bit(Vector3.new(CART.W, 0.5 * S, 0.04 * S), Vector3.new(0, 0.15 * S, CART.L / 2), grey)
		bit(Vector3.new(CART.W, 0.05 * S, 0.05 * S), Vector3.new(0, 0.45 * S, CART.L / 2 + 0.08 * S), accent)
		for _, x in { -1, 1 } do for _, z in { -1, 1 } do
			bit(Vector3.new(0.05 * S, 0.12 * S, 0.12 * S), Vector3.new(x * CART.W * 0.4, -0.44 * S, z * CART.L * 0.4), Color3.fromRGB(30, 32, 36))
		end end
	end
	m:SetAttribute("CartId", id)
	m.Parent = folder()
	return m, box
end

-- ------------------------------------------------------------------ moving it
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Include
local function cast(cf: CFrame, size: Vector3, dir: Vector3): RaycastResult?
	local map = workspace:FindFirstChild("Map")
	if not map or dir.Magnitude < 1e-5 then return nil end
	params.FilterDescendantsInstances = { map }
	return workspace:Blockcast(cf, size, dir, params)
end
local function boxCF(c: Cart, p: Vector3?): CFrame return CFrame.new((p or c.p) + Vector3.new(0, CART.H / 2, 0)) * CFrame.Angles(0, c.yaw, 0) end
local SIZE = Vector3.new(CART.W, CART.H, CART.L) * 0.94 -- (a hair inside the box: a cast from touching a wall still moves)
local function solid(c: Cart, on: boolean)
	c.box.CanCollide = on
	c.box.CanQuery = on
end
local function place(c: Cart)
	c.box.CFrame = boxCF(c)
	c.model:SetAttribute("CartState", c.state)
	c.model:SetAttribute("CartV", c.v)
end
local function remove(c: Cart, why: string)
	local i = table.find(carts, c)
	if i then table.remove(carts, i) end
	if c.rider and c.rider.kind == "player" then (c.rider.ref :: Player):SetAttribute("RidingCart", nil) end
	FxR:FireAllClients({ k = "cartx", id = c.id, p = c.p, why = why })
	c.model:Destroy()
end

local function stepFree(c: Cart, dt: number)
	c.v -= Vector3.new(0, CART.grav * dt, 0)
	local move = c.v * dt
	-- across: a wall bounces it back; a step up to 0.6 m it climbs
	local h = Vector3.new(move.X, 0, move.Z)
	if h.Magnitude > 1e-5 then
		local hit = cast(boxCF(c), SIZE, h)
		if hit then
			-- a step up to 0.6 m, only off the floor (in the air it would climb any wall a step a frame), then down onto it
			local up = Vector3.new(0, CART.step, 0)
			if c.ground and not cast(boxCF(c), SIZE, up) and not cast(boxCF(c, c.p + up), SIZE, h) then
				c.p += up + h
				local land = cast(boxCF(c), SIZE, -up)
				if land then c.p -= Vector3.new(0, math.max(0, land.Distance - 0.02), 0) end
			else
				c.p += h.Unit * math.max(0, hit.Distance - 0.02)
				local n = Vector3.new(hit.Normal.X, 0, hit.Normal.Z)
				if n.Magnitude > 1e-3 then
					n = n.Unit
					local vh = Vector3.new(c.v.X, 0, c.v.Z)
					local vn = vh:Dot(n)
					if vn < 0 then vh -= n * vn * (1 + CART.wallBounce) end
					c.v = Vector3.new(vh.X, c.v.Y, vh.Z)
				end
			end
		else
			c.p += h
		end
	end
	-- down / up
	c.ground = false
	local vy = Vector3.new(0, move.Y, 0)
	local hit = cast(boxCF(c), SIZE, vy)
	if hit then
		c.p += vy.Unit * math.max(0, hit.Distance - 0.02)
		if move.Y < 0 then
			c.ground = true
			local fall = -c.v.Y
			if fall > CART.dropMin then -- (a drop's speed carried on along its roll)
				local hv = Vector3.new(c.v.X, 0, c.v.Z)
				local dir = if hv.Magnitude > 0.1 then hv.Unit else Vector3.new(-math.sin(c.yaw), 0, -math.cos(c.yaw))
				c.v += dir * fall * CART.dropBoost
			end
		end
		c.v = Vector3.new(c.v.X, 0, c.v.Z)
	else
		c.p += vy
	end
	-- the floor's friction, and it turns to face where it rolls
	local hv = Vector3.new(c.v.X, 0, c.v.Z)
	local sp = hv.Magnitude
	if c.ground then
		local ns = math.max(0, sp - CART.fric * dt)
		hv = if sp > 1e-3 then hv * (ns / sp) else Vector3.zero
		c.v = Vector3.new(hv.X, c.v.Y, hv.Z)
		sp = ns
		if c.state == "fly" then c.state = "roll" end
	end
	if sp > 1 * S then c.yaw = math.atan2(-hv.X, -hv.Z) end
	-- parked: still for a moment on the floor
	if c.ground and sp < CART.restSp then
		c.rest += dt
		if c.rest >= CART.restT then c.state = "rest"; c.v = Vector3.zero end
	else
		c.rest = 0
	end
end

-- who it runs over: the box (its turned footprint) and a body, pad round it
local function plough(c: Cart)
	local sp = Vector3.new(c.v.X, 0.5 * c.v.Y, c.v.Z).Magnitude
	if sp < CART.minSp then return end
	local by = c.rider or c.owner
	local n = now()
	local cs, sn = math.abs(math.cos(c.yaw)), math.abs(math.sin(c.yaw))
	local hx = cs * CART.W / 2 + sn * CART.L / 2 + 0.4 * S + CART.pad
	local hz = sn * CART.W / 2 + cs * CART.L / 2 + 0.4 * S + CART.pad
	local hv = Vector3.new(c.v.X, 0, c.v.Z)
	local dir = if hv.Magnitude > 1e-3 then hv.Unit else Vector3.zero
	for _, t in Fight.all do
		if not t.alive or t == c.rider then continue end
		if t == c.owner and not c.rider and n - c.t0 < (if c.state == "fly" then CART.ownerSafeFly else CART.ownerSafe) then continue end
		if (c.hitT[t] or -math.huge) > n - CART.hitCd then continue end
		local ft = Fight.feet(t)
		if not ft then continue end
		local d = ft - c.p
		if math.abs(d.X) > hx or math.abs(d.Z) > hz or d.Y < -1.8 * S or d.Y > CART.H + CART.pad then continue end
		c.hitT[t] = n
		local kb = dir * CART.kbPerSp * sp + Vector3.new(0, CART.kbUp, 0)
		local dmg = math.min(CART.maxDmg, CART.dmgPerSp * sp / S)
		-- (your own cart on you, or one whose shooter has left: only the shove)
		if t == by or not table.find(Fight.all, by) or not Fight.allow(by, t) then Fight.knock(t, kb, "cart")
		else
			Fight.hurt(t, dmg, by, "cart", false, kb, ft + Vector3.new(0, 1 * S, 0))
			-- (26 Nov 2026) run over while hanging on a grapple rope: the rope goes (as WeaponProj's direct hits)
			if t.kind == "player" then
				local rp = t.ref :: Player
				local rope = workspace.Terrain:FindFirstChild("Rope_" .. rp.UserId)
				local gr = Remotes:FindFirstChild("Grapple")
				if rope then rope:Destroy(); if gr and gr:IsA("RemoteEvent") then gr:FireClient(rp, "cut", "shot") end end
			end
		end
		FxR:FireAllClients({ k = "carthit", id = c.id, p = ft + Vector3.new(0, 1 * S, 0) })
		if not c.rider then c.v = Vector3.new(c.v.X * CART.slow, c.v.Y, c.v.Z * CART.slow) end
	end
end

-- somebody standing in a parked cart's box: it isn't solid till they're out (no one is shut inside it)
local function occupied(c: Cart): boolean
	for _, t in Fight.all do
		local ft = t.alive and Fight.feet(t)
		if ft then
			local d = ft - c.p
			if math.abs(d.X) < CART.L / 2 + 0.4 * S and math.abs(d.Z) < CART.L / 2 + 0.4 * S and d.Y > -1.8 * S and d.Y < CART.H - 0.2 * S then return true end
		end
	end
	return false
end

RunService.Heartbeat:Connect(function(dt: number)
	local n = now()
	for i = #carts, 1, -1 do
		local c = carts[i]
		if n - c.t0 > CART.life then remove(c, "gone"); continue end
		if c.p.Y < workspace.FallenPartsDestroyHeight + 20 then remove(c, "gone"); continue end
		if c.state == "ride" then
			local r = c.rider
			local feet = r and r.alive and Fight.feet(r)
			if not r or not feet or not table.find(Fight.all, r) then
				c.rider = nil; c.state = "roll"
				if r and r.kind == "player" then (r.ref :: Player):SetAttribute("RidingCart", nil) end
			else
				local want = feet - Vector3.new(0, CART.H, 0)
				if (want - c.p).Magnitude > CART.leave + 40 * S * dt then
					-- (the rider is far from where the cart could be: they've left it)
					c.rider = nil; c.state = "roll"
					if r.kind == "player" then (r.ref :: Player):SetAttribute("RidingCart", nil) end
				else
					-- the cart under their feet; its speed the real move's, capped (a client can't claim a faster one)
					local real = (want - c.p) / math.max(dt, 1 / 120)
					local cap = math.min(CART.maxSp, real.Magnitude)
					c.v = if real.Magnitude > 2 * CART.maxSp then Vector3.zero elseif real.Magnitude > 1e-3 then real.Unit * cap else Vector3.zero
					local hv = Vector3.new(c.v.X, 0, c.v.Z)
					if hv.Magnitude > 1 * S then c.yaw = math.atan2(-hv.X, -hv.Z) end
					c.p = want
					if r.kind == "player" then (r.ref :: Player):SetAttribute("ACGrace", n + 0.6) end -- (a rider goes faster than running)
					plough(c)
				end
			end
		elseif c.state == "rest" then
			-- the floor gone from under it: it rolls again
			if not cast(boxCF(c), SIZE, Vector3.new(0, -0.35 * S, 0)) then c.state = "roll"; c.rest = 0
			else solid(c, not occupied(c)) end
		end
		if c.state == "fly" or c.state == "roll" then
			solid(c, false)
			stepFree(c, dt)
			plough(c)
		end
		place(c)
	end
end)

-- ------------------------------------------------------------------ the shot, hopping in and out
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function fire(p: Player, eye: Vector3, look: Vector3)
	local f = Fight.byPlayer[p]
	local w = Weapons.list.cart :: any
	if not f or not w or not f.alive or f.held ~= "cart" or not table.find(Rules.loadoutOf(f), "cart") then return end
	local n = now()
	if n < f.staggerUntil then return end
	if not Rules.gate(f, "cart", n, w.cd / 0.9 * 0.75) then return end
	local seye = Fight.eye(f)
	if not seye then return end
	if (eye - seye).Magnitude > 4 * S then eye = seye end
	-- your oldest past 3, the server's oldest past 6
	local mine = {}
	for _, c in carts do if c.owner == f then table.insert(mine, c) end end
	while #mine >= CART.perPlayer do remove(table.remove(mine, 1) :: Cart, "gone") end
	while #carts >= CART.perServer do remove(carts[1], "gone") end
	-- 1 m out in front of your eye (short of a wall), 0.75 m lower; inside the map: at your feet
	local map = workspace:FindFirstChild("Map")
	local out = 1.0 * S
	if map then
		mapParams.FilterDescendantsInstances = { map }
		local hit = workspace:Raycast(eye, look * 1.3 * S, mapParams)
		if hit then out = math.max(0, hit.Distance - 0.7 * S) end
	end
	local at = eye + look * out - Vector3.new(0, 0.75 * S, 0) - Vector3.new(0, CART.H / 2, 0)
	local root = Fight.root(f)
	local inherit = if root then root.AssemblyLinearVelocity * 0.3 else Vector3.zero
	inherit = Vector3.new(inherit.X, math.max(0, inherit.Y), inherit.Z)
	nextId += 1
	local id = nextId
	local m, box = build(id)
	local c: Cart = {
		id = id, owner = f, p = at, v = look * w.speed + inherit + Vector3.new(0, w.up, 0), yaw = math.atan2(-look.X, -look.Z),
		state = "fly", t0 = n, rest = 0, rider = nil, hitT = {}, model = m, box = box, ground = false,
	}
	-- (inside the map there, a shot down at the floor: lifted clear, or at your feet. a cast can't see what it starts in)
	local function inside(): boolean
		local mp = workspace:FindFirstChild("Map")
		if not mp then return false end
		local op = OverlapParams.new()
		op.FilterType = Enum.RaycastFilterType.Include
		op.FilterDescendantsInstances = { mp }
		for _, part in workspace:GetPartBoundsInBox(boxCF(c), SIZE, op) do
			if part:IsA("BasePart") and part.CanCollide and part ~= c.box then return true end
		end
		return false
	end
	local tries = 0
	while inside() and tries < 6 do tries += 1; c.p += Vector3.new(0, 0.5 * S, 0) end
	if inside() then
		local ft = Fight.feet(f)
		if ft then c.p = ft end
	end
	table.insert(carts, c)
	place(c)
	Fight.shot(f, "cart")
	FxR:FireAllClients({ k = "cart", id = id, by = p.UserId, p = c.p })
end
local function cartById(id: unknown): Cart?
	if type(id) ~= "number" then return nil end
	for _, c in carts do if c.id == id then return c end end
	return nil
end
local rideT: { [Player]: number } = {}
;(CartR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, op: unknown, a: unknown, b: unknown)
	if op == "fire" then
		if (p:GetAttribute("Zone") == "hub" and p:GetAttribute("DevArms") ~= true) or typeof(a) ~= "Vector3" or typeof(b) ~= "Vector3" then return end
		local lk = b :: Vector3
		if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 then return end
		fire(p, a :: Vector3, lk.Unit)
	elseif op == "ride" then
		local n = now()
		if n - (rideT[p] or 0) < 0.15 then return end
		rideT[p] = n
		local f = Fight.byPlayer[p]
		local c = cartById(a)
		if not f or not f.alive or not c or c.rider or c.state == "fly" or p:GetAttribute("RidingCart") then return end
		if Vector3.new(c.v.X, 0, c.v.Z).Magnitude > CART.maxRideIn then return end
		if p:GetAttribute("PinUntil") or n < f.staggerUntil then return end
		local feet = Fight.feet(f)
		if not feet then return end
		local top = c.p + Vector3.new(0, CART.H, 0)
		local d = feet - top
		if Vector3.new(d.X, 0, d.Z).Magnitude > CART.reach or math.abs(d.Y) > CART.upTol then return end
		c.rider, c.state = f, "ride"
		solid(c, false)
		p:SetAttribute("RidingCart", c.id)
		p:SetAttribute("ACGrace", n + 0.6)
	elseif op == "off" then
		local id = p:GetAttribute("RidingCart")
		p:SetAttribute("RidingCart", nil)
		local c = cartById(id)
		if not c or not c.rider or c.rider.ref ~= p then return end
		c.rider, c.state = nil, "roll"
		-- it keeps rolling at your speed, never faster than it was going + 2 (and 26 a side)
		if typeof(a) == "Vector3" then
			local v = a :: Vector3
			local lim = Vector3.new(c.v.X, 0, c.v.Z).Magnitude + 2 * S
			local hv = Vector3.new(v.X, 0, v.Z)
			if hv.Magnitude > lim then hv = hv.Unit * lim end
			c.v = Vector3.new(math.clamp(hv.X, -CART.maxSp, CART.maxSp), 0, math.clamp(hv.Z, -CART.maxSp, CART.maxSp))
		end
	end
end)
Players.PlayerRemoving:Connect(function(p)
	rideT[p] = nil
	for i = #carts, 1, -1 do
		local c = carts[i]
		if c.rider and c.rider.ref == p then c.rider = nil; c.state = "roll" end
	end
end)
