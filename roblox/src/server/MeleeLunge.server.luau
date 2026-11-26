--!strict
-- the melee LUNGE's say-so (26 Nov 2026; shared/Melee.luau, docs/MELEE.md). the client runs the lunge at once
-- (client/MeleeLunge.luau) and sends Lunge(target). here: a swung weapon in your hands, alive, where weapons work, after
-- GO, not stunned, staggered, held or mid-cast, the cooldown over (LungeT on you, server time), and the target a living
-- fighter you may fight (or a training dummy) within reach of the lunge and in sight (now or a moment ago, for lag).
-- yes: the anti-cheat is told (ACGrace for the lunge's time: the movement checks start afresh after it) and the cooldown
-- starts. no: "no" back, and the client stops where it is (it has only run a frame or two)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Melee = require(Shared:WaitForChild("Melee"))
local Weapons = require(Shared:WaitForChild("Weapons"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Matches = require(script.Parent:WaitForChild("Matches"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local W = Weapons.list :: any
local L = Melee.LUNGE

local LungeR = Remotes:FindFirstChild("Lunge") :: RemoteEvent?
if not LungeR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Lunge"
	r.Parent = Remotes
	LungeR = r
end
local FIGHT = { match = true, training = true, playground = true }
local function snow(): number return workspace:GetServerTimeNow() end

-- (Studio play tests) the last asks and answers: ServerStorage.JankMeleeTest "log"
local log: { any } = {}
local function note(e: any)
	table.insert(log, e)
	if #log > 30 then table.remove(log, 1) end
end

local function refuse(p: Player, why: string)
	note({ k = "no", by = p.Name, why = why, t = snow() })
	;(LungeR :: RemoteEvent):FireClient(p, "no", why)
end

;(LungeR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, target: unknown)
	local f = Fight.byPlayer[p]
	if not f or not f.alive then return refuse(p, "dead") end
	if not FIGHT[p:GetAttribute("Zone") :: any] and p:GetAttribute("DevArms") ~= true then return refuse(p, "no weapons here") end
	if not Melee.swung(W[f.held]) then return refuse(p, "not a melee weapon") end
	if Matches.roundLocked(p) then return refuse(p, "not yet") end
	if p:GetAttribute("Trap") or p:GetAttribute("Jail") or p:GetAttribute("Quiz") then return refuse(p, "held") end
	local n = os.clock()
	if n < f.staggerUntil or (f.castUntil and n < f.castUntil) then return refuse(p, "busy") end
	local stun = p:GetAttribute("StunUntil")
	if type(stun) == "number" and snow() < stun then return refuse(p, "stunned") end
	local ready = p:GetAttribute("LungeT")
	if type(ready) == "number" and snow() < ready - 0.2 then return refuse(p, "too soon") end
	if typeof(target) ~= "Instance" or not (target :: Instance):IsA("Model") then return refuse(p, "nobody") end
	local tm = target :: Model
	local t = Fight.of(Players:GetPlayerFromCharacter(tm) or tm)
	if not t or not t.alive or t == f then return refuse(p, "nobody") end
	if t.kind == "player" and not Fight.allow(f, t) then return refuse(p, "not a fair target") end -- (a teammate; training's other players)
	local fr, tr = Fight.root(f), Fight.root(t)
	if not fr or not tr then return refuse(p, "nobody") end
	-- in reach: the lunge's range and some lag, on the server's copy of either of you (and how fast you both go)
	local d = (tr.Position - fr.Position).Magnitude
	if d > L.range + L.slack + 0.3 * (Fight.speed(f) + Fight.speed(t)) then return refuse(p, "too far") end
	local eye = Fight.eye(f)
	if not eye or not Fight.sees(eye, t) then return refuse(p, "not in sight") end
	p:SetAttribute("LungeT", snow() + L.cd)
	p:SetAttribute("ACGrace", n + L.time + 0.5) -- (the anti-cheat: this burst is the server's say)
	note({ k = "lunge", by = p.Name, v = t.name, d = math.floor(d * 10) / 10, t = snow() })
end)
Fight.onSpawn(function(f: Rules.Fighter)
	if f.kind == "player" then (f.ref :: Player):SetAttribute("LungeT", nil) end -- (a fresh life starts ready)
end)

-- the test hook (Studio only): "log" (the asks), "clear"
if game:GetService("RunService"):IsStudio() then
	local ServerStorage = game:GetService("ServerStorage")
	local hook = ServerStorage:FindFirstChild("JankMeleeTest") :: BindableFunction?
	if not hook then
		local b = Instance.new("BindableFunction")
		b.Name = "JankMeleeTest"
		b.Parent = ServerStorage
		hook = b
	end
	(hook :: BindableFunction).OnInvoke = function(op: string, a: any)
		if op == "log" then return log end
		if op == "clear" then table.clear(log); return true end
		if op == "ready" and typeof(a) == "Instance" and a:IsA("Player") then a:SetAttribute("LungeT", nil); return true end
		return nil
	end
end
