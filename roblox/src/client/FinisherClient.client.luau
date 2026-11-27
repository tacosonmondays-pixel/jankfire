-- takes the server's finishers (JankfireRemotes.Finisher, from server/FinisherServer) and plays them (Finisher.luau;
-- roblox/docs/FINISHERS.md). one ends when a round goes live, when you go home, or when you respawn.
-- the settings page's "gfx.othersFinisher" (default on) turns off finishers you only watch; your own (as the killer or
-- the victim) always play, and SKIP ends any of them.
-- Studio tests: the player attribute FinisherTest = "preview:<id>" | "preview:<id>:short" | "stop" | "warm:<sceneId>" |
-- "unwarm"; training dummies'
-- looks are kept as they spawn so a test kill's victim has a whole body (Finisher.dummyLooks)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local F = require(script.Parent:WaitForChild("Finisher"))
local FFx = require(script.Parent:WaitForChild("FinisherFx"))
local Replay = require(script.Parent:WaitForChild("Replay"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer

local remote = Remotes:WaitForChild("Finisher") :: RemoteEvent
-- (a match's full cut holds its end screen until every viewer's is over: say so when ours is - played out, skipped,
-- turned off in the settings, or never started)
local function done(msg: any)
	if msg.kind == "full" then remote:FireServer({ t = "done" }) end
end
-- the WORLD finisher (a round won, not the match: client/FinisherWorld.luau, the VFX session's) - no camera, drawn on the
-- victim's body where it lies. Someone else's, with the settings' "others' finishers" off, isn't played at all: the
-- body's kill effect just carries on
local FW: any = nil
local function world(): any
	if FW == nil then
		local m = script.Parent:FindFirstChild("FinisherWorld")
		local ok, r = false, nil
		if m then ok, r = pcall(require, m) end
		FW = if ok and type(r) == "table" then r else false
	end
	return if FW then FW else nil
end
-- (27 Nov, films with no pop-in: loaded a few seconds after joining, not on the first round won. Its pictures, pack
-- templates and stings are fetched when it loads, so the first world finisher of a game has nothing left to fetch)
task.delay(4, world)
local worldOn: { Instance } = {}
remote.OnClientEvent:Connect(function(msg: any)
	if type(msg) ~= "table" or msg.t ~= "finisher" then return end
	-- (a scene may come at the end of the next round: its set built ahead, parked - Finisher.warm)
	if msg.kind == "warm" then
		if type(msg.scenes) == "table" then F.warm(msg.scenes) end
		return
	end
	if msg.kind == "world" then
		local w = world()
		if not (w and w.play) or typeof(msg.victim) ~= "Instance" then return end
		if msg.role == "watch" and FFx.setting("gfx.othersFinisher", true) == false then return end
		local ok, err = pcall(w.play, msg.id, msg.victim, { from = if typeof(msg.from) == "Vector3" then msg.from else nil,
			killer = if typeof(msg.killer) == "Instance" then msg.killer else nil })
		if not ok then warn("[jankfire] world finisher: " .. tostring(err)) end
		table.insert(worldOn, msg.victim)
		return
	end
	if msg.role == "watch" and FFx.setting("gfx.othersFinisher", true) == false then done(msg); return end
	local ok, err = pcall(F.play, msg)
	if not ok then warn("[jankfire] finisher: " .. tostring(err)) end
	task.spawn(function()
		while F.isPlaying() do task.wait(0.1) end
		done(msg)
	end)
end)

Remotes:WaitForChild("Round").OnClientEvent:Connect(function(r: any)
	if type(r) ~= "table" then return end
	if (r.start or r.hub) and F.isPlaying() then F.stop(nil, if r.hub then "home" else "a round started") end
	if r.hub then F.unwarm() end -- (home: a set built ahead and never played goes)
	if (r.start or r.hub) and #worldOn > 0 then
		local w = world()
		for _, vm in worldOn do if w and w.stop then pcall(w.stop, vm) end end
		table.clear(worldOn)
	end
end)
me.CharacterAdded:Connect(function()
	if F.isPlaying() then F.stop(nil, "a respawn") end
	if #worldOn > 0 then
		local w = world()
		for _, vm in worldOn do if w and w.stop then pcall(w.stop, vm) end end
		table.clear(worldOn)
	end
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
	if v == "stop" then F.stop(nil, "test stop"); return end
	-- ("warm:<sceneId>" builds a scene's set ahead as the match's warning does; "unwarm" drops it. The workspace attribute
	-- FinisherWarm says when it's ready)
	if v == "unwarm" then F.unwarm(); return end
	local wid = string.match(v, "^warm:([%w_]+)$")
	if wid then F.warm({ wid }); return end
	-- ("preview:<id>[:short][:<userId>]": a userId puts that player's own avatar in as the victim, as in a real match)
	local id, kind, uid = string.match(v, "^preview:([%w_]+):?(%a*):?(%d*)$")
	if id then
		local opts: any = { kind = if kind == "short" then "short" else "full" }
		if uid and uid ~= "" then
			local okL, look = pcall(function()
				local P = game:GetService("Players")
				local m = P:CreateHumanoidModelFromDescription(P:GetHumanoidDescriptionFromUserId(tonumber(uid) :: number), Enum.HumanoidRigType.R15)
				m.Name = "Stand-in"
				return m
			end)
			if okL and look then opts.victimLook = look end
		end
		local ok, res = pcall(F.preview, id, opts)
		me:SetAttribute("FinisherTestResult", if ok then tostring(res) else ("error: " .. tostring(res)))
	end
end)
