--!strict
-- weapons batch B (18 Nov 2026, WEAPONS.md "Leaf Blower", "Cigarette", "Big Laser Pointer"): the weapons you hold the
-- trigger on. the client says when the trigger goes down and up and where it looks while held (the Hold remote:
-- (wid, true | false | "aim", look)); the SERVER times everything and does the hurting, from its own eye, its own cone,
-- line of sight and fuel (the web server trusted the client for all of those):
--   blower (hold = "blow"): while held with fuel, every `tick` s everyone in the cone is shoved straight away from you
--     (toT x push + up), 0 damage (1 on some ticks), so a fall is your kill. fuel drains while held, refills when not
--   cig, the Hot Sauce (hold = "breath"): hold to take a swig (the charge, timed here), let go and you breathe fire for
--     min(charge, maxCharge) x exhaleMul s: every `tick` s `dmg` to everyone in the cone. let go past maxCharge, or
--     hold past coughAt, and it burns you instead (cough, 12)
--   laser (hold = "beam"): hold to charge (k = (held - tap) / (charge - tap), 0..1), let go for a beam of dur(k) s
--     that goes through everyone along your look: every `tick` s dmg(k) to everyone whose box (grown by r(k)) it
--     touches. cd after it. the slow while charging and your own kick are your client's
-- everyone sees it through Fx: "blow" (on/off), "breath" (on/off, the cone's look), "beam" (each tick's line)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local HoldR = Remotes:FindFirstChild("Hold") :: RemoteEvent?
if not HoldR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Hold"
	r.Parent = Remotes
	HoldR = r
end

local W = Weapons.list
local S = Weapons.S
local now = os.clock
type Fighter = Rules.Fighter

type HoldState = {
	wid: string, down: boolean, t0: number, look: Vector3, next: number,
	fuel: number, fuelT: number, -- the blower's tank
	exhaleUntil: number?, coughed: boolean?, -- the sauce
	beam: { k: number, untilT: number }?, cdUntil: number, -- the laser
	lastHit: { [Fighter]: number },
}
local state: { [Fighter]: HoldState } = setmetatable({}, { __mode = "k" }) :: any

local function finiteV(v: any): boolean
	return typeof(v) == "Vector3" and Rules.finite(v.X) and Rules.finite(v.Y) and Rules.finite(v.Z) and v.Magnitude < 1e6
end
local function uid(f: Fighter): number? return if f.kind == "player" then (f.ref :: Player).UserId else nil end
local function stateOf(f: Fighter, wid: string): HoldState
	local s = state[f]
	if not s or s.wid ~= wid then
		local w = W[wid] :: any
		s = { wid = wid, down = false, t0 = 0, look = Vector3.zAxis, next = 0, fuel = (w.fuel or 0), fuelT = now(),
			cdUntil = 0, lastHit = setmetatable({}, { __mode = "k" }) :: any }
		state[f] = s
	end
	return s :: HoldState
