--!strict
-- the hub is weapons-free (owner, 2026-11-14: "no weapons in the hub except for the training room"). when your Zone
-- (Matches sets it: hub / training / match) changes, the gun others see in your hand is put away or brought back
-- (Fight.showWeapon checks Fight.holstered), and a Tool (the Shredder) can't stay out in the hub. Combat refuses
-- shots, swings and guards from the hub; Arsenal hides your viewmodel there
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Fight = require(script.Parent:WaitForChild("Fight"))

local function refresh(p: Player)
	local f = Fight.byPlayer[p]
	if f and f.alive then Fight.showWeapon(f) end
end

local function watch(p: Player)
	p:GetAttributeChangedSignal("Zone"):Connect(function() refresh(p) end)
	p:GetAttributeChangedSignal("Unarmed"):Connect(function() refresh(p) end) -- (a HOLDOUT hider in a round, HuntRound)
end
for _, p in Players:GetPlayers() do watch(p) end
Players.PlayerAdded:Connect(watch)

local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.25 then return end
	acc = 0
	for _, p in Players:GetPlayers() do
		if (p:GetAttribute("Zone") ~= "hub" and p:GetAttribute("Unarmed") ~= true) or p:GetAttribute("DevArms") == true then continue end -- (DevArms: the owner's dev weapons, OwnerDev.server)
		local ch = p.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		if hum and ch:FindFirstChildOfClass("Tool") then hum:UnequipTools() end
		local hw = ch and ch:FindFirstChild("HeldWeapon")
		if hw then hw:Destroy() end
	end
end)
