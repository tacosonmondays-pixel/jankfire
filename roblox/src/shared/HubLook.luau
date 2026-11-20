--!strict
-- the looks: Lighting is one global thing and the saved values are tuned for the Rooftop, so each client swaps to its
-- own look while its player is somewhere else, and back to the saved look for a match (the places are far apart and
-- can't see each other). hub = THE LANES, a bowling alley: warm and a little dim, lit by its own lamps and glow (its
-- base light comes in two tints, HUB_TINT below, to go with the paint the room was built in);
-- training = a darker mood with more base light; playground = open air at dusk, the Rooftop's evening with more haze.
-- edit-time preview from the command bar: require(game.ReplicatedStorage.Jankfire.HubLook).preview("hub" | "training"
-- | "playground") and .preview(false) to put the saved look back. ALWAYS preview(false) before saving the place.
-- the Rooftop's values are parked as attributes on Lighting while a preview is on, so any copy of this module (a fresh
-- clone after an edit, since require caches) can turn it on, change it and turn it off again
local Lighting = game:GetService("Lighting")
local TweenService = game:GetService("TweenService")

type Look = { [string]: { [string]: any } }
-- the first hub's look (the rotunda, put away in ServerStorage.PolishBackup.HubArchive on 2026-11-15): dark and cozy.
-- kept as looks.rotunda, and every other look is still written as its differences from this one
local HUB: Look = {
	Lighting = {
		Ambient = Color3.fromRGB(104, 98, 122), OutdoorAmbient = Color3.fromRGB(104, 98, 122), Brightness = 0,
		ExposureCompensation = 0.1, EnvironmentDiffuseScale = 0.15, EnvironmentSpecularScale = 0.35,
	},
	Atmosphere = { Density = 0.22, Offset = 0, Haze = 0, Glare = 0, Color = Color3.fromRGB(40, 34, 52), Decay = Color3.fromRGB(18, 16, 26) },
	Bloom = { Intensity = 0.4, Size = 22, Threshold = 1.9 },
	ColorCorrection = { Brightness = 0, Contrast = 0.18, Saturation = 0.2, TintColor = Color3.fromRGB(255, 244, 234) },
	SunRays = { Intensity = 0 },
}
local function with(base: Look, over: Look): Look
	local out: Look = {}
	for name, props in base do
		out[name] = table.clone(props)
		if over[name] then for p, v in over[name] do out[name][p] = v end end
	end
	return out
end

-- the hub's base light comes in two tints, one for each kind of paint the Lanes can be built in (the builder,
-- ServerStorage.PolishBackup.HubLab, has the palettes: L.LANES_PALETTE. a build writes its palette's tint on this
-- script as the attribute HubTint, so the paint and the light change together; with no attribute it is "neutral").
--   neutral  (2026-11-15) for the sand room, where only the carpet is purple: a warm grey that adds no colour of its own
--   purple   the first look's own tint, for the all-purple room the owner picked on 2026-11-14. its values, should the
--            table below ever go: Ambient and OutdoorAmbient 112, 99, 126; Atmosphere Color 40, 34, 52 and Decay
--            18, 16, 26 (the rotunda's, above); Saturation 0.22
local HUB_TINT: { [string]: Look } = {
	neutral = {
		Lighting = { Ambient = Color3.fromRGB(114, 108, 106), OutdoorAmbient = Color3.fromRGB(114, 108, 106), ExposureCompensation = 0.25 },
		Atmosphere = { Density = 0.1, Color = Color3.fromRGB(44, 42, 42), Decay = Color3.fromRGB(20, 19, 19) },
		ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = 0.15, TintColor = Color3.fromRGB(255, 240, 226) },
	},
	purple = {
		Lighting = { Ambient = Color3.fromRGB(112, 99, 126), OutdoorAmbient = Color3.fromRGB(112, 99, 126), ExposureCompensation = 0.25 },
		Atmosphere = { Density = 0.1 },
		ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = 0.22, TintColor = Color3.fromRGB(255, 240, 226) },
	},
}
local hubTint: any = script:GetAttribute("HubTint")
if type(hubTint) ~= "string" or not HUB_TINT[hubTint] then hubTint = "neutral" end

