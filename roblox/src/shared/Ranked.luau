--!strict
-- RANKED: the rating maths, the tiers and the placements (roblox/docs/MATCHMAKING.md section 4). pure: no Instances,
-- no services, so the server, the clients and a test can all use it.
--
-- each player has one rating per ranked mode: r (the rating), rd (how unsure the game is of it) and vol (Glicko-2's
-- volatility). a match is one Glicko-2 rating period with one game: the expected result comes from your team's average
-- rating against the other team's average, with their rd combined as a root mean square (the "composite opponent"
-- of "Abstracting Glicko2 for Team Games"), and your own rd decides how far you move. win = 1, loss = 0.
-- the same maths in JS, used to tune the constants: tools/roblox/glicko_sim.mjs (keep the two in step).
local Ranked = {}

Ranked.SEASON = 1
Ranked.MODES = { "1v1", "2v2", "3v3", "4v4" } -- the ranked queues (1v1v1 stays casual)
Ranked.SIZE = { ["1v1"] = 1, ["2v2"] = 2, ["3v3"] = 3, ["4v4"] = 4 }
Ranked.START = { r = 1500, rd = 250, vol = 0.06 }
Ranked.RD_MIN = 80 -- a settled player still moves about 15 to 20 a match
Ranked.RD_MAX = 350
Ranked.TAU = 0.5
Ranked.PLACEMENTS = 5
Ranked.PLACEMENTS_RESET = 3 -- after a season reset
Ranked.PARTY_SPREAD = 400 -- a ranked party's highest and lowest rating in that mode may be this far apart
Ranked.WINDOW = { base = 100, perSecond = 8, openAfter = 90 } -- the search range (rating) by seconds waited

local Q = 173.7178 -- Glicko-2's scale: 400 / ln 10
local PI2 = math.pi * math.pi

export type Rating = { r: number, rd: number, vol: number, n: number?, w: number?, l: number?, peak: number?,
	last: number?, placed: boolean?, need: number? } -- n games, w/l, peak r, last os.time(), need = placements this season

-- a fresh rating for a mode
function Ranked.fresh(): Rating
	return { r = Ranked.START.r, rd = Ranked.START.rd, vol = Ranked.START.vol, n = 0, w = 0, l = 0, peak = 0, last = 0,
		placed = false, need = Ranked.PLACEMENTS }
end

local function g(phi: number): number
	return 1 / math.sqrt(1 + 3 * phi * phi / PI2)
end

-- the composite of a team: the average rating and the root mean square rd
function Ranked.team(list: { { r: number, rd: number } }): (number, number)
	if #list == 0 then return Ranked.START.r, Ranked.START.rd end
	local sr, s2 = 0, 0
	for _, x in list do sr += x.r; s2 += x.rd * x.rd end
	return sr / #list, math.sqrt(s2 / #list)
end

-- the chance a team rated `mine` beats one rated `theirs` (with their combined rd)
function Ranked.expect(mine: number, theirs: number, theirRd: number): number
	return 1 / (1 + math.exp(-g(theirRd / Q) * ((mine - theirs) / Q)))
end

