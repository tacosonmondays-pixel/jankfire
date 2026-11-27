--!strict
-- FINISHER PRO EFFECTS (26 Nov 2026): Tidecrest's ink and petals over the pro animator's take, on his frames (the brief
-- to him: finisher-boards/tidecrest_vfx_brief_for_animator.md - a manga cut: glints, a ring of action lines, the long
-- blade's arc, speed lines, dust, ink afterimages, two-tone ink frames, the ink stroke where the cut lands, petals; no
-- blood, nothing baked). FinisherPro.step calls Fx.step every frame; everything here is client-only parts in the
-- scene's folder, pooled, gone with it.
-- Fx.step(sc, s, fi, w, dt, katCF, L)   fi = the take's frame on screen (fractional), w = the scene's seconds
local Players = game:GetService("Players")

local Fx = {}

local INK = Color3.fromRGB(14, 13, 18)
local PAPER = Color3.fromRGB(246, 243, 236)
local SAKURA = Color3.fromRGB(242, 189, 208)
local SAKURA2 = Color3.fromRGB(250, 220, 230)
local GOLD = Color3.fromRGB(255, 226, 160)
local WHITE = Color3.fromRGB(255, 252, 246)
local GZ = -0.62

local function part(sc: any, size: Vector3, col: Color3, mat: Enum.Material?, shape: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Size = size; p.Color = col; p.Material = mat or Enum.Material.SmoothPlastic
	if shape then p.Shape = shape end
	p.CFrame = CFrame.new(0, -1e4, 0)
	p.Parent = sc.folder
	return p
end
-- a named pool of parts made on first use; parts not used this frame are hidden by Fx.step's sweep
local function pool(sc: any, key: string, n: number, make: () -> Part): { Part }
	sc.fxp = sc.fxp or {}
	local p = sc.fxp[key]
	if not p then p = {}; sc.fxp[key] = p end
	while #p < n do table.insert(p, make()) end
	return p
end
local function show(sc: any, p: Part, cf: CFrame, tr: number?)
	p.CFrame = cf
	p.Transparency = tr or 0
	sc.fxUsed[p] = true
end
local function smooth(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end
local function env(fi: number, a: number, b: number): number
	-- (0 outside [a, b], up fast, down slow: a flash's life)
	if fi < a or fi > b then return 0 end
	local u = (fi - a) / (b - a)
	return math.sin(math.pi * math.min(1, u * 1.6)) * (1 - u * 0.4)
end

-- a four-point glint (two crossed slivers, turned to the lens)
local function glint(sc: any, key: string, at: Vector3, size: number, col: Color3?)
	local ps = pool(sc, "glint" .. key, 2, function() return part(sc, Vector3.one, col or WHITE, Enum.Material.Neon) end)
	local cam = (workspace.CurrentCamera :: Camera).CFrame
	local base = CFrame.lookAt(at, at + cam.LookVector) * CFrame.Angles(0, 0, math.rad(20))
	ps[1].Size = Vector3.new(size * 0.07, size, 0.02)
	ps[2].Size = Vector3.new(size * 0.6, size * 0.06, 0.02)
	show(sc, ps[1], base)
	show(sc, ps[2], base)
end

-- action lines: ink strokes bursting out from a point across the lens's plane (u 0..1)
local function burstLines(sc: any, key: string, at: Vector3, u: number, n: number, reach: number, col: Color3)
	local ps = pool(sc, "lines" .. key, n, function() return part(sc, Vector3.one, col) end)
	local cam = (workspace.CurrentCamera :: Camera).CFrame
	local rnd = Random.new(#key * 31 + n)
	for i = 1, n do
		local a = (i / n) * math.pi * 2 + rnd:NextNumber(-0.2, 0.2)
		local dir = cam.RightVector * math.cos(a) + cam.UpVector * math.sin(a)
		local r0 = reach * (0.25 + 0.75 * smooth(u)) * rnd:NextNumber(0.7, 1.1)
		local len = reach * 0.45 * (1 - u) * rnd:NextNumber(0.6, 1.2) + 0.02
		local c = at + dir * (r0 + len / 2) + cam.LookVector * -0.05
		local p = ps[i]
		p.Color = col
		p.Size = Vector3.new(0.035 * reach, len, 0.01)
		show(sc, p, CFrame.lookAt(c, c - cam.LookVector, dir), u * 0.6)
	end
end

-- petals: a pool of small pink chips
-- (round 2, the judge: the end's petals read as "small orange squares ... embers" - now round, pink, lit from inside so
-- the lanterns' warm light can't turn them orange, and two and a half times as big)
local PETAL = Color3.fromRGB(255, 176, 200)
local PETAL2 = Color3.fromRGB(255, 208, 222)
local function petals(sc: any, key: string, n: number, size: number?): { Part }
	return pool(sc, "petal" .. key, n, function()
		local s = size or 0.75
		local p = part(sc, Vector3.new(0.04, s, s * 0.78), if math.random() < 0.35 then PETAL2 else PETAL, Enum.Material.Neon, Enum.PartType.Cylinder)
		p.Transparency = 1
		return p
	end)
end
-- (no petal right at the lens: one 2 studs off it fills the frame as a pale slab)
local function nearLens(p: Vector3): boolean
	return ((workspace.CurrentCamera :: Camera).CFrame.Position - p).Magnitude < 4
end
local function driftPetals(sc: any, key: string, center: Vector3, n: number, spread: number, t: number, vel: Vector3, seed: number, fade: number?)
	local ps = petals(sc, key, n)
	local rnd = Random.new(seed)
	for i = 1, n do
		local base = center + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.5, 1), rnd:NextNumber(-1, 1)) * spread
		local ph = rnd:NextNumber(0, 6.28)
		local p = base + vel * t * rnd:NextNumber(0.7, 1.2) + Vector3.new(math.sin(ph + t * 2.6) * 0.35, math.sin(ph * 2 + t * 1.9) * 0.15, math.cos(ph + t * 2.1) * 0.25)
		if not nearLens(p) then show(sc, ps[i], CFrame.new(p) * CFrame.Angles(ph + t * 1.6, ph * 0.7 + t * 1.1, t * 0.7), fade) end
	end
end

-- the long blade's trail: a carrier riding the blade (guard to tip), its Trail on while asked
local function trail(sc: any, katCF: CFrame, L: number, on: boolean, life: number, col: Color3)
	if not sc.trail then
		local c = part(sc, Vector3.new(0.1, 0.1, 0.1), INK)
		c.Transparency = 1
		local a0 = Instance.new("Attachment"); a0.Parent = c
		local a1 = Instance.new("Attachment"); a1.Parent = c
		local t = Instance.new("Trail")
		t.Attachment0, t.Attachment1 = a0, a1
		t.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(0.6, 0.55), NumberSequenceKeypoint.new(1, 1) })
		t.LightEmission = 0.5; t.LightInfluence = 0.2; t.FaceCamera = false; t.MinLength = 0; t.Enabled = false
		t.Parent = c
		sc.trail = { c = c, a0 = a0, a1 = a1, t = t }
	end
	local tr = sc.trail
	tr.c.CFrame = katCF
	tr.a0.Position = Vector3.new(0, 0, GZ - 0.2)
	tr.a1.Position = Vector3.new(0, 0.181 * L, GZ + (-3.84 - GZ) * L)
	tr.t.Lifetime = life
	tr.t.Color = ColorSequence.new(col)
	tr.t.Enabled = on
