--!strict
-- weapons batch D (WEAPONS.md "TV Remote", "Scales of Justice"; weapons-batchD-spec.md): the moves that aren't a shot,
-- a swing or a thrown thing. the server picks the target and does them; clients draw them (Fx "tvpause", "tvrewind",
-- "gavel", "gavelx").
--   the TV Remote (TVRemote remote: "pause" | "rewind", look): point it. pause: whoever you point at (45 m, 0.09 rad of
--     slack) is frozen 1.2 s, then their momentum comes back (3.5 s cooldown). rewind: they're snapped back to where the
--     server saw them 2 s ago, standing still (6 s); watched for 2.5 s and put back if their client missed it
--   the Scales' right click (Gavel remote: look): a pillar of light on someone far away (42 m, 0.16 rad), or where you
--     aim lands. it comes down 1 s later: 20 x the verdict to everyone in it (2.3 m round, 3.2 m up), a shove up. 10 s;
--     nobody and nowhere to aim at: no cooldown spent
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Verdict = require(script.Parent:WaitForChild("Verdict"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local function remote(name: string): RemoteEvent
	local r = Remotes:FindFirstChild(name)
	if r and r:IsA("RemoteEvent") then return r end
	local e = Instance.new("RemoteEvent")
	e.Name = name
	e.Parent = Remotes
	return e
end
local TVR, GavelR = remote("TVRemote"), remote("Gavel")

local W = Weapons.list
local S = Weapons.S
local now = os.clock
type Fighter = Rules.Fighter

local function uid(f: Fighter): number? return if f.kind == "player" then (f.ref :: Player).UserId else nil end
local function callout(f: Fighter, text: string, dur: number)
	if f.kind == "player" then CalloutR:FireClient(f.ref :: Player, text, dur) end
end
local function centre(t: Fighter): Vector3? local ft = Fight.feet(t); return ft and ft + Vector3.new(0, 0.9 * S, 0) end

-- ------------------------------------------------------------------ where everyone was: 10 a second, the last 2.6 s
local hist: { [Fighter]: { { t: number, cf: CFrame } } } = setmetatable({}, { __mode = "k" }) :: any
local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.1 then return end
	acc = 0
	local n = now()
	for _, f in Fight.all do
		if not f.alive then hist[f] = nil; continue end
		local r = Fight.root(f)
		if not r then continue end
		local h = hist[f] or {}
		hist[f] = h
		table.insert(h, { t = n, cf = r.CFrame })
		while #h > 26 do table.remove(h, 1) end
	end
end)
local function pastOf(f: Fighter, back: number): CFrame?
	local h = hist[f]
	if not h or #h == 0 then return nil end
	local want = now() - back
	local best = h[1].cf
	for _, s in h do if s.t <= want then best = s.cf end end
	return best
end

-- ------------------------------------------------------------------ who you're pointing at
local function pick(f: Fighter, look: Vector3, range: number, cone: number): Fighter?
	local eye = Fight.eye(f)
	if not eye then return nil end
	local best, ba = nil, math.huge
	for _, t in Fight.all do
		if t == f or not t.alive or not Fight.allow(f, t) then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= f.ref then continue end
		local c = centre(t)
		if not c then continue end
		local to = c - eye
		local d = to.Magnitude
		if d > range or d < 1e-3 then continue end
		local a = math.acos(math.clamp(to.Unit:Dot(look), -1, 1))
		if a > cone + math.atan(1.2 * S / d) then continue end -- (the slack, plus a body's width up close)
		if Fight.castMap(eye, to.Unit, d) then continue end
		if a < ba then best, ba = t, a end
	end
	return best
end
local function holding(p: Player, wid: string): Fighter?
	if (p:GetAttribute("Zone") == "hub" and p:GetAttribute("DevArms") ~= true) then return nil end
	local f = Fight.byPlayer[p]
	if not f or not f.alive or f.held ~= wid then return nil end
	if now() < f.staggerUntil then return nil end
	return f
end
local function flatLook(look: unknown): Vector3?
	if typeof(look) ~= "Vector3" then return nil end
	local lk = look :: Vector3
	if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 then return nil end
	return lk.Unit
end

-- ------------------------------------------------------------------ the TV Remote
-- (21 Nov 2026) whoever was paused can't be paused again till this (server time): two Remotes can't chain one person
local pauseFree: { [any]: number } = setmetatable({}, { __mode = "k" }) :: any
local function pauseOne(by: Fighter, t: Fighter, dur: number)
	local n = now()
	pauseFree[t] = n + dur + ((W.remote :: any).pause.immune or 0)
	Rules.stun(t, dur, n) -- (no shots, swings or guard while paused)
	if t.kind == "player" then
		local p = t.ref :: Player
		local st = workspace:GetServerTimeNow() + dur
		p:SetAttribute("PauseUntil", st) -- (their client holds them still, then gives the momentum back: WeaponStates)
		p:SetAttribute("StunUntil", st)
		p:SetAttribute("ACGrace", n + dur + 0.5)
	else
		local r = Fight.root(t)
		if r then
			local was, v = r.Anchored, r.AssemblyLinearVelocity
			r.Anchored = true
			task.delay(dur, function()
				if r.Parent then r.Anchored = was; if not was then r.AssemblyLinearVelocity = v end end
			end)
		end
	end
	FxR:FireAllClients({ k = "tvpause", model = Fight.model(t), dur = dur, by = uid(by) })
	callout(t, "PAUSED", dur)
end
local function rewindOne(by: Fighter, t: Fighter, back: number)
	local cf = pastOf(t, back)
	local r = Fight.root(t)
	if not cf or not r then return end
	local from = r.Position
	local function snap()
		local m = Fight.model(t)
		if not m or not t.alive then return end
		if t.kind == "player" then
			local p = t.ref :: Player
			p:SetAttribute("TeleportT", now()) -- (a server move: the anti-cheat starts afresh from here)
			p:SetAttribute("ACGrace", now() + 1)
		end
		m:PivotTo(cf :: CFrame)
		local rr = Fight.root(t)
		if rr then rr.AssemblyLinearVelocity = Vector3.zero end
	end
	snap()
	FxR:FireAllClients({ k = "tvrewind", model = Fight.model(t), a = from, b = (cf :: CFrame).Position, by = uid(by) })
	callout(t, "REWOUND", 1)
	-- watched: a client that kept going from where it was (it missed the snap) is put back
	for i = 1, 5 do
		task.delay(0.5 * i, function()
			local rr = Fight.root(t)
			if not t.alive or not rr then return end
			local dTo, dFrom = (rr.Position - (cf :: CFrame).Position).Magnitude, (rr.Position - from).Magnitude
			if dTo > 6 * S and dFrom < dTo then snap() end
		end)
	end
end
TVR.OnServerEvent:Connect(function(p: Player, op: unknown, look: unknown)
	local f = holding(p, "remote")
	local lk = flatLook(look)
	if not f or not lk or (op ~= "pause" and op ~= "rewind") then return end
	local w = W.remote :: any
	local n = now()
	local t = pick(f, lk, w.range, w.cone)
	if not t then return end -- (nobody there: nothing spent)
	if op == "pause" then
		if n < (pauseFree[t] or 0) then return end -- (just paused, by anyone: nothing spent)
		if not Rules.gate(f, "tvpause", n, w.pause.cd / 0.9) then return end
		pauseOne(f, t, w.pause.dur)
	else
		if not Rules.gate(f, "tvrewind", n, w.rewind.cd / 0.9) then return end
		rewindOne(f, t, w.rewind.back)
	end
	-- (21 Nov 2026) either button locks the other for a moment: no pause-then-rewind in one breath
	local other = if op == "pause" then "tvrewind" else "tvpause"
	f.gate[other] = math.max(f.gate[other] or -math.huge, n + (w.lock or 0))
	Fight.shot(f, "remote")
	Rules.tagged(t, f, "remote", n) -- (a fall after it is theirs)
end)

-- ------------------------------------------------------------------ the Scales of Justice's pillar
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function aimLands(eye: Vector3, look: Vector3, range: number): Vector3?
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	mapParams.FilterDescendantsInstances = { map }
	local hit = workspace:Raycast(eye, look * range, mapParams)
	if not hit then return nil end
	-- (a wall: the floor at its foot)
	local down = workspace:Raycast(hit.Position + hit.Normal * 0.5 * S + Vector3.new(0, 0.5 * S, 0), Vector3.new(0, -8 * S, 0), mapParams)
	return if down then down.Position else (if hit.Normal.Y > 0.6 then hit.Position else nil)
end
GavelR.OnServerEvent:Connect(function(p: Player, look: unknown)
	local f = holding(p, "scales")
	local lk = flatLook(look)
	if not f or not lk then return end
	local w = W.scales :: any
	local G = w.gavel
	local n = now()
	if (f.castUntil and n < f.castUntil) or Rules.parryOpen(f, n) then return end
	local eye = Fight.eye(f)
	if not eye then return end
	local t = pick(f, lk, G.range, G.cone)
	local at = if t then Fight.feet(t) else aimLands(eye, lk, G.range)
	if not at then return end -- (nowhere: nothing spent)
	if not Rules.gate(f, "gavel", n, G.cd / 0.9) then return end
	Fight.shot(f, "scales")
	local spot = at :: Vector3
	FxR:FireAllClients({ k = "gavel", p = spot, r = G.r, h = G.h, dur = G.delay, by = p.UserId })
	task.delay(G.delay, function()
		FxR:FireAllClients({ k = "gavelx", p = spot, r = G.r, h = G.h })
		if not table.find(Fight.all, f) then return end
		for _, o in Fight.all do
			if o == f or not o.alive or not Fight.allow(f, o) then continue end
			if o.onlyFor ~= nil and o.onlyFor ~= f.ref then continue end
			local ft = Fight.feet(o)
			if not ft then continue end
			local dl = ft - spot
			if Vector3.new(dl.X, 0, dl.Z).Magnitude > G.r or dl.Y < -1 * S or dl.Y > G.h then continue end
			Fight.hurt(o, G.dmg * Verdict.mult(f, o), f, "scales", false, Vector3.new(0, G.kbUp, 0), ft + Vector3.new(0, 1 * S, 0))
		end
	end)
end)

Players.PlayerRemoving:Connect(function(p)
	local f = Fight.byPlayer[p]
	if f then hist[f] = nil end
end)
