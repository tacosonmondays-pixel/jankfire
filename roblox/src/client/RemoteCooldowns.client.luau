--!strict
-- the TV Remote's two cooldowns on your screen (21 Nov 2026: pause 7 s, rewind 10 s, and either locks the other for
-- 1.5 s, server/WeaponTricks.server.luau). drawn like the Scythe's dash charges (ScytheDash.client.luau): while the Remote
-- is in your hands, two small circles sit just under the crosshair, the left one the left click (pause), the right one
-- the right click (rewind). a full white circle is ready; an empty one fills from the bottom as it comes back, from the
-- server's own ready times (player attributes TVPauseT / TVRewindT, server time), so it never says ready early. its
-- rim flashes the Remote's pink as it fills. a click before then gets Arsenal's dry click. no text
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local T = require(script.Parent:WaitForChild("Theme")) :: any

local me = Players.LocalPlayer
local W = Weapons.list :: any
local PINK = W.remote.color
local BLACK = Color3.new(0, 0, 0)
local KEYS = { "TVPauseT", "TVRewindT" }

local SIZE, GAP, BELOW = 9, 7, 24 -- px, as the dash charges (the two are never in your hands at once)
local gui = T.new("ScreenGui", { Name = "JankRemoteCooldowns", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false },
	me:WaitForChild("PlayerGui"))
local row = T.new("Frame", {
	Name = "Circles", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.5, BELOW),
	Size = UDim2.fromOffset(2 * SIZE + GAP, SIZE),
}, gui)
type Circle = { fill: Frame, rim: UIStroke, key: string, from: number, was: boolean, flashT: number }
local circles: { Circle } = {}
for i, key in KEYS do
	local holder = T.new("Frame", {
		Name = key, BackgroundTransparency = 1, Position = UDim2.fromOffset((i - 1) * (SIZE + GAP), 0), Size = UDim2.fromOffset(SIZE, SIZE),
	}, row)
	local disc = T.new("CanvasGroup", { Name = "Disc", BorderSizePixel = 0, BackgroundColor3 = BLACK, BackgroundTransparency = 0.55, Size = UDim2.fromScale(1, 1) }, holder)
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, disc)
	local fill = T.new("Frame", {
		Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 1),
	}, disc)
	local ring = T.new("Frame", { Name = "Rim", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, holder)
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, ring)
	local rim = T.new("UIStroke", { Thickness = 1, Color = BLACK, Transparency = 0.4 }, ring)
	local c: Circle = { fill = fill, rim = rim, key = key, from = 0, was = true, flashT = -math.huge }
	circles[i] = c
	-- (a new ready time: the wait starts now)
	me:GetAttributeChangedSignal(key):Connect(function() c.from = workspace:GetServerTimeNow() end)
end

local function held(): string?
	local ch = me.Character
	local hw = ch and ch:FindFirstChild("HeldWeapon")
	local id = hw and hw:GetAttribute("Weapon")
	return if type(id) == "string" then id else nil
end

RunService.RenderStepped:Connect(function()
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local fight = pg and pg:FindFirstChild("JankfireFight")
	local cross = fight and fight:FindFirstChild("Crosshair")
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local id = held()
	local w = if id then W[id] else nil
	-- (the Remote only, alive, out of the hub, and only while the crosshair itself is up)
	local show = w ~= nil and w.rewind ~= nil and hum ~= nil and hum.Health > 0 and (me:GetAttribute("Zone") ~= "hub" or me:GetAttribute("DevArms") == true)
		and fight ~= nil and (fight :: ScreenGui).Enabled and cross ~= nil and (cross :: GuiObject).Visible
	if gui.Enabled ~= show then gui.Enabled = show end
	if not show then return end
	local hook = pg and pg:FindFirstChild("JankHookCharges")
	local y = if hook and hook:IsA("ScreenGui") and hook.Enabled then BELOW + 16 else BELOW
	if row.Position.Y.Offset ~= y then row.Position = UDim2.new(0.5, 0, 0.5, y) end
	local now = workspace:GetServerTimeNow()
	for _, c in circles do
		local t = me:GetAttribute(c.key)
		local ready = type(t) ~= "number" or now >= t
		local k = 1
		if not ready then
			local span = (t :: number) - c.from
			k = if span > 0.05 then math.clamp((now - c.from) / span, 0, 1) else 0
		end
		if ready and not c.was then c.flashT = os.clock() end
		c.was = ready
		c.fill.Size = UDim2.fromScale(1, k)
		c.fill.BackgroundColor3 = if ready then T.TEXT else T.MUTED
		local fl = math.clamp(1 - (os.clock() - c.flashT) / 0.5, 0, 1)
		c.rim.Color = if fl > 0 then BLACK:Lerp(PINK, fl) else BLACK
		c.rim.Thickness = if fl > 0 then 1 + fl else 1
		c.rim.Transparency = if fl > 0 then 0 else 0.4
	end
end)
