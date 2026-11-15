--!strict
-- the HUD's quiet half: the speed readout, the announcer line and the controls line (Theme.luau has the look: dark
-- plates, white text, one amber accent). FightHud.luau draws everything about the fight
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))

local Hud = {}
local gui = Instance.new("ScreenGui")
gui.Name = "JankfireHud"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

-- everything here grows with the screen (Theme.scaled)
local hud = T.scaled(gui)

-- speed: a small plate beside the health plate (FightHud's: 24 px in from the left, 212 wide, the same height)
local speed = T.plate(hud, "Speed", UDim2.new(0, 244, 1, -88), UDim2.fromOffset(84, 64))
local speedNum = T.text(speed, "Value", "0", 24, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
speedNum.Position = UDim2.fromOffset(0, 11); speedNum.Size = UDim2.new(1, 0, 0, 26)
local speedSub = T.text(speed, "Unit", "m/s", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
speedSub.Position = UDim2.fromOffset(0, 40); speedSub.Size = UDim2.new(1, 0, 0, 14); speedSub.RichText = true

-- the announcer line: wide white capitals over a short amber rule, upper middle of the screen. behind it a soft dark
-- band that fades out to both sides, so the words read over a bright sign or the sky
local callBand = T.new("Frame", {
	Name = "CalloutBand", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.27, 4), Size = UDim2.new(0.72, 0, 0, 96),
	BackgroundColor3 = T.BG, BackgroundTransparency = 1, BorderSizePixel = 0,
}, hud)
T.new("UIGradient", {
	Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.28, 0.3), NumberSequenceKeypoint.new(0.72, 0.3), NumberSequenceKeypoint.new(1, 1),
	}),
}, callBand)
local call = T.text(hud, "Callout", "", 48, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
call.RichText = true -- (the key word of a line is coloured: see dress)
call.AnchorPoint = Vector2.new(0.5, 0.5); call.Position = UDim2.fromScale(0.5, 0.27); call.Size = UDim2.new(0.8, 0, 0, 58)
call.TextScaled = true; call.TextTransparency = 1; call.TextStrokeTransparency = 1
T.new("UITextSizeConstraint", { MaxTextSize = 48, MinTextSize = 14 }, call)
local callScale = T.new("UIScale", {}, call)
local callRule = T.new("Frame", {
	Name = "CalloutRule", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.27, 36), Size = UDim2.fromOffset(56, 4),
	BackgroundColor3 = T.ACCENT, BackgroundTransparency = 1, BorderSizePixel = 0,
}, hud)

-- the controls line: a slim plate along the bottom, in the gap between the plates on the left (they end 328 px in) and
-- the ammo plate on the right (256 px in). FightHud writes the full line, your three weapons first. on a narrow
-- screen it shrinks to fit the gap. (FightHud finds it by name, so it sits straight in the gui with its own scale)
local hint = T.new("TextLabel", {
	Name = "Keys", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -24), Size = UDim2.fromOffset(0, 28),
	AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.BG, BackgroundTransparency = 0.4, BorderSizePixel = 0,
	FontFace = T.FONT, TextSize = 13, TextColor3 = T.SOFT, RichText = true,
	Text = "shift run     C slide     hold E grapple     space on rope = fling     V camera",
}, gui)
T.corner(hint, 4)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12) }, hint)
local hintScale = T.new("UIScale", {}, hint)
local function fitHint()
	local cam = workspace.CurrentCamera
	if not cam then return end
	local s = T.scaleNow()
	local natural = hint.AbsoluteSize.X / hintScale.Scale
	-- (it is centred on the screen, under the crosshair: so it can be as wide as twice the room on its tighter side,
	-- the left, where the plates end 328 px in)
	hintScale.Scale = math.clamp((cam.ViewportSize.X - 680 * s) / math.max(natural, 1), 0.55, s)
	hint.Position = UDim2.new(0.5, 0, 1, -24 * s)
end
hint:GetPropertyChangedSignal("AbsoluteSize"):Connect(fitHint)
if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(fitHint) end

-- the words arrive in mixed case ("dummy down", "killed Name", "ROUND 2 · you're PINK"): lower-case words go to
-- capitals so the line is one voice. names, numbers and single letters (x3, 42m) are left as they came
local function caps(s: string): string
	return (string.gsub(s, "[%a']+", function(w: string): string
		return if #w > 1 and w == string.lower(w) then string.upper(w) else w
	end))
end

-- the line as it is drawn: capitals, and its key word in colour. a team's name takes the team's colour (the same three
-- as the pads and the score); with no team in it, the first number (42m, x3, 24) is amber. the words are not changed
local TEAM = { PINK = "#ff4fd8", CYAN = "#37d6ff", YELLOW = "#ffe14d" }
local function dress(s: string): string
	s = caps(s)
	s = (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
	local teams = 0
	s = (string.gsub(s, "%u+", function(w: string): string
		if TEAM[w] then teams += 1; return ('<font color="%s">%s</font>'):format(TEAM[w], w) end
		return w
	end))
	if teams == 0 then s = (string.gsub(s, "(%S*%d%S*)", ('<font color="%s">%%1</font>'):format(T.hex(T.ACCENT)), 1)) end
	return s
end

local token = 0
function Hud.callout(text: string, dur: number)
	token += 1
	local my = token
	call.Text = dress(text)
	call.TextTransparency = 0; call.TextStrokeTransparency = 0.55
	callRule.BackgroundTransparency = 0
	callBand.BackgroundTransparency = 0
	callScale.Scale = 1.1
	T.tween(callScale, 0.12, { Scale = 1 })
	task.delay(dur, function()
		if my ~= token then return end
		T.tween(call, 0.25, { TextTransparency = 1, TextStrokeTransparency = 1 })
		T.tween(callRule, 0.25, { BackgroundTransparency = 1 })
		T.tween(callBand, 0.25, { BackgroundTransparency = 1 })
	end)
end

function Hud.speed(ms: number, sliding: boolean, hooked: boolean)
	speedNum.Text = tostring(math.floor(ms + 0.5))
	speedNum.TextColor3 = if ms > 20 then T.ACCENT else T.TEXT
	local tag = if sliding then "SLIDE" elseif hooked then "ROPE" else nil
	local line = if tag then ('m/s  <font color="%s">%s</font>'):format(T.hex(T.ACCENT), tag) else "m/s"
	if speedSub.Text ~= line then speedSub.Text = line end
end

-- the server's callouts (e.g. "INTO THE SMOG")
local remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local co = remotes:WaitForChild("Callout") :: RemoteEvent
co.OnClientEvent:Connect(function(text: unknown, dur: unknown)
	if typeof(text) == "string" then Hud.callout(text, if typeof(dur) == "number" then dur else 1.2) end
end)

return Hud
