-- hold fire: tell the server you're sucking and where you look (20 times a second). the server does the pulling,
-- the teeth and the heat, and puts Heat / Hot / Sucking on the tool for this bar and the effects.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local tool = script.Parent
local remote = ReplicatedStorage:WaitForChild("ShredderRemote")
local lp = Players.LocalPlayer
local Hud
pcall(function() Hud = require(lp:WaitForChild("PlayerScripts"):WaitForChild("Jankfire"):WaitForChild("Hud")) end)

local firing = false
tool.Activated:Connect(function() firing = true end)
tool.Deactivated:Connect(function() firing = false; remote:FireServer("stop") end)

-- the heat bar: comic panel, pink border, hard cyan shadow, yellow fill (red when it's cooked)
local gui = Instance.new("ScreenGui")
gui.Name = "ShredderHeat"
gui.ResetOnSpawn = true
gui.Enabled = false
local shadow = Instance.new("Frame")
shadow.AnchorPoint = Vector2.new(0.5, 1)
shadow.Position = UDim2.new(0.5, 6, 1, -54)
shadow.Size = UDim2.fromOffset(220, 34)
shadow.BackgroundColor3 = Color3.fromRGB(79, 216, 255)
shadow.BorderSizePixel = 0
shadow.Parent = gui
local panel = Instance.new("Frame")
panel.AnchorPoint = Vector2.new(0.5, 1)
panel.Position = UDim2.new(0.5, 0, 1, -60)
panel.Size = UDim2.fromOffset(220, 34)
panel.BackgroundColor3 = Color3.fromRGB(18, 8, 24)
panel.BorderSizePixel = 0
panel.Parent = gui
local stroke = Instance.new("UIStroke")
stroke.Thickness = 4
stroke.Color = Color3.fromRGB(255, 79, 216)
stroke.Parent = panel
local fill = Instance.new("Frame")
fill.Position = UDim2.fromOffset(4, 4)
fill.Size = UDim2.new(0, 0, 1, -8)
fill.BackgroundColor3 = Color3.fromRGB(255, 225, 77)
fill.BorderSizePixel = 0
fill.Parent = panel
local label = Instance.new("TextLabel")
label.BackgroundTransparency = 1
label.Size = UDim2.fromScale(1, 1)
label.FontFace = Font.new("rbxasset://fonts/families/ComicNeueAngular.json", Enum.FontWeight.Bold)
label.TextSize = 20
label.TextColor3 = Color3.new(1, 1, 1)
label.TextStrokeTransparency = 0
label.Text = "SHREDDER HEAT"
label.ZIndex = 2
label.Parent = panel
gui.Parent = lp:WaitForChild("PlayerGui")

tool.Equipped:Connect(function() gui.Enabled = true end)
tool.Unequipped:Connect(function()
	gui.Enabled = false
	if firing then firing = false; remote:FireServer("stop") end
end)
tool.AncestryChanged:Connect(function() if not tool:IsDescendantOf(game) then gui:Destroy() end end)

local lamps = {}
for _, d in ipairs(tool:GetDescendants()) do if d:IsA("BasePart") and d.Name:match("^sh_lamp") then table.insert(lamps, d) end end

local acc, wasHot = 0, false
RunService.Heartbeat:Connect(function(dt)
	if not tool.Parent then return end
	local mine = tool.Parent == lp.Character
	if firing and mine then
		acc += dt
		if acc >= 0.05 then acc = 0; remote:FireServer("aim", workspace.CurrentCamera.CFrame.LookVector) end
	end
	local heat = tool:GetAttribute("Heat") or 0
	local hot = tool:GetAttribute("Hot") == true
	fill.Size = UDim2.new(math.clamp(heat, 0, 1) * (212 / 220), 0, 1, -8)
	fill.BackgroundColor3 = if hot then Color3.fromRGB(255, 48, 48) elseif heat > 0.75 then Color3.fromRGB(255, 140, 26) else Color3.fromRGB(255, 225, 77)
	label.Text = if hot then "OVERHEATED" else "SHREDDER HEAT"
	-- the power lamps blink while it cools
	local lampOn = not hot or (os.clock() * 6) % 2 < 1
	for _, l in ipairs(lamps) do l.Color = if lampOn then Color3.fromRGB(255, 40, 30) else Color3.fromRGB(60, 8, 8) end
	if hot and not wasHot and mine and Hud then Hud.callout("OVERHEATED", 0.8) end
	wasHot = hot
end)

-- while it's running, the gun swivels in your hands to face whoever it's got (up to 35°), and swings back when
-- there's nobody. the suction itself is aimed where you look (the server's cone); this is so you see who it's eating.
-- it bends the grip weld on your screen only.
local Players_ = Players
local h = tool:WaitForChild("Handle")
local hub = tool:FindFirstChild("sh_hub", true)
local G0 = tool.Grip
local axisH = h.CFrame:VectorToObjectSpace((h:WaitForChild("Muzzle").WorldPosition - hub.Position).Unit) -- muzzle dir, handle space
local mA = G0:VectorToObjectSpace(axisH) -- muzzle dir in the hand's grip space with no swivel
local MAXANG = math.rad(35)
local RANGE, COS_CONE = 42 + 6, math.cos(0.76)
local swivel = CFrame.identity
local sendAcc, lastSent = 0, CFrame.identity
local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Exclude

