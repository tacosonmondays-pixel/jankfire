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
local st = Movement.newState()
local rope: Beam? = nil
local ropeAnchor: Attachment? = nil
local thirdPerson = false

local function setCamera()
	player.CameraMode = if thirdPerson then Enum.CameraMode.Classic else Enum.CameraMode.LockFirstPerson
	if thirdPerson then player.CameraMinZoomDistance = 10; player.CameraMaxZoomDistance = 20 else player.CameraMinZoomDistance = 0.5 end
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
	b.Color = ColorSequence.new(Color3.fromRGB(255, 79, 216), Color3.fromRGB(255, 225, 77))
	b.LightEmission = 0.6
	b.Parent = workspace.Terrain
	rope, ropeAnchor = b, a1
end

GrappleRemote.OnClientEvent:Connect(function(what: string)
	if what == "cut" then -- the server said no (out of range, no line to it, too many hooks)
		releaseHook(false)
	end
end)

UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.LeftShift or k == Enum.KeyCode.RightShift then keys.sprint = true
	elseif k == Enum.KeyCode.C or k == Enum.KeyCode.LeftControl then keys.crouch = true
	elseif k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonA then keys.jump = true; keys.jumpPressed = true
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
local hipBase = 2
local function setup(ch: Model)
	releaseHook(false)
	st = Movement.newState()
	local hum = ch:WaitForChild("Humanoid") :: Humanoid
	local root = ch:WaitForChild("HumanoidRootPart") :: BasePart
	hum.UseJumpPower = true
	hum.JumpPower = Config.jump
	hum.WalkSpeed = Config.gSpeed
	hipBase = hum.HipHeight
	Body.attach(st, hum, root)
	local att = root:FindFirstChild("RootAttachment") :: Attachment? or Instance.new("Attachment", root)
	local v = Instance.new("LinearVelocity")
	v.Name = "JankMove"
	v.Attachment0 = att
	v.RelativeTo = Enum.ActuatorRelativeTo.World
	v.VelocityConstraintMode = Enum.VelocityConstraintMode.Plane
	v.PrimaryTangentAxis = Vector3.xAxis
	v.SecondaryTangentAxis = Vector3.zAxis
	v.MaxForce = 1e7
	v.Parent = root
	lv = v
	hum.Died:Connect(function() releaseHook(false); v.Enabled = false end)
	setCamera()
end
player.CharacterAdded:Connect(setup)
if player.Character then task.spawn(setup, player.Character) end

local lastPad = 0
local eye = Config.standEye
RunService.PreSimulation:Connect(function(dt: number)
	local ch, hum, root = character()
	if not ch or not hum or not root or not lv then return end
	dt = math.min(dt, 1 / 20)
	local v = root.AssemblyLinearVelocity
	st.vx, st.vy, st.vz = v.X, v.Y, v.Z
	local grounded = hum.FloorMaterial ~= Enum.Material.Air and v.Y < 1
	st.onGround = grounded
	st.groundTicks = if grounded then st.groundTicks + 1 else 0
	-- the wish direction: the control module's move vector is already camera-relative (MoveDirection)
	local md = hum.MoveDirection
	local look = camera.CFrame.LookVector
	local fw = Vector3.new(look.X, 0, look.Z)
	local fwd = fw.Magnitude > 0 and md.Magnitude > 0 and md:Dot(fw.Unit) > 0.3
	local inp: Movement.Input = {
		wx = md.X, wz = md.Z, forward = fwd, sprint = keys.sprint, crouch = keys.crouch,
		jump = keys.jump, jumpPressed = keys.jumpPressed, lookX = look.X, lookZ = look.Z,
	}
	keys.jumpPressed = false
	local chest = root.Position -- (the root's centre sits about 1 m over the feet: the web game's chest)
	local event = Movement.step(st, inp, dt, workspace.Gravity, chest.X, chest.Y, chest.Z)
	if event == "grappleJump" then
		dropRope(); GrappleRemote:FireServer("release")
		Hud.callout("GRAPPLE JUMP", 0.6)
	elseif event == "bhop" and st.combo >= 3 then
		Hud.callout("BHOP x" .. st.combo, 0.5)
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
	lv.PlaneVelocity = Vector2.new(st.vx, st.vz)
	if math.abs(st.vy - v.Y) > 1e-3 then root.AssemblyLinearVelocity = Vector3.new(st.vx, st.vy, st.vz) end
	hum.WalkSpeed = Config.gSpeed * (if st.sprinting then Config.sprintMul elseif st.crouching then Config.crouchMul else 1)
	-- the camera drops for a crouch / slide, the body sinks a bit into a slide (jank)
	eye += (Movement.eyeTarget(st) - eye) * math.min(1, dt * 14)
	hum.CameraOffset = Vector3.new(0, eye - Config.standEye, 0)
	hum.HipHeight = hipBase - (if st.sliding then 0.9 else 0)
	Hud.speed(math.sqrt(st.vx * st.vx + st.vz * st.vz) / Config.S, st.sliding, st.hook ~= nil)
	if rope and not st.hook then dropRope() end
end)
