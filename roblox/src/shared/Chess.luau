--!strict
-- CHESS for the hub's games table (shared/MiniGames.luau): the full rules (castling, en passant, promotion to a queen,
-- check, mate, stalemate, the 50-move rule, threefold repetition, too little material) and a small bot (negamax with
-- alpha-beta, captures first, a short capture search at the leaves; material plus piece-square tables). pure: the
-- server plays the real game with it and checks every move; each client uses it to show the legal moves
--   Chess.new() / Chess.decode(s) / Chess.encode(st)   a game state <-> the table's Pos string
--   Chess.legal(st)           { move }  (a move is an integer: from | to << 6 | promo << 12 | flags << 15)
--   Chess.from(m) / Chess.to(m) / Chess.promo(m)
--   Chess.find(st, from, to)  the legal move between two squares (a pawn reaching the end becomes a queen), or nil
--   Chess.play(st, m)         make the move (st changes); returns the piece taken (0 if none)
--   Chess.status(st)          "play" | "mate" | "stale" | "fifty" | "repeat" | "material"
--   Chess.inCheck(st)         the side to move is in check
--   Chess.best(st, depth, noise, tick)   the bot's move; tick() is called every few hundred positions (the server
--                                        yields there)
-- squares: 0..63, rank * 8 + file (a1 = 0, h1 = 7, a8 = 56). pieces: 0 empty, white 1 P 2 N 3 B 4 R 5 Q 6 K, black 9..14
-- (8 + the kind). side: 0 white (A), 8 black (B)
local Chess = {}

local band, bor, lshift, rshift = bit32.band, bit32.bor, bit32.lshift, bit32.rshift
local P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6
local CH = { [0] = ".", "P", "N", "B", "R", "Q", "K", nil, nil, "p", "n", "b", "r", "q", "k" } :: { [number]: string }
local OF: { [string]: number } = {}
for k, v in CH do OF[v] = k end
Chess.CH = CH
local VALUE = { [0] = 0, 100, 320, 330, 500, 900, 0 }

export type St = { b: { number }, side: number, castle: number, ep: number, half: number, full: number, kw: number, kb: number, hist: { [string]: number } }

-- ------------------------------------------------------------------ tables
local KN: { { number } } = {}
local KG: { { number } } = {}
local RAYS: { { { number } } } = {} -- RAYS[s + 1][d] = squares out from s in direction d (1..4 rook-like, 5..8 bishop-like)
local DIRS = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 }, { 1, 1 }, { -1, 1 }, { 1, -1 }, { -1, -1 } }
for s = 0, 63 do
	local f, r = s % 8, s // 8
	local kn, kg = {}, {}
	for _, d in { { 1, 2 }, { 2, 1 }, { 2, -1 }, { 1, -2 }, { -1, -2 }, { -2, -1 }, { -2, 1 }, { -1, 2 } } do
		local ff, rr = f + d[1], r + d[2]
		if ff >= 0 and ff < 8 and rr >= 0 and rr < 8 then table.insert(kn, rr * 8 + ff) end
	end
	for _, d in DIRS do
		local ff, rr = f + d[1], r + d[2]
		if ff >= 0 and ff < 8 and rr >= 0 and rr < 8 then table.insert(kg, rr * 8 + ff) end
	end
	KN[s + 1], KG[s + 1] = kn, kg
	local rays = {}
	for i, d in DIRS do
		local ray = {}
		local ff, rr = f + d[1], r + d[2]
		while ff >= 0 and ff < 8 and rr >= 0 and rr < 8 do
			table.insert(ray, rr * 8 + ff)
			ff += d[1]; rr += d[2]
		end
		rays[i] = ray
	end
	RAYS[s + 1] = rays
end

