--!strict
-- ZOMBIES: starts the mode's module (Zombies.luau) with the Fight and Matches it hooks into. the modules are the same
-- copies Main.server uses (one require cache per server)
local Fight = require(script.Parent:WaitForChild("Fight"))
local Matches = require(script.Parent:WaitForChild("Matches"))
local Zombies = require(script.Parent:WaitForChild("Zombies"))
Zombies.init(Fight, Matches)
