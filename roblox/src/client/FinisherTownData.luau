--!strict
-- FINISHER TOWNS: the kit towns a scene can stand in (client/FinisherTown.luau) and the spots of their blank cowboy
-- onlookers. Generated from tools/roblox/highnoon_town.py's spots json; do not edit by hand. Each spot:
-- { x, y, z (feet, local to the scene ORIGIN), face x, face z (the way they look), kind, floor, reaction? }
-- (kind: window | door | barrel duck at the draw; balcony | porch flinch at the shot. A reaction - "duck" | "cower" |
-- "flinch" - in place of the kind's: the one the clip check found to fit that opening, 20 Nov)
-- (the owner picked A on 20 Nov: only HighNoonTownA is in the place. B stays here as the spare, a switch away -
-- tools/roblox/highnoon_town_import.luau brings its set back - and is never loaded while its set isn't there)
return {
	highnoon = {
		A = { set = "HighNoonTownA", spots = {
			{ -14.4, 8.6, 17.75, 1, 0, "window", 1, "cower" },
			{ -14.4, 8.6, -13.5, 1, 0, "window", 1, "flinch" },
			{ -14.4, 8.6, -6.5, 1, 0, "window", 1, "cower" },
			{ -14.4, 0.9, -10.0, 1, 0, "door", 0, "cower" },
		} },
		B = { set = "HighNoonTownB", spots = {
			{ -16.2, 8.3, 19.25, 1, 0, "window", 1 },
			{ -11.5, 8.25, 21.0, 1, 0, "balcony", 1 },
			{ -16.0, 0.3, -10.0, 1, 0, "door", 0 },
			{ -11.5, 8.25, -6.5, 1, 0, "balcony", 1 },
			{ -11.5, 8.25, -13.0, 1, 0, "balcony", 1 },
			{ -16.2, 0.3, -21.7, 1, 0, "window", 0 },
			{ 11.5, 0.35, 13.5, -1, 0, "porch", 0 },
		} },
	},
}
