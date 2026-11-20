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
-- the shoot's light (20 Nov, the owner: "make it a western town now add lighting shadows make it pretty"): a low warm
-- sun with real shadows, a warm haze, a light grade. The place's own Lighting is saved first and put back by
-- shared.FinRealRestore() at the end of the turn - the place's look never changes
local LOOK = __LOOK__
local function lookOn()
	if not LOOK or R.lightWas then return end
	local L = game:GetService("Lighting")
	local was = { props = {}, added = {} }
	for _, k in ipairs({ "ClockTime", "GeographicLatitude", "Brightness", "OutdoorAmbient", "Ambient", "ColorShift_Top",
		"ColorShift_Bottom", "EnvironmentDiffuseScale", "EnvironmentSpecularScale", "ShadowSoftness", "ExposureCompensation",
		"GlobalShadows" }) do
		was.props[k] = L[k]
	end
	was.disabled = {}
	for _, e in ipairs(L:GetChildren()) do
		if (e:IsA("PostEffect") or e:IsA("Atmosphere")) then
			if e:IsA("Atmosphere") then was.atmo = { e, e.Density, e.Offset, e.Color, e.Decay, e.Glare, e.Haze }
			elseif e.Enabled then e.Enabled = false; table.insert(was.disabled, e) end
		end
	end
	R.lightWas = was
	L.ClockTime = LOOK.clock; L.GeographicLatitude = LOOK.lat; L.Brightness = LOOK.bright
	L.OutdoorAmbient = LOOK.outdoor; L.Ambient = LOOK.ambient; L.ColorShift_Top = LOOK.shiftTop
	L.ColorShift_Bottom = Color3.new(0, 0, 0); L.EnvironmentDiffuseScale = 0.45; L.EnvironmentSpecularScale = 0.4
	L.ShadowSoftness = 0.15; L.ExposureCompensation = LOOK.exposure; L.GlobalShadows = true
	local a = was.atmo and was.atmo[1]
	if not a then a = Instance.new("Atmosphere"); a.Name = "JankShootAtmo"; a.Parent = L; table.insert(was.added, a) end
	a.Density = 0.3; a.Offset = 0.12; a.Color = Color3.fromRGB(222, 176, 134); a.Decay = Color3.fromRGB(176, 118, 92)
	a.Glare = 0.35; a.Haze = 1.4
	local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "JankShootGrade"
	cc.TintColor = Color3.fromRGB(255, 238, 220); cc.Contrast = 0.08; cc.Saturation = 0.04; cc.Parent = L
	table.insert(was.added, cc)
end
shared.FinRealRestore = function()
	local was = R.lightWas
	if not was then return "no light to restore" end
	local L = game:GetService("Lighting")
	for k, v in pairs(was.props) do L[k] = v end
	if was.atmo then
		local a = was.atmo[1]; a.Density, a.Offset, a.Color, a.Decay, a.Glare, a.Haze = was.atmo[2], was.atmo[3], was.atmo[4], was.atmo[5], was.atmo[6], was.atmo[7]
	end
	for _, e in ipairs(was.disabled) do e.Enabled = true end
	for _, e in ipairs(was.added) do e:Destroy() end
	R.lightWas = nil
	return "light restored"
end
lookOn()
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
	local pc = if part == "RightHand" and R.handCF and R.handCF[m] then R.handCF[m] else p.CFrame
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
-- the revolver (the owner, 20 Nov: "the gun isn't held in her hand ... it sort of snaps off their waist"): in the hand
-- its own Grip attachment sits in the palm at the plan's hold angle; at rest it sits in the holster on the hip, grip
-- up, and the hand reaches onto it (reach below) and carries it out
local REV = game.ReplicatedStorage.JankfireSkins.revolver_dust
local function gunGripRel(): Vector3
	if R.gunGrip then return R.gunGrip end
	local att = REV:FindFirstChild("Grip", true)
	R.gunGrip = if att and att:IsA("Attachment") then att.WorldPosition * 3 else Vector3.new(0, -0.55, 0.25)
	return R.gunGrip
end
local function handCF(m)
	-- the right hand as the reach left it this frame (its joints are set, the part may not have moved yet)
	return (R.handCF and R.handCF[m]) or m.RightHand.CFrame
end
local function palm(m)
	local h = m.RightHand
	return handCF(m) * CFrame.new(0, -0.4 * h.Size.Y, 0)
end
local function gunInHand(m)
	local pc = palm(m)
	return CFrame.new(pc.Position) * pc.Rotation * CFrame.Angles(math.rad(-90), 0, 0) * CFrame.new(-gunGripRel())
