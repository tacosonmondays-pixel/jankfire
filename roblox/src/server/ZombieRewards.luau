--!strict
-- ZOMBIES: what an extraction pays (27 Nov 2026; roblox/docs/ZOMBIES.md 4.2). The owner: "If you extract at higher
-- floors you can leave and gain rewards ... rewards CAN be bags sprays and crates but rarely chances increase
-- significantly if you get to way higher rounds". Server-only: ZombieExtract calls it on the server's own extraction
-- event (and on a game over), never on anything a client says. Once per player per game: every grant carries a receipt
-- id `zmx:<game guid>:<user id>:<what>` (zmo: for a game over's XP) that Quests.grant, Stats.gift and Loot.grant each
-- keep, so a retry or a second call pays nothing twice.
--   ZombieRewards.track(m)                    the anti-farming numbers for a member (ZombieExtract fills them)
--   ZombieRewards.eligible(g, m) -> ok, why   a human with a real share of the fight, up and active half the game
--   ZombieRewards.extract(g, m) -> result     Brass, XP and the rolls (ZM.XR, the extraction round's band)
--   ZombieRewards.over(g, m) -> result        a game over's XP (10 a round, 250 at most)
-- Studio is dry unless ZombieRewards.REAL (the hook's "xreal" op): everything is rolled and shown, nothing is written,
-- because a Studio test plays on the tester's real save.
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))

local ZR = {}
ZR.REAL = not RunService:IsStudio()
ZR.GATE_OFF = false -- (the hook's "xelig" op: a Studio test that jumps rounds can't pass the time checks)
local rng = Random.new()

-- the modules that write a save (required lazily: they're the same copies their own scripts started)
local Q: any, St: any, L: any = nil, nil, nil
local function mods()
	if Q then return end
	local here = script.Parent
	local ok1, q = pcall(require, here:WaitForChild("Quests"))
	local ok2, s = pcall(require, here:WaitForChild("Stats"))
	local ok3, l = pcall(require, here:WaitForChild("Loot"))
	Q = if ok1 then q else nil
	St = if ok2 then s else nil
	L = if ok3 then l else nil
end

export type Track = { t: number, up: number, act: number, dmg: number, last: Vector3?, hitT: number, wdmg: { [string]: number } }
function ZR.track(m: any): Track
	local x = m.xt
	if not x then
		x = { t = 0, up = 0, act = 0, dmg = 0, last = nil, hitT = -math.huge, wdmg = {} }
		m.xt = x
	end
	return x
end

-- a human, at least 15% of the squad's damage to zombies or of its kills, up half the game, active half of it
function ZR.eligible(g: any, m: any): (boolean, string?)
	if not m.p then return false, "bot" end
	if ZR.GATE_OFF then return true, nil end
	local G = ZM.XR.gate
	local x = ZR.track(m)
	local dmg, kills = 0, 0
	for _, o in g.members do dmg += ZR.track(o).dmg; kills += o.kills end
	local share = math.max(if dmg > 0 then x.dmg / dmg else 0, if kills > 0 then m.kills / kills else 0)
	if share < G.share then return false, "share" end
	if x.t <= 0 or x.up / x.t < G.up then return false, "up" end
	if x.act / x.t < G.active then return false, "active" end
	return true, nil
end

local function rid(g: any, m: any, what: string): string
	return "zmx:" .. tostring(g.guid) .. ":" .. tostring(m.p and m.p.UserId or 0) .. ":" .. what
end

-- one extracted player's rewards. result: { n, band, ok (eligible), why, brass, xp, rolls = { { k, p, hit, got, wrap? } },
-- dry, notes }
function ZR.extract(g: any, m: any): any
	mods()
	local n = g.n
	local b = ZM.xBand(n)
	local res: any = { n = n, ok = false, brass = 0, xp = 0, rolls = {}, dry = not ZR.REAL, notes = {} }
	if not b then res.why = "round"; return res end
	res.band = b.from
	local ok, why = ZR.eligible(g, m)
	res.ok, res.why = ok, why
	local wraps = ZM.xWraps(n)
	local p = m.p :: Player
	for _, k in ZM.XR.rolls do
		if k == "wrap" and #wraps == 0 then continue end
		local r: any = { k = k, p = b[k] or 0, hit = false, got = false }
		table.insert(res.rolls, r)
		if not ok then continue end
		r.hit = rng:NextNumber() < r.p
		if r.hit and k == "wrap" then
			-- which one: by weight among the wraps open at this round that the player hasn't got (on every gun)
			local pool, total = {}, 0
			for _, w in wraps do
				if not (L and type(L.owns) == "function" and L.owns(p, "wrap", w.id)) then table.insert(pool, w); total += (w.w or 1) end
			end
			if #pool == 0 then r.owned = true; r.hit = false
			else
				local t = rng:NextNumber() * total
				local pick = pool[#pool]
				for _, w in pool do t -= (w.w or 1); if t <= 0 then pick = w; break end end
				r.wrap = pick.id
			end
		end
	end
	if not ok then return res end
	res.brass, res.xp = b.brass, b.xp
	if not ZR.REAL then return res end
	-- Brass (the 300-a-day cap across every caller stands: over it, it says so)
	if Q and type(Q.grant) == "function" then
		local okB, whyB = Q.grant(p, b.brass, "zombies extraction", rid(g, m, "brass"))
		if not okB then res.brass = 0; table.insert(res.notes, "brass " .. tostring(whyB)) end
	end
	if St and type(St.gift) == "function" then
		local okX, whyX = St.gift(p, { xp = b.xp }, rid(g, m, "xp"))
		if not okX then res.xp = 0; table.insert(res.notes, "xp " .. tostring(whyX)) end
	end
	for _, r in res.rolls do
		if not r.hit or not L then continue end
		if r.k == "wrap" then
			r.got = r.wrap ~= nil and L.grant(p, "zmwrap:" .. r.wrap, rid(g, m, "wrap")) == true
		else
			r.got = L.grant(p, r.k, rid(g, m, r.k)) == true
		end
		if not r.got then table.insert(res.notes, r.k .. " not written") end
	end
	return res
end

-- a game over (or left behind on an extraction): 10 XP a round reached, 250 at most, through the same checks
function ZR.over(g: any, m: any): any
	mods()
	local res: any = { n = g.n, ok = false, xp = 0, dry = not ZR.REAL }
	local ok, why = ZR.eligible(g, m)
	res.ok, res.why = ok, why
	if not ok or g.n < 1 then return res end
	res.xp = math.min(ZM.XR.overXpMax, ZM.XR.overXp * g.n)
	if ZR.REAL and St and type(St.gift) == "function" and m.p then
		local okX = St.gift(m.p, { xp = res.xp }, "zmo:" .. tostring(g.guid) .. ":" .. tostring(m.p.UserId))
		if not okX then res.xp = 0 end
	end
	return res
end

return ZR
