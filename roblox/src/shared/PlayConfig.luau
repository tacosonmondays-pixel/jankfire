--!strict
-- PLAY: the modes the Play screen offers, the party rules and the timings (roblox/docs/MATCHMAKING.md). shared by the
-- server (the rules) and the clients (the cards, the names, the countdowns).
local PlayConfig = {}

-- across servers (MemoryStore queues, MessagingService invites, reserved match servers: server/CrossServer.luau).
-- ON since 18 Nov 2026 (the owner: "can you also enable cross matchmaking", then "also can you enable custom
-- matchmaking for queue outside of pads"): the PLAY button's duels (casual and ranked) and QUICKPLAY reach other
-- servers after CrossServer.HANDOFF s, still searching in this server meanwhile; the hub pads stay in this server.
-- Studio never takes part (its own memory store names, no teleports) unless a test switches it on. its own publish,
-- then MATCHMAKING.md section 6's live check. false turns it off again, nothing else to undo
PlayConfig.CROSS_SERVER = true
-- the ranked extras across servers, apart from the matchmaking and still OFF (untested): the global top 100 on the
-- leaderboard (an OrderedDataStore) and a cheat restore telling another server to take it now (MessagingService)
PlayConfig.GLOBAL_RANKED = false
-- TRADING (18 Nov 2026, the owner: "we need trading"; server/Trading.luau, docs/TRADING.md). built and tested, held OFF:
-- the game's content questionnaire says "no trading" today and must say yes before this turns on (the main session)
PlayConfig.TRADING_ON = false

export type Mode = { id: string, name: string, teams: number, size: number, ranked: boolean, pad: string }
-- pad = the queue pads' Mode attribute it plays like (Matches.startQueued takes that pad's rules and arena rotation)
PlayConfig.MODES = {
	{ id = "1v1", name = "1V1", teams = 2, size = 1, ranked = true, pad = "1v1" },
	{ id = "2v2", name = "2V2", teams = 2, size = 2, ranked = true, pad = "2v2" },
	{ id = "3v3", name = "3V3", teams = 2, size = 3, ranked = true, pad = "3v3" },
	{ id = "4v4", name = "4V4", teams = 2, size = 4, ranked = true, pad = "4v4" },
	{ id = "1v1v1", name = "1V1V1", teams = 3, size = 1, ranked = false, pad = "1v1v1" },
} :: { Mode }
PlayConfig.byId = {} :: { [string]: Mode }
for _, m in PlayConfig.MODES do PlayConfig.byId[m.id] = m end

