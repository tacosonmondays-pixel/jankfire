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

-- (19 Nov 2026) before GO (RoundLock, Matches: the countdown, the loadout window, between rounds, a map room) a small
-- padlock sits under the crosshair, the pips dimmed: the grapple waits for the round. and QUICKPLAY's auto-lock
-- (HC.AUTO, QuickMatch on you): a LOCK pip right of the crosshair, filling over its cooldown (HookAutoT, the server's)
local lockF = new("Frame", { Name = "Lock", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.5, 40),
	Size = UDim2.fromOffset(12, 14), Visible = false }, gui)
local shackle = new("Frame", { Name = "Shackle", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 0),
	Size = UDim2.fromOffset(8, 9) }, lockF)
T.corner(shackle, 4)
T.edge(shackle, T.MUTED, 0.2, 1.5)
new("Frame", { Name = "Body", BorderSizePixel = 0, BackgroundColor3 = T.MUTED, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, 0),
	Size = UDim2.fromOffset(12, 8) }, lockF)
local autoB = new("Frame", { Name = "AutoLock", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.45,
	ClipsDescendants = true, AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0.5, 30, 0.5, 31), Size = UDim2.fromOffset(10, 10), Visible = false }, gui)
T.corner(autoB, 2)
T.edge(autoB, T.ACCENT, 0.35, 1)
local autoFill = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, AnchorPoint = Vector2.new(0, 1),
	Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 1) }, autoB)
T.corner(autoFill, 2)
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
	if gui.Enabled ~= (show or lockedNow or auto) then gui.Enabled = show or lockedNow or auto end
	if lockF.Visible ~= lockedNow then lockF.Visible = lockedNow end
	row.Visible = show
	for _, p in pips do p.back.BackgroundTransparency = if lockedNow then 0.75 else 0.45 end
	if autoB.Visible ~= (auto == true) then autoB.Visible = auto == true end
	if auto then
		local srv = me:GetAttribute("HookAutoT")
		local untilT = math.max(autoUntil, if type(srv) == "number" then srv else 0)
		if type(srv) == "number" and srv < autoUntil - 1 then autoUntil = srv end -- (the server let it go sooner: a cut)
		local k = math.clamp(1 - (untilT - now()) / autoCd, 0, 1)
		if k >= 1 and autoFill.Size.Y.Scale < 1 then flashT = os.clock() end -- (ready again: a flash)
		autoFill.Size = UDim2.fromScale(1, k)
		autoFill.BackgroundColor3 = if k >= 1 then T.ACCENT else T.MUTED
		local f = math.clamp((os.clock() - flashT) / 0.35, 0, 1)
		local px = math.floor(10 + 8 * (1 - f) + 0.5)
		if autoB.Size.X.Offset ~= px then autoB.Size = UDim2.fromOffset(px, px) end
	end
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
