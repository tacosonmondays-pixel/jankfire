--!strict
-- HUB TRAVEL's server (HubTravel.luau has the hubs, homeOf and the move): the remote the HUBS menu and each hub's
-- terminal use, each player's Hub attribute kept to where they are, and their last hub saved.
--   JankfireRemotes.HubTravel (RemoteFunction): ("list") -> { {id, title, here, players} }; ("go", id) -> ok, why
--   refused while in a match (Matches.matchOf), a mini-game (the MiniGame attribute) or a party's room (Party.inLobby)
--   LastHub: DataStore JankfireHub_v1 (Studio: _studio), key u<UserId>; loaded on join, saved when it changes (at most
--   once every SAVE_EVERY s) and on leave
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")
local RunService = game:GetService("RunService")

local HubTravel = require(script.Parent:WaitForChild("HubTravel"))
local Matches = require(script.Parent:WaitForChild("Matches"))
local okParty, Party = pcall(function() return require(script.Parent:WaitForChild("Party", 10)) end)

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local rf = Remotes:FindFirstChild("HubTravel") :: RemoteFunction?
if not rf then
	local r = Instance.new("RemoteFunction"); r.Name = "HubTravel"; r.Parent = Remotes
	rf = r
end

local SAVE_EVERY = 30
local store: DataStore? = nil
pcall(function() store = DataStoreService:GetDataStore(if RunService:IsStudio() then "JankfireHub_v1_studio" else "JankfireHub_v1") end)
local saved: { [Player]: string? } = {}
local savedAt: { [Player]: number } = {}

local function save(p: Player, force: boolean?)
	local id = p:GetAttribute("LastHub")
	if type(id) ~= "string" or id == saved[p] then return end
	if not force and savedAt[p] and os.clock() - savedAt[p] < SAVE_EVERY then return end
	saved[p] = id; savedAt[p] = os.clock()
	local st = store
	if st then task.spawn(function() pcall(function() (st :: DataStore):SetAsync("u" .. p.UserId, id) end) end) end
end

Players.PlayerAdded:Connect(function(p)
	local st = store
	if not st then return end
	local ok, v = pcall(function() return (st :: DataStore):GetAsync("u" .. p.UserId) end)
	if ok and type(v) == "string" and p.Parent then
		saved[p] = v
		if p:GetAttribute("LastHub") == nil then p:SetAttribute("LastHub", v) end
	end
end)
Players.PlayerRemoving:Connect(function(p)
	save(p, true)
	saved[p] = nil; savedAt[p] = nil
end)
game:BindToClose(function() for _, p in Players:GetPlayers() do save(p, true) end end)

-- where everyone is: the nearest hub within reach of their body (twice a second)
task.spawn(function()
	while true do
		task.wait(0.5)
		for _, p in Players:GetPlayers() do
			local ch = p.Character
			local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			if root then
				local h = HubTravel.at(root.Position)
				if h and p:GetAttribute("Hub") ~= h.id then p:SetAttribute("Hub", h.id) end
				if h and p:GetAttribute("LastHub") ~= h.id then p:SetAttribute("LastHub", h.id) end
			end
			save(p)
		end
	end
end)

local function why(p: Player): string?
	if Matches.matchOf(p) then return "in a match" end
	if p:GetAttribute("MiniGame") ~= nil then return "in a mini-game" end
	if okParty and Party and Party.inLobby and Party.inLobby(p) then return "in your party's room" end
	return nil
end

;(rf :: RemoteFunction).OnServerInvoke = function(p: Player, op: any, id: any): any
	if op == "list" then
		local counts: { [string]: number } = {}
		for _, q in Players:GetPlayers() do
			local h = q:GetAttribute("Hub")
			if type(h) == "string" then counts[h] = (counts[h] or 0) + 1 end
		end
		local out = {}
		for _, h in HubTravel.list() do
			table.insert(out, { id = h.id, title = h.title, here = p:GetAttribute("Hub") == h.id, players = counts[h.id] or 0 })
		end
		return out
	elseif op == "go" then
		if type(id) ~= "string" then return false, "?" end
		local no = why(p)
		if no then return false, no end
		if p:GetAttribute("Hub") == id then return false, "you're here" end
		return HubTravel.move(p, id)
	end
	return false, "?"
end
