-- takes the server's finishers (JankfireRemotes.Finisher, from server/FinisherServer) and plays them (Finisher.luau;
-- roblox/docs/FINISHERS.md). one ends when a round goes live, when you go home, or when you respawn.
-- the settings page's "gfx.othersFinisher" (default on) turns off finishers you only watch; your own (as the killer or
-- the victim) always play, and SKIP ends any of them.
-- Studio tests: the player attribute FinisherTest = "preview:<id>" | "preview:<id>:short" | "stop"; training dummies'
-- looks are kept as they spawn so a test kill's victim has a whole body (Finisher.dummyLooks)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local F = require(script.Parent:WaitForChild("Finisher"))
local FFx = require(script.Parent:WaitForChild("FinisherFx"))
local Replay = require(script.Parent:WaitForChild("Replay"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer

Remotes:WaitForChild("Finisher").OnClientEvent:Connect(function(msg: any)
	if type(msg) ~= "table" or msg.t ~= "finisher" then return end
	if msg.role == "watch" and FFx.setting("gfx.othersFinisher", true) == false then return end
	local ok, err = pcall(F.play, msg)
	if not ok then warn("[jankfire] finisher: " .. tostring(err)) end
end)

Remotes:WaitForChild("Round").OnClientEvent:Connect(function(r: any)
	if type(r) ~= "table" then return end
	if (r.start or r.hub) and F.isPlaying() then F.stop() end
end)
me.CharacterAdded:Connect(function()
	if F.isPlaying() then F.stop() end
end)

-- (Studio) the dummies' looks as they spawn: a test kill's victim is a dummy whose body has already come apart
if RunService:IsStudio() then
	task.spawn(function()
		local d = workspace:WaitForChild("Dummies", 20)
		if not d then return end
		local function keep(m: Instance)
			if not m:IsA("Model") then return end
			task.delay(1, function()
				if not m.Parent then return end
				local hum = m:FindFirstChildOfClass("Humanoid")
				if not hum or hum.Health <= 0 then return end
				local was = m.Archivable
				m.Archivable = true
				local ok, c = pcall(function() return m:Clone() end)
				m.Archivable = was
				if not ok or not c then return end
				local old = F.dummyLooks[m.Name]
				F.dummyLooks[m.Name] = Replay.clean(c)
				if old then old:Destroy() end
			end)
		end
		for _, m in d:GetChildren() do keep(m) end
		d.ChildAdded:Connect(keep)
	end)
end

me:GetAttributeChangedSignal("FinisherTest"):Connect(function()
	local v = me:GetAttribute("FinisherTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("FinisherTest", nil)
	if v == "stop" then F.stop(); return end
	local id, kind = string.match(v, "^preview:([%w_]+):?(%a*)$")
	if id then
		local ok, res = pcall(F.preview, id, { kind = if kind == "short" then "short" else "full" })
		me:SetAttribute("FinisherTestResult", if ok then tostring(res) else ("error: " .. tostring(res)))
	end
end)
