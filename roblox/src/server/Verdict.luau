--!strict
-- the Scales of Justice's verdict (weapons batch D; web shared/verdict.js, WEAPONS.md "Scales of Justice"): how hard a
-- hit lands on the one you hit, by how guilty they are against you. guilt g starts at 0:
--   their K/D better than yours +1, worse -1; their kills above yours +1 (top of the place with kills: +1 more), below
--   yours -1; your team behind theirs +1, ahead -1; their streak 3+ +1, 5+ +2; they killed you last +2.
--   dummies and bots: only the streak and the revenge count
-- the multiplier: g > 0: min(3, 1 + 0.4 g); g < 0: max(0.4, 1 - 0.25 |g|); g = 0: x1
local Fight = require(script.Parent:WaitForChild("Fight"))

local V = {}

local streak: { [any]: number } = setmetatable({}, { __mode = "k" }) :: any
local lastKiller: { [any]: any } = setmetatable({}, { __mode = "k" }) :: any
Fight.onKill(function(info: any)
	local v, k = info.v, info.k
	if v then streak[v] = 0 end
	if k and k ~= v then
		streak[k] = (streak[k] or 0) + 1
		if v then lastKiller[v] = k end
	end
end)

local function teamOf(f: any): any
	return if f.kind == "player" then (f.ref :: Player):GetAttribute("Team") else nil
end
local function kd(f: any): number return (f.kills or 0) / math.max(1, f.deaths or 0) end

function V.guilt(by: any, t: any): number
	local g = 0
	if t.kind == "player" and by.kind == "player" then
		if kd(t) > kd(by) then g += 1 elseif kd(t) < kd(by) then g -= 1 end
		if t.kills > by.kills then g += 1 elseif t.kills < by.kills then g -= 1 end
		-- top of the board (the players fighting in the same place), with kills
		if t.kills > 0 then
			local top = true
			local zone = (t.ref :: Player):GetAttribute("Zone")
			for _, o in Fight.all do
				if o ~= t and o.kind == "player" and (o.ref :: Player):GetAttribute("Zone") == zone and o.kills >= t.kills then top = false; break end
			end
			if top then g += 1 end
		end
		local tb, tt = teamOf(by), teamOf(t)
		if tb ~= nil and tt ~= nil and tb ~= tt then
			local mine, theirs = 0, 0
			for _, o in Fight.all do
				if o.kind ~= "player" then continue end
				local to = teamOf(o)
				if to == tb then mine += o.kills elseif to == tt then theirs += o.kills end
			end
			if mine < theirs then g += 1 elseif mine > theirs then g -= 1 end
		end
	end
	local s = streak[t] or 0
	if s >= 5 then g += 2 elseif s >= 3 then g += 1 end
	if lastKiller[by] == t then g += 2 end
	return g
end

function V.mult(by: any, t: any): number
	local g = V.guilt(by, t)
	if g > 0 then return math.min(3, 1 + 0.4 * g) end
	if g < 0 then return math.max(0.4, 1 - 0.25 * -g) end
	return 1
end

return V
