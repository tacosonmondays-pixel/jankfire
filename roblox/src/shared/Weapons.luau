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
	fan: { rate: number, hold: number, dmg: number, spread: number, kick: number }?, ricochet: number?, -- the Revolver
	heatUp: number?, heatDown: number?, -- the Belt Sander's barrel (looks and sound only)
	cycle: { clip: string, at: number }?, draw: string?, -- the clip after every shot (pump, bolt, lever), its own draw
	-- melee
	cd: number?, cone: number?, kb: number?, kbUp: number?, grow: number?, growMax: number?, hitT: number?,
	recoilVM: { back: number, up: number, roll: number, side: number, punch: number }?,
	vm: { p: Vector3, r: Vector3, s: number }?, -- viewmodel rest pose (camera space, studs / radians)
	-- how a gun looks and sounds when it fires (all optional). the gun code in Arsenal reads these, so a plain gun is
	-- one row here + a model + a sound, with no code of its own. big = the big muzzle flash, brass = a casing a shot,
	-- spray = the pellets are the tracer (the marbles), hole = false: chips, not holes. snd = the shot's Sound in
	-- JankfireSounds; tacho = the Redline's three renders by HP instead
	fx: { big: boolean?, brass: boolean?, spray: boolean?, hole: boolean?, scale: number?, shake: number?, splash: boolean?, vol: number? }?,
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

local W: { [string]: Weapon } = {
	redline = {
		id = "redline", name = "Redline", slot = "primary", kind = "hitscan", color = rgb(0xff3b3b),
		desc = "the lower your HP, the faster it fires. full health it plods, 10 HP it screams. watch the needle.",
		auto = true, rate = 6, rateMax = 22, mag = 40, reload = 1.8, pellets = 1, dmg = 10, head = 1.8, spread = 0.018,
		bloom = 0.0025, maxBloom = 0.06, recoil = 0.3 * S, kick = 0.006, range = 250 * S,
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
	},
	-- ---- batch 3, the plain guns (WEAPONS.md): data only. stats from shared/weapons.js, vm + recoilVM from
	-- public/js/weapons.js (VM, RECOIL), mdl from the export report and the web model's spots
	ar = {
		id = "ar", name = "Assault Rifle", slot = "primary", kind = "hitscan", color = rgb(0x9fd36b),
		desc = "full auto, steady, a laser when you aim. the honest gun. somebody has to be.",
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
		},
	},
	smg = {
		id = "smg", name = "SMG", slot = "primary", kind = "hitscan", color = rgb(0x6bd3c8),
		desc = "sprays fast, weighs nothing, and you run faster holding it. aiming is optional, enthusiasm isn't.",
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
		desc = "ten pellets of close-range bad news. shoot the floor and it throws you into the sky.",
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
		desc = "right click to scope. a headshot always kills, a body shot sends them flying off the map. hipfire is a gamble.",
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
		id = "burst", name = "Hat Trick", slot = "primary", kind = "hitscan", color = rgb(0x4f8bff),
		desc = "a bullpup that fires three at a time. land all three on one person for a BURST!. very accurate, very french.",
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
		id = "lmg", name = "Belt Sander", slot = "primary", kind = "hitscan", color = rgb(0xff5a1f),
		desc = "a hundred rounds on a belt you can watch run out. slow to aim, slow to reload, sands people down.",
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
		id = "dmr", name = "Second Opinion", slot = "primary", kind = "hitscan", color = rgb(0xb07dff),
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
		id = "lever", name = "Yeehaw", slot = "primary", kind = "hitscan", color = rgb(0xa58640), -- (its calm accent: the brass)
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
		id = "autoshot", name = "Lawn Mower", slot = "primary", kind = "hitscan", color = rgb(0x4ad66b),
		desc = "an automatic shotgun with a box mag. less per shot than the pump, but it never stops. mows lawns. and people.",
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
	revolver = {
		id = "revolver", name = "Revolver", slot = "secondary", kind = "hitscan", color = rgb(0xe0c070),
		desc = "six shots, a twirl after every one. tap for a dead-accurate shot, hold to fan the hammer. bullets bounce off walls twice.",
		auto = false, rate = 1 / 0.4, mag = 6, reload = 2.0, pellets = 1, dmg = 40, head = 2.4, spread = 0.003,
		recoil = 3 * S, kick = 0.07, range = 250 * S, ricochet = 2,
		fan = { rate = 6, hold = 0.2, dmg = 28, spread = 0.065, kick = 0.3 },
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
		id = "pistol", name = "Plan B", slot = "secondary", kind = "hitscan", color = rgb(0xa0b4ff),
		desc = "a plain pistol for when plan A runs dry. 12 shots, the slide locks back so you know you're empty.",
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
		id = "sawnoff", name = "Half a Shotgun", slot = "secondary", kind = "hitscan", color = rgb(0xe05a3a),
		desc = "somebody sawed a shotgun in half. two shells, point blank they go flying, shoot the floor for a little hop.",
		auto = false, rate = 1 / 0.3, mag = 2, reload = 2.3, pellets = 12, dmg = 9, head = 1.3, spread = 0.11,
		kb = 3.4 * S, kbUp = 9 * S, recoil = 10 * S, kick = 0.09, range = 32 * S,
		ads = { zoom = 1.12, spread = 0.7 }, tracer = rgb(0xffa060),
		fx = { big = true, shake = 0.5 }, snd = "gun_sawnoff", draw = "draw_sawnoff",
		recoilVM = { back = 3.4, up = 16, roll = 3.5, side = 0.35, punch = 0.085 },
		vm = { p = Vector3.new(0.19, -0.18, -0.34) * S, r = Vector3.new(0, 0.05, 0), s = 0.85 },
		mdl = {
			lo = Vector3.new(-0.0241, -0.1012, -0.311), hi = Vector3.new(0.0241, 0.0569, 0.1469),
			muzzle = Vector3.new(0, 0.02, -0.31), sight = Vector3.new(0, 0.037, 0.075),
			grip = Vector3.new(0, -0.05, 0.095),
			parts = {
				hinge = { at = Vector3.new(0, -0.002, -0.05), open = 0.7, nodes = { "hinge", "hinge_trim", "forend", "forend_iron", "shell1", "shell2" } },
				shells = { "shell1", "shell2" },
				hammers = { { node = "hammerR", at = Vector3.new(0.013, 0.028, 0.054) }, { node = "hammerL", at = Vector3.new(-0.013, 0.028, 0.054) } },
			},
		},
	},
	katana = {
		id = "katana", name = "Katana", slot = "melee", kind = "melee", color = rgb(0xe8e8f0),
		desc = "grows longer with every kill. right click parries; a perfect parry sends the bullets home.",
		cd = 0.5, range = 2.8 * S, cone = 0.7, dmg = 48, kb = 6 * S, kbUp = 2 * S, grow = 0.5 * S, growMax = 30, hitT = 0.12,
		vm = { p = Vector3.new(0.1, -0.185, -0.44) * S, r = Vector3.new(0.85, -0.7, 0.25), s = 0.85 },
	},
	-- kill credit only: bullets parried back, parry shoves into the smog
	parry = { id = "parry", name = "Katana Parry", slot = "none", kind = "parry", color = rgb(0x9fe8ff), desc = "", dmg = 0, range = 0 },
	-- the Shredder is a Tool of its own (key 4, StarterPack); this entry only names it in the kill feed
	shredder = { id = "shredder", name = "Shredder", slot = "none", kind = "shredder", color = rgb(0xffb31a), desc = "", dmg = 0, range = 0 },
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
