-- takes the server's clips (JankfireRemotes.Replay, from server/Recorder.luau) and plays them (Replay.luau):
--   killcam: right away (a new round going live, or the match ending, stops it)
--   potm (the play of the match): at the time the server names, when the end screen has had its moment
-- and keeps a clean copy of every player's look as they spawn (Replay.templates), so a ghost always wears the body,
-- clothes and accessories its player had, even after that player has died, left or respawned
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Replay = require(script.Parent:WaitForChild("Replay"))
local Settings = require(script.Parent:WaitForChild("Settings"))
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
		if me:GetAttribute("Finishing") then return end -- (a finisher is this death's camera: client/Finisher.luau)
		if Settings.get("hud.killcam") == false then return end -- (Settings > HUD: KILLCAM off. DeathCam.client's orbit stays)
		Replay.play(msg)
	elseif msg.t == "potm" then
		potmTok += 1
		local my = potmTok
		-- (20 Nov 2026, the owner, live: "during a match the cutscene animatin gets cut off still": the server times the play
		-- of the match for after a finisher's scene - its `at` ~17 s out, the scene's hold plus the end screen's moment -
		-- but the wait here stopped at 10 s, so the replay started ~11 s into the 14 s scene, and a finisher ends when a
		-- replay starts. Studio's test matches have no play of the match, so only a live match showed it. Now the whole
		-- wait, and never over a finisher: it waits for that to end; going home first drops it)
		local wait = (tonumber(msg.at) or 0) - workspace:GetServerTimeNow()
		task.delay(math.clamp(wait, 0, 45), function()
			if my ~= potmTok then return end
			local t0 = os.clock()
			while me:GetAttribute("Finishing") and os.clock() - t0 < 25 do task.wait(0.1) end
			if my ~= potmTok then return end
			if os.clock() - t0 > 0.05 then print(("[jankfire] the play of the match waited %.1f s for a finisher"):format(os.clock() - t0)) end
			Replay.play(msg)
		end)
	end
end)

-- a new round going live (or the match ending) ends a killcam: you're back in, or the end screen has the floor
Remotes:WaitForChild("Round").OnClientEvent:Connect(function(r: any)
	if type(r) ~= "table" then return end
	if (r.start or r.over or r.hub) and Replay.mode() == "killcam" then Replay.stop() end
	if r.hub and Replay.mode() == "potm" then Replay.stop() end
	if r.hub then potmTok += 1 end -- (home: one still waiting doesn't start here)
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