local function nearestTarget()
	local ch = lp.Character
	local head = ch and ch:FindFirstChild("Head")
	if not head then return nil end
	local cam = workspace.CurrentCamera
	local look = cam.CFrame.LookVector
	local bodies, list = {}, {}
	for _, p in ipairs(Players_:GetPlayers()) do
		if p.Character then table.insert(bodies, p.Character); if p ~= lp then table.insert(list, p.Character) end end
	end
	local dummies = workspace:FindFirstChild("Dummies")
	if dummies then table.insert(bodies, dummies); for _, m in ipairs(dummies:GetChildren()) do table.insert(list, m) end end
	ray.FilterDescendantsInstances = bodies
	local best, bestD = nil, math.huge
	for _, m in ipairs(list) do
		local hum = m:FindFirstChildOfClass("Humanoid")
		local root = m:FindFirstChild("HumanoidRootPart")
		if hum and root and hum.Health > 0 then
			local to = root.Position - head.Position
			local d = to.Magnitude
			if d < RANGE and d < bestD and (d < 9 or to.Unit:Dot(look) > COS_CONE) and not workspace:Raycast(head.Position, to, ray) then
				best, bestD = root.Position, d
			end
		end
	end
	return best
end

RunService.RenderStepped:Connect(function(dt)
	local ch = lp.Character
	local hand = ch and ch:FindFirstChild("RightHand")
	local grip = hand and hand:FindFirstChild("RightGrip")
	local att = hand and hand:FindFirstChild("RightGripAttachment")
	if tool.Parent ~= ch or not grip or not att then swivel = CFrame.identity return end
	local want = CFrame.identity
	local cam = workspace.CurrentCamera
	local target = if firing and not tool:GetAttribute("Hot") then nearestTarget() else nil
	-- nobody to eat: point at your crosshair (Roblox arms don't follow your view up and down on their own)
	target = target or cam.CFrame.Position + cam.CFrame.LookVector * 30
	do
		do
			local A = att.WorldCFrame
			local dA = A:VectorToObjectSpace((target - A.Position).Unit)
			local axis = mA:Cross(dA)
			local ang = math.acos(math.clamp(mA:Dot(dA), -1, 1))
			if axis.Magnitude > 1e-4 then want = CFrame.fromAxisAngle(axis.Unit, math.min(ang, MAXANG)) end
		end
	end
	swivel = swivel:Lerp(want, 1 - math.exp(-14 * dt))
	grip.C1 = G0 * swivel:Inverse()
	-- everyone else sees it too (the server checks it and puts it on the tool)
	sendAcc += dt
	if sendAcc >= 0.1 then
		sendAcc = 0
		local _, moved = (lastSent:Inverse() * swivel):ToAxisAngle()
		if math.abs(moved) > math.rad(1) then lastSent = swivel; remote:FireServer("sw", swivel - swivel.Position) end
	end
end)

-- first person: on your screen the gun is a copy locked to the camera (a viewmodel), so jump, fall, crouch and slide
-- animations can't knock it around. it aims at the crosshair and swivels toward whoever it's eating, like the real
-- one. the real gun stays in your hand for everyone else, and for you in third person (V).
local VM_POS = Vector3.new(1.5, -0.95, -1.5) -- where the grip sits, camera space
local AIM = Vector3.new(0, 0, -30) -- the crosshair point, camera space
local chuteP = tool:FindFirstChild("sh_bell2", true)
local axisW = (h.Muzzle.WorldPosition - hub.Position).Unit
local upW = chuteP.Position - hub.Position
upW = (upW - axisW * axisW:Dot(upW)).Unit
local gunFrameH = CFrame.lookAt(Vector3.zero, axisH, h.CFrame:VectorToObjectSpace(upW)) -- handle space: -Z muzzle, +Y up
local realParts = {}
for _, d in ipairs(tool:GetDescendants()) do if d:IsA("BasePart") then table.insert(realParts, d) end end
local realFx = tool:FindFirstChild("Suction", true)
local realRate = realFx and realFx.Rate or 0

local AvatarArms = require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("AvatarArms"))
local vm, vmFx = nil, nil
local function buildVM()
	local m = Instance.new("Model")
	m.Name = "ShredderViewmodel"
	for _, d in ipairs(tool:GetChildren()) do
		if not d:IsA("LuaSourceContainer") then d:Clone().Parent = m end
	end
	for _, d in ipairs(m:GetDescendants()) do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
			d.LocalTransparencyModifier = 0
			if d.Name:match("^sh_lamp") then table.insert(lamps, d) end -- (blinks with the real ones while it cools)
		elseif d:IsA("WeldConstraint") then
			d:Destroy()
		end
	end
	m.PrimaryPart = m:FindFirstChild("Handle")
	-- your own avatar's hands on it, like the other weapons: the right round the grip, the left under the body
	local hd = m.PrimaryPart
	if hd then
		local G = gunFrameH.Rotation
		local LEFT = G * CFrame.new(-0.25, 0.22, -0.8)
		local spots = {
			{ side = "Right", kind = "gun", fist = G, arm = G * CFrame.Angles(0.5, 0.25, 0) },
			{ side = "Left", kind = "gun", fist = LEFT, arm = LEFT * CFrame.Angles(0.5, -0.35, 0) },
		}
		if not AvatarArms.build(m, hd, spots, 3) then
			task.spawn(function() -- (your body may not be built yet: a spawn)
				for _ = 1, 24 do
					task.wait(0.25)
					if vm ~= m then return end
					if AvatarArms.build(m, hd, spots, 3) then return end
				end
			end)
		end
	end
	vmFx = m:FindFirstChild("Suction", true)
	if vmFx then vmFx.Enabled = false; vmFx.Rate = realRate end
	return m
