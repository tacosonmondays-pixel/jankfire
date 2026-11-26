--!strict
-- HOLDOUT's things you can use (26 Nov 2026; roblox/docs/HUNT.md section 2). The owner: "people will spawn inside and
-- wait for a new game to start! They can run around interact with stuff". Wires any model that carries a Hunt folder
-- built by studio-tools/HuntBuild (THE HOUSE now; the round maps later): doors that swing open as you walk into them and
-- shut behind you, the garage's roll-up door and its buttons, a light switch by every room, TVs, taps, the fridge,
-- toilets, the driveway's basketball, and the patio's store tables (prompts with ShopOpen: ShopClient opens the shop).
-- Prompts use F, like every other prompt in the game (E is the grapple's, and the push's in this mode).
--   HuntProps.wire(model)    once per model (again after a rebuild)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local P = HC.PROPS

local HuntProps = {}

-- a sound from the game's library (ReplicatedStorage.JankfireSounds, recordings only), played at a part
local Sounds = ReplicatedStorage:FindFirstChild("JankfireSounds")
local function sfx(name: string, at: BasePart, vol: number?)
	local s = Sounds and Sounds:FindFirstChild(name)
	if not (s and s:IsA("Sound")) then return end
	local c = s:Clone()
	c.RollOffMode = Enum.RollOffMode.InverseTapered; c.RollOffMinDistance = 8; c.RollOffMaxDistance = 70
	if vol then c.Volume = vol end
	c.Parent = at
	c:Play()
	task.delay(math.max(2, c.TimeLength + 0.5), function() c:Destroy() end)
end

local function prompt(at: BasePart, action: string, dist: number?): ProximityPrompt
	local p = Instance.new("ProximityPrompt")
	p.ActionText = action; p.ObjectText = ""
	p.KeyboardKeyCode = Enum.KeyCode.F; p.GamepadKeyCode = Enum.KeyCode.ButtonX
	p.HoldDuration = 0; p.MaxActivationDistance = dist or 8; p.RequiresLineOfSight = false
	p.Style = Enum.ProximityPromptStyle.Default
	p.Parent = at
	return p
end

local function roots(): { BasePart }
	local out = {}
	for _, pl in Players:GetPlayers() do
		local ch = pl.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local r = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if r and hum and hum.Health > 0 then table.insert(out, r) end
	end
	return out
end

-- ------------------------------------------------------------------ doors
type Door = { m: Model, hinge: BasePart, closed: CFrame, w: number, slide: number?, open: boolean, lastNear: number, tw: Tween? }
local function swingTo(d: Door, cf: CFrame, t: number)
	if d.tw then d.tw:Cancel() end
	local tw = TweenService:Create(d.hinge, TweenInfo.new(t, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = cf })
	d.tw = tw
	tw:Play()
end
local function doorCentre(d: Door): Vector3
	return (d.closed * CFrame.new(d.w / 2, 4.5, 0)).Position
end
local function openDoor(d: Door, from: Vector3)
	if d.open then return end
	d.open = true
	local cf: CFrame
	if d.slide then
		cf = d.closed * CFrame.new(d.slide, 0, 0)
	else
		-- swing away from whoever walked into it: the leaf's front (+Z) side is n
		local n = d.closed:VectorToWorldSpace(Vector3.zAxis)
		local side = (from - doorCentre(d)):Dot(n)
		cf = d.closed * CFrame.Angles(0, if side > 0 then math.pi / 2 else -math.pi / 2, 0)
	end
	swingTo(d, cf, P.doorOpen)
	sfx("hunt_door_open", d.hinge, 0.5)
end
local function shutDoor(d: Door)
	if not d.open then return end
	d.open = false
	swingTo(d, d.closed, P.doorOpen * 1.3)
	sfx("hunt_door_shut", d.hinge, 0.45)
end

