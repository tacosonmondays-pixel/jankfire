--!strict
-- PLAY AGAIN and LEAVE (27 Nov 2026, main for the owner): the two buttons on the victory card (client/VictoryCard.luau,
-- the victory-scene session) after every Matches match. roblox/docs/MATCHMAKING.md "Play again".
--   * PLAY AGAIN: the same queue again (mode, size, ranked or not), through its map vote as usual. a party's leader
--     re-queues the whole party; a member's PLAY AGAIN only says "I'm in". a hub pad match: back onto your side of the
--     same pad, so its countdown and map vote run again. a match on another server: back to a public server together,
--     one party again, searching at once (CrossServer's backHome and the "a:<token>" record)
--   * LEAVE: home as today (the party's room, or the hub). a member who picked LEAVE is taken out of the party when the
--     leader re-queues, so they're not pulled into the next match
--   * the picks act at the trip home (Matches' backToHub). when every real player in the match has picked, that trip
--     runs at once instead of after the end screen's count (Matches.homeNow), unless a play of the match is due
-- the Play remote (Party.ops): ("again", true | false) -> { ok, why?, view }    ("againview") -> { ok, view }
-- and PlayPush { t = "again", view } to everyone in the match at its end and on every pick. view = { can, why?, role
-- ("solo" | "leader" | "member"), queue (a short label), pick ("again" | "leave" | nil), lead (the leader's pick, for a
-- member), picked, of }
-- Studio: ServerStorage.JankPlayTest ("again", player, true | false) picks for a player; ("againview", player);
-- ("cross", "againarrive", player, token) a player arriving home with a PLAY AGAIN token (CrossServer.test)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PlayConfig = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("PlayConfig"))

local PlayAgain = {}
PlayAgain.WAIT = 20 -- s a PLAY AGAIN group back from another server waits for all its players before it searches
PlayAgain.BODY = 8 -- s at most for a fresh body in the hub before a pad's PLAY AGAIN gives up

-- what a player can do after the match they just played (kind: "party" a Play queue match here, "pad" a hub pad's,
-- "cross" a match on this match server)
type Snap = { m: any, kind: string, team: number, label: string, can: boolean, why: string?, pick: string?, party: number?,
	leader: Player?, size: number, group: string? }

local Matches: any
local Party: any
local CrossServer: any
local QuickJoin: any
local pushR: RemoteEvent
local snaps: { [Player]: Snap } = {}

local function push(p: Player, msg: any) if p.Parent then pushR:FireClient(p, msg) end end
local function toast(p: Player, text: string) push(p, { t = "toast", text = text }) end

-- the queue's short label: "2V2 RANKED", "QUICKPLAY", "1V1 PAD"
local function label(mode: string?, ranked: boolean, pad: boolean): string
	local cfg: any = if mode then PlayConfig.byId[mode] else nil
	local name = if mode == PlayConfig.QUICKPLAY then "QUICKPLAY" elseif cfg and cfg.name then string.upper(cfg.name) else string.upper(tostring(mode or "?"))
	return name .. (if pad then " PAD" elseif ranked then " RANKED" else "")
end

local function everyone(m: any): { Player }
	local out = {}
	for _, list in m.teams do for _, p in list do if p.Parent and not table.find(out, p) then table.insert(out, p) end end end
	return out
end

-- the cross-server match's own record (the matchmaker's): which party each player came in, and its leader
local function crossGroup(m: any, p: Player): (string?, number?)
	local rec = CrossServer.recordOf(m)
	if type(rec) ~= "table" or type(rec.rated) ~= "table" or type(rec.rated.teams) ~= "table" then return nil, nil end
	for t, list in rec.rated.teams do
		for _, x in list do
			if x.id == p.UserId then
				local g = t .. ":" .. tostring(x.g or x.id)
				local lead: number? = nil
				for _, y in list do if tostring(y.g or y.id) == tostring(x.g or x.id) and y.lead then lead = y.id end end
				return g, lead
			end
		end
	end
	return nil, nil
end

-- the snapshot at the match's end
local function snapOf(m: any, p: Player, team: number): Snap
	local s: Snap = { m = m, kind = "pad", team = team, label = "", can = true, why = nil, pick = nil, party = nil, leader = nil, size = 1, group = nil }
	local q = m.queue
	local cfg: any = PlayConfig.byId[m.mode]
	if type(q) == "string" and string.sub(q, 1, 6) == "cross:" then
		s.kind = "cross"
		local rec = CrossServer.recordOf(m)
		if type(rec) ~= "table" then
			s.can, s.why = false, "this match server can't queue you again"
		else
			s.label = label(if rec.quick then PlayConfig.QUICKPLAY else rec.mode, rec.ranked == true, false)
			local g, lead = crossGroup(m, p)
			s.group = g
			local n = 0
			for _, x in everyone(m) do
				local gx = crossGroup(m, x)
				if gx == g then n += 1 end
			end
			s.size = n
			if lead then s.leader = Players:GetPlayerByUserId(lead) end
		end
	elseif type(q) == "string" then
		s.kind = "party"
		local info = Party.infoOf(p)
		if not info then
			s.can, s.why = false, "your party is gone"
		else
			s.party, s.leader, s.size = info.id, info.leader, info.size
			s.label = label(info.mode, info.ranked == true, false)
			local icfg: any = PlayConfig.byId[info.mode]
			if icfg and icfg.coop then s.can, s.why = false, "not for ZOMBIES" end
		end
	else
		s.kind = "pad"
		s.label = label(m.mode, false, true)
		if not (m.pad and m.pad.Parent) then s.can, s.why = false, "that pad is gone" end
	end
	if cfg and cfg.coop then s.can, s.why = false, "not for ZOMBIES" end
	return s
end

-- the leader of p's party or group in that match (nil: p plays alone, or the leader isn't here)
local function leaderOf(s: Snap): Player?
	if s.size <= 1 then return nil end
	if s.leader and s.leader.Parent then return s.leader end
	if s.kind == "cross" then
		-- (the leader left: the first of the group still here leads)
		for _, x in everyone(s.m) do
			local o = snaps[x]
			if o and o.m == s.m and o.group == s.group then return x end
		end
	end
	return nil
