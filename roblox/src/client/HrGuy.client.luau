--!strict
-- THE TALL GUY FROM HR, on your screen (the server owns him: HrGuy.server; the web's client: public/js/hrguy.js).
-- While he's in workspace.Map.Lore ("HrGuy"): poses him from his Pose seed (the web's pose(): head tilted further,
-- one shoulder down, the clipboard up to his chest: a new, slightly worse pose every time he blinks closer), blinks his
-- earpiece, and tells the server where your camera looks (remote HrLook) while you're on the lot.
-- Staring at him (your HrStare, the server's meter): static over your screen (grey scan lines, the odd red tear, made
-- of plain frames: no picture), the picture shakes and washes out (never crushed to black), and a recorded hiss grows
-- (Pro Sound Effects "Radio And Television Static 2"). Near him: a low recorded drone, even behind you. When he blinks:
-- a step where he lands. When he has you ("hrtake"): full static fading out over 1.2 s and a deep boom; the server puts
-- you back in the spawn lounge. No words on the HUD (the web's "DON'T LOOK AT HIM" lines stay out: no flavour text).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local SoundService = game:GetService("SoundService")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Rigs = require(Shared:WaitForChild("LoreRigs")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local LoreR = Remotes:WaitForChild("Lore") :: RemoteEvent
local LookR = Remotes:WaitForChild("HrLook") :: RemoteEvent
local okSfx, Sfx = pcall(function() return require(script.Parent:WaitForChild("Sfx", 5)) :: any end)

local HISS, DRONE, BOOM = "rbxassetid://9118013971", "rbxassetid://9116328602", "boom"
local SEND_EVERY = 0.12 -- s between look reports while he's here
local IDLE_EVERY = 0.5 -- s between them on the lot while he isn't (he needs them to arrive out of sight)

-- ------------------------------------------------------------------ the static
local gui = Instance.new("ScreenGui")
gui.Name = "HrStatic"
gui.IgnoreGuiInset = true
gui.DisplayOrder = 70
gui.ResetOnSpawn = false
gui.Enabled = false
local veil = Instance.new("Frame")
veil.Size = UDim2.fromScale(1, 1)
veil.BackgroundColor3 = Color3.fromRGB(120, 120, 124)
veil.BorderSizePixel = 0
veil.BackgroundTransparency = 1
veil.Parent = gui
local BARS = 44
local bars: { Frame } = {}
for i = 1, BARS do
	local b = Instance.new("Frame")
	b.BorderSizePixel = 0
	b.AnchorPoint = Vector2.new(0, 0.5)
	b.Size = UDim2.new(1, 0, 0, 3)
	b.Parent = gui
	bars[i] = b
end
local tear = Instance.new("Frame")
tear.BorderSizePixel = 0
tear.BackgroundColor3 = Color3.fromRGB(200, 40, 52)
tear.Size = UDim2.new(1, 0, 0, 6)
tear.Parent = gui
gui.Parent = me:WaitForChild("PlayerGui")
local cc = Instance.new("ColorCorrectionEffect")
cc.Name = "HrWash"
cc.Enabled = false
cc.Parent = Lighting

local function drawStatic(k: number)
	if k < 0.03 then
		if gui.Enabled then gui.Enabled = false end
		if cc.Enabled then cc.Enabled = false end
		return
	end
	gui.Enabled = true
	cc.Enabled = true
	cc.Brightness = k * 0.18
	cc.Saturation = -0.75 * k
	cc.Contrast = -0.1 * k
	local op = math.min(0.72, k * 0.62 + (if math.random() < k * 0.15 then 0.25 else 0))
	veil.BackgroundTransparency = 1 - op * 0.35
	for i, b in bars do
		local v = math.random(40, 235)
		b.BackgroundColor3 = Color3.fromRGB(v, v, v)
		b.Position = UDim2.fromScale(0, math.random())
		b.Size = UDim2.new(1, 0, 0, math.random(1, 3 + math.floor(k * 9)))
		b.BackgroundTransparency = 1 - op * (0.3 + math.random() * 0.7)
	end
	if math.random() < k * 0.5 then
		tear.Visible = true
		tear.Position = UDim2.fromScale(0, math.random())
		tear.Size = UDim2.new(1, 0, 0, math.random(2, 10))
		tear.BackgroundTransparency = 0.5
	else
		tear.Visible = false
	end
end

-- ------------------------------------------------------------------ sounds (recordings, in your own world: not shared)
local function loop(id: string): Sound
	local s = Instance.new("Sound")
	s.SoundId = id
	s.Looped = true
	s.Volume = 0
	s.Parent = SoundService
	return s
end
local hiss = loop(HISS)
local drone = loop(DRONE)

-- ------------------------------------------------------------------ his pose (the web's pose(g, seed))
type J = { name: string, parent: J?, pre: CFrame, pos: { number }, rot: { number }, k: number, cf: CFrame }
local function local_(j: J): CFrame
	return CFrame.new(j.pos[1] * j.k, j.pos[2] * j.k, j.pos[3] * j.k) * CFrame.fromEulerAnglesXYZ(j.rot[1], j.rot[2], j.rot[3])
end
local rig = Rigs.hr
local function makeJoints(): ({ [string]: J }, { J })
	local Jm: { [string]: J } = {}
	local order: { J } = {}
	for _, j in rig.joints do
		local c = j.cf
		local rest = CFrame.new(c[1], c[2], c[3], c[4], c[5], c[6], c[7])
		local jj: J = { name = j.name, parent = if j.parent then Jm[j.parent] else nil, pre = CFrame.identity,
			pos = { j.pos[1], j.pos[2], j.pos[3] }, rot = { j.rot[1], j.rot[2], j.rot[3] }, k = j.k, cf = CFrame.identity }
		jj.pre = if j.parent then rest * local_(jj):Inverse() else CFrame.identity
		Jm[j.name] = jj
		table.insert(order, jj)
	end
	return Jm, order
end
local function pose(Jm: { [string]: J }, seed: number)
	local s = seed + 1
	local function r(): number s = (s * 16807) % 2147483647; return s / 2147483647 end
	Jm.head.rot = { (r() - 0.5) * 0.3, (r() - 0.5) * 0.6, (if r() < 0.5 then -1 else 1) * (0.15 + r() * 0.45) }
	Jm.body.rot = { 0, 0, (r() - 0.5) * 0.08 }
	Jm.armL.rot = { (r() - 0.5) * 0.2, 0, -0.06 - r() * 0.12 }
	Jm.foreL.rot = { -r() * 0.3, 0, 0 }
	local up = r() < 0.4 -- reading his clipboard. about you
	Jm.armR.rot = { if up then -0.5 else (r() - 0.5) * 0.15, 0, 0.06 + r() * 0.1 }
	Jm.foreR.rot = { if up then -1.2 else -r() * 0.25, 0, 0 }
end

type Hr = { model: Model, root: BasePart?, Jm: { [string]: J }, order: { J }, pieces: { { part: BasePart, j: J, off: CFrame } },
	seed: number, at: CFrame, ear: BasePart? }
local cur: Hr? = nil
local function adopt(m: Model)
	local Jm, order = makeJoints()
	local h: Hr = { model = m, root = nil, Jm = Jm, order = order, pieces = {}, seed = -1, at = CFrame.identity, ear = nil }
	for name, pc in rig.pieces do
		local part = m:WaitForChild(name, 5)
		if part and part:IsA("BasePart") then
			table.insert(h.pieces, { part = part, j = Jm[pc.joint], off = CFrame.new(pc.at[1], pc.at[2], pc.at[3]) })
			if pc.joint == "ear" then h.ear = part end
		end
	end
	local root = m:WaitForChild("Root", 5)
	h.root = if root and root:IsA("BasePart") then root else nil
	cur = h
end
local function lore(): Instance?
	local map = workspace:FindFirstChild("Map")
	return map and map:FindFirstChild("Lore")
end
task.spawn(function()
	local map = workspace:WaitForChild("Map")
	local l = map:WaitForChild("Lore")
	local function look(c: Instance)
		if c:IsA("Model") and c:GetAttribute("Hr") == true then task.spawn(adopt, c) end
	end
	for _, c in l:GetChildren() do look(c) end
	l.ChildAdded:Connect(look)
	l.ChildRemoved:Connect(function(c) if cur and cur.model == c then cur = nil end end)
end)

-- ------------------------------------------------------------------ the take
local takeT = -10
LoreR.OnClientEvent:Connect(function(op: string)
	if op ~= "hrtake" then return end
	takeT = os.clock()
	if okSfx and Sfx and Sfx.play then pcall(Sfx.play, BOOM, nil, 0.8, 0.7) end
end)

-- ------------------------------------------------------------------ every frame
local shown = 0
local lastSend, lastRootPos = 0, Vector3.zero
local shakeOn = false
RunService:BindToRenderStep("HrShake", Enum.RenderPriority.Camera.Value + 2, function()
	local cam = workspace.CurrentCamera
	if not cam or not shakeOn or cam.CameraType ~= Enum.CameraType.Custom then return end
	local k = shown
	local j = k * k * 0.012
	cam.CFrame = cam.CFrame * CFrame.Angles((math.random() - 0.5) * j, (math.random() - 0.5) * j, math.sin(os.clock() * 30) * k * 0.004)
end)
RunService.RenderStepped:Connect(function(dt)
	local now = os.clock()
	local cam = workspace.CurrentCamera
	local h = cur
	local onLot = me:GetAttribute("OnLot") == true
	-- your look, to the server
	if cam and onLot and now - lastSend >= (if h then SEND_EVERY else IDLE_EVERY) then
		lastSend = now
		LookR:FireServer(cam.CFrame.Position, cam.CFrame.LookVector)
	end
	local k, near = 0, 0
	if h and h.root and h.model.Parent then
		-- pose him when he's moved or changed pose
		local seed = h.model:GetAttribute("Pose")
		local at = h.root.CFrame
		if type(seed) == "number" then
			-- (every frame: the server's own move of his parts can land after ours, so the pose is laid on again)
			if (at.Position - lastRootPos).Magnitude > 1.5 and h.seed ~= -1 and okSfx and Sfx and Sfx.play then
				pcall(Sfx.play, "step_hard", at.Position, 0.9, 0.8)
			end
			lastRootPos = at.Position
			if seed ~= h.seed then pose(h.Jm, seed) end
			h.seed = seed
			h.at = at
			for _, j in h.order do
				local l = j.pre * local_(j)
				j.cf = if j.parent then j.parent.cf * l else l
			end
			local parts, cfs = {}, {}
			for _, pc in h.pieces do table.insert(parts, pc.part); table.insert(cfs, at * pc.j.cf * pc.off) end
			if #parts > 0 then workspace:BulkMoveTo(parts, cfs, Enum.BulkMoveMode.FireCFrameChanged) end
		end
		if h.ear then h.ear.Transparency = if math.floor(now / 0.7) % 3 == 0 then 0 else 1 end
		local st = me:GetAttribute("HrStare")
		k = if type(st) == "number" then st else 0
		local ch = me.Character
		local r = ch and ch:FindFirstChild("HumanoidRootPart")
		if r and r:IsA("BasePart") then
			local d = (r.Position - at.Position).Magnitude / 3
			near = if h.model:GetAttribute("Target") == me.UserId then math.max(0, 1 - d / 30) else math.max(0, 1 - d / 14) * 0.6
		end
	end
	shown += (k - shown) * math.min(1, dt * 8)
	local show = shown
	if now - takeT < 1.2 then show = math.max(show, 1 - (now - takeT) / 1.2) end
	shakeOn = show > 0.05
	drawStatic(show)
	-- the hiss with the meter, the drone with nearness (both eased)
	local wantHiss = math.min(1, show * 1.1) * 0.9
	hiss.Volume += (wantHiss - hiss.Volume) * math.min(1, dt * 6)
	drone.Volume += (near * 0.7 - drone.Volume) * math.min(1, dt * 3)
	if hiss.Volume > 0.01 and not hiss.IsPlaying then hiss:Play() elseif hiss.Volume <= 0.01 and hiss.IsPlaying then hiss:Stop() end
	if drone.Volume > 0.01 and not drone.IsPlaying then drone:Play() elseif drone.Volume <= 0.01 and drone.IsPlaying then drone:Stop() end
end)
