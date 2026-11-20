--!strict
-- FINISHER SCENES (19 Nov 2026; roblox/docs/FINISHERS.md): the owner's "cinematic" finishers. A finisher with a scene
-- (Finishers row `scene`) plays a small story in a few shots instead of the recording-based cut: the killer's and the
-- victim's own avatars (the replay's ghost copies, with their skins) act it out with mocap clips (Finishers.SCENE_ANIMS,
-- uploaded from the vault's Mixamo clips and the MotionBricks takes made from them), on a small set of its own built
-- far off the map, under a lens that moves the way the storyboards and the video planned it.
-- The plan is the video's (tools/roblox/finisher_r15.py video:<v>, boiled down by finisher_scene_data.py into
-- FinisherSceneData): per frame (24 fps) the lens, each body's clip and moment and where its root stands, where the
-- katana is. This plays it at the screen's frame rate (the frames are blended) and adds what moves on its own: the
-- blade's ink trail, drifting petals, the ink stroke, the petal burst, the body coming apart, the two-tone hit frames.
-- Scene.can(row, kind, kg, vg) -> boolean     both bodies are R15 with an Animator and the scene's data is here
-- Scene.start(s, kind) -> sc                  builds the set and takes the two bodies (s = Finisher.luau's state)
-- Scene.step(s, w) -> (shot name, u, last)    one frame at w s into the scene
-- Scene.stop(s)                               everything it made goes; the bodies are Finisher.luau's to destroy
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")

local Data = require(script.Parent:WaitForChild("FinisherSceneData")) :: any
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Finishers = require(Shared:WaitForChild("Finishers")) :: any

local Scene = {}

-- the set's spot: far from every map, nothing else is ever there (client-only parts)
local ORIGIN = CFrame.new(0, 600, -24000)
local RIG_HIP = 3.0 -- (the plan's root height over the floor: the stock R15's hip height + half its root)
local INK = Color3.new(0.05, 0.05, 0.07)
local SMEAR = Color3.new(1, 0.95, 0.97) -- (the blade's light trail: the cut flashes bright, never a dark fan)
local PAPER = Color3.new(0.97, 0.96, 0.94)
local SAKURA = Color3.new(0.95, 0.74, 0.82)
local SAKURA2 = Color3.new(0.98, 0.86, 0.9)
local LACQUER = Color3.new(0.1, 0.07, 0.09)
local GOLD = Color3.new(0.85, 0.68, 0.32)
local R15 = { "Head", "UpperTorso", "LowerTorso", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm",
	"RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }

-- the per-scene extras: where the round win's short payoff starts (a frame), its speed, the sound cues (frame,
-- Sfx name, volume: recordings from the game's library), the shots that trail ink off the blade (trail life, s)
local EXTRA: { [string]: any } = {
	inkfall = {
		-- (Tidecrest v4.2, 20 Nov: rebuilt from the scene-by-scene review - the grip, the two-hand draw with the long blade,
		-- the whirl to his face, the sprint, the pass, the hit frame, the freeze, the sheathe's click, the cut lands, the
		-- winner close on the right as he falls behind. a round win plays the cut landing and the end)
		short = { shot = "THE CUT LANDS", speed = 1 },
		cues = { { 1, "zone_lot", 0.5 }, { 1, "zone_playground", 1 }, { 7, "loot_pop", 0.3 }, { 17, "swing", 0.6 },
			{ 53, "loot_pop", 0.6 }, { 57, "swing", 1 }, { 57, "skin_katana_sakura_swing", 0.7 }, { 86, "whoops", 0.6 },
			{ 95, "zone_playground", 0.8 }, { 130, "swing", 1 }, { 131, "skin_katana_sakura_swing", 0.8 },
			{ 140, "round_end", 0.9 }, { 198, "loot_pop", 0.9 }, { 198, "zone_vip", 0.9 },
			{ 208, "skin_katana_sakura_hit", 0.8 }, { 234, "death", 0.6 } },
		trail = { ["THE LENGTH"] = 0.15, CLOSING = 0.1, ["THE PASS"] = 0.35, ["CUT FRAME"] = 0.35 },
		dust = { ["THE CHARGE"] = true, CLOSING = true, ["THE PASS"] = true },
	},
}

-- the plan is laid out in Blender's axes (z up, the victim at the origin facing -y): a Blender offset in the stage's
-- Roblox axes
local function B(x: number, y: number, z: number): Vector3 return Vector3.new(x, z, -y) end
local function cfOf(t: { number }): CFrame return CFrame.new(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], t[12]) end
local function ease(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end

local function part(parent: Instance, size: Vector3, cf: CFrame, col: Color3, mat: Enum.Material?, shape: Enum.PartType?): Part
	local p = Instance.new("Part")
	if shape then p.Shape = shape end
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Size = size; p.CFrame = cf; p.Color = col; p.Material = mat or Enum.Material.SmoothPlastic
	p.Parent = parent
	return p
end

-- a box from a to b (world), its length along Z, `up` turning its flat side
local function between(p: BasePart, a: Vector3, b: Vector3, w: number, h: number, up: Vector3)
	local d = b - a
	local L = d.Magnitude
	if L < 1e-3 then p.Size = Vector3.new(w, h, 0.01); return end
	local z = -d.Unit
	local x = up:Cross(z)
	if x.Magnitude < 1e-4 then x = Vector3.xAxis:Cross(z) end
	x = x.Unit
	local y = z:Cross(x)
	p.Size = Vector3.new(w, h, L)
	p.CFrame = CFrame.fromMatrix((a + b) / 2, x, y, z)
end

function Scene.can(row: any, kind: string, kg: any, vg: any): boolean
	if not row or type(row.scene) ~= "string" or not Data[row.scene] then return false end
	if kind ~= "full" and kind ~= "short" then return false end
	for _, g in { kg, vg } do
		if not g or not g.model or not g.model:FindFirstChild("LowerTorso") or not g.hum then return false end
		if not (g.hum :: Humanoid):FindFirstChildOfClass("Animator") then return false end
	end
	return true
end

-- ------------------------------------------------------------------ the bodies
local function takeBody(g: any)
	g.model:SetAttribute("TPWeapon", nil)
	if g.run then pcall(function() g.run:Stop(0) end) end
	if g.idle then pcall(function() g.idle:Stop(0) end) end
	-- (a beat later, as the victim's hand-off does: ThirdPerson drops the gun it drew when TPWeapon goes, then lets go)
	task.delay(0.05, function() if g.model.Parent then CollectionService:RemoveTag(g.model, "TPRig") end end)
	local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator") :: Animator
	for _, tr in an:GetPlayingAnimationTracks() do tr:Stop(0) end
	g.root.Anchored = true
end

local function trackFor(sc: any, who: string, g: any, ci: number): AnimationTrack?
	sc.tracks[who] = sc.tracks[who] or {}
	local have = sc.tracks[who][ci]
	if have then return have end
	local clip = sc.d.clips[ci]
	local id = Finishers.SCENE_ANIMS[clip]
	if not id then return nil end
	local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator")
	if not an then return nil end
	local a = Instance.new("Animation")
	a.AnimationId = "rbxassetid://" .. id
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(a) end)
	if not ok or not tr then return nil end
	tr.Looped = false
	tr.Priority = Enum.AnimationPriority.Action4
	sc.tracks[who][ci] = tr
	return tr
end

-- this frame's pose: the clip at its moment (paused; the moment set each frame), the root where the plan stands it
local function poseBody(sc: any, who: string, g: any, ci: number, t: number, root: CFrame)
	local tr = trackFor(sc, who, g, ci)
	if sc.cur[who] ~= ci then
		local old = sc.cur[who] and sc.tracks[who] and sc.tracks[who][sc.cur[who]]
		if old then old:Stop(0) end
		if tr then tr:Play(0, 1, 0) end
		sc.cur[who] = ci
	end
	if tr then
		local L = tr.Length
		tr.TimePosition = if L > 0 then math.clamp(t, 0, L - 1 / 60) else t
	end
	g.root.CFrame = ORIGIN * root + Vector3.new(0, sc.hip[who] - RIG_HIP, 0)
end

-- the victim comes apart: anchored copies of their body parts drift off as the original (hidden) keeps its pose
local function piecesFor(sc: any, g: any)
	if sc.pieces then return sc.pieces end
	local out = {}
	local rnd = Random.new(11)
	for _, n in R15 do
		local p = g.model:FindFirstChild(n)
		if p and p:IsA("BasePart") then
			local c = p:Clone()
			for _, d in c:GetDescendants() do
				if d:IsA("JointInstance") or d:IsA("Constraint") or d:IsA("Attachment") or d:IsA("BaseScript") then d:Destroy() end
			end
			c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false
			c.Parent = sc.folder
			local dir = Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.2, 1), rnd:NextNumber(-1, 1)).Unit
			table.insert(out, { src = p, copy = c, dir = dir * rnd:NextNumber(0.4, 1), rot = Vector3.new(rnd:NextNumber(-40, 40), rnd:NextNumber(-40, 40), rnd:NextNumber(-40, 40)) })
		end
	end
	for _, d in g.model:GetDescendants() do
		if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = 1 end
	end
	sc.pieces = out
	return out
end

-- ------------------------------------------------------------------ the katana, its sheath, the trail
local function katanaKit(sc: any, skin: string?)
	local skins = ReplicatedStorage:FindFirstChild("JankfireSkins")
	local tpl = skins and (skins:FindFirstChild(skin or "") or skins:FindFirstChild("katana_sakura"))
	sc.kat = {}
	if tpl then
		local k = tpl:Clone()
		-- (the skin's real blade tip, the front-most corner along -Z: the long-blade stretch lands THIS tip on the
		-- plan's -(0.6 + 2.3 L); taking every skin's tip as -2.9 left the sakura blade ~4 studs short at THE TIP)
		local tipZ = math.huge
		for _, p in k:GetDescendants() do
			if p:IsA("BasePart") then
				local oc = p.CFrame
				for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
					local z = (oc * Vector3.new(sx * p.Size.X / 2, sy * p.Size.Y / 2, sz * p.Size.Z / 2)).Z * 3
					if z < tipZ then tipZ = z end
				end end end
				p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
				p.Size *= 3
				table.insert(sc.kat, { p = p, rel = CFrame.new(oc.Position * 3) * oc.Rotation, size = p.Size, L = 1 })
			elseif p:IsA("BaseScript") or p:IsA("JointInstance") or p:IsA("Constraint") then
				p:Destroy()
			end
		end
		k.Parent = sc.folder
		sc.katModel = k
		sc.katTip = if tipZ < -1 and tipZ > -10 then tipZ else -2.9
	end
	-- the blade's trail: off a carrier that rides the blade (guard to tip, local -Z)
	local carrier = part(sc.folder, Vector3.new(0.1, 0.1, 0.1), ORIGIN, INK)
	carrier.Transparency = 1
	local a0 = Instance.new("Attachment"); a0.Position = Vector3.new(0, 0, -0.6); a0.Parent = carrier
	local a1 = Instance.new("Attachment"); a1.Position = Vector3.new(0, 0, -2.9); a1.Parent = carrier
	local tr = Instance.new("Trail")
	tr.Attachment0 = a0; tr.Attachment1 = a1
	tr.Color = ColorSequence.new(SMEAR)
	tr.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.7, 0.4), NumberSequenceKeypoint.new(1, 1) })
	tr.LightEmission = 0.6; tr.LightInfluence = 0; tr.FaceCamera = false; tr.MinLength = 0
	tr.Lifetime = 0.12; tr.Enabled = false
	tr.Parent = carrier
	sc.carrier, sc.trail, sc.tipA = carrier, tr, a1
	-- the scabbard at the left hip (the killer's LowerTorso: the mouth forward and up, running back and down)
	sc.sheath = { part(sc.folder, Vector3.one, ORIGIN, LACQUER), part(sc.folder, Vector3.one, ORIGIN, SAKURA), part(sc.folder, Vector3.one, ORIGIN, GOLD) }
end

local function placeKit(sc: any, f: any, kg: any)
	local lt = kg.model:FindFirstChild("LowerTorso") :: BasePart?
	local hand = kg.model:FindFirstChild("RightHand") :: BasePart?
	if lt then
		local a, b = lt.CFrame * Vector3.new(-0.95, 0.1, -0.75), lt.CFrame * Vector3.new(-1.25, -1.6, 2.2)
		local d = (b - a).Unit
		local up = lt.CFrame.YVector
		between(sc.sheath[1], a, b, 0.22, 0.34, up)
		between(sc.sheath[2], a + d * 0.3, a + d * 0.5, 0.26, 0.38, up)
		between(sc.sheath[3], b - d * 0.25, b, 0.26, 0.38, up)
	end
	local grip: CFrame? = nil
	local k = f.kat
	if k and k[1] == 1 and hand then grip = hand.CFrame * CFrame.new(0, -0.12, 0)
	elseif k and k[1] == 2 and lt then grip = lt.CFrame * cfOf(k[2]) end
	local L = f.L or 1
	for _, e in sc.kat do
		e.p.LocalTransparencyModifier = if grip then 0 else 1
		if grip then
			local rel = e.rel
			if L ~= 1 and rel.Position.Z < -0.6 then
				-- (the long-blade gag: the blade stretched out along the grip's -Z from the guard)
				rel = CFrame.new(rel.Position.X, rel.Position.Y, -0.44 + (rel.Position.Z + 0.44) * L) * rel.Rotation
				if e.L ~= L then
					local ax = { math.abs(rel.XVector.Z), math.abs(rel.YVector.Z), math.abs(rel.ZVector.Z) }
					local sz = e.size
					e.p.Size = if ax[1] >= ax[2] and ax[1] >= ax[3] then Vector3.new(sz.X * L, sz.Y, sz.Z)
						elseif ax[2] >= ax[3] then Vector3.new(sz.X, sz.Y * L, sz.Z) else Vector3.new(sz.X, sz.Y, sz.Z * L)
				end
			elseif e.L ~= L then
				e.p.Size = e.size
			end
			e.L = L
			e.p.CFrame = grip * rel
		end
	end
	if grip then
		sc.carrier.CFrame = grip
		sc.tipA.Position = Vector3.new(0, 0, -(0.6 + 2.3 * L))
	end
end

-- ------------------------------------------------------------------ effects that move on their own
local function petalPool(sc: any, key: string, n: number, neon: boolean?): { Part }
	sc.pools[key] = sc.pools[key] or {}
	local pool = sc.pools[key]
	while #pool < n do
		local i = #pool
		table.insert(pool, part(sc.folder, Vector3.new(0.32, 0.04, 0.22) * 1.3, ORIGIN, if i % 4 == 0 then SAKURA2 else SAKURA,
			if neon then Enum.Material.Neon else Enum.Material.SmoothPlastic))
	end
	return pool
end

-- loose petals drifting with the scene's clock (`t`), round a centre (stage-local)
local function drift(sc: any, key: string, center: Vector3, n: number, spread: number, t: number, vel: Vector3, seed: number)
	local pool = petalPool(sc, key, n)
	local rnd = Random.new(seed)
	for i = 1, n do
		local base = center + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.6, 1), rnd:NextNumber(-1, 1)) * spread
		local ph = rnd:NextNumber(0, 6.28)
		local ax, ay, az = rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28)
		local p = base + vel * t + Vector3.new(math.sin(ph + t * 3) * 0.25, math.cos(ph + t * 2.3) * 0.12, 0)
		pool[i].CFrame = ORIGIN * CFrame.new(p) * CFrame.Angles(ax + 2.4 * t, ay + 1.7 * t, az)
	end
