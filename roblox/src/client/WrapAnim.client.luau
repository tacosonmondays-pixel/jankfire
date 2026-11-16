--!strict
-- WrapAnim: the animated wraps come alive on every gun this player can see (their own in hand, everyone else's, the
-- hub racks, the loadout previews). docs/WRAP-TEXTURES.md, "Animated wraps".
--
-- The web game animates 18 wraps in its shader (public/js/wrappack.js): scrolling patterns, pulses running along traces,
-- a glint sweeping over gold, hue that shifts with the angle, flicker. A Roblox SurfaceAppearance cannot scroll its
-- texture, and its maps can only be set in Edit, so stepping through pre-drawn frames would mean swapping whole
-- SurfaceAppearances at runtime: a texture reload each time, a hitch and a blink. What CAN change at runtime, cheaply,
-- is the glow (EmissiveStrength, EmissiveTint) and the tint (Color). So each animated wrap gets a slow, smooth change
-- of those, off one shared clock so every gun wearing it moves in step: a breathing glow, a pulse, a glint that swells
-- and fades, a drift between two colours, an iridescent tint. Nothing flickers (the owner: smooth and subtle).
--
-- WeaponModels.wrap tags each worn picture "WrapSA" and gives it the attribute Wrap = <wrap id>, on the server (world
-- guns) and the client (the held gun, previews) alike; this script finds them by the tag.
-- Cost: one Heartbeat step at 20 Hz. A wrap's value is worked out once a step and written to each of its pieces;
-- pieces further than NEAR studs from the camera are skipped (checked twice a second). The attribute StepUs on this
-- script is the slowest step of the last second, in microseconds.
local CS = game:GetService("CollectionService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local TAU = math.pi * 2
local HZ = 20
local NEAR = 160

-- k: the kind of change, p: its period in seconds, lo/hi: the glow's range as a share of the wrap's own
-- EmissiveStrength, a/b: two glow colours to drift between, p2: the glow's own period when it differs, sat: saturation
type Spec = { k: string, p: number, lo: number?, hi: number?, a: Color3?, b: Color3?, p2: number?, sat: number? }
local SPEC: { [string]: Spec } = {
	hex = { k = "breathe", p = 2.6, lo = 0.7, hi = 1.25 },        -- web: light running along the grooves
	circuit = { k = "breathe", p = 2.0, lo = 0.6, hi = 1.3 },     -- web: pulses running along the traces
	kintsugi = { k = "glint", p = 4.5, lo = 0.5, hi = 1.6 },      -- web: a glint sweeping along the gold
	crt = { k = "breathe", p = 2.2, lo = 0.85, hi = 1.2 },        -- web: a bright bar rolling up the screen
	tokyo = { k = "breathe", p = 1.6, lo = 0.82, hi = 1.1 },      -- web: neon flicker (a hum here, never a flicker)
	stonks = { k = "breathe", p = 2.0, lo = 0.8, hi = 1.15 },     -- web: the chart scrolling
	vapor = { k = "breathe", p = 5.0, lo = 0.85, hi = 1.15 },     -- web: the grid scrolling
	corp = { k = "breathe", p = 2.1, lo = 0.7, hi = 1.1 },        -- web: the smileys pulsing
	blackhole = { k = "breathe", p = 4.0, lo = 0.8, hi = 1.2 },   -- the streaks; its one hole turns and breathes below
	lavalamp = { k = "breathe", p = 6.0, lo = 0.75, hi = 1.2 },   -- web: the blobs rising and merging
	glitch = { k = "drift", p = 5.0, lo = 0.85, hi = 1.1, a = Color3.fromHex("ff8ae8"), b = Color3.fromHex("8ae8ff") },
	aurora = { k = "drift", p = 9.0, p2 = 5.0, lo = 0.75, hi = 1.15, a = Color3.fromHex("b8ffd8"), b = Color3.fromHex("e2c4ff") },
	nebula = { k = "drift", p = 10.0, p2 = 7.0, lo = 0.85, hi = 1.1, a = Color3.fromHex("ffd2f0"), b = Color3.fromHex("cadaff") },
	opal = { k = "hue", p = 12.0, sat = 0.5 },                     -- web: the fire shifting as it turns
	holo = { k = "iris", p = 8.0, sat = 0.12 },                    -- web: the hue sweeping with the angle
	-- (after the Rivals study: there every top-tier wrap moves, so the two still Legendary pictures move too)
	missing = { k = "breathe", p = 1.8, lo = 0.8, hi = 1.15 },     -- the missing-texture glow hums
	rainbow = { k = "iris", p = 10.0, sat = 0.08 },                -- a slow shimmer across the stripes
}
script:SetAttribute("Animated", (function() local n = 0; for _ in SPEC do n += 1 end; return n end)())

type Entry = { spec: Spec, es: number, tint: Color3, col: Color3, near: boolean }
local live: { [SurfaceAppearance]: Entry } = {}

local function add(inst: Instance)
	if not inst:IsA("SurfaceAppearance") or inst:IsDescendantOf(ReplicatedStorage) then return end
	local id = inst:GetAttribute("Wrap")
	local spec = if type(id) == "string" then SPEC[id] else nil
	if not spec then return end
	live[inst] = { spec = spec, es = inst.EmissiveStrength, tint = inst.EmissiveTint, col = inst.Color, near = true }
end
for _, sa in CS:GetTagged("WrapSA") do add(sa) end
CS:GetInstanceAddedSignal("WrapSA"):Connect(add)
CS:GetInstanceRemovedSignal("WrapSA"):Connect(function(inst) live[inst :: any] = nil end)

local function wave(t: number, p: number): number return 0.5 + 0.5 * math.sin(TAU * t / p) end
local function smooth(x: number): number return x * x * (3 - 2 * x) end

-- one wrap's look at time t: a glow factor, and (when the kind sets them) a glow colour and a tint
type Look = { f: number?, tint: Color3?, col: Color3? }
local function look(s: Spec, t: number): Look
	local lo, hi = s.lo or 1, s.hi or 1
	if s.k == "breathe" then return { f = lo + (hi - lo) * wave(t, s.p) } end
	if s.k == "glint" then return { f = lo + (hi - lo) * wave(t, s.p) ^ 6 } end
	if s.k == "drift" then
		return { f = lo + (hi - lo) * wave(t, s.p2 or s.p), tint = (s.a :: Color3):Lerp(s.b :: Color3, smooth(wave(t, s.p))) }
	end
	if s.k == "hue" then return { tint = Color3.fromHSV((t / s.p) % 1, s.sat or 0.5, 1) } end
	if s.k == "iris" then
		local h = (t / s.p) % 1
		return { col = Color3.fromHSV(h, s.sat or 0.12, 1), tint = Color3.fromHSV((h + 0.5) % 1, 0.4, 1) }
	end
	return {}
end

-- Black Hole's one hole (WeaponModels.hole, docs/WRAP-TEXTURES.md "One black hole"): every frame the lit spiral turns
-- backwards, so its arms (wound with the radius falling as the angle rises) move inward and the space reads as falling
-- in; the unlit ring's Brightness breathes (it blooms all through); and a faint ripple shrinks from the rim down into the
-- ring every PULSE seconds, fading in and out. Off the shared clock, so every copy turns in step
local HOLE_TURN = 10 -- degrees a second
local PULSE = 2.8
local MOTE_T = 4.0 -- seconds for a mote to fall from the rim to the ring
local holes: { [SurfaceGui]: boolean } = {}
local function addHole(inst: Instance)
	if inst:IsA("SurfaceGui") and not inst:IsDescendantOf(ReplicatedStorage) then holes[inst] = true end
end
for _, g in CS:GetTagged("WrapHole") do addHole(g) end
CS:GetInstanceAddedSignal("WrapHole"):Connect(addHole)
CS:GetInstanceRemovedSignal("WrapHole"):Connect(function(inst) holes[inst :: any] = nil end)
RunService.RenderStepped:Connect(function()
	if next(holes) == nil then return end
	local t = workspace:GetServerTimeNow()
	for g in holes do
		local p = g.Parent
		if not p then holes[g] = nil; continue end
		-- a SurfaceGui ignores its part's LocalTransparencyModifier, the way the game hides your own world gun in first
		-- person and the viewmodel in third person or scoped: follow it, or a lone hole floats where the gun is hidden
		local show = p:IsA("BasePart") and p.LocalTransparencyModifier < 0.5 and p.Transparency < 0.99
		if g.Enabled ~= show then g.Enabled = show end
		if not show then continue end
		if g.Name == "WrapHole" then
			local pic = g:FindFirstChild("Pic")
			if pic and pic:IsA("ImageLabel") then pic.Rotation = -(t * HOLE_TURN) % 360 end
		else
			g.Brightness = 4 + 0.6 * math.sin(TAU * t / 3.2) -- (the radiant tier: the ring blooms all round at the breath's top)
			local pu = g:FindFirstChild("Pulse")
			local d = g:GetAttribute("D")
			if pu and pu:IsA("Frame") and type(d) == "number" then
				local ph = (t / PULSE) % 1
				local k = 0.95 - 0.74 * ph ^ 1.6 -- (the ring is 0.21 of the picture across; the fall speeds up)
				pu.Size = UDim2.fromOffset(d * k, d * k)
				local st = pu:FindFirstChildOfClass("UIStroke")
				if st then st.Transparency = 1 - 0.55 * math.sin(math.pi * ph) end
			end
			-- the motes: each winds down the spiral (the arms' own winding: the angle grows 2.6 x ln of the radius fallen)
			-- from the rim to the ring in MOTE_T seconds, faster as it nears, fading in and out
			local x = g:GetAttribute("X")
			if type(d) == "number" and type(x) == "number" then
				local rOut, rRing = d * 0.46, d * 0.105
				for _, mo in g:GetChildren() do
					local i = mo:GetAttribute("I")
					if not (mo:IsA("ImageLabel") and type(i) == "number") then continue end
					local ph = (t / MOTE_T + i * 0.1 + (i * 0.37) % 0.07) % 1
					local r = rRing + (rOut - rRing) * (1 - ph) ^ 1.6
					local a = i * 2.4 + 2.6 * math.log(rOut / r)
					mo.Position = UDim2.new(x, r * math.cos(a), 0.5, r * math.sin(a))
					local s = d * 0.045 * (1 - 0.45 * ph)
					mo.Size = UDim2.fromOffset(s, s)
					mo.ImageTransparency = 1 - 0.7 * math.sin(math.pi * ph) ^ 0.7
				end
			end
		end
	end
end)

-- WRAP EFFECTS (the owner, 16 Nov evening: "I want cool effects"): a few slow particles off a wrap's pieces, the kinds
-- and textures of Fx's skin effects (the ids copied from client/Fx.luau's TEX, the VFX session's file). The four biggest
-- picture pieces of the painted half emit from their surfaces (a ParticleEmitter on the part, ShapeStyle Surface), the
-- gun's rate shared out by their size, sizes scaled by the gun's. First person: they ride with the view (LockedToPart),
-- go quiet while aiming (the view narrows, as Fx tells it) and stop while the gun is hidden; guns further than NEAR
-- don't emit. Galaxy's are round dots (the owner's call for Galaxy: dots, no star shapes)
local TEXF = {
	glow = "rbxassetid://107753175681578",
	sparkle = "rbxassetid://118739981349944",
	bubble = "rbxassetid://127426547666953",
}
type FxSpec = { kind: string, col: Color3, col2: Color3?, rate: number, size: number, life: number, rise: number }
local FX: { [string]: FxSpec } = {
	-- (size in metres and rise in metres a second squared, as Fx's skin specs; x the gun's studs per metre)
	lava = { kind = "ember", col = Color3.fromHex("ffb04a"), col2 = Color3.fromHex("ff3a10"), rate = 7, size = 0.014, life = 1.2, rise = 0.6 },
	kintsugi = { kind = "sparkle", col = Color3.fromHex("ffd98a"), rate = 2.5, size = 0.02, life = 0.7, rise = 0.1 },
	nebula = { kind = "sparkle", col = Color3.fromHex("f4d2ff"), rate = 3, size = 0.018, life = 0.8, rise = 0.1 },
	galaxy = { kind = "dot", col = Color3.fromHex("dfe6ff"), rate = 4, size = 0.01, life = 1.0, rise = 0 },
	hex = { kind = "dot", col = Color3.fromHex("6fe2ff"), rate = 3, size = 0.009, life = 1.4, rise = 0.25 },
	circuit = { kind = "dot", col = Color3.fromHex("8dff7a"), rate = 2.5, size = 0.008, life = 0.6, rise = 0.1 },
	tokyo = { kind = "dot", col = Color3.fromHex("ff6ad8"), col2 = Color3.fromHex("5ad8ff"), rate = 3, size = 0.009, life = 1.0, rise = 0.2 },
	ducky = { kind = "bubble", col = Color3.fromHex("f1e9ea"), rate = 1.1, size = 0.026, life = 1.8, rise = 0.25 },
	holo = { kind = "sparkle", col = Color3.fromHex("ffffff"), rate = 2, size = 0.015, life = 0.6, rise = 0 },
}
local function nseq(...: number): NumberSequence
	local a, k = { ... }, {}
	for i = 1, #a, 2 do table.insert(k, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(k)
end
local function fxProps(e: FxSpec, s: number): { [string]: any }
	local col = ColorSequence.new(e.col, e.col2 or e.col)
	local life = NumberRange.new(e.life * 0.8, e.life * 1.2)
	local up = Vector3.new(0, e.rise * s, 0)
	if e.kind == "ember" then
		return { Texture = TEXF.glow, Color = col, LightInfluence = 0, LightEmission = 1, Brightness = 3, Size = nseq(0, e.size * s, 1, 0),
			Transparency = nseq(0, 0.1, 0.7, 0.3, 1, 1), Lifetime = life, Speed = NumberRange.new(0.05 * s, 0.25 * s),
			SpreadAngle = Vector2.new(30, 30), Acceleration = up, Drag = 1.5 }
	elseif e.kind == "sparkle" then -- (twinkles: grows in, shrinks away)
		return { Texture = TEXF.sparkle, Color = col, LightInfluence = 0, LightEmission = 1, Brightness = 2,
			Size = nseq(0, 0, 0.35, e.size * s, 1, 0), Transparency = NumberSequence.new(0.1), Lifetime = life,
			Speed = NumberRange.new(0.02 * s, 0.08 * s), SpreadAngle = Vector2.new(180, 180), Acceleration = up, Drag = 2,
			Rotation = NumberRange.new(-15, 15), RotSpeed = NumberRange.new(-40, 40) }
	elseif e.kind == "bubble" then -- (a soap bubble: rises with a drift, swells a touch, pops)
		local w = e.size * s
		return { Texture = TEXF.bubble, Color = col, LightInfluence = 0.3, LightEmission = 0.35, Brightness = 1.2,
			Size = nseq(0, w * 0.5, 0.15, w, 0.85, w * 1.05, 0.93, w * 1.2, 1, w * 0.2),
			Transparency = nseq(0, 0.6, 0.12, 0, 0.88, 0.05, 0.93, 0.3, 1, 1), Lifetime = life,
			Speed = NumberRange.new(0.1 * s, 0.3 * s), SpreadAngle = Vector2.new(35, 35), Acceleration = up + Vector3.new(0.15 * s, 0, 0), Drag = 1.2 }
	end
	-- dot: a round glowing mote that swells in and fades
	return { Texture = TEXF.glow, Color = col, LightInfluence = 0, LightEmission = 1, Brightness = 2, Size = nseq(0, 0, 0.3, e.size * s, 1, 0),
		Transparency = NumberSequence.new(0.15), Lifetime = life, Speed = NumberRange.new(0.02 * s, 0.1 * s),
		SpreadAngle = Vector2.new(180, 180), Acceleration = up, Drag = 2 }
end
-- the gun a picture piece belongs to: up through Models, stopping below a character (a Model with a Humanoid)
local function gunOf(p: Instance): Instance?
	local m = p.Parent
	if not (m and m:IsA("Model")) then return m end
	while m.Parent and m.Parent:IsA("Model") and not m.Parent:FindFirstChildOfClass("Humanoid") do m = m.Parent end
	return m
end
type GunFx = { ems: { ParticleEmitter }, parts: { BasePart }, fp: boolean, on: boolean }
local gunFx: { [Instance]: GunFx } = {}
local saGun: { [Instance]: Instance } = {}
local dirty: { [Instance]: boolean } = {}
local function rebuild(gun: Instance)
	dirty[gun] = nil
	local old = gunFx[gun]
	if old then for _, e in old.ems do e:Destroy() end; gunFx[gun] = nil end
	if not gun.Parent then return end
	local spec: FxSpec?, pieces = nil, {}
	for _, sa in gun:GetDescendants() do
		if not (sa:IsA("SurfaceAppearance") and sa.Name == "WrapSA" and sa.Parent and sa.Parent:IsA("BasePart")) then continue end
		local id = sa:GetAttribute("Wrap")
		local e = if type(id) == "string" then FX[id] else nil
		if not e or sa.Color ~= Color3.new(1, 1, 1) then continue end -- (the painted half only, not the dark second tone)
		spec = e
		table.insert(pieces, sa.Parent :: BasePart)
	end
	if not spec or #pieces == 0 then return end
	local function area(b: BasePart): number local z = b.Size; return z.X * z.Y + z.Y * z.Z + z.X * z.Z end
	table.sort(pieces, function(a, b) return area(a) > area(b) end)
	while #pieces > 4 do table.remove(pieces) end
	local total = 0
	for _, b in pieces do total += area(b) end
	local ext = if gun:IsA("Model") then gun:GetExtentsSize() else Vector3.new(3, 1, 1)
	local s = math.max(ext.X, ext.Y, ext.Z) / 2.9 * 3.2 -- (studs per metre-ish: sizes in the spec are metres on the 2.9-stud rifle)
	local fp = gun:IsDescendantOf(workspace.CurrentCamera)
	local G: GunFx = { ems = {}, parts = pieces, fp = fp, on = true }
	for _, b in pieces do
		local em = Instance.new("ParticleEmitter")
		em.Name = "WrapFx"
		for k, v in fxProps(spec, s) do (em :: any)[k] = v end
		em.Shape = Enum.ParticleEmitterShape.Box
		em.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
		em.Rate = spec.rate * area(b) / total
		em.LockedToPart = fp
		em.Parent = b
		table.insert(G.ems, em)
	end
	gunFx[gun] = G
end
local function addFx(inst: Instance)
	if not inst:IsA("SurfaceAppearance") or inst:IsDescendantOf(ReplicatedStorage) then return end
	local id = inst:GetAttribute("Wrap")
	if not (type(id) == "string" and FX[id]) then return end
	local gun = inst.Parent and gunOf(inst.Parent)
	if not gun then return end
	saGun[inst] = gun
	if not dirty[gun] then dirty[gun] = true; task.defer(rebuild, gun) end -- (one rebuild per wrap call, after all its pieces)
end
for _, sa in CS:GetTagged("WrapSA") do addFx(sa) end
CS:GetInstanceAddedSignal("WrapSA"):Connect(addFx)
CS:GetInstanceRemovedSignal("WrapSA"):Connect(function(inst)
	local gun = saGun[inst]
	saGun[inst] = nil
	if gun and not dirty[gun] then dirty[gun] = true; task.defer(rebuild, gun) end
end)
-- on / off: hidden (first person hides your world gun, third person the viewmodel), aiming (first person), far
local wideFov = 70
RunService.Heartbeat:Connect(function()
	if next(gunFx) == nil then return end
	local cam = workspace.CurrentCamera
	local fov = if cam then cam.FieldOfView else 70
	wideFov = math.max(fov, wideFov - 0.02)
	local aiming = fov < wideFov * 0.95
	local at = if cam then cam.CFrame.Position else Vector3.zero
	for gun, G in gunFx do
		if not gun.Parent then for _, e in G.ems do e:Destroy() end; gunFx[gun] = nil; continue end
		local b = G.parts[1]
		local hidden = b == nil or b.Parent == nil or b.LocalTransparencyModifier >= 0.5 or b.Transparency >= 0.99
		local on = not hidden and not (G.fp and aiming) and (G.fp or (b.Position - at).Magnitude < NEAR)
		if on ~= G.on then
			G.on = on
			for _, e in G.ems do e.Enabled = on; if hidden then e:Clear() end end
		end
	end
end)

local acc, nearAcc, worst, worstAcc = 0, 0, 0, 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt; nearAcc += dt; worstAcc += dt
	if acc < 1 / HZ then return end
	acc = 0
	local t0 = os.clock()
	local cam = workspace.CurrentCamera
	if nearAcc >= 0.5 and cam then
		nearAcc = 0
		local at = cam.CFrame.Position
		for sa, e in live do
			local p = sa.Parent
			e.near = not (p and p:IsA("BasePart") and p:IsDescendantOf(workspace)) or (p.Position - at).Magnitude < NEAR
		end
	end
	local t = workspace:GetServerTimeNow() -- (one clock for everyone: the same wrap pulses in step on every screen)
	local cache: { [Spec]: Look } = {}
	for sa, e in live do
		if not sa.Parent then live[sa] = nil; continue end
		if not e.near then continue end
		local l = cache[e.spec]
		if not l then l = look(e.spec, t); cache[e.spec] = l end
		if l.f then sa.EmissiveStrength = e.es * l.f end
		if l.tint then sa.EmissiveTint = l.tint end
		if l.col then sa.Color = Color3.new(e.col.R * l.col.R, e.col.G * l.col.G, e.col.B * l.col.B) end -- (on the base tint: a second half stays dark)
	end
	local us = (os.clock() - t0) * 1e6
	if us > worst then worst = us end
	if worstAcc >= 1 then
		script:SetAttribute("StepUs", math.floor(worst + 0.5))
		script:SetAttribute("Live", (function() local n = 0; for _ in live do n += 1 end; return n end)())
		worst, worstAcc = 0, 0
	end
end)
