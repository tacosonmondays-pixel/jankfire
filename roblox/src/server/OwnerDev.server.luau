--!strict
-- THE OWNER'S DEV MENU, the server half (18 Nov 2026, the owner: "can you give me a special title for being owner, I get
-- a command menu where I can fly, noclip, fling people like a troll thingy for being dev, essentially I can give myself
-- weapons in hub like remote freeze and rewind people"). client/OwnerDev.client draws the menu (F8, "/dev", or the
-- small DEV button); every command comes here through the OwnerDev remote and is checked here, one at a time:
--   who:   the place's creator only (game.CreatorId of a user-owned place). anyone else gets "owner only", once logged
--   where: everywhere, matches too (the owner, 18 Nov: "I can use it in matches, I'm the owner"). the safeguard: the
--          moment a dev power touches a match (the owner uses one in it, has one on in it, or does something to someone
--          in it) that match is flagged dev (m.dev): it plays on, but nobody's stats, rank, quests or loot change from
--          it (Stats, Quests, RankedData skip it), and its players carry MatchDev for the end card's small DEV tag
-- the powers on the owner are server attributes (a client can't write its own Player's attributes for the server):
--   DevFly = fly speed (studs/s), DevNoclip, DevSpeed = run speed x (nil = 1), DevArms (weapons out in the hub: any
--   roster weapon through the loadout's try layer, Zones.training; the hub's weapon checks let DevArms through)
--   DevOn: any of them on, and 3 s after the last goes off (a fly switched off mid-air comes down first). the
--   anti-cheat leaves the owner's movement alone while it's up and marks the owner's aim flags [dev]
-- what it can do to others (any player; in Studio also a training dummy, the stand-in for tests):
--   fling (a hard shove up and away; the one you look at: X), freeze / unfreeze (held still where they are; Z), go to,
--   bring. a frozen player is let go when they die or leave, and all of them when the owner leaves
-- nothing touches a save. hits and kills from the owner's dev weapons outside a match count for nothing
-- (Fight.devKill: no feed, no kill hooks, no score; the victim is back at once). Stats and quests only count live
-- matches anyway. victims of a fling, a bring or a freeze get the anti-cheat's usual pass for a server move
-- (ACGrace / TeleportT, docs/ANTI-CHEAT.md contracts), the same as a TV Remote rewind
-- every command is printed to the server log: "[dev] <owner> <what> <target>"
-- Studio tests: attribute TestNotOwner = true on this script makes the owner a stranger (every command refused);
-- ServerStorage.JankDev (Studio only): "state" (the owner's switches, who's frozen, the log), "as" (player, op, a, b:
-- a command as that player), "log"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Rules = require(script.Parent:WaitForChild("Rules")) :: any
local Zones = require(script.Parent:WaitForChild("Zones")) :: any
local Matches = require(script.Parent:WaitForChild("Matches")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local STUDIO = RunService:IsStudio()
local now = os.clock

-- ------------------------------------------------------------------ the numbers
local FLY = { min = 20, max = 300, default = 80 } -- studs/s
local RUN = { min = 1, max = 4 } -- x the usual run speed
local FLING = { side = 170, up = 130 } -- studs/s, away from the owner and up
local AIM = { range = 220, cone = 0.1 } -- the one you look at: this far, this much slack (rad) plus a body's width
local DEV_AFTER = 3 -- s the anti-cheat's pass outlasts the last power
local HIT_ZONES = { hub = true, training = true, playground = true } :: { [string]: boolean } -- dev weapons hurt players here

-- ------------------------------------------------------------------ who's the owner
local function isOwner(p: Player): boolean
	if STUDIO and script:GetAttribute("TestNotOwner") == true then return false end
	return game.CreatorType == Enum.CreatorType.User and p.UserId > 0 and p.UserId == game.CreatorId
end

-- ------------------------------------------------------------------ the log
local lines: { string } = {}
local function log(p: Player, what: string, target: string?)
	local line = ("[dev] %s %s%s"):format(p.Name, what, if target then " " .. target else "")
	print(line)
	table.insert(lines, os.date("!%H:%M:%S ") .. line)
	while #lines > 40 do table.remove(lines, 1) end
end

-- ------------------------------------------------------------------ a match a dev power touched: counts for nothing
local flagged: { [Player]: number } = {} -- a player in a flagged match: when they were last seen in it
local function flagMatch(by: Player, p: Player?, why: string)
	if not p then return end
	local m = Matches.raw(p)
	if not m or m.dev then return end
	m.dev = true
	local n = 0
	for _, list in (m.teams or {}) :: any do
		for _, q in list do
			if typeof(q) == "Instance" and q:IsA("Player") then q:SetAttribute("MatchDev", m.id); flagged[q] = os.clock(); n += 1 end
		end
	end
	log(by, ("match %s flagged dev (%s): counts for nothing"):format(tostring(m.id), why), ("(%d players)"):format(n))
end

-- ------------------------------------------------------------------ the owner's switches
type State = { fly: boolean, flySpeed: number, noclip: boolean, speed: number, arms: boolean, offAt: number? }
local states: { [Player]: State } = {}
local function stateOf(p: Player): State
	local s = states[p]
	if not s then
		s = { fly = false, flySpeed = FLY.default, noclip = false, speed = 1, arms = false, offAt = nil }
		states[p] = s
	end
	return s :: State
end
local function anyOn(s: State): boolean return s.fly or s.noclip or s.speed ~= 1 or s.arms end
local function view(s: State): any
	return { fly = s.fly, flySpeed = s.flySpeed, noclip = s.noclip, speed = s.speed, arms = s.arms }
end
local function publish(p: Player, s: State)
	p:SetAttribute("DevFly", if s.fly then s.flySpeed else nil)
	p:SetAttribute("DevFlySpeed", s.flySpeed) -- (the slider's value, fly on or off)
	p:SetAttribute("DevNoclip", if s.noclip then true else nil)
	p:SetAttribute("DevSpeed", if s.speed ~= 1 then s.speed else nil)
	local wasArms = p:GetAttribute("DevArms") == true
	p:SetAttribute("DevArms", if s.arms then true else nil)
	if anyOn(s) then
		s.offAt = nil
		p:SetAttribute("DevOn", true)
	elseif p:GetAttribute("DevOn") == true and not s.offAt then
		s.offAt = now() + DEV_AFTER
	end
	if wasArms ~= s.arms then
		local f = Fight.byPlayer[p]
		if f and f.alive then Fight.showWeapon(f) end -- (the gun in your hand, for everyone: Fight.holstered reads DevArms)
	end
end

-- ------------------------------------------------------------------ who can be touched
local function targetOf(a: unknown): (any, string)
	if typeof(a) ~= "Instance" then return nil, "nobody" end
	local inst = a :: Instance
	if inst:IsA("Player") then
		if inst.Parent ~= Players then return nil, "they've left" end
		return Fight.byPlayer[inst], inst.Name
	end
	if STUDIO and inst:IsA("Model") then -- (a training dummy: Studio's stand-in)
		local f = Fight.byModel[inst]
		if f and f.kind == "dummy" then return f, inst.Name .. " (dummy)" end
	end
	return nil, "nobody"
end
local function zoneOfF(f: any): string
	return if f.kind == "player" then Zones.of(f.ref :: Player) else "dummy"
end

-- ------------------------------------------------------------------ freeze
type Frozen = { anchored: boolean? }
local frozen: { [any]: Frozen } = {}
local function setFrozen(t: any, on: boolean)
	if on then
		if frozen[t] then return end
		if t.kind == "player" then
			local tp = t.ref :: Player
			frozen[t] = {}
			tp:SetAttribute("ACGrace", now() + 1)
			tp:SetAttribute("DevFrozen", true) -- (their own client holds their body: OwnerDev.client, everyone's half)
			Rules.stun(t, 3600, now()) -- (no shots, swings or guard while frozen)
		else
			local r = Fight.root(t)
			frozen[t] = { anchored = if r then r.Anchored else nil }
			if r then r.AssemblyLinearVelocity = Vector3.zero; r.Anchored = true end
		end
	else
		local fz = frozen[t]
		if not fz then return end
		frozen[t] = nil
		if t.kind == "player" then
			local tp = t.ref :: Player
			if tp.Parent then
				tp:SetAttribute("ACGrace", now() + 1.5)
				tp:SetAttribute("DevFrozen", nil)
			end
			t.staggerUntil = math.min(t.staggerUntil, now())
		else
			local r = Fight.root(t)
			if r and not fz.anchored then r.Anchored = false end
		end
	end
end
local function unfreezeAll()
	local list = {}
	for t in frozen do table.insert(list, t) end
	for _, t in list do setFrozen(t, false) end
	return #list
end

-- ------------------------------------------------------------------ moves
local function flatUnit(v: Vector3, fallback: Vector3): Vector3
	local f = Vector3.new(v.X, 0, v.Z)
	return if f.Magnitude > 0.05 then f.Unit else fallback
end
local function place(t: any, cf: CFrame)
	local m = Fight.model(t)
	if not m then return end
	if t.kind == "player" then
		local tp = t.ref :: Player
		tp:SetAttribute("TeleportT", now()) -- (a server move: the anti-cheat starts afresh from here)
		tp:SetAttribute("ACGrace", now() + 1)
	end
	m:PivotTo(cf)
	local r = Fight.root(t)
	if r then r.AssemblyLinearVelocity = Vector3.zero end
end
local Dummies: any = nil
local function fling(p: Player, t: any, tname: string, look: Vector3?)
	local r = Fight.root(t)
	if not r then return { ok = false, why = "no body" } end
	local of = Fight.byPlayer[p]
	local mine = of and Fight.root(of)
	local away = flatUnit(r.Position - (if mine then mine.Position else r.Position), flatUnit(look or Vector3.zAxis, Vector3.zAxis))
	local v = away * FLING.side + Vector3.new(0, FLING.up, 0)
	if frozen[t] then setFrozen(t, false) end
	if t.kind == "player" then
		(t.ref :: Player):SetAttribute("ACGrace", now() + 5) -- (a server throw: the anti-cheat's usual pass for one)
	else
		if Dummies == nil then
			local m = script.Parent:FindFirstChild("Dummies")
			local ok, D = false, nil
			if m and m:IsA("ModuleScript") then ok, D = pcall(require, m) end
			Dummies = if ok and type(D) == "table" then D else false
		end
		if Dummies and type(Dummies.slip) == "function" then pcall(Dummies.slip, t) end -- (so its legs don't eat the shove)
	end
	Fight.knock(t, v, "dev")
	if of then Rules.tagged(t, of, "dev", now()) end -- (a fall after it is the owner's: Fight.devKill, it counts for nothing)
	log(p, "fling", tname)
	return { ok = true, did = "flung " .. tname }
end

-- the one the owner looks at: the eye's ray, the nearest in angle, in sight
local function aimed(p: Player, look: unknown): any
	if typeof(look) ~= "Vector3" then return nil end
	local lk = look :: Vector3
	if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 then return nil end
	lk = lk.Unit
	local of = Fight.byPlayer[p]
	local eye = of and Fight.eye(of)
	if not eye then return nil end
	local best, ba = nil, math.huge
	for _, t in Fight.all do
		if t == of or not t.alive then continue end
		if t.kind ~= "player" and not (STUDIO and t.kind == "dummy") then continue end
		local r = Fight.root(t)
		if not r then continue end
		local to = r.Position - eye
		local d = to.Magnitude
		if d > AIM.range or d < 1e-3 then continue end
		local a = math.acos(math.clamp(to.Unit:Dot(lk), -1, 1))
		if a > AIM.cone + math.atan(3 / d) then continue end
		if Fight.castMap(eye, to.Unit, math.max(d - 2, 0.1)) then continue end
		if a < ba then best, ba = t, a end
	end
	return best
end

-- ------------------------------------------------------------------ the list the menu shows
local function list(p: Player): { any }
	local out = {}
	for _, q in Players:GetPlayers() do
		if q == p then continue end
		local f = Fight.byPlayer[q]
		table.insert(out, { ref = q, name = q.DisplayName, user = q.Name, zone = Zones.of(q), frozen = f ~= nil and frozen[f] ~= nil })
	end
	table.sort(out, function(a, b) return a.name < b.name end)
	if STUDIO then
		for _, f in Fight.all do
			if f.kind == "dummy" and f.ref and f.alive then
				table.insert(out, { ref = f.ref, name = f.name, user = "dummy", zone = "dummy", frozen = frozen[f] ~= nil })
			end
		end
	end
	return out
end

-- ------------------------------------------------------------------ the remote
local budget: { [Player]: { n: number, t: number } } = {}
local function spend(p: Player): boolean
	local b = budget[p] or { n = 20, t = now() }
	budget[p] = b
	b.n = math.min(20, b.n + (now() - b.t) * 8); b.t = now()
	if b.n < 1 then return false end
	b.n -= 1
	return true
end
local refused: { [Player]: boolean } = {}

local function handle(p: Player, op: unknown, a: unknown, b: unknown): any
	if not isOwner(p) then
		if not refused[p] then
			refused[p] = true
			log(p, "refused (not the owner): " .. string.sub(tostring(op), 1, 20), nil)
		end
		return { ok = false, why = "owner only" }
	end
	if not spend(p) then return { ok = false, why = "slow down" } end
	local s = stateOf(p)
	local zone = Zones.of(p)
	if op == "hello" or op == "state" then
		return { ok = true, owner = true, studio = STUDIO, zone = zone, state = view(s), log = lines[#lines] }
	elseif op == "players" then
		return { ok = true, players = list(p), zone = zone }
	end
	if zone == "match" and not (op == "set" and (a == "off" or b == false)) then flagMatch(p, p, tostring(op)) end
	if op == "set" then
		if a == "fly" then s.fly = b == true
		elseif a == "flySpeed" and type(b) == "number" and b == b then s.flySpeed = math.floor(math.clamp(b, FLY.min, FLY.max) + 0.5)
		elseif a == "noclip" then s.noclip = b == true
		elseif a == "speed" and type(b) == "number" and b == b then s.speed = math.floor(math.clamp(b, RUN.min, RUN.max) * 4 + 0.5) / 4
		elseif a == "arms" then s.arms = b == true
		elseif a == "off" then s.fly, s.noclip, s.speed, s.arms = false, false, 1, false
		else return { ok = false, why = "nope" } end
		publish(p, s)
		log(p, ("%s %s"):format(tostring(a), if a == "off" then "" else tostring(if a == "flySpeed" then s.flySpeed elseif a == "speed" then s.speed else b)), nil)
		return { ok = true, state = view(s) }
	elseif op == "unfreezeAll" then
		local n = unfreezeAll()
		log(p, "unfreeze all", tostring(n))
		return { ok = true, did = ("let %d go"):format(n) }
	end
	-- the rest are done to someone: a target, or (the Aim ones) whoever the owner looks at
	local t, tname
	if op == "flingAim" or op == "freezeAim" then
		t = aimed(p, a)
		if not t then return { ok = false, why = "nobody there" } end
		tname = if t.kind == "player" then (t.ref :: Player).Name else t.name .. " (dummy)"
	else
		t, tname = targetOf(a)
		if not t then return { ok = false, why = tname } end
	end
	if t == Fight.byPlayer[p] then return { ok = false, why = "not yourself" } end
	if not t.alive then return { ok = false, why = "they're down" } end
	if t.kind == "player" and zoneOfF(t) == "match" then flagMatch(p, t.ref :: Player, tostring(op) .. " on them") end
	if op == "fling" or op == "flingAim" then
		return fling(p, t, tname, if typeof(a) == "Vector3" then a :: Vector3 else nil)
	elseif op == "freeze" or op == "freezeAim" then
		local on = if op == "freezeAim" then frozen[t] == nil else b ~= false
		setFrozen(t, on)
		log(p, if on then "freeze" else "unfreeze", tname)
		return { ok = true, did = (if on then "froze " else "let go ") .. tname }
	elseif op == "goto" or op == "bring" then
		local of = Fight.byPlayer[p]
		local tr, mr = Fight.root(t), of and Fight.root(of)
		if not tr or not mr or not of then return { ok = false, why = "no body" } end
		if op == "goto" then
			local fwd = flatUnit(tr.CFrame.LookVector, Vector3.zAxis)
			local at = tr.Position + fwd * 5
			place(of, CFrame.lookAt(at, Vector3.new(tr.Position.X, at.Y, tr.Position.Z)))
		else
			if frozen[t] then setFrozen(t, false) end
			local fwd = flatUnit(mr.CFrame.LookVector, Vector3.zAxis)
			local at = mr.Position + fwd * 5
			place(t, CFrame.lookAt(at, Vector3.new(mr.Position.X, at.Y, mr.Position.Z)))
		end
		log(p, op, tname)
		return { ok = true, did = (if op == "goto" then "went to " else "brought ") .. tname }
	end
	return { ok = false, why = "nope" }
end

local Remote = Remotes:FindFirstChild("OwnerDev")
if not Remote or not Remote:IsA("RemoteFunction") then
	local r = Instance.new("RemoteFunction")
	r.Name = "OwnerDev"
	r.Parent = Remotes
	Remote = r
end
;(Remote :: RemoteFunction).OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown): any
	local ok, res = pcall(handle, p, op, a, b)
	if not ok then
		warn("[dev] " .. tostring(res))
		return { ok = false, why = "error" }
	end
	return res
end

-- ------------------------------------------------------------------ the hooks Fight and Matches ask
-- may the owner's dev weapons hurt this player (both out of a match: the hub, training, the playground)
Matches.devHit = function(by: Player, t: Player): boolean
	return by:GetAttribute("DevArms") == true and isOwner(by) and HIT_ZONES[Zones.of(by)] == true and HIT_ZONES[Zones.of(t)] == true
end
-- a kill outside a match by the owner (a dev weapon, a fall after a fling): counts for nothing, back at once
Fight.DEV_RESPAWN = 1
Fight.devKill = function(info: any): boolean
	local k, v = info.k, info.v
	if not k or k == v or k.kind ~= "player" or v.kind ~= "player" then return false end
	local kp, vp = k.ref :: Player, v.ref :: Player
	return isOwner(kp) and Zones.of(vp) ~= "match" and Zones.of(kp) ~= "match"
end

-- ------------------------------------------------------------------ the watch: 5 a second
local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.2 then return end
	acc = 0
	local t = now()
	for p, s in states do
		if not p.Parent then states[p] = nil; continue end
		if anyOn(s) and Zones.of(p) == "match" then flagMatch(p, p, "powers on in it") end
		if s.offAt and t >= s.offAt then
			s.offAt = nil
			p:SetAttribute("DevOn", nil)
		end
	end
	-- the frozen: held while they're alive, here and out of a match
	for f, _ in frozen do
		local gone = not f.alive or not table.find(Fight.all, f)
		if f.kind == "player" then
			local tp = f.ref :: Player
			if gone or not tp.Parent then setFrozen(f, false)
			else
				tp:SetAttribute("ACGrace", t + 1)
				if Zones.of(tp) == "match" then
					for o in states do flagMatch(o, tp, "a frozen player in it") break end
				end
			end
		elseif gone then
			frozen[f] = nil
		end
	end
	-- MatchDev comes off 15 s after its match is over for them (the end card has shown by then)
	for q, seen in flagged do
		local m = q.Parent and Matches.raw(q)
		if m and m.dev then flagged[q] = t
		elseif t - seen > 15 then
			flagged[q] = nil
			if q.Parent then q:SetAttribute("MatchDev", nil) end
		end
	end
	-- (only the server writes these, and only on the owner: anyone else's are wiped)
	for _, p in Players:GetPlayers() do
		if not states[p] and (p:GetAttribute("DevOn") ~= nil or p:GetAttribute("DevArms") ~= nil or p:GetAttribute("DevFly") ~= nil) then
			for _, k in { "DevOn", "DevArms", "DevFly", "DevNoclip", "DevSpeed" } do p:SetAttribute(k, nil) end
		end
	end
end)

local function added(p: Player)
	-- "/dev" in the legacy chat opens the menu (OwnerDev.client watches DevPanel)
	p.Chatted:Connect(function(msg: string)
		if string.lower(string.sub(msg, 1, 4)) == "/dev" and isOwner(p) then p:SetAttribute("DevPanel", os.clock()) end
	end)
	-- a new life is free
	p.CharacterAdded:Connect(function()
		local f = Fight.byPlayer[p]
		if f and frozen[f] then frozen[f] = nil end
		if p:GetAttribute("DevFrozen") ~= nil then p:SetAttribute("DevFrozen", nil) end
	end)
end
for _, p in Players:GetPlayers() do added(p) end
Players.PlayerAdded:Connect(added)
Players.PlayerRemoving:Connect(function(p: Player)
	if states[p] then
		states[p] = nil
		unfreezeAll()
	end
	local f = Fight.byPlayer[p]
	if f then frozen[f] = nil end
	budget[p], refused[p], flagged[p] = nil, nil, nil
end)

-- ------------------------------------------------------------------ Studio tests
if STUDIO then
	local old = ServerStorage:FindFirstChild("JankDev")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankDev"
	fn.OnInvoke = function(op: any, a: any, b: any, c: any, d: any): any
		if op == "state" then
			local out = { frozen = {}, owners = {} }
			for f in frozen do table.insert(out.frozen, f.name) end
			for p, s in states do
				out.owners[p.Name] = { state = view(s), attrs = { DevOn = p:GetAttribute("DevOn"), DevFly = p:GetAttribute("DevFly"), DevNoclip = p:GetAttribute("DevNoclip"), DevSpeed = p:GetAttribute("DevSpeed"), DevArms = p:GetAttribute("DevArms") } }
			end
			out.log = lines
			return out
		elseif op == "as" then
			return handle(a, b, c, d)
		elseif op == "log" then
			return lines
		end
		return nil
	end
	fn.Parent = ServerStorage
end
