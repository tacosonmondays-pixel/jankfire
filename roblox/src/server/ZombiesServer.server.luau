--!strict
-- ZOMBIES: starts the mode's module (Zombies.luau) with the Fight and Matches it hooks into, and plugs in stage 2
-- (ZombieExtra.luau: the power, colas, Voider, Cheat Machine, drops, boards, the crate). the modules are the same copies
-- Main.server uses (one require cache per server)
local Fight = require(script.Parent:WaitForChild("Fight"))
local Matches = require(script.Parent:WaitForChild("Matches"))
local Zombies = require(script.Parent:WaitForChild("Zombies"))
local ZombieExtra = require(script.Parent:WaitForChild("ZombieExtra"))
Zombies.init(Fight, Matches)
ZombieExtra.install(Zombies)