end

-- 2D speed lines over the frame (the run): thin streaks sliding across, the run's way
local function speedLines(sc: any, k: number, dir: number, w: number)
	if not sc.lines2d then
		local g = Instance.new("ScreenGui")
		g.Name = "JankProSpeed"; g.IgnoreGuiInset = true; g.DisplayOrder = 40; g.ResetOnSpawn = false
		g.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
		local list = {}
		local rnd = Random.new(5)
		for i = 1, 26 do
			local f = Instance.new("Frame")
			f.BorderSizePixel = 0; f.BackgroundColor3 = WHITE; f.AnchorPoint = Vector2.new(0.5, 0.5)
			f.Parent = g
			table.insert(list, { f = f, y = rnd:NextNumber(0.06, 0.94), len = rnd:NextNumber(0.12, 0.38), sp = rnd:NextNumber(1.6, 3.2), ph = rnd:NextNumber(0, 1), th = rnd:NextInteger(1, 3) })
		end
		sc.lines2d = { g = g, list = list }
		table.insert(sc.made, g)
	end
	for _, e in sc.lines2d.list do
		local x = ((e.ph + w * e.sp) % 1.4) - 0.2
		if dir < 0 then x = 1 - x end
		e.f.Position = UDim2.fromScale(x, e.y)
		e.f.Size = UDim2.new(e.len, 0, 0, e.th)
		-- (thinner toward the middle of the frame, where the action is)
		local mid = 1 - math.abs(e.y - 0.5) * 2
		e.f.BackgroundTransparency = 1 - k * (0.55 - 0.4 * mid)
	end