-- ------------------------------------------------------------------ the rest
local function rollup(gf: Instance)
	local m = gf:FindFirstChild("Rollup") :: Model?
	local root = m and m.PrimaryPart
	if not (m and root) then return end
	local closed, open = m:GetAttribute("Closed"), m:GetAttribute("Open")
	if typeof(closed) ~= "CFrame" or typeof(open) ~= "CFrame" then return end
	root.CFrame = closed
	local up, busy = false, false
	local function toggle()
		if busy then return end
		busy = true
		up = not up
		local tw = TweenService:Create(root, TweenInfo.new(P.rollup, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { CFrame = if up then open else closed })
		tw:Play()
		sfx("zm_door", root, 0.7)
		tw.Completed:Wait()
		busy = false
	end
	local bf = gf:FindFirstChild("Buttons")
	for _, b in (if bf then bf:GetChildren() else {}) do
		if b:IsA("BasePart") then prompt(b, "GARAGE DOOR", 7).Triggered:Connect(toggle) end
	end
end

local function switches(root: Instance, sf: Instance)
	local lights = root:FindFirstChild("Lights")
	local on: { [string]: boolean } = {}
	for _, s in sf:GetChildren() do
		if not s:IsA("BasePart") then continue end
		local room = s:GetAttribute("Room")
		if type(room) ~= "string" then continue end
		on[room] = true
		prompt(s, "LIGHTS", 7).Triggered:Connect(function()
			on[room] = not on[room]
			for _, lm in (if lights then lights:GetChildren() else {}) do
				if lm:GetAttribute("Room") == room then
					for _, l in lm:GetChildren() do if l:IsA("Light") then l.Enabled = on[room] end end
				end
			end
			sfx("hunt_switch", s, 0.6)
		end)
	end
end

local SCREEN_ON = Color3.fromRGB(118, 146, 168)
local SCREEN_OFF = Color3.fromRGB(35, 38, 43)
local function props(pf: Instance, zone: BasePart?)
	for _, p in pf:GetChildren() do
		local kind = p:GetAttribute("Kind")
		if kind == "tv" and p:IsA("BasePart") then
			local tv = p
			local glow = Instance.new("SurfaceLight"); glow.Face = Enum.NormalId.Back; glow.Range = 12; glow.Brightness = 0.7
			glow.Angle = 100; glow.Color = SCREEN_ON; glow.Enabled = false; glow.Parent = tv
			local on = false
			prompt(tv, "TV", 12).Triggered:Connect(function()
				on = not on
				tv.Color = if on then SCREEN_ON else SCREEN_OFF
				tv.Material = if on then Enum.Material.SmoothPlastic else Enum.Material.SmoothPlastic
				glow.Enabled = on
				sfx("hunt_switch", tv, 0.5)
			end)
		elseif kind == "tap" and p:IsA("BasePart") then
			local tap = p
			local at = Instance.new("Attachment"); at.Name = "Spout"; at.Parent = tap
			local e = Instance.new("ParticleEmitter")
			e.Name = "Water"; e.Enabled = false; e.Rate = 70; e.Lifetime = NumberRange.new(0.25, 0.35)
			e.Speed = NumberRange.new(2, 3); e.SpreadAngle = Vector2.new(4, 4); e.Acceleration = Vector3.new(0, -70, 0)
			e.EmissionDirection = Enum.NormalId.Bottom; e.Size = NumberSequence.new(0.18, 0.08)
			e.Color = ColorSequence.new(Color3.fromRGB(196, 222, 236)); e.Transparency = NumberSequence.new(0.25, 0.6)
			e.LightEmission = 0.1; e.Parent = at
			local running = false
			prompt(tap, "TAP", 6).Triggered:Connect(function()
				if running then return end
				running = true
				e.Enabled = true
				sfx("hunt_tap", tap, 0.5)
				task.delay(P.tap, function() e.Enabled = false; running = false end)
			end)
		elseif kind == "toilet" and p:IsA("BasePart") then
			local t = p
			local busy = false
			prompt(t, "FLUSH", 6).Triggered:Connect(function()
				if busy then return end
				busy = true
				sfx("hunt_flush", t, 0.6)
				task.delay(3, function() busy = false end)
			end)
		elseif kind == "fridge" and p:IsA("Model") then
			local m = p :: Model
			local hinge = m.PrimaryPart
			local leaf = m:FindFirstChild("Leaf") :: BasePart?
			if not (hinge and leaf) then continue end
			local closed = hinge.CFrame
			local inside = hinge:FindFirstChild("Inside") :: PointLight?
			local open = false
			prompt(leaf, "FRIDGE", 7).Triggered:Connect(function()
				if open then return end
				open = true
				TweenService:Create(hinge, TweenInfo.new(0.35, Enum.EasingStyle.Quad), { CFrame = closed * CFrame.Angles(0, -math.rad(100), 0) }):Play()
				if inside then inside.Enabled = true end
				sfx("hunt_fridge", leaf, 0.5)
				task.delay(P.fridge, function()
					TweenService:Create(hinge, TweenInfo.new(0.45, Enum.EasingStyle.Quad), { CFrame = closed }):Play()
					task.delay(0.45, function() if inside then inside.Enabled = false end; open = false end)
				end)
			end)
		elseif kind == "ball" and p:IsA("BasePart") then
			local ball = p
			local home = ball:GetAttribute("Home")
			ball.Anchored = false
			pcall(function() ball:SetNetworkOwner(nil) end)
			-- home again when it has been out of the lot (or fallen through) for a while
			local outSince: number? = nil
			task.spawn(function()
				while ball.Parent do
					task.wait(1)
					local inLot = true
					if zone then
						local rel = zone.CFrame:PointToObjectSpace(ball.Position)
						inLot = math.abs(rel.X) <= zone.Size.X / 2 and math.abs(rel.Z) <= zone.Size.Z / 2 and rel.Y > -zone.Size.Y / 2
					end
					if inLot then outSince = nil
					elseif not outSince then outSince = os.clock()
					elseif os.clock() - outSince > P.ballHome and typeof(home) == "Vector3" then
						ball.AssemblyLinearVelocity = Vector3.zero; ball.AssemblyAngularVelocity = Vector3.zero
						ball.CFrame = CFrame.new(home); outSince = nil
					end
				end
			end)
		end
	end
end

local function tables(tf: Instance)
	for _, t in tf:GetChildren() do
		if not t:IsA("BasePart") then continue end
		local tab = HC.TABLES[t:GetAttribute("Tab")]
		if not tab then continue end
		local pr = prompt(t, tab.label, 9)
		pr:SetAttribute("ShopOpen", tab.open) -- (ShopClient opens the shop on that tab, on the client that pressed it)
	end
end

local wired: { [Instance]: boolean } = {}
local doorList: { Door } = {}
function HuntProps.wire(model: Instance): string
	local hf = model:FindFirstChild("Hunt")
	if not hf or wired[hf] then return "nothing to wire" end
	wired[hf] = true
	local zone = hf:FindFirstChild("Zone") :: BasePart?
	local df = hf:FindFirstChild("Doors")
	local nd = 0
	for _, m in (if df then df:GetChildren() else {}) do
		if not m:IsA("Model") or not m.PrimaryPart then continue end
		local slide = m:GetAttribute("Slide")
		table.insert(doorList, { m = m, hinge = m.PrimaryPart, closed = m.PrimaryPart.CFrame, w = tonumber(m:GetAttribute("Width")) or 6,
			slide = if type(slide) == "number" then slide else nil, open = false, lastNear = -math.huge })
		nd += 1
	end
	local gf = hf:FindFirstChild("Garage")
	if gf then rollup(gf) end
	local sf = hf:FindFirstChild("Switches")
	if sf then switches(model, sf) end
	local pf = hf:FindFirstChild("Props")
	if pf then props(pf, zone) end
	local tf = hf:FindFirstChild("Tables")
	if tf then tables(tf) end
	return ("wired %s: %d doors"):format(model.Name, nd)
end

-- the doors' heartbeat: anyone alive within reach of a door's middle opens it (away from them); it shuts doorShut s
-- after the last body left. (dummies and the round's bots count too once they're Characters in workspace)
local acc = 0
RunService.Heartbeat:Connect(function(dt)
	acc += dt
	if acc < 0.12 then return end
	acc = 0
	if #doorList == 0 then return end
	local rs = roots()
	local now = os.clock()
	for _, d in doorList do
		if not d.m.Parent then continue end
		local c = doorCentre(d)
		local nearest: Vector3? = nil
		local nd = HC.PROPS.doorReach
		for _, r in rs do
			local dd = (r.Position - c).Magnitude
			if dd < nd then nearest, nd = r.Position, dd end
		end
		if nearest then
			d.lastNear = now
			if not d.open then openDoor(d, nearest) end
		elseif d.open and now - d.lastNear > P.doorShut then
			shutDoor(d)
		end
	end
end)

return HuntProps
