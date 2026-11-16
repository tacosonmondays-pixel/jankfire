--!strict
-- the server's rules for step 2, as pure functions on plain tables (no Roblox calls), so the Lune tests run the real
-- thing: who may fire / swing / parry, which hits count, HP, kills, kill credit, the katana's growth. the server wires
-- them to the remotes (Combat.server.luau). stricter than the web server (roblox/docs/WEAPONS.md "Where the web
-- server trusts the client"): the server checks the held weapon, ammo / mag / reload, the fire rate from ITS HP, line
-- of sight, range, the melee cone and "a swing came first", and the parry window
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))

local Rules = {}
local W = Weapons.list
local P = Weapons.PARRY
local S = Weapons.S

Rules.SLACK = 3 * S -- studs of lag allowance on range and reach (the web game uses 6 m; positions here are fresher)
Rules.EYE_SLACK = 5 -- studs a claimed eye may be from where the server has your head (and nothing solid in between)
Rules.JITTER = 0.1 -- s: how much early a shot may arrive (network jitter) without being refused
Rules.SHOT_LATE = 0.6 -- s: a melee hit must come this soon after its swing
Rules.AIM_PAD = 2 -- studs added round a target's boxes when the server re-checks where a shot pointed

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
	-- keys 1 2 3 (Loadout.luau): the weapons you carry this life, and the picks waiting for your next (re)arm
	loadout: { string }?, nextLoadout: { string }?,
	-- batch 3's guns: when each gun last fired, the Hat Trick's recent shots, the Yeehaw's chain, the Hat Trick's
	-- burst in flight, the last quick-scope paid out, when the scope went up (nil = not aiming)
	lastShot: { [string]: number }, shotLog: { [string]: { number } },
	lev: { to: Fighter, k: number, t: number }?, bst: { to: Fighter?, k: number, t0: number }?,
	qsT: number?, aimT: number?,
	-- a range Carl (RangeTest): the one runner who may hurt him (anything else that is not nil: nobody may)
	onlyFor: any?,
}

local nextId = 0
function Rules.newFighter(kind: string, name: string, ref: any): Fighter
	nextId += 1
	return {
		id = nextId, kind = kind, name = name, ref = ref,
		hp = Weapons.HP, alive = false, spawnT = -math.huge, diedT = -math.huge, held = "redline", equipT = -math.huge,
		ammo = {}, gate = {}, kat = 0, parryT = -math.huge, parryN = 0, staggerUntil = -math.huge,
		swing = nil, tag = nil, slipT = -math.huge, kills = 0, deaths = 0,
		lastShot = {}, shotLog = {},
	}
end

-- the weapons on your keys 1 2 3 (no loadout yet, or a dummy: the default three)
function Rules.loadoutOf(f: Fighter): { string }
	return f.loadout or Weapons.loadout
end

-- arm: take the picks waiting in nextLoadout (they never change mid-life on their own), full mags, slot 1 out.
-- every spawn does this; the hub also does it when the loadout screen closes
function Rules.arm(f: Fighter, now: number)
	if f.nextLoadout then f.loadout = f.nextLoadout end
	local lo = Rules.loadoutOf(f)
	f.held, f.equipT = lo[1], now
	f.swing = nil
	table.clear(f.lastShot); table.clear(f.shotLog)
	f.lev, f.bst, f.qsT, f.aimT = nil, nil, nil, nil
	table.clear(f.ammo) -- (nothing left over from weapons you no longer carry)
	for _, id in lo do
		local w = W[id]
		if w and w.mag then f.ammo[id] = { mag = w.mag, reloadUntil = 0 } end
		f.gate[id] = -math.huge
	end
end

-- (re)spawn: full HP, full mags, nothing left over from the last life
function Rules.spawn(f: Fighter, now: number)
	f.hp, f.alive, f.spawnT = Weapons.HP, true, now
	f.kat, f.parryT, f.staggerUntil, f.swing, f.tag = 0, -math.huge, -math.huge, nil, nil
	Rules.arm(f, now)
end

local function finite(x: any): boolean return type(x) == "number" and x == x and x > -math.huge and x < math.huge end
Rules.finite = finite

-- is this one of YOUR weapons this life (anything else is refused, whatever the client sends)
local function inLoadout(f: Fighter, w: any): boolean
	if type(w) ~= "string" then return false end
	return table.find(Rules.loadoutOf(f), w) ~= nil
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
	if not inLoadout(f, wid) then return "not your weapon" end
	if not f.alive then return "dead" end
	if f.held == wid then return nil end
	if now - (f.gate.equip or -math.huge) < 0.15 then return "too fast" end
	f.gate.equip = now
	f.swing = nil -- a swing doesn't land after you've put the blade away
	local a = f.ammo[f.held]
	if a and a.reloadUntil > 0 and now < a.reloadUntil then a.reloadUntil = 0 end
	f.held, f.equipT = wid, now
	f.aimT = nil -- (the sights come down with the swap)
	return nil
