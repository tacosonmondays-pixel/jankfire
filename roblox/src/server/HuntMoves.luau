--!strict
-- HOLDOUT's moves, the server's side (26 Nov 2026; roblox/docs/HUNT.md section 4). The owner: "They can run around
-- interact with stuff, punch push super push. Push is funny, if you lay down look up and push you'll send people
-- flying." The client (HuntMoves.client) asks; this judges and throws:
--   "jab"                 a quick punch
--   "wind" / "hay"        the wind-up starts / the haymaker lands (only if the wind-up was held long enough)
--   "hold" / "push" / "super"   the push button goes down / a shove / a super shove (held long enough)
--   "lie", on             lying on your back or not (a push from there goes along your whole look, up included)
-- Reach and cone from the server's own copy of the bodies (a miss is a whiff); everyone in the house (or the same
-- round) can be shoved; damage lands only where Fight.allow says so (the round, stage 2: only on the gunman). The
-- driveway's basketball takes shoves too. Knocks go through Fight.knock, which the anti-cheat already knows.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local HuntRagdoll = require(script.Parent:WaitForChild("HuntRagdoll")) :: any
local MV = HC.MOVES
-- (a Studio test bot, HuntBots: a table { f, Character } that acts through the same calls a player's remote does)
local function fOf(p: any): any return if type(p) == "table" then p.f else Fight.byPlayer[p] end

local HuntMoves = {}
-- (stage 2 sets these: may `a` shove `b` at all; may a punch from `a` hurt `b`)
HuntMoves.canShove = function(a: Player, b: Player): boolean
	return a:GetAttribute("Hunt") ~= nil and b:GetAttribute("Hunt") ~= nil
end
-- how far a shove moves this player (the gunman's FIRM STANCE: 0.5), and fighters with no player a move can reach
-- (the round's stand-in bodies in a Studio test): HuntRound / Hunt set these
HuntMoves.knockScale = function(_p: Player): number return 1 end
HuntMoves.extra = function(_p: Player): { any } return {} end
-- the weapon in your hand (a FIGHT BACK find: HuntItems), and what happens when a hit lands on a fighter (points)
HuntMoves.weaponOf = function(_p: Player): any return nil end
HuntMoves.landed = function(_p: Player, _f: any, _kind: string) end
-- (HuntItems: a prop gun's disguise breaks when its wearer attacks, or is downed)
HuntMoves.onAct = function(_p: Player) end
HuntMoves.onDowned = function(_f: any) end

type St = { cd: { [string]: number }, windT: number?, holdT: number?, lie: boolean, lock: number? }
local st: { [Player]: St } = {}
local function stOf(p: Player): St
	local s = st[p]
	if not s then s = { cd = {}, lie = false }; st[p] = s end
	return s
end

local Sounds = ReplicatedStorage:FindFirstChild("JankfireSounds")
local function sfx(name: string, at: BasePart, vol: number?)
	local s = Sounds and Sounds:FindFirstChild(name)
	if not (s and s:IsA("Sound")) then return end
	local c = s:Clone()
	c.RollOffMode = Enum.RollOffMode.InverseTapered; c.RollOffMinDistance = 8; c.RollOffMaxDistance = 80
	if vol then c.Volume *= vol end
	c.Parent = at
	c:Play()
	task.delay(math.max(1.5, c.TimeLength + 0.3), function() c:Destroy() end)
end

local function body(p: Player): (BasePart?, Humanoid?)
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local r = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not (r and hum) or hum.Health <= 0 then return nil, nil end
	return r, hum
end

-- everything a move from `p` (looking `look`) reaches: players (and the ball) within reach + slack, inside the cone
local function targets(p: Player, root: BasePart, look: Vector3, reach: number, cone: number, lying: boolean): { any }
	local out = {}
	local o = root.Position
	local flat = Vector3.new(look.X, 0, look.Z)
	local dir = if lying then look.Unit elseif flat.Magnitude > 1e-3 then flat.Unit else root.CFrame.LookVector
	local cosC = math.cos(math.rad(cone))
	local function consider(pos: Vector3, what: any)
		local d = pos - o
		if d.Magnitude > reach + MV.slack then return end
		local dd = if lying then d else Vector3.new(d.X, 0, d.Z)
		-- (point blank counts whatever the angle: you're touching them)
		if dd.Magnitude > 2.5 and dd.Unit:Dot(dir) < cosC then return end
		table.insert(out, { what = what, d = d.Magnitude, pos = pos })
	end
	for _, q in Players:GetPlayers() do
		if q == p then continue end
		local r = body(q)
		if r and HuntMoves.canShove(p, q) then consider(r.Position, q) end
	end
	local self = fOf(p)
	for _, f in HuntMoves.extra(p) do
		local r = Fight.root(f)
		if r and f.alive and f ~= self then consider(r.Position, f) end
	end
	local map = workspace:FindFirstChild("Map")
	local h = map and map:FindFirstChild(HC.HOUSE)
	local hf = h and h:FindFirstChild("Hunt")
	local pf = hf and hf:FindFirstChild("Props")
	local ball = pf and pf:FindFirstChild("Ball")
	if ball and ball:IsA("BasePart") then consider(ball.Position, ball) end
	table.sort(out, function(a, b) return a.d < b.d end)
	return out
end

-- the knock a move gives: along your look on the flat (all of it while lying: the launch), plus some up
local function knockOf(look: Vector3, kb: number, up: number, lying: boolean): Vector3
	if lying then
		local v = look.Unit * kb * MV.lie.launch
		return Vector3.new(v.X, math.max(v.Y, 0) + up * 0.5, v.Z)
	end
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.zero
	return flat * kb + Vector3.new(0, up, 0)
end

local function hit(p: Player, root: BasePart, look: Vector3, m: any, wid: string, dmg: number, onlyFirst: boolean, lying: boolean): (number, number)
	local list = targets(p, root, look, m.reach, m.cone, lying)
	local n, downs = 0, 0
	local by = fOf(p)
	for _, t in list do
		local v = knockOf(look, m.kb, m.up, lying)
		if typeof(t.what) == "Instance" and t.what:IsA("BasePart") then
			local ball = t.what :: BasePart
			ball.AssemblyLinearVelocity += v * MV.ball
			n += 1
		else
			local q: Player? = if typeof(t.what) == "Instance" and t.what:IsA("Player") then t.what else nil
			local f = if q then Fight.byPlayer[q] else t.what
			if not f or not f.alive then continue end
			if q then v *= HuntMoves.knockScale(q) end
			-- (damage where it's allowed: Fight.hurt asks Fight.allow, and the house says no to everyone; then it's just
			-- the shove)
			local rag = if wid == "push" then MV.push elseif wid == "superpush" then MV.super elseif wid == "punch" then MV.punch else nil
			if rag then
				-- (FIRM STANCE: the hunter is down half as long)
				local sc = if q then HuntMoves.knockScale(q) else 1
				if dmg > 0 and by and Fight.allow(by, f) then Fight.hurt(f, dmg, by, wid, false, nil) end
				if f.alive then
					if HuntRagdoll.down(f, v, rag.rag * sc, rag.min * sc) then
						downs += 1
						HuntMoves.onDowned(f)
					else
						Fight.knock(f, v * 0.3, wid) -- (just up, or already down: a nudge, never a chain)
					end
				end
				if by and Fight.allow(by, f) then HuntMoves.landed(p, f, wid) end
			elseif dmg > 0 and by and Fight.allow(by, f) then
				Fight.hurt(f, dmg, by, wid, false, v)
				HuntMoves.landed(p, f, wid)
			else
				Fight.knock(f, v, wid)
				if by and Fight.allow(by, f) then HuntMoves.landed(p, f, wid) end
			end
			local r = if q then body(q) else Fight.root(f)
			if r then sfx(if wid == "push" or wid == "superpush" then "hunt_shove" else "hunt_punch_hit", r, if wid == "superpush" then 1.4 else 1) end
			n += 1
		end
		if onlyFirst then break end
	end
	return n, downs
end
-- (Studio, HuntBots: what a move from p would reach, nearest first)
function HuntMoves.debugTargets(p: any, look: Vector3, reach: number, cone: number): { string }
	local r = body(p)
	if not r then return { "no body" } end
	local out = {}
	for _, t in targets(p, r, look, reach, cone, false) do
		table.insert(out, ("%s@%.1f"):format(if type(t.what) == "table" then tostring(t.what.name) else t.what.Name, t.d))
	end
	return out
end

local function ready(s: St, key: string, cd: number): boolean
	local t = s.cd[key]
	if t and os.clock() < t then return false end
	s.cd[key] = os.clock() + cd * 0.9 -- (a little slack for lag: the client keeps the real cooldown)
	return true
end

function HuntMoves.handle(p: Player, op: string, a: any, b: any)
	if p:GetAttribute("Hunt") == nil then return end
	if op == "getup" then HuntRagdoll.ask(p); return end -- (the get-up button: the hunter too)
	if p:GetAttribute("HuntRole") == "gunman" then return end -- (stage 2: the gunman has his gun, not these)
	if HuntRagdoll.isDown(fOf(p)) then return end -- (down: no moves)
	local root, hum = body(p)
	if not root or not hum then return end
	local s = stOf(p)
	local attack = op == "jab" or op == "hay" or op == "push" or op == "super"
	if attack then
		if os.clock() < (s.lock or 0) then return end -- (one move, then a breath: no chaining all three)
		HuntMoves.onAct(p)
	end
	local look = if typeof(a) == "Vector3" and a.Magnitude > 0.1 and a.Magnitude < 2 then a.Unit else root.CFrame.LookVector
	if op == "lie" then
		s.lie = a == true
		p:SetAttribute("HuntLie", if s.lie then true else nil)
		return
	end
	if op == "wind" then s.windT = os.clock(); return end
	if op == "hold" then s.holdT = os.clock(); return end
	local wpn = HuntMoves.weaponOf(p) -- (a FIGHT BACK weapon swings instead of the fist)
	local function landedCd(key: string, cd: number) -- (a punch that lands costs its full cooldown: the client reads it)
		s.cd[key] = os.clock() + cd * 0.9
		p:SetAttribute("HuntCd_" .. key, workspace:GetServerTimeNow() + cd)
	end
	if op == "jab" then
		local m = wpn or MV.jab
		if not ready(s, "punch", if wpn then m.cd else MV.punch.whiff) then return end
		s.lock = os.clock() + MV.lock * 0.9
		local _, downs = hit(p, root, look, m, if wpn then "melee" else "punch", m.dmg, true, false)
		if downs > 0 and not wpn then landedCd("punch", MV.punch.cd) end -- (a punch that downs nobody, an immune one too, costs only the miss)
	elseif op == "hay" then
		local held = if s.windT then os.clock() - s.windT else 0
		s.windT = nil
		if held < MV.hay.wind * 0.75 then return end -- (not wound up: the client sends a jab for a tap)
		local m = wpn or MV.hay
		if not ready(s, "punch", if wpn then m.cd else MV.punch.whiff) then return end
		s.lock = os.clock() + MV.lock * 0.9
		local _, downs = hit(p, root, look, m, if wpn then "melee" else "punch", if wpn then math.floor(m.dmg * 1.3) else m.dmg, true, false)
		if downs > 0 and not wpn then landedCd("punch", MV.punch.cd) end
	elseif op == "push" then
		s.holdT = nil
		if not ready(s, "push", MV.push.cd) then return end
		s.lock = os.clock() + MV.lock * 0.9
		hit(p, root, look, MV.push, "push", 0, false, s.lie)
	elseif op == "super" then
		local held = if s.holdT then os.clock() - s.holdT else 0
		s.holdT = nil
		if held < MV.super.hold * 0.75 then return end
		if not ready(s, "super", MV.super.cd) then return end
		s.lock = os.clock() + MV.lock * 0.9
		s.cd.push = os.clock() + MV.push.cd * 0.9
		hit(p, root, look, MV.super, "superpush", 0, false, s.lie)
	end
end

Players.PlayerRemoving:Connect(function(p) st[p] = nil end)

return HuntMoves
