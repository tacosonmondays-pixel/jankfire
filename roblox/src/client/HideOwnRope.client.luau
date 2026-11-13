--!strict
-- the server draws everyone's rope; ours is already drawn by Move.client.luau the moment we hook, so hide the server's
local Players = game:GetService("Players")
local me = Players.LocalPlayer
workspace.Terrain.ChildAdded:Connect(function(c: Instance)
	if c:IsA("Beam") and c:GetAttribute("Owner") == me.UserId then c.Enabled = false end
end)
