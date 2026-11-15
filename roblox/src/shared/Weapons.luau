--!strict
-- step 2's weapons, copied from shared/weapons.js and roblox/docs/WEAPONS.md. distances, speeds and knockback are in
-- studs (x3 from metres), times / rates / damage / angles stay as they are. the server and the client both read this.
local S = 3

export type Weapon = {
	id: string, name: string, slot: string, kind: string, color: Color3, desc: string,
	-- hitscan
	auto: boolean?, rate: number?, rateMax: number?, mag: number?, reload: number?, pellets: number?,
	dmg: number, head: number?, spread: number?, bloom: number?, maxBloom: number?, recoil: number?, kick: number?,
	range: number, ads: { zoom: number, spread: number }?, tracer: Color3?, marbles: boolean?,
	-- melee
	cd: number?, cone: number?, kb: number?, kbUp: number?, grow: number?, growMax: number?, hitT: number?,
	recoilVM: { back: number, up: number, roll: number, side: number, punch: number }?,
	vm: { p: Vector3, r: Vector3, s: number }?, -- viewmodel rest pose (camera space, studs / radians)
}

local function rgb(hex: number): Color3
	return Color3.fromRGB(bit32.rshift(hex, 16) % 256, bit32.rshift(hex, 8) % 256, hex % 256)
end

local W: { [string]: Weapon } = {
	redline = {
		id = "redline", name = "Redline", slot = "primary", kind = "hitscan", color = rgb(0xff3b3b),
		desc = "the lower your HP, the faster it fires. full health it plods, 10 HP it screams. watch the needle.",
		auto = true, rate = 6, rateMax = 22, mag = 40, reload = 1.8, pellets = 1, dmg = 10, head = 1.8, spread = 0.018,
		bloom = 0.0025, maxBloom = 0.06, recoil = 0.3 * S, kick = 0.006, range = 250 * S,
		ads = { zoom = 1.4, spread = 0.35 }, tracer = rgb(0xfff0a0),
		recoilVM = { back = 0.7, up = 2.4, roll = 1.6, side = 0.2, punch = 0.008 },
		vm = { p = Vector3.new(0.2, -0.2, -0.37) * S, r = Vector3.new(0, 0.04, 0), s = 0.72 },
	},
	marbles = {
		id = "marbles", name = "Marble Shotgun", slot = "secondary", kind = "hitscan", color = rgb(0x7fd0ff),
		desc = "a hundred marbles a shot. point blank it's a one-shot, and they stay on the floor to slip on.",
		auto = false, rate = 1 / 0.9, mag = 2, reload = 1.9, pellets = 100, dmg = 1.15, head = 1.3, spread = 0.27,
		recoil = 4 * S, kick = 0.07, range = 30 * S, marbles = true, ads = { zoom = 1.15, spread = 0.8 },
		recoilVM = { back = 2.0, up = 8, roll = 2.6, side = 0.35, punch = 0.04 },
		vm = { p = Vector3.new(0.18, -0.19, -0.34) * S, r = Vector3.new(0, 0.05, 0), s = 0.8 },
	},
	katana = {
		id = "katana", name = "Katana", slot = "melee", kind = "melee", color = rgb(0xe8e8f0),
		desc = "grows longer with every kill. right click parries; a perfect parry sends the bullets home.",
		cd = 0.5, range = 2.8 * S, cone = 0.7, dmg = 48, kb = 6 * S, kbUp = 2 * S, grow = 0.5 * S, growMax = 30, hitT = 0.12,
		vm = { p = Vector3.new(0.1, -0.185, -0.44) * S, r = Vector3.new(0.85, -0.7, 0.25), s = 0.85 },
	},
	-- kill credit only: bullets parried back, parry shoves into the smog
	parry = { id = "parry", name = "Katana Parry", slot = "none", kind = "parry", color = rgb(0x9fe8ff), desc = "", dmg = 0, range = 0 },
}

local Weapons = {
	S = S,
	list = W,
	loadout = { "redline", "marbles", "katana" }, -- keys 1, 2, 3
	-- katana right click (shared/weapons.js PARRY): times in s, arc = the full front cone in degrees
	PARRY = { win = 0.35, perfect = 0.15, cd = 0.8, slack = 0.05, arc = 140, shove = 14 * S, shoveUp = 5 * S, stagger = 0.55, perfectMul = 1.4 },
	-- the hit boxes (shared/physics.js), from the feet: body x/z +-0.52 m, y 0..1.62; head +-0.38, y 1.62..2.30
	BOX = { bodyR = 0.52 * S, bodyTop = 1.62 * S, headR = 0.38 * S, headTop = 2.30 * S },
	-- marbles on the floor (shared/marbles.js MSLIP)
	MSLIP = {
		life = 9, land = 0.35, n = 90, rMin = 1.1 * S, rMax = 2.5 * S, room = 10, per = 3, cd = 0.8,
		walk = 5.5 * S, crouch = 4.5 * S, slide = 7 * S, feetLo = -0.3 * S, feetHi = 0.35 * S, immune = 2,
		thin = 0.55, thinR = 0.85, minN = 10, minR = 0.8 * S,
	},
	-- the slip itself (public/js/player.js): 1.7 s, +6 m/s along your look, at least 6.5 m/s up
	SLIP = { time = 1.7, fwd = 6 * S, up = 6.5 * S },
	-- free-for-all (MODES.md Deathmatch): 20 kills or 6 minutes, 2.5 s respawn, 1.2 s spawn protection
	FFA = { kills = 20, time = 360, respawn = 2.5, protect = 1.2, over = 12 },
	HP = 100,
}

-- shots per second right now (shared/weapons.js fireRate): the Redline speeds up as your HP drops
function Weapons.fireRate(w: Weapon, hp: number): number
	local rate = w.rate or 1
	if not w.rateMax then return rate end
	local missing = math.clamp(1 - (hp or 0) / 100, 0, 1)
	return rate + (w.rateMax - rate) * missing
end

-- the Redline's tachometer: 0 at full HP, 1 at 0 HP
function Weapons.tacho(hp: number): number
	local w = W.redline
	return (Weapons.fireRate(w, hp) - (w.rate :: number)) / ((w.rateMax :: number) - (w.rate :: number))
end

-- the katana's reach with n kills on it
function Weapons.reach(w: Weapon, kat: number): number
	return w.range + math.clamp(kat, 0, w.growMax or 0) * (w.grow or 0)
end

-- damage of a hitscan hit: n pellets landed, h of them on the head
function Weapons.damage(w: Weapon, n: number, h: number): number
	return w.dmg * (n - h) + w.dmg * (w.head or 1) * h
end

return Weapons
