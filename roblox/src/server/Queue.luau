--!strict
-- QUEUE: the Play screen's matchmaker inside one server (roblox/docs/MATCHMAKING.md section 3). an entry is a party (a
-- solo player is a party of one) waiting for one mode, casual or ranked. Queue.step() tries to make matches; Party.luau
-- adds and drops entries and starts what is formed.
--   * parties are packed whole into the mode's teams (a small backtracking search), never split
--   * casual: the oldest entries that fill the teams go, first come first served
--   * ranked: the oldest entry is the anchor; another entry may join it only if both entries' search windows
--     (Ranked.window: 100 + 8 per second waited, open after 90 s) cover the gap between their ratings, and the teams'
--     average ratings end up within the narrowest window in the match
-- Queue.form is pure (entries in, teams out), so it can be tested without a server.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Ranked = require(Shared:WaitForChild("Ranked"))
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))

local Queue = {}

export type Entry = {
	key: string, mode: string, ranked: boolean, since: number, size: number, rating: number,
	owner: any, -- the party (or a test's stand-in group)
	state: string, -- "search" | "found" (formed, counting down: out of the search)
}

local lists: { [string]: { Entry } } = {}

function Queue.key(mode: string, ranked: boolean): string
	return (if ranked then "ranked:" else "casual:") .. mode
end

function Queue.add(e: Entry)
	local l = lists[e.key] or {}
	lists[e.key] = l
	if not table.find(l, e) then table.insert(l, e) end
	e.state = "search"
end

function Queue.remove(e: Entry)
	local l = lists[e.key]
	if not l then return end
	local i = table.find(l, e)
	if i then table.remove(l, i) end
end

function Queue.entries(key: string?): { Entry }
	if key then return lists[key] or {} end
	local out = {}
	for _, l in lists do for _, e in l do table.insert(out, e) end end
	return out
end

-- the narrowest window among these entries, at time `now`
local function narrowest(es: { Entry }, now: number): number
	local w = math.huge
	for _, e in es do w = math.min(w, Ranked.window(now - e.since)) end
	return w
end

-- try to fill `teams` teams of `size` with whole entries from `cands` (cands[1], the anchor, must be in). ok(teams)
-- has the last word on a full fill (ranked balance). returns the teams or nil
local function pack(cands: { Entry }, teams: number, size: number, ok: (({ { Entry } }) -> boolean)?): { { Entry } }?
	local out: { { Entry } } = {}
	local fill: { number } = {}
	for t = 1, teams do out[t] = {}; fill[t] = 0 end
	local need, total, steps = teams * size, 0, 0
	local function rec(i: number): boolean
		steps += 1
		if steps > 4000 then return false end
		if total == need then return ok == nil or (ok :: any)(out) end
		if i > #cands then return false end
		local e = cands[i]
		local triedEmpty = false
		for t = 1, teams do
			if fill[t] + e.size <= size then
				-- (empty teams are all alike: trying the first one is enough)
				if fill[t] == 0 then
					if triedEmpty then continue end
					triedEmpty = true
				end
				table.insert(out[t], e); fill[t] += e.size; total += e.size
				if rec(i + 1) then return true end
				table.remove(out[t]); fill[t] -= e.size; total -= e.size
			end
		end
		if i == 1 then return false end -- the anchor goes, or nothing does
		return rec(i + 1)
	end
	if rec(1) then return out end
	return nil
end

-- a free-for-all queue (an entry with ffa: QUICKPLAY, Shared.PlayConfig): whole parties, min..max players, each entry
-- its own list in what comes back (Party.luau's vote then picks the mode; Modes.luau makes every player their own side). it goes at max seats, or at min
-- once its oldest entry has waited fill s (a party of min or more may go on its own then). ranked: the oldest entry is
-- the anchor and every other must sit inside both search windows, like the duels. pure
local function formFfa(es: { Entry }, m: any, ranked: boolean, now: number): { { Entry } }?
	local open = {}
	for _, e in es do if e.state == "search" and e.size <= (m.size or PlayConfig.PARTY_MAX) then table.insert(open, e) end end
	table.sort(open, function(a, b) return a.since < b.since end)
	local lo, hi, fill = m.min or 2, m.max or 8, m.fill or 15
	for ai, anchor in open do
		local pick, seats = { anchor }, anchor.size
		local wa = Ranked.window(now - anchor.since)
		for j, e in open do
			if j ~= ai and seats + e.size <= hi then
				if not ranked or math.abs(e.rating - anchor.rating) <= math.min(wa, Ranked.window(now - e.since)) then
					table.insert(pick, e)
					seats += e.size
				end
			end
		end
		-- (ranked: never one party alone, it would let friends farm each other)
		if (seats >= hi or (seats >= lo and now - anchor.since >= fill)) and (not ranked or #pick >= 2) then
			local out = {}
			for _, e in pick do table.insert(out, { e }) end
			return out
		end
	end
	return nil
end

-- two sides from whole entries (parties kept together), each at most cap, at most one apart, every entry seated. the
-- most even split, or nil when there is none (a team mode: the classic team modes in QUICKPLAY and party matches). pure
function Queue.split(es: { Entry }, cap: number): { { Entry } }?
	local n = #es
	if n == 0 or n > 12 then return nil end
	local best: { { Entry } }? = nil
	local bestGap = math.huge
	for mask = 0, 2 ^ n - 1 do
		local a, b = 0, 0
		for i = 1, n do
			if bit32.btest(mask, 2 ^ (i - 1)) then b += es[i].size else a += es[i].size end
		end
		if a >= 1 and b >= 1 and a <= cap and b <= cap and math.abs(a - b) <= 1 and math.abs(a - b) < bestGap then
			local A, B = {}, {}
			for i = 1, n do
				if bit32.btest(mask, 2 ^ (i - 1)) then table.insert(B, es[i]) else table.insert(A, es[i]) end
			end
			best, bestGap = { A, B }, math.abs(a - b)
			if bestGap == 0 then break end
		end
	end
	return best
end

-- a party's pick with FILL FROM QUICKPLAY (the MODES tab's PARTY card; PlayConfig QUICKPLAY): the oldest party waiting
-- for this mode is the anchor. the other parties waiting for it, then the quickplay queue (oldest first), top it up with
-- whole parties to the mode's head-count (PlayConfig.counts). it goes full, or at the least once the anchor has waited
-- fill s. a team mode also needs its seats to split into two sides (Queue.split), else it waits. ranked: everyone inside
-- the anchor's and their own search windows, like the duels. pure (quick = the quickplay queue's entries)
local function formFill(es: { Entry }, quick: { Entry }, m: any, ranked: boolean, now: number): { { Entry } }?
	local lo, hi = PlayConfig.counts(m.id)
	local own = {}
	for _, e in es do if e.state == "search" and e.size <= PlayConfig.PARTY_MAX then table.insert(own, e) end end
	if #own == 0 then return nil end
	table.sort(own, function(a, b) return a.since < b.since end)
	local anchor = own[1]
	local pool = {}
	for i = 2, #own do table.insert(pool, own[i]) end
	local qs = {}
	for _, e in quick do if e.state == "search" and e.size <= PlayConfig.PARTY_MAX then table.insert(qs, e) end end
	table.sort(qs, function(a, b) return a.since < b.since end)
	for _, e in qs do table.insert(pool, e) end
	local pick, seats = { anchor }, anchor.size
	local wa = Ranked.window(now - anchor.since)
	for _, e in pool do
		if seats + e.size <= hi and (not ranked or math.abs(e.rating - anchor.rating) <= math.min(wa, Ranked.window(now - e.since))) then
			table.insert(pick, e)
			seats += e.size
		end
	end
	local waited = now - anchor.since >= (m.fill or 15)
	if not (seats >= hi or (seats >= lo and waited)) then return nil end
	if ranked and #pick < 2 then return nil end -- (ranked: never one party alone)
	if m.sides == 2 then
		-- the newest additions wait for the next match until the rest split into two sides; the party alone (one entry:
		-- Party.luau splits its members over the sides) only once it has waited
		while #pick > 1 do
			local s = Queue.split(pick, PlayConfig.PARTY_MAX)
			local n = 0
			for _, e in pick do n += e.size end
			if s and n >= lo then return s end
			table.remove(pick)
		end
		return if anchor.size >= lo and waited then { pick } else nil
	end
	local out = {}
	for _, e in pick do table.insert(out, { e }) end
	return out
end

-- the teams for one match from this queue's searching entries (oldest first), or nil. pure
function Queue.form(es: { Entry }, mode: string, ranked: boolean, now: number): { { Entry } }?
	local m = PlayConfig.byId[mode]
	if not m then return nil end
	-- a classic mode picked by a party (PARTY card): its own queue topped up from quickplay's. quickplay itself and
	-- any other free-for-all entry: formFfa
	if (m :: any).ladder == "party" and not (m :: any).quick then return formFill(es, lists[Queue.key(PlayConfig.QUICKPLAY, ranked)] or {}, m, ranked, now) end
	if (m :: any).ffa then return formFfa(es, m, ranked, now) end
	local open = {}
	for _, e in es do if e.state == "search" and e.size <= m.size then table.insert(open, e) end end
	table.sort(open, function(a, b) return a.since < b.since end)
	local seats = 0
	for _, e in open do seats += e.size end
	if seats < m.teams * m.size then return nil end
	for ai, anchor in open do
		local cands = { anchor }
		local wa = Ranked.window(now - anchor.since)
		for j, e in open do
			if j ~= ai then
				if not ranked then
					table.insert(cands, e)
				else
					local w = math.min(wa, Ranked.window(now - e.since))
					if math.abs(e.rating - anchor.rating) <= w then table.insert(cands, e) end
				end
			end
		end
		local balance: (({ { Entry } }) -> boolean)? = nil
		if ranked then
			balance = function(teams: { { Entry } }): boolean
				local all, avg = {}, {}
				for t, list in teams do
					local sum, n = 0, 0
					for _, e in list do sum += e.rating * e.size; n += e.size; table.insert(all, e) end
					avg[t] = if n > 0 then sum / n else 0
				end
				local lo, hi = math.huge, -math.huge
				for _, a in avg do lo = math.min(lo, a); hi = math.max(hi, a) end
				return hi - lo <= narrowest(all, now)
			end
		end
		local teams = pack(cands, m.teams, m.size, balance)
		if teams then return teams end
	end
	return nil
end

-- one pass over every queue: each formed match goes to onFormed(key, teams). its entries are marked "found" (the
-- caller drops them, or puts them back with Queue.back if the match couldn't start)
function Queue.step(now: number, onFormed: (string, { { Entry } }) -> ())
	-- (the quickplay queues last: a party's pick with FILL FROM QUICKPLAY takes its fillers first)
	local keys = {}
	for key in lists do table.insert(keys, key) end
	table.sort(keys, function(a, b)
		local qa, qb = string.find(a, PlayConfig.QUICKPLAY, 1, true) ~= nil, string.find(b, PlayConfig.QUICKPLAY, 1, true) ~= nil
		if qa ~= qb then return qb end
		return a < b
	end)
	for _, key in keys do
		local l = lists[key]
		local mode = string.match(key, ":(.+)$") :: string
		local ranked = string.sub(key, 1, 7) == "ranked:"
		for _ = 1, 8 do -- (several matches a pass from one queue, if the pool allows)
			local teams = Queue.form(l, mode, ranked, now)
			if not teams then break end
			for _, list in teams do for _, e in list do e.state = "found" end end
			onFormed(key, teams)
		end
	end
end

-- a found entry goes back to searching (its match fell through); it keeps its place by its old `since`
function Queue.back(e: Entry)
	e.state = "search"
	Queue.add(e)
end

return Queue
