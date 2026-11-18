--!strict
-- weapons batch E: your side of the Lasso (LassoServer.server runs the loop, the catch and the swing). Arsenal calls
-- press / release: hold fire to spin (1.1 s to full), let go to throw; with someone on your rope fire or aim lets go.
-- while you hold: where you aim streams to the server 20 times a second, the wheel lets out (up) and reels in (down),
-- R reels in, F lets out. while you're held: you follow where the server puts you; jump or WASD wriggles.
-- everyone's ropes and loops are drawn here (Fx "loop" / "loopx" / "lassohold" / "lassorope" / "lassoend")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Body = require(script.Parent:WaitForChild("Body"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local S = Weapons.S
local LZ = { spinT = 1.1, lenMin = 2 * S, lenMax = 16 * S, wheel = 1.5 * S, reel = 9 * S }
local C = { spinT = nil :: number?, len = 8 * S, sent = 0, wantSet = false, changed = false }

local function remote(): RemoteEvent?
	local r = Remotes:FindFirstChild("Lasso")
	return if r and r:IsA("RemoteEvent") then r else nil
end
local function holding(): boolean return me:GetAttribute("LassoHolding") == true end
local function held(): boolean return me:GetAttribute("LassoHeld") == true end

-- ---------------------------------------------------------------- the spin and the throw
local spinSnd: Sound? = nil
local function loopSound(name: string, parent: Instance): Sound?
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	local s = lib and lib:FindFirstChild(name)
	if not s or not s:IsA("Sound") then return nil end
	local c = s:Clone(); c.Looped = true; c.Parent = parent; c:Play()
	return c
end
function C.press()
	local r = remote()
	if not r then return end
	if holding() then r:FireServer("rel"); return end -- (fire with someone on the rope: let them go)
	if C.spinT then return end
	C.spinT = os.clock()
	r:FireServer("spin")
	local root = me.Character and me.Character:FindFirstChild("HumanoidRootPart")
	if root then spinSnd = loopSound("lasso_spin", root) end
end
function C.release(eye: Vector3, look: Vector3)
	local t0 = C.spinT
	if not t0 then return end
	C.spinT = nil
	if spinSnd then spinSnd:Destroy(); spinSnd = nil end
	local r = remote()
	if r then r:FireServer("throw", eye, look, math.clamp((os.clock() - t0) / LZ.spinT, 0, 1)) end
	Sfx.play("lasso_throw")
end
function C.aimPress() -- (right click with someone on the rope: let go)
	local r = remote()
	if r and holding() then r:FireServer("rel") end
end
function C.spinning(): number return if C.spinT then math.clamp((os.clock() - (C.spinT :: number)) / LZ.spinT, 0, 1) else 0 end

-- the wheel: let out (up) / reel in (down), while you hold someone
UserInputService.InputChanged:Connect(function(io: InputObject)
	if io.UserInputType == Enum.UserInputType.MouseWheel and holding() then
		C.len = math.clamp(C.len + io.Position.Z * LZ.wheel, LZ.lenMin, LZ.lenMax)
		C.changed = true
	end
end)
-- held: jump or WASD wriggles
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or not held() then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Space or k == Enum.KeyCode.W or k == Enum.KeyCode.A or k == Enum.KeyCode.S or k == Enum.KeyCode.D or k == Enum.KeyCode.ButtonA then
		local r = remote()
		if r then r:FireServer("wr") end
	end
end)

-- ---------------------------------------------------------------- held: where the server says you are
local target: { feet: Vector3, v: Vector3 }? = nil
local r0 = remote() or Remotes:WaitForChild("Lasso", 10)
if r0 and r0:IsA("RemoteEvent") then
	r0.OnClientEvent:Connect(function(op: any, p: any, v: any)
		if op == "pos" and typeof(p) == "Vector3" and typeof(v) == "Vector3" then
			target = { feet = p, v = v }
		elseif op == "free" and typeof(v) == "Vector3" then
			target = nil
			Body.held = nil
			local root = me.Character and me.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
			if root then root.AssemblyLinearVelocity = v end -- (off the rope at that speed: you fly on)
		end
	end)
end

-- ---------------------------------------------------------------- everyone's ropes and loops
local folder = Instance.new("Folder")
folder.Name = "JankfireLasso"
folder.Parent = workspace
local function anchorPart(at: Vector3): (Part, Attachment)
	local p = Instance.new("Part")
	p.Size = Vector3.new(0.1, 0.1, 0.1); p.Transparency = 1
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.CFrame = CFrame.new(at)
	p.Parent = folder
	local a = Instance.new("Attachment"); a.Parent = p
	return p, a
end
local function handOf(m: Instance?): Attachment?
	if typeof(m) ~= "Instance" then return nil end
	local hand = (m :: Instance):FindFirstChild("RightHand") or (m :: Instance):FindFirstChild("HumanoidRootPart")
	if not hand or not hand:IsA("BasePart") then return nil end
	local a = hand:FindFirstChild("LassoHand") :: Attachment?
	if not a then
		local na = Instance.new("Attachment"); na.Name = "LassoHand"; na.Parent = hand
		a = na
	end
	return a
