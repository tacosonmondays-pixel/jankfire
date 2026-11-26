--!strict
-- JANKFIRE movement on the default Roblox character: run, sprint (Shift), slide (C / Ctrl while fast), bhop (jump as
-- you land), air strafing, the grapple (hold E: aim at a wall), grapple jump (Space on the rope), jump pads.
-- In a walled arena: the sky line and the ledge round the edge (wallbox.py, 18 Nov).
-- How: the Humanoid still does the standing, stepping, jumping and animations; a LinearVelocity on the root holds the
-- character's sideways velocity at what JANKFIRE's maths (shared/Movement.luau) says, every physics step. Up/down is
-- the engine's gravity (Workspace.Gravity = JANKFIRE's 26 m/s²) plus the rope. Movement is the client's, like the
-- web game; the server checks hooks and catches teleports (server/Main.server.luau).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Config = require(Shared:WaitForChild("Config"))
local Movement = require(Shared:WaitForChild("Movement"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local Binds = require(script.Parent:WaitForChild("Binds")) :: any -- (the keys as bound, hold or toggle sprint and crouch: Settings)
local Body = require(script.Parent:WaitForChild("Body")) -- step 2: lets the weapons push you (recoil, knockback, slips)
local HookChargesUI = require(script.Parent:WaitForChild("HookChargesUI")) -- (ranked: 2 grapple charges)
local MeleeX = require(script.Parent:WaitForChild("MeleeLunge")) :: any -- (26 Nov 2026: the melee lunge; a melee weapon out holds the lock-on longer)
local Keys = require(script.Parent:WaitForChild("Keys")) -- (the keys, and the phone's buttons pressing them: TouchControls)
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any -- (a LoadoutOpen nothing holds: V clears it)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local GrappleRemote = Remotes:WaitForChild("Grapple") :: RemoteEvent

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera

local keys = { sprint = false, crouch = false, jump = false, hook = false, jumpPressed = false }
-- the last fresh jump press, any device (Space, a gamepad's A, the phone's jump button): a bhop needs one. it counts
-- for one jump, and only if that jump comes at most JUMP_BUF after it (the web game's 0.22 s jump buffer: tap just
-- before you land, or within Config.bhopTicks after)
local pressT = -10
local JUMP_BUF = 0.22
-- the open sky of a walled arena (18 Nov 2026, tools/roblox/wallbox.py): no lid; over its sky line (SkyY, put on you by
-- Main.server) nothing lifts you more than SKY_CAP higher. its edge is a step you can swing over but not stand on: the
-- step's top ('ledge') slides you back toward the middle (ArenaAt), LEDGE_PUSH along, LEDGE_HOP up so it lets go of you
local SKY_CAP, LEDGE_PUSH, LEDGE_HOP = 12, 30, 18
local function inArena(pos: Vector3): boolean
	local at = player:GetAttribute("ArenaAt")
	return typeof(at) == "Vector3" and Vector2.new(pos.X - at.X, pos.Z - at.Z).Magnitude < 600
end
local controlsRef: any = nil -- (the control module: the phone's jump button is read from it)
local touchWas = false
local st = Movement.newState()
local rope: Beam? = nil
local ropeAnchor: Attachment? = nil
-- hooked to a person (18 Nov 2026, the owner: "can you make it so you can grapple onto people"; the web's tryHook and
-- hookPoint): the rope ties onto a living body the hook hit (a player, or a training dummy) at its chest and follows
-- it. it reels you in at the rope's full pull and lets go Config.hook.bodyLet off them, your momentum carrying you into
-- them; it drops if they die, respawn or leave, or once they've been out of your sight Config.hook.bodyBlind. no text.
-- (Config.hook.TIE, off: the rope ties and holds instead of pulling, Movement.ropeStep's tie)
local hookBody: Model? = nil
local hookBlind, hookLookT = 0, 0
local bodyParams = RaycastParams.new()
bodyParams.FilterType = Enum.RaycastFilterType.Exclude
local function bodyOf(inst: Instance): Model?
	local m = inst:FindFirstAncestorOfClass("Model")
	while m do
		local hum = m:FindFirstChildOfClass("Humanoid")
		if hum then
			if hum.Health > 0 and m:FindFirstChild("HumanoidRootPart") and (Players:GetPlayerFromCharacter(m) or m:GetAttribute("Dummy")) then return m end
			return nil
		end
		m = m:FindFirstAncestorOfClass("Model")
	end
	return nil
end
local function bodyRoot(m: Model?): BasePart?
	if not m or not m.Parent then return nil end
	local hum = m:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then return nil end
	return m:FindFirstChild("HumanoidRootPart") :: BasePart?
end
local thirdPerson = false

local function setCamera()
	player.CameraMode = if thirdPerson then Enum.CameraMode.Classic else Enum.CameraMode.LockFirstPerson
	if thirdPerson then player.CameraMinZoomDistance = 10; player.CameraMaxZoomDistance = 20 else player.CameraMinZoomDistance = 0.5 end
	player:SetAttribute("ThirdPerson", thirdPerson) -- (ShoulderCam.client puts the camera over your shoulder)
end

local function dropRope()
	if rope then rope:Destroy(); rope = nil end
	if ropeAnchor then ropeAnchor:Destroy(); ropeAnchor = nil end
end

-- (the reel, below tryYank: pulled along the rope while its key is held, until untilT. pullPress: a press of a key
-- that's both the yank's and the reel's, waiting to see if it's a tap (the yank) or a hold (the reel). hookLock: the
-- lock-on's time on a person, Config.hook.lockGun / lockMelee; melee: a melee weapon was out, so it ties on)
local reel: { untilT: number }? = nil
local reelAsked, reelReady = 0, 0
local pullPress: { t: number }? = nil
local hookLock: { untilT: number, melee: boolean }? = nil
local function lockShow(endT: number?, dur: number?, tether: boolean?)
	-- (MeleeHud.client draws the ring from these: the server time it ends, how long it was, tied on)
	player:SetAttribute("HookLockEnd", endT)
	player:SetAttribute("HookLockDur", dur)
	player:SetAttribute("HookTether", tether)
end
local function releaseHook(tellServer: boolean)
	reel = nil
	pullPress = nil
	if hookLock then hookLock = nil; lockShow(nil, nil, nil) end
	if st.hook then st.hook = nil; st.lift = 1 end
	if hookBody then hookBody = nil; player:SetAttribute("HookBody", nil) end -- (HookBody: the phone's YANK button shows)
	dropRope()
	if tellServer then GrappleRemote:FireServer("release") end
end

-- the yank (18 Nov 2026, the owner: "when you grapple someone maybe you can press a button to like pull them towards
-- you"): with the rope on a person, the YANK key (Binds "yank": F, a pad's B, the phone's YANK) pulls them to you and
-- the rope goes. the server checks it and throws them (Main.server); everyone sees the rope snap taut and hears it
-- crack (GrappleYank.client). where weapons work only (not the hub: F is QUICK JOIN's there), and one every
-- Config.hook.yankCool (YankT, the server's, on you)
local YANK_ZONES = { match = true, training = true, playground = true }
local function yankReady(): boolean
	if not (st.hook and hookBody) or not YANK_ZONES[player:GetAttribute("Zone") :: any] then return false end
	if player:GetAttribute("RoundLock") then return false end -- (not before GO: RoundLock, Matches)
	local ready = player:GetAttribute("YankT")
	return not (type(ready) == "number" and workspace:GetServerTimeNow() < ready)
end
local function tryYank(): boolean
	if player:GetAttribute("NoGrapple") then return false end -- (HOLDOUT, 26 Nov 2026: no grapple in the house or a round)
	if not yankReady() then return false end
	GrappleRemote:FireServer("yank")
	releaseHook(false) -- (the server drops its rope with the yank)
	return true
end

-- the reel (19 Nov 2026, the owner: "the same way how you press F to push people in, I want a button that reels you
-- in"; a HOLD since 26 Nov 2026: "an actual reel in with f"): with your rope on anything, HOLD the REEL key (Binds
-- "reelin": F with the yank, a pad's B, the phone's REEL) and you're pulled along the rope at a steady
-- Config.hook.reelSpeed to where its end is now (a person's chest as they zip about) till you get there, let go, or
-- reelMax runs out. it starts at once; the server tells the anti-cheat (ACGrace) or says "reelno" (too soon) and it
-- stops. one every reelCool (ReelT, the server's; reelReady, this screen's guess)
local function tryReel(): boolean
	if not Config.hook.REEL then return false end
	if not st.hook or reel or player:GetAttribute("RoundLock") then return false end
	local sn = workspace:GetServerTimeNow()
	local ready = player:GetAttribute("ReelT")
	if (type(ready) == "number" and sn < ready) or sn < reelReady then return false end
	if os.clock() - reelAsked < 0.3 then return false end
	reelAsked = os.clock()
	reelReady = sn + Config.hook.reelCool
	reel = { untilT = os.clock() + Config.hook.reelMax }
	GrappleRemote:FireServer("reel")
	return true
end

-- the opponent nearest the middle of your view within cone degrees, in range and in sight from your head: the AUTO
-- GRAPPLE on X (tryLock below, shared/HookCharges.LOCK) and QUICKPLAY's old passive auto-lock (HookCharges.AUTO, off)
local HC = require(Shared:WaitForChild("HookCharges")) :: any
-- (Studio: AutoLockTest on you tries both anywhere, the training dummies counting as opponents)
local function lockTest(): boolean return RunService:IsStudio() and player:GetAttribute("AutoLockTest") == true end
local function cooled(): boolean
	local ready = player:GetAttribute("HookAutoT")
	return not (type(ready) == "number" and workspace:GetServerTimeNow() < ready)
end
-- the passive one's say-so: on, a QUICKPLAY match (QuickMatch on you, set by the server), cooled down
local function passiveAuto(): boolean
	local A = HC.AUTO
	return A ~= nil and A.on == true and (player:GetAttribute("QuickMatch") == true or lockTest()) and cooled()
end
local function autoTarget(head: Vector3, ch: Model, cone: number, dummies: boolean?): (Model?, BasePart?)
	local test = lockTest()
	local myArena, myTeam = player:GetAttribute("Arena"), player:GetAttribute("Team")
	local cam = camera.CFrame
	local best: Model?, bestRoot: BasePart?, bestAng = nil, nil, math.rad(cone)
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	local cands: { Model } = {}
	for _, q in Players:GetPlayers() do
		if q == player or q:GetAttribute("Arena") ~= myArena then continue end
		local qt = q:GetAttribute("Team")
		if myTeam ~= nil and qt == myTeam then continue end -- (a teammate: never)
		if q.Character then table.insert(cands, q.Character) end
	end
	if test then for _, d in workspace:GetDescendants() do if d:IsA("Model") and d:GetAttribute("Dummy") then table.insert(cands, d) end end
	elseif dummies then -- (the lock-on's snap: the training dummies too, workspace.Dummies only: no scan of the world)
		local dd = workspace:FindFirstChild("Dummies")
		if dd then for _, d in dd:GetChildren() do if d:IsA("Model") then table.insert(cands, d) end end end
	end
	for _, qc in cands do
		local tr = bodyRoot(qc)
		if not tr then continue end
		local chestAt = tr.Position + Vector3.new(0, Config.hook.bodyUp, 0)
		local fromHead = chestAt - head
		if fromHead.Magnitude > Config.hook.range then continue end
		local fromCam = chestAt - cam.Position
		local ang = math.acos(math.clamp(cam.LookVector:Dot(fromCam.Unit), -1, 1))
		if ang > bestAng then continue end
		rp.FilterDescendantsInstances = { ch, qc }
		if workspace:Raycast(head, fromHead, rp) then continue end -- (a wall in the way)
		best, bestRoot, bestAng = qc, tr, ang
	end
	return best, bestRoot
end

local function character(): (Model?, Humanoid?, BasePart?)
	local ch = player.Character
	if not ch then return nil end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root or hum.Health <= 0 then return ch, nil, nil end
	return ch, hum, root
end

-- E: fire the hook where you look (map only: the city's deco can't be hooked, same as the web game's boxes). locked =
-- the AUTO GRAPPLE's target (tryLock below): the hook goes onto them whatever is under the crosshair
local function tryHook(locked: Model?, lockedRoot: BasePart?)
	local ch, hum, root = character()
	if not ch or not hum or not root or st.hook then return end
	if player:GetAttribute("NoGrapple") then return end -- (HOLDOUT, 26 Nov 2026: no grapple there; E is its push)
	-- (not before GO: the countdown, the loadout window, between rounds, a map room. nothing is thrown or spent)
	if player:GetAttribute("RoundLock") then Hud.note("GRAPPLE AT GO", 0.7); return end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { ch }
	-- aim with the camera, then go from the head (in third person the camera is well behind you: the rope, the range
	-- and the server's line-of-sight check are all from your head, like the web game's eye)
	local cam = camera.CFrame
	local aim = workspace:Raycast(cam.Position, cam.LookVector * (Config.hook.range + 40), params)
	local head = root.Position + Vector3.new(0, 1.5, 0)
	local target = if aim then aim.Position else cam.Position + cam.LookVector * (Config.hook.range + 40)
	local dir = target - head
	local hit = if dir.Magnitude > 1e-3 then workspace:Raycast(head, dir.Unit * math.min(dir.Magnitude + 1, Config.hook.range), params) else nil
	-- (the AUTO GRAPPLE's target; or QUICKPLAY's passive auto-lock, off: no one under the crosshair, but an opponent near it)
	local auto: Model?, autoRoot: BasePart? = locked, lockedRoot
	if not auto and not (hit and bodyOf(hit.Instance)) and passiveAuto() then auto, autoRoot = autoTarget(head, ch, HC.AUTO.cone) end
	-- the lock-on's snap (26 Nov 2026, Config.hook.snapGun / snapMelee): nobody under the crosshair, but a person within
	-- that many degrees of it, in range and in sight, and not further off than what you aimed at: the hook goes on them
	local snapped = false
	if not auto and not (hit and bodyOf(hit.Instance)) then
		local cone = if MeleeX.meleeOut() then Config.hook.snapMelee else Config.hook.snapGun
		local sm, sr = autoTarget(head, ch, cone, true)
		if sm and sr and (not hit or (sr.Position - head).Magnitude <= ((hit :: RaycastResult).Position - head).Magnitude + 6) then
			auto, autoRoot, snapped = sm, sr, true
		end
	end
	if not hit and not auto then
		Hud.callout("TOO FAR", 0.5)
		return
	end
	if not HookChargesUI.try() then return end -- (ranked: no charge left, it says so)
	local p = if auto and autoRoot then autoRoot.Position else (hit :: RaycastResult).Position
	local body = if auto then auto else bodyOf((hit :: RaycastResult).Instance)
	local troot = if body then bodyRoot(body) else nil
	if auto and not snapped then HookChargesUI.autoUsed(if locked then HC.LOCK.cd else HC.AUTO.cd) end
	if body and troot then -- (a person: the rope ties onto them)
		p = troot.Position + Vector3.new(0, Config.hook.bodyUp, 0)
		hookBody, hookBlind, hookLookT = body, 0, os.clock()
		player:SetAttribute("HookBody", true)
		-- the lock-on's clock (Config.hook.lockGun, or lockMelee with a melee weapon out): the ring round the crosshair
		local mel = MeleeX.meleeOut() == true
		local dur = if mel then Config.hook.lockMelee else Config.hook.lockGun
		hookLock = { untilT = os.clock() + dur, melee = mel }
		lockShow(workspace:GetServerTimeNow() + dur, dur, nil)
	else
		body = nil
	end
	st.hook = { ax = p.X, ay = p.Y, az = p.Z, len = nil, tie = body ~= nil and Config.hook.TIE == true } -- (TIE off: a person pulls you in too)
	-- (the 4th: "lock" = the AUTO GRAPPLE, true = the passive auto-lock: the server checks each one's own rule)
	GrappleRemote:FireServer("hook", p, body, if locked then "lock" elseif auto and not snapped then true else nil) -- (a snap is a plain hook on them)
	-- our own rope right away (the server draws it for everyone else)
	local a0 = (ch:FindFirstChild("RightHand") or ch:FindFirstChild("Right Arm") or root):FindFirstChildWhichIsA("Attachment") or root:FindFirstChildWhichIsA("Attachment")
	local a1 = Instance.new("Attachment")
	if troot and body then
		a1.Position = Vector3.new(0, Config.hook.bodyUp, 0)
		a1.Parent = troot
	else
		a1.WorldPosition = p
		a1.Parent = workspace.Terrain
	end
	local b = Instance.new("Beam")
	b.Attachment0 = a0; b.Attachment1 = a1
	b.Width0 = 0.25; b.Width1 = 0.25; b.FaceCamera = true; b.Segments = 1
	b.Color = ColorSequence.new(Color3.fromRGB(236, 238, 242), Color3.fromRGB(176, 182, 192)) -- (a pale steel cable)
	b.LightEmission = 0.3
	b.Parent = workspace.Terrain
	rope, ropeAnchor = b, a1
end

-- X: the AUTO GRAPPLE (19 Nov 2026, the owner: "Can X instad of reel in since it already automatically reels in, you
-- have a charge that auto the grapple to you roppenent on a decently long cooldown"; shared/HookCharges.LOCK). in a
-- match after GO: your grapple onto the opponent nearest the middle of your view within LOCK.cone, a normal hook on
-- them (it pulls you in; ranked: a charge). one every LOCK.cd (HookAutoT, the server's; the LOCK pip). nobody there:
-- nothing fires, nothing is spent
local function tryLock()
	local L = HC.LOCK
	if not (L and L.on) then return end
	local ch, hum, root = character()
	if not ch or not hum or not root or st.hook then return end
	if player:GetAttribute("Zone") ~= "match" and not lockTest() then return end
	if player:GetAttribute("NoGrapple") then return end -- (HOLDOUT)
	if player:GetAttribute("ZmOn") then return end -- (a ZOMBIES game reads as Zone "match": no opponents to lock onto there)
	if player:GetAttribute("RoundLock") then Hud.note("GRAPPLE AT GO", 0.7); return end
	if HookChargesUI.lockWait() > 0 then HookChargesUI.lockNotReady(); return end
	local body, troot = autoTarget(root.Position + Vector3.new(0, 1.5, 0), ch, L.cone)
	if not body or not troot then Hud.note("NO TARGET", 0.6); return end
	tryHook(body, troot)
end

GrappleRemote.OnClientEvent:Connect(function(what: string, arg: any)
	if what == "cut" then -- the server said no (out of range, no line to it, too many hooks)
		releaseHook(false)
	elseif what == "reelno" then -- the reel refused (too soon): it stops, the rope stays
		reel = nil
		local ready = player:GetAttribute("ReelT")
		reelReady = if type(ready) == "number" then ready else 0
	end
end)

Keys.began(function(io: InputObject, gp: boolean)
	if gp then return end
	if player:GetAttribute("LoadoutOpen") then -- (the loadout screen is up)
		-- (V is always yours: a LoadoutOpen nothing holds any more, left by screens closing out of order, goes, and the
		-- key works. MenuCursor.unstick, 18 Nov 2026)
		if not (Binds.is("camera", io) and MenuCursor.unstick()) then return end
	end
	local k = io.KeyCode
	-- the yank and the reel (26 Nov 2026), on their own: their keys are shared (F with QUICK JOIN and the cart, a pad's B
	-- with crouch), and by default with each other. a press of a key that's both, with the rope on a person and the yank
	-- ready, waits Config.hook.reelTap: let go sooner, the yank; held, the reel. on a wall (or the yank not ready) the reel
	-- starts at once; a key that's only the yank's yanks at once, as before
	local isYank, isReel = Binds.is("yank", io), Binds.is("reelin", io)
	if isReel and st.hook then
		if isYank and yankReady() then pullPress = { t = os.clock() } else tryReel() end
	elseif isYank then tryYank() end
	-- (X: the AUTO GRAPPLE. a pad's D-Right is the emote wheel's outside a live match round: FlairClient)
	if Binds.is("reel", io) then tryLock() end
	if Binds.is("sprint", io) then keys.sprint = Binds.press("sprint", true)
	elseif Binds.is("crouch", io) and not (st.hook and (isYank or isReel)) then keys.crouch = Binds.press("crouch", true) -- (on a rope a pad's B is the yank's and the reel's)
	elseif k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonA then keys.jump = true; keys.jumpPressed = true; pressT = os.clock()
	elseif Binds.is("grapple", io) then keys.hook = true; tryHook()
	elseif Binds.is("camera", io) then thirdPerson = not thirdPerson; setCamera()
	end
end)
Keys.ended(function(io: InputObject)
	local k = io.KeyCode
	local isReel = Binds.is("reelin", io)
	if isReel or Binds.is("yank", io) then
		if pullPress then pullPress = nil; tryYank() -- (let go inside reelTap: a tap, the yank)
		elseif reel and isReel then reel = nil end -- (let go: the rope stays, and so does your speed)
	end
	if Binds.is("sprint", io) then keys.sprint = Binds.press("sprint", false)
	elseif Binds.is("crouch", io) then keys.crouch = Binds.press("crouch", false)
	elseif k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonA then keys.jump = false
	elseif Binds.is("grapple", io) then keys.hook = false; releaseHook(true)
	end
end)

-- the controller pieces on a fresh character
local lv: LinearVelocity? = nil
local lastSet: Vector3? = nil -- the velocity we asked for last step (the fling guard compares against it)
local hipBase = 2
local function setup(ch: Model)
	releaseHook(false)
	st = Movement.newState()
	-- (a toggled sprint or crouch ends with the life)
	if Binds.toggles("sprint") then keys.sprint = false; Binds.clear("sprint") end
	if Binds.toggles("crouch") then keys.crouch = false; Binds.clear("crouch") end
	local hum = ch:WaitForChild("Humanoid") :: Humanoid
	local root = ch:WaitForChild("HumanoidRootPart") :: BasePart
	hum.UseJumpPower = true
	hum.JumpPower = Config.jump
	hum.WalkSpeed = Config.gSpeed
	-- never trip over: a bump that tilts the body must not drop it into the Humanoid's own fall-over states (the
	-- marble slip and the grapple's BONK go over on purpose, with PlatformStand)
	hum:SetStateEnabled(Enum.HumanoidStateType.FallingDown, false)
	hum:SetStateEnabled(Enum.HumanoidStateType.Ragdoll, false)
	hipBase = hum.HipHeight
	lastSet = nil
	Body.attach(st, hum, root)
	local att = root:FindFirstChild("RootAttachment") :: Attachment? or Instance.new("Attachment", root)
	local v = Instance.new("LinearVelocity")
	v.Name = "JankMove"
	v.Attachment0 = att
	v.RelativeTo = Enum.ActuatorRelativeTo.World
	v.VelocityConstraintMode = Enum.VelocityConstraintMode.Plane
	v.PrimaryTangentAxis = Vector3.xAxis
	v.SecondaryTangentAxis = Vector3.zAxis
	-- about 3500 studs/s² on a light avatar: plenty in the air and with the Humanoid steered along (see "steering"),
	-- gentle enough that pressing into a wall, a kerb or another body can't build the huge contact shove 1e7 did
	v.MaxForce = math.max(2e4, root.AssemblyMass * 3500)
	v.Parent = root
	lv = v
	hum.Died:Connect(function() releaseHook(false); v.Enabled = false end)
	setCamera()
end
player.CharacterAdded:Connect(setup)
if player.Character then task.spawn(setup, player.Character) end

local lastPad = 0
-- the fling guard's room (studs/s in one step): sideways nothing of ours adds speed outside the maths; upwards the
-- Humanoid's own jump (a slide jump is the biggest) and stepping up a kerb have to fit
local FLING_SIDE = 6 * Config.S
local FLING_UP = Config.jump * Config.slideJumpUp + 4 * Config.S
local STEP_UP = 0.6 * Config.S -- the web game's step-up (shared/physics.js PH.step = 0.6 m)
local stepParams = RaycastParams.new()
stepParams.FilterType = Enum.RaycastFilterType.Exclude
stepParams.RespectCanCollide = true
local jumpBoostUntil: number? = nil
local eye = Config.standEye
-- steering the Humanoid. its own ground controller is very strong: left to walk where the keys point at WalkSpeed it
-- fights the LinearVelocity on every slide, bhop landing and knockback, which is why the LinearVelocity needed 1e7 (and
-- 1e7 pressed into a kerb or a dummy is what flung people). so after reading the keys, each step tells the Humanoid to
-- walk exactly where the maths is taking you, at that speed: it agrees, and the LinearVelocity can stay gentle.
-- the keys come from the control module calling its moveFunction each drawn frame; a step without that call keeps
-- the last keys for 0.15 s, then counts as no input (controls off: the loadout screen), never our own steer read back
local steering, inputFresh = false, false
local lastInput, lastInputT = Vector3.zero, -10
task.spawn(function()
	local ok, controls = pcall(function()
		return (require(player:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any) :: any):GetControls()
	end)
	if ok and type(controls) == "table" then controlsRef = controls end
	if not ok or type(controls) ~= "table" or type(controls.moveFunction) ~= "function" then
		warn("[jankfire] Move: no control module hook, the Humanoid walks on its own")
		return
	end
	local orig = controls.moveFunction
	controls.moveFunction = function(...)
		inputFresh = true
		return orig(...)
	end
	steering = true
end)
-- held at a round's spawn (Matches: SpawnHold while the round counts in): no speed kept, none built, the rope let go;
-- let go, the movement starts from nothing, so nothing carries into the round (18 Nov, the owner: "I got a head start
-- forward because it carried my momentum")
local spawnHeld = false
RunService.PreSimulation:Connect(function(dt: number)
	local ch, hum, root = character()
	if not ch or not hum or not root or not lv then return end
	if Body.flying then lastSet = nil; return end -- (the owner's dev fly drives the body itself: OwnerDev.client)
	if player:GetAttribute("SpawnHold") then
		if not spawnHeld then spawnHeld = true; releaseHook(false) end
		for k, v in Movement.newState() do (st :: any)[k] = v end
		st.hook = nil
		keys.jumpPressed = false
		pressT = -10
		lv.PlaneVelocity = Vector2.zero
		lastSet = Vector3.zero
		return
	elseif spawnHeld then
		spawnHeld = false
		for k, v in Movement.newState() do (st :: any)[k] = v end
		lv.PlaneVelocity = Vector2.zero
		lastSet = Vector3.zero
	end
	dt = math.min(dt, 1 / 20)
	local v = root.AssemblyLinearVelocity
	local swimming = hum:GetState() == Enum.HumanoidStateType.Swimming
	-- the fling guard. the maths below starts from the body's real velocity, and the LinearVelocity then holds whatever
	-- it says: so a one-step collision spike (brushing a kerb, a sill, a dummy, another player) used to be read back
	-- in and held, spinning you up and throwing you across the map. a jump in speed that none of our own moves made
	-- (Body.kick: pushes, knockback, slips, launches; pads and the rope are in lastSet already) is put back
	-- (19 Nov 2026, the owner: marbles or a Chicken Rocket "on certain walls or corners ... launches you super far
	-- away". the guard was off for a whole slip (PlatformStand) and for 0.15 s after every shove, so a body thrown or
	-- tumbling into a corner kept the wall's push-back, and on your back there's no friction to eat it. now it stays on:
	-- through a slip, and just after a throw it lets through what the throw set (Body.throwV), nothing more. a bare kick,
	-- Move's own pulls and the dash, still passes as before; the grapple's BONK ragdoll, PlatformStand too, stays free)
	local kicked = os.clock() - Body.kickT <= 0.15
	local tv = Body.throwV
	if lastSet and (not hum.PlatformStand or Body.slipping()) and (not kicked or tv) then
		local ref = lastSet
		if kicked and tv and Vector3.new(tv.X, 0, tv.Z).Magnitude > Vector3.new(lastSet.X, 0, lastSet.Z).Magnitude then ref = tv end
		local upRef = if kicked and tv then math.max(lastSet.Y, tv.Y, 0) else math.max(lastSet.Y, 0)
		local h, hl = Vector3.new(v.X, 0, v.Z), Vector3.new(ref.X, 0, ref.Z)
		local vy, spiked = v.Y, false
		if h.Magnitude > hl.Magnitude + FLING_SIDE then h = hl; spiked = true end
		if not swimming and vy > upRef + FLING_UP then vy = upRef; spiked = true end
		if spiked then
			v = Vector3.new(h.X, vy, h.Z)
			root.AssemblyLinearVelocity = v
		end
	end
	-- and no tumbling: the Humanoid turns you about the vertical itself; spin about any other axis is a bump
	if not hum.PlatformStand then
		local w = root.AssemblyAngularVelocity
		if math.abs(w.X) + math.abs(w.Z) > 0.5 or math.abs(w.Y) > 30 then
			root.AssemblyAngularVelocity = Vector3.new(0, math.clamp(w.Y, -30, 30), 0)
		end
	end
	st.vx, st.vy, st.vz = v.X, v.Y, v.Z
	local grounded = not swimming and hum.FloorMaterial ~= Enum.Material.Air and v.Y < 1
	st.onGround = grounded
	st.groundTicks = if grounded then st.groundTicks + 1 else 0
	-- the wish direction: the control module's move vector is already camera-relative (MoveDirection)
	-- (the control module runs once per drawn frame, this once per physics frame: when drawing is throttled, an
	-- unfocused or minimised window, some steps get no fresh call. keep the last real keys for a moment then)
	local md: Vector3
	if not steering then
		md = hum.MoveDirection
	elseif inputFresh then
		md = hum.MoveDirection
		lastInput, lastInputT = md, os.clock()
	else
		md = if os.clock() - lastInputT < 0.15 then lastInput else Vector3.zero
	end
	inputFresh = false
	local look = camera.CFrame.LookVector
	local fw = Vector3.new(look.X, 0, look.Z)
	local fwd = fw.Magnitude > 0 and md.Magnitude > 0 and md:Dot(fw.Unit) > 0.3
	-- jumping. the phone's jump button isn't a key: read it from the control module, a new touch = a fresh press
	local touchHeld = false
	local tj = controlsRef and controlsRef.touchJumpController
	if tj then
		local okJ, j = pcall(function() return tj:GetIsJumping() end)
		touchHeld = okJ and j == true
	end
	if touchHeld and not touchWas then pressT = os.clock(); keys.jumpPressed = true end
	touchWas = touchHeld
	-- a bhop needs a fresh press (Movement.step): holding Space still hops, the Humanoid re-jumps, but each landing
	-- is a plain ground step. a tap made just before landing (the buffer) jumps you as you touch down
	local fresh = os.clock() - pressT <= JUMP_BUF
	local held = keys.jump or touchHeld
	-- (a fresh press jumps you now, below: a released key has already told the Humanoid "no jump" this frame, and a
	-- held one only gets it to jump again about 0.13 s after landing, past the bhop window)
	local jumpNow = grounded and fresh and not st.hook and not Body.slipping() and not Body.pinned() and not Body.stunned()
	local inp: Movement.Input = {
		wx = md.X, wz = md.Z, forward = fwd, sprint = keys.sprint, crouch = keys.crouch,
		jump = held or (grounded and fresh and not Body.slipping()), jumpPressed = keys.jumpPressed, fresh = fresh,
		lookX = look.X, lookZ = look.Z,
	}
	keys.jumpPressed = false
	if Body.stunned() then inp.wx, inp.wz, inp.jump, inp.jumpPressed, inp.forward, inp.sprint = 0, 0, false, false, false, false end -- (tased: frozen)
	if grounded and inp.jump and not st.hook then pressT = -10 end -- (one press, one jump)
	local chest = root.Position -- (the root's centre sits about 1 m over the feet: the web game's chest)
	local event: any = nil
	if pullPress and os.clock() - pullPress.t >= Config.hook.reelTap then pullPress = nil; tryReel() end -- (held: the reel)
	-- a person on the rope (above): the end follows their chest; gone, reeled in, or out of sight too long, it lets go
	-- (a tie, Config.hook.TIE, holds however close: only a reel lets go there, below)
	if st.hook and hookBody then
		local tr = bodyRoot(hookBody)
		if not tr then
			releaseHook(true)
		else
			local c = tr.Position + Vector3.new(0, Config.hook.bodyUp, 0)
			local h = st.hook :: any
			h.ax, h.ay, h.az = c.X, c.Y, c.Z
			local nowL = os.clock()
			local lk = hookLock
			local dist = (c - chest).Magnitude
			if lk and nowL >= lk.untilT then
				releaseHook(true) -- (the lock-on's time is up)
			elseif not h.tie and not reel and dist < Config.hook.bodyLet then
				-- there: a gun lets go (your momentum carries you into them); a melee weapon ties on for the rest of the lock
				-- (Movement.ropeStep's tie: no pull, you walk, they can't get further than the rope)
				if lk and lk.melee then
					h.tie, h.len = true, math.max(dist, Config.hook.tieMin)
					lockShow(player:GetAttribute("HookLockEnd") :: any, player:GetAttribute("HookLockDur") :: any, true)
				else
					releaseHook(true)
				end
			elseif nowL - hookLookT >= 0.1 then
				local eye = root.Position + Vector3.new(0, 1.5, 0)
				bodyParams.FilterDescendantsInstances = { ch, hookBody :: Model }
				hookBlind = if workspace:Raycast(eye, c - eye, bodyParams) then hookBlind + (nowL - hookLookT) else 0
				hookLookT = nowL
				if hookBlind >= Config.hook.bodyBlind then releaseHook(true) end
			end
		end
	elseif not st.hook and hookBody then
		hookBody = nil
		player:SetAttribute("HookBody", nil)
	end
	if swimming then
		-- swimming (the Rooftop pool is Terrain water): paddle where you look, with water drag. Space swims up (and pops
		-- you out at the edge), C dives; with nothing pressed the Humanoid's own buoyancy holds you at the surface
		st.sliding = false
		local spd = Config.gSpeed * (if keys.sprint then 0.75 else 0.55)
		local k = math.min(1, dt * 3.5)
		st.vx += (md.X * spd - st.vx) * k
		st.vz += (md.Z * spd - st.vz) * k
		local up: number? = nil
		if keys.jump then up = Config.jump * 0.75
		elseif keys.crouch then up = -spd * 0.7
		elseif fwd and math.abs(look.Y) > 0.3 then up = look.Y * spd end
		if up then st.vy += (up - st.vy) * math.min(1, dt * 5) end
	else
		st.speedMul = Body.speedMul * Body.boost * Body.wet * Body.devSpeed * Body.mini * Body.zm -- (the gun in your hands: the SMG is light, the Belt Sander isn't; slower while aiming; soaked; the boxing guard)
		st.grip = Body.grip -- (soaked by a Water Pistol: slidey)
		st.hookMul = tonumber(player:GetAttribute("ModeHook")) or 1 -- (spoons & grapples: the rope pulls x1.35, Modes.luau)
		event = Movement.step(st, inp, dt, workspace.Gravity, chest.X, chest.Y, chest.Z)
	end
	if Body.onStep then Body.onStep(st, chest, dt) end -- (a black hole eating your speed: Utility.client.luau)
	Body.slipClamp(st) -- (19 Nov 2026, the fling fix: on your back on marbles, no faster than the slip allows)
	-- (weapons batch A) nailed to a wall by a Nail Gun: pulled to the spot (web primaries.js: (spot - pos) x 14, at most
	-- 30 m/s), no gravity, no jumping, until the pin's time is up. you can still aim and shoot
	-- (the Scythe's dash: the server's path, run here at its speed, up or down too; the anti-cheat was told, ACGrace)
	local dsh = Body.dash
	local BodyA: any = Body -- (dashWas: the dash ran last frame)
	if dsh and Body.dashing() then
		if dsh.add then
			-- (26 Nov 2026, the owner: the "syctghe dash break[s] your momentum") on top of the run you had when it began, no
			-- faster in all than the quicker of the two: from a standstill it's the dash as before, flying it bends your path
			if BodyA.dashFor ~= dsh then BodyA.dashFor, BodyA.dashPre = dsh, Vector3.new(st.vx, 0, st.vz) end
			local pre: Vector3 = BodyA.dashPre
			local hv = pre + Vector3.new(dsh.v.X, 0, dsh.v.Z)
			local capH = math.max(pre.Magnitude, Vector3.new(dsh.v.X, 0, dsh.v.Z).Magnitude)
			if hv.Magnitude > capH then hv = hv.Unit * capH end
			st.vx, st.vz = hv.X, hv.Z
		else
			st.vx, st.vz = dsh.v.X, dsh.v.Z
		end
		-- (19 Nov 2026: the dash follows your look, up or down too) its own climb or drop while it runs; a level one keeps you off the floor as before
		st.vy = if math.abs(dsh.v.Y) > 1 then dsh.v.Y else math.max(st.vy, 0)
		Body.kick()
		BodyA.dashWas = dsh.v
	elseif BodyA.dashWas then
		-- the dash just ended: one that went up or down keeps almost none of its burst (a dash, not a launch): its climb
		-- 12 studs/s at most, its run a sprint's at most (in the air nothing else would slow it)
		local was: Vector3 = BodyA.dashWas
		BodyA.dashWas = nil
		local pre: Vector3? = if BodyA.dashFor and BodyA.dashFor.add then BodyA.dashPre else nil
		BodyA.dashFor, BodyA.dashPre = nil, nil
		if pre then
			-- (26 Nov 2026) the momentum you came in with is yours again: a level dash carries on as it went (no faster than the
			-- quicker of your run and its burst), one that went up or down hands back just your own run
			local hv = if math.abs(was.Y) > 1 then pre else pre + Vector3.new(was.X, 0, was.Z)
			local capH = if math.abs(was.Y) > 1 then pre.Magnitude else math.max(pre.Magnitude, Vector3.new(was.X, 0, was.Z).Magnitude)
			if hv.Magnitude > capH and hv.Magnitude > 1e-3 then hv = hv.Unit * capH end
			st.vx, st.vz = hv.X, hv.Z
			if math.abs(was.Y) > 1 and st.vy > 12 then st.vy = 12 end
		elseif math.abs(was.Y) > 1 then
			if st.vy > 12 then st.vy = 12 end
			local cap = Config.gSpeed * Config.sprintMul
			local hs = math.sqrt(st.vx * st.vx + st.vz * st.vz)
			if hs > cap then st.vx, st.vz = st.vx * cap / hs, st.vz * cap / hs end
		end
	end
	-- (batch E: on a Shopping Cart you go where it rolls; CartRide.client drives it)
	local rd = Body.ride
	if rd then st.vx, st.vz = rd.v.X, rd.v.Z end
	local pin = Body.pin
	if pin and Body.pinned() then
		local d = pin.at + Vector3.new(0, 3, 0) - chest
		local v = d * 14
		if v.Magnitude > 90 then v = v.Unit * 90 end
		st.vx, st.vy, st.vz = v.X, v.Y, v.Z
		Body.kick() -- (Move's fling guard: our own pull)
	end
	-- the reel (tryReel, held): along the rope to its end as it is now (a person's chest moves with them), at a steady
	-- reelSpeed (reached in a few frames). there: reelKeep of the speed carries on; off a wall point the rope goes, off
	-- a person a gun lets go and a melee weapon ties on (the lock-on, above), and the first swing gets Melee.REEL_HIT
	-- (the server's say: "reeled"). out of time or let go: the rope stays, and your speed with it
	if reel then
		local h = st.hook :: any
		local to = if h then Vector3.new(h.ax, h.ay, h.az) else nil
		local d = if to then to - chest else Vector3.zero
		local arrive = if hookBody then Config.hook.reelBody else Config.hook.reelArrive
		if not to then
			reel = nil
		elseif d.Magnitude <= arrive then
			reel = nil
			st.vx, st.vy, st.vz = st.vx * Config.hook.reelKeep, st.vy * Config.hook.reelKeep, st.vz * Config.hook.reelKeep
			local lk = hookLock
			if hookBody then
				GrappleRemote:FireServer("reeled")
				player:SetAttribute("ReelHit", workspace:GetServerTimeNow() + MeleeX.REEL_HIT.window) -- (Arsenal's swing reads it)
			end
			if hookBody and lk and lk.melee then
				h.tie, h.len = true, math.max(d.Magnitude, Config.hook.tieMin)
				lockShow(player:GetAttribute("HookLockEnd") :: any, player:GetAttribute("HookLockDur") :: any, true)
			else
				releaseHook(true)
			end
		elseif os.clock() > (reel :: any).untilT then
			reel = nil
		else
			local v = d.Unit * Config.hook.reelSpeed
			local k = math.min(1, dt * 25)
			st.vx += (v.X - st.vx) * k; st.vy += (v.Y - st.vy) * k; st.vz += (v.Z - st.vz) * k
			Body.kick() -- (Move's fling guard: our own pull)
		end
	end
	-- (26 Nov 2026) the melee lunge: straight at the one you lunged at (MeleeLunge; its server say-so told the anti-cheat)
	MeleeX.step(st, chest, dt, grounded)
	if event == "grappleJump" then
		dropRope(); GrappleRemote:FireServer("release")
		Hud.callout("GRAPPLE JUMP", 0.6)
	elseif event == "slideJump" then
		-- the extra height: this jump's JumpPower (the Humanoid does the jump itself, after this, in the same step)
		hum.JumpPower = Config.jump * Config.slideJumpUp
		jumpBoostUntil = os.clock() + 0.25
		Hud.callout("SLIDE JUMP", 0.5)
	elseif event == "bhop" and st.combo >= 3 then
		Hud.callout("BHOP x" .. st.combo, 0.5)
	end
	if jumpBoostUntil and os.clock() > jumpBoostUntil then
		hum.JumpPower = Config.jump
		jumpBoostUntil = nil
	end
	if jumpNow and not swimming then
		-- (the jump itself, this step: the Humanoid's own jump lags several steps out of its Landed state, and those
		-- steps' friction would eat the bhop)
		st.vy = math.max(st.vy, hum.JumpPower)
		root.CFrame += Vector3.new(0, 0.05, 0)
		hum:ChangeState(Enum.HumanoidStateType.Jumping)
	end
	-- jump pads: stand on one, get thrown (its Pad attribute is the launch velocity)
	local now = os.clock()
	if grounded and now - lastPad > 0.4 then
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Exclude
		params.FilterDescendantsInstances = { ch }
		local hit = workspace:Raycast(root.Position, Vector3.new(0, -hum.HipHeight - 2.5, 0), params)
		local pad = hit and hit.Instance:GetAttribute("Pad")
		if typeof(pad) == "Vector3" then
			lastPad = now
			st.vx, st.vy, st.vz = pad.X, pad.Y, pad.Z
			hum:ChangeState(Enum.HumanoidStateType.Freefall)
			Hud.callout("BOING", 0.5)
		elseif hit and (hit.Instance:GetAttribute("Mat") == "ledge" or hit.Instance:GetAttribute("Slide")) and inArena(root.Position) then
			-- the step round a walled arena's edge: no place to stand. back you go, toward the middle. (Slide: a roof over
			-- a spawn, the same: roofs.py open_up, 18 Nov 2026)
			local at = player:GetAttribute("ArenaAt") :: Vector3
			local d = Vector3.new(at.X - root.Position.X, 0, at.Z - root.Position.Z)
			if d.Magnitude > 1 then
				d = d.Unit
				st.vx, st.vz = d.X * LEDGE_PUSH, d.Z * LEDGE_PUSH
				st.vy = math.max(st.vy, LEDGE_HOP)
				hum:ChangeState(Enum.HumanoidStateType.Freefall)
			end
		end
	end
	-- stepping up: JANKFIRE walks onto anything 0.6 m (1.8 studs) high or lower without slowing (shared/physics.js
	-- PH.step). the Humanoid alone only manages about 1 stud at a sprint (the old 1e7 drive bulldozed over the rest),
	-- so a lip just ahead of your feet that you could stand on lifts you onto it
	local hsNow = math.sqrt(st.vx * st.vx + st.vz * st.vz)
	if grounded and st.vy < 1 and hsNow > 2 then
		stepParams.FilterDescendantsInstances = { ch }
		local dir = Vector3.new(st.vx, 0, st.vz) / hsNow
		local feetY = root.Position.Y - root.Size.Y / 2 - hum.HipHeight
		local reach = 1.4 + hsNow * dt
		local at = Vector3.new(root.Position.X, feetY + 0.15, root.Position.Z)
		local low = workspace:Raycast(at, dir * reach, stepParams)
		local body = low and low.Instance:FindFirstAncestorOfClass("Model")
		if low and math.abs(low.Normal.Y) < 0.35 and not (body and body:FindFirstChildOfClass("Humanoid")) then
			local over = Vector3.new(0, STEP_UP + 0.25 - 0.15, 0) -- (just over the highest step: is the way clear?)
			if not workspace:Raycast(at + over, dir * (reach + 0.6), stepParams) then
				local top = workspace:Raycast(low.Position + dir * 0.4 + Vector3.new(0, STEP_UP + 0.25 - (low.Position.Y - feetY), 0), Vector3.new(0, -(STEP_UP + 0.25), 0), stepParams)
				local rise = top and top.Position.Y - feetY
				if top and rise and top.Normal.Y > 0.7 and rise > 0.9 and rise <= STEP_UP then
					root.CFrame += Vector3.new(0, rise + 0.05, 0)
				end
			end
		end
	end
	-- the sky line: over it the climb eases off (rope, pad, launch, anything) and stops SKY_CAP higher, so the old lid's
	-- solids (their tops at 150, out of sight) can't be stood on
	local skyY = player:GetAttribute("SkyY")
	if type(skyY) == "number" and st.vy > 0 then
		local over = root.Position.Y - skyY
		if over > 0 and inArena(root.Position) then st.vy = math.min(st.vy, math.max(0, (SKY_CAP - over) * 5)) end
	end
	-- (batch E: on someone's Lasso you go where the server swings you, LassoClient)
	local hd = Body.held
	if hd then st.vx, st.vy, st.vz = hd.v.X, hd.v.Y, hd.v.Z end
	lv.PlaneVelocity = Vector2.new(st.vx, st.vz)
	if math.abs(st.vy - v.Y) > 1e-3 then root.AssemblyLinearVelocity = Vector3.new(st.vx, st.vy, st.vz) end
	-- (the Humanoid's own jump lands after this, inside FLING_UP)
	lastSet = Vector3.new(st.vx, st.vy, st.vz)
	-- on the rope right now: GrappleImpacts only counts swings that are really on it
	if player:GetAttribute("OnRope") ~= (st.hook ~= nil) then player:SetAttribute("OnRope", st.hook ~= nil) end
	-- where the rope bites (WallGrid.client draws the grid there when it's the wall box)
	local hookAt = if st.hook and not hookBody then Vector3.new(st.hook.ax, st.hook.ay, st.hook.az) else nil -- (not a person)
	if player:GetAttribute("HookAt") ~= hookAt then player:SetAttribute("HookAt", hookAt) end
	-- sprinting right now (SpeedLines.client's FOV kick: +6, as the web's)
	if player:GetAttribute("Sprinting") ~= st.sprinting then player:SetAttribute("Sprinting", st.sprinting) end
	local hs = math.sqrt(st.vx * st.vx + st.vz * st.vz)
	if steering and not swimming then
		if hs > 0.5 then
			hum.WalkSpeed = hs
			hum:Move(Vector3.new(st.vx / hs, 0, st.vz / hs), false)
		else
			hum:Move(Vector3.zero, false)
		end
	else
		hum.WalkSpeed = Config.gSpeed * (if st.sprinting then Config.sprintMul elseif st.crouching then Config.crouchMul else 1) * Body.speedMul * Body.boost * Body.devSpeed
	end
	-- the camera drops for a crouch / slide, the body sinks a bit into a slide (jank)
	eye += (Movement.eyeTarget(st) - eye) * math.min(1, dt * 14)
	hum.CameraOffset = Vector3.new(0, eye - Config.standEye, 0)
	hum.HipHeight = hipBase - (if st.sliding then 0.9 else 0) - Body.sink -- (Body.sink: HOLDOUT's lie-down)
	Hud.speed(math.sqrt(st.vx * st.vx + st.vz * st.vz) / Config.S, st.sliding, st.hook ~= nil)
	if rope and not st.hook then dropRope() end
end)
