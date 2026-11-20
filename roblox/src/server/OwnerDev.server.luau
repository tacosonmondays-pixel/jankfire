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
--   DevInvisible (18 Nov, round 2: "I can go invisible"): the owner's body, gun, name, title and pet are hidden from
--   everyone else (the server hides the body, gun and name; OverheadTitles, Pets and ThirdPerson skip an invisible
--   player); the owner's own client draws a faint ghost (OwnerDev.client)
-- what it can do to others (any player; in Studio also a training dummy, the stand-in for tests):
--   fling (a hard shove up and away; the one you look at: X), freeze / unfreeze (held still where they are; Z), go to,
--   bring. a frozen player is let go when they die or leave, and all of them when the owner leaves
--   THE JAIL (round 2: "a small room for funsey that I can send people to"): a small sealed room built here, high over
--   the hub (Map.DevJail, a ZonePiece: ZoneCull hides it from anyone not near). sent there = a server move (TeleportT).
--   out after JAIL_TIME s, on release, when they join a party or a lobby, die, or get moved by anything else; leaving the
--   game always works. sent from a match: taken out of it first (Matches.pull, as if they'd left; the match is flagged)
--   GIFT (18 Nov, round 3: "let me gift people stuff"): containers in any number, bundles and skin sets, single items,
--   Brass, Crate Tickets, coins, VIP, to anyone in the server or yourself (see "gifts" below)
--   GIFT EVERYONE and ANNOUNCE (19 Nov, round 4: "gift everyone stuff and write announcements that go across the screen
--   across all servers"): to everyone in this server or in every live server (MessagingService), once per player per
--   event; announcements through Roblox's filter first (see "gift everyone, and announcements" below)
--   RED CARD (round 2, football style; the one you look at: Y): the owner raises a red card (every client poses the
--   owner's arm and puts a card in the hand, DevFx "redcard"), a referee's whistle blows (a Pro Sound Effects recording),
--   the target's screen flashes a red card, and 1.2 s later they're in the jail
-- nothing touches a save. hits and kills from the owner's dev weapons outside a match count for nothing
-- (Fight.devKill: no feed, no kill hooks, no score; the victim is back at once). Stats and quests only count live
-- matches anyway. victims of a fling, a bring or a freeze get the anti-cheat's usual pass for a server move
-- (ACGrace / TeleportT, docs/ANTI-CHEAT.md contracts), the same as a TV Remote rewind
-- every command is printed to the server log: "[dev] <owner> <what> <target>"
-- Studio tests: attribute TestNotOwner = true on this script makes the owner a stranger (every command refused);
-- ServerStorage.JankDev (Studio only): "state" (the owner's switches, who's frozen, the log), "as" (player, op, a, b:
-- a command as that player), "log", "giftLine", "event" (play an event as another server would), "forget" (an event id),
-- "events" (what came in over MessagingService), "grant" (TEMP DEV on a player, minutes or c = seconds, as if by the
-- owner), "revoke", "temps". a training dummy with DevStandIn = "owner" / "temp" stands in for the owner or a temp dev
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Rules = require(script.Parent:WaitForChild("Rules")) :: any
local Zones = require(script.Parent:WaitForChild("Zones")) :: any
local Matches = require(script.Parent:WaitForChild("Matches")) :: any
local GiftFx = require(script.Parent:WaitForChild("GiftFx")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local STUDIO = RunService:IsStudio()
local now = os.clock

-- ------------------------------------------------------------------ the numbers
local FLY = { min = 20, max = 300, default = 80 } -- studs/s
local RUN = { min = 1, max = 4 } -- x the usual run speed
local FLING = { side = 170, up = 130 } -- studs/s, away from the owner and up
local AIM = { range = 220, cone = 0.1 } -- the one you look at: this far, this much slack (rad) plus a body's width
local DEV_AFTER = 3 -- s the anti-cheat's pass outlasts the last power
local JAIL_TIME = 60 -- s at most in the jail
local JAIL_UP = 420 -- studs over the hub's Origin (anything 60 under it is the void: Matches)
local CARD_POSE = 1.2 -- s the red card is held up before they go
local WHISTLE = "rbxassetid://9118113825" -- Pro Sound Effects "Referee Whistle, Exterior, Single Blast" (Roblox's licensed library)
local HIT_ZONES = { hub = true, training = true, playground = true } :: { [string]: boolean } -- dev weapons hurt players here

-- ------------------------------------------------------------------ who's the owner
local function isOwner(p: Player): boolean
	if STUDIO and script:GetAttribute("TestNotOwner") == true then return false end
	return game.CreatorType == Enum.CreatorType.User and p.UserId > 0 and p.UserId == game.CreatorId
end

-- ------------------------------------------------------------------ TEMP DEV: the owner lends the powers to a friend
-- (19 Nov 2026, the owner: "allow me to temp give command panel to friends exclude the gifting portion of it"). on the
-- FRIENDS tab the owner picks a player in this server and gives them TEMP DEV for 15 min, 30 min, 1 h, or until they
-- leave. it's held in this server's memory only, never saved: it ends at its time, when they leave, when the server
-- closes, or on REVOKE / REVOKE ALL. only the owner grants (a temp dev never can)
--   a temp dev gets: fly, noclip, run speed, invisible, weapons in the hub, and fling, freeze, go to, bring, jail, red
--   card, opened the same way (F8, "/dev", the DEV button), the POWERS tab only
--   never: GIFT with its XP and UNLOCKS, ANNOUNCE, the anti-cheat panel, granting, UNFREEZE EVERYONE / EMPTY THE JAIL,
--   anything to the owner or another temp dev, or a player the owner is holding (frozen or jailed by the owner).
--   refused here by who sent it (TEMP_OPS and the checks in handle), not only by the hidden tabs
--   the same safety as the owner's use: a match their power touches counts for nothing (m.dev), the anti-cheat's devOn
--   covers them while it lasts (DevTemp, which only this script writes), and every command they use goes in the server
--   log ("[dev temp] ...") and the anti-cheat panel's log (kind "tempdev"). no OWNER title (that's Stats.owns: the
--   creator only)
--   player attribute DevTemp = the os.time() it ends at, or 0 = until they leave (their menu reads it); DevFx
--   { k = "devaccess", on, ends } tells them as it starts and ends
local TEMP_TIMES = { [15] = true, [30] = true, [60] = true, [0] = true } :: { [number]: boolean } -- minutes (0 = until they leave)
type Temp = { untilT: number?, ends: number, by: Player, mins: number }
local temps: { [Player]: Temp } = {}
local function isTemp(p: Player): boolean
	local t = temps[p]
	return t ~= nil and p.Parent == Players and (t.untilT == nil or now() < (t.untilT :: number))
end
local function isDev(p: Player): boolean return isOwner(p) or isTemp(p) end
-- what a temp dev may send; everything else is the owner's alone
local TEMP_OPS = { hello = true, state = true, players = true, set = true, fling = true, flingAim = true, freeze = true,
	freezeAim = true, ["goto"] = true, bring = true, jail = true, release = true, redcard = true, redcardAim = true } :: { [string]: boolean }
local ACLog: any = nil
local function acNote(p: Player, act: string, info: string)
	if ACLog == nil then
		local m = script.Parent:FindFirstChild("AntiCheatLog")
		local ok, r = false, nil
		if m and m:IsA("ModuleScript") then ok, r = pcall(require, m) end
		ACLog = if ok and type(r) == "table" then r else false
	end
	if ACLog then pcall(ACLog.add, p, "tempdev", string.sub(act, 1, 40), info) end
end

-- ------------------------------------------------------------------ the log
local lines: { string } = {}
local function log(p: Player, what: string, target: string?)
	local temp = temps[p] ~= nil and not isOwner(p)
	local line = ("[dev%s] %s %s%s"):format(if temp then " temp" else "", p.Name, what, if target then " " .. target else "")
	print(line)
	table.insert(lines, os.date("!%H:%M:%S ") .. line)
	while #lines > 40 do table.remove(lines, 1) end
	-- (a temp dev's every command is in the anti-cheat panel's log too, with who lent it)
	if temp then acNote(p, what, (if target then target .. " " else "") .. "(temp dev from " .. (temps[p] :: Temp).by.Name .. ")") end
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
type State = { fly: boolean, flySpeed: number, noclip: boolean, speed: number, arms: boolean, invis: boolean, offAt: number? }
local states: { [Player]: State } = {}
local function stateOf(p: Player): State
	local s = states[p]
	if not s then
		s = { fly = false, flySpeed = FLY.default, noclip = false, speed = 1, arms = false, invis = false, offAt = nil }
		states[p] = s
	end
	return s :: State
end
local function anyOn(s: State): boolean return s.fly or s.noclip or s.speed ~= 1 or s.arms or s.invis end
local function view(s: State): any
	return { fly = s.fly, flySpeed = s.flySpeed, noclip = s.noclip, speed = s.speed, arms = s.arms, invis = s.invis }
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
-- who froze or jailed someone (TEMP DEV: a friend can't undo or touch what the owner is holding; theirs go free when
-- their access ends). only read while that someone is still frozen or jailed
local heldBy: { [any]: Player } = {}

-- ------------------------------------------------------------------ invisible
-- every part and decal of the owner's body (and whatever is added to it while it lasts: a new gun, a hat) goes fully
-- see-through on the server, lights, effects and labels on it go off, the name over it goes; each one's old value is
-- kept to put back. the part's old transparency is also its DevWas attribute: the owner's client draws its ghost from it
-- (a strong table: Roblox can drop an Instance key from a weak table while the part still exists, and then nothing
-- comes back. emptied as each thing is put back; things whose body is gone are swept out by the watch below)
local kept: { [Instance]: any } = {}
local OFF_CLASSES = { "ParticleEmitter", "Beam", "Trail", "Light", "Fire", "Smoke", "Sparkles", "Highlight", "BillboardGui", "SurfaceGui" }
local function hideOne(d: Instance)
	if kept[d] ~= nil or not d.Parent then return end
	if d:IsA("BasePart") or d:IsA("Decal") then
		local was = (d :: any).Transparency
		kept[d] = was
		d:SetAttribute("DevWas", was)
		;(d :: any).Transparency = 1
		return
	end
	for _, c in OFF_CLASSES do
		if d:IsA(c) then
			kept[d] = (d :: any).Enabled
			;(d :: any).Enabled = false
			return
		end
	end
end
local function showOne(d: Instance)
	if d:IsA("Humanoid") then return end -- (its name setting: setInvisible puts it back)
	local was = kept[d]
	if was == nil and (d:IsA("BasePart") or d:IsA("Decal")) then was = d:GetAttribute("DevWas") end
	if was == nil then return end
	kept[d] = nil
	if d:IsA("BasePart") or d:IsA("Decal") then
		(d :: any).Transparency = was
		d:SetAttribute("DevWas", nil)
	else
		(d :: any).Enabled = was
	end
end
local invisConns: { [Player]: { RBXScriptConnection } } = {}
local function hideBody(ch: Model, conns: { RBXScriptConnection })
	for _, d in ch:GetDescendants() do hideOne(d) end
	table.insert(conns, ch.DescendantAdded:Connect(function(d) task.defer(hideOne, d) end))
	local hum = ch:FindFirstChildOfClass("Humanoid")
	if hum and kept[hum] == nil then
		kept[hum] = hum.DisplayDistanceType
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	end
end
local function setInvisible(p: Player, on: boolean)
	for _, c in invisConns[p] or {} do c:Disconnect() end
	invisConns[p] = nil
	local ch = p.Character
	if on then
		p:SetAttribute("DevInvisible", true)
		local conns = {}
		if ch then hideBody(ch, conns) end
		table.insert(conns, p.CharacterAdded:Connect(function(c) task.defer(hideBody, c, conns) end))
		invisConns[p] = conns
	else
		p:SetAttribute("DevInvisible", nil)
		if ch then
			for _, d in ch:GetDescendants() do showOne(d) end
			local hum = ch:FindFirstChildOfClass("Humanoid")
			if hum then hum.DisplayDistanceType = kept[hum] or Enum.HumanoidDisplayDistanceType.Viewer; kept[hum] = nil end
		end
	end
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

-- ------------------------------------------------------------------ the jail
-- a small chunky room (the owner's look rule: few big shapes, flat quiet colours, a white light panel): 22 x 12 x 18
-- inside, bars across the front with a dark sealed corridor behind them, a bench, a ceiling lamp, a small bright window
-- in the back wall. every piece is solid and anchored (a grapple's ray hits it), so nobody walks, jumps or swings out
local jailModel: Model? = nil
local jailAt: Vector3 = Vector3.new(0, 600, 0) -- the floor's middle
local function jail(): Model?
	if jailModel and jailModel.Parent then return jailModel end
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	local old = map:FindFirstChild("DevJail")
	if old then old:Destroy() end
	local hub = map:FindFirstChild("Hub")
	local origin = hub and hub:GetAttribute("Origin")
	local base = if typeof(origin) == "Vector3" then origin + Vector3.new(0, JAIL_UP, 0) else Vector3.new(0, 600, 0)
	local m = Instance.new("Model")
	m.Name = "DevJail"
	m:SetAttribute("ZonePiece", true) -- (ZoneCull: drawn only for whoever is near it)
	local W, H, D, T, CORR = 22, 12, 18, 2, 4
	local function part(name: string, size: Vector3, at: Vector3, color: Color3, mat: Enum.Material?, shape: Enum.PartType?): Part
		local p = Instance.new("Part")
		p.Name = name
		if shape then p.Shape = shape end
		p.Size = size
		p.CFrame = CFrame.new(base + at)
		p.Color = color
		p.Material = mat or Enum.Material.SmoothPlastic
		p.Anchored = true
		p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
		p.Parent = m
		return p
	end
	local WALL, FLOOR, CEIL, DARK, STEEL = Color3.fromRGB(176, 178, 182), Color3.fromRGB(96, 98, 104), Color3.fromRGB(150, 152, 158), Color3.fromRGB(44, 46, 52), Color3.fromRGB(78, 80, 88)
	local fullD = D + CORR + T * 2
	local zMid = CORR / 2 -- (the box runs from the back wall to the corridor's far wall)
	part("Floor", Vector3.new(W + T * 2, T, fullD), Vector3.new(0, -T / 2, zMid), FLOOR, Enum.Material.Concrete)
	part("Ceiling", Vector3.new(W + T * 2, T, fullD), Vector3.new(0, H + T / 2, zMid), CEIL)
	part("WallBack", Vector3.new(W, H, T), Vector3.new(0, H / 2, -D / 2 - T / 2), WALL)
	part("WallLeft", Vector3.new(T, H, fullD), Vector3.new(-W / 2 - T / 2, H / 2, zMid), WALL)
	part("WallRight", Vector3.new(T, H, fullD), Vector3.new(W / 2 + T / 2, H / 2, zMid), WALL)
	part("WallFar", Vector3.new(W, H, T), Vector3.new(0, H / 2, D / 2 + CORR + T / 2), DARK)
	-- the bars: two rails and round bars every 1.6 studs (1.15-stud gaps: no body fits)
	local zb = D / 2
	part("RailLow", Vector3.new(W, 0.6, 0.6), Vector3.new(0, 0.3, zb), STEEL, Enum.Material.Metal)
	part("RailHigh", Vector3.new(W, 0.6, 0.6), Vector3.new(0, H - 0.3, zb), STEEL, Enum.Material.Metal)
	local n = 0
	for x = -W / 2 + 0.8, W / 2 - 0.8, 1.6 do
		n += 1
		local b = part("Bar" .. n, Vector3.new(H, 0.45, 0.45), Vector3.zero, STEEL, Enum.Material.Metal, Enum.PartType.Cylinder)
		b.CFrame = CFrame.new(base + Vector3.new(x, H / 2, zb)) * CFrame.Angles(0, 0, math.pi / 2)
	end
	-- the bench: one thick slab with a rounded front edge, on two blocks, along the left wall
	local BENCH = Color3.fromRGB(118, 112, 104)
	part("BenchSeat", Vector3.new(3.2, 1, 10), Vector3.new(-W / 2 + 1.6, 2.4, -2), BENCH)
	local edge = part("BenchEdge", Vector3.new(10, 1, 1), Vector3.zero, BENCH, nil, Enum.PartType.Cylinder)
	edge.CFrame = CFrame.new(base + Vector3.new(-W / 2 + 3.2, 2.4, -2)) * CFrame.Angles(0, math.pi / 2, 0)
	part("BenchLegA", Vector3.new(2.6, 1.9, 1.2), Vector3.new(-W / 2 + 1.4, 0.95, -5.6), Color3.fromRGB(88, 90, 96))
	part("BenchLegB", Vector3.new(2.6, 1.9, 1.2), Vector3.new(-W / 2 + 1.4, 0.95, 1.6), Color3.fromRGB(88, 90, 96))
	-- the lamp: a white light panel in the ceiling
	local lamp = part("Lamp", Vector3.new(6, 0.3, 4), Vector3.new(0, H - 0.15, -1), Color3.fromRGB(236, 238, 240), Enum.Material.Neon)
	local sl = Instance.new("SurfaceLight")
	sl.Face = Enum.NormalId.Bottom
	sl.Brightness = 1.6
	sl.Range = 20
	sl.Angle = 120
	sl.Color = Color3.fromRGB(255, 244, 226)
	sl.Parent = lamp
	-- the window: a deep frame high in the back wall, bright sky behind thick glass
	part("WindowFrame", Vector3.new(4.4, 3.2, 0.5), Vector3.new(4, 8.4, -D / 2 + 0.2), DARK, Enum.Material.Metal)
	part("WindowSky", Vector3.new(3.6, 2.4, 0.2), Vector3.new(4, 8.4, -D / 2 + 0.5), Color3.fromRGB(176, 214, 240), Enum.Material.Neon)
	local glass = part("WindowGlass", Vector3.new(3.6, 2.4, 0.2), Vector3.new(4, 8.4, -D / 2 + 0.75), Color3.fromRGB(210, 230, 240), Enum.Material.Glass)
	glass.Transparency = 0.6
	part("WindowBar", Vector3.new(0.3, 2.4, 0.3), Vector3.new(4, 8.4, -D / 2 + 0.95), DARK, Enum.Material.Metal)
	m.Parent = map
	jailModel = m
	jailAt = base
	return m
end
local function jailSpot(i: number): CFrame
	local at = jailAt + Vector3.new(-4 + (i % 4) * 3, 3.2, -1 + ((i // 4) % 2) * 3)
	return CFrame.lookAt(at, at + Vector3.new(0, 0, 1))
end
local function inJail(pos: Vector3): boolean
	local rel = pos - jailAt
	return math.abs(rel.X) < 14 and rel.Y > -4 and rel.Y < 16 and rel.Z > -12 and rel.Z < 16
end
type Jailed = { untilT: number, party: any, lobby: any, home: CFrame?, at: number, spot: CFrame, snapT: number }
local jailed: { [any]: Jailed } = {} -- a fighter in the jail
local jailN = 0
local function release(t: any, why: string, by: Player?, move: boolean)
	local j = jailed[t]
	if not j then return end
	jailed[t] = nil
	if t.kind == "player" then
		local tp = t.ref :: Player
		if tp.Parent then tp:SetAttribute("DevJailed", nil) end
		if move and t.alive and tp.Parent and Fight.spawnAt then
			local ok, at, face = pcall(Fight.spawnAt, t)
			if ok and typeof(at) == "Vector3" then
				local pos = at + Vector3.new(0, 3.2, 0)
				local lk = if typeof(face) == "Vector3" and Vector3.new(face.X, 0, face.Z).Magnitude > 1e-3 then Vector3.new(face.X, 0, face.Z).Unit else Vector3.zAxis
				place(t, CFrame.lookAt(pos, pos + lk))
			end
		end
		log(by or tp, "out of the jail (" .. why .. ")", if by then tp.Name else nil)
	elseif move and t.alive and j.home then
		place(t, j.home)
	end
end
local function toJail(by: Player, t: any, tname: string, why: string): any
	if not jail() then return { ok = false, why = "no map" } end
	if t.kind == "player" then
		local tp = t.ref :: Player
		if Matches.raw(tp) then
			flagMatch(by, tp, why)
			pcall(Matches.pull, tp) -- (out of the match first, as if they'd left it: it counts for nothing now)
		end
	end
	if frozen[t] then setFrozen(t, false) end
	local r = Fight.root(t)
	jailN += 1
	jailed[t] = {
		untilT = now() + JAIL_TIME,
		party = if t.kind == "player" then (t.ref :: Player):GetAttribute("Party") else nil,
		lobby = if t.kind == "player" then (t.ref :: Player):GetAttribute("Lobby") else nil,
		home = if t.kind ~= "player" and r then r.CFrame else nil,
		at = now(), spot = jailSpot(jailN), snapT = now(),
	}
	if t.kind == "player" then (t.ref :: Player):SetAttribute("DevJailed", workspace:GetServerTimeNow() + JAIL_TIME) end
	place(t, jailed[t].spot)
	log(by, why, tname)
	return { ok = true, did = (if why == "red card" then "red card: " else "jailed ") .. tname }
end

-- ------------------------------------------------------------------ the red card
local DevFx = GiftFx.remote -- (JankfireRemotes.DevFx: the red card, gifts, announcements; GiftFx makes it)
local carding: { [Player]: number } = {}
local function redCard(by: Player, t: any, tname: string): any
	if now() - (carding[by] or -math.huge) < CARD_POSE + 0.3 then return { ok = false, why = "one card at a time" } end
	carding[by] = now()
	if t.kind == "player" and Matches.raw(t.ref :: Player) then flagMatch(by, t.ref :: Player, "red card") end
	;(DevFx :: RemoteEvent):FireAllClients({ k = "redcard", by = by, target = if t.kind == "player" then t.ref else nil, model = Fight.model(t), sound = WHISTLE, pose = CARD_POSE })
	log(by, "red card shown", tname)
	task.delay(CARD_POSE, function()
		if t.alive and table.find(Fight.all, t) and (t.kind ~= "player" or (t.ref :: Player).Parent) then toJail(by, t, tname, "red card") end
	end)
	return { ok = true, did = "red card: " .. tname }
end

-- ------------------------------------------------------------------ TEMP DEV: lend, end
local function holder(t: any): Player?
	if frozen[t] or jailed[t] then return heldBy[t] end
	return nil
end
-- their access ends (time, left, revoked): every power off, the ones they froze let go, and they're told
local function endTemp(q: Player, why: string, by: Player?)
	local t = temps[q]
	if not t then return end
	temps[q] = nil
	if q.Parent then
		q:SetAttribute("DevTemp", nil)
		local s = states[q]
		if s then
			s.fly, s.noclip, s.speed, s.arms, s.invis = false, false, 1, false, false
			publish(q, s)
		end
		if q:GetAttribute("DevInvisible") == true then setInvisible(q, false) end
		pcall(function() (DevFx :: RemoteEvent):FireClient(q, { k = "devaccess", on = false }) end)
	end
	for f, who in heldBy do
		if who == q then
			if frozen[f] then setFrozen(f, false) end
			heldBy[f] = nil
		end
	end
	log(by or q, ("temp dev ended (%s)"):format(why), if by then q.Name else nil)
	acNote(q, "temp dev ended", why .. (if by then " by " .. by.Name else ""))
end
-- the owner lends it: mins 15 / 30 / 60, or 0 = until they leave (again on someone who has it: the new time).
-- secs: Studio tests only, a short one to see it run out
local function grant(by: Player, q: Player, mins: number, secs: number?, test: boolean?): any
	if not TEMP_TIMES[mins] and not secs then return { ok = false, why = "15, 30 or 60 minutes, or until they leave" } end
	if not test and (q == by or isOwner(q)) then return { ok = false, why = "not yourself" } end
	if q.Parent ~= Players then return { ok = false, why = "they've left" } end
	local long = secs or (if mins > 0 then mins * 60 else nil)
	local again = temps[q] ~= nil
	local t: Temp = { untilT = if long then now() + long else nil, ends = if long then os.time() + math.ceil(long) else 0, by = by, mins = mins }
	temps[q] = t
	q:SetAttribute("DevTemp", t.ends)
	pcall(function() (DevFx :: RemoteEvent):FireClient(q, { k = "devaccess", on = true, ends = t.ends, from = string.sub(by.DisplayName, 1, 32) }) end)
	local what = if secs then ("%d s (test)"):format(math.ceil(secs)) elseif mins > 0 then ("%d min"):format(mins) else "until they leave"
	log(by, ("temp dev %s (%s)"):format(if again then "changed" else "given", what), q.Name)
	acNote(q, "temp dev given", what .. ", by " .. by.Name)
	return { ok = true, did = ("%s has dev %s"):format(q.DisplayName, if long then "for " .. what else "until they leave") }
end

-- ------------------------------------------------------------------ gifts
-- (18 Nov 2026, the owner: "let me gift people stuff! bundles, cases bags cans at any quantity coins vip etc"). the
-- GIFT tab's "gift" op. every gift goes through the owning module's own grant, never the client:
--   container (crate / bag / spray, 1..999)       Loot.grant(p, id, receipt, n)   (the loot save: one write, one receipt)
--   bundle (a shop bundle or skin set, whole)     Loot.grant(p, bundleId, receipt)
--   item (a wrap, hat, skin, kill effect, emote, grapple or card look; wraps and hats on every gun)
--                                                 Loot.grant(p, "gift:<kind>:<id>", receipt)
--   brass ("coins": the same thing) / tickets     Quests.gift(p, brass, tickets, receipt)
--   vip (for good)                                Vip.gift(p, true)                   (the shop's: saved in JankfireVip)
--   weapon (a Robux one: Unlocks.ROBUX)           Purchases.giveWeapon(p, wid, "gift", receipt)   (the shop's)
--   (19 Nov, the owner: "allow me to also give people xp, I want to be able to unlock stuff for my friends!!")
--   xp: account XP or a level, weapon mastery XP or a mastery level
--                                                 Stats.gift(p, { xp | level | w + xp | w + level }, receipt)
--                                                 (the same XP a match gives: the level-up toast, the weapons a level
--                                                 opens, mastery's camos at their levels; a level only goes up; never
--                                                 near ranked; the receipt in the stats save with the XP)
--   unlock: one weapon with a lock (the 4 Robux ones, any level one), or UNLOCK ALL WEAPONS
--                                                 Purchases.unlockWeapons(p, wids, "gift", receipt)   (for good, like
--                                                 an early coin unlock: RobuxOwned; one write for all of them)
--   never the OWNER title (GiftFx.describe refuses it): that stays the owner's alone
-- what a thing is called and what its present shows come from GiftFx.describe (shared with the shop's paid gifts).
-- the receiver gets the present (GiftFx.present: GiftReveal.client; a toast in a match, the present at the break),
-- and a gift to someone else is said in the server's chat for everyone (GiftFx.say, 18 Nov: "when you gift someone it
-- has to be noticeable"): "<giver> gifted <receiver> <what>", from the two display names and the thing's own plain
-- name, never from anything typed. every gift is written to a gift log (giver, receiver, what, how many, when: user ids
-- only) in its own store, Studio apart from live. a gift in a match flags nothing: it doesn't change the fight
local giftStore: DataStore? = nil
pcall(function() giftStore = game:GetService("DataStoreService"):GetDataStore(if STUDIO then "JankDevGifts_v1_studio" else "JankDevGifts_v1") end)
local function storeRow(key: string, row: any, keep: number)
	if not giftStore then return end
	task.spawn(function()
		pcall(function()
			(giftStore :: DataStore):UpdateAsync(key, function(old: any)
				local list = if type(old) == "table" then old else {}
				table.insert(list, row)
				while #list > keep do table.remove(list, 1) end
				return list
			end)
		end)
	end)
end
local function giftLog(by: Player, to: Player, what: string, n: number)
	storeRow("log", { t = os.time(), by = by.UserId, to = to.UserId, what = what, n = n }, 500)
end
local mods: { [string]: any } = {}
local function mod(name: string): any
	local m = mods[name]
	if m ~= nil then return m or nil end
	local sc = script.Parent:FindFirstChild(name)
	local ok, r = false, nil
	if sc and sc:IsA("ModuleScript") then ok, r = pcall(require, sc) end
	mods[name] = if ok and type(r) == "table" then r else false
	return mods[name] or nil
end
local giftN = 0
local function receipt(to: Player): string
	giftN += 1
	return ("devgift-%d-%d-%d"):format(to.UserId, os.time(), giftN)
end
-- give one player a described thing (GiftFx.describe) under the receipt rid, through the module that owns it.
-- (true, "already") when there was nothing new to give: the same receipt again (a second delivery of one event), VIP
-- they have, a weapon they own
local function give(to: Player, spec: any, rid: string): (boolean, string?)
	local k = spec.kind
	if k == "container" or k == "bundle" or k == "item" then
		local Loot = mod("Loot")
		if not Loot then return false, "no loot module" end
		if type(Loot.hasReceipt) == "function" and Loot.hasReceipt(to, rid) then return true, "already" end
		if k == "container" then
			if Loot.GRANT_COUNT == true then -- (the loot module takes a count: one write, one receipt)
				if not Loot.grant(to, spec.id, rid, spec.qty) then return false, "their loot save isn't ready" end
			else -- (until it does: one grant, one save each, so at most 25)
				if spec.qty > 25 then return false, "25 at a time until the loot module takes a count" end
				for i = 1, spec.qty do
					if not Loot.grant(to, spec.id, rid .. "-" .. i) then return false, "their loot save isn't ready" end
				end
			end
		elseif k == "bundle" then
			if not Loot.grant(to, spec.id, rid) then return false, "their loot save isn't ready" end
		elseif not Loot.grant(to, "gift:" .. spec.id, rid) then
			return false, "not given (their loot save isn't ready, or that can't be gifted)"
		end
		return true, nil
	elseif k == "brass" or k == "tickets" then
		local Q = mod("Quests")
		if not Q or type(Q.gift) ~= "function" then return false, "not ready" end
		local ok, why = Q.gift(to, if k == "brass" then spec.qty else 0, if k == "tickets" then spec.qty else 0, rid)
		if not ok then return false, tostring(why) end
		return true, if why == "already" then "already" else nil
	elseif k == "vip" then
		local V = mod("Vip")
		if not V or type(V.gift) ~= "function" then return false, "VIP gifts aren't in yet" end
		if V.isVip(to) then return true, "already" end
		local ok, why = V.gift(to, true)
		if not ok then return false, tostring(why or "not given") end
		return true, nil
	elseif k == "weapon" then
		local Pu = mod("Purchases")
		if not Pu or type(Pu.giveWeapon) ~= "function" then return false, "weapon gifts aren't in yet" end
		local ok, why = Pu.giveWeapon(to, spec.id, "gift", rid)
		if not ok then return false, tostring(why or "not given") end
		return true, if why == "already" then "already" else nil
	elseif k == "unlock" then
		local Pu = mod("Purchases")
		if not Pu or type(Pu.unlockWeapons) ~= "function" then return false, "weapon unlocks aren't in yet" end
		local ok, _, why = Pu.unlockWeapons(to, spec.ids, "gift", rid)
		if not ok then return false, tostring(why or "not given") end
		return true, if why == "already" then "already" else nil
	elseif k == "xp" then
		local S = mod("Stats")
		if not S or type(S.gift) ~= "function" then return false, "XP gifts aren't in yet" end
		local ok, why = S.gift(to, spec.stats, rid)
		if not ok then return false, tostring(why or "not given") end
		return true, if why == "already" then "already" else nil
	end
	return false, "nope"
end
local function gift(p: Player, to: Player, kind: unknown, id: unknown, n: unknown): any
	local spec, why = GiftFx.describe(kind, id, n)
	if not spec then return { ok = false, why = why } end
	local ok, how = give(to, spec, receipt(to))
	if not ok then return { ok = false, why = how } end
	if how == "already" then return { ok = false, why = if spec.kind == "xp" then "they're past that already" else "they have it already" } end
	GiftFx.present(to, p.DisplayName, spec)
	if to ~= p then GiftFx.say(p.DisplayName, to.DisplayName, spec.plain) end
	giftLog(p, to, spec.what, spec.qty)
	log(p, ("gift %s x%d to"):format(spec.what, spec.qty), to.Name)
	return { ok = true, did = ("gave %s %s"):format(to.Name, spec.label) }
end

-- ------------------------------------------------------------------ gift everyone, and announcements
-- (19 Nov 2026, round 4, the owner: "from my command menu allow me to gift everyone stuff and write announcements that
-- go across the screen across all servers, it'll be helpful for admin abuse!!"). both are EVENTS:
--   { id, k = "gift" | "announce", by = the owner's user id, from = the owner's display name, kind/item/qty or text }
-- "this server" plays the event here. "all servers" publishes it once over MessagingService (EVENT_TOPIC: only this
-- game's own servers can publish to it, and only an owner's command here does; a server plays only events whose by is
-- the place's creator) and every live server plays it for the players it has right then:
--   GIFT EVERYONE: each player gets the thing under the receipt "ownerev-<id>" (Loot's receipts, Quests' grants), so
--   one event never gives anyone twice: not a second delivery, not a player who hopped servers. VIP they have or a
--   weapon they own is skipped. a save still loading is tried again for a minute. then their present (in a match: at
--   the break) and one chat line per server, "<owner> gifted everyone <what>". players who join later get nothing
--   ANNOUNCE: typed text, so Roblox's filter has it on the owner's server before anything is sent or shown
--   (TextService:FilterStringAsync(text, owner, PublicChat), then GetNonChatStringForBroadcastAsync); a filter that
--   doesn't answer sends nothing. every client shows the banner (AnnounceBanner.client: across the screen for about
--   6 s; smaller, high and clear of the crosshair in a match) and the chat gets "[ANNOUNCEMENT] <owner>: <text>"
-- a server plays an event id once (seen). each server adds itself to the event's reach (a MemoryStore hash map, a day);
-- REACH_WAIT s on, the owner's server reads it, logs it, writes the event to the gift log ("events") and toasts the owner
-- limits: one gift-everyone every EVERYONE_GAP s, one announcement every ANNOUNCE_GAP s (MessagingService takes far more)
-- Studio: its own topic and map (JankOwnerEvent_studio, jfs_ownerev): a test never reaches a live server
local MessagingService = game:GetService("MessagingService")
local MemoryStoreService = game:GetService("MemoryStoreService")
local HttpService = game:GetService("HttpService")
local TextService = game:GetService("TextService")
local EVENT_TOPIC = if STUDIO then "JankOwnerEvent_studio" else "JankOwnerEvent"
local REACH_MAP = if STUDIO then "jfs_ownerev" else "jf_ownerev"
local REACH_WAIT = 75 -- s
local EVERYONE_GAP = 5 -- s
local ANNOUNCE_GAP = 10 -- s
local ANNOUNCE_MAX = 120 -- characters
local seen: { [string]: number } = {}
local received = 0 -- (events that came in over MessagingService: Studio's check of the publish -> receive path)
local function newId(): string
	return ("%x%s"):format(os.time(), string.sub((string.gsub(HttpService:GenerateGUID(false), "-", "")), 1, 8))
end
local function reach(id: string, players: number)
	task.spawn(function()
		pcall(function()
			MemoryStoreService:GetHashMap(REACH_MAP):UpdateAsync(id, function(old: any)
				local v = if type(old) == "table" then old else { s = 0, p = 0 }
				v.s = (tonumber(v.s) or 0) + 1
				v.p = (tonumber(v.p) or 0) + players
				return v
			end, 86400)
		end)
	end)
end
-- is it an owner's event this server hasn't played? (marks it played)
local function accept(ev: any): (boolean, string?)
	if type(ev) ~= "table" or type(ev.id) ~= "string" or #ev.id < 4 or #ev.id > 40 then return false, "not an event" end
	if game.CreatorType ~= Enum.CreatorType.User or ev.by ~= game.CreatorId then return false, "not the owner's" end
	if seen[ev.id] then return false, "already" end
	seen[ev.id] = os.time()
	return true, nil
end
-- everyone here gets the thing (each in its own thread: a loading save is tried again for a minute); the reach counts
-- those given once all are done
local function giveEveryone(spec: any, id: string, fromName: string): number
	local list = Players:GetPlayers()
	local left, gave = #list, 0
	local rid = "ownerev-" .. id
	for _, q in list do
		task.spawn(function()
			for _ = 1, 20 do
				if not q.Parent then break end
				local ok, how = give(q, spec, rid)
				if ok then
					if how ~= "already" then
						gave += 1
						GiftFx.present(q, fromName, spec)
					end
					break
				end
				task.wait(3)
			end
			left -= 1
			if left == 0 then reach(id, gave) end
		end)
	end
	if #list == 0 then reach(id, 0) end
	return #list
end
local function play(ev: any, how: string): (boolean, string?)
	local from = string.sub(tostring(ev.from or "The owner"), 1, 32)
	if ev.k == "announce" then
		if type(ev.text) ~= "string" or ev.text == "" then return false, "no text" end
		local text = string.sub(ev.text, 1, ANNOUNCE_MAX * 4)
		DevFx:FireAllClients({ k = "announce", text = text, from = from })
		GiftFx.line(("[ANNOUNCEMENT] %s: %s"):format(from, text))
		reach(ev.id, #Players:GetPlayers())
		print(("[dev] event %s (%s): announcement shown to %d players"):format(ev.id, how, #Players:GetPlayers()))
		return true, nil
	elseif ev.k == "gift" then
		local spec, why = GiftFx.describe(ev.kind, ev.item, ev.qty)
		if not spec then return false, why end
		local n = giveEveryone(spec, ev.id, from)
		GiftFx.say(from, "everyone", spec.plain)
		print(("[dev] event %s (%s): %s x%d for everyone here (%d players)"):format(ev.id, how, spec.what, spec.qty, n))
		return true, nil
	end
	return false, "nope"
end
task.spawn(function()
	for i = 1, 6 do
		local ok, err = pcall(function()
			MessagingService:SubscribeAsync(EVENT_TOPIC, function(msg: any)
				received += 1
				local ev = if type(msg) == "table" then msg.Data else nil
				if accept(ev) then
					local ok2, why = play(ev, "msg")
					if not ok2 then warn("[dev] an owner event didn't play here: " .. tostring(why)) end
				end
			end)
		end)
		if ok then return end
		warn(("[dev] owner events: no subscription yet (%s)"):format(tostring(err)))
		task.wait(10 * i)
	end
end)
-- the owner starts one: here, or everywhere (published first; if that fails nothing happens, live)
local last = { gift = -math.huge, announce = -math.huge }
local function startEvent(p: Player, ev: any, scope: string, what: string): (boolean, string?)
	local ok, why = accept(ev)
	if not ok then return false, why end
	local note = nil
	if scope == "all" then
		local sent, err = pcall(function() MessagingService:PublishAsync(EVENT_TOPIC, ev) end)
		if not sent then
			if not STUDIO then return false, "couldn't reach the other servers: nothing sent" end
			note = "(Studio: the publish was refused, so this server only)"
			log(p, "owner event publish refused in Studio:", string.sub(tostring(err), 1, 100))
		end
	end
	local played, why2 = play(ev, "here")
	if not played then return false, why2 end
	task.delay(REACH_WAIT, function()
		local r: any = nil
		pcall(function() r = MemoryStoreService:GetHashMap(REACH_MAP):GetAsync(ev.id) end)
		local servers = if type(r) == "table" then tonumber(r.s) else nil
		local players = if type(r) == "table" then tonumber(r.p) else nil
		local line = ("event %s (%s, %s): reached %s servers, %s players"):format(ev.id, scope, what,
			if servers then tostring(servers) else "?", if players then tostring(players) else "?")
		log(p, line, nil)
		storeRow("events", { t = os.time(), by = p.UserId, id = ev.id, k = ev.k, scope = scope, what = what, servers = servers, players = players }, 200)
		if p.Parent then
			DevFx:FireClient(p, { k = "gift", text = ("%s · %s SERVERS · %s PLAYERS"):format(if ev.k == "announce" then "ANNOUNCEMENT" else "GIFT EVERYONE",
				if servers then tostring(servers) else "?", if players then tostring(players) else "?") })
		end
	end)
	return true, note
end
local function giftEveryone(p: Player, scope: unknown, b: unknown): any
	if scope ~= "server" and scope ~= "all" then return { ok = false, why = "this server or all servers" } end
	if type(b) ~= "table" then return { ok = false, why = "nope" } end
	local spec, why = GiftFx.describe((b :: any).kind, (b :: any).id, (b :: any).n)
	if not spec then return { ok = false, why = why } end
	local wait = EVERYONE_GAP - (now() - last.gift)
	if wait > 0 then return { ok = false, why = ("one every %d s: %d s to go"):format(EVERYONE_GAP, math.ceil(wait)) } end
	last.gift = now()
	-- (the kind as asked, not spec.kind: every server describes it again from these, and "level" or "mastery" come out
	-- as spec.kind "xp")
	local ev = { id = newId(), k = "gift", by = p.UserId, from = string.sub(p.DisplayName, 1, 32), kind = (b :: any).kind, item = spec.id, qty = spec.qty }
	local ok, note = startEvent(p, ev, scope :: string, spec.what)
	if not ok then last.gift = -math.huge; return { ok = false, why = note } end
	log(p, ("gift everyone (%s): %s x%d, event"):format(scope :: string, spec.what, spec.qty), ev.id)
	return { ok = true, id = ev.id, did = (if scope == "all" then "sent to every server: %s for everyone there now" else "gave everyone here %s"):format(spec.label)
		.. (if note then " " .. note else "") }
end
local announcing = false
local function announce(p: Player, text: unknown, scope: unknown): any
	if scope ~= "server" and scope ~= "all" then return { ok = false, why = "this server or all servers" } end
	if type(text) ~= "string" then return { ok = false, why = "type something" } end
	local t = string.gsub(text, "%c", " ")
	t = string.gsub(t, "%s+", " ")
	t = string.match(t, "^%s*(.-)%s*$") or ""
	local len = utf8.len(t)
	if not len or len == 0 then return { ok = false, why = "type something" } end
	if len > ANNOUNCE_MAX then return { ok = false, why = ("%d letters at most"):format(ANNOUNCE_MAX) } end
	if announcing then return { ok = false, why = "one at a time" } end
	local wait = ANNOUNCE_GAP - (now() - last.announce)
	if wait > 0 then return { ok = false, why = ("one every %d s: %d s to go"):format(ANNOUNCE_GAP, math.ceil(wait)) } end
	announcing = true
	local clean: string? = nil
	local okF = pcall(function()
		local res = TextService:FilterStringAsync(t, p.UserId, Enum.TextFilterContext.PublicChat)
		clean = res:GetNonChatStringForBroadcastAsync()
	end)
	if not okF or type(clean) ~= "string" or clean == "" then
		announcing = false
		return { ok = false, why = "Roblox's filter didn't answer: nothing sent" }
	end
	local ev = { id = newId(), k = "announce", by = p.UserId, from = string.sub(p.DisplayName, 1, 32), text = clean }
	local ok, note = startEvent(p, ev, scope :: string, "announcement")
	announcing = false
	if not ok then return { ok = false, why = note } end
	last.announce = now()
	log(p, ("announce (%s): %s"):format(scope :: string, clean :: string), nil)
	return { ok = true, id = ev.id, filtered = clean ~= t,
		did = (if scope == "all" then "announced in every server" else "announced here") .. (if clean ~= t then " (the filter changed some of it)" else "")
			.. (if note then " " .. note else "") }
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
		-- (owner = the place's creator, temp = when their TEMP DEV ends, 0 = until they leave; held = the owner holds them)
		local h = f and holder(f)
		table.insert(out, { ref = q, name = q.DisplayName, user = q.Name, zone = Zones.of(q), frozen = f ~= nil and frozen[f] ~= nil, jailed = f ~= nil and jailed[f] ~= nil,
			owner = isOwner(q), temp = if isTemp(q) then (temps[q] :: Temp).ends else nil, held = h ~= nil and isOwner(h) })
	end
	table.sort(out, function(a, b) return a.name < b.name end)
	if STUDIO then
		for _, f in Fight.all do
			if f.kind == "dummy" and f.ref and f.alive then
				-- (a dummy with DevStandIn = "owner" / "temp" stands in for the owner or a temp dev in a test)
				local si = (f.ref :: Instance):GetAttribute("DevStandIn")
				local h = holder(f)
				table.insert(out, { ref = f.ref, name = f.name, user = "dummy", zone = "dummy", frozen = frozen[f] ~= nil, jailed = jailed[f] ~= nil,
					owner = si == "owner", temp = if si == "temp" then 0 else nil, held = h ~= nil and isOwner(h) })
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
	local owner = isOwner(p)
	if not owner and not isTemp(p) then
		if not refused[p] then
			refused[p] = true
			log(p, "refused (not the owner): " .. string.sub(tostring(op), 1, 20), nil)
		end
		return { ok = false, why = "owner only" }
	end
	if not spend(p) then return { ok = false, why = "slow down" } end
	-- (a temp dev: the powers only. GIFT, XP, UNLOCKS, ANNOUNCE, granting and the rest are refused by who sent it)
	if not owner and not TEMP_OPS[tostring(op)] then
		log(p, "refused (the owner's only): " .. string.sub(tostring(op), 1, 20), nil)
		return { ok = false, why = "the owner's only" }
	end
	local s = stateOf(p)
	local zone = Zones.of(p)
	if op == "hello" or op == "state" then
		return { ok = true, owner = owner, temp = not owner, ends = if not owner then (temps[p] :: Temp).ends else nil,
			studio = STUDIO, zone = zone, state = view(s), log = lines[#lines] }
	elseif op == "players" then
		return { ok = true, players = list(p), zone = zone }
	elseif op == "grant" then -- (the owner only: a = the player, b = minutes 15 / 30 / 60, or 0 = until they leave)
		local q = if typeof(a) == "Instance" and (a :: Instance):IsA("Player") then a :: Player else nil
		if not q then return { ok = false, why = "nobody" } end
		return grant(p, q, tonumber(b) or -1, nil)
	elseif op == "revoke" then -- (a = the player)
		local q = if typeof(a) == "Instance" and (a :: Instance):IsA("Player") then a :: Player else nil
		if not q or not temps[q] then return { ok = false, why = "they don't have it" } end
		endTemp(q, "revoked", p)
		return { ok = true, did = ("%s's dev access ended"):format(q.DisplayName) }
	elseif op == "revokeAll" then
		local list2 = {}
		for q in temps do table.insert(list2, q) end
		for _, q in list2 do endTemp(q, "revoked", p) end
		return { ok = true, did = ("ended %d"):format(#list2) }
	end
	if zone == "match" and op ~= "gift" and op ~= "giftAll" and op ~= "announce" and not (op == "set" and (a == "off" or b == false)) then flagMatch(p, p, tostring(op)) end
	if op == "set" then
		if a == "fly" then s.fly = b == true
		elseif a == "flySpeed" and type(b) == "number" and b == b then s.flySpeed = math.floor(math.clamp(b, FLY.min, FLY.max) + 0.5)
		elseif a == "noclip" then s.noclip = b == true
		elseif a == "speed" and type(b) == "number" and b == b then s.speed = math.floor(math.clamp(b, RUN.min, RUN.max) * 4 + 0.5) / 4
		elseif a == "arms" then s.arms = b == true
		elseif a == "invis" then s.invis = b == true
		elseif a == "off" then s.fly, s.noclip, s.speed, s.arms, s.invis = false, false, 1, false, false
		else return { ok = false, why = "nope" } end
		publish(p, s)
		if (p:GetAttribute("DevInvisible") == true) ~= s.invis then setInvisible(p, s.invis) end
		log(p, ("%s %s"):format(tostring(a), if a == "off" then "" else tostring(if a == "flySpeed" then s.flySpeed elseif a == "speed" then s.speed else b)), nil)
		return { ok = true, state = view(s) }
	elseif op == "emptyJail" then
		local list, n = {}, 0
		for t in jailed do table.insert(list, t) end
		for _, t in list do release(t, "let go", p, true); n += 1 end
		log(p, "empty the jail", tostring(n))
		return { ok = true, did = ("let %d out"):format(n) }
	elseif op == "gift" then
		-- a: who gets it (a Player in this server, the owner too), b: { kind, id, n }
		local to = if typeof(a) == "Instance" and (a :: Instance):IsA("Player") and (a :: Instance).Parent == Players then a :: Player else nil
		if not to then return { ok = false, why = "nobody" } end
		if type(b) ~= "table" then return { ok = false, why = "nope" } end
		return gift(p, to, (b :: any).kind, (b :: any).id, (b :: any).n)
	elseif op == "giftAll" then -- (a: "server" or "all", b: { kind, id, n })
		return giftEveryone(p, a, b)
	elseif op == "announce" then -- (a: the text, b: "server" or "all")
		return announce(p, a, b)
	elseif op == "unfreezeAll" then
		local n = unfreezeAll()
		log(p, "unfreeze all", tostring(n))
		return { ok = true, did = ("let %d go"):format(n) }
	end
	-- the rest are done to someone: a target, or (the Aim ones) whoever the owner looks at
	local t, tname
	if op == "flingAim" or op == "freezeAim" or op == "redcardAim" then
		t = aimed(p, a)
		if not t then return { ok = false, why = "nobody there" } end
		tname = if t.kind == "player" then (t.ref :: Player).Name else t.name .. " (dummy)"
	else
		t, tname = targetOf(a)
		if not t then return { ok = false, why = tname } end
	end
	if t == Fight.byPlayer[p] then return { ok = false, why = "not yourself" } end
	if not owner then
		-- (TEMP DEV: never the owner, another temp dev, or someone the owner is holding. in Studio a dummy with
		-- DevStandIn = "owner" / "temp" stands in for one)
		local tp = if t.kind == "player" then t.ref :: Player else nil
		local si = if STUDIO and t.kind == "dummy" and typeof(t.ref) == "Instance" then (t.ref :: Instance):GetAttribute("DevStandIn") else nil
		local why = if (tp and isOwner(tp)) or si == "owner" then "not the owner"
			elseif (tp and isTemp(tp)) or si == "temp" then "not another dev"
			else nil
		local h = holder(t)
		if not why and h and h ~= p and isOwner(h) then why = "the owner is holding them" end
		if why then
			log(p, ("refused (%s): %s"):format(why, tostring(op)), tname)
			return { ok = false, why = why }
		end
	end
	if not t.alive then return { ok = false, why = "they're down" } end
	if t.kind == "player" and zoneOfF(t) == "match" then flagMatch(p, t.ref :: Player, tostring(op) .. " on them") end
	if op == "fling" or op == "flingAim" then
		return fling(p, t, tname, if typeof(a) == "Vector3" then a :: Vector3 else nil)
	elseif op == "freeze" or op == "freezeAim" then
		local on = if op == "freezeAim" then frozen[t] == nil else b ~= false
		setFrozen(t, on)
		heldBy[t] = if on then p else nil
		log(p, if on then "freeze" else "unfreeze", tname)
		return { ok = true, did = (if on then "froze " else "let go ") .. tname }
	elseif op == "redcard" or op == "redcardAim" then
		local res = redCard(p, t, tname)
		if res.ok then heldBy[t] = p end
		return res
	elseif op == "jail" then
		if jailed[t] then return { ok = false, why = "already in" } end
		local res = toJail(p, t, tname, "jail")
		if res.ok then heldBy[t] = p end
		return res
	elseif op == "release" then
		if not jailed[t] then return { ok = false, why = "not in the jail" } end
		release(t, "let go", p, true)
		heldBy[t] = nil
		return { ok = true, did = "let " .. tname .. " out" }
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
			if jailed[t] then release(t, "brought", p, false) end
			heldBy[t] = nil
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
	-- (a temp dev's too, never on the owner or another temp dev)
	if isTemp(by) and not isOwner(by) and (isOwner(t) or isTemp(t)) then return false end
	return by:GetAttribute("DevArms") == true and isDev(by) and HIT_ZONES[Zones.of(by)] == true and HIT_ZONES[Zones.of(t)] == true
end
-- a kill outside a match by the owner (a dev weapon, a fall after a fling): counts for nothing, back at once
Fight.DEV_RESPAWN = 1
Fight.devKill = function(info: any): boolean
	local k, v = info.k, info.v
	if not k or k == v or k.kind ~= "player" or v.kind ~= "player" then return false end
	local kp, vp = k.ref :: Player, v.ref :: Player
	return isDev(kp) and Zones.of(vp) ~= "match" and Zones.of(kp) ~= "match"
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
	for d in kept do if not d.Parent then kept[d] = nil end end -- (an invisible body that's gone: forget its things)
	-- the jail: out on time, on joining a party or a lobby, when they die or anything else moves them out
	for f, j in jailed do
		if f.kind == "player" then
			local tp = f.ref :: Player
			local r = Fight.root(f)
			if not tp.Parent then jailed[f] = nil
			elseif t >= j.untilT then release(f, "time", nil, true)
			elseif tp:GetAttribute("Party") ~= j.party and tp:GetAttribute("Party") ~= nil then release(f, "joined a party", nil, true)
			elseif tp:GetAttribute("Lobby") ~= j.lobby and tp:GetAttribute("Lobby") ~= nil then release(f, "joined a lobby", nil, false)
			elseif not f.alive or Zones.of(tp) == "match" or Zones.of(tp) == "staging" then release(f, "moved out", nil, false)
			elseif r and not inJail(r.Position) then
				-- (the first 2.5 s: their client may still send where it was before the move. put them back in; after that,
				-- something else moved them: they're out)
				if t - j.at < 2.5 then
					if t - j.snapT > 0.4 then j.snapT = t; place(f, j.spot) end
				else
					release(f, "moved out", nil, false)
				end
			end
		elseif not f.alive or not table.find(Fight.all, f) then jailed[f] = nil
		elseif t >= j.untilT then release(f, "time", nil, true)
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
	-- TEMP DEV: out at its time
	for q, tm in temps do
		if not q.Parent then temps[q] = nil
		elseif tm.untilT and t >= (tm.untilT :: number) then endTemp(q, "time", nil) end
	end
	-- (only the server writes these, and only on the owner or a temp dev: anyone else's are wiped)
	for _, p in Players:GetPlayers() do
		if not states[p] and (p:GetAttribute("DevOn") ~= nil or p:GetAttribute("DevArms") ~= nil or p:GetAttribute("DevFly") ~= nil) then
			for _, k in { "DevOn", "DevArms", "DevFly", "DevNoclip", "DevSpeed" } do p:SetAttribute(k, nil) end
		end
		if not temps[p] and p:GetAttribute("DevTemp") ~= nil then p:SetAttribute("DevTemp", nil) end
	end
end)

local function added(p: Player)
	-- "/dev" in the legacy chat opens the menu (OwnerDev.client watches DevPanel)
	p.Chatted:Connect(function(msg: string)
		if string.lower(string.sub(msg, 1, 4)) == "/dev" and isDev(p) then p:SetAttribute("DevPanel", os.clock()) end
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
	if temps[p] then endTemp(p, "left", nil) end
	if states[p] then
		states[p] = nil
		if isOwner(p) then unfreezeAll() end -- (the owner leaving lets everyone go; a temp dev's own went free just above)
	end
	for _, c in invisConns[p] or {} do c:Disconnect() end
	invisConns[p] = nil
	carding[p] = nil
	local f = Fight.byPlayer[p]
	if f then frozen[f] = nil; jailed[f] = nil; heldBy[f] = nil end
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
			out.jailed = {}
			for f, j in jailed do table.insert(out.jailed, ("%s %.0fs"):format(f.name, j.untilT - now())) end
			out.jailAt = jailAt
			out.jailBuilt = jailModel ~= nil and jailModel.Parent ~= nil
			for p, s in states do
				out.owners[p.Name] = { state = view(s), attrs = { DevOn = p:GetAttribute("DevOn"), DevFly = p:GetAttribute("DevFly"), DevNoclip = p:GetAttribute("DevNoclip"), DevSpeed = p:GetAttribute("DevSpeed"), DevArms = p:GetAttribute("DevArms") } }
			end
			out.log = lines
			return out
		elseif op == "as" then
			return handle(a, b, c, d)
		elseif op == "log" then
			return lines
		elseif op == "giftLine" then -- (a gift's chat line to a stand-in receiver's name: a = the giver, b = the name, c = what)
			GiftFx.say((a :: Player).DisplayName, tostring(b), tostring(c))
			return true
		elseif op == "event" then -- (a = an event, as another server gets it over MessagingService: played once per id)
			local ok, why = accept(a)
			if not ok then return { ran = false, why = why } end
			local played, why2 = play(a, "test")
			return { ran = played, why = why2 }
		elseif op == "grant" then -- (TEMP DEV for a test: a = the player, b = minutes or 0, c = seconds instead. with TestNotOwner
			-- on, the Studio player is the friend, granted as if by the owner)
			return grant(a, a, tonumber(b) or 0, tonumber(c), true)
		elseif op == "revoke" then
			if not temps[a] then return false end
			endTemp(a, "revoked (test)", nil)
			return true
		elseif op == "temps" then
			local out = {}
			for q, tm in temps do out[q.Name] = { ends = tm.ends, left = if tm.untilT then (tm.untilT :: number) - now() else -1, live = isTemp(q) } end
			return out
		elseif op == "forget" then -- (a = an event id: this server forgets it played it, like a server that never had it)
			seen[tostring(a)] = nil
			return true
		elseif op == "events" then -- (how many came in over MessagingService; the ids played here)
			local ids = {}
			for id in seen do table.insert(ids, id) end
			return { received = received, seen = ids, topic = EVENT_TOPIC }
		end
		return nil
	end
	fn.Parent = ServerStorage
end
