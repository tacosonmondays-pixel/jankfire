--!strict
-- the katana's moves on top of its guard (owner, 18 Nov 2026: "allow katana parry to parry as many bullets but if you
-- manually swing it to counter bullets it does a crit return! build enough parry and you can send a large forward
-- slash"). numbers in Weapons (PARRY, CRIT, EDGE, WAVE), the write-up in docs/KATANA.md. the server decides all of it;
-- clients only show it (Katana.client.luau):
--   the held guard     Rules.parryStart / parryStop / parryTurn / parryAt, from Combat's Parry remote
--   the crit return    Rules.critAt in Combat's applyHitscan -> Katana.crit: the same bullets go home x CRIT.mul,
--                      credited to the katana ("parry", as a perfect parry's are)
--   the edge meter     Katana.charge: every hit you parry or send back fills it (player attributes Edge 0..1, EdgeFull)
--   the slash wave     the KatanaWave remote with a full meter: a crescent the server flies itself (Katana.step),
--                      Fx "wave" / "waveHit" / "waveEnd" for everyone's screens; its kills are the katana's
-- Studio only: ServerStorage.JankKatanaTest (BindableFunction), see the end of the file
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Zones = require(script.Parent:WaitForChild("Zones"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local ShotR = Remotes:WaitForChild("Shot") :: RemoteEvent
-- the wave's key press (made here when the place doesn't have it yet: default.project.json lists it too)
local WaveR = Remotes:FindFirstChild("KatanaWave") :: RemoteEvent?
if not WaveR then
	local r = Instance.new("RemoteEvent")
	r.Name = "KatanaWave"
	r.Parent = Remotes
	WaveR = r
end

type Fighter = Rules.Fighter
local W = Weapons.list
local E, C, WV = Weapons.EDGE, Weapons.CRIT, Weapons.WAVE
local now = os.clock

local Katana = {}
local Fight: any = nil
local applyHitscan: any = nil

local function uid(f: Fighter): number? return if f.kind == "player" then (f.ref :: Player).UserId else nil end
local function chest(f: Fighter): Vector3? local r = Fight.root(f); return r and r.Position end
local function callout(f: Fighter, text: string, dur: number)
	if f.kind == "player" then CalloutR:FireClient(f.ref :: Player, text, dur) end
end
local function finiteV(v: any): boolean
	return typeof(v) == "Vector3" and Rules.finite(v.X) and Rules.finite(v.Y) and Rules.finite(v.Z) and v.Magnitude < 1e6
end

-- what happened, for the Studio test hook (the last 120 events)
local LOG: { { any } } = {}
local function log(...: any)
	if not RunService:IsStudio() then return end
	table.insert(LOG, { math.floor(now() * 1000) / 1000, ... })
	if #LOG > 120 then table.remove(LOG, 1) end
end

-- ------------------------------------------------------------------ the edge meter
-- shown to its player as attributes: Edge (0..1, two places) and EdgeFull. only players fill one
local function publish(f: Fighter)
	if f.kind ~= "player" then return end
	local p = f.ref :: Player
	local e = f.edge or 0
	local q = math.floor(math.clamp(e / E.max, 0, 1) * 100 + 0.5) / 100
	if p:GetAttribute("Edge") ~= q then p:SetAttribute("Edge", q) end
	local full = e >= E.max
	if (p:GetAttribute("EdgeFull") == true) ~= full then p:SetAttribute("EdgeFull", full) end
end
Katana.publish = publish

-- t parried (or sent back) something worth `pts` from `by`. nothing for a hit `by` wasn't allowed to land anyway (a
-- teammate's). x EDGE.train in training, so the owner can try the wave without a long fight
function Katana.charge(t: Fighter, by: Fighter?, pts: number)
	if t.kind ~= "player" or not t.alive or not (pts > 0) then return end
	if by and by ~= t and not Fight.allow(by, t) then return end
	local mul = if Zones.training(t.ref :: Player) then E.train else 1
	local was = t.edge or 0
	t.edge = math.min(E.max, was + pts * mul)
	publish(t)
	if was < E.max and (t.edge :: number) >= E.max then log("full", t.name) end
end

-- ------------------------------------------------------------------ the crit return
-- t's swing met f's bullets (Rules.critAt): no damage to t, the same bullets go back into f at CRIT.mul x (a Sniper
-- headshot stays lethal), credited to t's katana. everyone sees the sharp flash and the line home
function Katana.crit(t: Fighter, f: Fighter, wid: string, n: number, h: number, eye: Vector3)
	local w = W[wid]
	if not w then return end
	local base = Weapons.damage(w, n, h)
	local from = chest(t) or eye
	FxR:FireAllClients({ k = "crit", model = Fight.model(t), by = uid(t), att = uid(f), from = from, to = eye, w = wid })
	local back = base * C.mul
	local done = 0
	if f.alive then
		if w.lethalHead and h > 0 then back = math.max(back, f.hp) end
		done = Fight.hurt(f, back, t, "parry", h > 0, nil, eye)
	end
	callout(t, "CRIT RETURN", 0.9)
	Katana.charge(t, f, base * E.crit)
	log("crit", t.name, f.name, wid, n, back, done)
end

-- ------------------------------------------------------------------ the slash wave
type Wave = {
	id: number, f: Fighter, from: Vector3, dir: Vector3, right: Vector3, up: Vector3, len: number, wall: boolean,
	go: number, d: number, hit: { [Fighter]: boolean }, n: number,
}
local waves: { Wave } = {}
local nextId = 0
local lastPress: { [Player]: number } = {}
Players.PlayerRemoving:Connect(function(p) lastPress[p] = nil end)

-- the look, its pitch kept within +-WAVE.pitch
local function aimDir(look: Vector3): Vector3?
	local u = look.Unit
	local flat = Vector3.new(u.X, 0, u.Z)
	if flat.Magnitude < 1e-3 then return nil end
	local lim = math.rad(WV.pitch)
	local pitch = math.clamp(math.asin(math.clamp(u.Y, -1, 1)), -lim, lim)
	return (flat.Unit * math.cos(pitch) + Vector3.new(0, math.sin(pitch), 0)).Unit
end

local function finish(wv: Wave, why: string, at: Vector3?)
	local i = table.find(waves, wv)
	if i then table.remove(waves, i) end
	local p = at or (wv.from + wv.dir * wv.d)
	FxR:FireAllClients({ k = "waveEnd", id = wv.id, at = p, d = (p - wv.from):Dot(wv.dir), why = why })
	log("waveEnd", wv.id, why, math.floor((p - wv.from):Dot(wv.dir) * 10) / 10, wv.n)
end

-- send f's wave along dir (the checks are the remote's). why not, or nil
function Katana.cast(f: Fighter, look: Vector3, free: boolean?): string?
	local t = now()
	if not f.alive then return "dead" end
	if f.held ~= "katana" then return "no katana" end
	if Fight.holstered(f) then return "holstered" end
	if not free and (f.edge or 0) < E.max then return "not charged" end
	if t < f.staggerUntil then return "staggered" end
	if Rules.parryOpen(f, t) then return "guarding" end
	if f.castUntil and t < f.castUntil then return "casting" end
	if f.swing and t - f.swing.t < W.katana.hitT :: number then return "mid-swing" end
	local dir = aimDir(look)
	local root = Fight.root(f)
	if not dir or not root then return "no aim" end
	f.edge = 0
	publish(f)
	f.castUntil = t + WV.lock
	nextId += 1
	-- it leaves from the chest, a stride ahead (or the wall right in front of you, if that's nearer)
	local o = root.Position
	local lead = 1.5
	local near = Fight.castMap(o, dir, lead)
	local from = if near then near.Position - dir * 0.2 else o + dir * lead
	local right = dir:Cross(Vector3.yAxis)
	right = if right.Magnitude > 1e-3 then right.Unit else Vector3.xAxis
	local up = right:Cross(dir).Unit
	local hitWall = if near then near else Fight.castMap(from, dir, WV.range)
	local len = if near then 0 elseif hitWall then (hitWall.Position - from).Magnitude else WV.range
	local wv: Wave = {
		id = nextId, f = f, from = from, dir = dir, right = right, up = up, len = len, wall = hitWall ~= nil,
		go = t + WV.windup, d = 0, hit = {}, n = 0,
	}
	table.insert(waves, wv)
	FxR:FireAllClients({
		k = "wave", id = wv.id, model = Fight.model(f), by = uid(f), from = from, dir = dir, len = len, speed = WV.speed,
		wall = wv.wall, normal = if hitWall then hitWall.Normal else nil, t0 = workspace:GetServerTimeNow() + WV.windup,
	})
	-- everyone else sees the slash on your body (ThirdPerson's "swing"), the match recorder keeps it for killcams
	FxR:FireAllClients({ k = "swing", model = Fight.model(f), w = "katana", by = uid(f) })
	Fight.shotFx(f, "katana", nil, "swing")
	log("wave", f.name, wv.id, math.floor(len * 10) / 10)
	return nil
end

-- one server step for every wave in the air: the slab it swept this step hurts whoever is in it (once each), a guard
-- in front of it breaks it, the wall at the end of its line stops it
local PAD = 0.6 * Weapons.S -- (a body's half width)
function Katana.step()
	local t = now()
	for i = #waves, 1, -1 do
		local wv = waves[i]
		if t < wv.go then continue end
		local d0 = wv.d
		local d1 = math.min(wv.len, (t - wv.go) * WV.speed)
		wv.d = d1
		local stop: string? = nil
		local stopAt: Vector3? = nil
		-- who's inside the slab between d0 and d1 (nearest first, so the pierce count goes in flight order)
		local inside: { { f: Fighter, along: number, p: Vector3 } } = {}
		for _, o in Fight.all do
			if o == wv.f or not o.alive or wv.hit[o] then continue end
			local c = chest(o)
			if not c then continue end
			local rel = c - wv.from
			local along = rel:Dot(wv.dir)
			if along < d0 - PAD or along > d1 + PAD then continue end
			if math.abs(rel:Dot(wv.right)) > WV.width / 2 + PAD or math.abs(rel:Dot(wv.up)) > WV.height / 2 then continue end
			if not Fight.allow(wv.f, o) then continue end
			-- (not through a pillar at the crescent's edge: the line from the wave's middle must be clear)
			local mid = wv.from + wv.dir * math.clamp(along, 0, wv.len)
			local to = c - mid
			if to.Magnitude > 0.3 and Fight.castMap(mid, to.Unit, to.Magnitude) then continue end
			table.insert(inside, { f = o, along = along, p = c })
		end
		table.sort(inside, function(a, b) return a.along < b.along end)
		for _, x in inside do
			local o = x.f
			wv.hit[o] = true
			-- a guard (or a swing) facing it breaks the wave there: no damage, and the guard's meter fills
			local inc = -wv.dir * 10
			local pr = Rules.parryAt(o, inc, Fight.facing(o), t)
			local cut = pr == 0 and Rules.critAt(o, inc, Fight.facing(o), t)
			if pr > 0 or cut then
				FxR:FireAllClients({ k = "parry", model = Fight.model(o), by = uid(o), att = uid(wv.f), pf = pr == 2, kind = "wave", from = x.p, n = o.parryN })
				callout(o, "PARRY!", 0.8)
				Katana.charge(o, wv.f, WV.dmg * 0.5 * (if cut then E.crit elseif pr == 2 then E.perfect else E.block))
				stop, stopAt = "guard", wv.from + wv.dir * x.along
				log("waveParried", wv.id, o.name)
				break
			end
			local flat = Vector3.new(wv.dir.X, 0, wv.dir.Z)
			local kb = (if flat.Magnitude > 1e-3 then flat.Unit else wv.dir) * WV.kb + Vector3.new(0, WV.kbUp, 0)
			local done = Fight.hurt(o, WV.dmg, wv.f, "katana", false, kb, x.p)
			FxR:FireAllClients({ k = "waveHit", id = wv.id, model = Fight.model(o), at = x.p })
			wv.n += 1
			log("waveHit", wv.id, o.name, done, o.alive)
			if wv.n >= WV.pierce then stop, stopAt = "pierce", wv.from + wv.dir * x.along; break end
		end
		if not stop and d1 >= wv.len then stop = if wv.wall then "wall" else "range" end
		if stop then finish(wv, stop, stopAt) end
	end
end

-- the key (the client's look): checked here, the meter must be full
local function onWave(p: Player, look: unknown)
	local t = now()
	if t - (lastPress[p] or -math.huge) < 0.2 then return end
	lastPress[p] = t
	if not finiteV(look) then return end
	local lk = look :: Vector3
	if lk.Magnitude < 0.5 or lk.Magnitude > 1.5 then return end
	local f = Fight.byPlayer[p]
	if not f then return end
	local why = Katana.cast(f, lk)
	if why then log("waveRefused", p.Name, why) end
end

-- ------------------------------------------------------------------ wiring
function Katana.init(fight: any, apply: any)
	Fight, applyHitscan = fight, apply
	;(WaveR :: RemoteEvent).OnServerEvent:Connect(onWave)
	RunService.Heartbeat:Connect(Katana.step)
	-- a fresh life starts with an empty meter (Rules.spawn zeroes it; this shows it), a death empties it
	Fight.onSpawn(function(f: Fighter) f.edge = 0; publish(f) end)
	Fight.onKill(function(info: any)
		local v = info.v
		v.edge = 0
		v.castUntil = nil
		publish(v)
	end)
	if RunService:IsStudio() then Katana.testHook() end
end

-- ------------------------------------------------------------------ Studio play tests
--   local K = game.ServerStorage.JankKatanaTest
--   K:Invoke("state", player)      -> { edge, max, full, open, parryT, parryEnd, ready, castUntil, swingT, waves }
--   K:Invoke("edge", player, pts)  -> sets the meter (points; EDGE.max = full)
--   K:Invoke("spray", player, { by = "Plinker", w = "smg", n = 24, rate = 16, h = 0, at = <fighter name> })
--       a stand-in shooter: the dummy `by` fires n shots of weapon w at the player (or `at`) through the real hitscan
--       path (guard, crit, meter), tracers for everyone; returns at once
--   K:Invoke("cast", player, look)  -> the wave from the server's side (no meter needed), why not or nil
--   K:Invoke("log", "clear"?)      -> the last events { t, kind, ... } (and empties it)
function Katana.testHook()
	local old = ServerStorage:FindFirstChild("JankKatanaTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankKatanaTest"
	local function byName(n: any): Fighter?
		for _, f in Fight.all do if f.name == n or Fight.model(f) == n or f.ref == n then return f end end
		return nil
	end
	fn.OnInvoke = function(op: any, a: any, b: any): any
		local f = if typeof(a) == "Instance" and a:IsA("Player") then Fight.byPlayer[a] else nil
		local t = now()
		if op == "state" then
			if not f then return nil end
			return {
				edge = f.edge or 0, max = E.max, full = (f.edge or 0) >= E.max, open = Rules.parryOpen(f, t),
				parryT = f.parryT - t, parryEnd = if f.parryEnd then f.parryEnd - t else nil, ready = Rules.parryReady(f) - t,
				castUntil = if f.castUntil then f.castUntil - t else nil, swingT = if f.swing then f.swing.t - t else nil,
				swingYaw = if f.swing then f.swing.yaw else nil, parryN = f.parryN, hp = f.hp, waves = #waves, held = f.held,
			}
		elseif op == "edge" then
			if not f or type(b) ~= "number" then return false end
			f.edge = math.clamp(b, 0, E.max)
			publish(f)
			return true
		elseif op == "cast" then
			if not f or typeof(b) ~= "Vector3" then return "no look" end
			return Katana.cast(f, b, true)
		elseif op == "log" then
			local out = table.clone(LOG)
			if b == "clear" or a == "clear" then table.clear(LOG) end
			return out
		elseif op == "spray" then
			local o = if type(b) == "table" then b else {}
			local shooter = byName(o.by or "Plinker")
			local target = if o.at then byName(o.at) else f
			local w = W[o.w or "smg"]
			if not shooter or not target or not w then return false, "no shooter / target / weapon" end
			local n, rate = tonumber(o.n) or 20, tonumber(o.rate) or (w.rate or 10)
			task.spawn(function()
				for _ = 1, n do
					if not shooter.alive or not target.alive then break end
					local e, c = Fight.eye(shooter), chest(target)
					if not e or not c then break end
					applyHitscan(shooter, target, o.w or "smg", w.pellets or 1, math.min(tonumber(o.h) or 0, w.pellets or 1), e)
					for _, pl in Players:GetPlayers() do ShotR:FireClient(pl, { model = Fight.model(shooter), w = o.w or "smg", ends = { c } }) end
					task.wait(1 / rate)
				end
			end)
			return true
		end
		return nil
	end
	fn.Parent = ServerStorage
end

return Katana
