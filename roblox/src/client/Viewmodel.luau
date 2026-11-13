--!strict
-- your weapon in first person: the web game's pose stack (public/js/weapons.js, vmbob.js, anim.js), every frame, in
-- camera space: rest pose -> swap drop -> footstep bob -> breathing -> look sway -> run tilt -> aim (ADS) -> the clip
-- (draw / swing / parry / reload / staggered) -> recoil springs. plus the Redline's needle + vents, the katana's
-- length, two chunky hands. metres from the web game x3 = studs
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local Anims = require(Shared:WaitForChild("Anims")) :: any

local S = Weapons.S
local VM = {}
VM.onEvent = nil :: ((string) -> ())?
VM.wid = ""
VM.model = nil :: Model?
VM.hitStop = 0

local camera = workspace.CurrentCamera
local clip: { name: string, t: number, fired: { [number]: boolean } }? = nil
local swap = 0
local rec = { p = Vector3.zero, pv = Vector3.zero, r = Vector3.zero, rv = Vector3.zero }
local punch = { x = Vector3.zero, v = Vector3.zero }
local kick = 0
local bobPh, breathT = 0, 0
local sway = Vector2.zero
local runK = 0
local lastLook: Vector3? = nil
local needle: Weld? = nil
local needleAng = -2.3
local hubCF = CFrame.identity
local vents: { BasePart } = {}
local k = 3

local EASE = {
	linear = function(u: number) return u end,
	smooth = function(u: number) return u * u * (3 - 2 * u) end,
	snap = function(u: number) return 1 - (1 - u) ^ 3 end,
	["in"] = function(u: number) return u * u * u end,
	back = function(u: number) local c = 1.9; return 1 + (c + 1) * (u - 1) ^ 3 + c * (u - 1) ^ 2 end,
}

local function v3(a: { number }): Vector3 return Vector3.new(a[1], a[2], a[3]) end

