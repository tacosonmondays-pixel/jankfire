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
local Dummies = require(script.Parent:WaitForChild("Dummies"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(n: string): RemoteEvent return Remotes:WaitForChild(n) :: RemoteEvent end
local EquipR, FireR, ReloadR, SwingR, MeleeR, ParryR = remote("Equip"), remote("Fire"), remote("Reload"), remote("Swing"), remote("MeleeHit"), remote("Parry")
local ShotR, FxR, AmmoR, SlipR, PatchR, CalloutR = remote("Shot"), remote("Fx"), remote("Ammo"), remote("Slip"), remote("Patch"), remote("Callout")
local AimR = remote("Aim") -- right click with a scoped gun: the server times the scope itself (quick-scopes)

local W = Weapons.list
local S = Weapons.S
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
-- a parried shot: no damage; a perfect parry sends the same bullets back into the shooter, credited to the parrier
local function parriedShot(t: Fighter, f: Fighter, wid: string, n: number, h: number, pr: number, eye: Vector3)
	local from = chest(t) or eye
	FxR:FireAllClients({ k = "parry", model = Fight.model(t), by = uid(t), att = uid(f), pf = pr == 2, kind = "shot", from = from, to = eye })
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

-- eye = where the bullet's last leg started (the shooter's eye, or the last wall a Revolver bullet bounced off).
-- x = what the shot itself brings (the Fire handler): its damage multiplier (a fanned Revolver shot), a quick-scope
-- or no-scope claim. the dummies' shots bring none. the gimmicks are all judged here, from the server's own clock:
-- the Yeehaw's ramp, the Hat Trick's BURST!, the Second Opinion's quick-scope, the Sniper's lethal headshot, and the
-- shove (the direction is the server's shooter -> victim, not the client's word like the web game)
local function applyHitscan(f: Fighter, t: Fighter, wid: string, n: number, h: number, eye: Vector3, x: { mul: number?, qs: boolean?, ns: boolean? }?)
	local c = chest(t)
	if not c then return end
	local pr = Rules.parryAt(t, eye - c, Fight.facing(t), now())
	if pr > 0 then parriedShot(t, f, wid, n, h, pr, eye); return end
	local w = W[wid]
	local dmg = Weapons.damage(w, n, h) * (if x and x.mul then x.mul else 1)
	local extraKb = 0
	if w.ramp then
		local k = Rules.ramp(f, t, w, now())
		dmg *= 1 + w.ramp * k
		if k > 0 then callout(f, ("YEEHAW x%.2f"):format(1 + w.ramp * k), 0.8) end
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
	local done = Fight.hurt(t, dmg, f, wid, h > 0, kb, if h > 0 then feet + Vector3.new(0, Weapons.BOX.bodyTop + 1, 0) else c)
	-- a no-scope is a callout and nothing else: the hit landed, and the server's own clock says the scope was down
	if done > 0 and w.noscope and x and x.ns and f.aimT == nil then
		callout(f, ("NO SCOPE %dm"):format(math.floor(to.Magnitude / S + 0.5)), 1.0)
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
	if why == nil and f.held ~= before then
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

ReloadR.OnServerEvent:Connect(function(p: Player, wid: unknown)
	if not spend(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" then return end
	local why = Rules.reload(f, wid, now())
	if why and why ~= "full" and why ~= "already reloading" then ammoSync(p, f, wid, why) end
end)

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
	local why, mul = Rules.fire(f, wid, now(), seye, e, blocked, x.fan == true)
	if why then
		if W[wid] then ammoSync(p, f, wid, why) end
		return
	end
	Fight.shot(f, wid) -- (Stats.luau: one more attack for accuracy)
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

SwingR.OnServerEvent:Connect(function(p: Player, wid: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" then return end
	if Rules.swing(f, wid, now()) then return end
	Fight.shot(f, wid)
	FxR:FireAllClients({ k = "swing", model = Fight.model(f), w = wid, by = p.UserId })
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
			callout(t, if pr == 2 then "PERFECT PARRY!" else "PARRY!", 0.9)
			callout(f, "PARRIED", 0.8)
			continue
		end
		local kb = lk.Unit * (w.kb or 0) + Vector3.new(0, w.kbUp or 0, 0)
		Fight.hurt(t, w.dmg, f, wid, false, kb, tp)
	end
end)

AimR.OnServerEvent:Connect(function(p: Player, on: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if f then Rules.aim(f, on == true, now()) end
end)

ParryR.OnServerEvent:Connect(function(p: Player, yaw: unknown)
	if not spend(p) or holstered(p) then return end
	local f = Fight.byPlayer[p]
	if not f then return end
	if Rules.parryStart(f, now(), yaw) then return end
	FxR:FireAllClients({ k = "guard", model = Fight.model(f), by = p.UserId })
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
require(script.Parent:WaitForChild("RangeTest")).init(Fight) -- Cardboard Carl's: the pop-up target lane in the training hall
require(script.Parent:WaitForChild("Utility")).init(Fight) -- the item on G: charges, throws, blasts, domes, clouds, the medkit
require(script.Parent:WaitForChild("Loadout")).init(Fight) -- keys 1 2 3 + G + wraps, saved (before anyone spawns)
require(script.Parent:WaitForChild("TestHook")).init(Fight, Rules, Weapons) -- Studio play tests only: ServerStorage.JankTest
Fight.init()
