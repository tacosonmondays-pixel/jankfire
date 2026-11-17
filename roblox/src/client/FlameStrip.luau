--!strict
-- FlameStrip: a row of real-looking fire along the bottom edge of a UI frame (17 Nov 2026, the owner on the RANKED
-- switch: "can the flames be actual flames?"). The fire is a flipbook (vfx_fire_8x8: 64 frames, 128 px cells, drawn from
-- maths by tools/roblox/vfx/fire_sheet.py, looping) shown by a handful of ImageLabels stepping ImageRectOffset at 30
-- frames a second, each label on its own frame so the row never repeats; the cells' sides fade, so neighbours overlap
-- without a seam. Behind them a warm glow: a gradient rising off the bottom edge (UI has no additive blend, so the glow
-- is a layer of its own). ViewportFrames can't draw particles: this is plain UI, so it works anywhere a Frame does.
-- Cheap: count labels (8), one Size write each a frame, ImageRectOffset only when the frame changes, nothing at all
-- while it's out (the root is hidden and step returns at once). The caller drives it from its own loop:
--   local strip = FlameStrip.new(frame, { count = 8, zIndex = 1 })
--   strip:step(dt, level, sweep, H, hide)   -- every frame while the panel shows
--     level: how hot it sits (0 = out .. 1 = a low flicker along the bottom)
--     sweep: the climb (0 -> 1 -> 0 over a sweep: the flames run up to H and settle back)
--     H: the frame's height in the units its children use; hide: true to hide it (Party Ranked shows bubbles)
--   strip:destroy()
-- photos (Studio only): the workspace attribute FlameStripHold = a number holds every strip's sweep there (0..1, 1 = the
-- peak) at full heat, so a real panel can be photographed mid-sweep (its layer lifted over the cards, as in a real
-- sweep); remove it to let them run
local RunService = game:GetService("RunService")
local STUDIO = RunService:IsStudio()
local FlameStrip = {}
FlameStrip.__index = FlameStrip

FlameStrip.SHEET = "rbxassetid://79816315934163"
local GRID, CELL, FRAMES, FPS = 8, 128, 64, 30
local HOT = Color3.fromRGB(255, 150, 40)
local DEEP = Color3.fromRGB(196, 46, 12)

export type Strip = typeof(setmetatable({} :: {
	root: Frame, glow: Frame, flames: { { im: ImageLabel, off: number, seed: number, w: number } }, t: number, frame: number,
}, FlameStrip))

function FlameStrip.new(parent: GuiObject, opts: { count: number?, zIndex: number?, overlap: number? }?): Strip
	local o = opts or {}
	local count = o.count or 8
	local z = o.zIndex or 1
	local overlap = o.overlap or 0.4
	local root = Instance.new("Frame")
	root.Name = "FlameStrip"; root.BackgroundTransparency = 1; root.Size = UDim2.fromScale(1, 1); root.ZIndex = z
	root.Visible = false
	local glow = Instance.new("Frame")
	glow.Name = "Glow"; glow.BorderSizePixel = 0; glow.BackgroundColor3 = HOT; glow.AnchorPoint = Vector2.new(0.5, 1)
	glow.Position = UDim2.fromScale(0.5, 1); glow.Size = UDim2.new(1, 0, 0, 0); glow.ZIndex = z
	local g = Instance.new("UIGradient")
	g.Rotation = 270
	g.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, HOT), ColorSequenceKeypoint.new(0.5, DEEP), ColorSequenceKeypoint.new(1, DEEP) })
	g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(0.5, 0.8), NumberSequenceKeypoint.new(1, 1) })
	g.Parent = glow
	glow.Parent = root
	local flames = {}
	for i = 1, count do
		local im = Instance.new("ImageLabel")
		im.Name = "Flame"; im.BackgroundTransparency = 1; im.Image = FlameStrip.SHEET
		im.ImageRectSize = Vector2.new(CELL, CELL); im.ScaleType = Enum.ScaleType.Stretch
		im.AnchorPoint = Vector2.new(0.5, 1); im.Position = UDim2.new((i - 0.5) / count, 0, 1, 0)
		im.Size = UDim2.new((1 + overlap) / count, 0, 0, 0); im.ZIndex = z + 1
		im.Parent = root
		-- (each on its own frame, 11 apart; widths a little uneven)
		table.insert(flames, { im = im, off = (i * 11) % FRAMES, seed = math.random() * 100, w = (1 + overlap) / count * (0.9 + math.random() * 0.25) })
	end
	root.Parent = parent
	return setmetatable({ root = root, glow = glow, flames = flames, t = 0, frame = -1 }, FlameStrip)
end

function FlameStrip.step(self: Strip, dt: number, level: number, sweep: number, H: number, hide: boolean?)
	if STUDIO then
		local hold = workspace:GetAttribute("FlameStripHold")
		if type(hold) == "number" then
			level, sweep = 1, math.clamp(hold, 0, 1)
			-- (mid-sweep the fire runs over the panel's cards: lift the layer it sits in above its siblings, as the caller
			-- does while a real sweep runs)
			local layer = self.root.Parent
			if sweep > 0.02 and layer and layer:IsA("GuiObject") and layer.Parent then
				local top = 0
				for _, c in layer.Parent:GetChildren() do if c ~= layer and c:IsA("GuiObject") then top = math.max(top, c.ZIndex) end end
				layer.ZIndex = top + 1
			end
		end
	end
	local show = not hide and (level > 0.01 or sweep > 0.01)
	if self.root.Visible ~= show then self.root.Visible = show end
	if not show then return end
	self.t += dt
	local frame = math.floor(self.t * FPS)
	local newFrame = frame ~= self.frame
	self.frame = frame
	local fade = 1 - math.min(1, level * 1.3 + sweep)
	for _, f in self.flames do
		if newFrame then
			local k = (frame + f.off) % FRAMES
			f.im.ImageRectOffset = Vector2.new((k % GRID) * CELL, (k // GRID) * CELL)
		end
		local n = math.noise(f.seed, self.t * 1.4) * 0.5 + 0.5
		-- settled: a low flicker 56-96 tall, the tongues reaching up past the hot band into the dark panel; the sweep: up to
		-- the frame's height and a bit over (the fire fills the lower ~85 % of its cell). (v586: 34-62 tall over a strong glow
		-- read as one orange band, no flames)
		local h = (56 + 40 * n) * level + sweep * H * (1.0 + 0.3 * n)
		f.im.Size = UDim2.new(f.w, 0, 0, math.floor(h))
		f.im.ImageTransparency = fade
	end
	-- (the glow faint, so the flames stand out against it: at 0.15 it was an orange band as bright as they are)
	self.glow.Size = UDim2.new(1, 0, 0, math.floor((80 * level + sweep * H * 0.9)))
	self.glow.BackgroundTransparency = 0.72 + 0.28 * fade
end

function FlameStrip.destroy(self: Strip)
	self.root:Destroy()
end

return FlameStrip
