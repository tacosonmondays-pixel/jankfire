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
local MatchUi = require(script.Parent:WaitForChild("MatchUi"))
local Maps = require(Shared:WaitForChild("Maps"))
local Lighting = game:GetService("Lighting")
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(n: string): RemoteEvent return Remotes:WaitForChild(n) :: RemoteEvent end
local EquipR, FireR, ReloadR, SwingR, MeleeR, ParryR = remote("Equip"), remote("Fire"), remote("Reload"), remote("Swing"), remote("MeleeHit"), remote("Parry")
local MatchState = ReplicatedStorage:WaitForChild("Match")

local W = Weapons.list
local S = Weapons.S
local P = Weapons.PARRY
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
local smear: Trail? = nil

-- your loadout (the server sets it: the default three, or what you picked on the Range) and your room
local function loadout(): { string }
	local v = me:GetAttribute("Loadout")
	local out = {}
	if type(v) == "string" then for w in string.gmatch(v, "[^,]+") do if W[w] then table.insert(out, w) end end end
	return if #out == 3 then out else table.clone(Weapons.loadout)
end
local function myRoom(): string
	local r = me:GetAttribute("Room")
	return if type(r) == "string" then r else "ffa"
end
local function resetAmmo()
	for _, id in loadout() do
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
	-- only who's in your room: the match has people and bots, the Range has people and dummies
	local room = myRoom()
	for _, p in Players:GetPlayers() do
		local pr = p:GetAttribute("Room")
		if p ~= me and p.Character and (pr == nil or pr == room) then addModel(p.Character) end
	end
	local d = workspace:FindFirstChild(if room == "training" then "Dummies" else "Bots")
	if d then for _, m in d:GetChildren() do if m:IsA("Model") then addModel(m) end end end
	return out
end

local voteOpenRef: () -> boolean = function() return false end
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
	-- a menu open (the weapon picker, the vote): free the mouse so the cards can be clicked
	if MatchUi.pickerOpen() or voteOpenRef() then
		UserInputService.MouseBehavior = Enum.MouseBehavior.Default
		UserInputService.MouseIconEnabled = true
	end
end)

-- ---------------------------------------------------------------- swapping, reloading
local function setSmear()
	smear = nil
	local m = VM.model
	local root = m and m.PrimaryPart
	local a0 = root and root:FindFirstChild("Muzzle") :: Attachment?
	local a1 = root and root:FindFirstChild("Mid") :: Attachment?
	if not a0 or not a1 then return end
	local t = Instance.new("Trail")
	t.Attachment0 = a0; t.Attachment1 = a1; t.Lifetime = 0.18; t.Enabled = false; t.FaceCamera = false
	t.Color = ColorSequence.new(Color3.new(1, 1, 1)); t.LightEmission = 0.7
	t.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
	t.Parent = root
	smear = t
end

local function equip(wid: string)
	if wid == held and VM.model then return end
	if not W[wid] then return end
	local a = ammo[held]
	if a and a.reloadUntil > 0 then a.reloadUntil = 0 end -- swapping cancels a reload
	held = wid
	equipT = os.clock()
	aim = 0
	VM.set(wid, kat())
	setSmear()
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
	VM.play("reload_" .. held)
end