local H = {}
H.hubTint = hubTint -- (which one is on)
H.looks = {
	-- the hub is THE LANES (workspace.Map.Hub.Lanes): warm and a little dim, the lanes and the carpet do the colour
	hub = with(HUB, HUB_TINT[hubTint]),
	-- (the lobby's fountain is Terrain water indoors, 18 Nov: the saved water, the Rooftop pool's, reflects 0.75, and
	-- under a cream ceiling that read as a brown map on the water, its waves throwing ragged lights along the walls. in
	-- the hub the same teal, less mirror, calmer: its own Terrain entry, set just after this table)
	rotunda = HUB,
	-- the training hall is a place to shoot in: same mood, more base light, thinner haze (it's 220 studs long)
	training = with(HUB, {
		Lighting = { Ambient = Color3.fromRGB(140, 134, 156), OutdoorAmbient = Color3.fromRGB(140, 134, 156), ExposureCompensation = 0.25 },
		Atmosphere = { Density = 0.12 },
	}),
	-- the playground is a floodlit yard at dusk (PolishBackup.StructurePass, 2026-11-15; it was a midday test level): the
	-- Rooftop's own evening (its sky, its low warm sun, so no ClockTime here), a thicker haze that swallows the pylons'
	-- feet and the floor far below, a little more bloom for the decks' amber edges
	playground = with(HUB, {
		Lighting = {
			Ambient = Color3.fromRGB(105, 115, 140), OutdoorAmbient = Color3.fromRGB(138, 148, 173), Brightness = 3,
			ExposureCompensation = 0.05, EnvironmentDiffuseScale = 1, EnvironmentSpecularScale = 1,
		},
		-- (a mid-slate haze with little glare: a pale one whited out the far decks when you looked toward the sun)
		Atmosphere = { Density = 0.27, Offset = 0.1, Haze = 0.7, Glare = 0.05, Color = Color3.fromRGB(150, 156, 166), Decay = Color3.fromRGB(104, 110, 122) },
		Bloom = { Intensity = 0.3, Size = 24, Threshold = 2.3 },
		ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = 0.06, TintColor = Color3.fromRGB(255, 255, 255) },
		SunRays = { Intensity = 0.06 },
	}),
} :: { [string]: Look }
H.looks.hub.Terrain = { WaterColor = Color3.fromRGB(28, 150, 178), WaterTransparency = 0.5, WaterReflectance = 0.2, WaterWaveSize = 0.03, WaterWaveSpeed = 5 }
-- the three show hubs of the hub comparison that were not picked (put away in ServerStorage.PolishBackup.HubArchive,
-- each with its look zone: a part in Hub.LookZones with the attribute Look names the look for whoever stands inside
-- it). the fourth, the bowling alley, is the hub now: its look is looks.hub above
-- the station: cool, white and bright, like tiles under strip lights
H.looks.lab_platform = with(HUB, {
	Lighting = { Ambient = Color3.fromRGB(122, 128, 146), OutdoorAmbient = Color3.fromRGB(122, 128, 146), ExposureCompensation = 0.1 },
	Atmosphere = { Density = 0.08, Color = Color3.fromRGB(150, 160, 180), Decay = Color3.fromRGB(90, 100, 120) },
	Bloom = { Intensity = 0.3, Size = 20, Threshold = 2.1 },
	ColorCorrection = { Brightness = 0, Contrast = 0.1, Saturation = 0.1, TintColor = Color3.fromRGB(240, 246, 255) },
})
-- the food court: daylight through a glass roof
H.looks.lab_foodcourt = with(HUB, {
	Lighting = {
		Ambient = Color3.fromRGB(112, 116, 126), OutdoorAmbient = Color3.fromRGB(128, 136, 154), Brightness = 2.6,
		ExposureCompensation = 0.05, EnvironmentDiffuseScale = 0.35, EnvironmentSpecularScale = 0.5,
		-- (an early-afternoon sun from the south-west, behind the spawn's left shoulder, low enough that the trees, tables
		-- and the duck throw their shadows across the floor; straight overhead every shadow fell on its own planter)
		ClockTime = 13.0, GeographicLatitude = 41,
	},
	Atmosphere = { Density = 0.2, Offset = 0.1, Haze = 0.8, Glare = 0.05, Color = Color3.fromRGB(214, 228, 246), Decay = Color3.fromRGB(176, 198, 230) },
	Bloom = { Intensity = 0.25, Size = 20, Threshold = 2.2 },
	ColorCorrection = { Brightness = 0, Contrast = 0.08, Saturation = 0.12, TintColor = Color3.fromRGB(255, 252, 246) },
	SunRays = { Intensity = 0.03 },
})
-- the depot: the training hall's look with a little more base light
H.looks.lab_depot = with(HUB, {
	Lighting = { Ambient = Color3.fromRGB(150, 144, 150), OutdoorAmbient = Color3.fromRGB(150, 144, 150), ExposureCompensation = 0.3 },
	Atmosphere = { Density = 0.1 },
	ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = 0.16, TintColor = Color3.fromRGB(255, 246, 234) },
})
-- the training area v2 (ServerStorage.PolishBackup.TrainingV2, 16 Nov 2026): pale stone rooms under their own lamps,
-- the range open to an early-afternoon sky. more base light than the hub, little haze, neutral colour
H.looks.training_v2 = with(HUB, {
	Lighting = {
		Ambient = Color3.fromRGB(138, 135, 131), OutdoorAmbient = Color3.fromRGB(150, 150, 154), Brightness = 2.2,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.3, EnvironmentSpecularScale = 0.25,
		ClockTime = 14.5, GeographicLatitude = 30, ColorShift_Top = Color3.fromRGB(255, 246, 232),
	},
	Atmosphere = { Density = 0.12, Offset = 0.05, Haze = 0.6, Glare = 0.05, Color = Color3.fromRGB(200, 208, 222), Decay = Color3.fromRGB(150, 162, 186) },
	Bloom = { Intensity = 0.25, Size = 20, Threshold = 2.2 },
	ColorCorrection = { Brightness = 0, Contrast = 0.12, Saturation = 0.06, TintColor = Color3.fromRGB(255, 249, 240) },
	SunRays = { Intensity = 0.02 },
})
-- looks that want the engine's own blue sky: the saved Sky (a sunset box) is put away while one is on
H.plainSky = { lab_foodcourt = true } :: { [string]: boolean }
-- the training area comes in two builds (TrainingV2 switches them and writes the attribute TrainingLook on this
-- script): "v1" the old hall (looks.training above), "v2" the new rooms (looks.training_v2, under the open sky)
H.looks.training_v1 = H.looks.training
H.plainSky.training_v2 = true
if script:GetAttribute("TrainingLook") == "v2" then
	H.looks.training = H.looks.training_v2
	H.plainSky.training = true
