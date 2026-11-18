--!strict
-- the special (high-tier) skins' own sound layers, played ON TOP of the base gun's sound (the owner, 17 Nov 2026:
-- "make sure special weapons have custom bullet trails and sfx that match the style of the gun"; the sheet is
-- special-skins-trails-sfx.md in the main session's notes). recordings only, never code-made tones. every layer is a
-- Sound in ReplicatedStorage.JankfireSounds named "skin_<skin>_<kind>", quieter than the shot and at most about 0.6 s,
-- so gunfeel and loudness stay fair. played by client/Sfx.luau: Sfx.gun (the shot, yours or someone else's),
-- Sfx.skinEvent (your reload / cycle clip events, Reloads.luau names) and Sfx.skinHit (your melee hit).
--   fire   = a layer on each shot; chance = only that share of shots (a ricochet on some shots, not all)
--   alt    = an extra layer every `every` shots (Bubble Bath's duck squeak on every 5th shot, not every one)
--   ev     = clip event -> layer (magIn: the mag seats; cylIn / spinCyl: the cylinder; leverClack: a lever cycle;
--            shell: the sniper's bolt throws its case; whoosh: a katana swing)
--   hit    = a layer on your melee hit
--   item   = a skinned gadget's layers by event (throw, blast, cloud, land, open), played by Sfx.skinItem from the gadget
--            code (client/Utility.client) beside the gadget's own sound (18 Nov 2026: the four legendary gadget skins)
-- a new special skin: add its row here and its Sounds in JankfireSounds (tools/roblox/store_sounds.mjs, store.json)
local SkinSounds = {}

SkinSounds.skin = {
	ar_seraph = { fire = "skin_ar_seraph_fire", ev = { magIn = "skin_ar_seraph_reload" } }, -- a glass-chime tail; a plucked string
	ar_infernal = { fire = "skin_ar_infernal_fire", ev = { magIn = "skin_ar_infernal_reload" } }, -- a fire whoomp; an ember sizzle
	smg_pumpkin = { fire = "skin_smg_pumpkin_fire", ev = { magIn = "skin_smg_pumpkin_reload" } }, -- a hollow wooden thock; a creaky lid
	katana_sakura = { ev = { whoosh = "skin_katana_sakura_swing" }, hit = "skin_katana_sakura_hit" }, -- wind chimes; a wood-block tock
	lmg_ducky = { fire = "skin_lmg_ducky_fire", alt = { name = "skin_lmg_ducky_squeak", every = 5 }, ev = { magIn = "skin_lmg_ducky_reload" } }, -- bubbles; a squeak every 5th; a splash
	revolver_ducky = { fire = "skin_revolver_ducky_fire", ev = { spinCyl = "skin_revolver_ducky_cycle" } }, -- a sparkle chime; a squeak as the cylinder turns
	katana_ducky = { hit = "skin_katana_ducky_hit" }, -- a tiny squeak on the hit
	revolver_dust = { fire = "skin_revolver_dust_fire", chance = 0.35, ev = { spinCyl = "skin_revolver_dust_reload" } }, -- a western ricochet on some shots; spur jingle
	lever_dust = { fire = "skin_lever_dust_fire", ev = { leverClack = "skin_lever_dust_cycle" } }, -- a black-powder boom; a steam chuff on the lever
	revolver_star = { fire = "skin_revolver_star_fire", ev = { cylIn = "skin_revolver_star_reload" } }, -- a laser zap; a servo whirr
	lever_star = { fire = "skin_lever_star_fire", ev = { leverClack = "skin_lever_star_cycle" } }, -- a plasma zap; a sci-fi relay clack
	sniper_triangulum = { fire = "skin_sniper_triangulum_fire", ev = { shell = "skin_sniper_triangulum_cycle" } }, -- a falling shimmer; a soft chime on the bolt
	-- the legendary gadget skins (ItemSkins)
	frag_lantern = { item = { throw = "skin_frag_lantern_throw", blast = "skin_frag_lantern_blast" } }, -- a paper rustle; a firecracker pop under the blast
	medkit_bento = { item = { open = "skin_medkit_bento_open" } }, -- a lacquer lid lifting with a soft wooden knock
	smoke_censer = { item = { throw = "skin_smoke_censer_throw", cloud = "skin_smoke_censer_cloud" } }, -- a small bronze bell; a temple-bowl ring as the cloud starts
	duck_origami = { item = { throw = "skin_duck_origami_throw", land = "skin_duck_origami_land" } }, -- a paper flap; a paper crinkle on landing
} :: { [string]: { fire: string?, chance: number?, alt: { name: string, every: number }?, ev: { [string]: string }?, hit: string?, item: { [string]: string }? } }

return SkinSounds
