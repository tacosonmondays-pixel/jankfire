-- the Play button's server side (roblox/docs/MATCHMAKING.md): parties and private lobbies (Party.luau), the in-server
-- matchmaker (Queue.luau), ranked ratings (RankedData.luau) and, switched off, the cross-server pieces
-- (CrossServer.luau). the same Fight, Matches and Stats modules Combat and ProfileServer run (one require cache).
-- Studio play tests: ServerStorage.JankPlayTest (BindableFunction, Studio only): see the ops below.
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Jankfire = script.Parent
local Fight = require(Jankfire:WaitForChild("Fight"))
local Matches = require(Jankfire:WaitForChild("Matches"))
local Stats = require(Jankfire:WaitForChild("Stats"))
local RankedData = require(Jankfire:WaitForChild("RankedData"))
local Party = require(Jankfire:WaitForChild("Party"))
local CrossServer = require(Jankfire:WaitForChild("CrossServer"))
local Recorder = require(Jankfire:WaitForChild("Recorder"))
local QuickJoin = require(Jankfire:WaitForChild("QuickJoin"))

-- the remotes (in the saved place and default.project.json; made here too if missing)
local remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
for name, class in { Play = "RemoteFunction", PlayPush = "RemoteEvent" } do
	if not remotes:FindFirstChild(name) then
		local r = Instance.new(class)
		r.Name = name
		r.Parent = remotes
	end
end
local pushR = remotes:WaitForChild("PlayPush") :: RemoteEvent

RankedData.init(Matches, Stats, function(p: Player, msg: any) if p.Parent then pushR:FireClient(p, msg) end end)
Party.init(Fight, Matches, RankedData, remotes)
CrossServer.init(Matches, {}) -- (does nothing while PlayConfig.CROSS_SERVER is off)
-- every match recorded (Recorder.luau): killcams, the play of the match, recordings for reports
Recorder.init(Fight, Matches)
-- QUICK JOIN: a pop-up for everyone free in the hub when someone steps on a queue pad (QuickJoin.luau)
QuickJoin.init(Matches, Party, remotes)

-- ------------------------------------------------------------------ Studio play tests
--   T:Invoke("standins", n, rating)   n stand-ins in this server's invite list (invite one: it joins after 1 s)
--   T:Invoke("join", player)          a stand-in straight into the player's party
--   T:Invoke("rival", mode, ranked, size, rating)   a stand-in group searching that queue
--   T:Invoke("hold", secs, win)       a match with stand-ins in it lasts secs, then team `win` takes it
--   T:Invoke("state")                 parties, queues, rooms
--   T:Invoke("ranked", player)        the player's ratings (Studio's own store, JankfireRanked_studio)
--   T:Invoke("setranked", player, mode, { r, rd, n, placed, need, lp })   T:Invoke("resetranked", player)
--   T:Invoke("restore", cheaterId, since, queueAll)   a confirmed cheater: RankedData.restoreFor (queueAll: fixes go to the
--     store even for players here);  T:Invoke("fixes", userId) the fixes waiting for them;  T:Invoke("pull", player)
--     take and apply them (what a join does);  T:Invoke("log", player) their season's ranked log
--   T:Invoke("play", player) / ("leave", player)   what the PLAY and LEAVE buttons do
--   T:Invoke("qjstand", pad, side, name) / ("qjoff", pad) / ("qjgap", secs) / ("qjstate", player)   QUICK JOIN (QuickJoin.luau)
if RunService:IsStudio() then
	local old = ServerStorage:FindFirstChild("JankPlayTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankPlayTest"
	fn.OnInvoke = function(op: string, a: any, b: any, c: any, d: any): any
		if op == "ranked" or op == "setranked" or op == "resetranked" or op == "restore" or op == "unrestore" or op == "fixes" or op == "pull" or op == "log" then return RankedData.test(op, a, b, c) end
		if string.sub(op, 1, 2) == "qj" then return QuickJoin.test(op, a, b, c) end
		if op == "play" then return Party.enter(a) end
		if op == "leave" then Party.leave(a); return true end
		return Party.test(op, a, b, c, d)
	end
	fn.Parent = ServerStorage
end