end
-- the training area v5 (TrainingCompound, the compound, 20 Nov 2026): a late-afternoon sun, low and warm, and less base
-- light, so the compound's lamps, its panels in their housings and the green portal glow (the redo's judges, rounds 1-3:
-- "flat daylight makes nothing glow"); TrainingV2 writes TrainingLook = "v5" when it builds v5 live
H.looks.training_v5 = with(HUB, {
	Lighting = {
		Ambient = Color3.fromRGB(112, 110, 112), OutdoorAmbient = Color3.fromRGB(148, 142, 136), Brightness = 1.8,
		ExposureCompensation = -0.05, EnvironmentDiffuseScale = 0.22, EnvironmentSpecularScale = 0.3,
		ClockTime = 16.8, GeographicLatitude = 34, ColorShift_Top = Color3.fromRGB(255, 228, 196),
	},
	Atmosphere = { Density = 0.2, Offset = 0.08, Haze = 1.1, Glare = 0.12, Color = Color3.fromRGB(214, 200, 184), Decay = Color3.fromRGB(122, 116, 132) },
	Bloom = { Intensity = 0.4, Size = 22, Threshold = 1.7 },
	ColorCorrection = { Brightness = 0, Contrast = 0.1, Saturation = 0.08, TintColor = Color3.fromRGB(255, 245, 234) },
	SunRays = { Intensity = 0.04 },
})
H.plainSky.training_v5 = true
if script:GetAttribute("TrainingLook") == "v5" then
	H.looks.training = H.looks.training_v5
	H.plainSky.training = true
