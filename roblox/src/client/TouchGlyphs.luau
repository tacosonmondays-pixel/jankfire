--!strict
-- The phone buttons' glyphs (27 Nov 2026, ui-mocks; main: "one consistent glyph family ... flat, bold, readable at
-- thumb size"). One white family on one sprite sheet, drawn as vector shapes by tools/roblox/touch_glyphs.py (cell
-- order below = its ORDER), uploaded once as an Image. Each glyph is tinted like its button's words, so the A PLATE
-- colours (ink on bone, bone on FIRE's ink) carry over.
--   put(face, key, mode)  mode nil: a round button, the glyph above its word; "pill": the glyph before the word;
--                         "only": the glyph alone, centred. key nil (or one with no glyph): words only, as before
--   tint(face)            the glyph takes the words' colour and see-through (TouchControls' style calls it)
local G = {}

G.SHEET = "rbxassetid://79409184361495" -- (v2, the final push: SLIDE a sliding figure, AUTO FIRE a cartridge in a loop; v1 was 106966348842200)
G.CELL = 128
G.COLS = 5
G.CELLS = {
	fire = 0, aim = 1, jump = 2, crouch = 3, sprint = 4, hook = 5, reload = 6, swap = 7, melee = 8, item = 9,
	camera = 10, emote = 11, wave = 12, yank = 13, reel = 14, reelin = 15, lunge = 16, board = 17, settings = 18, auto = 19,
} :: { [string]: number }

function G.tint(face: GuiObject)
	local g = face:FindFirstChild("Glyph") :: ImageLabel?
	if g and face:IsA("TextButton") then
		g.ImageColor3 = face.TextColor3
		g.ImageTransparency = face.TextTransparency
	end
end

function G.put(face: TextButton, key: string?, mode: string?)
	local i = if key then G.CELLS[key] else nil
	local g = face:FindFirstChild("Glyph") :: ImageLabel?
	local pad = face:FindFirstChild("GlyphPad") :: UIPadding?
	if i == nil then
		if g then g:Destroy() end
		if pad then pad:Destroy() end
		face.TextYAlignment = Enum.TextYAlignment.Center
		face.TextXAlignment = Enum.TextXAlignment.Center
		return
	end
	if not g then
		local n = Instance.new("ImageLabel")
		n.Name = "Glyph"
		n.BackgroundTransparency = 1
		n.Image = G.SHEET
		n.ImageRectSize = Vector2.new(G.CELL, G.CELL)
		n.ScaleType = Enum.ScaleType.Fit
		n.ZIndex = face.ZIndex + 1
		local ar = Instance.new("UIAspectRatioConstraint")
		ar.AspectRatio = 1
		ar.DominantAxis = Enum.DominantAxis.Height
		ar.Parent = n
		n.Parent = face
		g = n
	end
	if not pad then
		local p = Instance.new("UIPadding")
		p.Name = "GlyphPad"
		p.Parent = face
		pad = p
	end
	local gl, pd = g :: ImageLabel, pad :: UIPadding
	local idx = i :: number
	gl.ImageRectOffset = Vector2.new((idx % G.COLS) * G.CELL, (idx // G.COLS) * G.CELL)
	if mode == "pill" then
		-- (the glyph at the left, the word right-aligned after it)
		gl.AnchorPoint = Vector2.new(0, 0.5); gl.Position = UDim2.new(0, 7, 0.5, 0); gl.Size = UDim2.fromScale(0.62, 0.62)
		pd.PaddingRight = UDim.new(0, 9); pd.PaddingBottom = UDim.new(0, 0)
		face.TextXAlignment = Enum.TextXAlignment.Right; face.TextYAlignment = Enum.TextYAlignment.Center
	elseif mode == "only" then
		gl.AnchorPoint = Vector2.new(0.5, 0.5); gl.Position = UDim2.fromScale(0.5, 0.5); gl.Size = UDim2.fromScale(0.68, 0.68)
		face.Text = ""
	else
		-- (a round button: the glyph in the upper middle, its word under it near the rim)
		gl.AnchorPoint = Vector2.new(0.5, 0.5); gl.Position = UDim2.fromScale(0.5, 0.4); gl.Size = UDim2.fromScale(0.42, 0.42)
		pd.PaddingBottom = UDim.new(0.15, 0); pd.PaddingRight = UDim.new(0, 0)
		face.TextXAlignment = Enum.TextXAlignment.Center; face.TextYAlignment = Enum.TextYAlignment.Bottom
	end
	G.tint(face)
end

return G
