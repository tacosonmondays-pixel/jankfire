--!nonstrict
-- the hub's VIP room (HubRotundaRooms builds it, behind the lounge): only VIP players get in, decided here on the server
-- by the shop's Vip.luau (Vip.isVip: the game pass, the free claim while testing, the owner's Studio unlock). the
-- player attribute VIP is for the screen only and is never trusted here.
--   the door: its leaves (the parts named Leaf in the Models tagged VipDoor) are in the collision group "VipDoor"; a VIP
--   player's character is in "VipGuest", which passes through it; everyone else's collides with it. the group is set
--   when a character appears, on every part it gains, and whenever Vip.changed says VIP turned on or off. (their own
--   screen also slides the leaves open for a VIP: HubVip.client, looks only)
--   the room: twice a second, anyone who isn't VIP and stands in it (the part tagged VipRoom) is put back out in front of
--   the door, facing away from it (its Out and OutLook attributes): the backstop for anything that gets past the door
-- until Vip.luau is in the place, nobody counts as VIP
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")
local PhysicsService = game:GetService("PhysicsService")

local DOOR, GUEST = "VipDoor", "VipGuest"
pcall(function() PhysicsService:RegisterCollisionGroup(DOOR) end)
pcall(function() PhysicsService:RegisterCollisionGroup(GUEST) end)
PhysicsService:CollisionGroupSetCollidable(DOOR, GUEST, false)

local Vip = nil
local function isVip(p: Player): boolean
	if not Vip or type(Vip.isVip) ~= "function" then return false end
	local ok, r = pcall(Vip.isVip, p)
	return ok and r == true
end

-- the door's leaves into their group
local function door(m: Instance)
	for _, p in m:GetDescendants() do if p:IsA("BasePart") and p.Name == "Leaf" then p.CollisionGroup = DOOR end end
end
CollectionService:GetInstanceAddedSignal("VipDoor"):Connect(door)
for _, m in CollectionService:GetTagged("VipDoor") do door(m) end

-- a character's group: VipGuest for a VIP, Default for anyone else
local function setGroup(p: Player)
	local ch = p.Character
	if not ch then return end
	local g = if isVip(p) then GUEST else "Default"
	for _, d in ch:GetDescendants() do if d:IsA("BasePart") and d.CollisionGroup ~= g then d.CollisionGroup = g end end
end
local function watch(p: Player)
	p.CharacterAdded:Connect(function(ch)
		setGroup(p)
		ch.DescendantAdded:Connect(function(d) if d:IsA("BasePart") then d.CollisionGroup = if isVip(p) then GUEST else "Default" end end)
	end)
	if p.Character then
		setGroup(p)
		p.Character.DescendantAdded:Connect(function(d) if d:IsA("BasePart") then d.CollisionGroup = if isVip(p) then GUEST else "Default" end end)
	end
end
Players.PlayerAdded:Connect(watch)
for _, p in Players:GetPlayers() do watch(p) end

-- the shop's Vip module (it may land in the place after this script starts)
task.spawn(function()
	local folder = script.Parent
	local m = folder:WaitForChild("Vip")
	local ok, res = pcall(require, m)
	if not ok or type(res) ~= "table" then warn("[jankfire] HubVip: Vip.luau did not load: " .. tostring(res)); return end
	Vip = res
	for _, p in Players:GetPlayers() do setGroup(p) end
	if typeof(Vip.changed) == "RBXScriptSignal" or (type(Vip.changed) == "table" and Vip.changed.Connect) then
		Vip.changed:Connect(function(p: Player) setGroup(p) end)
	end
end)

-- the backstop
while true do
	task.wait(0.5)
	local rooms = CollectionService:GetTagged("VipRoom")
	if #rooms == 0 then continue end
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart")
		if not root or isVip(p) then continue end
		for _, room in rooms do
			if not room:IsA("BasePart") then continue end
			local rel = room.CFrame:PointToObjectSpace(root.Position)
			local h = room.Size / 2
			if math.abs(rel.X) < h.X and math.abs(rel.Y) < h.Y + 2 and math.abs(rel.Z) < h.Z then
				local out, look = room:GetAttribute("Out"), room:GetAttribute("OutLook")
				if typeof(out) == "Vector3" then
					local dir = if typeof(look) == "Vector3" then look else Vector3.new(0, 0, 1)
					p:SetAttribute("TeleportT", os.clock()) -- (a server teleport: the anti-cheat starts afresh from the door)
					ch:PivotTo(CFrame.lookAt(out, out + dir))
					root.AssemblyLinearVelocity = Vector3.zero
				end
			end
		end
	end
end
