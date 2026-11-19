--!strict
-- the Overdrive Rig as a gadget (the owner, 19 Nov 2026: "can you add the overdrive's rocket punch again as a melee or a
-- gadget? I want the ability to still shoot out missiles!"; main: a UTILITY gadget on G; WEAPONS.md "Overdrive Rig",
-- web server/rig.js). G suits you up: armour on top of your HP for R.dur s or until it breaks. while it's on your guns,
-- melee and other items are off (Rules refuses them; Arsenal routes your buttons to RigClient):
--   LMB  the ROCKET PUNCH: hold to charge (R.punch.charge s), let go: a dash along your look (the Scythe's dash: DashV /
--        DashUntil on you, your client runs it, ACGrace for the anti-cheat) and the fist smashes everyone in its path
--        once, line of sight: damage, a shove along it. bigger with the charge
--   RMB  MISSILES: R.miss.n rockets out of the left forearm's rack, up for a moment, then homing-lite on the best targets
--        ahead (WeaponProj kind "rigmissile", fired through ServerStorage.JankRigVolley); each one a small blast
-- the armour takes every hit first (Fight.rigSoak, called by Fight.hurt) and drains R.drain a second; knockback on you
-- is cut to R.kbTake (Fight.knock). it ends at 0 armour (it bursts: "rigoff" brk), at R.dur s, or when you die.
-- a ModuleScript: the gadget (Utility.use, utility-slot's) calls Rig.start(f) and Rig.on(f); RigServer.server
-- requires it at server start so the remote and the clock run from the first frame. a Studio test can also use the
-- server-only BindableFunction ServerStorage.JankRig: Invoke("start", player) -> true | false, why; Invoke("on", player)
-- the player's attributes (everyone sees them): Rig = server time it ends; RigArmour; RigCharge = server time the
-- punch charge began (while held); RigPunchT / RigMissT = server times of the last punch / salvo
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local RigR = Remotes:FindFirstChild("Rig") :: RemoteEvent?
if not RigR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Rig"
	r.Parent = Remotes
	RigR = r
end

local S = Weapons.S
type Fighter = Rules.Fighter
local now = os.clock
local function snow(): number return workspace:GetServerTimeNow() end

-- the numbers (rebalanced from the web killstreak for a gadget and our 100 HP: WEAPONS.md "Overdrive Rig")
local R = {
	dur = 12, armour = 120, drain = 4, kbTake = 0.4,
	punch = {
		charge = 0.9, cd = 0.6,
		dmg = { 35, 75 }, dist = { 3.5 * S, 10 * S }, speed = 40 * S,
		kb = { 28 * S, 60 * S }, up = { 7 * S, 12 * S },
		width = 1.35 * S, -- (how far off the fist's path a body is still hit)
	},
	miss = {
		n = 4, cd = 5, cone = 0.4, range = 75 * S, targets = 2,
	},
}

type St = { untilT: number, armour: number, chargeT: number?, punchT: number, missT: number }
local state: { [Fighter]: St } = {}

local function playerOf(f: Fighter): Player? return if f.kind == "player" then f.ref :: Player else nil end
local function setAttr(f: Fighter, k: string, v: any) local p = playerOf(f); if p then p:SetAttribute(k, v) end end

local function stop(f: Fighter, brk: boolean)
	local st = state[f]
	if not st then return end
	state[f] = nil
	;(f :: any).rigUntil = nil
	setAttr(f, "Rig", nil); setAttr(f, "RigArmour", nil); setAttr(f, "RigCharge", nil)
	FxR:FireAllClients({ k = "rigoff", model = Fight.model(f), brk = brk or nil })
end

local function start(f: Fighter): (boolean, string?)
	if not f.alive then return false, "dead" end
	if state[f] then return false, "already on" end
	local t = now()
	state[f] = { untilT = t + R.dur, armour = R.armour, chargeT = nil, punchT = -math.huge, missT = -math.huge }
	;(f :: any).rigUntil = t + R.dur
	setAttr(f, "Rig", snow() + R.dur)
	setAttr(f, "RigArmour", R.armour)
	FxR:FireAllClients({ k = "rigon", model = Fight.model(f) })
	return true, nil
end

-- every hit on a rigged body: the armour takes it first (Fight.hurt calls this); what's left reaches your HP
Fight.rigSoak = function(t: Fighter, amt: number, _by: Fighter?, _wid: string): number
	local st = state[t]
	if not st or amt <= 0 then return amt end
	local take = math.min(st.armour, amt)
	st.armour -= take
	setAttr(t, "RigArmour", math.floor(st.armour + 0.5))
	if st.armour <= 0 then stop(t, true) end
	return amt - take
end
Fight.rigKb = R.kbTake -- (Fight.knock: knockback on a rigged body)

-- ------------------------------------------------------------------ the rocket punch
local function punch(p: Player, f: Fighter, look: Vector3)
	local st = state[f]
	if not st then return end
	local t = now()
	if t - st.punchT < R.punch.cd * 0.85 then return end
	local root = Fight.root(f)
	if not root then return end
	-- the charge: from when the server saw LMB go down (RigCharge), never from the client's say
	local c = if st.chargeT then math.clamp((t - st.chargeT) / R.punch.charge, 0, 1) else 0
	st.chargeT = nil
	setAttr(f, "RigCharge", nil)
	st.punchT = t
	local P = R.punch
	local function lerp(a: { number }): number return a[1] + (a[2] - a[1]) * c end
	local flat = Vector3.new(look.X, 0, look.Z)
	if flat.Magnitude < 0.05 then flat = Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z) end
	flat = flat.Unit
	-- the path: from the chest along your look (flat), short of the first wall
	local from = root.Position
	local len = lerp(P.dist)
	local hit = Fight.castMap(from, flat, len + 2)
	if hit then len = math.max(0, math.min(len, (hit.Position - from).Magnitude - 2)) end
	local dur = math.max(0.05, len / P.speed)
	local to = from + flat * len
	local p0 = playerOf(f)
	if p0 then
		p0:SetAttribute("ACGrace", t + dur + 0.5) -- (the anti-cheat: this burst is the server's say)
		p0:SetAttribute("DashV", flat * (len / dur))
		p0:SetAttribute("DashUntil", snow() + dur)
		p0:SetAttribute("RigPunchT", snow())
	end
	f.castUntil = t + dur -- (nothing else mid-dash)
	FxR:FireAllClients({ k = "rigpunch", model = Fight.model(f), from = from, to = to, c = c })
	-- the fist sweeps the path every server frame: everyone it passes within the width, once each, in sight
	local dmg, kb, up = lerp(P.dmg), lerp(P.kb), lerp(P.up)
	local seen: { [Fighter]: boolean } = {}
	local prev = from
	local conn: RBXScriptConnection? = nil
	conn = RunService.Heartbeat:Connect(function()
		local el = now() - t
		local at = from + flat * (len * math.clamp(el / dur, 0, 1))
		local seg = at - prev
		local sl = seg.Magnitude
		for _, v in Fight.all do
			if v == f or seen[v] or not v.alive or not Fight.allow(f, v) then continue end
			if v.onlyFor ~= nil and v.onlyFor ~= p then continue end
			local vr = Fight.root(v)
			if not vr then continue end
			local u = if sl > 1e-3 then math.clamp((vr.Position - prev):Dot(seg) / (sl * sl), 0, 1) else 0
			local q = prev + seg * u
			local rel = vr.Position - q
			if Vector3.new(rel.X, 0, rel.Z).Magnitude <= P.width + 1.5 and math.abs(rel.Y) <= 4.5 and Fight.sees(q, v) then
				seen[v] = true
				Fight.hurt(v, dmg, f, "rig_punch", false, flat * kb + Vector3.new(0, up, 0), vr.Position)
				FxR:FireAllClients({ k = "rigpunchhit", model = Fight.model(v), at = vr.Position, c = c })
			end
		end
		prev = at
		if el >= dur or not f.alive or not state[f] then if conn then conn:Disconnect() end end
	end)
end

-- ------------------------------------------------------------------ the missiles
local Volley = ServerStorage:WaitForChild("JankRigVolley", 30) :: BindableEvent?
local function missiles(p: Player, f: Fighter, look: Vector3)
	local st = state[f]
	if not st then return end
	local t = now()
	if t - st.missT < R.miss.cd * 0.9 then return end
	local eye = Fight.eye(f)
	if not eye then return end
	st.missT = t
	p:SetAttribute("RigMissT", snow())
	-- the best targets ahead: in the cone, in range, in sight, scored by angle and distance (web rig.js missile)
	local M = R.miss
	local cands: { { v: Fighter, s: number } } = {}
	for _, v in Fight.all do
		if v == f or not v.alive or not Fight.allow(f, v) then continue end
		if v.onlyFor ~= nil and v.onlyFor ~= p then continue end
		local vr = Fight.root(v)
		if not vr then continue end
		local to = vr.Position - eye
		local d = to.Magnitude
		if d > M.range or d < 1 then continue end
		local dot = look:Dot(to.Unit)
		if dot < M.cone or not Fight.sees(eye, v) then continue end
		table.insert(cands, { v = v, s = dot * 2 - d / M.range })
	end
	table.sort(cands, function(a, b) return a.s > b.s end)
	local models: { Instance } = {}
	for i = 1, math.min(M.targets, #cands) do
		local m = Fight.model(cands[i].v)
		if m then table.insert(models, m) end
	end
	if Volley then Volley:Fire(p, eye, look, models) end
end

-- ------------------------------------------------------------------ the remote
;(RigR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, op: unknown, a: unknown)
	local f = Fight.byPlayer[p]
	if not f or not f.alive or not state[f] then return end
	local st = state[f] :: St
	if op == "charge" then
		if a == true then
			if not st.chargeT then st.chargeT = now(); p:SetAttribute("RigCharge", snow()) end
		else
			st.chargeT = nil; p:SetAttribute("RigCharge", nil)
		end
	elseif op == "punch" and typeof(a) == "Vector3" and (a :: Vector3).Magnitude > 0.2 then
		punch(p, f, (a :: Vector3).Unit)
	elseif op == "miss" and typeof(a) == "Vector3" and (a :: Vector3).Magnitude > 0.2 then
		missiles(p, f, (a :: Vector3).Unit)
	end
end)

-- ------------------------------------------------------------------ every frame: drain, time, death
RunService.Heartbeat:Connect(function(dt: number)
	local t = now()
	for f, st in state do
		if not f.alive or not table.find(Fight.all, f) then stop(f, false); continue end
		if t >= st.untilT then stop(f, false); continue end
		local before = math.floor(st.armour + 0.5)
		st.armour -= R.drain * dt
		if st.armour <= 0 then stop(f, true); continue end
		local after = math.floor(st.armour + 0.5)
		if after ~= before then setAttr(f, "RigArmour", after) end
	end
end)
Players.PlayerRemoving:Connect(function(p: Player)
	local f = Fight.byPlayer[p]
	if f and state[f] then state[f] = nil end
end)

-- ------------------------------------------------------------------ the gadget's handle (server only)
local old = ServerStorage:FindFirstChild("JankRig")
if old then old:Destroy() end
local fn = Instance.new("BindableFunction")
fn.Name = "JankRig"
fn.OnInvoke = function(op: any, p: any): any
	local f = if typeof(p) == "Instance" and p:IsA("Player") then Fight.byPlayer[p] else nil
	if op == "on" then return f ~= nil and state[f] ~= nil end
	if op == "start" then
		if not f then return false, "no fighter" end
		return start(f)
	end
	if op == "stop" and f then stop(f, false); return true end
	if op == "R" then return R end
	return nil
end
fn.Parent = ServerStorage

return {
	start = start, -- (f) -> true | false, why
	on = function(f: Fighter): boolean return state[f] ~= nil end,
	stop = function(f: Fighter) stop(f, false) end,
	R = R,
}
