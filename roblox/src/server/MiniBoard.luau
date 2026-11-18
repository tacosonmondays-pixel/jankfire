--!strict
-- CHESS and CHECKERS, the server's half (shared/MiniGames.luau; shared/Chess, shared/Checkers are the rules). the
-- server holds the real game and checks every move; the table's attributes are what everyone draws (MiniBoard.client):
--   Game ("chess" | "checkers"), State ("open" | "play" | "over"), Pos (the position, the rules' encode()), Turn
--   ("A" | "B"), Last ("from,to" or a checkers jump route "a,b,c"), Took (the squares taken by the last move),
--   Check (the checked king's square, chess), Result ("A" | "B" | "draw") and Why ("mate", "resign", "time", "stale",
--   "agreed", "fifty", "repeat", "material", "blocked", "left"), Draw (the side offering a draw), ReadyA / ReadyB,
--   MoveAt (server time the move began: the move clock), N (moves so far)
-- A plays the light pieces and moves first (chess: white)
-- from the client: { op = "pick", game }, { op = "bot", level }, { op = "ready" } (two people: both ready starts it),
-- { op = "move", from, to }, { op = "resign" }, { op = "draw" } (offer, or accept the other's), { op = "decline" }
-- refusals come back by the remote: ("board", { op = "no", why })
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Chess = require(Shared:WaitForChild("Chess")) :: any
local Checkers = require(Shared:WaitForChild("Checkers")) :: any

local Board = {}
local RULES = { chess = Chess, checkers = Checkers }
local rng = Random.new()

local function other(side: string): string return if side == "A" then "B" else "A" end
local function set(T: any, k: string, v: any) T.model:SetAttribute(k, v) end
local function sideToMove(G: any): string
	if G.game == "chess" then return if G.st.side == 0 then "A" else "B" end
	return if G.st.side == 0 then "A" else "B"
end

local function publish(T: any, ctx: any)
	local G = T.g
	local R = RULES[G.game]
	set(T, "Game", G.game)
	set(T, "Pos", R.encode(G.st))
	set(T, "Turn", sideToMove(G))
	if G.game == "chess" then
		local ks = if G.st.side == 0 then G.st.kw else G.st.kb
		set(T, "Check", if G.state == "play" and Chess.inCheck(G.st) then ks else nil)
	else
		set(T, "Check", nil)
	end
	set(T, "N", G.n)
	set(T, "MoveAt", G.moveAt)
end

local function reset(T: any, game: string?, ctx: any)
	local G = T.g
	G.game = game or G.game or "chess"
	G.st = RULES[G.game].new()
	G.n = 0
	G.moveAt = ctx.now()
	set(T, "Last", nil); set(T, "Took", nil); set(T, "Result", nil); set(T, "Why", nil); set(T, "Draw", nil)
	publish(T, ctx)
end

local function setState(T: any, s: string, ctx: any)
	T.g.state = s
	set(T, "State", s)
end

function Board.setup(T: any, ctx: any)
	T.g = { game = "chess", state = "open", ready = {}, n = 0, moveAt = 0, thinking = false }
	reset(T, "chess", ctx)
	setState(T, "open", ctx)
end

function Board.canReplaceBot(T: any): boolean
	return T.g.state ~= "play"
end

local function finish(T: any, result: string, why: string, ctx: any)
	local G = T.g
	setState(T, "over", ctx)
	set(T, "Result", result)
	set(T, "Why", why)
	set(T, "Draw", nil)
	set(T, "Check", nil)
	G.ready = {}
	set(T, "ReadyA", nil); set(T, "ReadyB", nil)
end

local function start(T: any, ctx: any)
	local G = T.g
	reset(T, G.game, ctx)
	G.ready = {}
	set(T, "ReadyA", nil); set(T, "ReadyB", nil)
	setState(T, "play", ctx)
	Board.botTurn(T, ctx)
end

-- after a move: the game's end, or the next turn (the bot's, maybe)
local function afterMove(T: any, ctx: any)
	local G = T.g
	G.n += 1
	G.moveAt = ctx.now()
	set(T, "Draw", nil)
	publish(T, ctx)
	local R = RULES[G.game]
	local s = R.status(G.st)
	local mover = other(sideToMove(G))
	if s == "mate" then finish(T, mover, "mate", ctx)
	elseif s == "lost" then finish(T, mover, "blocked", ctx)
	elseif s == "stale" or s == "fifty" or s == "repeat" or s == "material" or s == "draw" then
		finish(T, "draw", if s == "draw" then "fifty" else s, ctx)
	else
		Board.botTurn(T, ctx)
	end
end

local function apply(T: any, from: number, to: number, ctx: any): boolean
	local G = T.g
	if G.game == "chess" then
		local m = Chess.find(G.st, from, to)
		if not m then return false end
		local fl = bit32.rshift(m, 15)
		local took = Chess.play(G.st, m)
		set(T, "Last", from .. "," .. to)
		local tookAt: number? = nil
		if took ~= 0 then tookAt = if bit32.band(fl, 1) ~= 0 then (if G.st.side == 8 then to - 8 else to + 8) else to end
		set(T, "Took", if tookAt then tostring(tookAt) else nil)
	else
		local m = Checkers.find(G.st, from, to)
		if not m then return false end
		Checkers.play(G.st, m)
		local p = {}
		for _, s in m.path do table.insert(p, tostring(s)) end
		set(T, "Last", table.concat(p, ","))
		local c = {}
		for _, s in m.caps do table.insert(c, tostring(s)) end
		set(T, "Took", if #c > 0 then table.concat(c, ",") else nil)
	end
	afterMove(T, ctx)
	return true
end

function Board.botTurn(T: any, ctx: any)
	local G = T.g
	if G.state ~= "play" or G.thinking then return end
	local side = sideToMove(G)
	local who = T.who[side]
	if not ctx.isBot(who) then return end
	G.thinking = true
	local n0 = G.n
	task.spawn(function()
		local t0 = os.clock()
		local W = ctx.MG.BOARD
		local depth = W.DEPTH[G.game][who.level] or 2
		local noise = W.NOISE[who.level] or 0
		local R = RULES[G.game]
		local ok, m = pcall(R.best, G.st, depth, noise, function() task.wait() end)
		local wait = rng:NextNumber(W.BOT_WAIT[1], W.BOT_WAIT[2]) - (os.clock() - t0)
		if wait > 0 then task.wait(wait) end
		G.thinking = false
		if G.state ~= "play" or G.n ~= n0 or T.who[side] ~= who then return end
		if not ok or not m then warn("[MiniBoard] the bot found no move: " .. tostring(m)); return end
		if G.game == "chess" then apply(T, Chess.from(m), Chess.to(m), ctx)
		else apply(T, m.path[1], m.path[#m.path], ctx) end
	end)
end

function Board.joined(T: any, side: string, p: Player, ctx: any)
	local G = T.g
	if G.state == "over" then
		-- a new player at a finished table: the board goes back to the start
		setState(T, "open", ctx)
		reset(T, G.game, ctx)
	end
end

function Board.left(T: any, side: string, who: any, ctx: any)
	local G = T.g
	local o = other(side)
	G.ready[side] = nil
	set(T, "Ready" .. side, nil)
	if G.state == "play" then
		if T.who[o] ~= nil then finish(T, o, "left", ctx) else setState(T, "open", ctx) end
	end
	-- a bot never sits alone
	if ctx.isBot(T.who[o]) then
		local humans = 0
		for _, s in { "A", "B" } do if T.who[s] ~= nil and not ctx.isBot(T.who[s]) then humans += 1 end end
		if humans == 0 then ctx.botSeat(T, o, nil) end
	end
	if T.who.A == nil and T.who.B == nil then
		setState(T, "open", ctx)
		reset(T, G.game, ctx)
	end
end

function Board.msg(T: any, p: Player, side: string, d: any, ctx: any)
	local G = T.g
	local o = other(side)
	local op = d.op
	if op == "pick" then
		if G.state == "play" or not RULES[d.game] then return end
		G.ready = {}
		set(T, "ReadyA", nil); set(T, "ReadyB", nil)
		setState(T, "open", ctx)
		reset(T, d.game, ctx)
	elseif op == "bot" then
		if G.state == "play" then return end
		if T.who[o] ~= nil and not ctx.isBot(T.who[o]) then return end
		local level = if ctx.MG.BOARD.NOISE[d.level] then d.level else "medium"
		ctx.botSeat(T, o, level)
		start(T, ctx)
	elseif op == "ready" then
		if G.state == "play" then return end
		if ctx.isBot(T.who[o]) then start(T, ctx); return end -- (a rematch against the same bot)
		G.ready[side] = not G.ready[side]
		set(T, "Ready" .. side, G.ready[side] or nil)
		if G.ready.A and G.ready.B and T.who.A ~= nil and T.who.B ~= nil then start(T, ctx) end
	elseif op == "move" then
		if G.state ~= "play" or sideToMove(G) ~= side then ctx.send(p, "board", { op = "no", why = "turn" }); return end
		local from, to = tonumber(d.from), tonumber(d.to)
		if not from or not to or from < 0 or from > 63 or to < 0 or to > 63 then return end
		if not apply(T, from :: number, to :: number, ctx) then ctx.send(p, "board", { op = "no", why = "illegal" }) end
	elseif op == "resign" then
		if G.state ~= "play" then return end
		finish(T, o, "resign", ctx)
	elseif op == "draw" then
		if G.state ~= "play" then return end
		if T.model:GetAttribute("Draw") == o then finish(T, "draw", "agreed", ctx); return end
		if ctx.isBot(T.who[o]) then
			-- the bot takes a draw only when it's losing
			local R = RULES[G.game]
			local sc = R.evaluate(G.st)
			local botToMove = sideToMove(G) == o
			local botView = if botToMove then sc else -sc
			if botView < -150 then finish(T, "draw", "agreed", ctx)
			else ctx.send(p, "board", { op = "no", why = "declined" }) end
			return
		end
		set(T, "Draw", side)
	elseif op == "decline" then
		if T.model:GetAttribute("Draw") == o then set(T, "Draw", nil) end
	end
end

function Board.step(T: any, dt: number, ctx: any)
	local G = T.g
	if G.state ~= "play" then return end
	local side = sideToMove(G)
	if ctx.isBot(T.who[side]) then return end
	if ctx.now() - G.moveAt > ctx.MG.BOARD.MOVE_LIMIT then finish(T, other(side), "time", ctx) end
end

return Board
