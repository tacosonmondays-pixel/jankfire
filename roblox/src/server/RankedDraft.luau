--!strict
-- RANKED's draft rules (19 Nov 2026, the owner: "limit switches on comp to 2, weapon ban at the start of match along with
-- map select and banning maps too"; docs/MATCHMAKING.md "Ranked draft"). casual play is untouched.
--   * the draft: before a ranked match starts, its players are in a map room (Matches.draftRoom). first each side bans a
--     weapon (a primary: the side's most votes, a tie drawn, no votes no ban), then each side bans one of three maps;
--     the match plays on the map left (two left: drawn). the bans hold for the whole match
--   * switches: your picks in the loadout window before round 1 are your starting set and free; after that, each break
--     between rounds you change a weapon in counts as one switch (several changes in one break are one). at most
--     MAX_SWITCHES a match; then the loadout keeps your set
-- this module holds each ranked player's match state and answers Loadout (the shop session's server/Loadout.luau:
-- RankedDraft.pick before a weapon pick takes, RankedDraft.carry for what you're armed with) and Matches (start,
-- round, stop). attributes for the clients: SwitchesLeft (a number while it counts), BannedWeapons ("lmg,sniper")
local RankedDraft = {}
RankedDraft.onChange = nil :: ((Player) -> ())? -- (Loadout sets it: a player's bans changed, re-work their next arming)

RankedDraft.ON = true -- (false: ranked plays as before, no draft, free switching)
RankedDraft.MAX_SWITCHES = 2
RankedDraft.WBAN = 10 -- s the weapon ban runs
RankedDraft.MBAN = 10 -- s the map ban runs
RankedDraft.SHOW = 2.5 -- s the bans and the map left show before the match

type St = { key: string, bans: { [string]: boolean }, used: number, lives: number, counted: { [number]: boolean } } -- (lives: rounds gone live so far)
local state: { [Player]: St } = {}

local function publish(p: Player, s: St?)
	if not p.Parent then return end
	if not s then
		p:SetAttribute("SwitchesLeft", nil)
		p:SetAttribute("BannedWeapons", nil)
		return
	end
	p:SetAttribute("SwitchesLeft", math.max(0, RankedDraft.MAX_SWITCHES - s.used))
	local list = {}
	for id in s.bans do table.insert(list, id) end
	table.sort(list)
	p:SetAttribute("BannedWeapons", if #list > 0 then table.concat(list, ",") else nil)
end

-- (Matches) a ranked match starts: its players, its bans (weapon ids)
function RankedDraft.start(key: string, players: { Player }, bans: { string }?)
	if not RankedDraft.ON then return end
	local set = {}
	for _, id in bans or {} do set[id] = true end
	for _, p in players do
		local s: St = { key = key, bans = set, used = 0, lives = 0, counted = {} }
		state[p] = s
		publish(p, s)
		if RankedDraft.onChange then pcall(RankedDraft.onChange, p) end -- (Loadout: a banned weapon in hand goes)
	end
end
-- (Matches) a round went live: picks from now on are switches, one per break between rounds (the break opens before
-- the next round's number goes up, so it's counted by the rounds gone live, not the round number)
function RankedDraft.live(key: string, players: { Player })
	for _, p in players do
		local s = state[p]
		if s and s.key == key then s.lives += 1 end
	end
end
-- (Matches) out of the match
function RankedDraft.stop(p: Player)
	if state[p] then
		state[p] = nil
		publish(p, nil)
		if RankedDraft.onChange then pcall(RankedDraft.onChange, p) end
	end
end

-- (Loadout) may p pick weapon id into a slot right now (a change of weapon, in the loadout window)? false and why
function RankedDraft.pick(p: Player, slot: string, id: string): (boolean, string?)
	local s = state[p]
	if not s then return true, nil end
	if s.bans[id] then return false, "banned this match" end
	if s.lives == 0 or s.counted[s.lives] then return true, nil end
	if s.used >= RankedDraft.MAX_SWITCHES then
		return false, ("no switches left: %d a ranked match"):format(RankedDraft.MAX_SWITCHES)
	end
	s.used += 1
	s.counted[s.lives] = true
	publish(p, s)
	return true, nil
end
-- (Loadout) is this weapon banned in p's match?
function RankedDraft.banned(p: Player, id: string?): boolean
	local s = state[p]
	return s ~= nil and id ~= nil and s.bans[id] == true
end
-- (Loadout) what p is armed with in a slot: their pick, or (banned) the slot's default, or the first live weapon of the
-- slot that isn't banned. list = the slot's live weapon ids in the roster's order
function RankedDraft.carry(p: Player, id: string, default: string, list: { string }): string
	local s = state[p]
	if not s or not s.bans[id] then return id end
	if not s.bans[default] then return default end
	for _, w in list do if not s.bans[w] then return w end end
	return id
end

-- the draft's arithmetic (Matches.draftRoom): the most-voted option of a side's votes ({ [userId] = id }), a tie drawn,
-- none = nil
function RankedDraft.top(votes: { [any]: string }, options: { string }): string?
	local counts = {}
	for _, id in votes do counts[id] = (counts[id] or 0) + 1 end
	local best, top = {}, 0
	for _, id in options do
		local c = counts[id] or 0
		if c > top then best, top = { id }, c elseif c == top and c > 0 then table.insert(best, id) end
	end
	if #best == 0 then return nil end
	return best[math.random(#best)]
end

return RankedDraft
