--!strict
-- JANKFIRE (Roblox) server, step 1: run around Rooftop. it owns: the grapple's say-so (range, sight, rate) and the
-- street below (fall in and you die: "into the smog"). movement itself is the client's, like the web game; the
-- movement checks (teleport, noclip, fly, speed) are AntiCheat.server.luau's; damage and hits are Combat's (step 2)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Config"))
local HookCheck = require(script.Parent:WaitForChild("HookCheck"))
local HookChargeServer = require(script.Parent:WaitForChild("HookChargeServer")) -- (ranked: 2 grapple charges)
local MeshSwap = require(script.Parent:WaitForChild("MeshSwap"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local GrappleRemote = Remotes:WaitForChild("Grapple") :: RemoteEvent
local CalloutRemote = Remotes:WaitForChild("Callout") :: RemoteEvent

local map = workspace:WaitForChild("Map")
-- the fall line is your match's arena's (matches run side by side, each in its own site: Matches.killY), else the
-- default arena's
local Matches = require(script.Parent:WaitForChild("Matches"))
local Fight = require(script.Parent:WaitForChild("Fight")) -- (a hook on a person: who they are, kill credit)
local Rules = require(script.Parent:WaitForChild("Rules"))
local swapped = MeshSwap.run(map)
if swapped > 0 then print(("[jankfire] %d Blender models swapped in"):format(swapped)) end

Players.RespawnTime = 2
-- the parts that stop bodies but no rays (WebArena's flag "c": rails, the columns over the roofs) are in JFRayBlind: it
-- collides with the players' groups (JFPlayers, JFShredded, VipGuest) but not with Default, where every ray, rope and
-- bullet is cast. (characters are never left in Default: HubVip and the Shredder put them in JFPlayers / VipGuest)
pcall(function() PhysicsService:RegisterCollisionGroup("JFRayBlind") end)
pcall(function() PhysicsService:CollisionGroupSetCollidable("JFRayBlind", "Default", false) end)

type Info = { hookTimes: { number }, rope: Beam?, anchor: Attachment?, last: Vector3?, lastT: number, tp: number?,
	body: Model?, bodyBlind: number, bodyNext: number, -- (body: the person the rope is tied to)
	bornT: number } -- (when the body loaded: the spawn grace below)
local info: { [Player]: Info } = {}

local function dropRope(i: Info)
	if i.rope then i.rope:Destroy(); i.rope = nil end
	if i.anchor then i.anchor:Destroy(); i.anchor = nil end
	i.body = nil
end

Players.PlayerAdded:Connect(function(p: Player)
	info[p] = { hookTimes = {}, lastT = 0, bodyBlind = 0, bodyNext = 0, bornT = 0 }
	p.CharacterAdded:Connect(function()
		local i = info[p]
		-- a new body gets moved to its spawn (the hub, the arena) right after it loads: give the teleport check a moment
		if i then dropRope(i); i.last = nil; i.lastT = os.clock() + 0.5; i.bornT = os.clock() end
	end)
end)
Players.PlayerRemoving:Connect(function(p: Player)
	local i = info[p]
	if i then dropRope(i) end
	info[p] = nil
end)

local function alive(p: Player): (Humanoid?, BasePart?)
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root or hum.Health <= 0 then return nil, nil end
	return hum, root
end

-- the rope everyone sees, from the hooker's hand to a1 (the hooker's own client hides this one: it draws its own)
local function tieRope(i: Info, p: Player, a1: Attachment)
	dropRope(i)
	local root = (p.Character :: Model):FindFirstChild("HumanoidRootPart")
	-- (the hold session, 18 Nov 2026: R6 bodies too) the hand: R15's RightHand, an R6 body's Right Arm (its grip at the end)
	local hand = (p.Character :: Model):FindFirstChild("RightHand") or (p.Character :: Model):FindFirstChild("Right Arm") or root
	local a0 = hand and ((hand.Name == "Right Arm" and hand:FindFirstChild("RightGripAttachment")) or hand:FindFirstChildWhichIsA("Attachment"))
	local b = Instance.new("Beam")
	b.Name = "Rope_" .. p.UserId -- (AntiCheat reads this name: on a rope, no fly checks)
	b.Attachment0 = a0; b.Attachment1 = a1
	b.Width0 = 0.25; b.Width1 = 0.25; b.FaceCamera = true; b.Segments = 1
	b.Color = ColorSequence.new(Color3.fromRGB(236, 238, 242), Color3.fromRGB(176, 182, 192)) -- (a pale steel cable, like the one its owner sees)
	b.LightEmission = 0.3
	b:SetAttribute("Owner", p.UserId)
	b.Parent = workspace.Terrain
	i.rope, i.anchor = b, a1
end

-- the yank (18 Nov 2026, the owner: "when you grapple someone maybe you can press a button to like pull them towards
-- you??"; Move.client's tryYank): with the rope on a person, one pull toward the hooker, and the rope goes. the shove
-- goes through Fight.knock (the anti-cheat knows it); an enemy or a training dummy is tagged like the hook itself, so a
-- fall within 10 s is the yanker's kill via the grapple. anyone you can't hurt (a teammate, another player in training)
-- gets Config.hook.yankMate of the pull and no tag: a rescue. where weapons work only (not the hub), one every yankCool
-- (YankT on the yanker, server time: their client and the phone's YANK button read it). everyone draws the snap
-- (GrappleYank.client: the rope taut, its crack, a trail on them)
local Dummies = require(script.Parent:WaitForChild("Dummies"))
local YANK_ZONES = { match = true, training = true, playground = true }
local function yankV(from: Vector3, to: Vector3, k: number): Vector3
	local H = Config.hook
	local d = Vector3.new(from.X - to.X, 0, from.Z - to.Z)
	local dist = d.Magnitude
	local dir = if dist > 0.1 then d / dist else Vector3.zero
	-- (sideways: enough to fly about yankAir s and come down a fifth of the way short of you, never past yankSpeed)
	local side = math.min(H.yankSpeed, dist * 0.8 / H.yankAir) * k
	local up = (H.yankUp + math.clamp(from.Y - to.Y, 0, H.yankClimb)) * (if k < 1 then 0.75 else 1)
	return dir * side + Vector3.new(0, up, 0)
end
local function yank(p: Player, i: Info)
	local function stop(why: string)
		dropRope(i)
		GrappleRemote:FireClient(p, "cut", why)
	end
	local tm = i.body
	local hum, root = alive(p)
	if not tm or not hum or not root then return stop("nobody there") end
	local ready = p:GetAttribute("YankT")
	if type(ready) == "number" and workspace:GetServerTimeNow() < ready - 0.15 then return stop("recharging") end -- (a little slack for the clocks)
	if not YANK_ZONES[Matches.zoneOf(p)] or p:GetAttribute("LoadoutWindow") ~= nil or Matches.roundLocked(p) then return stop("not here") end
	local tp = Players:GetPlayerFromCharacter(tm)
	local tf = Fight.of(tp or tm)
	local troot = tm:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not tf or not tf.alive or not troot or not tm:IsDescendantOf(workspace) then return stop("gone") end
	-- (held where they are: a soap bubble, a cage, a pop quiz, the loadout window before a round)
	if tp and (tp:GetAttribute("Trap") or tp:GetAttribute("Jail") or tp:GetAttribute("Quiz") or tp:GetAttribute("LoadoutWindow") ~= nil) then return stop("held") end
	local from, to = root.Position, troot.Position
	if (to - from).Magnitude > Config.hook.range + Config.check.hookSlack + 20 then return stop("out of range") end
	if i.bodyBlind > Config.hook.bodyBlind then return stop("out of sight") end
	local mf = Fight.byPlayer[p]
	local full = mf ~= nil and mf ~= tf and Fight.allow(mf, tf)
	local v = yankV(from, to, if full then 1 else Config.hook.yankMate)
	p:SetAttribute("YankT", workspace:GetServerTimeNow() + Config.hook.yankCool)
	if full then Rules.tagged(tf, mf :: any, "grapple", os.clock()) end
	if tf.kind == "dummy" then
		-- (a training dummy's legs would walk the pull off: it goes over for it, like a marble slip, chest first to you)
		pcall(Dummies.slip, tf)
		troot.AssemblyLinearVelocity = Vector3.zero
		local flat = Vector3.new(v.X, 0, v.Z)
		local d = if flat.Magnitude > 0.1 then flat.Unit else Vector3.zAxis
		troot.AssemblyAngularVelocity = Vector3.new(d.Z, 0, -d.X) * 6
		-- and it stops where it comes down: flat on its back it slid on 30 studs past the yanker (the v796 test), so
		-- the moment it's down again its slide is braked (a player's own movement friction does this for them)
		task.spawn(function()
			local rp = RaycastParams.new()
			rp.FilterType = Enum.RaycastFilterType.Exclude
			rp.FilterDescendantsInstances = { tm }
			local t0 = os.clock()
			task.wait(0.2)
			while os.clock() - t0 < 2.5 and troot.Parent do
				local tv = troot.AssemblyLinearVelocity
				if tv.Y <= 1 and workspace:Raycast(troot.Position, Vector3.new(0, -3.5, 0), rp) then
					troot.AssemblyLinearVelocity = Vector3.new(tv.X * 0.15, tv.Y, tv.Z * 0.15)
					break
				end
				task.wait()
			end
		end)
	end
	Fight.knock(tf, v, "grapple")
	if full and mf then pcall(function() require(script.Parent:WaitForChild("ScytheCombo")).step(mf :: any, tf, "yank") end) end -- (the combo's 2nd step)
	GrappleRemote:FireAllClients("yank", p.Character, tm, not full)
	dropRope(i)
end

-- the reel (19 Nov 2026, the owner: "the same way how you press F to push people in, I want a button that reels you
-- in"; Move.client's tryReel): with your rope on anything, you're pulled along it to its point, the yank's mirror. here:
-- the say-so (a rope of yours, in range, after GO, not held, one every reelCool: ReelT on you, server time), the
-- anti-cheat told (ACGrace for the pull's time), and "reel" back with that time; the client does the moving and lets go
-- when it gets there. on an enemy it's the Scythe combo's second step, like a yank (ScytheCombo)
local function reel(p: Player, i: Info)
	local function stop(why: string)
		dropRope(i)
		GrappleRemote:FireClient(p, "cut", why)
	end
	if not Config.hook.REEL then return end -- (off since 19 Nov 2026: X is the AUTO GRAPPLE. the rope stays)
	local hum, root = alive(p)
	if not hum or not root or not i.rope or not i.anchor or not i.anchor.Parent then return stop("no rope") end
	local ready = p:GetAttribute("ReelT")
	if type(ready) == "number" and workspace:GetServerTimeNow() < ready - 0.15 then return end -- (too soon: the rope stays)
	if Matches.roundLocked(p) or p:GetAttribute("LoadoutWindow") ~= nil then return stop("not yet") end
	if p:GetAttribute("Trap") or p:GetAttribute("Jail") or p:GetAttribute("Quiz") then return stop("held") end
	local to = (i.anchor :: Attachment).WorldPosition
	local dist = (to - root.Position).Magnitude
	if dist > Config.hook.range + Config.check.hookSlack + 20 then return stop("out of range") end
	local H = Config.hook
	local dur = math.min(H.reelMax, dist / H.reelSpeed + 0.2)
	p:SetAttribute("ACGrace", os.clock() + dur + 0.8) -- (the anti-cheat: this pull is the server's say)
	p:SetAttribute("ReelT", workspace:GetServerTimeNow() + H.reelCool)
	local tm = i.body
	if tm then
		local mf, tf = Fight.byPlayer[p], Fight.of(Players:GetPlayerFromCharacter(tm) or tm)
		if mf and tf and mf ~= tf and Fight.allow(mf, tf) then
			pcall(function() require(script.Parent:WaitForChild("ScytheCombo")).step(mf :: any, tf, "yank") end)
		end
	end
	GrappleRemote:FireClient(p, "reel", dur)
end

-- a hook the client fired at an opponent it wasn't aimed straight at. kind "lock": the AUTO GRAPPLE on X
-- (shared/HookCharges.LOCK, 19 Nov 2026): any match, ranked too (after GO: the hook's own RoundLock check), one every
-- LOCK.cd. kind "auto": QUICKPLAY's passive auto-lock (HookCharges.AUTO, off since then): a QUICKPLAY match that isn't
-- ranked, one every AUTO.cd. both: HookAutoT on you (server time); the body check is a hook's own (range, sight)
local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HookCharges")) :: any
local function autoOk(p: Player, kind: string): boolean
	local A = if kind == "lock" then HC.LOCK else HC.AUTO
	if not (A and A.on) then return false end
	local im = Matches.matchOf(p)
	local test = RunService:IsStudio() and p:GetAttribute("AutoLockTest") == true -- (Studio: try it anywhere)
	if not test then
		if not im then return false end
		if kind == "auto" and (not (im :: any).quick or im.ranked) then return false end
	end
	local ready = p:GetAttribute("HookAutoT")
	return not (type(ready) == "number" and workspace:GetServerTimeNow() < ready - 0.2)
end

GrappleRemote.OnServerEvent:Connect(function(p: Player, what: unknown, point: unknown, body: unknown, isAuto: unknown)
	local i = info[p]
	if not i or type(what) ~= "string" then return end
	if what == "release" then dropRope(i); return end
	if what == "yank" then yank(p, i); return end
	if what == "reel" then reel(p, i); return end
	if what ~= "hook" then return end
	local function cut(why: string)
		dropRope(i)
		GrappleRemote:FireClient(p, "cut", why)
	end
	-- (not before GO, 19 Nov 2026, the owner: "dont let player be able to use grapple or gadgets before round starts":
	-- the countdown, the loadout window, between rounds, a map room. refused before a charge is spent)
	if Matches.roundLocked(p) then return cut("not yet") end
	if p:GetAttribute("Rig") ~= nil then return cut("rigged") end -- (the Overdrive Rig gadget: no rope while suited up)
	if not HookCheck.rate(i.hookTimes, os.clock()) then return cut("too many") end
	local hum, root = alive(p)
	if not hum or not root then return cut("dead") end
	if typeof(point) ~= "Vector3" then return cut("bad point") end
	local pt = point :: Vector3
	local bad = HookCheck.point(pt.X, pt.Y, pt.Z)
	if bad then return cut(bad) end
	local from = root.Position + Vector3.new(0, 1.5, 0) -- about the head
	-- a person (18 Nov 2026, the owner: "can you make it so you can grapple onto people"): a living player or training
	-- dummy, in range and in sight (now or a moment ago, for lag). the rope is tied to their chest and follows them
	-- (Move.client reels the hooker in; the heartbeat below drops it when they go). an enemy hooked is tagged like a
	-- knock (Rules.tagged): a fall or a hazard within 10 s is the hooker's kill, "via" the grapple. a teammate never is
	local tm = if typeof(body) == "Instance" and body:IsA("Model") then body :: Model else nil
	if tm then
		local tf = Fight.of(Players:GetPlayerFromCharacter(tm) or tm)
		local troot = tm:FindFirstChild("HumanoidRootPart") :: BasePart?
		local thum = tm:FindFirstChildOfClass("Humanoid")
		if not tf or not tf.alive or not troot or not thum or thum.Health <= 0 or tm == p.Character or not tm:IsDescendantOf(workspace) then
			return cut("nobody there")
		end
		local chestAt = troot.Position + Vector3.new(0, Config.hook.bodyUp, 0)
		local badB = HookCheck.body((chestAt - root.Position).Magnitude, Fight.sees(from, tf))
		if badB then return cut(badB) end
		local autoKind = if isAuto == "lock" then "lock" elseif isAuto == true then "auto" else nil
		if autoKind and not autoOk(p, autoKind) then return cut("no auto-lock") end
		if not HookChargeServer.allow(p) then return cut("recharging") end
		-- (the cooldown only once the hook is sure: a ranked hook with no charge left spends none)
		if autoKind then p:SetAttribute("HookAutoT", workspace:GetServerTimeNow() + (if autoKind == "lock" then HC.LOCK.cd else HC.AUTO.cd)) end
		local mf = Fight.byPlayer[p]
		if mf and mf ~= tf and Fight.allow(mf, tf) then Rules.tagged(tf, mf, "grapple", os.clock()) end
		local a1 = Instance.new("Attachment")
		a1.Name = "RopeTie_" .. p.UserId
		a1.Position = Vector3.new(0, Config.hook.bodyUp, 0)
		a1.Parent = troot
		tieRope(i, p, a1)
		i.body, i.bodyBlind, i.bodyNext = tm, 0, os.clock() + 0.2
		-- (the Scythe's combo finisher, ScytheCombo: a rope on them is its first step)
		if mf and mf ~= tf then pcall(function() require(script.Parent:WaitForChild("ScytheCombo")).step(mf :: any, tf, "grapple") end) end
		return
	end
	local toPoint = (pt - from).Magnitude
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { p.Character :: Instance }
	local dir = if toPoint > 1e-3 then (pt - from).Unit else Vector3.yAxis
	local hit = workspace:Raycast(from, dir * (toPoint + 3), params)
	bad = HookCheck.reach((pt - root.Position).Magnitude, toPoint, hit and (hit.Position - from).Magnitude or nil)
	if bad then return cut(bad) end
	-- (a RANKED duel or PARTY RANKED: a hook spends one of 2 charges; none left = cut. shared/HookCharges.luau)
	if not HookChargeServer.allow(p) then return cut("recharging") end
	-- the rope everyone sees (the hooker's own client hides this one: it draws its own right away)
	dropRope(i)
	local a1 = Instance.new("Attachment")
	a1.WorldPosition = pt
	a1.Parent = workspace.Terrain
	tieRope(i, p, a1)
end)

-- the open sky (18 Nov 2026, tools/roblox/wallbox.py): a walled arena has no lid any more. while you're in one, its SkyY
-- and its middle (ArenaAt: the site's, a copy's own) go on you: Move.client lets nothing lift you past the sky line and
-- slides you off the ledge round the edge. anyone SKY_OUT over the line (only a client that skipped Move.client gets
-- there) is out of the world, like under the fall line. (only over the site itself: the hub stands higher than any sky)
local SKY_OUT = 60
local SPAWN_GRACE = 1 -- s (the spawn grace, in the heartbeat below)
local skyNext: { [Player]: number } = {}
local function siteOf(p: Player, pos: Vector3): Model?
	local an = p:GetAttribute("Arena")
	if type(an) ~= "string" then return nil end
	local best: Model?, bd = nil, 2500
	local function try(m: Instance?)
		if m and m:IsA("Model") then
			local d = m:GetPivot().Position - pos
			local h = Vector2.new(d.X, d.Z).Magnitude
			if h < bd then best, bd = m :: Model, h end
		end
	end
	try(map:FindFirstChild(an))
	local copies = map:FindFirstChild("ArenaCopies")
	if copies then
		for _, c in copies:GetChildren() do
			if string.sub(c.Name, 1, #an + 5) == an .. "_copy" then try(c) end
		end
	end
	return best
end
Players.PlayerRemoving:Connect(function(p: Player) skyNext[p] = nil end)

-- the street
RunService.Heartbeat:Connect(function()
	for p, i in info do
		local hum, root = alive(p)
		if not hum or not root then continue end
		local pos = root.Position
		-- the spawn grace (18 Nov): LoadCharacter yields, and until Fight.spawn places the new body it stands wherever
		-- Roblox first put it (the Rooftop v1's SpawnLocations, y -11 to 13). no fall line or sky line applies to it
		-- until it's placed (its fighter alive again), or for SPAWN_GRACE at most. (today every fall line is lower than
		-- those pads, so this only guards against spawns or fall lines moving; the script's attribute SpawnGrace = 0
		-- turns it off for a test)
		local f = Fight.byPlayer[p]
		if f and not f.alive then
			local g = script:GetAttribute("SpawnGrace")
			if os.clock() - i.bornT < (if type(g) == "number" then g else SPAWN_GRACE) then continue end
		end
		local killY = Matches.killY(p)
		if pos.Y < killY then
			hum.Health = 0
			dropRope(i)
			CalloutRemote:FireClient(p, "INTO THE SMOG", 1.5)
			continue
		end
		-- (the teleport check is AntiCheat.server.luau's now, with the fly, noclip and speed checks: a server teleport
		-- still stamps the player's TeleportT attribute so it starts afresh from the new spot)
		-- the sky line (above): what's on you follows your site, twice a second
		local now = os.clock()
		if now >= (skyNext[p] or 0) then
			skyNext[p] = now + 0.5
			local site = siteOf(p, pos)
			local sky = site and site:GetAttribute("SkyY")
			local at = if site and type(sky) == "number" then site:GetPivot().Position else nil
			if p:GetAttribute("SkyY") ~= sky then p:SetAttribute("SkyY", if type(sky) == "number" then sky else nil) end
			if p:GetAttribute("ArenaAt") ~= at then p:SetAttribute("ArenaAt", at) end
		end
		local sky, at = p:GetAttribute("SkyY"), p:GetAttribute("ArenaAt")
		if type(sky) == "number" and typeof(at) == "Vector3" and pos.Y > sky + SKY_OUT and Vector2.new(pos.X - at.X, pos.Z - at.Z).Magnitude < 600 then
			hum.Health = 0
			dropRope(i)
			CalloutRemote:FireClient(p, "OUT OF BOUNDS", 1.5)
			continue
		end
		-- a rope tied to a person (above), five times a second: they died, respawned or left, or the hooker hasn't seen
		-- them for a moment (the client lets go sooner; this is the say-so), and it drops
		if i.body and now >= i.bodyNext then
			i.bodyNext = now + 0.2
			local tm = i.body :: Model
			local tf = Fight.of(Players:GetPlayerFromCharacter(tm) or tm)
			local troot = tm:FindFirstChild("HumanoidRootPart") :: BasePart?
			if not tf or not tf.alive or not troot or not tm:IsDescendantOf(workspace) or not (i.anchor and i.anchor.Parent) then
				dropRope(i)
				GrappleRemote:FireClient(p, "cut", "gone")
			else
				local eye = pos + Vector3.new(0, 1.5, 0)
				local d = troot.Position + Vector3.new(0, Config.hook.bodyUp, 0) - eye
				local blocked = d.Magnitude > 0.1 and Fight.castMap(eye, d.Unit, d.Magnitude) ~= nil
				i.bodyBlind = if blocked then i.bodyBlind + 0.2 else 0
				if i.bodyBlind > Config.hook.bodyBlind + 0.4 then
					dropRope(i)
					GrappleRemote:FireClient(p, "cut", "out of sight")
				end
			end
		end
	end
end)
