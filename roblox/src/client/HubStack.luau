--!strict
-- the hub's menu stack on the left, top to bottom: PLAY, QUESTS, PARTY, PROFILE, SHOP, LOADOUT (owner, 18 Nov: "M play
-- should be at the top of the menus on the left in the main hub"). each button's own script asks here for its spot, so
-- the order lives in one place. design pixels in the HUD's scaled frame, from the bottom left; the stack ends just over
-- the health plate (FightHud, y -88). a phone (TouchControls: the same stack on the right) and a controller (PadNav: top
-- to bottom by position) follow these positions, so they need nothing of their own
-- 27 Nov 2026, the owner's pick from the ui-mocks sheet: the hub menu is direction A PLATE (UiKit.luau). PLAY is the one
-- ink block with the stencil slit through the word; under it the main four (QUESTS, PARTY, LOADOUT, SHOP) as white words
-- straight on the world, then the two smaller ones (HUBS, PROFILE). each button's script calls HubStack.style once, after
-- it is made: the look lives here, next to the order
local HubStack = {}

HubStack.ORDER = { "Play", "Quests", "Party", "Loadout", "Shop", "Hubs", "Profile" } -- (Hubs: travel between the hubs, HubTravelUI, 20 Nov)
HubStack.HEIGHT = { Play = 84, Hubs = 28, Profile = 28 } :: { [string]: number } -- (the rest 34)
HubStack.WIDTH = { Play = 300 } :: { [string]: number } -- (the rest 200)
HubStack.SMALL = { Hubs = true, Profile = true } :: { [string]: boolean } -- (the second, quieter group)
HubStack.GAP_AFTER = { Play = 14, Shop = 12 } :: { [string]: number } -- (the rest 2)
local X, PLAY_X, BOTTOM, GAP, H = 46, 16, -40, 2, 34

function HubStack.pos(id: string): UDim2
	local y = BOTTOM
	for i = #HubStack.ORDER, 1, -1 do
		local n = HubStack.ORDER[i]
		y -= HubStack.HEIGHT[n] or H
		if n == id then return UDim2.new(0, if n == "Play" then PLAY_X else X, 1, y) end
		local above = HubStack.ORDER[i - 1]
		y -= if above then (HubStack.GAP_AFTER[above] or GAP) else GAP
	end
	return UDim2.new(0, X, 1, y)
end
function HubStack.size(id: string): UDim2
	return UDim2.fromOffset(HubStack.WIDTH[id] or 200, HubStack.HEIGHT[id] or H)
end

