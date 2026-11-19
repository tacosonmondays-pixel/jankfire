--!strict
-- PARTY: parties, their private lobbies, invites, and the Play queue's start (roblox/docs/MATCHMAKING.md sections 1-3).
-- ported from the web game's server/party.js where it fits: a leader who alone picks, queues, kicks and passes the
-- lead; the lead passing to the next member when the leader goes; invites that expire; the whole party going into the
-- same match on the same team.
-- the private lobby IS the party: PLAY puts you in a room of your own (LobbyRooms) as a party of one; whoever joins
-- stands on the next plinth; leaving the room leaves the party. a lobby player's body stands anchored on its plinth and
-- respawns there (Matches.homeOf), so after a match the party is back in its room.
-- the remote ReplicatedStorage.JankfireRemotes.Play (RemoteFunction), always { ok, why?, ... }:
--   ("state") -> { party?, invites, ranked }      ("play") enter your lobby      ("leave") back to the hub
--   ("players") -> { list }    ("invite", userId)    ("answer", inviteId, yes)    ("kick", id)    ("promote", id)
--   ("mode", modeId, ranked)   ("find")   ("cancel")   ("map", arena | "random")   ("vote", modeId)   ("mapvote", arena)
-- and JankfireRemotes.PlayPush (RemoteEvent) to the client: { t = "party", party? } | { t = "invite", ... } |
-- { t = "inviteGone", id } | { t = "found", at } | { t = "ranked", result } | { t = "toast", text }
-- Studio play tests: stand-ins (a regular's avatar from ServerStorage.JankfireNPCs, negative ids) join parties and
-- queues so one tester can play a party of 2 and a 2v2; Party.test at the end (PlayServer's JankPlayTest).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))
local Ranked = require(Shared:WaitForChild("Ranked"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Arena = require(Shared:WaitForChild("Arena"))
local MapCards = require(Shared:WaitForChild("MapCards"))
local LobbyRooms = require(script.Parent:WaitForChild("LobbyRooms"))
local Queue = require(script.Parent:WaitForChild("Queue"))
local CrossServer = require(script.Parent:WaitForChild("CrossServer"))

local Party = {}

type Member = { id: number, player: Player?, name: string, display: string, model: Model?, rating: { [string]: any }?, inRoom: boolean? }
-- (vote / pick: a QUICKPLAY match's vote on its mode, and the mode it picked. mvote / map: the map vote of a
-- QUICKPLAY or casual duel match, and the arena it picked; a party pick's map is its leader's)
type Found = { key: string, mode: string, ranked: boolean, teams: { { Queue.Entry } }, at: number, waiting: boolean?, vote: any?, pick: string?,
	mvote: any?, map: string? }
type PartyT = {
	id: number, leader: Member, members: { Member }, mode: string, ranked: boolean, room: LobbyRooms.Room?,
	entry: Queue.Entry?, found: Found?, match: number?,
	fill: boolean?, -- (a classic mode picked on the PARTY card: FILL FROM QUICKPLAY)
	map: string?, -- (the leader's map for a PARTY card pick: an arena in the rotation; nil = RANDOM)
}
type Invite = { id: number, from: Player, party: PartyT, to: Player?, toStand: Member?, expires: number }

local Fight: any
local Matches: any
local RankedData: any
local pushR: RemoteEvent
local parties: { [number]: PartyT } = {}
local byPlayer: { [Player]: PartyT } = {}
local invites: { [number]: Invite } = {}
local sent: { [Player]: { number } } = {} -- invite times in the last minute
local founds: { Found } = {}
local nextId, nextInvite = 0, 0
local standPool: { Member } = {} -- (Studio tests: stand-ins nobody has invited yet)
local testHold: any = { secs = 25, win = "party" } -- (Studio tests: how long a match with stand-ins lasts, who takes it: a team number, or "party" = the real players' team)

local function now(): number return os.clock() end
local function serverNow(): number return workspace:GetServerTimeNow() end

local function push(p: Player?, msg: any)
	if p and p.Parent then pushR:FireClient(p, msg) end
end
local function toast(p: Player?, text: string) push(p, { t = "toast", text = text }) end

local function memberOf(pt: PartyT, id: number): Member?
	for _, m in pt.members do if m.id == id then return m end end
	return nil
end
local function realMembers(pt: PartyT): { Player }
	local out = {}
	for _, m in pt.members do if m.player and m.player.Parent then table.insert(out, m.player) end end
	return out
end

-- a member's rank view in a mode (stand-ins carry a test rating)
local function rankView(m: Member, mode: string): any
	local key = PlayConfig.ratingKey(mode)
	if not Ranked.SIZE[key] and key ~= Ranked.PARTY_KEY then return nil end
	if m.player then
		local all = RankedData.modes(m.player)
		return all[key]
	end
	local q = m.rating and m.rating[key]
	return RankedData.view(q, key)
end
local function ratingFor(m: Member, mode: string): (number, number)
	local key = PlayConfig.ratingKey(mode)
	if m.player then
		local r, rd = RankedData.rating(m.player, key)
		return r, rd
	end
	local q = m.rating and m.rating[key]
	if q then return q.r, q.rd end
	return Ranked.START.r, Ranked.START.rd
end

-- ------------------------------------------------------------------ the view each member's screen draws
-- the members standing in the room, in plinth order (stand-ins stand there whenever the room is open)
local function inRoom(pt: PartyT): { Member }
	local out = {}
	if not pt.room then return out end
	for _, m in pt.members do if m.inRoom or not m.player then table.insert(out, m) end end
	return out
end

-- ------------------------------------------------------------------ QUICKPLAY's vote (PlayConfig QUICKPLAY)
-- a quickplay match, once formed, votes on its mode: 3 of the classic modes its head-count fits (a team mode only when
-- its parties split into two sides), drawn by PlayConfig.QUICK_WEIGHT, never this server's last quickplay mode unless
-- nothing else fits. PlayConfig.VOTE s to tap one; most votes wins, a tie is drawn, no votes at all = a weighted draw
local lastQuick: string? = nil
local function quickFits(es: { Queue.Entry }): { string }
	local n = 0
	for _, e in es do n += e.size end
	local out = {}
	for _, m in PlayConfig.classic() do
		local lo, hi = PlayConfig.counts(m.id)
		if n >= lo and n <= hi and (m.sides ~= 2 or Queue.split(es, PlayConfig.PARTY_MAX) ~= nil) then table.insert(out, m.id) end
	end
	return out
end
local function drawOne(ids: { string }): string?
	local sum = 0
	for _, id in ids do sum += PlayConfig.QUICK_WEIGHT[id] or 1 end
	local r = math.random() * sum
	for _, id in ids do
		r -= PlayConfig.QUICK_WEIGHT[id] or 1
		if r <= 0 then return id end
	end
	return ids[#ids]
end
local function voteOffer(es: { Queue.Entry }): { string }
	local fits = quickFits(es)
	local pool = {}
	for _, id in fits do if id ~= lastQuick then table.insert(pool, id) end end
	if #pool == 0 then pool = fits end
	local out = {}
	while #out < 3 and #pool > 0 do
		local id = drawOne(pool) :: string
		table.insert(out, id)
		table.remove(pool, table.find(pool, id) :: number)
	end
	return out
end
local function voteCounts(v: any): { [string]: number }
	local counts = {}
	for _, id in v.votes do counts[id] = (counts[id] or 0) + 1 end
	return counts
end
local function voteResult(v: any): string
	local counts = voteCounts(v)
	local best, top = {}, 0
	for _, id in v.options do
		local c = counts[id] or 0
		if c > top then best, top = { id }, c elseif c == top and c > 0 then table.insert(best, id) end
	end
	if top == 0 then return drawOne(v.options) :: string end
	return best[math.random(#best)]
end
-- what a player's screen shows of it (client/QuickVoteUI.luau): the options, the clock, the counts, their own vote
local function voteView(f: Found, forP: Player): any
	local v = f.vote
	if not v then return nil end
	local opts = {}
	for _, id in v.options do
		local m = PlayConfig.byId[id]
		table.insert(opts, { id = id, name = if m then m.name else id, sub = if m then (m :: any).sub else "" })
	end
	return { options = opts, ends = serverNow() + math.max(0, v.ends - now()), counts = voteCounts(v), mine = v.votes[forP.UserId] }
end

-- ------------------------------------------------------------------ the map (17 Nov, the owner: "also add map selector before hand")
-- the maps are the rotation's (Arena.pool: workspace.Map's ArenaPool, the hub session's), named as the first banner
-- names them (Arena.title) with their card pictures (shared/MapCards.luau).
--   a PARTY card pick: the leader picks one, or RANDOM (the rotation, as before)
--   QUICKPLAY and casual duels: a map vote of 3 from the rotation, in the same PlayConfig.VOTE s as the mode vote;
--   most votes wins, a tie is drawn, no votes = a draw of the three; never the last map that vote picked
--   RANKED (duels and PARTY RANKED): the rotation, a fair random one, no vote
local function mapCard(id: string): any
	return { id = id, title = Arena.title(id), thumb = MapCards.thumb(id) }
end
local function mapList(teamSize: number?): { any }
	local out = {}
	for _, id in Arena.pool(teamSize) do table.insert(out, mapCard(id)) end
	return out
end
local lastMap: { [string]: string } = {} -- (per vote: "quick", "duel")
local function mapOffer(kind: string, teamSize: number?): { string }
	local pool = table.clone(Arena.pool(teamSize))
	local others = {}
	for _, id in pool do if id ~= lastMap[kind] then table.insert(others, id) end end
	if #others > 0 then pool = others end
	local out = {}
	while #out < 3 and #pool > 0 do
		table.insert(out, table.remove(pool, math.random(#pool)) :: string)
	end
	return out
end
local function mapResult(v: any): string?
	local counts = voteCounts(v)
	local best, top = {}, 0
	for _, id in v.options do
		local c = counts[id] or 0
		if c > top then best, top = { id }, c elseif c == top then table.insert(best, id) end
	end
	return if #best > 0 then best[math.random(#best)] else nil
end
local function mapVoteView(f: Found, forP: Player): any
	local v = f.mvote
	if not v then return nil end
	local opts = {}
	for _, id in v.options do table.insert(opts, mapCard(id)) end
	return { options = opts, ends = serverNow() + math.max(0, v.ends - now()), counts = voteCounts(v), mine = v.votes[forP.UserId] }
end
-- a map vote's clock ran out (or the match is starting): its pick
local function settleMap(f: Found)
	local v = f.mvote
	if not v or f.map then return end
	f.map = mapResult(v)
	if f.map then lastMap[v.kind] = f.map end
end

local function viewOf(pt: PartyT, forP: Player): any
	local ms = {}
	local here = inRoom(pt)
	local meIn = false
	for _, m in pt.members do
		local spot = table.find(here, m)
		if m.player == forP and spot then meIn = true end
		table.insert(ms, {
			id = m.id, name = m.name, display = m.display, leader = m == pt.leader, standIn = m.player == nil, spot = spot,
			inRoom = spot ~= nil, inMatch = m.player ~= nil and Matches.matchOf(m.player) ~= nil,
			rank = if pt.ranked then rankView(m, pt.mode) else nil,
		})
	end
	local q: any = nil
	local e = pt.entry
	if e and e.state == "search" then
		q = { since = serverNow() - (now() - e.since) } -- (no rating: the MMR never leaves the server)
	end
	local out = {}
	for _, iv in invites do
		if iv.party == pt then
			table.insert(out, { id = iv.id, name = if iv.to then iv.to.DisplayName elseif iv.toStand then iv.toStand.display else "?",
				left = math.max(0, iv.expires - now()) })
		end
	end
	local spots = {}
	if pt.room then for i = 1, #here do spots[i] = LobbyRooms.spot(pt.room, i) end end
	return {
		id = pt.id, me = forP.UserId, leader = pt.leader.id, mode = pt.mode, ranked = pt.ranked, members = ms,
		max = PlayConfig.PARTY_MAX, queue = q,
		found = if pt.found then { at = serverNow() + math.max(0, pt.found.at - now()), waiting = pt.found.waiting == true,
			vote = voteView(pt.found, forP), pick = pt.found.pick,
			mvote = mapVoteView(pt.found, forP), map = if pt.found.map then mapCard(pt.found.map) else nil } else nil,
		fill = pt.fill == true,
		-- (the PARTY card's map: the leader's pick, nil = RANDOM, out of maps)
		map = pt.map, maps = mapList(),
		inMatch = pt.match ~= nil, outgoing = out, meIn = meIn,
		-- (the room only for those standing in it: the client opens the lobby screen when it has one)
		room = if pt.room and meIn then { cam = pt.room.cam, focus = pt.room.focus, spots = spots, slot = pt.room.slot } else nil,
	}
end
local function pushParty(pt: PartyT)
	for _, p in realMembers(pt) do push(p, { t = "party", party = viewOf(pt, p) }) end
end

-- ------------------------------------------------------------------ bodies in the room
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	return ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
end
-- stand a real member on their plinth (anchored), or a stand-in's model
local function standAt(m: Member, cf: CFrame)
	if m.player then
		local ch = m.player.Character
		local root = rootOf(m.player)
		if not ch or not root then return end
		local pos = cf.Position + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)
		m.player:SetAttribute("TeleportT", os.clock()) -- (Main's teleport check starts afresh from here)
		root.Anchored = true
		ch:PivotTo(CFrame.lookAt(pos, pos + cf.LookVector))
	elseif m.model then
		local model = m.model
		local root = model:FindFirstChild("HumanoidRootPart") :: BasePart?
		local hum = model:FindFirstChildOfClass("Humanoid")
		if not root then return end
		local up = (if hum then hum.HipHeight else 2) + root.Size.Y / 2
		local want = CFrame.lookAt(cf.Position + Vector3.new(0, up, 0), cf.Position + Vector3.new(0, up, 0) + cf.LookVector)
		model:PivotTo(want * root.CFrame:ToObjectSpace(model:GetPivot()))
	end
end
local function place(pt: PartyT)
	local room = pt.room
	if not room then return end
	local here = inRoom(pt)
	LobbyRooms.rings(room, #here, table.find(here, pt.leader))
	if pt.match then return end -- (in a match: they come back to their spots when it ends)
	for i, m in here do
		local cf = LobbyRooms.spot(room, i)
		if cf and not (m.player and Matches.matchOf(m.player)) then standAt(m, cf) end -- (never pull a body out of a match)
	end
end
-- a fresh body where homeOf says (the plinth while in the room, else the hub)
local function respawn(p: Player)
	local f = Fight.byPlayer[p]
	if f then f.alive = false; task.spawn(Fight.spawn, f) end
end

-- where a body goes when it respawns outside a match (Matches.homeOf): a plinth while you stand in your party's room
function Party.homeOf(p: Player): CFrame?
	local pt = byPlayer[p]
	if not pt or not pt.room then return nil end
	for i, m in inRoom(pt) do
		if m.player == p then return LobbyRooms.spot(pt.room, i) end
	end
	return nil
end
function Party.inLobby(p: Player): boolean return Party.homeOf(p) ~= nil end
-- the ranked leaderboard on this player's screen (the hub's RANKED regular; tab "duels" or "party", nil = duels)
function Party.openBoard(p: Player, tab: string?)
	push(p, { t = "openBoard", tab = tab })
end
-- how many are in this player's party (stand-ins too), 0 when they have none (the quests session: "play 2 matches with your party")
function Party.sizeOf(p: Player): number
	local pt = byPlayer[p]
	return if pt then #pt.members else 0
end
-- (QuickJoin.luau) this player's party as players: its leader (nil when a stand-in leads) and its real members, or
-- nil when they have none
function Party.groupOf(p: Player): (Player?, { Player }?)
	local pt = byPlayer[p]
	if not pt then return nil, nil end
	local list = {}
	for _, m in pt.members do if m.player then table.insert(list, m.player) end end
	return pt.leader.player, list
end
-- (QuickJoin.luau, wired by PlayServer) ops other server modules answer through the Play remote: Party.ops[op](p, a, b)
Party.ops = {} :: { [string]: (Player, any, any) -> any }

-- ------------------------------------------------------------------ the queue's side
local function dropEntry(pt: PartyT, why: string?)
	local e = pt.entry
	local tk = (pt :: any).ticket
	if tk and e then (pt :: any).ticket = nil; task.spawn(CrossServer.withdraw, (pt :: any).ticketKey or e.key, tk) end
	;(pt :: any).ticketKey, (pt :: any).away = nil, nil -- (a cross-server ticket, a teleport under way: CrossServer)
	if e then Queue.remove(e) end
	pt.entry = nil
	local f = pt.found
	pt.found = nil
	if f then
		-- the match it was in falls through: the others go back to searching
		local i = table.find(founds, f)
		if i then table.remove(founds, i) end
		for _, list in f.teams do
			for _, x in list do
				if x ~= e then
					local opt = x.owner :: any
					if opt and opt.entry == x then
						opt.found = nil
						Queue.back(x)
						if opt.leader then pushParty(opt :: PartyT); for _, p in realMembers(opt :: PartyT) do toast(p, "a player left the match: searching again") end end
					else
						-- (a test rival group: back in the queue too)
						if x.owner and x.owner.rival then Queue.back(x) end
					end
				end
			end
		end
	end
	if why then for _, p in realMembers(pt) do toast(p, why) end end
end

-- ------------------------------------------------------------------ joining and leaving
-- (17 Nov, the owner's second pass: a party lives in the hub too. the room opens on PLAY and closes when nobody is
-- standing in it; LEAVE LOBBY takes you back to the hub still in the party, LEAVE PARTY takes you out)
local function standInModel(m: Member): Model?
	local src = ServerStorage:FindFirstChild("JankfireNPCs")
	local tpl = src and (src:FindFirstChild(m.name) or src:GetChildren()[1])
	if not tpl or not tpl:IsA("Model") then return nil end
	local c = tpl:Clone()
	for _, d in c:GetDescendants() do
		if d:IsA("BaseScript") then d:Destroy()
		elseif d:IsA("BasePart") then d.Anchored = d.Name == "HumanoidRootPart"; d.CanTouch = false; d.CanQuery = false end
	end
	local hum = c:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	c.Name = "StandIn_" .. m.name
	c:SetAttribute("StandIn", m.id)
	return c
end

-- the party's room, built now if it has none (stand-ins get their bodies in it)
local function ensureRoom(pt: PartyT): LobbyRooms.Room?
	if pt.room then return pt.room end
	local room = LobbyRooms.claim()
	if not room then return nil end
	room.model:SetAttribute("Party", pt.id)
	pt.room = room
	for _, m in pt.members do
		if not m.player then
			m.model = standInModel(m)
			if m.model then m.model.Parent = room.model end
		end
	end
	return room
end
-- nobody real standing in the room (and no match to come back from): it goes
local function closeRoomIfEmpty(pt: PartyT)
	if not pt.room or pt.match then return end
	for _, m in pt.members do if m.player and m.inRoom then return end end
	for _, m in pt.members do m.model = nil end -- (stand-ins' bodies go with the room)
	LobbyRooms.release(pt.room)
	pt.room = nil
end

local function addMember(pt: PartyT, m: Member)
	table.insert(pt.members, m)
	if m.player then byPlayer[m.player] = pt; m.player:SetAttribute("Party", pt.id) end
	if not m.player and pt.room then
		m.model = m.model or standInModel(m)
		if m.model then m.model.Parent = pt.room.model end
	end
end

-- a party changed while searching: out of the queue (the leader queues again)
local function changed(pt: PartyT, why: string?)
	if pt.entry or pt.found then dropEntry(pt, why or "the party changed: search stopped") end
end

local function newParty(p: Player): PartyT
	nextId += 1
	local me: Member = { id = p.UserId, player = p, name = p.Name, display = p.DisplayName, inRoom = false }
	local pt: PartyT = { id = nextId, leader = me, members = {}, mode = "2v2", ranked = false, room = nil }
	parties[pt.id] = pt
	addMember(pt, me)
	return pt
end

-- into the room: a fresh body on a plinth
local function goIn(pt: PartyT, m: Member)
	-- (not out of a match, nor out of a pad's map room mid-vote: the "staging" zone, MapRooms)
	if not m.player or m.inRoom or Matches.matchOf(m.player) or m.player:GetAttribute("Zone") == "staging" then return end
	m.inRoom = true
	m.player:SetAttribute("Lobby", pt.id)
	respawn(m.player) -- (the fresh body lands on its plinth: Matches.homeOf)
end

-- PLAY: into your party's room (a party of one if you have none). the leader brings every member who isn't in a
-- match; a member goes in alone
function Party.enter(p: Player): (boolean, string?)
	if Matches.matchOf(p) then return false, "finish your match first" end
	if p:GetAttribute("Zone") == "staging" then return false, "finish the map vote first" end
	local pt = byPlayer[p] or newParty(p)
	if not ensureRoom(pt) then return false, "no lobby free right now" end
	local me = memberOf(pt, p.UserId) :: Member
	if pt.leader == me then
		for _, m in pt.members do goIn(pt, m) end
	else
		goIn(pt, me)
	end
	place(pt)
	pushParty(pt)
	return true, nil
end

-- LEAVE LOBBY: back to the hub, still in the party
function Party.exit(p: Player)
	local pt = byPlayer[p]
	if not pt then return end
	local m = memberOf(pt, p.UserId)
	if not m or not m.inRoom then return end
	m.inRoom = false
	p:SetAttribute("Lobby", nil)
	if not Matches.matchOf(p) then respawn(p) end
	closeRoomIfEmpty(pt)
	place(pt)
	pushParty(pt)
end

local function disband(pt: PartyT)
	dropEntry(pt)
	for id, iv in invites do
		if iv.party == pt then invites[id] = nil; push(iv.to, { t = "inviteGone", id = id }) end
	end
	for _, m in pt.members do
		if m.model then m.model:Destroy(); m.model = nil end
		if not m.player then table.insert(standPool, m) end -- (stand-ins go back to the pool)
	end
	if pt.room then LobbyRooms.release(pt.room); pt.room = nil end
	parties[pt.id] = nil
end

-- out of the party (LEAVE PARTY, a kick, leaving the server, joining another party). toHub: a body standing in the
-- room goes back to the hub
local function removeMember(pt: PartyT, m: Member, toHub: boolean)
	local i = table.find(pt.members, m)
	if not i then return end
	table.remove(pt.members, i)
	changed(pt, if m.player then (m.display .. " left the party: search stopped") else nil)
	if m.player then
		byPlayer[m.player] = nil
		m.player:SetAttribute("Lobby", nil)
		m.player:SetAttribute("Party", nil)
		push(m.player, { t = "party", party = nil })
		if toHub and m.inRoom and m.player.Parent and not Matches.matchOf(m.player) then respawn(m.player) end
		m.inRoom = false
	elseif m.model then
		m.model:Destroy(); m.model = nil
		table.insert(standPool, m)
	end
	if #realMembers(pt) == 0 then disband(pt); return end
	if pt.leader == m or not pt.leader.player then
		-- the lead passes to the oldest real member (web party.js: the next member who hasn't dropped)
		for _, x in pt.members do if x.player then pt.leader = x; break end end
	end
	closeRoomIfEmpty(pt)
	place(pt)
	pushParty(pt)
end

-- LEAVE PARTY
function Party.leave(p: Player)
	local pt = byPlayer[p]
	if not pt then return end
	local m = memberOf(pt, p.UserId)
	if m then removeMember(pt, m, true) end
end

-- join pt (an accepted invite): out of your own party first. if pt's room is open you go in
local function join(p: Player, pt: PartyT): (boolean, string?)
	if #pt.members >= PlayConfig.PARTY_MAX then return false, ("that party is full (%d)"):format(PlayConfig.PARTY_MAX) end
	if pt.match then return false, "they're in a match: try again after it" end
	if Matches.matchOf(p) then return false, "finish your match first" end
	local old = byPlayer[p]
	if old == pt then return true, nil end
	if old then
		local m = memberOf(old, p.UserId)
		if m then
			removeMember(old, m, pt.room == nil) -- (out of the old room: to the hub, or straight into the new one)
		end
	end
	changed(pt)
	local me: Member = { id = p.UserId, player = p, name = p.Name, display = p.DisplayName, inRoom = false }
	addMember(pt, me)
	if pt.room then goIn(pt, me) end
	place(pt)
	pushParty(pt)
	return true, nil
end

-- ------------------------------------------------------------------ invites
local function rateOk(p: Player): boolean
	local t = now()
	local keep = {}
	for _, x in sent[p] or {} do if t - x < 60 then table.insert(keep, x) end end
	if #keep >= PlayConfig.INVITES_PER_MIN then sent[p] = keep; return false end
	table.insert(keep, t)
	sent[p] = keep
	return true
end

-- (Studio tests: a stand-in says yes after a second)
local function inviteStandIn(pt: PartyT, p: Player, m: Member, id: number)
	local iv: Invite = { id = id, from = p, party = pt, toStand = m, expires = now() + PlayConfig.INVITE_TTL }
	invites[id] = iv
	pushParty(pt)
	task.delay(1, function()
		if invites[id] ~= iv or not parties[pt.id] then return end
		invites[id] = nil
		local j = table.find(standPool, m)
		if not j or #pt.members >= PlayConfig.PARTY_MAX or pt.match then pushParty(pt); return end
		table.remove(standPool, j)
		changed(pt)
		addMember(pt, m)
		place(pt)
		pushParty(pt)
	end)
end

local function invite(p: Player, targetId: number): (boolean, string?)
	if Matches.matchOf(p) then return false, "after your match" end
	local pt = byPlayer[p] or newParty(p) -- (inviting from the hub starts your party there)
	if pt.match then return false, "after the match" end
	if #pt.members >= PlayConfig.PARTY_MAX then return false, "your party is full" end
	if targetId == p.UserId then return false, "that's you" end
	if memberOf(pt, targetId) then return false, "already in your party" end
	for _, iv in invites do
		if iv.party == pt and ((iv.to and iv.to.UserId == targetId) or (iv.toStand and iv.toStand.id == targetId)) then return false, "already invited" end
	end
	local target = Players:GetPlayerByUserId(targetId)
	local stand: Member? = nil
	if not target and RunService:IsStudio() then
		for _, m in standPool do if m.id == targetId then stand = m end end
	end
	if not target and not stand then return false, "they've left" end
	if not rateOk(p) then return false, "slow down: a few invites a minute" end
	nextInvite += 1
	local id = nextInvite
	if stand then inviteStandIn(pt, p, stand, id); return true, nil end
	local iv: Invite = { id = id, from = p, party = pt, to = target, expires = now() + PlayConfig.INVITE_TTL }
	invites[id] = iv
	push(target, { t = "invite", id = id, fromId = p.UserId, fromName = p.DisplayName, mode = pt.mode, ranked = pt.ranked,
		size = #pt.members, expires = serverNow() + PlayConfig.INVITE_TTL })
	pushParty(pt)
	return true, nil
end

local function answer(p: Player, id: number, yes: boolean): (boolean, string?)
	local iv = invites[id]
	if not iv or iv.to ~= p then return false, "that invite has gone" end
	invites[id] = nil
	local pt = iv.party
	if parties[pt.id] then pushParty(pt) end
	if not yes then
		toast(iv.from, p.DisplayName .. " declined")
		return true, nil
	end
	if now() > iv.expires then return false, "that invite ran out" end
	if not parties[pt.id] then return false, "that party has gone" end
	return join(p, pt)
end

-- invites run out after INVITE_TTL; a party or a player gone takes theirs with it
local function sweepInvites()
	local t = now()
	for id, iv in invites do
		if t > iv.expires or not parties[iv.party.id] or not iv.from.Parent or (iv.to and not iv.to.Parent) then
			invites[id] = nil
			push(iv.to, { t = "inviteGone", id = id })
			if parties[iv.party.id] then pushParty(iv.party) end
		end
	end
end

-- ------------------------------------------------------------------ the mode, the search
local function setMode(p: Player, mode: any, ranked: any): (boolean, string?)
	local pt = byPlayer[p]
	if not pt then return false, "press PLAY first" end
	if pt.leader.player ~= p then return false, "only the leader picks" end
	if type(mode) ~= "string" or not PlayConfig.byId[mode] then return false, "no such mode" end
	local r = ranked == true
	local ok, why = PlayConfig.fits(PlayConfig.byId[mode], #pt.members, r)
	if not ok then return false, why end
	if pt.mode == mode and pt.ranked == r then return true, nil end
	changed(pt, "the mode changed: search stopped")
	pt.mode, pt.ranked = mode, r
	pushParty(pt)
	return true, nil
end
-- the PARTY card's FILL FROM QUICKPLAY switch (the leader's)
local function setFill(p: Player, on: any): (boolean, string?)
	local pt = byPlayer[p]
	if not pt then return false, "press PLAY first" end
	if pt.leader.player ~= p then return false, "only the leader switches it" end
	if (pt.fill == true) == (on == true) then return true, nil end
	changed(pt, "fill changed: search stopped")
	pt.fill = on == true
	pushParty(pt)
	return true, nil
end
-- the PARTY card's MAP (the leader's): an arena in the rotation, or "random" / nil for the rotation's own pick
local function setMap(p: Player, id: any): (boolean, string?)
	local pt = byPlayer[p]
	if not pt then return false, "press PLAY first" end
	if pt.leader.player ~= p then return false, "only the leader picks the map" end
	if pt.found then return false, "the match is already found" end
	local want: string? = nil
	if type(id) == "string" and id ~= "random" then
		if not table.find(Arena.pool(), id) then return false, "that map isn't in the rotation" end
		want = id
	end
	if pt.map == want then return true, nil end
	pt.map = want
	pushParty(pt)
	return true, nil
end
-- a classic mode the party picked (PARTY card), not quickplay
local function partyPicked(pt: PartyT): boolean
	local m: any = PlayConfig.byId[pt.mode]
	return m ~= nil and m.ladder == "party" and not m.quick
end

local onFormed: (string, { { Queue.Entry } }) -> ()
local function find(p: Player): (boolean, string?)
	local pt = byPlayer[p]
	if not pt then return false, "press PLAY first" end
	if pt.leader.player ~= p then return false, "only the leader starts the search" end
	if pt.match then return false, "after the match" end
	if pt.entry then return true, nil end
	local mode = PlayConfig.byId[pt.mode]
	local ok, why = PlayConfig.fits(mode, #pt.members, pt.ranked)
	if not ok then return false, why end
	local priv = PlayConfig.private(mode, #pt.members) -- (the party fills the duel by itself: private, never ranked)
	local lo, hi, sum = math.huge, -math.huge, 0
	for _, m in pt.members do
		if pt.ranked and not priv and m.player and not RankedData.ready(m.player) then return false, m.display .. "'s ranked data is still loading" end
		local r = ratingFor(m, pt.mode)
		lo, hi, sum = math.min(lo, r), math.max(hi, r), sum + r
		if m.player and Matches.matchOf(m.player) then return false, m.display .. " is in a match" end
	end
	if pt.ranked and not priv and hi - lo > Ranked.PARTY_SPREAD then
		return false, ("ranked parties must be within %d rating of each other"):format(Ranked.PARTY_SPREAD)
	end
	-- (18 Nov 2026) a party that fills a duel by itself (2 for 1V1, 3 for 1V1V1, 4 for 2V2): a private match among
	-- itself, at once (PlayConfig.private). no queue, no other servers, never ranked: the casual key, whatever the
	-- switch says. it votes on its map like any casual duel; start() splits the party into the sides
	if priv then
		local e: Queue.Entry = { key = Queue.key(pt.mode, false), mode = pt.mode, ranked = false, since = now(),
			size = #pt.members, rating = sum / #pt.members, owner = pt, state = "found" }
		pt.entry = e
		onFormed(e.key, { { e } })
		return true, nil
	end
	-- a party's own pick without FILL FROM QUICKPLAY: the party plays it alone, now, never rated
	if partyPicked(pt) and not pt.fill then
		local need = PlayConfig.counts(pt.mode)
		if pt.ranked then return false, "PARTY RANKED needs other players: turn on FILL FROM QUICKPLAY" end
		if #pt.members < need then return false, ("%s needs %d players: turn on FILL FROM QUICKPLAY"):format((mode :: any).name, need) end
		local e: Queue.Entry = { key = Queue.key(pt.mode, false), mode = pt.mode, ranked = false, since = now(),
			size = #pt.members, rating = sum / #pt.members, owner = pt, state = "found" }
		pt.entry = e
		onFormed(e.key, { { e } })
		return true, nil
	end
	local e: Queue.Entry = { key = Queue.key(pt.mode, pt.ranked), mode = pt.mode, ranked = pt.ranked, since = now(),
		size = #pt.members, rating = sum / #pt.members, owner = pt, state = "search" }
	pt.entry = e
	Queue.add(e)
	pushParty(pt)
	return true, nil
end

local function cancel(p: Player): (boolean, string?)
	local pt = byPlayer[p]
	if not pt then return false, nil end
	if not pt.entry and not pt.found then return true, nil end
	dropEntry(pt, if pt.leader.player ~= p then p.DisplayName .. " stopped the search" else nil)
	pushParty(pt)
	return true, nil
end

-- the members of an entry (a party's, or a test rival group's)
local function entryMembers(e: Queue.Entry): { Member }
	local o = e.owner :: any
	return if o and o.members then o.members else {}
end

-- every party in a found match sees it again (a vote's counts, its pick)
local function pushFound(f: Found)
	for _, list in f.teams do
		for _, e in list do
			local o = e.owner :: any
			if o and o.leader and o.found == f then pushParty(o :: PartyT) end
		end
	end
end

-- a formed match: MATCH FOUND on every member's screen, the start PlayConfig.FOUND s later (a QUICKPLAY match votes on
-- its mode first: PlayConfig.VOTE s, then the pick shows for VOTE_SHOW s)
onFormed = function(key: string, teams: { { Queue.Entry } })
	local mode = string.match(key, ":(.+)$") :: string
	local f: Found = { key = key, mode = mode, ranked = string.sub(key, 1, 7) == "ranked:", teams = teams, at = now() + PlayConfig.FOUND }
	local es = {}
	for _, list in teams do for _, e in list do table.insert(es, e) end end
	local cfg: any = PlayConfig.byId[mode]
	if mode == PlayConfig.QUICKPLAY then
		f.vote = { options = voteOffer(es), votes = {}, ends = now() + PlayConfig.VOTE }
		f.at = now() + PlayConfig.VOTE + PlayConfig.VOTE_SHOW
	end
	-- the map: ranked = the rotation's; a party's own pick = its leader's (the party that waited longest); quickplay and
	-- casual duels vote, in the same clock as the mode vote. (quickplay's maps take half its head-count a side: Crate
	-- holds 3 a side, so it sits out an 8-player match)
	if not f.ranked then
		if cfg and cfg.ladder == "party" and not cfg.quick then
			local oldest: Queue.Entry? = nil
			for _, e in es do
				local o = e.owner :: any
				if o and o.leader and (oldest == nil or e.since < (oldest :: Queue.Entry).since) then oldest = e end
			end
			local o = oldest and (oldest.owner :: any)
			if o and type(o.map) == "string" and table.find(Arena.pool(), o.map) then f.map = o.map end
		elseif mode == PlayConfig.QUICKPLAY or (cfg and cfg.pad and cfg.ladder ~= "party") then
			local n = 0
			for _, e in es do n += e.size end
			local size = if mode == PlayConfig.QUICKPLAY then (if n >= 4 then math.ceil(n / 2) else nil) else cfg.size
			local kind = if mode == PlayConfig.QUICKPLAY then "quick" else "duel"
			f.mvote = { options = mapOffer(kind, size), votes = {}, ends = now() + PlayConfig.VOTE, kind = kind }
			f.at = now() + PlayConfig.VOTE + PlayConfig.VOTE_SHOW
		end
	end
	table.insert(founds, f)
	for _, list in teams do
		for _, e in list do
			local o = e.owner :: any
			o.found = f
			if o.leader then
				pushParty(o :: PartyT)
				for _, pl in realMembers(o :: PartyT) do push(pl, { t = "found", at = serverNow() + (f.at - now()), mode = mode, ranked = f.ranked }) end
			end
		end
	end
end

-- a QUICKPLAY vote (the Play remote's "vote" op): one vote a player, changeable while the clock runs
local function castVote(f: Found?, id: number, mode: any): (boolean, string?)
	local v = f and f.vote
	if not f or not v or f.pick or now() >= v.ends then return false, "no vote running" end
	if type(mode) ~= "string" or not table.find(v.options, mode) then return false, "not one of the three" end
	v.votes[id] = mode
	pushFound(f)
	return true, nil
end
-- a map vote (the Play remote's "mapvote" op), the same way
local function castMapVote(f: Found?, id: number, map: any): (boolean, string?)
	local v = f and f.mvote
	if not f or not v or f.map or now() >= v.ends then return false, "no map vote running" end
	if type(map) ~= "string" or not table.find(v.options, map) then return false, "not one of the three" end
	v.votes[id] = map
	pushFound(f)
	return true, nil
end

-- start a found match through Matches (the pads' code: same rules, arenas, copies and cap). false = try again soon
local function start(f: Found): boolean
	if f.vote and not f.pick then f.pick = voteResult(f.vote); lastQuick = f.pick end
	settleMap(f)
	local modeId = f.pick or f.mode
	local cfg = PlayConfig.byId[modeId]
	local all: { Queue.Entry } = {}
	for _, list in f.teams do for _, e in list do table.insert(all, e) end end
	-- the sides as the queue formed them, but a classic team mode splits whole parties into two (a quickplay vote only
	-- offers one when they split), or a party alone into two halves
	local groups: { { Member } } = {}
	-- (a private duel: the party fills the mode by itself and is split into its sides, a fresh random split each time)
	local priv = #all == 1 and PlayConfig.private(cfg, #entryMembers(all[1]))
	if (cfg :: any).sides == 2 and #all == 1 then
		groups = { {}, {} }
		for i, m in entryMembers(all[1]) do table.insert(groups[(i - 1) % 2 + 1], m) end
	elseif priv then
		local ms = table.clone(entryMembers(all[1]))
		for i = #ms, 2, -1 do local j = math.random(i); ms[i], ms[j] = ms[j], ms[i] end
		local n = (cfg :: any).teams :: number
		for t = 1, n do groups[t] = {} end
		for i, m in ms do table.insert(groups[(i - 1) % n + 1], m) end
	else
		local teams = if (cfg :: any).sides == 2 then (Queue.split(all, PlayConfig.PARTY_MAX) or f.teams) else f.teams
		for t, list in teams do
			groups[t] = {}
			for _, e in list do for _, m in entryMembers(e) do table.insert(groups[t], m) end end
		end
	end
	local sides: { { Player } } = {}
	local rated = { mode = modeId, rkey = PlayConfig.ratingKey(modeId), teams = {} }
	local standIns = false
	for t, list in groups do
		sides[t], rated.teams[t] = {}, {}
		for _, m in list do
			local r, rd = ratingFor(m, modeId)
			table.insert(rated.teams[t], { id = m.id, r = r, rd = rd })
			if m.player then
				if not m.player.Parent or Matches.matchOf(m.player) then return false end
				table.insert(sides[t], m.player)
			else
				standIns = true
			end
		end
	end
	-- (one party alone is never rated: friends could farm each other. the queue only forms a ranked match of two or more.
	-- 18 Nov 2026: and a party alone, a private duel or a PARTY-card pick without fill, counts for nothing at all:
	-- private, like an owner's dev match, so no stats, XP, mastery or quests either)
	local opts: any = { queue = f.key, ranked = f.ranked and #all >= 2, rated = rated, arena = f.map, private = #all == 1,
		quick = f.mode == PlayConfig.QUICKPLAY } -- (quick: QUICKPLAY's grapple auto-lock, shared/HookCharges.AUTO)
	-- (Studio only: a match with stand-ins in it can't play out, so it is held and ends after testHold.secs)
	if standIns and RunService:IsStudio() then
		local win = testHold.win
		if win == "party" then
			win = 1
			for t, list in sides do if #list > 0 then win = t; break end end
		elseif win == "rival" then
			win = 1
			for t, list in sides do if #list == 0 then win = t; break end end
		end
		opts.hold, opts.holdWin = testHold.secs, win
	end
	-- (19 Nov 2026, the owner: "weapon ban at the start of match along with map select and banning maps too") a ranked
	-- match first runs its draft in a map room (Matches.draftRoom, server/RankedDraft.luau): each side bans a weapon, then
	-- one of three maps; it then starts here on the map left, with the bans. until then this says "not yet" each second.
	-- a whole side leaving the room calls it off: everyone back to searching
	if opts.ranked and Matches.draftRoom then
		local fd = (f :: any).draft
		if not fd then
			fd = {}
			;(f :: any).draft = fd
			local n = 0
			for _, list in sides do n += #list end
			local size = if (cfg :: any).ladder == "party" then (if n >= 4 then math.ceil(n / 2) else nil) else (cfg :: any).size
			local okD = Matches.draftRoom(sides, size, function(arena: string, bans: { string })
				fd.arena, fd.bans, fd.done = arena, bans, true
				f.at = now()
			end, function(note: string)
				fd.cancel = "the other side left the draft: searching again"
			end, standIns and RunService:IsStudio())
			if not okD then fd.done = true end -- (no room free: straight on, no draft)
			return false
		end
		if fd.cancel then
			for _, list in f.teams do
				for _, e in list do
					local o = e.owner :: any
					o.found = nil
					if o.members and o.leader then
						e.state = "search"
						e.since = now()
						pushParty(o :: PartyT)
						for _, pl in realMembers(o :: PartyT) do toast(pl, fd.cancel) end
					else
						Queue.remove(e)
					end
				end
			end
			return true -- (this found match is over)
		end
		if not fd.done then return false end
		if fd.arena then opts.arena = fd.arena end
		opts.bans = fd.bans
	end
	-- (a mode from PlayConfig.EXTRA may bring its own start; the duels go through the pads' code)
	local m = if type((cfg :: any).start) == "function" then (cfg :: any).start(sides, opts) else Matches.startQueued(cfg.pad, sides, opts)
	if not m then
		if not f.waiting then
			f.waiting = true
			for _, list in f.teams do for _, e in list do local o = e.owner :: any; if o.leader then pushParty(o :: PartyT) end end end
		end
		return false
	end
	for _, list in f.teams do
		for _, e in list do
			Queue.remove(e)
			local o = e.owner :: any
			-- (matched here: a cross-server ticket of theirs is taken back, so no other server waits for them)
			if o.ticket then task.spawn(CrossServer.withdraw, o.ticketKey or e.key, o.ticket); o.ticket, o.ticketKey = nil, nil end
			o.entry, o.found = nil, nil
			if o.members and o.leader then
				local pt = o :: PartyT
				if priv then
					-- a private duel: back to the hub after it, still a party (PLAY again opens the room)
					for _, mem in pt.members do
						if mem.player then mem.inRoom = false; mem.player:SetAttribute("Lobby", nil) end
					end
					closeRoomIfEmpty(pt)
				else
					-- the whole party comes back to the room after the match (built now if everyone had left it)
					ensureRoom(pt)
					for _, mem in pt.members do
						if mem.player then mem.inRoom = true; mem.player:SetAttribute("Lobby", pt.id) end
					end
				end
				pt.match = m.id
				pushParty(pt)
			end
		end
	end
	return true
end

-- (PlayConfig.CROSS_SERVER, on since 17 Nov 2026: CrossServer.luau) a party that has searched here for
-- CrossServer.HANDOFF s (a duel or QUICKPLAY) also offers a ticket to every server's matchmaker, and keeps searching
-- here meanwhile: whichever finds a match first wins (matched here, the ticket is taken back). a ticket's result takes
-- the party out of this server's queue and teleports its players to that match server. anything failing on the way
-- (the memory store: no ticket, it simply searches here; the teleport: an error, TeleportInitFailed, or the players
-- still here CrossServer.AWAY s on) puts the party straight back in this server's queue with a short note. the memory
-- store calls yield, so this runs on its own thread, never holding up the queue's tick
local crossT = 0
local crossBusy = false
local function withdrawTicket(pt: PartyT)
	local o = pt :: any
	if o.ticket then
		task.spawn(CrossServer.withdraw, o.ticketKey or (pt.entry and pt.entry.key) or "", o.ticket)
		o.ticket, o.ticketKey = nil, nil
	end
end
-- back to searching here after a cross-server match fell through
local function searchHere(pt: PartyT, note: string)
	local o = pt :: any
	local away = o.away
	o.away = nil
	if not away or pt.entry ~= away.e or not parties[pt.id] then return end
	local e = away.e :: Queue.Entry
	e.state = "search"
	Queue.add(e)
	pushParty(pt)
	for _, pl in realMembers(pt) do toast(pl, note) end
end
-- (CrossServer's TeleportInitFailed) a player of a party on its way out stayed: the whole party searches here again
function Party.crossFailed(p: Player)
	local pt = byPlayer[p]
	if pt and (pt :: any).away then searchHere(pt, "couldn't reach the match server: searching here again") end
end
local function crossTick()
	if not CrossServer.active() or now() - crossT < 3 then return end
	crossT = now()
	local list = {}
	for _, pt in parties do table.insert(list, pt) end
	for _, pt in list do
		if not parties[pt.id] then continue end
		local o = pt :: any
		local e = pt.entry
		-- sent off, but still here: the teleport never went
		if o.away then
			if now() - o.away.t > CrossServer.AWAY then searchHere(pt, "couldn't reach the match server: searching here again") end
			continue
		end
		-- a ticket out for a party no longer searching here (found here, cancelled, left): taken back
		if o.ticket and (not e or e.state ~= "search" or e.key ~= o.ticketKey) then withdrawTicket(pt); continue end
		if not e or e.state ~= "search" or now() - e.since < CrossServer.HANDOFF or not CrossServer.crossable(e.mode) then continue end
		local ms = {}
		for _, m in pt.members do local r, rd = ratingFor(m, e.mode); table.insert(ms, { id = m.id, r = r, rd = rd }) end
		if not o.ticket then
			local id = CrossServer.offer(e, ms) -- (yields; nil if the memory store failed: it searches here anyway)
			if id and pt.entry == e and e.state == "search" then
				o.ticket, o.ticketKey = id, e.key
				for _, pl in realMembers(pt) do toast(pl, "searching other servers too") end
			elseif id then
				task.spawn(CrossServer.withdraw, e.key, id)
			end
		else
			local res = CrossServer.result(o.ticket)
			if pt.entry ~= e or e.state ~= "search" then continue end -- (found here meanwhile: the next pass takes the ticket back)
			if res then
				o.ticket, o.ticketKey = nil, nil
				Queue.remove(e)
				e.state = "away"
				o.away = { e = e, t = now() }
				local players = realMembers(pt)
				for _, pl in players do toast(pl, "match found on another server: moving you there") end
				local ok = CrossServer.send(players, res, { leader = pt.leader.id })
				if not ok then searchHere(pt, "couldn't reach the match server: searching here again") end
			else
				CrossServer.renew(e.key, o.ticket, e, ms)
			end
		end
	end
end

local function tick()
	sweepInvites()
	if not crossBusy and CrossServer.active() then
		crossBusy = true
		task.spawn(function() pcall(crossTick); crossBusy = false end)
	end
	Queue.step(now(), onFormed)
	for _, f in table.clone(founds) do
		-- (a quickplay vote's clock ran out: its pick shows for PlayConfig.VOTE_SHOW s, then the match starts)
		if f.vote and not f.pick and now() >= f.vote.ends then
			f.pick = voteResult(f.vote)
			lastQuick = f.pick
			settleMap(f)
			pushFound(f)
		elseif f.mvote and not f.map and now() >= f.mvote.ends then
			settleMap(f)
			pushFound(f)
		end
		if now() >= f.at then
			if start(f) then
				local i = table.find(founds, f)
				if i then table.remove(founds, i) end
			else
				f.at = now() + 1 -- (all arenas busy, or someone left: again in a second; dropEntry cleans up a leaver)
			end
		end
	end
end

-- a party's match is over: its players respawn on their plinths (Matches.homeOf) once Matches sends them home
local function onEnd(m: any)
	if not m.queue then return end
	-- (a play of the match keeps everyone in the arena longer: Matches.afterHook says how long)
	local after = if Matches.afterHook then Matches.afterHook(m) else nil
	task.delay((if after then after.total else (Matches.AFTER or 7)) + 0.3, function()
		for _, pt in parties do
			if pt.match == m.id then
				pt.match = nil
				place(pt)
				pushParty(pt)
			end
		end
	end)
end

-- ------------------------------------------------------------------ the remote
local budget: { [Player]: { n: number, t: number } } = {}
local function spend(p: Player): boolean
	local b = budget[p] or { n = 20, t = now() }
	budget[p] = b
	b.n = math.min(20, b.n + (now() - b.t) * 6); b.t = now()
	if b.n < 1 then return false end
	b.n -= 1
	return true
end

-- the ops that respawn bodies or claim / free a room go one per HEAVY_GAP s per player (the anti-cheat audit: a client
-- spamming PLAY / LEAVE could rebuild rooms and bodies several times a second). a request inside the gap waits out the
-- rest of it, so a quick LEAVE then PLAY still works; another one while that waits is refused quietly
local HEAVY_GAP = 2
local HEAVY = { play = true, leave = true, leaveparty = true, answer = true, kick = true, quickjoin = true }
local heavyAt: { [Player]: number } = {}
local heavyWaiting: { [Player]: boolean } = {}
local function heavyTurn(p: Player): boolean
	local left = (heavyAt[p] or -math.huge) + HEAVY_GAP - now()
	if left > 0 then
		if heavyWaiting[p] then return false end
		heavyWaiting[p] = true
		task.wait(left)
		heavyWaiting[p] = nil
		if not p.Parent then return false end
	end
	heavyAt[p] = now()
	return true
end

local function players(p: Player): any
	local mine = byPlayer[p]
	local out = {}
	for _, o in Players:GetPlayers() do
		if o ~= p then
			local inv = false
			for _, iv in invites do if iv.party == mine and iv.to == o then inv = true end end
			table.insert(out, { id = o.UserId, name = o.Name, display = o.DisplayName, mine = mine ~= nil and byPlayer[o] == mine,
				party = byPlayer[o] ~= nil, inMatch = Matches.matchOf(o) ~= nil, invited = inv, rank = RankedData.summary(o) })
		end
	end
	if RunService:IsStudio() then
		for _, m in standPool do
			local inv = false
			for _, iv in invites do if iv.party == mine and iv.toStand == m then inv = true end end
			table.insert(out, { id = m.id, name = m.name, display = m.display, standIn = true, invited = inv,
				rank = RankedData.view(m.rating and (m.rating :: any)["2v2"], "2v2") })
		end
	end
	return out
end

local function stateOf(p: Player): any
	local pt = byPlayer[p]
	local incoming = {}
	for id, iv in invites do
		if iv.to == p then
			table.insert(incoming, { id = id, fromId = iv.from.UserId, fromName = iv.from.DisplayName, mode = iv.party.mode,
				ranked = iv.party.ranked, size = #iv.party.members, expires = serverNow() + math.max(0, iv.expires - now()) })
		end
	end
	return { ok = true, party = if pt then viewOf(pt, p) else nil, invites = incoming, ranked = RankedData.modes(p),
		best = RankedData.summary(p), cross = CrossServer.active() }
end

-- (Studio: the leaderboard lists the stand-ins too, so a one-player test has a list to look at)
local function boardStandIns(r: any)
	if not RunService:IsStudio() or type(r) ~= "table" or not r.ok then return end
	local all, seen = {}, {}
	for _, m in standPool do table.insert(all, m) end
	for _, pt in parties do for _, m in pt.members do if not m.player then table.insert(all, m) end end end
	local function lpOf(q: any): number return math.floor(if type(q.lp) == "number" then q.lp else Ranked.ladderOf(q.r)) end
	for _, m in all do
		if seen[m.id] or not m.rating then continue end
		seen[m.id] = true
		local rt = m.rating :: any
		local mode, q = Ranked.best(rt)
		if mode and q and q.placed then table.insert(r.duels, { id = m.id, name = m.display, lp = lpOf(q), v = RankedData.view(q, mode) }) end
		local pq = rt[Ranked.PARTY_KEY]
		if pq and pq.placed then table.insert(r.party, { id = m.id, name = m.display, lp = lpOf(pq), v = RankedData.view(pq, Ranked.PARTY_KEY) }) end
	end
	for _, list in { r.duels, r.party } do
		table.sort(list, function(x, y) if x.lp ~= y.lp then return x.lp > y.lp end return x.name < y.name end)
	end
end

local function handle(p: Player, op: unknown, a: unknown, b: unknown): any
	if not spend(p) then return { ok = false, why = "slow down" } end
	-- (declining an invite moves nobody, so only a yes counts as heavy)
	if type(op) == "string" and HEAVY[op] and not (op == "answer" and b ~= true) and not heavyTurn(p) then return { ok = false } end
	local ok, why
	if op == "state" then return stateOf(p)
	elseif op == "players" then return { ok = true, list = players(p) }
	elseif op == "board" then
		local r = RankedData.board(p, a == true)
		boardStandIns(r)
		return r
	elseif op == "play" then ok, why = Party.enter(p)
	elseif op == "leave" then Party.exit(p); ok = true -- (LEAVE LOBBY)
	elseif op == "leaveparty" then Party.leave(p); ok = true
	elseif op == "invite" and type(a) == "number" then ok, why = invite(p, a)
	elseif op == "answer" and type(a) == "number" then ok, why = answer(p, a, b == true)
	elseif (op == "kick" or op == "promote") and type(a) == "number" then
		local pt = byPlayer[p]
		if not pt or pt.leader.player ~= p then return { ok = false, why = "only the leader can" } end
		local m = memberOf(pt, a)
		if not m or m.player == p then return { ok = false, why = "not in your party" } end
		if op == "kick" then
			if pt.match then return { ok = false, why = "after the match" } end
			removeMember(pt, m, true)
			toast(m.player, "you were removed from the party")
		else
			if not m.player then return { ok = false, why = "a stand-in can't lead" } end
			pt.leader = m
			place(pt)
			pushParty(pt)
		end
		ok = true
	elseif op == "mode" then ok, why = setMode(p, a, b)
	elseif op == "fill" then ok, why = setFill(p, a)
	elseif op == "vote" then
		local pt = byPlayer[p]
		ok, why = castVote(pt and pt.found, p.UserId, a)
	elseif op == "mapvote" then
		local pt = byPlayer[p]
		ok, why = castMapVote(pt and pt.found, p.UserId, a)
	elseif op == "map" then ok, why = setMap(p, a)
	elseif op == "find" then ok, why = find(p)
	elseif op == "cancel" then ok, why = cancel(p)
	elseif type(op) == "string" and Party.ops[op] then return Party.ops[op](p, a, b)
	else return { ok = false, why = "?" } end
	return { ok = ok == true, why = why }
end

-- ------------------------------------------------------------------ wiring
function Party.init(fight: any, matches: any, rankedData: any, remotes: Instance)
	Fight, Matches, RankedData = fight, matches, rankedData
	pushR = remotes:WaitForChild("PlayPush") :: RemoteEvent
	local fn = remotes:WaitForChild("Play") :: RemoteFunction
	fn.OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown): any
		local okC, res = pcall(handle, p, op, a, b)
		if not okC then warn("[jankfire] play: " .. tostring(res)); return { ok = false, why = "something went wrong" } end
		return res
	end
	Matches.homeOf = Party.homeOf
	Matches.onEnd(onEnd)
	-- a lobby body stands still on its plinth (anchored) whenever it respawns there
	Fight.onSpawn(function(f: any)
		local p = f.ref :: Player
		if f.kind ~= "player" or not Party.homeOf(p) or Matches.matchOf(p) then return end
		local root = rootOf(p)
		if root then root.Anchored = true end
	end)
	Players.PlayerRemoving:Connect(function(p)
		Party.leave(p)
		sent[p] = nil
		budget[p] = nil
		heavyAt[p] = nil
		heavyWaiting[p] = nil
	end)
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < PlayConfig.TICK then return end
		acc = 0
		local okT, err = pcall(tick)
		if not okT then warn("[jankfire] play tick: " .. tostring(err)) end
	end)
end

-- ------------------------------------------------------------------ Studio tests (PlayServer's JankPlayTest)
local NPC_NAMES = { "Looticus", "Dune", "Frisk1636", "Trisangle" }
local standN = 0
local function newStandIn(rating: number?, id: number?): Member
	standN += 1
	local name = NPC_NAMES[(standN - 1) % #NPC_NAMES + 1]
	local m: Member = { id = id or -standN, name = name, display = name, rating = {} }
	for _, mode in { "1v1", "2v2", "3v3", "4v4", Ranked.PARTY_KEY } do
		local q = Ranked.fresh()
		q.r = rating or 1500; q.rd = 90; q.n = 12; q.placed = true
		;(m.rating :: any)[mode] = q
	end
	return m
end

function Party.test(op: string, a: any, b: any, c: any, d: any): any
	if not RunService:IsStudio() then return nil end
	if op == "standins" then
		for _ = 1, math.clamp(tonumber(a) or 1, 1, 8) do table.insert(standPool, newStandIn(tonumber(b))) end
		local out = {}
		for _, m in standPool do table.insert(out, { id = m.id, name = m.name }) end
		return out
	elseif op == "rival" then
		-- a stand-in group searching for (mode, ranked) with `size` members rated `rating`
		local mode = if type(a) == "string" then a else "2v2"
		local group: any = { rival = true, members = {} }
		-- (c: how many, or a list of stand-in ids, so the same stand-in can play several matches: a cheat restore test)
		if type(c) == "table" then
			for _, id in c do table.insert(group.members, newStandIn(tonumber(d), tonumber(id))) end
		else
			for _ = 1, math.clamp(tonumber(c) or 1, 1, 4) do table.insert(group.members, newStandIn(tonumber(d))) end
		end
		local e: Queue.Entry = { key = Queue.key(mode, b == true), mode = mode, ranked = b == true, since = now(), size = #group.members,
			rating = tonumber(d) or 1500, owner = group, state = "search" }
		group.entry = e
		Queue.add(e)
		local ids = {}
		for _, m in group.members do table.insert(ids, m.id) end
		return { key = e.key, size = e.size, rating = e.rating, ids = ids }
	elseif op == "hold" then
		testHold.secs = tonumber(a) or testHold.secs
		testHold.win = if b == "party" or b == "rival" then b else (tonumber(b) or testHold.win)
		return testHold
	elseif op == "join" and typeof(a) == "Instance" and a:IsA("Player") then
		-- a stand-in straight into the player's party (no invite)
		local pt = byPlayer[a]
		if not pt then return false end
		local m = table.remove(standPool, 1) or newStandIn(tonumber(b))
		changed(pt)
		addMember(pt, m)
		place(pt)
		pushParty(pt)
		return { id = m.id, name = m.name }
	elseif op == "boardsample" then
		-- (the leaderboard photo: the pool's stand-ins spread over the ladders)
		for i, m in standPool do
			for mode, q in (m.rating :: any) do
				q.lp = math.max(0, 1880 - i * 150 + (i % 3) * 37 - (if mode == Ranked.PARTY_KEY then 90 else 0) + (if mode == "2v2" then 12 else 0))
				q.w, q.l = math.max(0, 22 - i), 6 + i
			end
		end
		return #standPool
	elseif op == "samplemodes" then
		-- (the same three sample classic modes the client's PlayTest "samplemodes" shows)
		if not PlayConfig.byId.sample_qp then
			PlayConfig.addMode({ id = "sample_qp", name = "QUICK PLAY", sub = "free for all · drop in any time", teams = 2, size = 4, pad = "4v4" })
			PlayConfig.addMode({ id = "sample_bomb", name = "PLANT & DEFUSE", sub = "attackers plant, defenders defuse", teams = 2, size = 4, pad = "4v4" })
			PlayConfig.addMode({ id = "sample_zm", name = "ZOMBIES", sub = "your squad against the rounds", teams = 2, size = 4, pad = "4v4", ranked = false })
		end
		return #PlayConfig.EXTRA
	elseif op == "qpvote" then
		-- (QUICKPLAY: stand-in a votes for mode b in the found match it is in)
		for _, f in founds do
			for _, list in f.teams do
				for _, e in list do
					for _, m in entryMembers(e) do
						if m.id == tonumber(a) then
							local okV, whyV = castVote(f, m.id, b)
							return { ok = okV, why = whyV, options = f.vote and f.vote.options }
						end
					end
				end
			end
		end
		return { ok = false, why = "no found match with " .. tostring(a) }
	elseif op == "qpmap" then
		-- (the map vote: stand-in a votes for map b in the found match it is in)
		for _, f in founds do
			for _, list in f.teams do
				for _, e in list do
					for _, m in entryMembers(e) do
						if m.id == tonumber(a) then
							local okV, whyV = castMapVote(f, m.id, b)
							return { ok = okV, why = whyV, options = f.mvote and f.mvote.options }
						end
					end
				end
			end
		end
		return { ok = false, why = "no found match with " .. tostring(a) }
	elseif op == "qpfill" then
		-- (QUICKPLAY and party fills: how long the oldest waits before a match goes below full; 15 s in play)
		for _, m in PlayConfig.EXTRA do (m :: any).fill = tonumber(a) or 15 end
		return { ok = true, fill = tonumber(a) or 15 }
	elseif op == "qpfound" then
		-- (the found matches: mode, vote options and votes, pick, seconds left)
		local out = {}
		for _, f in founds do
			local n = 0
			for _, list in f.teams do for _, e in list do n += e.size end end
			table.insert(out, { mode = f.mode, players = n, options = f.vote and f.vote.options, votes = f.vote and voteCounts(f.vote),
				pick = f.pick, left = f.at - now(), ranked = f.ranked,
				maps = f.mvote and f.mvote.options, mapVotes = f.mvote and voteCounts(f.mvote), map = f.map })
		end
		return out
	elseif op == "state" then
		local out = { parties = {}, queue = {}, founds = #founds, rooms = LobbyRooms.count(), pool = #standPool, invites = 0 }
		for _, pt in parties do
			local ms = {}
			for _, m in pt.members do table.insert(ms, (if m == pt.leader then "*" else "") .. m.display) end
			table.insert(out.parties, { id = pt.id, mode = pt.mode, ranked = pt.ranked, members = ms, queued = pt.entry ~= nil,
				found = pt.found ~= nil, match = pt.match, room = pt.room and pt.room.slot })
		end
		for _, e in Queue.entries() do table.insert(out.queue, { key = e.key, size = e.size, rating = e.rating, state = e.state, waited = now() - e.since }) end
		for _ in invites do out.invites += 1 end
		return out
	end
	return nil
end

return Party
