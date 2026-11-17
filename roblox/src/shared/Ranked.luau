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
	last: number?, placed: boolean?, need: number?, lp: number? }
-- n games, w/l, peak (the best RP), last os.time(), need = placements this season, lp = the ladder RP once placed

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
	out.lp = nil -- (placements again: the RP comes back from them)
	return out
end

-- how far a ranked search reaches after `waited` seconds (math.huge once it is open)
function Ranked.window(waited: number): number
	if waited >= Ranked.WINDOW.openAfter then return math.huge end
	return Ranked.WINDOW.base + Ranked.WINDOW.perSecond * math.max(0, waited)
end


-- ------------------------------------------------------------------ the ladder: tiers, divisions, rank points
-- (17 Nov, the owner: "display your rank with a bar and a number on the right of the bar with how much progression
-- you're missing before next rank up like 34/100"). the rank you see is a ladder of RANK POINTS (RP): 100 a division,
-- BRONZE III at 0, MASTER I ending at 1800, APEX from 1800 with no cap. the Glicko-2 rating above (the MMR) is hidden:
-- it decides matchmaking and how many RP a match is worth. each tier has three divisions, III then II then I.
-- the colours are the metals in Shared.Ranks (RankedStyle draws them)
export type Tier = { id: string, name: string }
Ranked.TIERS = {
	{ id = "bronze", name = "BRONZE" },
	{ id = "silver", name = "SILVER" },
	{ id = "gold", name = "GOLD" },
	{ id = "platinum", name = "PLATINUM" },
	{ id = "diamond", name = "DIAMOND" },
	{ id = "master", name = "MASTER" },
	{ id = "apex", name = "APEX" },
} :: { Tier }
Ranked.DIVS = { "III", "II", "I" }
Ranked.APEX_AT = 1800 -- RP where APEX starts (18 divisions under it)
Ranked.PLACE_CAP = 1490 -- placements land at most here (DIAMOND I, 90/100)
Ranked.RP = { win = 20, loss = 20, pull = 10, winMin = 8, winMax = 40, lossMin = 6, lossMax = 40 }

local function round(x: number): number return math.floor(x + 0.5) end

-- where the MMR says you belong on the ladder, in RP: 50 rating = 100 RP, BRONZE III's 0 at rating 1150 (so GOLD II
-- starts at 1500 and APEX at 2050, the first build's tier table)
function Ranked.ladderOf(r: number): number
	return math.max(0, (r - 1150) * 2)
end

export type Rank = {
	placed: boolean, tier: Tier, tierIndex: number, div: number?, name: string, r: number, lp: number, rp: number,
	step: number, progress: number, games: number, left: number,
	-- lp = your ladder RP; rp = the points inside your division (0..99; APEX: the points over 1800); progress 0..1;
	-- step = 1 (BRONZE III) .. 18 (MASTER I), 19 = APEX (promoted / demoted); left = placements still to play
}

-- the rank a stored rating shows
function Ranked.rankOf(p: Rating?): Rank
	local q: any = p or Ranked.fresh()
	local placed = q.placed == true
	local lp = if type(q.lp) == "number" then q.lp else (if placed then Ranked.ladderOf(q.r) else Ranked.ladderOf(q.r))
	lp = math.max(0, math.floor(lp))
	local step = math.min(19, lp // 100 + 1)
	local ti = math.min(#Ranked.TIERS, (step - 1) // 3 + 1)
	local tier = Ranked.TIERS[ti]
	local div: number? = if step <= 18 then (step - 1) % 3 + 1 else nil
	local rp = if div then lp % 100 else lp - Ranked.APEX_AT
	local need = q.need or Ranked.PLACEMENTS
	local games = q.n or 0
	local name: string
	if not placed then
		name = ("PLACEMENTS %d/%d"):format(math.min(games, need), need)
	elseif div then
		name = tier.name .. " " .. Ranked.DIVS[div :: number]
	else
		name = tier.name
	end
	return {
		placed = placed, tier = tier, tierIndex = ti, div = div, name = name, r = round(q.r), lp = lp, rp = rp, step = step,
		progress = if div then rp / 100 else 1, games = games, left = if placed then 0 else math.max(0, need - games),
	}
end

function Ranked.comma(n: number): string
	local s = tostring(math.floor(math.abs(n) + 0.5))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	if out:sub(1, 1) == "," then out = out:sub(2) end
	return (if n < 0 then "-" else "") .. out
end

-- the RP a placed match is worth: about 20 either way, pulled toward where the MMR says you belong (MMR above your
-- rank: gain more, lose less), then clamped (a win 8..40, a loss -6..-40)
function Ranked.points(lp: number, r: number, won: boolean): number
	local pull = math.clamp((Ranked.ladderOf(r) - lp) / Ranked.RP.pull, -15, 15)
	if won then
		return math.clamp(round(Ranked.RP.win + pull), Ranked.RP.winMin, Ranked.RP.winMax)
	end
	return -math.clamp(round(Ranked.RP.loss - pull), Ranked.RP.lossMin, Ranked.RP.lossMax)
end

-- ------------------------------------------------------------------ one finished match for one player
-- apply a result to a stored rating in place (the hidden MMR, then the RP) and return what the screens show:
-- { won, delta (RP; nil during placements), rpBefore, rpAfter, placedNow, promoted, demoted, mmrDelta,
--   rankBefore, rankAfter }
function Ranked.apply(p: Rating, teamR: number, oppR: number, oppRd: number, won: boolean, now: number): any
	local q: any = p
	local before = Ranked.rankOf(p)
	local r0 = p.r
	local new = Ranked.update(p, teamR, oppR, oppRd, if won then 1 else 0)
	p.r, p.rd, p.vol = new.r, new.rd, new.vol
	p.n = (p.n or 0) + 1
	if won then p.w = (p.w or 0) + 1 else p.l = (p.l or 0) + 1 end
	p.last = now
	local wasPlaced = p.placed == true
	local delta: number? = nil
	if not wasPlaced then
		if (p.n or 0) >= (p.need or Ranked.PLACEMENTS) then
			p.placed = true
			q.lp = math.min(Ranked.PLACE_CAP, math.floor(Ranked.ladderOf(p.r) / 10) * 10)
		end
	else
		local lp = if type(q.lp) == "number" then q.lp else Ranked.ladderOf(r0)
		delta = Ranked.points(lp, p.r, won)
		q.lp = math.max(0, lp + (delta :: number))
		delta = q.lp - lp -- (what really moved: 0 RP is a floor)
	end
	if p.placed then p.peak = math.max(p.peak or 0, q.lp or 0) end
	local after = Ranked.rankOf(p)
	return {
		won = won, delta = delta, rpBefore = before.rp, rpAfter = after.rp, mmrDelta = round(p.r) - round(r0),
		placedNow = p.placed == true and not wasPlaced,
		promoted = wasPlaced and after.step > before.step, demoted = wasPlaced and after.step < before.step,
		rankBefore = before, rankAfter = after,
	}
end

-- the best rank among a player's modes (for the card): the placed mode with the most RP, else the mode closest to
-- being placed, else nil (unranked)
function Ranked.best(modes: { [string]: Rating }?): (string?, Rating?)
	if not modes then return nil, nil end
	local bestMode, bestR, bestPlaced = nil, nil, false
	local function lpOf(q: any): number return if type(q.lp) == "number" then q.lp else Ranked.ladderOf(q.r) end
	for _, m in Ranked.MODES do
		local q = modes[m]
		if q and (q.n or 0) > 0 then
			local placed = q.placed == true
			if not bestR
				or (placed and not bestPlaced)
				or (placed == bestPlaced and placed and lpOf(q) > lpOf(bestR))
				or (placed == bestPlaced and not placed and (q.n or 0) > ((bestR :: Rating).n or 0)) then
				bestMode, bestR, bestPlaced = m, q, placed
			end
		end
	end
	return bestMode, bestR
end

return Ranked