-- the look of one button (A). `sized` is what carries the size when the face fills a holder (LoadoutUI's button)
function HubStack.style(face: TextButton, id: string, sized: GuiObject?)
	local T = require(script.Parent:WaitForChild("Theme")) :: any
	local K = require(script.Parent:WaitForChild("UiKit")) :: any
	local box = sized or face
	box.Size = HubStack.size(id)
	box.Position = HubStack.pos(id)
	for _, c in face:GetChildren() do
		if c:IsA("UICorner") or c:IsA("UIStroke") then c:Destroy() end
	end
	if sized then
		for _, c in sized:GetChildren() do
			if c:IsA("UIStroke") then c:Destroy() end
		end
	end
	face.AutoButtonColor = false
	local key = face:FindFirstChild("Key") :: Frame?
	local pad = face:FindFirstChildOfClass("UIPadding")
	-- a key cap in A's look: a small bone square, the letter in ink
	local function cap(k: Frame, s: number)
		k.BackgroundColor3 = K.A.BONE
		k.BackgroundTransparency = 0
		k.Size = UDim2.fromOffset(s, s)
		local st = k:FindFirstChildOfClass("UIStroke")
		if st then st.Enabled = false end
		local cr = k:FindFirstChildOfClass("UICorner")
		if cr then cr.CornerRadius = UDim.new(0, 4) end
		local l = k:FindFirstChild("Letter") :: TextLabel?
		if l then l.TextColor3 = K.A.INK; l.FontFace = T.FONT_HEAVY; l.TextSize = math.floor(s * 0.62) end
	end
	local alt = K.alt()
	if id == "Play" and alt then
		-- (the all-B alternative: a Butter slab, PLAY in Oswald, square)
		face.Text = ""
		face.BackgroundColor3 = K.B.BUTTER; face.BackgroundTransparency = 0
		if pad then pad.PaddingLeft = UDim.new(0, 0) end
		local w = K.text(face, "Word", "PLAY", 60, K.B.INK, K.COND)
		w.Position = UDim2.fromOffset(24, 8); w.Size = UDim2.new(1, -80, 1, -16)
		if key then
			cap(key, 24)
			key.BackgroundColor3 = K.B.INK
			local l = key:FindFirstChild("Letter") :: TextLabel?
			if l then l.TextColor3 = K.B.BUTTER end
			key.AnchorPoint = Vector2.new(1, 0.5); key.Position = UDim2.new(1, -20, 0.5, 0)
		end
		face.MouseEnter:Connect(function() face.BackgroundColor3 = K.B.BUTTER:Lerp(Color3.new(1, 1, 1), 0.2) end)
		face.MouseLeave:Connect(function() face.BackgroundColor3 = K.B.BUTTER end)
		return
	end
	if id == "Play" then
		-- the ink block: PLAY big with the slit, its key in a bone cap at the right
		face.Text = ""
		face.BackgroundColor3 = K.A.INK
		face.BackgroundTransparency = 0.04
		K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, face)
		if pad then pad.PaddingLeft = UDim.new(0, 0) end
		local hb, _, setWord = K.hero(face, "Word", 58, T.FONT_HEAVY, K.A.BONE, false)
		hb.Position = UDim2.fromOffset(22, 13)
		setWord("PLAY")
		if key then
			cap(key, 24)
			key.AnchorPoint = Vector2.new(1, 0.5)
			key.Position = UDim2.new(1, -20, 0.5, 0)
		end
		face.MouseEnter:Connect(function() face.BackgroundColor3 = K.A.INK:Lerp(Color3.new(1, 1, 1), 0.08) end)
		face.MouseLeave:Connect(function() face.BackgroundColor3 = K.A.INK end)
		-- (round 3: a soft dark fade up the left side, behind the whole menu, shown with PLAY)
		-- (its own ScreenGui under the menu's (DisplayOrder 6): in the PLAY button's own gui it dimmed the other buttons)
		local pg = game:GetService("Players").LocalPlayer:FindFirstChildOfClass("PlayerGui")
		local sg = pg and (pg:FindFirstChild("JankHubShade") or K.new("ScreenGui", { Name = "JankHubShade", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 5 }, pg))
		local holder = if sg then (sg:FindFirstChild("Scaled") or T.scaled(sg)) else nil
		if holder and not holder:FindFirstChild("MenuShade") then
			local shade = K.new("Frame", { Name = "MenuShade", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, Size = UDim2.new(0, 460, 1, 0), ZIndex = 0 }, holder)
			K.new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(0.55, 0.75), NumberSequenceKeypoint.new(1, 1) }) }, shade)
			shade.Visible = face.Visible
			face:GetPropertyChangedSignal("Visible"):Connect(function() shade.Visible = face.Visible end)
		end
		return
	end
	-- the rest: white words on the world, a bone line under the one the pointer is on
	local small = HubStack.SMALL[id] == true
	face.BackgroundTransparency = 1
	face.TextColor3 = K.A.WORLD
	face.FontFace = if alt then K.COND else T.FONT_HEAVY
	face.TextSize = if small then (if alt then 16 else 14) else (if alt then 24 else 19)
	face.TextStrokeColor3 = Color3.new(0, 0, 0)
	face.TextStrokeTransparency = 0.78
	face.TextXAlignment = Enum.TextXAlignment.Left
	if pad then pad.PaddingLeft = UDim.new(0, 0) end
	if key then
		local s = if small then 16 else 20
		cap(key, s)
		key.AnchorPoint = Vector2.new(0, 0.5)
		key.Position = UDim2.new(0, -s - 10, 0.5, 0)
	end
	local line = K.new("Frame", { Name = "Hover", BackgroundColor3 = K.A.BONE, BorderSizePixel = 0, Position = UDim2.new(0, 0, 1, -3), Size = UDim2.fromOffset(28, 3), Visible = false }, face)
	face.MouseEnter:Connect(function() line.Visible = true end)
	face.MouseLeave:Connect(function() line.Visible = false end)
	face.SelectionGained:Connect(function() line.Visible = true end)
	face.SelectionLost:Connect(function() line.Visible = false end)
end

return HubStack
