--!strict
-- ZOMBIES: extraction and the intro's timing (27 Nov 2026; roblox/docs/ZOMBIES.md section 4). The owner: "cinematic
-- for zombies mode please!!", "In zombies allow a way to extract!! If you extract at higher floors you can leave and
-- gain rewards". Plugs into Zombies.ext like stages 2 and 3 (installed after ZombieBots; each hook chains on).
--   the intro: the round waits for the film (ZombieCine.client): IntroT0 / IntroLen / IntroWin on the arena model, a
--     shambler's body in ReplicatedStorage.JankfireZmCine for the window shot; everyone skipped = round 1 soon after
--   the offer: the break after round 10, then every 5th, lasts ZM.X.voteS; Y (or EXTRACT) votes; more than half the
--     humans calls it (bots follow the humans)
--   the hold-out: the next round at once, heavier (ext.heavy), endless; the doors on the cheapest way to the zone roll
--     up for free; the bots run for the pad (ext.botGoal). The helicopter is drawn on each client from XT0 (the call's
--     server time) by ZM.heliAt
--   the end (ZM.X.hold s after the call): whoever stands in the zone is out. One human out = the extraction film and
--     ZombieRewards for them; the ones left behind get the normal game over. A wipe first = a normal game over
--   anti-farming: every member's time, time up, time active and damage to zombies (ZombieRewards.track)
-- Test ops (Studio's ServerStorage.JankZombies): "xoffer" (offer now), "xcall" (offer and call now), "xend" (end the
-- hold-out now), "xelig" [false] (the reward checks off/on), "xreal" (grant for real in Studio), "xstate"
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local ZR = require(script.Parent:WaitForChild("ZombieRewards"))

local ZombieExtract = {}
local XC = ZM.X
local now = os.clock
local function srv(): number return workspace:GetServerTimeNow() end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end

