--!strict
-- JANKFIRE movement on the default Roblox character: run, sprint (Shift), slide (C / Ctrl while fast), bhop (jump as
-- you land), air strafing, the grapple (hold E: aim at a wall), grapple jump (Space on the rope), jump pads.
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
local Body = require(script.Parent:WaitForChild("Body")) -- step 2: lets the weapons push you (recoil, knockback, slips)
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
local controlsRef: any = nil -- (the control module: the phone's jump button is read from it)
local touchWas = false
local st = Movement.newState()
local rope: Beam? = nil
local ropeAnchor: Attachment? = nil
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

local function releaseHook(tellServer: boolean)
	if st.hook then st.hook = nil; st.lift = 1 end
	dropRope()
	if tellServer then GrappleRemote:FireServer("release") end
end

local function character(): (Model?, Humanoid?, BasePart?)
	local ch = player.Character
	if not ch then return nil end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root or hum.Health <= 0 then return ch, nil, nil end
	return ch, hum, root
end

-- E: fire the hook where you look (map only: the city's deco can't be hooked, same as the web game's boxes)
local function tryHook()
	local ch, hum, root = character()
	if not ch or not hum or not root or st.hook then return end
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
	if not hit then
		Hud.callout("TOO FAR", 0.5)
		return
	end
	local p = hit.Position
	st.hook = { ax = p.X, ay = p.Y, az = p.Z, len = nil }
	GrappleRemote:FireServer("hook", p)
	-- our own rope right away (the server draws it for everyone else)
	local a0 = (ch:FindFirstChild("RightHand") or root):FindFirstChildWhichIsA("Attachment") or root:FindFirstChildWhichIsA("Attachment")
	local a1 = Instance.new("Attachment")
	a1.WorldPosition = p
	a1.Parent = workspace.Terrain
	local b = Instance.new("Beam")
	b.Attachment0 = a0; b.Attachment1 = a1
	b.Width0 = 0.25; b.Width1 = 0.25; b.FaceCamera = true; b.Segments = 1
	b.Color = ColorSequence.new(Color3.fromRGB(236, 238, 242), Color3.fromRGB(176, 182, 192)) -- (a pale steel cable)
	b.LightEmission = 0.3
	b.Parent = workspace.Terrain
	rope, ropeAnchor = b, a1
end

GrappleRemote.OnClientEvent:Connect(function(what: string)
	if what == "cut" then -- the server said no (out of range, no line to it, too many hooks)
		releaseHook(false)
	end
end)

UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or game:GetService("Players").LocalPlayer:GetAttribute("LoadoutOpen") then return end -- (the loadout screen is up)
	local k = io.KeyCode
	if k == Enum.KeyCode.LeftShift or k == Enum.KeyCode.RightShift then keys.sprint = true
	elseif k == Enum.KeyCode.C or k == Enum.KeyCode.LeftControl then keys.crouch = true
	elseif k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonA then keys.jump = true; keys.jumpPressed = true; pressT = os.clock()
	elseif k == Enum.KeyCode.E or k == Enum.KeyCode.ButtonL2 then keys.hook = true; tryHook()
	elseif k == Enum.KeyCode.V then thirdPerson = not thirdPerson; setCamera()
	end
end)
UserInputService.InputEnded:Connect(function(io: InputObject)
	local k = io.KeyCode
	if k == Enum.KeyCode.LeftShift or k == Enum.KeyCode.RightShift then keys.sprint = false
	elseif k == Enum.KeyCode.C or k == Enum.KeyCode.LeftControl then keys.crouch = false
	elseif k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonA then keys.jump = false
	elseif k == Enum.KeyCode.E or k == Enum.KeyCode.ButtonL2 then keys.hook = false; releaseHook(true)
	end
end)

-- the controller pieces on a fresh character
local lv: LinearVelocity? = nil
local lastSet: Vector3? = nil -- the velocity we asked for last step (the fling guard compares against it)
local hipBase = 2
local function setup(ch: Model)
	releaseHook(false)
	st = Movement.newState()
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
RunService.PreSimulation:Connect(function(dt: number)
	local ch, hum, root = character()
	if not ch or not hum or not root or not lv then return end
	dt = math.min(dt, 1 / 20)
	local v = root.AssemblyLinearVelocity
	local swimming = hum:GetState() == Enum.HumanoidStateType.Swimming
	-- the fling guard. the maths below starts from the body's real velocity, and the LinearVelocity then holds whatever
	-- it says: so a one-step collision spike (brushing a kerb, a sill, a dummy, another player) used to be read back
	-- in and held, spinning you up and throwing you across the map. a jump in speed that none of our own moves made
	-- (Body.kick: pushes, knockback, slips, launches; pads and the rope are in lastSet already) is put back
	if lastSet and not hum.PlatformStand and os.clock() - Body.kickT > 0.15 then
		local h, hl = Vector3.new(v.X, 0, v.Z), Vector3.new(lastSet.X, 0, lastSet.Z)
		local vy, spiked = v.Y, false
		if h.Magnitude > hl.Magnitude + FLING_SIDE then h = hl; spiked = true end
		if not swimming and vy > math.max(lastSet.Y, 0) + FLING_UP then vy = math.max(lastSet.Y, 0); spiked = true end
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
	local jumpNow = grounded and fresh and not st.hook and not Body.slipping()
	local inp: Movement.Input = {
		wx = md.X, wz = md.Z, forward = fwd, sprint = keys.sprint, crouch = keys.crouch,
		jump = held or (grounded and fresh and not Body.slipping()), jumpPressed = keys.jumpPressed, fresh = fresh,
		lookX = look.X, lookZ = look.Z,
	}
	keys.jumpPressed = false
	if grounded and inp.jump and not st.hook then pressT = -10 end -- (one press, one jump)
	local chest = root.Position -- (the root's centre sits about 1 m over the feet: the web game's chest)
	local event: any = nil
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
		st.speedMul = Body.speedMul * Body.boost -- (the gun in your hands: the SMG is light, the Belt Sander isn't; slower while aiming)
		event = Movement.step(st, inp, dt, workspace.Gravity, chest.X, chest.Y, chest.Z)
	end
	if Body.onStep then Body.onStep(st, chest, dt) end -- (a black hole eating your speed: Utility.client.luau)
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
	lv.PlaneVelocity = Vector2.new(st.vx, st.vz)
	if math.abs(st.vy - v.Y) > 1e-3 then root.AssemblyLinearVelocity = Vector3.new(st.vx, st.vy, st.vz) end
	-- (the Humanoid's own jump lands after this, inside FLING_UP)
	lastSet = Vector3.new(st.vx, st.vy, st.vz)
	-- on the rope right now: GrappleImpacts only counts swings that are really on it
	if player:GetAttribute("OnRope") ~= (st.hook ~= nil) then player:SetAttribute("OnRope", st.hook ~= nil) end
	local hs = math.sqrt(st.vx * st.vx + st.vz * st.vz)
	if steering and not swimming then
		if hs > 0.5 then
			hum.WalkSpeed = hs
			hum:Move(Vector3.new(st.vx / hs, 0, st.vz / hs), false)
		else
			hum:Move(Vector3.zero, false)
		end
	else
		hum.WalkSpeed = Config.gSpeed * (if st.sprinting then Config.sprintMul elseif st.crouching then Config.crouchMul else 1) * Body.speedMul * Body.boost
	end
	-- the camera drops for a crouch / slide, the body sinks a bit into a slide (jank)
	eye += (Movement.eyeTarget(st) - eye) * math.min(1, dt * 14)
	hum.CameraOffset = Vector3.new(0, eye - Config.standEye, 0)
	hum.HipHeight = hipBase - (if st.sliding then 0.9 else 0)
	Hud.speed(math.sqrt(st.vx * st.vx + st.vz * st.vz) / Config.S, st.sliding, st.hook ~= nil)
	if rope and not st.hook then dropRope() end
end)
