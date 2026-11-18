--!strict
-- JANKFIRE (Roblox) server, step 2: the weapons. every RemoteEvent here is checked (exploiters can fire any remote with
-- anything): types, finite numbers, array sizes, a per-player message budget, then Rules.luau decides (held weapon,
-- ammo / mag / reload, fire rate from the server's HP, line of sight, range, the melee cone and swing, parry timing).
-- the server owns HP, kills, the katana's growth and the marbles on the floor. movement stays the client's, so
-- knockback and slips go to the victim's client
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Marbles = require(Shared:WaitForChild("Marbles"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Verdict = require(script.Parent:WaitForChild("Verdict")) -- (weapons batch D: the Scales of Justice)
local Dummies = require(script.Parent:WaitForChild("Dummies"))
local Katana = require(script.Parent:WaitForChild("Katana")) -- (the katana's crit return, edge meter and slash wave: docs/KATANA.md)
local Zones = require(script.Parent:WaitForChild("Zones")) -- (training: no guard cooldown)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(n: string): RemoteEvent return Remotes:WaitForChild(n) :: RemoteEvent end
local EquipR, FireR, ReloadR, SwingR, MeleeR, ParryR = remote("Equip"), remote("Fire"), remote("Reload"), remote("Swing"), remote("MeleeHit"), remote("Parry")
local ShotR, FxR, AmmoR, SlipR, PatchR, CalloutR = remote("Shot"), remote("Fx"), remote("Ammo"), remote("Slip"), remote("Patch"), remote("Callout")
local AimR = remote("Aim") -- right click with a scoped gun: the server times the scope itself (quick-scopes)

local W = Weapons.list
local S = Weapons.S
local EDGE = Weapons.EDGE
local now = os.clock
type Fighter = Rules.Fighter

-- ------------------------------------------------------------------ input hygiene
local function finiteV(v: any): boolean
	return typeof(v) == "Vector3" and Rules.finite(v.X) and Rules.finite(v.Y) and Rules.finite(v.Z) and v.Magnitude < 1e6
end
-- a plain array of at most `max` entries, each passing `ok` (anything else: the whole message is dropped)
local function array(t: any, max: number, ok: (any) -> boolean): boolean
	if type(t) ~= "table" then return false end
	local n = 0
	for k, v in t do
		if type(k) ~= "number" or k ~= math.floor(k) or k < 1 or k > max then return false end
		if not ok(v) then return false end
		n += 1
	end
	return n <= max and #t == n
end
-- a per-player message budget for the combat remotes: 120 in the bank, +60 a second (the Redline's 22/s fits easily)
local budget: { [Player]: { n: number, t: number } } = {}
local function spend(p: Player): boolean
	local b = budget[p]
	local t = now()
	if not b then b = { n = 120, t = t }; budget[p] = b end
	b.n = math.min(120, b.n + (t - b.t) * 60); b.t = t
	if b.n < 1 then return false end
	b.n -= 1
	return true
end
Players.PlayerRemoving:Connect(function(p) budget[p] = nil end)

local function uid(f: Fighter): number? return if f.kind == "player" then (f.ref :: Player).UserId else nil end
local function chest(f: Fighter): Vector3? local r = Fight.root(f); return r and r.Position end
local function callout(f: Fighter, text: string, dur: number)
	if f.kind == "player" then CalloutR:FireClient(f.ref :: Player, text, dur) end
end
local function ammoSync(p: Player, f: Fighter, wid: string, why: string?)
	local a = Rules.ammoOf(f, wid, now())
	if a then AmmoR:FireClient(p, wid, a.mag, a.reloadUntil > 0 and math.max(0, a.reloadUntil - now()) or 0, why) end
end

-- ------------------------------------------------------------------ hitscan
-- a parried shot: no damage; a perfect parry sends the same bullets back into the shooter, credited to the parrier.
-- every one fills the parrier's edge meter (Katana.luau); n = the guard's count so far (clients play the first big)
local function parriedShot(t: Fighter, f: Fighter, wid: string, n: number, h: number, pr: number, eye: Vector3)
	local from = chest(t) or eye
	FxR:FireAllClients({ k = "parry", model = Fight.model(t), by = uid(t), att = uid(f), pf = pr == 2, kind = "shot", from = from, to = eye, n = t.parryN })
	Katana.charge(t, f, Weapons.damage(W[wid], n, h) * (if pr == 2 then EDGE.perfect else EDGE.block))
	if pr == 2 and f.alive then
		local back = Weapons.damage(W[wid], n, h)
		if W[wid].lethalHead and h > 0 then back = math.max(back, f.hp) end -- (a Sniper headshot stays lethal on its way home)
		Fight.hurt(f, back, t, "parry", h > 0, nil, eye)
		callout(t, "PERFECT PARRY!", 0.9)
	else
		callout(t, "PARRY!", 0.7)
		callout(f, "BLOCKED", 0.7)
	end
end

-- ------------------------------------------------------------------ weapons batch A (18 Nov 2026, WEAPONS.md)
-- the Water Pistol (web secondaries.js soak): every squirt that lands soaks them for soak.dur s. their own client runs
-- slower and slides (WeaponStates.client reads SoakUntil, the server clock's end time: workspace:GetServerTimeNow), and
-- everyone sees them drip. a dummy carries it on its model (drips only). refreshed at most every 0.45 s
local function wetHit(t: Fighter, w: Weapons.Weapon)
	local sk = w.soak :: any
	local m = Fight.model(t)
	if not m then return end
	local sNow = workspace:GetServerTimeNow()
	local holder: Instance = if t.kind == "player" then t.ref :: Player else m
	local old = holder:GetAttribute("SoakUntil")
	if type(old) == "number" and sNow + sk.dur - old < 0.45 then return end
	holder:SetAttribute("SoakUntil", sNow + sk.dur)
	if type(old) ~= "number" or old < sNow then FxR:FireAllClients({ k = "soak", model = m }) end
end

-- the Nail Gun (web primaries.js nailHit / pinTo): every nail that lands stays on its victim for nails.win s; once one
-- shooter has nails.n of them there, the victim is nailed to the wall behind them (along the shot, flat, within
-- nails.reach) for nails.dur s, or to the floor where they stand with no wall in reach, and can't be pinned again
-- until nails.safe s after. a player's own client holds them there (Body.pin, from PinAt / PinUntil); a dummy is
-- anchored. everyone sees the big nails (Fx "pin")
local nailLog: { [Fighter]: { { t: number, by: Fighter } } } = setmetatable({}, { __mode = "k" }) :: any
local pinEnd: { [Fighter]: number } = setmetatable({}, { __mode = "k" }) :: any
local function pinTo(t: Fighter, f: Fighter, w: Weapons.Weapon, dir: Vector3)
	local N = w.nails :: any
	local feet, m = Fight.feet(t), Fight.model(t)
	if not feet or not m then return end
	local flat = Vector3.new(dir.X, 0, dir.Z)
	local spot, nrm = feet, Vector3.zero
	if flat.Magnitude > 1e-3 then
		local hit = Fight.castMap(feet + Vector3.new(0, 1.1 * S, 0), flat.Unit, N.reach)
		if hit and math.abs(hit.Normal.Y) < 0.5 then
			nrm = hit.Normal
			local at = hit.Position + hit.Normal * N.off
			spot = Vector3.new(at.X, feet.Y + N.lift, at.Z)
		end
	end
	local n = now()
	pinEnd[t] = n + N.dur
	if t.kind == "player" then
		local p = t.ref :: Player
		p:SetAttribute("ACGrace", n + N.dur + 0.5) -- (the anti-cheat: this pull is the server's say)
		p:SetAttribute("PinAt", spot)
		p:SetAttribute("PinUntil", workspace:GetServerTimeNow() + N.dur)
	else
		local r = Fight.root(t)
		if r then
			r.Anchored = true
			r.CFrame = CFrame.new(spot + Vector3.new(0, Hitbox.ROOT_UP, 0)) * r.CFrame.Rotation
			task.delay(N.dur, function() if r.Parent then r.Anchored = false end end)
		end
	end
	FxR:FireAllClients({ k = "pin", model = m, at = spot, n = nrm, dur = N.dur, by = uid(f) })
	callout(f, "PINNED", 0.8)
end
local function nailHit(f: Fighter, t: Fighter, w: Weapons.Weapon, dir: Vector3)
	local N = w.nails :: any
	local n = now()
	local pe = pinEnd[t]
	if pe and n < pe + N.safe then return end -- (pinned now, or only just let go)
	local log = nailLog[t] or {}
	nailLog[t] = log
	while #log > 0 and (n - log[1].t > N.win or #log >= 24) do table.remove(log, 1) end
	table.insert(log, { t = n, by = f })
	local mine = 0
	for _, e in log do if e.by == f then mine += 1 end end
	if mine >= N.n then table.clear(log); pinTo(t, f, w, dir) end
end

-- eye = where the bullet's last leg started (the shooter's eye, or the last wall a Revolver bullet bounced off).
-- x = what the shot itself brings (the Fire handler): its damage multiplier (a fanned Revolver shot), a quick-scope
-- or no-scope claim. the dummies' shots bring none. the gimmicks are all judged here, from the server's own clock:
-- the Yeehaw's ramp, the Hat Trick's BURST!, the Second Opinion's quick-scope, the Sniper's lethal headshot, and the
-- shove (the direction is the server's shooter -> victim, not the client's word like the web game)
local function applyHitscan(f: Fighter, t: Fighter, wid: string, n: number, h: number, eye: Vector3, x: { mul: number?, qs: boolean?, ns: boolean? }?)
	local c = chest(t)
	if not c then return end
	-- a katana swing cutting it (the crit return, before the guard: you can't guard mid-swing anyway)
	if Rules.critAt(t, eye - c, Fight.facing(t), now()) and Fight.allow(f, t) then Katana.crit(t, f, wid, n, h, eye); return end
	local pr = Rules.parryAt(t, eye - c, Fight.facing(t), now())
	if pr > 0 then parriedShot(t, f, wid, n, h, pr, eye); return end
	local w = W[wid]
	local dmg = Weapons.damage(w, n, h, f.hp) * (if x and x.mul then x.mul else 1) -- (f.hp: the Redline's cut past 12 a second)
	local extraKb = 0
	if w.ramp then
		local k = Rules.ramp(f, t, w, now())
		dmg *= 1 + w.ramp * k
		if k > 0 then callout(f, ("CHAIN x%.2f"):format(1 + w.ramp * k), 0.8) end
	end
	if w.burst and Rules.burstHit(f, t, w, now()) then callout(f, "BURST!", 0.9) end
	if w.quick and x and Rules.quick(f, w, now(), x.qs == true) then
		dmg += w.qsDmg or 0
		extraKb = w.qsKb or 0
		callout(f, "QUICK SCOPE", 0.9)
	end
	if f.kind == "dummy" then dmg *= 0.7 end -- bots hit softer (web botDmg)
	if w.lethalHead and h > 0 and f.kind == "player" then dmg = math.max(dmg, t.hp) end -- the Sniper: a headshot always kills
	local feet = Fight.feet(t) :: Vector3
	local to = c - eye
	local kb = if to.Magnitude > 1e-3 then Weapons.gunKb(w, n, to.Unit, extraKb) else nil
	-- (a second form's hit is its weapon's: the Scythe's rifle kills with the Scythe, Weapons.base)
	local done = Fight.hurt(t, dmg, f, Weapons.base(wid), h > 0, kb, if h > 0 then feet + Vector3.new(0, Weapons.BOX.bodyTop + 1, 0) else c)
	-- a no-scope is a callout and nothing else: the hit landed, and the server's own clock says the scope was down
	if done > 0 and w.noscope and x and x.ns and f.aimT == nil then
		callout(f, ("NO SCOPE %dm"):format(math.floor(to.Magnitude / S + 0.5)), 1.0)
	end
	-- (weapons batch A) a squirt soaks them, a nail counts toward the pin
	if done > 0 and t.alive then
		if w.soak then wetHit(t, w) end
		if w.nails and to.Magnitude > 1e-3 then nailHit(f, t, w, to.Unit) end
	end
end

-- the Revolver's ricochets (the web server takes the shooter's word for them): walk the claimed bounce points with
-- the server's own rays. each one must be on the map, in sight of the one before, and the bullet must leave it the way
-- a bounce does (off the server's own surface normal). returns where the last leg starts, or nil: the path is made up
local function bounced(eye: Vector3, pts: { Vector3 }, final: Vector3, range: number): Vector3?
	local at, total = eye, 0
	local away: Vector3? = nil
	for _, b in pts do
		local v = b - at
		local len = v.Magnitude
		if len < 0.05 then return nil end
		local d = v.Unit
		if away and d:Dot(away) < 0.985 then return nil end
		local hit = Fight.castMap(at, d, len + 1.5)
		if not hit or (hit.Position - b).Magnitude > 1.5 then return nil end
		total += len
		away = d - 2 * d:Dot(hit.Normal) * hit.Normal
		at = hit.Position + hit.Normal * 0.05
	end
	local last = final - at
	if away and last.Magnitude > 0.05 and last.Unit:Dot(away) < 0.985 then return nil end
	if total + last.Magnitude > range + Rules.SLACK then return nil end
	return at
end

-- ------------------------------------------------------------------ the marbles on the floor
type Patch = Marbles.Patch
local patches: { Patch } = {}
local nextPatch = 0
local lastPatch: { [Fighter]: number } = {}
Players.PlayerRemoving:Connect(function(p)
	local f = Fight.byPlayer[p]
	if f then lastPatch[f] = nil end
end)
local function patchInfo(pt: Patch): { [string]: any }
	return { id = pt.id, c = pt.c, r = pt.r, n = pt.n, left = math.max(0, pt.untilT - now()), o = uid(pt.owner :: Fighter) }
end
local function dropPatch(pt: Patch)
	local i = table.find(patches, pt)
	if i then table.remove(patches, i); PatchR:FireAllClients({ op = "drop", id = pt.id }) end
end
local function castMap(o: Vector3, d: Vector3, len: number): (number?, Vector3?)
	local r = Fight.castMap(o, d, len)
	if r then return (r.Position - o).Magnitude, r.Normal end
	return nil, nil
end
local function makePatch(f: Fighter, eye: Vector3, ends: { Vector3 })
	local M = Weapons.MSLIP
	local t = now()
	if t - (lastPatch[f] or -math.huge) < M.cd then return end -- one patch per real shot
	lastPatch[f] = t
	local c, r, n = Marbles.patch(eye, ends, W.marbles.range, castMap)
	if not c or not r or not n then return end
	for _, old in Marbles.toDrop(patches, f) do dropPatch(old) end
	nextPatch += 1
	local pt: Patch = { id = nextPatch, c = c, r = r, n = n, owner = f, born = t, untilT = t + M.life }
	table.insert(patches, pt)
	PatchR:FireAllClients({ op = "add", p = patchInfo(pt) })
end

-- how fast you're really going over the marbles: what your character says, or what the server saw it move over the
-- last 0.3 s (x0.8 for jitter) if that's more, so a client can't cross claiming it stands still
local function realSpeed(f: Fighter): number
	local r = Fight.root(f)
	if not r then return 0 end
	local v = r.AssemblyLinearVelocity
	local flat = Vector3.new(v.X, 0, v.Z).Magnitude
	local seen = Fight.seenSpeed(f)
	return if seen then math.max(flat, seen * 0.8) else flat
end

local function slipsOn(t: Fighter, pt: Patch, n: number): boolean
	if not t.alive or n - t.slipT < Weapons.MSLIP.immune then return false end
	if t.kind == "player" and t ~= pt.owner and n - t.spawnT < Weapons.FFA.protect then return false end
	local r = Fight.root(t)
	if not r or math.abs(r.AssemblyLinearVelocity.Y) > 2 * S then return false end -- in the air
	local feet = Hitbox.feet(r.Position)
	if not Marbles.onPatch(pt.c, pt.r, feet, 0.15 * S) then return false end
	if realSpeed(t) <= Marbles.safeSpeed(1) then return false end
	local d = Vector3.new(feet.X - pt.c.X, 0, feet.Z - pt.c.Z)
	if d.Magnitude > 0.15 and Fight.castMap(pt.c + Vector3.new(0, 0.3 * S, 0), d.Unit, d.Magnitude) then return false end
	return true
end

local function slip(t: Fighter, pt: Patch, n: number)
	t.slipT = n
	if t.kind == "player" then
		SlipR:FireClient(t.ref :: Player, "marbles")
	else
		Dummies.slip(t)
	end
	local owner = pt.owner :: Fighter
	if owner and owner ~= t and table.find(Fight.all, owner) then Rules.tagged(t, owner, "marbles", n) end -- slip off a ledge = their kill
	local nn, nr, gone = Marbles.thin(pt.n, pt.r)
	pt.n, pt.r = nn, nr
	PatchR:FireAllClients({ op = "thin", id = pt.id, n = nn, r = nr, at = Fight.feet(t), by = uid(t) })
	if gone then dropPatch(pt) end
end

local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 1 / 30 then return end
	acc = 0
	local n = now()
	Fight.track(n) -- the position trail (marble speed, range / reach allowance)
	for _, pt in table.clone(patches) do
		if n > pt.untilT then dropPatch(pt); continue end
		if n - pt.born < Weapons.MSLIP.land then continue end -- still flying
		for _, t in Fight.all do
			if slipsOn(t, pt, n) then
				slip(t, pt, n)
				if not table.find(patches, pt) then break end
			end
		end
	end
	Dummies.tick(n)
end)

-- ------------------------------------------------------------------ the remotes
-- a swap. a second swap inside 0.15 s waits its turn instead of being lost (so client and server agree what's held)
local wantW: { [Player]: string } = {}
local function tryEquip(p: Player, wid: string)
	local f = Fight.byPlayer[p]
	if not f or wantW[p] ~= wid then return end
	local before = f.held
	local why = Rules.equip(f, wid, now())
	if why == "too fast" then task.delay(0.16, tryEquip, p, wid); return end
	-- (a Scythe switch refused, mid-swing or mid-shot: your client already turned it, so it's told what you hold)
	local hw = W[f.held]
	if why ~= nil and hw and hw.form and hw.form.to == wid then EquipR:FireClient(p, f.held) end
	if why == nil and f.held ~= before then
		p:SetAttribute("Spin", nil) -- (a Minigun put away stops spinning: Rules.equip)
		-- (the Scythe turned into its rifle or back: everyone's copy of it moves its blade and scope across, GunParts)
		local bw = W[before]
		if bw and bw.form and bw.form.to == f.held then p:SetAttribute("FormT", workspace:GetServerTimeNow()) end
		Fight.showWeapon(f)
		FxR:FireAllClients({ k = "equip", model = Fight.model(f), w = f.held })
	end
end
EquipR.OnServerEvent:Connect(function(p: Player, wid: unknown)
	if not spend(p) then return end
	if type(wid) ~= "string" or not W[wid] then return end
	wantW[p] = wid
	tryEquip(p, wid)
end)
Players.PlayerRemoving:Connect(function(p) wantW[p] = nil end)

ReloadR.OnServerEvent:Connect(function(p: Player, wid: unknown, hand: unknown)
	if not spend(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" then return end
	local hd = if hand == 2 then 2 else nil -- (Lefty & Righty: which hand)
	local why = Rules.reload(f, wid, now(), hd)
	if why and why ~= "full" and why ~= "already reloading" and W[wid] then ammoSync(p, f, Rules.handKey(W[wid], wid, hd), why) end
end)

-- ------------------------------------------------------------------ the server's own bullet (a fanned Revolver shot)
-- (owner, 18 Nov 2026: the Revolver should be "less accurate the longer you hold it") the fan's spread is rolled HERE and
-- the server fires the bullet itself, so a client can't make the fan a laser. it walks the map and everyone's boxes
-- where the shooter saw them (a round trip and an interpolation step back along the server's trail, +-0.1 s), bouncing
-- off walls the way Arsenal's bullets do, then tells everyone where it went (the shooter's own tracer comes from it)
local fanRng = Random.new()
local function seenAt(t: Fighter, lag: number): { Vector3 }
	local out = {}
	local n = now()
	local tr = Fight.trail[t]
	if lag <= 0.1 or not tr then
		local ft = Fight.feet(t)
		if ft then table.insert(out, ft) end
	end
	if tr then
		for i = #tr, 1, -1 do
			local age = n - tr[i].t
			if age > lag + 0.1 then break end
			if age >= lag - 0.1 then table.insert(out, Hitbox.feet(tr[i].p)) end
		end
	end
	return out
end
local function serverShot(p: Player, f: Fighter, wid: string, eye: Vector3, d: Vector3, mul: number)
	local w = W[wid]
	local ok, ping = pcall(function() return p:GetNetworkPing() end)
	local lag = math.clamp((if ok and type(ping) == "number" then ping else 0.1) + 0.08, 0.05, Fight.LAG)
	local cands: { { t: Fighter, spots: { Vector3 } } } = {}
	for _, t in Fight.all do
		if t == f or not t.alive then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= p then continue end -- (somebody else's range Carl isn't in this shooter's world)
		local spots = seenAt(t, lag)
		if #spots > 0 then table.insert(cands, { t = t, spots = spots }) end
	end
	local from, left, bounces = eye, w.range, w.ricochet or 0
	local path: { Vector3 }? = nil
	local who: Fighter?, head, best = nil, false, left
	while true do
		local mh = Fight.castMap(from, d, left)
		best = if mh then (mh.Position - from).Magnitude else left
		who, head = nil, false
		for _, c in cands do
			for _, ft in c.spots do
				local tt, hd = Hitbox.ray(from, d, ft, Hitbox.distScale((ft - from).Magnitude))
				if tt and tt < best then best, who, head = tt, c.t, hd end
			end
		end
		if who or not mh or bounces <= 0 or left - best <= 1 then break end
		bounces -= 1 -- off the wall (twice): the same bullet carries on with what's left of its range
		left -= best
		local at = from + d * best
		local pp: { Vector3 } = path or {}
		path = pp
		table.insert(pp, at)
		local nrm = (mh :: RaycastResult).Normal
		d = d - 2 * d:Dot(nrm) * nrm
		from = at + nrm * 0.05
	end
	local e = from + d * best
	for _, o in Players:GetPlayers() do
		ShotR:FireClient(o, { by = p.UserId, model = p.Character, w = wid, ends = { e }, path = path, fan = if o == p then true else nil })
	end
	Fight.shotFx(f, wid, { e }) -- (the match recorder keeps it for killcams and replays)
	local t = who
	if not t then return end
	local tf, ff = Fight.feet(t), Fight.feet(f)
	if not tf or not ff then return end
	local hwhy, n, hh = Rules.hit(f, t, wid, 1, if head then 1 else 0, now(), {
		dist = (tf - ff).Magnitude, speedF = Fight.speed(f), speedT = Fight.speed(t), los = true,
	})
	if hwhy then return end
	applyHitscan(f, t, wid, n, hh, from, { mul = mul })
end

-- one trigger pull: (weapon, eye, pellet end points (<= 12, the tracers + where the marbles go), hits per victim)
-- the hub is weapons-free: no shots, swings or guards there (Fight.holstered); training and matches only
local function holstered(p: Player): boolean return p:GetAttribute("Zone") == "hub" end
FireR.OnServerEvent:Connect(function(p: Player, wid: unknown, eye: unknown, ends: unknown, hits: unknown, opt: unknown)
	if not spend(p) or holstered(p) then return end
	-- opt: the shot's claims, each one checked: fan (a fanned Revolver shot: it only ever lowers the damage), path
	-- (where a Revolver bullet bounced), qs / ns (quick-scope, no-scope)
	local x: any = if type(opt) == "table" then opt else {}
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" or not finiteV(eye) then return end
	if not array(ends, 12, finiteV) then return end
	if not array(hits, 8, function(h: any): boolean
		return type(h) == "table" and typeof(h.m) == "Instance" and Rules.finite(h.n) and Rules.finite(h.h)
	end) then return end
	local seye = Fight.eye(f)
	if not seye then return end
	local e = eye :: Vector3
	-- the claimed eye must be a clear line from your real head (no firing from the far side of a wall)
	local off = e - seye
	local blocked = off.Magnitude > 0.05 and Fight.castMap(seye, off.Unit, off.Magnitude) ~= nil
	local hd = if x.hand == 2 then 2 else nil -- (Lefty & Righty: the right gun)
	local why, mul, fanSpread = Rules.fire(f, wid, now(), seye, e, blocked, x.fan == true, hd)
	if why then
		if W[wid] then ammoSync(p, f, Rules.handKey(W[wid], wid, hd), why) end
		return
	end
	Fight.shot(f, Weapons.base(wid)) -- (Stats.luau: one more attack for accuracy)
	if fanSpread then
		-- a fanned Revolver shot: the client's hits are ignored, the server rolls the spread round where it looked (its
		-- `look`, else the line to its first end point) and fires the bullet itself
		local en = ends :: { Vector3 }
		local look: Vector3? = if finiteV(x.look) and (x.look :: Vector3).Magnitude > 0.5 then (x.look :: Vector3).Unit
			elseif en[1] and (en[1] - e).Magnitude > 1e-3 then (en[1] - e).Unit else nil
		if look then serverShot(p, f, wid, e, Hitbox.spreadDir(look, fanSpread, fanRng:NextNumber(), fanRng:NextNumber()), mul) end
		return
	end
	-- a ricochet: the hits are judged from the last wall the bullet really bounced off (a made-up path hits nobody)
	local from: Vector3? = e
	local path: { Vector3 }? = nil
	if W[wid].ricochet and x.path ~= nil then
		from = nil
		local en = ends :: { Vector3 }
		if array(x.path, W[wid].ricochet :: number, finiteV) and #x.path > 0 and #en > 0 then
			from = bounced(e, x.path, en[1], W[wid].range)
			if from then path = x.path end
		end
	end
	-- everyone else's tracers (the shooter drew its own already)
	for _, o in Players:GetPlayers() do
		if o ~= p then ShotR:FireClient(o, { by = p.UserId, model = p.Character, w = wid, ends = ends, path = path }) end
	end
	Fight.shotFx(f, wid, ends :: any) -- (the match recorder keeps it for killcams and replays)
	local seen: { [Fighter]: boolean } = {}
	local ff = Fight.feet(f) :: Vector3
	local left = W[wid].pellets or 1 -- one shot's pellets in total, however many victims it claims
	for _, h in hits :: { any } do
		if left <= 0 or not from then break end
		local t = Fight.of(h.m)
		if not t or seen[t] then continue end
		seen[t] = true
		local tf = Fight.feet(t)
		if not tf then continue end
		-- line of sight and "was it aimed at them" both look back along the target's trail (Fight.LAG): the shooter
		-- fired at where they saw the target, which is where it was a ping ago
		local hwhy, n, hh = Rules.hit(f, t, wid, h.n, h.h, now(), {
			dist = (tf - ff).Magnitude, speedF = Fight.speed(f), speedT = Fight.speed(t), los = Fight.sees(from :: Vector3, t),
			aimed = Rules.aimed(W[wid], from :: Vector3, ends :: { Vector3 }, Fight.path(t)),
		})
		if hwhy then continue end
		-- head or body: for a one-bullet gun the server looks for itself (a claimed headshot that never crossed the head
		-- is paid as a body shot)
		if hh > 0 and (W[wid].pellets or 1) <= 1 and not Rules.headAimed(from :: Vector3, ends :: { Vector3 }, Fight.path(t)) then hh = 0 end
		n = math.min(n, left); hh = math.min(hh, n); left -= n
		applyHitscan(f, t, wid, n, hh, from :: Vector3, { mul = mul, qs = x.qs == true, ns = x.ns == true })
		if not f.alive then break end -- a perfect parry can kill the shooter mid-volley
	end
	if W[wid].marbles then makePatch(f, e, ends :: { Vector3 }) end
end)

SwingR.OnServerEvent:Connect(function(p: Player, wid: unknown, heavy: unknown, yaw: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" then return end
	-- (heavy: the knife's right-click stab; yaw: where you looked, the front of a katana swing's crit return)
	if Rules.swing(f, wid, now(), heavy == true, yaw) then return end
	Fight.shot(f, wid)
	FxR:FireAllClients({ k = "swing", model = Fight.model(f), w = wid, by = p.UserId, h = if heavy == true then true else nil,
		clip = if heavy == true then "stab_" .. wid else nil }) -- (clip: the stab others see, ThirdPerson.luau)
	Fight.shotFx(f, wid, nil, "swing")
end)

-- the swing's hit time: (weapon, look direction, the victims the client found in the cone)
MeleeR.OnServerEvent:Connect(function(p: Player, wid: unknown, look: unknown, targets: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" or not finiteV(look) then return end
	local lk = look :: Vector3
	if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 then return end
	if not array(targets, 6, function(x: any): boolean return typeof(x) == "Instance" end) then return end
	local eye, fr = Fight.eye(f), Fight.root(f)
	if not eye or not fr or not W[wid] or W[wid].kind ~= "melee" then return end
	local w = W[wid]
	for _, m in targets :: { Instance } do
		local t = Fight.of(m)
		local tr = t and Fight.root(t)
		if not t or not tr then continue end
		local tp = tr.Position -- feet + 1 m
		local to = tp - eye
		local why = Rules.meleeHit(f, t, wid, now(), {
			dist = to.Magnitude, look = lk.Unit, to = to, los = Fight.castMap(eye, to.Unit, to.Magnitude) == nil,
			speedF = Fight.speed(f), speedT = Fight.speed(t),
		})
		if why then continue end
		local pr = Rules.parryAt(t, fr.Position - tr.Position, Fight.facing(t), now())
		if pr > 0 then
			-- parried: no damage, the attacker staggers and gets shoved off (a fall now is the parrier's)
			local shove = Rules.stagger(f, fr.Position - tr.Position, pr == 2, now())
			Fight.knock(f, shove, "parry")
			Rules.tagged(f, t, "parry", now())
			FxR:FireAllClients({ k = "parry", model = Fight.model(t), by = uid(t), att = uid(f), pf = pr == 2, kind = "melee", st = f.staggerUntil - now(), from = tp })
			Katana.charge(t, f, if pr == 2 then EDGE.meleePerfect else EDGE.melee)
			callout(t, if pr == 2 then "PERFECT PARRY!" else "PARRY!", 0.9)
			callout(f, "PARRIED", 0.8)
			continue
		end
		-- the knife's heavy stab has its own numbers; from behind (web room.js: the victim's look . attacker->victim over
		-- 0.45) the knife does x3 and it counts as a headshot
		local sw = f.swing
		local hv = if sw and sw.heavy then w.heavy else nil
		local dmg = if hv then hv.dmg else w.dmg
		if w.verdict then dmg *= Verdict.mult(f, t) end -- (the Scales of Justice: as hard as they deserve, Verdict.luau)
		local hs = false
		if w.backstab then
			local face = Fight.facing(t)
			local flatF, toT = Vector3.new(face.X, 0, face.Z), Vector3.new(tp.X - fr.Position.X, 0, tp.Z - fr.Position.Z)
			if flatF.Magnitude > 1e-3 and toT.Magnitude > 1e-3 and flatF.Unit:Dot(toT.Unit) > 0.45 then dmg *= w.backstab; hs = true end
		end
		local kb = lk.Unit * (if hv then hv.kb else (w.kb or 0)) + Vector3.new(0, if hv then hv.kbUp else (w.kbUp or 0), 0)
		-- (weapons batch A) the Hand Slapper: straight away from you along the server's own attacker -> victim line, its
		-- up and down too (web radial), + kbUp
		local away = tp - fr.Position
		if w.radial and away.Magnitude > 1e-3 then kb = away.Unit * (w.kb or 0) + Vector3.new(0, w.kbUp or 0, 0) end
		local done = Fight.hurt(t, dmg, f, wid, hs, kb, tp)
		if done > 0 and w.slip and t.alive then -- (and onto their back: the marbles' slip)
			t.slipT = now()
			if t.kind == "player" then SlipR:FireClient(t.ref :: Player, wid) else Dummies.slip(t) end
		end
	end
end)

AimR.OnServerEvent:Connect(function(p: Player, on: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if f then Rules.aim(f, on == true, now()) end
end)

-- (weapons batch B) the Taser's click: (weapon, eye, look, the body under your crosshair). the server checks the eye
-- and the click (Rules.zap), takes the claimed body only if it's in reach, inside the darts' cone round the look and
-- in sight, else picks its own; then stuns it and chains through the soaked (web secondaries.js secTarget / zapOne)
local ZapR = Remotes:FindFirstChild("Zap") :: RemoteEvent?
if not ZapR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Zap"
	r.Parent = Remotes
	ZapR = r
end
local function chestOf(t: Fighter): Vector3? local ft = Fight.feet(t); return ft and ft + Vector3.new(0, Hitbox.ROOT_UP, 0) end
local function soakedNow(t: Fighter): boolean
	local m = Fight.model(t)
	local h: Instance? = if t.kind == "player" then t.ref :: Player else m
	local v = h and h:GetAttribute("SoakUntil")
	return type(v) == "number" and v > workspace:GetServerTimeNow()
end
local function stunOne(f: Fighter, t: Fighter, wid: string, s: number, dmg: number, up: number, at: Vector3?)
	Rules.stun(t, s, now())
	local m = Fight.model(t)
	local h: Instance? = if t.kind == "player" then t.ref :: Player else m
	if h then h:SetAttribute("StunUntil", workspace:GetServerTimeNow() + s) end
	if dmg > 0 and t ~= f then Fight.hurt(t, dmg, f, wid, false, if up > 0 then Vector3.new(0, up, 0) else nil, at) end
end
local function zapFrom(f: Fighter, wid: string, eye: Vector3, look: Vector3, claim: Fighter?)
	local w = W[wid]
	local Z = w.zap :: any
	local function fits(t: Fighter): number?
		if t == f or not t.alive or not Fight.allow(f, t) then return nil end
		if t.onlyFor ~= nil and t.onlyFor ~= f.ref then return nil end
		local c = chestOf(t)
		if not c then return nil end
		local to = c - eye
		local d = to.Magnitude
		if d < 1e-3 or d > w.range + Rules.SLACK then return nil end
		local allow = (w.cone or 0.1) + math.atan(Weapons.BOX.bodyR * 1.3 / d) + 0.04
		if math.acos(math.clamp(look:Dot(to.Unit), -1, 1)) > allow then return nil end
		if Fight.castMap(eye, to.Unit, d) then return nil end
		return d
	end
	local target: Fighter? = if claim and fits(claim) then claim else nil
	if not target then
		local bd = math.huge
		for _, t in Fight.all do
			local d = fits(t)
			if d and d < bd then target, bd = t, d end
		end
	end
	local links: { { Vector3 } } = {}
	local miss: Vector3? = nil
	if target then
		local tc = chestOf(target) :: Vector3
		table.insert(links, { eye, tc })
		stunOne(f, target, wid, Z.stun * (if soakedNow(target) then Z.wet else 1), w.dmg, w.kbUp or 0, tc)
		-- the chain: breadth-first from the target to everyone soaked within chainR, in sight, chainMax in all
		local seen: { [Fighter]: boolean } = { [target] = true, [f] = true }
		local queue, n = { target }, 1
		while #queue > 0 and n < Z.chainMax do
			local a = table.remove(queue, 1) :: Fighter
			local ca = chestOf(a)
			if not ca then continue end
			for _, t in Fight.all do
				if n >= Z.chainMax then break end
				if seen[t] or not t.alive or not soakedNow(t) or not Fight.allow(f, t) then continue end
				local ct = chestOf(t)
				if not ct then continue end
				local v = ct - ca
				if v.Magnitude > Z.chainR or (v.Magnitude > 1e-3 and Fight.castMap(ca, v.Unit, v.Magnitude)) then continue end
				seen[t] = true
				n += 1
				table.insert(queue, t)
				table.insert(links, { ca, ct })
				stunOne(f, t, wid, Z.chainStun, Z.chainDmg, 0, ct)
			end
		end
		if n > 2 then callout(f, ("%d LINKED"):format(n), 0.9) end
	else
		local h = Fight.castMap(eye, look, w.range)
		miss = if h then h.Position else eye + look * w.range
	end
	if soakedNow(f) then stunOne(f, f, wid, Z.self, 0, 0, nil) end -- (fired it soaked: it gets you too)
	FxR:FireAllClients({ k = "zap", by = uid(f), model = Fight.model(f), links = links, miss = miss })
end
(ZapR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, wid: unknown, eye: unknown, look: unknown, claim: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" or not W[wid] or not finiteV(eye) or not finiteV(look) then return end
	local lk = look :: Vector3
	if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 then return end
	local seye = Fight.eye(f)
	if not seye then return end
	local off = (eye :: Vector3) - seye
	if off.Magnitude > Rules.EYE_SLACK or (off.Magnitude > 0.05 and Fight.castMap(seye, off.Unit, off.Magnitude)) then return end
	if Rules.zap(f, wid, now()) then return end
	Fight.shot(f, wid)
	zapFrom(f, wid, eye :: Vector3, lk.Unit, Fight.of(claim))
end)

-- (weapons batch A) the Minigun's trigger: (true) the barrels start spinning up, (false) let go. the server keeps the
-- spin itself (Rules.spin: no shot before it's full) and everyone sees the barrels turn (the player's Spin attribute)
local SpinR = Remotes:FindFirstChild("Spin") :: RemoteEvent?
if not SpinR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Spin"
	r.Parent = Remotes
	SpinR = r
end
(SpinR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, on: unknown)
	if not spend(p) or holstered(p) or type(on) ~= "boolean" then return end
	local f = Fight.byPlayer[p]
	if not f then return end
	Rules.spin(f, on, now())
	p:SetAttribute("Spin", if on and f.spin ~= nil then true else nil)
end)

-- the guard: (yaw) right click down opens it, (yaw, "turn") while held its front follows your look, (yaw, false) the
-- let-go closes it (Rules: up to PARRY.hold s held, at least PARRY.win on a tap). everyone sees it go up and down
ParryR.OnServerEvent:Connect(function(p: Player, yaw: unknown, mode: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if not f then return end
	if mode == false then
		if Rules.parryStop(f, now()) then
			FxR:FireAllClients({ k = "guardEnd", model = Fight.model(f), by = p.UserId, at = (f.parryEnd :: number) - now() })
		end
		return
	elseif mode == "turn" then
		Rules.parryTurn(f, now(), yaw)
		return
	end
	if Rules.parryStart(f, now(), yaw, Zones.training(p)) then return end
	FxR:FireAllClients({ k = "guard", model = Fight.model(f), by = p.UserId, hold = Weapons.PARRY.hold })
end)

-- a late joiner gets the marbles already on the floor
Players.PlayerAdded:Connect(function(p: Player)
	local list = {}
	for _, pt in patches do table.insert(list, patchInfo(pt)) end
	if #list > 0 then PatchR:FireClient(p, { op = "list", list = list }) end
end)
Fight.onKill(function(info)
	if info.v.kind == "player" then
		local v = info.v.ref :: Player
		-- your mags fill on respawn (Rules.spawn); tell your client so its count matches
		task.delay(Weapons.FFA.respawn + 0.2, function()
			if v.Parent then for _, id in Rules.loadoutOf(info.v) do if W[id] and W[id].mag then ammoSync(v, info.v, id, nil) end end end
		end)
	end
end)

require(script.Parent:WaitForChild("Matches")).init(Fight) -- the hub, its pads and the matches (before anyone spawns)
Dummies.init(Fight, applyHitscan)
Katana.init(Fight, applyHitscan) -- the edge meter, the crit return's payout and the slash wave (+ ServerStorage.JankKatanaTest in Studio)
require(script.Parent:WaitForChild("RangeTest")).init(Fight) -- Cardboard Carl's: the pop-up target lane in the training hall
require(script.Parent:WaitForChild("Utility")).init(Fight) -- the item on G: charges, throws, blasts, domes, clouds, the medkit
require(script.Parent:WaitForChild("Loadout")).init(Fight) -- keys 1 2 3 + G + wraps, saved (before anyone spawns)
require(script.Parent:WaitForChild("TestHook")).init(Fight, Rules, Weapons) -- Studio play tests only: ServerStorage.JankTest
Fight.init()
