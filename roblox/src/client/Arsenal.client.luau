--!strict
-- your weapons (step 2): 1 Redline, 2 Marble Shotgun, 3 Katana. like the web game, your client finds what it hit
-- (rays from your eye against the map, then everyone's two hit boxes) and tells the server, which checks everything
-- (Combat.server.luau) and owns HP, kills, the katana's length and the marbles on the floor. this file: input,
-- firing, swings, the parry, your own juice (recoil, kick, flash, brass, tracers, marbles), and what the server says
-- happened (hit markers, DINK, the feed, knockback, slips, the end screen)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Anims = require(Shared:WaitForChild("Anims")) :: any
local Hud = require(script.Parent:WaitForChild("Hud"))
local H = require(script.Parent:WaitForChild("FightHud"))
local VM = require(script.Parent:WaitForChild("Viewmodel"))
local Fx = require(script.Parent:WaitForChild("Fx"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Body = require(script.Parent:WaitForChild("Body"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(n: string): RemoteEvent return Remotes:WaitForChild(n) :: RemoteEvent end
local EquipR, FireR, ReloadR, SwingR, MeleeR, ParryR = remote("Equip"), remote("Fire"), remote("Reload"), remote("Swing"), remote("MeleeHit"), remote("Parry")
local MatchState = ReplicatedStorage:WaitForChild("Match")

local W = Weapons.list
local S = Weapons.S
local P = Weapons.PARRY
local TRACER = Color3.fromRGB(255, 240, 160) -- the default tracer (a gun's row can name its own)
local me = Players.LocalPlayer
local camera = workspace.CurrentCamera

-- ---------------------------------------------------------------- state
local held = "redline"
local ammo: { [string]: { mag: number, reloadUntil: number } } = {}
local nextShot: { [string]: number } = {}
local bloom = 0
local aim = 0
local trigger, aimHeld = false, false
local firedT = -math.huge
local lastSwing, swingAlt, nextSwing = -math.huge, false, 0
local pending: { t: number }? = nil
local parryT, parryReady, parryBuf = -math.huge, 0, -math.huge
local staggerUntil = -math.huge
local shake = 0
local view = { pitch = 0, yaw = 0 } -- the visual offsets applied to the camera last frame (removed again next frame)
local equipT = 0

-- your loadout (the server sets it on every arm, Loadout.luau): the weapons on keys 1 2 3
local function lo(): { string }
	local s = me:GetAttribute("Loadout")
	if type(s) ~= "string" then return Weapons.loadout end
	local out = {}
	for id in string.gmatch(s, "[^,]+") do if W[id] then table.insert(out, id) end end
	return if #out == 3 then out else Weapons.loadout
end
-- the loadout screen is up (LoadoutUI): hands off the weapons
local function menuOpen(): boolean return me:GetAttribute("LoadoutOpen") == true end

local function resetAmmo()
	for _, id in lo() do
		local w = W[id]
		if w.mag then ammo[id] = { mag = w.mag, reloadUntil = 0 } end
		nextShot[id] = 0
	end
end
resetAmmo()

local function myChar(): (Model?, Humanoid?, BasePart?)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not hum or not root or hum.Health <= 0 then return nil, nil, nil end
	return ch, hum, root
end
-- the Shredder (a Tool, key 4) takes over while it's out: these weapons hide and hold fire
local function toolOut(): boolean
	local ch = me.Character
	return ch ~= nil and ch:FindFirstChildOfClass("Tool") ~= nil
end
-- the hub is weapons-free (owner, 2026-11-14): no viewmodel, no firing; the training room and matches arm you
-- (the server agrees: Fight.holstered, Combat, HubHolster)
local function inHub(): boolean
	return me:GetAttribute("Zone") == "hub"
end
-- the muzzle of the gun a character holds (third person: yours, or someone else's)
local function heldMuzzle(m: Instance?): Vector3?
	local wpn = m and m:FindFirstChild("HeldWeapon")
	local root = wpn and wpn:IsA("Model") and wpn.PrimaryPart
	local a = root and root:FindFirstChild("Muzzle")
	return if a and a:IsA("Attachment") then a.WorldPosition else nil
end
local function hp(): number
	local v = me:GetAttribute("Hp")
	return if type(v) == "number" then v else 100
end
local function kat(): number
	local v = me:GetAttribute("Kat")
	return if type(v) == "number" then v else 0
end
local function thirdPerson(): boolean
	local _, _, root = myChar()
	return root ~= nil and (camera.CFrame.Position - root.Position).Magnitude > 4.5
end
-- the eye (feet + 1.6 m, lower when crouched: the camera itself in first person), and where you're aiming
local function eyeAndAim(): (Vector3, Vector3)
	local _, _, root = myChar()
	local cam = camera.CFrame
	if not root or not thirdPerson() then return cam.Position, cam.LookVector end
	local eye = root.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0)
	local hit = Fx.castMap(cam.Position, cam.LookVector * 900)
	local target = if hit then hit.Position else cam.Position + cam.LookVector * 900
	return eye, (target - eye).Unit
end

-- everyone you could hit: other players and the test dummies (alive), with their feet
local function targets(): { { m: Model, feet: Vector3 } }
	local out = {}
	local function addModel(m: Model)
		local hum = m:FindFirstChildOfClass("Humanoid")
		local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if hum and root and hum.Health > 0 then table.insert(out, { m = m, feet = Hitbox.feet(root.Position) }) end
	end
	for _, p in Players:GetPlayers() do
		if p ~= me and p.Character then addModel(p.Character) end
	end
	local d = workspace:FindFirstChild("Dummies")
	if d then for _, m in d:GetChildren() do if m:IsA("Model") then addModel(m) end end end
	return out
end

-- ---------------------------------------------------------------- camera: kick (stays, like the web game) + punch/shake (visual)
local function kickCam(pitch: number, yaw: number)
	camera.CFrame = camera.CFrame * CFrame.Angles(pitch, yaw, 0)
end
RunService:BindToRenderStep("JankfireCamera", Enum.RenderPriority.Camera.Value + 1, function()
	-- the camera module reads the look back each frame, so visual offsets are applied as a change from last frame's
	local pr = VM.punch()
	local px, py, pz = pr:ToEulerAnglesXYZ()
	local sx, sy = (math.random() - 0.5) * shake * 0.02, (math.random() - 0.5) * shake * 0.02
	local tp, ty = px + sx, py + sy
	camera.CFrame = camera.CFrame * CFrame.Angles(tp - view.pitch, ty - view.yaw, 0) * CFrame.Angles(0, 0, pz)
	view.pitch, view.yaw = tp, ty
end)

-- ---------------------------------------------------------------- swapping, reloading
-- the katana's smear: the blade's middle and tip, sampled in CAMERA space during the clip's trail window and drawn as
-- a fading ribbon of triangles every frame. (a Trail leaves its points in the world, so moving or turning mid-swing
-- left the streak hanging in the air behind the blade)
local SMEAR_LIFE = 0.12
local smearPts: { { t: number, a: Vector3, b: Vector3 } } = {}
local smearPool: { WedgePart } = {}
local smearFolder: Folder? = nil
local function wedge(i: number): WedgePart
	local w = smearPool[i]
	if not w or not w.Parent then
		if not smearFolder or not smearFolder.Parent then
			local f = Instance.new("Folder"); f.Name = "KatanaSmear"; f.Parent = camera
			smearFolder = f
		end
		w = Instance.new("WedgePart")
		w.Anchored = true; w.CanCollide = false; w.CanQuery = false; w.CanTouch = false; w.CastShadow = false
		w.Material = Enum.Material.Neon; w.Color = Color3.fromRGB(225, 240, 255); w.Transparency = 1
		w.Parent = smearFolder
		smearPool[i] = w
	end
	return w :: WedgePart
end
-- one triangle out of two wedges (the classic way to draw a triangle with parts)
local function tri(n: number, a: Vector3, b: Vector3, c: Vector3, tr: number): number
	local ab, ac, bc = b - a, c - a, c - b
	if ac:Cross(ab).Magnitude < 1e-5 then return n end
	local abd, acd, bcd = ab:Dot(ab), ac:Dot(ac), bc:Dot(bc)
	if abd > acd and abd > bcd then c, a = a, c
	elseif acd > bcd and acd > abd then a, b = b, a end
	ab, ac, bc = b - a, c - a, c - b
	local right = ac:Cross(ab).Unit
	local up = bc:Cross(right).Unit
	local back = bc.Unit
	local height = math.abs(ab:Dot(up))
	local w1, w2 = wedge(n + 1), wedge(n + 2)
	w1.Size = Vector3.new(0.002, height, math.abs(ab:Dot(back)))
	w1.CFrame = CFrame.fromMatrix((a + b) / 2, right, up, back)
	w2.Size = Vector3.new(0.002, height, math.abs(ac:Dot(back)))
	w2.CFrame = CFrame.fromMatrix((a + c) / 2, -right, up, -back)
	w1.Transparency, w2.Transparency = tr, tr
	return n + 2
end
local function smearStep(now: number, hidden: boolean)
	local c = VM.playing()
	local an = c and Anims[c]
	local ct = VM.clipT()
	local root = VM.model and VM.model.PrimaryPart
	if not hidden and an and an.trail and ct and root and ct >= an.trail[1] and ct <= an.trail[2] then
		local mid = root:FindFirstChild("Mid") :: Attachment?
		local tip = root:FindFirstChild("Muzzle") :: Attachment?
		if mid and tip then
			local cf = camera.CFrame
			table.insert(smearPts, { t = now, a = cf:PointToObjectSpace(mid.WorldPosition), b = cf:PointToObjectSpace(tip.WorldPosition) })
		end
	end
	while #smearPts > 0 and (now - smearPts[1].t > SMEAR_LIFE or #smearPts > 24) do table.remove(smearPts, 1) end
	local used = 0
	if not hidden and #smearPts > 1 then
		local cf = camera.CFrame
		for i = 1, #smearPts - 1 do
			local p, q = smearPts[i], smearPts[i + 1]
			local tr = 0.3 + 0.7 * math.clamp((now - p.t) / SMEAR_LIFE, 0, 1) -- the oldest edge fades out
			local a1, b1 = cf:PointToWorldSpace(p.a), cf:PointToWorldSpace(p.b)
			local a2, b2 = cf:PointToWorldSpace(q.a), cf:PointToWorldSpace(q.b)
			used = tri(used, a1, b1, b2, tr)
			used = tri(used, a1, b2, a2, tr)
		end
	end
	for i = used + 1, #smearPool do
		local w = smearPool[i]
		if w.Transparency ~= 1 then w.Transparency = 1 end
	end
end

-- the Shredder in your primary slot: it's a Tool (ShredderServer runs it), so its key just pulls the Tool out
local function equipShredder()
	local ch, hum = myChar()
	if not ch or not hum then return end
	if ch:FindFirstChild("Shredder") then held = "shredder"; return end
	local bag = me:FindFirstChildOfClass("Backpack")
	local tool = bag and (bag:FindFirstChild("Shredder") or bag:WaitForChild("Shredder", 3))
	if not tool or not tool:IsA("Tool") or not hum.Parent then return end
	local a = ammo[held]
	if a and a.reloadUntil > 0 then a.reloadUntil = 0 end
	held = "shredder"
	equipT = os.clock()
	aim = 0
	VM.set("shredder", 0) -- (no viewmodel: the Tool is the model)
	hum:EquipTool(tool)
	EquipR:FireServer("shredder")
	Sfx.play("click")
end

local function equip(wid: string)
	if wid == "shredder" then equipShredder(); return end
	if wid == held and VM.model then return end
	if not W[wid] then return end
	if toolOut() then local _, hum = myChar(); if hum then hum:UnequipTools() end end
	local a = ammo[held]
	if a and a.reloadUntil > 0 then a.reloadUntil = 0 end -- swapping cancels a reload
	held = wid
	equipT = os.clock()
	aim = 0
	VM.set(wid, kat())
	table.clear(smearPts)
	EquipR:FireServer(wid)
	Sfx.play("click")
end

local function reload()
	local w = W[held]
	local a = ammo[held]
	if not a or not w.mag or a.reloadUntil > 0 or a.mag >= w.mag then return end
	a.reloadUntil = os.clock() + (w.reload :: number)
	aim = 0
	ReloadR:FireServer(held)
	VM.reload(held, w.reload :: number)
end

VM.onEvent = function(ev: string)
	if ev == "whoosh" then Sfx.play("swing")
	elseif ev == "shing" then Sfx.play("ting")
	elseif ev == "click" then Sfx.play("click")
	elseif ev == "glug" then Sfx.play("glug")
	elseif ev == "revUp" then Sfx.play("rev_up")
	elseif ev == "rattle" then Sfx.play("marble"); Sfx.play("marble", nil, 0.7, 1.2)
	elseif ev == "boing" then Sfx.play("boing")
	elseif ev == "thwack" then Sfx.play("thwack")
	-- the plain guns' reloads (Reloads.luau): mag out, mag in, the charging handle. anything not rendered yet clicks
	elseif ev == "magOut" then Sfx.play("click", nil, 0.9, 0.8)
	elseif ev == "magIn" then Sfx.play("reload")
	elseif ev == "chargeBack" then Sfx.play("click", nil, 0.8, 1.1)
	elseif ev == "chargeHome" then Sfx.play("click", nil, 1, 1.35)
	else Sfx.play("click", nil, 0.6) end
end

-- ---------------------------------------------------------------- firing
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include

local function fireGun(now: number)
	local w = W[held]
	local a = ammo[held]
	local _, _, root = myChar()
	if not root or not a then return end
	if a.reloadUntil > 0 then return end
	if a.mag <= 0 then Sfx.play("empty"); reload(); return end
	local iv = 1 / Weapons.fireRate(w, hp())
	nextShot[held] = math.max(nextShot[held], now - math.min(0.04, iv / 2)) + iv
	a.mag -= 1
	firedT = now
	local eye, look = eyeAndAim()
	local spread = ((w.spread or 0) + bloom) * (1 + ((if w.ads then w.ads.spread else 1) - 1) * aim)
	local map = workspace:FindFirstChild("Map")
	mapParams.FilterDescendantsInstances = { map :: Instance }
	local tg = targets()
	local hits: { [Model]: { n: number, h: number } } = {}
	local ends: { Vector3 } = {}
	local allEnds: { Vector3 } = {}
	local impacts: { RaycastResult } = {}
	local splashes: { Vector3 } = {}
	for _ = 1, w.pellets or 1 do
		local d = Hitbox.spreadDir(look, spread, math.random(), math.random())
		local mh = workspace:Raycast(eye, d * w.range, mapParams)
		local best = if mh then (mh.Position - eye).Magnitude else w.range
		local who: Model?, head = nil, false
		for _, t in tg do
			local k = Hitbox.distScale((t.feet - eye).Magnitude)
			local tt, hd = Hitbox.ray(eye, d, t.feet, k)
			if tt and tt < best then best, who, head = tt, t.m, hd end
		end
		local e = eye + d * best
		table.insert(allEnds, e)
		if #ends < 12 then table.insert(ends, e) end
		local wx = Fx.waterCross(eye, e) -- into the pool: a splash on the surface, not dust on the bottom
		if wx and #splashes < 4 then table.insert(splashes, wx) end
		if who then
			local g = hits[who] or { n = 0, h = 0 }
			g.n += 1; if head then g.h += 1 end
			hits[who] = g
		elseif mh and not wx and #impacts < 6 then table.insert(impacts, mh) end
	end
	local list = {}
	for m, g in hits do table.insert(list, { m = m, n = g.n, h = g.h }) end
	FireR:FireServer(held, eye, ends, list)
	-- your own feel: shove, climb, bloom, the gun kicks, flash, brass, tracer / marbles, sound
	Body.push(-look * (w.recoil or 0))
	kickCam((w.kick or 0) * (0.6 + math.random() * 0.8) * (1 - 0.5 * aim), (math.random() - 0.5) * (w.kick or 0) * 0.5)
	bloom = math.min(w.maxBloom or 0, bloom + (w.bloom or 0))
	VM.kick(w.recoilVM, if aim > 0.5 then 0.6 else 1, (w.rate or 0) > 8)
	local fpv = not thirdPerson()
	-- the muzzle: the viewmodel's in first person, the gun in your character's hand in third person
	local mz = (if fpv then nil else heldMuzzle(me.Character)) or VM.attachment("Muzzle") or (eye + look * 2)
	-- every gun's look comes from its row in Weapons (fx, tracer, snd): nothing here is per weapon
	local fx = w.fx or {}
	Fx.muzzle(CFrame.lookAt(mz, mz + look), fx.big == true, fpv)
	if fx.spray then
		Fx.marbles(mz, allEnds, 1) -- no tracers: the marbles are the tracers
	else
		if fx.brass then
			local port = VM.attachment("Port")
			if port and fpv then Fx.brass(CFrame.lookAt(port, port + look) * CFrame.Angles(0, 0, 0), false) end
		end
		for _, e in ends do Fx.tracer(mz, e, w.tracer or TRACER, 0.045 * S, 0.2) end
	end
	Sfx.gun(w, Weapons.tacho(hp()), nil)
	-- what the shots hit: holes, dust, sparks by material (marbles chip and puff, they don't punch holes)
	local o = if fx.hole == false then { hole = false, scale = fx.scale or 1 } else nil
	for _, im in impacts do Fx.impact(im.Position, im.Normal, im.Instance, im.Material, o) end
	if fx.splash ~= false then for _, s in splashes do Fx.splash(s, 0.3) end end -- (marbles plop in on their own)
	shake = math.max(shake, fx.shake or 0.06)
	if a.mag <= 0 then task.delay(0.15, reload) end
end

-- the katana: click = swing (the combo alternates within 0.75 s); the hit lands at the clip's hit time
local function swing(now: number)
	if now < nextSwing or now < staggerUntil or now - parryT < P.win then return end
	nextSwing = now + (W.katana.cd :: number)
	swingAlt = (now - lastSwing < 0.75) and not swingAlt
	lastSwing = now
	VM.play(if swingAlt then "swing_katana2" else "swing_katana")
	SwingR:FireServer("katana")
	pending = { t = now + (W.katana.hitT :: number) }
end

local function resolveSwing()
	pending = nil
	local _, _, root = myChar()
	if not root then return end
	local eye, look = eyeAndAim()
	local w = W.katana
	local reach = Weapons.reach(w, kat())
	local map = workspace:FindFirstChild("Map")
	mapParams.FilterDescendantsInstances = { map :: Instance }
	local hitList: { Model } = {}
	local firstAt: Vector3? = nil
	for _, t in targets() do
		local pt = t.feet + Vector3.new(0, Hitbox.ROOT_UP, 0)
		if Hitbox.inCone(eye, look, pt, reach, w.cone :: number) then
			local v = pt - eye
			if v.Magnitude < 0.5 or not workspace:Raycast(eye, v, mapParams) then
				table.insert(hitList, t.m)
				firstAt = firstAt or pt
				if #hitList >= 6 then break end
			end
		end
	end
	if #hitList == 0 then
		-- nobody in reach: the blade still bites what's in front of you (sparks off a wall, a splash in the pool)
		local h = workspace:Raycast(eye, look * reach, mapParams)
		local wx = Fx.waterCross(eye, if h then h.Position else eye + look * reach)
		if wx then Fx.splash(wx, 0.45)
		elseif h then Fx.slash(h.Position, h.Normal, h.Instance, h.Material, look); Sfx.play("tink", h.Position, 0.7) end
		return
	end
	MeleeR:FireServer("katana", look, hitList)
	-- the hit, felt right away: hit-stop, the flash, a bonk, a punch
	VM.hitStop = 0.06
	if firstAt then Fx.blast(firstAt, 0.6) end
	Sfx.play("bonk")
	shake = math.max(shake, 0.35)
	VM.jolt(-1.5)
end

local function tryParry(now: number)
	if held ~= "katana" then return end
	if now < parryReady or now < staggerUntil or pending or now - equipT < 0.12 then
		parryBuf = now -- an early press is kept for 250 ms
		return
	end
	parryBuf = -math.huge
	parryT = now
	parryReady = now + P.win + P.cd
	VM.play("parry_katana")
	local lk = camera.CFrame.LookVector
	ParryR:FireServer(math.atan2(-lk.X, -lk.Z)) -- where you look: the server's "front" for this guard
end

-- ---------------------------------------------------------------- input
local KEYS = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3 } -- the loadout's slots
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or menuOpen() or inHub() then return end
	local slot = KEYS[io.KeyCode]
	local want = if slot then lo()[slot] else nil
	if toolOut() then -- 1/2/3 put the Shredder away and take that weapon; the rest is the Shredder's
		if want and want ~= "shredder" then
			local _, hum = myChar()
			if hum then hum:UnequipTools() end
			equip(want)
		end
		return
	end
	if want then equip(want); return end
	if held == "shredder" then return end -- (the Shredder put away with 4: nothing to fire till you pick a slot)
	local now = os.clock()
	if io.UserInputType == Enum.UserInputType.MouseButton1 then
		trigger = true
		local _, _, root = myChar()
		if not root then return end
		if held == "katana" then swing(now)
		elseif not W[held].auto and now >= nextShot[held] then fireGun(now) end
	elseif io.UserInputType == Enum.UserInputType.MouseButton2 then
		aimHeld = true
		tryParry(now)
	elseif io.KeyCode == Enum.KeyCode.R then reload()
	end
end)
UserInputService.InputEnded:Connect(function(io: InputObject)
	if io.UserInputType == Enum.UserInputType.MouseButton1 then trigger = false
	elseif io.UserInputType == Enum.UserInputType.MouseButton2 then aimHeld = false end
end)
UserInputService.InputChanged:Connect(function(io: InputObject, gp: boolean)
	if gp or io.UserInputType ~= Enum.UserInputType.MouseWheel or toolOut() or menuOpen() or inHub() then return end
	local l = lo()
	local i = table.find(l, held) or 1
	i = (i - 1 + (if io.Position.Z > 0 then -1 else 1)) % #l + 1
	equip(l[i])
end)

-- ---------------------------------------------------------------- the third-person pose for everyone holding something
-- (the R15 arm raised to hold the weapon level; a melee swing whips it across; a guard lifts the blade overhead)
local poses: { [Motor6D]: { c0: CFrame, swingT: number, guardT: number } } = {}
-- the new avatar joints (AnimationConstraint) keep C0 read-only: their rest pose is the torso's shoulder attachment
local function getC0(sh: any): CFrame
	if sh:IsA("Motor6D") then return sh.C0 end
	local a = sh.Attachment0
	return if a then a.CFrame else CFrame.identity
end
local function setC0(sh: any, cf: CFrame)
	if sh:IsA("Motor6D") then sh.C0 = cf
	elseif sh.Attachment0 then sh.Attachment0.CFrame = cf end
end
local function shoulder(m: Model): Motor6D?
	local ua = m:FindFirstChild("RightUpperArm")
	return ua and ua:FindFirstChild("RightShoulder") :: Motor6D?
end
local function poseOf(m: Model?): { c0: CFrame, swingT: number, guardT: number }?
	if not m then return nil end
	local sh = shoulder(m)
	if not sh then return nil end
	local p = poses[sh]
	if not p then p = { c0 = getC0(sh), swingT = -math.huge, guardT = -math.huge }; poses[sh] = p end
	return p
end
local function poseStep(now: number)
	for sh, p in poses do
		if not sh.Parent then poses[sh] = nil; continue end
		local m = sh:FindFirstAncestorOfClass("Model")
		local wpn = m and m:FindFirstChild("HeldWeapon")
		if not wpn then setC0(sh, p.c0); continue end
		local isKat = wpn:GetAttribute("Weapon") == "katana"
		local rot = CFrame.Angles(if isKat then 0.95 else math.pi / 2, 0, 0)
		local st = now - p.swingT
		if st < 0.38 then -- the shared melee arm swing: yaw one way then back, pitch up
			local u = st / 0.38
			local yaw = 1.3 * math.sin(math.pi * u) * (if u < 0.35 then 1 else -1)
			rot = rot * CFrame.Angles(0.5 * math.sin(math.pi * u), yaw, 0)
		end
		local gt = now - p.guardT
		if gt < 0.56 then -- katana guard: up flat over the head, held, out
			local k = if gt < 0.05 then gt / 0.05 elseif gt < 0.35 then 1 else 1 - (gt - 0.35) / 0.21
			rot = rot:Lerp(CFrame.Angles(math.pi * 0.95, 0.75, 0), k)
		end
		setC0(sh, p.c0 * rot)
	end
end
local function watchModel(m: Model)
	local function check() if m:FindFirstChild("HeldWeapon") then poseOf(m) end end
	m.ChildAdded:Connect(check)
	check()
end
local function watchPlayer(p: Player)
	p.CharacterAdded:Connect(watchModel)
	if p.Character then watchModel(p.Character) end
end
for _, p in Players:GetPlayers() do watchPlayer(p) end
Players.PlayerAdded:Connect(watchPlayer)
task.spawn(function()
	local dummies = workspace:WaitForChild("Dummies", 10)
	if dummies then
		dummies.ChildAdded:Connect(function(m) if m:IsA("Model") then watchModel(m) end end)
		for _, m in dummies:GetChildren() do if m:IsA("Model") then watchModel(m) end end
	end
end)

-- ---------------------------------------------------------------- what the server says
remote("Dmg").OnClientEvent:Connect(function(d: any)
	if type(d) ~= "table" then return end
	local at = if typeof(d.at) == "Vector3" then d.at else nil
	local amt = if type(d.a) == "number" then d.a else 0
	if d.from == me.UserId then
		H.hit(d.hs == true)
		if d.hs then Sfx.play(if d.ko then "headshot_ko" else "headshot") else Sfx.play("hit") end
		if at then H.dmgNum(at, amt, d.hs == true) end
	end
	if d.to == me.UserId then
		if d.hs then Sfx.play(if d.ko then "headshot_taken_ko" else "headshot_taken") else Sfx.play("hurt") end
		H.hurt(amt)
	end
	if at then Fx.blood(at, Vector3.new(math.random() - 0.5, 0.3, math.random() - 0.5).Unit, amt) end
end)

remote("Kill").OnClientEvent:Connect(function(k: any)
	if type(k) ~= "table" or type(k.w) ~= "string" then return end
	local wid = if k.w == "void" and type(k.via) == "string" then k.via else k.w
	local victim = tostring(k.v)
	if not k.dummy then
		H.feed(if type(k.k) == "string" then k.k else nil, wid, victim, if k.w == "void" then "into the smog" else nil)
	end
	if k.kid == me.UserId then
		Sfx.play("kill")
		Hud.callout(if k.dummy then "dummy down" else "killed " .. victim, 1.4)
		if (k.w == "katana" or k.w == "parry") and type(k.kat) == "number" then
			task.delay(0.9, function() Hud.callout(("KATANA GROWS · %d kills"):format(k.kat), 1.2) end)
		end
	end
	if k.vid == me.UserId then
		Sfx.play("death")
		local wn = if W[wid] then W[wid].name else wid
		local killer = if type(k.k) == "string" then k.k else nil
		H.dead(if k.w == "void" then (if killer then ("%s knocked you into the smog  (%s)"):format(killer, wn) else "you fell into the smog")
			elseif killer then ("killed by %s  (%s)"):format(killer, wn) else "you died")
	end
end)

remote("Shot").OnClientEvent:Connect(function(s: any)
	if type(s) ~= "table" or type(s.ends) ~= "table" or s.by == me.UserId then return end
	local m = if typeof(s.model) == "Instance" then s.model :: Instance else nil
	local wpn = m and m:FindFirstChild("HeldWeapon")
	local root = wpn and (wpn :: Model).PrimaryPart
	local mz = root and root:FindFirstChild("Muzzle") :: Attachment?
	local head = m and m:FindFirstChild("Head") :: BasePart?
	local from = if mz then mz.WorldPosition elseif head then head.Position else nil
	if not from then return end
	local ends = {}
	for i, e in s.ends do if typeof(e) == "Vector3" and i <= 12 then table.insert(ends, e) end end
	local first = ends[1]
	local sw = if type(s.w) == "string" then W[s.w] else nil
	local sfx = (sw and sw.fx) or {}
	if first and (first - from).Magnitude > 0.1 then Fx.muzzle(CFrame.lookAt(from, first), sfx.big == true, false) end
	if sfx.spray then
		Fx.marbles(from, ends, 8)
	else
		for _, e in ends do Fx.tracer(from, e, (sw and sw.tracer) or TRACER, 0.045 * S, 0.2) end
	end
	if sw then Sfx.gun(sw, 0, from) end
	Fx.shotEnds(from, ends, sfx.spray == true) -- their holes, dust and splashes, seen here too
end)

remote("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" then return end
	local m = if typeof(f.model) == "Instance" and f.model:IsA("Model") then f.model :: Model else nil
	local now = os.clock()
	if f.k == "swing" then
		if f.by ~= me.UserId then
			local p = poseOf(m); if p then p.swingT = now end
			local r = m and m:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then Sfx.play("swing", r.Position) end
		end
	elseif f.k == "guard" then
		local p = poseOf(m); if p then p.guardT = now end
	elseif f.k == "parry" then
		local from = if typeof(f.from) == "Vector3" then f.from else nil
		local mine = f.by == me.UserId
		if from then
			Fx.sparks(from + Vector3.new(0, 1.5, 0), Vector3.yAxis, if f.pf then 40 else 26, if f.pf then 0.22 else 0.15)
			Sfx.play(if f.pf then "parry_perfect" else "parry", if mine then nil else from)
		end
		if f.kind == "shot" and f.pf and from and typeof(f.to) == "Vector3" then -- the bullets go home
			Fx.tracer(from, f.to, Color3.new(1, 1, 1), 0.07 * S, 0.3)
			Fx.tracer(from, f.to, Color3.fromRGB(159, 232, 255), 0.025 * S, 0.5)
			Sfx.play("ricochet", if mine then nil else from)
		end
		if mine then
			VM.hitStop = if f.pf then 0.13 else 0.09
			VM.jolt(if f.pf then 3 else 2)
			H.flash(if f.pf then 0.8 else 0.5, if f.pf then 0.3 else 0.2)
			shake = math.max(shake, if f.pf then 0.45 else 0.25)
		end
		if f.att == me.UserId and f.kind == "melee" and type(f.st) == "number" then -- your swing got parried
			staggerUntil = now + math.clamp(f.st, 0, 1)
			nextSwing = staggerUntil
			parryReady = math.max(parryReady, staggerUntil)
			VM.play("staggered")
			shake = math.max(shake, 0.45)
		end
	end
end)

remote("Ammo").OnClientEvent:Connect(function(wid: any, mag: any, left: any)
	if type(wid) ~= "string" or not ammo[wid] or type(mag) ~= "number" then return end
	ammo[wid].mag = mag
	ammo[wid].reloadUntil = if type(left) == "number" and left > 0 then os.clock() + left else 0
end)

remote("Patch").OnClientEvent:Connect(function(m: any)
	if type(m) ~= "table" then return end
	local function add(p: any)
		if type(p) == "table" and type(p.id) == "number" and typeof(p.c) == "Vector3" and type(p.r) == "number" and type(p.n) == "number" then
			Fx.patchAdd(p.id, p.c, p.r, math.min(p.n, 140))
		end
	end
	if m.op == "add" then add(m.p)
	elseif m.op == "list" and type(m.list) == "table" then for _, p in m.list do add(p) end
	elseif m.op == "thin" and type(m.id) == "number" and type(m.n) == "number" and type(m.r) == "number" then
		Fx.patchThin(m.id, m.n, m.r, if typeof(m.at) == "Vector3" then m.at else nil)
		if typeof(m.at) == "Vector3" and m.by ~= me.UserId then Sfx.play("clatter", m.at) end
	elseif m.op == "drop" and type(m.id) == "number" then Fx.patchDrop(m.id) end
end)

remote("Round").OnClientEvent:Connect(function(r: any)
	if type(r) ~= "table" then return end
	if r.start then
		H.hideEnd()
		Hud.callout("ROUND START", 1.4)
		Sfx.play("round_start")
	elseif r.over then
		Sfx.play("round_end")
		H.endScreen(if type(r.winner) == "string" then r.winner else nil, r.winnerId == me.UserId or r.youWon == true, if type(r.board) == "table" then r.board else {},
			if type(r.next) == "number" then r.next else 12, if type(r.nextLabel) == "string" then r.nextLabel else nil)
	elseif r.hub then -- back in the hub after a match
		H.hideEnd()
	end
end)

Body.onSlip = function(kind: string)
	Sfx.play("whoops"); Sfx.play("clatter")
	Hud.callout(if kind == "marbles" then "MARBLES!" else "WHOOPS!", 1.4)
end

me:GetAttributeChangedSignal("Kat"):Connect(function() VM.setKatana(kat()) end)

-- a fresh life: full mags, your gun out, no leftovers
me.CharacterAdded:Connect(function()
	resetAmmo()
	pending, staggerUntil, parryT, parryReady = nil, -math.huge, -math.huge, 0
	bloom, aim, shake = 0, 0, 0
	H.dead(nil)
	held = ""
	equip(lo()[1])
end)
if me.Character then task.defer(function() equip(lo()[1]) end) end
-- the server armed you (a spawn, or the loadout screen closing in the hub): fresh mags, slot 1 out
me:GetAttributeChangedSignal("ArmT"):Connect(function()
	resetAmmo()
	local _, hum = myChar()
	if hum and toolOut() then hum:UnequipTools() end
	held = ""
	equip(lo()[1])
end)
-- a new wrap (the loadout screen): rebuild what's in your hands with it
me:GetAttributeChangedSignal("Wraps"):Connect(function()
	if VM.model and held ~= "" and held ~= "shredder" then VM.set(held, kat()) end
end)

-- ---------------------------------------------------------------- every frame
RunService.RenderStepped:Connect(function(dt: number)
	local now = os.clock()
	local _, hum, root = myChar()
	local w = W[held]
	shake = math.max(0, shake - dt * 2.2)
	bloom = math.max(0, bloom - 0.06 * dt)
	-- reload finishes on its own clock
	local a = ammo[held]
	if a and a.reloadUntil > 0 and now >= a.reloadUntil then a.mag = w.mag :: number; a.reloadUntil = 0 end
	local reloading = a ~= nil and a.reloadUntil > 0
	-- aim down sights (can't while reloading): in ~0.14 s, out in ~0.125 s
	local canAim = w and w.ads ~= nil and not reloading and hum ~= nil
	aim = math.clamp(aim + (if aimHeld and canAim then 7 else -8) * dt, 0, 1)
	-- the base FOV is the P-menu slider's (JankSettings sets the BaseFov attribute); ADS zooms from it
	local fovAttr = me:GetAttribute("BaseFov")
	local baseFov = if type(fovAttr) == "number" then fovAttr else 70
	if w and w.ads then camera.FieldOfView = baseFov / (1 + (w.ads.zoom - 1) * aim) else camera.FieldOfView = baseFov end
	-- full auto
	local holstered = inHub()
	if holstered then trigger, aimHeld = false, false; if hum and toolOut() then hum:UnequipTools() end end
	if hum and trigger and w and w.auto and not toolOut() and not menuOpen() and now >= (nextShot[held] or 0) then
		local n = 0
		while trigger and now >= nextShot[held] and n < 4 and (ammo[held] :: any).mag > 0 and (ammo[held] :: any).reloadUntil == 0 do fireGun(now); n += 1 end
		if (ammo[held] :: any).mag <= 0 and (ammo[held] :: any).reloadUntil == 0 then reload() end
	end
	if pending and now >= pending.t then resolveSwing() end
	if hum and parryBuf > -math.huge and now - parryBuf < 0.25 and now >= parryReady and not pending and now >= staggerUntil then tryParry(now) end
	-- the parry ring
	if held == "katana" then
		if now - parryT < P.win then H.parryRing("open", 1)
		elseif now < parryReady then H.parryRing("drain", 1 - (parryReady - now) / P.cd)
		elseif now - parryReady < 0.25 then H.parryRing("ready", 1)
		else H.parryRing("hidden", 0) end
	else H.parryRing("hidden", 0) end
	-- the viewmodel (hidden in third person: your character holds it)
	local st = Body.st
	local spd = if root then Vector3.new(root.AssemblyLinearVelocity.X, 0, root.AssemblyLinearVelocity.Z).Magnitude else 0
	if VM.model then
		local tp = thirdPerson() or hum == nil or toolOut() or menuOpen() or holstered
		for _, d in VM.model:GetDescendants() do
			if d:IsA("BasePart") and d.Name ~= "Root" then d.LocalTransparencyModifier = if tp then 1 else 0 end
		end
		VM.update(dt, {
			aim = aim, speed = spd, sprint = st ~= nil and st.sprinting, slide = st ~= nil and st.sliding,
			grounded = st ~= nil and st.onGround, hp = hp(), firedT = firedT, slipping = Body.slipping(), now = now,
			sight = VM.adsPos(held),
		})
		-- the katana's smear, after the blade has moved this frame
		smearStep(now, tp)
	else
		smearStep(now, true)
	end
	H.step(dt, aim, false)
	H.hp(hp())
	-- the Shredder (key 4) out: its name and heat in the panel instead of the gun it put away
	local tool = toolOut() and me.Character and me.Character:FindFirstChildOfClass("Tool")
	if tool and tool.Name == "Shredder" then
		local heat = tool:GetAttribute("Heat")
		H.weapon("shredder", nil, false, 0, if tool:GetAttribute("Hot") then "OVERHEATED" else ("heat %d%%"):format(math.floor((if type(heat) == "number" then heat else 0) * 100 + 0.5)))
	elseif holstered then
		H.weapon(held, a and a.mag, reloading, kat(), "HOLSTERED")
	else
		H.weapon(held, a and a.mag, reloading, kat())
	end
	-- the top line: in a match its mode, round, score and clock (Matches.luau); else where you are
	local mh = me:GetAttribute("MatchHud")
	if type(mh) == "string" then
		local ends = me:GetAttribute("RoundEnds")
		local clock = ""
		if type(ends) == "number" then
			local left = math.max(0, ends - workspace:GetServerTimeNow())
			clock = (" · %d:%02d"):format(math.floor(left / 60), math.floor(left) % 60)
		end
		H.top(mh .. clock)
	elseif me:GetAttribute("Zone") == "training" then
		H.top("TRAINING · the dummies hit back in here")
	else
		H.top("HUB · weapons away · step on a pad to play · training behind you")
	end
	poseStep(now)
end)
