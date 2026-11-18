--!strict
-- T-BAG, the client side (18 Nov 2026, the owner: "bring back tbagging explosion"; server: TBag.server.luau).
--   * your crouch presses go to the server (the TBag remote); the server counts them (14 in 4 s and your knees go)
--   * the warning, on everyone's screen for everyone: from the 9th press (TBagHeat on that player, 0..1) a hot glow
--     and sparks round their legs and a sizzle, growing with the heat, gone when it cools. no text
--   * the blast itself is the frag's (the server sends the same "boom": Utility.client draws it, sounds it and shakes
--     the screens near it)
-- cheap: the glow is built once per body when it first heats up and only retuned when the heat changes (4 times a
-- second at most); nothing runs per frame
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Keys = require(script.Parent:WaitForChild("Keys"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local remote = Remotes:WaitForChild("TBag") :: RemoteEvent
local me = Players.LocalPlayer

-- ---------------------------------------------------------------- your presses
Keys.began(function(io: InputObject, gp: boolean)
	if gp or not Binds.is("crouch", io) then return end
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if hum and hum.Health > 0 then remote:FireServer() end
end)

-- ---------------------------------------------------------------- the warning on a body
local HOT = Color3.fromRGB(255, 132, 48)
local sizzleSrc: Sound? = nil
do
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	for _, n in { "tbag_sizzle", "sizzle", "fuse_tick", "fuse" } do
		local s = lib and lib:FindFirstChild(n)
		if s and s:IsA("Sound") then sizzleSrc = s; break end
	end
end

type Glow = { att: Attachment, sparks: ParticleEmitter, haze: ParticleEmitter, light: PointLight, sound: Sound? }
local glows: { [Model]: Glow } = {}

local function build(ch: Model): Glow?
	local part = (ch:FindFirstChild("LowerTorso") or ch:FindFirstChild("HumanoidRootPart")) :: BasePart?
	if not part then return nil end
	local att = Instance.new("Attachment")
	att.Name = "TBagHeat"
	att.Position = Vector3.new(0, -0.6, 0)
	local sparks = Instance.new("ParticleEmitter")
	sparks.Name = "Sparks"
	sparks.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	sparks.Color = ColorSequence.new(Color3.fromRGB(255, 220, 150), Color3.fromRGB(255, 96, 32))
	sparks.LightEmission = 1
	sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.32), NumberSequenceKeypoint.new(1, 0) })
	sparks.Lifetime = NumberRange.new(0.25, 0.55)
	sparks.Speed = NumberRange.new(7, 14)
	sparks.SpreadAngle = Vector2.new(70, 70)
	sparks.Acceleration = Vector3.new(0, -36, 0)
	sparks.Drag = 2
	sparks.Rate = 0
	sparks.Parent = att
	local haze = Instance.new("ParticleEmitter")
	haze.Name = "Haze"
	haze.Texture = "rbxasset://textures/particles/fire_main.dds"
	haze.Color = ColorSequence.new(HOT, Color3.fromRGB(255, 70, 30))
	haze.LightEmission = 1
	haze.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.2), NumberSequenceKeypoint.new(1, 2.2) })
	haze.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(1, 1) })
	haze.Lifetime = NumberRange.new(0.35, 0.6)
	haze.Speed = NumberRange.new(1, 2.5)
	haze.SpreadAngle = Vector2.new(25, 25)
	haze.LockedToPart = true
	haze.Rate = 0
	haze.Parent = att
	local light = Instance.new("PointLight")
	light.Color = HOT
	light.Shadows = false
	light.Brightness = 0
	light.Range = 6
	light.Parent = att
	local sound: Sound? = nil
	if sizzleSrc then
		local s = sizzleSrc:Clone()
		s.Name = "Sizzle"
		s.Looped = true
		s.Volume = 0
		s.RollOffMaxDistance = 80
		s.Parent = att
		s:Play()
		sound = s
	end
	att.Parent = part
	return { att = att, sparks = sparks, haze = haze, light = light, sound = sound }
end

local function tune(g: Glow, h: number)
	g.sparks.Rate = 20 + 140 * h
	g.haze.Rate = 6 + 28 * h
	g.light.Brightness = 0.8 + 4 * h
	g.light.Range = 6 + 9 * h
	if g.sound then
		g.sound.Volume = 0.15 + 0.6 * h
		g.sound.PlaybackSpeed = 0.9 + 0.45 * h
	end
end

local function drop(ch: Model)
	local g = glows[ch]
	if not g then return end
	glows[ch] = nil
	g.att:Destroy()
end

local function update(p: Player)
	local ch = p.Character
	local h = p:GetAttribute("TBagHeat")
	if type(h) ~= "number" or h <= 0 or not ch then
		if ch then drop(ch) end
		return
	end
	local g = glows[ch]
	if not g or not g.att.Parent then
		g = build(ch)
		if not g then return end
		glows[ch] = g
	end
	tune(g :: Glow, math.clamp(h, 0, 1))
end

local function watch(p: Player)
	p:GetAttributeChangedSignal("TBagHeat"):Connect(function() update(p) end)
	p.CharacterRemoving:Connect(function(ch: Model) drop(ch) end)
	update(p)
end
Players.PlayerAdded:Connect(watch)
for _, p in Players:GetPlayers() do watch(p) end