-- piece-square tables, white's view, a1 first (black reads them mirrored). simplified: centre good, edges poor
local PST = {
	[P] = { 0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, -20, -20, 10, 10, 5, 5, -5, -10, 0, 0, -10, -5, 5, 0, 0, 0, 20, 20, 0, 0, 0,
		5, 5, 10, 25, 25, 10, 5, 5, 10, 10, 20, 30, 30, 20, 10, 10, 50, 50, 50, 50, 50, 50, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0 },
	[N] = { -50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0, 5, 5, 0, -20, -40, -30, 5, 10, 15, 15, 10, 5, -30, -30, 0, 15, 20, 20, 15, 0, -30,
		-30, 5, 15, 20, 20, 15, 5, -30, -30, 0, 10, 15, 15, 10, 0, -30, -40, -20, 0, 0, 0, 0, -20, -40, -50, -40, -30, -30, -30, -30, -40, -50 },
	[B] = { -20, -10, -10, -10, -10, -10, -10, -20, -10, 5, 0, 0, 0, 0, 5, -10, -10, 10, 10, 10, 10, 10, 10, -10, -10, 0, 10, 10, 10, 10, 0, -10,
		-10, 5, 5, 10, 10, 5, 5, -10, -10, 0, 5, 10, 10, 5, 0, -10, -10, 0, 0, 0, 0, 0, 0, -10, -20, -10, -10, -10, -10, -10, -10, -20 },
	[R] = { 0, 0, 0, 5, 5, 0, 0, 0, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5,
		-5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, 5, 10, 10, 10, 10, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0 },
	[Q] = { -20, -10, -10, -5, -5, -10, -10, -20, -10, 0, 5, 0, 0, 0, 0, -10, -10, 5, 5, 5, 5, 5, 0, -10, 0, 0, 5, 5, 5, 5, 0, -5,
		-5, 0, 5, 5, 5, 5, 0, -5, -10, 0, 5, 5, 5, 5, 0, -10, -10, 0, 0, 0, 0, 0, 0, -10, -20, -10, -10, -5, -5, -10, -10, -20 },
	[K] = { 20, 30, 10, 0, 0, 10, 30, 20, 20, 20, 0, 0, 0, 0, 20, 20, -10, -20, -20, -20, -20, -20, -20, -10, -20, -30, -30, -40, -40, -30, -30, -20,
		-30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30 },
}

-- ------------------------------------------------------------------ states
local START = "RNBQKBNRPPPPPPPP................................pppppppprnbqkbnr"

function Chess.new(): St
	return Chess.decode(START .. " w KQkq - 0 1")
end

local function key(st: St): string
	local t = table.create(68)
	for s = 0, 63 do t[s + 1] = CH[st.b[s + 1]] end
	t[65] = if st.side == 0 then "w" else "b"
	t[66] = tostring(st.castle)
	t[67] = tostring(st.ep)
	return table.concat(t)
end

function Chess.encode(st: St): string
	local t = table.create(64)
	for s = 0, 63 do t[s + 1] = CH[st.b[s + 1]] end
	local c = ""
	if band(st.castle, 1) ~= 0 then c ..= "K" end
	if band(st.castle, 2) ~= 0 then c ..= "Q" end
	if band(st.castle, 4) ~= 0 then c ..= "k" end
	if band(st.castle, 8) ~= 0 then c ..= "q" end
	return table.concat(t) .. " " .. (if st.side == 0 then "w" else "b") .. " " .. (if c == "" then "-" else c) .. " "
		.. (if st.ep >= 0 then tostring(st.ep) else "-") .. " " .. st.half .. " " .. st.full
end

