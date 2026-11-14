--!strict
-- the looks: Lighting is one global thing and the saved values are tuned for the Rooftop, so each client swaps to its
-- own look while its player is somewhere else, and back to the saved look for a match (the places are far apart and
-- can't see each other). hub = dark and cozy, lit by its own lamps and glow; training = the same mood with more base
-- light; playground = open air, midday, clean and white.
-- edit-time preview from the command bar: require(game.ReplicatedStorage.Jankfire.HubLook).preview("hub" | "training"
-- | "playground") and .preview(false) to put the saved look back. ALWAYS preview(false) before saving the place
local Lighting = game:GetService("Lighting")
local TweenService = game:GetService("TweenService")

type Look = { [string]: { [string]: any } }
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

local H = {}
H.looks = {
	hub = HUB,
	-- the training hall is a place to shoot in: same mood, more base light, thinner haze (it's 220 studs long)
	training = with(HUB, {
		Lighting = { Ambient = Color3.fromRGB(140, 134, 156), OutdoorAmbient = Color3.fromRGB(140, 134, 156), ExposureCompensation = 0.25 },
		Atmosphere = { Density = 0.12 },
	}),
	-- the playground is outdoors: a midday sun, soft blue haze that swallows the far blocks, nothing moody
	playground = with(HUB, {
		Lighting = {
			Ambient = Color3.fromRGB(150, 156, 172), OutdoorAmbient = Color3.fromRGB(170, 178, 198), Brightness = 2.4,
			ExposureCompensation = 0.1, EnvironmentDiffuseScale = 0.6, EnvironmentSpecularScale = 0.5, ClockTime = 13.4,
		},
		Atmosphere = { Density = 0.3, Offset = 0.15, Haze = 1.4, Glare = 0.1, Color = Color3.fromRGB(214, 228, 246), Decay = Color3.fromRGB(176, 198, 230) },
		Bloom = { Intensity = 0.25, Size = 20, Threshold = 2.2 },
		ColorCorrection = { Brightness = 0.02, Contrast = 0.06, Saturation = 0.05, TintColor = Color3.fromRGB(255, 255, 255) },
		SunRays = { Intensity = 0.04 },
	}),
} :: { [string]: Look }
-- looks that want the engine's own blue sky: the saved Sky (a sunset box) is put away while one is on
H.plainSky = { playground = true } :: { [string]: boolean }

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
			local parked = script:GetAttribute(key(name, p))
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
local function sky(plain: boolean)
	local s = Lighting:FindFirstChildOfClass("Sky") or script:FindFirstChildOfClass("Sky")
	if s then s.Parent = if plain then script else Lighting end
end

-- name = "hub" / "training" / "playground", or nil for the saved (match) look. t = seconds to blend (nil or 0 snaps)
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

-- Studio only: show a look while editing. the Rooftop's values are parked as attributes on this module
function H.preview(name: any): string
	local parked = script:GetAttribute("Previewing") == true
	local look = if type(name) == "string" then H.looks[name] else nil
	if look then
		if not parked then
			for objName, props in allProps() do
				local inst = target(objName)
				if inst then for p in props do script:SetAttribute(key(objName, p), (inst :: any)[p]) end end
			end
			script:SetAttribute("Previewing", true)
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
			local v = script:GetAttribute(key(objName, p))
			if v ~= nil then (inst :: any)[p] = v; script:SetAttribute(key(objName, p), nil) end
		end
	end
	sky(false)
	script:SetAttribute("Previewing", nil)
	return "saved look restored"
end

return H