end

function Rules.reload(f: Fighter, wid: any, now: number): string?
	if not inLoadout(f, wid) or W[wid].kind ~= "hitscan" then return "not a gun" end
	if not f.alive then return "dead" end
	if f.held ~= wid then return "not held" end
	local a = ammoOf(f, wid, now)
	if not a then return "no ammo" end
	if a.reloadUntil > 0 then return "already reloading" end
	if a.mag >= (W[wid].mag :: number) then return "full" end
	a.reloadUntil = now + (W[wid].reload :: number) * 0.9 -- 10% slack: the client's clock starts a ping earlier
	return nil
end

-- one shot (one trigger pull: all its pellets). claimEye = where the client fired from, eye = where the server has it.
-- returns why it's refused (or nil) and what this shot's damage is multiplied by (the Revolver's fanned shots pay less)
function Rules.fire(f: Fighter, wid: any, now: number, eye: Vector3, claimEye: Vector3, eyeBlocked: boolean?, claimFan: boolean?): (string?, number)
	if not inLoadout(f, wid) then return "not your weapon", 1 end
	if W[wid].kind ~= "hitscan" then return "not a gun", 1 end
	local w = W[wid]
	if not f.alive then return "dead", 1 end
	if f.held ~= wid then return "not held", 1 end
	if now < f.staggerUntil then return "staggered", 1 end
	if (claimEye - eye).Magnitude > Rules.EYE_SLACK or eyeBlocked then return "not from your head", 1 end
	local a = ammoOf(f, wid, now)
	if not a then return "no ammo", 1 end
	if a.reloadUntil > 0 then return "reloading", 1 end
	if a.mag <= 0 then return "empty", 1 end
	-- the rate comes from the SERVER's HP (a client can't claim low HP to make the Redline scream)
	local iv = 1 / Weapons.fireRate(w, f.hp)
	local mul = 1
	if w.fan then
		-- the Revolver (web revolverHit): nothing goes faster than the fan; full damage only for a shot on the tap
		-- schedule that isn't flagged as fanned, anything quicker is paid at the fan's damage whatever the client says
		local last = f.lastShot[wid] or -math.huge
		if claimFan == true or now - last < iv * 0.9 - Rules.JITTER then mul = w.fan.dmg / w.dmg end
		iv = 1 / w.fan.rate
	end
	local log: { number }? = nil
	if w.burst then
		-- the Hat Trick (web rifleShot, there on hits; here on shots, since the server counts the bullets): any stretch
		-- as long as one burst plus most of its pause holds at most one burst
		local span = Weapons.burstSpan(w)
		log = f.shotLog[wid] or {}
		f.shotLog[wid] = log :: { number }
		while #(log :: { number }) > 0 and now - (log :: { number })[1] >= span do table.remove(log :: { number }, 1) end
		if #(log :: { number }) >= w.burst then return "too fast", 1 end
	end
	if not Rules.gate(f, wid, now, iv) then return "too fast", 1 end
	if log then table.insert(log, now) end
	f.lastShot[wid] = now
	a.mag -= 1
	return nil, mul
end

-- the Yeehaw's ramp (web rifleShot): a hit on the same person within `chain` s of your last hit raises k (to rampMax),
-- anyone else or too slow starts again at 0. damage x (1 + ramp k). judged from the server's own hit times
function Rules.ramp(f: Fighter, t: Fighter, w: Weapons.Weapon, now: number): number
	local L = f.lev
	local k = if L and L.to == t and now - L.t <= (w.chain or 0) then math.min(w.rampMax or 0, L.k + 1) else 0
	f.lev = { to = t, k = k, t = now }
	return k
end

-- the Hat Trick's BURST!: every shot of one burst landed on the same person (a callout only, no extra damage).
-- true on the hit that completes it
function Rules.burstHit(f: Fighter, t: Fighter, w: Weapons.Weapon, now: number): boolean
	local n = w.burst or 0
	if n < 2 then return false end
	local b = f.bst
	local inBurst = b ~= nil and now - b.t0 <= (n - 1) / (w.rate or 1) + 0.22 -- (+ network jitter)
	if not b or not inBurst then f.bst = { to = t, k = 1, t0 = now }; return false end
	if b.to == t then
		b.k += 1
		return b.k == n
	end
	b.to = nil -- split between two people: no BURST!
	return false
end

-- right click with a scoped gun out: the server keeps its own clock for the scope (the web game takes the shooter's
-- word for a quick-scope; here the claim has to fit this clock)
function Rules.aim(f: Fighter, on: boolean, now: number)
	local w = W[f.held]
	if on and f.alive and w and w.ads and w.ads.scope then f.aimT = now else f.aimT = nil end
end

