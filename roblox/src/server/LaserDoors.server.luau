--!strict
-- the hub's laser doors. walk into the red grid behind the spawn and you're in the training ground (a big hall well
-- away from the hub: Hub.TrainingGround, its zone Hub.TrainingZone, spawns Hub.TrainSpawns, dummies Hub.DummySpots);
-- its own grid takes you back to the hub (Hub.Doors.HubArrive). the move is the server's: it stamps the player's
-- TeleportT attribute first so Main's teleport check starts afresh instead of putting them back, then moves the body.
-- 1.5 s between hops per player so nobody bounces; not while in a match
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CalloutR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Callout") :: RemoteEvent
local hub = workspace:WaitForChild("Map"):WaitForChild("Hub")
local doors = hub:WaitForChild("Doors")

local last: { [Player]: number } = {}

local function inside(part: BasePart, pos: Vector3): boolean
	local rel = part.CFrame:PointToObjectSpace(pos)
	local h = part.Size / 2
	return math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z
end

local function pick(folder: Instance?): BasePart?
	if not folder then return nil end
	local list = {}
	for _, c in folder:GetChildren() do if c:IsA("BasePart") then table.insert(list, c) end end
	return if #list > 0 then list[math.random(#list)] else nil
end

local function hop(p: Player, ch: Model, root: BasePart, to: BasePart, text: string)
	last[p] = os.clock()
	p:SetAttribute("TeleportT", os.clock()) -- (Main: reset the teleport check)
	root.AssemblyLinearVelocity = Vector3.zero
	local at = to.Position + Vector3.new(0, 3, 0)
	local look = Vector3.new(to.CFrame.LookVector.X, 0, to.CFrame.LookVector.Z)
	ch:PivotTo(CFrame.lookAt(at, at + (if look.Magnitude > 0.01 then look.Unit else Vector3.zAxis)))
	CalloutR:FireClient(p, text, 1.2)
end

local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.1 then return end
	acc = 0
	local toTraining = doors:FindFirstChild("ToTraining") :: BasePart?
	local toHub = doors:FindFirstChild("ToHub") :: BasePart?
	local now = os.clock()
	for _, p in Players:GetPlayers() do
		if p:GetAttribute("Team") ~= nil or now - (last[p] or 0) < 1.5 then continue end
		local ch = p.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not ch or not hum or not root or hum.Health <= 0 then continue end
		if toTraining and inside(toTraining, root.Position) then
			local s = pick(hub:FindFirstChild("TrainSpawns"))
			if s then hop(p, ch, root, s, "TRAINING GROUND") end
		elseif toHub and inside(toHub, root.Position) then
			local s = pick(doors:FindFirstChild("HubArrive"))
			if s then hop(p, ch, root, s, "BACK TO THE HUB") end
		end
	end
end)

Players.PlayerRemoving:Connect(function(p: Player) last[p] = nil end)