end

-- pieces thrown out from a point, fast at first, slowing, then falling (u 0..1); world centre
local function burst(sc: any, key: string, center: Vector3, n: number, reach: number, u: number, seed: number, splat: boolean?, size: number?)
	sc.pools[key] = sc.pools[key] or {}
	local pool = sc.pools[key]
	while #pool < n do
		if splat then
			table.insert(pool, part(sc.folder, Vector3.one * 0.2, ORIGIN, INK, Enum.Material.SmoothPlastic, Enum.PartType.Ball))
		else
			local i = #pool
			table.insert(pool, part(sc.folder, Vector3.new(0.32, 0.04, 0.22) * (size or 1.3), ORIGIN, if i % 4 == 0 then SAKURA2 else SAKURA, Enum.Material.Neon))
		end
	end
	local rnd = Random.new(seed)
	local k = 1 - (1 - math.clamp(u, 0, 1)) ^ 2.2
	for i = 1, n do
		local d = Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.3, 1), rnd:NextNumber(-1, 1)).Unit
		local r = reach * rnd:NextNumber(0.35, 1)
		local p = center + d * r * k - Vector3.new(0, 0.8 * u * u, 0)
		if splat then
			local s = 0.18 * (size or 1) * rnd:NextNumber(0.6, 1.6) * (1 - 0.5 * u)
			pool[i].Size = Vector3.one * s
			pool[i].CFrame = CFrame.new(p)
		else
			pool[i].CFrame = CFrame.new(p) * CFrame.Angles(rnd:NextNumber(0, 6.28) + 5.2 * u, rnd:NextNumber(0, 6.28) + 3.5 * u, rnd:NextNumber(0, 6.28))
		end
	end
