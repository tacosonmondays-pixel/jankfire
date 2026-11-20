--!strict
-- STATS: what each player did in real matches, their XP (Shared.Ranks: the web game's level, our tiers), the look of
-- their player card and whether others may see their numbers. one session-locked save per player (Profiles.luau, the
-- loot save's layer, its own store "JankfireStats_v1", so a stats write can never touch what you own).
-- only matches count: both players in the same match on opposite teams, the round live. the hub, the training hall and
-- its dummies count for nothing (the web game's lobby and training mode give no XP either).
--   totals: k d (kills, deaths), m w (matches, wins), rp rw (rounds played, won), sh (attacks: a shot or a swing),
--           hi (attacks that hurt somebody), hc hs (hurts, of them headshots: headshot % = hs / hc, the web game's
--           hsh / hits), hk (kills whose last hit was a headshot), dmg, best (kill streak in one match without dying),
--           time (s alive in live rounds)
--   wpn[weapon] = { k, s, h, hs, t, dmg }: kills, attacks, attacks that hurt, headshots, seconds held, damage
--   recent: the last 10 matches, newest first { t, mode, map, r = "W"|"L", k, d, w (the weapon held longest), sc, dmg }
--   look = { border, banner, title } (Shared.CardStyles; free ones or ones you own: Loot.owns), private = hide my numbers
--   log: the last LOG matches, newest first, one record each keyed by the match's key (Matches: unique across servers)
--        { id = key, t (its end), mode, map, team, ranked?, r, k, d, rp, rw, xp, foes = { userIds }, mates = { userIds },
--        x = the cheater it was undone for }. what a cheat restore reads (below)
--   fixed[matchKey] = cheater (the matches already undone: twice is once), voids[since] = when (resets already done),
--   reset = false | { t, since } (shown on the card), backup = false | the numbers before the reset (undoRestore)
-- XP: +20 a kill on a player, +50 a round won, 2 a minute of live match time (web room.js).
--   mx[weapon] = xp: WEAPON MASTERY (Shared.Mastery, server/MasteryXp.luau): a kill 100 (+25 headshot), an assist 50, a
--   round or the match won 50 (to the weapon held longest in it). the same matches count as for everything here (never
--   a ghost or a dev match, never a dummy); a cheat restore takes it with the rest
--
-- CHEAT RESTORES (the owner, 17 Nov: "If someone is caught cheating give back any ranked stuff or stats!!"). the
-- anti-cheat calls Stats.restoreFor(cheaterUserId, since) when a cheater is confirmed (RankedData.restoreFor does RP
-- and MMR the same way):
--   * every match in the cheater's log that ended at or after `since`: everyone on the other side of it gets that
--     match's deaths off, and the match and its lost rounds too if they lost it. their kills stay, so does a win.
--   * the cheater: every number and the XP back to zero, the card marked STATS RESET <date> for everyone to see. the
--     old numbers are kept (backup), so Stats.undoRestore(userId) can put them back if the catch was wrong.
--   * players in this server get it at once; the rest through a pending entry in "JankfireStatsFix_v1" (applied on
--     their next join) and a MessagingService nudge (a server that has them applies it now).
--   * idempotent: a match is undone once (fixed), a reset done once per since (voids). running it twice does nothing.
--
-- the remote ReplicatedStorage.JankfireRemotes.Profile (RemoteFunction), always a table { ok, why?, ... }:
--   ("card", userId)    -> { card }: anyone in this server. a private player's card has no stats/weapons/recent
--   ("list")            -> { players = { { id, name, display, xp, look, private, ranked? } } }: everyone here, for the player list
-- a card or a row can carry more from other modules (Stats.cardExtra): ranked = the ranked session's (RankedStyle reads it)
--   ("owned")           -> { owned = { border = { id = true }, ... } }: which card looks you may wear
--   ("look", type, id)  -> { look }: wear one (it must be free or yours)
--   ("private", bool)   -> { private }
-- player attributes: Xp, Level (anyone's nametag or list can show them), StatsSave ("loading"|"cloud"|"off"|"lost"),
-- StatsPrivate (your own switch, for the settings panel).
-- Studio play tests: ServerStorage.JankStatsTest (BindableFunction), see Stats.test at the end.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local DataStoreService = game:GetService("DataStoreService")
local MessagingService = game:GetService("MessagingService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Ranks = require(Shared:WaitForChild("Ranks"))
local CardStyles = require(Shared:WaitForChild("CardStyles"))
local Roster = require(Shared:WaitForChild("Roster"))
local Profiles = require(script.Parent:WaitForChild("Profiles"))
local Loot = require(script.Parent:WaitForChild("Loot"))
-- weapon mastery (18 Nov 2026, Shared.Mastery, docs/MASTERY.md): XP per weapon in this save (mx), added from here
local Mastery = require(Shared:WaitForChild("Mastery"))
local MasteryXp = require(script.Parent:WaitForChild("MasteryXp"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Profile") :: RemoteFunction

local Stats = {}
local RECENT = 10
local LOG = 100 -- matches kept per player for cheat restores

local function template(): any
	return { v = 1, xp = 0, k = 0, d = 0, m = 0, w = 0, rp = 0, rw = 0, sh = 0, hi = 0, hc = 0, hs = 0, hk = 0, dmg = 0, best = 0, time = 0,
		wpn = {}, recent = {}, look = { border = CardStyles.DEFAULT.border, banner = CardStyles.DEFAULT.banner, title = CardStyles.DEFAULT.title },
		private = false, since = os.time(), log = {}, fixed = {}, voids = {}, reset = false, backup = false, mx = {} }
end
local store = Profiles.new("JankfireStats_v1", template)

type Fighter = any
-- the match you are in, as far as stats go
type Cur = { id: number, key: string, mode: string, arena: string, team: number, k: number, d: number, dmg: number,
	wt: { [string]: number }, streak: number, t0: number, test: boolean?, m: any?, -- (m: the match itself)
	foes: { number }, mates: { number }, ranked: boolean, rp: number, rw: number, xp: number,
	rwt: { [string]: number }, -- (seconds held per weapon this round: the round win's mastery XP goes to the longest)
	fix: number? } -- (fix: a cheater restored while this match was on: it comes off when it ends)
type State = { p: Player, prof: Profiles.Profile?, ready: boolean, cur: Cur?, att: { [string]: boolean }, xpAcc: number,
	budget: number, budgetT: number, devAll: boolean? }
local st: { [Player]: State } = {}
local lastHit: { [Fighter]: { by: Fighter, hs: boolean, t: number } } = setmetatable({}, { __mode = "k" }) :: any
local Fight: any
local Matches: any
local ghost: Fighter? = nil -- (Studio tests: a dummy that counts as a player on the other team)
-- (Studio tests: count ghost matches and the stand-in dummy. off unless a stats test turns it on, so nobody's Play test
-- of matches or dummies ever lands in the owner's real numbers)
local testCount = false
-- cheaters restored while this server runs (userId -> since): nothing more counts for them here, and a match still on
-- with them in it comes off its victims when it ends. every server learns it through the nudge
local watched: { [number]: number } = {}

-- only real weapons count: a live weapon or item of the roster. a test hook's "test" damage, a dummy's own gun or
-- anything else made up never reaches the numbers
local function real(wid: any): boolean
	local e = if type(wid) == "string" then Roster.byId[wid] else nil
	return e ~= nil and e.live == true
end
-- kills with no roster weapon that still count as kills (18 Nov): the t-bag's blast, and a fall after your grapple. they
-- go on the kill count, the streak and the xp, not on a weapon row (the card lists the roster's weapons)
local KILL_ONLY = { tbag = true, grapple = true } :: { [string]: boolean }

-- ------------------------------------------------------------------ the numbers
local function dataOf(s: State?): any
	return if s and s.prof then s.prof.data else nil
end
local function publish(s: State)
	local p = s.p
	if not p.Parent then return end
	local d = dataOf(s)
	local xp = if d then math.floor(tonumber(d.xp) or 0) else 0
	p:SetAttribute("Xp", xp)
	p:SetAttribute("Level", Ranks.levelOf(xp))
	p:SetAttribute("StatsSave", if not s.ready then "loading" elseif s.prof then s.prof.state else "off")
	p:SetAttribute("StatsPrivate", d ~= nil and d.private == true) -- (the settings panel's switch shows it)
	MasteryXp.publish(p) -- (the Mastery attribute: XP per weapon)
	-- (the card title you wear, for the one over your head: client/OverheadTitles; "none" shows nothing)
	local title = if d and type(d.look) == "table" and type(d.look.title) == "string" then d.look.title else "none"
	if p:GetAttribute("CardTitle") ~= title then p:SetAttribute("CardTitle", title) end
end
local function dirty(s: State)
	if s.prof then s.prof.dirty = true end
end
local function wpn(d: any, wid: string): any
	local w = d.wpn[wid]
	if type(w) ~= "table" then
		w = { k = 0, s = 0, h = 0, hs = 0, t = 0, dmg = 0 }
		d.wpn[wid] = w
	end
	return w
end
local function addXp(s: State, n: number)
	local d = dataOf(s)
	if not d or n <= 0 then return end
	d.xp = math.floor((tonumber(d.xp) or 0) + n)
	if s.cur then (s.cur :: Cur).xp += n end
	dirty(s)
	publish(s)
end

-- is this player's match one that counts right now (the round live)?
local function liveFor(s: State?): boolean
	if not s or not s.cur then return false end
	if watched[s.p.UserId] then return false end -- (a cheater restored here: nothing more counts)
	local c = s.cur :: Cur
	if c.test then return true end
	if c.m and c.m.ghost and not testCount then return false end -- (a Studio ghost match: not real)
	if c.m and c.m.dev then return false end -- (a match the owner used dev powers in, OwnerDev.server: counts for nothing)
	if c.m and c.m.private then return false end -- (a party alone, a private duel: Party.luau, counts for nothing)
	local mi = Matches.matchOf(s.p)
	return mi ~= nil and mi.id == c.id and mi.phase == "live"
end
local function stateOf(f: Fighter?): State?
	if not f or f.kind ~= "player" then return nil end
	return st[f.ref :: Player]
end
-- does this player's match count for weapon mastery? the same matches as the numbers here: a real one (or a stats
-- test's), never a ghost match (unless a stats test turned ghosts on) or a dev match, never a restored cheater. no
-- phase check: the blow that ends a round lands after the round is decided
local function masteryCounts(s: State?): boolean
	if not s or not s.cur or watched[s.p.UserId] then return false end
	local c = s.cur :: Cur
	if c.test then return true end
	return c.m ~= nil and not (c.m.ghost and not testCount) and not c.m.dev and not c.m.private
end
-- who hurt whom lately, for assists: victim -> { attacker -> { t (last hurt), w = { [weapon] = damage } } }
local hurtBy: { [Fighter]: { [Fighter]: { t: number, w: { [string]: number } } } } = setmetatable({}, { __mode = "k" }) :: any
-- two fighters on opposite teams of one counted match (or a test player and the test ghost)
local function enemies(a: Fighter?, b: Fighter?): boolean
	if not a or not b or a == b then return false end
	local sa, sb = stateOf(a), stateOf(b)
	if sa and sb then
		local ca, cb = sa.cur, sb.cur
		return ca ~= nil and cb ~= nil and ca.id == cb.id and ca.team ~= cb.team
	end
	if ghost and testCount and (a == ghost or b == ghost) then -- (only ever set by a Studio test)
		local s = sa or sb
		return s ~= nil and s.cur ~= nil
	end
	return false
end

-- an attack (a shot or a swing) that counts: one more for accuracy, and it waits to land
local function onShot(f: Fighter, wid: string)
	if not real(wid) then return end
	local s = stateOf(f)
	if not liveFor(s) then return end
	local d = dataOf(s)
	if not d then return end
	local ss = s :: State
	d.sh += 1
	wpn(d, wid).s += 1
	ss.att[wid] = false
	dirty(ss)
end

local function onHurt(t: Fighter, done: number, by: Fighter?, wid: string, hs: boolean?)
	if not by or not real(wid) or not enemies(by, t) then return end
	lastHit[t] = { by = by, hs = hs == true, t = os.clock() }
	-- (weapon mastery's assists: who hurt them, with what, and when last)
	local hb = hurtBy[t] or {}
	hurtBy[t] = hb
	local he = hb[by]
	if not he or os.clock() - he.t > Mastery.ASSIST_WINDOW then he = { t = 0, w = {} }; hb[by] = he end
	he.t = os.clock()
	he.w[wid] = (he.w[wid] or 0) + done
	local s = stateOf(by)
	local d = dataOf(s)
	if not s or not d or not s.cur or watched[s.p.UserId] then return end
	local c = s.cur :: Cur
	local w = wpn(d, wid)
	d.dmg += done; w.dmg += done; c.dmg += done
	d.hc += 1
	if hs then d.hs += 1; w.hs += 1 end
	-- the attack it came from landed (once per attack: a shotgun volley on two people is one hit)
	if s.att[wid] == false then
		s.att[wid] = true
		d.hi += 1
		w.h += 1
	end
	dirty(s)
end

local function onKill(info: any)
	local v, k = info.v, info.k
	local hb = hurtBy[v] -- (who hurt them: the assists below. gone with this death whatever happens)
	hurtBy[v] = nil
	local sv = stateOf(v)
	local dv = dataOf(sv)
	if sv and dv and sv.cur and liveFor(sv) then
		local c = sv.cur :: Cur
		dv.d += 1
		c.d += 1
		c.streak = 0
		dirty(sv)
	end
	if not k or not enemies(k, v) then lastHit[v] = nil; return end
	local sk = stateOf(k)
	local dk = dataOf(sk)
	if not sk or not dk or not sk.cur or watched[sk.p.UserId] then lastHit[v] = nil; return end
	local c = sk.cur :: Cur
	local wid = if info.w == "void" and type(info.via) == "string" then info.via else info.w
	if wid == "parry" then wid = "katana" end -- (a parry kill is the parrier's katana: a perfect parry's shot sent back, or a fall after a parry shove)
	-- (weapon mastery's assists: everyone else on the killer's side who hurt them in the last few seconds, on the weapon
	-- they hurt them most with)
	if hb then
		for f, e in hb do
			if f ~= k and os.clock() - e.t <= Mastery.ASSIST_WINDOW and enemies(f, v) then
				local sf = stateOf(f)
				local top, most = nil, 0
				for w, dmg in e.w do if dmg > most then top, most = w, dmg end end
				if sf and top and masteryCounts(sf) then MasteryXp.add(sf.p, top, Mastery.XP.assist, "assist") end
			end
		end
	end
	if not real(wid) and not KILL_ONLY[wid] then lastHit[v] = nil; return end
	dk.k += 1
	c.k += 1
	if real(wid) then wpn(dk, wid).k += 1 end
	c.streak += 1
	if c.streak > (tonumber(dk.best) or 0) then dk.best = c.streak end
	local lh = lastHit[v]
	local hsKill = info.w ~= "void" and lh ~= nil and lh.by == k and lh.hs and os.clock() - lh.t < 2
	if hsKill then dk.hk += 1 end
	lastHit[v] = nil
	dirty(sk)
	addXp(sk, Ranks.XP.kill)
	-- (weapon mastery: the kill to the weapon that made it, more for a headshot)
	if real(wid) and masteryCounts(sk) then
		MasteryXp.add(sk.p, wid, Mastery.XP.kill + (if hsKill then Mastery.XP.headshot else 0), "kill")
	end
end

-- ------------------------------------------------------------------ cheat restores: the pieces (on one save's data)
local NUMS = { "xp", "k", "d", "m", "w", "rp", "rw", "sh", "hi", "hc", "hs", "hk", "dmg", "best", "time" }
local function deepCopy(t: any): any
	if type(t) ~= "table" then return t end
	local o = {}
	for k, v in t do o[k] = deepCopy(v) end
	return o
end
local function num(v: any): number return tonumber(v) or 0 end

-- one match against a cheater comes off a victim: its deaths, and if they lost it, the match and the rounds they
-- lost. their kills, XP and a win stay. once per match (fixed); a match no longer in the log is marked and left
local function undoMatch(d: any, key: string, by: number): boolean
	if d.fixed[key] ~= nil then return false end
	d.fixed[key] = by
	for _, e in d.log do
		if type(e) == "table" and e.id == key then
			if e.x == nil then
				e.x = by
				d.d = math.max(0, num(d.d) - num(e.d))
				d.rp = math.max(num(d.rw), num(d.rp) - math.max(0, num(e.rp) - num(e.rw)))
				if e.r ~= "W" then d.m = math.max(num(d.w), num(d.m) - 1) end
			end
			break
		end
	end
	for _, r in d.recent do if type(r) == "table" and r.id == key then r.x = true end end
	return true
end

-- the cheater: every number and the XP to zero, the card marked. once per `since` (voids). the log stays (a later
-- restore with an earlier since still finds the victims), and so do the look, the switch and what they own
local function voidStats(d: any, since: number, at: number): boolean
	local vk = tostring(math.floor(since))
	if d.voids[vk] ~= nil then return false end
	d.voids[vk] = at
	local before: any = { wpn = deepCopy(d.wpn), recent = deepCopy(d.recent), mx = deepCopy(if type(d.mx) == "table" then d.mx else {}) }
	for _, k in NUMS do before[k] = num(d[k]) end
	-- (a second reset keeps the first one's numbers too: undo gives back everything)
	if type(d.backup) == "table" then
		local b = d.backup
		for _, k in NUMS do before[k] = if k == "best" then math.max(before.best, num(b.best)) else before[k] + num(b[k]) end
		for wid, w in b.wpn or {} do
			local cur = before.wpn[wid]
			if type(cur) ~= "table" then before.wpn[wid] = w else for f, v in w do cur[f] = num(cur[f]) + num(v) end end
		end
		for wid, x in (if type(b.mx) == "table" then b.mx else {}) do before.mx[wid] = num(before.mx[wid]) + num(x) end
	end
	d.backup = before
	for _, k in NUMS do d[k] = 0 end
	d.wpn, d.recent = {}, {}
	d.mx = {} -- (weapon mastery XP too; camos already granted stay with the loot save)
	d.reset = { t = at, since = since }
	return true
end

-- a wrong catch: the numbers from before the reset come back, added to what was played since
local function unvoid(d: any): boolean
	local b = d.backup
	if type(b) ~= "table" then return false end
	for _, k in NUMS do d[k] = if k == "best" then math.max(num(d.best), num(b.best)) else num(d[k]) + num(b[k]) end
	for wid, w in b.wpn or {} do
		local cur = d.wpn[wid]
		if type(cur) ~= "table" then d.wpn[wid] = w else for f, v in w do cur[f] = num(cur[f]) + num(v) end end
	end
	if type(d.mx) ~= "table" then d.mx = {} end
	for wid, x in (if type(b.mx) == "table" then b.mx else {}) do d.mx[wid] = math.min(Mastery.total(Mastery.MAX), num(d.mx[wid]) + num(x)) end
	local rec = table.clone(d.recent)
	for _, r in b.recent or {} do table.insert(rec, r) end
	while #rec > RECENT do table.remove(rec) end
	d.recent = rec
	d.backup, d.reset = false, false
	return true
end

-- ------------------------------------------------------------------ matches
local function begin(p: Player, id: number, mode: string, arena: string, team: number, test: boolean?, m: any?, key: string?, foes: { number }?, mates: { number }?)
	local s = st[p]
	if not s then return end
	s.cur = { id = id, key = key or ("t" .. os.time() .. "-" .. math.random(1e6)), mode = mode, arena = arena, team = team, k = 0, d = 0, dmg = 0, wt = {},
		streak = 0, t0 = os.time(), test = test, m = m, foes = foes or {}, mates = mates or {}, ranked = m ~= nil and m.ranked == true, rp = 0, rw = 0, xp = 0, rwt = {} }
	s.att = {}
	MasteryXp.matchStart(p)
end

-- a cheater restored in this server (or any, through the nudge) was on the other side of this match
local function cheaterIn(c: Cur): number?
	if c.fix then return c.fix end
	for _, uid in c.foes do if watched[uid] then return uid end end
	return nil
end

-- the match is over for this player: W or L (leaving = L), "5-3" (their wins first)
local function finish(p: Player, res: string, score: string?)
	local s = st[p]
	if not s or not s.cur then return end
	local c = s.cur :: Cur
	-- (weapon mastery: the match won is worth XP to the weapon held longest in it; then the client hears what it gave)
	local counts = masteryCounts(s)
	if counts and res == "W" then
		local top = MasteryXp.top(c.wt)
		if top then MasteryXp.add(p, top, Mastery.XP.matchWin, "match") end
	end
	MasteryXp.matchEnd(p, counts)
	s.cur = nil
	s.att = {}
	local d = dataOf(s)
	if not d then return end
	if c.m and c.m.ghost and not testCount then return end -- (a Studio ghost match is never recorded)
	if c.m and c.m.dev then return end -- (a match the owner used dev powers in, OwnerDev.server: counts for nothing)
	if c.m and c.m.private then return end -- (a party alone, a private duel: Party.luau, counts for nothing)
	-- the match's record first (a restore reads it), then the totals (not for a cheater restored here)
	table.insert(d.log, 1, { id = c.key, t = os.time(), mode = c.mode, map = c.arena, team = c.team, ranked = if c.ranked then true else nil, r = res,
		k = c.k, d = c.d, rp = c.rp, rw = c.rw, xp = c.xp, foes = c.foes, mates = c.mates })
	while #d.log > LOG do table.remove(d.log) end
	if not watched[p.UserId] then
		d.m += 1
		if res == "W" then d.w += 1 end
		local top, best = nil, -1
		for wid, t in c.wt do if t > best then top, best = wid, t end end
		table.insert(d.recent, 1, { id = c.key, t = os.time(), mode = c.mode, map = c.arena, r = res, k = c.k, d = c.d, w = top, sc = score or "", dmg = math.floor(c.dmg + 0.5) })
		while #d.recent > RECENT do table.remove(d.recent) end
	end
	-- a match against a cheater who was caught while it was on: it comes off at once
	local by = cheaterIn(c)
	if by then undoMatch(d, c.key, by) end
	dirty(s)
	-- (a finished match is worth writing soon: a crash later loses less)
	if s.prof and s.prof.state == "cloud" then task.spawn(Profiles.save, store, s.prof) end
end

local function scoreFor(wins: { number }, team: number): string
	local parts = { tostring(wins[team] or 0) }
	for t, n in wins do if t ~= team then table.insert(parts, tostring(n)) end end
	return table.concat(parts, "-")
end

local function hookMatches()
	Matches.onStart(function(m: any)
		-- (one key for the whole match, the same in every player's record: Matches makes it unique across servers)
		local key = if type(m.key) == "string" then m.key else ("x" .. tostring(m.id) .. "-" .. os.time() .. "-" .. math.random(1e6))
		for t, list in m.teams do
			for _, p in list do
				local foes, mates = {}, {}
				for t2, l2 in m.teams do
					for _, o in l2 do if o ~= p then table.insert(if t2 == t then mates else foes, o.UserId) end end
				end
				begin(p, m.id, tostring(m.mode or ""), tostring(m.arena or ""), t, nil, m, key, foes, mates)
			end
		end
	end)
	Matches.onRound(function(m: any, winner: number)
		if m.ghost and not testCount then return end
		if m.dev then return end -- (a match the owner used dev powers in, OwnerDev.server: counts for nothing)
		if m.private then return end -- (a party alone, a private duel: Party.luau, counts for nothing)
		for t, list in m.teams do
			for _, p in list do
				local s = st[p]
				local d = dataOf(s)
				if s and d and s.cur and (s.cur :: Cur).id == m.id then
					local c = s.cur :: Cur
					c.rp += 1
					if t == winner then c.rw += 1 end
					if not watched[p.UserId] then
						d.rp += 1
						if t == winner then d.rw += 1; addXp(s, Ranks.XP.roundWin) end
						-- (weapon mastery: a round won, to the weapon held longest in it)
						local top = if t == winner and masteryCounts(s) then MasteryXp.top(c.rwt) else nil
						if top then MasteryXp.add(p, top, Mastery.XP.roundWin, "round") end
						dirty(s)
					end
					c.rwt = {}
				end
			end
		end
	end)
	Matches.onEnd(function(m: any, winner: number?)
		for t, list in m.teams do
			for _, p in list do
				local s = st[p]
				if s and s.cur and (s.cur :: Cur).id == m.id then finish(p, if winner == t then "W" else "L", scoreFor(m.wins, t)) end
			end
		end
	end)
end

-- ------------------------------------------------------------------ the card
-- other modules add to a card or a player-list row (the ranked session's module sets card.ranked): fn(target, viewer,
-- card) runs for every card and every row, a private player's too (rank shows even when stats are hidden). each one
-- runs in a pcall, so a slip there never breaks a card
local extras: { (Player, Player?, any) -> () } = {}
function Stats.cardExtra(fn: (Player, Player?, any) -> ()) table.insert(extras, fn) end
-- (Loadout's weapon-unlock grandfather, 18 Nov: the weapons a player has used, any time held, shot or kill. nil while
-- their stats are loading)
function Stats.usedWeapons(p: Player): { string }?
	local s = st[p]
	if not s or not s.ready then return nil end
	local d = dataOf(s)
	local out = {}
	if d and type(d.wpn) == "table" then
		for wid, w in d.wpn do
			if type(wid) == "string" and type(w) == "table" and ((tonumber(w.t) or 0) > 0 or (tonumber(w.s) or 0) > 0 or (tonumber(w.k) or 0) > 0) then
				table.insert(out, wid)
			end
		end
	end
	return out
end
local function extra(target: Player, viewer: Player?, card: any): any
	for _, fn in extras do
		local ok, err = pcall(fn, target, viewer, card)
		if not ok then warn("[jankfire] stats: a card extra failed: " .. tostring(err)) end
	end
	return card
end

local SHOWN = { "k", "d", "m", "w", "rp", "rw", "sh", "hi", "hc", "hs", "hk", "dmg", "best", "time" }
local function cardOf(target: Player, viewer: Player?): any
	local s = st[target]
	local d = dataOf(s)
	local card: any = { id = target.UserId, name = target.Name, display = target.DisplayName, ready = s ~= nil and s.ready }
	if not d then
		card.xp, card.look, card.private = 0, table.clone(CardStyles.DEFAULT), false
		return extra(target, viewer, card)
	end
	card.xp = math.floor(tonumber(d.xp) or 0)
	card.look = { border = d.look.border, banner = d.look.banner, title = d.look.title }
	card.private = d.private == true
	card.since = d.since
	-- (a cheat restore reset this player's numbers: everyone sees when, a private player's card too)
	if type(d.reset) == "table" then card.reset = { t = d.reset.t } end
	if card.private and viewer ~= target then return extra(target, viewer, card) end
	local stats = {}
	for _, k in SHOWN do stats[k] = math.floor((tonumber(d[k]) or 0) + 0.5) end
	card.stats = stats
	-- weapons by time held (then attacks, then kills)
	local list = {}
	local total = 0
	for wid, w in d.wpn do
		if type(w) == "table" and real(wid) then -- (live weapons and items only: never a test hook's "test")
			table.insert(list, { id = wid, k = w.k or 0, s = w.s or 0, h = w.h or 0, hs = w.hs or 0, t = math.floor((w.t or 0) + 0.5), dmg = math.floor((w.dmg or 0) + 0.5) })
			total += w.t or 0
		end
	end
	table.sort(list, function(a, b)
		if a.t ~= b.t then return a.t > b.t end
		if a.s ~= b.s then return a.s > b.s end
		return a.k > b.k
	end)
	local top = {}
	for i = 1, math.min(5, #list) do
		list[i].share = if total > 0 then list[i].t / total else 0
		table.insert(top, list[i])
	end
	card.weapons = top
	card.recent = d.recent
	return extra(target, viewer, card)
end

-- the OWNER title is the place's creator's alone (CardStyles.OWNER), whatever any save or test says
local function creator(p: Player): boolean
	return game.CreatorType == Enum.CreatorType.User and p.UserId > 0 and p.UserId == game.CreatorId
end
local function owns(p: Player, t: string, id: string): boolean
	if CardStyles.isOwnerOnly and CardStyles.isOwnerOnly(t, id) then return creator(p) end
	if CardStyles.isFree(t, id) then return true end
	local s = st[p]
	if s and s.devAll and CardStyles.info(t, id) then return true end -- (a Studio test: wear anything, this session only)
	if not CardStyles.info(t, id) then return false end
	local ok, yes = pcall(Loot.owns, p, t, id)
	return ok and yes == true
end
local function ownedOf(p: Player): any
	local out = {}
	for _, t in CardStyles.TYPES do
		out[t] = {}
		for _, id in CardStyles.ORDER[t] do if owns(p, t, id) then out[t][id] = true end end
	end
	return out
end

-- ------------------------------------------------------------------ the remote
local function spend(s: State): boolean
	local t = os.clock()
	s.budget = math.min(20, s.budget + (t - s.budgetT) * 5); s.budgetT = t
	if s.budget < 1 then return false end
	s.budget -= 1
	return true
end

local function handle(p: Player, op: unknown, a: unknown, b: unknown): any
	local s = st[p]
	if not s then return { ok = false, why = "still loading" } end
	if not spend(s) then return { ok = false, why = "slow down" } end
	if op == "card" then
		local target = if type(a) == "number" then Players:GetPlayerByUserId(a) else p
		if not target then return { ok = false, why = "they've left" } end
		return { ok = true, card = cardOf(target, p) }
	elseif op == "list" then
		local out = {}
		for _, o in Players:GetPlayers() do
			local d = dataOf(st[o])
			table.insert(out, extra(o, p, { id = o.UserId, name = o.Name, display = o.DisplayName, xp = if d then math.floor(tonumber(d.xp) or 0) else 0,
				look = if d then { border = d.look.border, banner = d.look.banner, title = d.look.title } else table.clone(CardStyles.DEFAULT),
				private = d ~= nil and d.private == true }))
		end
		return { ok = true, players = out }
	elseif op == "owned" then
		return { ok = true, owned = ownedOf(p) }
	end
	local d = dataOf(s)
	if not s.ready or not d then return { ok = false, why = "your profile is still loading" } end
	if op == "look" then
		if type(a) ~= "string" or not CardStyles.isType(a) or type(b) ~= "string" then return { ok = false, why = "nope" } end
		if not CardStyles.info(a, b) then return { ok = false, why = "no such thing" } end
		if not owns(p, a, b) then return { ok = false, why = "you don't own that yet" } end
		d.look[a] = b
		dirty(s)
		publish(s)
		return { ok = true, look = { border = d.look.border, banner = d.look.banner, title = d.look.title } }
	elseif op == "private" then
		d.private = a == true
		dirty(s)
		publish(s)
		return { ok = true, private = d.private }
	end
	return { ok = false, why = "nope" }
end

Remote.OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown)
	local ok, res = pcall(handle, p, op, a, b)
	if not ok then
		warn("[jankfire] stats: " .. tostring(res))
		return { ok = false, why = "something broke. try again" }
	end
	return res
end

-- ------------------------------------------------------------------ cheat restores (Stats.restoreFor, at the top)
local FIX_TOPIC = "JankStatsFix"
local fixDs: DataStore? = nil
pcall(function() fixDs = DataStoreService:GetDataStore(if RunService:IsStudio() then "JankfireStatsFix_studio" else "JankfireStatsFix_v1") end)
local memPending: { [number]: { [string]: any } } = {} -- (no DataStores reachable: pending entries live here)
local leftLogs: { [number]: { t: number, log: any } } = {} -- the logs of players who left lately (kicked just before the call)
local stand: { [number]: { d: any, online: boolean } } = {} -- (Studio tests: stand-in players under made-up userIds)

-- the loaded save of a player in this server (and their state), or nil
local function hereData(uid: number): (any, State?)
	local p = Players:GetPlayerByUserId(uid)
	local s = if p then st[p] else nil
	if s and s.ready and s.prof then return s.prof.data, s end
	local si = stand[uid]
	if si and si.online then return si.d, nil end
	return nil, nil
end

-- a player's match records: from this server if they're here or just left, else read from their save. nil = unreadable
local function logOf(uid: number): { any }?
	local d = hereData(uid)
	if d then return d.log end
	if stand[uid] then return stand[uid].d.log end
	local left = leftLogs[uid]
	if left then return left.log end
	local ds = store.ds
	if not ds then return {} end
	local ok, raw = pcall(function() return (ds :: DataStore):GetAsync("u" .. uid) end)
	if not ok then return nil end
	return if type(raw) == "table" and type(raw.log) == "table" then raw.log else {}
end

-- fixes (id -> entry) on a loaded save, oldest first. returns whether anything changed
local function applyFixes(d: any, s: State?, fixes: { [string]: any }): boolean
	local list = {}
	for id, e in fixes do if type(e) == "table" then table.insert(list, e) end end
	table.sort(list, function(a, b) return num(a.at) < num(b.at) end)
	local changed = false
	for _, e in list do
		if e.op == "match" and type(e.key) == "string" then
			local c = if s then s.cur else nil
			if c and c.key == e.key then
				c.fix = num(e.by) -- (still playing it: it comes off when it ends)
			elseif undoMatch(d, e.key, num(e.by)) then
				changed = true
			end
		elseif e.op == "void" then
			if voidStats(d, num(e.since), num(e.at)) then changed = true end
		elseif e.op == "unvoid" then
			if unvoid(d) then changed = true end
		end
	end
	if changed and s then dirty(s); publish(s) end
	return changed
end

local function readPending(uid: number): { [string]: any }?
	if not fixDs then return memPending[uid] or {} end
	local ok, got = pcall(function() return (fixDs :: DataStore):GetAsync("u" .. uid) end)
	if not ok then return nil end
	return if type(got) == "table" then got else {}
end
local function addPending(uid: number, fixes: { [string]: any }): boolean
	if not fixDs then
		local t = memPending[uid] or {}
		for id, e in fixes do if t[id] == nil then t[id] = e end end
		memPending[uid] = t
		return true
	end
	local ok = pcall(function()
		(fixDs :: DataStore):UpdateAsync("u" .. uid, function(old: any)
			local t = if type(old) == "table" then old else {}
			for id, e in fixes do if t[id] == nil then t[id] = e end end
			return t
		end)
	end)
	return ok
end
-- off the list once applied and saved (an entry that changed since, by its time, stays)
local function dropPending(uid: number, done: { [string]: any })
	if not fixDs then
		local t = memPending[uid]
		if t then for id, e in done do if t[id] and num(t[id].at) == num(e.at) then t[id] = nil end end end
		return
	end
	pcall(function()
		(fixDs :: DataStore):UpdateAsync("u" .. uid, function(old: any)
			if type(old) ~= "table" then return nil end
			for id, e in done do if type(old[id]) == "table" and num(old[id].at) == num(e.at) then old[id] = nil end end
			return old
		end)
	end)
end

-- a player here takes their pending fixes: applied, written to their save, then off the list (a crash between the
-- two only re-runs fixes the save already marks done)
local pulling: { [number]: string } = {} -- ("busy", or "again": more came in while it ran)
local function pull(uid: number)
	if pulling[uid] then pulling[uid] = "again"; return end
	pulling[uid] = "busy"
	while true do
		local d, s = hereData(uid)
		local got = if d then readPending(uid) else nil
		if d and got and next(got) ~= nil then
			applyFixes(d, s, got)
			local saved = true
			if s and s.prof then
				saved = (s.prof.state == "cloud" and Profiles.save(store, s.prof)) or (s.prof.state == "off" and fixDs == nil)
			end
			if saved then dropPending(uid, got) end
		end
		if pulling[uid] ~= "again" then break end
		pulling[uid] = "busy"
	end
	pulling[uid] = nil
end

-- tell every server: these players have fixes waiting (pull now if you have them); this cheater is restored
local function nudge(uids: { number }, cheater: number?, since: number?, unwatch: boolean?)
	local i = 1
	repeat
		local chunk = table.move(uids, i, math.min(#uids, i + 59), 1, {})
		i += 60
		pcall(function() MessagingService:PublishAsync(FIX_TOPIC, { u = chunk, w = cheater, s = since, uw = unwatch }) end)
	until i > #uids
end

-- fixes for one player: applied now if they're here (and saved soon), else left pending. returns "now" | "queued" | nil
local function deliver(uid: number, fixes: { [string]: any }): string?
	local d, s = hereData(uid)
	if d then
		if applyFixes(d, s, fixes) and s and s.prof and s.prof.state == "cloud" then task.spawn(Profiles.save, store, s.prof) end
		return "now"
	end
	return if addPending(uid, fixes) then "queued" else nil
end

-- THE CALL (the anti-cheat, when a cheater is confirmed). since = os.time() seconds: matches that ended then or later
-- (nil or 0 = every match still in their log, the last LOG). yields (DataStores): call it in its own thread.
-- returns { ok = true, matches, victims, now, queued, failed } or { ok = false, why }
function Stats.restoreFor(cheater: number, since: number?): any
	if type(cheater) ~= "number" or cheater == 0 then return { ok = false, why = "no user id" } end
	local from = math.max(0, math.floor(tonumber(since) or 0))
	local now = os.time()
	watched[cheater] = math.min(watched[cheater] or from, from)
	local log = logOf(cheater)
	if not log then return { ok = false, why = "couldn't read their stats save; try again" } end
	local todo: { [number]: { [string]: any } } = {}
	local matches = 0
	for _, e in log do
		if type(e) == "table" and type(e.id) == "string" and num(e.t) >= from then
			matches += 1
			for _, uid in (if type(e.foes) == "table" then e.foes else {}) do
				if type(uid) == "number" and uid ~= cheater then
					todo[uid] = todo[uid] or {}
					todo[uid]["m:" .. e.id] = { op = "match", key = e.id, by = cheater, at = now }
				end
			end
		end
	end
	todo[cheater] = todo[cheater] or {}
	todo[cheater]["v:" .. from] = { op = "void", since = from, by = cheater, at = now }
	local out = { ok = true, matches = matches, victims = 0, now = 0, queued = 0, failed = 0 }
	local waiting = {}
	for uid, fixes in todo do
		if uid ~= cheater then out.victims += 1 end
		local how = deliver(uid, fixes)
		if how == "now" then out.now += 1
		elseif how == "queued" then out.queued += 1; table.insert(waiting, uid)
		else out.failed += 1 end
	end
	task.spawn(nudge, waiting, cheater, from)
	return out
end

-- a wrong catch (the anti-cheat's UNBAN): the cheater's own numbers come back. their victims keep the restore
function Stats.undoRestore(uid: number): any
	if type(uid) ~= "number" then return { ok = false, why = "no user id" } end
	watched[uid] = nil
	local now = os.time()
	local how = deliver(uid, { ["u:" .. now] = { op = "unvoid", by = uid, at = now } })
	task.spawn(nudge, if how == "queued" then { uid } else {}, uid, nil, true)
	return { ok = how ~= nil, now = how == "now", queued = how == "queued" }
end

-- a player's matches from their log since `since` (for RankedData's restore): newest first
-- { key, t, mode, ranked, team, r, foes = { userIds }, mates = { userIds } }; nil if the save couldn't be read
function Stats.matchesOf(uid: number, since: number?): { any }?
	local log = logOf(uid)
	if not log then return nil end
	local from = tonumber(since) or 0
	local out = {}
	for _, e in log do
		if type(e) == "table" and type(e.id) == "string" and num(e.t) >= from then
			table.insert(out, { key = e.id, t = e.t, mode = e.mode, ranked = e.ranked == true, team = e.team, r = e.r,
				foes = table.clone(e.foes or {}), mates = table.clone(e.mates or {}) })
		end
	end
	return out
end

-- ------------------------------------------------------------------ the owner's XP gifts (19 Nov 2026)
-- the owner's GIFT tab (OwnerDev.server; the owner: "allow me to also give people xp, I want to be able to unlock stuff
-- for my friends!!"): account XP or a level, and weapon mastery XP or a mastery level. it's the same XP a match gives:
-- the Xp / Level attributes (the level-up toast and the weapons it opens: UnlockClient), and mastery through
-- MasteryXp.add (its toast, and the camos at their levels). it's never on a match's log (cur.xp), so a cheat restore
-- for someone else never takes it, and ranked (RankedData) never sees it. a level only goes UP: below it, they're
-- raised to its start; at it or past it, nothing happens ("already"). once per receipt id: data.gifts keeps the last
-- GIFT_IDS ids in this save, with the XP, so both go in the same write
--   Stats.gift(p, what, rid) -> ok, why?   what = { xp = n } | { level = lv } | { w = weapon, xp = n } | { w = weapon, level = lv }
--   why "already" = nothing new (the receipt again, the level already reached, mastery maxed)
local GIFT_IDS = 200
Stats.GIFT_XP_MAX = 10000000
Stats.GIFT_LEVEL_MAX = 500
function Stats.gift(p: Player, what: any, rid: string): (boolean, string?)
	local s = st[p]
	local d = dataOf(s)
	if not s or not s.ready or not d then return false, "their stats save isn't ready" end
	if type(what) ~= "table" then return false, "nope" end
	if type(d.gifts) ~= "table" then d.gifts = {} end
	local id = string.sub(tostring(rid), 1, 80)
	if table.find(d.gifts, id) then return true, "already" end
	local n = if type(what.xp) == "number" then math.floor(what.xp) else nil
	local lv = if type(what.level) == "number" then math.floor(what.level) else nil
	if what.w ~= nil then
		local w = if type(what.w) == "string" then (Roster.formOf and Roster.formOf[what.w] or what.w) else nil
		if not w or not Mastery.levels(w) then return false, "not a weapon with mastery" end
		if type(d.mx) ~= "table" then d.mx = {} end
		local before = math.floor(tonumber(d.mx[w]) or 0)
		local add = 0
		if lv then
			add = Mastery.total(math.clamp(lv, 1, Mastery.MAX)) - before
		elseif n and n >= 1 and n <= Stats.GIFT_XP_MAX then
			add = n
		else
			return false, "how much"
		end
		if add <= 0 then return true, "already" end
		local after = MasteryXp.add(p, w, add, "owner gift")
		if not after then return false, "their mastery isn't ready" end
		if after <= before then return true, "already" end
	elseif lv then
		if lv < 2 or lv > Stats.GIFT_LEVEL_MAX then return false, "a level from 2 to " .. Stats.GIFT_LEVEL_MAX end
		local want = Ranks.xpForLevel(lv)
		if (tonumber(d.xp) or 0) >= want then return true, "already" end
		d.xp = want
	elseif n and n >= 1 and n <= Stats.GIFT_XP_MAX then
		d.xp = math.floor((tonumber(d.xp) or 0) + n)
	else
		return false, "how much"
	end
	table.insert(d.gifts, id)
	while #d.gifts > GIFT_IDS do table.remove(d.gifts, 1) end
	dirty(s)
	publish(s)
	return true, nil
end
function Stats.hasGift(p: Player, rid: string): boolean
	local d = dataOf(st[p])
	return d ~= nil and type(d.gifts) == "table" and table.find(d.gifts, string.sub(tostring(rid), 1, 80)) ~= nil
end

-- ------------------------------------------------------------------ players
local function cleanLook(p: Player, d: any)
	if type(d.look) ~= "table" then d.look = {} end
	for _, t in CardStyles.TYPES do
		local id = d.look[t]
		if type(id) ~= "string" or not CardStyles.info(t, id) then d.look[t] = CardStyles.DEFAULT[t] end
	end
	for _, k in { "wpn", "recent", "log", "fixed", "voids", "mx" } do
		if type(d[k]) ~= "table" then d[k] = {} end
	end
end

-- a card look you wore but no longer own (a test, a refund) comes off once the loot save has loaded (Loot.changed fires then, and on every change)
local function recheck(p: Player)
	local s = st[p]
	local d = dataOf(s)
	if not s or not d then return end
	for _, t in CardStyles.TYPES do
		if not owns(p, t, d.look[t]) then d.look[t] = CardStyles.DEFAULT[t]; dirty(s) end
	end
	publish(s)
end

local function added(p: Player)
	if st[p] then return end
	local s: State = { p = p, prof = nil, ready = false, cur = nil, att = {}, xpAcc = 0, budget = 20, budgetT = os.clock() }
	st[p] = s
	publish(s)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	s.prof = prof
	cleanLook(p, prof.data)
	-- (the OWNER title goes on for the creator once, the first visit after it came; they can take it off like any other)
	if creator(p) and prof.data.ownerTitle ~= true and CardStyles.info("title", "owner") then
		prof.data.ownerTitle = true
		prof.data.look.title = "owner"
		prof.dirty = true
	end
	s.ready = true
	MasteryXp.bind(p, prof.data, function() dirty(s) end) -- (weapon mastery: its XP lives in this save)
	prof.onLost.Event:Connect(function() publish(s) end)
	publish(s)
	if Loot.ready(p) then recheck(p) end -- (the loot save was first: no Loot.changed is coming)
	pull(p.UserId) -- (cheat restores left for them while they were away)
end

function Stats.init(fight: any, matches: any)
	Fight, Matches = fight, matches
	-- (a slip in here must never break a shot, a hit or a death: every hook runs in a pcall)
	local function safe(fn: any): any
		return function(...)
			local ok, err = pcall(fn, ...)
			if not ok then warn("[jankfire] stats: " .. tostring(err)) end
		end
	end
	Fight.onShot(safe(onShot))
	Fight.onHurt(safe(onHurt))
	Fight.onKill(safe(onKill))
	hookMatches()
	MasteryXp.init()
	for _, p in Players:GetPlayers() do task.spawn(added, p) end
	Players.PlayerAdded:Connect(added)
	Players.PlayerRemoving:Connect(function(p)
		local s = st[p]
		if s and s.cur then finish(p, "L", nil) end -- (leaving a match is a loss)
		-- (their log stays readable here a while: a kick for cheating comes just before the restore call)
		local d = dataOf(s)
		if d then leftLogs[p.UserId] = { t = os.clock(), log = d.log } end
		for uid, l in leftLogs do if os.clock() - l.t > 600 then leftLogs[uid] = nil end end
		st[p] = nil
		if s and s.prof then Profiles.release(store, s.prof) end
	end)
	if Loot.changed then
		Loot.changed:Connect(function(p: Player) task.defer(recheck, p) end)
	end
	-- another server restored a cheater: watch them here too, and take any fixes left for players in this server
	task.spawn(function()
		pcall(function()
			MessagingService:SubscribeAsync(FIX_TOPIC, function(msg: any)
				local m = if type(msg) == "table" then msg.Data else nil
				if type(m) ~= "table" then return end
				if type(m.w) == "number" then
					if m.uw then watched[m.w] = nil else watched[m.w] = math.min(watched[m.w] or num(m.s), num(m.s)) end
				end
				for _, uid in (if type(m.u) == "table" then m.u else {}) do
					if type(uid) == "number" and hereData(uid) then task.spawn(pull, uid) end
				end
			end)
		end)
	end)
	-- time in live rounds: the weapon in your hands, XP for the minutes
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 1 then return end
		local step = acc
		acc = 0
		for p, s in st do
			if s.cur and liveFor(s) then
				local f = Fight.byPlayer[p]
				local d = dataOf(s)
				if f and f.alive and d then
					local c = s.cur :: Cur
					d.time += step
					local held = tostring(f.held)
					held = Roster.formOf[held] or held -- (the Scythe's rifle form is time with the Scythe)
					if real(held) then
						c.wt[held] = (c.wt[held] or 0) + step
						c.rwt[held] = (c.rwt[held] or 0) + step
						wpn(d, held).t += step
					end
					s.xpAcc += step * Ranks.XP.perMinute / 60
					if s.xpAcc >= 1 then
						local n = math.floor(s.xpAcc)
						s.xpAcc -= n
						addXp(s, n)
					end
					dirty(s)
				end
			end
		end
	end)
	if RunService:IsStudio() then
		local old = ServerStorage:FindFirstChild("JankStatsTest")
		if old then old:Destroy() end
		local fn = Instance.new("BindableFunction")
		fn.Name = "JankStatsTest"
		fn.OnInvoke = function(op: string, a: any, b: any, c: any, e: any): any return Stats.test(op, a, b, c, e) end
		fn.Parent = ServerStorage
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankStatsTest)
-- a play test has one player, so a second one is stood in by a training dummy ("ghost": it counts as a player on
-- the other team for stats only, while the test player is in a match: a real one, JankMatchTest "ghost" with the
-- player in it, or a test one opened here):
--   ("begin", player, mode?, arena?, foes?) open a test match for the player (team 1) against those userIds: its key
--   ("round", player, won)             a round of it played (and won or not)
--   ("ghost", dummyName)              that dummy now counts as the enemy, and ghost matches count ("" = neither:
--                                     the default, so other sessions' Play tests never reach the owner's numbers)
--   ("finish", player, "W"|"L", score?) close it like a real match end
--   ("data", player)                  the player's saved data as it stands; ("card", target, viewer) the card viewer gets
--   ("save", player)                  write it now; ("reset", player) all numbers to zero (the look and the switch stay)
--   ("xp", player, n)                 set the XP (to see the badges)
--   ("unlock", player, on)            wear any card look this session (photos); nothing about owning is saved
--   ("put", player, data)              put a whole save back (a test's backup from "data")
-- cheat restores, with stand-in players under made-up userIds (negative ones: no real account has them):
--   ("stand", uid, online)             a stand-in with a fresh save, in this server or away; ("drop", uid) gone
--   ("fake", uid, { key, r, k, d, rp, rw, foes, mates?, team?, t? })  a finished match on a stand-in's (or a
--                                      player's) save, totals and record, as a real match end writes them
--   ("view", uid)                      a stand-in's or player's save; ("pending", uid) what waits for them
--   ("join", uid)                      a stand-in comes into this server and takes what waits
--   ("restore", uid, since) / ("undo", uid)  Stats.restoreFor / Stats.undoRestore
--   ("clean", uid)                     their pending entries gone and they're no longer watched here
function Stats.test(op: string, a: any, b: any, c: any, e: any): any
	if not RunService:IsStudio() then return nil end
	if op == "stand" then
		if not stand[a] then stand[a] = { d = template(), online = false } end
		stand[a].online = b == true
		return true
	elseif op == "drop" then
		stand[a] = nil
		return true
	elseif op == "fake" then
		local d = hereData(a) or (stand[a] and stand[a].d)
		if not d or type(b) ~= "table" then return false end
		local r = if b.r == "W" then "W" else "L"
		local t = tonumber(b.t) or os.time()
		table.insert(d.log, 1, { id = tostring(b.key), t = t, mode = "2V2", map = "RooftopV3", team = b.team or 1, r = r, k = num(b.k), d = num(b.d),
			rp = num(b.rp), rw = num(b.rw), xp = 0, foes = b.foes or {}, mates = b.mates or {} })
		d.m += 1
		if r == "W" then d.w += 1 end
		d.k += num(b.k); d.d += num(b.d); d.rp += num(b.rp); d.rw += num(b.rw)
		table.insert(d.recent, 1, { id = tostring(b.key), t = t, mode = "2V2", map = "RooftopV3", r = r, k = num(b.k), d = num(b.d), sc = ("%d-%d"):format(num(b.rw), num(b.rp) - num(b.rw)), dmg = 0 })
		while #d.recent > RECENT do table.remove(d.recent) end
		local _, s = hereData(a)
		if s then dirty(s); publish(s) end
		return true
	elseif op == "view" then
		return hereData(a) or (stand[a] and stand[a].d)
	elseif op == "pending" then
		return readPending(a)
	elseif op == "join" then
		if not stand[a] then return false end
		stand[a].online = true
		pull(a)
		return stand[a].d
	elseif op == "restore" then
		return Stats.restoreFor(a, b)
	elseif op == "undo" then
		return Stats.undoRestore(a)
	elseif op == "clean" then
		watched[a] = nil
		memPending[a] = nil
		if fixDs then pcall(function() (fixDs :: DataStore):RemoveAsync("u" .. a) end) end
		return true
	end
	if op == "ghost" then
		ghost = nil
		if type(a) == "string" and a ~= "" then
			for _, f in Fight.all do if f.kind ~= "player" and f.name == a then ghost = f end end
		end
		testCount = ghost ~= nil -- (ghost matches and the stand-in count only while this is on; "" turns it off)
		return ghost ~= nil
	end
	local p = a :: Player
	local s = st[p]
	if not s then return "no such player" end
	local d = dataOf(s)
	if op == "begin" then
		begin(p, -1, if type(b) == "string" then b else "1V1", if type(c) == "string" then c else "RooftopV2", 1, true, nil, nil, if type(e) == "table" then e else nil)
		return (s.cur :: Cur).key
	elseif op == "round" then
		local cu = s.cur
		if not cu or not d then return false end
		cu.rp += 1; d.rp += 1
		if b == true then cu.rw += 1; d.rw += 1 end
		dirty(s)
		return true
	elseif op == "put" then
		if not s.prof or type(b) ~= "table" then return false end
		s.prof.data = b
		cleanLook(p, b)
		MasteryXp.bind(p, b, function() dirty(s) end) -- (the save's table changed: weapon mastery reads the new one)
		dirty(s); publish(s)
		return true
	elseif op == "finish" then
		finish(p, if b == "W" then "W" else "L", if type(c) == "string" then c else "5-3")
		return true
	elseif op == "data" then
		return d
	elseif op == "card" then
		return cardOf(p, if typeof(b) == "Instance" then b else nil)
	elseif op == "save" then
		return if s.prof then Profiles.save(store, s.prof) else false
	elseif op == "reset" then
		if not d then return false end
		local keep = { look = d.look, private = d.private, since = d.since }
		local fresh = template()
		for k in d do d[k] = nil end
		for k, v in fresh do d[k] = v end
		d.look, d.private, d.since = keep.look, keep.private, keep.since
		dirty(s); publish(s)
		return true
	elseif op == "unlock" then
		s.devAll = b ~= false
		return s.devAll
	elseif op == "xp" then
		if not d then return false end
		d.xp = math.max(0, math.floor(tonumber(b) or 0))
		dirty(s); publish(s)
		return d.xp
	end
	return nil
end

return Stats
