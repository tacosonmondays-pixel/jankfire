-- (20 Nov 2026, hit registration) answers the server's latency echo straight away (server/Latency.luau): the round
-- trip sets how far back the server checks a target's trail for this player's headshots
local R = game:GetService("ReplicatedStorage"):WaitForChild("JankfireRemotes"):WaitForChild("LagEcho") :: RemoteEvent
R.OnClientEvent:Connect(function(id: any) R:FireServer(id) end)
