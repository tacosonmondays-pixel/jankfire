-- daily quests, Brass and the weekly track (Quests.luau, roblox/docs/QUESTS.md), fed by Fight's and Matches' hooks
-- (the same Fight and Matches modules Combat runs: one require cache)
local Jankfire = script.Parent
require(Jankfire:WaitForChild("Quests")).init(require(Jankfire:WaitForChild("Fight")), require(Jankfire:WaitForChild("Matches")))
