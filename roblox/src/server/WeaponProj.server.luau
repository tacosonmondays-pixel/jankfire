--!strict
-- weapons batch C (18 Nov 2026, WEAPONS.md "Chicken Rocket", "Peel Shooter", "Tennis Ball Launcher", "Snowball", "Blood
-- Cross"; the traced spec: side notes weapons-batchC-spec.md): the projectile weapons, flown by the SERVER. the client
-- sends the click (Throw remote: wid, eye, look); the server checks it, spawns the shot (a little along the look, pulled
-- back from a wall; + 0.35 of your own speed), flies it every Heartbeat (gravity, sphere casts against the map, bounces)
-- and decides every hit; clients replay the flight from its spawn (Fx "proj") and draw the bounces, hits and ends the
-- server sends ("proju", "projx"). kinds (the row's `proj`):
--   rocket: explodes on the first wall or body (radius, falloff, the shooter's own blast only shoves: the rocket jump)
--   peel: bonks a body (+ slip), bounces off walls, on the floor it leaves a peel for 12 s that trips the next one over it
--   ball: bounces up to 5 times off anything, each bounce +30% (the tennis ball)
--   (owner, 18 Nov 2026: "After a few bounces make it break, because otherwise it's out forever until it hits something")
--   every bouncing or rolling shot breaks after `bounces` (3 unless its row says more: the tennis ball's 5) and lives
--   MAX_LIFE s at most; the end is always sent (projx, brk = it broke), even if its step errors
--   snow: a hit adds frost (decaying), 4 freeze them solid for 2.4 s; a hit on someone frozen shatters them
--   blood: costs 12 HP a shot (thin and free when you can't pay), sticks in whoever it hits; 0.6 s later the cross
--     bursts out of them, 0.25 s after that it pops: the target and a small blast. a kill pays the HP back
-- weapons batch D (WEAPONS.md "Bowling Ball Launcher", "Slipper"; weapons-batchD-spec.md):
--   bowl: rolls along the floor in tiny hops and bowls over everyone in its way, on through them: 45 each and a shove
--     along its roll, once a person every 0.7 s (its thrower too, after 0.5 s); 2 people is a SPARE, 3 a STRIKE
--   slipper: a boomerang, one out at a time. out: it locks the nearest enemy ahead it can see and curves in (out for
--     0.45 s, 1 s while locked); then (or off a wall) it flies straight back to you through walls and you catch it.
--     30 and a shove on everyone it passes, both ways
--   arrow (the Bow, kind "bow": hold to draw, let go to fire): the draw c (the client's, never more than the time since
--     your last arrow allows) sets its speed 45..115 m/s and damage 30..70 (x1.5 above the shoulders); it stops at the
--     first wall. every arrow has a random tip, the next one rolled after each shot (BowTip on you): regular, power
--     (x1.8, faster), knockback (15, a huge shove), flame (15 + 5 every 0.5 s for 3 s), explosion (5.5 m: 50 at the
--     middle, you only get the shove), gas (10 + a 4.5 s cloud, 4 every 0.4 s within 5.5 m) and sleep (10 + 4 s asleep)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Dummies = require(script.Parent:WaitForChild("Dummies"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local SlipR = Remotes:WaitForChild("Slip") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local ThrowR = Remotes:FindFirstChild("Throw") :: RemoteEvent?
if not ThrowR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Throw"
	r.Parent = Remotes
	ThrowR = r
end
-- (the hold session's Bow draw, 18 Nov 2026) everyone else sees your Bow drawn from the player attribute BowDrawT: the
-- server time your draw began, nil when you're not drawing. your client says when it starts and stops (BowDraw true /
-- false, ProjClient); the arrow, a switch away, a death or a stun clear it here
local BowDrawR = Remotes:FindFirstChild("BowDraw") :: RemoteEvent?
if not BowDrawR then
	local r = Instance.new("RemoteEvent")
	r.Name = "BowDraw"
	r.Parent = Remotes
	BowDrawR = r
end

local W = Weapons.list
local S = Weapons.S
local now = os.clock
type Fighter = Rules.Fighter
type Proj = { id: number, wid: string, k: string, owner: Fighter, p: Vector3, v: Vector3, t0: number, b: number, thin: boolean?,
	hitT: { [Fighter]: number }?, victims: number?, phase: number?, tg: Fighter?, sync: number?, -- (batch D: who it hit when, the slipper's way out / back and its lock)
	charge: number?, tip: string?, -- (the Bow's draw and the arrow's tip)
	tgt: Fighter?, look: Vector3?, seekT: number?, -- (the Overdrive Rig's missiles: who it homes on, the salvo's aim)
	dmg: number? } -- (batch E: a thrown card's own damage, by its rank)

local projs: { Proj } = {}
local nextId = 0
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Include
local function sphere(o: Vector3, r: number, move: Vector3): RaycastResult?
	local map = workspace:FindFirstChild("Map")
	if not map or move.Magnitude < 1e-4 then return nil end
	params.FilterDescendantsInstances = { map }
	return workspace:Spherecast(o, r, move, params)
end
local function uid(f: Fighter): number? return if f.kind == "player" then (f.ref :: Player).UserId else nil end
local function holder(t: Fighter): Instance? return if t.kind == "player" then t.ref :: Player else Fight.model(t) end
local function callout(f: Fighter, text: string, dur: number)
	if f.kind == "player" then CalloutR:FireClient(f.ref :: Player, text, dur) end
end
local function centre(t: Fighter): Vector3? local ft = Fight.feet(t); return ft and ft + Vector3.new(0, 0.9 * S, 0) end
local function slip(t: Fighter, wid: string)
	if now() - t.slipT < Weapons.MSLIP.immune then return end -- (19 Nov 2026, the fling fix: one slip at a time)
	t.slipT = now()
	if t.kind == "player" then SlipR:FireClient(t.ref :: Player, wid) else Dummies.slip(t) end
end
local function fx(k: string, x: { [string]: any }) x.k = k; FxR:FireAllClients(x) end

-- ------------------------------------------------------------------ the fighters a segment passes through
local function sweep(pr: Proj, a: Vector3, b: Vector3, r: number): (Fighter?, number?, boolean)
	local d = b - a
	local L = d.Magnitude
	if L < 1e-4 then return nil, nil, false end
	local dir = d / L
	local best, bt, head = nil, math.huge, false
	local age = now() - pr.t0
	for _, t in Fight.all do
		if not t.alive then continue end
		if t == pr.owner and (age < 0.25 or pr.k == "blood" or pr.k == "slipper" or pr.k == "card" or (pr.k == "ball" and pr.b == 0) or (pr.k == "bowl" and age < 0.5) or pr.k == "rigmissile") then continue end
		-- (the bowling ball: once a person every 0.7 s; the slipper: once a person each way)
		local ht = pr.hitT and pr.hitT[t]
		if ht and (pr.k == "slipper" or now() - ht < 0.7) then continue end
		if t ~= pr.owner and not Fight.allow(pr.owner, t) then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= pr.owner.ref then continue end
		local ft = Fight.feet(t)
		if not ft then continue end
		local tt, hd = Hitbox.ray(a, dir, ft, Hitbox.distScale((ft - a).Magnitude), r, Hitbox.profile(Fight.model(t))) -- (the whole head)
		if tt and tt <= L and tt < bt then best, bt, head = t, tt, hd end
	end
	return best, (if best then bt else nil), head
end

-- ------------------------------------------------------------------ the chicken's blast (web explode)
local function blast(pr: Proj, at: Vector3)
	local w = W[pr.wid] :: any
	local R = w.radius
	fx("projx", { id = pr.id, p = at, x = true, r = R })
	for _, t in Fight.all do
		if not t.alive then continue end
		local c = centre(t)
		if not c then continue end
		local to = c - at
		local dist = to.Magnitude
		if dist > R then continue end
		local f = 1 - dist / R
		local dir = if dist < 0.1 * S then Vector3.yAxis else to.Unit
		local kb = dir * w.kb * (0.4 + 0.6 * f) + Vector3.new(0, 6 * S * f, 0)
		if t == pr.owner then
			Fight.hurt(t, 0, nil, pr.wid, false, kb * (w.selfKb or 1), at, nil, true) -- (your own: a shove, no damage)
		elseif Fight.allow(pr.owner, t) then
			Fight.hurt(t, w.dmg * (0.3 + 0.7 * f), pr.owner, pr.wid, false, kb, c, at)
		end
	end
end

-- ------------------------------------------------------------------ the peels on the floor
type Peel = { id: number, p: Vector3, owner: Fighter, t0: number }
-- (owner, 18 Nov 2026: "banans should disappear after a while": 30 s read as forever) how long a peel lies there
local PEEL_LIFE = 12
local peels: { Peel } = {}
local function dropPeel(pl: Peel, tripped: boolean)
	local i = table.find(peels, pl)
	if i then table.remove(peels, i) end
	fx("peelx", { id = pl.id, s = tripped })
end

-- ------------------------------------------------------------------ the snowball's frost
local frost: { [Fighter]: { n: number, t: number } } = setmetatable({}, { __mode = "k" }) :: any
local frozenUntil: { [Fighter]: number } = setmetatable({}, { __mode = "k" }) :: any

-- ------------------------------------------------------------------ the blood cross: stuck, then a burst, then a pop
type Cross = { owner: Fighter, t: Fighter, wid: string, dir: Vector3, thin: boolean, t0: number, phase: number }
local crosses: { Cross } = {}

-- ------------------------------------------------------------------ the Bow's tips: the blast, the burn, the gas, the sleep
local TIPS = { "regular", "power", "knockback", "flame", "explosion", "gas", "sleep" }
local bowTip: { [Fighter]: string } = setmetatable({}, { __mode = "k" }) :: any
local bowLast: { [Fighter]: number } = setmetatable({}, { __mode = "k" }) :: any
local function arrowBlast(pr: Proj, at: Vector3)
	local R = 5.5 * S
	fx("projx", { id = pr.id, p = at, x = true, r = R })
	for _, t in Fight.all do
		if not t.alive then continue end
		local c = centre(t)
		if not c then continue end
		local to = c - at
		local dist = to.Magnitude
		if dist > R then continue end
		local f = 1 - dist / R
		local dir = if dist < 0.1 * S then Vector3.yAxis else to.Unit
		local kb = dir * 30 * S * (0.4 + 0.6 * f) + Vector3.new(0, 6 * S * f, 0)
		if t == pr.owner then Fight.hurt(t, 0, nil, pr.wid, false, kb, at, nil, true)
		elseif Fight.allow(pr.owner, t) then Fight.hurt(t, 50 * (0.3 + 0.7 * f), pr.owner, pr.wid, false, kb, c, at) end
	end
end
type Burn = { t: Fighter, by: Fighter, wid: string, nextT: number, endT: number }
local burns: { Burn } = {}
local function burn(t: Fighter, by: Fighter, wid: string)
	local n = now()
	for _, b in burns do if b.t == t then b.by, b.endT = by, n + 3; return end end -- (a second flame tip: the 3 s start again)
	table.insert(burns, { t = t, by = by, wid = wid, nextT = n, endT = n + 3 })
	fx("burn", { model = Fight.model(t), dur = 3 })
end
type Cloud = { p: Vector3, by: Fighter, wid: string, nextT: number, endT: number }
local clouds: { Cloud } = {}
local function cloud(at: Vector3, by: Fighter, wid: string)
	local n = now()
	table.insert(clouds, { p = at, by = by, wid = wid, nextT = n, endT = n + 4.5 })
	fx("gas", { p = at, r = 5.5 * S, dur = 4.5 })
end
local function sleep(t: Fighter)
	local n = now()
	Rules.stun(t, 4, n) -- (no input, no shots, no swings)
	local h = holder(t)
	if h then
		local st = workspace:GetServerTimeNow() + 4
		h:SetAttribute("StunUntil", st)
		h:SetAttribute("SleepUntil", st)
	end
	fx("sleep", { model = Fight.model(t), dur = 4 })
end

-- ------------------------------------------------------------------ a body hit
local function hitBody(pr: Proj, t: Fighter, at: Vector3, head: boolean): boolean -- (true: the shot ends here)
	local w = W[pr.wid] :: any
	local d = if pr.v.Magnitude > 1e-3 then pr.v.Unit else Vector3.zAxis
	local own = t == pr.owner
	if pr.k == "rocket" or pr.k == "rigmissile" then blast(pr, at); return true
	elseif pr.k == "peel" then
		fx("projx", { id = pr.id, p = at, b = true })
		if not own then Fight.hurt(t, w.dmg, pr.owner, pr.wid, false, Vector3.new(d.X * w.kb, 3 * S, d.Z * w.kb), at) end
		if t.alive then slip(t, pr.wid) end
		return true
	elseif pr.k == "ball" then
		local k = 1 + 0.15 * pr.b
		local kb = Vector3.new(d.X * w.kb * k, w.kbUp, d.Z * w.kb * k)
		fx("projx", { id = pr.id, p = at, b = true, tb = pr.b })
		if own then Fight.knock(t, kb, pr.wid)
		else
			local ft = Fight.feet(t)
			local hs = head -- (the sweep's own head box: the whole visible head, Hitbox.profile)
			Fight.hurt(t, w.dmg * (1 + w.bonus * math.min(pr.b, w.bounces)) * (if hs then 1.5 else 1), pr.owner, pr.wid, hs, kb, at)
		end
		return true
	elseif pr.k == "snow" then
		fx("projx", { id = pr.id, p = at, b = true })
		if own then return true end
		local n = now()
		if frozenUntil[t] and n < frozenUntil[t] then
			-- frozen solid: this one shatters them
			fx("shatter", { model = Fight.model(t), p = centre(t) })
			Fight.hurt(t, math.max(t.hp, 1) + 1, pr.owner, pr.wid, false, nil, at)
			frozenUntil[t] = nil
			local h = holder(t)
			if h then h:SetAttribute("FrozenUntil", nil); h:SetAttribute("StunUntil", nil) end -- (the ice is gone with them)
			return true
		end
		local done = Fight.hurt(t, w.dmg, pr.owner, pr.wid, false, Vector3.new(d.X * w.kb, w.kbUp, d.Z * w.kb), at)
		if done > 0 and t.alive then
			local fr = frost[t] or { n = 0, t = n }
			fr.n = math.max(0, fr.n - math.floor((n - fr.t) / w.frostDecay)) + 1
			fr.t = n
			frost[t] = fr
			if fr.n >= w.freezeAt then
				fr.n = 0
				frozenUntil[t] = n + w.freeze
				Rules.stun(t, w.freeze, n) -- (no shots, swings or guard; their client stops: StunUntil)
				local h = holder(t)
				if h then h:SetAttribute("StunUntil", workspace:GetServerTimeNow() + w.freeze); h:SetAttribute("FrozenUntil", workspace:GetServerTimeNow() + w.freeze) end
				fx("freeze", { model = Fight.model(t), dur = w.freeze })
				callout(pr.owner, "FROZEN", 0.8)
			else
				fx("frost", { model = Fight.model(t), n = fr.n })
			end
		end
		return true
	elseif pr.k == "card" then
		-- (batch E: the Card Deck's thrown cards) one target each, its rank's damage, a little shove
		fx("projx", { id = pr.id, p = at, b = true })
		if own then return true end
		Fight.hurt(t, pr.dmg or w.dmg, pr.owner, pr.wid, false, Vector3.new(d.X * w.kb, 1 * S, d.Z * w.kb), at)
		return true
	elseif pr.k == "arrow" then
		local tip = pr.tip or "regular"
		if tip == "explosion" then arrowBlast(pr, at); return true end
		fx("projx", { id = pr.id, p = at, b = true, tip = tip })
		if own then return true end
		local c = pr.charge or 1
		local ft = Fight.feet(t)
		local hs = head -- (above the shoulders = the sweep's own head box: the whole visible head, Hitbox.profile)
		local dmg = (w.dmg + (w.dmgMax - w.dmg) * c) * (if hs then w.head else 1)
		local kb = Vector3.new(d.X * w.kb, w.kbUp, d.Z * w.kb)
		if tip == "power" then dmg *= 1.8
		elseif tip == "knockback" then dmg = 15; kb = Vector3.new(d.X * 60 * S, 15 * S, d.Z * 60 * S)
		elseif tip == "flame" then dmg = 15
		elseif tip == "gas" or tip == "sleep" then dmg = 10 end
		Fight.hurt(t, dmg, pr.owner, pr.wid, hs and (tip == "regular" or tip == "power"), kb, at)
		if t.alive then
			if tip == "flame" then burn(t, pr.owner, pr.wid)
			elseif tip == "sleep" then sleep(t) end
		end
		if tip == "gas" then cloud(at, pr.owner, pr.wid) end
		return true
	elseif pr.k == "bowl" then
		-- on through them: 45 and a shove along its roll each, then it rolls on a little slower
		local hv = Vector3.new(pr.v.X, 0, pr.v.Z)
		local dir = if hv.Magnitude > 1e-3 then hv.Unit else Vector3.new(d.X, 0, d.Z)
		local kb = dir * w.kb + Vector3.new(0, w.kbUp, 0)
		local hits = pr.hitT or {}
		pr.hitT = hits
		local first = hits[t] == nil
		hits[t] = now()
		if own then Fight.knock(t, kb, pr.wid)
		else
			Fight.hurt(t, w.dmg, pr.owner, pr.wid, false, kb, at)
			if first then
				pr.victims = (pr.victims or 0) + 1
				if pr.victims == 2 then callout(pr.owner, "SPARE", 1.0)
				elseif pr.victims == 3 then callout(pr.owner, "STRIKE", 1.2); fx("bowlstrike", { p = at }) end
			end
		end
		pr.v *= 0.85
		fx("proju", { id = pr.id, p = at, v = pr.v, h = true })
		return false
	elseif pr.k == "slipper" then
		local hits = pr.hitT or {}
		pr.hitT = hits
		hits[t] = now()
		if not own then Fight.hurt(t, w.dmg, pr.owner, pr.wid, false, Vector3.new(d.X * w.kb, w.kbUp, d.Z * w.kb), at) end
		fx("proju", { id = pr.id, p = at, v = pr.v, h = true })
		return false
	elseif pr.k == "blood" then
		if own then return false end
		fx("bcross", { id = pr.id, model = Fight.model(t), p = at, st = "stick", thin = pr.thin })
		table.insert(crosses, { owner = pr.owner, t = t, wid = pr.wid, dir = d, thin = pr.thin == true, t0 = now(), phase = 0 })
		return true
	end
	return true
end

-- ------------------------------------------------------------------ the slipper's flight (web room.js slipperTarget)
local outBy: { [Fighter]: Proj } = setmetatable({}, { __mode = "k" }) :: any
local rayParams = RaycastParams.new()
rayParams.FilterType = Enum.RaycastFilterType.Include
local function blocked(o: Vector3, d: Vector3): boolean
	local map = workspace:FindFirstChild("Map")
	if not map then return false end
	rayParams.FilterDescendantsInstances = { map }
	return workspace:Raycast(o, d, rayParams) ~= nil
end
-- the nearest enemy ahead it can see (the current lock wins unless another is clearly nearer); never one it already hit
local function slipperTarget(pr: Proj, w: any): Fighter?
	local s = pr.v.Magnitude
	if s < 1 then return nil end
	local cone = math.cos(math.rad(w.homeCone))
	local best, bs = nil, math.huge
	for _, t in Fight.all do
		if not t.alive or t == pr.owner or (pr.hitT and pr.hitT[t]) or not Fight.allow(pr.owner, t) then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= pr.owner.ref then continue end
		local c = centre(t)
		if not c then continue end
		local to = c - pr.p
		local dd = to.Magnitude
		local sc = if t == pr.tg then dd * 0.8 else dd
		if dd >= w.homeR or sc >= bs or dd < 1e-3 or to:Dot(pr.v) / (dd * s) < cone then continue end
		if blocked(pr.p, to) then continue end
		best, bs = t, sc
	end
	return best
end
-- turn v toward a point by at most maxA radians, keeping its speed
local function steer(v: Vector3, from: Vector3, to: Vector3, maxA: number): Vector3
	local s = v.Magnitude
	local want = to - from
	if want.Magnitude < 1e-3 or s < 1e-3 then return v end
	local a, b = v.Unit, want.Unit
	local ang = math.acos(math.clamp(a:Dot(b), -1, 1))
	local axis = a:Cross(b)
	if ang < 1e-4 or axis.Magnitude < 1e-6 then return v end
	return (CFrame.fromAxisAngle(axis.Unit, math.min(ang, maxA)) * a) * s
end
local function slipperGone(pr: Proj, caught: boolean)
	fx("projx", { id = pr.id, p = pr.p, c = if caught then true else nil })
	if outBy[pr.owner] == pr then outBy[pr.owner] = nil end
	if pr.owner.kind == "player" then (pr.owner.ref :: Player):SetAttribute("SlipperOut", nil) end
end
local function slipperStep(pr: Proj, w: any, dt: number, age: number): boolean
	local owner = pr.owner
	if not owner.alive or not table.find(Fight.all, owner) then slipperGone(pr, false); return false end
	if (pr.phase or 0) == 0 then
		local tg = if age < w.outLock then slipperTarget(pr, w) else nil
		if tg ~= pr.tg then pr.sync = math.min(pr.sync or 0, 0.03) end -- (a new lock: tell the clients soon)
		pr.tg = tg
		if tg then
			local c = centre(tg)
			if c then pr.v = steer(pr.v, pr.p, c, w.homeTurn * dt) end
		end
		local turn = age >= (if pr.tg then w.outLock else w.out)
		if not turn then
			local move = pr.v * dt
			local hit = sphere(pr.p, w.r, move)
			local to = if hit then pr.p + move.Unit * hit.Distance else pr.p + move
			local t, tt, head = sweep(pr, pr.p, to, w.r)
			if t and tt then hitBody(pr, t, pr.p + move.Unit * tt, head) end
			pr.p = to
			if hit then turn = true end
		end
		if turn then pr.phase = 1; pr.hitT = {}; pr.tg = nil; pr.sync = 0 end
	else
		-- back: straight at your eye, through walls, a little faster than you can run
		local eye = Fight.eye(owner)
		if not eye then slipperGone(pr, false); return false end
		local to = eye - Vector3.new(0, 0.3 * S, 0) - pr.p
		local dist = to.Magnitude
		if dist < 1.3 * S or age > w.life then slipperGone(pr, true); return false end
		local root = Fight.root(owner)
		local ov = if root then root.AssemblyLinearVelocity.Magnitude else 0
		pr.v = to / dist * math.max(w.back, ov + 10 * S)
		local nx = pr.p + pr.v * dt
		local t, tt, head = sweep(pr, pr.p, nx, w.r)
		if t and tt then hitBody(pr, t, pr.p + pr.v.Unit * tt, head) end
		pr.p = nx
	end
	pr.sync = (pr.sync or 0) - dt
	if (pr.sync :: number) <= 0 then pr.sync = 0.08; fx("proju", { id = pr.id, p = pr.p, v = pr.v }) end
	return true
end

-- ------------------------------------------------------------------ the click
local function fire(p: Player, wid: string, eye: Vector3, look: Vector3, claimC: unknown)
	local f = Fight.byPlayer[p]
	local w = W[wid] :: any
	if not f or not w or (w.kind ~= "proj" and w.kind ~= "bow") then return end
	if not table.find(Rules.loadoutOf(f), wid) or f.held ~= wid or not f.alive then return end
	local n = now()
	if w.kind == "bow" then p:SetAttribute("BowDrawT", nil) end -- (the let-go: the draw is over, whatever happens next)
	if n < f.staggerUntil then return end
	local seye = Fight.eye(f)
	if not seye then return end
	if (eye - seye).Magnitude > 4 * S then eye = seye end
	local thin = false
	if w.proj == "blood" then
		-- a shot costs `cost` HP (not damage: it can't kill you); with too little, a thin free shot on a longer cooldown
		thin = f.hp - w.cost < 1
		local cd = if thin then w.thin.cd else w.cd
		if not Rules.gate(f, wid, n, cd / 0.9 * 0.75) then return end
		if not thin then f.hp -= w.cost; Fight.syncHp(f) end
	else
		if w.proj == "slipper" and outBy[f] then return end -- (one slipper out at a time: catch it first)
		if not Rules.gate(f, wid, n, w.cd / 0.9 * 0.75) then return end -- (75 % of the cooldown: the web's lag slack)
	end
	Fight.shot(f, wid)
	local r = w.r
	local start = 0.8 * S
	local hit = sphere(eye, r, look * start)
	if hit then start = math.max(0, hit.Distance - 0.05) end
	local root = Fight.root(f)
	local inherit = if w.proj == "blood" or not root then Vector3.zero else root.AssemblyLinearVelocity * 0.35
	-- (the Bow: the draw, never more than the time since your last arrow allows; this arrow's tip, the next one rolled)
	local speed, charge, tip = w.speed, 1, nil
	if w.kind == "bow" then
		local claimed = if type(claimC) == "number" and claimC == claimC then claimC :: number else 0
		charge = math.max(0.15, math.min(1, claimed, (n - (bowLast[f] or -math.huge)) / (w.drawT * 0.85)))
		bowLast[f] = n
		tip = bowTip[f] or "regular"
		bowTip[f] = TIPS[math.random(#TIPS)]
		p:SetAttribute("BowTip", bowTip[f])
		speed = (w.speed + (w.speedMax - w.speed) * charge) * (if tip == "power" then 1.3 else 1)
	end
	nextId += 1
	local pr: Proj = { id = nextId, wid = wid, k = w.proj, owner = f, p = eye + look * start, v = look * speed + inherit, t0 = n, b = 0, thin = thin, charge = charge, tip = tip }
	table.insert(projs, pr)
	if w.proj == "slipper" then
		pr.phase, pr.sync = 0, 0.08
		outBy[f] = pr
		p:SetAttribute("SlipperOut", true) -- (your hand is empty till it's back: the hold, Arsenal)
	end
	fx("proj", { id = pr.id, w = wid, by = uid(f), model = Fight.model(f), p = pr.p, v = pr.v, g = w.grav, r = r, thin = thin, tip = tip })
	-- (owner, 18 Nov 2026) the Chicken Rocket's back-blast: every shot shoves you the other way to your aim (aim down to
	-- go up, behind you to dash), on the ground or in the air; no damage. your upward speed after it is capped
	-- (thrustCapUp). a shot whose blast will reach you (the floor at your feet, a wall in your face) is the old rocket
	-- jump on its own: no back-blast on top (both together threw you 60 m up in a test)
	-- (19 Nov 2026, the fling fix) none while you're slipping on marbles; and it never takes your run past thrustCapSide
	-- (a chain of level shots used to stack: nothing in the air slows you)
	if w.thrust and n - f.slipT >= Weapons.SLIP.time and not sphere(eye, w.r, look * w.radius) then
		local push = -look * w.thrust
		if Vector3.new(push.X, 0, push.Z).Magnitude > math.abs(push.Y) then push = Vector3.new(push.X, math.max(push.Y, w.thrustHop or 0), push.Z) end -- (a dash: off your feet)
		local rv = if root then root.AssemblyLinearVelocity else Vector3.zero
		local vy = rv.Y
		if push.Y > 0 then push = Vector3.new(push.X, math.clamp(w.thrustCapUp - vy, 0, push.Y), push.Z) end
		local vh, ph = Vector3.new(rv.X, 0, rv.Z), Vector3.new(push.X, 0, push.Z)
		local after = vh + ph
		local capS = w.thrustCapSide or math.huge
		if after.Magnitude > capS and after.Magnitude > 1e-3 then
			-- (never past the cap, nor past your speed now if you're already over it)
			local keep = after.Unit * math.max(capS, vh.Magnitude)
			ph = keep - vh
			push = Vector3.new(ph.X, push.Y, ph.Z)
		end
		Fight.knock(f, push, wid)
		p:SetAttribute("ACGrace", math.max(tonumber(p:GetAttribute("ACGrace")) or 0, n + 1.5)) -- (the anti-cheat: the launch is the server's)
		fx("thrust", { by = uid(f), p = eye - look * 1.2 * S, d = -look })
	end
end
;(ThrowR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, wid: unknown, eye: unknown, look: unknown, c: unknown)
	if (p:GetAttribute("Zone") == "hub" and p:GetAttribute("DevArms") ~= true) then return end
	if type(wid) ~= "string" or typeof(eye) ~= "Vector3" or typeof(look) ~= "Vector3" then return end
	local lk = look :: Vector3
	if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 or (eye :: Vector3).Magnitude > 1e6 then return end
	fire(p, wid, eye :: Vector3, lk.Unit, c)
end)

-- ------------------------------------------------------------------ the Card Deck's volleys (CardDeck.server picks the
-- cards and their aims; they fly here like every other shot). one spawn message for the whole fan
-- (the Overdrive Rig gadget, Rig.server: its salvo. n missiles 90 ms apart out of the left forearm's rack, each on one
-- of the targets it picked (in turn), up first, then homing: stepOne)
local RigVolley = Instance.new("BindableEvent")
RigVolley.Name = "JankRigVolley"
RigVolley.Parent = game:GetService("ServerStorage")
RigVolley.Event:Connect(function(p: Player, eye: Vector3, look: Vector3, models: { Instance })
	local f = Fight.byPlayer[p]
	local w = W.rig_missile :: any
	if not f or not f.alive or not w then return end
	local tgs: { Fighter } = {}
	for _, m in models do local t = Fight.of(m); if t then table.insert(tgs, t) end end
	local right = look:Cross(Vector3.yAxis)
	right = if right.Magnitude > 1e-3 then right.Unit else Vector3.xAxis
	for i = 1, 4 do
		task.delay((i - 1) * 0.09, function()
			if not f.alive then return end
			local from = (Fight.eye(f) or eye) - right * 1.2 * S * 0.5 + Vector3.new(0, 0.3 * S, 0)
			local up = (Vector3.yAxis + look * 0.35 + right * ((i - 2.5) * 0.18)).Unit
			-- (indoors the climb hit the ceiling and they all went off up there, 19 Nov test in the training hall: with no
			-- room overhead for the boost they leave mostly forward, still fanned)
			if Fight.castMap(from, up, w.speed * w.boost * 1.6 + 2) then up = (look + Vector3.yAxis * 0.2 + right * ((i - 2.5) * 0.12)).Unit end
			nextId += 1
			local pr: Proj = { id = nextId, wid = "rig_missile", k = "rigmissile", owner = f, p = from, v = up * w.speed, t0 = now(), b = 0,
				tgt = if #tgs > 0 then tgs[(i - 1) % #tgs + 1] else nil, look = look, seekT = 0 }
			table.insert(projs, pr)
			fx("proj", { id = pr.id, w = "rig_missile", by = uid(f), model = Fight.model(f), p = pr.p, v = pr.v, g = 0, r = w.r })
		end)
	end
end)

local Volley = Instance.new("BindableEvent")
Volley.Name = "JankCardVolley"
Volley.Parent = game:GetService("ServerStorage")
Volley.Event:Connect(function(p: Player, eye: Vector3, dirs: { Vector3 }, dmg: number, suit: string?)
	local f = Fight.byPlayer[p]
	local w = W.cards :: any
	if not f or not f.alive or not w then return end
	local ids, ps, vs = {}, {}, {}
	for _, d in dirs do
		local start = 0.8 * S
		local hit = sphere(eye, w.r, d * start)
		if hit then start = math.max(0, hit.Distance - 0.05) end
		nextId += 1
		local pr: Proj = { id = nextId, wid = "cards", k = "card", owner = f, p = eye + d * start, v = d * w.speed, t0 = now(), b = 0, dmg = dmg }
		table.insert(projs, pr)
		table.insert(ids, pr.id); table.insert(ps, pr.p); table.insert(vs, pr.v)
	end
	fx("projn", { w = "cards", by = uid(f), model = Fight.model(f), ids = ids, ps = ps, vs = vs, g = w.grav, r = w.r, suit = suit })
end)

-- ------------------------------------------------------------------ every Heartbeat
local MAX_LIFE, BOUNCES = 6, 3 -- (the hard cap on any shot's life, s; bounces before one breaks, unless its row says)
local function stepOne(pr: Proj, dt: number): boolean -- (false: it's gone)
	local w = W[pr.wid] :: any
	local age = now() - pr.t0
	if pr.k == "slipper" then return slipperStep(pr, w, dt, age) end
	if pr.k == "rigmissile" and age <= math.min(w.life or 5, MAX_LIFE) then
		-- (the Overdrive Rig's missile, web rigMissileStep) out of the rack straight up for `boost` s, speeding up; then it
		-- turns toward its target (re-seeking every 0.2 s: its own if still standing, else the nearest enemy ahead), at most
		-- `turn` rad/s, and goes off within `fuse` of it. the usual cast below still stops it on a wall or a body
		local spd = math.min(w.speedMax, w.speed + (w.speedMax - w.speed) * math.clamp(age / 0.8, 0, 1))
		local dir = if pr.v.Magnitude > 1e-3 then pr.v.Unit else Vector3.yAxis
		if age > w.boost then
			if age >= (pr.seekT or 0) then
				pr.seekT = age + 0.2
				local tg = pr.tgt
				if not tg or not tg.alive then
					tg = nil
					local best = math.huge
					for _, v in Fight.all do
						if v == pr.owner or not v.alive or not Fight.allow(pr.owner, v) then continue end
						local c = centre(v)
						if not c then continue end
						local to = c - pr.p
						local d = to.Magnitude
						if d < 75 * S and d > 0.1 and dir:Dot(to / d) > 0.2 and d < best then best, tg = d, v end
					end
					pr.tgt = tg
				end
			end
			local want = pr.look or dir
			local tg = pr.tgt
			local c = tg and centre(tg)
			if c then
				local to = c - pr.p
				if to.Magnitude < w.fuse then blast(pr, pr.p); return false end
				want = to.Unit
			end
			local ang = math.acos(math.clamp(dir:Dot(want), -1, 1))
			if ang > 1e-3 then dir = dir:Lerp(want, math.min(1, w.turn * dt / ang)).Unit end
		end
		pr.v = dir * spd
		pr.sync = (pr.sync or 0) - dt
		if (pr.sync :: number) <= 0 then pr.sync = 0.1; fx("proju", { id = pr.id, p = pr.p, v = pr.v }) end
	end
	if age > math.min(w.life or 5, MAX_LIFE) or not table.find(Fight.all, pr.owner) then
		fx("projx", { id = pr.id, p = pr.p, brk = true })
		return false
	end
	if pr.k == "ball" and age > 1 and pr.v.Magnitude < 0.5 * S then fx("projx", { id = pr.id, p = pr.p }); return false end
	pr.v -= Vector3.new(0, (w.grav or 0) * S * dt, 0)
	local move = pr.v * dt
	local hit = sphere(pr.p, w.r, move)
	local to = if hit then pr.p + move.Unit * hit.Distance else pr.p + move
	-- bodies first (a body in front of a wall is hit first)
	local t, tt, head = sweep(pr, pr.p, to, w.r)
	if t and tt then
		local at = pr.p + move.Unit * tt
		pr.p = at
		if hitBody(pr, t, at, head) then return false end
	end
	if hit then
		local nrm = hit.Normal
		pr.p = to + nrm * 0.02
		if pr.k == "rocket" or pr.k == "rigmissile" then blast(pr, pr.p); return false end
		if pr.k == "card" then fx("projx", { id = pr.id, p = pr.p }); return false end
		if pr.k == "arrow" then
			-- the first wall stops it: it sticks there (an explosion or gas tip goes off)
			if pr.tip == "explosion" then arrowBlast(pr, pr.p); return false end
			if pr.tip == "gas" then cloud(pr.p, pr.owner, pr.wid) end
			fx("projx", { id = pr.id, p = pr.p, n = nrm, stuck = true, tip = pr.tip })
			return false
		end
		if pr.k == "snow" then fx("projx", { id = pr.id, p = pr.p, b = true }); return false end
		if pr.k == "blood" then fx("bcross", { id = pr.id, p = pr.p, n = nrm, st = "wall" }); return false end
		if pr.k == "peel" and nrm.Y > 0.7 then
			-- on the floor: a peel stays there
			fx("projx", { id = pr.id, p = pr.p })
			nextId += 1
			local pl: Peel = { id = nextId, p = hit.Position, owner = pr.owner, t0 = now() }
			table.insert(peels, pl)
			while #peels > 40 do dropPeel(peels[1], false) end
			fx("peel", { id = pl.id, p = pl.p, n = nrm }) -- (n: the surface it lies flat on, ProjClient)
			return false
		end
		-- a bounce: the hit's normal part turned round (x bounce), the ball's slides lose a little
		local vn = pr.v:Dot(nrm)
		local tangent = pr.v - nrm * vn
		local e = w.bounce or 0
		if pr.k == "bowl" then
			-- (rolling: tiny hops off the floor, a little lost each touch; off a wall it comes back at 25 %. the clients
			-- keep it on the floor themselves, so only a wall is sent)
			if nrm.Y > 0.7 then
				pr.v = tangent * 0.995 - nrm * vn * e
				if math.abs(pr.v.Y) < 1.2 * S then pr.v = Vector3.new(pr.v.X, 0, pr.v.Z) end
			else
				pr.b += 1 -- (a wall: it breaks on the BOUNCES-th)
				if pr.b >= (w.bounces or BOUNCES) then fx("projx", { id = pr.id, p = pr.p, brk = true }); return false end
				pr.v = tangent - nrm * vn * e
				fx("proju", { id = pr.id, p = pr.p, v = pr.v })
			end
		elseif pr.k == "ball" then
			if math.abs(vn) > (w.minBounce or 3) * S then
				pr.b += 1
				if pr.b > w.bounces then fx("projx", { id = pr.id, p = pr.p, tb = pr.b, brk = true }); return false end
				pr.v = tangent * 0.94 - nrm * vn * e
				fx("proju", { id = pr.id, p = pr.p, v = pr.v, b = pr.b })
			else
				pr.v = tangent * 0.94 - nrm * vn * e
				if nrm.Y > 0.7 and math.abs(pr.v.Y) < 1.2 * S then pr.v = Vector3.new(pr.v.X, 0, pr.v.Z) end
			end
		else
			pr.b += 1 -- (anything else that bounces, the banana off a wall: it breaks on the BOUNCES-th)
			if pr.b >= (w.bounces or BOUNCES) then fx("projx", { id = pr.id, p = pr.p, brk = true }); return false end
			pr.v = tangent - nrm * vn * e
			fx("proju", { id = pr.id, p = pr.p, v = pr.v })
		end
	else
		pr.p = to
	end
	return true
end
RunService.Heartbeat:Connect(function(dt: number)
	for i = #projs, 1, -1 do
		local pr = projs[i]
		local ok, alive = pcall(stepOne, pr, dt)
		if not ok then
			-- (a step that errors used to drop the shot here without a word: every client kept flying it for ever)
			warn("[WeaponProj] step failed, " .. tostring(pr.k) .. ": " .. tostring(alive))
			pcall(fx, "projx", { id = pr.id, p = pr.p, brk = true, err = true })
		end
		if not ok or not alive then table.remove(projs, i) end
	end
	local n = now()
	-- peels: inert for 0.6 s, then the first body over one slips on it (its owner too); PEEL_LIFE at most
	for i = #peels, 1, -1 do
		local pl = peels[i]
		if n - pl.t0 > PEEL_LIFE then dropPeel(pl, false); continue end
		if n - pl.t0 < 0.6 then continue end
		for _, t in Fight.all do
			if not t.alive then continue end
			local ft = Fight.feet(t)
			if not ft then continue end
			local dl = ft - pl.p
			if math.abs(dl.X) < 0.85 * S and math.abs(dl.Z) < 0.85 * S and dl.Y > -0.4 * S and dl.Y < 0.5 * S then
				dropPeel(pl, true)
				if t ~= pl.owner and table.find(Fight.all, pl.owner) then Rules.tagged(t, pl.owner, "banana", n) end -- (a slip off a ledge is theirs)
				if t == pl.owner or Fight.allow(pl.owner, t) then slip(t, "banana") end
				break
			end
		end
	end
	-- crosses: 0.6 s stuck, then the burst, 0.25 s later the pop
	for i = #crosses, 1, -1 do
		local c = crosses[i]
		local w = W[c.wid] :: any
		if c.phase == 0 and n - c.t0 >= w.fuse then
			c.phase = 1
			fx("bcross", { model = Fight.model(c.t), p = centre(c.t), st = "erupt", thin = c.thin })
		elseif c.phase == 1 and n - c.t0 >= w.fuse + w.burst then
			table.remove(crosses, i)
			local at = centre(c.t)
			fx("bcross", { model = Fight.model(c.t), p = at, st = "boom", thin = c.thin })
			if not table.find(Fight.all, c.owner) or not at then continue end
			local before = c.owner.kills
			if c.t.alive then
				Fight.hurt(c.t, if c.thin then w.thin.dmg else w.dmg, c.owner, c.wid, false, Vector3.new(c.dir.X * w.kb, 4 * S, c.dir.Z * w.kb), at)
			end
			if not c.thin then
				for _, t in Fight.all do
					if t == c.t or t == c.owner or not t.alive or not Fight.allow(c.owner, t) then continue end
					local tc = centre(t)
					if not tc then continue end
					local to = tc - (at :: Vector3)
					local dist = to.Magnitude
					if dist > w.blastR then continue end
					local f = 1 - dist / w.blastR
					local dir = if dist > 1e-3 then to.Unit else Vector3.yAxis
					Fight.hurt(t, w.blastDmg * f, c.owner, c.wid, false, Vector3.new(dir.X * 9 * S * f, (3 + 3 * f) * S, dir.Z * 9 * S * f), tc)
				end
			end
			-- a kill pays the blood back
			if c.owner.kills > before and c.owner.alive then
				c.owner.hp = math.min(c.owner.maxHp or Weapons.HP, c.owner.hp + (if c.thin then w.thin.heal else w.cost))
				Fight.syncHp(c.owner)
				fx("bcross", { model = Fight.model(c.owner), st = "refund" })
			end
		end
	end
	-- (the Bow) burns: 5 every 0.5 s for 3 s; gas clouds: 4 every 0.4 s to everyone in 5.5 m but the archer
	for i = #burns, 1, -1 do
		local b = burns[i]
		if not b.t.alive or n >= b.endT then table.remove(burns, i); continue end
		if n >= b.nextT then
			b.nextT += 0.5
			if table.find(Fight.all, b.by) then Fight.hurt(b.t, 5, b.by, b.wid, false, nil, centre(b.t), nil, true) end
		end
	end
	for i = #clouds, 1, -1 do
		local cl = clouds[i]
		if n >= cl.endT or not table.find(Fight.all, cl.by) then table.remove(clouds, i); continue end
		if n >= cl.nextT then
			cl.nextT += 0.4
			for _, t in Fight.all do
				if t == cl.by or not t.alive or not Fight.allow(cl.by, t) then continue end
				local c = centre(t)
				if c and (c - cl.p).Magnitude <= 5.5 * S then Fight.hurt(t, 4, cl.by, cl.wid, false, nil, c, nil, true) end
			end
		end
	end
	-- frost and frozen marks fade (the attribute on a dummy's model / a player)
	for t, untilT in frozenUntil do
		if n >= untilT then
			frozenUntil[t] = nil
			local h = holder(t)
			if h then h:SetAttribute("FrozenUntil", nil) end
		end
	end
end)
-- the Bow's draw as others see it (BowDrawT): yours from the press; gone on the let-go, a switch away, a death, a stun
;(BowDrawR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, on: unknown)
	local f = Fight.byPlayer[p]
	local w = f and f.held and W[f.held] :: any
	if on == true and f and f.alive and w and w.kind == "bow" and (p:GetAttribute("Zone") ~= "hub" or p:GetAttribute("DevArms") == true) and now() >= f.staggerUntil then
		if p:GetAttribute("BowDrawT") == nil then p:SetAttribute("BowDrawT", workspace:GetServerTimeNow()) end
	else
		p:SetAttribute("BowDrawT", nil)
	end
end)
task.spawn(function()
	while true do
		task.wait(0.1)
		for _, p in Players:GetPlayers() do
			if p:GetAttribute("BowDrawT") == nil then continue end
			local f = Fight.byPlayer[p]
			local w = f and f.held and W[f.held] :: any
			if not f or not f.alive or not w or w.kind ~= "bow" or now() < f.staggerUntil then p:SetAttribute("BowDrawT", nil) end
		end
	end
end)
Players.PlayerRemoving:Connect(function(p)
		local f = Fight.byPlayer[p]
	if not f then return end
	for i = #projs, 1, -1 do if projs[i].owner == f then table.remove(projs, i) end end
	outBy[f] = nil
end)
