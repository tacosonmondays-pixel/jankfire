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
local Players = game:GetService("Players")

-- Settings, GRAPHICS > OTHER PLAYERS' SKIN EFFECTS ("animated wraps and flames"): when it is off, a gun held by someone
-- else keeps its wrap still (no breathing, no particles); your own gun, the racks and the pickers move as ever
local othersOff = false
local function isOthers(x: Instance): boolean
	for _, p in Players:GetPlayers() do
		if p ~= Players.LocalPlayer and p.Character and x:IsDescendantOf(p.Character) then return true end
	end
	return false
end

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
	lava = { k = "breathe", p = 3.4, lo = 0.8, hi = 1.15 },        -- (round 2, 20 Nov: the cracks' heat pulses under the rising embers)
	rainbow = { k = "iris", p = 10.0, sat = 0.08 },                -- a slow shimmer across the stripes
	-- the mastery camos (18 Nov 2026, weapon mastery): gold glints now and then; damascus's temper shifts very faintly;
	-- the diamond's facets sweep through the spectrum; Mastery Galaxy's gas drifts violet to teal and breathes
	mastery_gold = { k = "glint", p = 5.5, lo = 0.45, hi = 1.5 },
	mastery_damascus = { k = "iris", p = 14.0, sat = 0.05 },
	mastery_diamond = { k = "iris", p = 9.0, sat = 0.1 },
	mastery_galaxy = { k = "drift", p = 12.0, p2 = 6.0, lo = 0.8, hi = 1.15, a = Color3.fromHex("d2b8ff"), b = Color3.fromHex("a8f0ff") },
}
script:SetAttribute("Animated", (function() local n = 0; for _ in SPEC do n += 1 end; return n end)())

type Entry = { spec: Spec, es: number, tint: Color3, col: Color3, near: boolean }
local live: { [SurfaceAppearance]: Entry } = {}

-- (a picture shown in a ViewportFrame glows PREVIEW_GAIN times as strongly: see THE PICKERS below. Before the animation
-- reads its strength, so a breathing wrap breathes round the raised glow)
local PREVIEW_GAIN = 1.6
-- (the script's attribute PreviewGlowOff = true turns the gain and the halos off, for before / after photos; a preview
-- built while it is on keeps its gain)
local function gain(inst: SurfaceAppearance)
	if script:GetAttribute("PreviewGlowOff") then return end
	if inst:GetAttribute("PreviewGain") or not inst:FindFirstAncestorOfClass("ViewportFrame") then return end
	inst:SetAttribute("PreviewGain", true)
	inst.EmissiveStrength *= PREVIEW_GAIN
end

