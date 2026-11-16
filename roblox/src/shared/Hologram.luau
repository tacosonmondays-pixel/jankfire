--!strict
-- Hologram: turns any model (a gun, an item, an avatar) into a hologram on THIS client, and back. One module for the
-- hub's loadout and bundle holograms and training's mirror (owner, 16 Nov 2026: "can you figure out how to do a cool
-- hologram effect?"). Built and judged with the VFX pipeline (roblox/docs/VFX-PIPELINE.md, "Hologram").
--
-- The look: the real shape, see-through in one calm tint with a brighter rim (a Highlight); with `lines` the body is
-- Roblox's ForceField material (its moving pattern is drawn on the graphics card: no Texture objects, no script work);
-- now and then a thin bright disc sweeping up through it, a faint flicker of the rim, and once in a while a thin glitch
-- slice that flares for a few frames. Optional: a projector under it (a soft light cone up to it, motes rising, a
-- glowing lens), a scan that builds it in from the bottom (a bright line, the pieces lighting up as it passes), a slow
-- bob and turn.
--
-- Cheap (16 Nov evening, the owner's lag report in training; the perf session measured the mirror): every part is set
-- ONCE when it is dressed; per frame only the rim (one Highlight) and the one sweep disc change. Parts are written per
-- frame only while it builds in or scans out (1.5 s / 0.45 s), and only when a value changes. One RenderStepped for
-- all holograms; nothing runs past 260 studs.
--
--   local H = Hologram.apply(model, opts)   -- returns a handle; the model keeps its place in the world
--   H:remove(fade?)                          -- scans it out (fade s, 0 = at once) and puts every part back as it was
--   Hologram.of(model)                       -- the handle, if it is one
-- opts (all optional):
--   color     the tint (default a calm ice-blue)      see      body transparency, 0..1 (default 0.55)
--   rim       Highlight fill and outline (true)       lines    the ForceField pattern on the body (true)
--   band      the sweeping disc (true)                flicker  0..0.2 how much the rim wavers (0.05)
--   glitch    the odd glitch slice (true)
--   build     seconds of scan-in (1.5; 0 = at once): from the projector's lens (if any) up through the piece
--   projector CFrame of the lens under it (its up = up): a light cone from there to the model, motes, a glowing lens
--   pivot     CFrame: Hologram turns (spin, rad/s) and bobs (bob, studs) the model round this; else the caller moves it
local RunService = game:GetService("RunService")

local Hologram = {}
local TEX = {
	glow = "rbxassetid://107753175681578",
	beam = "rbxassetid://72229869149513", -- a soft core across its width
}
-- (round 2, the critic: calmer, a pale ice-blue that reads across a room by its outline, not its fill)
local CYAN = Color3.fromRGB(176, 226, 242)
local WHITE = Color3.new(1, 1, 1)
local FAR = 260

type Saved = { p: BasePart, mat: Enum.Material, col: Color3, tr: number, shadow: boolean, tex: string?, ltm: number,
	hidden: { Instance }, y: number, lastTr: number, lastGlow: number }
export type Handle = {
	model: Model, opts: any, parts: { Saved }, hl: Highlight?, t: number, phase: string, outT: number, outLen: number,
	h: number, y0: number, w: number, color: Color3, see: number, bandY: number?, nextBand: number, glitchY: number?, glitchT: number,
	nextGlitch: number, dip: number, nextDip: number, gear: { Instance }, beam: Beam?, line: BasePart?, disc: BasePart?,
	settled: boolean, hlFill: number, hlLine: number, yOff: number, remove: (Handle, number?) -> (),
}
local live: { [Model]: Handle } = {}

local function each(m: Model, f: (BasePart) -> ())
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then f(d) end end
end

-- a thin glowing disc (the build's scan line, the sweep, the glitch slice): one part, moved, never per piece
local function disc(H: Handle, name: string): BasePart
	local d = Instance.new("Part")
	d.Name = name; d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
	d.Shape = Enum.PartType.Cylinder; d.Material = Enum.Material.Neon; d.Color = H.color:Lerp(WHITE, 0.5)
	d.Size = Vector3.new(0.03, H.w, H.w); d.Transparency = 1
	d.Parent = workspace.CurrentCamera
	table.insert(H.gear, d)
	return d
end

-- every part's own look, kept so remove() can put it back; then the hologram's, set once
local function dress(H: Handle)
	local o = H.opts
	local holder = Instance.new("Folder")
	holder.Name = "HologramKept"
	local mat = if o.lines == false then Enum.Material.Neon else Enum.Material.ForceField
	each(H.model, function(p)
		if p.Transparency >= 0.99 then return end -- (hit boxes and hidden helpers stay hidden)
		local s: Saved = { p = p, mat = p.Material, col = p.Color, tr = p.Transparency, shadow = p.CastShadow, tex = nil,
			ltm = p.LocalTransparencyModifier, hidden = {}, y = 0, lastTr = -1, lastGlow = -1 }
		-- a drawn skin would cover the tint: its SurfaceAppearance, decals and the mesh's own picture go aside
		for _, c in p:GetChildren() do
			if c:IsA("SurfaceAppearance") or c:IsA("Decal") or c:IsA("Texture") then table.insert(s.hidden, c); c.Parent = holder end
		end
		if p:IsA("MeshPart") then s.tex = p.TextureID; p.TextureID = "" end
		p.Material = mat
		p.Color = H.color
		p.CastShadow = false
		table.insert(H.parts, s)
	end)
	holder.Parent = H.model
	table.insert(H.gear, holder)
	if o.rim ~= false then
		local hl = Instance.new("Highlight")
		hl.Adornee = H.model; hl.FillColor = H.color; hl.OutlineColor = H.color:Lerp(WHITE, 0.45)
		hl.FillTransparency = 1; hl.OutlineTransparency = 1; hl.DepthMode = Enum.HighlightDepthMode.Occluded
		hl.Parent = H.model
		H.hl = hl
	end
end

local function measure(H: Handle)
	local cf, size = H.model:GetBoundingBox()
	H.h = size.Y
	H.y0 = cf.Position.Y - size.Y / 2
	H.w = math.max(size.X, size.Z, 0.1)
	H.yOff = H.y0 - H.model:GetPivot().Position.Y -- (the foot follows the model when it bobs or is moved)
	for _, s in H.parts do s.y = (s.p.Position.Y - H.y0) / math.max(H.h, 0.01) end
end

-- the projector: a glowing lens, a soft cone of light up to the model, motes drifting up in it, a faint light
local function projector(H: Handle, lens: CFrame)
	local cf, size = H.model:GetBoundingBox()
	local w = math.max(size.X, size.Z)
	local rig = Instance.new("Part")
	rig.Name = "HologramProjector"; rig.Anchored = true; rig.CanCollide = false; rig.CanQuery = false; rig.CanTouch = false
	rig.CastShadow = false; rig.Transparency = 1; rig.Size = Vector3.new(w * 0.5, 0.2, w * 0.5); rig.CFrame = lens
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Parent = rig; a1.Parent = rig
	a1.WorldPosition = cf.Position - Vector3.new(0, size.Y * 0.45, 0) -- (the cone ends under the model: one object)
	local beam = Instance.new("Beam")
	beam.Attachment0 = a0; beam.Attachment1 = a1; beam.Texture = TEX.beam; beam.TextureMode = Enum.TextureMode.Stretch
	beam.Color = ColorSequence.new(H.color); beam.LightEmission = 1; beam.LightInfluence = 0; beam.Brightness = 1.2
	beam.Width0 = w * 0.16; beam.Width1 = w * 0.95; beam.FaceCamera = true; beam.Segments = 1
	beam.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.7, 0.88), NumberSequenceKeypoint.new(1, 1) })
	beam.Parent = rig
	local lensGlow = Instance.new("ParticleEmitter")
	lensGlow.Texture = TEX.glow; lensGlow.Color = ColorSequence.new(H.color); lensGlow.LightEmission = 1; lensGlow.LightInfluence = 0
	lensGlow.Size = NumberSequence.new(w * 0.22); lensGlow.Transparency = NumberSequence.new(0.35); lensGlow.Lifetime = NumberRange.new(0.6)
	lensGlow.Rate = 4; lensGlow.Speed = NumberRange.new(0); lensGlow.LockedToPart = true; lensGlow.Parent = a0
	local motes = Instance.new("ParticleEmitter")
	motes.Texture = TEX.glow; motes.Color = ColorSequence.new(H.color:Lerp(WHITE, 0.4)); motes.LightEmission = 1; motes.LightInfluence = 0
	motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.04), NumberSequenceKeypoint.new(1, 0) })
	motes.Transparency = NumberSequence.new(0.2); motes.Lifetime = NumberRange.new(2.5, 4); motes.Rate = 5
	motes.Speed = NumberRange.new(0.4, 0.9); motes.SpreadAngle = Vector2.new(12, 12); motes.Parent = rig -- (puffs from the lens' box)
	local light = Instance.new("PointLight")
	light.Color = H.color; light.Brightness = 0.2; light.Range = w * 1.6 + 4; light.Shadows = false; light.Parent = a1
	rig.Parent = workspace.CurrentCamera
	table.insert(H.gear, rig)
	H.beam = beam
end

function Hologram.of(model: Model): Handle?
	return live[model]
end

local function restore(H: Handle)
	for _, s in H.parts do
		local p = s.p
		if not p.Parent then continue end
		p.Material = s.mat; p.Color = s.col; p.Transparency = s.tr; p.CastShadow = s.shadow; p.LocalTransparencyModifier = s.ltm
		if s.tex and p:IsA("MeshPart") then p.TextureID = s.tex end
		for _, c in s.hidden do c.Parent = p end
	end
	if H.hl then H.hl:Destroy() end
	for _, g in H.gear do g:Destroy() end
end

local function remove(H: Handle, fade: number?)
	if H.phase == "gone" or H.phase == "out" then return end
	local f = fade or 0.45
	if f <= 0 then H.phase = "gone"; live[H.model] = nil; restore(H); return end
	H.phase, H.outT, H.outLen, H.settled = "out", 0, f, false
end

function Hologram.apply(model: Model, opts: any?): Handle
	local old = live[model]
	if old then old:remove(0) end
	local o = opts or {}
	local H: Handle = {
		model = model, opts = o, parts = {}, hl = nil, t = 0, phase = "in", outT = 0, outLen = 0, h = 1, y0 = 0, w = 1,
		color = o.color or CYAN, see = o.see or 0.55, bandY = nil, nextBand = 1.6 + math.random() * 1.5, glitchY = nil,
		glitchT = 0, nextGlitch = 3 + math.random() * 4, dip = 0, nextDip = 2 + math.random() * 3, gear = {}, beam = nil,
		line = nil, disc = nil, settled = false, hlFill = -1, hlLine = -1, yOff = 0, remove = remove,
	}
	if o.pivot then each(model, function(p) p.Anchored = true end) end -- (it moves the model: nothing may fall)
	dress(H)
	measure(H)
	if o.projector then projector(H, o.projector) end
	if (o.build or 1.5) > 0 then H.line = disc(H, "HologramScan") else H.phase = "show" end
	if o.band ~= false or o.glitch ~= false then H.disc = disc(H, "HologramSweep") end
	live[model] = H
	return H
end

-- the pieces while it builds in / scans out: shown as the line passes, flashing white right at it (written only on
-- change); `scan` nil = settle every piece at its steady look, once
local function paintParts(H: Handle, scan: number?)
	for _, s in H.parts do
		local f, glow = 1, 0
		if scan then
			local d = scan - s.y
			f = math.clamp(d / 0.08 + 0.5, 0, 1)
			glow = math.clamp(1 - math.abs(d) / 0.07, 0, 1)
		end
		local tr = 1 - (1 - math.max(H.see - 0.35 * glow, 0)) * f
		tr = math.floor(tr * 50 + 0.5) / 50
		glow = math.floor(glow * 20 + 0.5) / 20
		if tr ~= s.lastTr then s.lastTr = tr; s.p.Transparency = tr end
		if glow ~= s.lastGlow then s.lastGlow = glow; s.p.Color = H.color:Lerp(WHITE, 0.55 * glow) end
	end
end

-- the rim: the one per-frame write on a standing hologram (and only when it moves by a visible step)
local function paintRim(H: Handle, k: number)
	if not H.hl then return end
	local flick = 1 - (H.opts.flicker or 0.05) * (0.5 + 0.5 * math.sin(H.t * 23) * math.sin(H.t * 7.3)) - H.dip
	local fill = math.floor((1 - 0.25 * k * flick) * 100 + 0.5) / 100
	local line = math.floor((1 - 0.7 * k * flick) * 100 + 0.5) / 100
	if fill ~= H.hlFill then H.hlFill = fill; H.hl.FillTransparency = fill end
	if line ~= H.hlLine then H.hlLine = line; H.hl.OutlineTransparency = line end
end

-- the sweep and the glitch slice share one disc: the band rises through the piece every few seconds; a glitch flashes
-- it bright at one height for a few frames
local function paintDisc(H: Handle, pos: Vector3)
	local d = H.disc
	if not d then return end
	local y, a = nil, 0
	if H.glitchY then y, a = H.glitchY, 0.7
	elseif H.bandY then y, a = H.bandY, 0.6 * math.clamp(math.min(H.bandY + 0.1, 1.1 - H.bandY) / 0.2, 0, 1) end
	if y then
		d.CFrame = CFrame.new(pos.X, H.y0 + H.h * y, pos.Z) * CFrame.Angles(0, 0, math.pi / 2)
		d.Transparency = 1 - 0.75 * a
	elseif d.Transparency < 1 then
		d.Transparency = 1
	end
end

local STUDIO = RunService:IsStudio()
RunService.RenderStepped:Connect(function(rdt: number)
	-- (Studio: the VFX pipeline's frame captures slow or freeze it with the workspace attribute FxTimeScale, like Fx)
	local ts = if STUDIO then workspace:GetAttribute("FxTimeScale") else nil
	local dt = rdt * (if type(ts) == "number" then ts else 1)
	if dt <= 0 then return end
	local cam = workspace.CurrentCamera
	local eye = cam and cam.CFrame.Position or Vector3.zero
	for model, H in live do
		if not model.Parent then live[model] = nil; for _, g in H.gear do g:Destroy() end; continue end
		H.t += dt
		local o = H.opts
		if o.pivot then
			local bob = (o.bob or 0) * math.sin(H.t * 1.4)
			model:PivotTo(o.pivot * CFrame.new(0, bob, 0) * CFrame.Angles(0, H.t * (o.spin or 0), 0))
		end
		local pos = model:GetPivot().Position
		H.y0 = pos.Y + H.yOff
		if (pos - eye).Magnitude > FAR then continue end
		-- the sweep every few seconds, the odd dip in the rim, the odd glitch slice
		if o.band ~= false and H.phase == "show" and H.t >= H.nextBand then
			H.bandY = (H.bandY or -0.1) + dt / 1.1
			if H.bandY > 1.1 then H.bandY = nil; H.nextBand = H.t + 2.5 + math.random() * 2 end
		end
		if H.t >= H.nextDip then H.dip = 0.25; if H.t >= H.nextDip + 0.06 then H.dip = 0; H.nextDip = H.t + 2.5 + math.random() * 4 end end
		if o.glitch ~= false and H.phase == "show" then
			if H.t >= H.nextGlitch and not H.glitchY then H.glitchY = 0.15 + math.random() * 0.7; H.glitchT = 0 end
			if H.glitchY then
				H.glitchT += dt
				if H.glitchT > 0.08 then H.glitchY = nil; H.nextGlitch = H.t + 4 + math.random() * 5 end
			end
		end
		if H.phase == "in" then
			-- the owner's sweep (16 Nov, as the hub's own holograms do it): the line starts AT THE LENS, as narrow as the
			-- light cone is there, widens with the cone up to the piece's foot, then runs up through the whole piece,
			-- showing it from foot to top, and fades just over the top. quick off the lens, slower through the piece; full
			-- from 5 % of the time, fading over the last 18 %
			local build = o.build or 1.5
			local u = math.clamp(H.t / build, 0, 1)
			local top = H.y0 + H.h + 0.25
			local lens = if o.projector then (o.projector :: CFrame).Position.Y else H.y0
			local split = if lens < H.y0 - 0.2 then 0.3 else 0 -- (the share of the time spent from the lens to the foot)
			local y: number
			if u < split then
				local a = u / split
				y = lens + (H.y0 - lens) * (1 - (1 - a) * (1 - a))
			else
				local a = if split < 1 then (u - split) / (1 - split) else 1
				y = H.y0 + (top - H.y0) * a
			end
			paintParts(H, (y - H.y0) / math.max(H.h, 0.01))
			paintRim(H, 1)
			if H.line then
				local foot = H.w
				local wNow = if y < H.y0 and lens < H.y0 then foot * (0.17 + 0.83 * (y - lens) / (H.y0 - lens)) else foot
				H.line.Size = Vector3.new(0.03, wNow, wNow)
				H.line.CFrame = CFrame.new(pos.X, y, pos.Z) * CFrame.Angles(0, 0, math.pi / 2)
				local alpha = math.clamp(u / 0.05, 0, 1) * (1 - math.clamp((u - 0.82) / 0.18, 0, 1))
				H.line.Transparency = 1 - 0.45 * alpha
			end
			if u >= 1 then
				H.phase = "show"
				if H.line then H.line.Transparency = 1 end
				paintParts(H, nil); H.settled = true
			end
		elseif H.phase == "show" then
			if not H.settled then paintParts(H, nil); H.settled = true end
			paintRim(H, 1)
			paintDisc(H, pos)
		elseif H.phase == "out" then
			H.outT += dt
			local u = math.clamp(H.outT / H.outLen, 0, 1)
			paintParts(H, 1.1 - u * 1.15) -- (it goes from the top down)
			paintRim(H, 1 - u)
			if H.disc then H.disc.Transparency = 1 end
			if u >= 1 then H.phase = "gone"; live[model] = nil; restore(H) end
		end
	end
end)

return Hologram
