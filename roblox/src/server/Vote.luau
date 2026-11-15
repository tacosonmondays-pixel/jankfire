--!strict
-- the end-of-match vote (MODES.md "End of match", shared/vote.js): the end screen, then stage 1 the mode (up to 4
-- cards: the daily event, a mix of team and FFA, the mode just played only if nothing else), stage 2 the map (the one
-- just played goes last). people vote; bots vote at a random moment and only break ties. a stage closes on its timer,
-- or 2.5 s after every person has voted; a stage with one card just shows it. then the reveal, then the next round
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Modes = require(Shared:WaitForChild("Modes"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local VoteR = Remotes:WaitForChild("Vote") :: RemoteEvent

local Vote = {}
local V = Modes.VOTE
local Fight: any
local cur: { stage: string, cards: { string }, humans: { [Player]: number }, bots: { [any]: number }, allAt: number?, ends: number }? = nil
local lastVote: { [Player]: number } = {}
local lastGame, lastMap = "dm", "rooftop"
Vote.END_SCREEN = 5 -- s of the end screen (board + winner) before the first stage

local function voters(): { Player }
	local out = {}
	for _, f in Fight.all do if f.kind == "player" and f.room == "ffa" then table.insert(out, f.ref :: Player) end end
	return out
end

local function cardInfo(stage: string, id: string): { [string]: any }
	if stage == "mode" then
		local g = Modes.GAMES[id]
		return { id = id, name = g.name, desc = g.desc, teams = g.teams, event = id == Modes.eventFor(os.time() // 86400) }
	end
	local m = Modes.MAPS[id]
	return { id = id, name = m.name, desc = m.desc }
end

local function counts(): { number }
	local c = cur
	if not c then return {} end
	local out = table.create(#c.cards, 0)
	for _, i in c.humans do out[i] += 1 end
	return out
end

-- one stage: returns the winning card id
local function stage(name: string, cards: { string }, dur: number): string
	if #cards == 0 then return if name == "mode" then lastGame else lastMap end
	local infos = {}
	for _, id in cards do table.insert(infos, cardInfo(name, id)) end
	local single = #cards == 1
	local start = os.clock()
	local c = { stage = name, cards = cards, humans = {}, bots = {}, allAt = nil, ends = workspace:GetServerTimeNow() + (if single then V.single else dur) }
	cur = c
	VoteR:FireAllClients({ op = "stage", stage = name, cards = infos, ends = c.ends, single = single })
	if single then task.wait(V.single); cur = nil; return cards[1] end
	-- bots vote at a random moment (they only break ties)
	for _, f in Fight.all do
		if f.kind == "bot" then
			task.delay(V.botMin + math.random() * (V.botMax - V.botMin), function() if cur == c then c.bots[f] = math.random(#cards) end end)
		end
	end
	while true do
		task.wait(0.1)
		local people = voters()
		for p in c.humans do if not table.find(people, p) then c.humans[p] = nil end end -- (went to the Range: no say)
		local all = #people > 0
		for _, p in people do if not c.humans[p] then all = false; break end end
		if all and not c.allAt then c.allAt = os.clock() end
		if os.clock() >= Modes.closeAt(start, dur, c.allAt) then break end
	end
	local win = Modes.tally(#cards, c.humans, c.bots)
	cur = nil
	VoteR:FireAllClients({ op = "result", stage = name, win = win, id = cards[win], counts = (function() local o = table.create(#cards, 0); for _, i in c.humans do o[i] += 1 end; return o end)() })
	return cards[win]
end

function Vote.run(_board: { { any } })
	task.wait(Vote.END_SCREEN)
	local gid = stage("mode", Modes.modeCards(lastGame, os.time() // 86400, math.random), V.mode)
	local map = stage("map", Modes.mapCards(gid, lastMap), V.map)
	lastGame, lastMap = gid, map
	VoteR:FireAllClients({ op = "reveal", game = gid, map = map, gameName = Modes.GAMES[gid].name, mapName = Modes.MAPS[map].name, ends = workspace:GetServerTimeNow() + V.reveal })
	task.wait(V.reveal)
	VoteR:FireAllClients({ op = "done" })
	Fight.startRound(gid, map)
end

-- a person's vote: (stage name, card number). the stage must be the open one, the number a card, at most 4 a second
function Vote.onVote(p: Player, stageName: unknown, i: unknown)
	local c = cur
	if not c or stageName ~= c.stage or type(i) ~= "number" or i ~= math.floor(i) or i < 1 or i > #c.cards then return end
	local f = Fight.byPlayer[p]
	if not f or f.room ~= "ffa" then return end
	local t = os.clock()
	if t - (lastVote[p] or -math.huge) < 0.25 then return end
	lastVote[p] = t
	c.humans[p] = i
	VoteR:FireAllClients({ op = "counts", stage = c.stage, counts = counts() })
end

function Vote.init(fight: any)
	Fight = fight
	Fight.onRoundOver = Vote.run
	VoteR.OnServerEvent:Connect(Vote.onVote)
	Players.PlayerRemoving:Connect(function(p)
		lastVote[p] = nil
		if cur then cur.humans[p] = nil end
	end)
	-- a late joiner mid-vote sees the open stage
	Players.PlayerAdded:Connect(function(p)
		local c = cur
		if not c then return end
		local infos = {}
		for _, id in c.cards do table.insert(infos, cardInfo(c.stage, id)) end
		VoteR:FireClient(p, { op = "stage", stage = c.stage, cards = infos, ends = c.ends, single = #c.cards == 1 })
	end)
end

return Vote
