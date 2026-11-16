--!strict
-- the utility slot on the server (key G; the items are in Shared.Items, the spec in roblox/docs/WEAPONS.md "Phase 2:
-- ITEMS"). the server owns all of it: which item you carry, its charges and clock, every throw, every bounce, the
-- fuse, every blast and who it hurts, the heal, the domes and every hit they stop, the clouds. a client only says "I
-- pressed G" (Item: id, where I threw from, where I looked) and everything in that is checked: a real item, yours,
-- alive, out of the hub, a charge left, 0.4 s since the last, the throw point near your real head and in clear sight
-- of it (the web server only checks the distance), your look a real direction, the velocity a throw inherits held to
-- what the server saw you move. nothing is ever reported back by a client: blast hits are the server's own.
-- what the clients see: player attributes Item / ItemN / ItemAt (the charge clock in server time), and ItemFx for the
-- world (throws, bounces, booms, clouds, domes, the medkit)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Items = require(Shared:WaitForChild("Items"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local ItemR = Remotes:WaitForChild("Item") :: RemoteEvent
local ItemFx = Remotes:WaitForChild("ItemFx") :: RemoteEvent

type Fighter = Rules.Fighter
local S = Items.S
local L = Items.list
local now = os.clock
local function stamp(t: number): number return workspace:GetServerTimeNow() + (t - now()) end -- (os.clock -> the clock clients share)

local Utility = {}
local Fight: any = nil

-- ------------------------------------------------------------------ who carries what
type St = { item: string, nextItem: string?, ic: Items.Ic?, save: { [string]: Items.Ic }, useT: number, heal: number, reverseUntil: number }
local st: { [Fighter]: St } = {}
local function stateOf(f: Fighter): St
	local s = st[f]
	if not s then s = { item = Items.DEFAULT, save = {}, useT = -math.huge, heal = 0, reverseUntil = -math.huge }; st[f] = s end
	return s
end
-- your charges right now (a gadget brings its own, kept across deaths and swaps)
local function charges(s: St): Items.Ic
	local it = L[s.item]
	if not s.ic or s.ic.i ~= s.item then s.ic = (it.carry and s.save[s.item]) or Items.fresh(s.item) end
	local c = s.ic :: Items.Ic
	if it.carry then s.save[s.item] = c end
	Items.tick(c, now())
	return c
end
local function publish(f: Fighter)
	if f.kind ~= "player" then return end
	local p = f.ref :: Player
	if not p.Parent then return end
	local s = stateOf(f)
	local c = charges(s)
	p:SetAttribute("Item", s.item)
	p:SetAttribute("ItemN", c.n)
	p:SetAttribute("ItemAt", if c.next > 0 then stamp(c.next) else 0)
	p:SetAttribute("ItemNext", s.nextItem)
end

-- the loadout picked an item (Loadout.luau). web selectItem: while you're dead or in the first 5 s of a life it's in
-- your hand at once (what you used this life stays used); later, from your next life. now = true: the hub re-arm
function Utility.pick(f: Fighter, id: string, at: boolean?)
	if not L[id] then return end
	local s = stateOf(f)
	if id == s.item then s.nextItem = nil
	elseif at or not f.alive or now() - f.spawnT < Items.SWAP then
		local it = L[id]
		s.ic = (it.carry and s.save[id]) or Items.swapped(charges(s), id, now())
		s.item, s.nextItem = id, nil
	else
		s.nextItem = id
	end
	publish(f)
end
function Utility.itemOf(f: Fighter): string return stateOf(f).item end

-- ------------------------------------------------------------------ the world: thrown items, domes, clouds
type Pr = { id: number, k: string, owner: Fighter?, uid: number?, p: Vector3, v: Vector3, r: number, bounce: number, grav: number, born: number, fuse: number, life: number, syncT: number,
	lp: Vector3?, hid: Fighter?, hsync: number } -- (the duck: where it was last tick, who it's homing on, when it last told everyone)
-- a rubber duck's black hole: where it is, whose it is, when it opens (born; later than now while it's about to open
-- on someone it stuck to), the one it rides (on), the next pulse, the next "where it is" to everyone
type Hole = { id: number, p: Vector3, owner: Fighter?, born: number, on: Fighter?, tick: number, syncT: number }
local holes: { Hole } = {}
local MAX_HOLE = 12
local projs: { Pr } = {}
local bubbles: { Items.Bubble } = {}
local clouds: { Items.Cloud } = {}
local nextId = 0
local MAX_PROJ, MAX_BUB, MAX_CLOUD = 40, 24, 30 -- (a room's caps: charges keep each player far under them)

local function uidOf(f: Fighter?): number? return if f and f.kind == "player" then (f.ref :: Player).UserId else nil end
local function alive(f: Fighter?): Fighter? return if f and table.find(Fight.all, f) then f else nil end

local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function cast(o: Vector3, r: number, move: Vector3): (number?, Vector3?)
	local map = workspace:FindFirstChild("Map")
	if not map then return nil, nil end
	mapParams.FilterDescendantsInstances = { map }
	local res = workspace:Spherecast(o, r, move, mapParams)
	if res then return res.Distance, res.Normal end
	return nil, nil
end

-- the frag's blast (web room.js explodeAt): everyone whose centre is in the radius, walls or not (web rule). owner =
-- the thrower (no damage to themselves, the whole shove); a thrower who has left: nobody's, judged from the blast point
local function explode(at: Vector3, owner: Fighter?, wid: string, w: Items.Proj)
	ItemFx:FireAllClients({ k = "boom", w = wid, p = at, r = w.radius })
	local R = w.radius :: number
	for _, t in table.clone(Fight.all) do
		if not t.alive then continue end
		local feet = Fight.feet(t)
		if not feet then continue end
		local c = feet + Vector3.new(0, Items.CENTRE, 0)
		local to = c - at
		local dist = to.Magnitude
		if dist > R then continue end
		local f = 1 - dist / R
		local dir = if dist > 0.1 * S then to.Unit else Vector3.yAxis
		local self = owner ~= nil and t == owner
		local k = (w.kb :: number) * (0.4 + 0.6 * f)
		local kb = dir * k + Vector3.new(0, (w.kbUp :: number) * f, 0)
		local dmg = if self then 0 else (w.dmg :: number) * (0.3 + 0.7 * f)
		Fight.hurt(t, dmg, if self then nil else owner, wid, false, kb, c, if owner then nil else at)
	end
end

local function dropProj(pr: Pr, at: Vector3?)
	local i = table.find(projs, pr)
	if i then table.remove(projs, i) end
	ItemFx:FireAllClients({ k = "pd", id = pr.id, p = at or pr.p })
end

local function smokeAt(at: Vector3)
	local sm = L.smoke
	nextId += 1
	local cl: Items.Cloud = { id = nextId, p = at, r = sm.r :: number, untilT = now() + (sm.dur :: number) }
	table.insert(clouds, cl)
	while #clouds > MAX_CLOUD do table.remove(clouds, 1) end
	ItemFx:FireAllClients({ k = "smoke", id = cl.id, p = cl.p, r = cl.r, left = sm.dur })
end

local function throw(f: Fighter, k: string, o: Vector3, d: Vector3, vel: Vector3)
	local w = Items.PROJ[k]
	local p0, v0 = Items.launch(k, o, d, vel)
	-- (not out through a wall the throw point is pressed against: start where the hand is clear)
	local gap = p0 - o
	local hd = cast(o, w.r, gap)
	if hd then p0 = o + gap.Unit * math.max(0, hd - 0.05) end
	nextId += 1
	local pr: Pr = { id = nextId, k = k, owner = f, uid = uidOf(f), p = p0, v = v0, r = w.r, bounce = w.bounce, grav = w.grav,
		born = now(), fuse = w.fuse, life = w.life, syncT = 0, hsync = 0 }
	table.insert(projs, pr)
	while #projs > MAX_PROJ do dropProj(projs[1]) end
	ItemFx:FireAllClients({ k = "ps", id = pr.id, w = k, p = p0, v = v0, o = pr.uid, fuse = w.fuse })
end

-- ------------------------------------------------------------------ the rubber duck (room.js duckFly / makeHole / tickHoles)
local D = Items.DUCK
local function centre(t: Fighter): Vector3?
	local feet = Fight.feet(t)
	return feet and feet + Vector3.new(0, Items.CENTRE, 0)
end
local function modelOf(t: Fighter?): Instance? return if t then Fight.model(t) else nil end
local function holeInfo(h: Hole, k: string): { [string]: any }
	return { k = k, id = h.id, p = h.p, o = uidOf(h.owner), on = modelOf(h.on), age = now() - h.born, R = D.holeR }
end
local function makeHole(at: Vector3, owner: Fighter?, on: Fighter?, delay: number)
	nextId += 1
	local h: Hole = { id = nextId, p = at, owner = owner, born = now() + delay, on = on, tick = 0, syncT = now() + 0.5 }
	table.insert(holes, h)
	while #holes > MAX_HOLE do
		local old = table.remove(holes, 1) :: Hole
		ItemFx:FireAllClients({ k = "he", id = old.id, p = old.p, quiet = true })
	end
	ItemFx:FireAllClients(holeInfo(h, "hs"))
end
-- who the duck may stick to or home on: not its thrower, nobody the thrower can't hurt, nobody behind a dome
local function duckSkips(owner: Fighter, t: Fighter): boolean
	if t == owner or not t.alive or not Fight.allow(owner, t) then return true end
	local tf, of = Fight.feet(t), Fight.feet(owner)
	return tf ~= nil and #bubbles > 0 and Items.blocks(bubbles, tf, of, nil)
end
-- in flight: stick to anyone it touched since last tick, else turn toward the nearest enemy ahead of it in plain
-- view. true = it stuck and is gone
local function duckFly(pr: Pr, owner: Fighter?, dt: number): boolean
	if not owner then return false end -- (a thrower who has left: it just flies)
	local reach = pr.r + D.pad
	local stuck: Fighter? = nil
	for _, t in Fight.all do
		if duckSkips(owner, t) then continue end
		local ft = Fight.feet(t)
		if not ft then continue end
		local bl, bh, hl, hh = Hitbox.boxes(ft, 1, reach)
		local from = pr.lp or pr.p
		local seg = pr.p - from
		for _, box in { { bl, bh }, { hl, hh } } do
			local lo, hi = box[1], box[2]
			local inside = pr.p.X > lo.X and pr.p.Y > lo.Y and pr.p.Z > lo.Z and pr.p.X < hi.X and pr.p.Y < hi.Y and pr.p.Z < hi.Z
			local swept = false
			if not inside and seg.Magnitude > 1e-3 then
				local d = Hitbox.rayBox(from, seg.Unit, lo, hi)
				swept = d ~= nil and d <= seg.Magnitude
			end
			if inside or swept then stuck = t; break end
		end
		if stuck then break end
	end
	if stuck then
		local c = centre(stuck) or pr.p
		dropProj(pr, c)
		makeHole(c, owner, stuck, D.stick)
		Rules.tagged(stuck, owner, "duck", now())
		ItemFx:FireAllClients({ k = "dstick", o = pr.uid, on = modelOf(stuck), onUid = uidOf(stuck) })
		return true
	end
	pr.lp = pr.p
	-- homing: the nearest enemy within homeR inside a 60 degree cone of where it's flying, in plain view
	local sp = pr.v.Magnitude
	local tgt: Fighter? = nil
	local bd = D.homeR
	if sp > D.minSpeed then
		for _, t in Fight.all do
			if duckSkips(owner, t) then continue end
			local c = centre(t)
			if not c then continue end
			local to = c - pr.p
			local d = to.Magnitude
			if d >= bd or d < 0.05 * S or to:Dot(pr.v) / (d * sp) < D.homeCos then continue end
			if Fight.castMap(pr.p, to.Unit, d) then continue end
			tgt, bd = t, d
		end
	end
	if tgt then pr.v = Items.steer(pr.v, (centre(tgt) :: Vector3) - pr.p, D.turn * dt) end
	-- every client steers it the same way toward the same person: tell them when that changes, and 10x a second
	pr.hsync -= dt
	if tgt ~= pr.hid or (tgt and pr.hsync <= 0) then
		pr.hid = tgt; pr.hsync = 0.1
		ItemFx:FireAllClients({ k = "dh", id = pr.id, p = pr.p, v = pr.v, h = modelOf(tgt) })
	end
	return false
end
-- every tick: a stuck duck's hole rides its victim's middle (till they die); everyone hears where it is twice a second;
-- every 0.1 s it pulls; at holeTime it pops
local function tickHoles(dt: number)
	local t = now()
	for _, h in table.clone(holes) do
		if h.on then
			local c = if h.on.alive then centre(h.on) else nil
			if c then h.p = c else h.on = nil end
		end
		if t >= h.syncT then h.syncT = t + 0.5; ItemFx:FireAllClients(holeInfo(h, "hu")) end
		local age = t - h.born
		if age < 0 then continue end -- (stuck: it opens on them in a moment)
		local owner = alive(h.owner)
		if age >= D.holeTime then
			local i = table.find(holes, h)
			if i then table.remove(holes, i) end
			ItemFx:FireAllClients({ k = "he", id = h.id, p = h.p, r = D.blastR })
			if not owner then continue end -- (whoever threw it has left: it pops harmlessly)
			for _, v in table.clone(Fight.all) do
				if not v.alive then continue end
				local c = centre(v)
				if not c then continue end
				local to = c - h.p
				local dist = to.Magnitude
				if dist > D.blastR then continue end
				local f = 1 - dist / D.blastR
				local dir = if dist > 0.1 * S then to.Unit else Vector3.yAxis
				local self = v == owner
				local k = D.blastKb * (0.4 + 0.6 * f)
				Fight.hurt(v, if self then 0 else D.blastDmg * f, if self then nil else owner, "duck", false,
					dir * k + Vector3.new(0, D.blastUp * f, 0), c)
			end
			continue
		end
		-- (every 0.1 s on the dot: the clock adds a pulse instead of restarting it, or one tick in six is lost to rounding
		-- and it pulses every 0.117 s: measured 26 crushes in 3 s, not 30)
		h.tick -= dt
		if h.tick > 1e-6 then continue end
		h.tick += D.pulse
		if not owner then continue end
		for _, v in table.clone(Fight.all) do
			if not v.alive or not Fight.allow(owner, v) then continue end
			local vf = Fight.feet(v)
			if vf and #bubbles > 0 and v ~= owner and Items.blocks(bubbles, vf, Fight.feet(owner), nil) then continue end -- (no pulling people out of a dome)
			if v == h.on then Fight.hurt(v, D.stuckDmg, owner, "duck", false, nil, h.p, nil, true); continue end -- (the one it's stuck to IS the middle)
			local c = centre(v)
			if not c then continue end
			local to = h.p - c
			local dist = to.Magnitude
			if dist > D.holeR or dist < 0.05 * S then continue end
			local ramp = math.min(1, dist / D.ramp)
			local sp = (D.pull * (1 - dist / D.holeR) + D.push0) * D.pulse * ramp
			-- (and a little lift each pulse: off their feet, ground friction can't hold them back)
			Fight.knock(v, to / dist * sp + Vector3.new(0, D.lift * ramp, 0), "duck")
			if v ~= owner then
				Rules.tagged(v, owner, "duck", t)
				if dist < D.near then Fight.hurt(v, D.nearDmg, owner, "duck", false, nil, c, nil, true) end
			end
		end
	end
end

local function domeAt(f: Fighter)
	local feet = Fight.feet(f)
	if not feet then return end
	local b = L.bubble
	nextId += 1
	local bub: Items.Bubble = { id = nextId, p = feet + Vector3.new(0, b.up :: number, 0), r = b.r :: number, untilT = now() + (b.dur :: number) }
	table.insert(bubbles, bub)
	while #bubbles > MAX_BUB do
		local old = table.remove(bubbles, 1) :: Items.Bubble
		ItemFx:FireAllClients({ k = "bubx", id = old.id })
	end
	ItemFx:FireAllClients({ k = "bub+", id = bub.id, p = bub.p, r = bub.r, left = b.dur, o = uidOf(f) })
end

-- the party popper (web popperUse + popperHit). the web client picks who's in its cone and the server re-checks with
-- a wide slack; here the server picks them itself at the pop: the cone from your eye along your look, everyone whose
-- middle (feet + 1 m) is within range and inside the cone (or right up close) where they are or were a moment ago, in
-- clear sight. each gets the shove along you -> them, feet to feet (no damage; a fall now is yours). your own recoil
-- is your client's (your movement), like the web game
local function popperUse(f: Fighter, eye: Vector3, dir: Vector3)
	local P = Items.POPPER
	local p = f.ref :: Player
	ItemFx:FireAllClients({ k = "popper", o = p.UserId, model = Fight.model(f), p = eye, d = dir })
	local myFeet = Fight.feet(f)
	if not myFeet then return end
	local cosC = math.cos(P.cone)
	local slackF = 0.3 * Fight.speed(f)
	for _, t in table.clone(Fight.all) do
		if t == f or not t.alive then continue end
		local inCone = false
		for _, ft in Fight.path(t) do
			local to = ft + Vector3.new(0, 1 * S, 0) - eye
			local dist = to.Magnitude
			if dist > P.range + slackF + 0.3 * Fight.speed(t) or dist < 1e-3 then continue end
			if dist <= P.close or to.Unit:Dot(dir) >= cosC then inCone = true; break end
		end
		if not inCone or not Fight.sees(eye, t) then continue end
		local tf = Fight.feet(t) :: Vector3
		local toT = tf - myFeet
		toT = if toT.Magnitude > 1e-3 then toT.Unit else dir
		Fight.hurt(t, 0, f, "popper", false, toT * P.kb + Vector3.new(0, P.kbUp, 0), tf + Vector3.new(0, Items.CENTRE, 0))
	end
end

-- the reverse card (web reverseUse; the swap itself is Fight.hurt's, asked through Fight.reflects below)
local function reverseUse(f: Fighter)
	local s = stateOf(f)
	s.reverseUntil = now() + Items.REVERSE.dur
	local p = f.ref :: Player
	p:SetAttribute("ReverseUntil", stamp(s.reverseUntil))
	ItemFx:FireAllClients({ k = "reverse", o = p.UserId, model = Fight.model(f), dur = Items.REVERSE.dur })
end
-- does t send this hit back (web hurt: an attacker who isn't you and is alive, while your card is up)
local function reflects(by: Fighter, t: Fighter): boolean
	local s = st[t]
	if not s or now() >= s.reverseUntil then return false end
	ItemFx:FireAllClients({ k = "reflect", o = uidOf(t), by = uidOf(by), model = Fight.model(t) })
	return true
end

-- every damage goes through Fight.hurt, and Fight.hurt asks this first (web hurt -> bubbleBlocks): a hit on someone in
-- a dome from anyone outside it (or, with nobody behind it, from a point outside it) is dropped, shove and all
local function blocked(by: Fighter?, t: Fighter, from: Vector3?): boolean
	if by == t or #bubbles == 0 then return false end
	local tf = Fight.feet(t)
	if not tf then return false end
	local af = if by then Fight.feet(by) else nil
	if by and not af then return false end
	if Items.blocks(bubbles, tf, af, from) then
		ItemFx:FireAllClients({ k = "bubhit", p = tf + Vector3.new(0, Items.CENTRE, 0) })
		return true
	end
	return false
end

-- does a cloud stand between a and c (bots' eyes and, later, the gadgets that need sight: web room.js smokeBlocks)
function Utility.smokeBlocks(a: Vector3, c: Vector3): boolean
	return #clouds > 0 and Items.smokeBlocks(clouds, a, c)
end

-- ------------------------------------------------------------------ the G press
local budget: { [Player]: { n: number, t: number } } = {}
local function spendMsg(p: Player): boolean
	local b, t = budget[p], now()
	if not b then b = { n = 20, t = t }; budget[p] = b end
	b.n = math.min(20, b.n + (t - b.t) * 8); b.t = t
	if b.n < 1 then return false end
	b.n -= 1
	return true
end
local function finiteV(v: any): boolean
	return typeof(v) == "Vector3" and Rules.finite(v.X) and Rules.finite(v.Y) and Rules.finite(v.Z) and v.Magnitude < 1e6
end

-- the velocity a throw inherits: your character's, held to 1.25 x the flat speed the server saw you move (+ 10 studs/s)
-- and a sane fall speed, so a faked velocity can't fling a grenade across the map
local function throwVel(f: Fighter): Vector3
	local r = Fight.root(f)
	if not r then return Vector3.zero end
	local v = r.AssemblyLinearVelocity
	local flat = Vector3.new(v.X, 0, v.Z)
	local lim = 1.25 * (Fight.seenSpeed(f) or 0) + 10
	if flat.Magnitude > lim then flat = flat.Unit * lim end
	return flat + Vector3.new(0, math.clamp(v.Y, -60 * S, 30 * S), 0)
end

local function use(p: Player, i: unknown, o: unknown, d: unknown)
	if not spendMsg(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(i) ~= "string" or not table.find(Items.ORDER, i) then return end
	local s = stateOf(f)
	local c = charges(s)
	local t = now()
	local it = L[i]
	-- not alive, in the hub (weapons-free), not your item, not on roblox yet, out of charges, too soon: the real count
	-- goes back so the HUD can't drift
	if not f.alive or p:GetAttribute("Zone") == "hub" or i ~= s.item or not it.live or c.n <= 0 or t - s.useT < Items.SPAM then
		publish(f)
		return
	end
	local eye = Fight.eye(f)
	if not eye then return end
	s.useT = t
	Items.spend(c, t)
	publish(f)
	-- where from: your real head unless the claimed point is close and in clear sight of it
	local from = eye
	if finiteV(o) then
		local off = (o :: Vector3) - eye
		if off.Magnitude <= Items.EYE and (off.Magnitude < 0.05 or not Fight.castMap(eye, off.Unit, off.Magnitude)) then from = o :: Vector3 end
	end
	local dir = if finiteV(d) and (d :: Vector3).Magnitude > 1e-3 then (d :: Vector3).Unit else Vector3.new(0, 0, -1)
	if it.proj then
		throw(f, it.proj, from, dir, throwVel(f))
	elseif i == "medkit" then
		s.heal = it.heal :: number
		ItemFx:FireAllClients({ k = "medkit", o = p.UserId, model = p.Character })
	elseif i == "bubble" then
		domeAt(f)
	elseif i == "popper" then
		popperUse(f, from, dir)
	elseif i == "reverse" then
		reverseUse(f)
	end
end

-- ------------------------------------------------------------------ every tick
local acc = 0
local STEP = 1 / 60 -- (the web server's tick)
local function tick(dt: number)
	local t = now()
	-- thrown items: fly, bounce (a correction to everyone on each real bounce, at most 20 a second; rolling along a
	-- floor sends nothing: every client rolls it the same way), go off on the fuse
	for _, pr in table.clone(projs) do
		local age = t - pr.born
		if pr.k == "duck" and duckFly(pr, alive(pr.owner), dt) then continue end
		local hit = Items.step(pr, dt, cast)
		if hit > 4 and t - pr.syncT > 0.05 then
			pr.syncT = t
			ItemFx:FireAllClients({ k = "pb", id = pr.id, p = pr.p, v = pr.v })
		end
		if age >= pr.fuse then
			dropProj(pr)
			if pr.k == "frag" then explode(pr.p, alive(pr.owner), "frag", Items.PROJ.frag)
			elseif pr.k == "smokegren" then smokeAt(pr.p)
			elseif pr.k == "duck" then makeHole(pr.p, pr.owner, nil, 0) end
		elseif age >= pr.life or pr.p.Y < -1500 then
			dropProj(pr)
		end
	end
	-- domes and clouds run out
	for i = #bubbles, 1, -1 do
		if t >= bubbles[i].untilT then
			local b = table.remove(bubbles, i) :: Items.Bubble
			ItemFx:FireAllClients({ k = "bubx", id = b.id })
		end
	end
	for i = #clouds, 1, -1 do if t >= clouds[i].untilT then table.remove(clouds, i) end end
	tickHoles(dt)
	-- the medkit: 26 HP a second until the 45 is spent, never past 100 (web tickItems: it doesn't eat overheal, and
	-- the heal keeps draining while you're full)
	for f, s in st do
		if s.heal > 0 then
			if not f.alive then s.heal = 0; continue end
			local a = math.min(s.heal, (L.medkit.healRate :: number) * dt)
			s.heal -= a
			if f.hp < (L.medkit.healMax :: number) then
				f.hp = math.min(L.medkit.healMax :: number, f.hp + a)
				Fight.syncHp(f)
			end
		end
		-- a charge came back: tell that player's HUD
		local c = s.ic
		if c and c.next > 0 and t >= c.next then publish(f) end
	end
end

-- a late joiner sees what's already out there
local function welcome(p: Player)
	local t = now()
	local list = {}
	for _, b in bubbles do table.insert(list, { k = "bub+", id = b.id, p = b.p, r = b.r, left = b.untilT - t }) end
	for _, c in clouds do table.insert(list, { k = "smoke", id = c.id, p = c.p, r = c.r, left = c.untilT - t }) end
	for _, h in holes do table.insert(list, holeInfo(h, "hs")) end
	for _, pr in projs do table.insert(list, { k = "ps", id = pr.id, w = pr.k, p = pr.p, v = pr.v, o = pr.uid, fuse = pr.fuse - (t - pr.born) }) end
	if #list > 0 then ItemFx:FireClient(p, { k = "list", list = list }) end
end

function Utility.init(fight: any)
	Fight = fight
	Fight.blocks = blocked
	Fight.smokeBlocks = Utility.smokeBlocks
	Fight.reflects = reflects
	-- a new life: the item you picked meanwhile, full charges (a gadget keeps its own), no heal left over
	fight.onSpawn(function(f: Fighter)
		local s = stateOf(f)
		if s.nextItem then s.item, s.nextItem = s.nextItem, nil end
		s.ic = nil
		s.heal = 0
		s.reverseUntil = -math.huge
		if f.kind == "player" then (f.ref :: Player):SetAttribute("ReverseUntil", nil) end
		publish(f)
	end)
	fight.onKill(function(info: any)
		local s = st[info.v]
		if s then
			s.heal = 0
			if s.reverseUntil > now() then -- (the card ends on death)
				s.reverseUntil = -math.huge
				if info.v.kind == "player" then (info.v.ref :: Player):SetAttribute("ReverseUntil", nil) end
				ItemFx:FireAllClients({ k = "reversex", o = uidOf(info.v) })
			end
		end
	end)
	ItemR.OnServerEvent:Connect(use)
	Players.PlayerAdded:Connect(welcome)
	Players.PlayerRemoving:Connect(function(p)
		budget[p] = nil
		local f = Fight.byPlayer[p]
		if f then st[f] = nil end
	end)
	RunService.Heartbeat:Connect(function(dt: number)
		acc = math.min(acc + dt, 0.25)
		while acc >= STEP do
			acc -= STEP
			tick(STEP)
		end
	end)
end

-- Studio play tests (TestHook): give a fighter an item this life with full charges, read the server's numbers
function Utility.test(f: Fighter, id: string?): any
	local s = stateOf(f)
	if id and L[id] then s.item, s.nextItem, s.ic = id, nil, Items.fresh(id); publish(f) end
	local c = charges(s)
	return { item = s.item, n = c.n, next = if c.next > 0 then c.next - now() else 0, heal = s.heal, hp = f.hp,
		reverse = math.max(0, s.reverseUntil - now()),
		projs = #projs, bubbles = #bubbles, clouds = #clouds, holes = #holes, cloud = if #clouds > 0 then clouds[#clouds].p else nil }
end

return Utility
