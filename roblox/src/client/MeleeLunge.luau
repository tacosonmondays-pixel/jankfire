--!strict
-- the melee LUNGE and the forgiving swing, on your side (26 Nov 2026; shared/Melee.luau has the numbers and the why,
-- docs/MELEE.md the whole account).
--   MeleeLunge.try(wid)        a lunge press: at the person under your crosshair (within Melee.LUNGE.cone degrees and
--                              .range studs, in sight), if the cooldown is over. nobody there: nothing is spent, a
--                              quiet "NO TARGET". runs at once (no wait on the server); the server's say-so
--                              (MeleeLunge.server) tells the anti-cheat, starts the cooldown, or says no and it stops
--   MeleeLunge.press(io, wid)  Arsenal's key hook: the LUNGE key with a swung weapon out (true = used)
--   MeleeLunge.rightLunge(w)   right click lunges with this one (it has no right-click move of its own)
--   MeleeLunge.step(st, chest, dt, grounded)  Move.client, every physics step: true while lunging (it set st's velocity)
--   MeleeLunge.speed(w)        the run x with this weapon out (Melee.SPEED for a loadout melee, else 1)
--   MeleeLunge.meleeOut()      a swung weapon in your hands right now (the grapple's longer lock-on, Move.client)
--   MeleeLunge.hits(m, feet, eye, look, reach, cone, since)  the forgiving swing (Arsenal's resolveSwing): this body's
--                              column in the swing now, or anywhere along its last moments back to `since`
-- the cooldown pip under the crosshair is MeleeHud.client's (LungeGuess on you, this screen's; LungeT, the server's)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Melee = require(Shared:WaitForChild("Melee"))
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Body = require(script.Parent:WaitForChild("Body")) :: any
local Hud = require(script.Parent:WaitForChild("Hud")) :: any
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local W = Weapons.list :: any
local L = Melee.LUNGE

local me = Players.LocalPlayer
local camera = workspace.CurrentCamera
local function snow(): number return workspace:GetServerTimeNow() end

local M = {}
M.REEL_HIT = Melee.REEL_HIT -- (Move.client: the window after a reel onto someone)

local function heldId(): string?
	local ch = me.Character
	local hw = ch and ch:FindFirstChild("HeldWeapon")
	local id = hw and hw:GetAttribute("Weapon")
	return if type(id) == "string" then id else nil
end
function M.meleeOut(): boolean
	return Melee.swung(W[heldId() or ""])
end
function M.speed(w: any): number
	return if Melee.loadout(w) then Melee.SPEED else 1
end
function M.rightLunge(w: any): boolean
	return Melee.swung(w) and not Melee.ownRight(w)
end

-- ------------------------------------------------------------------ who's around (players, the training dummies)
local function bodies(): { Model }
	local out = {}
	local myArena, myTeam = me:GetAttribute("Arena"), me:GetAttribute("Team")
	for _, p in Players:GetPlayers() do
		if p == me or not p.Character then continue end
		if p:GetAttribute("Arena") ~= myArena then continue end
		if myTeam ~= nil and p:GetAttribute("Team") == myTeam then continue end -- (a teammate: never)
		table.insert(out, p.Character)
	end
	local d = workspace:FindFirstChild("Dummies")
	if d then for _, m in d:GetChildren() do if m:IsA("Model") then table.insert(out, m) end end end
	return out
end
local function rootOf(m: Model): BasePart?
	local hum = m:FindFirstChildOfClass("Humanoid")
	local r = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not r or hum.Health <= 0 or not m:IsDescendantOf(workspace) then return nil end
	return r
end

-- where each body's feet were lately (20 a second, the last 0.6 s): the swing looks back along it
local hist: { [Model]: { { t: number, f: Vector3 } } } = setmetatable({}, { __mode = "k" }) :: any
local sampleT = 0
RunService.Heartbeat:Connect(function()
	local t = os.clock()
	if t - sampleT < 0.05 then return end
	sampleT = t
	for _, m in bodies() do
		local r = rootOf(m)
		if not r then hist[m] = nil; continue end
		local h = hist[m]
		if not h then h = {}; hist[m] = h end
		table.insert(h, { t = t, f = Hitbox.feet(r.Position) })
		while #h > 0 and t - h[1].t > 0.6 do table.remove(h, 1) end
	end
end)
function M.hits(m: Model, feet: Vector3, eye: Vector3, look: Vector3, reach: number, cone: number, since: number?): (boolean, Vector3?)
	local ok, p = Melee.inSwing(eye, look, feet, reach, cone)
	if ok then return true, p end
	local h = hist[m]
	if not h or not since then return false, nil end
	local from = since - Melee.HIT.early
	for i = #h, 1, -1 do
		local s = h[i]
		if s.t < from then break end
		local ok2, p2 = Melee.inSwing(eye, look, s.f, reach, cone)
		if ok2 then return true, p2 end
	end
	return false, nil
end

-- ------------------------------------------------------------------ the lunge
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local FIGHT = { match = true, training = true, playground = true }
local LungeR: RemoteEvent? = nil
task.spawn(function() LungeR = Remotes:WaitForChild("Lunge", 30) :: RemoteEvent? end)

type Run = { m: Model, untilT: number, t0: number }
local run: Run? = nil
local guess = 0 -- (this screen's cooldown, server time: LungeGuess)

function M.left(): number
	return math.max(Melee.left(me:GetAttribute("LungeT"), snow()), guess - snow())
end
function M.lunging(): boolean return run ~= nil end

-- the person nearest the middle of your view inside the cone, in range and in sight from your chest
local function pick(chest: Vector3): (Model?, BasePart?)
	local cam = camera.CFrame
	local best: Model?, bestR: BasePart?, bestA = nil, nil, math.rad(L.cone)
	local map = workspace:FindFirstChild("Map")
	mapParams.FilterDescendantsInstances = if map then { map } else {}
	for _, m in bodies() do
		local r = rootOf(m)
		if not r then continue end
		local to = r.Position - chest
		local d = to.Magnitude
		if d > L.range or d < 0.5 then continue end
		local fromCam = r.Position - cam.Position
		local a = math.acos(math.clamp(cam.LookVector:Dot(fromCam.Unit), -1, 1))
		if a > bestA then continue end
		if map and workspace:Raycast(chest, to, mapParams) then continue end -- (a wall in the way)
		best, bestR, bestA = m, r, a
	end
	return best, bestR
end

function M.try(wid: string): boolean
	if not Melee.swung(W[wid]) then return false end
	if not FIGHT[me:GetAttribute("Zone") :: any] and me:GetAttribute("DevArms") ~= true then return false end
	if me:GetAttribute("RoundLock") or me:GetAttribute("LoadoutOpen") or me:GetAttribute("SpawnHold") then return false end
	if Body.stunned() or Body.slipping() or Body.pinned() then return false end
	if run then return false end
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not root or not hum or hum.Health <= 0 then return false end
	if M.left() > 0 then
		Hud.note(("LUNGE · %d S"):format(math.max(1, math.ceil(M.left()))), 0.6)
		return false
	end
	local m, r = pick(root.Position)
	if not m or not r then Hud.note("NO TARGET", 0.5); return false end
	if (r.Position - root.Position).Magnitude <= L.near + 0.5 then return false end -- (already in reach: just swing)
	run = { m = m, untilT = os.clock() + L.time, t0 = os.clock() }
	guess = snow() + L.cd
	me:SetAttribute("LungeGuess", guess)
	if LungeR then (LungeR :: RemoteEvent):FireServer(m) end
	pcall(Sfx.play, W[wid].swingSnd or "swing", nil, 0.7) -- (the weapon's own recorded whoosh)
	return true
end
function M.press(io: any, wid: string): boolean
	if not Binds.is("lunge", io) or not Melee.swung(W[wid]) then return false end
	M.try(wid)
	return true
end

-- the server's word: "no" (why) stops it and gives the cooldown back
task.spawn(function()
	local r = Remotes:WaitForChild("Lunge", 30)
	if r and r:IsA("RemoteEvent") then
		r.OnClientEvent:Connect(function(what: unknown)
			if what == "no" then
				run = nil
				guess = 0
				me:SetAttribute("LungeGuess", nil)
			end
		end)
	end
end)

-- every physics step (Move.client, after the rope and the dash): straight at their chest as it is now, at L.speed, at
-- most L.up degrees up or down (never down into the floor you stand on); it ends L.near off them, or after L.time,
-- and L.keep of the speed carries on (its climb no more than 12 studs/s: a lunge, not a launch)
function M.step(st: any, chest: Vector3, dt: number, grounded: boolean): boolean
	local r0 = run
	if not r0 then return false end
	local tr = rootOf(r0.m)
	local to = if tr then tr.Position - chest else Vector3.zero
	if not tr or to.Magnitude <= L.near or os.clock() > r0.untilT or Body.stunned() then
		run = nil
		st.vx, st.vz = st.vx * L.keep, st.vz * L.keep
		if st.vy > 12 then st.vy = 12 end
		return false
	end
	local flat = Vector3.new(to.X, 0, to.Z)
	local dir: Vector3
	if flat.Magnitude < 0.5 then
		dir = to.Unit
	else
		local pitch = math.atan2(to.Y, flat.Magnitude)
		pitch = math.clamp(pitch, -math.rad(L.up), math.rad(L.up))
		if grounded and pitch < 0 then pitch = 0 end
		dir = flat.Unit * math.cos(pitch) + Vector3.new(0, math.sin(pitch), 0)
	end
	local v = dir * L.speed
	st.vx, st.vy, st.vz = v.X, v.Y, v.Z
	Body.kick() -- (Move's fling guard: our own move)
	return true
end
me.CharacterAdded:Connect(function() run = nil end)

return M
