-- takes the server's clips (JankfireRemotes.Replay, from server/Recorder.luau) and plays them (Replay.luau):
--   killcam: right away (a new round going live, or the match ending, stops it)
--   potm (the play of the match): at the time the server names, when the end screen has had its moment
-- and keeps a clean copy of every player's look as they spawn (Replay.templates), so a ghost always wears the body,
-- clothes and accessories its player had, even after that player has died, left or respawned
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Replay = require(script.Parent:WaitForChild("Replay"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer

-- ------------------------------------------------------------------ each player's look
local function keep(p: Player, ch: Model)
	task.delay(2.5, function() -- (the avatar's clothes and accessories land after the body)
		if p.Character ~= ch or not ch.Parent then return end
		local hum = ch:FindFirstChildOfClass("Humanoid")
		if not hum or hum.Health <= 0 then return end
		local was = ch.Archivable
		ch.Archivable = true
		local ok, c = pcall(function() return ch:Clone() end)
		ch.Archivable = was
		if not ok or not c then return end
		local old = Replay.templates[p.UserId]
		Replay.templates[p.UserId] = Replay.clean(c)
		if old then old:Destroy() end
	end)
end
local function watch(p: Player)
	p.CharacterAdded:Connect(function(ch) keep(p, ch) end)
	if p.Character then keep(p, p.Character) end
end
for _, p in Players:GetPlayers() do watch(p) end
Players.PlayerAdded:Connect(watch)
-- (a leaver's look stays a while: the play of the match may still show them)
Players.PlayerRemoving:Connect(function(p)
	task.delay(120, function()
		if Players:GetPlayerByUserId(p.UserId) then return end
		local t = Replay.templates[p.UserId]
		if t then t:Destroy(); Replay.templates[p.UserId] = nil end
	end)
end)

-- ------------------------------------------------------------------ the server's clips
local potmTok = 0
Remotes:WaitForChild("Replay").OnClientEvent:Connect(function(msg: any)
	if type(msg) ~= "table" then return end
	if msg.t == "killcam" then
		if Replay.mode() == "potm" then return end
		Replay.play(msg)
	elseif msg.t == "potm" then
		potmTok += 1
		local my = potmTok
		local wait = (tonumber(msg.at) or 0) - workspace:GetServerTimeNow()
		task.delay(math.clamp(wait, 0, 10), function()
			if my ~= potmTok then return end
			Replay.play(msg)
		end)
	end
end)

-- a new round going live (or the match ending) ends a killcam: you're back in, or the end screen has the floor
Remotes:WaitForChild("Round").OnClientEvent:Connect(function(r: any)
	if type(r) ~= "table" then return end
	if (r.start or r.over or r.hub) and Replay.mode() == "killcam" then Replay.stop() end
	if r.hub and Replay.mode() == "potm" then Replay.stop() end
end)

-- a test hook (Play tests driven from Studio): the local player's attribute ReplayTest = "stop" ends a replay;
-- "count" puts the number of kept looks on the attribute ReplayLooks
me:GetAttributeChangedSignal("ReplayTest"):Connect(function()
	local v = me:GetAttribute("ReplayTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("ReplayTest", nil)
	if v == "stop" then Replay.stop()
	elseif v == "count" then
		local n = 0
		for _ in Replay.templates do n += 1 end
		me:SetAttribute("ReplayLooks", n)
	end
end)
