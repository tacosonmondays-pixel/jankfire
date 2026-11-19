--!strict
-- ARM WRESTLING, the server's half (shared/MiniGames.luau; the table is built by MiniGames.server). the server keeps the
-- meter (-1..1, + is A's way) and everyone's checks; a press only says where the needle was, and the server checks
-- that against where it really was (within the press's travel time) before it counts
-- the table's attributes (everyone draws from them, MiniArm.client): State ("open" | "count" | "bout" | "slam" |
-- "done"), Bal (the meter), At (server time the state began), Winner ("A" / "B"), Hit ("<side>:<perfect|hit|miss>:<n>",
-- the last press, for the other side's flash and the sound), AgainA / AgainB (a rematch asked for)
-- a player's own check comes by the remote: ("arm", { op = "check", chk = { id, c, w, T, t0 } }), the answer to a press
-- ("arm", { op = "result", id, res })
-- from the client: { op = "bot", level } (alone: a bot sits down and the bout starts), { op = "hit", id, pos },
-- { op = "again" } (a rematch: at once against a bot, when both ask against a person)
local Players = game:GetService("Players")

local Arm = {}

local rng = Random.new()
local function lerp(a: number, b: number, t: number): number return a + (b - a) * t end
local function other(side: string): string return if side == "A" then "B" else "A" end

local function set(T: any, k: string, v: any) T.model:SetAttribute(k, v) end
local function state(T: any, s: string, ctx: any)
	T.g.state = s
	T.g.at = ctx.now()
	set(T, "State", s)
	set(T, "At", T.g.at)
end

function Arm.setup(T: any, ctx: any)
	T.g = { state = "open", bal = 0, chk = {}, n = 0, hits = 0, again = {}, w = {} }
	state(T, "open", ctx)
	set(T, "Bal", 0)
end

function Arm.canReplaceBot(T: any): boolean
	return T.g.state == "open" or T.g.state == "done"
end

local function newCheck(T: any, side: string, ctx: any)
	local A = T.g
	local MA = ctx.MG.ARM
	local k = math.clamp((ctx.now() - A.boutT0) / MA.SHRINK, 0, 1)
	local w = A.w[side] or MA.W0 -- (your own zone: smaller with every hit, MG.ARM.HIT_SHRINK)
	local per = lerp(MA.T0, MA.T1, k)
	A.n += 1
	local chk = { id = A.n, c = rng:NextNumber(0.2 + w * 0.5, 1 - w - 0.04), w = w, T = per, t0 = ctx.now() + MA.GAP }
	A.chk[side] = chk
	local who = T.who[side]
	if ctx.isBot(who) then
		local B = MA.BOT[who.level] or MA.BOT.medium
		A.botAt = ctx.now() + MA.GAP + rng:NextNumber(B.every[1], B.every[2])
	else
		ctx.send(who, "arm", { op = "check", chk = chk })
	end
end

local function begin(T: any, ctx: any)
	local A = T.g
	A.bal = 0
	A.again = {}
	set(T, "Bal", 0)
	set(T, "Winner", nil)
	set(T, "AgainA", nil); set(T, "AgainB", nil)
	state(T, "count", ctx)
end

local function slam(T: any, winner: string, ctx: any)
	local A = T.g
	A.chk = {}
	A.bal = if winner == "A" then 1 else -1
	set(T, "Bal", A.bal)
	set(T, "Winner", winner)
	state(T, "slam", ctx)
end

local function press(T: any, side: string, pos: number, ctx: any)
	local A = T.g
	local chk = A.chk[side]
	if not chk or A.state ~= "bout" then return end
	local MA = ctx.MG.ARM
	local d = math.abs(pos - chk.c)
	local res = if d <= chk.w * MA.PERFECT_K then "perfect" elseif d <= chk.w then "hit" else "miss"
	local push = if res == "perfect" then MA.PERFECT elseif res == "hit" then MA.HIT else -MA.MISS
	-- (your next zone: smaller after a hit, more so after a perfect; a miss gives some back)
	local w0 = A.w[side] or MA.W0
	A.w[side] = math.clamp(w0 * (if res == "perfect" then MA.PERFECT_SHRINK elseif res == "hit" then MA.HIT_SHRINK else MA.MISS_GROW), MA.W1, MA.W0)
	A.bal = math.clamp(A.bal + (if side == "A" then push else -push), -1, 1)
	A.hits += 1
	set(T, "Bal", A.bal)
	set(T, "Hit", side .. ":" .. res .. ":" .. A.hits)
	local who = T.who[side]
	if not ctx.isBot(who) then ctx.send(who, "arm", { op = "result", id = chk.id, res = res }) end
	A.chk[side] = nil
	if A.bal >= 1 then slam(T, "A", ctx); return end
	if A.bal <= -1 then slam(T, "B", ctx); return end
	newCheck(T, side, ctx)
end

local function bothHere(T: any): boolean return T.who.A ~= nil and T.who.B ~= nil end
local function humans(T: any, ctx: any): number
	local n = 0
	for _, s in { "A", "B" } do if T.who[s] ~= nil and not ctx.isBot(T.who[s]) then n += 1 end end
	return n
end

function Arm.joined(T: any, side: string, p: Player, ctx: any)
	local A = T.g
	-- the IK: your right hand on the clasp, your left on your peg (each client moves the clasp: MiniArm.client)
	task.spawn(Arm.rig, T, side, p.Character, ctx)
	if bothHere(T) and (A.state == "open" or A.state == "done") then begin(T, ctx) end
end

function Arm.left(T: any, side: string, who: any, ctx: any)
	local A = T.g
	local o = other(side)
	if A.state == "bout" or A.state == "count" then
		if T.who[o] ~= nil then slam(T, o, ctx) else state(T, "open", ctx) end
	end
	A.again[side] = nil
	set(T, "Again" .. side, nil)
	-- a bot never sits alone
	if ctx.isBot(T.who[o]) and humans(T, ctx) == 0 then ctx.botSeat(T, o, nil) end
	if not bothHere(T) and A.state ~= "slam" then
		A.bal = 0
		set(T, "Bal", 0)
		if A.state ~= "open" then state(T, "open", ctx) end
	end
end

function Arm.msg(T: any, p: Player, side: string, d: any, ctx: any)
	local A = T.g
	local o = other(side)
	if d.op == "bot" then
		if T.who[o] ~= nil and not ctx.isBot(T.who[o]) then return end
		if A.state ~= "open" and A.state ~= "done" then return end
		local level = if ctx.MG.ARM.BOT[d.level] then d.level else "medium"
		ctx.botSeat(T, o, level)
		task.delay(0.6, function()
			if T.who[side] == p and ctx.isBot(T.who[o]) and (A.state == "open" or A.state == "done") then
				Arm.rig(T, o, T.bots[o], ctx)
				begin(T, ctx)
			end
		end)
	elseif d.op == "hit" then
		local chk = A.chk[side]
		if not chk or d.id ~= chk.id or type(d.pos) ~= "number" or d.pos ~= d.pos then return end
		local now = ctx.now()
		if now < chk.t0 - 0.05 then return end
		-- where the needle was over the last 0.45 s (the press's trip here): the claim must fall in that sweep
		local lo, hi = math.huge, -math.huge
		for i = 0, 9 do
			local x = ctx.MG.needle(chk, now - 0.45 * i / 9)
			lo = math.min(lo, x); hi = math.max(hi, x)
		end
		local pos = math.clamp(d.pos, 0, 1)
		if pos < lo - 0.03 or pos > hi + 0.03 then
			pos = ctx.MG.needle(chk, now - math.min(0.4, p:GetNetworkPing()))
		end
		press(T, side, pos, ctx)
	elseif d.op == "again" then
		if A.state ~= "done" then return end
		if ctx.isBot(T.who[o]) then begin(T, ctx); return end
		A.again[side] = true
		set(T, "Again" .. side, true)
		if A.again.A and A.again.B and bothHere(T) then begin(T, ctx) end
	end
end

-- the arms: IKControls on the sitter's humanoid, aimed at the table's attachments
function Arm.rig(T: any, side: string, ch: Model?, ctx: any)
	if not ch then return end
	local hum = ch:FindFirstChildOfClass("Humanoid") or ch:WaitForChild("Humanoid", 5)
	if not hum or not hum:IsA("Humanoid") then return end
	local root = T.model.PrimaryPart
	local function ik(name: string, chainRoot: string, effector: string, target: string, pole: string)
		local old = hum:FindFirstChild(name)
		if old then old:Destroy() end
		local cr = ch:FindFirstChild(chainRoot) :: BasePart?
		local ef = ch:FindFirstChild(effector, true)
		if not cr or not ef then return end
		local c = Instance.new("IKControl")
		c.Name = name
		c.Type = Enum.IKControlType.Position
		c.ChainRoot = cr
		c.EndEffector = ef :: any
		c.Target = root:FindFirstChild(target) :: Attachment
		c.Pole = root:FindFirstChild(pole) :: Attachment
		c.Weight = 1
		c.SmoothTime = 0.04
		c.Priority = 10
		c.Parent = hum
	end
	local r15 = hum.RigType == Enum.HumanoidRigType.R15
	if r15 then
		ik("MiniArmR", "RightUpperArm", "RightGripAttachment", "Hand" .. side, "Pole" .. side)
		ik("MiniArmL", "LeftUpperArm", "LeftGripAttachment", "Peg" .. side, "PolePeg" .. side)
	else
		ik("MiniArmR", "Right Arm", "RightGripAttachment", "Hand" .. side, "Pole" .. side)
		ik("MiniArmL", "Left Arm", "LeftGripAttachment", "Peg" .. side, "PolePeg" .. side)
	end
end

function Arm.step(T: any, dt: number, ctx: any)
	local A = T.g
	local MA = ctx.MG.ARM
	local now = ctx.now()
	if A.state == "count" then
		if not bothHere(T) then state(T, "open", ctx); return end
		if now - A.at >= MA.COUNT then
			state(T, "bout", ctx)
			A.boutT0 = now
			A.w = {}
			A.chk = {}
			for _, s in { "A", "B" } do newCheck(T, s, ctx) end
		end
	elseif A.state == "bout" then
		for _, s in { "A", "B" } do
			local chk = A.chk[s]
			local who = T.who[s]
			if not chk or who == nil then continue end
			if ctx.isBot(who) then
				if A.botAt and now >= A.botAt then
					local B = MA.BOT[who.level] or MA.BOT.medium
					local k = math.clamp((now - A.boutT0) / MA.SHRINK, 0, 1)
					local pos
					if rng:NextNumber() < B.hit - B.fall * k then
						local perfect = rng:NextNumber() < B.perfect
						local off = rng:NextNumber(-1, 1) * chk.w * (if perfect then MA.PERFECT_K * 0.9 else 0.95)
						pos = chk.c + off
					else
						local off = chk.w * rng:NextNumber(1.15, 2.6)
						pos = math.clamp(chk.c + (if rng:NextNumber() < 0.5 then off else -off), 0, 1)
					end
					A.botAt = nil
					press(T, s, pos, ctx)
					if A.state ~= "bout" then return end
				end
			elseif now > chk.t0 + chk.T * MA.TIMEOUT then
				press(T, s, -1, ctx) -- (no press at all: a miss)
				if A.state ~= "bout" then return end
			end
		end
	elseif A.state == "slam" then
		if now - A.at >= MA.SLAM_HOLD then
			A.bal = 0
			set(T, "Bal", 0)
			state(T, if bothHere(T) then "done" else "open", ctx)
		end
	end
end

return Arm
