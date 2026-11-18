--!strict
-- weapons batch E: riding a Shopping Cart (CartServer.server owns the carts). on top of one that isn't flying, the key
-- "ride" (F) hops in; then your client drives it (CART.ride: W pushes to 11 m/s, S brakes to a slow roll back, it
-- turns toward where you look, a little side slip) and you stand on it: a local floor under your feet and a local copy
-- of the cart (the server's own follows your feet, a ping late). F hops out, Space jumps out; it rolls on either way
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Body = require(script.Parent:WaitForChild("Body"))
local Binds = require(script.Parent:WaitForChild("Binds"))
local Keys = require(script.Parent:WaitForChild("Keys"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local S = Weapons.S
local RIDE = { acc = 7 * S, top = 11 * S, brake = 9.1 * S, back = 3 * S, fric = 1.4 * S, turn = 2.6, slip = 7, reach = 1.1 * S, upTol = 0.6 * S, H = 1.0 * S }

local riding: { id: number, speed: number, yaw: number, floor: BasePart, look: Model?, server: Model?, sent: number }? = nil

local function remote(): RemoteEvent?
	local r = Remotes:FindFirstChild("Cart")
	return if r and r:IsA("RemoteEvent") then r else nil
end
local function myRoot(): (BasePart?, Humanoid?)
	local ch = me.Character
	return ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?, ch and ch:FindFirstChildOfClass("Humanoid")
end
local function feetOf(root: BasePart, hum: Humanoid): Vector3
	return root.Position - Vector3.new(0, hum.HipHeight + root.Size.Y / 2, 0)
end
local function carts(): { Model }
	local map = workspace:FindFirstChild("Map")
	local f = map and map:FindFirstChild("JankfireCarts")
	local out = {}
	if f then for _, m in f:GetChildren() do if m:IsA("Model") and m:GetAttribute("CartId") then table.insert(out, m) end end end
	return out
end
-- the cart whose top you're standing on (or near enough)
local function nearest(): Model?
	local root, hum = myRoot()
	if not root or not hum then return nil end
	local feet = feetOf(root, hum)
	local best, bd = nil, math.huge
	for _, m in carts() do
		local box = m.PrimaryPart
		if not box or m:GetAttribute("CartState") == "fly" or m:GetAttribute("CartState") == "ride" then continue end
		local top = box.Position + Vector3.new(0, box.Size.Y / 2, 0)
		local d = feet - top
		local flat = Vector3.new(d.X, 0, d.Z).Magnitude
		if flat <= RIDE.reach + box.Size.Z / 2 and math.abs(d.Y) <= RIDE.upTol and flat < bd then best, bd = m, flat end
	end
	return best
end

local function stop(send: boolean)
	local r = riding
	if not r then return end
	riding = nil
	Body.ride = nil
	r.floor:Destroy()
	if r.look then r.look:Destroy() end
	if r.server then for _, d in r.server:GetDescendants() do if d:IsA("BasePart") then d.LocalTransparencyModifier = 0 end end end
	if send then
		local root = myRoot()
		local rm = remote()
		if rm then rm:FireServer("off", if root then root.AssemblyLinearVelocity else nil) end
	end
end
local function start(m: Model)
	local root, hum = myRoot()
	local rm = remote()
	if not root or not hum or not rm then return end
	local floor = Instance.new("Part")
	floor.Name = "CartFloor"; floor.Size = Vector3.new(2.6, 0.2, 2.6); floor.Transparency = 1
	floor.Anchored = true; floor.CanCollide = true; floor.CanQuery = false; floor.CanTouch = false
	floor.Parent = workspace
	-- your own copy of the cart under you; the server's hidden for you
	local look = m:Clone()
	for _, d in look:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
		if d:IsA("WeldConstraint") then d:Destroy() end
	end
	look.Name = "MyCart"
	look.Parent = workspace
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.LocalTransparencyModifier = 1 end end
	local lk = workspace.CurrentCamera.CFrame.LookVector
	riding = { id = m:GetAttribute("CartId") :: number, speed = 0, yaw = math.atan2(-lk.X, -lk.Z), floor = floor, look = look, server = m, sent = os.clock() }
	Body.ride = { v = Vector3.zero }
	rm:FireServer("ride", riding.id)
end

Keys.began(function(io: InputObject, gp: boolean)
	if gp then return end
	if Binds.is("ride", io) then
		if riding then stop(true) return end
		local m = nearest()
		if m then start(m) end
	elseif riding and io.KeyCode == Enum.KeyCode.Space then
		stop(true) -- (Space jumps out: Move's own jump goes on as usual)
	end
end)

local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
RunService.RenderStepped:Connect(function(dt: number)
	local r = riding
	if not r then return end
	local root, hum = myRoot()
	local id = me:GetAttribute("RidingCart")
	-- (the server never said yes within 0.8 s, or it let you go: out)
	if not root or not hum or hum.Health <= 0 or (id ~= r.id and os.clock() - r.sent > 0.8) then stop(false) return end
	if Body.stunned() or me:GetAttribute("PinUntil") or Body.dashing() then stop(true) return end
	-- drive: W pushes, S brakes (to a slow roll back), nothing: it slows; it turns toward your look
	local fwdKey = UserInputService:IsKeyDown(Enum.KeyCode.W)
	local backKey = UserInputService:IsKeyDown(Enum.KeyCode.S)
	local mv = hum.MoveDirection
	local lk = workspace.CurrentCamera.CFrame.LookVector
	local want = math.atan2(-lk.X, -lk.Z)
	local push = fwdKey or (not backKey and mv.Magnitude > 0.5 and mv:Dot(Vector3.new(lk.X, 0, lk.Z).Unit) > 0.3)
	if push then r.speed = math.min(RIDE.top, r.speed + RIDE.acc * dt)
	elseif backKey then r.speed = math.max(-RIDE.back, r.speed - RIDE.brake * dt)
	else r.speed = if r.speed > 0 then math.max(0, r.speed - RIDE.fric * dt) else math.min(0, r.speed + RIDE.fric * dt) end
	local dy = (want - r.yaw + math.pi) % (2 * math.pi) - math.pi
	r.yaw += math.clamp(dy, -RIDE.turn * dt, RIDE.turn * dt)
	local fwd = Vector3.new(-math.sin(r.yaw), 0, -math.cos(r.yaw))
	Body.ride = { v = fwd * r.speed }
	-- the cart on the floor under you, your feet on its top
	local map = workspace:FindFirstChild("Map")
	local groundY = feetOf(root, hum).Y - RIDE.H
	if map then
		mapParams.FilterDescendantsInstances = { map }
		local hit = workspace:Raycast(root.Position, Vector3.new(0, -12, 0), mapParams)
		if hit and not (hit.Instance:IsDescendantOf(map:FindFirstChild("JankfireCarts") or workspace.Terrain)) then groundY = hit.Position.Y end
	end
	local base = Vector3.new(root.Position.X, groundY, root.Position.Z)
	r.floor.CFrame = CFrame.new(base + Vector3.new(0, RIDE.H - 0.1, 0))
	if r.look and r.look.PrimaryPart then r.look:PivotTo(CFrame.new(base + Vector3.new(0, RIDE.H / 2, 0)) * CFrame.Angles(0, r.yaw, 0)) end
end)

