-- finisher VIDEO frames on REAL AVATARS (Edit only, far off the map, workspace.FinisherRealTemp): shared.FinReal(key)
-- poses the killer and victim avatars with the real mocap clips (Animator + StepAnimations), rebuilds the scabbard,
-- katana, holsters and revolvers from each body's OWN hands and hips (the frame data says what they are doing, not where
-- the stand-in's were), moves close lenses and body-bound effects onto the real parts, and sets the camera.
-- Placeholders: __IDS__ (frame data modules), __PACK2__ (the iai clip pack), __VICTIM__ (a user id, or nil = grey body).
local HS = game:GetService("HttpService")
local Players = game:GetService("Players")
local KSP = game:GetService("KeyframeSequenceProvider")
local INS = game:GetService("InsertService")
local IDS = { __IDS__ }
local PACKS = { 117991134964298, __PACK2__ }
local USERS = { k = 2833796200, v = __VICTIM__ }
local OFF = CFrame.new(-9000, 800, -9000)
local HATS = false          -- the cowboy hat props of the stand-ins (off: the avatars keep their own looks)
-- where each avatar's eyes sit against the stand-in's, in head space (studs; tuned by look on the eye close-ups:
-- the owner's anime head carries its eyes 0.43 lower, a classic head matches)
local EYE_DY = { k = __EYE_K__, v = __EYE_V__ }
local STAND_H = 3.0         -- the stand-in's HRP height at rest (the plan's roots are for it)

shared.FinVid = shared.FinVid or {}
for _, id in ipairs(IDS) do
	if not shared.FinVid["_loaded_" .. id] then
		local c = INS:LoadAsset(id)
		local ms = c:FindFirstChildWhichIsA("ModuleScript", true)
		local t = HS:JSONDecode(string.match(ms.Source, "%[==%[(.*)%]==%]"))
		for k, v in pairs(t) do shared.FinVid[k] = v end
		shared.FinVid["_loaded_" .. id] = true
		c:Destroy()
	end
end
local function C(t) return OFF * CFrame.new(table.unpack(t)) end
local function col(t) return Color3.new(t[1], t[2], t[3]) end
local GREY = Color3.fromRGB(160, 160, 166)
local LACQ, PINK, GOLD, LEATHER = Color3.fromRGB(70, 40, 52), Color3.fromRGB(242, 189, 209), Color3.fromRGB(214, 170, 82), Color3.fromRGB(107, 69, 41)
local KAT = game.ReplicatedStorage.JankfireSkins.katana_sakura
local TPL = game.ServerStorage.PolishBackup.AnimTrial.Rig

local R = shared.FinRealState or {}
shared.FinRealState = R
local root = workspace:FindFirstChild("FinisherRealTemp")
if not root then root = Instance.new("Folder"); root.Name = "FinisherRealTemp"; root.Parent = workspace end

-- clips: every keyframe sequence in the packs, by name
if not R.clips then
	R.clips = {}
	for _, id in ipairs(PACKS) do
		local c = INS:LoadAsset(id)
		for _, ks in ipairs(c:GetDescendants()) do
			if ks:IsA("KeyframeSequence") and not R.clips[ks.Name] then R.clips[ks.Name] = KSP:RegisterKeyframeSequence(ks) end
		end
		c:Destroy()
	end
end

local function makeBody(uid)
	local desc
	if uid then
		desc = Players:GetHumanoidDescriptionFromUserId(uid)
	else
		desc = Instance.new("HumanoidDescription")
		desc.HeadColor, desc.TorsoColor = GREY, GREY
		desc.LeftArmColor, desc.RightArmColor, desc.LeftLegColor, desc.RightLegColor = GREY, GREY, GREY, GREY
	end
	local m = Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
	m.HumanoidRootPart.Anchored = true
	m.HumanoidRootPart.Transparency = 1
	for _, d in ipairs(m:GetDescendants()) do
		if d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
	end
	return m
