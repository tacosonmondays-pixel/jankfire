--!strict
-- the hub's little bits of life, on your screen only (the server's copies stay still): models tagged "HubSpin" turn
-- (attribute Spin, rad/s; Bob = studs up and down), the JANK NEWS 24 ticker ("HubTicker") scrolls, the boot camp
-- tips screen ("HubTip") changes every 7 s. only while you're near the hub.
-- it also swaps the lighting: the hub's warm look (the Lanes), the training hall's, the playground's, the saved look in a match
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local HubLook = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HubLook")) :: any
-- which arena a match is in (the Rooftop v1 keeps the saved light; v2 and v3 have their own looks, HubLook.looks.rooftop_v2 / _v3)
local Arena = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Arena")) :: any
local me = Players.LocalPlayer
local looking = "?"
-- a part in Hub.LookZones with the attribute Look names another look for whoever stands inside it (the show hubs of the
-- hub comparison had one each; the folder is empty now that one of them is the hub). the server still calls the place "hub"
local function zoneLook(): string?
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local map = workspace:FindFirstChild("Map")
	local zones = map and map:FindFirstChild("Hub") and map.Hub:FindFirstChild("LookZones")
	if not root or not zones then return nil end
	for _, z in zones:GetChildren() do
		if z:IsA("BasePart") then
			local rel = z.CFrame:PointToObjectSpace(root.Position)
			if math.abs(rel.X) <= z.Size.X / 2 and math.abs(rel.Y) <= z.Size.Y / 2 and math.abs(rel.Z) <= z.Size.Z / 2 then
				local l = z:GetAttribute("Look")
				return if type(l) == "string" and HubLook.looks[l] then l else nil
			end
		end
	end
	return nil
end
local function relook(snap: boolean)
	local zone = me:GetAttribute("Zone")
	local want = if zone == "match" then (if Arena.name() == "RooftopV2" and HubLook.looks.rooftop_v2 then "rooftop_v2" elseif Arena.name() == "RooftopV3" and HubLook.looks.rooftop_v3 then "rooftop_v3" else "match") elseif zone == "training" then (if me:GetAttribute("OnLot") and HubLook.looks.lot then "lot" else "training") elseif zone == "playground" then "playground" else "hub" -- no zone yet = just joined = the hub
	if want == "hub" then want = zoneLook() or "hub" end
	if want == looking then return end
	looking = want
	HubLook.set(if want == "match" then nil else want, if snap then 0 else 0.6)
end
relook(true)
me:GetAttributeChangedSignal("Zone"):Connect(function() relook(false) end)
me:GetAttributeChangedSignal("OnLot"):Connect(function() relook(false) end) -- (the training area's back lot has its own light)
task.spawn(function() -- (walking or hopping between hubs doesn't change the zone, so look again now and then)
	while true do task.wait(0.4); relook(false) end
end)

local TIPS = {
	"the jump pads go up. the balcony goes nowhere. enjoy.",
	"step on a pad's colour to queue. stepping off un-queues you. that's the whole skill.",
	"the red grid behind the spawn is a door. walking into lasers is encouraged here only.",
	"the dummies in training shoot back. they're bad at it. so are you. it's fair.",
	"the 5v5 pad is coming soon. we checked. it isn't.",
	"the duck upstairs is a hologram. please stop tipping it.",
	"first to 5 rounds wins. no draws. the coin decides if nobody does.",
	"marbles on the floor are a choice. your choice. a bad one.",
}

type Spinner = { m: Model, base: CFrame, t: number }
local spinners: { [Model]: Spinner } = {}
local function addSpin(inst: Instance)
	if inst:IsA("Model") and not spinners[inst] then spinners[inst] = { m = inst, base = inst:GetPivot(), t = math.random() * 10 } end
end
CollectionService:GetInstanceAddedSignal("HubSpin"):Connect(addSpin)
CollectionService:GetInstanceRemovedSignal("HubSpin"):Connect(function(inst) spinners[inst :: Model] = nil end)
for _, m in CollectionService:GetTagged("HubSpin") do addSpin(m) end

local camera = workspace.CurrentCamera
local tipT, tipI = 0, 1
RunService.RenderStepped:Connect(function(dt: number)
	local cam = camera.CFrame.Position
	for m, s in spinners do
		if not m.Parent then spinners[m] = nil; continue end
		if (s.base.Position - cam).Magnitude > 260 then continue end
		s.t += dt
		local spin = m:GetAttribute("Spin")
		local bob = m:GetAttribute("Bob")
		local a = (if type(spin) == "number" then spin else 0.5) * s.t
		local y = if type(bob) == "number" then math.sin(s.t * 2) * bob else 0
		m:PivotTo(s.base * CFrame.new(0, y, 0) * CFrame.Angles(0, a, 0))
	end
	for _, t in CollectionService:GetTagged("HubTicker") do
		if t:IsA("TextLabel") then
			local x = t.Position.X.Scale - dt * 0.06
			if x < -2 then x = 1 end
			t.Position = UDim2.new(x, 0, t.Position.Y.Scale, 0)
		end
	end
	tipT += dt
	if tipT > 7 then
		tipT = 0
		tipI = tipI % #TIPS + 1
		for _, t in CollectionService:GetTagged("HubTip") do if t:IsA("TextLabel") then t.Text = TIPS[tipI] end end
	end
end)
