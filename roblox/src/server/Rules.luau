--!strict
-- the server's rules for step 2, as pure functions on plain tables (no Roblox calls), so the Lune tests run the real
-- thing: who may fire / swing / parry, which hits count, HP, kills, kill credit, the katana's growth. the server wires
-- them to the remotes (Combat.server.luau). stricter than the web server (roblox/docs/WEAPONS.md "Where the web
-- server trusts the client"): the server checks the held weapon, ammo / mag / reload, the fire rate from ITS HP, line
-- of sight, range, the melee cone and "a swing came first", and the parry window
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))

local Rules = {}
local W = Weapons.list
local P = Weapons.PARRY
local S = Weapons.S

Rules.SLACK = 3 * S -- studs of lag allowance on range and reach (the web game uses 6 m; positions here are fresher)
Rules.EYE_SLACK = 5 -- studs a claimed eye may be from where the server has your head (and nothing solid in between)
Rules.JITTER = 0.1 -- s: how much early a shot may arrive (network jitter) without being refused
Rules.SHOT_LATE = 0.6 -- s: a melee hit must come this soon after its swing

export type Ammo = { mag: number, reloadUntil: number }
export type Tag = { by: Fighter, w: string, t: number }
export type Swing = { t: number, w: string, hit: { [Fighter]: boolean } }
export type Fighter = {
	id: number, kind: string, name: string, ref: any,
	hp: number, alive: boolean, spawnT: number, diedT: number, held: string, equipT: number,
	ammo: { [string]: Ammo }, gate: { [string]: number },
	kat: number, parryT: number, parryN: number, staggerUntil: number,
	swing: Swing?, tag: Tag?, slipT: number, kills: number, deaths: number,
	parryYaw: number?, -- where you looked when you opened the guard (radians, Roblox yaw)
}

local nextId = 0
function Rules.newFighter(kind: string, name: string, ref: any): Fighter
	nextId += 1
	return {
		id = nextId, kind = kind, name = name, ref = ref,
		hp = Weapons.HP, alive = false, spawnT = -math.huge, diedT = -math.huge, held = "redline", equipT = -math.huge,
		ammo = {}, gate = {}, kat = 0, parryT = -math.huge, parryN = 0, staggerUntil = -math.huge,
		swing = nil, tag = nil, slipT = -math.huge, kills = 0, deaths = 0,
	}
end

-- (re)spawn: full HP, full mags, nothing left over from the last life
function Rules.spawn(f: Fighter, now: number)
	f.hp, f.alive, f.spawnT = Weapons.HP, true, now
	f.kat, f.parryT, f.staggerUntil, f.swing, f.tag = 0, -math.huge, -math.huge, nil, nil
	f.held, f.equipT = "redline", now
	for _, id in Weapons.loadout do
		local w = W[id]
		if w.mag then f.ammo[id] = { mag = w.mag, reloadUntil = 0 } end
		f.gate[id] = -math.huge
	end
end

local function finite(x: any): boolean return type(x) == "number" and x == x and x > -math.huge and x < math.huge end
Rules.finite = finite

local function inLoadout(w: any): boolean
	if type(w) ~= "string" then return false end
	return table.find(Weapons.loadout, w) ~= nil
end

-- the ammo, finishing a reload whose time has come
local function ammoOf(f: Fighter, wid: string, now: number): Ammo?
	local a = f.ammo[wid]
	if a and a.reloadUntil > 0 and now >= a.reloadUntil then a.mag = W[wid].mag :: number; a.reloadUntil = 0 end
	return a
end
Rules.ammoOf = ammoOf

-- a rate gate: refuse if it's too soon, else book the next slot. 10% under the real interval + a little early arrival
-- (jitter) is fine; idle time can't be banked for a burst (at most `JITTER` s of it)
function Rules.gate(f: Fighter, key: string, now: number, iv: number): boolean
	local nxt = f.gate[key] or -math.huge
	if now < nxt then return false end
	f.gate[key] = math.max(nxt, now - Rules.JITTER) + iv * 0.9
	return true
end

-- weapon swap (keys 1 2 3): cancels a reload, like the web game
function Rules.equip(f: Fighter, wid: any, now: number): string?
	if not inLoadout(wid) then return "not your weapon" end
	if not f.alive then return "dead" end
	if f.held == wid then return nil end
	if now - (f.gate.equip or -math.huge) < 0.15 then return "too fast" end
	f.gate.equip = now
	f.swing = nil -- a swing doesn't land after you've put the blade away
	local a = f.ammo[f.held]
	if a and a.reloadUntil > 0 and now < a.reloadUntil then a.reloadUntil = 0 end
	f.held, f.equipT = wid, now
	return nil
end

