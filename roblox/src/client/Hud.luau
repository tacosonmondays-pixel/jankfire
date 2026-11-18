--!strict
-- the HUD's quiet half: the speed readout, the announcer line (and which callouts it shows: KINDS), the small line under
-- the crosshair and the controls line (Theme.luau has the look: dark
-- plates, white text, one amber accent). FightHud.luau draws everything about the fight
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local Keys = require(script.Parent:WaitForChild("Keys")) -- (on a phone a callout names the button, not the key: Keys.say)

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

-- (16 Nov, owner: "can we hide this?") the controls line is hidden. it shows in a new player's first minute (no XP yet:
-- Stats.luau), while H is held, or all the time with the settings switch SHOW KEY HINTS (JankSettings sets the
-- player's ShowKeys attribute). never on a phone: it lists keys, and a phone has its touch buttons
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local KEYS_NEW = 60
local joined = os.clock()
local keysUntil = 0
local holdH = false
local keysOn = false
hint.Visible = false; hint.TextTransparency = 1; hint.BackgroundTransparency = 1
local function keysShow(on: boolean)
	if on == keysOn then return end
	keysOn = on
	if on then hint.Visible = true end
	local x = T.tween(hint, if on then 0.2 else 0.5, { TextTransparency = if on then 0 else 1, BackgroundTransparency = if on then 0.4 else 1 })
	if not on then
		x.Completed:Connect(function(st) if st == Enum.PlaybackState.Completed and not keysOn then hint.Visible = false end end)
	end
end
task.spawn(function()
	local lp = Players.LocalPlayer
	while lp:GetAttribute("StatsSave") == nil or lp:GetAttribute("StatsSave") == "loading" do -- (up to 15 s for the stats)
		if os.clock() - joined > 15 then break end
		task.wait(0.5)
	end
	local xp = lp:GetAttribute("Xp")
	if xp == nil or xp == 0 then keysUntil = joined + KEYS_NEW end
end)
local Binds = require(script.Parent:WaitForChild("Binds")) :: any -- (H, or whatever the player bound: Settings > KEYBINDS)
UIS.InputBegan:Connect(function(io, gp) if not gp and Binds.is("keys", io) then holdH = true end end)
UIS.InputEnded:Connect(function(io) if Binds.is("keys", io) then holdH = false end end)
RunService.RenderStepped:Connect(function()
	local touchOnly = UIS.TouchEnabled and not UIS.KeyboardEnabled
	keysShow(not touchOnly and (holdH or Players.LocalPlayer:GetAttribute("ShowKeys") == true or os.clock() < keysUntil))
end)

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
-- (colour-blind modes, Settings > HUD: the team's colour after the player's palette)
local TEAM_I = { PINK = 1, CYAN = 2, YELLOW = 3 }
local function teamHex(w: string): string
	local ok, S = pcall(require, script.Parent:WaitForChild("Settings"))
	return if ok and type(S) == "table" then (S :: any).teamHex(TEAM_I[w]) else TEAM[w]
end
local function dress(s: string): string
	s = caps(s)
	s = (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
	local teams = 0
	s = (string.gsub(s, "%u+", function(w: string): string
		if TEAM[w] then teams += 1; return ('<font color="%s">%s</font>'):format(teamHex(w), w) end
		return w
	end))
	if teams == 0 then s = (string.gsub(s, "(%S*%d%S*)", ('<font color="%s">%%1</font>'):format(T.hex(T.ACCENT)), 1)) end
	return s
end

-- the small line: under the crosshair, white on no band, gone in a moment (what you just did)
local note = T.text(hud, "Note", "", 16, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
note.AnchorPoint = Vector2.new(0.5, 0); note.Position = UDim2.new(0.5, 0, 0.5, 34); note.Size = UDim2.fromOffset(420, 20)
note.TextTransparency = 1
local noteTok = 0
function Hud.note(text: string, dur: number)
	noteTok += 1
	local my = noteTok
	note.Text = caps(Keys.say(text))
	note.TextTransparency = 0; note.TextStrokeTransparency = 0.6
	task.delay(math.max(dur, 0.6), function()
		if my ~= noteTok then return end
		T.tween(note, 0.25, { TextTransparency = 1, TextStrokeTransparency = 1 })
	end)
end

-- (16 Nov, owner: "can we get rid of unnecessary text like when slide jumping or grappling? maybe in like the tutorial
-- or training grounds that could make sense. I dont want unnecessary flavor text everywhere") every callout comes
-- through here (the scripts' own Hud.callout and the server's Callout remote), and this table says how each is shown:
--   big    the announcer line: match news, real warnings, what an item did to you. ANY LINE NOT LISTED IS BIG
--   small  the quiet line under the crosshair: what you just did (a kill, a parry, a recharge)
--   train  a move's name: only in the training ground (as a small line, to learn the moves), nowhere else
--   cut    never: jokes, and what you can already see (the weapon plate, the death line and the zone line say it)
-- a line matches by how it starts (the scripts add names and numbers after); "*words" matches words anywhere. the
-- first match wins, so a big line is listed before a small one that starts the same way
local KINDS: { { string } } = {
	{ "SLIDE JUMP", "train" }, { "GRAPPLE JUMP", "train" }, { "BHOP x", "train" }, { "LEDGE LAUNCH", "train" },
	{ "BUBBLED BY", "big" },
	{ "TOO FAR", "small" }, { "killed ", "small" }, { "PERFECT PARRY", "small" }, { "PARRY!", "small" }, { "PARRIED", "small" }, { "CRIT RETURN", "small" },
	{ "BLOCKED", "small" }, { "CHAIN x", "small" }, { "* LINKED", "small" }, { "QUICK SCOPE", "small" }, { "you are in a bubble", "small" },
	{ "*: recharging", "small" }, { "REVERSED", "small" }, { "ROPE SNAPPED", "small" }, { "POP QUIZ FOR ", "small" },
	{ "TICKET", "small" }, { "BUSTED!", "small" }, { "PHOTO TAKEN", "small" }, { "* WENT IN YOUR PHOTO", "small" },
	{ "BUBBLED ", "small" }, { "POPPED ", "small" }, { "QUACK! STUCK", "small" }, { "NO SIGNAL", "small" },
	{ "ADS SERVED", "small" }, { "NO PHOTO", "small" }, { "PINNED", "small" }, -- (PINNED: your Nail Gun pinned them, weapons batch A)
	-- (the classic modes, Modes.luau: a bullet earned and somebody else going out are what just happened, quietly)
	{ "+1 BULLET", "small" }, { "* IS OUT OF LIVES", "small" }, { "KILL CONFIRMED", "small" }, { "KILL DENIED", "small" },
	{ "BOING", "cut" }, { "BONK", "cut" }, { "MARBLES!", "cut" }, { "WHOOPS!", "cut" }, { "dummy down", "cut" },
	{ "KATANA GROWS", "cut" }, { "BURST!", "cut" }, { "NO SCOPE", "cut" }, { "IN THE TEETH", "cut" }, { "SHREDDED", "cut" },
	{ "OVERHEATED", "cut" }, { "POP!", "cut" }, { "WISH YOU WERE HERE", "cut" },
	-- (the doors: the zone line already flashes the place's name as you come in)
	{ "TRAINING GROUND", "cut" }, { "BACK TO THE HUB", "cut" }, { "YOU FOUND THE PLAYGROUND", "cut" }, { "BACK TO TRAINING", "cut" },
	{ "BACK INSIDE", "cut" }, { "YOU OPENED THE GARAGE", "cut" }, { "THE GARAGE REMEMBERS YOU", "cut" },
}
local function kindOf(text: string): string
	for _, k in KINDS do
		local pat = k[1]
		if string.sub(pat, 1, 1) == "*" then
			if string.find(text, string.sub(pat, 2), 1, true) then return k[2] end
		elseif string.sub(text, 1, #pat) == pat then
			return k[2]
		end
	end
	return "big"
end

local token = 0
function Hud.callout(text: string, dur: number)
	local kind = kindOf(text)
	if kind == "cut" then return end
	if kind == "train" then
		if Players.LocalPlayer:GetAttribute("Zone") ~= "training" then return end
		kind = "small"
	end
	if kind == "small" then Hud.note(text, dur); return end
	token += 1
	local my = token
	call.Text = dress(Keys.say(text))
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
