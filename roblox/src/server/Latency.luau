--!strict
-- (20 Nov 2026, hit registration) how far back the server looks along a target's trail for one shooter's headshot:
-- that shooter's own round trip plus a margin, between MIN and MAX seconds. A client sees everyone else about one
-- round trip and an interpolation step late, so a headshot claimed on a spot the target left longer ago than that is
-- one this shooter never saw: it's paid as a body shot (Combat -> Rules.headAimed). The round trip is our own echo
-- (remote LagEcho, client/LagEcho.client.luau, every EVERY seconds), so it counts everything that delays what the
-- client sees, not only the network (Player:GetNetworkPing is a floor). The window takes the worst of the last KEEP
-- samples, so a jittery ping stays covered; no samples yet, or an echo missing for over 1.5 s (a spike right now):
-- the full MAX. Nothing here kicks or flags anyone (the anti-cheat is AntiCheat.server.luau's)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local STUDIO = game:GetService("RunService"):IsStudio()

local Latency = {}
-- (MARGIN and MIN measured 21 Nov in Studio on the strafing Dummy: Roblox draws everyone else an interpolation step
-- behind on top of the round trip; at 0.1 / 0.15 three of five honest heads with no added lag were paid as body, at a
-- 0.25 floor eight of eight landed)
Latency.MARGIN, Latency.MIN, Latency.MAX = 0.15, 0.25, 0.6
Latency.EVERY = 1
Latency.KEEP = 6

type St = { sent: { [number]: number }, rtt: { number }, id: number }
local st: { [Player]: St } = {}

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local R = Remotes:FindFirstChild("LagEcho") :: RemoteEvent?
if not R then
	local r = Instance.new("RemoteEvent")
	r.Name = "LagEcho"
	r.Parent = Remotes
	R = r
end
local Echo = R :: RemoteEvent

Echo.OnServerEvent:Connect(function(p: Player, id: unknown)
	local s = st[p]
	if not s or type(id) ~= "number" then return end
	local t0 = s.sent[id]
	if not t0 then return end
	s.sent[id] = nil
	table.insert(s.rtt, os.clock() - t0)
	while #s.rtt > Latency.KEEP do table.remove(s.rtt, 1) end
	p:SetAttribute("LagWinMs", math.floor(Latency.window(p) * 1000 + 0.5)) -- (for tests: the window now, in ms)
end)
Players.PlayerRemoving:Connect(function(p: Player) st[p] = nil end)

task.spawn(function()
	while true do
		task.wait(Latency.EVERY)
		local n = os.clock()
		for _, p in Players:GetPlayers() do
			local s = st[p]
			if not s then s = { sent = {}, rtt = {}, id = 0 }; st[p] = s end
			for k, t in s.sent do if n - t > 5 then s.sent[k] = nil end end -- (an echo that's never coming)
			s.id += 1
			s.sent[s.id] = n
			Echo:FireClient(p, s.id)
		end
	end
end)

-- this shooter's last round trips (seconds), newest last: for tests
function Latency.samples(p: Player): { number }
	local s = st[p]
	return if s then table.clone(s.rtt) else {}
end

-- seconds back along a target's trail this shooter may have seen it
function Latency.window(p: Player?): number
	if not p then return Latency.MAX end
	if STUDIO then -- (a test's override, Studio only: the player attribute LagWinTest, seconds)
		local o = p:GetAttribute("LagWinTest")
		if type(o) == "number" then return o end
	end
	local s = st[p]
	if not s or #s.rtt == 0 then return Latency.MAX end
	local n = os.clock()
	for _, t in s.sent do if n - t > 1.5 then return Latency.MAX end end
	local worst = 0
	for _, r in s.rtt do worst = math.max(worst, r) end
	local ok, ping = pcall(function() return p:GetNetworkPing() end)
	if ok and type(ping) == "number" then worst = math.max(worst, ping) end
	return math.clamp(worst + Latency.MARGIN, Latency.MIN, Latency.MAX)
end

return Latency
