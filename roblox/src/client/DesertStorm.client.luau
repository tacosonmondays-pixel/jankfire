--!strict
-- DESERT v2's sandstorm, on your own screen (17 Nov 2026; the arena: tools/roblox/desert2_models.py, built by WebArena
-- as workspace.Map.DesertV2, copies in Map.ArenaCopies). The server picks when (DesertStorm.server writes the arena's
-- StormAt, the server time it starts, and StormLen). While one blows and your camera is in that arena:
--   the haze thickens into a sandy wall (Lighting's Atmosphere eased toward STORM over RAMP seconds, held, eased back),
--   sand streams past you (an emitter on a box round the camera, parented to the camera: yours alone),
--   the wind's recording plays if the arena has one (attribute WindSound, an rbxassetid string).
-- It is look only: nothing in play changes but how far anyone can see, the same for everyone.
-- It never fights HubLook: if your Zone or Arena changes mid-storm (the match ends, you leave), it stops at once and
-- leaves the Atmosphere to HubLife's new look; when a storm ends normally it eases back to the desert look's own values
-- (HubLook.looks.desert2.Atmosphere), or to what it found if that look isn't the one on.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local SoundService = game:GetService("SoundService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HubLook = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HubLook")) :: any
local LOOK = "desert2"
local RAMP = 3.5                                   -- seconds to thicken, and to clear
local HALF = Vector3.new(190, 120, 140)            -- the arena's reach round its origin (x, up and down, z)
local STORM = {
	Density = 0.75, Offset = 0.3, Haze = 3.0, Glare = 0,
	Color = Color3.fromRGB(212, 168, 112), Decay = Color3.fromRGB(168, 120, 72),
}
local WIND = Vector3.new(1, 0, -0.35).Unit        -- the way the sand blows (from the south-west)
local me = Players.LocalPlayer

-- ---------------------------------------------------------------- which desert arena the camera is in
local found: { Model } = {}
local look = 0
local function scan()
	table.clear(found)
	local map = workspace:FindFirstChild("Map")
	if not map then return end
	for _, parent in { map, map:FindFirstChild("ArenaCopies") } do
		if not parent then continue end
		for _, m in parent:GetChildren() do
			if m:IsA("Model") and m:GetAttribute("MapId") == "desert2" then table.insert(found, m) end
		end
	end
end
local function arenaAt(p: Vector3): Model?
	for _, m in found do
		if not m.Parent then continue end
		local d = p - m:GetPivot().Position
		if math.abs(d.X) <= HALF.X and math.abs(d.Y) <= HALF.Y and math.abs(d.Z) <= HALF.Z then return m end
	end
	return nil
end

-- ---------------------------------------------------------------- the storm's pieces (made once, kept idle)
local dust: Part? = nil
local emitter: ParticleEmitter? = nil
local wind: Sound? = nil
local function pieces(cam: Camera)
	if dust and dust.Parent then return end
	local p = Instance.new("Part")
	p.Name = "DesertStormDust"
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.new(150, 40, 150)
	local e = Instance.new("ParticleEmitter")
	e.Texture = "rbxasset://textures/particles/smoke_main.dds"
	e.Color = ColorSequence.new(Color3.fromRGB(214, 172, 118), Color3.fromRGB(190, 148, 98))
	e.LightEmission = 0; e.LightInfluence = 1
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 5), NumberSequenceKeypoint.new(1, 14) })
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.6), NumberSequenceKeypoint.new(0.8, 0.75), NumberSequenceKeypoint.new(1, 1) })
	e.Lifetime = NumberRange.new(1.6, 2.6)
	e.Speed = NumberRange.new(55, 85)
	e.SpreadAngle = Vector2.new(8, 8)
	e.Rotation = NumberRange.new(0, 360); e.RotSpeed = NumberRange.new(-30, 30)
	e.Acceleration = Vector3.new(0, -3, 0)
	e.EmissionDirection = Enum.NormalId.Front
	e.Shape = Enum.ParticleEmitterShape.Box
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	e.Rate = 0
	e.Parent = p
	p.Parent = cam                                  -- (under the camera: on your screen only)
	dust, emitter = p, e
end
local function stopPieces()
	if emitter then emitter.Rate = 0 end
	if wind then wind:Stop(); wind:Destroy(); wind = nil end
end

-- ---------------------------------------------------------------- the Atmosphere: ease between two sets of values
type Atmo = { Density: number, Offset: number, Haze: number, Glare: number, Color: Color3, Decay: Color3 }
local function read(a: Atmosphere): Atmo
	return { Density = a.Density, Offset = a.Offset, Haze = a.Haze, Glare = a.Glare, Color = a.Color, Decay = a.Decay }
