--!strict
-- footsteps, jumps, landings and slides for every character (16 Nov 2026), in place of Roblox's default ones.
-- RbxCharacterSounds loops one plastic footstep clip at a fixed rate whatever the floor and the speed; here a step
-- sounds every stride (strides lengthen with speed, so the pace rises gently from a walk to a sprint), picked by the
-- floor under you (hard, metal, wood or soft, four takes each, played through Sfx so they never repeat back to back).
-- your own steps are a little quieter than other people's, whose steps carry about 110 studs (RollMax on the Sounds),
-- so you can hear someone coming. a landing gets louder the harder you came down; a slide scrapes once as it starts.
-- the default Running / Jumping / Landing sounds are silenced (their SoundId emptied, which RbxCharacterSounds never
-- sets again), and Died too: the kill and death stings say that now.
-- sliding is read the way CrouchPoses reads it: your own from the hip dropping, everyone else's from the "Pose"
-- attribute the server puts on their character.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Sfx = require(script.Parent:WaitForChild("Sfx"))

local me = Players.LocalPlayer

local METAL = { Metal = true, CorrodedMetal = true, DiamondPlate = true, Foil = true }
local WOOD = { Wood = true, WoodPlanks = true }
local SOFT = { Grass = true, LeafyGrass = true, Ground = true, Mud = true, Sand = true, Snow = true, Fabric = true,
	Carpet = true, Leather = true, Rubber = true }
local function floorKind(m: Enum.Material): string
	local n = m.Name
	return if METAL[n] then "metal" elseif WOOD[n] then "wood" elseif SOFT[n] then "soft" else "hard"
end

local MUTE = { Running = true, Jumping = true, Landing = true, Died = true }
local function mute(s: Instance)
	if s:IsA("Sound") and MUTE[s.Name] then s.SoundId = "" end
end

type Body = {
	ch: Model, hum: Humanoid, root: BasePart, mine: boolean, hip: number,
	dist: number, air: boolean, fall: number, sliding: boolean, lastLand: number,
}
local bodies: { [Model]: Body } = {}

local function feet(b: Body): Vector3
	return b.root.Position - Vector3.new(0, b.hum.HipHeight + b.root.Size.Y / 2, 0)
end

local function sliding(b: Body): boolean
	if b.mine then return b.hum.HipHeight < b.hip - 0.5 end
	return b.ch:GetAttribute("Pose") == "slide"
end

local function crouched(b: Body): boolean
	return not b.mine and b.ch:GetAttribute("Pose") == "crouch"
end

local function step(b: Body)
	local vol = if b.mine then 0.75 else 1
	if crouched(b) then vol *= 0.45 end
	Sfx.play("step_" .. floorKind(b.hum.FloorMaterial), feet(b), vol)
end

local function track(ch: Model, mine: boolean)
	local hum = ch:WaitForChild("Humanoid", 10) :: Humanoid?
	local root = ch:WaitForChild("HumanoidRootPart", 10) :: BasePart?
	if not hum or not root or not ch.Parent then return end
	for _, d in ipairs(root:GetChildren()) do mute(d) end
	root.ChildAdded:Connect(mute)
	local b: Body = {
		ch = ch, hum = hum, root = root, mine = mine, hip = hum.HipHeight,
		dist = 0, air = false, fall = 0, sliding = false, lastLand = 0,
	}
	bodies[ch] = b
	hum.StateChanged:Connect(function(_, new)
		if new == Enum.HumanoidStateType.Jumping and bodies[ch] then
			Sfx.play("jump", feet(b), if mine then 0.8 else 1)
		end
	end)
	ch.AncestryChanged:Connect(function(_, parent) if not parent then bodies[ch] = nil end end)
	hum.Died:Connect(function() bodies[ch] = nil end)
end

local function watch(p: Player)
	local mine = p == me
	p.CharacterAdded:Connect(function(ch) task.spawn(track, ch, mine) end)
	if p.Character then task.spawn(track, p.Character, mine) end
end
for _, p in ipairs(Players:GetPlayers()) do watch(p) end
Players.PlayerAdded:Connect(watch)

RunService.Heartbeat:Connect(function(dt)
	for ch, b in bodies do
		if not b.root.Parent then bodies[ch] = nil; continue end
		local v = b.root.AssemblyLinearVelocity
		if b.hum.FloorMaterial == Enum.Material.Air then
			b.air = true
			b.fall = math.min(b.fall, v.Y)
			continue
		end
		local now = os.clock()
		if b.air then -- just touched down
			b.air = false
			local speed = -b.fall
			if speed > 14 and now - b.lastLand > 0.25 then
				b.lastLand = now
				Sfx.play("land", feet(b), math.clamp((speed - 6) / 40, 0.3, 1.2) * (if b.mine then 0.85 else 1))
			elseif speed > 4 then
				step(b)
			end
			b.dist = 0
		end
		b.fall = 0
		local sl = sliding(b)
		if sl and not b.sliding then Sfx.play("slide", feet(b), if b.mine then 0.85 else 1) end
		b.sliding = sl
		local hv = Vector3.new(v.X, 0, v.Z).Magnitude
		if sl or hv < 3 then
			b.dist = math.min(b.dist, 1.5) -- (so the first step comes soon after you set off)
			continue
		end
		b.dist += hv * dt
		local stride = math.clamp(2.2 + hv * 0.22, 3.6, 9)
		if b.dist >= stride then
			b.dist -= stride
			step(b)
		end
	end
end)
