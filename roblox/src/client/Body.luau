--!strict
-- the bridge between the weapons and your movement (Move.client.luau owns it, like the web game's player.js): your own
-- recoil shoves, the server's knockback (it sends the velocity, your client adds it), marble slips and spawns.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Movement = require(Shared:WaitForChild("Movement"))
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local GrappleRemote = Remotes:WaitForChild("Grapple") :: RemoteEvent

local Body = {}
Body.st = nil :: Movement.State?
Body.hum = nil :: Humanoid?
Body.root = nil :: BasePart?
Body.onSlip = nil :: ((string) -> ())?
Body.onKnock = nil :: ((Vector3) -> ())?
-- every physics step, after the movement maths, before the velocity is applied: (your movement state, your chest,
-- dt). the rubber duck's black hole eats your momentum here (Utility.client.luau)
Body.onStep = nil :: ((any, Vector3, number) -> ())?
-- a run-speed boost on top of speedMul (the pop quiz's gold star: x1.25 for 4 s, Utility.client.luau)
Body.boost = 1
-- (the owner's dev menu, OwnerDev.client) run speed x this (the server's DevSpeed), and flying: while it flies the
-- body, the movement script stands down (Move.client)
Body.devSpeed = 1
Body.flying = false
-- how fast you run right now, x the usual (Arsenal sets it: the gun in your hands, and slower down the sights)
Body.speedMul = 1
-- (19 Nov 2026) a hub mini-game's own pace on top: the boxing ring's guard (MiniBoxUI sets it, puts back 1 on leaving)
Body.mini = 1
-- (weapons batch A, 18 Nov 2026; WeaponStates.client sets these from the server's attributes on you) soaked by a Water
-- Pistol: run speed x wet, ground friction x grip (slidey). pinned by a Nail Gun: pulled to `at` (where your feet go)
-- until `untilT` (workspace:GetServerTimeNow()), no jumping
Body.wet, Body.grip = 1, 1
Body.pin = nil :: { at: Vector3, untilT: number }?
function Body.pinned(): boolean
	local p = Body.pin
	return p ~= nil and workspace:GetServerTimeNow() < p.untilT
end
-- (weapons batch B) stunned by a Taser until this server time: no moving, jumping, firing or swinging (WeaponStates)
Body.stunUntil = 0
-- (the Scythe) the server's dash: this velocity, flat, until this server time (WeaponStates sets it from DashV / DashUntil)
Body.dash = nil :: { v: Vector3, untilT: number }?
-- (batch E) riding a Shopping Cart: the cart's velocity, flat (CartRide.client drives it; Move runs you along it)
Body.ride = nil :: { v: Vector3 }?
-- (batch E) on someone's Lasso: the velocity that takes you where the server says (LassoClient), nothing of your own
Body.held = nil :: { v: Vector3 }?
function Body.dashing(): boolean
	local d = Body.dash
	return d ~= nil and workspace:GetServerTimeNow() < d.untilT
end
function Body.stunned(): boolean return workspace:GetServerTimeNow() < Body.stunUntil end
-- when one of our own moves last threw you (a push, a knock, a slip, a ledge launch, a shredder pull). Move's fling
-- guard lets a sudden jump in speed through only just after one of these: anything else is a collision spike
Body.kickT = -10
-- (19 Nov 2026, the fling fix) the velocity the last throw set, or nil after a bare kick (Move's own pulls). Move's
-- guard used to let ANY jump through for 0.15 s after a kick: a shove into a wall or a corner turned the wall's push-
-- back into a fling. now, after a throw, it only lets through up to what the throw set
Body.throwV = nil :: Vector3?
function Body.kick() Body.kickT = os.clock(); Body.throwV = nil end
local slipToken = 0
-- (the fling fix) the slip you're in: how fast you were going as it began (flat, and up). Body.slipClamp
local slipStart: { h: number, up: number }? = nil

function Body.attach(st: Movement.State, hum: Humanoid, root: BasePart)
	Body.st, Body.hum, Body.root = st, hum, root
	slipToken += 1
end

local function alive(): (Humanoid?, BasePart?)
	local h, r = Body.hum, Body.root
	if not h or not r or h.Health <= 0 or not r.Parent then return nil, nil end
	return h, r
end

-- set your velocity as one of our own throws: Move's fling guard lets it through, and Move's LinearVelocity takes it
-- as its target at once (a knock can land after Move has set this frame's target, which then braked it to nothing)
function Body.throw(v: Vector3)
	local root = Body.root
	if not root or not root.Parent then return end
	Body.kick()
	Body.throwV = v
	root.AssemblyLinearVelocity = v
	local jm = root:FindFirstChild("JankMove")
	if jm and jm:IsA("LinearVelocity") then jm.PlaneVelocity = Vector2.new(v.X, v.Z) end
	local st = Body.st
	if st then st.vx, st.vy, st.vz = v.X, v.Y, v.Z end
end

-- add a velocity (studs/s) to yourself. upward shoves lift you off the floor so the Humanoid doesn't eat them
function Body.push(v: Vector3)
	local hum, root = alive()
	if not hum or not root then return end
	Body.throw(root.AssemblyLinearVelocity + v)
	if v.Y > 1.5 and hum.FloorMaterial ~= Enum.Material.Air then
		root.CFrame += Vector3.new(0, 0.06, 0)
		hum:ChangeState(Enum.HumanoidStateType.Freefall)
	end
end

-- you slipped (marbles): feet out along your look, flat on your back for 1.7 s, no jumping, off the rope
function Body.slip(kind: string)
	local hum, root = alive()
	local st = Body.st
	if not hum or not root or not st then return end
	if Body.slipping() then return end -- (19 Nov 2026, the fling fix: one slip at a time. the server holds them 3.2 s apart too)
	local look = workspace.CurrentCamera.CFrame.LookVector
	local v = root.AssemblyLinearVelocity
	st.vx, st.vy, st.vz = v.X, v.Y, v.Z
	if st.hook then GrappleRemote:FireServer("release") end
	local Sl = Weapons.SLIP
	Movement.slip(st, look.X, look.Z, Sl.time, Sl.fwd, Sl.up)
	slipStart = { h = math.sqrt(st.vx * st.vx + st.vz * st.vz), up = st.vy }
	Body.throw(Vector3.new(st.vx, st.vy, st.vz))
	hum:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)
	hum.PlatformStand = true -- the body goes over (jank), the movement maths keeps sliding it
	root.AssemblyAngularVelocity = Vector3.new(-look.Z, 0, look.X) * -6
	slipToken += 1
	local my = slipToken
	task.delay(Sl.time, function()
		if my ~= slipToken or not hum.Parent then return end
		hum.PlatformStand = false
		hum:SetStateEnabled(Enum.HumanoidStateType.Jumping, true)
		hum:ChangeState(Enum.HumanoidStateType.GettingUp)
	end)
	if Body.onSlip then Body.onSlip(kind) end
end

function Body.slipping(): boolean
	local st = Body.st
	return st ~= nil and (st.slip or 0) > 0
end

-- (19 Nov 2026, the fling fix; Move runs it every step after the movement maths) while you slip you're never faster
-- than SLIP.cap, or than you were as the slip began (a Hand Slapper's slap comes with its slip), that allowance easing
-- down to the cap by the time you're up; and you climb no faster than either. with next to no friction on your back,
-- anything that sped you up mid-slip (a wall's push-back in a corner, a rocket) used to carry you across the map
function Body.slipClamp(st: Movement.State)
	if (st.slip or 0) <= 0 then slipStart = nil; return end
	local Sl = Weapons.SLIP
	local s0 = slipStart
	local left = math.clamp((st.slip :: number) / Sl.time, 0, 1)
	local capH = Sl.cap + math.max(0, (if s0 then s0.h else 0) - Sl.cap) * left
	local hs = math.sqrt(st.vx * st.vx + st.vz * st.vz)
	if hs > capH then st.vx, st.vz = st.vx * capH / hs, st.vz * capH / hs end
	local capUp = math.max(Sl.cap, if s0 then s0.up else 0)
	if st.vy > capUp then st.vy = capUp end
end

-- the server's knockback (studs/s)
Remotes:WaitForChild("Knock").OnClientEvent:Connect(function(v: unknown)
	if typeof(v) ~= "Vector3" or v.Magnitude > 2000 or v.Magnitude ~= v.Magnitude then return end
	-- (19 Nov 2026, the fling fix) on your back on marbles nothing holds you: a knock lands SLIP.knock at most (the
	-- server caps it too, Fight.knock)
	local kc = Weapons.SLIP.knock
	if Body.slipping() and v.Magnitude > kc then v = v.Unit * kc end
	Body.push(v)
	if Body.onKnock then Body.onKnock(v) end
end)
Remotes:WaitForChild("Slip").OnClientEvent:Connect(function(kind: unknown)
	Body.slip(if type(kind) == "string" then kind else "marbles")
end)
-- the server picked a spawn: put yourself there (your client owns your character's position), facing the way the
-- spawn faces (17 Nov: the camera kept its old heading through a respawn, so a round could open on a blank wall)
Remotes:WaitForChild("Spawn").OnClientEvent:Connect(function(at: unknown, look: unknown)
	if typeof(at) ~= "Vector3" then return end
	local face = if typeof(look) == "Vector3" and Vector3.new(look.X, 0, look.Z).Magnitude > 1e-3 then Vector3.new(look.X, 0, look.Z).Unit else nil
	task.defer(function()
		local ch = Players.LocalPlayer.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if root and (root.Position - at).Magnitude > 6 then
			local pos = at + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)
			;(ch :: Model):PivotTo(if face then CFrame.lookAt(pos, pos + face) else CFrame.new(pos))
			root.AssemblyLinearVelocity = Vector3.zero
		end
		if face then
			task.wait(0.05)
			local cam = workspace.CurrentCamera
			local p = cam.CFrame.Position
			cam.CFrame = CFrame.lookAt(p, p + face)
		end
	end)
end)

return Body
