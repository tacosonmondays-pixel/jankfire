-- your side of someone else's Shredder: the server says how hard you're pulled ("pull"), where you hang in the
-- teeth ("grab"), and where your body comes out ("spit"). movement is the client's, so the client applies it.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local lp = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("ShredderRemote")
local Hud
pcall(function() Hud = require(script.Parent:WaitForChild("Jankfire"):WaitForChild("Hud")) end)
local Body -- (Body.throw: tells Move the pull is meant, so its fling guard and its LinearVelocity go along)
pcall(function() Body = require(script.Parent:WaitForChild("Jankfire"):WaitForChild("Body")) end)
local function throw(root, v) if Body and Body.throw then Body.throw(v) else root.AssemblyLinearVelocity = v end end

local holdAt, holdUntil = nil, 0
local function ok(v) return typeof(v) == "Vector3" and v.X == v.X and v.Y == v.Y and v.Z == v.Z and v.Magnitude < 1e5 end

remote.OnClientEvent:Connect(function(kind, a, b)
	local ch = lp.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart")
	if kind == "fx" then
		if Hud and typeof(a) == "string" then Hud.callout(a, 0.8) end
		return
	end
	if not root then return end
	if kind == "pull" and ok(a) and a.Magnitude < 300 then
		throw(root, root.AssemblyLinearVelocity + a)
	elseif kind == "grab" and ok(a) then
		holdAt, holdUntil = a, os.clock() + 0.26
		if Hud then Hud.callout("IN THE TEETH", 0.3) end
	elseif kind == "spit" and ok(a) and ok(b) then
		holdAt = nil
		for _, d in ipairs(ch:GetDescendants()) do
			if d:IsA("BasePart") then
				d.CFrame = CFrame.new(a) * (d.CFrame - d.CFrame.Position)
				d.AssemblyLinearVelocity = b + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 36
				d.AssemblyAngularVelocity = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 30
			end
		end
		if Hud then Hud.callout("SHREDDED", 1.2) end
	end
end)

RunService.Heartbeat:Connect(function()
	if not holdAt or os.clock() > holdUntil then holdAt = nil return end
	local ch = lp.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart")
	if not root then return end
	local v = (holdAt - root.Position) * 9
	if v.Magnitude > 90 then v = v.Unit * 90 end
	throw(root, v)
end)

-- other people's Shredders: the gun swivels toward whoever it's eating (its owner sends it, the server checks it and
-- puts it on the tool as "Swivel"); here it's eased in and bent into their grip weld, on this screen
local smooth = {} -- [tool] = the swivel shown now
local function holders()
	local list = {}
	for _, p in ipairs(Players:GetPlayers()) do if p ~= lp and p.Character then table.insert(list, p.Character) end end
	local dummies = workspace:FindFirstChild("Dummies")
	if dummies then for _, m in ipairs(dummies:GetChildren()) do table.insert(list, m) end end
	return list
end
RunService.RenderStepped:Connect(function(dt)
	local a = 1 - math.exp(-14 * dt)
	for _, ch in ipairs(holders()) do
		local tool = ch:FindFirstChild("Shredder")
		local hand = ch:FindFirstChild("RightHand")
		local grip = hand and hand:FindFirstChild("RightGrip")
		if tool and tool:IsA("Tool") and grip then
			local want = tool:GetAttribute("Swivel")
			if typeof(want) ~= "CFrame" then want = CFrame.identity end
			local cur = (smooth[tool] or CFrame.identity):Lerp(want, a)
			smooth[tool] = cur
			grip.C1 = tool.Grip * cur:Inverse()
		end
	end
	for tool in pairs(smooth) do if not tool.Parent then smooth[tool] = nil end end
end)