end
-- the training area's back lot (16 Nov 2026: TrainingLot builds it, TheLot opens it), out in the open behind the
-- garage door: HubLife picks it for whoever is on the lot (the attribute OnLot). v2's light with more air: a thicker
-- haze softens the far horizon (the playground's towers stand far beyond the hills to the south)
H.looks.lot = with(H.looks.training_v2, {
	Lighting = { Brightness = 2.4, OutdoorAmbient = Color3.fromRGB(156, 158, 164) },
	Atmosphere = { Density = 0.42, Offset = 0.3, Haze = 1.8, Glare = 0.08, Color = Color3.fromRGB(196, 214, 236), Decay = Color3.fromRGB(176, 196, 224) },
})
H.plainSky.lot = true
-- Rooftop v2 (ServerStorage.PolishBackup.RooftopV2, 16 Nov 2026): its own light, picked by HubLife in a match when
-- workspace.Map's attribute Arena is "RooftopV2" (v1 keeps the saved evening). an early-afternoon sun from the
-- south-west, high over the lanes, so neither team starts a round looking into a low sun (the first judging failed v2's
-- defenders' spawn for that); the engine's own sky; a little less exposure for its pale stone
H.looks.rooftop_v2 = {
	Lighting = {
		Ambient = Color3.fromRGB(120, 119, 120), OutdoorAmbient = Color3.fromRGB(134, 135, 140), Brightness = 2.6,
		ExposureCompensation = -0.1, EnvironmentDiffuseScale = 0.55, EnvironmentSpecularScale = 0.5,
		ClockTime = 13.2, GeographicLatitude = 41,
		-- (the saved fog is the Rooftop's dusk navy: it turned v2's far horizon into a dark band)
		FogColor = Color3.fromRGB(208, 213, 222), FogStart = 450, FogEnd = 2600,
	},
	-- (a denser pale haze: the far city fades instead of standing black on the horizon)
	Atmosphere = { Density = 0.31, Offset = 0.15, Haze = 1.3, Glare = 0.05, Color = Color3.fromRGB(212, 216, 224), Decay = Color3.fromRGB(162, 170, 184) },
	Bloom = { Intensity = 0.2, Size = 20, Threshold = 2.4 },
	ColorCorrection = { Brightness = 0, Contrast = 0.12, Saturation = -0.06, TintColor = Color3.fromRGB(255, 251, 246) },
	SunRays = { Intensity = 0.02 },
} :: Look
H.plainSky.rooftop_v2 = true
-- Rooftop v3 (ServerStorage.PolishBackup.RooftopV3, 16 Nov 2026: v1's layout redressed to the principles): its own light,
-- picked by HubLife in a match when workspace.Map's attribute Arena is "RooftopV3". v2's afternoon a little warmer: a
-- lower sun from the south, across the lanes (neither team starts looking into it), a pale haze and a pale fog so the far city fades
-- (v1's saved dusk fog is navy: it drew a black band on the horizon)
H.looks.rooftop_v3 = {
	Lighting = {
		Ambient = Color3.fromRGB(118, 116, 114), OutdoorAmbient = Color3.fromRGB(132, 134, 140), Brightness = 2.5,
		ExposureCompensation = -0.1, EnvironmentDiffuseScale = 0.5, EnvironmentSpecularScale = 0.45,
		-- (round 2: "one pale colour under flat midday light") a lower, warmer sun from the south, across the lanes,
		-- so shadows are long and neither team looks into it; a cooler, thicker haze so the city falls back
		-- (measured: latitude 78 at 13:30 puts the sun about 31 degrees up, 14 degrees west of due south)
		ClockTime = 13.5, GeographicLatitude = 78, ColorShift_Top = Color3.fromRGB(255, 226, 192),
		FogColor = Color3.fromRGB(186, 194, 208), FogStart = 400, FogEnd = 2300,
	},
	Atmosphere = { Density = 0.38, Offset = 0.2, Haze = 2.0, Glare = 0.04, Color = Color3.fromRGB(194, 200, 210), Decay = Color3.fromRGB(140, 150, 166) },
	Bloom = { Intensity = 0.2, Size = 20, Threshold = 2.4 },
	ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = -0.1, TintColor = Color3.fromRGB(255, 248, 240) }, -- (rounds 3 and 4: a calmer sky)
	SunRays = { Intensity = 0.02 },
	-- the pool's water, pinned (the owner, 16 Nov 2026: "keep the amazing water look"): Terrain's water exactly as it was
	-- when v3 was judged, so a later change to the place's global water for another arena can't change v3's pool
	Terrain = { WaterColor = Color3.fromRGB(28, 150, 178), WaterTransparency = 0.55, WaterReflectance = 0.75, WaterWaveSize = 0.08, WaterWaveSpeed = 8 },
} :: Look
H.plainSky.rooftop_v3 = true
-- the maps ported from the web game (17 Nov 2026): each arena model's name -> its look here (HubLife, in a match)
H.byArena = {} :: { [string]: string }
-- CRATE (ServerStorage.PolishBackup.WebArena): a toy chest on a tower of giant blocks in a giant child's playroom. The
-- room is closed but for one big window in its north wall: a low sun from the north comes in through it onto the chest
-- (long soft shadows, the far side of the room in its light), the rest is warm indoor light; a pale warm haze
H.looks.crate = {
	Lighting = {
		Ambient = Color3.fromRGB(150, 142, 136), OutdoorAmbient = Color3.fromRGB(150, 144, 140), Brightness = 2.4,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.4, EnvironmentSpecularScale = 0.3,
		ClockTime = 12, GeographicLatitude = -45, ColorShift_Top = Color3.fromRGB(255, 236, 214),
		FogColor = Color3.fromRGB(214, 206, 198), FogStart = 900, FogEnd = 5200,
	},
	Atmosphere = { Density = 0.22, Offset = 0, Haze = 0.6, Glare = 0, Color = Color3.fromRGB(222, 214, 205), Decay = Color3.fromRGB(196, 186, 176) },
	Bloom = { Intensity = 0.25, Size = 22, Threshold = 2.2 },
	ColorCorrection = { Brightness = 0.02, Contrast = 0.1, Saturation = -0.08, TintColor = Color3.fromRGB(255, 249, 242) },
	SunRays = { Intensity = 0.04 },
} :: Look
H.plainSky.crate = true
H.byArena.Crate = "crate"
-- PLATFORM (ServerStorage.PolishBackup.WebArena): an oil rig in a grey northern sea. A bright overcast afternoon: a soft
-- high sun from the south-west, a pale grey-blue haze that swallows the horizon, the sea a step darker than the sky
H.looks.platform = {
	Lighting = {
		Ambient = Color3.fromRGB(128, 132, 138), OutdoorAmbient = Color3.fromRGB(146, 150, 158), Brightness = 2.0,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.5, EnvironmentSpecularScale = 0.4,
		ClockTime = 14.5, GeographicLatitude = 50, ColorShift_Top = Color3.fromRGB(240, 236, 230),
		FogColor = Color3.fromRGB(196, 204, 212), FogStart = 350, FogEnd = 2600,
	},
	Atmosphere = { Density = 0.42, Offset = 0.1, Haze = 2.4, Glare = 0, Color = Color3.fromRGB(202, 210, 218), Decay = Color3.fromRGB(150, 160, 172) },
	Bloom = { Intensity = 0.2, Size = 20, Threshold = 2.4 },
	ColorCorrection = { Brightness = 0, Contrast = 0.12, Saturation = -0.12, TintColor = Color3.fromRGB(248, 250, 255) },
	SunRays = { Intensity = 0.01 },
} :: Look
H.plainSky.platform = true
H.byArena.Platform = "platform"
-- BAZAAR (ServerStorage.PolishBackup.WebArena): a walled desert market town at the end of the day. A warm sun from the
-- south-west, about 35 degrees up (across the gate plazas' line, so neither team starts looking into it), long shadows
-- down the streets, a pale sand haze that hides the desert's edge
H.looks.bazaar = {
	Lighting = {
		Ambient = Color3.fromRGB(138, 128, 118), OutdoorAmbient = Color3.fromRGB(150, 140, 128), Brightness = 2.4,
		ExposureCompensation = -0.05, EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.35,
		ClockTime = 15.5, GeographicLatitude = 35, ColorShift_Top = Color3.fromRGB(255, 230, 200),
		FogColor = Color3.fromRGB(226, 210, 186), FogStart = 400, FogEnd = 2600,
	},
	Atmosphere = { Density = 0.34, Offset = 0.15, Haze = 2.0, Glare = 0.1, Color = Color3.fromRGB(226, 210, 186), Decay = Color3.fromRGB(190, 160, 130) },
	Bloom = { Intensity = 0.22, Size = 22, Threshold = 2.3 },
	ColorCorrection = { Brightness = 0, Contrast = 0.12, Saturation = -0.1, TintColor = Color3.fromRGB(255, 246, 236) },
	SunRays = { Intensity = 0.03 },
} :: Look
H.plainSky.bazaar = true
H.byArena.Bazaar = "bazaar"
-- THE GUT (ServerStorage.PolishBackup.WebArena; tools/roblox/gut_models.py): a soft pink district round the heart tower
-- (17 Nov 2026: "Can we have a map based on the gut district?"). A warm red sky with a pink haze that swallows the far
-- domes; a low warm sun from the south, across the halls' line, so neither team starts looking into it. The subway
-- below has its own lamps
H.looks.gut = {
	Lighting = {
		Ambient = Color3.fromRGB(138, 126, 126), OutdoorAmbient = Color3.fromRGB(160, 140, 138), Brightness = 2.2,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.25, EnvironmentSpecularScale = 0.3,
		ClockTime = 12.5, GeographicLatitude = 92, ColorShift_Top = Color3.fromRGB(255, 222, 205),
		FogColor = Color3.fromRGB(214, 140, 140), FogStart = 300, FogEnd = 1800,
	},
	Atmosphere = { Density = 0.3, Offset = 0.1, Haze = 1.5, Glare = 0.1, Color = Color3.fromRGB(242, 178, 172), Decay = Color3.fromRGB(176, 96, 100) },
	Bloom = { Intensity = 0.32, Size = 24, Threshold = 2.0 },
	ColorCorrection = { Brightness = -0.02, Contrast = 0.17, Saturation = -0.06, TintColor = Color3.fromRGB(255, 246, 244) }, -- (round 2: less haze, more contrast: players must read against the pink)
	SunRays = { Intensity = 0.03 },
} :: Look
-- THE MAP ROOM (server/MapRooms.luau, the "staging" zone; 18 Nov 2026, the owner: "spawn you in liek a void area where
-- the map options appear"): a dark, quiet void. no sun (night), a near-black haze that swallows everything past the
-- platform; enough ambient that the charcoal floor and the bodies still read (the linear-lighting lesson). the light in
-- the room is the three map screens' own glow and one dim lamp over the middle. play-party-ranked's
H.looks.void = {
	Lighting = {
		Ambient = Color3.fromRGB(78, 80, 88), OutdoorAmbient = Color3.fromRGB(60, 62, 70), Brightness = 0.6,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.1, EnvironmentSpecularScale = 0.2,
		ClockTime = 0, GeographicLatitude = 41, ColorShift_Top = Color3.fromRGB(0, 0, 0),
		FogColor = Color3.fromRGB(10, 11, 14), FogStart = 70, FogEnd = 260,
	},
	Atmosphere = { Density = 0.55, Offset = 0, Haze = 0, Glare = 0, Color = Color3.fromRGB(12, 13, 16), Decay = Color3.fromRGB(8, 9, 11) },
	Bloom = { Intensity = 0.4, Size = 24, Threshold = 1.6 },
	ColorCorrection = { Brightness = 0, Contrast = 0.08, Saturation = -0.25, TintColor = Color3.fromRGB(250, 251, 255) },
	SunRays = { Intensity = 0 },
} :: Look
H.plainSky.void = true
H.ownSky = {} :: { [string]: string }    -- a look with its own Sky: the Sky's name in Lighting.SkyParked (attribute OwnSky)
H.ownSky.gut = "GutSky"                    -- (plain gradient faces, tools/roblox/gut_sky.py)
H.byArena.Gut = "gut"
-- BAZAAR v2, "BAZAAR: ROOFTOPS" (ServerStorage.PolishBackup.WebArena; tools/roblox/bazaar2_models.py): a new desert market
-- town with a second level on its roofs (17 Nov 2026). A warm afternoon: the sun from the south about 33 degrees up
-- (across the courtyards' line, so neither team starts looking into it), a pale sand haze over the dunes
H.looks.bazaar2 = {
	Lighting = {
		Ambient = Color3.fromRGB(140, 128, 112), OutdoorAmbient = Color3.fromRGB(156, 142, 124), Brightness = 2.5,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.35,
		ClockTime = 13.0, GeographicLatitude = 80, ColorShift_Top = Color3.fromRGB(255, 228, 196),
		FogColor = Color3.fromRGB(226, 206, 176), FogStart = 400, FogEnd = 2600,
	},
	Atmosphere = { Density = 0.3, Offset = 0.12, Haze = 1.6, Glare = 0.15, Color = Color3.fromRGB(232, 214, 184), Decay = Color3.fromRGB(196, 160, 120) },
	Bloom = { Intensity = 0.24, Size = 22, Threshold = 2.2 },
	ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = -0.06, TintColor = Color3.fromRGB(255, 246, 234) },
	SunRays = { Intensity = 0.03 },
} :: Look
H.plainSky.bazaar2 = true
H.byArena.BazaarV2 = "bazaar2"
-- DESERT v2, "DESERT: CANYON" (WebArena; tools/roblox/desert2_models.py): a winding canyon between two mesas, a rope
-- bridge, sandstorms (DesertStorm.client eases this look's Atmosphere into a sandy wall and back). Hot afternoon light,
-- the sun from the south about 33 degrees up (across the camps' line), a pale dust haze
H.looks.desert2 = {
	Lighting = {
		Ambient = Color3.fromRGB(140, 126, 112), OutdoorAmbient = Color3.fromRGB(156, 140, 122), Brightness = 2.6,
		ExposureCompensation = -0.05, EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.3,
		ClockTime = 13.0, GeographicLatitude = 80, ColorShift_Top = Color3.fromRGB(255, 232, 200),
		FogColor = Color3.fromRGB(228, 206, 172), FogStart = 400, FogEnd = 2600,
	},
	Atmosphere = { Density = 0.3, Offset = 0.12, Haze = 1.6, Glare = 0.15, Color = Color3.fromRGB(232, 210, 176), Decay = Color3.fromRGB(196, 158, 112) },
	Bloom = { Intensity = 0.2, Size = 22, Threshold = 2.3 },
	ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = -0.08, TintColor = Color3.fromRGB(255, 246, 234) },
	SunRays = { Intensity = 0.03 },
} :: Look
H.plainSky.desert2 = true
H.byArena.DesertV2 = "desert2"
-- SUBURB v2, "SUBURB: CUL-DE-SAC" (WebArena; tools/roblox/suburb2_models.py): a quiet suburb on a clear afternoon. A
-- warm sun from the south about 38 degrees up (across the cul-de-sacs' line), a clean blue sky, a light haze over the
-- far hills
H.looks.suburb2 = {
	Lighting = {
		Ambient = Color3.fromRGB(132, 134, 138), OutdoorAmbient = Color3.fromRGB(150, 152, 156), Brightness = 2.4,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.35,
		ClockTime = 13.0, GeographicLatitude = 75, ColorShift_Top = Color3.fromRGB(255, 240, 222),
		FogColor = Color3.fromRGB(200, 212, 224), FogStart = 400, FogEnd = 2600,
	},
	Atmosphere = { Density = 0.28, Offset = 0.08, Haze = 1.2, Glare = 0.05, Color = Color3.fromRGB(204, 216, 228), Decay = Color3.fromRGB(150, 166, 186) },
	Bloom = { Intensity = 0.22, Size = 22, Threshold = 2.3 },
	ColorCorrection = { Brightness = 0, Contrast = 0.12, Saturation = -0.08, TintColor = Color3.fromRGB(255, 250, 244) },
	SunRays = { Intensity = 0.02 },
} :: Look
H.plainSky.suburb2 = true
H.byArena.SuburbV2 = "suburb2"
-- SPOOKY FOREST (WebArena; tools/roblox/forest_models.py, the web's Scary Forest): a pine wood at night by a lake. A
-- moonlit blue-grey, a low cold haze the trunks fade into, warm lamps (the cabin's windows, the camp lantern, the car's
-- hazards, the mast's red lights) doing the rest; dark but readable: a player shows at 150 studs
H.looks.forest = {
	Lighting = {
		Ambient = Color3.fromRGB(132, 140, 160), OutdoorAmbient = Color3.fromRGB(144, 154, 180), Brightness = 2.0,
		ExposureCompensation = 0.55, EnvironmentDiffuseScale = 0.3, EnvironmentSpecularScale = 0.25,
		ClockTime = 0.6, GeographicLatitude = 60, ColorShift_Top = Color3.fromRGB(150, 170, 210),
		FogColor = Color3.fromRGB(46, 56, 76), FogStart = 80, FogEnd = 620,
	},
	Atmosphere = { Density = 0.36, Offset = 0.05, Haze = 1.6, Glare = 0, Color = Color3.fromRGB(92, 106, 132), Decay = Color3.fromRGB(58, 68, 90) },
	Bloom = { Intensity = 0.45, Size = 24, Threshold = 1.6 },
	ColorCorrection = { Brightness = 0.02, Contrast = 0.12, Saturation = -0.18, TintColor = Color3.fromRGB(226, 234, 255) },
	SunRays = { Intensity = 0 },
	Terrain = { WaterColor = Color3.fromRGB(34, 50, 62), WaterTransparency = 0.35, WaterReflectance = 0.35, WaterWaveSize = 0.05, WaterWaveSpeed = 6 },
} :: Look
H.plainSky.forest = true -- (Roblox's own night sky: the moon and the stars)
H.byArena.Forest = "forest"
-- BACKROOMS (WebArena; tools/roblox/backrooms_models.py, the web's Backrooms): sealed yellow rooms. No sun: the light is
-- the ceiling's, a warm yellow-white ambient with a yellowish haze close in and soft bloom on the panels
H.looks.backrooms = {
	Lighting = {
		Ambient = Color3.fromRGB(150, 140, 112), OutdoorAmbient = Color3.fromRGB(120, 112, 90), Brightness = 0,
		ExposureCompensation = 0.1, EnvironmentDiffuseScale = 0.2, EnvironmentSpecularScale = 0.15,
		ClockTime = 0, GeographicLatitude = 41, ColorShift_Top = Color3.fromRGB(0, 0, 0),
		FogColor = Color3.fromRGB(196, 182, 128), FogStart = 40, FogEnd = 420,
	},
	Atmosphere = { Density = 0.4, Offset = 0, Haze = 1.4, Glare = 0, Color = Color3.fromRGB(204, 188, 128), Decay = Color3.fromRGB(170, 150, 96) },
	Bloom = { Intensity = 0.4, Size = 24, Threshold = 1.7 },
	ColorCorrection = { Brightness = 0.02, Contrast = 0.1, Saturation = -0.05, TintColor = Color3.fromRGB(255, 248, 228) },
	SunRays = { Intensity = 0 },
	Terrain = { WaterColor = Color3.fromRGB(120, 176, 180), WaterTransparency = 0.8, WaterReflectance = 0.25, WaterWaveSize = 0, WaterWaveSpeed = 0 },
} :: Look
H.plainSky.backrooms = true
H.byArena.Backrooms = "backrooms"
-- ARCTIC CABIN (WebArena; tools/roblox/arctic_models.py, a new arena): a snowy cabin compound on a bright winter
-- midday. A low sun from the south (about 28 degrees up, across the teams' line), a cool pale haze over the mountains,
-- bloom held back so the snow never blows out
H.looks.arctic = {
	Lighting = {
		Ambient = Color3.fromRGB(128, 134, 146), OutdoorAmbient = Color3.fromRGB(146, 154, 168), Brightness = 2.1,
		ExposureCompensation = -0.15, EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.3,
		ClockTime = 13.3, GeographicLatitude = 84, ColorShift_Top = Color3.fromRGB(255, 236, 214),
		FogColor = Color3.fromRGB(206, 216, 228), FogStart = 300, FogEnd = 2200,
	},
	Atmosphere = { Density = 0.34, Offset = 0.06, Haze = 1.6, Glare = 0.08, Color = Color3.fromRGB(212, 222, 232), Decay = Color3.fromRGB(156, 170, 190) },
	Bloom = { Intensity = 0.16, Size = 20, Threshold = 2.6 },
	ColorCorrection = { Brightness = -0.02, Contrast = 0.1, Saturation = -0.12, TintColor = Color3.fromRGB(246, 249, 255) },
	SunRays = { Intensity = 0.015 },
} :: Look
H.plainSky.arctic = true
H.byArena.ArcticCabin = "arctic"
-- SKATEPARK (WebArena; tools/roblox/skatepark_models.py, a new small arena): a city skatepark late in the day. A low
-- golden sun from the south (across the teams' line, so nobody starts a round staring into it), a warm haze over the
-- city, the floodlights already on
H.looks.skatepark = {
	Lighting = {
		Ambient = Color3.fromRGB(118, 110, 104), OutdoorAmbient = Color3.fromRGB(138, 128, 120), Brightness = 2.0,
		ExposureCompensation = -0.3, EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.3,
		ClockTime = 13.0, GeographicLatitude = 86, ColorShift_Top = Color3.fromRGB(255, 214, 170),
		FogColor = Color3.fromRGB(220, 196, 176), FogStart = 400, FogEnd = 2600,
	},
	Atmosphere = { Density = 0.3, Offset = 0.06, Haze = 1.4, Glare = 0.12, Color = Color3.fromRGB(226, 200, 178), Decay = Color3.fromRGB(170, 140, 132) },
	Bloom = { Intensity = 0.3, Size = 24, Threshold = 2.0 },
	ColorCorrection = { Brightness = 0, Contrast = 0.12, Saturation = -0.06, TintColor = Color3.fromRGB(255, 246, 236) },
	SunRays = { Intensity = 0.03 },
} :: Look
H.plainSky.skatepark = true
H.byArena.Skatepark = "skatepark"
-- STATION (WebArena; tools/roblox/station_arena_models.py, a new medium arena): a small-town terminus at golden hour, a
-- train waiting. A warm low sun from the south, a little west (across the teams' line), warm haze
H.looks.station = {
	Lighting = {
		Ambient = Color3.fromRGB(134, 124, 114), OutdoorAmbient = Color3.fromRGB(156, 140, 124), Brightness = 2.2,
		ExposureCompensation = -0.15, EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.3,
		ClockTime = 14.6, GeographicLatitude = 78, ColorShift_Top = Color3.fromRGB(255, 214, 170),
		FogColor = Color3.fromRGB(224, 206, 186), FogStart = 400, FogEnd = 2400,
	},
	Atmosphere = { Density = 0.3, Offset = 0.08, Haze = 1.4, Glare = 0.12, Color = Color3.fromRGB(232, 206, 176), Decay = Color3.fromRGB(180, 140, 110) },
	Bloom = { Intensity = 0.24, Size = 22, Threshold = 2.2 },
	ColorCorrection = { Brightness = 0, Contrast = 0.1, Saturation = -0.06, TintColor = Color3.fromRGB(255, 244, 230) },
	SunRays = { Intensity = 0.03 },
} :: Look
H.plainSky.station = true
H.byArena.Station = "station"
-- JANKFIELD HIGH (WebArena; tools/roblox/school_models.py, the zombies school): a school at night. Roblox's own night sky
-- (the moon), a cool dim violet outside and a faint haze over the grounds; inside, the ceiling panels light the halls
H.looks.school = {
	Lighting = {
		Ambient = Color3.fromRGB(96, 92, 112), OutdoorAmbient = Color3.fromRGB(84, 80, 108), Brightness = 0.7,
		ExposureCompensation = 0.1, EnvironmentDiffuseScale = 0.3, EnvironmentSpecularScale = 0.2,
		ClockTime = 0.5, GeographicLatitude = 41, ColorShift_Top = Color3.fromRGB(150, 160, 210),
		FogColor = Color3.fromRGB(40, 34, 58), FogStart = 160, FogEnd = 900,
	},
	Atmosphere = { Density = 0.3, Offset = 0.04, Haze = 1.2, Glare = 0, Color = Color3.fromRGB(72, 64, 98), Decay = Color3.fromRGB(42, 36, 60) },
	Bloom = { Intensity = 0.35, Size = 24, Threshold = 1.8 },
	ColorCorrection = { Brightness = 0.02, Contrast = 0.1, Saturation = -0.08, TintColor = Color3.fromRGB(244, 242, 255) },
	SunRays = { Intensity = 0 },
} :: Look
H.plainSky.school = true
H.byArena.JankfieldHigh = "school"
-- JANKFIELD HIGH v2A / v2B (20 Nov 2026; school_models.py --variant): the same school rebuilt chunky, darker. The owner:
-- "make it a little darker, maybe the ceiling lights flicker". A cold moon outside, a low ambient floor (never black where
-- you play), denser haze; the light comes from every other ceiling fitting (pools and shadow) and SchoolLife.client
-- flickers a few. v2A (old: brick, terrazzo, timber, globes) a touch warm; v2B (new: concrete, felt, troughs) a touch cool.
-- (round 2: the ambient a third lower and neutral; the judges saw the shadows go violet and an even blue fill)
H.looks.school_v2a = {
	Lighting = {
		Ambient = Color3.fromRGB(68, 65, 61), OutdoorAmbient = Color3.fromRGB(50, 53, 64), Brightness = 0.55,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.25, EnvironmentSpecularScale = 0.2,
		ClockTime = 0.3, GeographicLatitude = 41, ColorShift_Top = Color3.fromRGB(150, 168, 222),
		FogColor = Color3.fromRGB(26, 28, 40), FogStart = 120, FogEnd = 700,
	},
	Atmosphere = { Density = 0.36, Offset = 0.04, Haze = 1.6, Glare = 0, Color = Color3.fromRGB(52, 56, 76), Decay = Color3.fromRGB(26, 28, 40) },
	Bloom = { Intensity = 0.4, Size = 24, Threshold = 1.6 },
	ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = -0.1, TintColor = Color3.fromRGB(252, 246, 236) },
	SunRays = { Intensity = 0 },
} :: Look
H.plainSky.school_v2a = true
H.byArena.JankfieldHighV2A = "school_v2a"
H.looks.school_v2b = {
	Lighting = {
		Ambient = Color3.fromRGB(70, 71, 73), OutdoorAmbient = Color3.fromRGB(48, 52, 64), Brightness = 0.55,
		ExposureCompensation = 0, EnvironmentDiffuseScale = 0.25, EnvironmentSpecularScale = 0.25,
		ClockTime = 0.3, GeographicLatitude = 41, ColorShift_Top = Color3.fromRGB(150, 168, 222),
		FogColor = Color3.fromRGB(24, 28, 40), FogStart = 120, FogEnd = 700,
	},
	Atmosphere = { Density = 0.36, Offset = 0.04, Haze = 1.6, Glare = 0, Color = Color3.fromRGB(50, 56, 78), Decay = Color3.fromRGB(24, 28, 40) },
	Bloom = { Intensity = 0.4, Size = 24, Threshold = 1.6 },
	ColorCorrection = { Brightness = 0, Contrast = 0.14, Saturation = -0.12, TintColor = Color3.fromRGB(246, 248, 252) },
	SunRays = { Intensity = 0 },
} :: Look
H.plainSky.school_v2b = true
H.byArena.JankfieldHighV2B = "school_v2b"

-- THE HOTEL (studio-tools/HubHotel.luau, its look zone): an interior lit by its chandeliers and coffer lamps, so the
-- ambient a step lower than the hub's and warm, the bloom a little readier for the lamps (judge round 1)
H.looks.hotel = with(HUB, {
	-- (round 4, judge round 3: "one even warm beige wash") a lower, nearly neutral ambient and a light tint, so the lamps,
	-- the signs and the pads are the bright things and the ceilings sit darker than the walls
	Lighting = { Ambient = Color3.fromRGB(78, 77, 78), OutdoorAmbient = Color3.fromRGB(78, 77, 78), ExposureCompensation = -0.1 }, -- (round 5: a step dimmer)
	Atmosphere = { Density = 0.05, Color = Color3.fromRGB(52, 48, 44), Decay = Color3.fromRGB(24, 22, 20) },
	Bloom = { Intensity = 0.5, Size = 22, Threshold = 1.5 },
	ColorCorrection = { Brightness = 0, Contrast = 0.2, Saturation = 0.05, TintColor = Color3.fromRGB(255, 248, 240) },
})

local function target(name: string): Instance?
	if name == "Terrain" then return workspace.Terrain end -- (a look may pin the water: rooftop_v3)
	return if name == "Lighting" then Lighting else Lighting:FindFirstChild(name)
end
local function key(name: string, prop: string): string return "Saved_" .. name .. "_" .. prop end
-- every property any look touches (a look that doesn't name one gets the saved value back)
local function allProps(): { [string]: { [string]: boolean } }
	local all = {}
	for _, look in H.looks do
		for name, props in look do
			all[name] = all[name] or {}
			for p in props do all[name][p] = true end
		end
	end
	return all
end

-- the look to go back to: the values an edit-time preview parked on this module if there are any (so a place saved
-- mid-preview still restores), else what Lighting holds right now
local function capture(): Look
	local s: Look = {}
	for name, props in allProps() do
		local inst = target(name)
		if not inst then continue end
		s[name] = {}
		for p in props do
			local parked = Lighting:GetAttribute(key(name, p))
			s[name][p] = if parked ~= nil then parked else (inst :: any)[p]
		end
	end
	return s
end

local saved: Look? = nil
local function merged(look: Look?): Look
	local out: Look = {}
	for name, props in saved :: Look do
		out[name] = table.clone(props)
		if look and look[name] then for p, v in look[name] do out[name][p] = v end end
	end
	return out
end
-- the saved Sky is put away in a folder under Lighting (a Sky only counts as Lighting's own child), never in this
-- script: an edit-time preview may run from a throwaway copy of the module, and the Sky must outlive it
-- a look may bring its own Sky instead (H.ownSky: a Sky with the attribute OwnSky, kept in the same folder until its
-- look is on)
local function savedSky(within: Instance?): Sky?
	if not within then return nil end
	for _, c in within:GetChildren() do
		if c:IsA("Sky") and not c:GetAttribute("OwnSky") then return c end
	end
	return nil
end
local function sky(plain: boolean, own: string?)
	local park: Instance? = Lighting:FindFirstChild("SkyParked")
	if (plain or own) and not park then
		local f = Instance.new("Folder")
		f.Name = "SkyParked"; f.Parent = Lighting
		park = f
	end
	for _, c in Lighting:GetChildren() do
		if c:IsA("Sky") and c:GetAttribute("OwnSky") and c.Name ~= own and park then c.Parent = park end
	end
	local s = savedSky(Lighting) or savedSky(park) or savedSky(script)
	local mine = if own and park then park:FindFirstChild(own) else nil
	if s then s.Parent = if (plain or mine) and park then park else Lighting end
	if mine then mine.Parent = Lighting end
end

-- name = "hub" / "training" / "playground" (or any other key of H.looks), or nil for the saved (match) look. t = seconds to blend (nil or 0 snaps)
function H.set(name: string?, t: number?)
	if not saved then saved = capture() end
	local to = merged(if name then H.looks[name] else nil)
	sky(name ~= nil and H.plainSky[name] == true, if name then H.ownSky[name] else nil)
	for objName, props in to do
		local inst = target(objName)
		if not inst then continue end
		if t and t > 0 then
			TweenService:Create(inst, TweenInfo.new(t, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), props):Play()
		else
			for p, v in props do (inst :: any)[p] = v end
		end
	end
end

-- Studio only: show a look while editing. the Rooftop's values are parked as attributes on Lighting
function H.preview(name: any): string
	local parked = Lighting:GetAttribute("Previewing") == true
	local look = if type(name) == "string" then H.looks[name] else nil
	if look then
		if not parked then
			for objName, props in allProps() do
				local inst = target(objName)
				if inst then for p in props do Lighting:SetAttribute(key(objName, p), (inst :: any)[p]) end end
			end
			Lighting:SetAttribute("Previewing", true)
		end
		saved = capture()
		for objName, props in merged(look) do
			local inst = target(objName)
			if inst then for p, v in props do (inst :: any)[p] = v end end
		end
		sky(H.plainSky[name] == true, H.ownSky[name])
		return name .. " look ON (preview). run preview(false) before saving"
	end
	if not parked then return "not previewing" end
	for objName, props in allProps() do
		local inst = target(objName)
		if not inst then continue end
		for p in props do
			local v = Lighting:GetAttribute(key(objName, p))
			if v ~= nil then (inst :: any)[p] = v; Lighting:SetAttribute(key(objName, p), nil) end
		end
	end
	sky(false)
	Lighting:SetAttribute("Previewing", nil)
	return "saved look restored"
end

return H
