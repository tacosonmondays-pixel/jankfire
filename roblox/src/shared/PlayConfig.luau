--!strict
-- PLAY: the modes the Play screen offers, the party rules and the timings (roblox/docs/MATCHMAKING.md). shared by the
-- server (the rules) and the clients (the cards, the names, the countdowns).
local PlayConfig = {}

-- across servers (MemoryStore queues, MessagingService invites, reserved match servers: server/CrossServer.luau).
-- OFF: teleports and reserved servers don't run in Studio Play, so this has never been tested. turn on only after
-- publishing and testing it with real players
PlayConfig.CROSS_SERVER = false

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
	table.insert(PlayConfig.EXTRA, m)
	PlayConfig.byId[m.id] = m
end

PlayConfig.PARTY_MAX = 4 -- the biggest team
PlayConfig.INVITE_TTL = 60 -- s an invite stays open
PlayConfig.INVITES_PER_MIN = 6
PlayConfig.FOUND = 3 -- s from MATCH FOUND to the arena
PlayConfig.TICK = 0.5 -- s between matchmaking passes

-- can a party of `n` play this mode (it must fit one team), and may it be ranked?
function PlayConfig.fits(mode: Mode?, n: number, ranked: boolean): (boolean, string?)
	if not mode then return false, "pick a mode" end
	if n > mode.size then
		return false, if mode.size == 1 then ("solo only: your party is %d"):format(n) else ("%d a side: your party is %d"):format(mode.size, n)
	end
	if ranked and not mode.ranked then return false, mode.name .. " has no ranked queue" end
	return true, nil
end

return PlayConfig
