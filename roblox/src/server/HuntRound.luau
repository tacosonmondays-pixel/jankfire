--!strict
-- HOLDOUT's round (26 Nov 2026; roblox/docs/HUNT.md section 5). The owner: "The gunman will have a random gun from ar to
-- sniper to shotgun etc.. Hiders bodies can be 'dismembered' but it'll be like blocky particles ... headshots always
-- kill instantly! If you hide for 2ish minutes you will be given a chance to fight back". The friend's: "one killer, and
-- everyone is a hider ... killer gets a gun and various passives".
--   the lobby: 2+ players in THE HOUSE -> a 20 s count on the board -> a round with everyone in the house then
--   the round: a COPY of a map (HuntConfig.MAPS; the source stays as it is) at a site far out; one gunman (never the
--     last round's while anyone else can be), the rest hiders spread over the map; HIDE 20 s (the gunman sealed in a
--     dark room over the map), then HUNT 4:00; FIGHT BACK from 2:00 in (stage 3: search spots, the weapons)
--   the end: every hider down = the gunman's; the clock out with a hider standing, or the gunman down = the hiders';
--     a 6 s results card, then everyone back in the house and the copy gone
-- How it plugs in (every hook chained, re-asserted each tick over whatever is there):
--   Matches.zoneHook: a member reads as Zone "match" (the hub's menus hide, loadouts lock)
--   Fight.allow (gunman <-> hider only, in HUNT), Fight.modDamage (a headshot on a hider kills), Fight.holdRespawn (the
--   dead watch till the end), Fight.noItems (no gadgets), Fight.onKill (the break-up), Fight.onSpawn (no joint break)
--   Rules: the gunman's f.forced = { his gun }, f.maxHp; the hiders carry nothing (player attribute Unarmed: Fight.
--   holstered, Arsenal and HubHolster treat it like the hub)
-- Studio: ReplicatedStorage attribute HuntTestMin lowers the players a round needs; HuntRound.test(...) (JankHuntTest
-- "round") starts one with stand-in bodies.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Weapons = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Weapons")) :: any
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Rules = require(script.Parent:WaitForChild("Rules")) :: any
local HuntItems = require(script.Parent:WaitForChild("HuntItems")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent
local RD = HC.ROUND

type Fighter = any
type Member = { p: Player?, f: Fighter, role: string, spawn: CFrame, alive: boolean, standin: Model?, grace: number? }
local HuntRound = {}
HuntRound.G = nil :: any
HuntRound.lastGunman = nil :: Player?
local G: any = nil
local now = os.clock

local function serverNow(): number return workspace:GetServerTimeNow() end
local function member(f: Fighter?): Member?
	local g = G
	if not g or not f then return nil end
	return g.byF[f]
end
HuntRound.member = member
function HuntRound.memberOf(p: Player): Member?
	local f = Fight.byPlayer[p]
	return member(f)
end
function HuntRound.busy(): boolean return G ~= nil end

-- ------------------------------------------------------------------ the HUD's state (ReplicatedStorage attributes)
local function pub(k: string, v: any) if ReplicatedStorage:GetAttribute(k) ~= v then ReplicatedStorage:SetAttribute(k, v) end end
local function phase(ph: string?, endsAt: number?)
	pub("HuntRoundPhase", ph)
	pub("HuntRoundEnd", endsAt)
end

-- ------------------------------------------------------------------ the map's copy and the gunman's room
local function pickMap(want: string?): any
	local ok = {}
	local map = workspace:FindFirstChild("Map")
	for _, m in HC.MAPS do if map and map:FindFirstChild(m.source) and (want == nil or m.id == want) then table.insert(ok, m) end end
	return if #ok > 0 then ok[math.random(#ok)] else nil
end
local function copyMap(def: any, k: number): Model?
	local src = workspace.Map:FindFirstChild(def.source)
	if not src then return nil end
	local m = src:Clone() :: Model
	m.Name = "HuntGame_" .. def.id
	for _, s in (def.strip or {}) do local x = m:FindFirstChild(s); if x then x:Destroy() end end
	for _, a in { "Enabled", "ZombiesMap" } do m:SetAttribute(a, nil) end
	m:SetAttribute("HuntCopy", true)
	m:PivotTo(CFrame.new(RD.site + Vector3.new(RD.gap * k, 0, 0)))
	m.Parent = workspace
	return m
end
local function pen(at: Vector3, into: Instance): CFrame
	local f = Instance.new("Folder"); f.Name = "HuntPen"; f.Parent = into
	local W, H = 16, 11
	local dark = Color3.fromRGB(26, 27, 30)
	for _, b in {
		{ Vector3.new(0, -0.5, 0), Vector3.new(W + 2, 1, W + 2) }, { Vector3.new(0, H + 0.5, 0), Vector3.new(W + 2, 1, W + 2) },
		{ Vector3.new(W / 2 + 0.5, H / 2, 0), Vector3.new(1, H, W + 2) }, { Vector3.new(-W / 2 - 0.5, H / 2, 0), Vector3.new(1, H, W + 2) },
		{ Vector3.new(0, H / 2, W / 2 + 0.5), Vector3.new(W, H, 1) }, { Vector3.new(0, H / 2, -W / 2 - 0.5), Vector3.new(W, H, 1) },
	} do
		local p = Instance.new("Part")
		p.Anchored = true; p.Size = b[2]; p.CFrame = CFrame.new(at + b[1]); p.Color = dark; p.Material = Enum.Material.SmoothPlastic
		p.CanQuery = true; p:SetAttribute("Mat", "concrete"); p.Parent = f
	end
	return CFrame.lookAt(at + Vector3.new(0, 0.1, 0), at + Vector3.new(0, 0.1, -1))
end

-- ------------------------------------------------------------------ stand-ins (Studio tests: a body that counts as a player)
local function standin(name: string, at: CFrame, into: Instance): (Model?, Fighter?)
	local desc = Instance.new("HumanoidDescription")
	desc.HeadColor = Color3.fromRGB(234, 184, 146); desc.TorsoColor = Color3.fromRGB(70, 110, 150)
	desc.LeftArmColor = desc.HeadColor; desc.RightArmColor = desc.HeadColor
	desc.LeftLegColor = Color3.fromRGB(60, 62, 70); desc.RightLegColor = desc.LeftLegColor
	local ok, m = pcall(function() return Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15) end)
	if not ok or not m then return nil, nil end
	m.Name = name
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then hum.BreakJointsOnDeath = false; hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	m:PivotTo(at + Vector3.new(0, 3, 0))
	m.Parent = into
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then pcall(function() root:SetNetworkOwner(nil) end) end
	local f = Rules.newFighter("dummy", name, m)
	Rules.spawn(f, now())
	Fight.byModel[m] = f
	table.insert(Fight.all, f)
	return m, f
