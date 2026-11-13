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
		Fight.hurt(f, Weapons.damage(W[wid], n, h), t, "parry", h > 0, nil, eye)
		callout(t, "PERFECT PARRY!", 0.9)
	else
		callout(t, "PARRY!", 0.7)
		callout(f, "BLOCKED", 0.7)
	end
end

local function applyHitscan(f: Fighter, t: Fighter, wid: string, n: number, h: number, eye: Vector3)
	local c = chest(t)
	if not c then return end
	local pr = Rules.parryAt(t, eye - c, Fight.facing(t), now())
	if pr > 0 then parriedShot(t, f, wid, n, h, pr, eye); return end
	local dmg = Weapons.damage(W[wid], n, h)
	if f.kind == "dummy" then dmg *= 0.7 end -- bots hit softer (web botDmg)
	local feet = Fight.feet(t) :: Vector3
	Fight.hurt(t, dmg, f, wid, h > 0, nil, if h > 0 then feet + Vector3.new(0, Weapons.BOX.bodyTop + 1, 0) else c)
end

-- ------------------------------------------------------------------ the marbles on the floor
type Patch = Marbles.Patch
local patches: { Patch } = {}
local nextPatch = 0
local lastPatch: { [Fighter]: number } = {}
local function patchInfo(pt: Patch): { any }
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
local trail: { [Fighter]: { { t: number, p: Vector3 } } } = {}
local function realSpeed(f: Fighter): number
	local r = Fight.root(f)
	if not r then return 0 end
	local v = r.AssemblyLinearVelocity
	local flat = Vector3.new(v.X, 0, v.Z).Magnitude
	local tr = trail[f]
	if not tr or #tr < 2 then return flat end
	local d, t0 = 0, nil
	for i = 2, #tr do
		if tr[i].t < now() - 0.3 then continue end
		t0 = t0 or tr[i - 1].t
		local a, b = tr[i - 1].p, tr[i].p
		local s = Vector3.new(b.X - a.X, 0, b.Z - a.Z).Magnitude
		if s < 1.5 * S then d += s end
	end
	local dt = if t0 then tr[#tr].t - t0 else 0
	return if dt < 0.15 then flat else math.max(flat, d / dt * 0.8)
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
	for _, f in Fight.all do -- the position trail (for realSpeed)
		local r = Fight.root(f)
		if not r or not f.alive then trail[f] = nil; continue end
		local tr = trail[f] or {}
		trail[f] = tr
		table.insert(tr, { t = n, p = r.Position })
		while #tr > 0 and tr[1].t < n - 0.45 do table.remove(tr, 1) end
	end
	for k in trail do if not table.find(Fight.all, k) then trail[k] = nil end end
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
EquipR.OnServerEvent:Connect(function(p: Player, wid: unknown)
	if not spend(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" then return end
	local before = f.held
	if Rules.equip(f, wid, now()) == nil and f.held ~= before then
		Fight.showWeapon(f)
		FxR:FireAllClients({ k = "equip", model = Fight.model(f), w = f.held })
	end
end)

ReloadR.OnServerEvent:Connect(function(p: Player, wid: unknown)
	if not spend(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" then return end
	local why = Rules.reload(f, wid, now())
	if why and why ~= "full" and why ~= "already reloading" then ammoSync(p, f, wid, why) end
end)

-- one trigger pull: (weapon, eye, pellet end points (<= 12, the tracers + where the marbles go), hits per victim)
FireR.OnServerEvent:Connect(function(p: Player, wid: unknown, eye: unknown, ends: unknown, hits: unknown)
	if not spend(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" or not finiteV(eye) then return end
	if not array(ends, 12, finiteV) then return end
	if not array(hits, 8, function(h: any): boolean
		return type(h) == "table" and typeof(h.m) == "Instance" and Rules.finite(h.n) and Rules.finite(h.h)
	end) then return end
	local seye = Fight.eye(f)
	if not seye then return end
	local e = eye :: Vector3
	local why = Rules.fire(f, wid, now(), seye, e)
	if why then
		if W[wid] then ammoSync(p, f, wid, why) end
		return
	end
	-- everyone else's tracers (the shooter drew its own already)
	for _, o in Players:GetPlayers() do
		if o ~= p then ShotR:FireClient(o, { by = p.UserId, model = p.Character, w = wid, ends = ends }) end
	end
	local seen: { [Fighter]: boolean } = {}
	local ff = Fight.feet(f) :: Vector3
	for _, h in hits :: { any } do
		local t = Fight.of(h.m)
		if not t or seen[t] then continue end
		seen[t] = true
		local tf = Fight.feet(t)
		if not tf then continue end
		local hwhy, n, hh = Rules.hit(f, t, wid, h.n, h.h, now(), {
			dist = (tf - ff).Magnitude, speedF = Fight.speed(f), speedT = Fight.speed(t), los = Fight.sees(e, t),
		})
		if hwhy then continue end
		applyHitscan(f, t, wid, n, hh, e)
		if not f.alive then break end -- a perfect parry can kill the shooter mid-volley
	end
	if W[wid].marbles then makePatch(f, e, ends :: { Vector3 }) end
end)

SwingR.OnServerEvent:Connect(function(p: Player, wid: unknown)
	if not spend(p) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" then return end
	if Rules.swing(f, wid, now()) then return end
	FxR:FireAllClients({ k = "swing", model = Fight.model(f), w = wid, by = p.UserId })
end)

-- the swing's hit time: (weapon, look direction, the victims the client found in the cone)
MeleeR.OnServerEvent:Connect(function(p: Player, wid: unknown, look: unknown, targets: unknown)
	if not spend(p) then return end
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

ParryR.OnServerEvent:Connect(function(p: Player)
	if not spend(p) then return end
	local f = Fight.byPlayer[p]
	if not f then return end
	if Rules.parryStart(f, now()) then return end
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
			if v.Parent then for _, id in Weapons.loadout do if W[id].mag then ammoSync(v, info.v, id, nil) end end end
		end)
	end
end)

Dummies.init(Fight, applyHitscan)
Fight.init()
