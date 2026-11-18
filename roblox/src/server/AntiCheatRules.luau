--!strict
-- the anti-cheat's numbers and its pure maths (no Roblox calls here, so they can be checked outside Studio). this sits
-- in ServerScriptService on purpose: clients can't read it, so a cheat can't be tuned to stay just under a threshold.
-- how the checks work and why each number is what it is: docs/ANTI-CHEAT.md
local S = 3 -- studs a metre

local R = {}

R.C = {
	-- switches. bans are the owner's call: off until the owner turns them on. kicks are on in a live server; in Studio a kick
	-- is only written down (it would end the Play test), see AntiCheat.server.luau
	BANS = false, -- the panel's BAN / UNBAN buttons (Players:BanAsync / UnbanAsync)
	AUTO_BAN = false, -- ban by itself after AUTO_BAN_KICKS kicks inside AUTO_BAN_DAYS (needs BANS too)
	AUTO_BAN_KICKS = 3,
	AUTO_BAN_DAYS = 7,
	BAN_DAYS = 7, -- how long a ban from the panel or the auto-ban lasts (0 = for good)
	KICK = true,
	-- the movement checks' own kicks (the ladder: teleport, noclip, inside, fly, stall, speed). off since 18 Nov 2026: a
	-- friend in the private preview was kicked for lag. off = every catch is still put back and written down, a full
	-- ladder writes "would kick" and starts counting again. the owner's panel KICK button doesn't read this
	KICK_MOVE = false,
	-- ------------------------------------------------------------------ movement
	SAMPLE = 0.1, -- s between the server's looks at each body
	GRAV = 26 * S, -- Workspace.Gravity (Config.grav)
	-- teleport: Main's old check, with room for every push the game gives on top
	maxSpeed = 140 * S, -- studs/s, any state: past any bhop, rope, pad or knock in the game
	slack = 30, -- studs of jitter allowance per look
	stallCredit = 1.0, -- s: a body that stopped moving (lag) gets this much travel time back when it catches up
	-- speed hack: only counted after a long time on the ground (a slide keeps speed for 0.8 s, bhops land for 3 ticks,
	-- ground friction (6/s) then eats any carried speed within half a second)
	groundFor = 1.6, -- s on the ground without a break
	groundWin = 0.5, -- s the speed is measured over
	run = 10 * S, -- Config.gSpeed
	sprint = 1.45, -- Config.sprintMul
	gunMul = 1.2, -- the lightest gun (the SMG)
	star = 1.25, -- the pop quiz's gold star (FastUntil)
	groundTol = 1.3, -- x on top, plus groundAdd studs/s
	groundAdd = 8,
	-- fly: in free flight a body falls with gravity. a window of free-flight looks is fitted with a parabola; its
	-- curvature is the body's vertical acceleration (-78 for anyone really falling). hovering or flying = about 0
	flyWin = 1.2, -- s
	flyMinN = 9, -- looks in the window at least
	flyAccel = 0.45, -- a window must show at least 45% of gravity pulling down
	flyRms = 0.8, -- studs: a fit worse than this (a bump, a stall, a lag burst) proves nothing
	kickUp = 12, -- studs/s: vertical speed going UP this much between two looks is a kick (gravity takes 7.8 off)
	kickClear = 6, -- studs: a kick with ground this close under the feet is a landing the looks missed
	-- the climb: since its last take-off a body can rise at most v0^2 / 2g (energy: nothing in the air pushes it up).
	-- v0 = a jump (the slide jump's 33 studs/s, +1) on top of 1.3 x its speed then (a ramp turns speed into height),
	-- or a pad's throw on top of that if one is within padNear studs, or a push's size + a jump, or a rope's ropeV0
	jumpV0 = 34,
	speedV0 = 1.3,
	padNear = 14,
	ropeV0 = 180, -- (a grapple jump: 1.12 x the rope's pull, 126, + 33 up)
	climbTol = 1.15, -- x the climb that v0 allows, plus climbAdd studs
	climbAdd = 4,
	flyRise = 6, -- studs/s up at the window's end: the catch is called "rising" rather than "hovering"
	stallFor = 3.0, -- s in the air without moving at all (an anchored body)
	quiet = 0.3, -- s after a push (knock, recoil, an item, a rope, a launch) before free flight is measured again
	quietPing = 2.5, -- x the player's ping on top for pushes the server sends (they land a round trip later)
	-- noclip: a straight line between two looks that goes in one face of something solid and out the opposite one
	-- studs of solid crossed, at two heights of the body out of three. thin on purpose: many walls are two thin skins
	-- round a hollow (the range's walls), and the in-one-face-out-the-opposite rule already rules out corner cuts
	noclipMin = 0.1,
	noclipLen = 30, -- studs: longer steps are the teleport check's (a lag burst's path isn't a straight line)
	insideFor = 3, -- looks in a row with the body's middle inside something solid
	-- lag (18 Nov 2026: a friend on a bad connection was kicked by the stall check, three 3 s freezes in two minutes).
	-- the client beats 8 times a second (client/AntiCheatPanel.client.luau, remote ACBeat, unreliable). a body that
	-- hasn't moved while nothing has come from the client for `silent` s is a frozen connection, not a hover: nothing is
	-- judged on its stale copy. when updates come again, the catch-up step gets room for the gap
	silent = 0.5, -- s with no beat and no gameplay remote
	lagMax = 4, -- s: at most this much of a gap is credited
	lagSpeed = 150, -- studs/s of travel room for each second of the gap, on top of the usual room (a rope pulls 126)
	lagAfter = 5, -- s after a gap in which a catch counts lagMul of its points
	pingBad = 0.3, -- s: a ping this high lately (pingHi) counts every catch lagMul too
	lagMul = 0.5,
	pingFall = 0.02, -- s a second: the room's ping is the highest lately, coming down this fast (spikes come back)
	-- the ladder: every catch is put back and scores points, and every catch's points halve every halfLife s. a kick
	-- takes kickAt points from at least kickMinN catches spread over kickSpan s or more: a flyer or a teleporter caught
	-- over and over, never one burst (a lag spike can trip three checks at once) and never a catch now and then
	window = 180, -- s: catches older than this are dropped (by then they're worth under 5%)
	halfLife = 40, -- s
	kickAt = 10, -- points
	kickMinN = 4, -- catches in the last kickWin s
	kickWin = 60, -- s
	kickSpan = 5, -- s from the first of those to the last
	weights = { teleport = 2, noclip = 3, inside = 2, fly = 2, stall = 2, speed = 1 } :: { [string]: number },
	-- ------------------------------------------------------------------ aim (written down for the owner, never acted on)
	aimMinHits = 30, -- hits with a one-bullet gun before the head and snap ratios count
	headRatio = 0.65, -- headshots / hits over that many (good players land 25-40%)
	snapDeg = 35, -- degrees the aim moved in the snapBefore s before a hit
	snapBefore = 0.15,
	snapRatio = 0.35, -- share of hits that came right after a snap
	smokeMin = 6, -- hits through a smoke cloud before the share counts
	smokeRatio = 0.3,
	flagEvery = 300, -- s between two flags of one kind for one player
}

-- y = a + b t + c t^2 by least squares; t from the first sample. returns (accel = 2c, velocity at the last sample,
-- rms of the fit) or nil when the samples can't fix a parabola
function R.fitParabola(ts: { number }, ys: { number }): (number?, number?, number?)
	local n = #ts
	if n < 4 then return nil, nil, nil end
	local t0 = ts[1]
	local s0, s1, s2, s3, s4 = n, 0, 0, 0, 0
	local y0, y1, y2 = 0, 0, 0
	for i = 1, n do
		local t = ts[i] - t0
		local y = ys[i]
		local t2 = t * t
		s1 += t; s2 += t2; s3 += t2 * t; s4 += t2 * t2
		y0 += y; y1 += y * t; y2 += y * t2
	end
	-- | s0 s1 s2 | |a|   |y0|
	-- | s1 s2 s3 | |b| = |y1|
	-- | s2 s3 s4 | |c|   |y2|
	local function det3(a11: number, a12: number, a13: number, a21: number, a22: number, a23: number, a31: number, a32: number, a33: number): number
		return a11 * (a22 * a33 - a23 * a32) - a12 * (a21 * a33 - a23 * a31) + a13 * (a21 * a32 - a22 * a31)
	end
	local D = det3(s0, s1, s2, s1, s2, s3, s2, s3, s4)
	if math.abs(D) < 1e-9 then return nil, nil, nil end
	local a = det3(y0, s1, s2, y1, s2, s3, y2, s3, s4) / D
	local b = det3(s0, y0, s2, s1, y1, s3, s2, y2, s4) / D
	local c = det3(s0, s1, y0, s1, s2, y1, s2, s3, y2) / D
	local err = 0
	for i = 1, n do
		local t = ts[i] - t0
		local d = ys[i] - (a + b * t + c * t * t)
		err += d * d
	end
	local tl = ts[n] - t0
	return 2 * c, b + 2 * c * tl, math.sqrt(err / n)
end

-- the fly verdict on a window of free-flight looks: "fly" (not falling as gravity demands), "rise" (the same, going
-- up), or nil. g = the body's gravity (Moon Boots-style streaks can lower it: ACGravity)
function R.flyVerdict(ts: { number }, ys: { number }, g: number): (string?, number?, number?)
	local C = R.C
	if #ts < C.flyMinN or ts[#ts] - ts[1] < C.flyWin * 0.8 then return nil, nil, nil end
	local acc, vEnd, rms = R.fitParabola(ts, ys)
	if not acc or not rms or not vEnd then return nil, nil, nil end
	if rms > C.flyRms then return nil, acc, rms end
	if acc > -g * C.flyAccel then
		return (if vEnd > C.flyRise then "rise" else "fly"), acc, rms
	end
	return nil, acc, rms
end

-- the fastest anyone can keep going on the ground (studs/s): a sprint with the lightest gun, the gold star if on
function R.groundLimit(star: boolean): number
	local C = R.C
	return C.run * C.sprint * C.gunMul * (if star then C.star else 1) * C.groundTol + C.groundAdd
end

-- how far a body may go in dt (studs): the cap, any recent push on top, the jitter slack
function R.moveRoom(dt: number, push: number, ping: number): number
	local C = R.C
	return (C.maxSpeed + push) * dt + C.slack + C.maxSpeed * math.min(ping, 0.5)
end

-- a straight step that enters one face of a solid and leaves by the opposite one (a corner cut enters one face and
-- leaves by the next one, at right angles: that's a fast body going round a corner between two looks)
function R.throughSlab(enterNormal: Vector3, exitNormal: Vector3): boolean
	return enterNormal:Dot(exitNormal) < -0.7
end

-- the ladder: add a catch, drop the old ones, return the points now (each catch's halved every halfLife s)
function R.strike(list: { { t: number, w: number } }, now: number, w: number): number
	table.insert(list, { t = now, w = w })
	return R.points(list, now)
end
function R.points(list: { { t: number, w: number } }, now: number): number
	while #list > 0 and now - list[1].t > R.C.window do table.remove(list, 1) end
	local n = 0
	for _, s in list do n += s.w * 0.5 ^ (math.max(now - s.t, 0) / R.C.halfLife) end
	return n
end
-- a kick is due: the points, and in the last kickWin s kickMinN catches or more, the first and last kickSpan s apart
-- at least (one clump of catches is never a kick)
function R.kickDue(list: { { t: number, w: number } }, now: number): boolean
	local C = R.C
	if R.points(list, now) < C.kickAt then return false end
	local n, first = 0, nil
	for _, s in list do
		if now - s.t <= C.kickWin then n += 1; first = first or s.t end
	end
	return n >= C.kickMinN and first ~= nil and list[#list].t - first >= C.kickSpan
end

-- degrees between two yaws (radians), the short way round
function R.yawDiff(a: number, b: number): number
	local d = (a - b) % (2 * math.pi)
	if d > math.pi then d = 2 * math.pi - d end
	return math.deg(d)
end

return R
