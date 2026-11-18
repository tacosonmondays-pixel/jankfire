--!strict
-- the one look every screen is built from (the HUD, the end screen, the loadout, the settings): calm dark plates, white
-- and grey text, one amber accent, red only for danger. Builder Sans for text, Builder Extended (its wide cut) for
-- titles and announcer lines. nothing tilts, nothing has an offset shadow, nothing bounces.
-- colour that carries information (team scores, a weapon's chip, wraps, rarities) is the caller's own
local TweenService = game:GetService("TweenService")

local T = {}
T.BG = Color3.fromRGB(16, 18, 22) -- a plate
T.BG_A = 0.26 -- how see-through a plate is over the world (0.3 greyed out over a bright floor, 0.18 sat on the view like a brick)
T.CARD = Color3.fromRGB(28, 31, 38) -- a card sitting on a plate
T.CARD_HI = Color3.fromRGB(42, 46, 56) -- a card under the mouse
T.TRACK = Color3.fromRGB(58, 62, 72) -- an empty bar
T.EDGE = Color3.fromRGB(255, 255, 255) -- hairline edges
T.EDGE_A = 0.86
T.TEXT = Color3.fromRGB(240, 242, 245)
T.MUTED = Color3.fromRGB(156, 162, 172) -- labels
T.SOFT = Color3.fromRGB(200, 204, 211) -- second-rank words that still have to be read at a glance (a weapon in the feed)
T.DIM = Color3.fromRGB(104, 110, 120)
T.ACCENT = Color3.fromRGB(255, 196, 61) -- the one accent: what you should look at
T.DANGER = Color3.fromRGB(235, 77, 75) -- low health, a headshot, a refusal
T.INK = Color3.fromRGB(14, 15, 18) -- text on an accent button
T.RADIUS = 6

local function face(family: string, weight: Enum.FontWeight): Font
	return Font.new("rbxasset://fonts/families/" .. family .. ".json", weight)
end
T.FONT = face("BuilderSans", Enum.FontWeight.Medium)
T.FONT_BOLD = face("BuilderSans", Enum.FontWeight.Bold)
T.FONT_HEAVY = face("BuilderSans", Enum.FontWeight.ExtraBold)
T.FONT_TITLE = face("BuilderExtended", Enum.FontWeight.Bold)
T.FONT_SHOUT = face("BuilderExtended", Enum.FontWeight.ExtraBold) -- the announcer line

function T.new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
function T.corner(o: Instance, r: number?): UICorner
	return T.new("UICorner", { CornerRadius = UDim.new(0, r or T.RADIUS) }, o)
end
-- a hairline round a frame (never round its text)
function T.edge(o: Instance, color: Color3?, alpha: number?, thick: number?): UIStroke
	return T.new("UIStroke", {
		Color = color or T.EDGE, Transparency = alpha or T.EDGE_A, Thickness = thick or 1,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
	}, o)
end
-- a plate: the dark, slightly see-through panel everything sits on
function T.plate(parent: Instance, name: string, pos: UDim2, size: UDim2): Frame
	local f = T.new("Frame", { Name = name, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0, Position = pos, Size = size }, parent)
	T.corner(f)
	T.edge(f)
	return f
end
-- a line of text. over the bare world (no plate under it) pass shadow = true for a soft dark outline
function T.text(parent: Instance, name: string, text: string, size: number, color: Color3?, font: Font?, align: Enum.TextXAlignment?, shadow: boolean?): TextLabel
	return T.new("TextLabel", {
		Name = name, BackgroundTransparency = 1, FontFace = font or T.FONT, TextSize = size, Text = text,
		TextColor3 = color or T.TEXT, TextXAlignment = align or Enum.TextXAlignment.Left,
		TextStrokeColor3 = Color3.new(0, 0, 0), TextStrokeTransparency = if shadow then 0.55 else 1,
	}, parent)
end
function T.tween(o: Instance, t: number, props: { [string]: any }, style: Enum.EasingStyle?, dir: Enum.EasingDirection?): Tween
	local x = TweenService:Create(o, TweenInfo.new(t, style or Enum.EasingStyle.Quad, dir or Enum.EasingDirection.Out), props)
	x:Play()
	return x
end
-- a key cap: the small rounded box a key's letter sits in
function T.key(parent: Instance, letter: string, pos: UDim2): Frame
	local f = T.new("Frame", { Name = "Key", BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, Position = pos, Size = UDim2.fromOffset(22, 22) }, parent)
	T.corner(f, 4)
	T.edge(f, nil, 0.8)
	local l = T.text(f, "Letter", letter, 13, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
	l.Size = UDim2.fromScale(1, 1)
	-- a phone has no keys: no cap there, and a button that kept room for one centres its words instead
	local uis = game:GetService("UserInputService")
	if (uis.TouchEnabled and not uis.KeyboardEnabled) or game:GetService("StarterPlayer"):GetAttribute("TouchForce") == true then
		f.Visible = false
		local pad = parent:FindFirstChildOfClass("UIPadding")
		if parent:IsA("TextButton") and pad and pad.PaddingLeft.Offset >= 40 then
			pad.PaddingLeft = UDim.new(0, 0)
			parent.TextXAlignment = Enum.TextXAlignment.Center
		end
	end
	-- a controller: while one is in your hands the cap shows the pad's button for the same action, in the same cap (Pad)
	local pm = script.Parent:FindFirstChild("Pad")
	if pm then
		local ok, Pad = pcall(require, pm)
		if ok and type(Pad) == "table" and (Pad :: any).chip then pcall((Pad :: any).chip, f, letter) end
	end
	return f
end
function T.hex(c: Color3): string return "#" .. c:ToHex() end

-- how much the HUD grows with the screen: plates are laid out for a 720-pixel-tall screen and scale up from there
-- (1.5x at 1080p, 2x at 1440p and above), so they are as easy to read on a big monitor as on a small window
-- Settings > HUD: HUD SIZE scales every scaled holder below on top of the screen's own scale (SettingsApply sets it
-- and fires rescaled)
T.hudScale = 1
T.rescaled = Instance.new("BindableEvent")
-- (a phone: TouchControls draws the fight HUD's guis smaller there, T.guiK[<ScreenGui name>] = 0.7 or so. nil = 1)
T.guiK = {} :: { [string]: number }
function T.scaleNow(): number
	local cam = workspace.CurrentCamera
	return math.clamp((if cam then cam.ViewportSize.Y else 720) / 720, 1, 2)
end
-- a full-screen holder for plates: its children are placed in those 720-tall "design pixels" and grow with the screen.
-- it is exactly the screen's size, so a child anchored to an edge or the centre lands where it should. the crosshair
-- and anything that must stay pixel-exact goes straight in the ScreenGui, not in here
function T.scaled(gui: Instance): Frame
	local f = T.new("Frame", { Name = "Scaled", BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, gui)
	local sc = T.new("UIScale", {}, f)
	local function fit()
		local s = T.scaleNow() * T.hudScale * (T.guiK[gui.Name] or 1)
		sc.Scale = s
		f.Size = UDim2.fromScale(1 / s, 1 / s)
	end
	fit()
	local cam = workspace.CurrentCamera
	if cam then cam:GetPropertyChangedSignal("ViewportSize"):Connect(fit) end
	T.rescaled.Event:Connect(fit)
	return f
end

return T
