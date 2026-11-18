--!strict
-- the Scythe's dash charges on your screen (18 Nov 2026, the owner: "the dash can you get two charges like tracer, a
-- kill recharges the dash like genji", then "can little circles under your crosshair indentify how many dash charges
-- you have and they fill over time"; server/ScytheDash.server.luau counts them, WEAPONS.md "Scythe"). while the scythe
-- form is in your hands, one small circle per charge sits just under the crosshair, drawn like the crosshair's bars
-- (white, a dark rim): a full circle is a dash ready, an empty one fills from the bottom as it comes back (one at a
-- time, dash.cd s apart, counted here from the server's DashN / DashT0). a Scythe kill fills one at once (DashRefundT):
-- its rim flashes the Scythe's teal and the charge click plays. under the grapple's ranked pips (HookChargesUI) when
-- those show too. no text
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any

local me = Players.LocalPlayer
local W = Weapons.list :: any
local D = W.scythe.dash
local MAX = D.charges or 1
local TEAL = W.scythe.color
local BLACK = Color3.new(0, 0, 0)

-- the circles: straight in their own gui, pixel for pixel like the crosshair (FightHud keeps it out of the scaled hud)
local SIZE, GAP, BELOW = 9, 7, 24 -- px: each circle, between them, the row's top under the screen's middle
local gui = T.new("ScreenGui", { Name = "JankDashCharges", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false },
	me:WaitForChild("PlayerGui"))
local row = T.new("Frame", {
	Name = "Circles", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.5, BELOW),
	Size = UDim2.fromOffset(MAX * SIZE + (MAX - 1) * GAP, SIZE),
}, gui)
local circles: { { fill: Frame, rim: UIStroke } } = {}
for i = 1, MAX do
	local holder = T.new("Frame", {
		Name = "Charge" .. i, BackgroundTransparency = 1, Position = UDim2.fromOffset((i - 1) * (SIZE + GAP), 0), Size = UDim2.fromOffset(SIZE, SIZE),
	}, row)
	-- (a CanvasGroup clips the fill to the circle, so it rises inside it like a level)
	local disc = T.new("CanvasGroup", { Name = "Disc", BorderSizePixel = 0, BackgroundColor3 = BLACK, BackgroundTransparency = 0.55, Size = UDim2.fromScale(1, 1) }, holder)
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, disc)
	local fill = T.new("Frame", {
		Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 1),
	}, disc)
	local ring = T.new("Frame", { Name = "Rim", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, holder)
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, ring)
	local rim = T.new("UIStroke", { Thickness = 1, Color = BLACK, Transparency = 0.4 }, ring)
	circles[i] = { fill = fill, rim = rim }
end

local function held(): string?
	local ch = me.Character
	local hw = ch and ch:FindFirstChild("HeldWeapon")
	local id = hw and hw:GetAttribute("Weapon")
	return if type(id) == "string" then id else nil
end

-- charges now and how far the next one is along (0..1): the server writes on a dash, a refund and a spawn; the ones
-- coming back on their own are counted here the way the server counts them
local function counts(): (number, number)
	local n = tonumber(me:GetAttribute("DashN")) or MAX
	local t0 = tonumber(me:GetAttribute("DashT0")) or 0
	if t0 <= 0 or n >= MAX then return math.min(n, MAX), 0 end
	local now = workspace:GetServerTimeNow()
	while n < MAX and now - t0 >= D.cd do
		n += 1
		t0 += D.cd
	end
	return n, if n < MAX then math.clamp((now - t0) / D.cd, 0, 1) else 0
end

local flashT = -math.huge
me:GetAttributeChangedSignal("DashRefundT"):Connect(function()
	flashT = os.clock()
	pcall(Sfx.play, "click", nil, 1, 1.35) -- (Arsenal's charge-home click)
end)

RunService.RenderStepped:Connect(function()
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local fight = pg and pg:FindFirstChild("JankfireFight")
	local cross = fight and fight:FindFirstChild("Crosshair")
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local id = held()
	local w = if id then W[id] else nil
	-- (the scythe form only, alive, out of the hub, and only while the crosshair itself is up)
	local show = w ~= nil and w.dash ~= nil and hum ~= nil and hum.Health > 0 and me:GetAttribute("Zone") ~= "hub"
		and fight ~= nil and (fight :: ScreenGui).Enabled and cross ~= nil and (cross :: GuiObject).Visible
	if gui.Enabled ~= show then gui.Enabled = show end
	if not show then return end
	-- (the grapple's ranked pips sit at +26: these go under them while they show)
	local hook = pg and pg:FindFirstChild("JankHookCharges")
	local y = if hook and hook:IsA("ScreenGui") and hook.Enabled then BELOW + 16 else BELOW
	if row.Position.Y.Offset ~= y then row.Position = UDim2.new(0.5, 0, 0.5, y) end
	local n, frac = counts()
	local fl = math.clamp(1 - (os.clock() - flashT) / 0.5, 0, 1)
	for i, c in circles do
		local k = if i <= n then 1 elseif i == n + 1 then frac else 0
		c.fill.Size = UDim2.fromScale(1, k)
		c.fill.BackgroundColor3 = if i <= n then T.TEXT else T.MUTED
		local flash = i == n and fl > 0 -- (the one a kill just filled)
		c.rim.Color = if flash then BLACK:Lerp(TEAL, fl) else BLACK
		c.rim.Thickness = if flash then 1 + fl else 1
		c.rim.Transparency = if flash then 0 else 0.4
	end
end)
