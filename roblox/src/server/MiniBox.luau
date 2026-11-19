--!strict
-- BOXING, the server's half (shared/MiniGames.luau MG.BOX has every number; the ring is built by MiniGames.server).
-- the owner, 19 Nov 2026: "when you step into the ring can it be a boxing mini game? perfect dodge, counter b low,
-- upper cut jab, hook ... weave duck you know !". the server runs the bout: every punch has a wind-up (its tell), lands
-- at a set time and is judged against what the other boxer was doing then (a dodge pressed in time counts: the client
-- says when it pressed, within a fair window, and a punch is judged GRACE s after it lands). no rewards, hub only
-- what everyone sees is in the ring model's attributes (MiniBoxUI draws it):
--   State "open" | "count" | "fight" | "rest" | "down" | "done", At (server time it began), Round, RoundEnd
--   A_hp / B_hp, A_st / B_st (rounded), A_act / B_act = "<act>:<side>:<t0>:<len>" (act: idle, jab, hook, upper, body,
--   feint, duck, weave, block, hit, open, down, up; side "L"/"R" or "-"; t0 server time; len its length),
--   A_block / B_block, A_kd / B_kd (knockdowns taken), A_dmg / B_dmg (damage dealt), Winner ("A" / "B" / "draw"),
--   Why ("ko", "points", "left"), Ev = "<n>:<kind>:<who>:<move>:<flags>" (kind hit, block, dodge, perfect, whiff, down,
--   up, bell; who = the one it happened TO for hit/block/down, the dodger for dodge/perfect; flags: "big", "counter",
--   "body"), AgainA / AgainB
-- from the client: { op = "bot", level }, { op = "act", a = jab|hook|upper|body|duck|weaveL|weaveR, t = its server
-- time }, { op = "block", on }, { op = "step" } (a dash-step: its stamina; the client moves itself), { op = "again" }
-- free in the ring since 19 Nov ("I want to freely move in the boxing arena!"): people walk where they like (their own
-- client fences them in at the ropes and turns them to face the other one), the server puts both on their marks at
-- each round's start, judges every punch by where the two bodies are (MOVES[a].reach, CONE: else a "whiff"), and walks
-- a bot (its own Humanoid, the server's physics): it hovers just out of reach, circles, steps in to punch and backs off
local Box = {}

local rng = Random.new()
local ATTACK = { jab = true, hook = true, upper = true, body = true }
local function other(s: string): string return if s == "A" then "B" else "A" end
local function set(T: any, k: string, v: any) if T.model:GetAttribute(k) ~= v then T.model:SetAttribute(k, v) end end

type F = { hp: number, st: number, act: string, side: string, t0: number, len: number, hitT: number?, untilT: number,
	block: boolean, dodge: string?, dodgeSide: string?, dodgeT0: number, dodgeLen: number, nextDodge: number,
	counterUntil: number, counter: boolean, tired: boolean, resolved: boolean, feint: boolean, kd: number, dmg: number,
	lastAct: number, nextStep: number, botNext: number, botSeen: number, botPlan: any?, botBlockTill: number,
	botWas: string, botBackUntil: number, botSlipUntil: number, botCircle: number, botCircleT: number, botFlipT: number,
	botApproach: string?, botApproachUntil: number }

local function fresh(BX: any): F
	return { hp = BX.HP, st = BX.ST_MAX, act = "idle", side = "-", t0 = 0, len = 0, hitT = nil, untilT = 0, block = false,
		dodge = nil, dodgeSide = nil, dodgeT0 = -10, dodgeLen = 0, nextDodge = 0, counterUntil = 0, counter = false,
		tired = false, resolved = true, feint = false, kd = 0, dmg = 0, lastAct = 0, nextStep = 0, botNext = 0, botSeen = 0,
		botPlan = nil, botBlockTill = 0, botWas = "idle", botBackUntil = 0, botSlipUntil = 0, botCircle = 1, botCircleT = 0,
		botFlipT = 0, botApproach = nil, botApproachUntil = 0 }
end

-- ------------------------------------------------------------------ bodies in the ring
-- a boxer's root: a person's character, a Studio stand-in's body, or the bot's
local function rootOf(T: any, side: string): BasePart?
	local who = T.who[side]
	local ch: Instance? = if typeof(who) == "Instance" and who:IsA("Player") then who.Character
		elseif type(who) == "table" and who.Character then who.Character else T.bots[side]
	return if ch then ch:FindFirstChild("HumanoidRootPart") :: BasePart? else nil
end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end
local function isPerson(who: any): boolean return typeof(who) == "Instance" and who:IsA("Player") end
-- the flat gap between the two, and the way from `side` to the other one
local function gapOf(T: any, side: string): (number, Vector3?)
	local a, b = rootOf(T, side), rootOf(T, other(side))
	if not a or not b then return 0, nil end
	local v = flat(b.Position - a.Position)
	return v.Magnitude, if v.Magnitude > 0.05 then v.Unit else nil
end

local function pubAct(T: any, side: string, f: F)
	set(T, side .. "_act", ("%s:%s:%.3f:%.3f"):format(f.act, f.side, f.t0, f.len))
end
local function pubBars(T: any)
	for _, s in { "A", "B" } do
		local f = T.g.f[s]
		set(T, s .. "_hp", math.max(0, math.floor(f.hp + 0.5)))
		set(T, s .. "_st", math.max(0, math.floor(f.st + 0.5)))
		set(T, s .. "_block", f.block)
		set(T, s .. "_kd", f.kd)
		set(T, s .. "_dmg", math.floor(f.dmg + 0.5))
	end
end
local function ev(T: any, kind: string, who: string, move: string?, flags: string?)
	T.g.evN += 1
	set(T, "Ev", ("%d:%s:%s:%s:%s"):format(T.g.evN, kind, who, move or "-", flags or ""))
end
local function state(T: any, s: string, ctx: any)
	T.g.state = s
	T.g.at = ctx.now()
	set(T, "State", s)
	set(T, "At", T.g.at)
end
local function setAct(T: any, side: string, f: F, act: string, len: number, sd: string?, ctx: any)
	f.act = act
	f.side = sd or "-"
	f.t0 = ctx.now()
	f.len = len
	pubAct(T, side, f)
end

function Box.setup(T: any, ctx: any)
	local BX = ctx.MG.BOX
	T.g = { state = "open", f = { A = fresh(BX), B = fresh(BX) }, round = 0, roundEnd = 0, at = 0, evN = 0, again = {}, pauseLeft = 0, downSide = nil }
	state(T, "open", ctx)
	for _, s in { "A", "B" } do pubAct(T, s, T.g.f[s]) end
	pubBars(T)
end

function Box.canReplaceBot(T: any): boolean
	return T.g.state == "open" or T.g.state == "done"
end

local function bothHere(T: any): boolean return T.who.A ~= nil and T.who.B ~= nil end

local function begin(T: any, ctx: any)
	local BX = ctx.MG.BOX
	local G = T.g
	G.f = { A = fresh(BX), B = fresh(BX) }
	G.round = 0
	G.again = {}
	set(T, "Winner", nil); set(T, "Why", nil); set(T, "AgainA", nil); set(T, "AgainB", nil); set(T, "Round", 0)
	for _, s in { "A", "B" } do setAct(T, s, G.f[s], "idle", 0, nil, ctx); ctx.toMark(T, s) end
	pubBars(T)
	state(T, "count", ctx)
end

local function finish(T: any, winner: string, why: string, ctx: any)
	local G = T.g
	set(T, "Winner", winner)
	set(T, "Why", why)
	for _, s in { "A", "B" } do
		local f = G.f[s]
		f.block = false
		if f.act ~= "down" then setAct(T, s, f, "idle", 0, nil, ctx) end
	end
	pubBars(T)
	ev(T, "bell", "-", "end")
	state(T, "done", ctx)
end

local function startRound(T: any, ctx: any)
	local BX = ctx.MG.BOX
	local G = T.g
	G.round += 1
	G.roundEnd = ctx.now() + BX.ROUND
	set(T, "Round", G.round)
	set(T, "RoundEnd", G.roundEnd)
	for _, s in { "A", "B" } do
		local f = G.f[s]
		f.botNext = ctx.now() + rng:NextNumber(0.8, 1.6)
		f.botApproach = nil
		setAct(T, s, f, "idle", 0, nil, ctx)
		if G.round > 1 then ctx.toMark(T, s) end -- (round 1: they're on their marks from the count)
	end
	ev(T, "bell", "-", "start")
	state(T, "fight", ctx)
end

-- ------------------------------------------------------------------ actions
local function canAct(f: F, now: number): boolean
	return now >= f.untilT and f.act ~= "down" and f.act ~= "up"
end

local function startAttack(T: any, side: string, a: string, ctx: any, botWind: number?): boolean
	local BX = ctx.MG.BOX
	local G = T.g
	local f: F = G.f[side]
	local now = ctx.now()
	if G.state ~= "fight" or not canAct(f, now) then return false end
	local m = BX.MOVES[a]
	local counter = now < f.counterUntil
	local wind = m.wind * (if counter then BX.COUNTER_WIND else 1) * (botWind or 1)
	f.counter = counter
	f.counterUntil = 0
	f.tired = f.st < m.st
	f.st = math.max(0, f.st - m.st)
	f.lastAct = now
	f.block = false
	f.dodge = nil
	f.feint = false
	f.resolved = false
	f.hitT = now + wind
	f.untilT = now + wind + m.rec
	-- a hook comes from the puncher's hand: the player's is the right hand, a bot's either
	local hand = if a == "hook" then (if ctx.isBot(T.who[side]) and rng:NextNumber() < 0.5 then "L" else "R") else "-"
	setAct(T, side, f, a, wind, hand, ctx)
	return true
end

local function startDodge(T: any, side: string, a: string, t: number, ctx: any): boolean
	local BX = ctx.MG.BOX
	local G = T.g
	local f: F = G.f[side]
	local now = ctx.now()
	if G.state ~= "fight" or not canAct(f, now) or now < f.nextDodge then return false end
	local kind = if a == "duck" then "duck" else "weave"
	local len = BX.DODGE[kind]
	f.dodge = kind
	f.dodgeSide = if a == "weaveL" then "L" elseif a == "weaveR" then "R" else nil
	f.dodgeT0 = t
	f.dodgeLen = len
	f.untilT = t + len
	f.nextDodge = t + len + BX.DODGE_REST
	f.st = math.max(0, f.st - BX.DODGE_ST)
	f.lastAct = now
	f.block = false
	setAct(T, side, f, kind, len, f.dodgeSide, ctx)
	f.t0 = t
	pubAct(T, side, f)
	return true
end

local function knockdown(T: any, side: string, ctx: any)
	local BX = ctx.MG.BOX
	local G = T.g
	local f: F = G.f[side]
	f.kd += 1
	f.hp = 0
	f.block = false
	f.dodge = nil
	setAct(T, side, f, "down", BX.DOWN, nil, ctx)
	f.untilT = ctx.now() + BX.DOWN + BX.UP
	ev(T, "down", side, "-", tostring(f.kd))
	-- the other one stops where they are
	local o: F = G.f[other(side)]
	o.resolved = true
	o.untilT = ctx.now() + BX.DOWN
	if o.act ~= "idle" then setAct(T, other(side), o, "idle", 0, nil, ctx) end
	G.downSide = side
	G.pauseLeft = math.max(0, G.roundEnd - ctx.now())
	pubBars(T)
	state(T, "down", ctx)
end

-- a punch lands: what was the other one doing at that moment?
local function resolve(T: any, side: string, ctx: any)
	local BX = ctx.MG.BOX
	local G = T.g
	local f: F = G.f[side]
	local d: F = G.f[other(side)]
	local ds = other(side)
	f.resolved = true
	local a = f.act
	local m = BX.MOVES[a]
	if not m or f.feint then return end
	-- where they are now: only someone in front of you and within the punch's reach can be hit. else a whiff: a
	-- whoosh, and a little longer before you can act (stepping out of reach is a dodge too, with no counter)
	local ra, rd = rootOf(T, side), rootOf(T, ds)
	if ra and rd then
		local v = flat(rd.Position - ra.Position)
		local dist = v.Magnitude
		local reach = (m.reach or 3.5) + (if isPerson(T.who[side]) or isPerson(T.who[ds]) then BX.REACH_SLACK else 0)
		local look = flat(ra.CFrame.LookVector)
		local ahead = dist < 0.6 or look.Magnitude < 0.01 or look.Unit:Dot(v.Unit) >= math.cos(math.rad(BX.CONE))
		if dist > reach or not ahead then
			f.untilT += BX.WHIFF_REC
			ev(T, "whiff", side, a, ("%.1f"):format(dist))
			return
		end
	end
	local hitT = f.hitT :: number
	local arrives = if f.side == "R" then "L" elseif f.side == "L" then "R" else nil -- (the side of the one it hits)
	local dodging = d.dodge ~= nil and hitT >= d.dodgeT0 - 0.02 and hitT <= d.dodgeT0 + d.dodgeLen
	local slips = false
	if dodging then
		if d.dodge == "duck" then slips = (a == "jab" or a == "hook")
		else slips = (a == "jab" or a == "upper" or a == "body") or (a == "hook" and d.dodgeSide == arrives) end
	end
	if slips then
		local perfect = hitT - d.dodgeT0 <= BX.PERFECT
		if perfect then
			f.untilT = ctx.now() + BX.OPEN
			setAct(T, side, f, "open", BX.OPEN, nil, ctx)
			d.counterUntil = ctx.now() + BX.COUNTER
			d.untilT = math.min(d.untilT, ctx.now() + 0.05) -- (free to punch back at once)
			ev(T, "perfect", ds, a, "")
		else
			ev(T, "dodge", ds, a, "")
		end
		return
	end
	if d.block and a ~= "body" and d.st > 0 then
		local dmg = m.dmg * m.chip * (if f.tired then BX.TIRED else 1)
		d.hp -= dmg
		f.dmg += dmg
		d.st = math.max(0, d.st - BX.BLOCK_HIT_ST)
		ev(T, "block", ds, a, "")
		if d.hp <= 0 then knockdown(T, ds, ctx) end
		pubBars(T)
		return
	end
	local x = (if f.counter then BX.COUNTER_X else 1) * (if f.tired then BX.TIRED else 1)
		* (if a == "upper" and dodging and d.dodge == "duck" then BX.UPPER_DUCK else 1)
	local dmg = m.dmg * x
	d.hp -= dmg
	f.dmg += dmg
	if m.drain then d.st = math.max(0, d.st - m.drain) end
	local big = m.big or f.counter
	-- the one hit: stunned, and a punch they were winding up is gone
	d.block = false
	d.dodge = nil
	d.resolved = true
	d.untilT = ctx.now() + (if big then BX.BIG_STUN else BX.HIT_STUN)
	setAct(T, ds, d, "hit", if big then BX.BIG_STUN else BX.HIT_STUN, if a == "body" then "B" else (arrives or "-"), ctx)
	local flags = {}
	if big then table.insert(flags, "big") end
	if f.counter then table.insert(flags, "counter") end
	if a == "body" then table.insert(flags, "body") end
	ev(T, "hit", ds, a, table.concat(flags, ","))
	if d.hp <= 0 then knockdown(T, ds, ctx) end
	pubBars(T)
end

-- ------------------------------------------------------------------ the bot
-- its feet (the server's physics: its own Humanoid walks, its MiniFace turns it to face you). it hovers `keep` studs
-- off, circling; steps in to punch (BOX.MOVES[a].reach) and closes a little more while it winds up; backs off after
-- a punch now and then; slips out of reach when it reads one coming (`slip`). never past the ropes (L.box.bound)
local function botMove(T: any, side: string, ctx: any)
	local BX = ctx.MG.BOX
	-- (this ring's own bound: its marker's Half, the mat's middle to inside its ropes, less a body; else L.box.bound)
	local half = T.model:GetAttribute("Half")
	local L = { bound = if type(half) == "number" then half - 1.75 else ctx.MG.L.box.bound }
	local G = T.g
	local rig = T.bots[side]
	local hum = rig and rig:FindFirstChildOfClass("Humanoid")
	local root = rig and rig:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root or root.Anchored then return end
	local f: F = G.f[side]
	local now = ctx.now()
	-- (its body is the server's: Roblox hands a body near a player to that player's physics unless told. checked once
	-- a second: on 19 Nov the first call, as it stepped in, didn't hold)
	if now >= (T.ownT or 0) then
		T.ownT = now + 1
		pcall(function() if root:GetNetworkOwner() ~= nil then root:SetNetworkOwner(nil) end end)
	end
	local dist, fwd0 = gapOf(T, side)
	local fwd = fwd0 or flat(root.CFrame.LookVector).Unit
	local ao = root:FindFirstChild("MiniFace") :: AlignOrientation?
	if ao and f.act ~= "down" then ao.CFrame = CFrame.lookAt(Vector3.zero, fwd) end
	local lp = T.cf:PointToObjectSpace(root.Position)
	-- (pushed through the ropes, or fallen: back onto its mark)
	if math.abs(lp.X) > L.bound + 2.5 or math.abs(lp.Z) > L.bound + 2.5 or lp.Y < -5 then ctx.toMark(T, side); return end
	local B = BX.BOT[T.who[side] and T.who[side].level] or BX.BOT.medium
	local free = G.state == "fight" and f.act ~= "down" and f.act ~= "up" and f.act ~= "hit" and f.act ~= "open" and fwd0 ~= nil
	if not free then hum:Move(Vector3.zero, false); return end
	local want, speed = B.keep, B.speed
	if f.botApproach then want = BX.MOVES[f.botApproach].reach - 0.5; speed = B.speed * 1.25 end
	if ATTACK[f.act] and not f.resolved and BX.MOVES[f.act] then want = BX.MOVES[f.act].reach - 0.8; speed = B.speed * 1.3 end
	if now < f.botBackUntil then want = B.keep + 2; speed = B.speed * 1.2 end
	local slipping = now < f.botSlipUntil
	if slipping then want = 99; speed = BX.STEP.speed end
	local radial = math.clamp((dist - want) / 0.8, -1, 1)
	local lat = 0
	if not ATTACK[f.act] and not slipping then
		if now >= f.botCircleT then
			f.botCircleT = now + rng:NextNumber(1.2, 2.8)
			f.botCircle = if rng:NextNumber() < 0.5 then -1 else 1
		end
		lat = f.botCircle * B.circle
	end
	local right = fwd:Cross(Vector3.yAxis)
	local ld = T.cf:VectorToObjectSpace(fwd * radial + right * lat)
	-- the ropes: nothing outward past the bound; circling into them turns it round
	local b = L.bound - 0.4
	local x, z = ld.X, ld.Z
	local blocked = false
	if (lp.X > b and x > 0) or (lp.X < -b and x < 0) then x = 0; blocked = true end
	if (lp.Z > b and z > 0) or (lp.Z < -b and z < 0) then z = 0; blocked = true end
	if blocked and lat ~= 0 and now >= f.botFlipT then f.botCircle = -f.botCircle; f.botFlipT = now + 0.8 end
	local dir = T.cf:VectorToWorldSpace(Vector3.new(x, 0, z))
	if dir.Magnitude > 1 then dir = dir.Unit end
	hum.WalkSpeed = speed
	hum:Move(dir, false)
end

local function botStep(T: any, side: string, dt: number, ctx: any)
	local BX = ctx.MG.BOX
	local G = T.g
	local f: F = G.f[side]
	local o: F = G.f[other(side)]
	local who = T.who[side]
	local B = BX.BOT[who.level] or BX.BOT.medium
	local now = ctx.now()
	-- after its punch (or a hit taken), now and then it backs off
	if f.botWas ~= f.act then
		if (ATTACK[f.botWas] or f.botWas == "hit") and not ATTACK[f.act] and rng:NextNumber() < B.backoff then
			f.botBackUntil = now + rng:NextNumber(0.4, 0.8)
		end
		f.botWas = f.act
	end
	-- a punch coming: read it (once), and answer in time
	if ATTACK[o.act] and not o.resolved and o.t0 ~= f.botSeen then
		f.botSeen = o.t0
		f.botPlan = nil
		if rng:NextNumber() < B.read then
			local at = o.t0 + rng:NextNumber(B.react[1], B.react[2])
			if at < (o.hitT :: number) - 0.04 then
				local answer
				if rng:NextNumber() < B.slip then answer = "slip"
				elseif rng:NextNumber() < B.block and o.act ~= "body" then answer = "block"
				elseif o.act == "jab" then answer = if rng:NextNumber() < 0.5 then "duck" else (if rng:NextNumber() < 0.5 then "weaveL" else "weaveR")
				elseif o.act == "hook" then answer = if rng:NextNumber() < 0.5 then "duck" else (if o.side == "R" then "weaveL" else "weaveR")
				else answer = if rng:NextNumber() < 0.5 then "weaveL" else "weaveR" end
				f.botPlan = { at = at, a = answer, till = o.hitT :: number }
			end
		end
	end
	local plan = f.botPlan
	if plan and now >= plan.at then
		f.botPlan = nil
		if plan.a == "block" then
			if canAct(f, now) then f.block = true; f.botBlockTill = plan.till + 0.15; setAct(T, side, f, "block", 0, nil, ctx) end
		elseif plan.a == "slip" then
			if canAct(f, now) then f.botSlipUntil = now + 0.13; f.botApproach = nil end
		else
			startDodge(T, side, plan.a, now, ctx)
		end
	end
	if f.block and now > (f.botBlockTill or 0) then f.block = false; if f.act == "block" then setAct(T, side, f, "idle", 0, nil, ctx) end end
	-- its own punches: right away into a counter window; else on its rhythm, if it has the breath. out of reach, it
	-- steps in first (botMove) and throws once it's there
	if not canAct(f, now) or f.block then return end
	if o.act == "down" then f.botApproach = nil; return end
	local dist = gapOf(T, side)
	local function throw(a: string)
		if startAttack(T, side, a, ctx, B.wind) and now >= f.counterUntil and rng:NextNumber() < B.feint and a ~= "jab" then
			-- a fake: the wind-up starts, then it pulls back
			f.feint = true
			local cut = ((f.hitT :: number) - now) * 0.55
			f.hitT = now + cut
			f.untilT = now + cut + 0.15
		end
	end
	if f.botApproach then
		local a = f.botApproach :: string
		if dist <= BX.MOVES[a].reach + 0.3 then
			f.botApproach = nil
			throw(a)
		elseif now > f.botApproachUntil then
			f.botApproach = nil
			f.botNext = now + rng:NextNumber(0.3, 0.8)
		end
		return
	end
	local go = now < f.counterUntil or now >= f.botNext
	if not go or f.st < 12 then return end
	f.botNext = now + rng:NextNumber(B.every[1], B.every[2])
	local r = rng:NextNumber()
	local a = if now < f.counterUntil then (if r < 0.5 then "hook" else "upper")
		elseif r < 0.4 then "jab" elseif r < 0.65 then "hook" elseif r < 0.8 then "upper" else "body"
	if dist <= BX.MOVES[a].reach + 0.3 then throw(a)
	else f.botApproach = a; f.botApproachUntil = now + 1.5 end
end

-- ------------------------------------------------------------------ the module's hooks (MiniGames.server)
function Box.joined(T: any, side: string, p: Player, ctx: any)
	local G = T.g
	ctx.gloves(T, side, true)
	if bothHere(T) and (G.state == "open" or G.state == "done") then begin(T, ctx) end
end

function Box.left(T: any, side: string, who: any, ctx: any)
	local G = T.g
	local o = other(side)
	ctx.gloves(T, side, false, who) -- (who: ctx.leave has already cleared T.who[side])
	if G.state == "fight" or G.state == "rest" or G.state == "down" or G.state == "count" then
		if T.who[o] ~= nil then finish(T, o, "left", ctx) else state(T, "open", ctx) end
	end
	G.again[side] = nil
	set(T, "Again" .. side, nil)
	if ctx.isBot(T.who[o]) then
		local humans = 0
		for _, s in { "A", "B" } do if T.who[s] ~= nil and not ctx.isBot(T.who[s]) then humans += 1 end end
		if humans == 0 then ctx.gloves(T, o, false); ctx.botSeat(T, o, nil) end
	end
	if not bothHere(T) and G.state == "done" then state(T, "open", ctx) end
end

function Box.msg(T: any, p: Player, side: string, d: any, ctx: any)
	local G = T.g
	local o = other(side)
	local now = ctx.now()
	if d.op == "bot" then
		if T.who[o] ~= nil and not ctx.isBot(T.who[o]) then return end
		if G.state ~= "open" and G.state ~= "done" then return end
		local level = if ctx.MG.BOX.BOT[d.level] then d.level else "medium"
		ctx.botSeat(T, o, level)
		task.delay(0.4, function()
			if T.who[side] == p and ctx.isBot(T.who[o]) then ctx.gloves(T, o, true); begin(T, ctx) end
		end)
	elseif d.op == "act" then
		local a = d.a
		local t = if type(d.t) == "number" and d.t == d.t then math.clamp(d.t, now - 0.3, now) else now
		if ATTACK[a] then startAttack(T, side, a, ctx)
		elseif a == "duck" or a == "weaveL" or a == "weaveR" then startDodge(T, side, a, t, ctx) end
	elseif d.op == "block" then
		local f: F = G.f[side]
		local on = d.on == true
		if on and (G.state ~= "fight" or not canAct(f, now)) then return end
		if f.block ~= on then
			f.block = on
			if on then f.dodge = nil end
			setAct(T, side, f, if on then "block" else "idle", 0, nil, ctx)
			pubBars(T)
		end
	elseif d.op == "step" then
		-- (a dash-step: the client moves itself at once; here it costs its stamina, no more often than STEP.rest)
		local f: F = G.f[side]
		local S = ctx.MG.BOX.STEP
		if G.state ~= "fight" or f.act == "down" or f.act == "up" or now < f.nextStep then return end
		f.st = math.max(0, f.st - S.st)
		f.nextStep = now + S.rest - 0.08
		f.lastAct = now
		pubBars(T)
	elseif d.op == "again" then
		if G.state ~= "done" then return end
		if ctx.isBot(T.who[o]) then begin(T, ctx); return end
		G.again[side] = true
		set(T, "Again" .. side, true)
		if G.again.A and G.again.B and bothHere(T) then begin(T, ctx) end
	end
end

-- (each ring its own: several bouts run at once, one per ring in the gym)
function Box.step(T: any, dt: number, ctx: any)
	local BX = ctx.MG.BOX
	local G = T.g
	local now = ctx.now()
	-- the bodies the server moves: a bot walks (any state: it stands still outside a round), a Studio stand-in (held
	-- still, anchored) turns to face the other one
	for _, s in { "A", "B" } do
		local who = T.who[s]
		if ctx.isBot(who) then botMove(T, s, ctx)
		elseif type(who) == "table" and who.standIn then
			local r = rootOf(T, s)
			local _, fwd = gapOf(T, s)
			if r and r.Anchored and fwd and flat(r.CFrame.LookVector).Unit:Dot(fwd) < 0.999 and G.f[s].act ~= "down" then
				(who.Character :: Model):PivotTo(CFrame.lookAt(r.Position, r.Position + fwd))
			end
		end
	end
	if G.state == "count" then
		if not bothHere(T) then state(T, "open", ctx); return end
		if now - G.at >= BX.COUNT then startRound(T, ctx) end
		return
	elseif G.state == "rest" then
		if now - G.at >= BX.REST then startRound(T, ctx) end
		return
	elseif G.state == "down" then
		local ds = G.downSide
		local f: F = G.f[ds]
		if now - G.at >= BX.DOWN then
			if f.kd >= BX.KOS then
				finish(T, other(ds), "ko", ctx)
				return
			end
			f.hp = BX.GETUP[math.min(f.kd, #BX.GETUP)]
			f.st = math.max(f.st, 50)
			setAct(T, ds, f, "up", BX.UP, nil, ctx)
			f.untilT = now + BX.UP
			ev(T, "up", ds, "-", "")
			G.roundEnd = now + G.pauseLeft + BX.UP
			set(T, "RoundEnd", G.roundEnd)
			pubBars(T)
			state(T, "fight", ctx)
		end
		return
	elseif G.state ~= "fight" then
		return
	end
	-- punches that have landed (judged a moment later, so a dodge pressed just in time still counts)
	for _, s in { "A", "B" } do
		local f: F = G.f[s]
		if ATTACK[f.act] and not f.resolved and f.hitT and now >= (f.hitT :: number) + BX.GRACE then
			resolve(T, s, ctx)
			if G.state ~= "fight" then return end
		end
	end
	-- actions ending, stamina
	for _, s in { "A", "B" } do
		local f: F = G.f[s]
		if f.act ~= "idle" and f.act ~= "block" and now >= f.untilT then
			f.dodge = nil
			setAct(T, s, f, if f.block then "block" else "idle", 0, nil, ctx)
		end
		if f.block then
			f.st = math.max(0, f.st - BX.BLOCK_DRAIN * dt)
			if f.st <= 0 then f.block = false; setAct(T, s, f, "idle", 0, nil, ctx) end
		elseif now - f.lastAct > BX.ST_WAIT and (f.act == "idle") then
			f.st = math.min(BX.ST_MAX, f.st + BX.ST_REGEN * dt)
		end
	end
	for _, s in { "A", "B" } do
		if ctx.isBot(T.who[s]) then botStep(T, s, dt, ctx) end
	end
	-- the bell
	if now >= G.roundEnd then
		if G.round >= BX.ROUNDS then
			local a, b = G.f.A.dmg, G.f.B.dmg
			finish(T, if math.abs(a - b) < 0.5 then "draw" elseif a > b then "A" else "B", "points", ctx)
		else
			for _, s in { "A", "B" } do
				local f: F = G.f[s]
				f.hp = math.min(BX.HP, f.hp + BX.REST_HP)
				f.st = BX.ST_MAX
				f.block = false
				f.dodge = nil
				setAct(T, s, f, "idle", 0, nil, ctx)
			end
			ev(T, "bell", "-", "rest")
			state(T, "rest", ctx)
		end
	end
	G.pubT = (G.pubT or 0) + dt
	if G.pubT >= 0.1 then G.pubT = 0; pubBars(T) end
end

return Box
