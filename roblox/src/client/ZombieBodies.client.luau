--!strict
-- ZOMBIES bodies on this client (27 Nov 2026, the owner: "make sure they can be dismembered and body parts aren't
-- floating after they die!!"). The server ragdolls a dead zombie and lets it lie (Zombies.luau ragdoll), throws off the
-- pieces a hit takes (ZombieSpecial cut); this draws the rest, locally:
--   * the fade: a corpse (ZmFade on its model) or a loose piece (ZmFade on the part) fades out over FADE s from that
--     server time (LocalTransparencyModifier: no property traffic), and the server removes it after
--   * a piece coming off (ZmLimb): a small puff of grey dust where it leaves (no blood, no red: cartoon) and a dull
--     recorded thump (zm_limb, the library's)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local okSfx, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
local FADE = 0.6
local DOT = "rbxassetid://107753175681578" -- (the VFX library's soft round glow, vfx_glow)
local DUST = Color3.fromRGB(150, 148, 142)

local function srv(): number return workspace:GetServerTimeNow() end
local function arena(): Model?
	local n = me:GetAttribute("ZmArena")
	local a = if type(n) == "string" then workspace:FindFirstChild(n) else nil
	return if a and a:IsA("Model") then a else nil
end

-- what's fading: the thing (a model or a part) -> when it started (server time)
local fading: { [Instance]: number } = {}
local function watch(x: Instance)
	local function read()
		local t = x:GetAttribute("ZmFade")
		if type(t) == "number" then fading[x] = t end
	end
	read()
	x:GetAttributeChangedSignal("ZmFade"):Connect(read)
end

-- the dust puff where a piece left the body: a few soft grey blobs, gone in half a second
local function puff(at: Vector3)
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.Transparency = 1
	p.Size = Vector3.new(0.6, 0.6, 0.6)
	p.CFrame = CFrame.new(at)
	local e = Instance.new("ParticleEmitter")
	e.Texture = DOT
	e.Color = ColorSequence.new(DUST)
	e.LightInfluence = 1
	e.LightEmission = 0.05
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 1.4) })
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 1) })
	e.Lifetime = NumberRange.new(0.35, 0.6)
	e.Speed = NumberRange.new(2, 5)
	e.SpreadAngle = Vector2.new(180, 180)
	e.Drag = 6
	e.Acceleration = Vector3.new(0, 1.5, 0)
	e.Rate = 0
	e.Parent = p
	p.Parent = workspace
	e:Emit(9)
	task.delay(0.8, function() p:Destroy() end)
end
local lastSound = 0
local function limbOff(part: BasePart)
	puff(part.Position)
	local t = os.clock()
	if t - lastSound > 0.06 and okSfx and Sfx then -- (a blast takes four at once: one thump)
		lastSound = t
		pcall((Sfx :: any).play, "zm_limb", part.Position, 1)
	end
end

-- the corpses (workspace.Dummies) and the loose pieces (the arena's children)
local dm = workspace:WaitForChild("Dummies", 30)
if dm then
	for _, c in dm:GetChildren() do watch(c) end
	dm.ChildAdded:Connect(watch)
end
local seenArena: Model? = nil
local arenaConn: RBXScriptConnection? = nil
task.spawn(function()
	while true do
		local a = arena()
		if a ~= seenArena then
			if arenaConn then arenaConn:Disconnect(); arenaConn = nil end
			seenArena = a
			if a then
				arenaConn = a.ChildAdded:Connect(function(c: Instance)
					if not c:IsA("BasePart") or c:GetAttribute("ZmFade") == nil then return end
					watch(c) -- (every piece of a limb fades; the first one puffs and thumps for it)
					if c:GetAttribute("ZmLimb") == true then limbOff(c) end
				end)
			end
		end
		task.wait(1)
	end
end)

RunService.RenderStepped:Connect(function()
	local t = srv()
	for x, t0 in fading do
		if not x.Parent then fading[x] = nil; continue end
		local u = math.clamp((t - t0) / FADE, 0, 1)
		if u <= 0 then continue end
		if x:IsA("BasePart") then
			x.LocalTransparencyModifier = u
		else
			for _, d in x:GetDescendants() do
				if d:IsA("BasePart") or d:IsA("Decal") then (d :: any).LocalTransparencyModifier = u end
			end
		end
		if u >= 1 then fading[x] = nil end
	end
end)
