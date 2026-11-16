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
-- looks that want the engine's own blue sky: the saved Sky (a sunset box) is put away while one is on
H.plainSky = { lab_foodcourt = true } :: { [string]: boolean }

local function target(name: string): Instance?
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
local function sky(plain: boolean)
	local park: Instance? = Lighting:FindFirstChild("SkyParked")
	local s = Lighting:FindFirstChildOfClass("Sky") or (park and park:FindFirstChildOfClass("Sky")) or script:FindFirstChildOfClass("Sky")
	if not s then return end
	if plain then
		if not park then
			local f = Instance.new("Folder")
			f.Name = "SkyParked"; f.Parent = Lighting
			park = f
		end
		s.Parent = park
	else
		s.Parent = Lighting
	end
end

-- name = "hub" / "training" / "playground" (or any other key of H.looks), or nil for the saved (match) look. t = seconds to blend (nil or 0 snaps)
function H.set(name: string?, t: number?)
	if not saved then saved = capture() end
	local to = merged(if name then H.looks[name] else nil)
	sky(name ~= nil and H.plainSky[name] == true)
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
		sky(H.plainSky[name] == true)
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
