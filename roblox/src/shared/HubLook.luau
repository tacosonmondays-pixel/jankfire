--!strict
-- the indoor looks: dark and cozy, lit by the rooms' own lamps and glow. Lighting is one global thing and the saved
-- values are tuned for the Rooftop, so each client swaps to an indoor look while its player is in the hub or the
-- training hall, and back to the saved look for a match (the places are far apart and can't see each other).
-- edit-time preview from the command bar: require(game.ReplicatedStorage.Jankfire.HubLook).preview("hub" | "training")
-- and .preview(false) to put the saved look back. ALWAYS preview(false) before saving the place
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
} :: { [string]: Look }

local function target(name: string): Instance?
	return if name == "Lighting" then Lighting else Lighting:FindFirstChild(name)
end
local function key(name: string, prop: string): string return "Saved_" .. name .. "_" .. prop end

-- the look to go back to: the values an edit-time preview parked on this module if there are any (so a place saved
-- mid-preview still restores), else what Lighting holds right now
local function capture(): Look
	local s: Look = {}
	for name, props in HUB do
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

-- name = "hub" / "training", or nil for the saved (match) look. t = seconds to blend (nil or 0 snaps)
function H.set(name: string?, t: number?)
	if not saved then saved = capture() end
	local to = (if name then H.looks[name] else nil) or saved :: any
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

-- Studio only: show an indoor look while editing. the Rooftop's values are parked as attributes on this module
function H.preview(name: any): string
	local parked = script:GetAttribute("Previewing") == true
	local look = if type(name) == "string" then H.looks[name] else nil
	if look then
		if not parked then
			for objName, props in HUB do
				local inst = target(objName)
				if inst then for p in props do script:SetAttribute(key(objName, p), (inst :: any)[p]) end end
			end
			script:SetAttribute("Previewing", true)
		end
		for objName, props in look do
			local inst = target(objName)
			if inst then for p, v in props do (inst :: any)[p] = v end end
		end
		return name .. " look ON (preview). run preview(false) before saving"
	end
	if not parked then return "not previewing" end
	for objName, props in HUB do
		local inst = target(objName)
		if not inst then continue end
		for p in props do
			local v = script:GetAttribute(key(objName, p))
			if v ~= nil then (inst :: any)[p] = v; script:SetAttribute(key(objName, p), nil) end
		end
	end
	script:SetAttribute("Previewing", nil)
	return "saved look restored"
end

return H
