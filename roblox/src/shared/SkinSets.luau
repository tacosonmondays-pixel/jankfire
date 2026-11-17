--!strict
-- SKIN SETS (16 Nov 2026, the owner: "can the weapon skins, not all of them but a couple, be like sets? Halloween
-- style. maybe demon vs angels, maybe japanese like"). A set is a family of weapon skins that read as one at a glance:
-- one name prefix, one palette, one motif placed the same way on every piece, one glow colour (the logic from the
-- vault note Research/Rivals skin sets.md: a line of about five skins over primary, secondary and melee; the top piece
-- the biggest reshape with the glow). Heaven and Hell is a PAIR: the same five weapons twice, the same layout with the
-- motifs swapped (halo / horns, feathered / bat wings, gold trim / ember seams).
-- The models are ordinary weapon skins (GunSkins.luau; built by tools/roblox/gun_sets*.py, in
-- ReplicatedStorage.JankfireSkins); this module only says which skins make a set and what they are called.
--   SkinSets.SETS[setId]   = { name, pair?, colour (the banner's), members = { skin id, ... } }
--   SkinSets.SKINS[skinId] = { name, rarity, weapon, set, tier }   (the loot session merges these into LootTable.SKINS)
--   SkinSets.TIER[skinId]  = "basic" | "mid" | "high", for EVERY weapon skin (the sets' and the 26 older ones)
--   SkinSets.FX[skinId]    = the high tier's effects spec (the VFX session's Fx plays it)
-- TIERS (16 Nov, the owner: "basic tier can be simple modifications, mid tiers can be like new models, high tiers will be
-- remodeled with vfx"): basic = the base gun with small changes (parts swapped, trims, a stock or muzzle, colour
-- blocking); mid = a new model; high = a full remodel plus effects that live on the gun (an idle glow, particles drifting
-- off it, its own muzzle flash and tracer). A set skin's rarity follows its tier (basic = rare, mid = epic, high =
-- legendary); the older skins keep their web rarities and get a tier for the card.
local SkinSets = {}

export type SetInfo = { name: string, pair: string?, vip: boolean?, colour: Color3, accent: Color3, order: number, members: { string } }

SkinSets.SETS = {
	set_seraph = {
		name = "Seraph", pair = "set_infernal", order = 1,
		colour = Color3.fromRGB(221, 216, 204), accent = Color3.fromRGB(255, 212, 110),
		members = { "ar_seraph", "sniper_seraph", "burst_seraph", "pistol_seraph", "katana_seraph" },
	},
	set_infernal = {
		name = "Infernal", pair = "set_seraph", order = 2,
		colour = Color3.fromRGB(35, 32, 37), accent = Color3.fromRGB(255, 90, 30),
		members = { "ar_infernal", "sniper_infernal", "burst_infernal", "pistol_infernal", "katana_infernal" },
	},
	set_halloween = { -- Halloween: deep purple-black, bone ivory, pumpkin, one warm candle glow (a sickly green on the brew)
		name = "Witching Hour", order = 3,
		colour = Color3.fromRGB(44, 38, 51), accent = Color3.fromRGB(255, 156, 69),
		members = { "smg_pumpkin", "marbles_cauldron", "katana_hex", "revolver_candle", "shotgun_bone" },
	},
	set_tidecrest = { -- Japanese maki-e (17 Nov, the owner's pick, J-A): black lacquer and gold, a gold tortoiseshell
		-- ground on every black field, gold rims, a red sea-wave handguard, an inlaid vine, one flowering gold branch
		-- (tools/roblox/gun_sets_japan2.py; the keys stay, so owners keep their pieces)
		name = "Tidecrest", order = 4,
		colour = Color3.fromRGB(42, 37, 38), accent = Color3.fromRGB(217, 187, 114),
		members = { "katana_sakura", "ar_lacquer", "lever_cloudlock", "dmr_nighttide", "sawnoff_twintide" },
	},
	set_ducky = { -- VIP (the owner: "the ducky set is a high tier set you get by purchasing vip"): the VIP pack's skins,
		-- never in crates or the shop. A magical-girl kawaii rubber-duck line ("can you make the duck magical kawaii girl
		-- kinda thing"): each gun shaped AS a duck, a pink bow with a gold star clip, pearl wings, glowing heart gems
		name = "Ducky", order = 5, vip = true,
		colour = Color3.fromRGB(214, 189, 74), accent = Color3.fromRGB(192, 106, 46),
		members = { "lmg_ducky", "revolver_ducky", "katana_ducky" },
	},
	-- SPACE WESTERN, a pair (17 Nov, the owner, after seeing a frontier skin line elsewhere: a classic and a futuristic look
	-- of the same weapons; ours is our own): Dust Drover is the frontier (case iron, walnut, brass, a 7-point star, a horse,
	-- a train, a wagon wheel, a spyglass, a horseshoe); Star Drover the same five built in the far future (plum graphite,
	-- tan ceramic, brass, teal hard light). Models: tools/roblox/gun_sets_west.py
	set_dust = {
		name = "Dust Drover", pair = "set_star", order = 6,
		colour = Color3.fromRGB(107, 74, 50), accent = Color3.fromRGB(196, 164, 99),
		members = { "revolver_dust", "lever_dust", "sawnoff_dust", "sniper_dust", "katana_dust" },
	},
	set_star = {
		name = "Star Drover", pair = "set_dust", order = 7,
		colour = Color3.fromRGB(62, 53, 70), accent = Color3.fromRGB(69, 230, 214),
		members = { "revolver_star", "lever_star", "sawnoff_star", "sniper_star", "katana_star" },
	},
} :: { [string]: SetInfo }

-- id = { name, rarity, weapon, set, tier }. In the pair the rifle is the headline (the high tier: remodel + effects)
SkinSets.SKINS = {
	ar_seraph = { "Seraph Rifle", "legendary", "ar", "set_seraph", "high" },
	katana_seraph = { "Seraph Katana", "epic", "katana", "set_seraph", "mid" },
	sniper_seraph = { "Seraph Sniper", "epic", "sniper", "set_seraph", "mid" },
	burst_seraph = { "Seraph Hat Trick", "epic", "burst", "set_seraph", "mid" },
	pistol_seraph = { "Seraph Plan B", "rare", "pistol", "set_seraph", "basic" },
	ar_infernal = { "Infernal Rifle", "legendary", "ar", "set_infernal", "high" },
	katana_infernal = { "Infernal Katana", "epic", "katana", "set_infernal", "mid" },
	sniper_infernal = { "Infernal Sniper", "epic", "sniper", "set_infernal", "mid" },
	burst_infernal = { "Infernal Hat Trick", "epic", "burst", "set_infernal", "mid" },
	pistol_infernal = { "Infernal Plan B", "rare", "pistol", "set_infernal", "basic" },
	smg_pumpkin = { "Pumpkin Patch", "legendary", "smg", "set_halloween", "high" },
	marbles_cauldron = { "Cauldron", "epic", "marbles", "set_halloween", "mid" },
	katana_hex = { "Hex Blade", "epic", "katana", "set_halloween", "mid" },
	revolver_candle = { "Vigil", "epic", "revolver", "set_halloween", "mid" },
	shotgun_bone = { "Gravekeeper", "rare", "shotgun", "set_halloween", "basic" },
	katana_sakura = { "Sakura", "legendary", "katana", "set_tidecrest", "high" },
	ar_lacquer = { "Yoroi", "epic", "ar", "set_tidecrest", "mid" },
	lever_cloudlock = { "Cloudlock", "epic", "lever", "set_tidecrest", "mid" },
	dmr_nighttide = { "Kintsugi", "rare", "dmr", "set_tidecrest", "basic" },
	sawnoff_twintide = { "Twin Tide", "rare", "sawnoff", "set_tidecrest", "basic" },
	lmg_ducky = { "Bubble Bath", "legendary", "lmg", "set_ducky", "high" },
	revolver_ducky = { "Wish Duck", "legendary", "revolver", "set_ducky", "high" },
	katana_ducky = { "Ribbon Duck", "legendary", "katana", "set_ducky", "high" },
	revolver_dust = { "Dust Drover", "legendary", "revolver", "set_dust", "high" },
	lever_dust = { "Iron Horse", "legendary", "lever", "set_dust", "high" },
	sawnoff_dust = { "Wagon Wheel", "epic", "sawnoff", "set_dust", "mid" },
	sniper_dust = { "Brass Spyglass", "epic", "sniper", "set_dust", "mid" },
	katana_dust = { "Horseshoe", "rare", "katana", "set_dust", "basic" },
	revolver_star = { "Star Drover", "legendary", "revolver", "set_star", "high" },
	lever_star = { "Streamliner", "legendary", "lever", "set_star", "high" },
	sawnoff_star = { "Warp Wheel", "epic", "sawnoff", "set_star", "mid" },
	sniper_star = { "Star Spyglass", "epic", "sniper", "set_star", "mid" },
	katana_star = { "Star Horseshoe", "rare", "katana", "set_star", "basic" },
} :: { [string]: { any } }

SkinSets.TIERS = {
	basic = { name = "Basic", rarity = "rare", order = 1 },
	mid = { name = "Mid", rarity = "epic", order = 2 },
	high = { name = "High", rarity = "legendary", order = 3 },
}

-- every weapon skin's tier: the sets' from SKINS, the 26 older ones here (most are new models; three are the base gun
-- with small changes)
SkinSets.TIER = {
	sniper_golden = "basic", katana_bokken = "basic", katana_shirasaya = "basic",
	ar_toy = "mid", ar_bullpup = "mid", ar_keytar = "mid", smg_uzi = "mid", smg_label = "mid", burst_ticket = "mid",
	lmg_leaf = "mid", dmr_pen = "mid", autoshot_trimmer = "mid", sniper_musket = "mid", sniper_cue = "mid",
	lever_capgun = "mid", shotgun_double = "basic", shotgun_umbrella = "mid", sawnoff_pepper = "mid",
	marbles_gumball = "mid", redline_hotrod = "mid", pistol_calc = "mid", revolver_flint = "mid", revolver_drill = "mid",
	katana_baguette = "mid", katana_neon = "mid", shredder_chipper = "mid",
} :: { [string]: string }
-- the VIP daily reward's sniper (17 Nov 2026): the Triangulum, a high-tier skin in no set and not a concept (the shop
-- session's VipDailyData.EXCLUSIVE marks it daily-only; the loot session lists it in LootTable.SKINS)
SkinSets.TIER.sniper_triangulum = "high"
for id, row in SkinSets.SKINS do SkinSets.TIER[id] = row[5] end

-- the older skins remodelled on 16 Nov (after a review of every skin) that took a new name (the loot session's
-- LootTable.SKINS holds their names: it applies these)
SkinSets.RENAME = { smg_uzi = "Hairdryer", sawnoff_pepper = "Double Chili" } :: { [string]: string }

-- the cute-set concepts in the game for the owner to choose from (not sold, not in crates; one becomes the set)
-- (cute v3, 17 Nov: A-D rebuilt with bigger signature pieces, tools/roblox/gun_sets_cute3.py; E Daydream dropped)
SkinSets.CONCEPTS = { "ar_cute_a", "pistol_cute_a", "ar_cute_b", "pistol_cute_b", "ar_cute_c", "pistol_cute_c",
	"ar_cute_d", "pistol_cute_d",
	-- the Ducklings (17 Nov, the owner: "Can you also tell it to make a few blender ducky skins?"): Wish Duck's family
	-- built with the Blender-artist method and its baked shade shells (tools/roblox/gun_sets_ducky_art.py)
	"ar_duckling", "smg_duckling", "pistol_duckling" } :: { string }

-- THE HIGH TIER'S EFFECTS (played by the VFX session's Fx; the owner: "the angel gun can have cool angel themed design
-- white and gold with a black and gold glow and maybe feathers coming off it"). Points are in the gun's frame in
-- metres (x right, y up, z back, the muzzle toward -z), mirrored to both sides where `both` is set. Cheap: a few slow
-- particles at a time, none in front of the sights
SkinSets.FX = {
	ar_seraph = {
		idle = {
			{ kind = "feather", colour = Color3.fromRGB(245, 240, 228), rate = 4.5, life = 1.8, size = 0.035, drift = "fall",
				at = { { 0.103, 0.088, 0.512 }, { 0.13, 0.113, 0.646 }, { 0.089, -0.016, 0.536 } }, both = true }, -- (shed off the glowing wing edges)
			{ kind = "sparkle", colour = Color3.fromRGB(255, 212, 110), rate = 3, life = 0.8, size = 0.012, drift = "rise",
				at = { { 0, 0.165, 0.005 } } },
		},
		glow = { colour = Color3.fromRGB(255, 200, 90), dark = Color3.fromRGB(20, 18, 14) }, -- a gold glow edged in black
		-- a short glowing trail off each wing's top feather as the gun moves (the owner: "the glowing parts can have a bit of
		-- a trail as you move"): a Trail between the two points of each seg, mirrored with both
		trail = { colour = Color3.fromRGB(255, 214, 120), life = 0.18, width0 = 0.03, width1 = 0,
			segs = { { { 0.084, 0.071, 0.416 }, { 0.13, 0.11, 0.646 } } }, both = true },
		flash = Color3.fromRGB(255, 226, 150), tracer = Color3.fromRGB(255, 205, 95),
		bullet = { kind = "feathers" }, -- (its bullet trail, Fx.bulletTrail: a gold-white streak shedding white feathers, a gold flare where it lands)
	},
	ar_infernal = {
		idle = {
			{ kind = "ember", colour = Color3.fromRGB(255, 110, 40), rate = 3, life = 1.2, size = 0.012, drift = "rise",
				at = { { 0.036, 0.022, -0.07 }, { 0.1, 0.06, 0.55 } }, both = true },
			{ kind = "haze", colour = Color3.fromRGB(60, 40, 36), rate = 1, life = 1.5, size = 0.06, drift = "rise",
				at = { { 0, 0.04, -0.62 } }, afterFire = true }, -- a faint heat shimmer off the barrel after firing
		},
		glow = { colour = Color3.fromRGB(255, 90, 30) },
		trail = { colour = Color3.fromRGB(255, 96, 34), life = 0.18, width0 = 0.03, width1 = 0,
			segs = { { { 0.075, 0.06, 0.418 }, { 0.126, 0.077, 0.672 } } }, both = true },
		flash = Color3.fromRGB(255, 120, 50), tracer = Color3.fromRGB(255, 80, 30),
		bullet = { kind = "ember" }, -- (an orange core, a dark smoke wisp, falling sparks; an ember burst)
	},
	smg_pumpkin = { -- a thin curl of smoke out of the jack-o'-lantern's face, embers out of the receiver's carved grin
		idle = {
			{ kind = "haze", colour = Color3.fromRGB(179, 165, 151), rate = 0.5, life = 1.1, size = 0.02, drift = "rise",
				at = { { -0.052, -0.14, -0.125 } } },
			{ kind = "ember", colour = Color3.fromRGB(255, 156, 69), rate = 1.5, life = 0.9, size = 0.008, drift = "rise",
				at = { { -0.03, 0.004, -0.07 }, { -0.03, 0.006, -0.03 } } },
		},
		glow = { colour = Color3.fromRGB(255, 156, 69) },
		flash = Color3.fromRGB(255, 156, 69), tracer = Color3.fromRGB(255, 156, 69),
		bullet = { kind = "wisp" }, -- (an orange flame wisp, gently curved; a grey puff at the muzzle every third shot)
	},
	-- the Ducky VIP set (v3, 17 Nov: Bubble Bath and Ribbon Duck redone in Wish Duck's clean style, one shared rubber-duck
	-- bill on all three): sparkles off the heart gems and the bow's star clip, soap bubbles from the bill (a puff after a
	-- burst), a pink-gold trail, a soft pink-gold flash, a pink tracer
	lmg_ducky = {
		idle = {
			{ kind = "sparkle", colour = Color3.fromRGB(246, 215, 138), rate = 3, life = 0.6, size = 0.012, drift = "rise",
				at = { { -0.096, -0.149, -0.137 }, { -0.096, -0.149, -0.089 }, { -0.096, -0.149, -0.041 }, -- the heart box (rides the mag)
					{ -0.072, 0.041, -0.51 } } }, -- the bow's star clip, left of the head
			{ kind = "bubble", colour = Color3.fromRGB(241, 228, 234), rate = 0.8, life = 1.6, size = 0.018, drift = "rise",
				at = { { -0.04, 0.014, -0.66 }, { -0.02, 0.03, -0.684 } } }, -- the bill's left mouth corner and tip
			{ kind = "bubble", colour = Color3.fromRGB(241, 228, 234), rate = 6, life = 1.2, size = 0.014, drift = "rise",
				at = { { -0.04, 0.014, -0.66 }, { -0.02, 0.03, -0.684 } }, afterFire = true }, -- a puff after a burst
		},
		glow = { colour = Color3.fromRGB(242, 122, 168) },
		trail = { colour = Color3.fromRGB(247, 182, 205), life = 0.4, width0 = 0.02, width1 = 0,
			segs = { { { -0.048, 0.037, 0.014 }, { -0.049, 0.052, 0.105 } } } }, -- the left wing's gold edge
		flash = Color3.fromRGB(255, 225, 234), tracer = Color3.fromRGB(244, 154, 192),
		bullet = { kind = "bubbles" }, -- (the pink tracer with soap bubbles along it that pop)
	},
	revolver_ducky = {
		idle = {
			{ kind = "sparkle", colour = Color3.fromRGB(246, 215, 138), rate = 2.5, life = 0.6, size = 0.01, drift = "rise",
				at = { { -0.037, 0.045, -0.128 }, { -0.034, 0.039, 0.017 }, { -0.05, 0.009, -0.05 } } },
			{ kind = "bubble", colour = Color3.fromRGB(241, 228, 234), rate = 0.9, life = 1.5, size = 0.018, drift = "rise",
				at = { { 0, 0.03, 0.13 }, { -0.03, 0.03, 0.074 } } },
		},
		glow = { colour = Color3.fromRGB(242, 122, 168) },
		trail = { colour = Color3.fromRGB(247, 182, 205), life = 0.4, width0 = 0.015, width1 = 0, segs = { { { -0.028, 0.051, 0.003 }, { -0.028, 0.063, 0.068 } } } },
		flash = Color3.fromRGB(255, 225, 234), tracer = Color3.fromRGB(244, 154, 192),
		bullet = { kind = "hearts" }, -- (the pink tracer with tiny hearts twinkling along it; a sparkle burst)
	},
	katana_ducky = {
		idle = {
			{ kind = "sparkle", colour = Color3.fromRGB(246, 215, 138), rate = 2.5, life = 0.6, size = 0.01, drift = "rise",
				at = { { -0.027, 0.002, 0.115 }, { -0.036, 0.048, -0.102 } } }, -- the left pommel heart, the bow's star clip
		},
		glow = { colour = Color3.fromRGB(242, 122, 168) },
		trail = { colour = Color3.fromRGB(247, 182, 205), life = 0.4, width0 = 0.04, width1 = 0, -- (a glitter swing trail off the blade)
			segs = { { { 0, 0.006, -0.26 }, { 0, 0.083, -0.836 } } } },
		swing = { kind = "sparkle", colour = Color3.fromRGB(255, 214, 150) }, -- (gold sparkles shed along each swing, a burst on a hit)
	},
	-- the space-western high pieces: warm dust motes and a gold tracer on the frontier side, teal light on the star side; the
	-- model builder's shot and lever-cycle effects (EFFECTS in gun_sets_west.py) as `shot` / `lever` bursts and a `pulse`
	-- (Fx.skinIdle says what each field means: kind spark / puff / steam, n, size, life, speed, delay, at, dir, both)
	revolver_dust = {
		idle = {
			{ kind = "sparkle", colour = Color3.fromRGB(232, 201, 154), rate = 1.5, life = 1.8, size = 0.007, drift = "rise",
				at = { { -0.05, 0.03, -0.05 }, { -0.04, 0.0, 0.06 } } },
		},
		shot = {
			{ kind = "spark", colour = Color3.fromRGB(255, 210, 122), n = { 2, 3 }, size = 0.025, life = 0.14, speed = 1.2, -- (the hammer falling)
				at = { { 0.0, 0.07, 0.06 } }, dir = { 0, 1, 0.6 } },
			{ kind = "puff", colour = Color3.fromRGB(184, 173, 156), size = 0.03, life = 0.8, delay = 0.3, -- (curling up off the muzzle and the cylinder gap)
				at = { { 0.0, 0.035, -0.3 }, { -0.045, 0.02, -0.1 } } },
		},
		flash = Color3.fromRGB(255, 196, 106), tracer = Color3.fromRGB(242, 220, 160),
		bullet = { kind = "dust" }, -- (a warm gold streak; a dust kick where it lands)
	},
	revolver_star = {
		idle = {
			{ kind = "sparkle", colour = Color3.fromRGB(201, 164, 216), rate = 1.5, life = 1.8, size = 0.007, drift = "rise",
				at = { { -0.05, 0.03, -0.05 }, { -0.04, 0.0, 0.06 } } },
		},
		glow = { colour = Color3.fromRGB(69, 230, 214) },
		shot = {
			{ kind = "spark", colour = Color3.fromRGB(69, 230, 214), n = { 2, 3 }, size = 0.022, life = 0.15, speed = 1.4, spread = 25, -- (off the rotor's sides as it clicks round)
				at = { { 0.047, 0.009, -0.05 } }, dir = { 1, 0.3, 0 }, both = true },
		},
		pulse = { parts = { "cylinder" }, t = 0.1 }, -- (the rotor's hub flares on each shot)
		flash = Color3.fromRGB(191, 247, 240), tracer = Color3.fromRGB(69, 230, 214),
		bullet = { kind = "hardlight" }, -- (a thin white-teal core in a teal glow, a ring off the muzzle; a ring burst)
	},
	lever_dust = {
		idle = {
			{ kind = "haze", colour = Color3.fromRGB(169, 162, 154), rate = 0.5, life = 1.2, size = 0.02, drift = "rise",
				at = { { 0.0, 0.066, -0.655 } } },
			{ kind = "sparkle", colour = Color3.fromRGB(232, 201, 154), rate = 1.2, life = 1.8, size = 0.007, drift = "rise",
				at = { { -0.06, 0.0, -0.25 } } },
		},
		shot = {
			{ kind = "steam", colour = Color3.fromRGB(233, 230, 223), size = 0.07, life = 0.7, speed = 0.5, at = { { 0.0, 0.066, -0.655 } } }, -- (a chuff out of the stack)
		},
		lever = { -- (the Iron Horse's wheels don't turn: the lever cycle is its moving moment)
			{ kind = "steam", colour = Color3.fromRGB(233, 230, 223), size = 0.05, life = 0.6, speed = 0.4, at = { { 0.0, 0.066, -0.655 } } },
			{ kind = "steam", colour = Color3.fromRGB(233, 230, 223), size = 0.05, life = 0.5, speed = 0.5, -- (the cylinder cocks by the wheels)
				at = { { -0.05, -0.05, -0.66 } }, dir = { -1, -0.2, 0 }, both = true },
			{ kind = "spark", colour = Color3.fromRGB(255, 179, 90), n = { 1, 2 }, size = 0.022, life = 0.18, speed = 1.3, -- (off the drive wheels' rims)
				at = { { -0.05, -0.09, -0.6 }, { -0.05, -0.09, -0.48 } }, dir = { 0, -0.4, 1 }, both = true },
		},
		flash = Color3.fromRGB(255, 196, 106), tracer = Color3.fromRGB(242, 220, 160),
		bullet = { kind = "powder" }, -- (the gold tracer; a black-powder puff off the muzzle)
	},
	lever_star = {
		idle = {
			{ kind = "sparkle", colour = Color3.fromRGB(69, 230, 214), rate = 1.5, life = 0.8, size = 0.008, drift = "fall",
				at = { { 0.0, -0.085, -0.6 }, { 0.0, -0.085, -0.47 } } },
		},
		glow = { colour = Color3.fromRGB(69, 230, 214) },
		lever = {
			{ kind = "spark", colour = Color3.fromRGB(69, 230, 214), n = { 2, 3 }, size = 0.02, life = 0.3, speed = 0.6, spread = 20, -- (dropping from under the hover rings)
				at = { { 0.0, -0.085, -0.6 }, { 0.0, -0.085, -0.47 } }, dir = { 0, -1, 0 } },
		},
		pulse = { parts = { "barrel" }, t = 0.1 }, -- (the nose ring and the light line flare on each shot)
		flash = Color3.fromRGB(191, 247, 240), tracer = Color3.fromRGB(69, 230, 214),
		bullet = { kind = "rail" }, -- (a teal rail of dashes running forward with rings along it)
	},
	katana_sakura = { -- (the J-A Maki-e katana since v498) petals drifting off the guard's gold rim, the hilt's two blossom
		-- ornaments and the blade's back (the blade points move with its stretch). points measured on the model, 17 Nov: the
		-- guard's top at y 0.055-0.059, the blossoms at x +-0.023 z -0.024, the blade's back y 0.034 at z -0.26 rising to 0.07
		idle = {
			{ kind = "petal", colour = Color3.fromRGB(233, 183, 195), colour2 = Color3.fromRGB(246, 221, 227), rate = 2.2,
				life = 2.2, size = 0.016, drift = "fall",
				at = { { 0, 0.057, -0.148 }, { 0.023, 0.006, -0.024 }, { 0, 0.035, -0.26 }, { 0, 0.042, -0.453 }, { 0, 0.071, -0.731 } },
				both = true, blade = { 3, 4, 5 } },
		},
		glow = { colour = Color3.fromRGB(236, 186, 200) },
		trail = { colour = Color3.fromRGB(246, 196, 212), life = 0.2, width0 = 0.04, width1 = 0, -- (a swing trail off the blade)
			segs = { { { 0, 0.035, -0.25 }, { 0, 0.077, -0.78 } } } },
		swing = { kind = "petal" }, -- (petals shed along each swing, a burst of them on a hit)
	},
	-- the Triangulum (the VIP daily sniper): no idle bits (the mark's six star cores are its glow); starlight FFE7A6 flash
	-- and a thin gold-white line with stars twinkling along it
	sniper_triangulum = {
		flash = Color3.fromRGB(255, 236, 196), tracer = Color3.fromRGB(255, 231, 166),
		bullet = { kind = "stars" }, -- (a thin gold-white line with small stars twinkling along it; a fading star where it lands)
	},
} :: { [string]: any }

-- the set a skin belongs to (nil for a lone skin)
function SkinSets.setOf(skinId: string): string?
	local row = SkinSets.SKINS[skinId]
	return row and row[4] or nil
end

-- the sets in their display order (ids)
function SkinSets.ordered(): { string }
	local ids = {}
	for id in SkinSets.SETS do table.insert(ids, id) end
	table.sort(ids, function(a, b) return SkinSets.SETS[a].order < SkinSets.SETS[b].order end)
	return ids
end

-- how much of a set a player has: owns(skinId) -> boolean (the loot session's Loot.owns, or the client's view of it).
-- returns owned, total and the missing skin ids (in the set's order)
function SkinSets.progress(setId: string, owns: (string) -> boolean): (number, number, { string })
	local s = SkinSets.SETS[setId]
	if not s then return 0, 0, {} end
	local n, missing = 0, {}
	for _, id in s.members do
		if owns(id) then n += 1 else table.insert(missing, id) end
	end
	return n, #s.members, missing
end

return SkinSets