end
local function write(a: Atmosphere, v: Atmo)
	a.Density = v.Density; a.Offset = v.Offset; a.Haze = v.Haze; a.Glare = v.Glare; a.Color = v.Color; a.Decay = v.Decay
end
local function mix(x: Atmo, y: any, k: number): Atmo
	return {
		Density = x.Density + (y.Density - x.Density) * k, Offset = x.Offset + (y.Offset - x.Offset) * k,
		Haze = x.Haze + (y.Haze - x.Haze) * k, Glare = x.Glare + (y.Glare - x.Glare) * k,
		Color = x.Color:Lerp(y.Color, k), Decay = x.Decay:Lerp(y.Decay, k),
	}
end
-- the desert look's own Atmosphere when it is the one on (your match is on a desert arena), else nil
local function lookTarget(base: Atmo): Atmo?
	if me:GetAttribute("Zone") ~= "match" then return nil end
	local an = me:GetAttribute("Arena")
	local by = HubLook.byArena
	if type(an) ~= "string" or not by or by[an] ~= LOOK then return nil end
	local l = HubLook.looks[LOOK]
	local at = l and l.Atmosphere
	if not at then return nil end
	return {
		Density = at.Density or base.Density, Offset = at.Offset or base.Offset, Haze = at.Haze or base.Haze,
		Glare = at.Glare or base.Glare, Color = at.Color or base.Color, Decay = at.Decay or base.Decay,
	}
end

-- ---------------------------------------------------------------- the storm itself
local active: { arena: Model, at: number, len: number, base: Atmo, key: string }? = nil
local function keyNow(): string return tostring(me:GetAttribute("Zone")) .. "|" .. tostring(me:GetAttribute("Arena")) end

local function strength(now: number, at: number, len: number): number
	if now < at or now > at + len then return 0 end
	local up = math.clamp((now - at) / RAMP, 0, 1)
	local down = math.clamp((at + len - now) / RAMP, 0, 1)
	local k = math.min(up, down)
	return k * k * (3 - 2 * k)
end

RunService.RenderStepped:Connect(function(dt)
	look += dt
	if look > 2 then look = 0; scan() end
	local cam = workspace.CurrentCamera
	if not cam then return end
	local atmo = Lighting:FindFirstChildOfClass("Atmosphere")
	local now = workspace:GetServerTimeNow()
	local here = arenaAt(cam.CFrame.Position)
	if active then
		local s = active
		-- the match / look changed: stop now and touch nothing (HubLife's new look takes the light)
		if keyNow() ~= s.key then
			stopPieces(); active = nil
			return
		end
		-- the camera left the arena (a death camera, a teleport) with the look unchanged: clear the haze now
		if here ~= s.arena or not s.arena.Parent then
			if atmo then write(atmo, lookTarget(s.base) or s.base) end
			stopPieces(); active = nil
			return
		end
		local k = strength(now, s.at, s.len)
		if now > s.at + s.len then
			if atmo then write(atmo, lookTarget(s.base) or s.base) end
			stopPieces(); active = nil
			return
		end
		if atmo then write(atmo, mix(lookTarget(s.base) or s.base, STORM, k)) end
		if dust and emitter then
			local p = cam.CFrame.Position + Vector3.new(0, 8, 0) - WIND * 40
			dust.CFrame = CFrame.lookAt(p, p + WIND)
			emitter.Rate = 260 * k
		end
		if wind then wind.Volume = 0.7 * k end
		return
	end
	if not here then return end
	local at, len = here:GetAttribute("StormAt"), here:GetAttribute("StormLen")
	if type(at) ~= "number" or type(len) ~= "number" then return end
	if now < at or now > at + len - RAMP then return end
	-- a storm is on and we're in it: start (late joiners come in part way)
	pieces(cam)
	local base = if atmo then read(atmo) else { Density = 0.3, Offset = 0, Haze = 1, Glare = 0, Color = Color3.new(1, 1, 1), Decay = Color3.new(1, 1, 1) }
	active = { arena = here, at = at, len = len, base = base, key = keyNow() }
	local id = here:GetAttribute("WindSound")
	if type(id) == "string" and id ~= "" then
		local s = Instance.new("Sound")
		s.Name = "DesertStormWind"; s.SoundId = id; s.Looped = true; s.Volume = 0
		s.Parent = SoundService
		s:Play()
		wind = s
	end
end)
scan()
