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
local Items = require(Shared:WaitForChild("Items")) -- (a death by frag names the frag)
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Anims = require(Shared:WaitForChild("Anims")) :: any
local Hud = require(script.Parent:WaitForChild("Hud"))
local H = require(script.Parent:WaitForChild("FightHud"))
local VM = require(script.Parent:WaitForChild("Viewmodel"))
local Fx = require(script.Parent:WaitForChild("Fx"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Body = require(script.Parent:WaitForChild("Body"))
local Binds = require(script.Parent:WaitForChild("Binds")) :: any -- (the keys as the player bound them, hold or toggle aim: Settings)
local Settings = require(script.Parent:WaitForChild("Settings")) :: any
-- every body handling its weapon in third person (ThirdPerson.luau). if it ever fails to load, the weapons still work
local TP: any = nil
do
	local ok, m = pcall(require, script.Parent:WaitForChild("ThirdPerson"))
	if ok then TP = m else
		warn("[Arsenal] ThirdPerson didn't load: " .. tostring(m))
		local nop = function(...) end
		TP = { muzzle = function(_: any): Vector3? return nil end, fired = nop, reload = nop, cancelReload = nop, swing = nop, parry = nop, mine = nop }
	end
end
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(n: string): RemoteEvent return Remotes:WaitForChild(n) :: RemoteEvent end
local EquipR, FireR, ReloadR, SwingR, MeleeR, ParryR = remote("Equip"), remote("Fire"), remote("Reload"), remote("Swing"), remote("MeleeHit"), remote("Parry")
local AimR = remote("Aim") -- the sights of a scoped gun going up / coming down (the server times quick-scopes itself)
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
local pending: { t: number, w: string?, heavy: boolean? }? = nil -- (the swing waiting for its hit time: which weapon, a heavy stab)
local parryT, parryReady, parryBuf = -math.huge, 0, -math.huge
-- the held guard (18 Nov 2026): up while right click is held (to PARRY.hold), when it closed, the last "turn" sent,
-- the last parry sound (a spray's are spaced out). the wave's no-swing time is the attribute KatanaCast (Katana.client)
local guard = { up = false, close = -math.huge, turn = 0, snd = 0 }
local staggerUntil = -math.huge
local shake = 0
local view = { pitch = 0, yaw = 0 } -- the visual offsets applied to the camera last frame (removed again next frame)
local equipT = 0
-- batch 3: when the trigger went down (the Revolver fans after a hold), the Hat Trick's shots still to come in this
-- burst, the next fanned shot, the scope (up = the overlay is on), what the server was last told about the sights
local pressT = -math.huge
local burstLeft = 0
local fanNext = 0
local fanArmed = false -- a fan needs a fresh click after running dry, reloading or aiming
-- (weapons batch A) the Minigun's barrels: spin 0..1, whether the server was told the trigger is down, the motor's
-- looped whine (a Sound of ours while it spins), GunParts (it turns the barrels from GunParts.mySpin)
local minigun = { spin = 0, on = false, snd = nil :: Sound?, parts = require(script.Parent:WaitForChild("GunParts")) :: any, zapNext = 0 } -- (zapNext: the Taser's next click)
-- (weapons batch B) the held-trigger weapons (the Leaf Blower, the Hot Sauce, the Big Laser Pointer): HoldClient
minigun.hold = require(script.Parent:WaitForChild("HoldClient")) :: any
-- the Hot Sauce's swig (18 Nov 2026): HoldClient.charging() says ("cig", 0..1 of the 3 s swig) while its trigger is
-- down; the viewmodel brings the bottle up to your mouth (VM.update's swig). nil when not swigging
function minigun.swig(): number?
	local h = minigun.hold
	if held ~= "cig" or not h or type(h.charging) ~= "function" then return nil end
	local ok, wid, k = pcall(h.charging)
	if not ok or wid ~= "cig" then return nil end
	return if type(k) == "number" then math.clamp(k, 0, 1) else 0
end
-- the Bow (18 Nov 2026): ProjClient.drawn() is how far it's drawn (0..1) while ProjClient.bowT says you're drawing; the
-- viewmodel pulls the string and your hand back by it (VM.update's draw). nil when not drawing
function minigun.bowDraw(): number?
	local p = minigun.proj
	if held ~= "bow" or not p or p.bowT == nil or type(p.drawn) ~= "function" then return nil end
	local ok, d = pcall(p.drawn)
	return if ok and type(d) == "number" then math.clamp(d, 0, 1) else 0
end
-- (weapons batch C) the projectile weapons (the Chicken Rocket, the Peel Shooter, the Tennis Ball Launcher, the
-- Snowball, the Blood Cross): ProjClient sends the click, the server flies them
minigun.proj = require(script.Parent:WaitForChild("ProjClient")) :: any
-- (the Scythe's two forms) mid-switch till formUntil; the form each two-form weapon was last in (its slot key takes that
-- one out again); when your last shot went off (no switch right after a shot)
minigun.formUntil, minigun.lastForm, minigun.shotT = 0, {} :: { [string]: string }, -math.huge
-- (weapons batch D) the TV Remote's clicks and the Scales' pillar: the server picks the target and gates the cooldowns
-- (WeaponTricks.server); these only keep you from spamming the remotes
minigun.trickNext = {} :: { [string]: number }
minigun.cards = require(script.Parent:WaitForChild("CardsClient")) :: any -- (batch E: the Card Deck's hand)
minigun.lasso = require(script.Parent:WaitForChild("LassoClient")) :: any -- (batch E: the Lasso)
minigun.rig = require(script.Parent:WaitForChild("RigClient")) :: any -- (the Overdrive Rig gadget: its buttons while suited up)
function minigun.trick(name: string, op: string?, cd: number)
	local t = os.clock()
	local key = name .. (op or "")
	if t < (minigun.trickNext[key] or 0) then return end
	minigun.trickNext[key] = t + math.min(cd, 0.5)
	local r = Remotes:FindFirstChild(name)
	if not r or not r:IsA("RemoteEvent") then return end
	local lk = workspace.CurrentCamera.CFrame.LookVector
	if op then r:FireServer(op, lk) else r:FireServer(lk) end
end
function minigun.send(on: boolean)
	local r = Remotes:FindFirstChild("Spin")
	if r and r:IsA("RemoteEvent") then r:FireServer(on) end
end
function minigun.loop(on: boolean, vol: number, pitch: number)
	local s = minigun.snd
	if on and not s then
		local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
		local src = lib and lib:FindFirstChild("minigun_spin")
		if not (src and src:IsA("Sound")) then return end
		local c = src:Clone()
		c.Looped = true
		c:SetAttribute("BaseVol", src.Volume)
		c.Parent = game:GetService("SoundService")
		c:Play()
		minigun.snd, s = c, c
	elseif not on and s then
		s:Destroy()
		minigun.snd = nil
		return
	end
	if s then
		s.Volume = (tonumber(s:GetAttribute("BaseVol")) or 0.5) * vol
		s.PlaybackSpeed = pitch
	end
end
local scoped, scopedAt = false, -math.huge
local aimSent = false

-- your loadout (the server sets it on every arm, Loadout.luau): the weapons on keys 1 2 3. a classic mode's kit can be
-- fewer (Modes.luau: gun game's one weapon, one in the chamber's two)
local function lo(): { string }
	local s = me:GetAttribute("Loadout")
	if type(s) ~= "string" then return Weapons.loadout end
	local out = {}
	for id in string.gmatch(s, "[^,]+") do if W[id] then table.insert(out, id) end end
	return if #out >= 1 and #out <= 3 then out else Weapons.loadout
end
-- the loadout screen is up (LoadoutUI): hands off the weapons
local function menuOpen(): boolean return me:GetAttribute("LoadoutOpen") == true end

local function resetAmmo()
	for _, id in lo() do
		local w = W[id]
		if w.mag then ammo[id] = { mag = w.mag, reloadUntil = 0 } end
		nextShot[id] = 0
		if w.hands == 2 and w.mag then ammo[id .. "@2"] = { mag = w.mag, reloadUntil = 0 }; nextShot[id .. "@2"] = 0 end -- (Lefty & Righty's right gun)
		local alt = w.form and W[w.form.to] -- (the Scythe's rifle: its own mag, Rules.arm)
		if alt then
			if alt.mag then ammo[alt.id] = { mag = alt.mag, reloadUntil = 0 } end
			nextShot[alt.id] = 0
		end
	end
	minigun.formUntil = 0
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
	return me:GetAttribute("Zone") == "hub" and me:GetAttribute("DevArms") ~= true -- (DevArms: the owner's dev weapons, OwnerDev)
end
-- the muzzle of the gun a character holds (third person: yours, or someone else's)
local function heldMuzzle(m: Instance?, hand: number?): Vector3?
	local tp = TP.muzzle(m, hand) -- (the gun as everyone sees it held: ThirdPerson; hand 1: Lefty's)
	if tp then return tp end
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
	-- (third person is on: the shoulder camera can come in closer than that in a tight corner. scoped in from third
	-- person (TPScope, ShoulderCam) is first person: the scope, the shot from your eye)
	return (me:GetAttribute("ThirdPerson") == true and me:GetAttribute("TPScope") ~= true)
		or (root ~= nil and (camera.CFrame.Position - root.Position).Magnitude > 4.5)
end
-- the eye (feet + 1.6 m, lower when crouched: the camera itself in first person), and where you're aiming. In third
-- person: from the eye to what's under the crosshair (TP.crosshair: the map or a body's hit box), so the shot lands
-- on the crosshair even up close, with the camera over your shoulder
local function eyeAndAim(): (Vector3, Vector3)
	local _, _, root = myChar()
	local cam = camera.CFrame
	if not root or not thirdPerson() then return cam.Position, cam.LookVector end
	local eye = root.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0)
	local target: Vector3
	if TP.crosshair then
		target = TP.crosshair(eye)
	else
		local hit = Fx.castMap(cam.Position, cam.LookVector * 900)
		target = if hit then hit.Position else cam.Position + cam.LookVector * 900
	end
	local to = target - eye
	return eye, if to.Magnitude > 1 then to.Unit else cam.LookVector
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
-- (weapons batch B) the Taser's click: who's under your crosshair goes with it, and the server (Combat Zap) decides
-- who the darts really hit; the darts, the bolts and the stun come back to everyone as Fx "zap" (WeaponStates)
function minigun.zap(now: number)
	local w = W[held]
	if not w or now < (minigun.zapNext or 0) then return end
	minigun.zapNext = now + (w.cd or 1)
	local eye, look = eyeAndAim()
	local best: Model?, bd = nil, math.huge
	for _, t in targets() do
		local tt = Hitbox.ray(eye, look, t.feet, Hitbox.distScale((t.feet - eye).Magnitude), 1.5)
		if tt and tt < bd and tt <= w.range then best, bd = t.m, tt end
	end
	local r = Remotes:FindFirstChild("Zap")
	if r and r:IsA("RemoteEvent") then r:FireServer(held, eye, look, best) end
	Sfx.play(w.snd or "click")
	VM.kick(w.recoilVM, 0.8, false, 1, 1)
	VM.shot(w)
end

-- ---------------------------------------------------------------- camera: kick + punch/shake (visual)
-- the kick climbs the real look (the web game's, cut by VM.feel's climb); since 17 Nov 2026 (the owner: "can the gun
-- not shoot up when you shoot or at least not as aggressively?") what a shot climbed eases back toward where you aimed
-- once the gun's hold after its last shot is over (a ~0.1 s ease), and a steady part of it (the gun's pull) even
-- while you keep firing, so sustained fire no longer walks off the target (the Redline at low HP fires faster than
-- any hold). only the climb is taken back: your own mouse moves stay yours
local climb = { p = 0, y = 0, t = 0, hold = 0.06, pull = 0 }
local function kickCam(pitch: number, yaw: number, hold: number?, pull: number?)
	camera.CFrame = camera.CFrame * CFrame.Angles(pitch, yaw, 0)
	climb.p += pitch; climb.y += yaw; climb.t = os.clock(); climb.hold = hold or 0.06; climb.pull = pull or 0
end
RunService:BindToRenderStep("JankfireCamera", Enum.RenderPriority.Camera.Value + 1, function(dt: number)
	local back = if os.clock() - climb.t > climb.hold then 12 else climb.pull
	if (climb.p ~= 0 or climb.y ~= 0) and back > 0 then
		local k = 1 - math.exp(-back * dt)
		local dp, dy = climb.p * k, climb.y * k
		if math.abs(climb.p) < 1e-4 and math.abs(climb.y) < 1e-4 then dp, dy = climb.p, climb.y end
		camera.CFrame = camera.CFrame * CFrame.Angles(-dp, -dy, 0)
		climb.p -= dp; climb.y -= dy
	end
	-- the camera module reads the look back each frame, so visual offsets are applied as a change from last frame's
	local pr = VM.punch()
	local px, py, pz = pr:ToEulerAnglesXYZ()
	local sk = if Settings.get("gfx.shake") == false then 0 else shake -- (Settings > CONTROLS: SCREEN SHAKE)
	local sx, sy = (math.random() - 0.5) * sk * 0.02, (math.random() - 0.5) * sk * 0.02
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
			Fx.bladeFlames(VM.model, mid.WorldPosition, tip.WorldPosition) -- (an angel katana: flame tongues off the blade)
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
	-- (an angel katana: the smear takes its spray's glow colour, Fx.bladeGlow)
	local smearCol = Fx.bladeGlow(VM.model) or Color3.fromRGB(225, 240, 255)
	for i = 1, used do local w = smearPool[i]; if w.Color ~= smearCol then w.Color = smearCol end end
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
	if a and a.reloadUntil > 0 then a.reloadUntil = 0; TP.cancelReload() end
	held = "shredder"
	equipT = os.clock()
	aim = 0
	VM.set("shredder", 0) -- (no viewmodel: the Tool is the model)
	hum:EquipTool(tool)
	EquipR:FireServer("shredder")
	Sfx.play("click")
end

local function equip(wid: string)
	if me:GetAttribute("Rig") ~= nil then return end -- (the Overdrive Rig: no weapon swaps while suited up)
	if wid == "shredder" then equipShredder(); return end
	if wid == held and VM.model then return end
	if not W[wid] then return end
	if toolOut() then local _, hum = myChar(); if hum then hum:UnequipTools() end end
	local a = ammo[held]
	if a and a.reloadUntil > 0 then a.reloadUntil = 0; TP.cancelReload() end -- swapping cancels a reload
	held = wid
	equipT = os.clock()
	aim = 0
	burstLeft = 0
	if Binds.toggles("aim") then aimHeld = false end -- (a toggled aim doesn't carry over to the next weapon)
	VM.set(wid, kat())
	table.clear(smearPts)
	EquipR:FireServer(wid)
	Sfx.play("click")
end

-- the key "form" (Q) with the Scythe out: it turns into its rifle, or back (Rules.equip checks the same: not mid-swing,
-- mid-shot, mid-dash or mid-switch). the blade and scope move across (GunParts), nothing fires or swings till it's done
function minigun.form(now: number)
	local w = W[held]
	local F = w and w.form
	if not F or not W[F.to] or Body.stunned() or Body.dashing() then return end
	if now < minigun.formUntil or now < staggerUntil or pending then return end
	if now - lastSwing < F.swingLock or now - minigun.shotT < F.shotLock then return end
	minigun.formUntil = now + F.time
	minigun.lastForm[w.formOf or held] = F.to
	minigun.parts.myFormT = now
	equip(F.to)
	VM.play("form_scythe")
	Sfx.play("scythe_form") -- (a metal slide and the lock: the sound session's, v816)
	if W[F.to].kind == "hitscan" then
		nextShot[F.to] = math.max(nextShot[F.to] or 0, now + F.time + F.fireDelay)
	else
		nextSwing = math.max(nextSwing, now + F.time)
	end
end

local function reload(hand: number?): boolean
	local w = W[held]
	local a = ammo[if hand == 2 and w and w.hands == 2 then held .. "@2" else held]
	if not a or not w.mag or a.reloadUntil > 0 or a.mag >= w.mag then return false end
	if os.clock() < minigun.formUntil then return false end -- (mid-switch: the Scythe's rifle reloads once it's a rifle)
	if me:GetAttribute("NoReload") then return false end -- (one in the chamber: kills are the only bullets, Modes.luau)
	a.reloadUntil = os.clock() + (w.reload :: number)
	aim = 0
	burstLeft = 0
	fanArmed = false
	ReloadR:FireServer(held, hand)
	if w.reloadSnd then Sfx.play(w.reloadSnd) end -- (a whole reload's own recording: the Minigun's ammo box)
	VM.reload(held, w.reload :: number, a.mag <= 0, hand)
	TP.reload(held, w.reload :: number, a.mag <= 0, hand)
	return true
end
-- (Lefty & Righty) R reloads both, one after the other: lefty first, righty when it's done
function minigun.reloadBoth()
	local wid = held
	local w = W[wid]
	if reload(1) then
		task.delay((w.reload :: number) + 0.05, function() if held == wid then reload(2) end end)
	else
		reload(2)
	end
end

-- fire with rounds still in the mag cancels a reload (the owner, 18 Nov 2026: "can you cancel reload by shooting"):
-- the reload clip stops, no rounds go in, and the shot goes off. with the mag empty the reload carries on. the server
-- drops its own reload on that shot (Rules.fire), so it can't skip any reload time. guns only (not the blades, not the
-- Shredder)
local function cancelReload(): boolean
	local a, w = ammo[held], W[held]
	if not a or not w or w.kind ~= "hitscan" or a.reloadUntil <= 0 or a.mag <= 0 then return false end
	a.reloadUntil = 0
	VM.stop()
	TP.cancelReload()
	return true
end

-- a spent case out of the port (the pump's red hull, the bolt's and the lever's brass: thrown by the clip, not the shot)
local function eject(big: boolean)
	local port = VM.attachment("Port")
	local _, _, root = myChar()
	if not port or not root or (camera.CFrame.Position - root.Position).Magnitude > 4.5 then return end
	Fx.brass(CFrame.lookAt(port, port + camera.CFrame.LookVector), big)
end

VM.onEvent = function(ev: string)
	Sfx.skinEvent(held, ev) -- (a special skin's own reload / cycle / swing layer: shared/SkinSounds)
	if ev == "whoosh" then Sfx.play(if W[held] and W[held].swingSnd then W[held].swingSnd :: string else "swing")
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
	-- batch 3's clips: cases thrown by the pump / bolt / lever, and the clicks and clacks of their moving parts
	elseif ev == "shellRed" then eject(true)
	elseif ev == "shell" or ev == "shellUp" then eject(false); Sfx.play("click", nil, 0.7, 1.5)
	elseif ev == "shellIn" or ev == "thumb" or ev == "loaderIn" then Sfx.play("click", nil, 0.8, 1.25)
	elseif ev == "pumpBack" or ev == "boltBack" or ev == "boltUp" or ev == "coverUp" or ev == "break" or ev == "cylOut" then Sfx.play("click", nil, 0.9, 0.85)
	elseif ev == "pumpHome" or ev == "boltHome" or ev == "boltDown" or ev == "leverClack" or ev == "close" or ev == "cylIn"
		or ev == "slideHome" or ev == "hkSlap" or ev == "cock" then Sfx.play("click", nil, 1, 1.35)
	elseif ev == "clunk" and W[held] and W[held].drawSnd then Sfx.play(W[held].drawSnd :: string) -- (the Minigun's heavy draw)
	elseif ev == "coverSlam" or ev == "clunk" then Sfx.play("thwack", nil, 0.5, 0.8)
	elseif ev == "belt" or ev == "casings" or ev == "eject" or ev == "spinCyl" or ev == "loaderTwist" then Sfx.play("marble", nil, 0.5, 1.3)
	else Sfx.play("click", nil, 0.6) end
end

-- ---------------------------------------------------------------- firing
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include

-- fan = a fanned Revolver shot (the trigger held): the fan's own rate, spread and softer kick
local function fireGun(now: number, fan: boolean?, hand: number?)
	local w = W[held]
	local key = if hand == 2 and w and w.hands == 2 then held .. "@2" else held -- (Lefty & Righty's right gun: its own mag)
	local a = ammo[key]
	local _, _, root = myChar()
	if not root or not a then return end
	if a.reloadUntil > 0 then return end
	if a.mag <= 0 then Sfx.play("empty"); burstLeft = 0; reload(hand); return end
	local F = if fan then w.fan else nil
	local iv = 1 / Weapons.fireRate(w, hp())
	nextShot[key] = math.max(nextShot[key] or 0, now - math.min(0.04, iv / 2)) + iv
	minigun.shotT = now
	if w.fan then fanNext = now + 1 / w.fan.rate end
	if w.burst then -- the Hat Trick: a press is a whole burst, then a breath before the next one
		if burstLeft <= 0 then burstLeft = w.burst end
		burstLeft -= 1
		if burstLeft <= 0 then nextShot[held] += w.burstGap or 0 end
	end
	a.mag -= 1
	firedT = now
	local eye, look = eyeAndAim()
	local spread = ((if F then F.spread else (w.spread or 0)) + bloom) * (1 + ((if w.ads then w.ads.spread else 1) - 1) * aim)
	local map = workspace:FindFirstChild("Map")
	mapParams.FilterDescendantsInstances = { map :: Instance }
	local tg = targets()
	local hits: { [Model]: { n: number, h: number } } = {}
	local ends: { Vector3 } = {}
	local allEnds: { Vector3 } = {}
	local impacts: { RaycastResult } = {}
	local splashes: { Vector3 } = {}
	local path: { Vector3 }? = nil -- the Revolver: where this bullet bounced (the server walks the same path)
	for _ = 1, if F then 0 else (w.pellets or 1) do -- (a fanned Revolver shot is the server's to fire: fanEcho)
		local d = Hitbox.spreadDir(look, spread, math.random(), math.random())
		local from, left, bounces = eye, w.range, w.ricochet or 0
		local mh: RaycastResult? = nil
		local best = left
		local who: Model?, head = nil, false
		while true do
			mh = workspace:Raycast(from, d * left, mapParams)
			best = if mh then (mh.Position - from).Magnitude else left
			who, head = nil, false
			for _, t in tg do
				local k = Hitbox.distScale((t.feet - from).Magnitude)
				local tt, hd = Hitbox.ray(from, d, t.feet, k, nil, Hitbox.profile(t.m)) -- (the whole head, as the server: Hitbox.profile)
				if tt and tt < best then best, who, head = tt, t.m, hd end
			end
			if who or not mh or bounces <= 0 or left - best <= 1 then break end
			-- off the wall (the Revolver, twice): the same bullet carries on with what's left of its range
			bounces -= 1
			left -= best
			local at = from + d * best
			local pp: { Vector3 } = path or {}
			path = pp
			table.insert(pp, at)
			Fx.impact(mh.Position, mh.Normal, mh.Instance, mh.Material, { hole = false, scale = 0.6 })
			Sfx.play("ricochet", at, 0.6)
			d = d - 2 * d:Dot(mh.Normal) * mh.Normal
			from = at + mh.Normal * 0.05
		end
		local e = from + d * best
		table.insert(allEnds, e)
		if #ends < 12 then table.insert(ends, e) end
		local wx = Fx.waterCross(from, e) -- into the pool: a splash on the surface, not dust on the bottom
		if wx and #splashes < 4 then table.insert(splashes, wx) end
		if who then
			local g = hits[who] or { n = 0, h = 0 }
			g.n += 1; if head then g.h += 1 end
			hits[who] = g
		elseif mh and not wx and #impacts < 6 then table.insert(impacts, mh) end
	end
	local list = {}
	for m, g in hits do table.insert(list, { m = m, n = g.n, h = g.h }) end
	-- the shot's claims (the server checks each one): a fanned shot, the bounce points, a quick-scope (fired within
	-- `quick` s of the scope coming up), a no-scope (a scoped gun fired with the scope down)
	local opt: { [string]: any }? = nil
	local qs = w.quick ~= nil and scoped and now - scopedAt <= (w.quick :: number)
	local ns = w.noscope == true and not scoped
	if F or path or qs or ns then
		opt = { fan = if F then true else nil, path = path, qs = if qs then true else nil, ns = if ns then true else nil }
	end
	if F then -- (where you look: the server rolls the fan's spread round it, fires the bullet and sends it back, fanEcho)
		(opt :: any).look = look
		ends = { eye + look * w.range }
	end
	if hand then opt = opt or {}; (opt :: any).hand = hand end -- (Lefty & Righty: which gun)
	FireR:FireServer(held, eye, ends, list, opt)
	-- your own feel: shove, climb, bloom, the gun kicks, flash, brass, tracer / marbles, sound
	local km = if F then F.kick else 1
	Body.push(-look * (w.recoil or 0) * km)
	local fl = VM.feel(held, w) -- (how hard this kind of gun kicks: the climb, its upward tilt, the view punch)
	-- (this shot's own rate: the Redline's climbs to 22 a second as your HP drops. past 10 a second each shot kicks
	-- that much less, so a faster spray doesn't climb or tilt faster: the owner, 18 Nov 2026, "fix recoil on redline")
	local rt = 1 / iv
	local rk = math.min(1, 10 / rt)
	kickCam((w.kick or 0) * km * rk * fl.climb * (0.6 + math.random() * 0.8) * (1 - 0.5 * aim), (math.random() - 0.5) * (w.kick or 0) * km * rk * fl.climb * 0.5, fl.hold, fl.pull)
	bloom = math.min(w.maxBloom or 0, bloom + (w.bloom or 0))
	local vis = Settings.get("gfx.recoil") -- (a visual-only recoil slider, 0..1; nil = 1)
	vis = if type(vis) == "number" then math.clamp(vis, 0, 1) else 1
	VM.kick(w.recoilVM, (if aim > 0.5 then 0.6 else 1) * rk, rt > 8, fl.up * vis, fl.punch * vis, hand)
	VM.shot(w, hand) -- the cylinder turns, the hammer falls, the slide kicks, the barrel warms (hand: Lefty & Righty's)
	TP.fired(held, F ~= nil, hand) -- (and the gun in your character's hands kicks, for you in third person and for everyone)
	if w.cycle then VM.follow(w.cycle.clip, w.cycle.at) end -- then the pump / the bolt / the lever
	if w.fan then -- the Revolver: a twirl round the finger after a tap (not down the sights), a whole turn per fanned shot
		if F then VM.play("fan_revolver") elseif aim < 0.3 then VM.play("twirl_revolver") end
	end
	local fpv = not thirdPerson()
	-- the muzzle: the viewmodel's in first person, the gun in your character's hand in third person
	local mz = (if fpv then nil else heldMuzzle(me.Character, hand)) or VM.attachment("Muzzle", hand) or (eye + look * 2) -- (hand 1: Lefty's own muzzle)
	-- every gun's look comes from its row in Weapons (fx, tracer, snd): nothing here is per weapon
	local fx = w.fx or {}
	-- the flash (not through the scope: it hides the gun, flash and all) and the tracers, bent at a bounce, by the web's
	-- rules for this gun (Fx.gunShot: size, flash time, tracer width and life)
	Fx.gunShot(w, CFrame.lookAt(mz, mz + look), if F then {} else ends, path, fpv, scoped and fpv) -- (fanned: the flash only)
	if fx.spray then
		Fx.marbles(mz, allEnds, 1) -- no tracers: the marbles are the tracers
	elseif fx.brass and not scoped then
		local port = VM.attachment("Port")
		if port and fpv then Fx.brass(CFrame.lookAt(port, port + look) * CFrame.Angles(0, 0, 0), false) end
	end
	Sfx.gun(w, Weapons.tacho(hp()), nil, VM.heat())
	-- what the shots hit: holes, dust, sparks by material (marbles chip and puff, they don't punch holes)
	local o = if fx.hole == false then { hole = false, scale = fx.scale or 1 } else nil
	for _, im in impacts do Fx.impact(im.Position, im.Normal, im.Instance, im.Material, o) end
	if fx.splash ~= false then for _, s in splashes do Fx.splash(s, 0.3) end end -- (marbles plop in on their own)
	shake = math.max(shake, fx.shake or 0.06)
	if a.mag <= 0 then task.delay(0.15, reload) end
end

-- a melee weapon (the katana, the knife, the claw): click = swing (the combo alternates within 0.75 s); the hit lands at
-- the clip's hit time. heavy = the knife's right-click stab (its own clip, numbers and cooldown, the slash's too)
local function swing(now: number, heavy: boolean?)
	local w = W[held]
	if not w or w.kind ~= "melee" then return end
	local hv = if heavy then w.heavy else nil
	if heavy and not hv then return end
	if now < nextSwing or now < staggerUntil or guard.up or now < guard.close or now < (tonumber(me:GetAttribute("KatanaCast")) or 0) then return end
	nextSwing = now + ((if hv then hv.cd else w.cd) :: number)
	local clip: string
	if hv then
		clip = "stab_" .. held
	else
		-- the swing chain while you keep swinging (within 0.75 s, or the weapon's own cooldown + 0.35 s for a slow one: the
		-- Scythe's 0.95 s cooldown never let its second swing play): swing_<id>, swing_<id>2, then swing_<id>3 and
		-- swing_<id>4 if the weapon has them, round again; a pause starts it over. (18 Nov 2026, the Scythe's mocap: a
		-- 3-hit chain and a finisher; workspace attribute ScytheExtras = false keeps it to swings 1 and 2.) every link
		-- is the same swing to the server: damage, reach and timing don't change along the chain
		local within = now - lastSwing < math.max(0.75, ((if hv then hv.cd else w.cd) :: number) + 0.35)
		local len = 1
		while len < 4 and Anims["swing_" .. held .. tostring(len + 1)] do len += 1 end
		if held == "scythe" and workspace:GetAttribute("ScytheExtras") == false then len = math.min(len, 2) end
		if held == "katana" and Anims.kat_light3 then len = 3 end -- (20 Nov 2026: the pack's 3-hit combo, kat_light1..3)
		local at = if within then ((minigun :: any).swingN or 1) + 1 else 1
		if at > len then at = 1 end
		;(minigun :: any).swingN = at
		swingAlt = at == 2
		lastSwing = now
		clip = if at == 1 then "swing_" .. held else "swing_" .. held .. tostring(at)
		if held == "katana" and Anims["kat_light" .. tostring(at)] then clip = "kat_light" .. tostring(at) end
	end
	VM.play(clip)
	TP.swing(if hv then false else swingAlt, clip) -- (third person: the same link of the chain, or the stab: ThirdPerson.luau)
	local lk = camera.CFrame.LookVector
	SwingR:FireServer(held, if hv then true else nil, math.atan2(-lk.X, -lk.Z)) -- (where you look: a katana swing's front for the crit return)
	pending = { t = now + ((if hv then hv.hitT else w.hitT) :: number), w = held, heavy = hv ~= nil }
end

local function resolveSwing()
	local pd = pending :: any
	pending = nil
	local _, _, root = myChar()
	if not root then return end
	local eye, look = eyeAndAim()
	local wid = (pd and pd.w) or "katana"
	local w = W[wid]
	if not w then return end
	local hv = if pd and pd.heavy then w.heavy else nil
	local reach = if hv then hv.range else Weapons.reach(w, kat())
	local cone = (if hv then hv.cone else w.cone) :: number
	local map = workspace:FindFirstChild("Map")
	mapParams.FilterDescendantsInstances = { map :: Instance }
	local hitList: { Model } = {}
	local firstAt: Vector3? = nil
	for _, t in targets() do
		local pt = t.feet + Vector3.new(0, Hitbox.ROOT_UP, 0)
		if Hitbox.inCone(eye, look, pt, reach, cone) then
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
		elseif h and w.pogo then
			-- (weapons batch A) the Bread smacks the floor or a wall and pogos you off it, the way you looked (web 1171)
			Body.push(-look * w.pogo)
			Fx.impact(h.Position, h.Normal, h.Instance, h.Material, { hole = false, scale = 1.2 })
			Sfx.play(w.hitSnd or "bonk", h.Position, 0.8)
		elseif h then Fx.slash(h.Position, h.Normal, h.Instance, h.Material, look); Sfx.play("tink", h.Position, 0.7) end
		return
	end
	MeleeR:FireServer(wid, look, hitList)
	-- the hit, felt right away: hit-stop, the flash, a bonk (a spoon tings; a stab crunches), a punch
	VM.hitStop = if hv then 0.11 elseif w.latch then w.latch.t else 0.06 -- (the Scythe: its blade holds for the latch's beat)
	if firstAt then Fx.blast(firstAt, if hv then 1.1 else 0.6) end
	if firstAt then Fx.skinHit(VM.model, firstAt) end -- (a high-tier katana's own burst: Sakura's petals, Ribbon Duck's sparkles)
	Sfx.play(if wid == "knife" and me:GetAttribute("SpoonLook") then "ting" else (w.hitSnd or "bonk")) -- (the Bread thuds, the Slapper slaps)
	Sfx.skinHit(wid)
	if hv then Sfx.play("crunch") end
	shake = math.max(shake, if hv then 0.6 elseif w.latch then 0.55 else 0.35) -- (a latch kicks the camera a bit harder)
	VM.jolt(-1.5)
end

-- right click with the katana: the guard goes up and stays while the button is held (to PARRY.hold s; a tap still
-- gives PARRY.win), and the server parries every bullet from the front in it (Rules.parryAt). the cooldown is known
-- at the let-go: the longer it was held, the longer (none in training)
local function tryParry(now: number)
	if held ~= "katana" or guard.up then return end
	if now < parryReady or now < staggerUntil or pending or now - equipT < 0.12 or now < (tonumber(me:GetAttribute("KatanaCast")) or 0) then
		parryBuf = now -- an early press is kept for 250 ms
		return
	end
	parryBuf = -math.huge
	parryT = now
	guard.up, guard.close, guard.turn = true, now + P.win, now
	parryReady = math.huge -- (set at the let-go)
	VM.play(if Anims.kat_block then "kat_block" else "parry_katana") -- (the pack's Block, 20 Nov 2026)
	TP.parry()
	local lk = camera.CFrame.LookVector
	ParryR:FireServer(math.atan2(-lk.X, -lk.Z)) -- where you look: the server's "front" for this guard
end
-- the let-go (cap: the hold ran out, and the server closes it on its own)
local function guardEnd(now: number, cap: boolean?)
	if not guard.up then return end
	guard.up = false
	guard.close = math.max(parryT + P.win, math.min(now, parryT + P.hold))
	local heldFor = math.clamp(guard.close - parryT, P.win, P.hold)
	local z = me:GetAttribute("Zone")
	parryReady = if z == "training" or z == "playground" then guard.close + 0.05
		else parryT + heldFor + P.cd + P.holdCd * (heldFor - P.win) / (P.hold - P.win)
	if not cap then
		local lk = camera.CFrame.LookVector
		ParryR:FireServer(math.atan2(-lk.X, -lk.Z), false)
	end
end

-- ---------------------------------------------------------------- input
local KEYS = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3 } -- the loadout's slots
local Keys = require(script.Parent:WaitForChild("Keys")) -- (the keys, and the phone's buttons pressing them: TouchControls)
Keys.began(function(io: InputObject, gp: boolean)
	if gp or menuOpen() or inHub() then return end
	local slot = Binds.slot(io)
	-- (a key that's closing a pop-up ad or answering a pop quiz right now isn't a weapon key: Utility.client.luau)
	local busy = me:GetAttribute("BusyKeys")
	if slot and type(busy) == "string" and string.find(busy, tostring(slot), 1, true) then return end
	local want = if slot then lo()[slot] else nil
	if not want and Binds.is("next", io) then -- (a controller's next-weapon button: round the loadout)
		local l = lo()
		want = l[(table.find(l, Weapons.base(held)) or 0) % #l + 1]
	end
	-- (the Scythe comes out in the form you last had it in; its own key while it's out keeps that form)
	if want then want = minigun.lastForm[want] or want end
	if want and me:GetAttribute("LassoHolding") then return end -- (batch E: no switching with someone on your rope)
	if not want and Binds.is("form", io) and W[held] and W[held].form and not toolOut() then
		minigun.form(os.clock())
		return
	end
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
	-- (the mouse is out, by Toggle Cursor or a menu: a click is for the screen. it doesn't fire, swing or aim: MenuCursor)
	if me:GetAttribute("MenuCursor") == true and (Binds.is("fire", io) or Binds.is("aim", io)) then return end
	-- (the Overdrive Rig gadget, 19 Nov 2026: while suited up, LMB is the rocket punch and RMB the missiles: RigClient)
	if me:GetAttribute("Rig") ~= nil and (Binds.is("fire", io) or Binds.is("aim", io)) then
		minigun.rig.down(if Binds.is("fire", io) then "fire" else "aim")
		return
	end
	if Binds.is("fire", io) then
		trigger = true
		pressT = now
		fanArmed = true
		local _, _, root = myChar()
		if not root then return end
		if Body.stunned() then return end -- (tased: no firing or swinging till it wears off)
		if W[held] and W[held].kind == "melee" then swing(now)
		elseif W[held] and W[held].kind == "zap" then minigun.zap(now) -- (weapons batch B: the Taser)
		elseif W[held] and W[held].kind == "hold" then minigun.hold.press(held) -- (batch B: blower, sauce, laser)
		elseif W[held] and W[held].kind == "lasso" then minigun.lasso.press() -- (batch E: spin, or let go of whoever's on it)
		elseif W[held] and W[held].kind == "cart" then -- (batch E: the Shopping Cart Cannon; CartServer flies it)
			if now >= (minigun.trickNext.cart or 0) then
				minigun.trickNext.cart = now + (W[held].cd or 1.6)
				local eye, look = eyeAndAim()
				local r = Remotes:FindFirstChild("Cart")
				if r and r:IsA("RemoteEvent") then r:FireServer("fire", eye, look) end
				Body.push(-look * 6 * Weapons.S) -- (the kick pushes you back)
				VM.kick(W[held].recoilVM, 1, false, 1, 1); VM.shot(W[held]); TP.fired(held, false)
				if W[held].snd then Sfx.play(W[held].snd) end
			end
		elseif W[held] and W[held].kind == "cards" then -- (batch E: the Card Deck plays the picked card)
			local eye, look = eyeAndAim()
			if minigun.cards.play(eye, look) then
				VM.kick(W[held].recoilVM, 0.8, false, 1, 1); VM.shot(W[held]); TP.fired(held, false)
			end
		elseif W[held] and W[held].kind == "bow" then -- (batch D: the Bow draws while you hold; the arrow goes on the let-go)
			if not minigun.proj.bowT then
				minigun.proj.bowT = now
				local ds = W[held].drawSnd
				if ds then Sfx.play(ds) end
			end
		elseif W[held] and W[held].kind == "remote" then -- (batch D: the TV Remote's left click pauses whoever you point at)
			minigun.trick("TVRemote", "pause", 0.3)
			VM.kick(W[held].recoilVM, 0.6, false, 1, 1)
			Sfx.play(W[held].snd or "click")
		elseif W[held] and W[held].kind == "proj" then -- (batch C: the projectiles)
			local eye, look = eyeAndAim()
			if minigun.proj.throw(held, eye, look) then VM.kick(W[held].recoilVM, 0.8, false, 1, 1); VM.shot(W[held]); TP.fired(held, false) end
		else
			cancelReload() -- (a reload with rounds left: the shot wins)
			if not W[held].auto and now >= nextShot[held] then fireGun(now) end
		end
	elseif Binds.is("aim", io) then
		aimHeld = Binds.press("aim", true, aimHeld) -- (hold or toggle: Settings > CONTROLS)
		if W[held] and W[held].hands == 2 then minigun.trigger2 = true -- (Lefty & Righty: right click is the right gun)
		elseif W[held] and W[held].dash then -- (the Scythe: right click dashes; the server runs it, ScytheDash.server)
			local r = Remotes:FindFirstChild("Dash")
			if r and r:IsA("RemoteEvent") and not Body.stunned() and os.clock() >= minigun.formUntil then r:FireServer(camera.CFrame.LookVector) end
		elseif W[held] and W[held].heavy then swing(now, true)
		elseif W[held] and W[held].kind == "remote" then -- (batch D: the TV Remote's right click rewinds them)
			minigun.trick("TVRemote", "rewind", 0.3)
			VM.kick(W[held].recoilVM, 0.6, false, 1, 1)
			Sfx.play(W[held].snd or "click")
		elseif W[held] and W[held].kind == "cards" then minigun.cards.select() -- (batch E: the next card along)
		elseif W[held] and W[held].kind == "lasso" then minigun.lasso.aimPress() -- (batch E: let go)
		elseif W[held] and W[held].gavel then -- (batch D: the Scales of Justice's pillar of light)
			if not Body.stunned() then
				minigun.trick("Gavel", nil, 0.3)
				local raise = (VM :: any).raise -- (the hold session's pose: the scales up and out, tipped up)
				if raise then raise(0.6) end
			end
		elseif aimHeld then tryParry(now) else guardEnd(now) end -- (the knife stabs; the katana guards while it's held: toggle aim lets go on the next press)
	elseif Binds.is("reload", io) then
		if W[held] and W[held].hands == 2 then minigun.reloadBoth()
		elseif W[held] and W[held].kind == "cards" then minigun.cards.redraw() -- (batch E: a new hand)
		else reload() end
	end
end)
Keys.ended(function(io: InputObject)
	if Binds.is("fire", io) and minigun.rig.on() then minigun.rig.up("fire") end -- (the Overdrive Rig: the punch on let-go)
	if Binds.is("fire", io) then trigger = false; minigun.hold.release(held)
		if W[held] and W[held].kind == "lasso" then -- (batch E: the Lasso's let-go throws the loop)
			local eye, look = eyeAndAim()
			if minigun.lasso.spinning() > 0 then VM.shot(W[held]) end -- (the loop leaves the fist: GunParts refill)
			minigun.lasso.release(eye, look)
		end
		-- (batch D: the Bow's let-go: the arrow, drawn as far as you held it)
		local bt = minigun.proj.bowT
		if bt and W[held] and W[held].kind == "bow" then
			minigun.proj.bowT = nil
			local eye, look = eyeAndAim()
			if not Body.stunned() and minigun.proj.throw(held, eye, look, (os.clock() - bt) / W[held].drawT) then
				VM.kick(W[held].recoilVM, 0.8, false, 1, 1); VM.shot(W[held]); TP.fired(held, false)
			end
		elseif bt then minigun.proj.bowT = nil end
	elseif Binds.is("aim", io) then
		aimHeld = Binds.press("aim", false, aimHeld)
		minigun.trigger2 = false
		if not aimHeld then guardEnd(os.clock()) end -- (the katana's guard comes down with the button)
	end
end)
UserInputService.InputChanged:Connect(function(io: InputObject, gp: boolean)
	if io.UserInputType ~= Enum.UserInputType.MouseWheel or io.Position.Z == 0 or toolOut() or menuOpen() or inHub() then return end
	-- (with the mouse locked to the middle and no menu or Toggle Cursor, the wheel is always the weapons', even when
	-- something else (the camera's zoom, a screen under the middle) marked it used (gp); a wheel event with no turn
	-- (Z 0) used to count as down. the owner, 18 Nov 2026: "scroll wheel inv doesnt work for down yes for up")
	if gp and not (UserInputService.MouseBehavior == Enum.MouseBehavior.LockCenter and me:GetAttribute("MenuCursor") ~= true) then return end
	local l = lo()
	local i = table.find(l, held) or 1
	i = (i - 1 + (if io.Position.Z > 0 then -1 else 1)) % #l + 1
	equip(l[i])
end)

-- ---------------------------------------------------------------- the third-person pose for everyone holding something
-- (ThirdPerson.luau: the gun at the hip or up at the eye, both of the avatar's own hands on it, the look pitch, the
-- kick, the reload, the katana's moves, for every body in the game)

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
	-- (no blood off a model this client has taken out of its world: somebody else's range Carl, TrainingDoors.client)
	local gone = typeof(d.model) == "Instance" and not d.model:IsDescendantOf(workspace)
	if at and not gone then Fx.blood(at, Vector3.new(math.random() - 0.5, 0.3, math.random() - 0.5).Unit, amt) end
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
		local item = Items.list[wid]
		local wn = if W[wid] then W[wid].name elseif item then item.name else wid
		local killer = if type(k.k) == "string" then k.k else nil
		H.dead(if k.w == "void" then (if killer then ("%s knocked you into the smog  (%s)"):format(killer, wn) else "you fell into the smog")
			elseif killer then ("killed by %s  (%s)"):format(killer, wn) else "you died")
	end
end)

remote("Shot").OnClientEvent:Connect(function(s: any)
	if type(s) ~= "table" or type(s.ends) ~= "table" then return end
	if s.by == me.UserId then
		-- your own fanned Revolver shot as the server fired it (Combat serverShot; its flash went off as you fired): the
		-- tracer from your muzzle, bent at each bounce, chips and a ricochet at each bounce, the impact where it ended
		local fw = if s.fan == true and type(s.w) == "string" then W[s.w] else nil
		local fe = s.ends[1]
		if not fw or typeof(fe) ~= "Vector3" then return end
		local bp: { Vector3 } = {}
		if type(s.path) == "table" then for i, b in s.path do if typeof(b) == "Vector3" and i <= 2 then table.insert(bp, b) end end end
		local fpv = not thirdPerson()
		local fm = (if fpv then nil else heldMuzzle(me.Character)) or VM.attachment("Muzzle") or (eyeAndAim())
		if ((bp[1] or fe) - fm).Magnitude > 0.1 then Fx.gunShot(fw, CFrame.lookAt(fm, bp[1] or fe), { fe }, if #bp > 0 then bp else nil, fpv, true) end
		local prev = fm
		for _, b in bp do Fx.shotEnds(prev, { b }, true); Sfx.play("ricochet", b, 0.6); prev = b end
		Fx.shotEnds(prev, { fe }, false)
		return
	end
	local m = if typeof(s.model) == "Instance" then s.model :: Instance else nil
	local wpn = m and m:FindFirstChild("HeldWeapon")
	local root = wpn and (wpn :: Model).PrimaryPart
	local mz = root and root:FindFirstChild("Muzzle") :: Attachment?
	local head = m and m:FindFirstChild("Head") :: BasePart?
	local from = TP.muzzle(m, if s.hand == 2 then 2 elseif s.hand == 1 then 1 else nil) or (if mz then mz.WorldPosition elseif head then head.Position else nil)
	if not from then return end
	local ends = {}
	for i, e in s.ends do if typeof(e) == "Vector3" and i <= 12 then table.insert(ends, e) end end
	local first = ends[1]
	local sw = if type(s.w) == "string" then W[s.w] else nil
	local sfx = (sw and sw.fx) or {}
	if first and (first - from).Magnitude > 0.1 then
		-- their flash and tracers (a Revolver bullet bends at each bounce) by the web's rules; an unknown gun gets the
		-- plain look (Fx.gunShot)
		Fx.gunShot(sw or { fx = sfx, tracer = TRACER }, CFrame.lookAt(from, first), if sfx.spray then {} else ends,
			if type(s.path) == "table" then s.path else nil, false)
	end
	if sfx.spray then Fx.marbles(from, ends, 8) end
	if sw then Sfx.gun(sw, 0, from) end
	Fx.shotEnds(from, ends, sfx.spray == true) -- their holes, dust and splashes, seen here too
end)

remote("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" then return end
	local m = if typeof(f.model) == "Instance" and f.model:IsA("Model") then f.model :: Model else nil
	local now = os.clock()
	if f.k == "swing" then
		if f.by ~= me.UserId then
			local r = m and m:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then Sfx.play("swing", r.Position) end
			if Settings.get("gfx.othersSkin") ~= false then Fx.swingFlames(m) end -- (their angel katana's flame arc; Settings: OTHERS' SKIN EFFECTS)
		end
	elseif f.k == "parry" then
		local from = if typeof(f.from) == "Vector3" then f.from else nil
		local mine = f.by == me.UserId
		-- (a held guard's 2nd, 3rd... bullet of a spray: smaller sparks and pop, the sound spaced out, a light jolt)
		local first = f.pf or not (type(f.n) == "number" and f.n > 1)
		if from then
			Fx.sparks(from + Vector3.new(0, 1.5, 0), Vector3.yAxis, if f.pf then 40 elseif first then 26 else 12, if f.pf then 0.22 elseif first then 0.15 else 0.09)
			if first or now - guard.snd > 0.085 then
				guard.snd = now
				Sfx.play(if f.pf then "parry_perfect" else "parry", if mine then nil else from, if first then nil else 0.75)
			end
		end
		if f.kind == "shot" and f.pf and from and typeof(f.to) == "Vector3" then -- the bullets go home
			Fx.tracer(from, f.to, Color3.new(1, 1, 1), 0.07 * S, 0.3)
			Fx.tracer(from, f.to, Color3.fromRGB(159, 232, 255), 0.025 * S, 0.5)
			Sfx.play("ricochet", if mine then nil else from)
		end
		if mine then
			VM.hitStop = if f.pf then 0.13 elseif first then 0.09 else 0.02
			VM.jolt(if f.pf then 3 elseif first then 2 else 0.7)
			H.flash(if f.pf then 0.8 elseif first then 0.5 else 0.1, if f.pf then 0.3 elseif first then 0.2 else 0.08)
			shake = math.max(shake, if f.pf then 0.45 elseif first then 0.25 else 0.12)
			-- (20 Nov 2026) the guard's first hit, a perfect one or a sword: the pack's deflect, then the Block again
			if first and held == "katana" and Anims.kat_deflect then
				VM.play("kat_deflect")
				local tpx = TP :: any
				if tpx.kat then tpx.kat("deflect") end
			end
		end
		if f.att == me.UserId and f.kind == "melee" and type(f.st) == "number" then -- your swing got parried
			staggerUntil = now + math.clamp(f.st, 0, 1)
			nextSwing = staggerUntil
			parryReady = math.max(parryReady, staggerUntil)
			VM.play(if held == "katana" and Anims.kat_stagger then "kat_stagger" else "staggered")
			shake = math.max(shake, 0.45)
		end
	end
end)

-- the server kept you on the other form (a switch it refused: Combat tryEquip): back to what it says you hold
remote("Equip").OnClientEvent:Connect(function(wid: any)
	if type(wid) ~= "string" or not W[wid] or wid == held or toolOut() then return end
	minigun.formUntil = 0
	local b = Weapons.base(wid)
	if b ~= wid or (W[wid].form ~= nil) then minigun.lastForm[b] = wid end
	equip(wid)
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

-- the server's verdicts on the gimmicks arrive as callouts (Hud shows the words): a ding to go with them
remote("Callout").OnClientEvent:Connect(function(text: unknown)
	if type(text) ~= "string" then return end
	if string.sub(text, 1, 6) == "BURST!" then
		Sfx.play("burst_ding", nil, 0.8) -- (a real desk-bell ding, the sound session's: no more one clip pitched into a tune)
	elseif string.sub(text, 1, 7) == "CHAIN x" then -- (the Lever Rifle's chain on one person)
		local mul = tonumber(string.match(text, "x([%d%.]+)")) or 1.15
		Sfx.play("ting", nil, 0.7, 1 + 0.25 * (mul - 1) / 0.15)
	elseif text == "QUICK SCOPE" or string.sub(text, 1, 8) == "NO SCOPE" then
		Sfx.play("ting", nil, 0.9, 0.8)
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
	guard.up, guard.close = false, -math.huge
	bloom, aim, shake = 0, 0, 0
	climb.p, climb.y = 0, 0
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

-- every weapon's meshes and pictures are fetched up front: a gun never comes out invisible, or blank white while its
-- pictures are still on their way, the first time you draw it
task.spawn(function()
	local lib = ReplicatedStorage:WaitForChild("JankfireWeapons", 15)
	if lib then pcall(function() game:GetService("ContentProvider"):PreloadAsync(lib:GetChildren()) end) end
end)

-- ---------------------------------------------------------------- every frame
-- (the hold session, 19 Nov 2026; the owner: "gun models like vibrate in game") after the camera, not on RenderStepped:
-- RenderStepped fires before the camera's own step, so the gun was placed on last frame's camera and shook against
-- it by however far the camera then moved (measured walking: 0.83 studs a frame on average, 2 at most). bound just
-- after JankfireCamera (Camera + 1), the gun, its muzzle and the shot's eye all use the camera you see
RunService:BindToRenderStep("JankfireArsenal", Enum.RenderPriority.Camera.Value + 2, function(dt: number)
	local now = os.clock()
	local _, hum, root = myChar()
	local w = W[held]
	shake = math.max(0, shake - dt * 2.2)
	bloom = math.max(0, bloom - 0.06 * dt)
	-- reload finishes on its own clock
	local a = ammo[held]
	if a and a.reloadUntil > 0 and now >= a.reloadUntil then a.mag = w.mag :: number; a.reloadUntil = 0 end
	local a2 = if w and w.hands == 2 then ammo[held .. "@2"] else nil -- (Lefty & Righty's right gun)
	minigun.cards.show(held == "cards" and hum ~= nil and not toolOut() and not menuOpen()) -- (batch E: the hand's tiles)
	if a2 and a2.reloadUntil > 0 and now >= a2.reloadUntil then a2.mag = w.mag :: number; a2.reloadUntil = 0 end
	local reloading = a ~= nil and a.reloadUntil > 0
	-- aim down sights (can't while reloading): in ~0.14 s, out in ~0.125 s
	local canAim = w and w.ads ~= nil and not reloading and hum ~= nil
	aim = math.clamp(aim + (if aimHeld and canAim then 7 * (w.adsSpeed or 1) else -8) * dt, 0, 1)
	-- a scope (the Sniper, the Second Opinion): the overlay comes up at 92% aim and the gun itself is hidden behind it
	local isScoped = w ~= nil and w.ads ~= nil and w.ads.scope == true and aim > 0.92
	if isScoped and not scoped then scopedAt = now end
	scoped = isScoped
	-- (in third person a scoped gun's aim takes the camera into your head for the scope, ShoulderCam: the owner, 18 Nov
	-- 2026, "when in 3rd person sniper scope doesnt show up". how far in: ScopeAim, a scoped gun's aim, nil = none)
	local sa: number? = if w and w.ads and w.ads.scope == true and hum then math.floor(aim * 100 + 0.5) / 100 else nil
	if sa == 0 then sa = nil end
	if me:GetAttribute("ScopeAim") ~= sa then me:SetAttribute("ScopeAim", sa) end
	local wantAim = aimHeld and canAim == true and w.ads ~= nil and w.ads.scope == true
	if wantAim ~= aimSent then aimSent = wantAim; AimR:FireServer(wantAim) end
	-- how fast you run with it out (the SMG is light, the Belt Sander isn't), slower down the sights (web: x0.75)
	-- (a classic mode's run speed on top: spoons & grapples x1.6, Modes.luau's ModeSpeed)
	local ms = tonumber(me:GetAttribute("ModeSpeed")) or 1
	Body.speedMul = (if w and not inHub() then w.speedMul or 1 else 1) * (1 - 0.25 * aim) * (if inHub() then 1 else ms) * minigun.hold.speed()
	-- the base FOV is the P-menu slider's (JankSettings sets the BaseFov attribute); ADS zooms from it
	local fovAttr = me:GetAttribute("BaseFov")
	local baseFov = if type(fovAttr) == "number" then fovAttr else 70
	-- (the speed FOV kick on top: SpeedLines.client's SpeedFov, the web's fovKick; zoomed with it down the sights)
	local kick = me:GetAttribute("SpeedFov")
	if type(kick) == "number" then baseFov += kick end
	local punch = me:GetAttribute("ScyPunch") -- (the Scythe's combo finisher: a quick punch-in, ScytheDash.client)
	if type(punch) == "number" then baseFov -= punch end
	if w and w.ads then camera.FieldOfView = baseFov / (1 + (w.ads.zoom - 1) * aim) else camera.FieldOfView = baseFov end
	-- full auto
	local holstered = inHub()
	if holstered then trigger, aimHeld = false, false; if hum and toolOut() then hum:UnequipTools() end end
	if holstered then burstLeft = 0 end
	-- (weapons batch A) the Minigun: the barrels spin up over spinup s while the trigger is held and down over spindown
	-- s once it's let go; it fires only at full spin. the server is told when the trigger goes down and up (Spin) and
	-- keeps its own spin, so a client can't skip it. GunParts turns the barrels from GunParts.mySpin
	local spinning = false
	if w and w.spinup then
		local a2 = ammo[held]
		spinning = hum ~= nil and trigger and not Body.stunned() and not toolOut() and not menuOpen() and me:GetAttribute("MenuCursor") ~= true
			and a2 ~= nil and a2.mag > 0 and a2.reloadUntil == 0
		minigun.spin = if spinning then math.min(1, minigun.spin + dt / w.spinup) else math.max(0, minigun.spin - dt / (w.spindown or 0.9))
	else
		minigun.spin = 0
	end
	if spinning ~= minigun.on then
		minigun.on = spinning
		minigun.send(spinning)
		-- (the motor: a spin-up as the trigger goes down, a spin-down as it's let go; the steady whine in between)
		if spinning and minigun.spin < 0.9 then Sfx.play("minigun_spinup", nil, 1, 0.6 / (w and w.spinup or 0.6) * (1 + minigun.spin * 0.6))
		elseif not spinning and minigun.spin > 0.25 then Sfx.play("minigun_spindown", nil, minigun.spin) end
	end
	minigun.parts.mySpin = minigun.spin
	minigun.hold.step(dt, held) -- (the held-trigger weapons: where you look, your thrust, a swap lets go)
	minigun.loop(minigun.on and minigun.spin >= 0.98, 1, 1)
	-- (the Peel Shooter: held down, it keeps firing at its own rate; the projectiles have no magazine)
	if hum and trigger and w and w.kind == "proj" and w.auto and not Body.stunned() and not toolOut() and not menuOpen() and me:GetAttribute("MenuCursor") ~= true then
		local eye, look = eyeAndAim()
		if minigun.proj.throw(held, eye, look) then VM.kick(w.recoilVM, 0.6, false, 1, 1); TP.fired(held, false) end
	end
	if hum and (trigger or burstLeft > 0) and w and w.auto and w.kind == "hitscan" and (not w.spinup or minigun.spin >= 1) and not Body.stunned() and not toolOut() and not menuOpen() and me:GetAttribute("MenuCursor") ~= true and now >= (nextShot[held] or 0) then
		local n = 0
		-- (a Hat Trick burst always finishes, even on a tap)
		while (trigger or burstLeft > 0) and now >= nextShot[held] and n < 4 and (ammo[held] :: any).mag > 0 and (ammo[held] :: any).reloadUntil == 0 do fireGun(now, nil, if w.hands == 2 then 1 else nil); n += 1 end
		if (ammo[held] :: any).mag <= 0 and (ammo[held] :: any).reloadUntil == 0 then burstLeft = 0; reload(if w.hands == 2 then 1 else nil) end
	end
	-- (Lefty & Righty) the right gun on right click, its own mag and rate
	if hum and w and w.hands == 2 and minigun.trigger2 and not Body.stunned() and not toolOut() and not menuOpen() and me:GetAttribute("MenuCursor") ~= true then
		local k2 = held .. "@2"
		local a2r = ammo[k2]
		local n2 = 0
		while a2r and now >= (nextShot[k2] or 0) and n2 < 4 and a2r.mag > 0 and a2r.reloadUntil == 0 do fireGun(now, nil, 2); n2 += 1 end
		if a2r and a2r.mag <= 0 and a2r.reloadUntil == 0 then reload(2) end
	end
	-- the Revolver: hold the trigger (not down the sights) and the rest of the cylinder is fanned out
	if aim >= 0.1 or not trigger then fanArmed = false end
	if hum and trigger and fanArmed and w and w.fan and a and not Body.stunned() and not toolOut() and not menuOpen() and me:GetAttribute("MenuCursor") ~= true and now - pressT > w.fan.hold
		and now >= fanNext and a.mag > 0 and a.reloadUntil == 0 then
		fireGun(now, true)
	end
	if pending and now >= pending.t then resolveSwing() end
	if hum and aimHeld and parryBuf > -math.huge and now - parryBuf < 0.25 and now >= parryReady and not pending and now >= staggerUntil then tryParry(now) end
	-- the held guard: down at the hold's end (or with the katana put away); while up, the pose holds and its front turns
	-- with your look (PARRY.turn a second)
	if guard.up then
		if held ~= "katana" or not hum then guardEnd(now)
		elseif now - parryT >= P.hold then guardEnd(now, true)
		else
			local vm, tp = VM :: any, TP :: any
			if vm.holdAt then vm.holdAt("parry_katana", 0.2) end
			if Anims.kat_block then -- (the pack's Block held; raised again once a deflect has played)
				if vm.holdAt then vm.holdAt("kat_block", Anims.kat_block.hold or 0.07) end
				if vm.playing and vm.playing() == nil then VM.play("kat_block") end
			end
			if tp.holdKat then tp.holdKat(me.Character, "guard", 0.2) end
			if now - guard.turn >= 1 / P.turn then
				guard.turn = now
				local lk = camera.CFrame.LookVector
				ParryR:FireServer(math.atan2(-lk.X, -lk.Z), "turn")
			end
		end
	end
	-- the parry ring: full while the guard is up, draining over its cooldown
	if held == "katana" then
		if guard.up or now < guard.close then H.parryRing("open", 1)
		elseif now < parryReady then H.parryRing("drain", 1 - (parryReady - now) / math.max(0.05, parryReady - guard.close))
		elseif now - parryReady < 0.25 then H.parryRing("ready", 1)
		else H.parryRing("hidden", 0) end
	else H.parryRing("hidden", 0) end
	-- the viewmodel (hidden in third person: your character holds it)
	local st = Body.st
	local spd = if root then Vector3.new(root.AssemblyLinearVelocity.X, 0, root.AssemblyLinearVelocity.Z).Magnitude else 0
	if VM.model then
		local tp = thirdPerson() or hum == nil or toolOut() or menuOpen() or holstered
		local gone = tp or scoped or (held == "slipper" and me:GetAttribute("SlipperOut") == true) -- (batch D: the slipper's out of your hand)
		for _, d in VM.model:GetDescendants() do
			-- (Hide: a piece that's out of the gun right now: a dropped mag, a belt link that's been fired)
			if d:IsA("BasePart") and d.Name ~= "Root" then d.LocalTransparencyModifier = if gone or d:GetAttribute("Hide") then 1 else 0 end
		end
		VM.update(dt, {
			aim = aim, speed = spd, sprint = st ~= nil and st.sprinting, slide = st ~= nil and st.sliding,
			grounded = st ~= nil and st.onGround, hp = hp(), firedT = firedT, slipping = Body.slipping(), now = now,
			sight = VM.adsPos(held), ammo = if a then a.mag else nil, reloading = reloading, hidden = gone,
			swig = minigun.swig(), -- (the Hot Sauce's swig: the bottle up to your mouth)
			draw = minigun.bowDraw(), -- (the Bow drawn: its string and your right hand pulled back)
			spin = if held == "lasso" then minigun.lasso.spinning() else nil, -- (the Lasso spun up: your hand up and round, the loop over your head)
		})
		-- the katana's smear, after the blade has moved this frame
		smearStep(now, tp)
	else
		smearStep(now, true)
	end
	H.step(dt, aim, scoped, held, if w and w.kind ~= "melee" then ((w.spread or 0) + bloom) * (1 + ((if w.ads then w.ads.spread else 1) - 1) * aim) else 0)
	-- the Shredder's copy: its own script goes with its tool (a death, a test deleting it) and can't clear it, so a copy
	-- whose tool is gone would stay in your camera (seen 16 Nov 2026)
	for _, c in camera:GetChildren() do
		if c.Name == "ShredderViewmodel" then
			local o = c:FindFirstChild("Owner") :: ObjectValue?
			if o and not (o.Value and o.Value:IsDescendantOf(game)) then c:Destroy() end
		end
	end
	-- its heat bar (PlayerGui.ShredderHeat) the same way: shown only while its Shredder is in your living hands, cleared
	-- once that Shredder is gone (owner, 17 Nov 2026: the bar stayed up after switching guns)
	local pg = me:FindFirstChildOfClass("PlayerGui")
	if pg then
		for _, g in pg:GetChildren() do
			if g.Name == "ShredderHeat" and g:IsA("ScreenGui") then
				local o = g:FindFirstChild("Owner") :: ObjectValue?
				local t = o and o.Value
				if not (t and t:IsDescendantOf(game)) then g:Destroy()
				elseif g.Enabled and not (hum and me.Character and t.Parent == me.Character) then g.Enabled = false end
			end
		end
	end
	H.scope(scoped and not thirdPerson(), if held == "sniper" then "full" else "short") -- (only the Sniper blacks the screen)
	H.hp(hp())
	-- the Shredder (key 4) out: its name and heat in the panel instead of the gun it put away
	local tool = toolOut() and me.Character and me.Character:FindFirstChildOfClass("Tool")
	if tool and tool.Name == "Shredder" then
		local heat = tool:GetAttribute("Heat")
		H.weapon("shredder", nil, false, 0, if tool:GetAttribute("Hot") then "OVERHEATED" else ("heat %d%%"):format(math.floor((if type(heat) == "number" then heat else 0) * 100 + 0.5)))
	elseif holstered then
		H.weapon(held, a and a.mag, reloading, kat(), "HOLSTERED")
	elseif a2 then -- (Lefty & Righty: both mags, left | right)
		H.weapon(held, a and a.mag, reloading or a2.reloadUntil > 0, kat(), nil, a2.mag)
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
		H.top("TRAINING")
	elseif me:GetAttribute("Zone") == "playground" then
		H.top("THE PLAYGROUND")
	else
		H.top("HUB") -- (16 Nov, owner: no flavour text. the place's name only: FightHud flashes it for 3 s as you come in)
	end
	TP.mine(aim, st ~= nil and st.sprinting, if a then a.mag else nil, minigun.bowDraw()) -- (your aim and mag for the third-person pose; the Bow drawn)
end)