-- the Second Opinion's quick-scope: fired within `quick` s of the scope coming up (the scope takes 0.92 / 7 s to
-- come up once you press), at most once every 1.2 s. true = pay the bonus. the "sights up" message and the shot
-- travel the same way, so their gap here is the gap the client had: too soon for the scope to be up, or more than
-- the window (+ a quarter second of lag) after it, and the claim is refused
function Rules.quick(f: Fighter, w: Weapons.Weapon, now: number, claimed: boolean): boolean
	if not claimed or not w.quick or not f.aimT then return false end
	local age = now - f.aimT
	local up = 0.92 / (7 * (w.adsSpeed or 1))
	if age < up * 0.5 or age > up + w.quick + 0.25 then return false end
	if now - (f.qsT or -math.huge) < 1.2 then return false end
	f.qsT = now
	return true
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

-- was this shot really pointed at the target? eye + ends = what the client sent (the pellets' end points, at most 12),
-- feet = where the target is and has just been (Fight.path: now first, then back along its trail), so a shooter with
-- lag is checked against the target they saw. one bullet must pass through a padded box at one of those spots; a
-- spray (pellets > 1, where only a sample of the pellets is sent) needs the target inside its cone
function Rules.aimed(w: Weapons.Weapon, eye: Vector3, ends: { Vector3 }, feet: { Vector3 }): boolean
	if #ends == 0 or #feet == 0 then return false end
	if (w.pellets or 1) <= 1 then
		for _, e in ends do
			local v = e - eye
			if v.Magnitude < 1e-3 then continue end
			local d = v.Unit
			for _, ft in feet do
				if Hitbox.ray(eye, d, ft, Hitbox.distScale((ft - eye).Magnitude), Rules.AIM_PAD) then return true end
			end
		end
		return false
	end
	local sum = Vector3.zero
	for _, e in ends do
		local v = e - eye
		if v.Magnitude > 1e-3 then sum += v.Unit end
	end
	if sum.Magnitude < 1e-3 then return false end
	local aim = sum.Unit
	local spread = (w.spread or 0) + (w.maxBloom or 0)
	for _, ft in feet do
		local to = ft + Vector3.new(0, Weapons.BOX.bodyTop * 0.6, 0) - eye
		local dist = to.Magnitude
		if dist < 2 * S then return true end -- point blank: they fill the cone whichever way it points
		local size = Weapons.BOX.bodyTop * 0.6 * Hitbox.distScale(dist) + Rules.AIM_PAD
		local allow = spread * 1.3 + math.atan(size / dist) + 0.05
		if math.acos(math.clamp(aim:Dot(to.Unit), -1, 1)) <= allow then return true end
	end
	return false
end

-- a headshot claimed by a one-bullet gun: the bullet has to pass through the target's head box (a little padded for
-- lag) somewhere along its recent trail. the web server takes the shooter's word for head or body; with the Sniper's
-- headshot always lethal, that word is worth too much to take
Rules.HEAD_PAD = 1
function Rules.headAimed(eye: Vector3, ends: { Vector3 }, feet: { Vector3 }): boolean
	for _, e in ends do
		local v = e - eye
		if v.Magnitude < 1e-3 then continue end
		local d = v.Unit
		for _, ft in feet do
			local _, _, hl, hh = Hitbox.boxes(ft, Hitbox.distScale((ft - eye).Magnitude), Rules.HEAD_PAD)
			if Hitbox.rayBox(eye, d, hl, hh) then return true end
		end
	end
	return false
end

-- aimed: nil = not checked (the dummies' shots are the server's own)
export type HitCtx = { dist: number, speedF: number, speedT: number, los: boolean, aimed: boolean? }

-- a hitscan hit on t from the shot f just fired: returns the reason it's refused, or nil + the (clamped) pellets
function Rules.hit(f: Fighter, t: Fighter, wid: string, n: any, h: any, _now: number, c: HitCtx): (string?, number, number)
	local w = W[wid]
	if t == f then return "yourself", 0, 0 end
	if not t.alive then return "already dead", 0, 0 end
	if not finite(n) or not finite(h) then return "bad count", 0, 0 end
	if c.dist > w.range + Rules.SLACK + 0.3 * (c.speedF + c.speedT) then return "out of range", 0, 0 end
	if not c.los then return "through a wall", 0, 0 end
	if c.aimed == false then return "not aimed at them", 0, 0 end
	local nn = math.clamp(math.floor(n), 1, Rules.maxPellets(w, c.dist))
	local hh = math.clamp(math.floor(h), 0, nn)
	return nil, nn, hh
end

-- a melee swing (the click). the hits come at the animation's hit time, each checked against this swing
function Rules.swing(f: Fighter, wid: any, now: number): string?
	if not inLoadout(f, wid) or W[wid].kind ~= "melee" then return "not a melee weapon" end
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