-- one player's new rating after one match. teamR = their team's average, oppR / oppRd = the other team's composite,
-- s = 1 (won) or 0 (lost). returns a new table (r, rd, vol); the caller keeps the counts
function Ranked.update(p: Rating, teamR: number, oppR: number, oppRd: number, s: number): Rating
	local phi, sig = p.rd / Q, p.vol
	local gg = g(oppRd / Q)
	local E = 1 / (1 + math.exp(-gg * ((teamR - oppR) / Q)))
	E = math.clamp(E, 1e-6, 1 - 1e-6)
	local v = 1 / (gg * gg * E * (1 - E))
	local delta = v * gg * (s - E)
	-- the new volatility (Glicko-2 step 5, the Illinois method)
	local a = math.log(sig * sig)
	local tau = Ranked.TAU
	local function f(x: number): number
		local ex = math.exp(x)
		local d2 = phi * phi + v + ex
		return ex * (delta * delta - phi * phi - v - ex) / (2 * d2 * d2) - (x - a) / (tau * tau)
	end
	local A, B = a, 0
	if delta * delta > phi * phi + v then
		B = math.log(delta * delta - phi * phi - v)
	else
		local k = 1
		while f(a - k * tau) < 0 and k < 100 do k += 1 end
		B = a - k * tau
	end
	local fA, fB = f(A), f(B)
	local i = 0
	while math.abs(B - A) > 1e-6 and i < 100 do
		i += 1
		local C = A + (A - B) * fA / (fB - fA)
		local fC = f(C)
		if fC * fB <= 0 then A, fA = B, fB else fA /= 2 end
		B, fB = C, fC
	end
	local sig2 = math.exp(A / 2)
	local phiS = math.sqrt(phi * phi + sig2 * sig2)
	local phi2 = 1 / math.sqrt(1 / (phiS * phiS) + 1 / v)
	local mu2 = (p.r - 1500) / Q + phi2 * phi2 * gg * (s - E)
	phi2 = math.clamp(phi2, Ranked.RD_MIN / Q, Ranked.RD_MAX / Q)
	return { r = 1500 + Q * mu2, rd = Q * phi2, vol = sig2 }
end

-- rd grows back while you don't play (Glicko-2's rule for a period with no games, one period a day)
function Ranked.idle(p: Rating, days: number): number
	if days <= 0 then return p.rd end
	local phi = p.rd / Q
	return math.clamp(Q * math.sqrt(phi * phi + p.vol * p.vol * days), Ranked.RD_MIN, Ranked.RD_MAX)
end

-- a new season: halfway back toward the middle (60% kept), more unsure, a few placements again
function Ranked.seasonReset(p: Rating): Rating
	local out = table.clone(p)
	out.r = 1500 + (p.r - 1500) * 0.6
	out.rd = math.max(p.rd, 180)
	out.placed = false
	out.need = Ranked.PLACEMENTS_RESET
	out.peak = 0
	return out
end

-- how far a ranked search reaches after `waited` seconds (math.huge once it is open)
function Ranked.window(waited: number): number
	if waited >= Ranked.WINDOW.openAfter then return math.huge end
	return Ranked.WINDOW.base + Ranked.WINDOW.perSecond * math.max(0, waited)
end

-- ------------------------------------------------------------------ tiers and divisions
export type Tier = { id: string, name: string, from: number }
-- from = the rating the tier starts at (BRONZE has no floor). 50 rating a division, three divisions (III, II, I).
-- the top tier has none and shows the rating. the colours are the metals in Shared.Ranks (RankedStyle draws them)
Ranked.TIERS = {
	{ id = "bronze", name = "BRONZE", from = -math.huge },
	{ id = "silver", name = "SILVER", from = 1300 },
	{ id = "gold", name = "GOLD", from = 1450 },
	{ id = "platinum", name = "PLATINUM", from = 1600 },
	{ id = "diamond", name = "DIAMOND", from = 1750 },
	{ id = "master", name = "MASTER", from = 1900 },
	{ id = "apex", name = "APEX", from = 2050 },
} :: { Tier }
Ranked.DIV = 50
Ranked.DIVS = { "III", "II", "I" }

export type Rank = {
	placed: boolean, tier: Tier?, tierIndex: number, div: number?, name: string, r: number, step: number,
	lo: number, hi: number, progress: number, -- the division's rating range and where you are in it, 0..1
	games: number, left: number, -- placements still to play (0 once placed)
}

local function round(x: number): number return math.floor(x + 0.5) end

