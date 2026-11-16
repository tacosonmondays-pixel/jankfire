-- the player cards' server side: Stats.luau (stats from the fights and the matches, XP, the card's look, the privacy
-- switch), fed by Fight's and Matches' hooks. (the same Fight and Matches modules Combat runs: one require cache)
local Jankfire = script.Parent
require(Jankfire:WaitForChild("Stats")).init(require(Jankfire:WaitForChild("Fight")), require(Jankfire:WaitForChild("Matches")))