VM.onEvent = function(ev: string)
	if ev == "whoosh" then Sfx.play("swing")
	elseif ev == "shing" then Sfx.play("ting")
	elseif ev == "click" then Sfx.play("click")
	elseif ev == "glug" then Sfx.play("glug")
	elseif ev == "revUp" then Sfx.play("rev_up")
	elseif ev == "rattle" then Sfx.play("marble"); Sfx.play("marble", nil, 0.7, 1.2)
	elseif ev == "boing" then Sfx.play("boing")
	elseif ev == "thwack" then Sfx.play("thwack") end
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
	if myRoom() ~= "training" then a.mag -= 1 end -- the Range: infinite ammo
	firedT = now
	local eye, look = eyeAndAim()
	local spread = ((w.spread or 0) + bloom) * (1 + ((if w.ads then w.ads.spread else 1) - 1) * aim)
	local map = workspace:FindFirstChild("Map")
	mapParams.FilterDescendantsInstances = { map :: Instance }
	local tg = targets()
	local hits: { [Model]: { n: number, h: number } } = {}
	local ends: { Vector3 } = {}
	local allEnds: { Vector3 } = {}
	local impacts: { { Vector3 } } = {}
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
		if who then
			local g = hits[who] or { n = 0, h = 0 }
			g.n += 1; if head then g.h += 1 end
			hits[who] = g
		elseif mh and #impacts < 6 then table.insert(impacts, { mh.Position, mh.Normal }) end
	end
	local list = {}
	for m, g in hits do table.insert(list, { m = m, n = g.n, h = g.h }) end
	FireR:FireServer(held, eye, ends, list)
	-- your own feel: shove, climb, bloom, the gun kicks, flash, brass, tracer / marbles, sound
	Body.push(-look * (w.recoil or 0))
	kickCam((w.kick or 0) * (0.6 + math.random() * 0.8) * (1 - 0.5 * aim), (math.random() - 0.5) * (w.kick or 0) * 0.5)
	bloom = math.min(w.maxBloom or 0, bloom + (w.bloom or 0))
	VM.kick(w.recoilVM, if aim > 0.5 then 0.6 else 1, (w.rate or 0) > 8)
	local mz = VM.attachment("Muzzle") or (eye + look * 2)
	local fpv = not thirdPerson()
	if fpv then Fx.flash(CFrame.lookAt(mz, mz + look), held == "marbles") end
	if held == "redline" then
		local port = VM.attachment("Port")
		if port and fpv then Fx.brass(CFrame.lookAt(port, port + look) * CFrame.Angles(0, 0, 0), false) end
		for _, e in ends do Fx.tracer(mz, e, w.tracer :: Color3, 0.045 * S, 0.2) end
		Sfx.redline(Weapons.tacho(hp()), nil)
	else
		Fx.marbles(mz, allEnds, 1) -- no tracers: the marbles are the tracers
		Sfx.play("gun_marbles")
	end
	for _, im in impacts do Fx.impact(im[1], im[2]) end
	shake = math.max(shake, if held == "marbles" then 0.35 else 0.06)
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
	if #hitList == 0 then return end
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
local KEYS = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4 }
local voteOpen: string? = nil -- the open vote stage: 1-4 vote instead of swapping
voteOpenRef = function() return voteOpen ~= nil end
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp then return end
	local now = os.clock()
	if io.KeyCode == Enum.KeyCode.T then MatchUi.onRoom(if myRoom() == "training" then "ffa" else "training"); return end
	if io.KeyCode == Enum.KeyCode.B then MatchUi.togglePicker(); return end
	if voteOpen and KEYS[io.KeyCode] then MatchUi.pick(KEYS[io.KeyCode]); return end
	if MatchUi.pickerOpen() then return end
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
	elseif KEYS[io.KeyCode] and loadout()[KEYS[io.KeyCode]] then equip(loadout()[KEYS[io.KeyCode]])
	end
end)
UserInputService.InputEnded:Connect(function(io: InputObject)
	if io.UserInputType == Enum.UserInputType.MouseButton1 then trigger = false
	elseif io.UserInputType == Enum.UserInputType.MouseButton2 then aimHeld = false end
end)
UserInputService.InputChanged:Connect(function(io: InputObject, gp: boolean)
	if gp or io.UserInputType ~= Enum.UserInputType.MouseWheel then return end
	local lo = loadout()
	local i = table.find(lo, held) or 1
	i = (i - 1 + (if io.Position.Z > 0 then -1 else 1)) % #lo + 1
	equip(lo[i])
end)

