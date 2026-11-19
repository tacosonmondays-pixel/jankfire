--!strict
-- step 2's weapons, copied from shared/weapons.js and roblox/docs/WEAPONS.md. distances, speeds and knockback are in
-- studs (x3 from metres), times / rates / damage / angles stay as they are. the server and the client both read this.
local S = 3

export type Weapon = {
	id: string, name: string, slot: string, kind: string, color: Color3, desc: string,
	-- hitscan
	auto: boolean?, rate: number?, rateMax: number?, mag: number?, reload: number?, pellets: number?,
	dmg: number, head: number?, spread: number?, bloom: number?, maxBloom: number?, recoil: number?, kick: number?,
	range: number, ads: { zoom: number, spread: number, scope: boolean? }?, tracer: Color3?, marbles: boolean?,
	-- batch 3's extras (all optional; WEAPONS.md has each gun's section). kb / kbUp (below) also shove whoever a GUN
	-- hits: kb studs/s per pellet along the shot, kbUp studs/s x the share of the pellets that landed
	speedMul: number?, adsSpeed: number?, thick: number?, -- run speed with it out, how fast the sights come up, tracer width
	lethalHead: boolean?, noscope: boolean?, -- the Sniper: a player's headshot always kills; unscoped hits get a callout
	burst: number?, burstGap: number?, -- the Hat Trick: shots per burst, the pause after one
	ramp: number?, rampMax: number?, chain: number?, -- the Yeehaw: +ramp damage per chained hit on the same person
	quick: number?, qsDmg: number?, qsKb: number?, -- the Second Opinion: the quick-scope window and what it buys
	-- the Revolver's fan: a fanned shot (held trigger) is fired by the SERVER (Combat serverShot). the k-th one in a
	-- string does dmg x fall^(k-1) with spread + grow x (k-1) (up to maxSpread); `reset` s without a shot, or an aimed
	-- tap, starts a new string (Weapons.fanShot)
	fan: { rate: number, hold: number, dmg: number, spread: number, kick: number, fall: number?, grow: number?, maxSpread: number?, reset: number? }?,
	ricochet: number?, -- the Revolver's bounces
	over: { at: number, keep: number }?, -- the Redline: past `at` shots a second, the extra rate is only `keep` as deadly (Weapons.shotDmg)
	heatUp: number?, heatDown: number?, -- the Belt Sander's barrel (looks and sound only)
	-- weapons batch A (18 Nov 2026, WEAPONS.md): the Minigun fires only `spinup` s after the trigger went down (the server
	-- holds it to that too) and spins down over `spindown` s; the Water Pistol's squirts soak whoever they hit (`dur` s at
	-- x`slow` run speed and x`grip` ground friction); the Nail Gun pins whoever takes `n` of one shooter's nails inside
	-- `win` s to the wall behind them (Combat nailHit); the Bread's swing that finds nobody but the map pogos you off it
	-- at `pogo` studs/s; the Hand Slapper shoves straight away from you (`radial`) and slips them
	spinup: number?, spindown: number?,
	soak: { dur: number, slow: number, grip: number }?,
	nails: { n: number, win: number, dur: number, safe: number, reach: number, lift: number, off: number, stick: number }?,
	pogo: number?, slip: boolean?, radial: boolean?,
	-- nothing in your hands but your own (the owner, 18 Nov 2026: "Blood cross and zombie hand can just be our normal
	-- hand!! Zombie will just turn it green!!"): WeaponModels builds no model, only the spots
	bare: boolean?,
	-- the Scythe's right click (ScytheDash.server): a flat dash of dist studs in time s, `charges` of them, each coming
	-- back cd s after the last started (one at a time, like Tracer's Blink; a Scythe kill gives one back at once), then
	-- recover s with no swing, guard or dash; the first enemy on its path (within width) takes dmg and a shove
	dash: { dist: number, time: number, cd: number, charges: number?, recover: number, dmg: number, kb: number, kbUp: number, width: number }?,
	-- (the Scythe, ScytheLatch.luau) a hit latches: the blade holds them for t s (no shove yet: a hit-stop beat), then
	-- you spring back (back studs/s away from them, backUp up) and they go back a little (push, pushUp), each cut short
	-- by a wall behind. the chain's last link (chain: the finisher) pushes x finisher. kb / kbUp aren't used for its hits
	-- (a training dummy stands its ground against a push that size: theirs is x dummy across)
	latch: { t: number, back: number, backUp: number, push: number, pushUp: number, finisher: number, chain: number, dummy: number }?,
	-- a weapon with two forms (the Scythe and its rifle, Rules.equip): the key "form" (Q) turns it into `to` in `time` s
	-- (no swing, dash, shot or reload meanwhile), the gun's first shot `fireDelay` s after that; not within `swingLock` s
	-- of a swing's click or `shotLock` s of a shot. formOf: this row is the second form of that loadout weapon (it shares
	-- its slot, unlock, stats and kill credit, Weapons.base)
	form: { to: string, time: number, fireDelay: number, swingLock: number, shotLock: number }?,
	formOf: string?,
	-- weapons batch C, the projectiles (kind "proj", WeaponProj.server flies them): proj = "rocket" | "peel" | "ball" |
	-- "snow" | "blood", speed / grav (studs/s, /s^2), r (studs), life (s); the rocket's radius and selfKb, the ball's
	-- bounces / bonus / minBounce, the snowball's frost, the blood cross's cost / thin / fuse / burst / blast
	proj: string?, speed: number?, grav: number?, life: number?, radius: number?, selfKb: number?, bounce: number?,
	bounces: number?, bonus: number?, minBounce: number?, freezeAt: number?, freeze: number?, frostDecay: number?,
	cost: number?, thin: { cd: number, dmg: number, heal: number }?, fuse: number?, burst: number?, blastR: number?, blastDmg: number?,
	-- weapons batch D: the slipper's way out (out s, outLock s while locked on) and back (back studs/s), its homing (homeR
	-- studs, homeCone degrees off its heading, homeTurn rad/s); the Scales' verdict and right-click pillar (gavel); the TV
	-- Remote (kind "remote": range, cone; pause dur / cd, rewind back / cd)
	out: number?, back: number?, homeR: number?, homeCone: number?, homeTurn: number?, outLock: number?,
	verdict: boolean?, gavel: { range: number, cone: number, delay: number, r: number, h: number, dmg: number, kbUp: number, cd: number }?,
	pause: { dur: number, cd: number }?, rewind: { back: number, cd: number }?,
	-- the Bow (kind "bow", proj "arrow"): hold drawT s to full; speed .. speedMax studs/s and dmg .. dmgMax by the draw
	drawT: number?, speedMax: number?, dmgMax: number?,
	hands: number?, -- (Lefty & Righty: 2 guns, left click the left, right click the right, each its own mag of `mag`)
	-- batch E, the Card Deck (kind "cards", CardDeck.server): a card's dmg + perRank x rank; a spade's fan (fanN over
	-- fanSpread rad), a picture spade's (ultN over ultSpread), the flick every other card throws
	perRank: number?, fanN: number?, fanSpread: number?, ultN: number?, ultSpread: number?, flick: number?,
	up: number?, -- (the Shopping Cart Cannon, kind "cart": the shot's lift; CartServer flies the cart)
	-- own recordings (JankfireSounds): a melee hit, a melee swing's whoosh, the draw's clunk, a whole reload
	hitSnd: string?, swingSnd: string?, drawSnd: string?, reloadSnd: string?, snd2: string?, -- (snd2: a second layer on the shot)
	-- weapons batch B: the Taser (kind "zap", the server picks who it hits): stun s (x wet if soaked), the chain through
	-- soaked people within chainR, up to chainMax in all, each chainStun s + chainDmg; self = your own stun firing it wet
	zap: { stun: number, wet: number, chainR: number, chainMax: number, chainStun: number, chainDmg: number, self: number }?,
	-- the held-trigger weapons (kind "hold", HoldWeapons.server): hold = "blow" (the Leaf Blower), "breath" (the Hot
	-- Sauce), "beam" (the Big Laser Pointer); their numbers are each row's own (WEAPONS.md "Balance"-free web values)
	hold: string?, tick: number?, push: number?, pushUp: number?, self: number?, fuel: number?, regen: number?,
	maxCharge: number?, coughAt: number?, exhaleMul: number?, jet: number?, cough: number?,
	charge: number?, tap: number?, dur: { number }?, r: { number }?, dmgK: { number }?, kbK: { number }?, slow: number?,
	cycle: { clip: string, at: number }?, draw: string?, -- the clip after every shot (pump, bolt, lever), its own draw
	-- melee
	cd: number?, cone: number?, kb: number?, kbUp: number?, grow: number?, growMax: number?, hitT: number?,
	-- the knife: x this from behind (and the hit counts as a headshot), and its right-click heavy stab
	backstab: number?, heavy: { dmg: number, cd: number, range: number, cone: number, kb: number, kbUp: number, hitT: number }?,
	recoilVM: { back: number, up: number, roll: number, side: number, punch: number }?,
	vm: { p: Vector3, r: Vector3, s: number }?, -- viewmodel rest pose (camera space, studs / radians)
	-- how a gun looks and sounds when it fires (all optional). the gun code in Arsenal reads these, so a plain gun is
	-- one row here + a model + a sound, with no code of its own. big = the big muzzle flash, brass = a casing a shot,
	-- spray = the pellets are the tracer (the marbles), hole = false: chips, not holes. snd = the shot's Sound in
	-- JankfireSounds; tacho = the Redline's three renders by HP instead
	fx: { big: boolean?, brass: boolean?, spray: boolean?, hole: boolean?, scale: number?, shake: number?, splash: boolean?, vol: number?, water: boolean?, nails: boolean? }?,
	snd: string?, tacho: boolean?,
	-- the model: its Blender file's bounds (tools/roblox/export_weapons.py prints them) and the spots the hands and
	-- effects use, in the file's frame (metres, -Z forward). WeaponModels builds a plain stand-in from these until the
	-- Blender model (ReplicatedStorage.JankfireWeapons.w_<id>) is there
	-- parts = the pieces that move (GunParts.luau), by the node they hang off in the file: where each one turns (at)
	-- and how far it goes, from the model's own notes (tools/roblox/export_weapons.py writes them to export_report.json)
	mdl: { lo: Vector3, hi: Vector3, muzzle: Vector3, sight: Vector3?, port: Vector3?, grip: Vector3, fore: Vector3?, parts: { [string]: any }? }?,
}

