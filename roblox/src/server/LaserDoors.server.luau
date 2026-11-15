--!strict
-- the hub's laser doors. walk into the red grid behind the spawn and you're in the training ground (a big hall well
-- away from the hub: Hub.TrainingGround, its zone Hub.TrainingZone, spawns Hub.TrainSpawns, dummies Hub.DummySpots);
-- its own grid takes you back to the hub (Hub.Doors.HubArrive). the move is the server's: it stamps the player's
-- TeleportT attribute first so Main's teleport check starts afresh instead of putting them back, then moves the body.
-- 1.5 s between hops per player so nobody bounces; not while in a match.
-- there is also a secret: the bullseye of the hall's middle wall target (Doors.ToPlayground, a small box 14 studs up:
-- grapple it) drops you in the PLAYGROUND, a block course in the open air far away. its own grid brings you back, and
-- anyone who falls off its blocks is put back on its start (no death, no smog).
-- any other part in Hub.Doors with the attribute Land is a door too: Land names the marker folder in Hub.Doors you
-- arrive on ("@TrainSpawns" = the training ground's spawns), Say is the callout. the show hubs of the hub comparison
-- (workspace.Map.HubLab) use these for their training doors and the discs that take you from hub to hub
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CalloutR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Callout") :: RemoteEvent
local hub = workspace:WaitForChild("Map"):WaitForChild("Hub")
local doors = hub:WaitForChild("Doors")

local last: { [Player]: number } = {}

-- a trigger box in Hub.Doors -> the markers you land on, and what your screen says
local ROUTES: { { trigger: string, land: () -> Instance?, text: string } } = {
	{ trigger = "ToTraining", land = function() return hub:FindFirstChild("TrainSpawns") end, text = "TRAINING GROUND" },
	{ trigger = "ToHub", land = function() return doors:FindFirstChild("HubArrive") end, text = "BACK TO THE HUB" },
	{ trigger = "ToPlayground", land = function() return doors:FindFirstChild("PlaygroundArrive") end, text = "YOU FOUND THE PLAYGROUND" },
	{ trigger = "FromPlayground", land = function() return doors:FindFirstChild("TrainingArrive") end, text = "BACK TO TRAINING" },
}

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
	local now = os.clock()
	local pz = hub:FindFirstChild("PlaygroundZone") :: BasePart?
	local fallY = pz and pz:GetAttribute("FallY")
	for _, p in Players:GetPlayers() do
		if p:GetAttribute("Team") ~= nil then continue end
		local ch = p.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not ch or not hum or not root or hum.Health <= 0 then continue end
		-- fell off the playground's blocks: back on its start (this doesn't wait for the hop cooldown)
		if pz and type(fallY) == "number" and root.Position.Y < fallY and now - (last[p] or 0) > 0.3 then
			local rel = pz.CFrame:PointToObjectSpace(root.Position)
			if math.abs(rel.X) <= pz.Size.X / 2 and math.abs(rel.Z) <= pz.Size.Z / 2 and rel.Y > -pz.Size.Y / 2 - 60 then
				local s = pick(doors:FindFirstChild("PlaygroundArrive"))
				if s then hop(p, ch, root, s, "WHOOPS. AGAIN.") end
				continue
			end
		end
		if now - (last[p] or 0) < 1.5 then continue end
		local went = false
		for _, r in ROUTES do
			local t = doors:FindFirstChild(r.trigger)
			if t and t:IsA("BasePart") and inside(t, root.Position) then
				local s = pick(r.land())
				if s then hop(p, ch, root, s, r.text) end
				went = true
				break
			end
		end
		if went then continue end
		for _, t in doors:GetChildren() do
			local land = t:GetAttribute("Land")
			if type(land) == "string" and t:IsA("BasePart") and inside(t, root.Position) then
				local folder = if land == "@TrainSpawns" then hub:FindFirstChild("TrainSpawns") else doors:FindFirstChild(land)
				local s = pick(folder)
				local say = t:GetAttribute("Say")
				if s then hop(p, ch, root, s, if type(say) == "string" then say else "") end
				break
			end
		end
	end
end)

Players.PlayerRemoving:Connect(function(p: Player) last[p] = nil end)