end
-- everyone in the cone from eye round look out to range, in sight (web conePlayers, done here: the server's own)
local function inCone(f: Fighter, eye: Vector3, look: Vector3, range: number, cone: number): { { t: Fighter, dir: Vector3, c: Vector3 } }
	local out = {}
	for _, t in Fight.all do
		if t == f or not t.alive or not Fight.allow(f, t) then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= f.ref then continue end
		local ft = Fight.feet(t)
		if not ft then continue end
		local c = ft + Vector3.new(0, Hitbox.ROOT_UP, 0)
		local to = c - eye
		local d = to.Magnitude
		if d < 1e-3 or d > range + Rules.SLACK then continue end
		if d > 1.5 * S and look:Dot(to.Unit) < math.cos(cone + math.atan(Weapons.BOX.bodyR / d)) then continue end
		if Fight.castMap(eye, to.Unit, d) then continue end
		table.insert(out, { t = t, dir = to.Unit, c = c })
	end
	return out
end
local function fx(f: Fighter, k: string, x: { [string]: any })
	x.k, x.by, x.model = k, uid(f), Fight.model(f)
	FxR:FireAllClients(x)
end

-- the trigger: (wid, true) down, (wid, false) up, (wid, "aim", look) where you look while it's down
local budget: { [Player]: { n: number, t: number } } = {}
;(HoldR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, wid: unknown, mode: unknown, look: unknown)
	local b = budget[p] or { n = 60, t = now() }
	budget[p] = b
	b.n = math.min(60, b.n + (now() - b.t) * 40); b.t = now()
	if b.n < 1 then return end
	b.n -= 1
	if (p:GetAttribute("Zone") == "hub" and p:GetAttribute("DevArms") ~= true) then return end
	local f = Fight.byPlayer[p]
	if not f or type(wid) ~= "string" or not W[wid] or (W[wid] :: any).kind ~= "hold" then return end
	if f.held ~= wid or not f.alive then return end
	local w = W[wid] :: any
	local s = stateOf(f, wid)
	local n = now()
	if finiteV(look) and (look :: Vector3).Magnitude > 0.5 then s.look = (look :: Vector3).Unit end
	if mode == "aim" then return end
	if mode == true and not s.down then
		if n < f.staggerUntil then return end -- (tased or staggered: nothing)
		if w.hold == "beam" and (s.beam or n < s.cdUntil) then return end -- (a beam running, or the cooldown)
		if w.hold == "breath" and s.exhaleUntil and n < s.exhaleUntil then return end
		s.down, s.t0, s.coughed = true, n, nil
		if w.hold == "breath" then p:SetAttribute("Swig", true) end -- (everyone's third person: the bottle at the mouth)
		if w.hold == "blow" then fx(f, "blow", { on = true }) end
		if w.hold == "beam" then fx(f, "charge", { on = true }) end
	elseif mode == false and s.down then
		s.down = false
		p:SetAttribute("Swig", nil)
		local held = n - s.t0
		if w.hold == "blow" then fx(f, "blow", { on = false })
		elseif w.hold == "breath" and not s.coughed then
			if held > w.maxCharge then
				s.coughed = true
				Fight.hurt(f, w.cough or 12, nil, wid, false, nil, nil, nil, true)
				fx(f, "cough", {})
			elseif held > 0.12 then
				s.exhaleUntil = n + math.min(held, w.maxCharge) * w.exhaleMul
				s.next = n
				fx(f, "breath", { on = true, dur = (s.exhaleUntil :: number) - n })
			end
		elseif w.hold == "beam" then
			fx(f, "charge", { on = false })
			local k = math.clamp((held - w.tap) / (w.charge - w.tap), 0, 1)
			local dur = w.dur[1] + (w.dur[2] - w.dur[1]) * k
			s.beam = { k = k, untilT = n + dur }
			s.next = n
			s.cdUntil = n + dur + w.cd
		end
	end
end)
Players.PlayerRemoving:Connect(function(p) budget[p] = nil end)

-- the ticks, every Heartbeat: fuel, the cone, the breath, the beam
RunService.Heartbeat:Connect(function(dt: number)
	local n = now()
	for f, s in state do
		local w = W[s.wid] :: any
		if not w then continue end
		local alive = f.alive and f.held == s.wid and n >= f.staggerUntil
			and not (f.kind == "player" and (f.ref :: Player):GetAttribute("Zone") == "hub" and (f.ref :: Player):GetAttribute("DevArms") ~= true) -- (the hub is weapons-free)
		if not alive then
			if s.down and w.hold == "blow" then fx(f, "blow", { on = false }) end
			if s.down and w.hold == "beam" then fx(f, "charge", { on = false }) end
			s.down, s.exhaleUntil, s.beam = false, nil, nil
		end
		local eye = Fight.eye(f)
		if w.hold == "blow" then
			if s.down and s.fuel > 0 then
				s.fuel = math.max(0, s.fuel - dt)
				if s.fuel <= 0 then fx(f, "blow", { on = false }) end
				if eye and n >= s.next then
					s.next = math.max(s.next, n - w.tick) + w.tick
					for _, h in inCone(f, eye, s.look, w.range, w.cone) do
						local last = s.lastHit[h.t]
						if last and n - last < 0.075 then continue end
						s.lastHit[h.t] = n
						local away = h.c - eye
						away = if away.Magnitude > 1e-3 then away.Unit else Vector3.yAxis
						Fight.hurt(h.t, if math.random() < 0.3 then 1 else 0, f, s.wid, false, away * w.push + Vector3.new(0, w.pushUp, 0), h.c)
					end
				end
			elseif not s.down then
				s.fuel = math.min(w.fuel, s.fuel + w.regen * dt)
			end
		elseif w.hold == "breath" then
			if s.down and not s.coughed and n - s.t0 > w.coughAt then
				s.coughed, s.down = true, false
				if f.kind == "player" then (f.ref :: Player):SetAttribute("Swig", nil) end
				Fight.hurt(f, w.cough or 12, nil, s.wid, false, nil, nil, nil, true)
				fx(f, "cough", {})
			end
			if s.exhaleUntil then
				if n >= s.exhaleUntil or not alive then
					s.exhaleUntil = nil
					fx(f, "breath", { on = false })
				elseif eye and n >= s.next then
					s.next = math.max(s.next, n - w.tick) + w.tick
					for _, h in inCone(f, eye, s.look, w.range, w.cone) do
						local last = s.lastHit[h.t]
						if last and n - last < 0.075 then continue end
						s.lastHit[h.t] = n
						Fight.hurt(h.t, w.dmg, f, s.wid, false, Vector3.new(s.look.X * w.kb, w.kbUp, s.look.Z * w.kb), h.c)
					end
				end
			end
		elseif w.hold == "beam" and s.beam then
			local bm = s.beam :: { k: number, untilT: number }
			if n >= bm.untilT or not alive then
				s.beam = nil
			elseif eye and n >= s.next then
				s.next = math.max(s.next, n - w.tick) + w.tick
				local k = bm.k
				local r = w.r[1] + (w.r[2] - w.r[1]) * k
				local hit = Fight.castMap(eye, s.look, w.range)
				local len = if hit then (hit.Position - eye).Magnitude else w.range
				local dmg = w.dmgK[1] + (w.dmgK[2] - w.dmgK[1]) * k
				local kb = w.kbK[1] + (w.kbK[2] - w.kbK[1]) * k
				for _, t in Fight.all do
					if t == f or not t.alive or not Fight.allow(f, t) then continue end
					if t.onlyFor ~= nil and t.onlyFor ~= f.ref then continue end
					local ft = Fight.feet(t)
					if not ft then continue end
					-- (the beam goes through people: every box it touches, grown by its radius, is hit)
					local tt = Hitbox.ray(eye, s.look, ft, Hitbox.distScale((ft - eye).Magnitude), r)
					if tt and tt <= len then
						Fight.hurt(t, dmg, f, s.wid, false, s.look * kb + Vector3.new(0, w.kbUp, 0), eye + s.look * tt)
					end
				end
				fx(f, "beam", { a = eye, b = eye + s.look * len, kq = k }) -- (kq: the charge; k is the event's name)
			end
		end
	end
end)
