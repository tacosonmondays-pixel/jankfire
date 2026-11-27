--!strict
-- ZOMBIES lights, this client's side (27 Nov 2026, the owner: "Can you make zombies having glowing eyes, also some parts
-- of the map you need a flashlight it'll be like most games f for flashlight?"; the server's side: server/ZombieLight.luau)
--   * every beam: each other player of your game with ZmLight on, and each squad bot whose body has ZmLight (on in a
--     dark area before the power), carries a SpotLight from the head, made here so everyone sees everyone's (ForestLife's
--     pattern). Yours rides your camera instead (the head doesn't tilt with your look), the only one with shadows
--   * F (Binds "light"; a pad's D-pad up; the phone's LIGHT) asks the server to turn yours on or off, with a recorded
--     click. While your rope is on something F is the yank's / the reel's (Move.client): the light leaves it alone then
--   * the dark areas (ZM.DARK) before the power: while your camera is in one the light here eases down to near-black (a
--     faint fill, so you can still move) and comes back as you leave or the power comes on. Films own the light (ZmFilm)
--   * a boss's eyes get a faint light of their own (no other zombie has one: 36 at a time would cost too much)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local Keys = require(script.Parent:WaitForChild("Keys")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local okSfx, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
local zr = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Zm") :: RemoteEvent

local BEAM, GLOW = "ZmBeam", "ZmEyeGlow"
local WARM = Color3.fromRGB(255, 238, 212) -- (a warm white)
local DARK_AMB, DARK_OUT = Color3.fromRGB(16, 18, 24), Color3.fromRGB(18, 21, 28)
local DARK_EXP = 0.7 -- (exposure down by this much, fully dark)
local EASE = 0.6 -- (s, in and out)
local BOSS: { [string]: boolean } = {}
for _, b in ZM.BOSSES do BOSS[b] = true end

local function inGame(): boolean return me:GetAttribute("ZmOn") == true end
local function arena(): Model?
	local n = me:GetAttribute("ZmArena")
	local a = if type(n) == "string" then workspace:FindFirstChild(n) else nil
	return if a and a:IsA("Model") then a else nil
end
local maps: { [Model]: any } = {}
local function mapOf(a: Model): any
	local m = maps[a]
	if m == nil then
		local ok, r = pcall(ZM.read, a)
		m = if ok and r then r else false
		maps[a] = m
		a.Destroying:Connect(function() maps[a] = nil end)
	end
	return if m then m else nil
end
local function headOf(m: Instance?): BasePart?
	local h = m and m:FindFirstChild("Head")
	return if h and h:IsA("BasePart") then h else nil
end

-- ------------------------------------------------------------ the beams (others', the bots')
local function setBeam(head: BasePart?, on: boolean)
	if not head then return end
	local l = head:FindFirstChild(BEAM)
	if on and not l then
		local s = Instance.new("SpotLight")
		s.Name = BEAM
		s.Face = Enum.NormalId.Front
		s.Angle, s.Range, s.Brightness = 42, 48, 2.4
		s.Color = WARM
		s.Shadows = false
		s.Parent = head
	elseif not on and l then
		l:Destroy()
	end
end
local function setGlow(head: BasePart?)
	if not head or head:FindFirstChild(GLOW) then return end
	local l = Instance.new("PointLight")
	l.Name = GLOW
	l.Range, l.Brightness = 7, 0.7
	l.Color = ZM.EYE
	l.Shadows = false
	l.Parent = head
end
local function sweep()
	local a = arena()
	local live = inGame() and a ~= nil
	local myArena = me:GetAttribute("ZmArena")
	for _, p in Players:GetPlayers() do
		setBeam(headOf(p.Character), live and p ~= me and p:GetAttribute("ZmArena") == myArena and p:GetAttribute("ZmLight") == true)
	end
	if a then
		for _, c in a:GetChildren() do -- (the squad's bots live in the arena)
			if c:IsA("Model") and string.match(c.Name, "^Bot %d+$") then setBeam(headOf(c), live and c:GetAttribute("ZmLight") == true) end
		end
	end
	local dm = workspace:FindFirstChild("Dummies") -- (the zombies live here: docs/ZOMBIES.md)
	if dm and live then
		for _, c in dm:GetChildren() do
			local ty = c:GetAttribute("ZmType")
			if type(ty) == "string" and BOSS[ty] then setGlow(headOf(c)) end
		end
	end
end
task.spawn(function()
	while true do
		local ok, err = pcall(sweep)
		if not ok and RunService:IsStudio() then warn("[ZombieLight] " .. tostring(err)) end
		task.wait(0.25)
	end
end)

-- ------------------------------------------------------------ your own light (on the camera) and the toggle
local myPart: BasePart? = nil
local function myLight(on: boolean)
	if on and not myPart then
		local p = Instance.new("Part")
		p.Name = "ZmMyLight"
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
		p.Transparency = 1
		p.Size = Vector3.new(0.2, 0.2, 0.2)
		local s = Instance.new("SpotLight")
		s.Face = Enum.NormalId.Front
		s.Angle, s.Range, s.Brightness = 40, 56, 2.6
		s.Color = WARM
		s.Shadows = true
		s.Parent = p
		p.Parent = workspace
		myPart = p
	elseif not on and myPart then
		myPart:Destroy()
		myPart = nil
	end
end
Keys.began(function(io: any, gp: boolean)
	if gp or not inGame() or not Binds.is("light", io) then return end
	if me:GetAttribute("OnRope") == true or me:GetAttribute("ZmFilm") == true then return end
	zr:FireServer({ k = "light" })
	if okSfx and Sfx then pcall((Sfx :: any).play, "zm_flashlight", nil, 0.8) end
end)

-- ------------------------------------------------------------ the dark areas
local k, want, nextCheck = 0, 0, 0
local base: any = nil -- the light as it was (or as the look last set it), from before the dark
local wrote: any = nil -- what this script last wrote (anything else: someone else changed the light)
local function darkHere(): boolean
	if not inGame() or me:GetAttribute("ZmFilm") == true then return false end
	local a = arena()
	if not a or a:GetAttribute("Power") == true then return false end
	local map = mapOf(a)
	local cam = workspace.CurrentCamera
	if not map or not cam then return false end
	local id = ZM.areaAt(map, cam.CFrame.Position)
	return id ~= nil and ZM.DARK[id] == true
end
local function restore()
	if base then
		Lighting.Ambient, Lighting.OutdoorAmbient, Lighting.ExposureCompensation = base.amb, base.out, base.exp
	end
	base, wrote, k = nil, nil, 0
end

RunService.RenderStepped:Connect(function(dt: number)
	-- yours
	myLight(inGame() and me:GetAttribute("ZmLight") == true and me.Character ~= nil and me:GetAttribute("ZmFilm") ~= true)
	local cam = workspace.CurrentCamera
	if myPart and cam then myPart.CFrame = cam.CFrame * CFrame.new(0.35, -0.45, -0.6) end
	-- the dark
	local t = os.clock()
	if t >= nextCheck then nextCheck = t + 0.15; want = if darkHere() then 1 else 0 end
	if me:GetAttribute("ZmFilm") == true then if base then restore() end; return end
	if want == 0 and k == 0 then return end
	if wrote and (Lighting.Ambient ~= wrote.amb or Lighting.OutdoorAmbient ~= wrote.out or math.abs(Lighting.ExposureCompensation - wrote.exp) > 1e-3) then
		base = { amb = Lighting.Ambient, out = Lighting.OutdoorAmbient, exp = Lighting.ExposureCompensation } -- (the look changed it)
	end
	if not base then base = { amb = Lighting.Ambient, out = Lighting.OutdoorAmbient, exp = Lighting.ExposureCompensation } end
	k = if want > k then math.min(1, k + dt / EASE) else math.max(0, k - dt / EASE)
	if k <= 0 then restore(); return end
	local amb, out, exp = base.amb:Lerp(DARK_AMB, k), base.out:Lerp(DARK_OUT, k), base.exp - DARK_EXP * k
	if wrote == nil or wrote.k ~= k then
		Lighting.Ambient, Lighting.OutdoorAmbient, Lighting.ExposureCompensation = amb, out, exp
		wrote = { amb = Lighting.Ambient, out = Lighting.OutdoorAmbient, exp = Lighting.ExposureCompensation, k = k }
	end
end)