end
local function restH(m)
	local hum = m:FindFirstChildOfClass("Humanoid")
	return hum.HipHeight + m.HumanoidRootPart.Size.Y / 2
end
local function pose(m, clip, t, clip2, t2, w2)
	-- one clip at a moment, or two blended (the plan's clip2 at weight w2)
	local hum = m:FindFirstChildOfClass("Humanoid")
	local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
	for _, old in ipairs(an:GetPlayingAnimationTracks()) do old:Stop(0); old:Destroy() end
	local function play(c, tt, w)
		local id = R.clips[c]
		if not id or w <= 0.001 then return end
		local a = Instance.new("Animation"); a.AnimationId = id
		local tr = an:LoadAnimation(a)
		tr:Play(0, w, 0)
		tr.TimePosition = tt
	end
	if not R.clips[clip] then return false end
	if clip2 and w2 then
		play(clip, t, 1 - w2)
		play(clip2, t2, w2)
	else
		play(clip, t, 1)
	end
	an:StepAnimations(0)
	return true
end
local function place(m, rootCF)
	m:PivotTo(rootCF * CFrame.new(0, restH(m) - STAND_H, 0))
end
local function gripR(m) local h = m.RightHand; return h.CFrame * CFrame.new(0, -0.4 * h.Size.Y, 0) end

if not R.av then
	R.av = { k = makeBody(USERS.k), v = makeBody(USERS.v) }
	R.av.k.Name, R.av.v.Name = "real_k", "real_v"
	-- the scabbard's mouth sits this far from the left hand (toward the hilt), measured on THIS body at the iai grab
	R.av.k.Parent = root
	place(R.av.k, OFF * CFrame.new(0, STAND_H, 0))
	pose(R.av.k, "mb_iai_draw", 0.1)
	R.m0 = math.max(0.2, (R.av.k.LeftHand.Position - gripR(R.av.k).Position).Magnitude - 0.44)
end
local function ghost(name)
	if not R.av[name] then
		local g = R.av.k:Clone(); g.Name = "real_" .. name
		R.av[name] = g
	end
	return R.av[name]
end
local function setTr(m, tr)
	for _, d in ipairs(m:GetDescendants()) do
		if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" then d.Transparency = tr
		elseif d:IsA("Decal") then d.Transparency = tr end
	end
end

-- the hips (for the hip-hung scabbard and the holster), as the body-fit test settled them
local function hips(m)
	local lt = m.LowerTorso
	local hw, hd = lt.Size.X / 2, lt.Size.Z / 2
	local lh = lt:FindFirstChild("LeftHipRigAttachment")
	if lh and lh:IsA("Attachment") then hw = math.max(hw, math.abs(lh.Position.X) + 0.45) end
	for _, d in ipairs(m:GetDescendants()) do if d:IsA("WrapLayer") then hw *= 1.12; hd *= 1.18; break end end
	local leg = m:FindFirstChildOfClass("Humanoid").HipHeight / 2
	return lt, hw, hd, leg
end
local function hipSheath(m)
	local lt, hw, hd, leg = hips(m)
	local mouth = lt.CFrame * Vector3.new(-hw * 0.95, 0.1, -(hd + 0.25))
	local tip = lt.CFrame * Vector3.new(-hw * 1.25, -1.6 * leg, hd * 4.4)
	return mouth, (tip - mouth).Unit
end
local function holsterCF(m)
	local lt, hw, hd, leg = hips(m)
	return lt.CFrame * CFrame.new(hw * 1.12, -0.45 * leg, -0.05), lt, hw, hd
end

local SIZES = {}
for _, p in ipairs(TPL:GetChildren()) do if p:IsA("BasePart") then SIZES[p.Name] = p.Size end end
local function standin(f, rig, part)
	for _, r in ipairs(f.rigs) do if r.name == rig and r.parts[part] then return C(r.parts[part]) end end
	return nil
end
-- a world CFrame of the plan, re-hung from the stand-in's anchor onto the real one (offsets scaled by the part's size)
local function reanchor(cfW, f, anchor)
	if anchor == "mouth" then
		if not (f.sem and f.sem.mouth and R.mouthReal) then return cfW end
		return R.mouthReal * (C(f.sem.mouth):Inverse() * cfW)
	end
	local rig, part = string.match(anchor, "^(%w+)%.(%w+)$")
	local s = rig and standin(f, rig, part)
	local m = rig and R.av[rig]
	local p = m and m:FindFirstChild(part)
	if not (s and p and SIZES[part]) then return cfW end
	local rel = s:Inverse() * cfW
	local k = p.Size.Y / SIZES[part].Y
	local pc = p.CFrame
	if part == "Head" then pc = pc * CFrame.new(0, EYE_DY[rig] or 0, 0) end
	return pc * (CFrame.new(rel.Position * k) * rel.Rotation)
