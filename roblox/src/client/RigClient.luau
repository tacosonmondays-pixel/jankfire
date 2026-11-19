--!strict
-- the Overdrive Rig gadget, your side (19 Nov 2026; the server is Rig.server, the plan overdrive-gadget-plan.md in the
-- side notes). while the player attribute Rig is set Arsenal hands LMB / RMB here instead of the held gun:
--   LMB down: the punch charges (the server times it from "charge"); LMB up: the ROCKET PUNCH along your look
--   RMB: the MISSILES (5 s apart)
-- and here: everyone's rig moments (the Fx remote's rigon / rigoff / rigpunch / rigpunchhit, the missiles' launch),
-- recordings only (rig_* when they're in, else the nearest we have), and your rig panel: the armour, the time left,
-- the punch and the missiles ready. the arms you see are the hold session's (Viewmodel / ThirdPerson) from these:
--   RigClient.on() -> boolean, RigClient.charge() -> 0..1, RigClient.punched() / fired() -> s since, or nil
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Fx = require(script.Parent:WaitForChild("Fx"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local RigClient = {}
local me = Players.LocalPlayer
local S = Weapons.S
local CHARGE, PUNCH_CD, MISS_CD, DUR, ARMOUR = 0.9, 0.6, 5, 12, 120 -- (Rig.server's R: the panel's scale only)
local PINK, AMBER = Color3.fromRGB(255, 42, 109), Color3.fromRGB(255, 176, 0)

local chargeT: number? = nil
local punchT, missT = -math.huge, -math.huge
local hum: Sound? = nil -- (rig_charge is a loop: it runs while you charge)
local function humOff() if hum then hum:Stop(); hum:Destroy(); hum = nil end end

local function remote(): RemoteEvent?
	local r = Remotes:FindFirstChild("Rig")
	return if r and r:IsA("RemoteEvent") then r else nil
end
local function look(): Vector3 return workspace.CurrentCamera.CFrame.LookVector end
-- a recording by its rig name, else the nearest one we have (until the sound session's rig_* are in)
local function snd(name: string, fallback: string, at: Vector3?, vol: number?)
	if not Sfx.play(name, at, vol) then Sfx.play(fallback, at, vol) end
end

function RigClient.on(): boolean return me:GetAttribute("Rig") ~= nil end
function RigClient.charge(): number return if chargeT then math.clamp((os.clock() - chargeT) / CHARGE, 0, 1) else 0 end
function RigClient.punched(): number? return if punchT > -1e9 then os.clock() - punchT else nil end
function RigClient.fired(): number? return if missT > -1e9 then os.clock() - missT else nil end

-- the buttons (Arsenal, while rigged)
function RigClient.down(btn: string)
	local r = remote()
	if not r then return end
	if btn == "fire" then
		if chargeT then return end
		chargeT = os.clock()
		r:FireServer("charge", true)
		humOff()
		hum = Sfx.play("rig_charge", nil, 0.8)
	elseif btn == "aim" then
		if os.clock() - missT < MISS_CD then snd("rig_denied", "empty", nil, 0.6); return end
		missT = os.clock()
		r:FireServer("miss", look())
		snd("rig_missile", "chicken_fire", nil, 0.9)
	end
end
function RigClient.up(btn: string)
	local r = remote()
	if btn ~= "fire" or not chargeT or not r then return end
	chargeT = nil
	humOff()
	if os.clock() - punchT < PUNCH_CD then r:FireServer("charge", false); return end
	punchT = os.clock()
	r:FireServer("punch", look())
end
me:GetAttributeChangedSignal("Rig"):Connect(function()
	if me:GetAttribute("Rig") == nil then chargeT = nil; humOff() end
end)

-- ------------------------------------------------------------------ everyone's rig moments
local function rootOf(m: any): BasePart?
	return if typeof(m) == "Instance" then (m :: Instance):FindFirstChild("HumanoidRootPart") :: BasePart? else nil
end
Remotes:WaitForChild("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" or type(f.k) ~= "string" then return end
	local k = f.k
	if k == "rigon" then
		local r = rootOf(f.model)
		if r then
			snd("rig_on", "whirr", r.Position, 1)
			Fx.impact(r.Position, Vector3.yAxis, nil, Enum.Material.Metal, { hole = false, scale = 1.2 })
		end
	elseif k == "rigoff" then
		local r = rootOf(f.model)
		if r then
			if f.brk then
				-- the armour gone: the frame bursts into scrap
				Fx.explosion(r.Position + Vector3.new(0, 1, 0), 1.2 * S)
				snd("rig_break", "boom", r.Position, 0.8)
			else
				snd("rig_off", "whirr", r.Position, 0.7)
			end
		end
	elseif k == "rigpunch" and typeof(f.from) == "Vector3" and typeof(f.to) == "Vector3" then
		local c = tonumber(f.c) or 0
		snd("rig_punch", "boom", f.from, 0.45 + 0.4 * c)
		-- the rocket's trail along the dash
		Fx.tracer(f.from, f.to, PINK, (0.25 + 0.35 * c) * S, 0.25)
	elseif k == "rigpunchhit" and typeof(f.at) == "Vector3" then
		snd("rig_punch_hit", "thwack", f.at, 1)
		Fx.impact(f.at, Vector3.yAxis, nil, Enum.Material.Metal, { hole = false, scale = 1.4 + (tonumber(f.c) or 0) })
	end
end)

-- ------------------------------------------------------------------ your rig panel (first person and third)
local panel: { f: Frame, armour: Frame, time: Frame, punch: Frame, miss: Frame }? = nil
local function build()
	local pg = me:FindFirstChildOfClass("PlayerGui")
	if not pg then return nil end
	local old = pg:FindFirstChild("JankRig")
	if old then old:Destroy() end
	local g = T.new("ScreenGui", { Name = "JankRig", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 7, Enabled = false }, pg)
	local f = T.new("Frame", { Name = "Panel", BackgroundColor3 = T.CARD or Color3.fromRGB(22, 24, 30), BackgroundTransparency = 0.15, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -112), Size = UDim2.fromOffset(240, 38) }, g)
	T.corner(f, 6)
	local function bar(y: number, h: number, col: Color3): Frame
		local tr = T.new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.fromOffset(12, y), Size = UDim2.new(1, -60, 0, h) }, f)
		T.corner(tr, 2)
		local fill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = col, Size = UDim2.fromScale(1, 1) }, tr)
		T.corner(fill, 2)
		return fill
	end
	local armour = bar(9, 8, PINK)
	local time = bar(22, 4, Color3.fromRGB(210, 214, 222))
	local function pip(x: number): Frame
		local d = T.new("Frame", { BorderSizePixel = 0, BackgroundColor3 = AMBER, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(1, x, 0.5, 0), Size = UDim2.fromOffset(12, 12) }, f)
		T.corner(d, 6)
		return d
	end
	return { f = f, armour = armour, time = time, punch = pip(-34), miss = pip(-16) }
end
RunService.RenderStepped:Connect(function()
	local on = RigClient.on()
	if on and (not panel or not panel.f.Parent) then panel = build() end
	local P = panel
	if not P then return end
	local g = P.f.Parent :: ScreenGui
	if g.Enabled ~= on then g.Enabled = on end
	if not on then return end
	local a = tonumber(me:GetAttribute("RigArmour")) or 0
	local untilT = tonumber(me:GetAttribute("Rig")) or 0
	P.armour.Size = UDim2.fromScale(math.clamp(a / ARMOUR, 0, 1), 1)
	P.time.Size = UDim2.fromScale(math.clamp((untilT - workspace:GetServerTimeNow()) / DUR, 0, 1), 1)
	local t = os.clock()
	P.punch.BackgroundTransparency = if t - punchT >= PUNCH_CD then 0 else 0.7
	P.miss.BackgroundTransparency = if t - missT >= MISS_CD then 0 else 0.7
	P.punch.BackgroundColor3 = if chargeT then PINK:Lerp(Color3.new(1, 1, 1), RigClient.charge() * 0.6) else AMBER
end)

return RigClient
