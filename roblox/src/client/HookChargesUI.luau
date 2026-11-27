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

-- (27 Nov 2026, the owner's pick A PLATE, play-party's go: nothing under the crosshair (the critic read the pips, the
-- padlock and the AUTO square there as unlabelled lights). the same three things as words over your health, bottom
-- left (inside FightHud's "Hp", so a phone's layout moves them with it): [E] HOOK with a pip per charge, AT GO while
-- the round hasn't started, then [X] AUTO with its cooldown filling. the old ScreenGui JankHookCharges stays and is
-- never enabled: RemoteCooldowns and ScytheDash read its .Enabled to move their rows under the crosshair)
local gui = new("ScreenGui", { Name = "JankHookCharges", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false },
	me:WaitForChild("PlayerGui"))
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local BONE, INK, WORLD = Color3.fromRGB(229, 226, 219), Color3.fromRGB(29, 31, 35), Color3.new(1, 1, 1)
local readout = new("Frame", { Name = "HookReadout", BackgroundTransparency = 1, Position = UDim2.new(0, 0, 0, -30), Size = UDim2.fromOffset(340, 22), Visible = false })
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder,
	Padding = UDim.new(0, 6) }, readout)
local function cap(order: number): TextLabel
	local f = new("TextLabel", { Name = "Key", BackgroundColor3 = BONE, BorderSizePixel = 0, Size = UDim2.fromOffset(18, 18), AutomaticSize = Enum.AutomaticSize.X,
		FontFace = T.FONT_HEAVY, TextSize = 11, TextColor3 = INK, Text = "", LayoutOrder = order }, readout)
	new("UICorner", { CornerRadius = UDim.new(0, 4) }, f)
	new("UIPadding", { PaddingLeft = UDim.new(0, 5), PaddingRight = UDim.new(0, 5) }, f)
	return f
end
local function word(text: string, order: number, size: number?): TextLabel
	local l = new("TextLabel", { BackgroundTransparency = 1, FontFace = T.FONT_HEAVY, TextSize = size or 14, TextColor3 = WORLD, Text = text,
		TextStrokeColor3 = Color3.new(0, 0, 0), TextStrokeTransparency = 0.78, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 22),
		LayoutOrder = order }, readout)
	return l
end
local hookCap = cap(1)
local hookWord = word("GRAPPLE", 2)
local row = new("Frame", { Name = "Pips", BackgroundTransparency = 1, Size = UDim2.fromOffset(HC.CHARGES * 9 + (HC.CHARGES - 1) * 4, 9), LayoutOrder = 3 }, readout)
local pips: { { back: Frame, fill: Frame } } = {}
for i = 1, HC.CHARGES do
	local bk = new("Frame", { Name = "Pip" .. i, BorderSizePixel = 0, BackgroundColor3 = Color3.fromRGB(20, 20, 24), BackgroundTransparency = 0.45,
		ClipsDescendants = true, Position = UDim2.fromOffset((i - 1) * 13, 0), Size = UDim2.fromOffset(9, 9) }, row)
	T.corner(bk, 2)
	local f = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = BONE, AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 1) }, bk)
	T.corner(f, 2)
	pips[i] = { back = bk, fill = f }
end
local lockF = word("OFF UNTIL GO", 4, 12)
lockF.TextTransparency = 0.25
local gap = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(8, 1), LayoutOrder = 5 }, readout)
local autoCap = cap(6)
local autoWord = word("AUTO GRAPPLE", 7)
local autoState = word("READY", 9, 12) -- (READY, or the seconds left: words, not a bar)
local autoB = new("Frame", { Name = "AutoLock", BorderSizePixel = 0, BackgroundColor3 = Color3.fromRGB(20, 20, 24), BackgroundTransparency = 0.45,
	Size = UDim2.fromOffset(28, 5), LayoutOrder = 8, Visible = false }, readout)
