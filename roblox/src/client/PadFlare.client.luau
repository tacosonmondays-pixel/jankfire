--!strict
-- JUMP PADS LIGHT UP (17 Nov 2026, the owner: "pads should glow when you step on them!"). Any part with a Pad attribute
-- (Move throws you off it: the hub's, training's and the Rooftop's JumpPadTop and the like) flares in its own colour when
-- someone is thrown off it: its glowing pieces flash pale, a light pulses, a soft glow bursts on the face and a ring of
-- light spreads off it, a few motes shoot up; all gone in about 0.6 s. While someone stands on one it stays brighter.
-- Everyone sees it: the launch comes from PadSignal (Steps.client fires it for every character it sees leave a pad),
-- the standing from a look at each character's floor ten times a second.
-- Cheap: nothing at all for an idle pad. A pad's light, emitters and glowing pieces are found the first time it fires and
-- kept; the flash and fades are tweens.
-- Test hook (Studio): the player attribute PadFlareTest = "launch" (the nearest pad flares), "stand" (it holds the
-- standing glow for 3 s) or "both".
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local me = Players.LocalPlayer
local STUDIO = RunService:IsStudio()
local RING = "rbxassetid://136567724057402" -- (vfx_ring: a shock ring)
local GLOW = "rbxassetid://107753175681578" -- (vfx_glow: a soft round glow; its bright middle under half its width)
local CYAN = Color3.fromRGB(55, 214, 255)
local WHITE = Color3.new(1, 1, 1)
local LIFE = 0.6

type Lit = { p: BasePart, c: Color3, m: Enum.Material }
type Pad = { top: BasePart, att: Attachment, light: PointLight, ring: ParticleEmitter, flare: ParticleEmitter,
	motes: ParticleEmitter, face: ParticleEmitter, hold: ParticleEmitter, lit: { Lit }, col: Color3, standT: number,
	holding: boolean, t: number }
local pads: { [BasePart]: Pad } = {}

local function ns(...: number): NumberSequence
	local a = { ... }
	local k = {}
	for i = 1, #a, 2 do table.insert(k, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(k)
end

-- the pad's visible kit: the JumpPad model laid over the (see-through) top by the hub and training builders. Its meshes
-- don't answer spatial queries (CanQuery off), so the kits are listed by name, once, and kept up to date
local kits: { Model } = {}
for _, d in workspace:GetDescendants() do if d:IsA("Model") and d.Name == "JumpPad" then table.insert(kits, d) end end
workspace.DescendantAdded:Connect(function(d) if d:IsA("Model") and d.Name == "JumpPad" then table.insert(kits, d) end end)

-- the pad's own coloured pieces (its accents: Neon or strongly coloured), which glow in the flare; no kit: the top itself
-- if it can be seen
local function glowing(top: BasePart): ({ Lit }, Color3)
	local kit: Model? = nil
	local bd = math.max(top.Size.X, top.Size.Z) * 0.8 + 2
	for i = #kits, 1, -1 do
		local m = kits[i]
		if not m.Parent then table.remove(kits, i); continue end
		local d = m:GetPivot().Position - top.Position
		if math.abs(d.Y) < 3 and Vector2.new(d.X, d.Z).Magnitude < bd then kit = m; bd = Vector2.new(d.X, d.Z).Magnitude end
	end
	local list, best, bestS = {}, CYAN, -1
	local function consider(p: BasePart)
		-- (never the hub's queue pads: PadGlow.client drives their "Glow" parts, which carry Team, every frame)
		if p:GetAttribute("Team") ~= nil or p:FindFirstAncestor("QueuePads") ~= nil then return end
		if p.Transparency > 0.6 then return end
		local _, s, v = p.Color:ToHSV()
		if p.Material == Enum.Material.Neon or s * v > 0.35 then
			table.insert(list, { p = p, c = p.Color, m = p.Material })
			if s * v > bestS then bestS = s * v; best = p.Color end
		end
	end
	if kit then for _, d in kit:GetDescendants() do if d:IsA("BasePart") then consider(d) end end end
	if #list == 0 then consider(top) end
	if bestS < 0.25 then best = CYAN end
	return list, best
end

local function rig(top: BasePart): Pad
	local pd = pads[top]
	if pd then return pd end
	local lit, col = glowing(top)
	local att = Instance.new("Attachment")
	att.Name = "PadFlare"; att.Position = Vector3.new(0, top.Size.Y / 2 + 0.06, 0); att.Parent = top
	local light = Instance.new("PointLight")
	light.Color = col; light.Brightness = 0; light.Range = 14; light.Shadows = false; light.Enabled = false; light.Parent = att
	-- (the ring lies on the face: VelocityPerpendicular with a tiny upward speed faces the sprite up)
	local ring = Instance.new("ParticleEmitter")
	ring.Name = "Ring"; ring.Texture = RING; ring.Color = ColorSequence.new(col:Lerp(WHITE, 0.25)); ring.LightEmission = 1
	ring.LightInfluence = 0; ring.Brightness = 2; ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
	ring.EmissionDirection = Enum.NormalId.Top; ring.Speed = NumberRange.new(0.02); ring.SpreadAngle = Vector2.zero
	local w = math.max(top.Size.X, top.Size.Z)
	ring.Size = ns(0, w * 0.3, 1, w * 1.25); ring.Transparency = ns(0, 0.1, 0.6, 0.55, 1, 1)
	ring.Lifetime = NumberRange.new(LIFE * 0.9); ring.Rate = 0; ring.LockedToPart = true; ring.Parent = att
	local flare = Instance.new("ParticleEmitter")
	flare.Name = "Flare"; flare.Texture = GLOW; flare.Color = ColorSequence.new(col:Lerp(WHITE, 0.45)); flare.LightEmission = 1
	flare.LightInfluence = 0; flare.Brightness = 2.5; flare.Speed = NumberRange.new(0); flare.Size = ns(0, w * 0.55, 1, w * 0.2)
	flare.Transparency = ns(0, 0.15, 1, 1); flare.Lifetime = NumberRange.new(0.28); flare.Rate = 0; flare.LockedToPart = true
	flare.Parent = att
	local motes = Instance.new("ParticleEmitter")
	motes.Name = "Motes"; motes.Texture = GLOW; motes.Color = ColorSequence.new(col:Lerp(WHITE, 0.3)); motes.LightEmission = 1
	motes.LightInfluence = 0; motes.Brightness = 2; motes.EmissionDirection = Enum.NormalId.Top; motes.SpreadAngle = Vector2.new(25, 25)
	motes.Speed = NumberRange.new(10, 18); motes.Drag = 3; motes.Size = ns(0, 0.22, 1, 0); motes.Transparency = ns(0, 0.1, 1, 1)
	motes.Lifetime = NumberRange.new(0.35, 0.55); motes.Rate = 0; motes.Shape = Enum.ParticleEmitterShape.Disc
	motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume; motes.Parent = att
	-- (a glow lying on the face itself: the flare's, and a steady fainter one while someone stands there)
	local function flat(name: string, a0: number, life: number): ParticleEmitter
		local e = Instance.new("ParticleEmitter")
		e.Name = name; e.Texture = GLOW; e.Color = ColorSequence.new(col:Lerp(WHITE, 0.2)); e.LightEmission = 1; e.LightInfluence = 0
		e.Brightness = 2; e.Orientation = Enum.ParticleOrientation.VelocityPerpendicular; e.EmissionDirection = Enum.NormalId.Top
		e.Speed = NumberRange.new(0.02); e.SpreadAngle = Vector2.zero; e.Size = ns(0, w * 0.62, 1, w * 0.7)
		e.Transparency = ns(0, a0, 0.5, a0 + (1 - a0) * 0.35, 1, 1); e.Lifetime = NumberRange.new(life); e.Rate = 0
		e.LockedToPart = true; e.Parent = att
		return e
	end
	local face = flat("Face", 0.05, LIFE)
	local hold = flat("Hold", 0.55, 0.5)
	pd = { top = top, att = att, light = light, ring = ring, flare = flare, motes = motes, face = face, hold = hold, lit = lit,
		col = col, standT = 0, holding = false, t = 0 }
	pads[top] = pd
	return pd
end

local FADE = TweenInfo.new(LIFE, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local HOLD_LIGHT = 1.4
local function settle(pd: Pad)
	-- (where it rests: brighter while someone stands on it, else dark)
	local hold = pd.holding
	TweenService:Create(pd.light, FADE, { Brightness = if hold then HOLD_LIGHT else 0 }):Play()
	pd.hold.Rate = if hold then 6 else 0
	for _, g in pd.lit do
		if g.p.Parent then TweenService:Create(g.p, FADE, { Color = if hold then pd.col:Lerp(WHITE, 0.45) else g.c }):Play() end
	end
	-- (the accents glow, Neon, while it flares or someone stands there; their own material back once it's dark)
	local t0 = pd.t
	task.delay(if hold then 0 else LIFE * 0.75, function()
		if pd.t ~= t0 then return end
		for _, g in pd.lit do if g.p.Parent then g.p.Material = if pd.holding then Enum.Material.Neon else g.m end end
	end)
	if not hold then
		task.delay(LIFE + 0.05, function()
			if not pd.holding and os.clock() - pd.t >= LIFE then pd.light.Enabled = false end
		end)
	end
end

local function launch(top: BasePart)
	if not top.Parent then return end
	local pd = rig(top)
	local now = os.clock()
	if now - pd.t < 0.25 then return end -- (one flare per throw, whoever saw it first)
	pd.t = now
	pd.light.Enabled = true; pd.light.Brightness = 5
	-- (every glowing piece in the pad's own colour, a white face too: the hub's pads have a white disc)
	for _, g in pd.lit do if g.p.Parent then g.p.Material = Enum.Material.Neon; g.p.Color = pd.col:Lerp(WHITE, 0.3) end end
	pd.face:Emit(1)
	pd.flare:Emit(1)
	pd.ring:Emit(1)
	task.delay(0.09, function() pd.ring:Emit(1) end)
	pd.motes:Emit(12)
	settle(pd)
end

local function stand(top: BasePart, on: boolean)
	local pd = rig(top)
	if pd.holding == on then return end
	pd.holding = on
	if on then pd.light.Enabled = true end
	settle(pd)
end

-- the launches (every character, from Steps.client through PadSignal)
task.spawn(function()
	local m = script.Parent:WaitForChild("PadSignal", 20)
	if not (m and m:IsA("ModuleScript")) then return end
	local ok, S = pcall(require, m)
	if ok and type(S) == "table" and S.launched then
		(S :: any).launched:Connect(function(pad: any) if typeof(pad) == "Instance" and pad:IsA("BasePart") then launch(pad) end end)
	end
end)

-- who stands on a pad: each character's floor, ten times a second (only characters on the ground: one ray each)
local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Exclude
local testUntil: { [BasePart]: number } = {}
task.spawn(function()
	while true do
		task.wait(0.1)
		local on: { [BasePart]: boolean } = {}
		for _, p in Players:GetPlayers() do
			local ch = p.Character
			local hum = ch and ch:FindFirstChildOfClass("Humanoid")
			local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			if hum and root and hum.FloorMaterial ~= Enum.Material.Air and hum.Health > 0 then
				ray.FilterDescendantsInstances = { ch }
				local hit = workspace:Raycast(root.Position, Vector3.new(0, -(hum.HipHeight + root.Size.Y / 2 + 1.5), 0), ray)
				if hit and typeof(hit.Instance:GetAttribute("Pad")) == "Vector3" then on[hit.Instance :: BasePart] = true end
			end
		end
		local now = os.clock()
		for top, u in testUntil do if now < u then on[top] = true else testUntil[top] = nil end end
		for top, pd in pads do
			if not top.Parent then pads[top] = nil; continue end
			if pd.holding and not on[top] then stand(top, false) end
		end
		for top in on do stand(top, true) end
	end
end)

if STUDIO then
	me:GetAttributeChangedSignal("PadFlareTest"):Connect(function()
		local v = me:GetAttribute("PadFlareTest")
		if type(v) ~= "string" then return end
		me:SetAttribute("PadFlareTest", nil)
		local root = me.Character and me.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not root then return end
		local best: BasePart?, bd = nil, 60
		for _, d in workspace:GetDescendants() do
			if d:IsA("BasePart") and typeof(d:GetAttribute("Pad")) == "Vector3" then
				local dd = (d.Position - root.Position).Magnitude
				if dd < bd then best, bd = d, dd end
			end
		end
		if not best then me:SetAttribute("PadFlareTestResult", "no pad within 60"); return end
		local top = best :: BasePart
		if v == "stand" or v == "both" then testUntil[top] = os.clock() + 3; stand(top, true) end
		if v == "launch" or v == "both" then launch(top) end
		local pd = pads[top]
		me:SetAttribute("PadFlareTestResult", string.format("%s at %.0f studs, %d glowing pieces, colour %s", top:GetFullName(), bd,
			if pd then #pd.lit else 0, if pd then pd.col:ToHex() else "-"))
	end)
end