function ZombieExtract.install(Z: any)
	local ext, X = Z.ext, Z.X
	local Fight = X.fight()
	local zr = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Zm") :: RemoteEvent

	local function chain(name: string, fn: (...any) -> any)
		local prev = ext[name]
		ext[name] = function(...)
			local r = if prev then prev(...) else nil
			local mine = fn(r, ...)
			if mine ~= nil then return mine end
			return r
		end
	end
	local function humans(g: any): { any }
		local out = {}
		for _, m in g.members do if m.p and m.p.Parent then table.insert(out, m) end end
		return out
	end
	local function attrs(g: any, t: { [string]: any })
		for k, v in t do g.model:SetAttribute(k, v) end
	end
	local function unset(g: any, ...: string)
		for _, k in { ... } do g.model:SetAttribute(k, nil) end
	end
	local function cineFolder(): Folder
		local f = ReplicatedStorage:FindFirstChild("JankfireZmCine")
		if not f then
			f = Instance.new("Folder")
			f.Name = "JankfireZmCine"
			f.Parent = ReplicatedStorage
		end
		return f :: Folder
	end

	-- ------------------------------------------------------------------ the intro
	chain("start", function(_r: any, g: any)
		g.guid = HttpService:GenerateGUID(false)
		g.x = { st = "off", votes = {}, skips = {}, acc = 0 }
		for _, m in g.members do ZR.track(m) end
		local z = XC.zones[g.model.Name]
		if z then g.x.z = z; g.x.pad = ZM.padOf(X.site, z) end
		-- the lobby's first window for the film's second shot, and a shambler's body for it
		local win = nil
		for _, w in g.map.windows do if w.area == g.map.start then win = w.i; break end end
		local f = cineFolder()
		f:ClearAllChildren()
		local tpl = g.templates and g.templates[0]
		if tpl then local c = tpl:Clone(); c.Name = "Zombie"; c.Parent = f end
		g.untilT = now() + XC.intro + 1.5
		attrs(g, { IntroT0 = srv() + 0.4, IntroLen = XC.intro, IntroWin = win })
		return nil
	end)

	-- ------------------------------------------------------------------ the offer, the call
	local function routeOpen(g: any, area: string): { number }
		-- the cheapest way from the open areas to the zone's: open doors cost nothing, shut ones their price
		local dist: { [string]: number }, via: { [string]: { i: number, from: string } }, done: { [string]: boolean } = {}, {}, {}
		for a in g.areas do dist[a] = 0 end
		while true do
			local best, bd = nil, math.huge
			for a, d in dist do if not done[a] and d < bd then best, bd = a, d end end
			if not best then break end
			done[best] = true
			if best == area then break end
			for i, d in g.map.doors do
				local other = if d.a == best then d.b elseif d.b == best then d.a else nil
				if other and not done[other] then
					local c = bd + (if g.open[i] then 0 else d.price)
					if c < (dist[other] or math.huge) then dist[other] = c; via[other] = { i = i, from = best } end
				end
			end
		end
		local opened = {}
		local a = area
		while via[a] do
			local v = via[a]
			if not g.open[v.i] then X.openDoor(g, v.i, nil); table.insert(opened, v.i) end
			a = v.from
		end
		return opened
	end
	local function callIt(g: any, by: string?)
		local x = g.x
		x.st = "hold"
		x.t0, x.s0 = now(), srv()
		g.untilT = now() -- (the next round, the hold-out, starts on the next tick)
		local opened = routeOpen(g, x.z.area)
		attrs(g, { XSt = "hold", XT0 = x.s0, XN = g.n })
		X.sayAll({ k = "xcall", n = g.n, by = by, opened = #opened })
	end
	local function vote(g: any, p: Player)
		local x = g.x
		if not x or x.st ~= "offer" then return end
		x.votes[p.UserId] = true
		local hs = humans(g)
		local yes = 0
		for _, m in hs do if x.votes[(m.p :: Player).UserId] then yes += 1 end end
		local need = math.floor(#hs / 2) + 1
		X.sayAll({ k = "xvote", yes = yes, need = need, by = p.DisplayName })
		if yes >= need then callIt(g, p.DisplayName) end
	end
	chain("cleared", function(_r: any, g: any)
		local x = g.x
		if not x or x.st ~= "off" or not x.z or not ZM.xOffered(g.n) then return nil end
		x.st = "offer"
		x.votes = {}
		g.untilT = now() + XC.voteS
		attrs(g, { XSt = "offer", XN = g.n })
		local hs = humans(g)
		X.sayAll({ k = "xoffer", n = g.n, need = math.floor(#hs / 2) + 1, s = XC.voteS })
		return nil
	end)
	chain("round", function(_r: any, g: any)
		local x = g.x
		if x and x.st == "offer" then -- (nobody called it: on as usual)
			x.st = "off"
			unset(g, "XSt")
		end
		return nil
	end)
	chain("heavy", function(_r: any, g: any)
		local x = g.x
		if x and x.st == "hold" then return XC.heavy end
		return nil
	end)
	-- the bots: by the helicopter's open side (its left), spread along it
	chain("botGoal", function(_r: any, g: any, m: any)
		local x = g.x
		if not x or x.st ~= "hold" or not x.pad then return nil end
		local pad: CFrame = x.pad
		local k = ((m.bot and m.bot.i) or 1) - 2
		return pad.Position - pad.RightVector * 9 + pad.LookVector * (k * 3.2)
	end)

	-- ------------------------------------------------------------------ the anti-farming numbers
	chain("hitZombie", function(r: any, g: any, z: any, amt: number, a: any, wid: string)
		local d = if type(r) == "number" then r else amt
		local x = ZR.track(a)
		local real = math.min(d, math.max(0, z.f.hp))
		x.dmg += real
		x.hitT = now()
		x.wdmg[wid] = (x.wdmg[wid] or 0) + real
		return nil
	end)
	local function sample(g: any)
		if g.st == "pre" or g.st == "over" then return end
		for _, m in g.members do
			local x = ZR.track(m)
			x.t += 1
			local up = m.f.alive and not m.down and not m.dead
			if up then x.up += 1 end
			local r = Fight.root(m.f)
			local moved = false
			if r and x.last then moved = (r.Position - x.last).Magnitude > 1.5 end
			if r then x.last = r.Position end
			if up and (moved or now() - x.hitT < 4) then x.act += 1 end
		end
	end

	-- ------------------------------------------------------------------ the end of the hold-out
	local function inZone(g: any, m: any): boolean
		local x = g.x
		if not m.f.alive or m.down or m.dead then return false end
		local r = Fight.root(m.f)
		if not r then return false end
		local feet = X.feetOf(r)
		local P = (x.pad :: CFrame).Position
		return flat(feet - P).Magnitude <= x.z.r and math.abs(feet.Y - P.Y) < 6
	end
	local function rowsOf(g: any): { any }
		local rows = {}
		for _, m in g.members do table.insert(rows, { m.name, m.kills, m.heads, m.downs, m.revives, m.earned }) end
		table.sort(rows, function(a, b) return a[2] > b[2] end)
		return rows
	end
	local function resolve(g: any)
		local x = g.x
		local out, anyHuman = {}, false
		for _, m in g.members do
			if inZone(g, m) then table.insert(out, m); if m.p then anyHuman = true end end
		end
		if not anyHuman then
			-- nobody human made it: the plain game over (its own hook pays the XP)
			x.st = "lost"
			unset(g, "XSt")
			X.gameOver(g)
			return
		end
		x.st = "out"
		g.st = "over"
		g.overT = now() + 10 -- (Zombies.stop 12 s after this: the film and the reward screen)
		local names = {}
		for _, m in out do
			m.extracted = true
			m.iframe = math.huge
			table.insert(names, m.name)
		end
		X.saveBest(g)
		local lift = x.s0 + XC.hold + XC.board
		attrs(g, { XSt = "out", XLift = lift })
		X.sayAll({ k = "xout", who = names, n = g.n })
		X.publish()
		-- the bots walk in at the open side; the bodies go in when the film's first shot ends
		local pad: CFrame = x.pad
		local door = pad.Position - pad.RightVector * 4.2 + Vector3.new(0, 3, 0)
		for _, m in out do
			if m.bot then
				local hum = Fight.hum(m.f)
				if hum then hum:MoveTo(door) end
			end
		end
		task.delay(XC.board - 0.5, function()
			for _, m in out do
				local mdl = Fight.model(m.f)
				if not mdl or not mdl.Parent then continue end
				local r = Fight.root(m.f)
				if r then r.Anchored = true end
				for _, d in mdl:GetDescendants() do
					if d:IsA("BasePart") then d.Transparency = 1; d.CanCollide = false
					elseif d:IsA("Decal") then d.Transparency = 1 end
				end
			end
		end)
		-- the rewards: the server's own event, once per player (receipt ids)
		local rows = rowsOf(g)
		for _, m in g.members do
			if not m.p then continue end
			if m.extracted then
				local ok, res = pcall(ZR.extract, g, m)
				if not ok then warn("[jankfire] zombies rewards: " .. tostring(res)); res = { n = g.n, ok = false, why = "error", rolls = {} } end
				X.say(m, { k = "xreward", res = res })
				print(("[jankfire] zombies extraction: %s out at round %d, ok %s (%s), brass %s, xp %s, dry %s"):format(
					m.name, g.n, tostring(res.ok), tostring(res.why), tostring(res.brass), tostring(res.xp), tostring(res.dry)))
			else
				local ok, res = pcall(ZR.over, g, m)
				X.say(m, { k = "over", n = g.n, rows = rows, left = true })
				if ok then X.say(m, { k = "xover", res = res }) end
			end
		end
	end

	chain("tick", function(_r: any, g: any, dt: number)
		local x = g.x
		if not x then return nil end
		x.acc += dt
		if x.acc >= 1 then x.acc -= 1; sample(g) end
		if x.st == "hold" then
			if g.st == "live" and g.toSpawn < 8 then g.toSpawn = 8 end -- (no end to it)
			if now() >= x.t0 + XC.hold then resolve(g) end
		end
		return nil
	end)
	chain("over", function(_r: any, g: any)
		local x = g.x
		if x and x.st ~= "out" then x.st = "lost"; unset(g, "XSt") end
		for _, m in g.members do
			if not m.p then continue end
			local ok, res = pcall(ZR.over, g, m)
			if ok then X.say(m, { k = "xover", res = res }) end
		end
		return nil
	end)
	chain("stop", function(_r: any, _g: any)
		local f = ReplicatedStorage:FindFirstChild("JankfireZmCine")
		if f then f:ClearAllChildren() end
		return nil
	end)

	-- ------------------------------------------------------------------ what clients say
	zr.OnServerEvent:Connect(function(p: Player, msg: any)
		if type(msg) ~= "table" then return end
		local g = Z.game()
		if not g or not g.x then return end
		local mine = false
		for _, m in g.members do if m.p == p then mine = true end end
		if not mine then return end
		if msg.k == "xcall" then
			vote(g, p)
		elseif msg.k == "xskip" then
			g.x.skips[p.UserId] = true
			if g.st ~= "pre" then return end
			for _, m in humans(g) do if not g.x.skips[(m.p :: Player).UserId] then return end end
			g.untilT = math.min(g.untilT, now() + 2.5)
		end
	end)

	-- ------------------------------------------------------------------ Studio test ops
	chain("test", function(r: any, op: string, a: any, _b: any)
		if r ~= nil then return nil end
		local g = Z.game()
		if op == "xelig" then ZR.GATE_OFF = a ~= false; return "reward checks " .. (if ZR.GATE_OFF then "OFF" else "on") end
		if op == "xreal" then ZR.REAL = a ~= false; return "real grants " .. tostring(ZR.REAL) end
		if not g or not g.x then return nil end
		local x = g.x
		if op == "xoffer" or op == "xcall" then
			if not x.z then return "no zone on " .. g.model.Name end
			if x.st == "off" then
				x.st = "offer"; x.votes = {}
				attrs(g, { XSt = "offer", XN = g.n })
				X.sayAll({ k = "xoffer", n = g.n, need = 1, s = XC.voteS })
			end
			if op == "xcall" and x.st == "offer" then callIt(g, "test") end
			return x.st
		elseif op == "xend" then
			if x.st == "hold" then x.t0 = now() - XC.hold; x.s0 = srv() - XC.hold; attrs(g, { XT0 = x.s0 }) end
			return x.st
		elseif op == "xstate" then
			local rows = {}
			for _, m in g.members do
				local t = ZR.track(m)
				local ok, why = ZR.eligible(g, m)
				table.insert(rows, string.format("%s t%d up%d act%d dmg%.0f kills%d in%s elig %s %s", m.name, t.t, t.up, t.act, t.dmg,
					m.kills, tostring(x.pad and inZone(g, m)), tostring(ok), tostring(why or "")))
			end
			return { st = x.st, n = g.n, t = if x.t0 then now() - x.t0 else nil, pad = if x.pad then tostring(x.pad.Position) else nil, rows = rows }
		end
		return nil
	end)
end

return ZombieExtract
