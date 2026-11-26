--!strict
-- the grapple's LOCK-ON ring and the melee LUNGE pip, round the crosshair (26 Nov 2026; docs/MELEE.md).
--   * a rope on a person holds for Config.hook.lockGun / lockMelee s (Move.client). a thin ring round the crosshair
--     empties clockwise over that time; it turns the accent once a melee weapon has tied on (HookTether), and pulses
--     in its last half second. from the attributes Move sets on you: HookLockEnd (server time), HookLockDur, HookTether
--   * the first swing after a reel onto someone (ReelHit, server time): a wider accent ring for that window
--   * with a swung melee weapon out where weapons work: a small pip left of the crosshair filling over the lunge's
--     cooldown (LungeT, the server's; LungeGuess, this screen's), the HUD's other pips' style (HookChargesUI)
-- no words: the ring and the pip are the whole of it (no-flavour-text)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Melee = require(Shared:WaitForChild("Melee"))
local Weapons = require(Shared:WaitForChild("Weapons"))
local T = require(script.Parent:WaitForChild("Theme")) :: any
local W = Weapons.list :: any

local me = Players.LocalPlayer
local function snow(): number return workspace:GetServerTimeNow() end

local gui = T.new("ScreenGui", { Name = "JankMeleeHud", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = true },
	me:WaitForChild("PlayerGui"))

-- a ring drawn in two clipped halves, each a whole circle's stroke under a hard-edged gradient turned to the angle:
-- the right half shows 0..180 degrees clockwise from the top, the left 180..360 (UIGradient on a UIStroke)
local function ring(name: string, size: number, thick: number): (Frame, (number) -> (), (Color3, number) -> ())
	local box = T.new("Frame", { Name = name, BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(size, size), Visible = false }, gui) :: Frame
	local grads: { UIGradient } = {}
	local strokes: { UIStroke } = {}
	for i, side in { "R", "L" } do
		local clip = T.new("Frame", { Name = side, BackgroundTransparency = 1, ClipsDescendants = true,
			Position = UDim2.fromScale(if side == "R" then 0.5 else 0, 0), Size = UDim2.fromScale(0.5, 1) }, box)
		local c = T.new("Frame", { Name = "Circle", BackgroundTransparency = 1,
			Position = UDim2.fromScale(if side == "R" then -1 else 0, 0), Size = UDim2.fromScale(2, 1) }, clip)
		T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, c)
		local s = T.new("UIStroke", { Color = T.TEXT, Thickness = thick, Transparency = 0.1, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, c) :: UIStroke
		local g = T.new("UIGradient", { Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.499, 0),
			NumberSequenceKeypoint.new(0.5, 1), NumberSequenceKeypoint.new(1, 1) }) }, s) :: UIGradient
		grads[i], strokes[i] = g, s
	end
	-- k: how much of the ring is drawn, 0..1, clockwise from the top
	local function set(k: number)
		local a = math.clamp(k, 0, 1) * 360
		grads[1].Rotation = math.min(a, 180) -- (the right half: drawn up to a)
		grads[2].Rotation = math.max(a, 180) -- (the left half: drawn from 180 up to a)
	end
	local function look(c: Color3, alpha: number)
		for _, s in strokes do s.Color = c; s.Transparency = alpha end
	end
	return box, set, look
end

local lockBox, lockSet, lockLook = ring("LockRing", 46, 2.5)
local hitBox, hitSet, hitLook = ring("ReelHitRing", 62, 2)
hitSet(1) -- (the reel-hit ring is always whole: it fades over its window)

-- the lunge pip: left of the crosshair, level with the AUTO GRAPPLE's on the right (HookChargesUI)
local pip = T.new("Frame", { Name = "LungePip", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.45,
	ClipsDescendants = true, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(0.5, -30, 0.5, 31), Size = UDim2.fromOffset(10, 10), Visible = false }, gui)
T.corner(pip, 2)
T.edge(pip, T.TEXT, 0.35, 1)
local pipFill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, AnchorPoint = Vector2.new(0, 1),
	Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 1) }, pip)
T.corner(pipFill, 2)

local FIGHT = { match = true, training = true, playground = true }
local function heldId(): string?
	local ch = me.Character
	local hw = ch and ch:FindFirstChild("HeldWeapon")
	local id = hw and hw:GetAttribute("Weapon")
	return if type(id) == "string" then id else nil
end

local readyFlash = -10
local wasReady = true
RunService.RenderStepped:Connect(function()
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local alive = hum ~= nil and hum.Health > 0
	local sn = snow()
	-- the lock-on ring
	local endT, dur = me:GetAttribute("HookLockEnd"), me:GetAttribute("HookLockDur")
	local showLock = alive and type(endT) == "number" and type(dur) == "number" and dur > 0
	if lockBox.Visible ~= showLock then lockBox.Visible = showLock end
	if showLock then
		local left = math.max(0, (endT :: number) - sn)
		lockSet(left / (dur :: number))
		local tied = me:GetAttribute("HookTether") == true
		local pulse = if left < 0.5 then 0.35 * (0.5 + 0.5 * math.cos(os.clock() * 18)) else 0
		lockLook(if tied then T.ACCENT else T.TEXT, 0.1 + pulse)
	end
	-- the first swing after a reel
	local rh = me:GetAttribute("ReelHit")
	local hitLeft = if alive and type(rh) == "number" then rh - sn else -1
	local showHit = hitLeft > 0
	if hitBox.Visible ~= showHit then hitBox.Visible = showHit end
	if showHit then hitLook(T.ACCENT, 0.15 + 0.6 * (1 - hitLeft / Melee.REEL_HIT.window)) end
	-- the lunge pip
	local w = W[heldId() or ""]
	local showPip = alive and Melee.swung(w) and (FIGHT[me:GetAttribute("Zone") :: any] == true or me:GetAttribute("DevArms") == true)
	if pip.Visible ~= showPip then pip.Visible = showPip end
	if showPip then
		local untilT = math.max(Melee.left(me:GetAttribute("LungeT"), sn), Melee.left(me:GetAttribute("LungeGuess"), sn))
		local k = math.clamp(1 - untilT / Melee.LUNGE.cd, 0, 1)
		local ready = untilT <= 0
		if ready and not wasReady then readyFlash = os.clock() end
		wasReady = ready
		pipFill.Size = UDim2.fromScale(1, k)
		pipFill.BackgroundColor3 = if ready then T.TEXT else T.MUTED
		local f = math.clamp((os.clock() - readyFlash) / 0.35, 0, 1)
		local px = math.floor(10 + 8 * (1 - f) + 0.5)
		if pip.Size.X.Offset ~= px then pip.Size = UDim2.fromOffset(px, px) end
	end
end)