end

local function slerpDir(a, b, maxAng)
	local ang = math.acos(math.clamp(a:Dot(b), -1, 1))
	if ang <= maxAng or ang < 1e-4 then return b end
	local axis = a:Cross(b)
	if axis.Magnitude < 1e-4 then return a end
	return CFrame.fromAxisAngle(axis.Unit, maxAng):VectorToWorldSpace(a)
end

local vmDir = (AIM - VM_POS).Unit
local function showReal(on)
	for _, p in ipairs(realParts) do p.LocalTransparencyModifier = if on then 0 else 1 end
	if realFx then realFx.Rate = if on then realRate else 0 end
end

local bindName = "ShredderVM_" .. tostring(math.random(1, 1e9))
RunService:BindToRenderStep(bindName, Enum.RenderPriority.Camera.Value + 2, function(dt)
	local ch = lp.Character
	local head = ch and ch:FindFirstChild("Head")
	local cam = workspace.CurrentCamera
	local equipped = tool.Parent == ch and head ~= nil
	local firstPerson = equipped and (cam.CFrame.Position - head.Position).Magnitude < 3.5
	if not firstPerson then
		if vm then vm.Parent = nil end
		showReal(true)
		return
	end
	vm = vm or buildVM()
	vm.Parent = cam
	showReal(false)
	-- aim: the crosshair, or toward whoever it's eating (up to 35°)
	local want = (AIM - VM_POS).Unit
	if firing and not tool:GetAttribute("Hot") then
		local target = nearestTarget()
		if target then want = slerpDir(want, (cam.CFrame:PointToObjectSpace(target) - VM_POS).Unit, MAXANG) end
	end
	vmDir = vmDir:Lerp(want, 1 - math.exp(-14 * dt)).Unit
	local sucking = tool:GetAttribute("Sucking") == true
	if vmFx then vmFx.Enabled = sucking end
	local shake = if sucking then Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 0.05 else Vector3.zero
	local F = CFrame.lookAt(VM_POS + shake, VM_POS + shake + vmDir, Vector3.yAxis)
	vm:PivotTo(cam.CFrame * F * gunFrameH:Inverse())
end)
tool.AncestryChanged:Connect(function()
	if not tool:IsDescendantOf(game) then
		RunService:UnbindFromRenderStep(bindName)
		if vm then vm:Destroy() end
	end
end)