function Rules.reload(f: Fighter, wid: any, now: number): string?
	if not inLoadout(wid) or W[wid].kind ~= "hitscan" then return "not a gun" end
	if not f.alive then return "dead" end
	if f.held ~= wid then return "not held" end
	local a = ammoOf(f, wid, now)
	if not a then return "no ammo" end
	if a.reloadUntil > 0 then return "already reloading" end
	if a.mag >= (W[wid].mag :: number) then return "full" end
	a.reloadUntil = now + (W[wid].reload :: number) * 0.9 -- 10% slack: the client's clock starts a ping earlier
	return nil
end

-- one shot (one trigger pull: all its pellets). claimEye = where the client fired from, eye = where the server has it
function Rules.fire(f: Fighter, wid: any, now: number, eye: Vector3, claimEye: Vector3, eyeBlocked: boolean?): string?
	if not inLoadout(wid) or W[wid].kind ~= "hitscan" then return "not a gun" end
	local w = W[wid]
	if not f.alive then return "dead" end
	if f.held ~= wid then return "not held" end
	if now < f.staggerUntil then return "staggered" end
	if (claimEye - eye).Magnitude > Rules.EYE_SLACK or eyeBlocked then return "not from your head" end
	local a = ammoOf(f, wid, now)
	if not a then return "no ammo" end
	if a.reloadUntil > 0 then return "reloading" end
	if a.mag <= 0 then return "empty" end
	-- the rate comes from the SERVER's HP (a client can't claim low HP to make the Redline scream)
	if not Rules.gate(f, wid, now, 1 / Weapons.fireRate(w, f.hp)) then return "too fast" end
	a.mag -= 1
	return nil
end

-- how many pellets can really land at this distance (server/room.js maxPellets): stops "all 100 marbles hit" from far
function Rules.maxPellets(w: Weapons.Weapon, dist: number): number
	local pellets = w.pellets or 1
	if pellets <= 1 then return pellets end
	local dm = dist / S
	local R = (w.spread or 0) * dm * 0.7
	local ds = 1 + math.clamp((dm - 25) / 60, 0, 1) * 0.8
	local frac = if R > 0 then math.min(1, (2.4 * ds * ds) / (math.pi * R * R)) else 1
	return math.clamp(math.ceil(pellets * frac * 1.35 + 2), 1, pellets)
end

-- line of sight: can `from` see the target's head, chest or feet + 1 m. cast(origin, dir, len) -> something hit?
function Rules.sees(cast: (Vector3, Vector3, number) -> boolean, from: Vector3, feet: Vector3): boolean
	for _, up in { Weapons.BOX.bodyTop + 1, 3, 0.5 * S } do
		local v = feet + Vector3.new(0, up, 0) - from
		if v.Magnitude < 0.5 then return true end
		if not cast(from, v.Unit, v.Magnitude) then return true end
	end
	return false
end

export type HitCtx = { dist: number, speedF: number, speedT: number, los: boolean }

-- a hitscan hit on t from the shot f just fired: returns the reason it's refused, or nil + the (clamped) pellets
function Rules.hit(f: Fighter, t: Fighter, wid: string, n: any, h: any, _now: number, c: HitCtx): (string?, number, number)
	local w = W[wid]
	if t == f then return "yourself", 0, 0 end
	if not t.alive then return "already dead", 0, 0 end
	if not finite(n) or not finite(h) then return "bad count", 0, 0 end
	if c.dist > w.range + Rules.SLACK + 0.3 * (c.speedF + c.speedT) then return "out of range", 0, 0 end
	if not c.los then return "through a wall", 0, 0 end
	local nn = math.clamp(math.floor(n), 1, Rules.maxPellets(w, c.dist))
	local hh = math.clamp(math.floor(h), 0, nn)
	return nil, nn, hh
end

-- a melee swing (the click). the hits come at the animation's hit time, each checked against this swing
function Rules.swing(f: Fighter, wid: any, now: number): string?
	if not inLoadout(wid) or W[wid].kind ~= "melee" then return "not a melee weapon" end
	local w = W[wid]
	if not f.alive then return "dead" end
	if f.held ~= wid then return "not held" end
	if now < f.staggerUntil then return "staggered" end
	if now - f.parryT < P.win then return "guarding" end
	if not Rules.gate(f, "swing", now, w.cd :: number) then return "too fast" end
	f.swing = { t = now, w = wid, hit = {} }
	return nil
end

export type MeleeCtx = { dist: number, look: Vector3, to: Vector3, los: boolean, speedF: number, speedT: number }