-- ---------------------------------------------------------------- the third-person pose for everyone holding something
-- (the R15 arm raised to hold the weapon level; a melee swing whips it across; a guard lifts the blade overhead)
local poses: { [Motor6D]: { c0: CFrame, swingT: number, guardT: number } } = {}
local function shoulder(m: Model): Motor6D?
	local ua = m:FindFirstChild("RightUpperArm")
	return ua and ua:FindFirstChild("RightShoulder") :: Motor6D?
end
local function poseOf(m: Model?): { c0: CFrame, swingT: number, guardT: number }?
	if not m then return nil end
	local sh = shoulder(m)
	if not sh then return nil end
	local p = poses[sh]
	if not p then p = { c0 = sh.C0, swingT = -math.huge, guardT = -math.huge }; poses[sh] = p end
	return p
end
local function poseStep(now: number)
	for sh, p in poses do
		if not sh.Parent then poses[sh] = nil; continue end
		local m = sh:FindFirstAncestorOfClass("Model")
		local wpn = m and m:FindFirstChild("HeldWeapon")
		if not wpn then sh.C0 = p.c0; continue end
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
		sh.C0 = p.c0 * rot
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
for _, fname in { "Dummies", "Bots" } do
	task.spawn(function()
		local fo = workspace:WaitForChild(fname, 10)
		if fo then
			fo.ChildAdded:Connect(function(m) if m:IsA("Model") then watchModel(m) end end)
			for _, m in fo:GetChildren() do if m:IsA("Model") then watchModel(m) end end
		end
	end)
end

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
	if not k.dummy and (k.room == nil or k.room == myRoom()) then
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
	if s.w == "marbles" then
		Fx.marbles(from, ends, 8)
		Sfx.play("gun_marbles", from)
	else
		for _, e in ends do Fx.tracer(from, e, W.redline.tracer :: Color3, 0.045 * S, 0.2) end
		Sfx.redline(0, from)
	end
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
		MatchUi.voteDone(); voteOpen = nil
		if myRoom() == "ffa" then
			Hud.callout("ROUND START", 1.4)
			Sfx.play("round_start")
		end
	elseif r.over then
		if myRoom() ~= "ffa" then return end -- (on the Range: the match's end screen isn't yours)
		Sfx.play("round_end")
		H.endScreen(if type(r.winner) == "string" then r.winner else nil, r.winnerId == me.UserId, if type(r.board) == "table" then r.board else {}, if type(r.next) == "number" then r.next else 12)
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
	equip(loadout()[1])