-- the rank a rating shows. placed = false: "PLACEMENTS 2/5" (the tier is still worked out, for the badge's hint)
function Ranked.rankOf(p: Rating?): Rank
	local q: Rating = p or Ranked.fresh()
	local r = round(q.r)
	local ti = 1
	for i, t in Ranked.TIERS do if r >= t.from then ti = i end end
	local tier = Ranked.TIERS[ti]
	local div: number? = nil
	local lo, hi
	if ti == #Ranked.TIERS then
		lo, hi = tier.from, tier.from + 3 * Ranked.DIV
	else
		local nextFrom = Ranked.TIERS[ti + 1].from
		-- BRONZE: III below 1200, II from 1200, I from 1250
		local d = math.clamp(3 - math.floor((nextFrom - 1 - r) / Ranked.DIV), 1, 3)
		div = d
		lo = nextFrom - (4 - d) * Ranked.DIV
		hi = lo + Ranked.DIV
		if ti == 1 and d == 1 then lo = -math.huge end
	end
	local need = q.need or Ranked.PLACEMENTS
	local games = q.n or 0
	local placed = q.placed == true
	local name: string
	if not placed then
		name = ("PLACEMENTS %d/%d"):format(math.min(games, need), need)
	elseif div then
		name = tier.name .. " " .. Ranked.DIVS[div :: number]
	else
		name = tier.name .. " " .. Ranked.comma(r)
	end
	local span = if lo == -math.huge then Ranked.DIV else hi - lo
	local base = if lo == -math.huge then hi - Ranked.DIV else lo
	return {
		placed = placed, tier = tier, tierIndex = ti, div = div, name = name, r = r,
		step = (ti - 1) * 3 + (if div then (div :: number) else 3), -- 1 (BRONZE III) .. 18 (MASTER I), 21 (APEX): for promoted / demoted
		lo = lo, hi = hi, progress = math.clamp((r - base) / span, 0, 1),
		games = games, left = if placed then 0 else math.max(0, need - games),
	}
end

function Ranked.comma(n: number): string
	local s = tostring(math.floor(math.abs(n) + 0.5))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	if out:sub(1, 1) == "," then out = out:sub(2) end
	return (if n < 0 then "-" else "") .. out
end

-- ------------------------------------------------------------------ one finished match for one player
-- apply a result to a stored rating in place and return what the screens show:
-- { mode, won, before, after, delta, placedNow, promoted, demoted, rankBefore, rankAfter }
function Ranked.apply(p: Rating, teamR: number, oppR: number, oppRd: number, won: boolean, now: number): any
	local before = Ranked.rankOf(p)
	local r0 = p.r
	local new = Ranked.update(p, teamR, oppR, oppRd, if won then 1 else 0)
	p.r, p.rd, p.vol = new.r, new.rd, new.vol
	p.n = (p.n or 0) + 1
	if won then p.w = (p.w or 0) + 1 else p.l = (p.l or 0) + 1 end
	p.last = now
	local wasPlaced = p.placed == true
	if not wasPlaced and (p.n or 0) >= (p.need or Ranked.PLACEMENTS) then p.placed = true end
	if p.placed then p.peak = math.max(p.peak or 0, p.r) end
	local after = Ranked.rankOf(p)
	return {
		won = won, before = round(r0), after = round(p.r), delta = round(p.r) - round(r0),
		placedNow = p.placed == true and not wasPlaced,
		promoted = wasPlaced and after.step > before.step, demoted = wasPlaced and after.step < before.step,
		rankBefore = before, rankAfter = after,
	}
end

-- the best rank among a player's modes (for the card): the placed mode with the highest rating, else the mode
-- closest to being placed, else nil (unranked)
function Ranked.best(modes: { [string]: Rating }?): (string?, Rating?)
	if not modes then return nil, nil end
	local bestMode, bestR, bestPlaced = nil, nil, false
	for _, m in Ranked.MODES do
		local q = modes[m]
		if q and (q.n or 0) > 0 then
			local placed = q.placed == true
			if not bestR
				or (placed and not bestPlaced)
				or (placed == bestPlaced and placed and q.r > (bestR :: Rating).r)
				or (placed == bestPlaced and not placed and (q.n or 0) > ((bestR :: Rating).n or 0)) then
				bestMode, bestR, bestPlaced = m, q, placed
			end
		end
	end
	return bestMode, bestR
end

return Ranked
