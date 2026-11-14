-- grapple impacts, server side: a client that just got launched off a ledge or ragdolled by a wall asks for its rope
-- to be dropped. at most twice a second, alive only; the server tells Move to let go ("cut", the same message the
-- hook checks use). the vault and the ragdoll themselves are the client's, like all movement.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remote = ReplicatedStorage:WaitForChild("ImpactRemote")
local GrappleRemote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Grapple")
local lastT = {}
remote.OnServerEvent:Connect(function(p, kind)
	if kind ~= "launch" and kind ~= "ragdoll" then return end
	local now = os.clock()
	if now - (lastT[p] or 0) < 0.5 then return end
	lastT[p] = now
	local hum = p.Character and p.Character:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then return end
	GrappleRemote:FireClient(p, "cut")
end)
Players.PlayerRemoving:Connect(function(p) lastT[p] = nil end)