end
local function rope(a0: Attachment, a1: Attachment): Beam
	local b = Instance.new("Beam")
	b.Attachment0 = a0; b.Attachment1 = a1
	b.Width0 = 0.12; b.Width1 = 0.12; b.Segments = 8; b.CurveSize0 = 0; b.CurveSize1 = 0
	b.Color = ColorSequence.new(Color3.fromRGB(196, 158, 100)); b.LightInfluence = 1; b.FaceCamera = true
	b.Parent = a1.Parent
	return b
end
type Fly = { ring: Part, p: Vector3, v: Vector3, g: number }
local flying: { [number]: Fly } = {}
type Rope = { far: Part, beam: Beam, ring: Part, snd: Sound? }
local ropes: { [Instance]: Rope } = {}
local function ringPart(at: Vector3): Part
	local ring = Instance.new("Part")
	ring.Shape = Enum.PartType.Cylinder
	ring.Size = Vector3.new(0.08, 1.1 * S, 1.1 * S)
	ring.Color = Color3.fromRGB(196, 158, 100); ring.Material = Enum.Material.Fabric; ring.Transparency = 0.15
	ring.Anchored = true; ring.CanCollide = false; ring.CanQuery = false; ring.CanTouch = false; ring.CastShadow = false
	ring.CFrame = CFrame.new(at) * CFrame.Angles(0, 0, math.pi / 2)
	ring.Parent = folder
	return ring
end
local function dropRope(holder: Instance)
	local r = ropes[holder]
	if not r then return end
	ropes[holder] = nil
	r.far:Destroy(); r.ring:Destroy()
	if r.snd then r.snd:Destroy() end
end
Remotes:WaitForChild("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" then return end
	if f.k == "loop" and type(f.id) == "number" and typeof(f.p) == "Vector3" and typeof(f.v) == "Vector3" then
		flying[f.id] = { ring = ringPart(f.p), p = f.p, v = f.v, g = tonumber(f.g) or 0 }
		if f.by ~= me.UserId then Sfx.play("lasso_throw", f.p, 0.8) end
	elseif f.k == "loopx" and type(f.id) == "number" then
		local fl = flying[f.id]
		flying[f.id] = nil
		if fl then fl.ring:Destroy() end
		if f.caught and typeof(f.p) == "Vector3" then Sfx.play("lasso_catch", f.p, 1) end
	elseif f.k == "lassohold" and typeof(f.holder) == "Instance" and typeof(f.p) == "Vector3" then
		dropRope(f.holder)
		local hand = handOf(f.holder)
		if not hand then return end
		local far, a1 = anchorPart(f.p)
		ropes[f.holder] = { far = far, beam = rope(hand, a1), ring = ringPart(f.p), snd = loopSound("rope_creak", far) }
	elseif f.k == "lassorope" and typeof(f.holder) == "Instance" and typeof(f.p) == "Vector3" then
		local r = ropes[f.holder]
		if r then
			r.far.CFrame = CFrame.new(f.p)
			r.ring.CFrame = CFrame.new(f.p) * CFrame.Angles(0, 0, math.pi / 2) -- (the loop round the waist)
		end
	elseif f.k == "lassoend" and typeof(f.holder) == "Instance" then
		dropRope(f.holder)
	elseif f.k == "lassoslam" and typeof(f.p) == "Vector3" then
		Sfx.play("lasso_slam", f.p, 1)
	end
end)

RunService.RenderStepped:Connect(function(dt: number)
	-- loops in flight
	for _, fl in flying do
		fl.v -= Vector3.new(0, fl.g * dt, 0)
		fl.p += fl.v * dt
		fl.ring.CFrame = CFrame.new(fl.p) * CFrame.Angles(0, 0, math.pi / 2)
	end
	local now = os.clock()
	-- holding: stream where you aim and how long you want the rope
	if holding() then
		if not C.wantSet then -- (the rope starts at the catch's length: the server's)
			local l0 = me:GetAttribute("LassoLen")
			C.len = if type(l0) == "number" then l0 else 8 * S
			C.changed = false
		end
		if UserInputService:IsKeyDown(Enum.KeyCode.R) then C.len = math.max(LZ.lenMin, C.len - LZ.reel * dt); C.changed = true end
		if UserInputService:IsKeyDown(Enum.KeyCode.F) then C.len = math.min(LZ.lenMax, C.len + LZ.reel * dt); C.changed = true end
		if now - C.sent >= 0.05 then
			C.sent = now
			local lk = workspace.CurrentCamera.CFrame.LookVector
			local r = remote()
			if r then r:FireServer("aim", math.atan2(-lk.X, -lk.Z), math.asin(math.clamp(lk.Y, -1, 1)), if C.changed then C.len else nil) end
		end
		C.wantSet = true
	else
		C.wantSet = false
		C.len = 8 * S
	end
	-- held: go where the server says (its last word, carried on by its speed)
	if held() and target then
		local ch = me.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		if root and hum then
			local t = target :: { feet: Vector3, v: Vector3 }
			local want = t.feet + Vector3.new(0, hum.HipHeight + root.Size.Y / 2, 0)
			Body.held = { v = t.v + (want - root.Position) * 12 }
		end
	elseif not held() then
		Body.held = nil
		target = nil
	end
end)

return C