end

-- dust: a soft puff where a foot plants (the run), pale on the night stone
local function dust(sc: any, g: any, w: number, on: boolean)
	sc.dustL = sc.dustL or {}
	sc.dustT = sc.dustT or {}
	local floorY = sc.floorY
	if on then
		for _, fn in { "LeftFoot", "RightFoot" } do
			local p = g.model:FindFirstChild(fn) :: BasePart?
			if p then
				local low = p.Position.Y - p.Size.Y * 0.5 - floorY
				local key = g.model.Name .. fn
				if low < 0.25 and w - (sc.dustT[key] or -9) > 0.22 then
					sc.dustT[key] = w
					table.insert(sc.dustL, { w, Vector3.new(p.Position.X, floorY, p.Position.Z) })
				end
			end
		end
	end
	local ps = pool(sc, "dust", 18, function() return part(sc, Vector3.one, Color3.fromRGB(176, 186, 206), Enum.Material.SmoothPlastic, Enum.PartType.Ball) end)
	local n = 0
	for i = #sc.dustL, 1, -1 do
		local e = sc.dustL[i]
		local age = w - e[1]
		if age > 0.6 then table.remove(sc.dustL, i); continue end
		for k = 1, 3 do
			n += 1
			if n > #ps then break end
			local u = age / 0.6
			local r = (0.35 + 0.15 * k) * (1 + 1.6 * u)
			local off = Vector3.new(math.cos(k * 2.1), 0, math.sin(k * 2.1)) * (0.3 + 0.6 * u)
			ps[n].Size = Vector3.one * r
			show(sc, ps[n], CFrame.new(e[2] + off + Vector3.new(0, r * 0.3, 0)), 0.45 + 0.55 * u)
		end
	end
end

-- the two-tone ink frame: the bodies flat ink on paper (or the inverse), the set and its effects gone, a backdrop behind
local function twoTone(sc: any, s: any, on: boolean, inv: boolean)
	local was = sc.hitOn == true
	if was == on and (not on or sc.hitInv == inv) then return end
	sc.hitOn, sc.hitInv = on, inv
	local FG, BG = if inv then PAPER else INK, if inv then INK else PAPER
	if sc.set then
		for _, d in sc.set:GetDescendants() do
			if d:IsA("BasePart") then d.LocalTransparencyModifier = if on then 1 else 0
			elseif d:IsA("Beam") or d:IsA("ParticleEmitter") then (d :: any).Enabled = not on end
		end
	end
	for _, m in { s.kg.model, s.vg.model, sc.katModel, sc.sheathModel } do
		if m then
			local h = m:FindFirstChild("JankProInk") :: Highlight?
			if on then
				local hl = h or Instance.new("Highlight")
				hl.Name = "JankProInk"; hl.FillColor = FG; hl.FillTransparency = 0; hl.OutlineColor = BG; hl.OutlineTransparency = 0
				hl.DepthMode = Enum.HighlightDepthMode.Occluded
				hl.Parent = m
			elseif h then
				h:Destroy()
			end
		end
	end
	if not sc.backdrop then
		sc.backdrop = part(sc, Vector3.new(4000, 4000, 1), PAPER, Enum.Material.Neon)
	end
	local cam = (workspace.CurrentCamera :: Camera).CFrame
	sc.backdrop.Color = BG
	sc.backdrop.CFrame = if on then cam * CFrame.new(0, 0, -900) else CFrame.new(0, -1e4, 0)
	local L = game:GetService("Lighting")
	for _, e in L:GetChildren() do
		if e:IsA("Atmosphere") and e.Name == "SceneAtmo" then
			if on then sc.atmoD = sc.atmoD or e.Density; e.Density = 0 elseif sc.atmoD then e.Density = sc.atmoD end
		end
	end
