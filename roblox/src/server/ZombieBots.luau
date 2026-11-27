--!strict
-- ZOMBIES: the squad's bots, their brains (26 Nov 2026, the owner: "the bots follow you instead of actually playing,
-- let them shoot open doors buy guns etc.."). Zombies.luau makes each bot's body, spawns it and keeps its credits like
-- anyone's; this module decides what it does, one step every tick, in this order:
--   1. REVIVE a downed friend (people first), walking there on the nav grid.
--   2. FIGHT the nearest zombie it can see (one at a window too), with a person's aim and trigger finger: bursts from
--      an automatic, one pellet roll per pellet from a shotgun; it backs off from the ones in its face.
--   3. SHOP when nothing's close: throws the power, buys a better wall gun, opens the cheapest door out of the open
--      areas (one door a round for the bots together, from round 2), voids its gun at the Warranty Voider, buys Jank Cola then Get Up Juice.
--      Same prices and the same checks as yours (Zombies.X / ZombieExtra's ext.bot*): it pays with its own credits.
--   4. HOLD A POST: each bot takes a different window of the open areas near the players, stands a few studs inside it
--      facing it, and nails the planks back between fights; with no window near, a spot round the players. So the
--      squad spreads out round you instead of trailing you.
-- Studio test: ServerStorage.JankZombies "bots" lists each bot's state, gun, credits and what it's doing; "botc" n sets
-- every bot's credits
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local ZM = require(Shared:WaitForChild("ZM"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Nav = require(script.Parent:WaitForChild("ZombieNav"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local ZombieBots = {}
local W = Weapons.list
local R = ZM.R
local now = os.clock
local INF = math.huge
local Z: any = nil
local X: any = nil

-- how far it looks for zombies; how close is "in my face"; what counts as quiet enough to shop
local SIGHT, SIGHT_WIN = 90, 45
local QUIET = 30
local POST_NEAR = 80 -- studs on foot from a player: windows further off aren't anyone's post
local POST_EVERY = 12 -- s between post picks (sooner if the players move or a door opens)

type Field = { d: { [number]: number }, t: number, at: Vector3 }
type Goal = { kind: string, id: string?, at: Vector3, why: string, t0: number, act: () -> (), holdT: number? }
type St = {
	post: { at: Vector3, look: Vector3, wi: number? }?, postT: number, postFrom: Vector3, postField: number,
	goal: Goal?, goalField: Field, postFieldT: Field, own: Field, ownT: number,
	shopT: number, doorRound: number, nailT: number, burst: number, doing: string, failT: { [string]: number },
}
local ST: { [any]: St } = setmetatable({}, { __mode = "k" }) :: any
local SQUAD_DOOR: { [any]: number } = setmetatable({}, { __mode = "k" }) :: any -- (game -> the round the bots last opened a door)
local function st(m: any): St
	local s = ST[m]
	if not s then
		s = {
			post = nil, postT = -INF, postFrom = Vector3.new(1e9, 0, 0), postField = -INF, goal = nil,
			goalField = { d = {}, t = -INF, at = Vector3.new(1e9, 0, 0) }, postFieldT = { d = {}, t = -INF, at = Vector3.new(1e9, 0, 0) },
			own = { d = {}, t = -INF, at = Vector3.new(1e9, 0, 0) }, ownT = -INF,
			shopT = now() + 3 + math.random() * 3, doorRound = -1, nailT = 0, burst = 0, doing = "", failT = {},
		}
		ST[m] = s
	end
	return s
end

local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end
-- rays against the game's own map copy (its walls, shut doors, furniture: Fight.castMap only knows workspace.Map; the
-- bots' bodies in the copy are CanQuery false, the zombies are in workspace.Dummies)
local PARAMS: { [any]: RaycastParams } = setmetatable({}, { __mode = "k" }) :: any
local function mapRay(g: any, from: Vector3, to: Vector3): RaycastResult?
	local p = PARAMS[g]
	if not p then
		p = RaycastParams.new()
		p.FilterType = Enum.RaycastFilterType.Include
		p.FilterDescendantsInstances = { g.model }
		PARAMS[g] = p
	end
	return workspace:Raycast(from, to - from, p)
end
-- the floor point on the nav grid under (or nearest) p: a cell's centre on its floor
local function floorAt(g: any, p: Vector3): Vector3?
	local c = Nav.cellOf(g.nav, p)
	if c < 0 or not g.nav.floor[c] then return nil end
	local x, z = Nav.centre(g.nav, c)
	return Vector3.new(x, g.nav.floor[c], z)
end
-- a field to a fixed spot, redone when the spot moves, a door opens, or it's old
local function fieldTo(g: any, f: Field, at: Vector3, maxAge: number): { [number]: number }
	if now() - f.t > maxAge or flat(at - f.at).Magnitude > 3 or math.abs(at.Y - f.at.Y) > 4 or f.t < g.fieldT then
		Nav.flow(g.nav, g.open, at, f.d)
		f.t, f.at = now(), at
	end
	return f.d
end
local function areaOpen(g: any, p: Vector3): boolean
	local a = ZM.areaAt(g.map, p)
	return a ~= nil and g.areas[a] == true
end

-- ------------------------------------------------------------------ guns: how good one is for a bot
-- (damage a second to a zombie IN A BOT'S HANDS, held up over a whole magazine and its reload: the bot's own trigger
-- timing from shoot() below; hitscan guns only, the ones it can fire. 26 Nov play test: scored on the gun's raw rate,
-- the starting revolver (2.5 a second) outranked every wall gun near the start and no bot bought one; held fire, its
-- six rounds and their reload put it where it belongs)
local START = { revolver = true, pistol = true } -- (the bots' starting guns: anything off a wall beats them)
local function score(wid: string): number
	local w = W[wid]
	if not w or w.kind ~= "hitscan" or not w.mag then return 0 end
	local rate = math.max(0.5, Weapons.fireRate(w, 100))
	local gap = if w.auto then 1.15 / rate + 0.4 / 6.5 else 1 / rate + 0.27
	local mag = w.mag :: number
	local cycle = mag * gap + ((w.reload :: number?) or 1.5)
	local d = (w.dmg :: number) * ((w.pellets :: number?) or 1) * (if Weapons.base(wid) == "revolver" then R.revolverDmg / math.max(1, w.dmg :: number) else 1)
	local s = d * mag / cycle * (if (w.pellets or 1) > 1 then 0.55 else 1) -- (a shotgun's pellets don't all land)
	return s * (if START[wid] then 0.8 else 1)
end
local function setGun(g: any, m: any, wid: string)
	local b = m.bot
	local f = m.f
	m.guns = { wid }
	b.gun = wid
	b.mag, b.reloadUntil = (W[wid].mag :: number?) or 6, 0
	f.forced = X.kitList(m)
	f.held = wid
	if f.alive then X.fight().showWeapon(f) end
	local _ = g
end

-- ------------------------------------------------------------------ one shot (or a shotgun's pellets) at a zombie
local function shoot(g: any, m: any, z: any)
	local b = m.bot
	local f = m.f
	local Fight = X.fight()
	local w = W[b.gun]
	local eye = Fight.eye(f)
	if not eye or not w then return end
	local tf = X.feetOf(z.root)
	local k = z.k or 1
	local head = math.random() < 0.24
	local aimAt = tf + Vector3.new(0, (if head then 5.2 else 3.4) * k, 0)
	local dist = (aimAt - eye).Magnitude
	local err = 0.05 + dist / 520 -- (radians of spread on top of the gun's own: a person's aim, web zhDiff)
	local range = (w.range :: number?) or 300
	local n, hs, ends = 0, 0, {}
	local base = (aimAt - eye).Unit
	-- (the aim's error is one per trigger pull; the gun's own spread is per pellet)
	local aimDir = Hitbox.spreadDir(base, err, math.random(), math.random())
	for _ = 1, math.max(1, (w.pellets :: number?) or 1) do
		local d = Hitbox.spreadDir(aimDir, ((w.spread :: number?) or 0.01), math.random(), math.random())
		local hitMap = mapRay(g, eye, eye + d * range)
		local mapT = if hitMap then (hitMap.Position - eye).Magnitude else range
		local t, hd = Hitbox.ray(eye, d, tf, Hitbox.distScale((tf - eye).Magnitude), nil, Hitbox.profile(z.m))
		if t and t < mapT then
			n += 1
			if hd then hs += 1 end
			if #ends < 12 then table.insert(ends, eye + d * t) end
		elseif #ends < 12 then
			table.insert(ends, eye + d * mapT)
		end
	end
	if n > 0 and Fight.applyHitscan then Fight.applyHitscan(f, z.f, b.gun, n, hs, eye) end
	local r = Remotes:FindFirstChild("Shot")
	if r and r:IsA("RemoteEvent") then r:FireAllClients({ model = Fight.model(f), w = b.gun, ends = ends }) end
	b.mag -= 1
	local rate = math.max(0.5, Weapons.fireRate(w, f.hp))
	local s = st(m)
	if w.auto then
		-- an automatic: a burst of 4 to 9 at the gun's rate (a little slower), then a beat to re-aim
		if s.burst <= 0 then s.burst = math.random(4, 9) end
		s.burst -= 1
		b.nextShot = now() + 1.15 / rate + (if s.burst <= 0 then 0.25 + math.random() * 0.3 else 0)
	else
		b.nextShot = now() + 1 / rate + 0.12 + math.random() * 0.3 -- (a person's trigger finger)
	end
	if b.mag <= 0 then b.reloadUntil = now() + ((w.reload :: number?) or 1.5); s.burst = 0 end
end

-- ------------------------------------------------------------------ posts: a window each, near the players
local function people(g: any): { any }
	local out = {}
	for _, o in g.members do if not o.bot and o.f.alive then table.insert(out, o) end end
	return out
end
local function pickPosts(g: any)
	local live = people(g)
	local bots = {}
	for _, o in g.members do if o.bot and o.f.alive then table.insert(bots, o) end end
	if #bots == 0 then return end
	local Fight = X.fight()
	-- no one up: stay where they are (reviving comes first anyway)
	if #live == 0 then return end
	-- windows of the open areas, by how far they are on foot from the nearest player
	local cands = {}
	for wi, w in g.map.windows do
		if not g.areas[w.area] then continue end
		local at = floorAt(g, w.inn + w.n * 5.5 + Vector3.new(0, 1, 0))
		if not at then continue end
		local best = INF
		for _, p in live do
			local fl = p.field
			if fl then best = math.min(best, Nav.dist(g.nav, g.open, fl.d, at)) end
		end
		if best <= POST_NEAR then table.insert(cands, { wi = wi, at = at, look = -w.n, d = best }) end
	end
	table.sort(cands, function(a, b) return a.d < b.d end)
	-- the bots nearest a window first, so nobody runs across the room past another bot's post
	local taken = {}
	for _, o in bots do
		local s = st(o)
		local r = Fight.root(o.f)
		if not r then continue end
		local me = X.feetOf(r)
		local best, bd = nil, INF
		for ci, c in cands do
			if taken[ci] then continue end
			local d = c.d + flat(c.at - me).Magnitude * 0.35
			if d < bd then bd, best = d, ci end
		end
		if best then
			taken[best] = true
			local c = cands[best]
			s.post = { at = c.at, look = c.look, wi = c.wi }
		else
			-- a spot round a player, its own side of them
			local p = live[((o.bot.i - 1) % #live) + 1]
			local pr = Fight.root(p.f)
			if pr then
				local a = (o.bot.i / 4) * math.pi * 2 + 0.6
				local at = floorAt(g, X.feetOf(pr) + Vector3.new(math.cos(a), 0, math.sin(a)) * 12 + Vector3.new(0, 1, 0))
				local fl = p.field
				if at and fl and Nav.dist(g.nav, g.open, fl.d, at) < 40 then
					s.post = { at = at, look = flat(X.feetOf(pr) - at).Unit, wi = nil }
				else
					s.post = nil
				end
			end
		end
		s.postT = now()
	end
end

-- ------------------------------------------------------------------ shopping (only when it's quiet round the bot)
local function quiet(g: any, pos: Vector3): boolean
	if g.st ~= "live" then return true end
	for _, z in g.mobs do
		if z.f.alive and z.ph == "hunt" and (z.root.Position - pos).Magnitude < QUIET then return false end
	end
	return true
end
-- the doors a bot may buy: shut, one side open, the other not
local function frontier(g: any): { number }
	local out = {}
	for i, d in g.map.doors do
		if g.open[i] then continue end
		if (g.areas[d.a] == true) ~= (g.areas[d.b] == true) then table.insert(out, i) end
	end
	return out
end
-- where to stand to use a wall marker (a wall buy, the power, a machine): in front of it, on the floor
local function frontOf(g: any, cf: CFrame, out: number): Vector3?
	local look = flat(cf.LookVector)
	look = if look.Magnitude > 1e-3 then look.Unit else Vector3.zAxis
	return floorAt(g, cf.Position + look * out + Vector3.new(0, 1, 0))
end
local function doorSide(g: any, i: number): Vector3?
	local sh = g.map.doors[i].shutter :: BasePart
	local thin = if sh.Size.X <= sh.Size.Z then sh.CFrame.RightVector else sh.CFrame.LookVector
	for _, sgn in { 1, -1 } do
		local p = sh.Position + thin * (sgn * 3.6)
		local fp = floorAt(g, p)
		if fp and areaOpen(g, fp + Vector3.new(0, 1, 0)) then return fp end
	end
	return nil
end
local function decide(g: any, m: any, s: St, pos: Vector3): Goal?
	local b = m.bot
	local n = now()
	local c = m.c
	-- how far everything is on foot from here (one field, redone at most every 4 s)
	local own = fieldTo(g, s.own, pos, 6)
	local function far(at: Vector3): number return Nav.dist(g.nav, g.open, own, at) end
	local function ok(key: string): boolean return n >= (s.failT[key] or 0) end
	local ext = Z.ext
	local spots = if ext.botSpots then ext.botSpots(g) else {}
	-- 1. the power (free)
	for _, sp in spots do
		if sp.kind == "power" and ok("power") then
			local at = frontOf(g, sp.cf, 2.6)
			if at and areaOpen(g, at + Vector3.new(0, 1, 0)) and far(at) < 260 then
				return { kind = "power", at = at, why = "power", t0 = n, act = function() ext.botUse(g, m, "power") end }
			end
		end
	end
	-- 2. a better wall gun
	local mine = score(b.gun)
	local bestB, bestS = nil, mine * 1.08 -- (a clear step up: a pistol bot takes the AR, the LMG, the burst rifle)
	for _, wb in g.map.buys do
		if wb.price > c - 100 or not ok("buy" .. wb.i) then continue end
		local sc = score(wb.w)
		if sc <= bestS then continue end
		local at = frontOf(g, wb.part.CFrame, 3)
		if not at or not areaOpen(g, at + Vector3.new(0, 1, 0)) or far(at) > 240 then continue end
		bestB, bestS = wb, sc
	end
	if bestB then
		local wb = bestB
		local at = frontOf(g, wb.part.CFrame, 3) :: Vector3
		return { kind = "gun", id = wb.w, at = at, why = "buy " .. wb.w, t0 = n, act = function()
			if m.c < wb.price or not X.inOpenArea(m) then return end
			if X.pay(m, wb.price) then
				setGun(g, m, wb.w)
				X.sayAll({ k = "buy", ok = true, m = m.name .. " bought " .. ((W[wb.w] and W[wb.w].name) or wb.w) })
			end
		end }
	end
	-- 3. a door (one a round each, from round 2: the squad's spending isn't all on doors)
	if g.n >= 2 and s.doorRound ~= g.n and SQUAD_DOOR[g] ~= g.n then -- (26 Nov play test: a door a bot a round opened 7 by round 8; now one a round for the bots together)
		local bestI, bestK = nil, INF
		for _, i in frontier(g) do
			local d = g.map.doors[i]
			if d.price + 250 > c or not ok("door" .. i) then continue end
			local at = doorSide(g, i)
			if not at then continue end
			local dd = far(at)
			if dd > 220 then continue end
			local k = d.price + dd * 2
			if k < bestK then bestK, bestI = k, i end
		end
		if bestI then
			local i = bestI
			local d = g.map.doors[i]
			return { kind = "door", id = tostring(i), at = doorSide(g, i) :: Vector3, why = "open " .. d.label, t0 = n, act = function()
				if g.open[i] or m.c < d.price or not X.inOpenArea(m) then return end
				if SQUAD_DOOR[g] == g.n then return end
				if X.pay(m, d.price) then X.openDoor(g, i, m); s.doorRound = g.n; SQUAD_DOOR[g] = g.n end
			end }
		end
	end
	-- 4. the Warranty Voider on its gun, 5. colas (Jank Cola, then Get Up Juice)
	for _, sp in spots do
		local at = frontOf(g, sp.cf, 3)
		if not at or not areaOpen(g, at + Vector3.new(0, 1, 0)) or far(at) > 240 then continue end
		if sp.kind == "void" and ok("void") then
			local tier = ext.botHas(g, m, "void", b.gun)
			local price = ZM.UP.price[tier + 1]
			if price and c >= price + 400 and mine > 0 then
				return { kind = "void", at = at, why = "void " .. b.gun, t0 = n, act = function() ext.botUse(g, m, "void") end }
			end
		elseif sp.kind == "cola" and (sp.id == "jank" or sp.id == "getup") and ok("cola" .. sp.id) then
			if not ext.botHas(g, m, "cola", sp.id) and c >= sp.price + 500 then
				return { kind = "cola", id = sp.id, at = at, why = "cola " .. sp.id, t0 = n, act = function() ext.botUse(g, m, "cola", sp.id) end }
			end
		end
	end
	return nil
end

-- ------------------------------------------------------------------ the step
local function step(g: any, m: any, dt: number)
	local b = m.bot
	local f = m.f
	local Fight = X.fight()
	local hum = Fight.hum(f)
	local r = Fight.root(f)
	if not f.alive or not hum or not r or g.st == "over" then
		if hum and f.alive then hum:Move(Vector3.zero, false) end
		return
	end
	local s = st(m)
	local n = now()
	local pos = X.feetOf(r)
	local eye = Fight.eye(f) or r.Position
	-- think: the zombie to shoot, the friend to revive
	if n >= b.think then
		b.think = n + 0.25 + math.random() * 0.15
		local th, td = nil :: any, INF
		for _, z in g.mobs do
			if not z.f.alive then continue end
			local d = (z.root.Position - r.Position).Magnitude
			local lim = if z.ph == "hunt" then SIGHT else SIGHT_WIN
			if d > lim then continue end
			-- (one close to a player matters more than one far off)
			local k = d
			for _, o in g.members do
				local orr = not o.bot and o.f.alive and Fight.root(o.f)
				if orr and (orr.Position - z.root.Position).Magnitude < 10 then k -= 12 end
			end
			if k < td and not mapRay(g, eye, z.root.Position + Vector3.new(0, 1.5 * (z.k or 1), 0)) then th, td = z, k end
		end
		if th and th ~= b.th then b.nextShot = math.max(b.nextShot, n + 0.3 + math.random() * 0.25) end -- (a moment to react)
		b.th, b.td = th, if th then (th.root.Position - r.Position).Magnitude else INF
		local best, bd = nil, INF
		for _, o in g.members do
			if o == m or not o.down or (o.reviver and o.reviver ~= m) then continue end
			local orr = Fight.root(o.f)
			if not orr then continue end
			local d = (orr.Position - r.Position).Magnitude - (if o.p then 40 else 0) -- (people first)
			if d < bd then bd, best = d, o end
		end
		if b.task ~= best and b.task and b.task.reviver == m then b.task.reviver = nil end
		b.task = best
	end
	-- the posts: picked again every few seconds, when the players move off, or a door opens
	local live = people(g)
	local anchor = live[1] and Fight.root(live[1].f)
	if n - s.postT > POST_EVERY or s.postField < g.fieldT or (anchor and flat(anchor.Position - s.postFrom).Magnitude > 26) then
		pickPosts(g)
		for _, o in g.members do if o.bot then local os_ = st(o); os_.postField = now(); if anchor then os_.postFrom = anchor.Position end end end
	end
	local wish = Vector3.zero
	local reviving = false
	local th = b.th
	if th and not th.f.alive then th = nil; b.th = nil end
	local o = b.task
	local function walkTo(at: Vector3, fld: Field): Vector3
		local p = Nav.downhill(g.nav, g.open, fieldTo(g, fld, at, 4 + (m.bot.i % 3) * 0.5), pos) -- (staggered ages: three bots never refresh in one tick)
		return if p then flat(p - pos) else flat(at - pos)
	end
	if o and o.down then
		-- 1. revive
		s.doing = "revive " .. o.name
		s.goal = nil
		local orr = Fight.root(o.f)
		if orr then
			local at = X.feetOf(orr)
			if flat(at - pos).Magnitude > 5.4 or math.abs(at.Y - pos.Y) > 5 then
				wish = walkTo(at, s.goalField)
			else
				reviving = true
				if o.reviver ~= m then o.reviver = m; b.revT0 = n end
				if n - b.revT0 >= R.revive then X.standUp(o, m); b.task = nil end
			end
		end
	else
		if o and o.reviver == m then o.reviver = nil end
		b.task = nil
		-- 2. the extraction (27 Nov, ZombieExtract): once it's called, run for the helicopter's pad, fighting on the way
		local xf = Z.ext.botGoal
		local xg = if xf then xf(g, m) else nil
		if typeof(xg) == "Vector3" then s.goal = nil end
		-- 3. shop when it's quiet
		local calm = quiet(g, r.Position)
		local goal = s.goal
		if goal and (n - goal.t0 > 30) then s.failT[goal.kind .. (goal.id or "")] = n + 45; goal = nil; s.goal = nil end -- (couldn't get there)
		if not goal and not xg and calm and n >= s.shopT then
			s.shopT = n + 2.5 + math.random()
			goal = decide(g, m, s, pos)
			s.goal = goal
		end
		if typeof(xg) == "Vector3" then
			s.doing = "extract"
			if flat(xg - pos).Magnitude > 2.5 or math.abs(xg.Y - pos.Y) > 4.5 then wish = walkTo(xg, s.goalField) end
		elseif goal then
			s.doing = goal.why
			local d = flat(goal.at - pos).Magnitude
			if d > 3.6 or math.abs(goal.at.Y - pos.Y) > 4.5 then
				wish = walkTo(goal.at, s.goalField)
				goal.holdT = nil
			elseif not th or b.td > 14 then
				-- there: a beat to "hold Q", then buy
				goal.holdT = goal.holdT or (n + 0.45)
				if n >= (goal.holdT :: number) then
					local okA, errA = pcall(goal.act)
					if not okA then warn("[jankfire] zombies bot shop: " .. tostring(errA)) end
					s.failT[goal.kind .. (goal.id or "")] = n + 20 -- (bought or refused: not again straight away)
					s.goal = nil
					s.shopT = n + 1.5
				end
			end
		else
			-- 4. the post: get there, face the window, nail planks back between fights
			local post = s.post
			if post then
				local d = flat(post.at - pos).Magnitude
				local wi = post.wi
				local ext = Z.ext
				local nailing = false
				if wi and not th and ext.planks and ext.botBoard and (ext.planks(g, wi) or R.planks) < R.planks then
					local w = g.map.windows[wi]
					local at = floorAt(g, w.at.Position + w.n * 2.6 - Vector3.new(0, 1, 0))
					if at then
						nailing = true
						s.doing = "boards"
						if flat(at - pos).Magnitude > 3 then
							wish = walkTo(at, s.postFieldT)
						elseif n >= s.nailT then
							s.nailT = n + R.board + 0.15
							ext.botBoard(g, m, wi)
							r.CFrame = CFrame.lookAt(r.Position, r.Position + flat(w.at.Position - r.Position).Unit)
						end
					end
				end
				if not nailing then
					s.doing = if wi then "post window " .. wi else "post"
					if d > 2.5 then
						wish = walkTo(post.at, s.postFieldT)
					elseif not th then
						local lk = post.look
						if lk.Magnitude > 0.1 and r.CFrame.LookVector:Dot(lk) < 0.95 then
							r.CFrame = CFrame.lookAt(r.Position, r.Position + lk)
						end
					end
				end
			else
				s.doing = "with the squad"
				local ar = anchor
				if ar and flat(ar.Position - r.Position).Magnitude > 14 then
					local fl = live[1].field
					local p = if fl then Nav.downhill(g.nav, g.open, fl.d, pos) else nil
					wish = if p then flat(p - pos) else flat(ar.Position - r.Position)
				end
			end
		end
	end
	-- 2. a zombie: shoot it; one in its face: back off (sideways a bit), unless mid-revive
	if th then
		local close = b.td < (if th.kind > 0 then 16 else 11)
		if close and th.ph == "hunt" and not (reviving and b.td > 5.4) then
			local away = flat(r.Position - th.root.Position)
			if away.Magnitude > 1e-3 then
				away = away.Unit
				wish = away + Vector3.new(-away.Z, 0, away.X) * b.side * 0.6
				if math.random() < dt * 0.8 then b.side = -b.side end
			end
		end
		if b.reloadUntil > 0 and n >= b.reloadUntil then b.mag = (W[b.gun].mag :: number?) or 6; b.reloadUntil = 0 end
		if b.reloadUntil == 0 and n >= b.nextShot and (not reviving or b.td < 7.5) then
			local to = flat(th.root.Position - r.Position)
			if to.Magnitude > 0.1 then r.CFrame = CFrame.lookAt(r.Position, r.Position + to.Unit) end
			shoot(g, m, th)
		end
	elseif b.reloadUntil == 0 and b.mag < ((W[b.gun].mag :: number?) or 6) * 0.5 then
		b.reloadUntil = n + ((W[b.gun].reload :: number?) or 1.5) -- (reloads in a lull, like a person)
	elseif b.reloadUntil > 0 and n >= b.reloadUntil then
		b.mag = (W[b.gun].mag :: number?) or 6; b.reloadUntil = 0
	end
	-- wedged: hop and sidestep
	if n - b.chk > 1.1 then
		local moved = flat(r.Position - b.chkPos).Magnitude
		if wish.Magnitude > 0.1 and moved < 1.5 then
			b.stuck += 1; hum.Jump = true; b.sideT = n + 0.6; b.side = -b.side
			if b.stuck > 6 and s.goal then s.failT[s.goal.kind .. (s.goal.id or "")] = n + 40; s.goal = nil end
		else
			b.stuck = 0
		end
		b.chk, b.chkPos = n, r.Position
	end
	if n < b.sideT and wish.Magnitude > 0.1 then
		local a = b.side * 1.2
		local ca, sa = math.cos(a), math.sin(a)
		wish = Vector3.new(wish.X * ca - wish.Z * sa, 0, wish.X * sa + wish.Z * ca)
	end
	if wish.Magnitude > 0.1 and not reviving then
		hum.WalkSpeed = 27
		hum:Move(wish.Unit, false)
	else
		hum:Move(Vector3.zero, false)
	end
	local wk = X.botWalk(m)
	if wk then
		local v = flat(r.AssemblyLinearVelocity).Magnitude
		if v > 1.5 then
			if not wk.IsPlaying then wk:Play(0.2) end
			wk:AdjustSpeed(math.clamp(v / 16, 0.6, 1.8))
		elseif wk.IsPlaying then
			wk:Stop(0.25)
		end
	end
end

function ZombieBots.install(zombies: any)
	Z = zombies
	X = zombies.X
	local ext = zombies.ext
	ext.botStep = step
	ext.botGun = function(g: any, m: any, wid: string) setGun(g, m, wid) end
	-- (Studio's ServerStorage.JankZombies) bots: what each bot is up to
	local prevTest = ext.test
	ext.test = function(op: string, a: any, b: any): any
		local g = Z.game()
		if g and op == "bots" then
			local out = {}
			for _, m in g.members do
				if not m.bot then continue end
				local s = st(m)
				local r = X.fight().root(m.f)
				table.insert(out, string.format("%s c%d %s %s%s at %s post %s", m.name, m.c, m.bot.gun, s.doing,
					if m.f.alive then "" elseif m.down then " DOWN" else " OUT",
					if r then string.format("(%.0f,%.0f,%.0f)", r.Position.X, r.Position.Y, r.Position.Z) else "-",
					if s.post then tostring(s.post.wi or "ring") else "none"))
			end
			return out
		elseif g and op == "botc" then -- botc n: every bot's credits to n (a shopping test)
			for _, m in g.members do if m.bot then X.give(m, (tonumber(a) or 0) - m.c, "test") end end
			return true
		end
		return if prevTest then prevTest(op, a, b) else nil
	end
end

return ZombieBots
