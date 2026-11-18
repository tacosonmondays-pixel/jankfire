--!strict
-- weapons batch E: the Lasso (WEAPONS.md "Lasso"; traced spec weapons-batchE-spec.md, web shared/lasso.js holdStep).
-- hold fire to spin the loop (1.1 s to full), let go to throw it: 12 to 28 m out, 24 to 38 m/s by the spin. it catches the
-- first one it touches that it can see (a katana guard facing it cuts it; teammates too, for a ride): the rope ties at
-- the WAIST. then they swing on your rope: a spring toward where you aim at the rope's length (2 to 16 m: the wheel, R
-- reels in, F lets out), never past 1.1 x the rope + 1 m; turning, shaking and walking back pump it. let go (fire or aim)
-- and they fly on with their speed (x1.2) and yours; hitting a wall or the floor at 22 m/s and up hurts ((s - 22) x 2.4,
-- 140 at most). they wriggle free with 18 presses (a teammate with 1), and the rope slips after 5 s.
-- this port runs the swing on the SERVER (the web ran it on the holder's machine and checked it): the holder streams
-- where they aim ("aim"), the server steps the body and sends the held one where to be ("pos"); their client follows
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local LassoR = Remotes:FindFirstChild("Lasso") :: RemoteEvent?
if not LassoR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Lasso"
	r.Parent = Remotes
	LassoR = r
end

local S = Weapons.S
local now = os.clock
type Fighter = Rules.Fighter

local L = {
	spinT = 1.1, rangeMin = 12 * S, rangeMax = 28 * S, speedMin = 24 * S, speedMax = 38 * S, up = 1.2 * S, inherit = 0.3, inheritCap = 25 * S,
	grav = 6 * S, r = 0.55 * S, flight = 2.5, cd = 0.35, missCd = 1.2,
	lenMin = 2 * S, lenMax = 16 * S, ease = 14 * S, waist = 1.1 * S, k = 100, zeta = 0.12, aMax = 95 * S, bodyGrav = 26 * S,
	ropeK = 1.1, ropeAdd = 1 * S, fric = 8 * S, give = 6 * S, hold = 5,
	fling = 1.2, flingSelf = 40 * S, flingCap = 120 * S, mateCap = 45 * S, wriggle = 18, wrGap = 0.06,
	splatMin = 22 * S, splatK = 2.4, splatMax = 140, splatGap = 0.3, flyT = 4,
}
L.c = 2 * L.zeta * math.sqrt(L.k)

local function uid(f: Fighter): number? return if f.kind == "player" then (f.ref :: Player).UserId else nil end
local function callout(f: Fighter, text: string, dur: number) if f.kind == "player" then CalloutR:FireClient(f.ref :: Player, text, dur) end end
local function waistOf(t: Fighter): Vector3? local ft = Fight.feet(t); return ft and ft + Vector3.new(0, L.waist, 0) end

-- ------------------------------------------------------------------ who's holding whom
type Hold = {
	holder: Fighter, victim: Fighter, len: number, want: number, yaw: number, pitch: number, t0: number,
	p: Vector3, v: Vector3, tPrev: Vector3?, wr: number, wrT: number, splatT: number, mate: boolean, sent: number, ropeT: number?,
}
local holds: { Hold } = {}
local function holdOf(f: Fighter): Hold? for _, h in holds do if h.holder == f then return h end end return nil end
local function heldBy(f: Fighter): Hold? for _, h in holds do if h.victim == f then return h end end return nil end

-- a flung body for a few seconds after: the server watches it hit things
type Fly = { t: Fighter, by: Fighter?, t0: number, lastV: Vector3, splatT: number }
local flying: { Fly } = {}

local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function mapOnly(): RaycastParams?
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	mapParams.FilterDescendantsInstances = { map }
	return mapParams
end

local function setHeld(t: Fighter, on: boolean)
	if t.kind ~= "player" then return end
	local p = t.ref :: Player
	p:SetAttribute("LassoHeld", if on then true else nil)
	if on then p:SetAttribute("ACGrace", now() + L.hold + 1) end
end
local function finish(h: Hold, why: string, fling: Vector3?)
	local i = table.find(holds, h)
	if not i then return end
	table.remove(holds, i)
	setHeld(h.victim, false)
	if h.holder.kind == "player" then (h.holder.ref :: Player):SetAttribute("LassoHolding", nil) end
	local v = fling or h.v
	if v.Magnitude > L.flingCap then v = v.Unit * L.flingCap end
	-- off the rope with that speed: their client (or the dummy) flies on
	if h.victim.alive then
		if h.victim.kind == "player" then
			local p = h.victim.ref :: Player
			p:SetAttribute("ACGrace", now() + L.flyT + 2)
			;(LassoR :: RemoteEvent):FireClient(p, "free", h.p, v)
		else
			local r = Fight.root(h.victim)
			if r then r.AssemblyLinearVelocity = v end
		end
		table.insert(flying, { t = h.victim, by = if h.mate then nil else h.holder, t0 = now(), lastV = v, splatT = 0 })
		if not h.mate then Rules.tagged(h.victim, h.holder, "lasso", now()) end -- (a fall after it is theirs)
	end
	FxR:FireAllClients({ k = "lassoend", holder = Fight.model(h.holder), victim = Fight.model(h.victim), why = why })
	if why == "fling" and v.Magnitude >= 45 * S then callout(h.holder, ("%d m/s"):format(math.floor(v.Magnitude / S + 0.5)), 0.9) end
end

-- ------------------------------------------------------------------ the swing (holdStep)
local BODY = Vector3.new(0.8 * S, 1.8 * S, 0.8 * S) * 0.9
local function splat(t: Fighter, by: Fighter?, s: number, at: Vector3, last: number): number
	if s < L.splatMin or now() - last < L.splatGap then return last end
	local dmg = math.min(L.splatMax, (s / S - L.splatMin / S) * L.splatK)
	if by and Fight.allow(by, t) then Fight.hurt(t, dmg, by, "lasso", false, nil, at)
	else Fight.hurt(t, dmg, nil, "lasso", false, nil, at, nil, true) end
	FxR:FireAllClients({ k = "lassoslam", p = at })
	return now()
end
local function stepHold(h: Hold, dt: number)
	local eye = Fight.eye(h.holder)
	if not eye then return end
	-- the rope eases toward the length you want
	h.len += math.clamp(h.want - h.len, -L.ease * dt, L.ease * dt)
	local cp = math.cos(h.pitch)
	local aim = Vector3.new(-math.sin(h.yaw) * cp, math.sin(h.pitch), -math.cos(h.yaw) * cp)
	local T = eye + aim * h.len
	local vT = if h.tPrev then (T - h.tPrev) / dt else Vector3.zero
	h.tPrev = T
	local a = (T - h.p) * L.k + (vT - h.v) * L.c
	if a.Magnitude > L.aMax then a = a.Unit * L.aMax end
	a -= Vector3.new(0, L.bodyGrav, 0)
	h.v += a * dt
	-- the rope: no further than 1.1 x it + 1 m (only the outward speed goes, relative to you: a hard turn swings them round)
	local hr = Fight.root(h.holder)
	local hv = if hr then hr.AssemblyLinearVelocity else Vector3.zero
	local ropeMax = L.ropeK * h.len + L.ropeAdd
	local nxt = h.p + h.v * dt
	local out = nxt - eye
	if out.Magnitude > ropeMax then
		local dir = out.Unit
		local vr = (h.v - hv):Dot(dir)
		if vr > 0 then h.v -= dir * vr end
		nxt = h.p + h.v * dt
	end
	-- the map: what's lost against it is the impact
	local params = mapOnly()
	local move = nxt - h.p
	if params and move.Magnitude > 1e-4 then
		local hit = workspace:Blockcast(CFrame.new(h.p), BODY, move, params)
		if hit then
			local n = hit.Normal
			local into = -h.v:Dot(n)
			if into > 0 then
				h.v += n * into
				h.splatT = splat(h.victim, if h.mate then nil else h.holder, into, hit.Position, h.splatT)
			end
			nxt = h.p + move.Unit * math.max(0, hit.Distance - 0.05)
			if n.Y > 0.6 then -- (dragged along the floor)
				local fl = Vector3.new(h.v.X, 0, h.v.Z)
				local sp = fl.Magnitude
				if sp > 1e-3 then fl *= math.max(0, sp - L.fric * dt) / sp end
				h.v = Vector3.new(fl.X, math.max(h.v.Y, 0), fl.Z)
			end
		end
	end
	h.p = nxt
	-- still past the rope's end: eased back toward it
	local o2 = h.p - eye
	if o2.Magnitude > ropeMax then h.p = eye + o2.Unit * math.max(ropeMax, o2.Magnitude - L.give * dt) end
end

-- ------------------------------------------------------------------ the loop in flight
type Loop = { id: number, owner: Fighter, p: Vector3, v: Vector3, eye: Vector3, range: number, t0: number, tried: { [Fighter]: boolean } }
local loops: { Loop } = {}
local nextId = 0
local nextT: { [Fighter]: number } = setmetatable({}, { __mode = "k" }) :: any
local spin0: { [Fighter]: number } = setmetatable({}, { __mode = "k" }) :: any

local function catchable(t: Fighter): boolean
	if not t.alive or holdOf(t) or heldBy(t) then return false end
	if now() < t.staggerUntil then return false end -- (stunned or frozen)
	if t.kind == "player" and now() - t.spawnT < 1.2 then return false end -- (just spawned)
	return true
end
local function catch(lp: Loop, t: Fighter, at: Vector3)
	local f = lp.owner
	local eye, waist = Fight.eye(f), waistOf(t)
	if not eye or not waist then return end
	local h: Hold = {
		holder = f, victim = t, len = 0, want = 0, yaw = 0, pitch = 0, t0 = now(), p = waist, v = Vector3.zero, tPrev = nil,
		wr = 0, wrT = 0, splatT = 0, mate = not Fight.allow(f, t), sent = 0,
	}
	h.len = math.clamp((waist - eye).Magnitude, L.lenMin, L.lenMax)
	h.want = h.len
	local root = Fight.root(f)
	if root then
		local lk = root.CFrame.LookVector
		h.yaw = math.atan2(-lk.X, -lk.Z)
	end
	table.insert(holds, h)
	setHeld(t, true)
	if f.kind == "player" then
		(f.ref :: Player):SetAttribute("LassoLen", h.len) -- (the rope's start: the holder's wheel and keys go from here)
		;(f.ref :: Player):SetAttribute("LassoHolding", true)
	end
	if not h.mate then Rules.tagged(t, f, "lasso", now()) end
	FxR:FireAllClients({ k = "lassohold", holder = Fight.model(f), victim = Fight.model(t), by = uid(f), p = at })
end
local function stepLoop(lp: Loop, dt: number): boolean -- (false: it's done)
	local f = lp.owner
	if not table.find(Fight.all, f) or not f.alive or now() - lp.t0 > L.flight then return false end
	lp.v -= Vector3.new(0, L.grav * dt, 0)
	local move = lp.v * dt
	local params = mapOnly()
	local hit = if params then workspace:Spherecast(lp.p, L.r, move, params) else nil
	local to = if hit then lp.p + move.Unit * hit.Distance else lp.p + move
	-- the first body it touches (the loop is wide: half a metre round)
	local best, bt = nil, math.huge
	local dir = if move.Magnitude > 1e-4 then move.Unit else Vector3.zAxis
	local len = (to - lp.p).Magnitude
	for _, t in Fight.all do
		if t == f or lp.tried[t] or not t.alive then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= f.ref then continue end
		local w = waistOf(t)
		if not w then continue end
		local rel = w - lp.p
		local along = math.clamp(rel:Dot(dir), 0, len)
		local miss = (rel - dir * along).Magnitude
		if miss <= L.r + 0.6 * S and along < bt then best, bt = t, along end
	end
	if best then
		local t = best :: Fighter
		lp.tried[t] = true
		local at = lp.p + dir * bt
		local c = waistOf(t) :: Vector3
		local blocked = params and workspace:Raycast(at, c - at, params)
		if not blocked then
			-- a katana guard facing it cuts it
			local tr = Fight.root(t)
			if tr and Fight.allow(f, t) and Rules.parryAt(t, lp.p - tr.Position, Fight.facing(t), now()) > 0 then
				FxR:FireAllClients({ k = "loopx", id = lp.id, p = at, cut = true })
				nextT[f] = now() + L.missCd
				callout(f, "CUT", 0.8)
				return false
			end
			if catchable(t) then
				FxR:FireAllClients({ k = "loopx", id = lp.id, p = at, caught = true })
				catch(lp, t, at)
				return false
			end
		end
	end
	lp.p = to
	if hit or (lp.p - lp.eye).Magnitude > lp.range then
		FxR:FireAllClients({ k = "loopx", id = lp.id, p = lp.p })
		nextT[f] = now() + L.missCd
		return false
	end
	return true
end

local function throw(p: Player, eye: Vector3, look: Vector3, claimS: unknown)
	local f = Fight.byPlayer[p]
	if not f or not f.alive or f.held ~= "lasso" or not table.find(Rules.loadoutOf(f), "lasso") then return end
	if holdOf(f) or heldBy(f) then return end
	local n = now()
	if n < f.staggerUntil or n < (nextT[f] or 0) then return end
	for _, lp in loops do if lp.owner == f then return end end
	local seye = Fight.eye(f)
	if not seye then return end
	if (eye - seye).Magnitude > 4 * S then eye = seye end
	local s = math.clamp(if type(claimS) == "number" and claimS == claimS then claimS else 0, 0, 1)
	s = math.min(s, if spin0[f] then (n - (spin0[f] :: number)) / L.spinT + 0.25 else 0.25)
	spin0[f] = nil
	p:SetAttribute("LassoSpin", nil)
	nextT[f] = n + L.cd
	local root = Fight.root(f)
	local inh = if root then root.AssemblyLinearVelocity * L.inherit else Vector3.zero
	if inh.Magnitude > L.inheritCap then inh = inh.Unit * L.inheritCap end
	local params = mapOnly()
	local out = 0.9 * S
	local hit = params and workspace:Raycast(eye, look * out, params)
	if hit then out = math.max(0, hit.Distance - 0.3 * S) end
	nextId += 1
	local lp: Loop = {
		id = nextId, owner = f, p = eye + look * out, v = look * (L.speedMin + (L.speedMax - L.speedMin) * s) + Vector3.new(0, L.up, 0) + inh,
		eye = eye, range = L.rangeMin + (L.rangeMax - L.rangeMin) * s, t0 = n, tried = {},
	}
	table.insert(loops, lp)
	Fight.shot(f, "lasso")
	FxR:FireAllClients({ k = "loop", id = lp.id, by = p.UserId, model = Fight.model(f), p = lp.p, v = lp.v, g = L.grav })
end

;(LassoR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, op: unknown, a: unknown, b: unknown, c: unknown)
	local f = Fight.byPlayer[p]
	if not f then return end
	if op == "spin" then
		-- (LassoSpin: everyone's copy of you spins the loop overhead, ThirdPerson; off at the throw)
		if f.held == "lasso" then spin0[f] = now(); p:SetAttribute("LassoSpin", true) end
	elseif op == "throw" then
		if p:GetAttribute("Zone") == "hub" or typeof(a) ~= "Vector3" or typeof(b) ~= "Vector3" then return end
		local lk = b :: Vector3
		if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 then return end
		throw(p, a :: Vector3, lk.Unit, c)
	elseif op == "aim" then
		-- the holder: where they aim (yaw, pitch) and the rope length they want
		local h = holdOf(f)
		if not h or type(a) ~= "number" or type(b) ~= "number" then return end
		if a ~= a or b ~= b then return end
		h.yaw = a :: number
		h.pitch = math.clamp(b :: number, -1.4, 1.4)
		if type(c) == "number" and c == c then h.want = math.clamp(c :: number, L.lenMin, L.lenMax) end
	elseif op == "rel" then
		local h = holdOf(f)
		if not h then return end
		local root = Fight.root(f)
		local mine = if root then root.AssemblyLinearVelocity else Vector3.zero
		if mine.Magnitude > L.flingSelf then mine = mine.Unit * L.flingSelf end
		local v = h.v * L.fling + mine
		if h.mate and v.Magnitude > L.mateCap then v = v.Unit * L.mateCap end
		finish(h, "fling", v)
	elseif op == "wr" then
		local h = heldBy(f)
		if not h then return end
		local n = now()
		if n - h.wrT < L.wrGap then return end
		h.wrT = n
		h.wr += 1
		if h.mate or h.wr >= L.wriggle then finish(h, "wriggle") end
	end
end)

-- ------------------------------------------------------------------ every Heartbeat: the loops, the holds (120 Hz steps), the flights
RunService.Heartbeat:Connect(function(dt: number)
	-- a spin that never became a throw (switched away, died, or held too long): its LassoSpin goes
	for f, t0 in spin0 do
		if now() - t0 > 4 or f.held ~= "lasso" or not f.alive then
			spin0[f] = nil
			if f.kind == "player" then (f.ref :: Player):SetAttribute("LassoSpin", nil) end
		end
	end
	for i = #loops, 1, -1 do
		local ok, alive = pcall(stepLoop, loops[i], dt)
		if not ok or not alive then table.remove(loops, i) end
	end
	local n = now()
	for i = #holds, 1, -1 do
		local h = holds[i]
		if not h.holder.alive or not h.victim.alive or not table.find(Fight.all, h.holder) or not table.find(Fight.all, h.victim) then finish(h, "gone"); continue end
		if n - h.t0 > L.hold then finish(h, "slip"); continue end
		if n < h.holder.staggerUntil then finish(h, "stagger"); continue end
		local steps = math.clamp(math.ceil(dt * 120), 1, 6)
		for _ = 1, steps do stepHold(h, dt / steps) end
		-- the held one: a dummy is put there; a player's client is told where to be (30 a second)
		local root = Fight.root(h.victim)
		local feet = h.p - Vector3.new(0, L.waist, 0)
		if h.victim.kind ~= "player" then
			if root then
				local m = Fight.model(h.victim)
				local hip = if root then root.Position.Y - (Fight.feet(h.victim) or root.Position).Y else 3
				if m then m:PivotTo(CFrame.new(feet + Vector3.new(0, hip, 0)) * (root.CFrame - root.CFrame.Position)) end
				root.AssemblyLinearVelocity = h.v
			end
		elseif n - h.sent >= 1 / 30 then
			h.sent = n
			local p = h.victim.ref :: Player
			p:SetAttribute("ACGrace", n + 1)
			;(LassoR :: RemoteEvent):FireClient(p, "pos", feet, h.v)
		end
		if n - (h.ropeT or 0) >= 0.05 then -- (the rope's far end for everyone's beam, 20 a second)
			h.ropeT = n
			FxR:FireAllClients({ k = "lassorope", holder = Fight.model(h.holder), p = h.p })
		end
	end
	-- flung: a hard stop against something hurts (the server reads their real speed)
	for i = #flying, 1, -1 do
		local fl = flying[i]
		if n - fl.t0 > L.flyT or not fl.t.alive then table.remove(flying, i); continue end
		local r = Fight.root(fl.t)
		if not r then table.remove(flying, i); continue end
		local v = r.AssemblyLinearVelocity
		local lost = (fl.lastV - v).Magnitude
		if fl.lastV.Magnitude >= L.splatMin and lost >= 0.6 * fl.lastV.Magnitude then
			fl.splatT = splat(fl.t, fl.by, lost, r.Position, fl.splatT)
			table.remove(flying, i)
			continue
		end
		fl.lastV = v
	end
end)

Players.PlayerRemoving:Connect(function(p)
	local f = Fight.byPlayer[p]
	if not f then return end
	for i = #holds, 1, -1 do local h = holds[i]; if h.holder == f or h.victim == f then finish(h, "gone") end end
	for i = #loops, 1, -1 do if loops[i].owner == f then table.remove(loops, i) end end
end)
