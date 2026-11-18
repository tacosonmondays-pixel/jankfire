--!strict
-- ArcticLife (18 Nov 2026): light snowfall in the Arctic Cabin. One invisible part (in the camera: on this client only)
-- with one ParticleEmitter, kept 25 studs over the camera ten times a second while your arena is the Arctic Cabin (or
-- a match copy of it: copies share the Arena name). Slow, soft, pale-grey dots drifting a little with the wind; off the
-- moment you leave. Nothing per frame on many instances (roblox/docs/PERFORMANCE.md).
local Players = game:GetService("Players")
local me = Players.LocalPlayer
local ARENA = "ArcticCabin"
local DOT = "rbxassetid://107753175681578" -- (the VFX library's soft round glow, roblox/assets/vfx/assets.json vfx_glow)

local part: BasePart? = nil
local emitter: ParticleEmitter? = nil

local function make()
	local cam = workspace.CurrentCamera
	if not cam then return end
	local p = Instance.new("Part")
	p.Name = "ArcticSnow"
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.new(90, 1, 90)
	local e = Instance.new("ParticleEmitter")
	e.Texture = DOT
	e.EmissionDirection = Enum.NormalId.Bottom
	e.Shape = Enum.ParticleEmitterShape.Box
	e.Rate = 140
	e.Lifetime = NumberRange.new(6, 9)
	e.Speed = NumberRange.new(3.5, 6)
	e.SpreadAngle = Vector2.new(14, 14)
	e.Acceleration = Vector3.new(1.4, 0, 0.6)
	e.Drag = 0.2
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16), NumberSequenceKeypoint.new(1, 0.24) })
	e.Color = ColorSequence.new(Color3.fromRGB(236, 240, 246))
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.08, 0.25),
		NumberSequenceKeypoint.new(0.85, 0.35), NumberSequenceKeypoint.new(1, 1) })
	e.LightEmission = 0; e.LightInfluence = 1
	e.Rotation = NumberRange.new(0, 360); e.RotSpeed = NumberRange.new(-30, 30)
	e.Enabled = false
	e.Parent = p
	p.Parent = cam
	part, emitter = p, e
end

while true do
	task.wait(0.1)
	local on = me:GetAttribute("Arena") == ARENA
	if on and not (part and part.Parent) then make() end
	local cam = workspace.CurrentCamera
	if part and cam then
		if on then part.CFrame = CFrame.new(cam.CFrame.Position + Vector3.new(0, 25, 0)) end
		if emitter and emitter.Enabled ~= on then emitter.Enabled = on end
	end
end
