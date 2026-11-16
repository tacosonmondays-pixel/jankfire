--!nonstrict
-- the hub's VIP room: only VIP players may be in it. the door is shut and solid on the server; a VIP player's own screen
-- opens it (HubVip.client). twice a second this puts anyone who isn't VIP and stands in the room (the part tagged
-- VipRoom, HubRotundaRooms builds it) back out in front of the door, facing away from it (its Out and OutLook
-- attributes). who is VIP: the shop's Vip.luau (Vip.isVip), or, if that module isn't in the place, the player attribute
-- VIP it sets (only the server can set it)
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")

local Vip = nil
task.spawn(function()
	local folder = script.Parent
	local m = folder and folder:WaitForChild("Vip", 10)
	if m and m:IsA("ModuleScript") then
		local ok, res = pcall(require, m)
		if ok and type(res) == "table" then Vip = res end
	end
end)

local function isVip(p: Player): boolean
	if Vip and type(Vip.isVip) == "function" then
		local ok, r = pcall(Vip.isVip, p)
		if ok then return r == true end
	end
	return p:GetAttribute("VIP") == true
end

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
					ch:PivotTo(CFrame.lookAt(out, out + dir))
					root.AssemblyLinearVelocity = Vector3.zero
				end
			end
		end
	end
end
