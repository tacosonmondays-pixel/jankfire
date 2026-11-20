--!strict
-- FINISHERS (17 Nov 2026; roblox/docs/FINISHERS.md): a short cinematic that plays when a high-tier skin that owns one
-- lands the kill that wins a round or the match. The owner: "a cinematic finisher with effects ... only with high tier
-- skins ... super dynamic and fluid movement, angles, perspective."
--   * the MATCH-WINNING kill plays the full cut (about 2.9 s) for everyone in the match, in the end-of-match window
--     (the end screen is already up and nobody is playing)
--   * a ROUND-WINNING kill plays the short cut (about 1.7 s) for the killer and the victim only, in the 3 s between rounds
--   * a classic mode (Matches.startMode) has no rounds of that kind: only the kill that ends it plays, the full cut
--   * no other kill plays one, so nobody still playing is ever blinded or held. SPACE / the SKIP button ends it
-- A finisher is played from the match recording (server/Recorder.luau): the last moments before the kill, on the
-- replay's own ghost bodies (client/Replay.luau), with a scripted camera of several shots (client/Finisher.luau) and
-- its theme's effects (client/FinisherFx.luau). This module is the data: which finishers exist, which skins own one,
-- the shot lists, and the pure decision of which cut a kill gets.
-- To add a finisher: a row in LIST (its skins, colours, theme) and, for a new look, a theme in FinisherFx.THEMES.
local Finishers = {}

