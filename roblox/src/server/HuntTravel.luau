--!strict
-- HOLDOUT's way in and out (26 Nov 2026; roblox/docs/HUNT.md section 1). The owner: "The new gamemode will start in a
-- new lobby, we'll teleport you there since itll technically be a new game". Today the lobby, THE HOUSE, is a far
-- corner of this place (workspace.Map.HuntHouse), so going there is a server move with the anti-cheat's TeleportT
-- stamp; once HOLDOUT is its own place in this experience (HuntConfig.PLACE_ID), the same calls teleport instead, and
-- coins, skins, loadouts, ranks and VIP carry over by themselves (DataStores and passes belong to the experience)
--   HuntTravel.go(p)     to the house (from the hub, the PLAY screen's HOLDOUT card or a HuntPortal prompt)
--   HuntTravel.back(p)   back to your hub (the house's front door)
--   HuntTravel.spawnAt() a house spawn (CFrame), for respawns and arrivals
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TeleportService = game:GetService("TeleportService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any

local HuntTravel = {}
HuntTravel.COOLDOWN = 2
local lastGo: { [Player]: number } = {}

local function house(): Instance?
	local map = workspace:FindFirstChild("Map")
	return map and map:FindFirstChild(HC.HOUSE)
end
function HuntTravel.spawnAt(): CFrame?
	local h = house()
	local hf = h and h:FindFirstChild("Hunt")
	local sp = hf and hf:FindFirstChild("Spawns")
	if not sp then return nil end
	local list = {}
	for _, s in sp:GetChildren() do if s:IsA("BasePart") then table.insert(list, s) end end
	if #list == 0 then return nil end
	-- the spawn furthest from anyone already standing there (people arriving together don't land in a pile)
	local best, bd = nil, -1
	for _, s in list do
		local near = math.huge
		for _, p in Players:GetPlayers() do
			local r = p.Character and p.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then near = math.min(near, (r.Position - s.Position).Magnitude) end
		end
		near += math.random() * 3
		if near > bd then best, bd = s, near end
	end
	return if best then best.CFrame else nil
end

-- the move itself: TeleportT first (the anti-cheat's contract), velocity zeroed, onto the marker facing its way
local function moveTo(p: Player, cf: CFrame): boolean
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not (ch and root and hum) or hum.Health <= 0 then return false end
	if hum.SeatPart then hum.Sit = false end
	p:SetAttribute("TeleportT", os.clock())
	root.AssemblyLinearVelocity = Vector3.zero
	ch:PivotTo(cf + Vector3.new(0, 3, 0))
	return true
end

function HuntTravel.go(p: Player): (boolean, string?)
	local t = lastGo[p]
	if t and os.clock() - t < HuntTravel.COOLDOWN then return false, "wait" end
	if p:GetAttribute("Zone") ~= "hub" then return false, "not from here" end -- (a match, training, a map room)
	if p:GetAttribute("MiniGame") then return false, "in a game" end
	lastGo[p] = os.clock()
	if HC.PLACE_ID then
		local opts = Instance.new("TeleportOptions")
		opts:SetTeleportData({ from = "hub" })
		local ok, err = pcall(function() TeleportService:TeleportAsync(HC.PLACE_ID, { p }, opts) end)
		return ok, if ok then nil else tostring(err)
	end
	local cf = HuntTravel.spawnAt()
	if not cf then return false, "the house isn't built" end
	return moveTo(p, cf), nil
end

function HuntTravel.back(p: Player): (boolean, string?)
	local t = lastGo[p]
	if t and os.clock() - t < HuntTravel.COOLDOWN then return false, "wait" end
	lastGo[p] = os.clock()
	if HC.PLACE_ID and game.PlaceId == HC.PLACE_ID then
		local opts = Instance.new("TeleportOptions")
		opts:SetTeleportData({ from = "hunt" })
		local ok, err = pcall(function() TeleportService:TeleportAsync(HC.HUB_PLACE_ID, { p }, opts) end)
		return ok, if ok then nil else tostring(err)
	end
	-- your hub's arrival point (HubTravel), the way the training hall's door sends you back
	local HT: any = nil
	local m = script.Parent:FindFirstChild("HubTravel")
	if m then local ok, r = pcall(require, m); if ok then HT = r end end
	local to: BasePart? = if HT then HT.arrive(p) else nil
	local cf: CFrame? = if to then CFrame.lookAt(to.Position, to.Position + Vector3.new(to.CFrame.LookVector.X, 0, to.CFrame.LookVector.Z)) elseif HT then HT.homeOf(p) else nil
	if not cf then return false, "no hub to go back to" end
	return moveTo(p, cf), nil
end

Players.PlayerRemoving:Connect(function(p) lastGo[p] = nil end)

return HuntTravel