end

-- dust kicked up where a foot strikes the floor (the crouched sprint of the owner's reference): each puff grows, drifts
-- back along the run and thins out over half a second; T = the scene's clock
local DUSTO = { { 0, 0, 0.2, 0.55 }, { 0.35, -0.25, 0.15, 0.42 }, { -0.3, -0.35, 0.28, 0.36 } }
local function dust(sc: any, g: any, T: number, kick: boolean)
	sc.dustL = sc.dustL or {}
	sc.dustLast = sc.dustLast or {}
	if kick then
		for _, f in { "LeftFoot", "RightFoot" } do
			local p = g.model:FindFirstChild(f) :: BasePart?
			if p and ORIGIN:PointToObjectSpace(p.Position).Y < 0.6 and T - (sc.dustLast[f] or -9) > 0.16 then
				sc.dustLast[f] = T
				table.insert(sc.dustL, { T, p.Position })
			end
		end
	end
	sc.pools.dust = sc.pools.dust or {}
	local pool = sc.pools.dust
	local n = 0
	for _, e in sc.dustL do
		local age = T - e[1]
		if age >= 0 and age <= 0.5 then
			local k = age / 0.5
			for _, o in DUSTO do
				n += 1
				local p = pool[n]
				if not p then
					p = part(sc.folder, Vector3.one, ORIGIN, Color3.new(0.78, 0.76, 0.74), Enum.Material.SmoothPlastic, Enum.PartType.Ball)
					pool[n] = p
				end
				local r = o[4] * (1 + 1.7 * k)
				local q = e[2] + B(o[1], o[2] - 0.9 * k, o[3] + 0.45 * k)
				p.Size = Vector3.one * r
				p.CFrame = CFrame.new(q.X, math.max(q.Y, ORIGIN.Y + r * 0.3), q.Z)
				p.Transparency = 0.3 + 0.65 * k
			end
		end
	end
	for j = n + 1, #pool do pool[j].Transparency = 1 end
end

-- the ink stroke where the swing passed: a brush of boxes from a to b, bulging, thick in the middle (world points)
local function stroke(sc: any, key: string, a: Vector3, b: Vector3, bulge: number, width: number, facing: Vector3, col: Color3, seed: number): { Part }
	local n = 16
	local d = b - a
	local side = d:Cross(facing).Unit
	local rnd = Random.new(seed)
	local pts = {}
	for i = 0, n do table.insert(pts, a + d * (i / n) + side * (bulge * math.sin(math.pi * i / n))) end
	local out = {}
	for i = 1, n do
		local t = (i - 0.5) / n
		local w = width * (math.sin(math.pi * math.min(1, t * 1.1)) ^ 0.6) * rnd:NextNumber(0.75, 1) + 0.02
		local p = part(sc.folder, Vector3.one, ORIGIN, col, if col == INK then Enum.Material.Neon else Enum.Material.SmoothPlastic)
		between(p, pts[i], pts[i + 1], 0.06, w, side)
		table.insert(out, p)
	end
	sc.pools[key] = out
	return out
end

-- the two-tone hit frame: the bodies in ink on paper, the set gone, the accent (the trail, the stroke) in the skin's pink
local function setHit(sc: any, s: any, on: boolean, accent: { Part }?, inv: boolean?)
	if sc.hitOn == on and sc.hitInv == (inv == true) and not on then return end
	if sc.hitOn == on and sc.hitInv == (inv == true) and on then return end
	sc.hitOn = on
	sc.hitInv = inv == true
	local FG, BG = if inv then PAPER else INK, if inv then INK else PAPER
	for _, d in sc.stage:GetDescendants() do if d:IsA("BasePart") then d.LocalTransparencyModifier = if on then 1 else 0 end end
	for _, pool in sc.pools do
		for _, p in pool do if p:IsA("BasePart") then p.LocalTransparencyModifier = if on and not (accent and table.find(accent, p)) then 1 else 0 end end
	end
	for _, m in { s.kg.model, s.vg.model, sc.katModel } do
		if m then
			local h = m:FindFirstChild("JankSceneHit") :: Highlight?
			if on then
				local hl = h or Instance.new("Highlight")
				hl.Name = "JankSceneHit"
				hl.FillColor = FG; hl.FillTransparency = 0
				hl.OutlineColor = BG; hl.OutlineTransparency = 0
				hl.DepthMode = Enum.HighlightDepthMode.Occluded
				hl.Parent = m
			elseif h then
				h:Destroy()
			end
		end
	end
	for _, p in sc.sheath do p.LocalTransparencyModifier = if on then 1 else 0 end
	if on then
		if not sc.backdrop then
			local b = part(sc.folder, Vector3.new(3000, 3000, 1), ORIGIN, PAPER, Enum.Material.Neon)
			sc.backdrop = b
		end
		sc.backdrop.Color = BG
		sc.backdrop.LocalTransparencyModifier = 0
		sc.trail.Color = ColorSequence.new(s.row.colour)
		for _, p in accent or {} do
			sc.orig[p] = sc.orig[p] or { p.Color, p.Material }
			p.Color = s.row.colour; p.Material = Enum.Material.Neon
		end
	else
		if sc.backdrop then sc.backdrop.LocalTransparencyModifier = 1 end
		sc.trail.Color = ColorSequence.new(SMEAR)
		for p, o in sc.orig do p.Color = o[1]; p.Material = o[2] end
		table.clear(sc.orig)
	end
end

-- ------------------------------------------------------------------ v2 (Tidecrest v4.2, 20 Nov): the plan's semantic layer
-- the scabbard in the left hand or on the hip, the blade's mode (hand / the pack's own sword track / trailing / home /
-- through the mouth / streaming out / aimed), lenses and effects riding on the real bodies, two-clip blends, afterimages,
-- each body grounded by its lowest point (the stand-in's legs aren't the player's)

local PACK_C0 = CFrame.new(0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -1, 0) -- (the pack's sword handle off the right hand)
local BODYP = { "Head", "UpperTorso", "LowerTorso", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm",
	"RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }

local function gripR(m: Model): CFrame?
	local h = m:FindFirstChild("RightHand") :: BasePart?
	if not h then return nil end
	return h.CFrame * CFrame.new(0, -0.4 * h.Size.Y, 0)
end

-- the lowest point of a body's own parts (accessories don't count), world y
local function lowestOf(m: Model): number
	local y = math.huge
	for _, n in BODYP do
		local p = m:FindFirstChild(n) :: BasePart?
		if p then
			local cf, h = p.CFrame, p.Size / 2
			for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
				y = math.min(y, (cf * Vector3.new(sx * h.X, sy * h.Y, sz * h.Z)).Y)
			end end end
		end
	end
	return y
end

-- a body's tracks: one per clip; this frame's clip at its moment, a second blended in at its weight, the rest stopped
local function trackOf(sc: any, who: string, g: any, ci: number): AnimationTrack?
	sc.tracks[who] = sc.tracks[who] or {}
	local have = sc.tracks[who][ci]
	if have then return have end
	local clip = sc.d.clips[ci]
	local id = Finishers.SCENE_ANIMS[clip]
	if not id then return nil end
	local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator")
	if not an then return nil end
	local a = Instance.new("Animation")
	a.AnimationId = "rbxassetid://" .. id
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(a) end)
	if not ok or not tr then return nil end
	tr.Looped = false
	tr.Priority = Enum.AnimationPriority.Action4
	sc.tracks[who][ci] = tr
	return tr
end

local function setTime(tr: AnimationTrack, t: number)
	local L = tr.Length
	if L > 0 then
		-- (a clip the plan loops - the run, the idle - wraps; others hold their ends)
		t = if t > L then t % L else math.clamp(t, 0, L - 1 / 60)
	end
	tr.TimePosition = t
end

local function poseV2(sc: any, who: string, g: any, e: any, ground: number?)
	local ci, t, ci2, t2, w2 = e[1], e[2], e[5], e[6], e[7]
	local want = { [ci] = if ci2 then 1 - w2 else 1 }
	if ci2 then want[ci2] = w2 end
	for c, w in want do
		local tr = trackOf(sc, who, g, c)
		if tr then
			if not tr.IsPlaying then tr:Play(0, math.max(w, 0.001), 0) else tr:AdjustWeight(math.max(w, 0.001), 0) end
			setTime(tr, if c == ci then t else t2)
		end
	end
	for c, tr in sc.tracks[who] or {} do
		if not want[c] and tr.IsPlaying then tr:Stop(0) end
	end
	local root = ORIGIN * cfOf(e[3]) + Vector3.new(0, sc.hip[who] - RIG_HIP, 0)
	-- grounding: last frame's real lowest point against the stand-in's, carried as a running offset (the pose the
	-- Animator shows is a frame behind the moment set here)
	if ground and sc.lowWas[who] then
		sc.gOff[who] = (sc.gOff[who] or 0) + (ORIGIN.Y + ground) - sc.lowWas[who]
		sc.gOff[who] = math.clamp(sc.gOff[who], -3, 3)
	end
	g.root.CFrame = root + Vector3.new(0, sc.gOff[who] or 0, 0)
end

-- the afterimages: copies of the killer, posed a moment behind, see-through
local function ghosts(sc: any, s: any, list: any)
	sc.ghosts = sc.ghosts or {}
	for gi, e in list or {} do
		local gh = sc.ghosts[gi]
		if not gh then
			local ok, m = pcall(function() return (s.kg.model :: Model):Clone() end)
			if not ok or not m then return end
			m.Name = "JankSceneGhost" .. gi
			for _, d in m:GetDescendants() do
				if d:IsA("BaseScript") then d:Destroy() elseif d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
			end
			m.Parent = sc.folder
			local hum = m:FindFirstChildOfClass("Humanoid")
			local hrp = m:FindFirstChild("HumanoidRootPart") :: BasePart?
			if not hum or not hrp then m:Destroy(); return end
			hrp.Anchored = true
			gh = { model = m, hum = hum, root = hrp }
			sc.ghosts[gi] = gh
			sc.hip["g" .. gi] = sc.hip.k
		end
		poseV2(sc, "g" .. gi, gh, e, nil)
		for _, d in gh.model:GetDescendants() do
			if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" then d.LocalTransparencyModifier = e[4]
			elseif d:IsA("Decal") then d.LocalTransparencyModifier = e[4] end
		end
		gh.model.Parent = sc.folder
	end
	for gi = #(list or {}) + 1, #sc.ghosts do sc.ghosts[gi].model.Parent = nil end
end

-- the real body point an anchor names (this frame), and the stand-in's (from the data); offsets scale by the part
local ANCH = { kH = { "k", "Head" }, kU = { "k", "UpperTorso" }, kL = { "k", "LowerTorso" }, vH = { "v", "Head" },
	vU = { "v", "UpperTorso" }, vL = { "v", "LowerTorso" } }
local function realAnchor(sc: any, s: any, key: string): (CFrame?, number)
	if key == "mouth" then return sc.mouthCF, 1 end
	local a = ANCH[key]
	if not a then return nil, 1 end
	local g = if a[1] == "k" then s.kg else s.vg
	local p = g.model:FindFirstChild(a[2]) :: BasePart?
	if not p then return nil, 1 end
	local sz = sc.d.sizes and sc.d.sizes[a[2]]
	return p.CFrame, if sz then p.Size.Y / sz[2] else 1
end
local function rehang(sc: any, s: any, f: any, key: string?, cfW: CFrame): CFrame
	if not key or key == "" or not f.an or not f.an[key] then return cfW end
	local real, k = realAnchor(sc, s, key)
	if not real then return cfW end
	local rel = (ORIGIN * cfOf(f.an[key])):Inverse() * cfW
	return real * (CFrame.new(rel.Position * k) * rel.Rotation)
end

-- the scabbard and the blade from the killer's own hands (v2 plans: f.sh / f.kat modes)
local function placeKitV2(sc: any, s: any, f: any)
	local m = s.kg.model :: Model
	local lt = m:FindFirstChild("LowerTorso") :: BasePart?
	local lh = m:FindFirstChild("LeftHand") :: BasePart?
	local rh = m:FindFirstChild("RightHand") :: BasePart?
	local g0 = gripR(m)
	sc.mouthCF = nil
	local mouth: Vector3?, d: Vector3? = nil, nil
	local sh = f.sh
	if sh and lt then
		if sh[1] == 1 and lh and g0 then
			local rp, lp = g0.Position, lh.Position
			d = (lp - rp).Unit
			mouth = lp - (d :: Vector3) * (sc.m0 or sh[2])
			if sh[3] and sh[3] ~= 0 then mouth = (mouth :: Vector3) + lt.CFrame.LookVector * sh[3] end
		else
			mouth = lt.CFrame * Vector3.new(-0.95, 0.1, -0.75)
			d = ((lt.CFrame * Vector3.new(-1.25, -1.6, 2.2)) - (mouth :: Vector3)).Unit
		end
		sc.mouthCF = CFrame.lookAt(mouth :: Vector3, (mouth :: Vector3) + (d :: Vector3))
		local up = lt.CFrame.YVector
		local a = mouth :: Vector3
		local dd = d :: Vector3
		between(sc.sheath[1], a, a + dd * 3.3, 0.22, 0.4, up)
		between(sc.sheath[2], a + dd * 0.3, a + dd * 0.5, 0.26, 0.44, up)
		between(sc.sheath[3], a + dd * 3.05, a + dd * 3.3, 0.26, 0.44, up)
		for _, p in sc.sheath do p.LocalTransparencyModifier = 0 end
	else
		for _, p in sc.sheath do p.LocalTransparencyModifier = 1 end
	end
	local k = f.kat
	local L = f.L or 1
	local grip: CFrame? = nil
	if k and g0 then
		local mode = k[1]
		if mode == 1 then
			grip = g0
		elseif (mode == 3 or mode == 8) and rh then
			grip = rh.CFrame * PACK_C0 * cfOf(k[2]) * CFrame.Angles(math.rad(90), 0, 0)
			if mode == 8 then
				-- (turned toward the victim's face, its tip a hair short of it)
				local vh = s.vg.model:FindFirstChild("Head") :: BasePart?
				local w = k[4] or 1
				if vh and grip then
					local gp = (grip :: CFrame).Position
					-- (the blade runs along the grip's -Z, i.e. its LookVector, so the look goes AT the face: the
					-- first in-game try looked away and THE TIP showed no blade)
					local want = (vh.Position - gp).Unit
					local turned = CFrame.lookAt(gp, gp + want, Vector3.yAxis)
					grip = (grip :: CFrame):Lerp(turned, w)
					L = L * (1 - w) + math.max(1, ((vh.Position - gp).Magnitude - 0.95 - 0.6) / 2.3) * w
				end
			end
		elseif mode == 4 and lt then
			local lk = lt.CFrame.LookVector
			lk = Vector3.new(lk.X, 0, lk.Z).Unit
			local dirv = (-lk * 0.93 + Vector3.new(0, -0.36, 0)).Unit
			grip = CFrame.lookAt(g0.Position, g0.Position + dirv)
		elseif mode == 5 and mouth and d then
			local gp = (mouth :: Vector3) - (d :: Vector3) * ((k[2] or 0) + 0.44)
			grip = CFrame.lookAt(gp, gp + (d :: Vector3))
			L = 1
		elseif mode == 6 and mouth and d then
			local v = (mouth :: Vector3) - g0.Position
			if v.Magnitude < 0.5 then
				local gp = (mouth :: Vector3) - (d :: Vector3) * 0.44
				grip = CFrame.lookAt(gp, gp + (d :: Vector3)); L = 1
			else
				grip = CFrame.lookAt(g0.Position, g0.Position + v.Unit)
				L = math.max(1, (v.Magnitude + 2.4) / 2.3)
			end
		elseif mode == 7 and mouth and d then
			local gp = (mouth :: Vector3) - (d :: Vector3) * (k[2] + 0.44)
			grip = CFrame.lookAt(gp, gp + (d :: Vector3))
		end
	end
	-- (a grown blade lands the skin's own tip, sc.katTip, on the plan's -(0.6 + 2.3 L); a normal one keeps the skin's
	-- length - blended over L 1..2 so the growth has no jump)
	local den = 2.46 + ((-(sc.katTip or -2.9) - 0.44) - 2.46) * math.clamp(L - 1, 0, 1)
	local Ls = (0.16 + 2.3 * L) / den
	for _, e in sc.kat do
		e.p.LocalTransparencyModifier = if grip then 0 else 1
		if grip then
			local rel = e.rel
			if Ls ~= 1 and rel.Position.Z < -0.6 then
				rel = CFrame.new(rel.Position.X, rel.Position.Y, -0.44 + (rel.Position.Z + 0.44) * Ls) * rel.Rotation
				if e.L ~= Ls then
					local ax = { math.abs(rel.XVector.Z), math.abs(rel.YVector.Z), math.abs(rel.ZVector.Z) }
					local sz = e.size
					e.p.Size = if ax[1] >= ax[2] and ax[1] >= ax[3] then Vector3.new(sz.X * Ls, sz.Y, sz.Z)
						elseif ax[2] >= ax[3] then Vector3.new(sz.X, sz.Y * Ls, sz.Z) else Vector3.new(sz.X, sz.Y, sz.Z * Ls)
				end
			elseif e.L ~= Ls then
				e.p.Size = e.size
			end
			e.L = Ls
			e.p.CFrame = (grip :: CFrame) * rel
		end
	end
	if grip then
		sc.carrier.CFrame = grip
		sc.tipA.Position = Vector3.new(0, 0, -(0.6 + 2.3 * L))
	end
end

-- effects (the plan's fx list): each drawn this frame from pooled parts; what isn't drawn this frame hides
local function fxPart(sc: any, key: string, n: number, make: () -> Part): Part
	sc.pools[key] = sc.pools[key] or {}
	local pool = sc.pools[key]
	while #pool < n do table.insert(pool, make()) end
	sc.used[key] = math.max(sc.used[key] or 0, n)
	return pool[n]
end
local function P3(sc: any, s: any, f: any, an: string?, x: number, y: number, z: number): Vector3
	return rehang(sc, s, f, an, ORIGIN * CFrame.new(x, y, z)).Position
end
local function drawFx(sc: any, s: any, f: any, T: number)
	table.clear(sc.used)
	for idx, e in f.fx or {} do
		local an, kind = e[1], e[2]
		if kind == "ring" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local fw = (P3(sc, s, f, an, e[11], e[12], e[13]) - c).Unit
			local ux = fw:Cross(Vector3.yAxis)
			ux = if ux.Magnitude > 1e-3 then ux.Unit else Vector3.xAxis
			local uy = ux:Cross(fw).Unit
			local rnd = Random.new(e[10])
			for j = 1, e[8] do
				local a = 2 * math.pi * (j - 1) / e[8] + rnd:NextNumber(-0.12, 0.12)
				local dv = ux * math.cos(a) + uy * math.sin(a)
				local p = fxPart(sc, "ring" .. idx, j, function() return part(sc.folder, Vector3.one, ORIGIN, SMEAR, Enum.Material.Neon) end)
				between(p, c + dv * e[6] * rnd:NextNumber(0.9, 1.2), c + dv * e[7] * rnd:NextNumber(0.8, 1.15), 0.02, 0.035, fw)
				p.LocalTransparencyModifier = 0
				table.insert(sc.accent, p)
			end
		elseif kind == "stroke" then
			local a = P3(sc, s, f, an, e[3], e[4], e[5])
			local b = P3(sc, s, f, an, e[6], e[7], e[8])
			local fc = (P3(sc, s, f, an, e[11], e[12], e[13]) - a).Unit
			local key = "stroke" .. idx
			local col = if e[14] == 0 then INK else s.row.colour
			local n = 16
			local dd = b - a
			local side = dd:Cross(fc).Unit
			local rnd = Random.new(e[15])
			for i = 1, n do
				local p0 = a + dd * ((i - 1) / n) + side * (e[9] * math.sin(math.pi * (i - 1) / n))
				local p1 = a + dd * (i / n) + side * (e[9] * math.sin(math.pi * i / n))
				local t = (i - 0.5) / n
				local w = e[10] * (math.sin(math.pi * math.min(1, t * 1.1)) ^ 0.6) * rnd:NextNumber(0.75, 1) + 0.02
				local p = fxPart(sc, key, i, function() return part(sc.folder, Vector3.one, ORIGIN, col, if col == INK then Enum.Material.Neon else Enum.Material.SmoothPlastic) end)
				p.Color = col
				between(p, p0, p1, 0.06, w, side)
				p.LocalTransparencyModifier = 0
				p.Transparency = e[16] or 0
				table.insert(sc.accent, p)
			end
		elseif kind == "burst" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			burst(sc, "burst" .. idx, c, e[6], e[7], e[8], e[9], e[10] == 1, e[11])
			for i = 1, e[6] do sc.pools["burst" .. idx][i].LocalTransparencyModifier = 0 end
			sc.used["burst" .. idx] = e[6]
		elseif kind == "drift" then
			local key = "drift" .. idx
			local pool = petalPool(sc, key, e[6])
			local rnd = Random.new(e[9])
			local base0 = P3(sc, s, f, an, e[3], e[4], e[5])
			local vel = Vector3.new(e[11], e[12], e[13])
			local t = e[8]
			for i = 1, e[6] do
				local bp = base0 + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.6, 1), rnd:NextNumber(-1, 1)) * e[7]
				local ph = rnd:NextNumber(0, 6.28)
				local ax, ay, az = rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28)
				local q = bp + vel * t + Vector3.new(math.sin(ph + t * 3) * 0.25, math.cos(ph + t * 2.3) * 0.12, 0)
				pool[i].CFrame = CFrame.new(q) * CFrame.Angles(ax + 2.4 * t, ay + 1.7 * t, az)
				pool[i].LocalTransparencyModifier = 0
			end
			sc.used[key] = e[6]
		elseif kind == "splats" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local rnd = Random.new(e[8])
			for i = 1, e[6] do
				local p = fxPart(sc, "splats" .. idx, i, function() return part(sc.folder, Vector3.one * 0.2, ORIGIN, INK, Enum.Material.SmoothPlastic, Enum.PartType.Ball) end)
				local q = c + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1)) * e[7]
				local sz = 0.18 * e[9] * rnd:NextNumber(0.6, 1.6)
				p.Size = Vector3.one * sz
				p.CFrame = CFrame.new(q)
				p.LocalTransparencyModifier = 0
				table.insert(sc.accent, p)
			end
		elseif kind == "glint" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local sz = math.max(0.3, e[6])
			local a1 = fxPart(sc, "glint" .. idx, 1, function() return part(sc.folder, Vector3.one, ORIGIN, PAPER, Enum.Material.Neon) end)
			local a2 = fxPart(sc, "glint" .. idx, 2, function() return part(sc.folder, Vector3.one, ORIGIN, PAPER, Enum.Material.Neon) end)
			local cam = (workspace.CurrentCamera :: Camera).CFrame
			a1.Size = Vector3.new(0.04, sz, 0.04); a1.CFrame = CFrame.lookAt(c, c + cam.LookVector)
			a2.Size = Vector3.new(sz, 0.04, 0.04); a2.CFrame = CFrame.lookAt(c, c + cam.LookVector)
			a1.LocalTransparencyModifier = 0; a2.LocalTransparencyModifier = 0
		elseif kind == "sweat" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local p = fxPart(sc, "sweat" .. idx, 1, function()
				local q = part(sc.folder, Vector3.new(0.16, 0.22, 0.16), ORIGIN, Color3.new(0.85, 0.93, 1), Enum.Material.Glass, Enum.PartType.Ball)
				q.Transparency = 0.15
				return q
			end)
			p.CFrame = CFrame.new(c)
			p.LocalTransparencyModifier = 0
		end
	end
	-- (pools not drawn this frame hide; the petals of the air and the dust keep their own)
	for key, pool in sc.pools do
		if key ~= "dust" and key ~= "air" then
			local n = sc.used[key] or 0
			for j = n + 1, #pool do pool[j].LocalTransparencyModifier = 1 end
		end
	end
