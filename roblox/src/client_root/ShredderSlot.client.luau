-- the Shredder on key 4, when you carry it (it's a primary now: pick it on the loadout screen, then 1 or 4 pull it out). the Roblox hotbar is off,
-- so 1 can't grab the Shredder as well. 4 again puts it away (and the weapon you had comes back)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local StarterGui = game:GetService("StarterGui")
local me = Players.LocalPlayer
task.spawn(function()
	for _ = 1, 20 do
		if pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false) end) then break end
		task.wait(0.5)
	end
end)
UIS.InputBegan:Connect(function(io, gp)
	if gp or not require(script.Parent:WaitForChild("Jankfire"):WaitForChild("Binds")).is("slot4", io) or me:GetAttribute("LoadoutOpen") then return end -- (4, or the player's own key)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then return end
	if ch:FindFirstChild("Shredder") then hum:UnequipTools(); return end
	local bag = me:FindFirstChildOfClass("Backpack")
	local tool = bag and bag:FindFirstChild("Shredder")
	if tool then hum:EquipTool(tool) end
end)
