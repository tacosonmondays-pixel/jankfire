--!strict
-- where a player is, as the server decides it: one helper for everything that changes by zone (the owner, 17 Nov
-- 2026: "training room should also have no cooldown on stuff since its for training", and "when you're in the
-- training hub you're free to use any weapon"). it asks Matches.zoneOf, the live answer the server's own "Zone"
-- attribute is made from (Matches sets it 6 times a second; a client can't write it): "match" while you're in a
-- match, "training" in the training hall (with its back lot and basement), "playground" in the playground off the
-- hall, "hub" anywhere else. until Matches is up (its first tick) the attribute stands in; nothing here trusts a client
--   Zones.of(p)        the zone name
--   Zones.training(p)  the training hall, its back lot and basement, or the playground: free practice (Utility's
--                      items cost nothing; Loadout's try-anything layer)
local Zones = {}

Zones.TRAINING = { training = true, playground = true } :: { [string]: boolean }

local Matches: any = nil
function Zones.of(p: Player): string
	if not Matches then
		local m = script.Parent:FindFirstChild("Matches")
		if m and m:IsA("ModuleScript") then
			local ok, M = pcall(require, m)
			if ok and type(M) == "table" then Matches = M end
		end
	end
	if Matches and type(Matches.zoneOf) == "function" then
		local ok, z = pcall(Matches.zoneOf, p)
		if ok and type(z) == "string" then return z end
	end
	return tostring(p:GetAttribute("Zone") or "hub")
end

function Zones.training(p: Player): boolean
	return Zones.TRAINING[Zones.of(p)] == true
end

return Zones
