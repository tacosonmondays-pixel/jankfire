--!strict
-- HOUSE HUNT's Studio test bots (27 Nov 2026; main: "a server-side harness that gets as close to a real round as
-- stand-ins allow"). Each of a round's stand-ins is wrapped as a bot ({ f, Character }) that acts through the very calls
-- a player's remote reaches: HuntMoves.handle (push, super push, punch, the bat), HuntItems.pick / handle (the tables,
-- the traps and items), HuntRagdoll.ask (GET UP). The hunter stand-in walks a route and fires at survivors (Fight.hurt,
-- as a landed shot would). Scenarios ("show", "kill", "hunter", "time") run on a thread and write a log of checks:
--   JankHuntTest("bots", p, scenario) starts one in the current round; JankHuntTest("botlog") reads the log.
-- What this can't prove: a real client's input, camera and replication with other players (the owner's 3-client test).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local HuntRound = require(script.Parent:WaitForChild("HuntRound")) :: any
local HuntMoves = require(script.Parent:WaitForChild("HuntMoves")) :: any
local HuntItems = require(script.Parent:WaitForChild("HuntItems")) :: any
local HuntRagdoll = require(script.Parent:WaitForChild("HuntRagdoll")) :: any

local HuntBots = {}
local log: { string } = {}
local t0 = os.clock()
local function say(s: string) table.insert(log, ("%5.1f  %s"):format(os.clock() - t0, s)) end
local function check(ok: boolean, what: string) say((if ok then "PASS  " else "FAIL  ") .. what) end
function HuntBots.log(): string return table.concat(log, "\n") end

local Bot = {}
Bot.__index = Bot
function Bot:GetAttribute(k: string): any return self.Character:GetAttribute(k) end
function Bot:SetAttribute(k: string, v: any) self.Character:SetAttribute(k, v) end

local bots: { [string]: any } = {}
local function wrapAll(): { [string]: any }
	bots = {}
	local g = HuntRound.G
	if not g then return bots end
	for _, m in g.members do
		if not m.p and m.standin then
			local b = setmetatable({ f = m.f, Character = m.standin, Name = m.f.name, role = m.role, isBot = true }, Bot)
			b:SetAttribute("Hunt", "round"); b:SetAttribute("HuntRole", m.role)
			if m.role == "hider" then HuntItems.addBot(b) end
			bots[m.f.name] = b
		end
	end
	return bots
end
local function root(x: any): BasePart?
	if typeof(x) == "Instance" and x:IsA("Player") then
		return x.Character and x.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
	end
	return x and x.Character and x.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
end
local function fOf(x: any): any return if typeof(x) == "Instance" then Fight.byPlayer[x] else x.f end
local function faceTo(b: any, target: any): Vector3
	local r, tr = root(b), root(target)
	if not r or not tr then return Vector3.new(0, 0, -1) end
	local d = tr.Position - r.Position
	d = Vector3.new(d.X, 0, d.Z)
	if d.Magnitude < 0.1 then return r.CFrame.LookVector end
	if typeof(b) ~= "Instance" then r.CFrame = CFrame.lookAt(r.Position, r.Position + d.Unit) end
	return d.Unit
end
-- stand a bot `dist` studs in front of a target, facing it (a move's reach is 7)
local function closeIn(b: any, target: any, dist: number)
	local r, tr = root(b), root(target)
	if not r or not tr or typeof(b) == "Instance" then return end
	local d = r.Position - tr.Position
	d = Vector3.new(d.X, 0, d.Z)
	d = if d.Magnitude > 0.1 then d.Unit else Vector3.new(1, 0, 0)
	local at = tr.Position + d * dist
	r.CFrame = CFrame.lookAt(at, Vector3.new(tr.Position.X, at.Y, tr.Position.Z))
end
local function aimAt(b: any, target: any): Vector3
	local r, tr = root(b), root(target)
	if not r or not tr then return Vector3.new(0, 0, -1) end
	faceTo(b, target)
	return (tr.Position - (r.Position + Vector3.new(0, 1.6, 0))).Unit
end
local function act(b: any, op: string, target: any)
	local look = faceTo(b, target)
	if op == "super" then HuntMoves.handle(b, "hold", look); task.wait(0.9) end
	if op == "jab" then HuntMoves.handle(b, "wind", look) end
	HuntMoves.handle(b, op, look)
end
local function isDown(x: any): boolean return HuntRagdoll.isDown(fOf(x)) end
local function hp(x: any): number local f = fOf(x); return if f then f.hp else -1 end
local function phase(): string local g = HuntRound.G; return if g then tostring(g.phase) else "none" end
local function waitPhase(ph: string, limit: number): boolean
	local t = os.clock()
	while phase() ~= ph and os.clock() - t < limit do task.wait(0.1) end
	return phase() == ph
end
local function hunterBot(): any for _, b in bots do if b.role == "gunman" then return b end end return nil end
local function survivors(): { any }
	local out = {}
	for _, b in bots do if b.role == "hider" then table.insert(out, b) end end
	table.sort(out, function(a, c) return a.Name < c.Name end)
	return out
end
-- the hunter: walks toward the nearest living survivor and "fires" (a landed shot's damage) every `every` s
local function hunterRun(me: Player?, dmg: number, every: number, untilT: number, also: { any })
	local h = hunterBot()
	if not h then say("no hunter bot"); return end
	local hum = h.Character:FindFirstChildOfClass("Humanoid")
	local nextShot = 0
	while os.clock() < untilT and phase() == "hunt" and h.f.alive do
		local best, bd = nil, math.huge
		for _, x in also do
			local f = fOf(x)
			local r = root(x)
			if f and f.alive and r and root(h) then
				local d = (r.Position - (root(h) :: BasePart).Position).Magnitude
				if d < bd then best, bd = x, d end
			end
		end
		if not best then say("the hunter: nobody left in reach"); break end
		if hum and not isDown(h) then hum:MoveTo((root(best) :: BasePart).Position) end
		local stun = tonumber(h.Character:GetAttribute("StunUntil")) or 0
		if os.clock() >= nextShot and workspace:GetServerTimeNow() >= stun then
			nextShot = os.clock() + every
			local done = Fight.hurt(fOf(best), dmg, h.f, tostring(HuntRound.G and HuntRound.G.gun or "ar"), false, nil)
			say(("the hunter shoots %s at %.0f studs: %s"):format(if typeof(best) == "Instance" then best.Name else best.Name, bd, tostring(done)))
		end
		task.wait(0.15)
	end
end

local scenarios: { [string]: (Player) -> () } = {}
-- the knockdowns, GET UP, the lockout and the immunity, and a bot downing the real player (the MP4)
scenarios.show = function(me: Player)
	local S = survivors()
	if #S < 3 then say("need 3 survivor bots"); return end
	local A, B, C = S[1], S[2], S[3]
	-- a bot shoves the real player: their own client goes limp, GET UP on Space
	closeIn(A, me, 4)
	task.wait(0.3)
	act(A, "push", me)
	task.wait(0.3)
	check(isDown(me), "a bot's push downs the real player")
	local mins = tonumber(me:GetAttribute("HuntRagMin"))
	check(mins ~= nil, "the player's HuntRagMin is set (GET UP key)")
	local w = os.clock()
	while isDown(me) and os.clock() - w < 3 do task.wait(0.1) end
	say(("the player was up after %.1f s (Space or the 1 s auto)"):format(os.clock() - w + 0.3))
	-- the player shoves a bot (the remote's server call), then a punch from another bot, then the lockout
	task.wait(1.0)
	closeIn(B, me, 4)
	HuntMoves.handle(me, "push", faceTo(me, B))
	task.wait(0.25)
	check(isDown(B), "the player's push downs a bot (1 s)")
	HuntRagdoll.ask(B) -- (at about 0.25 s: too soon)
	check(isDown(B), "GET UP refused before 0.5 s")
	task.wait(0.5)
	HuntRagdoll.ask(B)
	check(not isDown(B), "GET UP works after 0.5 s")
	closeIn(C, B, 4)
	act(C, "jab", B)
	task.wait(0.2)
	check(not isDown(B), "just up: immune for 2 s (a punch does nothing)")
	task.wait(2.1)
	act(C, "jab", B)
	task.wait(0.2)
	check(isDown(B), "a punch downs (3 s)")
	task.wait(1.0)
	HuntRagdoll.ask(B)
	check(isDown(B), "a punch's stun: GET UP refused at 1 s")
	closeIn(A, C, 4)
	act(C, "push", A)
	task.wait(0.2)
	check(not isDown(A), "the 1 s lockout: a push inside a second of the punch does nothing")
	task.wait(1.8)
	HuntRagdoll.ask(B)
	check(not isDown(B), "GET UP works after the 2.5 s stun")
	task.wait(0.5)
	closeIn(A, C, 4)
	act(A, "super", C)
	task.wait(0.25)
	check(isDown(C), "a super push downs (2 s)")
end
-- the survivors kill the hunter: picks, taser, bear trap, the bat, a shove on him
scenarios.kill = function(me: Player)
	local S = survivors()
	local H = hunterBot()
	if #S < 3 or not H then say("need 3 survivors and a hunter"); return end
	local A, B, C = S[1], S[2], S[3]
	check(HuntItems.pick(A, "bat") == "ok", A.Name .. " takes the BASEBALL BAT")
	check(HuntItems.pick(B, "taser") == "ok" and B:GetAttribute("HuntPoints") == 0, B.Name .. " buys the TASER ($40 -> $0)")
	check(HuntItems.pick(C, "beartrap") == "ok", C.Name .. " takes the BEAR TRAP")
	check(HuntItems.pick(A, "spray") == "taken", "a second pick is refused")
	check(HuntItems.pick(me, "medkit") == "ok", "the player buys the MEDKIT")
	if not waitPhase("hunt", 40) then say("no hunt phase"); return end
	say("the hunt: the hunter is let out")
	local hr = root(H)
	-- the bear trap on his way, the taser when he's close, the bat and a punch
	if hr then closeIn(C, H, 9) end
	task.wait(0.2)
	HuntItems.handle(C, "use", 1, faceTo(C, H))
	check(C:GetAttribute("HuntItems") == "", C.Name .. " set the bear trap")
	local hpBefore = hp(H)
	task.wait(1.2) -- (a set trap arms after 1 s)
	-- the hunter walks into it
	local hh = H.Character:FindFirstChildOfClass("Humanoid")
	if hh and root(C) then hh:MoveTo((root(C) :: BasePart).Position) end
	local w = os.clock()
	while hp(H) >= hpBefore and os.clock() - w < 6 do task.wait(0.1) end
	check(hp(H) < hpBefore, ("the bear trap springs on the hunter (hp %d -> %d)"):format(hpBefore, hp(H)))
	task.wait(3.2) -- (the trap's hold ends)
	closeIn(C, H, 16); closeIn(A, H, 18) -- (out of the taser's line)
	closeIn(B, H, 8)
	HuntItems.handle(B, "use", 1, aimAt(B, H))
	task.wait(0.2)
	check((tonumber(H.Character:GetAttribute("StunUntil")) or 0) > workspace:GetServerTimeNow(), "the taser stuns the hunter")
	task.wait(2.2)
	closeIn(B, H, 16); closeIn(C, H, 18)
	closeIn(A, H, 4)
	say("the bat reaches: " .. table.concat(HuntMoves.debugTargets(A, faceTo(A, H), 7.5, 50), ", "))
	local hits = 0
	local start = hp(H)
	while H.f.alive and hits < 12 do
		if isDown(H) then task.wait(0.3) end
		closeIn(A, H, 4)
		act(A, "jab", H)
		hits += 1
		task.wait(1.0)
	end
	say(("the bat: %d swings, hunter hp %d -> %d"):format(hits, start, hp(H)))
	check(not H.f.alive, "the survivors kill the hunter")
	check(waitPhase("outro", 3) or waitPhase("end", 3), "the round ends (" .. phase() .. ")")
end
-- the hunter wins: spray, bandages, the prop gun on furniture, then he shoots everyone
scenarios.hunter = function(me: Player)
	local S = survivors()
	local H = hunterBot()
	if #S < 3 or not H then say("need 3 survivors and a hunter"); return end
	local A, B, C = S[1], S[2], S[3]
	check(HuntItems.pick(A, "bandage") == "ok", A.Name .. " takes BANDAGES")
	check(HuntItems.pick(B, "spray") == "ok", B.Name .. " takes PEPPER SPRAY")
	check(HuntItems.pick(C, "propgun") == "ok", C.Name .. " buys the PROP GUN")
	-- the prop gun: the nearest real piece of furniture in front of it
	local g = HuntRound.G
	local cr = root(C)
	local best, bd = nil, math.huge
	if g and cr then
		for _, d in g.map:GetDescendants() do
			local mdl = d:FindFirstAncestorOfClass("Model")
			local isBody = mdl ~= nil and mdl:FindFirstChildOfClass("Humanoid") ~= nil
			if d:IsA("BasePart") and d.CanQuery and (d.Transparency < 0.5 or d:FindFirstAncestor("Solid") ~= nil) and not isBody and not d:FindFirstAncestor("HuntPicks") then -- (THE HOUSE: the hit boxes)
				local sz = d.Size
				local big = math.max(sz.X, sz.Y, sz.Z)
				if big <= 12 and big >= 1.5 and sz.Y >= 1.2 then
					local dd = (d.Position - cr.Position).Magnitude
					if dd < bd and dd < 28 then best, bd = d, dd end
				end
			end
		end
	end
	if best and cr then
		cr.CFrame = CFrame.lookAt(cr.Position, Vector3.new(best.Position.X, cr.Position.Y, best.Position.Z))
		local eye = cr.Position + Vector3.new(0, 1.6, 0)
		HuntItems.handle(C, "use", 1, (best.Position - eye).Unit)
		local dm = C.Character:FindFirstChild("HuntDisguise")
		check(C:GetAttribute("HuntProp") == true, ("the prop gun: %s aims at a %.0fx%.0fx%.0f piece and becomes %s"):format(C.Name, best.Size.X, best.Size.Y, best.Size.Z, dm and (if dm:IsA("Model") then "a kit piece" else "a copy") or "nothing"))
	else
		say("no furniture in reach for the prop gun")
	end
	if not waitPhase("hunt", 40) then say("no hunt phase"); return end
	local ch = C.Character:FindFirstChildOfClass("Humanoid")
	if ch and cr then ch:MoveTo(cr.Position + cr.CFrame.LookVector * 20) end
	task.wait(1.2)
	check(C:GetAttribute("HuntProp") == nil, "the disguise breaks when it runs")
	closeIn(B, H, 8)
	local p0 = tonumber(B:GetAttribute("HuntPoints")) or 0
	HuntItems.handle(B, "use", 1, aimAt(B, H))
	task.wait(0.2)
	check((tonumber(B:GetAttribute("HuntPoints")) or 0) > p0, "the pepper spray catches the hunter (cash for it)")
	Fight.hurt(A.f, 40, H.f, "ar", false, nil)
	local h0 = hp(A)
	HuntItems.handle(A, "use", 1, faceTo(A, H))
	task.wait(0.2)
	check(hp(A) > h0, ("BANDAGES heal (%d -> %d)"):format(h0, hp(A)))
	local targets: { any } = { me }
	for _, b in S do table.insert(targets, b) end
	hunterRun(me, 50, 0.6, os.clock() + 30, targets)
	check(waitPhase("outro", 4) or waitPhase("end", 4), "the hunter wins (" .. phase() .. ")")
end
-- the survivors win on time; the medkit heals over its 2.5 s
scenarios.time = function(me: Player)
	local S = survivors()
	local H = hunterBot()
	if #S < 1 or not H then say("need bots"); return end
	local A = S[1]
	check(HuntItems.pick(A, "medkit") == "ok", A.Name .. " buys the MEDKIT")
	if not waitPhase("hunt", 40) then say("no hunt phase"); return end
	Fight.hurt(A.f, 60, H.f, "ar", false, nil)
	local h0 = hp(A)
	HuntItems.handle(A, "use", 1, Vector3.new(0, 0, -1))
	task.wait(3.0)
	check(hp(A) >= 99, ("the MEDKIT heals to full over 2.5 s (%d -> %d)"):format(h0, hp(A)))
	local w = os.clock()
	while phase() == "hunt" and os.clock() - w < 60 do task.wait(0.2) end
	check(phase() == "outro" or phase() == "end", "the survivors win on time (" .. phase() .. ")")
end

function HuntBots.run(me: Player, name: string): string
	local fn = scenarios[name]
	if not fn then return "no scenario " .. tostring(name) end
	log = {}
	t0 = os.clock()
	wrapAll()
	say(("scenario %s: %d bots, phase %s"):format(name, (function() local n = 0; for _ in bots do n += 1 end; return n end)(), phase()))
	task.spawn(function()
		local ok, err = pcall(fn, me)
		if not ok then say("ERROR " .. tostring(err)) end
		say("done")
	end)
	return "started"
end
_ = Players

return HuntBots
