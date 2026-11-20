--!strict
-- FINISHER TOWNS: the kit towns a scene can stand in (client/FinisherTown.luau) and the spots of their blank cowboy
-- onlookers. Generated from tools/roblox/highnoon_town.py's spots json; do not edit by hand. Each spot:
-- { x, y, z (feet, local to the scene ORIGIN), face x, face z (the way they look), kind, floor }
-- (kind: window | door | barrel duck at the draw; balcony | porch flinch at the shot)
return {
	highnoon = {
		A = { set = "HighNoonTownA", spots = {
			{ -12.6, 8.6, 17.75, 1, 0, "window", 1 },
			{ -12.6, 8.6, -13.5, 1, 0, "window", 1 },
			{ -12.6, 8.6, -6.5, 1, 0, "window", 1 },
			{ -12.4, 0.9, -10.0, 1, 0, "door", 0 },
			{ 12.6, 0.9, 17.325, -1, 0, "window", 0 },
			{ -9.6, 0.62, 13.6, 1, 0, "barrel", 0 },
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