local function rgb(hex: number): Color3
	return Color3.fromRGB(bit32.rshift(hex, 16) % 256, bit32.rshift(hex, 8) % 256, hex % 256)
end

-- the Scythe's blade, scythe -> rifle (guns-remodel's kit, c0716af; file metres, the model's own space): 120 degrees
-- about (-1, 1, 1) and down the haft, from its root at the collar (0.012, 0.02, -1.218) to the heel slot (0, 0.012,
-- 0.114). the kit bakes every turn into the meshes, so this can't be measured off the two models: it is written here
local SCYTHE_TURN = CFrame.new(0.02, 1.23, 0.126, 0, -1, 0, 0, 0, 1, -1, 0, 0)

local W: { [string]: Weapon } = {
	redline = {
		id = "redline", name = "Redline", slot = "primary", kind = "hitscan", color = rgb(0xff3b3b),
		desc = "the lower your HP, the faster it fires: 6 a second at full health, up to 22 at low HP. the needle shows the rate.",
		auto = true, rate = 6, rateMax = 22, mag = 40, reload = 1.8, pellets = 1, dmg = 10, head = 1.8, spread = 0.018,
		bloom = 0.0025, maxBloom = 0.06, recoil = 0.3 * S, kick = 0.006, range = 250 * S,
		-- (owner, 18 Nov 2026: "redline damage at higher speeds needs to maybe be capped? its super strong") the rate
		-- still climbs to 22, but past 12 a second each shot does less: 60 damage a second at full HP, 120 at 62 HP,
		-- 126 at 50, 143 at 10 (was 140 and 204). WEAPONS.md "Balance pass, 18 Nov"
		over = { at = 12, keep = 0.25 },
		ads = { zoom = 1.4, spread = 0.35 }, tracer = rgb(0xfff0a0),
		fx = { brass = true, shake = 0.06 }, tacho = true,
		recoilVM = { back = 0.7, up = 2.4, roll = 1.6, side = 0.2, punch = 0.008 },
		vm = { p = Vector3.new(0.2, -0.2, -0.37) * S, r = Vector3.new(0, 0.04, 0), s = 0.72 },
	},
	marbles = {
		id = "marbles", name = "Marble Shotgun", slot = "secondary", kind = "hitscan", color = rgb(0x7fd0ff),
		desc = "a hundred marbles a shot. point blank it's a one-shot, and they stay on the floor to slip on.",
		auto = false, rate = 1 / 0.9, mag = 2, reload = 1.9, pellets = 100, dmg = 1.15, head = 1.3, spread = 0.27,
		recoil = 4 * S, kick = 0.07, range = 30 * S, marbles = true, ads = { zoom = 1.15, spread = 0.8 },
		fx = { big = true, spray = true, hole = false, scale = 0.7, shake = 0.35, splash = false }, snd = "gun_marbles",
		recoilVM = { back = 2.0, up = 8, roll = 2.6, side = 0.35, punch = 0.04 },
		vm = { p = Vector3.new(0.18, -0.19, -0.34) * S, r = Vector3.new(0, 0.05, 0), s = 0.8 },
		-- (16 Nov, the owner: "gumball shotgun should lose less gumballs ... the reload is like this cage thing"): only its
		-- moving pieces (the model, its spots and the hold come from WeaponModels.BUILD.marbles and the Blender model):
		-- the jar's 14 balls (marble_00 bottom .. marble_13 top) show the ammo, fuller for longer (ammo / mag to the power
		-- `curve`), and fill again while the bag pours; the lid flips open on its front hinge for the pour and snaps
		-- shut; the Gumball Machine's crank turns once as it shuts
		mdl = {
			parts = {
				jar = { n = 14, curve = 0.6, pour = { 0.66, 1.18 } },
				lid = { at = Vector3.new(0, 0.147, -0.099), open = -1.9, times = { 0.42, 0.6, 1.42, 1.5 } },
				crank = { at = Vector3.new(-0.043, -0.008, -0.07), times = { 1.55, 1.75 } },
			},
		},
	},
	-- ---- batch 3, the plain guns (WEAPONS.md): data only. stats from shared/weapons.js, vm + recoilVM from
	-- public/js/weapons.js (VM, RECOIL), mdl from the export report and the web model's spots
	ar = {
		id = "ar", name = "Assault Rifle", slot = "primary", kind = "hitscan", color = rgb(0x9fd36b),
		desc = "full auto and steady. accurate when you aim down sights.",
		auto = true, rate = 10, mag = 30, reload = 1.7, pellets = 1, dmg = 11, head = 2, spread = 0.01,
		bloom = 0.004, maxBloom = 0.04, recoil = 0.4 * S, kick = 0.008, range = 300 * S,
		ads = { zoom = 1.5, spread = 0.2 }, tracer = rgb(0xfff0a0),
		fx = { brass = true, shake = 0.06 }, snd = "gun_ar",
		recoilVM = { back = 0.9, up = 3, roll = 1.5, side = 0.15, punch = 0.012 },
		vm = { p = Vector3.new(0.2, -0.2, -0.38) * S, r = Vector3.new(0, 0.04, 0), s = 0.7 },
		mdl = {
			lo = Vector3.new(-0.04, -0.3944, -0.7215), hi = Vector3.new(0.0437, 0.1228, 0.4689),
			muzzle = Vector3.new(0, 0.015, -0.72), sight = Vector3.new(0, 0.114, 0.234), port = Vector3.new(0.036, 0.03, -0.05),
			grip = Vector3.new(0, -0.1, 0.08), fore = Vector3.new(0, -0.04, -0.28),
			-- (16 Nov reload check: the rifle had no moving pieces listed, so its magazine never left the gun in a reload)
			parts = { mag = { at = Vector3.new(0, -0.05, -0.105) }, charge = {} },
		},
	},
	smg = {
		id = "smg", name = "SMG", slot = "primary", kind = "hitscan", color = rgb(0x6bd3c8),
		desc = "sprays fast. light: you run faster holding it.",
		auto = true, rate = 16, mag = 45, reload = 1.5, pellets = 1, dmg = 7, head = 1.5, spread = 0.03,
		bloom = 0.002, maxBloom = 0.05, recoil = 0.2 * S, kick = 0.005, range = 200 * S, speedMul = 1.2,
		ads = { zoom = 1.3, spread = 0.4 }, tracer = rgb(0xfff0a0),
		fx = { brass = true, shake = 0.05 }, snd = "gun_smg",
		recoilVM = { back = 0.6, up = 2.2, roll = 1.4, side = 0.2, punch = 0.008 },
		vm = { p = Vector3.new(0.2, -0.19, -0.36) * S, r = Vector3.new(0, 0.05, 0), s = 0.8 },
		mdl = {
			lo = Vector3.new(-0.0387, -0.222, -0.3705), hi = Vector3.new(0.0293, 0.068, 0.3219),
			muzzle = Vector3.new(0, 0.01, -0.37), sight = Vector3.new(0, 0.054, 0.102), port = Vector3.new(0.03, 0.03, -0.09),
			grip = Vector3.new(0, -0.1, 0.06), fore = Vector3.new(0, -0.035, -0.22),
			parts = { mag = { at = Vector3.new(0, -0.048, -0.088) }, charge = {} },
		},
	},
	shotgun = {
		id = "shotgun", name = "Shotgun", slot = "primary", kind = "hitscan", color = rgb(0xe0a060),
		desc = "ten pellets, best up close. shoot the floor to launch yourself up.",
		auto = false, rate = 1 / 0.75, mag = 6, reload = 2.0, pellets = 10, dmg = 8, head = 1.5, spread = 0.075,
		recoil = 17 * S, kick = 0.08, range = 80 * S, ads = { zoom = 1.2, spread = 0.65 },
		fx = { big = true, shake = 0.5 }, snd = "gun_shotgun", cycle = { clip = "pump_shotgun", at = 0.22 },
		recoilVM = { back = 2.4, up = 9, roll = 3, side = 0.3, punch = 0.05 },
		vm = { p = Vector3.new(0.2, -0.2, -0.36) * S, r = Vector3.new(0, 0.04, 0), s = 0.7 },
		mdl = {
			lo = Vector3.new(-0.0388, -0.1385, -0.74), hi = Vector3.new(0.0242, 0.0807, 0.4066),
			muzzle = Vector3.new(0, 0.025, -0.74), sight = Vector3.new(0, 0.0712, -0.0386), port = Vector3.new(0.03, 0.02, -0.1),
			grip = Vector3.new(0, -0.06, 0.13), fore = Vector3.new(0, -0.03, -0.4),
			parts = { pump = { travel = 0.09975 } },
		},
	},
	sniper = {
		id = "sniper", name = "Sniper", slot = "primary", kind = "hitscan", color = rgb(0xa2457c), -- (its calm accent: the magenta mark)
		desc = "right click to scope. a headshot always kills, a body shot sends them flying off the map. hipfire is inaccurate.",
		auto = false, rate = 1 / 1.1, mag = 5, reload = 2.2, pellets = 1, dmg = 55, head = 2, spread = 0.05,
		kb = 75 * S, kbUp = 14 * S, recoil = 12 * S, kick = 0.06, range = 500 * S, lethalHead = true, noscope = true,
		ads = { zoom = 4, spread = 0, scope = true }, tracer = rgb(0xff4fd8), thick = 0.09 * S,
		fx = { big = true, shake = 0.5 }, snd = "gun_sniper", cycle = { clip = "bolt_sniper", at = 0.32 },
		recoilVM = { back = 3, up = 11, roll = 2, side = 0.2, punch = 0.075 },
		vm = { p = Vector3.new(0.2, -0.2, -0.38) * S, r = Vector3.new(0, 0.03, 0), s = 0.5 },
		mdl = {
			lo = Vector3.new(-0.0701, -0.2714, -1.48), hi = Vector3.new(0.1077, 0.1937, 0.5974),
			muzzle = Vector3.new(0, 0.02, -1.48), sight = Vector3.new(0, 0.12354, 0.10316), port = Vector3.new(0.04, 0.04, -0.12),
			grip = Vector3.new(0, -0.11, 0.085), fore = Vector3.new(0, -0.06, -0.5),
			parts = { bolt = { at = Vector3.new(0, 0.02, -0.12396), lift = 1.05, travel = 0.14028 } },
		},
	},
	burst = {
		id = "burst", name = "Burst Rifle", slot = "primary", kind = "hitscan", color = rgb(0x4f8bff),
		desc = "a bullpup that fires three at a time. land all three on one person for a BURST. very accurate.",
		auto = true, rate = 14, burst = 3, burstGap = 0.28, mag = 30, reload = 2.0, pellets = 1, dmg = 15, head = 2,
		spread = 0.006, bloom = 0.002, maxBloom = 0.018, recoil = 0.35 * S, kick = 0.006, range = 320 * S,
		ads = { zoom = 1.6, spread = 0.15 }, tracer = rgb(0x4f8bff),
		fx = { brass = true, shake = 0.06 }, snd = "gun_burst", draw = "draw_burst",
		recoilVM = { back = 0.7, up = 2.2, roll = 1.1, side = 0.12, punch = 0.01 },
		vm = { p = Vector3.new(0.2, -0.205, -0.37) * S, r = Vector3.new(0, 0.04, 0), s = 0.72 },
		mdl = {
			lo = Vector3.new(-0.08, -0.276, -0.6708), hi = Vector3.new(0.0576, 0.156, 0.5428),
			muzzle = Vector3.new(0, 0.012, -0.67), sight = Vector3.new(0, 0.1448, 0.1204), port = Vector3.new(0.03, 0.06, 0.09),
			grip = Vector3.new(0, -0.12, -0.06), fore = Vector3.new(0, -0.12, -0.235),
			parts = { mag = { at = Vector3.new(0, -0.0616, 0.0708) }, charge = {} },
		},
	},
	lmg = {
		id = "lmg", name = "LMG", slot = "primary", kind = "hitscan", color = rgb(0xff5a1f),
		desc = "a hundred rounds on a belt you can watch run out. slow to aim, slow to reload. the barrel glows the longer you hold it.",
		auto = true, rate = 12, mag = 100, reload = 4.2, pellets = 1, dmg = 10, head = 1.6, spread = 0.034,
		bloom = 0.0012, maxBloom = 0.03, kb = 0.25 * S, recoil = 0.45 * S, kick = 0.006, range = 260 * S,
		speedMul = 0.86, adsSpeed = 0.42, heatUp = 0.24, heatDown = 0.4,
		ads = { zoom = 1.35, spread = 0.4 }, tracer = rgb(0xfff0a0),
		fx = { brass = true, shake = 0.06 }, snd = "gun_lmg", draw = "draw_lmg",
		recoilVM = { back = 0.55, up = 1.6, roll = 1.3, side = 0.3, punch = 0.008 },
		vm = { p = Vector3.new(0.215, -0.235, -0.4) * S, r = Vector3.new(0, 0.035, 0), s = 0.64 },
		mdl = {
			lo = Vector3.new(-0.0847, -0.3401, -0.8713), hi = Vector3.new(0.0732, 0.1111, 0.5454),
			muzzle = Vector3.new(0, 0.02, -0.87), sight = Vector3.new(0, 0.10379, 0.08), port = Vector3.new(0.04, 0.04, -0.06),
			grip = Vector3.new(0, -0.11, 0.14), fore = Vector3.new(0, -0.06, -0.42),
			parts = { mag = { at = Vector3.new(-0.02, -0.1, -0.08) }, cover = { at = Vector3.new(0, 0.065, 0.08) }, belt = { n = 12 }, heat = { piece = "lmg_heat" } },
		},
	},
	dmr = {
		id = "dmr", name = "Marksman Rifle", slot = "primary", kind = "hitscan", color = rgb(0xb07dff),
		desc = "a marksman rifle with a little scope. two to the body or one to the head. quick-scope it for a bit extra.",
		auto = false, rate = 1 / 0.55, mag = 10, reload = 2.1, pellets = 1, dmg = 52, head = 2, spread = 0.045,
		recoil = 3 * S, kick = 0.035, range = 400 * S, speedMul = 0.96, quick = 0.3, qsDmg = 10, qsKb = 9 * S,
		ads = { zoom = 2.6, spread = 0, scope = true }, tracer = rgb(0xb07dff), thick = 0.06 * S,
		fx = { big = true, brass = true, shake = 0.5 }, snd = "gun_dmr", draw = "draw_dmr",
		recoilVM = { back = 2.2, up = 8, roll = 1.8, side = 0.2, punch = 0.05 },
		vm = { p = Vector3.new(0.2, -0.2, -0.38) * S, r = Vector3.new(0, 0.035, 0), s = 0.6 },
		mdl = {
			lo = Vector3.new(-0.0444, -0.1809, -0.8906), hi = Vector3.new(0.0486, 0.1572, 0.5878),
			muzzle = Vector3.new(0, 0.02, -0.89), sight = Vector3.new(0, 0.11996, 0.1204), port = Vector3.new(0.03, 0.04, -0.03),
			grip = Vector3.new(0, -0.08, 0.17), fore = Vector3.new(0, -0.02, -0.33),
			parts = { mag = { at = Vector3.new(0, -0.0232, -0.0092) }, charge = {} },
		},
	},
	lever = {
		id = "lever", name = "Lever Rifle", slot = "primary", kind = "hitscan", color = rgb(0xa58640), -- (its calm accent: the brass)
		desc = "a lever-action you crank after every shot. keep hitting the same person and every hit stings a bit more.",
		auto = false, rate = 1 / 0.42, mag = 8, reload = 2.6, pellets = 1, dmg = 30, head = 2, spread = 0.012,
		kb = 2 * S, kbUp = 0.5 * S, recoil = 2 * S, kick = 0.04, range = 280 * S, ramp = 0.15, rampMax = 3, chain = 0.8,
		ads = { zoom = 1.45, spread = 0.2 }, tracer = rgb(0xffc0cc),
		fx = { shake = 0.25 }, snd = "gun_lever", cycle = { clip = "lever_cycle", at = 0.04 }, draw = "draw_lever",
		recoilVM = { back = 1.8, up = 9, roll = 1.6, side = 0.2, punch = 0.045 },
		vm = { p = Vector3.new(0.19, -0.19, -0.36) * S, r = Vector3.new(0, 0.045, 0), s = 0.72 },
		mdl = {
			lo = Vector3.new(-0.0339, -0.1775, -0.71), hi = Vector3.new(0.0236, 0.0704, 0.4862),
			muzzle = Vector3.new(0, 0.02, -0.71), sight = Vector3.new(0, 0.06, -0.2), port = Vector3.new(0, 0.06, 0.02),
			grip = Vector3.new(0, -0.105, 0.1), fore = Vector3.new(0, -0.03, -0.3),
			parts = { lever = { at = Vector3.new(0, -0.04, -0.02) }, lhammer = { at = Vector3.new(0, 0.03, 0.09) }, twirl = { at = Vector3.new(0, -0.085, 0.075) } },
		},
	},
	autoshot = {
		id = "autoshot", name = "Auto Shotgun", slot = "primary", kind = "hitscan", color = rgb(0x4ad66b),
		desc = "an automatic shotgun with a box mag. less per shot than the pump, but it keeps firing while you hold.",
		auto = true, rate = 3, mag = 10, reload = 2.4, pellets = 8, dmg = 5, head = 1.5, spread = 0.07,
		recoil = 5.5 * S, kick = 0.045, range = 60 * S, ads = { zoom = 1.2, spread = 0.7 },
		fx = { big = true, brass = true, shake = 0.3 }, snd = "gun_autoshot", draw = "draw_autoshot",
		recoilVM = { back = 1.9, up = 6.5, roll = 2.4, side = 0.35, punch = 0.04 },
		vm = { p = Vector3.new(0.2, -0.2, -0.37) * S, r = Vector3.new(0, 0.04, 0), s = 0.7 },
		mdl = {
			lo = Vector3.new(-0.0534, -0.2622, -0.7606), hi = Vector3.new(0.0586, 0.0849, 0.5076),
			muzzle = Vector3.new(0, 0.02, -0.76), sight = Vector3.new(0, 0.07796, 0.11018), port = Vector3.new(0.035, 0.04, -0.08),
			grip = Vector3.new(0, -0.11, 0.13), fore = Vector3.new(0, -0.03, -0.38),
			parts = { mag = { at = Vector3.new(0, -0.04552, -0.07582) }, charge = {} },
		},
	},
	-- ---- weapons batch A (18 Nov 2026): stats from shared/weapons.js, vm + recoilVM from public/js/weapons.js (VM,
	-- RECOIL), WEAPONS.md has each one's section. mdl = the stand-in until the kit model is in JankfireWeapons
	minigun = {
		id = "minigun", name = "Minigun", slot = "primary", kind = "hitscan", color = rgb(0xc8c8c8),
		desc = "spins up, then fires 25 a second while you hold. the bullets shove people, and the recoil is strong enough to fly on.",
		auto = true, rate = 25, mag = 250, reload = 3.5, pellets = 1, dmg = 6, head = 1.5, spread = 0.045,
		kb = 1.7 * S, recoil = 1.25 * S, kick = 0.004, range = 200 * S, spinup = 0.6, spindown = 0.9,
		ads = { zoom = 1.15, spread = 0.6 }, tracer = rgb(0xfff0a0),
		fx = { brass = true, shake = 0.03 }, snd = "gun_minigun", draw = "draw_heavy", drawSnd = "draw_minigun", reloadSnd = "reload_minigun",
		recoilVM = { back = 0.35, up = 0.9, roll = 1.2, side = 0.25, punch = 0.004 },
		vm = { p = Vector3.new(0.22, -0.26, -0.42) * S, r = Vector3.new(0, 0.03, 0), s = 0.7 },
		mdl = {
			lo = Vector3.new(-0.079, -0.252, -0.75), hi = Vector3.new(0.1054, 0.15, 0.2),
			muzzle = Vector3.new(0, 0, -0.75), grip = Vector3.new(0, -0.13, 0.143), fore = Vector3.new(0, -0.14, -0.15),
			parts = { barrels = { at = Vector3.new(0, 0, -0.45) } },
		},
	},
	nailgun = {
		id = "nailgun", name = "Nail Gun", slot = "primary", kind = "hitscan", color = rgb(0xff6f3c),
		desc = "fires nails, fast. six in a row and they're nailed to the wall behind them.",
		auto = true, rate = 11, mag = 36, reload = 1.9, pellets = 1, dmg = 9, head = 1.6, spread = 0.022,
		bloom = 0.003, maxBloom = 0.045, kb = 0.5 * S, recoil = 0.25 * S, kick = 0.006, range = 120 * S,
		tracer = rgb(0xd8dde4), thick = 0.018 * S,
		nails = { n = 6, win = 1.2, dur = 1.1, safe = 2.5, reach = 7 * S, lift = 0.35 * S, off = 0.42 * S, stick = 10 },
		ads = { zoom = 1.35, spread = 0.35 },
		fx = { nails = true, shake = 0.05 }, snd = "gun_nailgun",
		recoilVM = { back = 0.8, up = 2.6, roll = 1.8, side = 0.25, punch = 0.01 },
		vm = { p = Vector3.new(0.2, -0.155, -0.42) * S, r = Vector3.new(0, 0.3, 0), s = 0.6 },
		mdl = {
			lo = Vector3.new(-0.06, -0.205, -0.358), hi = Vector3.new(0.06, 0.1744, 0.134),
			muzzle = Vector3.new(0, 0.04, -0.358), sight = Vector3.new(0, 0.1744, 0.1324),
			grip = Vector3.new(0, -0.06, 0.05), fore = Vector3.new(0, -0.03, -0.2),
			parts = { mag = { at = Vector3.new(0, -0.07, -0.1555) } },
		},
	},
	revolver = {
		id = "revolver", name = "Revolver", slot = "secondary", kind = "hitscan", color = rgb(0xe0c070),
		desc = "six shots, a twirl after every one. tap for a dead-accurate shot, hold to fan the hammer. bullets bounce off walls twice.",
		auto = false, rate = 1 / 0.4, mag = 6, reload = 2.0, pellets = 1, dmg = 40, head = 2.4, spread = 0.003,
		recoil = 3 * S, kick = 0.07, range = 250 * S, ricochet = 2,
		-- (owner, 18 Nov 2026: "revolver needs to either do less damage or be less accurate the longer you hold it") the
		-- tap stays 40 and dead accurate; the fanned shots after it go 24, 21, 19, 16, 14 at spreads 0.045 .. 0.165, so a
		-- held cylinder still kills point blank, misses half of itself at 12 m and most past 20 m (was 28 each at 0.065)
		fan = { rate = 6, hold = 0.2, dmg = 24, fall = 0.88, spread = 0.045, grow = 0.03, maxSpread = 0.165, reset = 0.45, kick = 0.3 },
		ads = { zoom = 1.4, spread = 0.2 }, tracer = rgb(0xffd060),
		fx = { shake = 0.3 }, snd = "gun_revolver",
		recoilVM = { back = 1.6, up = 13, roll = 2.5, side = 0.2, punch = 0.045 },
		vm = { p = Vector3.new(0.17, -0.16, -0.32) * S, r = Vector3.new(0, 0.06, 0), s = 1.0 },
		mdl = {
			lo = Vector3.new(-0.03, -0.204, -0.2907), hi = Vector3.new(0.03, 0.0915, 0.154),
			muzzle = Vector3.new(0, 0.03, -0.29), sight = Vector3.new(0, 0.08325, 0.168),
			grip = Vector3.new(0, -0.1, 0.085),
			parts = { cylinder = { at = Vector3.new(0, 0.009, -0.029), step = math.pi / 3 }, hammer = { at = Vector3.new(0, 0.033, 0.052), kind = "revolver" }, twirl = { at = Vector3.new(0, -0.02, 0.02) } },
		},
	},
	pistol = {
		id = "pistol", name = "Pistol", slot = "secondary", kind = "hitscan", color = rgb(0xa0b4ff),
		desc = "a plain pistol. 12 shots, the slide locks back so you know you're empty.",
		auto = false, rate = 5, mag = 12, reload = 1.35, pellets = 1, dmg = 20, head = 2.2, spread = 0.006,
		bloom = 0.007, maxBloom = 0.03, recoil = 0.6 * S, kick = 0.035, range = 220 * S, speedMul = 1.05,
		ads = { zoom = 1.35, spread = 0.25 }, tracer = rgb(0xb8c8ff),
		fx = { brass = true, shake = 0.12 }, snd = "gun_pistol", draw = "draw_pistol",
		recoilVM = { back = 1.1, up = 7, roll = 1.6, side = 0.15, punch = 0.022 },
		vm = { p = Vector3.new(0.165, -0.155, -0.31) * S, r = Vector3.new(0, 0.06, 0), s = 1.0 },
		mdl = {
			lo = Vector3.new(-0.0262, -0.1413, -0.25), hi = Vector3.new(0.0262, 0.0585, 0.0781),
			muzzle = Vector3.new(0, 0.03, -0.25), sight = Vector3.new(0, 0.0585, 0.0485), port = Vector3.new(0.027, 0.045, -0.06),
			grip = Vector3.new(0, -0.085, 0.035),
			parts = { slide = { travel = 0.038 }, mag = { at = Vector3.new(0, -0.13008, 0.01148), dir = Vector3.new(0, -0.95106, 0.30902) }, hammer = { at = Vector3.new(0, 0.0048, 0.0545), kind = "pistol" } },
		},
	},
	sawnoff = {
		id = "sawnoff", name = "Sawed-Off", slot = "secondary", kind = "hitscan", color = rgb(0xe05a3a),
		desc = "a sawed-off double. two shells, point blank they go flying, shoot the floor for a little hop.",
		auto = false, rate = 1 / 0.3, mag = 2, reload = 2.3, pellets = 12, dmg = 9, head = 1.3, spread = 0.11,
		kb = 3.4 * S, kbUp = 9 * S, recoil = 10 * S, kick = 0.09, range = 32 * S,
		ads = { zoom = 1.12, spread = 0.7 }, tracer = rgb(0xffa060),
		fx = { big = true, shake = 0.5 }, snd = "gun_sawnoff", draw = "draw_sawnoff",
		recoilVM = { back = 3.4, up = 16, roll = 3.5, side = 0.35, punch = 0.085 },
		vm = { p = Vector3.new(0.19, -0.18, -0.34) * S, r = Vector3.new(0, 0.05, 0), s = 0.85 },
		mdl = {
			lo = Vector3.new(-0.0241, -0.1012, -0.311), hi = Vector3.new(0.0241, 0.0569, 0.1469),
			muzzle = Vector3.new(0, 0.02, -0.31), sight = Vector3.new(0, 0.065, 0.075),
			grip = Vector3.new(0, -0.05, 0.095),
			parts = {
				hinge = { at = Vector3.new(0, -0.002, -0.05), open = 0.7, nodes = { "hinge", "hinge_trim", "forend", "forend_iron", "shell1", "shell2" } },
				shells = { "shell1", "shell2" },
				hammers = { { node = "hammerR", at = Vector3.new(0.013, 0.028, 0.054) }, { node = "hammerL", at = Vector3.new(-0.013, 0.028, 0.054) } },
			},
		},
	},
	-- (weapons batch A) a plain hitscan squirt gun: 1 a squirt, but every squirt that lands soaks them (Combat soakHit)
	water = {
		id = "water", name = "Water Pistol", slot = "secondary", kind = "hitscan", color = rgb(0x3fb8ff),
		desc = "a big plastic squirt gun. whoever it hits gets soaked: they slip about and slow down for a few seconds.",
		auto = true, rate = 9, mag = 40, reload = 1.6, pellets = 1, dmg = 1, head = 1.5, spread = 0.03,
		kb = 0.6 * S, recoil = 0, kick = 0.002, range = 26 * S,
		soak = { dur = 4, slow = 0.72, grip = 0.3 },
		ads = { zoom = 1.2, spread = 0.5 }, tracer = rgb(0x9fd8ff),
		fx = { water = true, hole = false, shake = 0 }, snd = "gun_water",
		recoilVM = { back = 0.8, up = 2.5, roll = 1, side = 0.2, punch = 0.01 },
		vm = { p = Vector3.new(0.18, -0.18, -0.355) * S, r = Vector3.new(0.02, 0.08, 0), s = 0.74 },
		mdl = {
			lo = Vector3.new(-0.038, -0.1568, -0.29), hi = Vector3.new(0.038, 0.136, 0.1553),
			muzzle = Vector3.new(0, 0.01, -0.29), sight = Vector3.new(0, 0.136, 0.09),
			grip = Vector3.new(0, -0.09, 0.108),
			parts = { water = { at = Vector3.new(0, 0.0545, -0.0775) }, pump = { travel = 0.03 } },
		},
	},
	-- ---- weapons batch C (18 Nov 2026): the projectiles. the server flies every one (WeaponProj.server); the web's
	-- numbers x3 for studs (side notes weapons-batchC-spec.md has the traced rules)
	chicken = {
		id = "chicken", name = "Chicken Rocket", slot = "primary", kind = "proj", proj = "rocket", color = rgb(0xffe14d),
		desc = "rubber chickens that explode. every shot kicks you the other way: aim down to fly. shoot your own feet to rocket jump.",
		cd = 0.85, speed = 36 * S, grav = 6, r = 0.35 * S, radius = 7.5 * S, dmg = 55, kb = 34 * S, selfKb = 1.0, range = 200 * S,
		-- (owner, 18 Nov 2026: "if you press left click with the rocket launcher it does like s thrust explosion so you can
		-- use it propel yourself through the air!") every shot's back-blast shoves you the other way to your aim, 18 m/s,
		-- on the ground or in the air, no damage (WeaponProj.server). against 26 m/s² and 0.85 s a shot, a chain aimed down
		-- climbs for a few shots, then sinks slowly. your upward speed after it is capped at 32 m/s (thrustCapUp)
		-- a mostly level shot also hops you 7 m/s (thrustHop): on the floor a flat shove is eaten by your footing at once
		-- (4 m/s carried a level dash only 4.5 m in a test: you landed too soon)
		thrust = 18 * S, thrustCapUp = 32 * S, thrustHop = 7 * S,
		snd = "chicken_fire", snd2 = "chicken_squeak", -- (the launcher's thunk, and the rubber chicken's squeak with it)
		recoilVM = { back = 1.6, up = 6, roll = 1, side = 0.2, punch = 0.03 },
		vm = { p = Vector3.new(0.22, -0.22, -0.42) * S, r = Vector3.new(0, 0.03, 0), s = 0.7 },
		mdl = { lo = Vector3.new(-0.0885, -0.2066, -0.7903), hi = Vector3.new(0.0885, 0.091, 0.622), muzzle = Vector3.new(0, 0, -0.62), grip = Vector3.new(0, -0.1322, 0.0798), fore = Vector3.new(0, -0.134, -0.272),
			parts = { refill = { node = "bird", back = 0.7 } } }, -- (the kit model's, v813: the next chicken's head pokes out of the muzzle)
	},
	banana = {
		id = "banana", name = "Peel Shooter", slot = "primary", kind = "proj", proj = "peel", color = rgb(0xffe135),
		desc = "hard bananas that bonk and make them slip. misses stay on the floor as peels for 12 s.",
		auto = true, cd = 0.3, speed = 42 * S, grav = 18, r = 0.25 * S, dmg = 14, kb = 9 * S, bounce = 0.35, range = 200 * S,
		snd = "banana_fire",
		recoilVM = { back = 0.6, up = 2, roll = 0.8, side = 0.15, punch = 0.008 },
		vm = { p = Vector3.new(0.2, -0.2, -0.4) * S, r = Vector3.new(0, 0.04, 0), s = 0.7 },
		mdl = { lo = Vector3.new(-0.0477, -0.2172, -0.3625), hi = Vector3.new(0.0497, 0.068, 0.226), muzzle = Vector3.new(0, 0, -0.3625), sight = Vector3.new(0, 0.068, 0.0778), grip = Vector3.new(0, -0.0882, 0.0965), fore = Vector3.new(0, -0.004, -0.2) }, -- (the kit model's, v813)
	},
	tennis = {
		id = "tennis", name = "Tennis Ball Launcher", slot = "primary", kind = "proj", proj = "ball", color = rgb(0xd4ff3a),
		desc = "fuzzy balls that bounce up to 5 times and hit harder every bounce. bank it round a corner.",
		cd = 0.5, speed = 40 * S, grav = 14, r = 0.1 * S, bounce = 0.8, dmg = 20, kb = 7 * S, kbUp = 2.5 * S, life = 4.5,
		bounces = 5, bonus = 0.3, minBounce = 3, range = 200 * S,
		snd = "tennis_fire",
		recoilVM = { back = 0.9, up = 3, roll = 0.8, side = 0.15, punch = 0.012 },
		vm = { p = Vector3.new(0.2, -0.2, -0.4) * S, r = Vector3.new(0, 0.04, 0), s = 0.7 },
		mdl = { lo = Vector3.new(-0.08, -0.1889, -0.545), hi = Vector3.new(0.08, 0.2, 0.0448), muzzle = Vector3.new(0, 0.03, -0.545), grip = Vector3.new(0, -0.0837, 0), fore = Vector3.new(0, -0.062, -0.36),
			parts = { refill = { node = "ball", back = 0.4 } } }, -- (the kit model's, v813: the next ball waits in the bore)
	},
	snowball = {
		id = "snowball", name = "Snowball", slot = "secondary", kind = "proj", proj = "snow", color = rgb(0xdff4ff),
		desc = "low damage. 4 hits freeze them solid, one more shatters them.",
		cd = 0.3, speed = 46 * S, grav = 10, r = 0.13 * S, dmg = 9, kb = 3 * S, kbUp = 1.5 * S, life = 3, range = 140 * S,
		freezeAt = 4, freeze = 2.4, frostDecay = 3, snd = "snow_throw",
		recoilVM = { back = 0.3, up = 1.5, roll = 0.5, side = 0.1, punch = 0.004 },
		vm = { p = Vector3.new(0.18, -0.2, -0.36) * S, r = Vector3.new(0, 0, 0), s = 1 },
		mdl = { lo = Vector3.new(-0.069, -0.0494, -0.1481), hi = Vector3.new(0.0731, 0.088, -0.0096), muzzle = Vector3.new(0, 0.02, -0.08), grip = Vector3.new(0, 0.02, -0.08) }, -- (the kit model's, v813: the ball in the hand)
	},
	-- (the owner, 18 Nov 2026: cast from your own hand, no model) a bolt of blood from your fingertip, stylised: a deep red X
	bloodcross = {
		id = "bloodcross", name = "Blood Cross", slot = "secondary", kind = "proj", proj = "blood", color = rgb(0xff1f3d),
		desc = "every shot costs you 12 HP. it sticks in them, a cross bursts out and they pop. a kill pays the blood back.",
		bare = true, cd = 0.7, speed = 75 * S, grav = 0, r = 0.15 * S, life = 2, cost = 12, thin = { cd = 1.1, dmg = 34, heal = 12 },
		fuse = 0.6, burst = 0.25, dmg = 75, blastR = 3 * S, blastDmg = 35, kb = 6 * S, range = 150 * S,
		snd = "blood_fire",
		recoilVM = { back = 0.4, up = 3, roll = 0, side = 0, punch = 0.004 }, -- (a short upward flick of the hand)
		vm = { p = Vector3.new(0.2, -0.2, -0.36) * S, r = Vector3.new(0, 0, 0), s = 1 },
		-- (bare: only these spots are built, the fingertip the bolt leaves from and the hand)
		mdl = { lo = Vector3.new(-0.02, -0.02, -0.1), hi = Vector3.new(0.02, 0.02, 0.02), muzzle = Vector3.new(0, 0, -0.1), grip = Vector3.new(0, 0, 0) },
	},
	-- ------------------------------------------------------------ weapons batch D (18 Nov 2026; WEAPONS.md, the traced spec
	-- weapons-batchD-spec.md). code stand-in models until the kit ones are in (guns-remodel)
	-- rolls along the floor and bowls over everyone in its way, on through them (WeaponProj "bowl")
	bowling = {
		id = "bowling", name = "Bowling Ball Launcher", slot = "primary", kind = "proj", proj = "bowl", color = rgb(0x6b7bff),
		desc = "rolls a bowling ball along the floor. it knocks over everyone in its way and keeps rolling.",
		cd = 1.3, speed = 30 * S, grav = 30, r = 0.45 * S, bounce = 0.25, dmg = 45, kb = 40 * S, kbUp = 10 * S, life = 6, range = 200 * S,
		snd = "gun_bowling", hitSnd = "bowl_hit",
		recoilVM = { back = 2.2, up = 7, roll = 1, side = 0.2, punch = 0.04 },
		vm = { p = Vector3.new(0.22, -0.24, -0.42) * S, r = Vector3.new(0, 0.03, 0), s = 0.65 },
		mdl = { lo = Vector3.new(-0.11, -0.2091, -0.61), hi = Vector3.new(0.11, 0.11, 0.1385), muzzle = Vector3.new(0, 0, -0.5), grip = Vector3.new(0, -0.1099, 0.026), fore = Vector3.new(0, -0.146, -0.255),
			parts = { refill = { node = "ball", back = 1.0 } } }, -- (the kit model's, 76cbc02: the loaded ball goes with the shot)
	},
	-- a boomerang: curves into the nearest enemy ahead, then back to your hand (WeaponProj "slipper")
	slipper = {
		id = "slipper", name = "Slipper", slot = "melee", kind = "proj", proj = "slipper", color = rgb(0xff9ad5),
		desc = "thrown like a boomerang. it curves into the nearest enemy in front of it, then flies back to you. it hits both ways.",
		cd = 0.5, speed = 32 * S, grav = 0, r = 0.3 * S, out = 0.45, back = 38 * S, dmg = 30, kb = 22 * S, kbUp = 6 * S, life = 3,
		homeR = 30 * S, homeCone = 70, homeTurn = 5, outLock = 1, range = 30 * S,
		snd = "slipper_throw", hitSnd = "slipper_hit",
		recoilVM = { back = 0.8, up = 3, roll = 2, side = 0.4, punch = 0.01 },
		vm = { p = Vector3.new(0.22, -0.22, -0.4) * S, r = Vector3.new(0.2, 0.2, -0.1), s = 0.9 },
	},
	-- hits as hard as they deserve (Verdict.luau: x0.4 to x3); right click, a pillar of light on someone far away
	scales = {
		id = "scales", name = "Scales of Justice", slot = "melee", kind = "melee", color = rgb(0xffc83a),
		desc = "damage depends on the target: leaders, streakers and whoever killed you take up to x3. right click calls a pillar of light down on someone far away.",
		cd = 0.6, range = 3.2 * S, cone = 0.75, dmg = 35, kb = 14 * S, kbUp = 5 * S, hitT = 0.22, speedMul = 0.95, verdict = true,
		gavel = { range = 42 * S, cone = 0.16, delay = 1.0, r = 2.3 * S, h = 3.2 * S, dmg = 20, kbUp = 7 * S, cd = 10 },
		swingSnd = "scales_swing", hitSnd = "scales_hit",
		recoilVM = { back = 0.6, up = 2, roll = 1.2, side = 0.3, punch = 0.012 },
		vm = { p = Vector3.new(0.22, -0.24, -0.42) * S, r = Vector3.new(0.3, 0.15, -0.2), s = 0.7 },
	},
	-- ------------------------------------------------------------ weapons batch E (18 Nov 2026; weapons-batchE-spec.md)
	-- hold to spin the loop, let go to throw; catch someone and swing them on the rope (LassoServer, LassoClient)
	lasso = {
		id = "lasso", name = "Lasso", slot = "secondary", kind = "lasso", color = rgb(0xe0b070),
		desc = "hold to spin the loop, let go to throw. catch someone and they swing on your rope: the wheel, r and f reel it. click to let go and they fly. walls and floors hurt.",
		cd = 0.35, range = 28 * S,
		mdl = { parts = { refill = { node = "loop", back = 2.5 } } } :: any, -- (the kit's loop leaves your fist with the throw)
		snd = "lasso_throw",
		recoilVM = { back = 0.6, up = 2, roll = 1, side = 0.3, punch = 0.006 },
		vm = { p = Vector3.new(0.2, -0.22, -0.38) * S, r = Vector3.new(0, 0, 0), s = 0.9 },
	},
	-- fires a shopping cart that runs people over; parked it's cover, and you can hop in (F) and ride it (CartServer)
	cart = {
		id = "cart", name = "Shopping Cart Cannon", slot = "primary", kind = "cart", color = rgb(0x9b5cff),
		desc = "fires a shopping cart that runs people over. it stays as cover, or hop in (f) and ride it.",
		cd = 1.6, speed = 22 * S, up = 3.5 * S, speedMul = 0.93, range = 100 * S,
		snd = "gun_cart",
		recoilVM = { back = 2.6, up = 6, roll = 1, side = 0.2, punch = 0.04 },
		vm = { p = Vector3.new(0.22, -0.24, -0.42) * S, r = Vector3.new(0, 0.03, 0), s = 0.6 },
		mdl = { lo = Vector3.new(-0.1384, -0.221, -0.74), hi = Vector3.new(0.1384, 0.2095, 0.0754), muzzle = Vector3.new(0, 0, -0.66), grip = Vector3.new(0, -0.1382, 0.036), fore = Vector3.new(0, -0.1599, -0.29),
			parts = { refill = { node = "load", back = 1.2 } } }, -- (the kit model's, 724781e: the next cart sits in the mouth till it's fired)
	},
	-- a hand of 5 from a 54-card deck: right click picks, left click plays, R a new hand (CardDeck.server; the cards fly
	-- in WeaponProj "card")
	cards = {
		id = "cards", name = "Card Deck", slot = "secondary", kind = "cards", proj = "card", color = rgb(0xffffff),
		desc = "hold 5 cards. right click picks one, left click plays it, r draws a new hand. spades throw a fan, hearts heal, clubs blast, diamonds dash, aces teleport, picture cards are stronger, jokers are any of them.",
		cd = 0.35, speed = 85 * S, grav = 2, r = 0.26 * S, life = 5.7, dmg = 11, perRank = 0.6, kb = 4 * S, range = 150 * S,
		fanN = 6, fanSpread = 0.16, ultN = 24, ultSpread = 0.9, flick = 2,
		snd = "card_throw",
		recoilVM = { back = 0.4, up = 1.5, roll = 0.5, side = 0.2, punch = 0.004 },
		vm = { p = Vector3.new(0.2, -0.2, -0.36) * S, r = Vector3.new(0, 0, 0), s = 1 },
	},
	-- two machine pistols: left click fires lefty, right click righty; each its own 20 and its own reload (Rules.handKey)
	akimbo = {
		id = "akimbo", name = "Lefty & Righty", slot = "secondary", kind = "hitscan", hands = 2, color = rgb(0x00e5a0),
		desc = "two machine pistols, one per hand. left click fires lefty, right click fires righty, hold both to fire both. they reload one at a time.",
		auto = true, rate = 9, mag = 20, reload = 1.5, pellets = 1, dmg = 6, head = 1.6, spread = 0.045, bloom = 0.003, maxBloom = 0.05,
		kb = 0, recoil = 0.25 * S, kick = 0.012, range = 140 * S, tracer = rgb(0x7dffd0), speedMul = 1.05,
		fx = { brass = true, shake = 0.04 }, snd = "gun_akimbo",
		recoilVM = { back = 0.5, up = 1.8, roll = 1.2, side = 0.2, punch = 0.006 },
		vm = { p = Vector3.new(0.2, -0.2, -0.36) * S, r = Vector3.new(0, 0.03, 0), s = 0.9 },
		mdl = { lo = Vector3.new(-0.028, -0.1499, -0.2), hi = Vector3.new(0.028, 0.086, 0.088), muzzle = Vector3.new(0, 0.03, -0.2), grip = Vector3.new(0, -0.064, 0.035) },
	},
	-- hold to draw, let go to fire; every arrow has a random tip (WeaponProj "arrow")
	bow = {
		id = "bow", name = "Bow", slot = "primary", kind = "bow", proj = "arrow", color = rgb(0xc88a4a),
		desc = "hold to draw, let go to fire. every arrow has a random tip: regular, power, knockback, flame, explosion, gas or sleep.",
		cd = 0.35, drawT = 0.7, speed = 45 * S, speedMax = 115 * S, grav = 8, r = 0.24 * S, dmg = 30, dmgMax = 70, head = 1.5,
		kb = 6 * S, kbUp = 2 * S, life = 4, range = 300 * S,
		snd = "gun_bow", drawSnd = "bow_draw",
		recoilVM = { back = 1.2, up = 3, roll = 0.5, side = 0.2, punch = 0.01 },
		vm = { p = Vector3.new(0.18, -0.2, -0.4) * S, r = Vector3.new(0, 0.05, 0), s = 0.75 },
		mdl = { lo = Vector3.new(-0.0368, -0.4249, -0.0372), hi = Vector3.new(0.0235, 0.4249, 0.1192), muzzle = Vector3.new(0, 0, -0.0075), grip = Vector3.new(-0.012, -0.06, -0.0008), fore = Vector3.new(0, 0, 0.1132) }, -- (the kit model's, 40f47a7: fore = the nocking point)
	},
	-- point and click: left click pauses them, right click rewinds them 2 s (WeaponTricks.server)
	remote = {
		id = "remote", name = "TV Remote", slot = "secondary", kind = "remote", color = rgb(0xff5a8a),
		desc = "point and click. left click pauses them for a second. right click rewinds them to where they were 2 seconds ago.",
		range = 45 * S, cone = 0.09, pause = { dur = 1.2, cd = 3.5 }, rewind = { back = 2, cd = 6 }, speedMul = 1.05,
		snd = "remote_click",
		recoilVM = { back = 0.3, up = 1.5, roll = 0, side = 0, punch = 0.004 },
		vm = { p = Vector3.new(0.2, -0.2, -0.36) * S, r = Vector3.new(0, 0, 0), s = 1 },
	},
	-- (weapons batch B) the Leaf Blower: hold it, everyone in the cone is shoved away from you (0 damage: a fall is yours),
	-- 4 s of fuel that refills when you let go; pointed at the floor, its thrust holds you up
	blower = {
		id = "blower", name = "Leaf Blower", slot = "secondary", kind = "hold", hold = "blow", color = rgb(0xff9a3a),
		desc = "pushes people off the map. point it at the floor and you hover.",
		dmg = 0, range = 16 * S, cone = 0.42, tick = 0.09, push = 5.5 * S, pushUp = 1.2 * S, self = 34 * S, fuel = 4, regen = 0.8,
		snd = "blower_loop",
		vm = { p = Vector3.new(0.2, -0.22, -0.4) * S, r = Vector3.new(0, 0.04, 0), s = 0.7 },
		mdl = {
			lo = Vector3.new(-0.094, -0.11, -0.87), hi = Vector3.new(0.093, 0.224, 0.17),
			muzzle = Vector3.new(0, -0.03, -0.87), grip = Vector3.new(0, 0.2015, 0.06), fore = Vector3.new(0, -0.03, -0.31),
		},
	},
	-- (weapons batch B) the web game's Cigarette as a Roblox-safe Hot Sauce (no tobacco on Roblox; the same gimmick, id
	-- kept): hold to take a swig, let go and you breathe fire for as long as you held it (x1.2, at most 3.6 s); let go
	-- past 3 s or hold past 4.5 s and it burns you instead. the breath pushes you back a little
	cig = {
		id = "cig", name = "Hot Sauce", slot = "secondary", kind = "hold", hold = "breath", color = rgb(0xff7a1a),
		desc = "hold to take a swig, let go to breathe fire for as long as you held it. too long and it burns you instead.",
		dmg = 5, range = 13 * S, cone = 0.42, tick = 0.09, maxCharge = 3, coughAt = 4.5, exhaleMul = 1.2, jet = 6 * S,
		kb = 1.5 * S, kbUp = 0.6 * S, cough = 12,
		snd = "breath_loop",
		vm = { p = Vector3.new(0.16, -0.17, -0.3) * S, r = Vector3.new(0.1, 0.1, 0), s = 1.0 },
		mdl = {
			lo = Vector3.new(-0.026, -0.026, -0.118), hi = Vector3.new(0.026, 0.026, 0.0895),
			muzzle = Vector3.new(0, 0, -0.118), grip = Vector3.new(0, 0, 0.05), -- (the cap forward: guns-remodel 3dd4d82)
		},
	},
	-- (weapons batch B) the Big Laser Pointer: hold to charge (1.2 s, slower on your feet), let go for a beam through
	-- everyone in its line; a tap is a little zap (2 ticks of 5), a full charge 7 ticks of 21
	laser = {
		id = "laser", name = "Big Laser Pointer", slot = "primary", kind = "hold", hold = "beam", color = rgb(0x39ff14),
		desc = "hold to charge it, let go for a beam through everyone in a line. a tap fires a short, weak beam.",
		dmg = 21, range = 120 * S, charge = 1.2, tap = 0.3, cd = 0.45, tick = 0.1, dur = { 0.16, 0.62 }, r = { 0.22 * S, 0.7 * S },
		dmgK = { 5, 21 }, kbK = { 1.5 * S, 7 * S }, kbUp = 1.5 * S, slow = 0.72, speedMul = 0.97,
		snd = "laser_fire", tracer = rgb(0x7dff5a),
		vm = { p = Vector3.new(0.2, -0.22, -0.42) * S, r = Vector3.new(0, 0.03, 0), s = 0.7 },
		mdl = {
			lo = Vector3.new(-0.0475, -0.1705, -0.4205), hi = Vector3.new(0.0475, 0.0535, 0.3635),
			muzzle = Vector3.new(0, 0, -0.42), grip = Vector3.new(0, -0.0984, 0.132), fore = Vector3.new(0, 0, -0.28),
		},
	},
	-- (weapons batch B, 18 Nov 2026) two darts on wires (web secondaries.js zapOne): the server picks the target from
	-- the shot's line, stuns it (Rules.stun: no firing, swinging or guarding; its client stops moving) and chains through
	-- everyone soaked by a Water Pistol near it. fire it soaked and it gets you too
	taser = {
		id = "taser", name = "Taser", slot = "secondary", kind = "zap", color = rgb(0xe8ff3a),
		desc = "two darts on wires: whoever they hit is stunned for a second. it jumps through everyone soaked nearby.",
		cd = 1.25, range = 9 * S, cone = 0.1, dmg = 18, kbUp = 2.5 * S, speedMul = 1.05,
		zap = { stun = 1.0, wet = 1.5, chainR = 9 * S, chainMax = 8, chainStun = 1.0, chainDmg = 12, self = 0.4 },
		snd = "taser_fire", tracer = rgb(0xf0f070),
		recoilVM = { back = 0.8, up = 2.5, roll = 1, side = 0.2, punch = 0.01 },
		vm = { p = Vector3.new(0.165, -0.14, -0.31) * S, r = Vector3.new(0.03, 0.12, -0.1), s = 0.95 },
		mdl = {
			lo = Vector3.new(-0.0305, -0.1487, -0.199), hi = Vector3.new(0.0305, 0.066, 0.1039),
			muzzle = Vector3.new(0, 0.012, -0.172), sight = Vector3.new(0, 0.066, 0.093), grip = Vector3.new(0, -0.068, 0.06),
		},
	},
	katana = {
		id = "katana", name = "Katana", slot = "melee", kind = "melee", color = rgb(0xe8e8f0),
		desc = "grows longer with every kill. hold right click to parry every bullet from the front; a timed swing sends them back twice as hard; parry enough and the blade sends a slash wave.",
		cd = 0.5, range = 2.8 * S, cone = 0.7, dmg = 48, kb = 6 * S, kbUp = 2 * S, grow = 0.5 * S, growMax = 30, hitT = 0.12,
		vm = { p = Vector3.new(0.1, -0.185, -0.44) * S, r = Vector3.new(0.85, -0.7, 0.25), s = 0.85 },
	},
	-- the knife (shared/weapons.js knife, WEAPONS.md "Knife"): fast slashes, right click a heavy stab; from behind (the
	-- victim facing away within about 63 degrees) either hit is x3 and counts as a headshot. the classic modes wear it as
	-- a spoon (gun game's last rung, spoons & grapples: GunSkins "spoon"). 17 Nov 2026
	knife = {
		id = "knife", name = "Knife", slot = "melee", kind = "melee", color = rgb(0xc8d0dc),
		desc = "fast slashes. right click: a heavy stab. from behind, three times the hit.",
		cd = 0.42, range = 2.6 * S, cone = 0.75, dmg = 55, kb = 9 * S, kbUp = 3 * S, hitT = 0.1, backstab = 3, speedMul = 1.1,
		heavy = { dmg = 90, cd = 0.95, range = 2.2 * S, cone = 0.6, kb = 16 * S, kbUp = 4 * S, hitT = 0.29 },
		draw = "draw_knife",
		vm = { p = Vector3.new(0.17, -0.2, -0.42) * S, r = Vector3.new(0.12, -0.22, 0.08), s = 0.85 },
	},
	-- (weapons batch A) home runs along your aim; a swing that finds nobody but the floor or a wall pogos you off it
	bread = {
		id = "bread", name = "Bread", slot = "melee", kind = "melee", color = rgb(0xd9a35b),
		desc = "a huge loaf. home runs people along your aim, and smacking the floor pogos you into the sky.",
		cd = 0.55, range = 4.2 * S, cone = 0.8, dmg = 40, kb = 38 * S, kbUp = 10 * S, hitT = 0.19, pogo = 16 * S,
		draw = "draw_bread", hitSnd = "bread_bonk",
		vm = { p = Vector3.new(0.3, -0.3, -0.42) * S, r = Vector3.new(0.35, 0.2, -0.25), s = 0.55 },
	},
	-- (the owner, 18 Nov 2026: "Bring scythe in as a weapon, balance it especially its dash", then "It's a sniper too
	-- remember") the web game's killstreak Scythe as a loadout melee, toned down (WEAPONS.md "Scythe"): a slow wide reap
	-- (an overhead since the owner's "can you do an overhead with the scythe": Anims swing_scythe / swing_scythe2) that
	-- two-hits, a right-click dash with two charges ("two charges like tracer, a kill recharges the dash like genji, the
	-- dash travels farther!": 12 m, was 8), a recovery, no invulnerability; Q turns it into its rifle (scythe_rifle).
	-- each form a little under the specialist: the Katana up close, the Sniper at range
	scythe = {
		id = "scythe", name = "Scythe", slot = "melee", kind = "melee", color = rgb(0x3ee6c8),
		desc = "a slow, wide overhead reap that kills in two. right click dashes you forward and cuts the first one in your way. q turns it into a rifle.",
		cd = 0.95, range = 3.3 * S, cone = 0.95, dmg = 50, kb = 18 * S, kbUp = 6 * S, hitT = 0.24, speedMul = 0.95,
		dash = { dist = 12 * S, time = 0.28, cd = 6, charges = 2, recover = 0.35, dmg = 25, kb = 18 * S, kbUp = 4 * S, width = 1.4 * S },
		-- (the owner, 18 Nov 2026: "when you scythe it should latch on and send you back! and send them back a bit too")
		latch = { t = 0.15, back = 8.5 * S, backUp = 5 * S, push = 6 * S, pushUp = 3 * S, finisher = 1.5, chain = 4, dummy = 3 },
		form = { to = "scythe_rifle", time = 0.45, fireDelay = 0.15, swingLock = 0.6, shotLock = 0.35 },
		draw = "draw_scythe", hitSnd = "scythe_hit", swingSnd = "scythe_swing",
		recoilVM = { back = 0.6, up = 2, roll = 1.2, side = 0.3, punch = 0.012 },
		vm = { p = Vector3.new(0.22, -0.25, -0.44) * S, r = Vector3.new(0.3, 0.15, -0.2), s = 0.6 },
		-- (GunParts: the blade and scope move across in a switch, each about its own root `at`; cf = this form -> the
		-- other. no file bounds here: the kit model brings its own)
		mdl = { parts = { form = { set = {
			blade = { cf = SCYTHE_TURN, at = Vector3.new(0.012, 0.02, -1.218) },
			scope = { cf = CFrame.new(0, 0.0645, 0), at = Vector3.new(0, 0.013, -0.24) },
		} } } } :: any,
	},
	-- the Scythe's second form: the blade slides back down the haft and turns under it as the stock, the collar is the
	-- muzzle and a short scope comes up. no one-shot headshot, no big shove: under the Sniper at range
	scythe_rifle = {
		id = "scythe_rifle", name = "Scythe", slot = "melee", kind = "hitscan", color = rgb(0x3ee6c8), formOf = "scythe",
		desc = "the scythe's rifle form. right click to scope. q turns it back into the scythe.",
		auto = false, rate = 1 / 1.0, mag = 4, reload = 2.0, pellets = 1, dmg = 45, head = 1.8, spread = 0.06,
		kb = 30 * S, kbUp = 8 * S, recoil = 10 * S, kick = 0.06, range = 400 * S,
		ads = { zoom = 3, spread = 0, scope = true }, tracer = rgb(0x3ee6c8), thick = 0.07 * S,
		fx = { big = true, shake = 0.4 }, snd = "gun_scythe",
		form = { to = "scythe", time = 0.45, fireDelay = 0.15, swingLock = 0.6, shotLock = 0.35 },
		draw = "form_scythe",
		recoilVM = { back = 2.5, up = 9, roll = 1.6, side = 0.2, punch = 0.06 },
		vm = { p = Vector3.new(0.2, -0.22, -0.4) * S, r = Vector3.new(0, 0.03, 0), s = 0.5 },
		mdl = { parts = { form = { set = {
			blade = { cf = SCYTHE_TURN:Inverse(), at = Vector3.new(0, 0.012, 0.114) },
			scope = { cf = CFrame.new(0, -0.0645, 0), at = Vector3.new(0, 0.0775, -0.24) },
		} } } } :: any,
	},
	-- (weapons batch A) point blank, barely hurts: shoves them straight away from you and they slip
	slapper = {
		id = "slapper", name = "Hand Slapper", slot = "melee", kind = "melee", color = rgb(0xff7ab8),
		desc = "a giant toy hand on a stick. point blank only, low damage, sends them flying and off their feet.",
		cd = 0.8, range = 1.9 * S, cone = 0.8, dmg = 15, kb = 55 * S, kbUp = 14 * S, hitT = 0.17, slip = true, radial = true,
		draw = "draw_melee", hitSnd = "slap_hit", swingSnd = "slap_whoosh",
		vm = { p = Vector3.new(0.22, -0.24, -0.42) * S, r = Vector3.new(0.25, 0.1, 0), s = 0.7 },
	},
	-- the zombie claw (shared/weapons.js claw): infection's only weapon, handed out by the mode, never in a loadout
	claw = {
		id = "claw", name = "Zombie Claw", slot = "mode", kind = "melee", color = rgb(0x7dff4f),
		desc = "infection only. two swipes and they turn.",
		cd = 0.45, range = 2.6 * S, cone = 0.85, dmg = 55, kb = 8 * S, kbUp = 3 * S, hitT = 0.1, speedMul = 1.3,
		bare = true, -- (your own hands, tinted green while you're a zombie: AvatarArms + Modes' ZombieTint)
		vm = { p = Vector3.new(0.18, -0.22, -0.4) * S, r = Vector3.new(0.05, -0.15, 0), s = 0.85 },
	},
	-- kill credit only: bullets parried back, parry shoves into the smog
	parry = { id = "parry", name = "Katana Parry", slot = "none", kind = "parry", color = rgb(0x9fe8ff), desc = "", dmg = 0, range = 0 },
	-- the Shredder is a Tool of its own (key 4, StarterPack); this entry only names it in the kill feed
	shredder = { id = "shredder", name = "Shredder", slot = "none", kind = "shredder", color = rgb(0xffb31a), desc = "", dmg = 0, range = 0 },
	-- the grapple tied to a person (18 Nov): a fall or a hazard soon after is the hooker's kill; this entry only names it
	grapple = { id = "grapple", name = "Grapple", slot = "none", kind = "grapple", color = rgb(0xc8ccd2), desc = "", dmg = 0, range = 0 },
	-- the t-bag (18 Nov: 14 crouches in 4 s, your knees explode, TBag.server): its blast's kills and your own death
	tbag = { id = "tbag", name = "T-Bag", slot = "none", kind = "tbag", color = rgb(0xff8a3a), desc = "", dmg = 0, range = 0 },
	-- (the Overdrive Rig gadget, 19 Nov 2026, Rig.server: its punch and missiles, for the kill feed and WeaponProj. the
	-- missile: up for `boost` s, then it homes, `turn` rad/s, speed to speedMax, goes off within `fuse` of its target)
	rig_punch = { id = "rig_punch", name = "Rocket Punch", slot = "none", kind = "rig", color = rgb(0xff2a6d), desc = "", dmg = 0, range = 0 },
	rig_missile = { id = "rig_missile", name = "Rig Missile", slot = "none", kind = "rig", proj = "rigmissile", color = rgb(0xff6a3d), desc = "",
		dmg = 16, radius = 3.2 * S, kb = 12 * S, selfKb = 0, r = 0.25 * S, speed = 16 * S, speedMax = 44 * S, turn = 4.2, boost = 0.25,
		life = 5, fuse = 1.4 * S, range = 200 * S, grav = 0 } :: any,
}

local Weapons = {
	S = S,
	list = W,
	loadout = { "redline", "marbles", "katana" }, -- keys 1, 2, 3
	-- katana right click (shared/weapons.js PARRY): times in s, arc = the full front cone in degrees. (owner, 18 Nov
	-- 2026: "allow katana parry to parry as many bullets") the guard stays up while right click is held, up to `hold` s
	-- (a tap still gives `win`), and blocks every bullet and pellet from the front in it; its first `perfect` s send
	-- them home. the cooldown after it grows with how long it was held: `cd` after a tap, cd + `holdCd` after a full
	-- hold. while held, its front follows your look (`turn` updates a second). docs/KATANA.md
	PARRY = { win = 0.35, hold = 1.5, perfect = 0.15, cd = 0.8, holdCd = 0.6, slack = 0.05, arc = 140, turn = 10,
		shove = 14 * S, shoveUp = 5 * S, stagger = 0.55, perfectMul = 1.4 },
	-- a katana swing as a counter (owner: "if you manually swing it to counter bullets it does a crit return!"; called
	-- Return to Sender in docs/KATANA.md, never on screen): bullets from the swing's front arc that reach you `from` to
	-- `to` s after the click (the blade's sweep, + `slack` for the network) go back into the shooter at `mul` x their
	-- damage, credited to the katana (as "parry")
	CRIT = { from = 0.02, to = 0.2, slack = 0.04, arc = 110, mul = 2 },
	-- the edge meter: what you parry fills it, in points = the stopped hit's damage x block / perfect / crit (a melee
	-- swing parried: melee / meleePerfect). full at `max`, x `train` in training; emptied by the wave or a death
	EDGE = { max = 240, block = 1, perfect = 1.25, crit = 1.5, melee = 30, meleePerfect = 40, train = 3 },
	-- the slash wave with a full meter (owner: "build enough parry and you can send a large forward slash"; called Cold
	-- Front in docs/KATANA.md, never on screen): a wide ice-blue crescent leaves `windup` s after the key, flies `speed`
	-- studs/s along your look (pitch kept within +-`pitch` degrees) for up to `range` studs, stops at the first wall on
	-- its line, and hurts up to `pierce` enemies it passes through (each once) for `dmg`, shoving them along it. a guard
	-- in front of it breaks it. hit box: `width` studs side to side, `height` up and down round its line. `lock` s with
	-- no swing or guard for the caster
	WAVE = { windup = 0.12, lock = 0.45, speed = 60 * S, range = 40 * S, width = 6 * S, height = 2 * S, dmg = 70, pierce = 3,
		kb = 9 * S, kbUp = 4 * S, pitch = 20 },
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

-- the loadout weapon a row belongs to: a second form's own (the Scythe's rifle is the Scythe), else itself. its kills,
-- hits and time held count there (Combat, Stats)
function Weapons.base(wid: string): string
	local w = (Weapons.list :: any)[wid]
	return if w and w.formOf then w.formOf else wid
end

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
function Weapons.damage(w: Weapon, n: number, h: number, hp: number?): number
	local d = Weapons.shotDmg(w, hp)
	return d * (n - h) + d * (w.head or 1) * h
end

-- one bullet's damage before the head multiplier, at the shooter's HP (nil = the row's dmg). the Redline's past
-- `over.at` shots a second keeps only `over.keep` of the extra rate as damage: 10 a shot up to 12/s, 9.0 at 14/s
-- (50 HP), 7.0 at 20.4/s (10 HP). rounded up to a tenth, so the hits to kill stay whole (15 x 7.0, not 17 x 5.88)
function Weapons.shotDmg(w: Weapon, hp: number?): number
	local o = w.over
	if not o or hp == nil then return w.dmg end
	local r = Weapons.fireRate(w, hp)
	if r <= o.at then return w.dmg end
	return math.ceil(w.dmg * (o.at + (r - o.at) * o.keep) / r * 10 - 1e-6) / 10
end

-- the Revolver's k-th fanned shot in a row (1 = the first after the tap): its damage and its spread (Combat rolls it)
function Weapons.fanShot(w: Weapon, k: number): (number, number)
	local F = w.fan :: any
	local i = math.max(1, math.floor(k)) - 1
	return F.dmg * (F.fall or 1) ^ i, math.min(F.maxSpread or F.spread, F.spread + (F.grow or 0) * i)
end

-- the shove a gun's hit gives its victim (web room.js applyHitscan): kb a pellet along the shot, kbUp x the share of
-- the pellets that landed. dir = shooter -> victim, extra = more along the shot (the Second Opinion's quick-scope)
function Weapons.gunKb(w: Weapon, n: number, dir: Vector3, extra: number?): Vector3?
	local k = (w.kb or 0) * n + (extra or 0)
	local up = (w.kbUp or 0) * n / (w.pellets or 1)
	if k <= 0 and up <= 0 then return nil end
	return dir * k + Vector3.new(0, up, 0)
end

-- seconds between two shots inside a Hat Trick burst, and the longest stretch that may hold one whole burst
function Weapons.burstSpan(w: Weapon): number
	return ((w.burst or 1) - 1) / (w.rate or 1) + (w.burstGap or 0) * 0.8
end

return Weapons