end)
if me.Character then task.defer(function() equip(loadout()[1]) end) end
-- a new loadout (the Range's picker): fresh mags for anything new, swap off a weapon you no longer carry
me:GetAttributeChangedSignal("Loadout"):Connect(function()
	local lo = loadout()
	for _, id in lo do if W[id].mag and not ammo[id] then ammo[id] = { mag = W[id].mag :: number, reloadUntil = 0 } end; nextShot[id] = nextShot[id] or 0 end
	if not table.find(lo, held) then held = ""; equip(lo[1]) end
end)

-- ---------------------------------------------------------------- step 3: the room button, the picker, the vote
MatchUi.onRoom = function(room: string) remote("Room"):FireServer(room) end
MatchUi.onLoadout = function(list: { string }) remote("Loadout"):FireServer(list) end
MatchUi.onVote = function(stage: string, i: number) remote("Vote"):FireServer(stage, i) end
remote("Vote").OnClientEvent:Connect(function(v: any)
	if type(v) ~= "table" then return end
	if myRoom() ~= "ffa" then MatchUi.voteDone(); voteOpen = nil; return end -- (the Range doesn't vote)
	if v.op == "stage" and type(v.cards) == "table" and type(v.stage) == "string" then
		H.hideEnd()
		MatchUi.voteStage(v.stage, v.cards, if type(v.ends) == "number" then v.ends else 0, v.single == true)
		voteOpen = if v.single then nil else v.stage
	elseif v.op == "counts" and type(v.counts) == "table" then MatchUi.voteCounts(v.stage, v.counts)
	elseif v.op == "result" and type(v.win) == "number" then MatchUi.voteResult(v.stage, v.win, if type(v.counts) == "table" then v.counts else {}); voteOpen = nil
	elseif v.op == "reveal" then MatchUi.reveal(tostring(v.gameName), tostring(v.mapName)); voteOpen = nil
	elseif v.op == "done" then MatchUi.voteDone(); voteOpen = nil end
end)

-- each map's own sky: the Range is a sunny afternoon, Rooftop keeps the place's night (client-side lighting)
local night = { ClockTime = Lighting.ClockTime, Brightness = Lighting.Brightness, Ambient = Lighting.Ambient, OutdoorAmbient = Lighting.OutdoorAmbient, FogColor = Lighting.FogColor, FogStart = Lighting.FogStart, FogEnd = Lighting.FogEnd }
local litFor = ""
local function lightFor(pos: Vector3)
	local m = Maps.at(pos)
	local id = m and m:GetAttribute("MapId")
	if type(id) ~= "string" or id == litFor then return end
	litFor = id
	if id == "range" then
		local fc, fs, fe = m:GetAttribute("FogColor"), m:GetAttribute("FogStart"), m:GetAttribute("FogEnd")
		Lighting.ClockTime = 14.5; Lighting.Brightness = 2.2
		Lighting.Ambient = Color3.fromRGB(120, 130, 150); Lighting.OutdoorAmbient = Color3.fromRGB(150, 165, 190)
		if typeof(fc) == "Color3" then Lighting.FogColor = fc end
		if type(fs) == "number" then Lighting.FogStart = fs end
		if type(fe) == "number" then Lighting.FogEnd = fe end
	else
		for k, v in night do (Lighting :: any)[k] = v end
	end
end

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
	if w and w.ads then camera.FieldOfView = 70 / (1 + (w.ads.zoom - 1) * aim) else camera.FieldOfView = 70 end
	-- full auto
	if hum and trigger and w and w.auto and now >= (nextShot[held] or 0) then
		local n = 0
		while trigger and now >= nextShot[held] and n < 4 and (ammo[held] :: any).mag > 0 and (ammo[held] :: any).reloadUntil == 0 do fireGun(now); n += 1 end
		if (ammo[held] :: any).mag <= 0 and (ammo[held] :: any).reloadUntil == 0 then reload() end
	end
	if pending and now >= pending.t then resolveSwing() end
	if hum and parryBuf > -math.huge and now - parryBuf < 0.25 and now >= parryReady and not pending and now >= staggerUntil then tryParry(now) end
	-- the katana's smear during the clip's trail window
	if smear then
		local c = VM.playing()
		local an = c and Anims[c]
		smear.Enabled = an ~= nil and an.trail ~= nil and true or false
	end
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
		local tp = thirdPerson() or hum == nil
		for _, d in VM.model:GetDescendants() do
			if d:IsA("BasePart") and d.Name ~= "Root" then d.LocalTransparencyModifier = if tp then 1 else 0 end
		end
		VM.update(dt, {
			aim = aim, speed = spd, sprint = st ~= nil and st.sprinting, slide = st ~= nil and st.sliding,
			grounded = st ~= nil and st.onGround, hp = hp(), firedT = firedT, slipping = Body.slipping(), now = now,
			sight = VM.adsPos(held),
		})
	end
	H.step(dt, aim, false)
	H.hp(hp())
	H.weapon(held, a and a.mag, reloading, kat())
	local ends = MatchState:GetAttribute("EndsAt")
	local target = MatchState:GetAttribute("Target")
	local kills = me:GetAttribute("Kills")
	if root then lightFor(root.Position) end
	MatchUi.step()
	if myRoom() == "training" then H.roundLine("TRAINING · nobody is judging · B weapons · T leave")
	elseif type(ends) == "number" and type(target) == "number" then
		H.round(target, if MatchState:GetAttribute("Phase") == "live" then ends - workspace:GetServerTimeNow() else 0, if type(kills) == "number" then kills else 0)
	end
	poseStep(now)
end)