end

-- ------------------------------------------------------------------ start
local function spawnCF(def: any, i: number, origin: CFrame): CFrame
	local s = def.hiders[((i - 1) % #def.hiders) + 1]
	local at = origin * CFrame.new(s[1], s[2] + 0.1, s[3])
	return CFrame.lookAt(at.Position, at.Position + origin.LookVector)
end
local function shuffled(n: number): { number }
	local t = {}
	for i = 1, n do t[i] = i end
	for i = n, 2, -1 do local j = math.random(i); t[i], t[j] = t[j], t[i] end
	return t
end

function HuntRound.start(players: { Player }, opts: any?): (boolean, string?)
	if G then return false, "busy" end
	opts = opts or {}
	local def = pickMap(opts.map) -- (opts.map: one map's id, for tests)
	if not def then return false, "no map" end
	local copy = copyMap(def, 0)
	if not copy then return false, "no copy" end
	local origin = copy:GetPivot()
	local penAt = pen(origin.Position + RD.pen, copy)
	local gm = origin * CFrame.new(def.gunman[1], def.gunman[2] + 0.1, def.gunman[3])
	local gunmanSpawn = CFrame.lookAt(gm.Position, gm.Position + Vector3.new(def.gunman[4], 0, def.gunman[5]))
	-- the gunman: anyone but last round's (unless they're alone), or the one a test names
	local pool = {}
	for _, p in players do if p ~= HuntRound.lastGunman then table.insert(pool, p) end end
	if #pool == 0 then pool = table.clone(players) end
	local gunman: Player? = if opts.gunman ~= nil then opts.gunman else pool[math.random(#pool)]
	if opts.gunman == false then gunman = nil end
	-- his gun and two passives
	local gun = opts.gun or HC.GUNS[math.random(#HC.GUNS)]
	local idx = shuffled(#HC.PASSIVES)
	local passives = { HC.PASSIVES[idx[1]].id, HC.PASSIVES[idx[2]].id }
	if opts.passives then passives = opts.passives end
	local g = { def = def, map = copy, origin = origin, penAt = penAt, gunmanSpawn = gunmanSpawn, members = {}, byF = {},
		phase = "hide", t0 = now(), gun = gun, passives = passives, gunman = nil :: Member?, kills = 0,
		nextPulse = 0, nextTracks = 0, standins = {} }
	g.hideEnd = now() + (opts.hide or RD.hide)
	g.huntEnd = g.hideEnd + (opts.hunt or RD.hunt)
	g.fightAt = g.hideEnd + (opts.fightBack or RD.fightBack)
	G = g; HuntRound.G = g
	local order = shuffled(#def.hiders)
	local hi = 0
	local function add(p: Player?, f: Fighter, role: string, sm: Model?)
		local spawn: CFrame
		if role == "gunman" then spawn = penAt else hi += 1; spawn = spawnCF(def, order[((hi - 1) % #order) + 1], origin) end
		local m: Member = { p = p, f = f, role = role, spawn = spawn, alive = true, standin = sm, grace = now() + 6 }
		table.insert(g.members, m)
		g.byF[f] = m
		if role == "gunman" then g.gunman = m end
		return m
	end
	for _, p in players do
		local f = Fight.byPlayer[p]
		if not f then continue end
		local role = if p == gunman then "gunman" else "hider"
		add(p, f, role, nil)
		p:SetAttribute("Hunt", "round"); p:SetAttribute("HuntRole", role); p:SetAttribute("Arena", def.source)
		p:SetAttribute("NoGrapple", true); p:SetAttribute("HuntLie", nil)
		p:SetAttribute("Unarmed", if role == "hider" then true else nil)
		if role == "gunman" then
			f.forced = { gun }
			f.maxHp = RD.gunmanHp + (if table.find(passives, "thick") then 100 else 0)
		else
			f.forced = nil; f.maxHp = nil
		end
		f.alive = false
		task.spawn(Fight.spawn, f)
	end
	-- (Studio) stand-ins: hiders at hider spots, or the gunman at his release point
	for i = 1, (opts.standins or 0) do
		local role = if opts.standinRole == "gunman" and i == 1 then "gunman" else "hider"
		local at = if role == "gunman" then gunmanSpawn else spawnCF(def, order[((hi) % #order) + 1], origin)
		local sm, sf = standin("Standin" .. i, at, copy)
		if sm and sf then
			if role == "gunman" then sf.maxHp = RD.gunmanHp; sf.hp = RD.gunmanHp end
			local m = add(nil, sf, role, sm)
			m.spawn = at
			table.insert(g.standins, sm)
		end
	end
	HuntItems.onStart(g)
	pub("HuntPhase", "round")
	pub("HuntGun", gun); pub("HuntPassives", table.concat(passives, ",")); pub("HuntMap", def.title)
	phase("hide", serverNow() + (opts.hide or RD.hide))
	Remote:FireAllClients("round", { map = def.title, gun = gun, passives = passives })
	return true, nil
end

-- ------------------------------------------------------------------ the end
local function alive(m: Member): boolean
	return m.alive and (m.f.alive or now() <= (m.grace or 0)) -- (being re-made with the round's kit counts as up)
end
local function finish(winner: string, why: string)
	local g = G
	if not g or g.phase == "end" then return end
	g.phase = "end"
	g.endAt = now() + RD.results
	local survivors = {}
	for _, m in g.members do
		if m.role == "hider" and alive(m) then table.insert(survivors, if m.p then m.p.DisplayName else m.f.name) end
	end
	local gm = g.gunman
	local res = { winner = winner, why = why, gunman = if gm then (if gm.p then gm.p.DisplayName else gm.f.name) else nil,
		kills = g.kills, survivors = survivors, gun = g.gun }
	pub("HuntWinner", winner)
	phase("end", serverNow() + RD.results)
	Remote:FireAllClients("results", res)
end
local function cleanup()
	local g = G
	if not g then return end
	G = nil; HuntRound.G = nil
	if g.gunman and g.gunman.p then HuntRound.lastGunman = g.gunman.p end
	pcall(HuntItems.onEnd, g)
	pub("HuntFightBack", nil)
	for _, m in g.members do
		local f = m.f
		f.forced = nil; f.maxHp = nil
		if m.p then
			local p = m.p
			for _, a in { "HuntRole", "Unarmed", "Arena", "HuntLie" } do p:SetAttribute(a, nil) end
			p:SetAttribute("Hunt", "lobby")
			HuntRound.returning[p] = true
			if p.Parent then f.alive = false; task.spawn(Fight.spawn, f) end
		else
			local i = table.find(Fight.all, f)
			if i then table.remove(Fight.all, i) end
			if f.ref then Fight.byModel[f.ref] = nil end
		end
	end
	for _, sm in g.standins do if sm.Parent then sm:Destroy() end end
	if g.map then g.map:Destroy() end
	pub("HuntPhase", "lobby"); pub("HuntWinner", nil); pub("HuntGun", nil); pub("HuntPassives", nil); pub("HuntMap", nil)
	phase(nil, nil)
end
HuntRound.returning = {} :: { [Player]: boolean }
function HuntRound.stop(): string
	if not G then return "no round" end
	finish("none", "stopped")
	cleanup()
	return "stopped"
end

-- ------------------------------------------------------------------ the tick
local function letOut(g: any)
	local m = g.gunman
	if not m then return end
	if m.p then
		local ch = m.p.Character
		if ch then
			m.p:SetAttribute("TeleportT", os.clock())
			local r = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then r.AssemblyLinearVelocity = Vector3.zero end
			ch:PivotTo(g.gunmanSpawn + Vector3.new(0, 3, 0))
		end
	end
	m.spawn = g.gunmanSpawn
end
function HuntRound.tick()
	local g = G
	if not g then return end
	local t = now()
	-- leavers
	for _, m in g.members do
		if m.p and not m.p.Parent then m.alive = false end
		-- (a body that isn't up: dead, unless it is still being re-made with its round kit: Fight.spawn takes a moment.
		-- the Studio test of 26 Nov 23:48 ended every round at once: the gunman's respawn read as a death)
		if not m.f.alive and now() > (m.grace or 0) then m.alive = false end
	end
	if g.phase == "hide" and t >= g.hideEnd then
		g.phase = "hunt"
		letOut(g)
		phase("hunt", serverNow() + (g.huntEnd - t))
		Remote:FireAllClients("phase", "hunt")
	end
	if g.phase == "hunt" then
		if not g.fightOn and t >= g.fightAt then
			g.fightOn = true
			pub("HuntFightBack", true)
			HuntItems.onFightBack(g)
			Remote:FireAllClients("phase", "fightback")
		end
		local hiders, gunUp = 0, g.gunman ~= nil and alive(g.gunman)
		for _, m in g.members do if m.role == "hider" and alive(m) then hiders += 1 end end
		if hiders == 0 then finish("gunman", "every hider is down"); return end
		if not gunUp then finish("hiders", "the gunman is down"); return end
		if t >= g.huntEnd then finish("hiders", "time"); return end
		-- the gunman's passives: PULSE (hiders near him, through walls, a moment) and TRACKS (running hiders' prints)
		local gm = g.gunman
		local gp = gm and gm.p
		local groot = gm and Fight.root(gm.f)
		if gp and groot then
			if table.find(g.passives, "pulse") and t >= g.nextPulse then
				local P = HC.PASSIVES[1]
				for _, pv in HC.PASSIVES do if pv.id == "pulse" then P = pv end end
				g.nextPulse = t + P.every
				local list = {}
				for _, m in g.members do
					local r = m.role == "hider" and alive(m) and Fight.root(m.f)
					if r and (r.Position - groot.Position).Magnitude <= P.range then table.insert(list, Fight.model(m.f)) end
				end
				Remote:FireClient(gp, "pulse", list, P.show)
			end
			if table.find(g.passives, "tracks") and t >= g.nextTracks then
				g.nextTracks = t + 0.3
				local prints = {}
				for _, m in g.members do
					if m.role ~= "hider" or not alive(m) or not m.p then continue end
					local r = Fight.root(m.f)
					local fast = m.p:GetAttribute("Sprinting") == true or (r and r.AssemblyLinearVelocity.Magnitude > 34)
					if r and fast then table.insert(prints, r.Position - Vector3.new(0, 2.9, 0)) end
				end
				if #prints > 0 then Remote:FireClient(gp, "tracks", prints) end
			end
		end
	end
	if g.phase == "hunt" or g.phase == "hide" then HuntItems.tick(g, 0.25) end
	if g.phase == "end" and t >= g.endAt then cleanup() end
end

-- ------------------------------------------------------------------ the Fight hooks (installed and re-asserted by Hunt)
HuntRound.allow = function(prev: any)
	return function(by: Fighter?, t: Fighter): boolean
		local g = G
		if g and by and by ~= t then
			local a, b = member(by), member(t)
			if a or b then
				if not (a and b) then return false end
				if g.phase ~= "hunt" then return false end
				return a.role ~= b.role
			end
		end
		return prev(by, t)
	end
end
HuntRound.modDamage = function(prev: any)
	return function(t: Fighter, amt: number, by: Fighter?, wid: string): number
		if prev then amt = prev(t, amt, by, wid) end
		local a, b = member(by), member(t)
		-- (the owner: "headshots always kill instantly")
		if a and b and a.role == "gunman" and b.role == "hider" and Fight.hitHs then amt = math.max(amt, t.hp + 1) end
		return amt
	end
end
HuntRound.holdRespawn = function(prev: any)
	return function(f: Fighter): boolean
		if member(f) then return true end
		return prev(f)
	end
end
HuntRound.noItems = function(prev: any)
	return function(f: Fighter): boolean
		if member(f) then return true end
		return prev(f)
	end
end
function HuntRound.spawnFor(f: Fighter): CFrame?
	local m = member(f)
	if m then return m.spawn end
	return nil
end
-- (FIRM STANCE: shoves move the gunman half as far; HuntMoves asks)
function HuntRound.knockScale(p: Player): number
	local m = HuntRound.memberOf(p)
	if G and m and m.role == "gunman" and table.find(G.passives, "firm") then return 0.5 end
	return 1
end
-- may a shove from a reach b: both in the house, or both in the round's hunt
function HuntRound.canShove(a: Player, b: Player): boolean
	local ma, mb = HuntRound.memberOf(a), HuntRound.memberOf(b)
	if ma or mb then return ma ~= nil and mb ~= nil and G ~= nil and G.phase == "hunt" end
	return a:GetAttribute("Hunt") == "lobby" and b:GetAttribute("Hunt") == "lobby"
end

-- a death in the round: the body breaks into cubes on every client (HuntFx), the stand-in leaves the fighter list
Fight.onKill(function(info: any)
	local m = member(info.v)
	if not m then return end
	m.alive = false
	local g = G
	if g and info.k and member(info.k) and member(info.k).role == "gunman" then g.kills += 1 end
	local model = Fight.model(info.v)
	if model then Remote:FireAllClients("shatter", model, info.v.kind == "player") end
	if not m.p then
		local i = table.find(Fight.all, info.v)
		if i then table.remove(Fight.all, i) end
		task.delay(2, function() if m.standin and m.standin.Parent then m.standin:Destroy() end end)
	end
end)
Fight.onSpawn(function(f: Fighter)
	local m = member(f)
	if not m then return end
	local hum = Fight.hum(f)
	if hum then hum.BreakJointsOnDeath = false end -- (the client breaks the body into cubes: no limbs fall off)
end)
Players.PlayerRemoving:Connect(function(p)
	HuntRound.returning[p] = nil
	if HuntRound.lastGunman == p then HuntRound.lastGunman = nil end
end)
_ = RunService; _ = Weapons

return HuntRound
