--!strict
-- the Scythe's dash (the owner, 18 Nov 2026: "Bring scythe in as a weapon, balance it especially its dash"; WEAPONS.md
-- "Scythe"). right click with the scythe out: the server checks it (yours, out, alive, not stunned or mid-swing, a
-- charge left), finds the path (flat along your look, dash.dist studs, stopped short of a wall), hands it to your
-- client to run (DashV / DashUntil on you; ACGrace so the anti-cheat lets the burst through) and cuts the first enemy
-- within dash.width of that path: dash.dmg and a shove along it. a katana guard facing the dash parries it: no damage,
-- you're staggered instead. no invulnerability; after it, dash.recover s with no swing, guard or dash
-- (the owner, later on 18 Nov: "the dash can you get two charges like tracer, a kill recharges the dash like genji, the
-- dash travels farther!") dash.charges charges, coming back one at a time dash.cd s apart (Tracer's Blink); a kill with
-- the Scythe in either form gives one back at once (Genji's Swift Strike); 12 m (was 8). the count is the server's, on
-- the player: DashN (charges left), DashT0 (server time the one coming back started; 0 = full), DashRefundT (server
-- time of the last kill's refund). ScytheDash.client draws them as small circles under the crosshair
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local DashR = Remotes:FindFirstChild("Dash") :: RemoteEvent?
if not DashR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Dash"
	r.Parent = Remotes
	DashR = r
end
local W = Weapons.list
local now = os.clock
local function snow(): number return workspace:GetServerTimeNow() end
local _ = Players
local SCY = (W :: any).scythe.dash -- (the charges are the Scythe's: they count on through its rifle form)

-- ------------------------------------------------------------------ the charges (server time)
type Charge = { n: number, t0: number? } -- left; when the one coming back started (nil = full)
local charges: { [any]: Charge } = setmetatable({}, { __mode = "k" }) :: any
local MAX = SCY.charges or 1
local function update(c: Charge, sn: number)
	while c.n < MAX and c.t0 ~= nil and sn - (c.t0 :: number) >= SCY.cd do
		c.n += 1
		c.t0 = if c.n < MAX then (c.t0 :: number) + SCY.cd else nil
	end
end
local function publish(f: Rules.Fighter, c: Charge)
	if f.kind ~= "player" then return end
	local p = f.ref :: Player
	p:SetAttribute("DashN", c.n)
	p:SetAttribute("DashT0", c.t0 or 0)
end
local function chargeOf(f: Rules.Fighter): Charge
	local c = charges[f]
	if not c then c = { n = MAX, t0 = nil }; charges[f] = c end
	update(c, snow())
	return c
end
-- (Studio play tests) the last dashes and refunds
local log: { any } = {}
local function note(e: any)
	table.insert(log, e)
	if #log > 20 then table.remove(log, 1) end
end

-- a fresh life starts full
Fight.onSpawn(function(f: Rules.Fighter)
	local c = { n = MAX, t0 = nil }
	charges[f] = c
	publish(f, c)
end)
-- a kill with the Scythe (either form; a fall it knocked them into too) gives a charge back at once
Fight.onKill(function(info: Rules.KillInfo)
	local k = info.k
	if not k or not k.alive then return end
	local w = if info.w == "void" then info.via else info.w
	if type(w) ~= "string" or Weapons.base(w) ~= "scythe" then return end
	local c = chargeOf(k)
	if c.n >= MAX then return end
	c.n += 1
	if c.n >= MAX then c.t0 = nil end
	publish(k, c)
	if k.kind == "player" then (k.ref :: Player):SetAttribute("DashRefundT", snow()) end
	note({ k = "refund", by = k.name, v = info.v.name, w = info.w, n = c.n, t = snow() })
end)

;(DashR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, look: unknown)
	if (p:GetAttribute("Zone") == "hub" and p:GetAttribute("DevArms") ~= true) or typeof(look) ~= "Vector3" then return end
	local f = Fight.byPlayer[p]
	if not f or not f.alive then return end
	local wid = f.held
	local w = W[wid] :: any
	local D = w and w.dash
	if not D then return end
	local n = now()
	if n < f.staggerUntil or (f.castUntil and n < f.castUntil) or Rules.parryOpen(f, n) or Rules.transforming(f, n) then return end
	local c = chargeOf(f)
	if c.n <= 0 then return end -- (none left: the next comes back SCY.cd s after the last one started)
	local root = Fight.root(f)
	if not root then return end
	local flat = Vector3.new((look :: Vector3).X, 0, (look :: Vector3).Z)
	if flat.Magnitude < 0.2 then flat = Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z) end
	flat = flat.Unit
	-- the path: from the chest along the look, short of any wall in the way (a body's width back from it)
	local from = root.Position
	local len = D.dist
	local hit = Fight.castMap(from, flat, len + 2)
	if hit then len = math.max(0, (hit.Position - from).Magnitude - 2) end
	local to = from + flat * len
	-- spend the charge: the one coming back starts now if none was
	local sn = snow()
	c.n -= 1
	if c.t0 == nil then c.t0 = sn end
	publish(f, c)
	note({ k = "dash", by = f.name, from = from, to = to, len = len, n = c.n, t = sn })
	f.castUntil = n + D.time + D.recover -- (no swing or guard through the dash and its recovery)
	p:SetAttribute("ACGrace", n + D.time + 0.4) -- (the anti-cheat: this burst is the server's say)
	p:SetAttribute("DashV", flat * (len / D.time))
	p:SetAttribute("DashUntil", workspace:GetServerTimeNow() + D.time)
	FxR:FireAllClients({ k = "dash", model = Fight.model(f), a = from, b = to })
	-- (the owner, 18 Nov 2026: "if you make any contact while dashing it auto latches and does that kick back") the dash
	-- feels for contact the whole way: every server frame, the stretch of the server's path you covered since the last
	-- one is checked against every enemy body (within D.width of it across, under 4 studs up or down), even one that
	-- steps in mid-dash or that you only brush past. the first contact is the dash's one hit
	local done1 = false
	local prev = from
	local conn: RBXScriptConnection? = nil
	local function contact(t: Rules.Fighter, tr: BasePart, at: Vector3, side: number)
		done1 = true
		if conn then conn:Disconnect() end
		local nn = now()
		note({ k = "contact", by = f.name, v = t.name, at = at, side = side, el = nn - n, t = snow() })
		-- a katana guard facing the dash stops it: you're staggered and shoved back off it (the melee parry)
		local pr = Rules.parryAt(t, at - tr.Position, Fight.facing(t), nn)
		if pr > 0 then
			p:SetAttribute("DashUntil", workspace:GetServerTimeNow())
			local dv = p:GetAttribute("DashV")
			if typeof(dv) == "Vector3" then Fight.knock(f, -(dv :: Vector3), "parry") end
			local shove = Rules.stagger(f, at - tr.Position, pr == 2, nn)
			Fight.knock(f, shove, "parry")
			Rules.tagged(f, t, "parry", nn)
			FxR:FireAllClients({ k = "parry", model = Fight.model(t), by = if t.kind == "player" then (t.ref :: Player).UserId else nil, att = p.UserId, pf = pr == 2, kind = "melee", st = f.staggerUntil - nn, from = tr.Position })
			if t.kind == "player" then CalloutR:FireClient(t.ref :: Player, if pr == 2 then "PERFECT PARRY!" else "PARRY!", 0.9) end
			CalloutR:FireClient(p, "PARRIED", 0.8)
			return
		end
		if not w.latch then
			Fight.hurt(t, D.dmg, f, wid, false, flat * D.kb + Vector3.new(0, D.kbUp, 0), tr.Position)
			return
		end
		-- (the latch, ScytheLatch: the owner's "latch on and send you back") the dash stops on them: it ends here and its
		-- speed is taken back off you, the blade holds them for the latch's beat, then the two spring apart
		local dv = p:GetAttribute("DashV")
		p:SetAttribute("DashUntil", workspace:GetServerTimeNow())
		if typeof(dv) == "Vector3" then Fight.knock(f, -(dv :: Vector3), wid) end
		p:SetAttribute("ACGrace", nn + w.latch.t + 0.7)
		f.castUntil = math.max(f.castUntil or 0, nn + w.latch.t) -- (no swing mid-latch)
		local dealt = Fight.hurt(t, D.dmg, f, wid, false, nil, tr.Position)
		if dealt > 0 then require(script.Parent:WaitForChild("ScytheLatch")).apart(f, { t }, wid, false) end
	end
	local function sweep(): boolean
		local el = now() - n
		local at = from + flat * (len * math.clamp(el / D.time, 0, 1))
		local seg = at - prev
		local sl = seg.Magnitude
		for _, t in Fight.all do
			if t == f or not t.alive or not Fight.allow(f, t) then continue end
			if t.onlyFor ~= nil and t.onlyFor ~= p then continue end
			local tr = Fight.root(t)
			if not tr then continue end
			-- the nearest point of this frame's stretch to them
			local u = if sl > 1e-3 then math.clamp((tr.Position - prev):Dot(seg) / (sl * sl), 0, 1) else 0
			local q = prev + seg * u
			local rel = tr.Position - q
			local side = Vector3.new(rel.X, 0, rel.Z).Magnitude
			if side <= D.width and math.abs(rel.Y) <= 4 then contact(t, tr, q, side); return true end
		end
		prev = at
		return el >= D.time
	end
	if sweep() then return end -- (already touching them as it starts)
	conn = RunService.Heartbeat:Connect(function()
		if done1 or not f.alive then if conn then conn:Disconnect() end return end
		if sweep() and conn then conn:Disconnect() end
	end)
end)

-- ------------------------------------------------------------------ Studio play tests
--   local S = game.ServerStorage.JankScytheTest
--   S:Invoke("state", player)  -> { n, t0, max, cd, now }
--   S:Invoke("fill", player)   -> full charges
--   S:Invoke("set", player, n) -> n charges left, the next one starting to come back now (a refund test)
--   S:Invoke("log", "clear"?)  -> the last dashes { from, to, len, n } and refunds (and empties it)
--   S:Invoke("latch")          -> the last latches (ScytheLatch.log: the pushes sent, the room found)
if RunService:IsStudio() then
	local ServerStorage = game:GetService("ServerStorage")
	local old = ServerStorage:FindFirstChild("JankScytheTest")
	if old then old:Destroy() end
	local bf = Instance.new("BindableFunction")
	bf.Name = "JankScytheTest"
	bf.OnInvoke = function(what: string, a: any, b: any): any
		if what == "latch" then return table.clone(require(script.Parent:WaitForChild("ScytheLatch")).log) end
		if what == "log" then
			local out = table.clone(log)
			if a == "clear" then table.clear(log) end
			return out
		end
		local f = if typeof(a) == "Instance" then Fight.byPlayer[a :: Player] else nil
		if not f then return nil end
		local c = chargeOf(f)
		if what == "fill" then c.n, c.t0 = MAX, nil; publish(f, c) end
		if what == "set" and type(b) == "number" then
			c.n = math.clamp(math.floor(b), 0, MAX)
			c.t0 = if c.n < MAX then snow() else nil
			publish(f, c)
		end
		return { n = c.n, t0 = c.t0, max = MAX, cd = SCY.cd, now = snow() }
	end
	bf.Parent = ServerStorage
end
