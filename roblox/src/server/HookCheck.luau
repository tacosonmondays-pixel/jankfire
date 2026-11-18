--!strict
-- the server's say on a grapple: pure checks (tests run them outside Roblox). the client moves itself, like the web
-- game, but it only gets to hang off points that are real, in range and in sight, and not a hundred times a second
local Config = require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("Config"))

local HookCheck = {}

local function finite(x: number): boolean return x == x and x > -math.huge and x < math.huge end

-- reason it's refused, or nil if it's fine. dist = from the player's root to the point; seenDist = how far a ray from
-- the player's head toward the point got before it hit something (nil = nothing hit)
function HookCheck.point(px: unknown, py: unknown, pz: unknown): string?
	if type(px) ~= "number" or type(py) ~= "number" or type(pz) ~= "number" then return "bad point" end
	if not (finite(px) and finite(py) and finite(pz)) then return "bad point" end
	-- (huge but finite: its distance overflows to inf before the range check, and the ray gets a NaN direction)
	if math.abs(px) > 1e6 or math.abs(py) > 1e6 or math.abs(pz) > 1e6 then return "bad point" end
	return nil
end

function HookCheck.reach(dist: number, toPoint: number, seenDist: number?): string?
	if dist > Config.hook.range + Config.check.hookSlack then return "out of range" end
	if seenDist == nil then return "nothing there" end
	if math.abs(seenDist - toPoint) > 4 then return "blocked" end -- something in the way (or the point is in thin air)
	return nil
end

-- a hook on a person (18 Nov 2026, "grapple onto people"): dist = from the hooker's root to their chest, seen = whether
-- the hooker's head sees them now or a moment ago (Fight.sees looks back along their trail, for lag)
function HookCheck.body(dist: number, seen: boolean): string?
	if dist > Config.hook.range + Config.check.hookSlack then return "out of range" end
	if not seen then return "blocked" end
	return nil
end

-- a sliding window of request times per player
function HookCheck.rate(times: { number }, now: number): boolean
	while #times > 0 and now - times[1] > 1 do table.remove(times, 1) end
	if #times >= Config.check.hookRate then return false end
	table.insert(times, now)
	return true
end

return HookCheck
