--!strict
-- THE BACK LOT (16 Nov 2026): the training area's secret outdoor grounds behind the big garage door at the end of the
-- dummy yard, and the little easter egg that opens it. three GOLD CARLS hide in the training rooms; shoot all three
-- within 90 seconds of the first and the garage door is yours (the key, below). EVERYONE'S OWN (owner, 17 Nov, from
-- the friends' preview: "yellow dummies to enter outside once shot by someone dont appear for others"): every player
-- has their own three gold Carls, their own 90 s and their own count. a gold Carl carries the attribute Owner (the
-- player's UserId: every other screen takes him out of its world, TrainingDoors.client, as the range's Carls) and
-- f.onlyFor (the player: nobody else's shot lands on him, Fight.hurt), so the shot is still the server's to judge.
-- how far you are is your attributes LotGold (bits 1, 2, 4: the ones you have found) and LotGoldBy (server time your
-- clock runs out); the panel over the door shows yours on your screen (one cardboard man lit per gold Carl you found,
-- your clock), with a ding where he stood and a buzz when your time is up. a key holder's are found for good: none
-- stand for them, and the panel shows all three. out on the lot, cardboard Carls on the long lane and in
-- the blocks fold when shot and stand back up. you leave the lot by its side door (EXIT: down to the basement and up
-- its walk-out into the range, on foot) or the garage while it is open. while you are on the lot (attribute OnLot) the Plinker in the yard leaves you alone.
-- a Carl here is a real fighter of kind "dummy", made like RangeTest's (so every weapon and hit check works on him).
-- the door (owner, 16 Nov: "when you go up to garage doors can they slide up"): it rolls up when someone walks up to
-- it from the lot (it always lets you back in); on the yard's side it lifts a hand's width, rattles and drops while
-- LOCKED flashes. the slats move on each player's screen (TrainingDoors.client, from the Door's attributes From,
-- Goal, Dur, Since and Rattle); here the server only decides when, and whether the slats block.
-- YOURS FOR GOOD (owner, 17 Nov: "once you find the golden dummies, the main garage is permanently open for you"):
-- whoever shoots their three gets the key, kept in their own session-locked save
-- (Profiles, store "JankfireLot_v1": { egg, eggAt }, like Stats and Quests keep theirs, so a write here can never
-- touch what you own) and shown as the player attribute LotKey. for a key holder the door is up on their own screen
-- from the moment they are there, and its slats and block let them through (TrainingDoors.client: their own body is
-- theirs to move; the anti-cheat already skips this door): the reveal is the door rolling up on their screen. for
-- everyone else it stays shut. key holders don't open, hold or rattle the door for others. the map is data, made by
-- ServerStorage.PolishBackup.
-- TrainingLot into Hub.TrainingGround.Lot:
--   Door       (Model) parts with the attribute Shut (their shut CFrame); its attributes Lift (studs it goes up) and
--              Top (a slat whose bottom is over this height is put away inside the wall)
--   Doorway    (Part, unseen) a body inside it holds the door open (nobody is shut in it)
--   Panel      parts with the attribute Pip (1, 2, 3: the cardboard men that light up) and a part Timer whose Gui has Text
--              (both painted on each screen, TrainingDoors.client; the door's sounds are in Timer)
--   Beacons    models tagged HubSpin (HubLife turns them while Spin > 0); parts in them with the attribute Lens glow
--   GoldSpots  parts Gold1..Gold3: where a gold Carl stands (its look = the way he faces)
--   Targets    parts: where a lot Carl stands (its look points at the shooters)
--   Area       (Parts, unseen, one or more: the loading bay, past the façade) inside one a player is on the lot
-- nothing happens while the training area is v1 (no Lot): it looks again every few seconds.
-- Studio play tests: ServerStorage.LotTest (a BindableFunction, Studio only) answers "state" (the door, and every
-- hunt: found, seconds left, done, which gold Carls stand), "gold" (n: the first player's own gold Carl n down as if
-- they shot him), "lotcarl" (one lot Carl down), "open" (the first player's remaining gold Carls down: their key),
-- "shut", "carls", "key" (the first player's saved key: { egg, eggAt, save state }), "forget" (clear the first
-- player's key and save it: their gold Carls stand up), "setkey" ({ egg, eggAt }: put the first player's saved key
-- back exactly, and save), "ghost" (uid: a stand-in hunter with that UserId, its own three gold Carls, nobody's to
-- shoot: a second player for two-player tests, seen with the client's ViewAs), "ghostgold" (n: the stand-in's gold
-- Carl n down), "ghostgone" (the stand-in and its Carls away)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Profiles = require(script.Parent:WaitForChild("Profiles"))
local CalloutR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Callout") :: RemoteEvent

local WINDOW = 90     -- seconds from your first gold Carl to get the other two
local MOVE_FAST = 1.5 -- seconds to roll up when someone walks up to it
local CLOSE_T = 2.0   -- seconds to roll down
local NEAR = 11       -- studs out from the doorway (either side) that count as walking up to it
local HOLD = 1.5      -- seconds it stays up after the last person near it has gone
local PASS_U = 0.42   -- over this the bottom slat is high enough to walk under: the slats stop blocking
local BACK_UP = 2.6   -- seconds a lot Carl lies down before he stands up again
local HP = 30         -- like Cardboard Carl's: three rifle rounds, two to the head

-- one player's try at the egg (or a Studio stand-in's: p nil). who = the fighter's onlyFor (the Player itself)
type Hunt = { p: Player?, uid: number, who: any, found: { boolean }, endsAt: number, by: number, done: boolean }
type Entry = { spot: BasePart, gold: number?, hunt: Hunt? }
local lot: Instance? = nil
local carls: { [any]: Entry } = {}          -- fighter -> where he stands (and, for a gold one, whose)
local hunts: { [any]: Hunt } = {}           -- who -> their try
local ready: { [Player]: boolean } = {}     -- their save is read: we know whether they have the key
local state = "shut"                          -- shut | opening | open | closing
local moveT = MOVE_FAST
local holdUntil, rattleAt = 0, 0
local u = 0                                   -- how far up the door is: 0 shut .. 1 open
local openUntil = 0
local slats: { { p: BasePart, shut: CFrame, solid: boolean, query: boolean } } = {}
local lift, top = 20.6, math.huge

-- ---------------------------------------------------------------- the key: your own save
local store = Profiles.new("JankfireLot_v1", function() return { v = 1, egg = false, eggAt = 0 } end)
local profs: { [Player]: Profiles.Profile } = {}
local function hasKey(p: Player): boolean return p:GetAttribute("LotKey") == true end
local startHunt: (Player) -> () -- (below: their own gold Carls, once we know about the key)
local function joined(p: Player)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil end)
	if prof and not p.Parent then Profiles.release(store, prof); return end
	if not p.Parent then return end
	if prof then
		profs[p] = prof
		if prof.data.egg == true then p:SetAttribute("LotKey", true) end
	end
	-- (no save, saves off or failing: no key known, so they hunt; finding it still opens it for this visit)
	ready[p] = true
	if startHunt then startHunt(p) end -- (nil only if the save answered before this script's end ran: setup starts it)
end
-- found it: the key, saved now (and on screen at once, even if the save is slow or off)
local function grantKey(p: Player)
	if not p.Parent then return end
	p:SetAttribute("LotKey", true)
	local prof = profs[p]
	if prof and prof.data.egg ~= true then
		prof.data.egg = true; prof.data.eggAt = os.time(); prof.dirty = true
		task.spawn(Profiles.save, store, prof)
	end
end
Players.PlayerAdded:Connect(function(p) task.spawn(joined, p) end)
for _, p in Players:GetPlayers() do task.spawn(joined, p) end
local endHunt: (any) -> () -- (below)
Players.PlayerRemoving:Connect(function(p)
	ready[p] = nil
	if endHunt then endHunt(p) end
	local prof = profs[p]
	profs[p] = nil
	if prof then Profiles.release(store, prof) end
end)

local function lib(): Instance? return ServerStorage:FindFirstChild("JankfireMeshes") end
local function dummyFolder(): Instance return workspace:FindFirstChild("Dummies") or workspace end

-- the lot's sounds play from the panel over the door, for everyone near it
local function sound(name: string)
	-- (18 Nov: the panel can stand by the TOP door; the garage door's own sounds stay at the garage, in Lot.DoorSounds)
	local ds = lot and lot:FindFirstChild("DoorSounds")
	local panel = lot and lot:FindFirstChild("Panel")
	local s = (ds and ds:FindFirstChild(name, true)) or (panel and panel:FindFirstChild(name, true))
	if s and s:IsA("Sound") then s:Play() end
end

local function say(p: Player, text: string, dur: number) CalloutR:FireClient(p, text, dur) end
-- (a gold Carl's ding, chime and buzz are the finder's alone: their screen plays them, TrainingDoors.client)

-- ---------------------------------------------------------------- the Carls
-- a gold Carl is the cardboard man painted gold (light parts brighter, dark parts deeper)
local function gild(c: Color3): Color3
	local l = 0.3 * c.R + 0.59 * c.G + 0.11 * c.B
	return Color3.fromRGB(150, 98, 28):Lerp(Color3.fromRGB(255, 220, 120), math.clamp(l * 1.25, 0, 1))
end

local function makeCarl(e: Entry): any
	local spot = e.spot
	local feet = spot.Position
	local lv = spot.CFrame.LookVector
	local look = Vector3.new(lv.X, 0, lv.Z)
	look = if look.Magnitude > 0.01 then look.Unit else Vector3.zAxis
	local base = CFrame.lookAt(feet, feet - look) -- (+Z of this frame = the way he faces: the model's front)
	local m = Instance.new("Model")
	m.Name = if e.gold then "GoldCarl" else "Carl"
	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"; root.Size = Vector3.new(2, 2, 1); root.Transparency = 1
	root.Anchored = true; root.CanCollide = false; root.CanQuery = false; root.CanTouch = false
	root.CFrame = base + Vector3.new(0, Hitbox.ROOT_UP, 0)
	root.Parent = m
	m.PrimaryPart = root
	local l = lib()
	local tmpl = l and l:FindFirstChild("bc_cutout")
	local body: Model? = nil
	local rel = CFrame.identity
	if tmpl and tmpl:IsA("Model") then
		local b = tmpl:Clone()
		b.Name = "Body"
		for _, d in b:GetDescendants() do
			if d:IsA("BasePart") then
				d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
				if e.gold then d.Color = gild(d.Color) end
			end
		end
		local cf, sz = b:GetBoundingBox()
		rel = CFrame.new(0, sz.Y / 2, 0) * (cf:Inverse() * b:GetPivot()).Rotation
		b:PivotTo(base * CFrame.Angles(-1.45, 0, 0) * rel)
		b.Parent = m
		body = b
	end
	local hum = Instance.new("Humanoid")
	hum.RequiresNeck = false; hum.BreakJointsOnDeath = false
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	hum.MaxHealth = 100; hum.Health = 100
	hum.Parent = m
	m:SetAttribute("Dummy", true); m:SetAttribute("Base", base)
	if e.gold then m:SetAttribute("GoldCarl", e.gold) end
	-- (someone's own gold Carl: only on their screen, only their shots land. set before he is in the world)
	if e.hunt then m:SetAttribute("Owner", e.hunt.uid) end
	m.Parent = dummyFolder()
	local f = Rules.newFighter("dummy", if e.gold then "Gold Carl" else "Cardboard Carl", m)
	Rules.spawn(f, os.clock())
	f.hp = HP
	if e.hunt then f.onlyFor = e.hunt.who end
	Fight.byModel[m] = f
	table.insert(Fight.all, f)
	carls[f] = e
	if body then -- up from flat on his back
		local b = body
		task.spawn(function()
			local t0 = os.clock()
			while os.clock() - t0 < 0.3 and b.Parent and f.alive do
				local k = (os.clock() - t0) / 0.3
				b:PivotTo(base * CFrame.Angles(-1.45 * (1 - k) * (1 - k), 0, 0) * rel)
				RunService.Heartbeat:Wait()
			end
			if b.Parent and f.alive then b:PivotTo(base * rel) end
		end)
	end
	return f
end

-- off the fighter lists at once (nothing hits him twice, Fight never respawns him), then the cardboard tips over
local function fold(f: any)
	carls[f] = nil
	f.alive = false
	local i = table.find(Fight.all, f)
	if i then table.remove(Fight.all, i) end
	local m = f.ref :: Model?
	if not m then return end
	Fight.byModel[m] = nil
	local body = m:FindFirstChild("Body") :: Model?
	local base = m:GetAttribute("Base")
	task.spawn(function()
		if body and typeof(base) == "CFrame" then
			local b = base :: CFrame
			local rel = b:ToObjectSpace(body:GetPivot())
			local t0 = os.clock()
			while os.clock() - t0 < 0.22 and body.Parent do
				local k = (os.clock() - t0) / 0.22
				body:PivotTo(b * CFrame.Angles(-1.45 * k * k, 0, 0) * rel)
				RunService.Heartbeat:Wait()
			end
		end
		task.wait(0.6)
		m:Destroy()
	end)
end

local function goldStanding(h: Hunt, i: number): boolean
	for _, e in carls do if e.hunt == h and e.gold == i then return true end end
	return false
end

-- their gold Carls not found this try stand in their places (a finished hunt has none)
local function goldBack(h: Hunt)
	local spots = lot and lot:FindFirstChild("GoldSpots")
	if not spots or h.done then return end
	for i = 1, 3 do
		local s = spots:FindFirstChild("Gold" .. i)
		if s and s:IsA("BasePart") and not h.found[i] and not goldStanding(h, i) then makeCarl({ spot = s, gold = i, hunt = h }) end
	end
end
-- their gold Carls away (they left, or have the key)
local function goldAway(h: Hunt)
	for f, e in carls do if e.hunt == h then fold(f) end end
end

-- ---------------------------------------------------------------- the hunts: everyone's own
local function countOf(h: Hunt): number
	local n = 0
	for i = 1, 3 do if h.found[i] then n += 1 end end
	return n
end
-- how far they are, on their player for their screen: LotGold (bits 1, 2, 4), LotGoldBy (server time it runs out)
local function showHunt(h: Hunt)
	local p = h.p
	if not p or not p.Parent then return end
	local bits = 0
	if not h.done then for i = 1, 3 do if h.found[i] then bits += 2 ^ (i - 1) end end end
	p:SetAttribute("LotGold", if bits > 0 then bits else nil)
	p:SetAttribute("LotGoldBy", if bits > 0 then h.by else nil)
end
local function huntOf(who: any, p: Player?, uid: number): Hunt
	local h = hunts[who]
	if not h then
		h = { p = p, uid = uid, who = who, found = { false, false, false }, endsAt = 0, by = 0, done = false }
		hunts[who] = h
	end
	return h :: Hunt
end
-- a new try: nothing found, no clock; their three stand
local function resetHunt(h: Hunt)
	h.found = { false, false, false }; h.endsAt = 0; h.by = 0
	showHunt(h)
	goldBack(h)
end
-- their hunt as their key says: a key holder's is done (no gold Carls), anyone else's starts (or carries on)
startHunt = function(p: Player)
	if not ready[p] or not p.Parent then return end
	local h = huntOf(p, p, p.UserId)
	local was = h.done
	h.done = hasKey(p)
	if h.done then goldAway(h); showHunt(h)
	elseif was then resetHunt(h) -- (the key gone, a Studio test's forget: a fresh try, all three standing)
	else goldBack(h); showHunt(h) end
end
endHunt = function(who: any)
	local h = hunts[who]
	if not h then return end
	hunts[who] = nil
	goldAway(h)
end

-- one of their gold Carls is down (only their shot can do it: f.onlyFor)
local function goldDown(h: Hunt, i: number)
	if h.done or h.found[i] then return end
	h.found[i] = true
	if h.endsAt == 0 then h.endsAt = os.clock() + WINDOW; h.by = workspace:GetServerTimeNow() + WINDOW end
	local n = countOf(h)
	local p = h.p
	if n == 3 then
		h.done = true
		-- the key first, so their screen has it before their count goes (TrainingDoors.client: no buzz)
		if p then grantKey(p); say(p, "THE GARAGE IS OPEN", 2.2) end
	elseif p then -- (every gold hit says how long is left: the clock runs from the first)
		local left = math.max(0, h.endsAt - os.clock())
		say(p, ("GOLD %d OF 3 · %d:%02d"):format(n, math.floor(left / 60), math.floor(left % 60)), 1.8)
	end
	showHunt(h)
end

-- ---------------------------------------------------------------- the door
-- (the panel's men and clock are everyone's own now: each screen paints its player's, TrainingDoors.client)
local function setBeacons(on: boolean)
	local b = lot and lot:FindFirstChild("Beacons")
	if not b then return end
	for _, m in b:GetChildren() do
		m:SetAttribute("Spin", if on then 5 else 0)
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") and d:GetAttribute("Lens") then
				d.Material = if on then Enum.Material.Neon else Enum.Material.SmoothPlastic
				d.Color = if on then Color3.fromRGB(255, 170, 60) else Color3.fromRGB(150, 112, 62)
			elseif d:IsA("Light") then
				d.Enabled = on
			end
		end
	end
end

local passable: boolean? = nil
local function placeDoor()
	-- (the slats stay at their shut places here; whether they block follows how far up the door is)
	local up = u >= PASS_U
	if up == passable then return end
	passable = up
	for _, s in slats do
		s.p.CanCollide = s.solid and not up
		s.p.CanQuery = s.query and not up
	end
	local blk = lot and lot:FindFirstChild("DoorBlock") :: BasePart?
	if blk then blk.CanCollide = not up; blk.CanQuery = not up end
end
-- tell every screen to roll the door from where it is now to goal (0 shut, 1 up) over dur seconds
local function publish(goal: number, dur: number)
	local door = lot and lot:FindFirstChild("Door")
	if not door then return end
	door:SetAttribute("From", u); door:SetAttribute("Goal", goal); door:SetAttribute("Dur", dur)
	door:SetAttribute("Since", workspace:GetServerTimeNow())
end
local function goUp(dur: number)
	state = "opening"; moveT = dur
	publish(1, dur)
end
-- locked: the door jumps a hand's width and drops (every screen), it clatters, and LOCKED over the panel flashes
local function rattle()
	local door = lot and lot:FindFirstChild("Door")
	if door then door:SetAttribute("Rattle", workspace:GetServerTimeNow()) end
	sound("Rattle")
	local panel = lot and lot:FindFirstChild("Panel")
	local head = panel and panel:FindFirstChild("PanelHead")
	local g = head and head:FindFirstChild("Gui")
	local l = g and g:FindFirstChild("Line1")
	if l and l:IsA("TextLabel") then
		task.spawn(function()
			local was = l.TextColor3
			for _ = 1, 3 do
				l.TextColor3 = Color3.fromRGB(255, 92, 72); task.wait(0.14)
				l.TextColor3 = was; task.wait(0.12)
			end
		end)
	end
end
-- who is near the doorway, on the yard's side and on the lot's (not key holders: theirs is open on their own screen)
local function nearDoor(): ({ Player }, { Player })
	local yard, back = {}, {}
	local dw = lot and lot:FindFirstChild("Doorway") :: BasePart?
	if not dw then return yard, back end
	for _, p in Players:GetPlayers() do
		if hasKey(p) then continue end
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		if root and hum and hum.Health > 0 then
			local rel = dw.CFrame:PointToObjectSpace(root.Position)
			local h = dw.Size / 2
			if math.abs(rel.X) <= h.X + 1 and math.abs(rel.Y) <= h.Y + 4 and math.abs(rel.Z) <= h.Z + NEAR then
				if root.Position.Z > dw.Position.Z then table.insert(yard, p) else table.insert(back, p) end
			end
		end
	end
	return yard, back
end

local function someoneIn(part: BasePart, grow: number): boolean
	for _, p in Players:GetPlayers() do
		if hasKey(p) then continue end -- (the door never shuts on a key holder: it isn't there for them)
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if root then
			local rel = part.CFrame:PointToObjectSpace(root.Position)
			local h = part.Size / 2
			if math.abs(rel.X) <= h.X + grow and math.abs(rel.Y) <= h.Y + grow and math.abs(rel.Z) <= h.Z + grow then return true end
		end
	end
	return false
end

-- ---------------------------------------------------------------- the lot coming and going (v1 has none)
local function setup(l: Instance)
	lot = l
	table.clear(slats)
	local door = l:FindFirstChild("Door")
	if door then
		local lf, tp = door:GetAttribute("Lift"), door:GetAttribute("Top")
		lift = if type(lf) == "number" then lf else 20.6
		top = if type(tp) == "number" then tp else math.huge
		for _, d in door:GetDescendants() do
			local shut = d:GetAttribute("Shut")
			if d:IsA("BasePart") and typeof(shut) == "CFrame" then
				d.CFrame = shut; d.Transparency = 0
				table.insert(slats, { p = d, shut = shut, solid = d.CanCollide, query = d.CanQuery })
			end
		end
	end
	state, u, passable = "shut", 0, nil
	placeDoor()
	publish(0, 0)
	setBeacons(false)
	local targets = l:FindFirstChild("Targets")
	if targets then
		for _, s in targets:GetChildren() do if s:IsA("BasePart") then makeCarl({ spot = s }) end end
	end
	-- everyone's own gold Carls, each try from the start (a stand-in's too)
	for _, h in hunts do resetHunt(h) end
	for p in ready do startHunt(p) end
end

local function teardown()
	for f in carls do fold(f) end
	lot = nil
	table.clear(slats)
	for _, p in Players:GetPlayers() do if p:GetAttribute("OnLot") then p:SetAttribute("OnLot", nil) end end
end

Fight.onKill(function(info: any)
	local v = info.v
	local e = carls[v]
	if not e then return end
	fold(v)
	if e.gold then
		if e.hunt then goldDown(e.hunt, e.gold) end
	else
		task.delay(BACK_UP, function()
			if lot and e.spot.Parent then makeCarl(e) end
		end)
	end
end)

local acc, look = 0, 0
RunService.Heartbeat:Connect(function(dt: number)
	local now = os.clock()
	look += dt
	if look > 3 then
		look = 0
		local tg = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub") and workspace.Map.Hub:FindFirstChild("TrainingGround")
		local l = tg and tg:FindFirstChild("Lot")
		if l ~= lot then
			if lot then teardown() end
			if l then setup(l) end
		end
	end
	if not lot then return end
	-- the door
	if state == "opening" then
		u = math.min(1, u + dt / moveT)
		placeDoor()
		if u >= 1 then state = "open"; openUntil = now end
	elseif state == "closing" then
		local dw = lot:FindFirstChild("Doorway") :: BasePart?
		if dw and someoneIn(dw, 0.5) then
			goUp(MOVE_FAST); sound("Open") -- (the safety eye: back up)
		else
			u = math.max(0, u - dt / CLOSE_T)
			placeDoor()
			if u <= 0 then
				state = "shut"
				setBeacons(false)
			end
		end
	end
	acc += dt
	if acc < 0.2 then return end
	acc = 0
	-- who is at the door: from the lot it always lets you back in; on the yard's side it rattles (LOCKED). key holders
	-- are left out of both: it is open on their own screen
	local yard, back = nearDoor()
	if #back > 0 then
		holdUntil = now + HOLD
		if state == "shut" or state == "closing" then
			goUp(MOVE_FAST)
			sound("Open")
			setBeacons(true)
		end
	elseif #yard > 0 and state == "shut" and now >= rattleAt then
		rattleAt = now + 2.4
		rattle()
	end
	if state == "open" then
		if now >= openUntil and now >= holdUntil then
			local dw = lot:FindFirstChild("Doorway") :: BasePart?
			if dw and someoneIn(dw, 0.5) then
				holdUntil = now + 1
			else
				state = "closing"; publish(0, CLOSE_T); sound("Close")
			end
		end
	end
	-- everyone's own clock: out of time, their gold Carls stand up again (their screen buzzes)
	for _, h in hunts do
		if not h.done and h.endsAt > 0 and now >= h.endsAt then
			if h.p then say(h.p, "TOO SLOW. THE GOLD ONES ARE BACK", 2) end
			resetHunt(h)
		end
	end
	-- who is on the lot
	local areas: { BasePart } = {}
	for _, c in lot:GetChildren() do if c.Name == "Area" and c:IsA("BasePart") then table.insert(areas, c) end end
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local on = false
		if root then
			for _, area in areas do
				local rel = area.CFrame:PointToObjectSpace(root.Position)
				local h = area.Size / 2
				if math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z then on = true; break end
			end
		end
		if (p:GetAttribute("OnLot") == true) ~= on then p:SetAttribute("OnLot", if on then true else nil) end
	end
end)

-- ---------------------------------------------------------------- Studio play tests only
if RunService:IsStudio() then
	local bf = Instance.new("BindableFunction")
	bf.Name = "LotTest"
	bf.OnInvoke = function(op: string, a: any): any
		local function huntCarl(h: Hunt?, i: any): any
			for f, e in carls do if h and e.hunt == h and e.gold == i then return f end end
			return nil
		end
		if op == "state" then
			local hs = {}
			for _, h in hunts do
				local up = {}
				for i = 1, 3 do if huntCarl(h, i) then table.insert(up, i) end end
				hs[if h.p then h.p.Name else "ghost " .. h.uid] = { found = table.clone(h.found), done = h.done, standing = up,
					left = if h.endsAt > 0 then math.max(0, h.endsAt - os.clock()) else nil }
			end
			return { state = state, u = u, lot = lot ~= nil, slats = #slats, hunts = hs }
		elseif op == "gold" or op == "ghostgold" then
			local p = Players:GetPlayers()[1]
			local h = if op == "gold" then (p and hunts[p]) else hunts.ghost
			local f = huntCarl(h, a)
			if not f then return false end
			local k = if op == "gold" and p then Fight.byPlayer[p] else nil
			local info = Rules.kill(f, k, "redline", os.clock())
			Fight.died(info, nil)
			return true
		elseif op == "ghost" then -- a stand-in hunter: its own three, onlyFor "ghost" (no player's shot lands on them)
			endHunt("ghost")
			local h = huntOf("ghost", nil, if type(a) == "number" then a else 7)
			goldBack(h)
			local out = {}
			for f, e in carls do if e.hunt == h then local r = Fight.root(f); out[e.gold :: number] = if r then r.Position else true end end
			return out
		elseif op == "ghostgone" then
			endHunt("ghost")
			return true
		elseif op == "lotcarl" then -- put one lot Carl down (he stands up again after BACK_UP)
			for f, e in carls do
				if not e.gold then
					local info = Rules.kill(f, nil, "redline", os.clock())
					Fight.died(info, nil)
					return e.spot.Position
				end
			end
			return nil
		elseif op == "open" then
			local p = Players:GetPlayers()[1]
			local h = p and hunts[p]
			if not h then return false end
			for i = 1, 3 do local f = huntCarl(h, i); if f then Fight.died(Rules.kill(f, Fight.byPlayer[p], "redline", os.clock()), nil) end end
			return h.done
		elseif op == "shut" then if state == "open" then openUntil = 0; holdUntil = 0 end; return true
		elseif op == "key" then
			local p = Players:GetPlayers()[1]
			local prof = p and profs[p]
			return if prof then { egg = prof.data.egg, eggAt = prof.data.eggAt, save = prof.state, attr = p:GetAttribute("LotKey") } else nil
		elseif op == "forget" then
			local p = Players:GetPlayers()[1]
			local prof = p and profs[p]
			if not p or not prof then return false end
			prof.data.egg = false; prof.data.eggAt = 0; prof.dirty = true
			p:SetAttribute("LotKey", nil)
			local ok = Profiles.save(store, prof)
			startHunt(p)
			return ok
		elseif op == "setkey" then -- put the first player's saved key back exactly ({ egg, eggAt }) and save it
			local p = Players:GetPlayers()[1]
			local prof = p and profs[p]
			if not p or not prof or type(a) ~= "table" then return false end
			prof.data.egg = a.egg == true; prof.data.eggAt = if type(a.eggAt) == "number" then a.eggAt else 0; prof.dirty = true
			p:SetAttribute("LotKey", if a.egg == true then true else nil)
			local ok = Profiles.save(store, prof)
			startHunt(p)
			return ok
		elseif op == "carls" then
			local out = {}
			for f, e in carls do
				local r = Fight.root(f)
				table.insert(out, { name = f.name, gold = e.gold, owner = if e.hunt then e.hunt.uid else nil, alive = f.alive, pos = if r then r.Position else nil })
			end
			return out
		end
		return nil
	end
	bf.Parent = ServerStorage
end