-- MODES (the Play screen's second tab): JANKFIRE's classic modes, ported by a later session. empty until then.
-- an entry is a Mode (above) plus sub (its one line); PlayConfig.addMode puts it here and in byId, so the screen draws
-- its card and the server's queue takes it like a duel. its match starts through Matches.startQueued with its pad
-- (that session can give the entry a start function instead: Party.luau's start() calls it when it is there)
PlayConfig.EXTRA = {} :: { any }
function PlayConfig.addMode(m: any)
	-- (a classic mode is ranked on the PARTY RANKED ladder unless it says ranked = false: one rating for them all)
	if m.ranked == nil then m.ranked = true end
	m.ladder = m.ladder or "party"
	table.insert(PlayConfig.EXTRA, m)
	PlayConfig.byId[m.id] = m
end
-- the rating a mode is played for: the duels' own per mode, every classic mode the one "party" rating
function PlayConfig.ratingKey(modeId: string): string
	local m = PlayConfig.byId[modeId]
	return if m and (m :: any).ladder == "party" then "party" else modeId
end

-- QUICKPLAY and PARTY (17 Nov, the owner: "also modes should be quickplay or party choosing individual modes would be
-- impossible to fill up with proper matches! maybe"). the MODES tab is two cards (client/ModesTab.luau):
--   QUICKPLAY  one public queue for every classic mode, 2-8 players, whole parties. when a match forms, its players vote
--              on 3 modes its head-count fits (Party.luau): most votes wins, a tie is drawn, no votes = a weighted draw;
--              never the server's last quickplay mode twice running
--   PARTY      the leader picks one mode (the classic modes below): the party plays it alone, or with FILL FROM QUICKPLAY
--              on, the quickplay queue tops it up (Queue.luau's formFill)
-- both are rated on the PARTY RANKED ladder like any classic mode, except a match of one party alone (it would let
-- friends farm each other)
PlayConfig.QUICKPLAY = "quickplay"
PlayConfig.VOTE = 6 -- s the mode and map votes run once a match forms (21 Nov 2026: 8 -> 6, "short", main for the owner)
PlayConfig.VOTE_SHOW = 2 -- s the picked mode shows before the match starts
-- the head-count a classic mode takes in a quickplay or party match: 2-8 unless listed here (a mode's own addMode entry
-- may say qmin / qmax instead). team modes need two a side; infection one to turn and three to chase
PlayConfig.QUICK_COUNTS = { tdm = { 4, 8 }, tags = { 4, 8 }, inf = { 4, 8 } } :: { [string]: { number } }
-- how likely a mode is to be one of the 3 on offer, and to win a vote nobody voted in: 1 unless listed
PlayConfig.QUICK_WEIGHT = {} :: { [string]: number }
-- (registered first, so it leads PlayConfig.EXTRA; ModeConfig adds the classic modes after it. min / max / fill are
-- ModeConfig.MIN / MAX / FILL's numbers: the free-for-all queue's)
PlayConfig.addMode({ id = PlayConfig.QUICKPLAY, name = "QUICKPLAY", sub = "every mode · 2 to 8 players · the match votes on its mode",
	teams = 8, size = 4, ffa = true, min = 2, max = 8, fill = 15, pad = "modes", quick = true })
-- a classic mode's head-count (lowest, highest) in a quickplay or party match
function PlayConfig.counts(id: string): (number, number)
	local m: any = PlayConfig.byId[id]
	local c = PlayConfig.QUICK_COUNTS[id]
	return (m and m.qmin) or (c and c[1]) or 2, (m and m.qmax) or (c and c[2]) or 8
end
-- the classic modes: what QUICKPLAY rotates through and a party leader picks from (every EXTRA entry but quickplay)
function PlayConfig.classic(): { any }
	local out = {}
	for _, m in PlayConfig.EXTRA do if not m.quick then table.insert(out, m) end end
	return out
end

-- ZOMBIES (19 Nov 2026: the owner brought back the web game's co-op wave mode; the mode itself is weapons-port's
-- server/Zombies.luau, docs/ZOMBIES.md). its own card on the MODES tab (client/ModesTab.luau). co-op: one squad of up
-- to 4, whole parties and solos packed together oldest first (Queue's formCoop); it starts when full, or COOP_WAIT s
-- after its oldest began searching, and the mode's bots fill the empty slots. never ranked, never across servers
-- (CrossServer.crossable), its own maps (Zombies.maps(), never in Arena.pool). not a classic mode: in byId, not in
-- EXTRA, so QUICKPLAY and the PARTY picker never offer it. the server opens it (ReplicatedStorage attribute
-- ZombiesOn, Party.luau) once Zombies.luau has its start / busy / maps; till then the card says SOON
PlayConfig.ZOMBIES = "zombies"
PlayConfig.COOP_WAIT = 10 -- s a squad short of 4 waits for more before it goes with bots
-- (no pad: it starts through its own start, Party.luau, and so never gets the duels' map vote either)
PlayConfig.byId[PlayConfig.ZOMBIES] = { id = PlayConfig.ZOMBIES, name = "ZOMBIES", sub = "co-op waves · a squad of 4 · bots fill the empty slots",
	teams = 1, size = 4, ranked = false, coop = true } :: any

PlayConfig.PARTY_MAX = 4 -- the biggest team
PlayConfig.INVITE_TTL = 60 -- s an invite stays open
PlayConfig.INVITES_PER_MIN = 6
PlayConfig.FOUND = 3 -- s from MATCH FOUND to the arena
PlayConfig.TICK = 0.5 -- s between matchmaking passes

-- can a party of `n` play this mode (it must fit one team), and may it be ranked?
-- (18 Nov 2026, the owner: "if you're in a party of 2 you can search 1v1, it'll just send you to a private matching
-- 1v1!") a party exactly the size of a duel mode's whole match (2 for 1V1, 3 for 1V1V1, 4 for 2V2) plays it among
-- itself, at once: no queue, no other servers, never ranked whatever the switch says, and it counts for nothing
-- (Matches' m.private: no stats, XP, mastery, quests or rank), so friends can't farm each other
function PlayConfig.private(mode: any, n: number): boolean
	return mode ~= nil and mode.ladder ~= "party" and type(mode.teams) == "number" and type(mode.size) == "number"
		and n >= 2 and n == mode.teams * mode.size
end

function PlayConfig.fits(mode: Mode?, n: number, ranked: boolean): (boolean, string?)
	if not mode then return false, "pick a mode" end
	if PlayConfig.private(mode, n) then return true, nil end -- (the whole match in one party: private, any switch)
	if n > mode.size then
		return false, if mode.size == 1 then ("solo only: your party is %d"):format(n) else ("%d a side: your party is %d"):format(mode.size, n)
	end
	if ranked and not mode.ranked then return false, mode.name .. " has no ranked queue" end
	return true, nil
end

return PlayConfig
