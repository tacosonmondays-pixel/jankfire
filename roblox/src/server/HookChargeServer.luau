--!strict
-- the server's grapple charges (shared/HookCharges.luau: 2 charges, back one at a time every 6 s). they count only in
-- a ranked match (Matches.matchOf(p).ranked: a RANKED duel or a PARTY RANKED match). Main's hook check asks
-- HookChargeServer.allow(p) once a hook has passed its range and sight checks; a hook with no charge left is cut
-- ("recharging"). a new body (each round, each respawn) starts full.
-- what the client reads (client/HookChargesUI.luau predicts with the same maths and corrects to these):
--   HookLimit  true while the charges count       HookN  charges left       HookT0  the server time the charge coming
--                                                                                   back started (0 = full)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HookCharges"))
local Matches = require(script.Parent:WaitForChild("Matches"))

local HookChargeServer = {}
local state: { [Player]: HC.State } = {}

local function now(): number return workspace:GetServerTimeNow() end
local function limited(p: Player): boolean
	local m = Matches.matchOf(p)
	return m ~= nil and m.ranked == true
end
local function publish(p: Player, s: HC.State)
	if p:GetAttribute("HookN") ~= s.n then p:SetAttribute("HookN", s.n) end
	local t0 = s.t0 or 0
	if p:GetAttribute("HookT0") ~= t0 then p:SetAttribute("HookT0", t0) end
end
local function fresh(p: Player)
	local s = HC.new()
	state[p] = s
	publish(p, s)
end

-- (Main's hook check) may this hook go? spends a charge in a ranked match; always yes elsewhere
function HookChargeServer.allow(p: Player): boolean
	if not limited(p) then return true end
	local s = state[p]
	if not s then fresh(p); s = state[p] end
	local ok = HC.spend(s :: HC.State, now())
	publish(p, s :: HC.State)
	return ok
end

local function watch(p: Player)
	p.CharacterAdded:Connect(function() fresh(p) end)
end
for _, p in Players:GetPlayers() do watch(p) end
Players.PlayerAdded:Connect(watch)
Players.PlayerRemoving:Connect(function(p) state[p] = nil end)

local acc = 0
RunService.Heartbeat:Connect(function(dt)
	acc += dt
	if acc < 0.25 then return end
	acc = 0
	for _, p in Players:GetPlayers() do
		local lim = limited(p)
		if p:GetAttribute("HookLimit") ~= lim then
			p:SetAttribute("HookLimit", lim)
			if lim then fresh(p) end
		end
		local s = state[p]
		if lim and s then HC.update(s, now()); publish(p, s) end
	end
end)

return HookChargeServer