end

local function counts(m: any): (number, number)
	local picked, of = 0, 0
	for _, x in everyone(m) do
		of += 1
		local o = snaps[x]
		if o and o.m == m and o.pick then picked += 1 end
	end
	return picked, of
end

local function viewOf(p: Player): any
	local s = snaps[p]
	if not s then return { can = false, why = "no match to play again", role = "solo", queue = "", picked = 0, of = 0 } end
	local ld = leaderOf(s)
	local role = if s.size <= 1 or not ld then "solo" elseif ld == p then "leader" else "member"
	local lead: string? = nil
	if role == "member" and ld then
		local o = snaps[ld]
		lead = if o and o.m == s.m then o.pick else nil
	end
	local picked, of = counts(s.m)
	return { can = s.can, why = s.why, role = role, queue = s.label, pick = s.pick, lead = lead, picked = picked, of = of }
end

local function pushAll(m: any)
	for _, x in everyone(m) do
		local o = snaps[x]
		if o and o.m == m then push(x, { t = "again", view = viewOf(x) }) end
	end
end

-- a button: yes = PLAY AGAIN, no = LEAVE
function PlayAgain.pick(p: Player, yes: any): any
	local s = snaps[p]
	if not s then return { ok = false, why = "no match to play again", view = viewOf(p) } end
	if s.m.on == false then return { ok = false, why = "you're already on your way", view = viewOf(p) } end
	if yes == true and not s.can then return { ok = false, why = s.why or "can't queue again from here", view = viewOf(p) } end
	s.pick = if yes == true then "again" else "leave"
	pushAll(s.m)
	-- (everyone has picked: home now, not after the count. picked during the scene: as soon as the end screen is up)
	local picked, of = counts(s.m)
	if picked >= of and of > 0 then
		local m = s.m
		task.spawn(function()
			local t0 = os.clock()
			while m.on ~= false and not m.endAt and os.clock() - t0 < 60 do task.wait(0.2) end
			local p2, o2 = counts(m)
			if p2 >= o2 and o2 > 0 then Matches.homeNow(m) end
		end)
	end
	return { ok = true, view = viewOf(p) }