T.corner(autoB, 2)
local autoFill = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = BONE, Size = UDim2.fromScale(1, 1) }, autoB)
T.corner(autoFill, 2)
-- (it lives in FightHud's health frame, once that's there)
task.spawn(function()
	local fight = me:WaitForChild("PlayerGui"):WaitForChild("JankfireFight", 30)
	local sc = fight and fight:WaitForChild("Scaled", 10)
	local hp = sc and sc:WaitForChild("Hp", 10)
	readout.Parent = hp or gui
end)
-- (19 Nov 2026: the AUTO GRAPPLE on X, HC.LOCK, uses the same pip: shown in any match, filling over LOCK.cd, a flash
-- when it's ready again; pressed too soon, the not-ready sound and the seconds left on the quiet line)
local autoUntil = 0 -- (this screen's guess till HookAutoT comes back)
local autoCd = (HC.LOCK and HC.LOCK.cd) or 15 -- (the cooldown the pip fills over: the last one used)
local flashT = -10
function HookChargesUI.autoUsed(cd: number?)
	autoCd = cd or autoCd
	autoUntil = now() + autoCd
end
-- s till the AUTO GRAPPLE is ready (0 = ready): this screen's guess or the server's HookAutoT, the later
function HookChargesUI.lockWait(): number
	local srv = me:GetAttribute("HookAutoT")
	return math.max(0, math.max(autoUntil, if type(srv) == "number" then srv else 0) - now())
end
function HookChargesUI.lockNotReady()
	Hud.note(("AUTO GRAPPLE · %d S"):format(math.max(1, math.ceil(HookChargesUI.lockWait()))), 0.9)
	pcall(Sfx.play, "hook_empty")
end
GrappleRemote.OnClientEvent:Connect(function(what: string)
	-- (a cut: the server spent no cooldown unless it set HookAutoT; back to its word)
	if what == "cut" then local srv = me:GetAttribute("HookAutoT"); autoUntil = if type(srv) == "number" then srv else 0 end
end)
function HookChargesUI.locked(): boolean return me:GetAttribute("RoundLock") == true end

local lastN = s.n
RunService.RenderStepped:Connect(function()
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local alive = hum ~= nil and hum.Health > 0
	local lockedNow = alive and HookChargesUI.locked() and me:GetAttribute("Zone") ~= "hub"
	local test = RunService:IsStudio() and me:GetAttribute("AutoLockTest") == true
	local auto = alive and ((HC.LOCK and HC.LOCK.on and (me:GetAttribute("Zone") == "match" or test) and not me:GetAttribute("ZmOn"))
		or (HC.AUTO and HC.AUTO.on and me:GetAttribute("QuickMatch") == true))
	local show = HookChargesUI.limited() and alive
	local any = show or lockedNow or auto == true
	if readout.Visible ~= any then readout.Visible = any end
	if not any then lastN = s.n; return end
	-- the hook part: its key, HOOK, the pips while charges count, AT GO before the round
	local hk = Binds.label("grapple")
	if hookCap.Text ~= hk then hookCap.Text = hk end
	local UIS = game:GetService("UserInputService")
	local touch = (UIS.TouchEnabled and not UIS.KeyboardEnabled) or me:GetAttribute("TouchForce") == true
		or game:GetService("StarterPlayer"):GetAttribute("TouchForce") == true
	hookCap.Visible = (show or lockedNow) and not touch; hookWord.Visible = show or lockedNow
	row.Visible = show
	lockF.Visible = lockedNow
	gap.Visible = (show or lockedNow) and auto == true
	autoCap.Visible = auto == true and not touch; autoWord.Visible = auto == true; autoState.Visible = auto == true; autoB.Visible = false
	if auto then
		local ak = Binds.label("reel")
		if autoCap.Text ~= ak then autoCap.Text = ak end
		local srv = me:GetAttribute("HookAutoT")
		local untilT = math.max(autoUntil, if type(srv) == "number" then srv else 0)
		if type(srv) == "number" and srv < autoUntil - 1 then autoUntil = srv end -- (the server let it go sooner: a cut)
		local k = math.clamp(1 - (untilT - now()) / autoCd, 0, 1)
		if k >= 1 and autoFill.Size.X.Scale < 1 then flashT = os.clock() end -- (ready again: a flash)
		autoFill.Size = UDim2.fromScale(k, 1)
		local f = math.clamp((os.clock() - flashT) / 0.35, 0, 1)
		autoWord.TextTransparency = if k >= 1 then 0 else 0.45
		autoState.Text = if k >= 1 then "READY" else ("%d S"):format(math.max(1, math.ceil(untilT - now())))
		autoState.TextTransparency = if k >= 1 then 0 else 0.3
		autoState.TextSize = math.floor(12 + 3 * (1 - f) + 0.5)
	end
	for _, p in pips do p.back.BackgroundTransparency = if lockedNow then 0.75 else 0.45 end
	if not show then lastN = s.n; return end
	local _, frac = HC.nextIn(s, now())
	if s.n > lastN then pcall(Sfx.play, "hook_ready") end
	lastN = s.n
	for i, p in pips do
		local k = if i <= s.n then 1 elseif i == s.n + 1 then frac else 0
		p.fill.Size = UDim2.fromScale(1, k)
		p.fill.BackgroundTransparency = if i <= s.n then 0 else 0.5
	end
end)

return HookChargesUI