end

-- ------------------------------------------------------------------ the scene
function Scene.start(s: any, kind: string): any
	local d = Data[s.row.scene]
	local ex = EXTRA[s.row.scene] or {}
	local sc: any = { d = d, ex = ex, kind = kind, i0 = 1, i1 = #d.f, speed = 1, tracks = {}, cur = {}, hip = {}, pools = {}, cued = {}, orig = {},
		shotOf = {}, shotStart = {}, lastShot = d.shots[#d.shots][1], v2 = d.sizes ~= nil, lowWas = {}, gOff = {}, used = {}, accent = {} }
	if kind == "short" and ex.short then
		local from = ex.short.from
		if ex.short.shot then
			local k0 = 0
			for _, sh in d.shots do
				if sh[1] == ex.short.shot then from = k0 + 1; break end
				k0 += sh[2]
			end
		end
		sc.i0, sc.speed = from or 1, ex.short.speed or 1
	end
	sc.total = (sc.i1 - sc.i0 + 1) / d.fps / sc.speed
	local k = 0
	for _, sh in d.shots do
		for j = 1, sh[2] do sc.shotOf[k + j] = sh[1]; sc.shotStart[k + j] = k + 1 end
		k += sh[2]
	end
	-- the set
	local folder = Instance.new("Folder")
	folder.Name = "JankFinisherStage"
	folder.Parent = workspace
	sc.folder = folder
	local stage = Instance.new("Folder")
	stage.Name = "Set"
	stage.Parent = folder
	sc.stage = stage
	sc.setParts = {}
	for _, q in d.stage do
		local okm, mat = pcall(function() return (Enum.Material :: any)[q[9]] end)
		local shape = if q[1] == "Ball" then Enum.PartType.Ball elseif q[1] == "Cylinder" then Enum.PartType.Cylinder else nil
		-- (the painted sky ring is plain paint: Neon blows out white in the game's light)
		local p = part(stage, Vector3.new(q[2], q[3], q[4]), ORIGIN * cfOf(q[5]), Color3.new(q[6], q[7], q[8]), if q[10] == "sky" then Enum.Material.SmoothPlastic elseif okm then mat else nil, shape)
		p.CastShadow = q[10] ~= "floor" and q[10] ~= "sky" -- (the painted sky ring and its lid never shade the court)
		p.Name = q[10]
		table.insert(sc.setParts, p)
	end
	-- the two of them
	takeBody(s.kg)
	takeBody(s.vg)
	for who, g in { k = s.kg, v = s.vg } do
		local hum = g.hum :: Humanoid
		sc.hip[who] = hum.HipHeight + (g.root :: BasePart).Size.Y / 2
	end
	katanaKit(sc, s.msg.skin)
	return sc
end

local function frameAt(sc: any, w: number): (number, number)
	local fi = sc.i0 + w * sc.d.fps * sc.speed
	local i = math.clamp(math.floor(fi), sc.i0, sc.i1)
	return i, math.clamp(fi - i, 0, 1)
end

function Scene.step(s: any, w: number): (string, number, boolean)
	local sc = s.scene
	local d = sc.d
	local i, a = frameAt(sc, w)
	local j = math.min(i + 1, sc.i1)
	local A, Bf = d.f[i], d.f[j]
	local same = j ~= i and sc.shotOf[i] == sc.shotOf[j]
	if not same then a = 0 end
	local shot = sc.shotOf[i]
	local s0 = sc.shotStart[i]
	local nIn = 0
	for _, sh in d.shots do if sh[1] == shot then nIn = sh[2] end end
	local li = i - s0 -- (the frame in its shot, from 0)
	local u = if nIn > 1 then math.clamp((li + a) / (nIn - 1), 0, 1) else 0
	local T = (i - 1 + a) / d.fps -- (the scene's own clock, s)
	-- the lens
	local cA = cfOf(A.c)
	local c = if same then cA:Lerp(cfOf(Bf.c), a) else cA
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = ORIGIN * c
	cam.FieldOfView = if same then A.fov + (Bf.fov - A.fov) * a else A.fov
	cam.Focus = cam.CFrame * CFrame.new(0, 0, -10)
	if sc.v2 then
		-- the lens, riding on its body point
		if A.la then cam.CFrame = rehang(sc, s, A, A.la, cam.CFrame) end
		-- the bodies (two clips blended where the plan blends, grounded), the afterimages
		for who, g in { k = s.kg, v = s.vg } do
			local fa, fb = A[who], Bf[who]
			if fa then
				local e = table.clone(fa)
				if same and fb and fb[1] == fa[1] then
					e[2] = fa[2] + (fb[2] - fa[2]) * a
					e[3] = fa[3]
				end
				poseV2(sc, who, g, e, A["g" .. who])
				if same and fb and fb[1] == fa[1] then
					g.root.CFrame = (ORIGIN * cfOf(fa[3])):Lerp(ORIGIN * cfOf(fb[3]), a) + Vector3.new(0, sc.hip[who] - RIG_HIP + (sc.gOff[who] or 0), 0)
				end
				sc.lowWas[who] = lowestOf(g.model)
			end
		end
		ghosts(sc, s, A.g)
		-- the scabbard's mouth sits where this body's own left hand holds it (measured once the grab's pose shows)
		if not sc.m0 and A.kat and A.kat[1] == 5 and A.sh and A.sh[1] == 1 and i >= sc.i0 + 2 then
			local lh = s.kg.model:FindFirstChild("LeftHand") :: BasePart?
			local g0 = gripR(s.kg.model)
			if lh and g0 then sc.m0 = math.max(0.2, (lh.Position - g0.Position).Magnitude - 0.44) end
		end
		placeKitV2(sc, s, A)
		local life = sc.ex.trail and sc.ex.trail[shot]
		sc.trail.Enabled = life ~= nil
		if life then sc.trail.Lifetime = life end
		dust(sc, s.kg, T, sc.ex.dust ~= nil and sc.ex.dust[shot] == true)
		table.clear(sc.accent)
		drawFx(sc, s, A, T)
		-- the cut one coming apart (the plan's scatter)
		local scat = A.v and A.v[4] or 0
		if scat > 0 then
			for _, pc in piecesFor(sc, s.vg) do
				local r = pc.rot * scat
				pc.copy.CFrame = CFrame.new(pc.dir * scat) * pc.src.CFrame * CFrame.Angles(math.rad(r.X), math.rad(r.Y), math.rad(r.Z))
				pc.copy.Transparency = math.clamp((scat - 0.25) / 0.25, 0, 1)
			end
		end
		local hit = A.hit ~= nil
		setHit(sc, s, hit, if hit then sc.accent else nil, A.hit == 2)
		-- (the plan clears the pillars standing in a wide lens's way - THE LENGTH's gag shot - so this frame hides the
		-- set's pieces it lists; the next frame without them shows them again)
		local hide = if hit then nil else A.hide
		if sc.hidWas ~= hide then
			for _, ix in sc.hidWas or {} do local p = sc.setParts[ix]; if p and not hit then p.LocalTransparencyModifier = 0 end end
			for _, ix in hide or {} do local p = sc.setParts[ix]; if p then p.LocalTransparencyModifier = 1 end end
			sc.hidWas = hide
		end
		if hit then
			-- (every hit frame: only the accents show - the blade's trail, the rings, the stroke - in the skin's colour)
			if sc.backdrop then sc.backdrop.CFrame = cam.CFrame * CFrame.new(0, 0, -180) end
			for _, pool in sc.pools do
				for _, p in pool do
					if table.find(sc.accent, p) then
						sc.orig[p] = sc.orig[p] or { p.Color, p.Material }
						p.Color = s.row.colour; p.Material = Enum.Material.Neon
						p.LocalTransparencyModifier = 0
					else
						p.LocalTransparencyModifier = 1
					end
				end
			end
		end
		for _, q in sc.ex.cues or {} do
			if not sc.cued[q] and i >= q[1] and q[1] >= sc.i0 then
				sc.cued[q] = true
				pcall(Sfx.play, q[2], nil, q[3])
			end
		end
		return shot, u, shot == sc.lastShot
	end
	-- the bodies
	for who, g in { k = s.kg, v = s.vg } do
		local fa, fb = A[who], Bf[who]
		if fa then
			local t = fa[2]
			local root = cfOf(fa[3])
			if same and fb and fb[1] == fa[1] then
				t += (fb[2] - fa[2]) * a
				root = root:Lerp(cfOf(fb[3]), a)
			end
			poseBody(sc, who, g, fa[1], t, root)
		end
	end
	placeKit(sc, A, s.kg)
	-- the blade's ink trail
	local life = sc.ex.trail and sc.ex.trail[shot]
	sc.trail.Enabled = life ~= nil
	if life then sc.trail.Lifetime = life end
	-- dust off the runner's feet
	dust(sc, s.kg, T, sc.ex.dust ~= nil and sc.ex.dust[shot] == true)
	-- petals on the air all through
	drift(sc, "air", B(-5, 9, 3), 10, 4, T, B(0.6, -0.3, -0.35), 401)
	local vg = s.vg
	local vHead = vg.model:FindFirstChild("Head") :: BasePart?
	local vUT = vg.model:FindFirstChild("UpperTorso") :: BasePart?
	if shot == "THE END" and vUT then
		local click = sc.ex.clickAt or 16
		if li >= click then
			if not sc.strokeAt then
				-- the cut shows across the victim's belly where the blade went through: ink with a pink edge
				local cc = vUT.Position + B(0, 0, -0.6)
				sc.strokeAt = cc
				local ink = stroke(sc, "stroke", cc + B(-2.2, -0.8, 0.55), cc + B(2.2, -0.8, -0.3), 0.25, 0.5, B(0, -1, 0), INK, 61)
				local edge = stroke(sc, "edge", cc + B(-1.9, -0.86, 0.4), cc + B(1.9, -0.86, -0.2), 0.22, 0.15, B(0, -1, 0), s.row.colour, 62)
				sc.strokeParts = table.move(edge, 1, #edge, #ink + 1, table.clone(ink))
			end
			accent = sc.strokeParts
			local fade = if li < click + 5 then 0 else math.min(0.9, (li - click - 5 + a) * 0.09)
			for _, p in sc.strokeParts do p.Transparency = fade end
			if li >= click + 2 then burst(sc, "splat", sc.strokeAt + B(0.4, -0.9, 0), 10, 2.0, (li - click - 2 + a) / 10, 71, true, 0.7) end
		end
		if li >= click + 10 then
			-- down on the ground, coming apart into petals
			if not sc.vc then sc.vc = vUT.Position end
			local uu = math.clamp((li - click - 10 + a) / math.max(1, nIn - click - 11), 0, 1)
			burst(sc, "burst", vUT.Position + B(0, 0, 0.3), 60, 2.6, uu, 421, false, 1.2)
			local scat = (A.v and A.v[4] or 0)
			if same and Bf.v then scat += ((Bf.v[4] or 0) - scat) * a end
			if scat > 0 then
				for _, pc in piecesFor(sc, vg) do
					local r = pc.rot * scat
					pc.copy.CFrame = CFrame.new(pc.dir * scat) * pc.src.CFrame * CFrame.Angles(math.rad(r.X), math.rad(r.Y), math.rad(r.Z))
					pc.copy.Transparency = math.clamp((uu - 0.6) / 0.4, 0, 1)
				end
			end
		end
	end
	-- the hit frames
	local hit = A.hit == true
	if hit and shot == "CUT FRAME" then accent = {} end
	setHit(sc, s, hit, accent)
	if hit and sc.backdrop then sc.backdrop.CFrame = cam.CFrame * CFrame.new(0, 0, -180) end
	-- the sounds, on their frames (the short payoff only hears its own)
	for _, q in sc.ex.cues or {} do
		if not sc.cued[q] and i >= q[1] and q[1] >= sc.i0 then
			sc.cued[q] = true
			pcall(Sfx.play, q[2], nil, q[3])
		end
	end
	return shot, u, shot == sc.lastShot
end

function Scene.hitNow(s: any): boolean
	return s.scene ~= nil and s.scene.hitOn == true
end

function Scene.stop(s: any)
	local sc = s.scene
	if not sc then return end
	s.scene = nil
	for _, set in sc.tracks do for _, tr in set do pcall(function() tr:Stop(0) end) end end
	if sc.folder then sc.folder:Destroy() end
	for _, g in { s.kg, s.vg } do
		if g and g.model then
			local h = g.model:FindFirstChild("JankSceneHit")
			if h then h:Destroy() end
		end
	end
end

return Scene
