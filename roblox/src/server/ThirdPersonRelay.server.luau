--!strict
-- the third-person pose's network (16 Nov 2026; the client side is client/ThirdPerson.luau): each client says where
-- its player looks and two flags, and the server puts that on the player's character as the "TP" attribute
-- (Vector3: pitch, yaw offset, flags), so every other client can pose that body. small numbers only, checked, at most
-- 30 a second per player (a client sends about 12)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local remote = Remotes:FindFirstChild("TPState") :: RemoteEvent?
if not remote then
	local r = Instance.new("RemoteEvent")
	r.Name = "TPState"
	r.Parent = Remotes
	remote = r
end

local budget: { [Player]: { t: number, n: number } } = {}
local function num(v: unknown): number?
	if type(v) ~= "number" or v ~= v or v == math.huge or v == -math.huge then return nil end
	return v
end

(remote :: RemoteEvent).OnServerEvent:Connect(function(p: Player, pitch: unknown, yaw: unknown, flags: unknown)
	local a, b, c = num(pitch), num(yaw), num(flags)
	if not a or not b or not c then return end
	local now = os.clock()
	local bg = budget[p]
	if not bg or now - bg.t > 1 then bg = { t = now, n = 0 }; budget[p] = bg end
	bg.n += 1
	if bg.n > 30 then return end
	local ch = p.Character
	if not ch then return end
	local v = Vector3.new(math.clamp(math.floor(a + 0.5), -89, 89), math.clamp(math.floor(b + 0.5), -70, 70), bit32.band(math.clamp(math.floor(c), 0, 7), 7))
	if ch:GetAttribute("TP") ~= v then ch:SetAttribute("TP", v) end
end)
Players.PlayerRemoving:Connect(function(p) budget[p] = nil end)
