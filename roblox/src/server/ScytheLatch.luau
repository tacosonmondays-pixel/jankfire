--!strict
-- the Scythe's latch (the owner, 18 Nov 2026: "when you scythe it should latch on and send you back! and send them back
-- a bit too"; WEAPONS.md "Scythe"). a scythe hit (a swing's, Combat's MeleeHit, or the dash's, ScytheDash) holds them
-- on the blade for latch.t s: the damage lands at once, but nobody is shoved yet (the attacker's client hit-stops the
-- swing for the same beat). then the two spring apart, server-run through Fight.knock (the anti-cheat knows that path;
-- ACGrace covers the hop too):
--   you      back latch.back studs/s, away from the nearest one you hit (+ backUp), a short hop back
--   they     latch.push away from you (+ pushUp): less than you
-- the chain's finisher (Latch.link: the server's own count of the swing chain, the same rule as the client's) pushes
-- x latch.finisher. a wall close behind either one cuts that push short (it scales with the room there), so nobody is
-- shoved into or through geometry
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Weapons = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))

local W = Weapons.list :: any
local Latch = {}

-- (Studio play tests) the last latches: who, the pushes as sent, the room found
Latch.log = {} :: { any }
local function note(e: any)
	table.insert(Latch.log, e)
	if #Latch.log > 20 then table.remove(Latch.log, 1) end
end

-- the swing chain on the server: the link this swing is (1..chain, round again), counted from when the server took the
-- swings: within max(0.75, cd + 0.35) s of the last is the next link (Arsenal's rule); workspace attribute
-- ScytheExtras = false keeps the Scythe to 2
local chain: { [any]: { n: number, t: number } } = setmetatable({}, { __mode = "k" }) :: any
function Latch.swing(f: Rules.Fighter, wid: string, now: number): number?
	local w = W[wid]
	local L = w and w.latch
	if not L then return nil end
	local len = if workspace:GetAttribute("ScytheExtras") == false then math.min(2, L.chain) else L.chain
	local c = chain[f]
	local at = if c and now - c.t < math.max(0.75, w.cd + 0.35) then c.n + 1 else 1
	if at > len then at = 1 end
	chain[f] = { n = at, t = now }
	return at
end
function Latch.link(f: Rules.Fighter): number? local c = chain[f]; return c and c.n end
function Latch.finisher(f: Rules.Fighter, wid: string): boolean
	local L = W[wid] and W[wid].latch
	local c = chain[f]
	return L ~= nil and c ~= nil and c.n == (if workspace:GetAttribute("ScytheExtras") == false then math.min(2, L.chain) else L.chain)
		and c.n > 2 -- (with the extras off there's no finisher: swings 1 and 2 only)
end

-- how much of a push fits: 1 with dist studs clear along dir from here, less with a wall nearer (never under 0.12)
local function room(from: Vector3, dir: Vector3, dist: number): number
	local hit = Fight.castMap(from, dir, dist)
	if not hit then return 1 end
	return math.clamp(((hit.Position - from).Magnitude - 1.5) / dist, 0.12, 1)
end

-- after the latch, the two spring apart. targets: the ones this hit landed on (alive or not: you still spring back off
-- a kill). finisher: the chain's last link
function Latch.apart(f: Rules.Fighter, targets: { Rules.Fighter }, wid: string, finisher: boolean, after: number?)
	local w = W[wid]
	local L = w and w.latch
	if not L or #targets == 0 then return end
	local k = if finisher then L.finisher else 1
	task.delay(after or L.t, function()
		local fr = Fight.root(f)
		if not f.alive or not fr then return end
		local near, best = nil :: Vector3?, math.huge
		local pushed = {}
		for _, t in targets do
			local tr = Fight.root(t)
			if not tr then continue end
			local d = tr.Position - fr.Position
			d = Vector3.new(d.X, 0, d.Z)
			if d.Magnitude < 1e-3 then continue end
			if d.Magnitude < best then near, best = d.Unit, d.Magnitude end
			if t.alive then
				local dir = d.Unit
				local r = room(tr.Position, dir, 8)
				local v = dir * (L.push * k * r) + Vector3.new(0, L.pushUp * k, 0)
				Fight.knock(t, v, wid)
				Rules.tagged(t, f, wid, os.clock()) -- (a fall now is yours)
				table.insert(pushed, { who = t.name, v = v, room = r })
			end
		end
		if near then
			local back = -(near :: Vector3)
			local r = room(fr.Position, back, 10)
			local v = back * (L.back * k * r) + Vector3.new(0, L.backUp * k, 0)
			if f.kind == "player" then (f.ref :: Player):SetAttribute("ACGrace", os.clock() + 0.7) end -- (the hop: the server's say)
			Fight.knock(f, v, wid)
			note({ by = f.name, back = v, room = r, finisher = finisher, targets = pushed, t = os.clock() })
		end
	end)
end

return Latch