end
function PlayAgain.view(p: Player): any
	return { ok = true, view = viewOf(p) }
end

-- ------------------------------------------------------------------ the trip home
-- a pad match: once the body is back in the hub, onto your side of the same pad (QuickJoin.onto)
local function backOnPad(p: Player, m: any, team: number)
	local was = p.Character
	local t0 = os.clock()
	while os.clock() - t0 < PlayAgain.BODY do
		local ch = p.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		-- (a fresh body, or the one there after 1.5 s: the respawn may have come before this ran)
		if ch and (ch ~= was or os.clock() - t0 > 1.5) and hum and hum.Health > 0 and ch:FindFirstChild("HumanoidRootPart") and not Matches.matchOf(p) then break end
		task.wait(0.2)
	end
	if not p.Parent or Matches.matchOf(p) then return end
	task.wait(0.3) -- (the hub spawn settles: the pad reads where the body stands)
	local ok, why = QuickJoin.onto(p, m.pad, team)
	if not ok then toast(p, why or "couldn't put you back on that pad") end
end

local function run(m: any)
	local list = {}
	for p, s in snaps do if s.m == m then table.insert(list, p) end end
	for _, p in list do
		local s = snaps[p]
		if not p.Parent then continue end
		if s.kind == "pad" then
			if s.pick == "again" and s.can then task.spawn(backOnPad, p, m, s.team) end
		elseif s.kind == "party" then
			-- (Party's own end hook has put the party back in its room by now)
			local info = Party.infoOf(p)
			if s.pick == "again" and s.can and info and info.leader == p then
				local drop = {}
				for _, q in info.members do
					local o = snaps[q]
					if q ~= p and o and o.m == m and o.pick == "leave" then table.insert(drop, q) end
				end
				local ok, why = Party.requeue(p, drop)
				if ok then
					for _, q in info.members do if q.Parent and not table.find(drop, q) then toast(q, "searching again: " .. s.label) end end
				else
					toast(p, "couldn't search again: " .. tostring(why or "?"))
				end
			end
		end
		-- (a cross-server match: CrossServer's backHome asks homeGroups below and sends everyone)
	end
	-- (a cross-server match's stay a little: backHome reads them for its groups at the same moment)
	task.delay(5, function()
		for _, p in list do if snaps[p] and snaps[p].m == m then snaps[p] = nil end end
	end)
end

-- (CrossServer's backHome) the PLAY AGAIN groups of a match on this match server: one per party whose leader picked
-- PLAY AGAIN (members who picked LEAVE stay out), with the queue to search at home. everyone else goes home as before
function PlayAgain.homeGroups(m: any, all: { Player }): { any }
	local out = {}
	local rec = CrossServer.recordOf(m)
	if type(rec) ~= "table" then return out end
	local seen: { [string]: boolean } = {}
	for _, p in all do
		local s = snaps[p]
		if not s or s.m ~= m or s.kind ~= "cross" or not s.group or seen[s.group] then continue end
		local ld = leaderOf(s) or p
		local ls = snaps[ld]
		local alone = s.size <= 1
		if not ((alone and s.pick == "again") or (not alone and ls and ls.m == m and ls.pick == "again")) or not s.can then continue end
		seen[s.group :: string] = true
		local players, ids = {}, {}
		for _, x in all do
			local o = snaps[x]
			if x.Parent and o and o.m == m and o.group == s.group and (x == ld or o.pick ~= "leave") then
				table.insert(players, x)
				table.insert(ids, x.UserId)
			end
		end
		if #players > 0 then
			table.insert(out, { players = players, rec = { mode = if rec.quick then PlayConfig.QUICKPLAY else rec.mode, ranked = rec.ranked == true,
				lead = ld.UserId, ids = ids } })
		end
	end
	return out
end

-- ------------------------------------------------------------------ home again (a PLAY AGAIN group from another server)
type Pend = { players: { Player }, t0: number }
local pend: { [string]: Pend } = {}
local function bodyIn(p: Player): boolean
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	return ch ~= nil and hum ~= nil and hum.Health > 0 and ch:FindFirstChild("HumanoidRootPart") ~= nil
end
-- (CrossServer: a player joined with teleport data { back = true, again = token })
function PlayAgain.arrive(p: Player, tok: any)
	if type(tok) ~= "string" or #tok > 64 then return end
	local pe = pend[tok]
	if pe then
		if not table.find(pe.players, p) then table.insert(pe.players, p) end
		return
	end
	pe = { players = { p }, t0 = os.clock() }
	pend[tok] = pe
	task.spawn(function()
		local rec = CrossServer.againRecord(tok)
		if type(rec) ~= "table" or type(rec.ids) ~= "table" or type(rec.mode) ~= "string" then
			task.delay(60, function() pend[tok] = nil end)
			return
		end
		-- everyone listed here with a body, or WAIT s
		while os.clock() - pe.t0 < PlayAgain.WAIT do
			local all = true
			for _, id in rec.ids do
				local q = Players:GetPlayerByUserId(id)
				if not q or not table.find(pe.players, q) or not bodyIn(q) then all = false end
			end
			if all then break end
			task.wait(0.5)
		end
		-- (only those listed in the record AND arrived with its token: a token can't pull anyone else in)
		local members = {}
		for _, q in pe.players do
			if q.Parent and table.find(rec.ids, q.UserId) and bodyIn(q) then table.insert(members, q) end
		end
		task.delay(60, function() pend[tok] = nil end)
		if #members == 0 then return end
		local leader = Players:GetPlayerByUserId(tonumber(rec.lead) or 0)
		if not leader or not table.find(members, leader) then leader = members[1] end
		local ok, why = Party.form(leader :: Player, members, rec.mode, rec.ranked == true)
		local text = if ok then "searching again: " .. label(rec.mode, rec.ranked == true, false) else "couldn't search again: " .. tostring(why or "?")
		for _, q in members do toast(q, text) end
	end)
end

-- ------------------------------------------------------------------ wiring
function PlayAgain.init(matches: any, party: any, cross: any, quickJoin: any, remotes: Instance)
	Matches, Party, CrossServer, QuickJoin = matches, party, cross, quickJoin
	pushR = remotes:WaitForChild("PlayPush") :: RemoteEvent
	Party.ops.again = function(p: Player, a: any): any return PlayAgain.pick(p, a) end
	Party.ops.againview = function(p: Player): any return PlayAgain.view(p) end
	CrossServer.hook("homeGroups", PlayAgain.homeGroups)
	CrossServer.hook("onAgain", PlayAgain.arrive)
	Matches.onEnd(function(m: any)
		for t, list in m.teams do
			for _, p in list do
				if p.Parent then snaps[p] = snapOf(m, p, t) end
			end
		end
		pushAll(m)
		-- the trip home: backToHub sets m.on = false (120 s at most); Party's own hook puts a party back in its room 0.3 s
		-- after, so this goes 0.6 s after
		task.spawn(function()
			local t0 = os.clock()
			while m.on ~= false and os.clock() - t0 < 120 do task.wait(0.25) end
			task.wait(0.6)
			local okR, err = pcall(run, m)
			if not okR then warn("[jankfire] play again: " .. tostring(err)) end
		end)
	end)
	Players.PlayerRemoving:Connect(function(p) snaps[p] = nil end)
end

-- Studio (PlayServer's JankPlayTest): ("again", player, yes) picks for a player; ("againview", player)
function PlayAgain.test(op: string, a: any, b: any): any
	if op == "again" then return PlayAgain.pick(a, b) end
	if op == "againview" then return PlayAgain.view(a) end
	return nil
end

return PlayAgain
