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
local slipToken = 0

function Body.attach(st: Movement.State, hum: Humanoid, root: BasePart)
	Body.st, Body.hum, Body.root = st, hum, root
	slipToken += 1
end

local function alive(): (Humanoid?, BasePart?)
	local h, r = Body.hum, Body.root
	if not h or not r or h.Health <= 0 or not r.Parent then return nil, nil end
	return h, r
end

-- add a velocity (studs/s) to yourself. upward shoves lift you off the floor so the Humanoid doesn't eat them
function Body.push(v: Vector3)
	local hum, root = alive()
	if not hum or not root then return end
	root.AssemblyLinearVelocity += v
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
	local look = workspace.CurrentCamera.CFrame.LookVector
	local v = root.AssemblyLinearVelocity
	st.vx, st.vy, st.vz = v.X, v.Y, v.Z
	if st.hook then GrappleRemote:FireServer("release") end
	local Sl = Weapons.SLIP
	Movement.slip(st, look.X, look.Z, Sl.time, Sl.fwd, Sl.up)
	root.AssemblyLinearVelocity = Vector3.new(st.vx, st.vy, st.vz)
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

-- the server's knockback (studs/s)
Remotes:WaitForChild("Knock").OnClientEvent:Connect(function(v: unknown)
	if typeof(v) ~= "Vector3" or v.Magnitude > 2000 or v.Magnitude ~= v.Magnitude then return end
	Body.push(v)
	if Body.onKnock then Body.onKnock(v) end
end)
Remotes:WaitForChild("Slip").OnClientEvent:Connect(function(kind: unknown)
	Body.slip(if type(kind) == "string" then kind else "marbles")
end)
-- the server picked a spawn: put yourself there (your client owns your character's position)
Remotes:WaitForChild("Spawn").OnClientEvent:Connect(function(at: unknown)
	if typeof(at) ~= "Vector3" then return end
	task.defer(function()
		local ch = Players.LocalPlayer.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if root and (root.Position - at).Magnitude > 6 then
			(ch :: Model):PivotTo(CFrame.new(at + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)))
			root.AssemblyLinearVelocity = Vector3.zero
		end
	end)
end)

return Body
