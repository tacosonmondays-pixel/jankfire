--!strict
-- ZoneSounds: a short, soft sting when you move from one area into another (the owner, 17 Nov 2026: "can you have a
-- sfx when entering and leaving areas?"). one sting per area, played for you alone as you arrive there (the hub and the
-- VIP room have none): recordings (Freesound CC0 / Pro Sound Effects), each about a second, quiet.
--   hub        (none: see below)                       training   a pneumatic air hiss (the hall's doors)
--   playground a light, slow swoosh                    lot        a gust of wind (the back lot, outdoors)
--   vip        (none: its door rings, see below)        lobby      a soft whoosh into your party's room
-- where you are: the server's "Zone" attribute (hub / training / playground / match, Matches.zoneOf), its "OnLot"
-- (TheLot), and here: inside a part tagged VipRoom, or inside a room of workspace.PartyLobbies.
-- quiet on purpose: arriving in the hub, from anywhere (its sting was a crowd murmur; the owner, 17 Nov: "when you step
-- out I think there's like a crowd sound effect, I don't want that, cut it to just the bell", then "why is the crowd sfx
-- still there i want it gone completely": the Sound zone_hub is gone from JankfireSounds too, and no other sound
-- replaces it), into the VIP room (the door's own chime and slide, HubVip.client, are the only sounds there), the first
-- area after you spawn or respawn, anything to or from a match (the round has its own sounds), and a second sting within
-- 1.5 s (walking back and forth over a line doesn't spam). the Sounds are named "zone_<area>" in JankfireSounds, so the
-- settings page's EFFECTS volume covers them (SettingsApply).
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")

local Sfx = require(script.Parent:WaitForChild("Sfx"))

local me = Players.LocalPlayer
local COOLDOWN = 1.5
local SPAWN_QUIET = 2.5

local function inside(cf: CFrame, size: Vector3, pos: Vector3): boolean
	local rel = cf:PointToObjectSpace(pos)
	local h = size / 2
	return math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y + 2 and math.abs(rel.Z) <= h.Z
end

local lobbyBoxes: { [Instance]: { CFrame | Vector3 } } = {}
local function inLobby(pos: Vector3): boolean
	local rooms = workspace:FindFirstChild("PartyLobbies")
	if not rooms then return false end
	for _, m in ipairs(rooms:GetChildren()) do
		if m:IsA("Model") then
			local box = lobbyBoxes[m]
			if not box then
				local cf, size = m:GetBoundingBox()
				box = { cf, size }
				lobbyBoxes[m] = box
				m.Destroying:Once(function() lobbyBoxes[m] = nil end)
			end
			if inside(box[1] :: CFrame, box[2] :: Vector3, pos) then return true end
		end
	end
	return false
end

local function inVip(pos: Vector3): boolean
	for _, p in ipairs(CollectionService:GetTagged("VipRoom")) do
		if p:IsA("BasePart") and inside(p.CFrame, p.Size, pos) then return true end
	end
	return false
end

local function areaNow(): string?
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local zone = me:GetAttribute("Zone")
	if not root or type(zone) ~= "string" then return nil end
	if zone == "match" then return "match" end
	local pos = root.Position
	if inLobby(pos) then return "lobby" end
	if me:GetAttribute("OnLot") == true then return "lot" end
	if zone == "hub" and inVip(pos) then return "vip" end
	return zone
end

local area: string? = nil
local lastSting = -math.huge
local spawnedAt = os.clock()
me.CharacterAdded:Connect(function() spawnedAt = os.clock(); area = nil end)

while true do
	task.wait(0.2)
	local now = os.clock()
	local a = areaNow()
	if a and a ~= area then
		local from = area
		area = a
		local quiet = from == nil -- (the first area after you spawn: no sting)
			or now - spawnedAt < SPAWN_QUIET
			or a == "match" or from == "match"
			or a == "hub" -- (no crowd, no sting: the owner wants it gone)
			or a == "vip" -- (the VIP door has its own sounds)
			or now - lastSting < COOLDOWN
		if not quiet then
			lastSting = now
			Sfx.play("zone_" .. a)
		end
	end
end