function Chess.decode(s: string): St
	local board, side, cs, ep, half, full = string.match(s, "^(%S+) (%a) (%S+) (%S+) (%d+) (%d+)")
	assert(board and #board == 64, "bad chess position")
	local b = table.create(64, 0)
	local kw, kb = 4, 60
	for i = 1, 64 do
		local v = OF[string.sub(board :: string, i, i)] or 0
		b[i] = v
		if v == K then kw = i - 1 elseif v == 8 + K then kb = i - 1 end
	end
	local castle = 0
	if string.find(cs :: string, "K", 1, true) then castle = bor(castle, 1) end
	if string.find(cs :: string, "Q", 1, true) then castle = bor(castle, 2) end
	if string.find(cs :: string, "k", 1, true) then castle = bor(castle, 4) end
	if string.find(cs :: string, "q", 1, true) then castle = bor(castle, 8) end
	local st: St = { b = b, side = if side == "w" then 0 else 8, castle = castle, ep = tonumber(ep) or -1,
		half = tonumber(half) or 0, full = tonumber(full) or 1, kw = kw, kb = kb, hist = {} }
	st.hist[key(st)] = 1
	return st
end

function Chess.from(m: number): number return band(m, 63) end
function Chess.to(m: number): number return band(rshift(m, 6), 63) end
function Chess.promo(m: number): number return band(rshift(m, 12), 7) end
local function flags(m: number): number return rshift(m, 15) end
local function mv(f: number, t: number, promo: number, fl: number): number
	return bor(f, lshift(t, 6), lshift(promo, 12), lshift(fl, 15))
end
local EP, CASTLE, DOUBLE = 1, 2, 4

-- ------------------------------------------------------------------ attacks
-- is square s attacked by the side `by` (0 / 8)?
local function attacked(b: { number }, s: number, by: number): boolean
	-- pawns
	local f = s % 8
	if by == 0 then
		if s >= 9 and f > 0 and b[s - 9 + 1] == P then return true end
		if s >= 7 and f < 7 and b[s - 7 + 1] == P then return true end
	else
		if s <= 54 and f < 7 and b[s + 9 + 1] == 8 + P then return true end
		if s <= 56 and f > 0 and b[s + 7 + 1] == 8 + P then return true end
	end
	for _, t in KN[s + 1] do if b[t + 1] == by + N then return true end end
	for _, t in KG[s + 1] do if b[t + 1] == by + K then return true end end
	local rays = RAYS[s + 1]
	for d = 1, 8 do
		for _, t in rays[d] do
			local v = b[t + 1]
			if v ~= 0 then
				if v > by and v <= by + 6 then
					local k = v - by
					if k == Q or (d <= 4 and k == R) or (d > 4 and k == B) then return true end
				end
				break
			end
		end
	end
	return false
end

function Chess.inCheck(st: St): boolean
	local ks = if st.side == 0 then st.kw else st.kb
	return attacked(st.b, ks, 8 - st.side)
end

-- ------------------------------------------------------------------ moves
local function pseudo(st: St, out: { number }, capsOnly: boolean?)
	local b, us, them = st.b, st.side, 8 - st.side
	for s = 0, 63 do
		local v = b[s + 1]
		if v == 0 or v <= us or v > us + 6 then continue end
		local k = v - us
		if k == P then
			local dir = if us == 0 then 8 else -8
			local r = s // 8
			local last = if us == 0 then 6 else 1 -- (the rank before promotion)
			local f = s % 8
			local one = s + dir
			if not capsOnly or r == last then
				if b[one + 1] == 0 then
					if r == last then table.insert(out, mv(s, one, Q, 0))
					else
						table.insert(out, mv(s, one, 0, 0))
						local start = if us == 0 then 1 else 6
						if r == start and b[one + dir + 1] == 0 then table.insert(out, mv(s, one + dir, 0, DOUBLE)) end
					end
				end
			end
			for _, df in { -1, 1 } do
				if f + df < 0 or f + df > 7 then continue end
				local t = one + df
				local tv = b[t + 1]
				if tv > them and tv <= them + 6 then
					table.insert(out, mv(s, t, if r == last then Q else 0, 0))
				elseif t == st.ep then
					table.insert(out, mv(s, t, 0, EP))
				end
			end
		elseif k == N or k == K then
			for _, t in (if k == N then KN else KG)[s + 1] do
				local tv = b[t + 1]
				if tv == 0 then
					if not capsOnly then table.insert(out, mv(s, t, 0, 0)) end
				elseif tv > them and tv <= them + 6 then
					table.insert(out, mv(s, t, 0, 0))
				end
			end
			if k == K and not capsOnly then
				-- castling: rights, empty between, the king not in, through or into check
				if us == 0 and s == 4 then
					if band(st.castle, 1) ~= 0 and b[6] == 0 and b[7] == 0 and b[8] == R and not attacked(b, 4, 8) and not attacked(b, 5, 8) and not attacked(b, 6, 8) then
						table.insert(out, mv(4, 6, 0, CASTLE))
					end
					if band(st.castle, 2) ~= 0 and b[4] == 0 and b[3] == 0 and b[2] == 0 and b[1] == R and not attacked(b, 4, 8) and not attacked(b, 3, 8) and not attacked(b, 2, 8) then
						table.insert(out, mv(4, 2, 0, CASTLE))
					end
				elseif us == 8 and s == 60 then
					if band(st.castle, 4) ~= 0 and b[62] == 0 and b[63] == 0 and b[64] == 8 + R and not attacked(b, 60, 0) and not attacked(b, 61, 0) and not attacked(b, 62, 0) then
						table.insert(out, mv(60, 62, 0, CASTLE))
					end
					if band(st.castle, 8) ~= 0 and b[60] == 0 and b[59] == 0 and b[58] == 0 and b[57] == 8 + R and not attacked(b, 60, 0) and not attacked(b, 59, 0) and not attacked(b, 58, 0) then
						table.insert(out, mv(60, 58, 0, CASTLE))
					end
				end
			end
		else
			local d0, d1 = 1, 8
			if k == R then d1 = 4 elseif k == B then d0 = 5 end
			local rays = RAYS[s + 1]
			for d = d0, d1 do
				for _, t in rays[d] do
					local tv = b[t + 1]
					if tv == 0 then
						if not capsOnly then table.insert(out, mv(s, t, 0, 0)) end
					else
						if tv > them and tv <= them + 6 then table.insert(out, mv(s, t, 0, 0)) end
						break
					end
				end
			end
		end
	end
end

-- castling rights lost when a square is moved from or onto
local CASTLE_KEEP = table.create(64, 15)
CASTLE_KEEP[1] = 15 - 2; CASTLE_KEEP[8] = 15 - 1; CASTLE_KEEP[5] = 15 - 3
CASTLE_KEEP[57] = 15 - 8; CASTLE_KEEP[64] = 15 - 4; CASTLE_KEEP[61] = 15 - 12

type Undo = { m: number, cap: number, capAt: number, castle: number, ep: number, half: number, kw: number, kb: number, moved: number }

local function make(st: St, m: number): Undo
	local b = st.b
	local f, t, promo, fl = band(m, 63), band(rshift(m, 6), 63), band(rshift(m, 12), 7), rshift(m, 15)
	local v = b[f + 1]
	local u: Undo = { m = m, cap = b[t + 1], capAt = t, castle = st.castle, ep = st.ep, half = st.half, kw = st.kw, kb = st.kb, moved = v }
	if band(fl, EP) ~= 0 then
		u.capAt = if st.side == 0 then t - 8 else t + 8
		u.cap = b[u.capAt + 1]
		b[u.capAt + 1] = 0
	end
	b[t + 1] = if promo ~= 0 then st.side + promo else v
	b[f + 1] = 0
	if band(fl, CASTLE) ~= 0 then
		if t == 6 then b[6] = R; b[8] = 0
		elseif t == 2 then b[4] = R; b[1] = 0
		elseif t == 62 then b[62] = 8 + R; b[64] = 0
		elseif t == 58 then b[60] = 8 + R; b[57] = 0 end
	end
	if v == K then st.kw = t elseif v == 8 + K then st.kb = t end
	st.castle = band(st.castle, CASTLE_KEEP[f + 1], CASTLE_KEEP[t + 1])
	st.ep = if band(fl, DOUBLE) ~= 0 then (f + t) // 2 else -1
	st.half = if (v - st.side) == P or u.cap ~= 0 then 0 else st.half + 1
	if st.side == 8 then st.full += 1 end
	st.side = 8 - st.side
	return u
end

local function unmake(st: St, u: Undo)
	local b = st.b
	local m = u.m
	local f, t, fl = band(m, 63), band(rshift(m, 6), 63), rshift(m, 15)
	st.side = 8 - st.side
	if st.side == 8 then st.full -= 1 end
	b[f + 1] = u.moved
	b[t + 1] = 0
	b[u.capAt + 1] = u.cap
	if band(fl, CASTLE) ~= 0 then
		if t == 6 then b[8] = R; b[6] = 0
		elseif t == 2 then b[1] = R; b[4] = 0
		elseif t == 62 then b[64] = 8 + R; b[62] = 0
		elseif t == 58 then b[57] = 8 + R; b[60] = 0 end
	end
	st.castle, st.ep, st.half, st.kw, st.kb = u.castle, u.ep, u.half, u.kw, u.kb
end

local function legalInto(st: St, out: { number }, capsOnly: boolean?)
	local raw = {}
	pseudo(st, raw, capsOnly)
	local us = st.side
	for _, m in raw do
		local u = make(st, m)
		local ks = if us == 0 then st.kw else st.kb
		if not attacked(st.b, ks, 8 - us) then table.insert(out, m) end
		unmake(st, u)
	end
end

function Chess.legal(st: St): { number }
	local out = {}
	legalInto(st, out)
	return out
end

function Chess.find(st: St, from: number, to: number): number?
	for _, m in Chess.legal(st) do
		if band(m, 63) == from and band(rshift(m, 6), 63) == to then return m end
	end
	return nil
end

function Chess.play(st: St, m: number): number
	local u = make(st, m)
	local k = key(st)
	st.hist[k] = (st.hist[k] or 0) + 1
	return u.cap
end

local function material(b: { number }): boolean -- too little to mate on both sides
	local minors, others = 0, 0
	for i = 1, 64 do
		local v = b[i]
		if v == 0 then continue end
		local k = if v > 8 then v - 8 else v
		if k == K then continue end
		if k == N or k == B then minors += 1 else others += 1 end
	end
	return others == 0 and minors <= 1
end

function Chess.status(st: St): string
	if #Chess.legal(st) == 0 then return if Chess.inCheck(st) then "mate" else "stale" end
	if st.half >= 100 then return "fifty" end
	if (st.hist[key(st)] or 0) >= 3 then return "repeat" end
	if material(st.b) then return "material" end
	return "play"
end

-- ------------------------------------------------------------------ the bot
local function evaluate(st: St): number -- (centipawns, for the side to move)
	local b = st.b
	local sc = 0
	for i = 1, 64 do
		local v = b[i]
		if v == 0 then continue end
		if v < 8 then
			sc += VALUE[v] + PST[v][i]
		else
			local k = v - 8
			local r, f = (i - 1) // 8, (i - 1) % 8
			sc -= VALUE[k] + PST[k][(7 - r) * 8 + f + 1]
		end
	end
	return if st.side == 0 then sc else -sc
end
Chess.evaluate = evaluate

local function order(st: St, ms: { number })
	local b = st.b
	local score = {}
	for _, m in ms do
		local t, f = band(rshift(m, 6), 63), band(m, 63)
		local cap = b[t + 1]
		local s = 0
		if cap ~= 0 then
			local ck = if cap > 8 then cap - 8 else cap
			local mk = b[f + 1]; mk = if mk > 8 then mk - 8 else mk
			s = 10 * VALUE[ck] - VALUE[mk] + 10000
		end
		if band(rshift(m, 12), 7) ~= 0 then s += 9000 end
		score[m] = s
	end
	table.sort(ms, function(x, y) return score[x] > score[y] end)
end

local MATE = 100000
local nodes = 0
local tickFn: (() -> ())? = nil
local function tick()
	nodes += 1
	if nodes % 300 == 0 and tickFn then (tickFn :: () -> ())() end
end

local function quiesce(st: St, alpha: number, beta: number, depth: number): number
	tick()
	local stand = evaluate(st)
	if depth <= 0 then return stand end
	if stand >= beta then return beta end
	if stand > alpha then alpha = stand end
	local ms = {}
	legalInto(st, ms, true)
	order(st, ms)
	for _, m in ms do
		local u = make(st, m)
		local sc = -quiesce(st, -beta, -alpha, depth - 1)
		unmake(st, u)
		if sc >= beta then return beta end
		if sc > alpha then alpha = sc end
	end
	return alpha
end

local function search(st: St, depth: number, alpha: number, beta: number, ply: number, qs: number): number
	tick()
	if depth <= 0 then return if qs > 0 then quiesce(st, alpha, beta, qs) else evaluate(st) end
	local ms = {}
	legalInto(st, ms)
	if #ms == 0 then
		return if Chess.inCheck(st) then -MATE + ply else 0
	end
	if st.half >= 100 then return 0 end
	order(st, ms)
	for _, m in ms do
		local u = make(st, m)
		local sc = -search(st, depth - 1, -beta, -alpha, ply + 1, qs)
		unmake(st, u)
		if sc >= beta then return beta end
		if sc > alpha then alpha = sc end
	end
	return alpha
end

-- the bot's move at this depth; noise (centipawns) is added at random to each root move's score (an easy bot misjudges)
function Chess.best(st0: St, depth: number, noise: number?, tickF: (() -> ())?): (number?, number)
	local st = Chess.decode(Chess.encode(st0)) -- (a private copy: the search makes and unmakes on it)
	nodes = 0
	tickFn = tickF
	local ms = Chess.legal(st)
	if #ms == 0 then return nil, 0 end
	order(st, ms)
	local rng = Random.new()
	local best, bestSc = ms[1], -math.huge
	local qs = if depth >= 2 then 4 else 2
	local alpha = -MATE - 1
	local noisy = noise ~= nil and noise > 0
	for _, m in ms do
		local u = make(st, m)
		-- (with noise every root move gets a full window, so its score is real before the noise; else alpha-beta)
		local sc = -search(st, depth - 1, -MATE - 1, if noisy then MATE + 1 else -alpha, 1, qs)
		unmake(st, u)
		if noisy then sc += rng:NextNumber(-(noise :: number), noise :: number) end
		if sc > bestSc then best, bestSc = m, sc end
		if not noisy and sc > alpha then alpha = sc end
	end
	tickFn = nil
	return best, bestSc
end

return Chess
