-- crouch / slide poses: a client says which pose it's in, the server puts it on their character as "Pose" so every
-- other client can bend that body. three known values only, at most 12 changes a second.
local Players = game:GetService("Players")
local remote = game:GetService("ReplicatedStorage"):WaitForChild("PoseRemote")
local VALID = { stand = true, crouch = true, slide = true }
local budget = {}
remote.OnServerEvent:Connect(function(p, pose)
	if type(pose) ~= "string" or not VALID[pose] then return end
	local now = os.clock()
	local b = budget[p]
	if not b or now - b.t > 1 then b = { t = now, n = 0 }; budget[p] = b end
	b.n += 1
	if b.n > 12 then return end
	local ch = p.Character
	if ch then ch:SetAttribute("Pose", pose) end
end)
Players.PlayerRemoving:Connect(function(p) budget[p] = nil end)
