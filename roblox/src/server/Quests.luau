--!strict
-- DAILY QUESTS, BRASS AND THE WEEKLY TRACK (roblox/docs/QUESTS.md). the owner, 17 Nov 2026: "Add daily quests for
-- rewards!! ... maybe a different currency and weekly rewards grant you a case or maybe tickets to eventually redeem a
-- case? I don't want to be too too charitable". the numbers and the pool are Shared.QuestData.
--   * 3 quests a day (easy, medium, hard), new at 00:00 UTC, one free reroll. a finished quest pays Brass and weekly
--     points at once; the weekly bar pays Brass and Crate Tickets at its steps (Monday 00:00 UTC it starts again).
--   * everything counts here, on the server, from real matches only: the same rules as the player cards' stats
--     (Stats.luau: opposite teams of one match, the round live, live Roster weapons) plus a took-part rule (no AFK):
--     a match counts for play / win quests only if you hurt an enemy in it, a round only if you hurt one in that round.
--     the hub, training dummies and Studio ghost matches never count. one exception: range quests take a finished run's
--     score on Cardboard Carl's (RangeTest.onRun), which the range itself keeps honest.
--   * one session-locked save per player (Profiles.luau), its own store: "JankfireQuests_v1" ("_studio" in Studio).
--   * redeems: tickets or Brass -> a container through Loot.grant with a unique receipt id (idempotent), a pending
--     entry in between so a crash never loses or doubles one.
--   * cheaters: Quests.restoreFor(userId, since) / Quests.undoRestore(userId), the anti-cheat's calls (Stats' shape).
--
-- the remote ReplicatedStorage.JankfireRemotes.Quests (RemoteFunction), always a table { ok, why?, ... }:
--   ("state")                -> the state (below)
--   ("reroll", slot)         -> swap that quest (not done) for another of its tier: once a day, free
--   ("redeem", kind, cur)    -> kind "crate"|"bag"|"spray", cur "tix"|"brass": { ok, why?, stock, state }
--   ("seen")                 -> the panel was opened (QuestNews goes off)
-- the state: { brass, tix, owed?, list = { { slot, id, tier, text, goal, n, done } x3 }, rerolls (left today), pts,
--   got (steps paid), dayLeft, weekLeft (s), save, frozen }
-- JankfireRemotes.QuestPush (RemoteEvent) to the client: { t = "done", id, text, tier, brass, pts } (a quest finished),
-- { t = "step", i, at, brass?, tix? } (a weekly step paid), { t = "state", state } (progress moved)
-- player attributes: Brass, CrateTickets, QuestsDone (today's, 0-3), QuestSave ("loading"|"cloud"|"off"|"lost"),
-- QuestNews (true: something new since the panel was last opened: today's quests not looked at, a quest finished or a
-- weekly step paid since. rewards pay themselves, so there's never anything to claim: this is the badge over Dune)
-- Studio play tests: ServerStorage.JankQuestTest (BindableFunction), Quests.test at the end.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local DataStoreService = game:GetService("DataStoreService")
local MessagingService = game:GetService("MessagingService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local QD = require(Shared:WaitForChild("QuestData"))
local Roster = require(Shared:WaitForChild("Roster"))
local Config = require(Shared:WaitForChild("Config"))
local Profiles = require(script.Parent:WaitForChild("Profiles"))
local Loot = require(script.Parent:WaitForChild("Loot"))

-- the remotes (in the saved place and default.project.json; made here too if missing)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
for name, class in { Quests = "RemoteFunction", QuestPush = "RemoteEvent" } do
	if not Remotes:FindFirstChild(name) then
		local r = Instance.new(class)
		r.Name = name
		r.Parent = Remotes
	end
end
local Remote = Remotes:WaitForChild("Quests") :: RemoteFunction
local PushR = Remotes:WaitForChild("QuestPush") :: RemoteEvent

local STUDIO = RunService:IsStudio()
local Quests = {}
local EARN_DAYS = 60 -- days of pay kept per day (what a cheat restore can take back)
local GRAPPLE_AFTER = 1.5 -- s after letting go of the rope that a kill still counts as on the grapple
local ROPE_MAX = 10 -- s: a rope older than this with no word from the client is let go
local LOOT_FREE_CAP = 10 -- (Loot.luau BUY_MAX: free stock past this is lost)

local function template(): any
	return { v = 1, brass = 0, tix = 0, day = -1, list = {}, rolls = 0, avoid = {}, week = -1, pts = 0, got = 0,
		earned = {}, owed = { b = 0, x = 0 }, pending = {}, nextId = 1, voids = {}, total = { quests = 0, brass = 0, tix = 0 },
		grants = {}, gday = -1, gsum = 0, -- (Quests.grant: other modules' Brass, the last 50, and today's sum for the cap)
		news = true } -- (something new since the panel was last opened: today's roll, a finished quest, a step paid)
end
local store = Profiles.new(if STUDIO then "JankfireQuests_studio" else "JankfireQuests_v1", template)

type Fighter = any
-- the match you're in, as far as quests go
type Cur = { id: number, team: number, m: any, act: boolean, ract: boolean, streak: number, ranked: boolean, party: boolean }
type State = { p: Player, prof: Profiles.Profile?, ready: boolean, cur: Cur?, budget: number, budgetT: number,
	roped: boolean, hookT: number, relT: number, itemN: number?, item: string?, busy: boolean, pushAt: number?, conns: { RBXScriptConnection } }
local st: { [Player]: State } = {}
local lastHit: { [Fighter]: { by: Fighter, hs: boolean, t: number } } = setmetatable({}, { __mode = "k" }) :: any
local Fight: any
local Matches: any
local watched: { [number]: number } = {} -- cheaters restored (userId -> since): nothing more counts for them here
-- (Studio tests) a dummy that counts as an enemy player, and whether ghost / held matches count (off by default, so
-- nobody else's Play test ever moves quests)
local ghost: Fighter? = nil
local testCount = false
local offset = 0 -- (Studio tests: the quest clock moved, "clock")
local function now(): number return os.time() + offset end
local clock = os.clock

local function num(v: any): number return tonumber(v) or 0 end
local function real(wid: any): boolean
	local e = if type(wid) == "string" then Roster.byId[wid] else nil
	return e ~= nil and e.live == true
end
local function dataOf(s: State?): any
	return if s and s.prof then s.prof.data else nil
end
local function dirty(s: State)
	if s.prof then s.prof.dirty = true end
end

-- ------------------------------------------------------------------ the day, the week, the wallet
-- a new UTC day: three new quests (none of yesterday's), the reroll back
local function freshDay(uid: number, d: any): boolean
	local day = QD.day(now())
	if d.day == day and #d.list == #QD.ORDER then return false end
	local avoid = {}
	for _, e in d.list do if type(e) == "table" then avoid[e.id] = true end end
	d.list = {}
	for i, tier in QD.ORDER do
		local id = QD.roll(uid, day, tier, 0, avoid)
		avoid[id] = true
		d.list[i] = { id = id, n = 0, done = false }
	end
	d.day, d.rolls, d.avoid = day, 0, {}
	d.news = true
	return true
end
local function freshWeek(d: any): boolean
	local wk = QD.week(now())
	if d.week == wk then return false end
	d.week, d.pts, d.got = wk, 0, 0
	return true
end
local function fresh(s: State): boolean
	local d = dataOf(s)
	if not d then return false end
	local a = freshDay(s.p.UserId, d)
	local b = freshWeek(d)
	if a or b then dirty(s) end
	return a or b
end

-- pay into the wallet: what a restore made owed is paid off first. track = keep it in the day's pay (a restore takes
-- that back); a restore's own refund isn't tracked
local function credit(d: any, b: number, x: number, track: boolean)
	local ob = math.min(b, num(d.owed.b)); b -= ob; d.owed.b = num(d.owed.b) - ob
	local ox = math.min(x, num(d.owed.x)); x -= ox; d.owed.x = num(d.owed.x) - ox
	d.brass = num(d.brass) + b
	d.tix = num(d.tix) + x
	if not track or (b <= 0 and x <= 0) then return end
	d.total.brass = num(d.total.brass) + b
	d.total.tix = num(d.total.tix) + x
	local today = QD.day(now())
	local key = tostring(today)
	local e = d.earned[key]
	if type(e) ~= "table" then e = { b = 0, x = 0 }; d.earned[key] = e end
	e.b = num(e.b) + b; e.x = num(e.x) + x
	for k in d.earned do if (tonumber(k) or 0) < today - EARN_DAYS then d.earned[k] = nil end end
end

local function publish(s: State)
	local p = s.p
	if not p.Parent then return end
	local d = dataOf(s)
	p:SetAttribute("Brass", if d then math.floor(num(d.brass)) else 0)
	p:SetAttribute("CrateTickets", if d then math.floor(num(d.tix)) else 0)
	local done = 0
	if d and d.day == QD.day(now()) then for _, e in d.list do if e.done then done += 1 end end end
	p:SetAttribute("QuestsDone", done)
	p:SetAttribute("QuestNews", d ~= nil and d.news == true)
	p:SetAttribute("QuestSave", if not s.ready then "loading" elseif s.prof then s.prof.state else "off")
end

local function stateFor(s: State): any
	local d = dataOf(s)
	if not d then return { ok = false, why = "your quests are still loading" } end
	fresh(s)
	local list = {}
	for i, e in d.list do
		local q = QD.byId[e.id]
		if q then table.insert(list, { slot = i, id = q.id, tier = q.tier, text = q.text, goal = q.goal, n = math.min(q.goal, math.floor(num(e.n))), done = e.done == true }) end
	end
	local t = now()
	local owed = if num(d.owed.b) > 0 or num(d.owed.x) > 0 then { b = num(d.owed.b), x = num(d.owed.x) } else nil
	return { ok = true, brass = math.floor(num(d.brass)), tix = math.floor(num(d.tix)), owed = owed, list = list,
		rerolls = math.max(0, QD.REROLLS - num(d.rolls)), pts = num(d.pts), got = num(d.got),
		dayLeft = QD.dayLeft(t), weekLeft = QD.weekLeft(t), save = if s.prof then s.prof.state else "off",
		frozen = watched[s.p.UserId] ~= nil }
end
-- progress moved: the client gets the state again (at most every 0.4 s: the loop below sends it)
local function soon(s: State)
	if not s.pushAt then s.pushAt = clock() + 0.4 end
end
local function push(s: State, msg: any)
	if s.p.Parent then PushR:FireClient(s.p, msg) end
end

-- ------------------------------------------------------------------ progress
local function complete(s: State, q: QD.Quest)
	local d = dataOf(s)
	local tier = QD.TIERS[q.tier]
	credit(d, tier.brass, 0, true)
	d.total.quests = num(d.total.quests) + 1
	freshWeek(d)
	d.pts = num(d.pts) + tier.pts
	d.news = true
	push(s, { t = "done", id = q.id, text = q.text, tier = q.tier, brass = tier.brass, pts = tier.pts })
	while num(d.got) < #QD.STEPS and d.pts >= QD.STEPS[num(d.got) + 1].at do
		d.got = num(d.got) + 1
		local step = QD.STEPS[d.got]
		credit(d, step.brass or 0, step.tix or 0, true)
		push(s, { t = "step", i = d.got, at = step.at, brass = step.brass, tix = step.tix })
	end
	-- (paid: worth writing soon)
	if s.prof and s.prof.state == "cloud" then task.spawn(Profiles.save, store, s.prof) end
end

-- n more of `stat` (or, for a "best of" quest, a value of n). today's quests that count it move
local function bump(s: State?, stat: string, n: number)
	if not s or not s.ready or n <= 0 or watched[s.p.UserId] then return end
	local d = dataOf(s)
	if not d then return end
	fresh(s)
	local moved = false
	for _, e in d.list do
		local q = QD.byId[e.id]
		if q and not e.done and q.stat == stat then
			local was = num(e.n)
			e.n = if q.max then math.max(was, n) else was + n
			if e.n ~= was then moved = true end
			if e.n >= q.goal then
				e.n, e.done = q.goal, true
				complete(s, q)
			end
		end
	end
	if moved then
		dirty(s)
		publish(s)
		soon(s)
	end
end
Quests.bump = function(p: Player, stat: string, n: number) bump(st[p], stat, n) end

-- ------------------------------------------------------------------ Brass from other modules (the VIP daily reward)
-- Quests.grant(player, amount, reason, id?) -> (ok, why?): Brass only (Crate Tickets come from the weekly track and
-- nowhere else). logged (the save keeps the last 50, and the output says it), capped at GRANT_DAY Brass a UTC day per
-- player across every caller, and idempotent by id ("vipdaily:<day>": the same id twice pays once, the second answers
-- true, "already"). false, "loading" = the save isn't loaded yet: try again later. what it pays counts as earned that
-- day, so a cheat restore takes it back too
Quests.GRANT_DAY = 300
function Quests.grant(p: Player, amount: number, reason: string, id: string?): (boolean, string?)
	local s = st[p]
	if not s or not s.ready or not s.prof then return false, "loading" end
	if type(amount) ~= "number" or amount ~= amount or amount < 1 or amount == math.huge then return false, "bad amount" end
	if type(reason) ~= "string" or reason == "" then return false, "no reason" end
	if id ~= nil and type(id) ~= "string" then return false, "bad id" end
	if watched[p.UserId] then return false, "on hold" end
	local d = s.prof.data
	if id then for _, g in d.grants do if type(g) == "table" and g.id == id then return true, "already" end end end
	local n = math.floor(amount)
	local today = QD.day(now())
	if d.gday ~= today then d.gday, d.gsum = today, 0 end
	if num(d.gsum) + n > Quests.GRANT_DAY then return false, "over today's cap" end
	-- (true only once it's written: a failed save takes it all back, and the caller tries again later with the same id)
	local before = { brass = num(d.brass), owed = num(d.owed.b), gsum = num(d.gsum), tb = num(d.total.brass),
		day = tostring(today), e = if type(d.earned[tostring(today)]) == "table" then table.clone(d.earned[tostring(today)]) else nil }
	d.gsum = num(d.gsum) + n
	credit(d, n, 0, true)
	table.insert(d.grants, 1, { t = now(), b = n, why = string.sub(reason, 1, 40), id = id })
	while #d.grants > 50 do table.remove(d.grants) end
	dirty(s)
	local prof = s.prof :: Profiles.Profile
	local saved = if prof.state == "cloud" then Profiles.save(store, prof) else prof.state == "off"
	if not saved then
		d.brass, d.owed.b, d.gsum, d.total.brass = before.brass, before.owed, before.gsum, before.tb
		d.earned[before.day] = before.e
		table.remove(d.grants, 1)
		publish(s)
		return false, "couldn't save"
	end
	publish(s)
	soon(s)
	print(("[jankfire] quests: +%d Brass to %s (%s)"):format(n, p.Name, reason))
	return true, nil
end
-- the owner's gift (OwnerDev.server's GIFT tab, 18 Nov 2026): Quests.gift(player, brass, tickets, id) -> (ok, why?).
-- not capped (the owner's own call, checked there: the place's creator only), idempotent by id, logged in grants like
-- Quests.grant, written before it answers true. not counted as earned (a gift isn't play): a cheat restore leaves it
function Quests.gift(p: Player, brass: number, tix: number, id: string): (boolean, string?)
	local s = st[p]
	if not s or not s.ready or not s.prof then return false, "loading" end
	local b = if type(brass) == "number" and brass == brass and brass ~= math.huge then math.max(0, math.floor(brass)) else 0
	local x = if type(tix) == "number" and tix == tix and tix ~= math.huge then math.max(0, math.floor(tix)) else 0
	if b <= 0 and x <= 0 then return false, "nothing to give" end
	if type(id) ~= "string" or id == "" then return false, "no id" end
	local d = s.prof.data
	for _, g in d.grants do if type(g) == "table" and g.id == id then return true, "already" end end
	local before = { brass = num(d.brass), tix = num(d.tix), ob = num(d.owed.b), ox = num(d.owed.x) }
	credit(d, b, x, false)
	table.insert(d.grants, 1, { t = now(), b = b, x = x, why = "owner gift", id = id })
	while #d.grants > 50 do table.remove(d.grants) end
	dirty(s)
	local prof = s.prof :: Profiles.Profile
	local saved = if prof.state == "cloud" then Profiles.save(store, prof) else prof.state == "off"
	if not saved then
		d.brass, d.tix, d.owed.b, d.owed.x = before.brass, before.tix, before.ob, before.ox
		table.remove(d.grants, 1)
		publish(s)
		return false, "couldn't save"
	end
	publish(s)
	print(("[jankfire] quests: owner gift +%d Brass +%d tickets to %s"):format(b, x, p.Name))
	return true, nil
end
-- the VIP daily's call (the shop session): Quests.giveBrass(player, amount, receiptId) -> boolean, written to the save
function Quests.giveBrass(p: Player, amount: number, receiptId: string): boolean
	local ok = Quests.grant(p, amount, "vip daily", receiptId)
	return ok
end

-- ------------------------------------------------------------------ what counts
local function stateOf(f: Fighter?): State?
	if not f or f.kind ~= "player" then return nil end
	return st[f.ref :: Player]
end
-- a Studio ghost or held match (Matches.test "ghost", the Play queue's stand-in "hold")
local function isGhost(c: Cur): boolean return c.m ~= nil and c.m.ghost ~= nil end
-- does this player's match count at all (not a cheater restored here, not a ghost unless a test said so)
local function matchCounts(s: State, c: Cur): boolean
	if watched[s.p.UserId] then return false end
	if isGhost(c) and not testCount then return false end
	if c.m ~= nil and c.m.dev then return false end -- (a match the owner used dev powers in, OwnerDev.server: counts for nothing)
	if c.m ~= nil and c.m.private then return false end -- (a party alone, a private duel: Party.luau, counts for nothing)
	return true
end
-- the took-part rule, waived only for a Studio test's ghost match (nobody to hurt in one)
local function waived(c: Cur): boolean return STUDIO and testCount and isGhost(c) end
-- does it count right now (the round live)
local function live(s: State?): boolean
	if not s or not s.ready or not s.cur then return false end
	local c = s.cur :: Cur
	if not matchCounts(s, c) then return false end
	local mi = Matches.matchOf(s.p)
	return mi ~= nil and mi.id == c.id and mi.phase == "live"
end
-- two fighters on opposite teams of one match (or the test player and the test ghost)
local function enemies(a: Fighter?, b: Fighter?): boolean
	if not a or not b or a == b then return false end
	local sa, sb = stateOf(a), stateOf(b)
	if sa and sb then
		local ca, cb = sa.cur, sb.cur
		return ca ~= nil and cb ~= nil and ca.id == cb.id and ca.team ~= cb.team
	end
	if ghost and testCount and (a == ghost or b == ghost) then
		local s = sa or sb
		return s ~= nil and s.cur ~= nil
	end
	return false
end

local function onHurt(t: Fighter, done: number, by: Fighter?, wid: string, hs: boolean?)
	if not by or not real(wid) or not enemies(by, t) then return end
	lastHit[t] = { by = by, hs = hs == true, t = clock() }
	local s = stateOf(by)
	if not live(s) or done <= 0 then return end
	local c = (s :: State).cur :: Cur
	c.act, c.ract = true, true
	bump(s, "dmg", done)
	if hs then bump(s, "hs", 1) end
end

local function onKill(info: any)
	local v, k = info.v, info.k
	local sv = stateOf(v)
	if sv and sv.cur then (sv.cur :: Cur).streak = 0 end
	local lh = lastHit[v]
	lastHit[v] = nil
	if not k or not enemies(k, v) then return end
	local sk = stateOf(k)
	if not sk or not live(sk) then return end
	local wid = if info.w == "void" and type(info.via) == "string" then info.via else info.w
	if wid == "parry" then wid = "katana" end -- (a parry kill is the parrier's katana: a perfect parry's shot sent back, or a fall after a parry shove)
	if not real(wid) then return end
	local c = sk.cur :: Cur
	c.act, c.ract = true, true
	c.streak += 1
	bump(sk, "kill", 1)
	for _, cid in QD.CLASS_OF[wid] or {} do bump(sk, "kill:" .. cid, 1) end
	if info.w == "void" then bump(sk, "voidkill", 1) end
	if info.w ~= "void" and lh and lh.by == k and lh.hs and clock() - lh.t < 2 then bump(sk, "hskill", 1) end
	local ch = sk.p.Character
	if ch and ch:GetAttribute("Pose") == "slide" then bump(sk, "slidekill", 1) end
	if (sk.roped and clock() - sk.hookT < ROPE_MAX) or clock() - sk.relT < GRAPPLE_AFTER then bump(sk, "grapplekill", 1) end
	if wid == "sniper" and info.w ~= "void" then
		local a, b = Fight.root(k), Fight.root(v)
		if a and b and (a.Position - b.Position).Magnitude >= QD.LONG * Config.S then bump(sk, "longkill", 1) end
	end
	bump(sk, "streak", c.streak)
end

-- in a party of two or more when the match started (Party.sizeOf; before that existed: a teammate in the same party)
local function inParty(p: Player, mates: { Player }): boolean
	local pm = script.Parent:FindFirstChild("Party")
	if pm then
		local ok, P = pcall(require, pm)
		if ok and type(P) == "table" and type((P :: any).sizeOf) == "function" then
			local ok2, n = pcall((P :: any).sizeOf, p)
			if ok2 and type(n) == "number" then return n >= 2 end
		end
	end
	local id = p:GetAttribute("Party")
	if id == nil then return false end
	for _, o in mates do if o ~= p and o:GetAttribute("Party") == id then return true end end
	return false
end

local function hookMatches()
	Matches.onStart(function(m: any)
		for t, list in m.teams do
			for _, p in list do
				local s = st[p]
				if s then
					s.cur = { id = m.id, team = t, m = m, act = false, ract = false, streak = 0, ranked = m.ranked == true, party = inParty(p, list) }
				end
			end
		end
	end)
	Matches.onRound(function(m: any, winner: number)
		for t, list in m.teams do
			for _, p in list do
				local s = st[p]
				local c = s and s.cur
				if s and c and c.id == m.id then
					if t == winner and matchCounts(s, c) and (c.ract or waived(c)) then bump(s, "round", 1) end
					c.ract = false
				end
			end
		end
	end)
	Matches.onEnd(function(m: any, winner: number?)
		for t, list in m.teams do
			for _, p in list do
				local s = st[p]
				local c = s and s.cur
				if s and c and c.id == m.id then
					s.cur = nil
					if matchCounts(s, c) and (c.act or waived(c)) then
						bump(s, "play", 1)
						if c.ranked then bump(s, "ranked", 1) end
						if c.party then bump(s, "party", 1) end
						if winner == t then
							bump(s, "win", 1)
							if c.ranked then bump(s, "rankedwin", 1) end
							local clean = true
							for t2, w in m.wins do if t2 ~= t and num(w) > 0 then clean = false end end
							if clean then bump(s, "flawless", 1) end
						end
					end
				end
			end
		end
	end)
end

-- the item on G: Utility.luau publishes the charges left (ItemN); one fewer of the same item in a live round = a use
local function watchItems(s: State)
	local p = s.p
	s.itemN, s.item = p:GetAttribute("ItemN") :: number?, p:GetAttribute("Item") :: string?
	table.insert(s.conns, p:GetAttributeChangedSignal("ItemN"):Connect(function()
		local n, it = p:GetAttribute("ItemN"), p:GetAttribute("Item")
		local was, wasItem = s.itemN, s.item
		s.itemN, s.item = if type(n) == "number" then n else nil, if type(it) == "string" then it else nil
		if type(n) == "number" and type(was) == "number" and it == wasItem and n < was and real(it) and live(s) then
			bump(s, "item", was - n)
		end
	end))
	table.insert(s.conns, p:GetAttributeChangedSignal("Item"):Connect(function()
		local n, it = p:GetAttribute("ItemN"), p:GetAttribute("Item")
		s.itemN, s.item = if type(n) == "number" then n else nil, if type(it) == "string" then it else nil
	end))
	table.insert(s.conns, p.CharacterAdded:Connect(function() s.roped = false end))
end

-- ------------------------------------------------------------------ redeems
local function stockOf(p: Player): { [string]: number }
	local out = {}
	local raw = p:GetAttribute("LootStock")
	if type(raw) == "string" then
		for k, v in string.gmatch(raw, "(%w+)=(%d+)") do out[k] = tonumber(v) or 0 end
	end
	return out
end

local function grantNow(p: Player, kind: string, id: string): boolean
	local ok, res = pcall(Loot.grant, p, kind, id)
	return ok and res == true
end

local function redeem(s: State, kind: unknown, cur: unknown): any
	local p = s.p
	local d = dataOf(s)
	if not d then return { ok = false, why = "your quests are still loading" } end
	local price = if type(kind) == "string" then QD.PRICES[kind] else nil
	if not price then return { ok = false, why = "no such container" } end
	if cur ~= "tix" and cur ~= "brass" then return { ok = false, why = "nope" } end
	local cost = (price :: any)[cur]
	if type(cost) ~= "number" then return { ok = false, why = if cur == "brass" then "Brass can't buy that" else "tickets can't buy that" } end
	local have = if cur == "tix" then num(d.tix) else num(d.brass)
	if have < cost then return { ok = false, why = if cur == "tix" then "not enough Crate Tickets" else "not enough Brass" } end
	if watched[p.UserId] then return { ok = false, why = "your rewards are on hold" } end
	if not Loot.ready(p) then return { ok = false, why = "your inventory is still loading" } end
	if Config.LOOT_FREE and (stockOf(p)[kind :: string] or 0) >= LOOT_FREE_CAP then return { ok = false, why = "you have 10 of those: open some first" } end
	if s.busy then return { ok = false, why = "one at a time" } end
	s.busy = true
	local id = ("q%d-%d"):format(p.UserId, num(d.nextId))
	d.nextId = num(d.nextId) + 1
	if cur == "tix" then d.tix -= cost else d.brass -= cost end
	d.pending[id] = { kind = kind, cur = cur, price = cost, t = now() }
	dirty(s)
	local prof = s.prof :: Profiles.Profile
	local saved = if prof.state == "cloud" then Profiles.save(store, prof) else prof.state == "off"
	local granted = saved and grantNow(p, kind :: string, id)
	if not granted then
		-- (not written, or loot said no: the price comes back)
		if cur == "tix" then d.tix += cost else d.brass += cost end
	end
	d.pending[id] = nil
	dirty(s)
	s.busy = false
	publish(s)
	if prof.state == "cloud" then task.spawn(Profiles.save, store, prof) end
	if not granted then return { ok = false, why = if saved then "the shop couldn't hand it over. try again" else "couldn't save. try again" } end
	return { ok = true, kind = kind, id = id, stock = stockOf(p), state = stateFor(s) }
end

-- a redeem a crash left half done: Loot.grant with the same id either finds it given (true) or gives it now. false
-- with the loot save loaded = it was never given: the price comes back. loot not loaded: it waits for the next join
local function settle(s: State)
	local d = dataOf(s)
	if not d or next(d.pending) == nil then return end
	local t0 = clock()
	while s.p.Parent and not Loot.ready(s.p) and clock() - t0 < 60 do task.wait(1) end
	if not s.p.Parent or not Loot.ready(s.p) then return end
	for id, e in table.clone(d.pending) do
		if type(e) == "table" and grantNow(s.p, tostring(e.kind), id) then
			d.pending[id] = nil
		elseif type(e) == "table" then
			if e.cur == "tix" then d.tix = num(d.tix) + num(e.price) else d.brass = num(d.brass) + num(e.price) end
			d.pending[id] = nil
		end
	end
	dirty(s)
	publish(s)
end

-- ------------------------------------------------------------------ the remote
local function spend(s: State): boolean
	local t = clock()
	s.budget = math.min(10, s.budget + (t - s.budgetT) * 3); s.budgetT = t
	if s.budget < 1 then return false end
	s.budget -= 1
	return true
end

local function handle(p: Player, op: unknown, a: unknown, b: unknown): any
	local s = st[p]
	if not s or not s.ready then return { ok = false, why = "your quests are still loading" } end
	if not spend(s) then return { ok = false, why = "slow down" } end
	if op == "state" then return stateFor(s) end
	if op == "seen" then -- (the panel was opened: nothing new any more, QuestNews off)
		local d0 = dataOf(s)
		if d0 and d0.news then d0.news = false; dirty(s); publish(s) end
		return { ok = true }
	end
	local d = dataOf(s)
	if not d then return { ok = false, why = "your quests are still loading" } end
	if op == "reroll" then
		fresh(s)
		local slot = if type(a) == "number" then math.floor(a) else 0
		local e = d.list[slot]
		local q = e and QD.byId[e.id]
		if not e or not q then return { ok = false, why = "no such quest" } end
		if e.done then return { ok = false, why = "that one's done" } end
		if num(d.rolls) >= QD.REROLLS then return { ok = false, why = "no rerolls left today" } end
		local avoid = table.clone(d.avoid)
		for _, o in d.list do avoid[o.id] = true end
		local id = QD.roll(p.UserId, QD.day(now()), q.tier, num(d.rolls) + 1, avoid)
		d.avoid[e.id] = true
		d.list[slot] = { id = id, n = 0, done = false }
		d.rolls = num(d.rolls) + 1
		dirty(s)
		publish(s)
		return stateFor(s)
	elseif op == "redeem" then
		return redeem(s, a, b)
	end
	return { ok = false, why = "nope" }
end

Remote.OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown)
	local ok, res = pcall(handle, p, op, a, b)
	if not ok then
		warn("[jankfire] quests: " .. tostring(res))
		return { ok = false, why = "something broke. try again" }
	end
	return res
end

-- ------------------------------------------------------------------ cheat restores (Stats.restoreFor's shape)
local FIX_TOPIC = "JankQuestsFix"
local fixDs: DataStore? = nil
pcall(function() fixDs = DataStoreService:GetDataStore(if STUDIO then "JankfireQuestsFix_studio" else "JankfireQuestsFix_v1") end)
local memPending: { [number]: { [string]: any } } = {}

-- one fix on a loaded save. returns whether it changed anything
local function applyFix(d: any, e: any): boolean
	if e.op == "void" then
		local key = tostring(math.floor(num(e.since)))
		if d.voids[key] ~= nil then return false end
		local from = QD.day(num(e.since))
		local b, x = 0, 0
		for k, v in d.earned do
			if (tonumber(k) or 0) >= from and type(v) == "table" then
				b += num(v.b); x += num(v.x)
				d.earned[k] = nil -- (an earlier `since` later can't take it twice)
			end
		end
		local tb, tx = math.min(b, num(d.brass)), math.min(x, num(d.tix))
		d.brass = num(d.brass) - tb; d.tix = num(d.tix) - tx
		d.owed.b = num(d.owed.b) + (b - tb); d.owed.x = num(d.owed.x) + (x - tx)
		d.voids[key] = { b = b, x = x, t = num(e.at) }
		return true
	elseif e.op == "unvoid" then
		local changed = false
		for _, v in d.voids do
			if type(v) == "table" and not v.undone then
				v.undone = true
				credit(d, num(v.b), num(v.x), false)
				changed = true
			end
		end
		return changed
	end
	return false
end

local function hereData(uid: number): (any, State?)
	local p = Players:GetPlayerByUserId(uid)
	local s = if p then st[p] else nil
	if s and s.ready and s.prof then return s.prof.data, s end
	return nil, nil
end

local function applyFixes(d: any, s: State?, fixes: { [string]: any }): boolean
	local list = {}
	for _, e in fixes do if type(e) == "table" then table.insert(list, e) end end
	table.sort(list, function(a, b) return num(a.at) < num(b.at) end)
	local changed = false
	for _, e in list do if applyFix(d, e) then changed = true end end
	if changed and s then dirty(s); publish(s); soon(s) end
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
	return (pcall(function()
		(fixDs :: DataStore):UpdateAsync("u" .. uid, function(old: any)
			local t = if type(old) == "table" then old else {}
			for id, e in fixes do if t[id] == nil then t[id] = e end end
			return t
		end)
	end))
end
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

-- a player here takes what waits for them: applied, saved, then off the list
local pulling: { [number]: boolean } = {}
local function pull(uid: number)
	if pulling[uid] then return end
	pulling[uid] = true
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
	pulling[uid] = nil
end

local function nudge(uids: { number }, who: number, since: number?, unwatch: boolean?)
	pcall(function() MessagingService:PublishAsync(FIX_TOPIC, { u = uids, w = who, s = since, uw = unwatch }) end)
end

local function deliver(uid: number, fixes: { [string]: any }): string?
	local d, s = hereData(uid)
	if d then
		if applyFixes(d, s, fixes) and s and s.prof and s.prof.state == "cloud" then task.spawn(Profiles.save, store, s.prof) end
		return "now"
	end
	return if addPending(uid, fixes) then "queued" else nil
end

-- THE CALL (the anti-cheat, a cheater confirmed): what quests and the weekly track paid from the UTC day of `since`
-- (os.time(); nil / 0 = the last EARN_DAYS days) comes off their wallet, what's already spent becomes owed, and
-- nothing more counts for them here. yields: call it in its own thread. { ok, now, queued } or { ok = false, why }
function Quests.restoreFor(uid: number, since: number?): any
	if type(uid) ~= "number" or uid == 0 then return { ok = false, why = "no user id" } end
	local from = math.max(0, math.floor(tonumber(since) or 0))
	watched[uid] = math.min(watched[uid] or from, from)
	local t = now()
	local how = deliver(uid, { ["v:" .. from] = { op = "void", since = from, at = t } })
	task.spawn(nudge, if how == "queued" then { uid } else {}, uid, from)
	return { ok = how ~= nil, now = how == "now", queued = how == "queued", why = if how == nil then "couldn't reach their quest save" else nil }
end

-- a wrong catch (the anti-cheat's UNBAN): every restore of theirs is given back
function Quests.undoRestore(uid: number): any
	if type(uid) ~= "number" then return { ok = false, why = "no user id" } end
	watched[uid] = nil
	local t = now()
	local how = deliver(uid, { ["u:" .. t] = { op = "unvoid", at = t } })
	task.spawn(nudge, if how == "queued" then { uid } else {}, uid, nil, true)
	return { ok = how ~= nil, now = how == "now", queued = how == "queued" }
end

-- ------------------------------------------------------------------ players
local function clean(d: any)
	for _, k in { "list", "avoid", "earned", "pending", "voids", "grants" } do if type(d[k]) ~= "table" then d[k] = {} end end
	if type(d.owed) ~= "table" then d.owed = { b = 0, x = 0 } end
	if type(d.total) ~= "table" then d.total = { quests = 0, brass = 0, tix = 0 } end
	-- (a quest that left the pool: a fresh roll for the day)
	for _, e in d.list do if type(e) ~= "table" or not QD.byId[e.id] then d.day = -1 end end
end

local function added(p: Player)
	if st[p] then return end
	local s: State = { p = p, prof = nil, ready = false, cur = nil, budget = 10, budgetT = clock(), roped = false, hookT = 0,
		relT = -100, busy = false, conns = {} }
	st[p] = s
	publish(s)
	watchItems(s)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	s.prof = prof
	clean(prof.data)
	s.ready = true
	fresh(s)
	prof.onLost.Event:Connect(function() publish(s) end)
	publish(s)
	push(s, { t = "state", state = stateFor(s) })
	task.spawn(pull, p.UserId) -- (a cheat restore left for them while they were away)
	task.spawn(settle, s) -- (a redeem a crash cut in half)
end

function Quests.init(fight: any, matches: any)
	Fight, Matches = fight, matches
	local function safe(fn: any): any
		return function(...)
			local ok, err = pcall(fn, ...)
			if not ok then warn("[jankfire] quests: " .. tostring(err)) end
		end
	end
	Fight.onHurt(safe(onHurt))
	Fight.onKill(safe(onKill))
	hookMatches()
	-- the grapple: the same remote Main.server.luau answers (only whether you're on a rope is read here)
	local g = Remotes:FindFirstChild("Grapple")
	if g and g:IsA("RemoteEvent") then
		g.OnServerEvent:Connect(function(p: Player, what: unknown)
			local s = st[p]
			if not s then return end
			if what == "hook" then s.roped, s.hookT = true, clock()
			elseif what == "release" then
				if s.roped then s.relT = clock() end
				s.roped = false
			end
		end)
	end
	-- the range quests: a finished run's score on a plate
	local rm = script.Parent:FindFirstChild("RangeTest")
	if rm then
		local ok, R = pcall(require, rm)
		if ok and type(R) == "table" and type((R :: any).onRun) == "function" then
			(R :: any).onRun(safe(function(p: Player, level: string, score: number)
				if type(level) == "string" and QD.RANGE[level] and type(score) == "number" then bump(st[p], "range:" .. level, score) end
			end))
		end
	end
	for _, p in Players:GetPlayers() do task.spawn(added, p) end
	Players.PlayerAdded:Connect(added)
	Players.PlayerRemoving:Connect(function(p)
		local s = st[p]
		st[p] = nil
		if not s then return end
		for _, c in s.conns do c:Disconnect() end
		if s.prof then Profiles.release(store, s.prof) end
	end)
	-- a cheater restored in another server: watched here too; fixes for players here are pulled
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
	-- the clock: a new day / week rolls for everyone here; progress goes out to the clients
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 0.2 then return end
		acc = 0
		local t = clock()
		for _, s in st do
			if s.ready then
				if (s.pushAt == nil or s.pushAt <= t) and fresh(s) then publish(s); soon(s) end
				if s.pushAt and s.pushAt <= t then
					s.pushAt = nil
					push(s, { t = "state", state = stateFor(s) })
				end
			end
		end
	end)
	if STUDIO then
		local old = ServerStorage:FindFirstChild("JankQuestTest")
		if old then old:Destroy() end
		local fn = Instance.new("BindableFunction")
		fn.Name = "JankQuestTest"
		fn.OnInvoke = function(op: string, a: any, b: any, c: any, d: any, e: any): any return Quests.test(op, a, b, c, d, e) end
		fn.Parent = ServerStorage
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankQuestTest)
--   ("count", on)                      ghost / held matches count, the took-part rule waived for them (default off)
--   ("ghost", dummyName)                that dummy counts as an enemy player while the test player is in a match
--   ("hit", player, dummyName, dmg, weapon, hs)  a real Fight.hurt from the player on that fighter
--   ("set", player, slot, questId)      that quest in that slot, from zero
--   ("bump", player, stat, n)           n more of a counter
--   ("data", player) / ("put", player, data) / ("reset", player)   read / put back / start afresh
--   ("state", player)                   what the client gets
--   ("clock", secs)                     move the quest clock (day and week resets)
--   ("restore", uid, since) / ("undo", uid)   the cheat calls
--   ("cur", player)                     the match as quests see it
function Quests.test(op: string, a: any, b: any, c: any, d: any, e: any): any
	if not STUDIO then return nil end
	if op == "count" then
		testCount = a == true
		return testCount
	elseif op == "ghost" then
		ghost = nil
		if type(a) == "string" and a ~= "" then
			for _, f in Fight.all do if f.kind ~= "player" and f.name == a then ghost = f end end
		end
		return ghost ~= nil
	elseif op == "clock" then
		offset = tonumber(a) or 0
		return now()
	elseif op == "restore" then
		return Quests.restoreFor(a, b)
	elseif op == "undo" then
		return Quests.undoRestore(a)
	end
	local p = a :: Player
	local s = st[p]
	if not s then return "no such player" end
	local data = dataOf(s)
	if op == "hit" then
		local by = Fight.byPlayer[p]
		local target = nil
		for _, f in Fight.all do if f.name == b then target = f end end
		if not by or not target then return "no fighter" end
		return Fight.hurt(target, tonumber(c) or 10, by, if type(d) == "string" then d else "ar", e == true)
	elseif op == "set" then
		local q = QD.byId[c]
		if not data or not q or type(b) ~= "number" then return false end
		fresh(s)
		data.list[b] = { id = q.id, n = 0, done = false }
		dirty(s); publish(s); soon(s)
		return true
	elseif op == "bump" then
		bump(s, tostring(b), tonumber(c) or 1)
		return stateFor(s)
	elseif op == "data" then
		return data
	elseif op == "put" then
		if not s.prof or type(b) ~= "table" then return false end
		s.prof.data = b
		clean(b)
		dirty(s); publish(s); soon(s)
		return true
	elseif op == "reset" then
		if not s.prof then return false end
		s.prof.data = template()
		fresh(s)
		dirty(s); publish(s); soon(s)
		return true
	elseif op == "state" then
		return stateFor(s)
	elseif op == "grant" then
		local ok, why = Quests.grant(p, b, c, d)
		return { ok = ok, why = why }
	elseif op == "cur" then
		local cu = s.cur
		return if cu then { id = cu.id, team = cu.team, act = cu.act, ract = cu.ract, streak = cu.streak, ranked = cu.ranked, party = cu.party, ghost = isGhost(cu), live = live(s) } else false
	end
	return nil
end

return Quests
