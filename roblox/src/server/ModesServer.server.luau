-- the classic modes' server side (Modes.luau; the numbers and cards in Shared.ModeConfig, the web rules in
-- roblox/docs/MODES.md): the MODES tab's cards get their start, and the mode rules go on Fight's hooks. the same Fight,
-- Matches, Utility and Recorder modules Combat and PlayServer run (one require cache).
-- Studio play tests: ServerStorage.JankModeTest (BindableFunction, Studio only): Modes.test's ops
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local Jankfire = script.Parent
local Fight = require(Jankfire:WaitForChild("Fight"))
local Matches = require(Jankfire:WaitForChild("Matches"))
local Utility = require(Jankfire:WaitForChild("Utility"))
local Recorder = require(Jankfire:WaitForChild("Recorder"))
local Modes = require(Jankfire:WaitForChild("Modes"))

Modes.init(Fight, Matches, Utility, Recorder)

if RunService:IsStudio() then
	local old = ServerStorage:FindFirstChild("JankModeTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankModeTest"
	fn.OnInvoke = function(op: string, a: any, b: any, c: any, d: any): any return Modes.test(op, a, b, c, d) end
	fn.Parent = ServerStorage
end
