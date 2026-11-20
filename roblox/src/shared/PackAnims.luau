--!strict
-- animations from packs the owner bought, uploaded as Animations to the owner's account. the packs' own files stay in
-- the vault (Documents\JANKFIRE Vault\Tools\Packs-20nov) and NEVER go in git: these ids are all of it that is ours.
-- one table, so every user shares one upload (cinematic-finishers' Tidecrest uses katana.equip / unequip).
--   katana: robloxanimations.com "Katana Combat Pack - 34 Animations" (BuiltByBit 117603, bought 20 Nov 2026), R15,
--   each the pack's KeyframeSequence as it came (speed 1, its markers kept). upper = the legs dropped and the root and
--   lower torso unweighted, so it plays over a walk or a run. hit = the pack's swing marker (s). tools/roblox/
--   katana_pack.py exported them (from the vault copy), uploaded 20 Nov 2026 through Open Cloud. the katana's own rows
--   are in Anims.luau (kat_*), docs/KATANA.md "Mocap"
return {
	katana = {
		block = { id = 86655046417517, len = 2.0, upper = true, src = "Animations Block" }, -- (up by 0.1 s, then held)
		deflect = { id = 100089422703963, len = 1.333, upper = true, src = "Animations DeflectedUp" },
		light1 = { id = 95363076019189, len = 0.933, upper = true, hit = 0.1667, src = "BasicAttackTypes Light01" },
		light2 = { id = 94835463875042, len = 0.933, upper = true, hit = 0.1667, src = "BasicAttackTypes Light02" },
		light3 = { id = 132114568020105, len = 1.25, upper = true, hit = 0.25, src = "BasicAttackTypes Light03" },
		stagger = { id = 140232916534684, len = 0.667, upper = true, src = "Stagger Types KatanaParry Left" },
		wave = { id = 122543974629370, len = 1.1, upper = true, hit = 0.1667, src = "BasicAttackTypes Ultimate, from 0.4 s" },
		equipUpper = { id = 127861015989285, len = 0.667, upper = true, src = "Animations Equip" },
		equip = { id = 87695619849581, len = 0.667, src = "Animations Equip" }, -- (full body: the finishers)
		unequip = { id = 109417036578604, len = 0.667, src = "Animations Unequip" }, -- (full body: the finishers)
	},
	-- the same pack's R6 file, for R6 bodies (Anims kat_* tp6): each move cut as its R15 one (same length and markers),
	-- the legs dropped and the root and the Torso unweighted
	katanaR6 = {
		block = { id = 111503153459996, len = 2.0, upper = true, src = "Animations Block" },
		deflect = { id = 79313209306371, len = 1.333, upper = true, src = "Animations DeflectedUp" },
		light1 = { id = 116226052058452, len = 0.933, upper = true, hit = 0.1667, src = "BasicAttackTypes Light01" },
		light2 = { id = 101626943092173, len = 0.933, upper = true, hit = 0.1667, src = "BasicAttackTypes Light02" },
		light3 = { id = 121053388545839, len = 1.25, upper = true, hit = 0.25, src = "BasicAttackTypes Light03" },
		stagger = { id = 91503477131103, len = 0.667, upper = true, src = "Stagger Types KatanaParry Left" },
		wave = { id = 94359662741712, len = 1.1, upper = true, hit = 0.1667, src = "BasicAttackTypes Ultimate, from 0.4 s" },
	},
}