end

-- the ink stroke where the cut lands: a brush of segments across the belly in the swing's way, drawn in (u 0..1),
-- thick in the middle, then fading (fade 0..1)
local function stroke(sc: any, a: Vector3, b: Vector3, bulge: number, width: number, facing: Vector3, u: number, fade: number)
	local n = 18
	local ps = pool(sc, "stroke", n, function() return part(sc, Vector3.one, INK, Enum.Material.SmoothPlastic) end)
	local d = b - a
	local side = d:Cross(facing)
	side = if side.Magnitude > 1e-4 then side.Unit else Vector3.yAxis
	local rnd = Random.new(7)
	local drawn = math.floor(n * smooth(u) + 0.5)
	for i = 1, n do
		local t0, t1 = (i - 1) / n, i / n
		local p0 = a + d * t0 + side * (bulge * math.sin(math.pi * t0))
		local p1 = a + d * t1 + side * (bulge * math.sin(math.pi * t1))
		local wdt = width * (math.sin(math.pi * math.min(1, (t0 + t1) / 2 * 1.08)) ^ 0.6) * rnd:NextNumber(0.75, 1) + 0.03
		if i <= drawn then
			local mid, len = (p0 + p1) / 2, (p1 - p0).Magnitude
			ps[i].Size = Vector3.new(wdt, 0.05, len + 0.06)
			show(sc, ps[i], CFrame.lookAt(mid, p1, facing), fade)
		end
	end
end
local function splats(sc: any, at: Vector3, u: number, fade: number)
	local ps = pool(sc, "splat", 14, function() return part(sc, Vector3.one, INK, Enum.Material.SmoothPlastic, Enum.PartType.Ball) end)
	local rnd = Random.new(23)
	local k = 1 - (1 - math.clamp(u, 0, 1)) ^ 2.4
	for i = 1, #ps do
		local dir = Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.4, 1), rnd:NextNumber(-1, 1)).Unit
		local r = rnd:NextNumber(0.8, 2.2) * k
		local sz = rnd:NextNumber(0.08, 0.24) * (1 - 0.4 * u)
		ps[i].Size = Vector3.one * sz
		show(sc, ps[i], CFrame.new(at + dir * r - Vector3.new(0, 0.6 * u * u, 0)), fade)
	end
end

