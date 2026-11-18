--!strict
-- CHECKERS (English draughts) for the hub's games table (shared/MiniGames.luau): 8 x 8, the dark squares, 12 pieces
-- each; men move and take forward, kings both ways; a capture must be taken (any one, played to its end); a man that
-- reaches the far row is crowned and its move ends. you lose with no move left. a draw after 80 moves in a row with no
-- capture and no man moved, or the same position three times. the side that sits at A (the light pieces) moves first.
-- a small bot: negamax with alpha-beta (men, kings, how far men have come, the back row kept)
--   Checkers.new() / decode(s) / encode(st)
--   Checkers.legal(st)        { { path = { squares }, caps = { squares } } }  (path[1] = from, path[#path] = to)
--   Checkers.find(st, from, to)   the legal move between those squares (the first, if two jump routes end there)
--   Checkers.play(st, m)      make it (st changes)
--   Checkers.status(st)       "play" | "lost" (the side to move has no move) | "draw" | "repeat"
--   Checkers.best(st, depth, noise, tick)
-- squares 0..63 = rank * 8 + file, the dark ones have (rank + file) even. pieces: 0, 1 A's man, 2 A's king, 3 B's man,
-- 4 B's king. side: 0 = A (moves up the ranks), 1 = B
local Checkers = {}

export type Move = { path: { number }, caps: { number } }
export type St = { b: { number }, side: number, quiet: number, hist: { [string]: number } }

local CH = { [0] = ".", "a", "A", "b", "B" } :: { [number]: string }
local OF: { [string]: number } = { ["."] = 0, a = 1, A = 2, b = 3, B = 4 }
Checkers.CH = CH

local function mine(v: number, side: number): boolean
	return if side == 0 then (v == 1 or v == 2) else (v == 3 or v == 4)
end
local function isKing(v: number): boolean return v == 2 or v == 4 end

function Checkers.encode(st: St): string
	local t = table.create(64)
	for i = 1, 64 do t[i] = CH[st.b[i]] end
	return table.concat(t) .. " " .. (if st.side == 0 then "a" else "b") .. " " .. st.quiet
end
local function key(st: St): string
	local t = table.create(65)
	for i = 1, 64 do t[i] = CH[st.b[i]] end
	t[65] = tostring(st.side)
	return table.concat(t)
end

function Checkers.decode(s: string): St
	local board, side, quiet = string.match(s, "^(%S+) (%a) (%d+)")
	assert(board and #board == 64, "bad checkers position")
	local b = table.create(64, 0)
	for i = 1, 64 do b[i] = OF[string.sub(board :: string, i, i)] or 0 end
	local st: St = { b = b, side = if side == "a" then 0 else 1, quiet = tonumber(quiet) or 0, hist = {} }
	st.hist[key(st)] = 1
	return st
end

function Checkers.new(): St
	local t = table.create(64, ".")
	for s = 0, 63 do
		local r, f = s // 8, s % 8
		if (r + f) % 2 == 0 then
			if r <= 2 then t[s + 1] = "a" elseif r >= 5 then t[s + 1] = "b" end
		end
	end
	return Checkers.decode(table.concat(t) .. " a 0")
end

local function dirsOf(v: number): { { number } }
	if v == 1 then return { { 1, 1 }, { -1, 1 } } end
	if v == 3 then return { { 1, -1 }, { -1, -1 } } end
	return { { 1, 1 }, { -1, 1 }, { 1, -1 }, { -1, -1 } }
end
local function crownRow(v: number): number? return if v == 1 then 7 elseif v == 3 then 0 else nil end

-- every full jump route from s for the piece v (the board as it is: taken pieces stay till the end, but can't be
-- jumped twice)
local function jumps(b: { number }, s: number, v: number, side: number, path: { number }, caps: { number }, taken: { [number]: boolean }, out: { Move })
	local f, r = s % 8, s // 8
	local any = false
	for _, d in dirsOf(v) do
		local f1, r1, f2, r2 = f + d[1], r + d[2], f + 2 * d[1], r + 2 * d[2]
		if f2 < 0 or f2 > 7 or r2 < 0 or r2 > 7 then continue end
		local mid, to = r1 * 8 + f1, r2 * 8 + f2
		local mv = b[mid + 1]
		if mv == 0 or mine(mv, side) or taken[mid] then continue end
		if b[to + 1] ~= 0 and to ~= path[1] then continue end -- (the square left can be landed on again)
		any = true
		local p2 = table.clone(path); table.insert(p2, to)
		local c2 = table.clone(caps); table.insert(c2, mid)
		taken[mid] = true
		local cr = crownRow(v)
		if cr and r2 == cr then
			table.insert(out, { path = p2, caps = c2 }) -- (crowned: the move ends here)
		else
			jumps(b, to, v, side, p2, c2, taken, out)
		end
		taken[mid] = nil
	end
	if not any and #caps > 0 then table.insert(out, { path = path, caps = caps }) end
end

function Checkers.legal(st: St): { Move }
	local b, side = st.b, st.side
	local caps: { Move } = {}
	for s = 0, 63 do
		local v = b[s + 1]
		if v ~= 0 and mine(v, side) then jumps(b, s, v, side, { s }, {}, {}, caps) end
	end
	if #caps > 0 then return caps end
	local out: { Move } = {}
	for s = 0, 63 do
		local v = b[s + 1]
		if v == 0 or not mine(v, side) then continue end
		local f, r = s % 8, s // 8
		for _, d in dirsOf(v) do
			local f1, r1 = f + d[1], r + d[2]
			if f1 < 0 or f1 > 7 or r1 < 0 or r1 > 7 then continue end
			local to = r1 * 8 + f1
			if b[to + 1] == 0 then table.insert(out, { path = { s, to }, caps = {} }) end
		end
	end
	return out
end

function Checkers.find(st: St, from: number, to: number): Move?
	for _, m in Checkers.legal(st) do
		if m.path[1] == from and m.path[#m.path] == to then return m end
	end
	return nil
end

type Undo = { m: Move, v: number, capd: { number }, quiet: number, became: number }
local function make(st: St, m: Move): Undo
	local b = st.b
	local from, to = m.path[1], m.path[#m.path]
	local v = b[from + 1]
	local u: Undo = { m = m, v = v, capd = {}, quiet = st.quiet, became = v }
	for i, c in m.caps do u.capd[i] = b[c + 1]; b[c + 1] = 0 end
	b[from + 1] = 0
	local cr = crownRow(v)
	local nv = v
	if cr and to // 8 == cr then nv = v + 1 end
	b[to + 1] = nv
	u.became = nv
	st.quiet = if #m.caps > 0 or not isKing(v) then 0 else st.quiet + 1
	st.side = 1 - st.side
	return u
end
local function unmake(st: St, u: Undo)
	local b = st.b
	local m = u.m
	b[m.path[#m.path] + 1] = 0
	b[m.path[1] + 1] = u.v
	for i, c in m.caps do b[c + 1] = u.capd[i] end
	st.quiet = u.quiet
	st.side = 1 - st.side
end

function Checkers.play(st: St, m: Move)
	make(st, m)
	local k = key(st)
	st.hist[k] = (st.hist[k] or 0) + 1
end

function Checkers.status(st: St): string
	if #Checkers.legal(st) == 0 then return "lost" end
	if st.quiet >= 80 then return "draw" end
	if (st.hist[key(st)] or 0) >= 3 then return "repeat" end
	return "play"
end

-- ------------------------------------------------------------------ the bot
local function evaluate(st: St): number
	local b = st.b
	local sc = 0
	for s = 0, 63 do
		local v = b[s + 1]
		if v == 0 then continue end
		local r, f = s // 8, s % 8
		local centre = if f >= 2 and f <= 5 and r >= 2 and r <= 5 then 6 else 0
		if v == 1 then sc += 100 + r * 5 + centre + (if r == 0 then 8 else 0)
		elseif v == 2 then sc += 165 + centre
		elseif v == 3 then sc -= 100 + (7 - r) * 5 + centre + (if r == 7 then 8 else 0)
		elseif v == 4 then sc -= 165 + centre end
	end
	return if st.side == 0 then sc else -sc
end
Checkers.evaluate = evaluate

local WIN = 100000
local nodes = 0
local tickFn: (() -> ())? = nil
local function search(st: St, depth: number, alpha: number, beta: number, ply: number): number
	nodes += 1
	if nodes % 300 == 0 and tickFn then (tickFn :: () -> ())() end
	local ms = Checkers.legal(st)
	if #ms == 0 then return -WIN + ply end
	if depth <= 0 and #ms[1].caps == 0 then return evaluate(st) end -- (never stop in the middle of an exchange)
	if depth <= -4 then return evaluate(st) end
	for _, m in ms do
		local u = make(st, m)
		local sc = -search(st, depth - 1, -beta, -alpha, ply + 1)
		unmake(st, u)
		if sc >= beta then return beta end
		if sc > alpha then alpha = sc end
	end
	return alpha
end

function Checkers.best(st0: St, depth: number, noise: number?, tickF: (() -> ())?): (Move?, number)
	local st = Checkers.decode(Checkers.encode(st0))
	nodes = 0
	tickFn = tickF
	local ms = Checkers.legal(st)
	if #ms == 0 then return nil, 0 end
	local rng = Random.new()
	local noisy = noise ~= nil and noise > 0
	local best, bestSc, alpha = ms[1], -math.huge, -WIN - 1
	for _, m in ms do
		local u = make(st, m)
		local sc = -search(st, depth - 1, -WIN - 1, if noisy then WIN + 1 else -alpha, 1)
		unmake(st, u)
		if noisy then sc += rng:NextNumber(-(noise :: number), noise :: number) end
		if sc > bestSc then best, bestSc = m, sc end
		if not noisy and sc > alpha then alpha = sc end
	end
	tickFn = nil
	return best, bestSc
end

return Checkers
