--!strict
-- grapple charges on your screen (shared/HookCharges.luau; the server's count: server/HookChargeServer.luau). while
-- they count (the HookLimit attribute: a RANKED duel or a PARTY RANKED match) two pips sit under the crosshair, each
-- filling as it comes back. Move.client asks HookChargesUI.try() before it fires the hook: it spends a charge on this
-- screen at once (the server's attributes correct it), or says "GRAPPLE RECHARGING · N S" on the quiet line and
-- plays the not-ready sound. a charge coming back plays the reel click. the sounds are recordings from the sound
-- session (hook_empty, hook_ready in JankfireSounds); until they exist Sfx plays nothing
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HookCharges"))
local T = require(script.Parent:WaitForChild("Theme"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))

local me = Players.LocalPlayer
local new = T.new
local HookChargesUI = {}

local s = HC.new()
local function now(): number return workspace:GetServerTimeNow() end
local function sync()
	local n = me:GetAttribute("HookN")
	local t0 = me:GetAttribute("HookT0")
	if type(n) == "number" then s.n = n end
	s.t0 = if type(t0) == "number" and t0 > 0 then t0 else nil
end
me:GetAttributeChangedSignal("HookN"):Connect(sync)
me:GetAttributeChangedSignal("HookT0"):Connect(sync)
sync()
-- (a hook the server cut for its own reasons, out of range or out of sight, spent nothing there: the guess here
-- did. back to the server's count, or the screen says recharging with a charge left)
local GrappleRemote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Grapple") :: RemoteEvent
GrappleRemote.OnClientEvent:Connect(function(what: string) if what == "cut" then sync() end end)

function HookChargesUI.limited(): boolean return me:GetAttribute("HookLimit") == true end

-- (Move.client's tryHook, once it has a point to hook) true = fire it
function HookChargesUI.try(): boolean
	if not HookChargesUI.limited() then return true end
	if HC.spend(s, now()) then return true end
	local left = HC.nextIn(s, now())
	Hud.note(("GRAPPLE RECHARGING · %d S"):format(math.max(1, math.ceil(left or HC.CD))), 0.9)
	pcall(Sfx.play, "hook_empty")
	return false
end

-- the pips: under the crosshair, one per charge, a used one filling from the bottom as it comes back
local gui = new("ScreenGui", { Name = "JankHookCharges", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false },
	me:WaitForChild("PlayerGui"))
local row = new("Frame", { Name = "Pips", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.5, 26),
	Size = UDim2.fromOffset(HC.CHARGES * 10 + (HC.CHARGES - 1) * 6, 10) }, gui)
local pips: { { back: Frame, fill: Frame } } = {}
for i = 1, HC.CHARGES do
	local b = new("Frame", { Name = "Pip" .. i, BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.45,
		ClipsDescendants = true, Position = UDim2.fromOffset((i - 1) * 16, 0), Size = UDim2.fromOffset(10, 10) }, row)
	T.corner(b, 5)
	T.edge(b, T.TEXT, 0.35, 1)
	local f = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 1) }, b)
	T.corner(f, 5)
	pips[i] = { back = b, fill = f }
end

local lastN = s.n
RunService.RenderStepped:Connect(function()
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local show = HookChargesUI.limited() and hum ~= nil and hum.Health > 0
	if gui.Enabled ~= show then gui.Enabled = show end
	if not show then lastN = s.n; return end
	local _, frac = HC.nextIn(s, now())
	if s.n > lastN then pcall(Sfx.play, "hook_ready") end
	lastN = s.n
	for i, p in pips do
		local k = if i <= s.n then 1 elseif i == s.n + 1 then frac else 0
		p.fill.Size = UDim2.fromScale(1, k)
		p.fill.BackgroundColor3 = if i <= s.n then T.TEXT else T.MUTED
	end
end)

return HookChargesUI