local function add(inst: Instance)
	if not inst:IsA("SurfaceAppearance") or inst:IsDescendantOf(ReplicatedStorage) then return end
	gain(inst)
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
		if g:GetAttribute("Style") == "mark" then
			-- a mark (Triangulum) holds still; its stars breathe slowly, one after another (each its own label)
			if g.Name ~= "WrapHole" then
				for _, st in g:GetChildren() do
					local i = st:GetAttribute("I")
					if st:IsA("ImageLabel") and type(i) == "number" then
						local f = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(TAU * (t / 4.5 - i / 3))) ^ 2
						st.ImageColor3 = Color3.new(f, f, f)
					end
				end
			end
		elseif g.Name == "WrapHole" then
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
	-- (18 Nov, the owner: "can you make nebula twinkle": stars that fade bright and dim where they sit, each at its own
	-- slow pace, about ten on a rifle at once; the drawn four-point stars keep their bloom under them)
	nebula = { kind = "twinkle", col = Color3.fromHex("f6dcff"), col2 = Color3.fromHex("dce6ff"), rate = 5, size = 0.016, life = 2.2, rise = 0 },
	galaxy = { kind = "dot", col = Color3.fromHex("dfe6ff"), rate = 4, size = 0.01, life = 1.0, rise = 0 },
	hex = { kind = "dot", col = Color3.fromHex("6fe2ff"), rate = 3, size = 0.009, life = 1.4, rise = 0.25 },
	circuit = { kind = "dot", col = Color3.fromHex("8dff7a"), rate = 2.5, size = 0.008, life = 0.6, rise = 0.1 },
	tokyo = { kind = "dot", col = Color3.fromHex("ff6ad8"), col2 = Color3.fromHex("5ad8ff"), rate = 3, size = 0.009, life = 1.0, rise = 0.2 },
	ducky = { kind = "bubble", col = Color3.fromHex("f1e9ea"), rate = 1.1, size = 0.026, life = 1.8, rise = 0.25 },
	holo = { kind = "sparkle", col = Color3.fromHex("ffffff"), rate = 2, size = 0.015, life = 0.6, rise = 0 },
	-- (the mastery camos: gold glints off the gold, the diamond and Mastery Galaxy twinkle where they sit)
	mastery_gold = { kind = "sparkle", col = Color3.fromHex("ffe6a0"), rate = 2.2, size = 0.018, life = 0.7, rise = 0.1 },
	mastery_diamond = { kind = "twinkle", col = Color3.fromHex("ffffff"), col2 = Color3.fromHex("d8ecff"), rate = 4, size = 0.014, life = 1.6, rise = 0 },
	mastery_galaxy = { kind = "twinkle", col = Color3.fromHex("f0e4ff"), col2 = Color3.fromHex("c8f4ff"), rate = 5, size = 0.016, life = 2.2, rise = 0 },
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
	elseif e.kind == "twinkle" then -- (a star that fades in, holds, fades out where it is: no drift; lives 0.6 to 1.4 x)
		local w = e.size * s
		return { Texture = TEXF.sparkle, Color = col, LightInfluence = 0, LightEmission = 1, Brightness = 3,
			Size = nseq(0, w * 0.55, 0.5, w, 1, w * 0.55), Transparency = nseq(0, 1, 0.3, 0.08, 0.55, 0, 0.75, 0.2, 1, 1),
			Lifetime = NumberRange.new(e.life * 0.6, e.life * 1.4), Speed = NumberRange.new(0, 0), SpreadAngle = Vector2.zero,
			Acceleration = Vector3.zero, Drag = 0, Rotation = NumberRange.new(-20, 20), RotSpeed = NumberRange.new(-4, 4) }
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
	if othersOff and isOthers(gun) then return end
	local spec: FxSpec?, pieces = nil, {}
	for _, sa in gun:GetDescendants() do
		if not (sa:IsA("SurfaceAppearance") and sa.Name == "WrapSA" and sa.Parent and sa.Parent:IsA("BasePart")) then continue end
		local id = sa:GetAttribute("Wrap")
		local e = if type(id) == "string" then FX[id] else nil
		if not e or sa:GetAttribute("Partner") then continue end -- (the pattern's own pieces only, not the partner)
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
		-- (first person, the VFX session's round 12 photos: Lava's embers rose into the upper middle of the view, one
		-- inside the middle fifth; 0.55 of the life keeps them round the gun, a third of the climb)
		-- (a twinkle stays where it was born, so it keeps its whole life and rides the gun everywhere)
		local still = spec.kind == "twinkle"
		if fp and not still then em.Lifetime = NumberRange.new(em.Lifetime.Min * 0.55, em.Lifetime.Max * 0.55) end
		em.Shape = Enum.ParticleEmitterShape.Box
		em.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
		em.Rate = spec.rate * area(b) / total
		em.LockedToPart = fp or still
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
-- (OTHER PLAYERS' SKIN EFFECTS, above: a change rebuilds every gun's particles)
task.spawn(function()
	local ok, Settings = pcall(function() return require(script.Parent:WaitForChild("Settings")) :: any end)
	if not ok or type(Settings) ~= "table" then return end
	Settings.watch("gfx.othersSkin", function(v: any)
		othersOff = v == false
		for _, gun in saGun do if not dirty[gun] then dirty[gun] = true; task.defer(rebuild, gun) end end
	end)
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

-- THE PICKERS (18 Nov 2026, the owner: "can you add a glow to certain textures like a brighter glow? I can't see it
-- when applying it really"): a ViewportFrame (the loadout, the match loadout, the shop, crates) draws no Bloom, so a
-- glow wrap's light can't spread past its lines there as it does in the world. In one, a glowing picture glows
-- PREVIEW_GAIN times as strongly (gain, above), and a wrap that glows at least HALO_MIN (its book strength) gets a soft
-- halo behind the weapon in its glow colour (the picture's Accent), breathing slowly: an ImageLabel just behind the
-- frame, fitted every frame round the weapon as the frame's camera sees it (so it follows the loadout's turning gun).
-- A frame whose parent lays its children out (a list or a grid) gets the gain only: a halo there would take a slot.
-- The pattern's pieces decide: the partner alone (NORMAL / REVERSE's other side) gets no halo.
-- Particles don't draw in a ViewportFrame either, so a glowing wrap with WRAP EFFECTS (FX) gets a few of them drawn
-- over the weapon as images instead (MOTES): Nebula's twinkles fading in and out where they sit, Lava's embers rising,
-- Galaxy's dots, Kintsugi's and Holo's glints, at points on its picture pieces, following the turning gun
local HALO_MIN = 1.5
local HALO_TEX = TEXF.glow
type Mote = { img: ImageLabel, part: BasePart, off: Vector3, t0: number, life: number }
type Halo = { img: ImageLabel, vp: ViewportFrame, sas: { [Instance]: number }, col: Color3, a: number, wid: string?,
	motes: { Mote }, due: number }
local MOTES = { twinkle = { n = 7, size = 0.06, tex = "sparkle" }, sparkle = { n = 4, size = 0.05, tex = "sparkle" },
	dot = { n = 5, size = 0.032, tex = "glow" }, ember = { n = 5, size = 0.04, tex = "glow" }, bubble = { n = 3, size = 0.06, tex = "bubble" } }
local halos: { [ViewportFrame]: Halo } = {}
local function bookOf(sa: Instance): SurfaceAppearance?
	local id = sa:GetAttribute("Wrap")
	local lib = ReplicatedStorage:FindFirstChild("JankfireWraps")
	local b = if type(id) == "string" and lib then lib:FindFirstChild(id) else nil
	return if b and b:IsA("SurfaceAppearance") then b else nil
end
local function addHalo(inst: Instance)
	if not inst:IsA("SurfaceAppearance") or inst:IsDescendantOf(ReplicatedStorage) then return end
	if inst:GetAttribute("Partner") then return end -- (the pattern's own pieces only)
	local vp = inst:FindFirstAncestorOfClass("ViewportFrame")
	local book = bookOf(inst)
	if not (vp and book and book.EmissiveStrength >= HALO_MIN) then return end
	local acc = book:GetAttribute("Accent")
	local col = (if typeof(acc) == "Color3" then acc else Color3.new(1, 1, 1)):Lerp(Color3.new(1, 1, 1), 0.15)
	local h = halos[vp]
	if not h then
		local par = vp.Parent
		if not (par and par:IsA("GuiBase2d")) or par:FindFirstChildWhichIsA("UIGridStyleLayout") then return end
		local img = Instance.new("ImageLabel")
		img.Name = "WrapGlowHalo"
		img.BackgroundTransparency = 1
		img.Image = HALO_TEX
		img.ImageTransparency = 1
		img.AnchorPoint = Vector2.new(0.5, 0.5)
		img.ZIndex = vp.ZIndex - 1
		img.Active = false
		img.Selectable = false
		img.Parent = par
		h = { img = img, vp = vp, sas = {}, col = col, a = 0, motes = {}, due = 0 }
		halos[vp] = h
	end
	local hh = h :: Halo
	hh.sas[inst] = book.EmissiveStrength
	hh.col = col
	local wid = inst:GetAttribute("Wrap")
	hh.wid = if type(wid) == "string" then wid else nil
	local strongest = 0
	for _, es in hh.sas do strongest = math.max(strongest, es) end
	hh.a = math.clamp(0.3 + strongest * 0.05, 0.38, 0.6) -- (the halo's opacity at the top of its breath)
end
for _, sa in CS:GetTagged("WrapSA") do addHalo(sa) end
CS:GetInstanceAddedSignal("WrapSA"):Connect(addHalo)
local function dropHalo(vp: ViewportFrame)
	local h = halos[vp]
	if h then
		h.img:Destroy()
		for _, mo in h.motes do mo.img:Destroy() end
		halos[vp] = nil
	end
end
local CORNERS = { -1, 1 }
RunService.RenderStepped:Connect(function()
	if next(halos) == nil then return end
	local t = workspace:GetServerTimeNow()
	for vp, h in halos do
		local model: Instance? = nil
		for sa in h.sas do
			if sa.Parent and sa:IsDescendantOf(vp) then
				if not model then
					local m = sa.Parent :: Instance
					while m.Parent and m.Parent ~= vp and m.Parent:IsA("Model") do m = m.Parent end
					model = m
				end
			else
				h.sas[sa] = nil
			end
		end
		if not model or not vp.Parent or h.img.Parent ~= vp.Parent then dropHalo(vp); continue end
		local cam = vp.CurrentCamera
		local abs = vp.AbsoluteSize
		local show = vp.Visible and cam ~= nil and abs.X > 4 and abs.Y > 4 and model:IsA("Model") and not script:GetAttribute("PreviewGlowOff")
		if show then
			-- the weapon's box as the frame's camera sees it: the eight corners, projected
			local cf, size = (model :: Model):GetBoundingBox()
			local th = math.tan(math.rad((cam :: Camera).FieldOfView) / 2)
			local aspect = abs.X / abs.Y
			local x0, x1, y0, y1 = math.huge, -math.huge, math.huge, -math.huge
			for _, sx in CORNERS do for _, sy in CORNERS do for _, sz in CORNERS do
				local p = (cam :: Camera).CFrame:PointToObjectSpace(cf:PointToWorldSpace(size * Vector3.new(sx, sy, sz) / 2))
				local d = math.max(-p.Z, 0.05)
				local fx, fy = 0.5 + p.X / d / (th * aspect) / 2, 0.5 - p.Y / d / th / 2
				x0, x1, y0, y1 = math.min(x0, fx), math.max(x1, fx), math.min(y0, fy), math.max(y1, fy)
			end end end
			local w, ht = (x1 - x0) * 1.3, math.max((y1 - y0) * 1.9, (x1 - x0) * aspect * 0.42) -- (fractions of the frame)
			local cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
			local P, S, A = vp.Position, vp.Size, vp.AnchorPoint
			h.img.Position = UDim2.new(P.X.Scale + S.X.Scale * (cx - A.X), P.X.Offset + S.X.Offset * (cx - A.X),
				P.Y.Scale + S.Y.Scale * (cy - A.Y), P.Y.Offset + S.Y.Offset * (cy - A.Y))
			h.img.Size = UDim2.new(S.X.Scale * w, S.X.Offset * w, S.Y.Scale * ht, S.Y.Offset * ht)
			h.img.ImageColor3 = h.col
			h.img.ImageTransparency = 1 - h.a * (0.82 + 0.18 * math.sin(TAU * t / 3.0))
			-- the motes: born at a random point in a random picture piece's box, faded in and out over their life
			local spec = if h.wid then FX[h.wid] else nil
			local kind = if spec then MOTES[spec.kind] else nil
			if spec and kind and #h.motes < kind.n and t >= h.due then
				local pieces = {}
				for sa in h.sas do
					local p = sa.Parent
					if p and p:IsA("BasePart") then table.insert(pieces, p) end
				end
				if #pieces > 0 then
					local p = pieces[math.random(#pieces)]
					local img = Instance.new("ImageLabel")
					img.Name = "WrapMote"
					img.BackgroundTransparency = 1
					img.Image = (TEXF :: any)[kind.tex]
					img.ImageColor3 = if spec.col2 and math.random() < 0.5 then spec.col2 else spec.col
					img.ImageTransparency = 1
					img.AnchorPoint = Vector2.new(0.5, 0.5)
					img.Rotation = math.random(-20, 20)
					img.Active = false
					img.Parent = vp -- (a frame's own children draw over its picture)
					local z = p.Size * 0.45
					table.insert(h.motes, { img = img, part = p, t0 = t, life = spec.life * (0.6 + 0.8 * math.random()),
						off = Vector3.new((math.random() * 2 - 1) * z.X, (math.random() * 2 - 1) * z.Y, (math.random() * 2 - 1) * z.Z) })
				end
				h.due = t + spec.life / kind.n * (0.5 + math.random())
			end
			local gw = (x1 - x0) * aspect -- (the weapon's width on screen, in frame heights)
			for i = #h.motes, 1, -1 do
				local mo = h.motes[i]
				local k = (t - mo.t0) / mo.life
				if k >= 1 or not mo.part.Parent or not spec or not kind then mo.img:Destroy(); table.remove(h.motes, i); continue end
				local wp = mo.part.CFrame:PointToWorldSpace(mo.off)
				if spec.kind == "ember" then wp += Vector3.new(0, k * 0.5, 0) end
				local p = (cam :: Camera).CFrame:PointToObjectSpace(wp)
				local d = math.max(-p.Z, 0.05)
				mo.img.Position = UDim2.fromScale(0.5 + p.X / d / (th * aspect) / 2, 0.5 - p.Y / d / th / 2)
				local sz = kind.size * gw * (if spec.kind == "twinkle" then 0.75 + 0.25 * math.sin(math.pi * k) else 1)
				mo.img.Size = UDim2.fromScale(sz / aspect, sz)
				mo.img.ImageTransparency = 1 - 0.95 * math.sin(math.pi * k) ^ (if spec.kind == "twinkle" then 1.5 else 1)
			end
		else
			for _, mo in h.motes do mo.img:Destroy() end
			table.clear(h.motes)
		end
		h.img.Visible = show
	end
end)

-- WRAP FLOW (19 Nov 2026, the owner: "also can some of the wraps be animated?"; docs/WRAP-TEXTURES.md "Moving wraps").
-- A SurfaceAppearance cannot scroll its picture, but a Texture can (OffsetStudsU / V), and since Roblox's PBR decals a
-- Texture can glow too (EmissiveMaskContent, EmissiveStrength). So a moving wrap is its still picture plus one or two
-- see-through glowing Textures over the pattern's biggest pieces, slid along the gun: Galaxy's and Nebula's stars drift
-- in two layers at two speeds (depth), a soft band of light sweeps along the gold of Kintsugi and Mastery Gold every few
-- seconds. The pictures are tools/roblox/wrap_flow.py's (round soft dots; one slanted band).
-- Cost (memory roblox-performance: never write many instances from Lua every frame): each Texture is moved by one
-- looping linear tween (the engine moves it; no Lua per frame), at most FLOW_PIECES pieces a gun x 3 sides x its layers;
-- a gun's tweens pause while it is hidden, further than NEAR or (GRAPHICS > OTHER PLAYERS' SKIN EFFECTS off) in someone
-- else's hands. The attribute FlowTex is how many Textures are moving.
local TweenService = game:GetService("TweenService")
-- (the pictures can't be set by a game script while playing: "cannot write EmissiveMaskContent", seen in Play 20 Nov.
-- So the Textures are made in Edit, ReplicatedStorage.JankfireWrapFlow.stars / .glint, by studio-tools/WrapPartnerBook
-- with tools/roblox/wrap_flow.py's pictures (stars 90506142503050 + mask 138098836499581, glint 119853642092920 + mask
-- 119596018117654), and cloned here; only Face, tiles, offsets, Transparency, Color3 and the glow are set, each in a
-- pcall so one refused property can't stop a gun's layer)
local function flowTemplate(name: string): Texture?
	local f = ReplicatedStorage:FindFirstChild("JankfireWrapFlow")
	local t = f and f:FindFirstChild(name)
	return if t and t:IsA("Texture") then t else nil
end
local function put(x: Instance, prop: string, v: any)
	pcall(function() (x :: any)[prop] = v end)
end
-- tex: the picture; u, v: its tile, in metres of gun along it and across it (x the gun's K studs a metre); speed:
-- metres a second along the gun, toward the stock (negative: toward the muzzle; a glint's tile is long, so its band
-- crosses a rifle once a tile: every u / speed seconds; 0 = still along); rise: metres a second up the gun's sides (negative: falling; only on the left and right
-- faces); glow: the Texture's EmissiveStrength; tint: its colour; a: how much of it shows (1 - Transparency); sides:
-- which of the gun's "left", "right", "top" faces wear it (all three when nil)
type Layer = { tex: string, u: number, v: number, speed: number, rise: number?, glow: number, tint: Color3?, a: number?,
	sides: { string }? }
local FLOW: { [string]: { Layer } } = {
	-- (Galaxy: dots only, the owner's rule for it; a fine slow layer and a sparser quicker one in front: depth)
	galaxy = {
		{ tex = "stars", u = 0.34, v = 0.34, speed = 0.022, glow = 2.0, tint = Color3.fromHex("dfe6ff"), a = 0.7 },
		{ tex = "stars", u = 0.62, v = 0.62, speed = 0.05, glow = 3.0, tint = Color3.fromHex("ffffff"), a = 0.9 },
	},
	nebula = {
		{ tex = "stars", u = 0.36, v = 0.36, speed = 0.024, glow = 2.2, tint = Color3.fromHex("f3e2ff"), a = 0.7 },
		{ tex = "stars", u = 0.64, v = 0.64, speed = 0.052, glow = 3.0, tint = Color3.fromHex("e2ecff"), a = 0.9 },
	},
	mastery_galaxy = {
		{ tex = "stars", u = 0.36, v = 0.36, speed = 0.026, glow = 2.4, tint = Color3.fromHex("eadfff"), a = 0.75 },
		{ tex = "stars", u = 0.66, v = 0.66, speed = 0.056, glow = 3.2, tint = Color3.fromHex("d8f6ff"), a = 0.9 },
	},
	triangulum = {
		{ tex = "stars", u = 0.4, v = 0.4, speed = 0.02, glow = 2.0, tint = Color3.fromHex("fff1cc"), a = 0.6 },
	},
	-- (the glints: one band every u / speed seconds, crossing a rifle in under two seconds)
	kintsugi = { { tex = "glint", u = 3.2, v = 0.7, speed = 0.62, glow = 2.1, tint = Color3.fromHex("ffd98a"), a = 0.75 } },
	mastery_gold = { { tex = "glint", u = 3.0, v = 0.7, speed = 0.66, glow = 2.4, tint = Color3.fromHex("fff0c8") } },
	mastery_diamond = { { tex = "glint", u = 3.6, v = 0.7, speed = 0.7, glow = 2.8, tint = Color3.fromHex("eef6ff") } },
	holo = { { tex = "glint", u = 3.4, v = 0.7, speed = 0.6, glow = 1.8, tint = Color3.fromHex("ffffff"), a = 0.8 } },
	-- ROUND 2 (20 Nov 2026, main for the owner: "how ar ethe animated wraps coming?"). The rule from the Rivals study:
	-- the pattern moves, the gun's overall brightness stays put, and the motion is slow (a drift you notice, not a
	-- flicker); one or two layers, the second slower or the other way for depth; light that rises or falls only on the
	-- gun's sides
	-- (Lava: embers rise off the cracks, and its glow breathes: SPEC above)
	lava = { { tex = "embers", u = 0.24, v = 0.24, speed = 0.004, rise = 0.035, glow = 3.2, tint = Color3.fromHex("ffa04a"), a = 0.85,
		sides = { "left", "right" } } },
	-- (water: two nets of light drifting against each other, so the caustics shimmer and re-form)
	bigwave = {
		{ tex = "caustics", u = 0.3, v = 0.3, speed = 0.018, rise = 0.006, glow = 1.4, tint = Color3.fromHex("d8f2ff"), a = 0.32 },
		{ tex = "caustics", u = 0.43, v = 0.43, speed = -0.011, glow = 1.1, tint = Color3.fromHex("bfe6ff"), a = 0.22 },
	},
	koi = {
		{ tex = "caustics", u = 0.28, v = 0.28, speed = 0.014, rise = 0.005, glow = 1.3, tint = Color3.fromHex("dff8ff"), a = 0.3 },
		{ tex = "caustics", u = 0.4, v = 0.4, speed = -0.009, glow = 1.0, tint = Color3.fromHex("c8f0ea"), a = 0.2 },
	},
	-- (Aurora: two soft curtains sliding past each other, green over violet)
	aurora = {
		{ tex = "curtain", u = 0.7, v = 0.5, speed = 0.03, glow = 2.0, tint = Color3.fromHex("b8ffd8"), a = 0.42 },
		{ tex = "curtain", u = 1.05, v = 0.5, speed = -0.017, glow = 1.6, tint = Color3.fromHex("e2c4ff"), a = 0.3 },
	},
	-- (light running back along the traces and the grooves, head first on the side you see; brighter and denser after
	-- the 20 Nov clips, where they were hard to see)
	circuit = { { tex = "pulses", u = 0.7, v = 0.16, speed = 0.26, glow = 4.5, tint = Color3.fromHex("b4ffa0"), a = 1 } },
	hex = { { tex = "pulses", u = 0.7, v = 0.16, speed = 0.2, glow = 4.2, tint = Color3.fromHex("9aeeff"), a = 1 } },
	-- (CRT: a soft bright bar rolling up the screen every ~6 s)
	crt = { { tex = "scan", u = 0.1, v = 0.4, speed = 0, rise = 0.07, glow = 1.6, tint = Color3.fromHex("dcffe6"), a = 0.5,
		sides = { "left", "right" } } },
	-- (Tokyo Night: a light rain over the neon; stronger after the 20 Nov clips, where it barely showed)
	tokyo = { { tex = "rain", u = 0.26, v = 0.26, speed = 0, rise = -0.24, glow = 2.2, tint = Color3.fromHex("d6e0ff"), a = 0.8,
		sides = { "left", "right" } } },
	-- (Sakura Storm: single petals blowing along the gun and down)
	sakura = { { tex = "petals", u = 0.45, v = 0.45, speed = 0.04, rise = -0.02, glow = 0.5, tint = Color3.fromHex("ffd6e4"), a = 0.9 } },
	-- (Vaporwave: the neon grid scrolls toward you, like the grid floor under a horizon)
	vapor = { { tex = "grid", u = 0.16, v = 0.16, speed = 0.06, glow = 2.2, tint = Color3.fromHex("ff74dc"), a = 0.42 } },
	-- (Lava Lamp: soft blobs rising)
	lavalamp = { { tex = "blobs", u = 0.4, v = 0.4, speed = 0, rise = 0.022, glow = 1.8, tint = Color3.fromHex("ff9a5a"), a = 0.5,
		sides = { "left", "right" } } },
	-- (a slow light through the panes; the opal's fire catching)
	stained = { { tex = "glint", u = 3.6, v = 0.8, speed = 0.5, glow = 1.6, tint = Color3.fromHex("fff0d6"), a = 0.55 } },
	opal = { { tex = "glint", u = 3.4, v = 0.7, speed = 0.55, glow = 2.0, tint = Color3.fromHex("f6eaff"), a = 0.7 } },
}
local FLOW_PIECES = 6
-- (which way OffsetStuds moves the picture: the Edit probe of 20 Nov put the same bar on two slabs, one with
-- OffsetStudsV 0.5 more, and that bar sat 0.5 stud HIGHER, so a growing offset moves the picture toward -V; with
-- FACE_UV's axes that makes both signs -1, which also lines a band up across the pieces)
local FLOW_OFFSIGN = -1
local FLOW_RISESIGN = -1
-- each face's +U and +V in the part's own frame (Roblox lays a Texture as a Decal reads: upright, seen from outside)
local FACE_UV: { [Enum.NormalId]: { Vector3 } } = {
	[Enum.NormalId.Left] = { Vector3.new(0, 0, 1), Vector3.new(0, -1, 0) },
	[Enum.NormalId.Right] = { Vector3.new(0, 0, -1), Vector3.new(0, -1, 0) },
	[Enum.NormalId.Front] = { Vector3.new(-1, 0, 0), Vector3.new(0, -1, 0) },
	[Enum.NormalId.Back] = { Vector3.new(1, 0, 0), Vector3.new(0, -1, 0) },
	[Enum.NormalId.Top] = { Vector3.new(1, 0, 0), Vector3.new(0, 0, 1) },
	[Enum.NormalId.Bottom] = { Vector3.new(1, 0, 0), Vector3.new(0, 0, -1) },
}
local FACES = { Enum.NormalId.Left, Enum.NormalId.Right, Enum.NormalId.Top, Enum.NormalId.Bottom, Enum.NormalId.Front, Enum.NormalId.Back }
type FlowGun = { texs: { Texture }, tweens: { Tween }, parts: { BasePart }, fp: boolean, on: boolean }
local flowGuns: { [Instance]: FlowGun } = {}
local flowSaGun: { [Instance]: Instance } = {}
local flowDirty: { [Instance]: boolean } = {}
local function flowCount()
	local n = 0
	for _, G in flowGuns do if G.on then n += #G.texs end end
	script:SetAttribute("FlowTex", n)
end
local function flowRebuild(gun: Instance)
	flowDirty[gun] = nil
	local old = flowGuns[gun]
	if old then
		for _, tw in old.tweens do tw:Cancel() end
		for _, tx in old.texs do tx:Destroy() end
		flowGuns[gun] = nil
	end
	if not gun.Parent then flowCount(); return end
	if othersOff and isOthers(gun) then flowCount(); return end
	local layers: { Layer }?, pieces = nil, {}
	for _, sa in gun:GetDescendants() do
		if not (sa:IsA("SurfaceAppearance") and sa.Name == "WrapSA" and sa.Parent and sa.Parent:IsA("BasePart")) then continue end
		if sa:GetAttribute("Partner") then continue end
		local id = sa:GetAttribute("Wrap")
		local L = if type(id) == "string" then FLOW[id] else nil
		if not L then continue end
		layers = L
		table.insert(pieces, sa.Parent :: BasePart)
	end
	if not layers or #pieces == 0 then flowCount(); return end
	local function area(b: BasePart): number local z = b.Size; return z.X * z.Y + z.Y * z.Z + z.X * z.Z end
	table.sort(pieces, function(a, b) return area(a) > area(b) end)
	while #pieces > FLOW_PIECES do table.remove(pieces) end
	-- the gun's own frame and long axis (as WeaponModels.wrap measures it), its studs a metre
	local ref = if gun:IsA("Model") then gun:GetPivot() else (pieces[1] :: BasePart).CFrame
	local ext = if gun:IsA("Model") then gun:GetExtentsSize() else Vector3.new(3, 1, 1)
	local kk = gun:GetAttribute("K")
	local k = if type(kk) == "number" and kk > 0 then kk else math.max(ext.X, ext.Y, ext.Z) / 0.9
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, d in gun:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.99 then
			local v = ref:PointToObjectSpace(d.Position); lo = lo:Min(v); hi = hi:Max(v)
		end
	end
	local span = hi - lo
	local axisL = if span.X >= span.Y and span.X >= span.Z then Vector3.xAxis elseif span.Y >= span.Z then Vector3.yAxis else Vector3.zAxis
	local along = ref:VectorToWorldSpace(axisL)
	local up = ref.UpVector
	local SIDE = { left = -ref.RightVector, right = ref.RightVector, top = ref.UpVector } -- (the gun's left, right and top)
	local G: FlowGun = { texs = {}, tweens = {}, parts = pieces, fp = gun:IsDescendantOf(workspace.CurrentCamera), on = true }
	for _, p in pieces do
		local cf, sz = p.CFrame, p.Size
		for _, side in { "left", "right", "top" } do
			-- the piece's face that looks most that way
			local want = SIDE[side]
			local best, bestD = Enum.NormalId.Left, -2
			for _, f in FACES do
				local d = cf:VectorToWorldSpace(Vector3.fromNormalId(f)):Dot(want)
				if d > bestD then best, bestD = f, d end
			end
			if bestD < 0.5 then continue end
			local uv = FACE_UV[best]
			local n = Vector3.fromNormalId(best)
			-- which texture axis runs along the gun on this face (A) and which across it (C), their signs, and where the
			-- face's U / V start along and up the gun (so a band crosses the pieces as one)
			local gl, gu = cf:VectorToObjectSpace(along), cf:VectorToObjectSpace(up)
			local alongV = math.abs(gl:Dot(uv[2])) > math.abs(gl:Dot(uv[1]))
			local axA = if alongV then uv[2] else uv[1]
			local axC = if alongV then uv[1] else uv[2]
			local sA = if axA:Dot(gl) >= 0 then 1 else -1
			local sC = if axC:Dot(gu) >= 0 then 1 else -1
			local upOk = math.abs(axC:Dot(gu)) > 0.5 -- (this face's across axis really runs up the gun: a side)
			local corner = cf:PointToWorldSpace((n - uv[1] - uv[2]) * sz / 2)
			local startA = (corner - ref.Position):Dot(along)
			local startC = (corner - ref.Position):Dot(up)
			for _, L in layers :: { Layer } do
				if L.sides and not table.find(L.sides, side) then continue end
				local rise = if upOk then (L.rise or 0) else 0
				if L.speed == 0 and rise == 0 then continue end
				local tmpl = flowTemplate(L.tex)
				if not tmpl then continue end
				local tx = tmpl:Clone()
				tx.Name = "WrapFlow"
				put(tx, "Face", best)
				put(tx, "EmissiveStrength", L.glow)
				put(tx, "EmissiveTint", L.tint or Color3.new(1, 1, 1))
				put(tx, "Color3", L.tint or Color3.new(1, 1, 1))
				put(tx, "Transparency", 1 - (L.a or 1))
				local tileA, tileC = L.u * k, L.v * k
				put(tx, "StudsPerTileU", if alongV then tileC else tileA)
				put(tx, "StudsPerTileV", if alongV then tileA else tileC)
				put(tx, "ZIndex", 2)
				if p.LocalTransparencyModifier >= 0.5 then put(tx, "LocalTransparencyModifier", 1) end -- (born hidden: no flash)
				local propA = if alongV then "OffsetStudsV" else "OffsetStudsU"
				local propC = if alongV then "OffsetStudsU" else "OffsetStudsV"
				local baseA = -FLOW_OFFSIGN * sA * startA
				local baseC = -FLOW_RISESIGN * sC * startC
				put(tx, propA, baseA)
				put(tx, propC, baseC)
				-- one looping linear tween; each axis it moves goes a whole number of tiles, so the loop has no seam
				local goal: { [string]: number } = {}
				local T: number
				if L.speed ~= 0 then
					T = tileA / math.abs(L.speed * k)
					goal[propA] = baseA + FLOW_OFFSIGN * sA * tileA * math.sign(L.speed)
					if rise ~= 0 then
						local nC = math.max(1, math.floor(math.abs(rise * k) * T / tileC + 0.5))
						goal[propC] = baseC + FLOW_RISESIGN * sC * tileC * nC * math.sign(rise)
					end
				else
					T = tileC / math.abs(rise * k)
					goal[propC] = baseC + FLOW_RISESIGN * sC * tileC * math.sign(rise)
				end
				tx.Parent = p
				local tw = TweenService:Create(tx, TweenInfo.new(T, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, -1), goal)
				tw:Play()
				table.insert(G.texs, tx)
				table.insert(G.tweens, tw)
			end
		end
	end
	flowGuns[gun] = G
	flowCount()
end
local function addFlow(inst: Instance)
	if not inst:IsA("SurfaceAppearance") or inst:IsDescendantOf(ReplicatedStorage) then return end
	local id = inst:GetAttribute("Wrap")
	if not (type(id) == "string" and FLOW[id]) then return end
	local gun = inst.Parent and gunOf(inst.Parent)
	if not gun then return end
	flowSaGun[inst] = gun
	if not flowDirty[gun] then flowDirty[gun] = true; task.defer(flowRebuild, gun) end
end
for _, sa in CS:GetTagged("WrapSA") do addFlow(sa) end
CS:GetInstanceAddedSignal("WrapSA"):Connect(addFlow)
CS:GetInstanceRemovedSignal("WrapSA"):Connect(function(inst)
	local gun = flowSaGun[inst]
	flowSaGun[inst] = nil
	if gun and not flowDirty[gun] then flowDirty[gun] = true; task.defer(flowRebuild, gun) end
end)
task.spawn(function()
	local ok, Settings = pcall(function() return require(script.Parent:WaitForChild("Settings")) :: any end)
	if not ok or type(Settings) ~= "table" then return end
	Settings.watch("gfx.othersSkin", function()
		for _, gun in flowSaGun do if not flowDirty[gun] then flowDirty[gun] = true; task.defer(flowRebuild, gun) end end
	end)
end)
-- on / off, four times a second: hidden (first person hides your world gun, third person the viewmodel; a Texture
-- follows its part's LocalTransparencyModifier only through its own) or far
local flowAcc = 0
RunService.Heartbeat:Connect(function(dt: number)
	flowAcc += dt
	if flowAcc < 0.25 or next(flowGuns) == nil then return end
	flowAcc = 0
	local cam = workspace.CurrentCamera
	local at = if cam then cam.CFrame.Position else Vector3.zero
	local changed = false
	for gun, G in flowGuns do
		if not gun.Parent then
			for _, tw in G.tweens do tw:Cancel() end
			for _, tx in G.texs do tx:Destroy() end
			flowGuns[gun] = nil; changed = true; continue
		end
		local b = G.parts[1]
		local hidden = b == nil or b.Parent == nil or b.LocalTransparencyModifier >= 0.5 or b.Transparency >= 0.99
		local on = not hidden and (G.fp or (b.Position - at).Magnitude < NEAR)
		if on ~= G.on then
			G.on = on; changed = true
			for _, tw in G.tweens do if on then tw:Play() else tw:Pause() end end
			for _, tx in G.texs do put(tx, "LocalTransparencyModifier", if hidden then 1 else 0) end
		end
	end
	if changed then flowCount() end
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
			local was = e.near
			e.near = (not (p and p:IsA("BasePart") and p:IsDescendantOf(workspace)) or (p.Position - at).Magnitude < NEAR)
				and not (othersOff and p ~= nil and isOthers(p))
			-- (a piece that stops moving rests at its own look, not wherever the breath left it)
			if was and not e.near then sa.EmissiveStrength = e.es; sa.EmissiveTint = e.tint; sa.Color = e.col end
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