-- a melee hit: needs a swing just before, the target in reach (incl. the katana's growth), in the cone and in sight
function Rules.meleeHit(f: Fighter, t: Fighter, wid: any, now: number, c: MeleeCtx): string?
	local sw = f.swing
	if not sw or sw.w ~= wid then return "no swing" end
	if now - sw.t > Rules.SHOT_LATE then return "swing too old" end
	if t == f then return "yourself" end
	if sw.hit[t] then return "already hit" end
	if not f.alive or not t.alive then return "dead" end
	if now < f.staggerUntil then return "staggered" end
	local w = W[wid]
	if c.dist > Weapons.reach(w, f.kat) + Rules.SLACK + 0.3 * (c.speedF + c.speedT) then return "out of reach" end
	if c.dist > 1.5 * S and c.to.Magnitude > 1e-3 and c.look.Magnitude > 1e-3 then
		local cosA = math.clamp(c.look.Unit:Dot(c.to.Unit), -1, 1)
		if math.acos(cosA) > (w.cone :: number) + 0.5 then return "outside the swing" end
	end
	if not c.los then return "through a wall" end
	sw.hit[t] = true
	return nil
end

-- right click with the katana out: opens the 0.35 s guard
function Rules.parryStart(f: Fighter, now: number, yaw: any): string?
	if not f.alive then return "dead" end
	if f.held ~= "katana" then return "no katana" end
	if now < f.staggerUntil then return "staggered" end
	if now - f.parryT < (P.win + P.cd) * 0.9 then return "cooldown" end
	if f.swing and now - f.swing.t < W.katana.hitT :: number then return "mid-swing" end
	f.parryT, f.parryN = now, 0
	f.parryYaw = if finite(yaw) then yaw else nil
	return nil
end

-- is a hit from direction `inc` (parrier -> source) parried? 0 no, 1 parried, 2 perfect. facing = the parrier's look
function Rules.parryAt(t: Fighter, inc: Vector3, facing: Vector3, now: number): number
	if not t.alive or t.held ~= "katana" then return 0 end
	local age = now - t.parryT
	if age < 0 or age > P.win + P.slack then return 0 end
	local len = inc.Magnitude
	local flat = Vector3.new(inc.X, 0, inc.Z)
	if len > 1e-6 and flat.Magnitude >= 0.3 * len then -- (from right above or below always counts)
		local ff = Vector3.new(facing.X, 0, facing.Z)
		if ff.Magnitude < 1e-6 then return 0 end
		local cosA = math.clamp(flat.Unit:Dot(ff.Unit), -1, 1)
		if math.deg(math.acos(cosA)) > P.arc / 2 then return 0 end
	end
	t.parryN += 1
	return if age <= P.perfect + P.slack then 2 else 1
end

-- a parried melee attacker: staggered and shoved away from the parrier (studs/s). returns the shove
function Rules.stagger(f: Fighter, away: Vector3, perfect: boolean, now: number): Vector3
	local mul = if perfect then P.perfectMul else 1
	f.staggerUntil = now + P.stagger * mul
	local flat = Vector3.new(away.X, 0, away.Z)
	local d = if flat.Magnitude > 1e-6 then flat.Unit else Vector3.zero
	return d * (P.shove * mul) + Vector3.new(0, P.shoveUp, 0)
end

-- spawn protection: 1.2 s after spawning a player can't be hurt by others (dummies can)
function Rules.protected(t: Fighter, by: Fighter?, now: number): boolean
	return t.kind == "player" and by ~= nil and by ~= t and now - t.spawnT < Weapons.FFA.protect
end

-- whoever hurt you last (10 s): a fall into the smog is their kill
function Rules.tagged(t: Fighter, by: Fighter, wid: string, now: number)
	if by ~= t then t.tag = { by = by, w = wid, t = now } end
end

export type KillInfo = { k: Fighter?, v: Fighter, w: string, via: string? }

-- the one place a fighter dies. credit: the attacker; a fall ("void") goes to whoever tagged you in the last 10 s, with
-- `via` = what they last hit you with. katana / parry kills grow the killer's katana (a void kill doesn't: web rule)
function Rules.kill(t: Fighter, by: Fighter?, wid: string, now: number): KillInfo
	t.alive, t.hp, t.diedT = false, 0, now
	t.deaths += 1
	t.kat = 0
	local k, via = by, nil
	if wid == "void" then
		k = nil
		if t.tag and now - t.tag.t <= 10 and t.tag.by ~= t then k, via = t.tag.by, t.tag.w end
	end
	if k == t then k = nil end
	if k then
		if t.kind ~= "dummy" then k.kills += 1 end -- (test dummies don't score, but they do feed the katana)
		if wid == "katana" or wid == "parry" then k.kat = math.min(W.katana.growMax :: number, k.kat + 1) end
	end
	t.tag = nil
	return { k = k, v = t, w = wid, via = via }
end

-- the one place HP drops. returns the damage done and the kill, if it killed
function Rules.damage(t: Fighter, amt: number, by: Fighter?, wid: string, now: number): (number, KillInfo?)
	if not t.alive or amt <= 0 or not finite(amt) then return 0, nil end
	if Rules.protected(t, by, now) then return 0, nil end
	if by then Rules.tagged(t, by, wid, now) end
	local done = math.min(amt, t.hp)
	t.hp -= amt
	if t.hp <= 0 then return done, Rules.kill(t, by, wid, now) end
	return done, nil
end

return Rules
