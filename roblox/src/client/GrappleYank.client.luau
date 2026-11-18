--!strict
-- the yank, as everyone sees and hears it (18 Nov 2026, the owner: "when you grapple someone maybe you can press a
-- button to like pull them towards you??"; Move.client's tryYank asks, Main.server's yank() throws them and tells
-- everyone: Grapple remote, "yank", the yanker's body, the one yanked, mate = a teammate's gentle pull): the rope snaps
-- taut for a moment, hand to chest, bright and dead straight, and cracks (the recorded "ropesnap"); the one yanked
-- trails a short pale streak as they fly. nothing on screen. cheap: one beam and one trail, gone within a second
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Config"))
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local GrappleRemote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Grapple") :: RemoteEvent
local me = Players.LocalPlayer

local STEEL, PALE = Color3.fromRGB(246, 248, 252), Color3.fromRGB(188, 196, 208)
local SNAP_T, TRAIL_T, TRAIL_LIFE = 0.22, 0.55, 0.28 -- s: the taut rope's flash, the trail's streak, a streak bit's life

local function snap(from: Model, to: Model, mate: boolean)
	local troot = to:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hand = (from:FindFirstChild("RightHand") or from:FindFirstChild("HumanoidRootPart")) :: BasePart?
	if not troot or not hand then return end
	-- (a test, for photos: YankFxHold on you = hold the snap and the streak that many seconds)
	local hold = me:GetAttribute("YankFxHold")
	local snapT = if type(hold) == "number" then hold else SNAP_T
	local trailT = if type(hold) == "number" then hold else TRAIL_T
	-- the rope, taut: from the hand to their chest, a straight bright cable that thins and fades
	local a0 = Instance.new("Attachment")
	a0.Name = "YankHand"
	a0.Parent = hand
	local a1 = Instance.new("Attachment")
	a1.Name = "YankTie"
	a1.Position = Vector3.new(0, Config.hook.bodyUp, 0)
	a1.Parent = troot
	local b = Instance.new("Beam")
	b.Name = "YankRope"
	b.Attachment0, b.Attachment1 = a0, a1
	b.FaceCamera, b.Segments, b.CurveSize0, b.CurveSize1 = true, 1, 0, 0
	b.Color = ColorSequence.new(STEEL, PALE)
	b.LightEmission = 0.6
	local w0 = if mate then 0.3 else 0.5
	b.Width0, b.Width1 = w0, w0
	b.Parent = workspace.Terrain
	-- the streak on them while they fly
	local t0 = Instance.new("Attachment")
	t0.Name = "YankTrailTop"
	t0.Position = Vector3.new(0, 1.3, 0)
	t0.Parent = troot
	local t1 = Instance.new("Attachment")
	t1.Name = "YankTrailLow"
	t1.Position = Vector3.new(0, -1.1, 0)
	t1.Parent = troot
	local tr = Instance.new("Trail")
	tr.Name = "YankTrail"
	tr.Attachment0, tr.Attachment1 = t0, t1
	tr.Color = ColorSequence.new(STEEL, PALE)
	tr.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, if mate then 0.6 else 0.35), NumberSequenceKeypoint.new(1, 1) })
	tr.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.15) })
	tr.Lifetime = if type(hold) == "number" then hold else TRAIL_LIFE
	tr.MinLength = 0.05
	tr.LightEmission = 0.5
	tr.FaceCamera = true
	tr.Parent = troot
	-- the crack: yours on you (like your own shots), anyone else's where it bites them
	if from == me.Character then Sfx.play("ropesnap") else Sfx.play("ropesnap", troot.Position) end
	task.spawn(function()
		local start = os.clock()
		while true do
			local k = (os.clock() - start) / snapT
			if k >= 1 or not b.Parent then break end
			local w = w0 * (1 - 0.7 * k)
			b.Width0, b.Width1 = w, w
			b.Transparency = NumberSequence.new(k * k)
			RunService.Heartbeat:Wait()
		end
		b:Destroy(); a0:Destroy(); a1:Destroy()
	end)
	task.delay(trailT, function() if tr.Parent then tr.Enabled = false end end)
	task.delay(trailT + tr.Lifetime + 0.1, function() tr:Destroy(); t0:Destroy(); t1:Destroy() end)
end

GrappleRemote.OnClientEvent:Connect(function(what: unknown, from: unknown, to: unknown, mate: unknown)
	if what ~= "yank" then return end
	if typeof(from) ~= "Instance" or typeof(to) ~= "Instance" or not (from :: Instance):IsA("Model") or not (to :: Instance):IsA("Model") then return end
	local ok, err = pcall(snap, from :: Model, to :: Model, mate == true)
	if not ok then warn("[jankfire] the yank's look: " .. tostring(err)) end
end)
