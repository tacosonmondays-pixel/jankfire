--!strict
-- HOUSE HUNT's dust in the light (owner, 27 Nov: "Can you add ambiance stuff like dust particles under light?"): tiny
-- soft motes drifting in a lit volume, and a faint shaft for them to live in. The films' rooms use it on the client
-- (the intro's PC glow, the attic's TV); THE HOUSE's own windows and lamp pools are built in Edit by
-- studio-tools/HuntBuild B.ambience with the same numbers.
-- The motes are lit by the scene (LightInfluence 1, a little emission): they show where light falls. Counts stay low
-- (rate from the volume, capped), so hiding stays readable and the render cost is a fraction of a millisecond.
local D = {}

D.DOT = "rbxassetid://107753175681578" -- (the VFX library's soft round glow, roblox/assets/vfx/assets.json vfx_glow)

local function kp(t: number, v: number, e: number?): NumberSequenceKeypoint
	return NumberSequenceKeypoint.new(t, v, e or 0)
end

-- motes in a box (cf, size), the colour of the light they sit in. prefill: emit a lifetime's worth at once (a room
-- built as a film starts would otherwise fill up over ten seconds)
function D.motes(parent: Instance, cf: CFrame, size: Vector3, col: Color3, opts: any?): BasePart
	local o = opts or {}
	local p = Instance.new("Part")
	p.Name = o.name or "DustMotes"
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = size; p.CFrame = cf
	local e = Instance.new("ParticleEmitter")
	e.Name = "Motes"
	e.Texture = D.DOT
	e.Color = ColorSequence.new(col)
	e.LightInfluence = 1
	e.LightEmission = o.emission or 0.35
	e.Brightness = o.brightness or 1.6
	-- (27 Nov, in Play: 0.06 studs at 35% read as nothing; this size and opacity read as fine dust in the light)
	e.Size = NumberSequence.new({ kp(0, 0.11, 0.03), kp(1, 0.13, 0.03) })
	e.Transparency = NumberSequence.new({ kp(0, 1), kp(0.2, o.see or 0.12), kp(0.8, o.see or 0.12), kp(1, 1) })
	e.Lifetime = NumberRange.new(8, 12)
	local vol = size.X * size.Y * size.Z
	e.Rate = o.rate or math.clamp(vol * (o.density or 0.01), 0.6, o.max or 5)
	e.Speed = NumberRange.new(0.03, 0.12)
	e.SpreadAngle = Vector2.new(180, 180)
	e.Acceleration = Vector3.new(0, -0.006, 0)
	e.Drag = 0.4
	e.RotSpeed = NumberRange.new(0, 0)
	e.Shape = Enum.ParticleEmitterShape.Box
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	e.Orientation = Enum.ParticleOrientation.FacingCamera
	e.Parent = p
	p.Parent = parent
	if o.prefill ~= false then e:Emit(math.floor(e.Rate * 10)) end
	return p
end

-- a faint shaft from a to b (a camera-facing soft band: the round glow stretched along it), see = its transparency
function D.shaft(parent: Instance, a: Vector3, b: Vector3, width: number, col: Color3, opts: any?): BasePart
	local o = opts or {}
	local p = Instance.new("Part")
	p.Name = o.name or "LightShaft"
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.new(0.2, 0.2, 0.2); p.CFrame = CFrame.new(a)
	local a0 = Instance.new("Attachment"); a0.Position = Vector3.zero; a0.Parent = p
	local a1 = Instance.new("Attachment"); a1.Position = b - a; a1.Parent = p
	-- (27 Nov, in Play: a beam's transparency is sampled per segment, so one segment drew it fully clear; and the soft
	-- glow stretched along a beam leaves almost no alpha) two plain bands, the inner half as wide: soft-ish sides
	local see = o.see or 0.9
	for i, k in { 1, 0.55 } do
		local bm = Instance.new("Beam")
		bm.Name = if i == 1 then "Shaft" else "ShaftCore"
		bm.Attachment0 = a0; bm.Attachment1 = a1
		bm.FaceCamera = true
		bm.Width0 = width * k; bm.Width1 = width * k * (o.spread or 1.25)
		bm.LightEmission = o.emission or 0.3; bm.LightInfluence = 0; bm.Brightness = o.brightness or 1
		bm.Color = ColorSequence.new(col)
		bm.Transparency = NumberSequence.new({ kp(0, 1), kp(0.22, see), kp(0.62, see), kp(1, 1) })
		bm.Segments = 12
		bm.Parent = p
	end
	p.Parent = parent
	return p
end

-- a room's screen (the intro's PC, the attic's TV): motes in its light in front of it, and for a TV a faint shaft
-- toward the seats. screen: the Part (its front face lights the room), col: its light's colour
function D.screen(parent: Instance, screen: BasePart, col: Color3, opts: any?): ()
	local o = opts or {}
	local f = screen.CFrame -- (LookVector: out of the screen, into the room)
	local w, h = screen.Size.X, screen.Size.Y
	local depth = o.depth or 4.5
	D.motes(parent, f * CFrame.new(0, 0, -(0.6 + depth / 2)), Vector3.new(w + 2.4, h + 2.2, depth), col,
		{ name = "ScreenMotes", density = o.density or 0.06, max = 5, emission = 0.4 })
	if o.shaft then
		D.shaft(parent, f.Position + f.LookVector * 0.4, f.Position + f.LookVector * (o.shaftLen or 7) + Vector3.new(0, -1.2, 0),
			w * 0.9, col, { name = "ScreenShaft", see = o.see or 0.9 })
	end
end

return D