-- the victim comes apart into petals: his parts thin away, petals rise off where each one was
local BODY = { "Head", "UpperTorso", "LowerTorso", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm",
	"RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }
local function comeApart(sc: any, s: any, u: number, w: number)
	local vm = s.vg.model
	if not sc.apartFrom then
		sc.apartFrom = {}
		for _, n in BODY do
			local p = vm:FindFirstChild(n)
			if p and p:IsA("BasePart") then table.insert(sc.apartFrom, p.Position) end
		end
	end
	for _, d in vm:GetDescendants() do
		if d:IsA("BasePart") or d:IsA("Decal") then (d :: any).LocalTransparencyModifier = smooth(u * 1.3) end
	end
	local per = 4
	local ps = petals(sc, "apart", #sc.apartFrom * per)
	local rnd = Random.new(41)
	local wind = Vector3.new(0.9, 0.8, 0.5)
	for i, at in sc.apartFrom do
		for k = 1, per do
			local idx = (i - 1) * per + k
			local start = rnd:NextNumber(0, 0.45)
			local t = math.max(0, u - start) * 1.8
			local ph = rnd:NextNumber(0, 6.28)
			local p = at + Vector3.new(rnd:NextNumber(-0.4, 0.4), rnd:NextNumber(-0.3, 0.3), rnd:NextNumber(-0.4, 0.4))
				+ wind * t * rnd:NextNumber(0.6, 1.3) + Vector3.new(math.sin(ph + t * 3) * 0.4, 0, math.cos(ph + t * 2.4) * 0.3)
			if u > start and not nearLens(p) then
				show(sc, ps[idx], CFrame.new(p) * CFrame.Angles(ph + t * 2, ph + t * 1.4, t * 0.7), math.clamp((u - 0.75) * 4, 0, 1))
			end
		end
	end
end

-- the frames, his numbering (24 fps); fi is the frame on screen
function Fx.step(sc: any, s: any, fi: number, w: number, dt: number, katCF: CFrame, L: number)
	sc.fxUsed = {}
	sc.floorY = sc.floorY or 600 -- (FinisherPro sets the floor's height)
	local tip = katCF * Vector3.new(0, 0.181 * L, GZ + (-3.84 - GZ) * L)
	local guard = katCF * Vector3.new(0, 0, GZ)
	local vH = s.vg.model:FindFirstChild("Head") :: BasePart?
	local vU = s.vg.model:FindFirstChild("UpperTorso") :: BasePart?
	local vL = s.vg.model:FindFirstChild("LowerTorso") :: BasePart?
	-- 1 THE GRIP: a glint in the gap as the guard eases out, then the ring of action lines and the kick
	if fi >= 8.5 and fi < 10.8 and sc.mouthW then glint(sc, "grip", sc.mouthW + Vector3.new(0, 0.15, 0), 0.9 * env(fi, 8.5, 10.8) + 0.05) end
	if fi >= 10.5 and fi < 14 and sc.mouthW then burstLines(sc, "ring", sc.mouthW, (fi - 10.5) / 3.5, 18, 1.6, INK) end
	-- 2 THE DRAW: a glint running down the blade at the full stretch, a spark as the tip comes free
	if fi >= 40 and fi < 54 then
		local u = (fi - 40) / 14
		glint(sc, "draw", guard:Lerp(tip, 0.15 + 0.8 * u), 0.55 + 0.25 * math.sin(math.pi * u))
	end
	if fi >= 54 and fi < 57 then glint(sc, "pop", tip, 1.4 * env(fi, 54, 57) + 0.05, GOLD) end
	-- 3 THE LENGTH: the giant blade's arc (a pale trail), a dust puff as he settles into guard
	-- 7 THE PASS: the smear following the blade (the skin's pink), ink afterimages below
	local trOn, life, col = false, 0.2, WHITE
	if fi >= 56 and fi < 66 then trOn, life, col = true, 0.28, Color3.fromRGB(236, 240, 255) end
	if fi >= 130 and fi < 139 then trOn, life, col = true, 0.5, SAKURA end
	trail(sc, katCF, L, trOn, life, col)
	-- 4 THE TIP: a glint where the tip stops at his nose; the sweat bead (High Noon's teardrop) at his temple
	if fi >= 85 and fi < 89 then glint(sc, "tip", tip, 0.7 * env(fi, 85, 89) + 0.05) end
	if fi >= 84 and fi < 94 and vH then
		local ps = pool(sc, "sweat", 1, function()
			local sets = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireFinisherSets")
			local src = sets and sets:FindFirstChild("SweatDrop")
			local q: any = if src and src:IsA("MeshPart") then src:Clone() else part(sc, Vector3.new(0.12, 0.17, 0.12), WHITE, Enum.Material.Glass, Enum.PartType.Ball)
			q.Anchored = true; q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.CastShadow = false
			q.Color = Color3.fromRGB(206, 232, 255); q.Material = Enum.Material.Glass; q.Reflectance = 0.2
			q.Parent = sc.folder
			return q
		end)
		local u = (fi - 84) / 10
		local hs = vH.Size
		local c = vH.CFrame * Vector3.new(hs.X * 0.42, hs.Y * (0.18 - 0.3 * smooth(u)), -hs.Z * 0.3)
		local cam = (workspace.CurrentCamera :: Camera).CFrame
		ps[1].Size = Vector3.new(0.13, 0.18, 0.13)
		show(sc, ps[1], CFrame.lookAt(c, c + Vector3.new(cam.LookVector.X, 0, cam.LookVector.Z) * -1), 0.15)
	end
	-- 5 THE CHARGE, 6 CLOSING: speed lines across the frame, stronger on the last strides; dust on the footfalls
	local slk = 0
	if fi >= 94 and fi < 116 then slk = 0.55 * smooth((fi - 94) / 4) end
	if fi >= 116 and fi < 130 then slk = 0.95 end
	if fi >= 130 and fi < 139 then slk = 0.5 end
	if sc.lines2d or slk > 0 then speedLines(sc, slk, 1, w) end
	if sc.lines2d then sc.lines2d.g.Enabled = slk > 0 end
	dust(sc, s.kg, w, (fi >= 68 and fi < 74) or (fi >= 94 and fi < 139))
	dust(sc, s.vg, w, fi >= 100 and fi < 139)
	-- 7 THE PASS: two ink afterimages of the killer, a moment behind
	if fi >= 131 and fi < 139 then
		Fx.afterimages(sc, s, fi)
	elseif sc.ghosts then
		for _, gh in sc.ghosts do gh.model.Parent = nil end
	end
	-- 8 CUT FRAME: two-tone ink frames (the inverse on its 2nd and 5th), action lines out of the contact on its 3rd-4th;
	-- 12 THE CUT LANDS: two-tone for its first 2 frames
	local hit, inv = false, false
	if fi >= 139 and fi < 145 then
		hit = true
		local k = math.floor(fi - 139)
		inv = k == 1 or k == 4
		if k == 2 or k == 3 then
			local ctr = if vL then vL.Position:Lerp(guard, 0.5) else guard
			burstLines(sc, "hit", ctr, (fi - 141) / 2, 22, 3.2, if inv then PAPER else INK)
		end
	end
	if fi >= 207 and fi < 209 then hit = true end
	twoTone(sc, s, hit, inv)
	-- 9 PAST HIM: a few petals drifting through; 10 STILLNESS: one petal crossing his face
	if fi >= 145 and fi < 181 and vH then
		local t = (fi - 145) / 24
		driftPetals(sc, "past", vH.Position + Vector3.new(-1.5, 0.5, -2), 7, 2.4, t, Vector3.new(0.9, -0.35, 0.6), 3)
	end
	if fi >= 163 and fi < 181 and vH then
		local u = (fi - 163) / 18
		local ps = petals(sc, "face", 1, 0.32)
		local cam = (workspace.CurrentCamera :: Camera).CFrame
		local c = vH.Position + cam.RightVector * (1.3 - 2.6 * u) + Vector3.new(0, 0.35 - 0.5 * u + 0.08 * math.sin(u * 9), 0) - cam.LookVector * 0.25
		show(sc, ps[1], CFrame.new(c) * CFrame.Angles(u * 5, u * 3.5, u * 2))
	end
	-- 11 HOME: a glint on the click
	if fi >= 203.5 and fi < 206.5 and sc.mouthW then glint(sc, "click", sc.mouthW + Vector3.new(0, 0.2, 0), 0.9 * env(fi, 203.5, 206.5) + 0.05, GOLD) end
	-- 12 THE CUT LANDS: the ink stroke wipes across his belly in the swing's way, splats burst off it, then it fades
	if fi >= 208 and fi < 221 and vL and vU then
		local u = math.clamp((fi - 208) / 4, 0, 1)
		local fade = math.clamp((fi - 215) / 6, 0, 1)
		local belly = vL.Position:Lerp(vU.Position, 0.45)
		local right = vL.CFrame.RightVector
		local front = -vL.CFrame.LookVector
		local cam = (workspace.CurrentCamera :: Camera).CFrame
		stroke(sc, belly - right * 1.6 + front * 0.62 + Vector3.new(0, 0.25, 0), belly + right * 1.6 + front * 0.62 - Vector3.new(0, 0.2, 0), 0.25, 0.42,
			-cam.LookVector, u, fade)
		if fi >= 209.5 then splats(sc, belly + front * 0.6, (fi - 209.5) / 8, fade) end
	end
	-- the moon's road on the water: the set's thin glint streaks, each flickering on its own beat
	if sc.set and not sc.streaks then
		sc.streaks = {}
		for _, d in sc.set:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "MoonStreak" then table.insert(sc.streaks, { p = d, ph = (#sc.streaks * 1.7) % 6.28, sp = 2.5 + (#sc.streaks % 5) * 0.9, base = d.Transparency }) end
		end
	end
	if not sc.hitOn then
		for _, e in sc.streaks or {} do
			e.p.Transparency = math.clamp(e.base + 0.35 * math.sin(w * e.sp + e.ph), 0, 1)
		end
	end
	-- 13 THE END: he comes apart into petals that drift away
	if fi >= 226 then comeApart(sc, s, math.clamp((fi - 226) / 24, 0, 1), w) end
	-- (every pooled part not used this frame: out of sight)
	for _, list in sc.fxp or {} do
		for _, p in list do
			if not sc.fxUsed[p] and p.Transparency < 1 then p.Transparency = 1 end
		end
	end
end

-- the pass's ink afterimages: copies of the killer, posed a step behind him (their own Animator on the same take)
function Fx.afterimages(sc: any, s: any, fi: number)
	if not sc.ghosts then
		sc.ghosts = {}
		local was = s.kg.model.Archivable
		s.kg.model.Archivable = true
		for k = 1, 2 do
			local ok, m = pcall(function() return s.kg.model:Clone() end)
			if ok and m then
				m.Name = "JankProGhost" .. k
				for _, d in m:GetDescendants() do
					if d:IsA("BaseScript") or d:IsA("Highlight") then d:Destroy()
					elseif d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false end
				end
				local hum = m:FindFirstChildOfClass("Humanoid")
				local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
				local an = hum and hum:FindFirstChildOfClass("Animator")
				if hum and root and an then
					root.Anchored = true
					for _, tr in an:GetPlayingAnimationTracks() do tr:Stop(0) end
					local a = Instance.new("Animation"); a.AnimationId = "rbxassetid://" .. sc.d.anims.k
					local tr = an:LoadAnimation(a); tr.Looped = false; tr.Priority = Enum.AnimationPriority.Action4; tr:Play(0, 1, 0)
					-- (round 2: "pale grey-green ghosts ... motion blur, not ink" - solid ink, the further one fainter)
					local hl = Instance.new("Highlight"); hl.FillColor = Color3.fromRGB(20, 20, 30); hl.OutlineColor = Color3.fromRGB(20, 20, 30)
					hl.FillTransparency = 0; hl.OutlineTransparency = 1; hl.DepthMode = Enum.HighlightDepthMode.Occluded; hl.Parent = m
					for _, d in m:GetDescendants() do if d:IsA("BasePart") or d:IsA("Decal") then (d :: any).LocalTransparencyModifier = 0.15 + 0.3 * k end end
					table.insert(sc.ghosts, { model = m, tr = tr, root = root, lag = 1.6 * k })
				else
					m:Destroy()
				end
			end
		end
		s.kg.model.Archivable = was
	end
	for _, gh in sc.ghosts do
		gh.model.Parent = sc.folder
		gh.root.CFrame = s.kg.root.CFrame
		local L = gh.tr.Length
		local T = math.max(0, fi - gh.lag) / 24
		gh.tr.TimePosition = if L > 0 then math.clamp(T, 0, L - 1 / 60) else T
	end
end

return Fx