end
-- the reach (the owner, 20 Nov: "Holsters were fine before, just make the hand reach closer to the gun and pull the
-- gun!"): the draw clip's hand passes a hand's length off THIS body's holster, so the right arm is bent onto the gun -
-- a two-bone reach laid over the clip's own pose (the clip still moves the body; only the arm is pulled to the gun):
-- the hand hovers just over the grip while it waits, closes on the grip at the grab, then eases back into the clip as
-- the gun comes out with it (the plan's re-holster plays the draw backwards, so it gets the same reach in reverse)
local function inHolster(m)
	local hcf = holsterCF(m)
	return hcf * CFrame.new(0, 0.15, 0) * CFrame.Angles(math.rad(-90), 0, 0) * CFrame.new(0, 0, -0.1)
end
local function handOnGrip(m)
	-- the RightHand CFrame that puts the palm on the holstered gun's grip (gunInHand turned inside out)
	local pc = inHolster(m) * CFrame.new(gunGripRel()) * CFrame.Angles(math.rad(90), 0, 0)
	return pc * CFrame.new(0, 0.4 * m.RightHand.Size.Y, 0)
end
local function sm(x) x = math.clamp(x, 0, 1); return x * x * (3 - 2 * x) end
-- clip times: hover reached by `hover`, hover -> grip over grip0..grip1, on the grip until out0 (the plan hands the gun
-- over between 0.30 and 0.35), back into the clip by out1
local REACH = { quick_draw_t1 = { hover = 0.12, grip0 = 0.14, grip1 = 0.28, out0 = 0.34, out1 = 0.54 } }
local HOVER = Vector3.new(0.12, 0, -0.04) -- the hover's sideways part (lower-torso axes): out, a touch forward
local function turn(v1, v2)
	local ax = v1:Cross(v2)
	if ax.Magnitude < 1e-6 then return CFrame.identity end
	return CFrame.fromAxisAngle(ax.Unit, math.acos(math.clamp(v1:Dot(v2), -1, 1)))
end
local function jframes(j)
	-- a joint's two frames (Part1 = Part0 * f0 * Transform * f1:Inverse()): Motor6D C0/C1, or (the layered avatars'
	-- rigs) an AnimationConstraint's two attachments
	if j:IsA("Motor6D") then return j.C0, j.C1, j.Part0 end
	if j:IsA("AnimationConstraint") and j.Attachment0 and j.Attachment1 then
		return j.Attachment0.CFrame, j.Attachment1.CFrame, j.Attachment0.Parent
	end
	return nil
end
local function armTo(m, Hd)
	-- bend the right arm (shoulder, elbow, wrist joints) so the hand lands on Hd, the elbow keeping the clip's side
	local UA, LA, H = m:FindFirstChild("RightUpperArm"), m:FindFirstChild("RightLowerArm"), m:FindFirstChild("RightHand")
	local sh = UA and UA:FindFirstChild("RightShoulder")
	local el = LA and LA:FindFirstChild("RightElbow")
	local wr = H and H:FindFirstChild("RightWrist")
	if not (sh and el and wr) then return nil end
	local s0, s1, sp0 = jframes(sh)
	local e0, e1 = jframes(el)
	local w0, w1 = jframes(wr)
	if not (s0 and e0 and w0 and sp0) then return nil end
	local P0, UAc, LAc = sp0.CFrame, UA.CFrame, LA.CFrame
	local S = (UAc * s1).Position
	local E = (UAc * e0).Position
	local a = (e0.Position - s1.Position).Magnitude
	local b = (w0.Position - e1.Position).Magnitude
	local dv = (Hd * w1).Position - S
	if a < 1e-3 or b < 1e-3 or dv.Magnitude < 1e-3 then return nil end
	local u = dv.Unit
	local d = math.clamp(dv.Magnitude, math.abs(a - b) + 1e-3, a + b - 1e-3)
	local pv = (E - S) - u * (E - S):Dot(u)
	if pv.Magnitude < 1e-3 then local back = -P0.LookVector; pv = back - u * back:Dot(u) end
	pv = pv.Unit
	local ca = math.clamp((a * a + d * d - b * b) / (2 * a * d), -1, 1)
	local E2 = S + u * (a * ca) + pv * (a * math.sqrt(1 - ca * ca))
	local r1 = CFrame.new(S) * turn((E - S).Unit, (E2 - S).Unit) * CFrame.new(-S)
	local UA2, LA1 = r1 * UAc, r1 * LAc
	local W1 = (LA1 * w0).Position
	local r2 = CFrame.new(E2) * turn((W1 - E2).Unit, ((S + u * d) - E2).Unit) * CFrame.new(-E2)
	local LA2 = r2 * LA1
	local Wj = (LA2 * w0).Position
	local H2 = CFrame.new(Wj - Hd.Rotation * w1.Position) * Hd.Rotation
	-- (a joint's Transform set by hand does nothing in Edit on these rigs - the Animator owns it - so for this frame the
	-- three arm joints are let go and the arm's parts are set where the reach puts them; unreach() joins them again
	-- before the next pose)
	R.armOff = R.armOff or {}
	R.armOff[m] = { joints = { sh, el, wr }, parts = { UA, LA, H } }
	sh.Enabled, el.Enabled, wr.Enabled = false, false, false
	UA.Anchored, LA.Anchored, H.Anchored = true, true, true
	UA.CFrame, LA.CFrame, H.CFrame = UA2, LA2, H2
	return H2
end
local function unreach(m)
	local off = R.armOff and R.armOff[m]
	if not off then return end
	for _, p in ipairs(off.parts) do p.Anchored = false end
	for _, j in ipairs(off.joints) do j.Enabled = true end
	R.armOff[m] = nil
end
local function reach(m, a)
	local rc = a and REACH[a.clip]
	if not rc or a.clip2 or not m:FindFirstChild("RightHand") then return end
	local t = a.t
	local w = sm(t / rc.hover) * (1 - sm((t - rc.out0) / (rc.out1 - rc.out0)))
	if w < 0.002 then return end
	local grip = handOnGrip(m)
	-- (hovering a fifth of the way from the grip up toward the shoulder, a touch out: bodies differ a lot - a short
	-- one's holster sits nearly at shoulder height, so a fixed lift sent her hand up behind her)
	local ua = m:FindFirstChild("RightUpperArm")
	local up = ua and (ua.Position - grip.Position) * 0.2 or Vector3.zero
	local hover = CFrame.new(up + m.LowerTorso.CFrame:VectorToWorldSpace(HOVER)) * grip
	local target = hover:Lerp(grip, sm((t - rc.grip0) / (rc.grip1 - rc.grip0)))
	local H2 = armTo(m, m.RightHand.CFrame:Lerp(target, w))
	if H2 then R.handCF = R.handCF or {}; R.handCF[m] = H2 end
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
	-- 1. the bodies: the killer and victim (and the killer's afterimages) on their roots, posed from the clips (the
	-- right arm then reaching onto the holstered gun through the draw)
	local used = {}
	R.handCF = {}
	for name, a in pairs(f.anim or {}) do
		local m = R.av[name]
		if m then
			m.Parent = root
			unreach(m)
			place(m, C(a.root))
			pose(m, a.clip, a.t, a.clip2, a.t2, a.w2)
			ground(m, f, name)
			reach(m, a)
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
	-- (the owner, 20 Nov: the holster hung where the hand reached came off the body - so it stays on the hip, and the
	-- hand reaches onto the gun there (reach above): at the hand-over the hand is already on the grip, so the gun in the
	-- hand sits where the holstered one sat, and comes out with the hand)
	for name, state in pairs(sem.hol or {}) do
		local m = R.av[name]
		if m and used[name] then
			local hcf, lt, hw, hd = holsterCF(m)
			part(Vector3.new(0.32, 0.95, 0.55), hcf, LEATHER, Enum.Material.Leather)
			part(Vector3.new(2 * hw * 1.06, 0.28, 2 * hd * 1.1), lt.CFrame * CFrame.new(0, 0.05, 0), LEATHER, Enum.Material.Leather)
			if state == "in" then placeKit(REV, inHolster(m), 3, "gun") end
		end
	end
	for name, state in pairs(sem.gun or {}) do
		local m = R.av[name]
		if m and used[name] and state == "hand" then placeKit(REV, gunInHand(m), 3, "gun") end
	end
	for _, g in ipairs(f.guns or {}) do
		-- (the afterimage guns ride the real hand, not the stand-in's)
		if g.tr then placeKit(game.ReplicatedStorage.JankfireSkins[g.model], reanchor(C(g.cf), f, "k.RightHand"), 3, "gun", g.tr) end
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
		if q.tag == "lamp" and not f.impact then
			local pl = Instance.new("PointLight"); pl.Range = 10; pl.Brightness = 1.6; pl.Shadows = true
			pl.Color = Color3.fromRGB(255, 190, 120); pl.Parent = p
		end
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
	-- the fixed set (the town is 600+ parts) is built once and kept (a "real_" folder survives the per-frame clear);
	-- the two-tone hit frames hide it
	local skey = if f.stage == true then "_stage" elseif type(f.stage) == "string" then f.stage else nil
	if skey and R.staticKey ~= skey then
		local old = root:FindFirstChild("real_static")
		if old then old:Destroy() end
		local keep = stage
		stage = Instance.new("Folder"); stage.Name = "real_static"
		local imp = f.impact
		f.impact = nil
		for _, q in ipairs(data[skey].props) do addProp(q) end
		f.impact = imp
		stage.Parent = root
		R.static, R.staticKey, R.staticHidden = stage, skey, false
		stage = keep
	end
	if R.static then
		local hide = f.impact ~= nil or not skey
		if hide ~= R.staticHidden then
			for _, p in ipairs(R.static:GetDescendants()) do
				if p:IsA("BasePart") then
					if hide then p:SetAttribute("TrWas", p.Transparency); p.Transparency = 1
					else p.Transparency = p:GetAttribute("TrWas") or 0 end
				elseif p:IsA("Light") then p.Enabled = not hide end
			end
			R.staticHidden = hide
		end
	end
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
