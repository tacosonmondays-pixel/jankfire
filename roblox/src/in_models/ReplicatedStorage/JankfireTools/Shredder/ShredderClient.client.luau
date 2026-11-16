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

-- the heat bar: a small dark plate low in the middle of the screen, a thin bar that goes white > amber > red when
-- it's cooked (the look is the HUD's: PlayerScripts.Jankfire.Theme)
local T = require(lp:WaitForChild("PlayerScripts"):WaitForChild("Jankfire"):WaitForChild("Theme"))
local gui = Instance.new("ScreenGui")
gui.Name = "ShredderHeat"
gui.ResetOnSpawn = true
gui.Enabled = false
local panel = T.plate(T.scaled(gui), "Heat", UDim2.new(0.5, -120, 1, -150), UDim2.fromOffset(240, 40))
local label = T.text(panel, "Label", "SHREDDER HEAT", 11, T.MUTED, T.FONT_BOLD)
label.Position = UDim2.fromOffset(14, 7)
label.Size = UDim2.new(1, -28, 0, 14)
local track = T.new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.new(0, 14, 1, -14), Size = UDim2.new(1, -28, 0, 5) }, panel)
T.corner(track, 3)
local fill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, Size = UDim2.fromScale(0, 1) }, track)
T.corner(fill, 3)
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
	fill.Size = UDim2.fromScale(math.clamp(heat, 0, 1), 1)
	fill.BackgroundColor3 = if hot then T.DANGER elseif heat > 0.75 then T.ACCENT else T.TEXT
	label.Text = if hot then "OVERHEATED" else "SHREDDER HEAT"
	label.TextColor3 = if hot then T.DANGER else T.MUTED
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
-- (a fresh copy in your backpack can arrive a piece at a time: wait for the pieces read below, or the script stopped
-- here on a nil hub and the gun showed full size in first person, seen 16 Nov 2026)
local function piece(name: string): BasePart
	local p = tool:FindFirstChild(name, true)
	local t0 = os.clock()
	while not p and os.clock() - t0 < 15 do tool.DescendantAdded:Wait(); p = tool:FindFirstChild(name, true) end
	return p :: BasePart
end
local hub = piece("sh_hub")
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
local VM_POS = Vector3.new(1.3, -0.95, -1.6) -- where the grip sits, camera space (if Holds has no shredderVM)
local AIM = Vector3.new(0, 0, -30) -- the crosshair point, camera space
-- (the grip spot and aim point per look, from holds.json's shredder.vm_looks: before / after / combined, like the other
-- weapons; the player's HoldLook attribute shows another in a test)
local HoldsOk, Holds = pcall(function() return require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Holds")) end)
local function vmLook(): (Vector3, Vector3)
	local SV = HoldsOk and Holds and (Holds :: any).shredderVM
	if not SV then return VM_POS, AIM end
	local want = lp:GetAttribute("HoldLook")
	local l = (type(want) == "string" and SV.looks[want]) or SV.looks[SV.use]
	if not l then return VM_POS, AIM end
	return l.pos, l.aim
end
local chuteP = piece("sh_bell2")
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
	-- your own avatar's hands on it, like the other weapons: the right on the grip, the left under the body behind
	-- the cone (the hold table's "shredder" row, in the gun's own frame G)
	local hd = m.PrimaryPart
	if hd then
		local G = gunFrameH.Rotation
		if not AvatarArms.hold(m, hd, "shredder", 3, G) then
			task.spawn(function() -- (your body may not be built yet: a spawn)
				for _ = 1, 24 do
					task.wait(0.25)
					if vm ~= m then return end
					if AvatarArms.hold(m, hd, "shredder", 3, G) then return end
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
	-- (the tool is gone: a binding outlives its script, so the copy would stay in your camera; seen 16 Nov 2026)
	if not tool:IsDescendantOf(game) then
		RunService:UnbindFromRenderStep(bindName)
		if vm then vm:Destroy(); vm = nil end
		return
	end
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
	local VP, AP = vmLook()
	local want = (AP - VP).Unit
	if firing and not tool:GetAttribute("Hot") then
		local target = nearestTarget()
		if target then want = slerpDir(want, (cam.CFrame:PointToObjectSpace(target) - VP).Unit, MAXANG) end
	end
	vmDir = vmDir:Lerp(want, 1 - math.exp(-14 * dt)).Unit
	local sucking = tool:GetAttribute("Sucking") == true
	if vmFx then vmFx.Enabled = sucking end
	local shake = if sucking then Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 0.05 else Vector3.zero
	local F = CFrame.lookAt(VP + shake, VP + shake + vmDir, Vector3.yAxis)
	vm:PivotTo(cam.CFrame * F * gunFrameH:Inverse())
	AvatarArms.aim(vm, cam.CFrame) -- (your arms: each from its hold toward your elbow)
end)
tool.AncestryChanged:Connect(function()
	if not tool:IsDescendantOf(game) then
		RunService:UnbindFromRenderStep(bindName)
		if vm then vm:Destroy() end
	end
end)
