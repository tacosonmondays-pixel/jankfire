--!strict
-- GRAPPLE CHARGES in ranked play (17 Nov 2026, the owner: "For competitive should we limit the grapple to like 2
-- grapples with a short cooldown between recharge?"). the web game's own rule for Jank Royale (shared/royale.js
-- BR.hook = { charges: 2, cd: 8 }, hookCharges / hookSpend): a grab spends a charge, and charges come back one at a
-- time, CD s apart. it counts in a RANKED duel and a PARTY RANKED match only; casual play, training and the hub keep
-- the free grapple.
--   the server counts (server/HookChargeServer.luau; Main's hook check cuts a rope fired with none) and tells the
--   client in attributes; the client predicts (client/HookChargesUI.luau: the pips under the crosshair, the line)
-- pure: times are whatever clock the caller uses (both sides use workspace:GetServerTimeNow())
local HookCharges = {}
HookCharges.CHARGES = 2
HookCharges.CD = 6 -- s (the web's 8 was set for the royale's big map; the owner asked for a short one)
-- QUICKPLAY's auto-lock grapple (19 Nov 2026, the owner: "for quickplay can we try having an auto lock grapple to
-- opponent, like it's on a cooldown?"): in a QUICKPLAY match (not ranked, not a duel), a grapple press that hits no
-- one but is aimed within cone degrees of an opponent in range and in sight ties onto them. one every cd s (the HUD's
-- LOCK pip). on = false turns it off everywhere
HookCharges.AUTO = { on = true, cone = 10, cd = 8 }

export type State = { n: number, t0: number? } -- charges left; when the charge coming back started (nil = full)

function HookCharges.new(): State
	return { n = HookCharges.CHARGES, t0 = nil }
end

-- the charges that have come back by `now`
function HookCharges.update(s: State, now: number)
	while s.n < HookCharges.CHARGES and s.t0 ~= nil and now - (s.t0 :: number) >= HookCharges.CD do
		s.n += 1
		s.t0 = if s.n < HookCharges.CHARGES then (s.t0 :: number) + HookCharges.CD else nil
	end
end

-- a grab: spends one charge; false when there is none
function HookCharges.spend(s: State, now: number): boolean
	HookCharges.update(s, now)
	if s.n <= 0 then return false end
	s.n -= 1
	if s.t0 == nil then s.t0 = now end
	return true
end

-- seconds until the next charge comes back (nil when full), and how far along it is (0..1)
function HookCharges.nextIn(s: State, now: number): (number?, number)
	HookCharges.update(s, now)
	if s.t0 == nil then return nil, 1 end
	local left = HookCharges.CD - (now - (s.t0 :: number))
	return left, math.clamp(1 - left / HookCharges.CD, 0, 1)
end

return HookCharges
