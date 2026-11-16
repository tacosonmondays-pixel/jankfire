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
-- XP: +20 a kill on a player, +50 a round won, 2 a minute of live match time (web room.js).
--
-- the remote ReplicatedStorage.JankfireRemotes.Profile (RemoteFunction), always a table { ok, why?, ... }:
--   ("card", userId)    -> { card }: anyone in this server. a private player's card has no stats/weapons/recent
--   ("list")            -> { players = { { id, name, display, xp, look, private } } }: everyone here, for the player list
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

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Ranks = require(Shared:WaitForChild("Ranks"))
local CardStyles = require(Shared:WaitForChild("CardStyles"))
local Roster = require(Shared:WaitForChild("Roster"))
local Profiles = require(script.Parent:WaitForChild("Profiles"))
local Loot = require(script.Parent:WaitForChild("Loot"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Profile") :: RemoteFunction

local Stats = {}
local RECENT = 10

local function template(): any
	return { v = 1, xp = 0, k = 0, d = 0, m = 0, w = 0, rp = 0, rw = 0, sh = 0, hi = 0, hc = 0, hs = 0, hk = 0, dmg = 0, best = 0, time = 0,
		wpn = {}, recent = {}, look = { border = CardStyles.DEFAULT.border, banner = CardStyles.DEFAULT.banner, title = CardStyles.DEFAULT.title },
		private = false, since = os.time() }
end
local store = Profiles.new("JankfireStats_v1", template)

type Fighter = any
-- the match you are in, as far as stats go
type Cur = { id: number, mode: string, arena: string, team: number, k: number, d: number, dmg: number,
	wt: { [string]: number }, streak: number, t0: number, test: boolean?, m: any? } -- (m: the match itself)
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

-- only real weapons count: a live weapon or item of the roster. a test hook's "test" damage, a dummy's own gun or
-- anything else made up never reaches the numbers
local function real(wid: any): boolean
	local e = if type(wid) == "string" then Roster.byId[wid] else nil
	return e ~= nil and e.live == true
end

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
	dirty(s)
	publish(s)
end

-- is this player's match one that counts right now (the round live)?
local function liveFor(s: State?): boolean
	if not s or not s.cur then return false end
	local c = s.cur :: Cur
	if c.test then return true end
	if c.m and c.m.ghost and not testCount then return false end -- (a Studio ghost match: not real)
	local mi = Matches.matchOf(s.p)
	return mi ~= nil and mi.id == c.id and mi.phase == "live"
end
local function stateOf(f: Fighter?): State?
	if not f or f.kind ~= "player" then return nil end
	return st[f.ref :: Player]
end
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
	local s = stateOf(by)
	local d = dataOf(s)
	if not s or not d or not s.cur then return end
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
	if not sk or not dk or not sk.cur then lastHit[v] = nil; return end
	local c = sk.cur :: Cur
	local wid = if info.w == "void" and type(info.via) == "string" then info.via else info.w
	if not real(wid) then lastHit[v] = nil; return end
	dk.k += 1
	c.k += 1
	wpn(dk, wid).k += 1
	c.streak += 1
	if c.streak > (tonumber(dk.best) or 0) then dk.best = c.streak end
	local lh = lastHit[v]
	if info.w ~= "void" and lh and lh.by == k and lh.hs and os.clock() - lh.t < 2 then dk.hk += 1 end
	lastHit[v] = nil
	dirty(sk)
	addXp(sk, Ranks.XP.kill)
end

-- ------------------------------------------------------------------ matches
local function begin(p: Player, id: number, mode: string, arena: string, team: number, test: boolean?, m: any?)
	local s = st[p]
	if not s then return end
	s.cur = { id = id, mode = mode, arena = arena, team = team, k = 0, d = 0, dmg = 0, wt = {}, streak = 0, t0 = os.time(), test = test, m = m }
	s.att = {}
end

-- the match is over for this player: W or L (leaving = L), "5-3" (their wins first)
local function finish(p: Player, res: string, score: string?)
	local s = st[p]
	if not s or not s.cur then return end
	local c = s.cur :: Cur
	s.cur = nil
	s.att = {}
	local d = dataOf(s)
	if not d then return end
	if c.m and c.m.ghost and not testCount then return end -- (a Studio ghost match is never recorded)
	d.m += 1
	if res == "W" then d.w += 1 end
	local top, best = nil, -1
	for wid, t in c.wt do if t > best then top, best = wid, t end end
	table.insert(d.recent, 1, { t = os.time(), mode = c.mode, map = c.arena, r = res, k = c.k, d = c.d, w = top, sc = score or "", dmg = math.floor(c.dmg + 0.5) })
	while #d.recent > RECENT do table.remove(d.recent) end
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
		for t, list in m.teams do
			for _, p in list do begin(p, m.id, tostring(m.mode or ""), tostring(m.arena or ""), t, nil, m) end
		end
	end)
	Matches.onRound(function(m: any, winner: number)
		if m.ghost and not testCount then return end
		for t, list in m.teams do
			for _, p in list do
				local s = st[p]
				local d = dataOf(s)
				if s and d and s.cur and (s.cur :: Cur).id == m.id then
					d.rp += 1
					if t == winner then d.rw += 1; addXp(s, Ranks.XP.roundWin) end
					dirty(s)
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
local SHOWN = { "k", "d", "m", "w", "rp", "rw", "sh", "hi", "hc", "hs", "hk", "dmg", "best", "time" }
local function cardOf(target: Player, viewer: Player?): any
	local s = st[target]
	local d = dataOf(s)
	local card: any = { id = target.UserId, name = target.Name, display = target.DisplayName, ready = s ~= nil and s.ready }
	if not d then
		card.xp, card.look, card.private = 0, table.clone(CardStyles.DEFAULT), false
		return card
	end
	card.xp = math.floor(tonumber(d.xp) or 0)
	card.look = { border = d.look.border, banner = d.look.banner, title = d.look.title }
	card.private = d.private == true
	card.since = d.since
	if card.private and viewer ~= target then return card end
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
	return card
end

local function owns(p: Player, t: string, id: string): boolean
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
			table.insert(out, { id = o.UserId, name = o.Name, display = o.DisplayName, xp = if d then math.floor(tonumber(d.xp) or 0) else 0,
				look = if d then { border = d.look.border, banner = d.look.banner, title = d.look.title } else table.clone(CardStyles.DEFAULT),
				private = d ~= nil and d.private == true })
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

-- ------------------------------------------------------------------ players
local function cleanLook(p: Player, d: any)
	if type(d.look) ~= "table" then d.look = {} end
	for _, t in CardStyles.TYPES do
		local id = d.look[t]
		if type(id) ~= "string" or not CardStyles.info(t, id) then d.look[t] = CardStyles.DEFAULT[t] end
	end
	if type(d.wpn) ~= "table" then d.wpn = {} end
	if type(d.recent) ~= "table" then d.recent = {} end
end

-- a card look you wore but no longer own (a test, a refund) comes off once the loot save has loaded (Loot.changed fires then, and on every change)
local function recheck(p: Player)
	local s = st[p]
	local d = dataOf(s)
	if not s or not d then return end
	for _, t in CardStyles.TYPES do
		if not owns(p, t, d.look[t]) then d.look[t] = CardStyles.DEFAULT[t]; dirty(s) end
	end
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
	s.ready = true
	prof.onLost.Event:Connect(function() publish(s) end)
	publish(s)
	if Loot.ready(p) then recheck(p) end -- (the loot save was first: no Loot.changed is coming)
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
	for _, p in Players:GetPlayers() do task.spawn(added, p) end
	Players.PlayerAdded:Connect(added)
	Players.PlayerRemoving:Connect(function(p)
		local s = st[p]
		if s and s.cur then finish(p, "L", nil) end -- (leaving a match is a loss)
		st[p] = nil
		if s and s.prof then Profiles.release(store, s.prof) end
	end)
	if Loot.changed then
		Loot.changed:Connect(function(p: Player) task.defer(recheck, p) end)
	end
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
					if real(held) then
						c.wt[held] = (c.wt[held] or 0) + step
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
		fn.OnInvoke = function(op: string, a: any, b: any, c: any): any return Stats.test(op, a, b, c) end
		fn.Parent = ServerStorage
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankStatsTest)
-- a play test has one player, so a second one is stood in by a training dummy ("ghost": it counts as a player on
-- the other team for stats only, while the test player is in a match: a real one, JankMatchTest "ghost" with the
-- player in it, or a test one opened here):
--   ("begin", player, mode?, arena?)  open a test match for the player (team 1)
--   ("ghost", dummyName)              that dummy now counts as the enemy, and ghost matches count ("" = neither:
--                                     the default, so other sessions' Play tests never reach the owner's numbers)
--   ("finish", player, "W"|"L", score?) close it like a real match end
--   ("data", player)                  the player's saved data as it stands; ("card", target, viewer) the card viewer gets
--   ("save", player)                  write it now; ("reset", player) all numbers to zero (the look and the switch stay)
--   ("xp", player, n)                 set the XP (to see the badges)
--   ("unlock", player, on)            wear any card look this session (photos); nothing about owning is saved
function Stats.test(op: string, a: any, b: any, c: any): any
	if not RunService:IsStudio() then return nil end
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
		begin(p, -1, if type(b) == "string" then b else "1V1", if type(c) == "string" then c else "RooftopV2", 1, true)
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