-- a clip's pose at time t: position offset (studs) and the rotation (base euler + offset; quaternion blend for slerp)
function VM.sample(name: string, t: number, base: Vector3): (Vector3, CFrame)
	local a = Anims[name]
	local keys = a.keys
	local k0, k1 = keys[1], keys[#keys]
	if t <= keys[1].t then k1 = keys[1] end
	for i = 1, #keys - 1 do
		if t >= keys[i].t and t < keys[i + 1].t then k0, k1 = keys[i], keys[i + 1]; break end
	end
	local span = k1.t - k0.t
	local u = if span > 0 then math.clamp((t - k0.t) / span, 0, 1) else 1
	local e = (EASE :: any)[k1.e](u)
	local p = v3(k0.p):Lerp(v3(k1.p), e) * S
	if a.slerp then
		local sb = v3(a.slerp)
		local c0 = CFrame.fromEulerAnglesXYZ((sb + v3(k0.r)).X, (sb + v3(k0.r)).Y, (sb + v3(k0.r)).Z)
		local c1 = CFrame.fromEulerAnglesXYZ((sb + v3(k1.r)).X, (sb + v3(k1.r)).Y, (sb + v3(k1.r)).Z)
		return p, c0:Lerp(c1, e)
	end
	local r = base + v3(k0.r):Lerp(v3(k1.r), e)
	return p, CFrame.fromEulerAnglesXYZ(r.X, r.Y, r.Z)
end

function VM.play(name: string)
	if not Anims[name] then return end
	clip = { name = name, t = 0, fired = {} }
end
function VM.playing(): string? return clip and clip.name end
function VM.stop() clip = nil end

-- a shot: the gun's recoil row on the springs + a camera view punch (public/js/weapons.js kickVM)
local function rnd(): number return (if math.random() < 0.5 then -1 else 1) * (0.5 + math.random() * 0.5) end
function VM.kick(row: { back: number, up: number, roll: number, side: number, punch: number }?, mul: number, fast: boolean)
	local r = row or { back = 0.8, up = 2.5, roll = 1, side = 0.2, punch = 0.01 }
	rec.pv += Vector3.new(r.side * rnd(), 0, r.back) * mul
	rec.rv += Vector3.new(r.up, 0, r.roll * rnd()) * mul
	punch.v += Vector3.new(r.punch, r.punch * 0.35 * rnd(), r.punch * 0.5 * rnd()) * mul * 21
	kick += if fast then 0.25 else 1
end
-- a landed parry / hit: a jolt on the blade
function VM.jolt(up: number) rec.rv += Vector3.new(up, 0, 0); rec.pv += Vector3.new(0, 0, up * 0.3) end

-- the camera's view punch (visual only): applied after the camera module each frame
function VM.punch(): CFrame return CFrame.fromEulerAnglesXYZ(punch.x.X, punch.x.Y, punch.x.Z) end

local function hands(m: Model, root: BasePart)
	local skin, sleeve = Color3.fromRGB(255, 206, 160), Color3.fromRGB(255, 79, 216)
	for _, spot in { "Grip", "Fore" } do
		local a = root:FindFirstChild(spot) :: Attachment?
		if not a then continue end
		local fist = Instance.new("Part")
		fist.Name = "Hand" .. spot; fist.Size = Vector3.new(0.09, 0.1, 0.11) * k; fist.Color = skin
		fist.Material = Enum.Material.SmoothPlastic; fist.CanCollide = false; fist.CanQuery = false; fist.CanTouch = false; fist.CastShadow = false
		fist.CFrame = root.CFrame * CFrame.new(a.Position) * CFrame.new(if spot == "Fore" then -0.01 * k else 0.01 * k, -0.02 * k, 0)
		local cuff = Instance.new("Part")
		cuff.Name = "Sleeve" .. spot; cuff.Size = Vector3.new(0.1, 0.1, 0.5) * k; cuff.Color = sleeve
		cuff.Material = Enum.Material.SmoothPlastic; cuff.CanCollide = false; cuff.CanQuery = false; cuff.CanTouch = false; cuff.CastShadow = false
		-- the forearm runs back and down to a shoulder off screen, so the hands never float
		cuff.CFrame = fist.CFrame * CFrame.Angles(0.5, if spot == "Fore" then -0.35 else 0.25, 0) * CFrame.new(0, -0.03 * k, 0.28 * k)
		for _, p in { fist, cuff } do
			local w = Instance.new("WeldConstraint"); w.Part0 = root; w.Part1 = p; w.Parent = p
			p.Parent = m
		end
	end
end

-- swap to a weapon: build its viewmodel, play its draw
function VM.set(wid: string, kat: number)
	if VM.model then VM.model:Destroy(); VM.model = nil end
	VM.wid = wid
	needle, vents = nil, {}
	local w = Weapons.list[wid]
	if not w or not w.vm then return end
	k = S * w.vm.s
	local m = WeaponModels.build(wid, k)
	if not m or not m.PrimaryPart then return end
	local root = m.PrimaryPart
	root.Anchored = true
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.CastShadow = false; d.CanQuery = false; d.CanTouch = false end
	end
	hands(m, root)
	if wid == "katana" then WeaponModels.setKatana(m, kat, k) end
	-- the needle turns round its pivot (a Weld we drive) instead of being glued
	local n = m:FindFirstChild("needle") :: BasePart?
	if n then
		local pv = n:GetAttribute("Pivot")
		local pivot = if typeof(pv) == "Vector3" then pv * k else Vector3.new(-0.041, 0.03, -0.05) * k
		local wc = n:FindFirstChildOfClass("WeldConstraint")
		if wc then wc:Destroy() end
		hubCF = CFrame.new(pivot)
		local rel = hubCF:ToObjectSpace(root.CFrame:ToObjectSpace(n.CFrame))
		local wd = Instance.new("Weld")
		wd.Part0 = root; wd.Part1 = n; wd.C0 = hubCF; wd.C1 = rel:Inverse(); wd.Parent = n
		needle = wd
	end
	for _, d in m:GetChildren() do if d:IsA("BasePart") and d.Name == "vent" then table.insert(vents, d) end end
	m.Parent = camera
	VM.model = m
	swap = 0.2
	VM.play(if wid == "katana" then "draw_katana" else "draw_gun")
end

function VM.attachment(name: string): Vector3?
	local m = VM.model
	local a = m and m.PrimaryPart and m.PrimaryPart:FindFirstChild(name) :: Attachment?
	return a and a.WorldPosition
end

export type Ctx = { aim: number, speed: number, sprint: boolean, slide: boolean, grounded: boolean, hp: number, firedT: number, slipping: boolean, now: number, sight: Vector3? }

function VM.update(dt: number, c: Ctx)
	local m = VM.model
	local w = Weapons.list[VM.wid]
	if not m or not m.PrimaryPart or not w or not w.vm then return end
	-- hit-stop: the clip's clock stops (melee hits and parries)
	local adt = dt
	if VM.hitStop > 0 then VM.hitStop -= dt; adt = 0 end
	if clip then
		clip.t += adt
		local a = Anims[clip.name]
		for i, ev in a.events do
			if not clip.fired[i] and clip.t >= ev[1] then
				clip.fired[i] = true
				if VM.onEvent then VM.onEvent(ev[2]) end
			end
		end
		if clip.t >= a.dur then clip = nil end
	end
	-- springs (240 Hz sub-steps)
	local nSub = math.clamp(math.ceil(dt * 240), 1, 40)
	local h = dt / nSub
	for _ = 1, nSub do
		rec.pv += (-220 * rec.p - 20 * rec.pv) * h; rec.p += rec.pv * h
		rec.rv += (-200 * rec.r - 18 * rec.rv) * h; rec.r += rec.rv * h
		punch.v += (-160 * punch.x - 18 * punch.v) * h; punch.x += punch.v * h
	end
	kick = math.max(0, kick - 6 * dt)
	swap = math.max(0, swap - 5 * dt)
	local base, rot = w.vm.p, w.vm.r
	local px, py, pz = base.X, base.Y - 0.3 * swap * S, base.Z
	local rx, ry, rz = 0, 0, 0
	-- footstep bob: one dip per foot strike
	local spd = c.speed / S
	local stride = math.min(4.3, 1.2 + 0.29 * spd)
	if c.grounded then bobPh += spd * dt / stride * math.pi end
	local run = math.clamp((spd - 6) / 4, 0, 1)
	local sprint = math.clamp((spd - 11.5) / 2.5, 0, 1)
	local amp = (0.011 + 0.008 * run + 0.01 * sprint) * (if c.grounded then math.min(1, spd / 3) else 0)
	local dip = -math.abs(math.sin(bobPh))
	px += math.sin(bobPh) * amp * 1.1 * S; py += dip * amp * 1.6 * S; rx += dip * amp * 2.5; rz += math.sin(bobPh) * amp * 3.5
	-- breathing
	breathT += dt
	px += math.sin(breathT * 1.3) * 0.0025 * S; py += math.sin(breathT * 2.1) * 0.0018 * S; rz += math.sin(breathT * 1.1) * 0.008
	-- look sway: the gun trails the mouse
	local look = camera.CFrame.LookVector
	if lastLook then
		local dyaw = math.atan2(-look.X, -look.Z) - math.atan2(-lastLook.X, -lastLook.Z)
		if dyaw > math.pi then dyaw -= 2 * math.pi elseif dyaw < -math.pi then dyaw += 2 * math.pi end
		local dpitch = math.asin(math.clamp(look.Y, -1, 1)) - math.asin(math.clamp(lastLook.Y, -1, 1))
		local tgt = Vector2.new(math.clamp(dyaw * 0.6, -0.07, 0.07), math.clamp(dpitch * 0.6, -0.07, 0.07))
		sway = sway:Lerp(tgt, math.min(1, dt * 9))
	end
	lastLook = look
	px += 0.2 * sway.X * S; py -= 0.12 * sway.Y * S; rx -= 0.8 * sway.Y; ry += 1.3 * sway.X; rz += 0.6 * sway.X
	-- run tilt / slide roll
	runK += ((if c.sprint and c.grounded and c.aim < 0.1 then 1 else 0) - runK) * math.min(1, dt * 8)
	py -= 0.03 * runK * S; rx -= 0.25 * runK; ry += 0.35 * runK; rz += 0.2 * runK
	if c.slide then rz += 0.3 end
	-- slipping on marbles: the gun flung up, then wobbling
	if c.slipping then rx += 0.85 * 0.5 + math.sin(breathT * 9 * 2 * math.pi) * 0.12; rz += 0.5 * 0.5 + math.sin(breathT * 14 * 2 * math.pi) * 0.1 end
	-- the clip (draw / swing / parry / reload / stagger)
	local cp, crot: CFrame? = Vector3.zero, nil
	if clip then
		cp, crot = VM.sample(clip.name, clip.t, rot)
	end
	-- aim down sights: blend to the sight on the screen's centre, rotation to none
	local ra = 1 - c.aim * 0.6
	local pos = Vector3.new(px, py, pz) + cp
	local ads = c.sight
	if ads and c.aim > 0 then
		local e = c.aim * c.aim * (3 - 2 * c.aim)
		pos = pos:Lerp(ads, e)
		rx, ry, rz = rx * (1 - e), ry * (1 - e), rz * (1 - e)
	end
	pos += Vector3.new(rec.p.X * ra, rec.p.Y * (1 - c.aim * 0.3), (kick * 0.04 * S + rec.p.Z) * ra)
	local baseRot = crot or CFrame.fromEulerAnglesXYZ(rot.X, rot.Y, rot.Z)
	if ads and c.aim > 0 and not crot then baseRot = CFrame.fromEulerAnglesXYZ(rot.X, rot.Y, rot.Z):Lerp(CFrame.identity, c.aim) end
	local jig = CFrame.fromEulerAnglesXYZ(rx + (kick * 0.12 + rec.r.X) * ra, ry, rz + rec.r.Z * ra)
	m.PrimaryPart.CFrame = camera.CFrame * CFrame.new(pos) * jig * baseRot
	-- the Redline's tachometer + vents (from your HP; it bangs off the limiter when it's in the red and firing)
	if VM.wid == "redline" then
		local tk = Weapons.tacho(c.hp)
		local tgt = -2.3 + 4.6 * tk
		if tk > 0.85 and c.now - c.firedT < 0.2 then tgt += math.sin(c.now * 1000 * 0.08) * 0.12 end
		if clip and clip.name == "reload_redline" then -- the rev: forced into the red, wobbles, back
			local t = clip.t
			local f = if t < 1.3 then 0 elseif t < 1.42 then (t - 1.3) / 0.12 elseif t < 1.56 then 1 elseif t < 1.76 then 1 - (t - 1.56) / 0.2 else 0
			tgt += (2.3 - tgt) * f + (if t > 1.46 and t < 1.56 then math.sin(t * 90) * 0.15 else 0)
		end
		needleAng += (tgt - needleAng) * math.min(1, dt * 12)
		if needle then needle.C0 = hubCF * CFrame.Angles(needleAng, 0, 0) end
		local col = Color3.new(0.25 + 0.75 * tk, 0.04 + 0.3 * tk * tk, 0.02 + (if c.now - c.firedT < 0.2 then 0.15 * tk else 0))
		for _, v in vents do v.Color = col end
	end
end

-- the katana grew (or reset): restretch
function VM.setKatana(n: number)
	if VM.wid == "katana" and VM.model then WeaponModels.setKatana(VM.model, n, k) end
end

-- where the sight sits while aiming (camera space, studs): on the screen's centre line (public/js/weapons.js adsPose)
function VM.adsPos(wid: string): Vector3?
	local w = Weapons.list[wid]
	if not w or not w.vm or not w.ads then return nil end
	local s = w.vm.s
	if wid == "redline" then return Vector3.new(0, -0.0737 * s, -0.17 - 0.1058 * s) * S end
	return Vector3.new(0.06, math.min(-0.1, -0.03 - 0.1479 * s), -0.3) * S -- no sights: under and right of the middle
end

return VM
