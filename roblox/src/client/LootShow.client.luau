-- other players' openings, seen from here: when someone near you opens a Crate, Duffel Bag or Spray Can, the server
-- (Loot.luau) sends one LootShow event and LootOpening.show draws it: their container drops on the ground in front of
-- them, pops, and what they got rises over it with a sign. a player who turned it off in Settings (P) sends nothing
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Opening = require(script.Parent:WaitForChild("LootOpening"))
local ev = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("LootShow", 60)
if ev and ev:IsA("RemoteEvent") then
	ev.OnClientEvent:Connect(function(data) Opening.show(data) end)
end
