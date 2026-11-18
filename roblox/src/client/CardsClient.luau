--!strict
-- weapons batch E: your Card Deck hand (CardDeck.server deals it and decides everything). the five cards along the
-- bottom of the screen while the deck is out, the picked one raised; right click picks the next, left click plays it,
-- R draws a new 5 (Arsenal calls these). ranks and suits are drawn here as text, never baked into an uploaded image
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local T = require(script.Parent:WaitForChild("Theme"))

local C = { hand = {} :: { string }, sel = 1, left = 0, nextT = 0, shown = false }
local me = Players.LocalPlayer
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(): RemoteEvent?
	local r = Remotes:FindFirstChild("Cards")
	return if r and r:IsA("RemoteEvent") then r else nil
end

local SUIT = {
	h = { "♥", Color3.fromRGB(200, 40, 48) }, s = { "♠", Color3.fromRGB(24, 26, 30) },
	c = { "♣", Color3.fromRGB(24, 26, 30) }, d = { "♦", Color3.fromRGB(200, 40, 48) },
	j = { "★", Color3.fromRGB(150, 110, 220) },
} :: { [string]: { any } }
local RANKS = { "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K" }

-- ---------------------------------------------------------------- the five tiles
local gui = T.new("ScreenGui", { Name = "JankCards", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false }, me:WaitForChild("PlayerGui"))
local row = T.new("Frame", { AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -118), Size = UDim2.fromOffset(5 * 58, 90), BackgroundTransparency = 1 }, gui)
type Tile = { f: Frame, rank: TextLabel, pip: TextLabel, stroke: UIStroke }
local tiles: { Tile } = {}
for i = 1, 5 do
	local f = T.new("Frame", { Size = UDim2.fromOffset(50, 72), Position = UDim2.fromOffset((i - 1) * 58 + 4, 14), BackgroundColor3 = Color3.fromRGB(240, 238, 232) }, row)
	T.corner(f, 6)
	local stroke = T.new("UIStroke", { Color = T.EDGE, Thickness = 1, Transparency = 0.7 }, f)
	local rank = T.new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(5, 3), Size = UDim2.fromOffset(30, 18), FontFace = T.FONT_HEAVY, TextSize = 16, TextXAlignment = Enum.TextXAlignment.Left, Text = "" }, f)
	local pip = T.new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.58), Size = UDim2.fromOffset(40, 40), TextSize = 30, Text = "" }, f)
	tiles[i] = { f = f, rank = rank, pip = pip, stroke = stroke }
end
local function render()
	for i, t in tiles do
		local id = C.hand[i]
		if id then
			local suit, r = string.sub(id, 1, 1), tonumber(string.sub(id, 2)) or 0
			local s = SUIT[suit] or SUIT.j
			t.f.BackgroundTransparency = 0
			t.rank.Text = if suit == "j" then "" else (RANKS[r] or "")
			t.rank.TextColor3 = s[2]
			t.pip.Text = s[1]
			t.pip.TextColor3 = s[2]
		else
			t.f.BackgroundTransparency = 0.85
			t.rank.Text = ""
			t.pip.Text = ""
		end
		local on = id ~= nil and i == C.sel
		t.f.Position = UDim2.fromOffset((i - 1) * 58 + 4, if on then 0 else 14)
		t.stroke.Color = if on then T.ACCENT else T.EDGE
		t.stroke.Thickness = if on then 2 else 1
		t.stroke.Transparency = if on then 0 else 0.7
	end
end
render()

local r0 = remote() or Remotes:WaitForChild("Cards", 10)
if r0 and r0:IsA("RemoteEvent") then
	r0.OnClientEvent:Connect(function(op: any, hand: any, left: any)
		if op ~= "hand" or type(hand) ~= "table" then return end
		local h = {}
		for _, id in hand do if type(id) == "string" then table.insert(h, id) end end
		C.hand = h
		C.left = if type(left) == "number" then left else 0
		if C.sel > #h then C.sel = math.max(1, #h) end
		render()
	end)
end

-- right click: the next card along
function C.select()
	if #C.hand == 0 then return end
	C.sel = C.sel % #C.hand + 1
	render()
end
-- left click: play the picked card (the server checks the cooldown too)
function C.play(eye: Vector3, look: Vector3): boolean
	local t = os.clock()
	if t < C.nextT or #C.hand == 0 then return false end
	C.nextT = t + 0.35
	local r = remote()
	if r then r:FireServer("play", C.sel, eye, look) end
	return true
end
-- R: a new hand (every 2.5 s, the server's gate)
function C.redraw()
	local r = remote()
	if r then r:FireServer("redraw") end
end
-- the deck out or put away: the tiles with it (asks for the hand the first time)
function C.show(on: boolean)
	if on == C.shown then return end
	C.shown = on
	gui.Enabled = on
	if on and #C.hand == 0 then
		local r = remote()
		if r then r:FireServer("hand") end
	end
end
return C