export type Row = {
	name: string, -- (on screen: the finisher's name)
	set: string, -- SkinSets set id
	skins: { string }, -- the skin that owns it: ONE gun per set (the owner, 20 Nov: "special cutscene should be applied to one gun in the set")
	theme: string, -- FinisherFx.THEMES key
	colour: Color3, -- the theme's main light
	accent: Color3, -- its second colour
	grade: { tint: Color3, sat: number, con: number, bright: number }, -- the colour grade while it plays
	anim: string?, -- the victim's reaction (Finishers.ANIMS key)
	cut: any?, -- (optional) its own shot lists by cut kind, in place of CUTS for guns ({ full = { ... } })
	order: number,
	scene: string?, -- (optional) the match win plays this scene instead of the cut (client/FinisherScene.luau)
	sceneLen: { full: number, short: number }?, -- the scene's lengths (s), for the server's end-screen wait
	vip: boolean?,
	built: boolean, -- false = planned (a row the next pass builds), never chosen
}

Finishers.LIST = {
	ascension = { -- Seraph: the victim is lifted up a column of light, two great wings open behind them, feathers fall
		-- (the Seraph set's rifle is the owner's Tripo one since 18 Nov: ar_seraph_tripo. shop-gui)
		name = "Ascension", set = "set_seraph", skins = { "ar_seraph_tripo" }, theme = "seraph", order = 1, built = true,
		colour = Color3.fromRGB(255, 214, 120), accent = Color3.fromRGB(250, 246, 236),
		grade = { tint = Color3.fromRGB(255, 246, 228), sat = -0.15, con = 0.08, bright = 0.03 }, anim = "lift",
	},
	hellgate = { -- Infernal: the ground cracks open under the victim, hellfire climbs out and drags them down
		name = "Hellgate", set = "set_infernal", skins = { "ar_infernal" }, theme = "infernal", order = 2, built = true,
		colour = Color3.fromRGB(255, 96, 34), accent = Color3.fromRGB(255, 190, 90),
		grade = { tint = Color3.fromRGB(255, 222, 205), sat = -0.25, con = 0.18, bright = -0.02 }, anim = "kneel",
	},
	splashdown = { -- Ducky (VIP): a giant rubber duck drops out of the sky onto the victim in a burst of soap bubbles
		-- (both Ducky sets since 18 Nov: the VIP set's Tripo ducks and the code's Ducky Classic trio. shop-gui)
		-- (20 Nov, the owner: "special cutscene should be applied to one gun in the set ... maybe the ducky sniper")
		name = "Splashdown", set = "set_ducky", skins = { "sniper_ducky_tripo" }, theme = "ducky",
		order = 3, built = true, vip = true,
		colour = Color3.fromRGB(247, 182, 205), accent = Color3.fromRGB(246, 215, 138),
		grade = { tint = Color3.fromRGB(255, 236, 244), sat = 0.08, con = 0.04, bright = 0.03 }, anim = "shield",
	},
	-- the second pass (17 Nov): the other five high-tier looks
	highnoon = { -- Dust Drover: a high-noon standoff, the lens pushing in on the shooter's eyes as the world stretches
		-- behind them (a dolly zoom); the victim spins and drops, a dust devil turns, a tumbleweed rolls through
		-- (20 Nov, the owner: one gun per set owns the cutscene - "Cowboy revolver")
		name = "High Noon", set = "set_dust", skins = { "revolver_dust" }, theme = "dust", order = 4, built = true,
		colour = Color3.fromRGB(255, 196, 106), accent = Color3.fromRGB(206, 182, 142),
		grade = { tint = Color3.fromRGB(255, 232, 196), sat = -0.3, con = 0.15, bright = 0 }, anim = "spinfall",
		cut = { full = { { "eyes", 0.72 }, { "chase", 0.5 }, { "impact", 0.42 }, { "resolve", 1.18 } } },
		-- (20 Nov, the owner: "take out tidecrest put in revolver": the High Noon Western they approved as video
		-- (western_town_v3) plays in the game on the two real avatars - a standoff in a sunset town, the holsters on
		-- their hips, the hands reaching onto the guns, one shot; FinisherScene + FinisherSceneData_highnoon(_set).
		-- a round win plays the draw, the shot and the far shot)
		scene = "highnoon", sceneLen = { full = 14.15, short = 3.27 },
	},
	inkfall = { -- Tidecrest: one ink-wash brush slash across the frame, the victim splits into sakura petals
		-- (20 Nov, Tidecrest v4.2, the owner: "I think tidecrest is ready for Roblox": the grip, the two-hand draw of the
		-- long blade, the whirl to his face, the sprint, the pass, the hit frame, the freeze, the sheathe's click, the cut
		-- lands, the winner close on the right as he falls behind; FinisherScene + FinisherSceneData, the video's plan.
		-- a round win plays the cut landing and the end)
		name = "Inkfall", set = "set_tidecrest", skins = { "katana_sakura" }, theme = "ink", order = 5, built = true,
		scene = "inkfall", sceneLen = { full = 10.63, short = 2.04 },
		colour = Color3.fromRGB(236, 186, 200), accent = Color3.fromRGB(217, 187, 114),
		grade = { tint = Color3.fromRGB(246, 238, 232), sat = -0.5, con = 0.16, bright = 0 }, anim = "bowdown",
	},
	warpout = { -- Star Drover: the victim is pulled into a teal hard-light ring and the stars streak past in a warp
		-- (20 Nov, one gun per set: the Star Drover's revolver, as the Dust Drover's)
		name = "Warp Out", set = "set_star", skins = { "revolver_star" }, theme = "warp", order = 6, built = true,
		colour = Color3.fromRGB(69, 230, 214), accent = Color3.fromRGB(201, 164, 216),
		grade = { tint = Color3.fromRGB(226, 246, 255), sat = 0, con = 0.12, bright = -0.02 }, anim = "pulled",
	},
	lanternlight = { -- Pumpkin Patch: a giant carved pumpkin closes round the victim and its face lights up from inside
		name = "Lantern Light", set = "set_halloween", skins = { "smg_pumpkin" }, theme = "lantern", order = 7, built = true,
		colour = Color3.fromRGB(255, 156, 69), accent = Color3.fromRGB(179, 165, 151),
		grade = { tint = Color3.fromRGB(236, 226, 246), sat = -0.2, con = 0.14, bright = -0.03 }, anim = "cower",
	},
	starchart = { -- Triangulum: stars light on the victim's joints and the lines draw between them, then it fades to sky
		name = "Starchart", set = "", skins = { "sniper_triangulum" }, theme = "stars", order = 8, built = true,
		colour = Color3.fromRGB(255, 231, 166), accent = Color3.fromRGB(255, 236, 196),
		grade = { tint = Color3.fromRGB(205, 214, 255), sat = -0.15, con = 0.12, bright = -0.07 }, anim = "starpose",
	},
} :: { [string]: Row }

-- the victim's reactions, made with Studio's prompt-to-animation (generate_animation, 4 takes each, the best kept,
-- 17 Nov: FINISHERS.md, docs/finishers/reaction_takes.jpg). id = the published animation (empty = moved by code
-- alone). Each clip is 2.5 s; speed fits most of it into the impact and the resolve
Finishers.ANIMS = {
	lift = { id = "120752615367600", speed = 1.6 }, -- struck, then rises with the arms opening and the head back (take 4)
	kneel = { id = "102848812527442", speed = 1.6 }, -- struck, drops to the knees, slumps forward (take 3)
	shield = { id = "99441068703478", speed = 1.6 }, -- struck, looks straight up with the arms raised (take 3)
	-- the second pass's own clips (17 Nov ~14:30-15:30 UTC, 4 takes each; sheet docs/finishers/reaction_takes2.jpg)
	spinfall = { id = "80430806221753", speed = 1.6 }, -- High Noon: shot in the shoulder, spins half round and falls back to the ground (take 1)
	bowdown = { id = "108121066232094", speed = 1.6 }, -- Inkfall: stands frozen after the cut, then sinks to one knee and bows the head (take 1)
	pulled = { id = "122059547987683", speed = 1.6 }, -- Warp Out: yanked backwards off the feet, arms reaching forward (take 3)
	cower = { id = "137185623825862", speed = 1.6 }, -- Lantern Light: looks up in fright, stumbles back, crouches low with the arms over the head (take 4)
	starpose = { id = "125088229863050", speed = 1.6 }, -- Starchart: rises onto the toes, arms and legs spread wide like a star, head up (take 4)
} :: { [string]: { id: string, speed: number } }

-- the scenes' mocap clips (Roblox animations uploaded 19 Nov from the vault's Mixamo clips and the MotionBricks takes
-- made from them; the clip names are FinisherSceneData's): clip -> animation id
Finishers.SCENE_ANIMS = {
	inkfall_slash_t1 = "94188181886964", -- the run-in and the one big horizontal slash
	victim_lookaround_t2 = "77808638913840", -- standing, then looking round: nothing happened?
	sheathe_t2 = "134557117553244", -- the blade slid home at the left hip
	bx_18_block_high_center = "113614195469370", -- a guard thrown up too late
	bx_27_hit_stomach = "81006356768412", -- folding over the hit
	bx_28_knockdown_liver = "72820154953051", -- the knees go, down
	-- (Tidecrest v4.2, 20 Nov: the two-hand iai draw, the lean sprint, the winner's idle; and from the bought Katana
	-- Combat Pack - its files stay in the vault, only these uploads are ours - the whirl to a guard, the dash-through
	-- cut, the death that rolls and settles)
	mb_iai_draw = "71056343687693",
	mx_sprint_lean = "107791474095487",
	id_06_dune_weight_shift = "70471285286190",
	kp_readys_mainanimation_keyframesequence = "77378208505552",
	kp_basicattacktypes_dashlight_keyframesequence = "94578161823866",
	kp_death_actions_deathanimation_keyframesequence = "102418985491836",
	-- (High Noon, 20 Nov: the quick draw - also played backwards for the re-holster - and the victim's knockdown and
	-- the fall that stays down)
	quick_draw_t1 = "89643464186256",
	bx_30_knockdown_punch = "90235382579488",
	bx_29_knocked_out_back = "71597412128503",
} :: { [string]: string }

-- the shot lists: each shot is a camera move (client/Finisher.luau SHOTS) and its length in s. `full` is the match's
-- last kill (with a CHARGE close-up on the gun as the theme's light gathers at the muzzle), `short` a round's. a melee kill swaps the bullet chase for a whip round the swing (`melee`)
Finishers.CUTS = {
	full = { { "hero", 0.5 }, { "charge", 0.38 }, { "chase", 0.48 }, { "impact", 0.42 }, { "resolve", 1.12 } },
	short = { { "chase", 0.45 }, { "impact", 0.32 }, { "resolve", 0.9 } },
	melee = { full = { { "hero", 0.55 }, { "whip", 0.62 }, { "impact", 0.45 }, { "resolve", 1.18 } },
		short = { { "whip", 0.45 }, { "impact", 0.32 }, { "resolve", 0.9 } } },
} :: any

-- how much recording a finisher needs before the kill (s): the hero shot plays the last of it
Finishers.LEAD = 1.4
-- a round's last kill counts if the round was won within this long of it (s)
Finishers.FRESH = 0.75

Finishers.BY_SKIN = {} :: { [string]: string }
for id, row in Finishers.LIST do
	if row.built then for _, s in row.skins do Finishers.BY_SKIN[s] = id end end
end

-- the in-game scenes, each behind a switch. 20 Nov, the owner: "take out tidecrest put in revolver" - Tidecrest goes to a
-- professional, so its scene is OFF and Inkfall plays its normal cut again. FinisherScene and its data stay in the
-- place; true here brings the scene back (row.sceneOff keeps its id). High Noon is held OFF for the owner's zombies-fix
-- publish (main, 20 Nov) until its eye shots and sound are signed off; the revolver plays its normal cut meanwhile
Finishers.SCENE_ON = { inkfall = false, highnoon = false } :: { [string]: boolean }
for id, row in Finishers.LIST do
	if row.scene and Finishers.SCENE_ON[id] == false then
		(row :: any).sceneOff = row.scene
		row.scene = nil
		row.sceneLen = nil
	end
end

-- the finisher a skin owns (built ones only), and its row
function Finishers.forSkin(skinId: string?): (string?, Row?)
	if type(skinId) ~= "string" then return nil, nil end
	local id = Finishers.BY_SKIN[skinId]
	return id, if id then Finishers.LIST[id] else nil
end

-- every finisher in its order (ids), built ones first
function Finishers.ordered(): { string }
	local ids = {}
	for id in Finishers.LIST do table.insert(ids, id) end
	table.sort(ids, function(a, b)
		local A, B = Finishers.LIST[a], Finishers.LIST[b]
		if A.built ~= B.built then return A.built end
		return A.order < B.order
	end)
	return ids
end

-- the shot list for a cut ("full" | "short") and a weapon class (melee or not); a finisher's own list (row.cut) for a gun
function Finishers.cut(kind: string, melee: boolean, row: Row?): { { any } }
	if row and row.cut and row.cut[kind] and not melee then return row.cut[kind] end
	if melee then return Finishers.CUTS.melee[kind] or Finishers.CUTS.melee.full end
	return Finishers.CUTS[kind] or Finishers.CUTS.full
end
function Finishers.length(kind: string, melee: boolean, row: Row?): number
	if row and row.scene and row.sceneLen then return if kind == "short" then row.sceneLen.short else row.sceneLen.full end
	local n = 0
	for _, s in Finishers.cut(kind, melee, row) do n += s[2] end
	return n
end

-- which cut a kill gets (pure, so it can be tested): nil, "short" or "full"
--   o.since       s from the kill to now (the round being won / the match ending)
--   o.owned       the killer's skin on the weapon that killed owns a finisher
--   o.weapon      the weapon that killed ("void" and "shredder" never play one: no shot to show)
--   o.killerAlive the killer is still standing (a trade has no hero)
--   o.victimPlayer the victim is a player (not a dummy)
--   o.sameTeam    the killer is on the team that won (the round or the match)
--   o.event       "round" (a round won, wins = that team's wins now, need = Matches.WIN) | "end" (a classic mode's end)
--   o.classic     the match is a classic mode's (only its end counts)
function Finishers.decide(o: any): string?
	if not o.owned or not o.killerAlive or not o.victimPlayer or not o.sameTeam then return nil end
	if o.weapon == "void" or o.weapon == "shredder" then return nil end
	if type(o.since) ~= "number" or o.since < 0 or o.since > Finishers.FRESH + (if o.event == "end" then 0.75 else 0) then return nil end
	if o.event == "round" then
		if o.classic then return nil end
		return if (o.wins or 0) >= (o.need or math.huge) then "full" else "short"
	elseif o.event == "end" then
		return if o.classic then "full" else nil -- (a normal match's end came from its last round: that one played it)
	end
	return nil
end

return Finishers