end
-- the owner (20 Nov): the real bodies sank into the ground (their legs aren't the stand-in's). After posing, each real
-- body is lifted or lowered so its lowest body point sits exactly where the stand-in's did (standing or lying)
local BODY = { "Head", "UpperTorso", "LowerTorso", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm",
	"RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }
local function lowCorner(cf, half)
	local y = math.huge
	for _, sx in ipairs({ -1, 1 }) do for _, sy in ipairs({ -1, 1 }) do for _, sz in ipairs({ -1, 1 }) do
		y = math.min(y, (cf * Vector3.new(sx * half.X, sy * half.Y, sz * half.Z)).Y)
	end end end
	return y
end
local function lowestReal(m)
	local y = math.huge
	for _, n in ipairs(BODY) do
		local p = m:FindFirstChild(n)
		if p and p:IsA("BasePart") then y = math.min(y, lowCorner(p.CFrame, p.Size / 2)) end
	end
	return y
end
local function lowestStandin(f, rig)
	for _, r in ipairs(f.rigs) do
		if r.name == rig then
			local y = math.huge
			for n, t in pairs(r.parts) do
				if SIZES[n] and n ~= "HumanoidRootPart" then y = math.min(y, lowCorner(C(t), SIZES[n] / 2)) end
			end
			return y
		end
	end
	return nil
end
local function ground(m, f, rig)
	local want = lowestStandin(f, rig)
	if not want or want == math.huge then return end
	local dy = want - lowestReal(m)
	if math.abs(dy) > 1e-3 then m:PivotTo(m:GetPivot() + Vector3.new(0, dy, 0)) end
end
local SKIP = { sheath = true, holster = true, belt = true }
local REANCHOR = { glint = "mouth", sweat = "v.Head", stroke = "v.UpperTorso", stroke_edge = "v.UpperTorso",
	splat = "v.UpperTorso", shock = "v.UpperTorso", flash = "k.RightHand", gsmear = "k.RightHand", smoke = "k.RightHand",
	hat = nil }
local STRIP = { Weld = true, WeldConstraint = true, Motor6D = true, AnimationConstraint = true, BallSocketConstraint = true, RigidConstraint = true, NoCollisionConstraint = true }
local function clean(m)
	for _, d in ipairs(m:GetDescendants()) do
		if STRIP[d.ClassName] or d:IsA("BaseScript") then d:Destroy()
		elseif d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
	end
end

shared.FinReal = function(key)
	local data = shared.FinVid
	local f = data[key]
	if not f then return "no frame " .. key end
	local sem = f.sem or {}
	for _, ch in ipairs(root:GetChildren()) do
		if not string.match(ch.Name, "^real_") then ch:Destroy() end
	end
	-- 1. the bodies: the killer and victim (and the killer's afterimages) on their roots, posed from the clips
	local used = {}
	for name, a in pairs(f.anim or {}) do
		local m = R.av[name]
		if m then
			m.Parent = root
			place(m, C(a.root))
			pose(m, a.clip, a.t, a.clip2, a.t2, a.w2)
			ground(m, f, name)
			setTr(m, math.min(1, (a.sc or 0) * 1.4))
			used[name] = true
		end
	end
	for name, a in pairs(f.ghost or {}) do
		local m = ghost(name)
		m.Parent = root
		place(m, C(a.root))
		pose(m, a.clip, a.t)
		ground(m, f, name)
		setTr(m, a.tr)
		used[name] = true
	end
	for name, m in pairs(R.av) do if not used[name] then m.Parent = nil end end
	for name, face in pairs(f.faces or {}) do
		local m = R.av[name]
		local fc = m and m:FindFirstChild("Head") and m.Head:FindFirstChildOfClass("FaceControls")
		if fc then for k, v in pairs(face) do pcall(function() fc[k] = v end) end end
	end

	local kit = Instance.new("Model"); kit.Name = "kit"; kit.Parent = root
	local function part(size, cf, c, mat)
		local p = Instance.new("Part")
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Size = size; p.CFrame = cf; p.Color = c; p.Material = mat or Enum.Material.SmoothPlastic
		p.Parent = kit
		return p
	end
	local function between(a, b, w, h, c)
		return part(Vector3.new(w, h, (b - a).Magnitude), CFrame.lookAt((a + b) / 2, b), c)
	end
	local function placeKit(tplm, grip, scale, name, tr, L)
		local k = tplm:Clone(); k.Name = name
		clean(k)
		-- (stretched so the tip lands at the plan's tipz = -(0.6 + 2.3 L): the skin's tip at -2.9 maps to it)
		local Ls = L and (0.16 + 2.3 * L) / 2.46
		for _, p in ipairs(k:GetDescendants()) do
			if p:IsA("BasePart") then
				local oc = p.CFrame
				p.Size = p.Size * scale
				local rel = CFrame.new(oc.Position * scale) * oc.Rotation
				if Ls and Ls ~= 1 and rel.Position.Z < -0.6 then
					local L = Ls
					local pz = -0.44 + (rel.Position.Z + 0.44) * L
					rel = CFrame.new(rel.Position.X, rel.Position.Y, pz) * oc.Rotation
					local ax = { math.abs(rel.XVector.Z), math.abs(rel.YVector.Z), math.abs(rel.ZVector.Z) }
					local sz = p.Size
					if ax[1] >= ax[2] and ax[1] >= ax[3] then p.Size = Vector3.new(sz.X * L, sz.Y, sz.Z)
					elseif ax[2] >= ax[3] then p.Size = Vector3.new(sz.X, sz.Y * L, sz.Z)
					else p.Size = Vector3.new(sz.X, sz.Y, sz.Z * L) end
				end
				p.CFrame = grip * rel
				if tr then p.Transparency = math.max(p.Transparency, tr) end
			end
		end
		k.Parent = kit
		return k
	end

	-- 2. the scabbard and the katana, from the killer's own hands
	local K = R.av.k
	R.mouthReal = nil
	local mouth, d
	if sem.sh and used.k then
		if sem.sh.mode == "lhand" then
			local rp, lp = gripR(K).Position, K.LeftHand.Position
			d = (lp - rp).Unit
			mouth = lp - d * R.m0
			if sem.sh.fwd then mouth += K.LowerTorso.CFrame.LookVector * sem.sh.fwd end
		else
			mouth, d = hipSheath(K)
		end
		R.mouthReal = CFrame.lookAt(mouth, mouth + d)
		between(mouth, mouth + d * 3.3, 0.22, 0.4, LACQ)
		between(mouth + d * 0.3, mouth + d * 0.5, 0.26, 0.44, PINK)
		between(mouth + d * 3.05, mouth + d * 3.3, 0.26, 0.44, GOLD)
	end
	local kat = sem.kat
	if kat and used.k then
		if kat.mode == "hand" then
			placeKit(KAT, gripR(K), 3, "katana", nil, f.katL)
		elseif kat.mode == "pack" then
			-- the bought pack's own sword track: the handle hangs off the right hand (C0 = -90 deg about X), our blade
			-- runs along its +Y
			local C0 = CFrame.new(0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -1, 0)
			placeKit(KAT, K.RightHand.CFrame * C0 * CFrame.new(table.unpack(kat.T)) * CFrame.Angles(math.rad(90), 0, 0), 3, "katana", nil, f.katL)
		elseif kat.mode == "trail" then
			local g = gripR(K).Position
			local lk = K.LowerTorso.CFrame.LookVector
			lk = Vector3.new(lk.X, 0, lk.Z).Unit
			local dirv = (-lk * 0.93 + Vector3.new(0, -0.36, 0)).Unit
			placeKit(KAT, CFrame.lookAt(g, g + dirv), 3, "katana", nil, f.katL)
		elseif mouth and kat.mode == "home" then
			local g = mouth - d * ((kat.push or 0) + 0.44)
			placeKit(KAT, CFrame.lookAt(g, g + d), 3, "katana", nil, 1)
		elseif mouth and kat.mode == "out" then
			local g = mouth - d * (kat.e + 0.44)
			local gcf = CFrame.lookAt(g, g + d)
			placeKit(KAT, gcf, 3, "katana", nil, f.katL)
			if kat.glints then
				for j = 0, 39 do
					local x = 0.7 + j * 0.85
					local o = kat.e - x
					if o >= 0.05 and o <= 4.5 then
						local p = part(Vector3.new(0.1, 0.28, 0.07), gcf * CFrame.new(0, 0, -(0.44 + x)), Color3.new(1, 0.97, 0.95), Enum.Material.Neon)
						p.Name = "glint"
					end
				end
			end
		elseif mouth and kat.mode == "through" then
			local rp = gripR(K).Position
			local v = mouth - rp
			if v.Magnitude < 0.5 then
				local g = mouth - d * 0.44
				placeKit(KAT, CFrame.lookAt(g, g + d), 3, "katana", nil, 1)
			else
				placeKit(KAT, CFrame.lookAt(rp, rp + v.Unit), 3, "katana", nil, math.max(1, (v.Magnitude + 2.4) / 2.3))
			end
		end
	end
	-- 3. holsters and revolvers, from each body's own hips and hand
	for name, state in pairs(sem.hol or {}) do
		local m = R.av[name]
		if m and used[name] then
			local hcf, lt, hw, hd = holsterCF(m)
			part(Vector3.new(0.32, 0.95, 0.55), hcf, LEATHER, Enum.Material.Leather)
			part(Vector3.new(2 * hw * 1.06, 0.28, 2 * hd * 1.1), lt.CFrame * CFrame.new(0, 0.05, 0), LEATHER, Enum.Material.Leather)
			if state == "in" then
				placeKit(game.ReplicatedStorage.JankfireSkins.revolver_dust, hcf * CFrame.new(0, 0.15, 0) * CFrame.Angles(math.rad(-90), 0, 0) * CFrame.new(0, 0, -0.1), 3, "gun")
			end
		end
	end
	for name, state in pairs(sem.gun or {}) do
		local m = R.av[name]
		if m and used[name] and state == "hand" then
			local g = m.RightHand.CFrame * CFrame.new(0, -0.1, 0) * CFrame.Angles(math.rad(-90), 0, 0) * CFrame.new(0, 0.55, -0.25)
			placeKit(game.ReplicatedStorage.JankfireSkins.revolver_dust, g, 3, "gun")
		end
	end
	for _, g in ipairs(f.guns or {}) do
		if g.tr then placeKit(game.ReplicatedStorage.JankfireSkins[g.model], C(g.cf), 3, "gun", g.tr) end
	end

	-- 4. the stage and the effects (body-bound ones moved onto the real parts)
	local stage = Instance.new("Folder"); stage.Name = "stage"
	local accent, accM = {}, nil
	for _, a in ipairs(f.impact and f.impact.accent or {}) do accent[a] = true end
	local function addProp(q)
		if SKIP[q.tag] or (q.tag == "hat" and not HATS) then return end
		local p = Instance.new("Part")
		if q.shape == "Ball" then p.Shape = Enum.PartType.Ball elseif q.shape == "Cylinder" then p.Shape = Enum.PartType.Cylinder end
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = q.tag ~= "petal" and q.tag ~= "sky"
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Size = Vector3.new(q.size[1], q.size[2], q.size[3])
		local cf = C(q.cf)
		if REANCHOR[q.tag] then cf = reanchor(cf, f, REANCHOR[q.tag]) end
		p.CFrame = cf
		p.Color = col(q.col)
		local okm, mat = pcall(function() return Enum.Material[q.mat] end)
		p.Material = okm and mat or Enum.Material.SmoothPlastic
		if q.tag == "sky" then p.Material = Enum.Material.SmoothPlastic end   -- (Neon blows out white in the place's light)
		p.Name = q.tag
		p.Transparency = q.tr or 0
		local into = stage
		if f.impact then
			if accent[q.tag] then
				p.Color = col(f.impact.accent_col); p.Material = Enum.Material.SmoothPlastic; p.Transparency = 0
				if not accM then
					accM = Instance.new("Model"); accM.Name = "accent"
					local h = Instance.new("Highlight"); h.FillColor = col(f.impact.accent_col); h.FillTransparency = 0
					h.OutlineTransparency = 1; h.DepthMode = Enum.HighlightDepthMode.Occluded; h.Parent = accM
				end
				into = accM
			else p.Transparency = 1 end
		end
		p.Parent = into
	end
	local stg = (f.stage == true and data._stage) or (type(f.stage) == "string" and data[f.stage]) or nil
	if stg then for _, q in ipairs(stg.props) do addProp(q) end end
	for _, q in ipairs(f.props) do addProp(q) end
	stage.Parent = root
	if accM then accM.Parent = root end
	if f.impact then
		for name in pairs(used) do
			-- (the two-tone frame: one Highlight per body, kept on it and switched off on normal frames)
			local hb = R.av[name]:FindFirstChild("fin_hl") or Instance.new("Highlight")
			hb.Name = "fin_hl"; hb.FillColor = col(f.impact.fg); hb.FillTransparency = 0; hb.OutlineColor = col(f.impact.bg)
			hb.OutlineTransparency = 0; hb.DepthMode = Enum.HighlightDepthMode.Occluded; hb.Enabled = true; hb.Parent = R.av[name]
		end
		local hk = Instance.new("Highlight"); hk.FillColor = col(f.impact.fg); hk.FillTransparency = 0
		hk.OutlineColor = col(f.impact.bg); hk.OutlineTransparency = 0; hk.Parent = kit
	else
		for _, m in pairs(R.av) do local hb = m:FindFirstChild("fin_hl"); if hb then hb.Enabled = false end end
	end

	-- 5. the lens: close ones follow their anchor on the real body
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Scriptable
	local lcf = C(f.lens.cf)
	if sem.lens then lcf = reanchor(lcf, f, sem.lens) end
	cam.CFrame = lcf
	local vs = cam.ViewportSize
	local kk = math.max(1, vs.Y / (vs.X * 9 / 16))
	cam.FieldOfView = math.deg(2 * math.atan(math.tan(math.rad(f.lens.fov / 2)) * kk))
	if f.impact then
		local b = Instance.new("Part"); b.Name = "backdrop"; b.Anchored = true; b.CanCollide = false; b.CanQuery = false
		b.Size = Vector3.new(3000, 3000, 1); b.Material = Enum.Material.Neon; b.Color = col(f.impact.bg)
		b.CFrame = cam.CFrame * CFrame.new(0, 0, -180); b.Parent = root
	end
	return "ok " .. key .. " " .. f.name
end
return shared.FinReal("__FIRST__")
