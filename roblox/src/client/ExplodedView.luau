--!strict
-- THE EXPLODED VIEW (19 Nov 2026, the owner: "not destructible, like blueprint-wise, where parts get 'blown up' to see
-- individual pieces"). On a weapon preview (the loadout's, the shop's inspect) a BREAKDOWN button (X on a keyboard, Y on a
-- pad, a tap on a phone) pushes the weapon's parts out along their own ways, one step after another with a little
-- ease and a soft whoosh, while a blueprint fades in behind it: deep blue, a fine grid, thin white leader lines from each
-- part back to its home. Again (ASSEMBLE) and it snaps back together. Which parts, which way, how far, in what order:
-- shared/GunExplode (worked out from the pieces, so every gun and skin has it). No words on the parts.
--   ExplodedView.attach(holder)   holder: the Frame holding the preview's ViewportFrame (the first one in it; the model
--                                 is the first Model in that). One line in the screen that owns the preview; the
--                                 button sits in the holder's bottom right corner. Returns { toggle, set, open }
-- Sounds (recordings): card_dash (the quick airy whoosh) going apart, scythe_form (a metal slide and a lock clack)
-- coming back together.
-- Studio tests: ExplodedView.handles (every attached view), handle.set(true / false), handle.open()
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GunExplode = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("GunExplode")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local okS, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))

local ExplodedView = {}

local STAGGER, DUR = 0.09, 0.42             -- going apart: each step this much after the last, each move this long
local STAGGER_IN, DUR_IN = 0.035, 0.24      -- coming back: quicker, the last out first in
local BLUE, GRID = Color3.fromRGB(13, 36, 78), Color3.fromRGB(120, 170, 235)
local LINE = Color3.fromRGB(235, 244, 255)
local ZOOM = 1.34                           -- the preview camera's field of view while apart, times what it was

local function play(name: string) if okS and type(Sfx) == "table" then pcall((Sfx :: any).play, name) end end
local function ease(x: number): number
	-- (out-back, a small overshoot: the part settles into place)
	x = math.clamp(x, 0, 1)
	local c1 = 1.25
	local c3 = c1 + 1
	return 1 + c3 * (x - 1) ^ 3 + c1 * (x - 1) ^ 2
end

local function shown(o: GuiObject): boolean
	local x: Instance? = o
	while x do
		if x:IsA("GuiObject") and not x.Visible then return false end
		if x:IsA("LayerCollector") then return (x :: any).Enabled ~= false end
		x = x.Parent
	end
	return false
end

-- a screen shrunk small (the loadout on a phone: its preview at 0.42 under the stage's own scale) would leave the
-- button a few pixels: it is scaled back up to at least 0.8 of its size on screen
local function shrink(o: Instance): number
	local s = 1
	local x: Instance? = o.Parent
	while x do
		local u = x:FindFirstChildOfClass("UIScale")
		if u then s *= u.Scale end
		if x:IsA("LayerCollector") then break end
		x = x.Parent
	end
	return s
end

type Handle = { holder: GuiObject, vp: ViewportFrame?, model: Model?, plan: any, open: boolean, t0: number,
	closing: boolean, backdrop: Frame, grid: { Frame }, btn: TextButton, cap: Frame, lines: Folder?,
	props: { [BasePart]: number }, shownAt: number, fovCam: Camera?, fovBase: number,
	toggle: () -> (), set: (boolean) -> (), isOpen: () -> boolean }
ExplodedView.handles = {} :: { Handle }

-- the blueprint: deep blue, a fine grid with every fourth line brighter (in scale, so any size fits)
local function backdrop(holder: GuiObject, z: number): (Frame, { Frame })
	local f = T.new("Frame", { Name = "Blueprint", BackgroundColor3 = BLUE, BackgroundTransparency = 1, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), ZIndex = z, ClipsDescendants = true }, holder)
	local hc = holder:FindFirstChildOfClass("UICorner")
	if hc then T.new("UICorner", { CornerRadius = hc.CornerRadius }, f) end
	local lines = {}
	local nx, ny = 24, 18
	for i = 1, nx - 1 do
		local major = i % 4 == 0
		local l = T.new("Frame", { BackgroundColor3 = GRID, BackgroundTransparency = 1, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.fromScale(i / nx, 0), Size = UDim2.new(0, if major then 2 else 1, 1, 0), ZIndex = z }, f)
		l:SetAttribute("A", if major then 0.6 else 0.84)
		table.insert(lines, l)
	end
	for i = 1, ny - 1 do
		local major = i % 4 == 0
		local l = T.new("Frame", { BackgroundColor3 = GRID, BackgroundTransparency = 1, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.fromScale(0, i / ny), Size = UDim2.new(1, 0, 0, if major then 2 else 1), ZIndex = z }, f)
		l:SetAttribute("A", if major then 0.6 else 0.84)
		table.insert(lines, l)
	end
	-- (a soft dark rim, so the grid sinks into the panel's edge)
	local v = T.new("Frame", { BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z }, f)
	v:SetAttribute("A", 0.55)
	T.new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.18, 1),
		NumberSequenceKeypoint.new(0.82, 1), NumberSequenceKeypoint.new(1, 0) }) }, v)
	table.insert(lines, v)
	return f, lines
end

local function fade(h: Handle, on: boolean)
	T.tween(h.backdrop, 0.35, { BackgroundTransparency = if on then 0 else 1 })
	for _, l in h.grid do
		local a = l:GetAttribute("A")
		T.tween(l, 0.35, { BackgroundTransparency = if on then (if type(a) == "number" then a else 0.8) else 1 })
	end
	-- (the screen's own props in the viewport, the loadout's podium: out of the blueprint while it shows)
	local vp = h.vp
	if vp and on then
		for _, d in vp:GetChildren() do
			if d:IsA("BasePart") and not h.props[d] then h.props[d] = d.Transparency; d.Transparency = 1 end
		end
	elseif not on then
		for p, t in h.props do if p.Parent then p.Transparency = t end end
		table.clear(h.props)
	end
	-- (the parts spread to about 1.7 times the gun's length: the screen's camera widens a third while it is apart, and
	-- goes back to what it was)
	local cam = if vp then vp.CurrentCamera else nil
	if on and cam and h.fovCam ~= cam then
		h.fovCam, h.fovBase = cam, cam.FieldOfView
		T.tween(cam, 0.4, { FieldOfView = math.min(cam.FieldOfView * ZOOM, 70) })
	elseif not on and h.fovCam then
		if h.fovCam.Parent then T.tween(h.fovCam, 0.3, { FieldOfView = h.fovBase }) end
		h.fovCam = nil
	end
end

-- the leader lines: a thin white rod from each part's home to where it is, and a small dot at home
local function makeLines(h: Handle)
	if h.lines then h.lines:Destroy(); h.lines = nil end
	local plan, m = h.plan, h.model
	if not plan or not m then return end
	local f = Instance.new("Folder")
	f.Name = "ExplodeLines"
	local th = plan.size * 0.0055
	for _, g in plan.groups do
		if g.core then continue end
		for _, kind in { "Rod", "Dot" } do
			local p = Instance.new("Part")
			p.Name = g.name .. "_" .. kind
			p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
			p.Material = Enum.Material.Neon; p.Color = LINE; p.Transparency = 1
			p.Shape = if kind == "Rod" then Enum.PartType.Cylinder else Enum.PartType.Ball
			p.Size = if kind == "Rod" then Vector3.new(0.01, th, th) else Vector3.one * th * 2.6
			p:SetAttribute("NoWrap", true); p:SetAttribute("ExplodeLine", true)
			p.Parent = f
		end
	end
	f.Parent = m
	h.lines = f
end

local function drawLines(h: Handle, fOf: (any) -> number)
	local plan, f = h.plan, h.lines
	if not plan or not f then return end
	local ref = if plan.root then plan.root.CFrame else plan.model:GetPivot()
	for _, g in plan.groups do
		if g.core then continue end
		local rod = f:FindFirstChild(g.name .. "_Rod") :: Part?
		local dot = f:FindFirstChild(g.name .. "_Dot") :: Part?
		if not rod or not dot then continue end
		local k = fOf(g)
		local a, b = ref * GunExplode.at(g, 0), ref * GunExplode.at(g, k)
		local len = (b - a).Magnitude
		if len < plan.size * 0.01 then
			rod.Transparency = 1; dot.Transparency = 1
		else
			rod.Size = Vector3.new(len, rod.Size.Y, rod.Size.Z)
			rod.CFrame = CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0)
			rod.Transparency = 0.25
			dot.CFrame = CFrame.new(a); dot.Transparency = 0.15
		end
	end
end

local function label(h: Handle)
	h.btn.Text = if h.open then "ASSEMBLE" else "BREAKDOWN"
end

local active: Handle? = nil

function ExplodedView.attach(holder: GuiObject): Handle
	local vp0 = holder:FindFirstChildWhichIsA("ViewportFrame")
	local z = if vp0 then vp0.ZIndex else (holder.ZIndex + 1)
	local bd, grid = backdrop(holder, z - 1)
	if vp0 then bd.ZIndex = vp0.ZIndex - 1 end
	local btn = T.new("TextButton", { Name = "Breakdown", Text = "BREAKDOWN", FontFace = T.FONT_BOLD, TextSize = 14, TextColor3 = T.TEXT,
		BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.05, AutoButtonColor = true, AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.new(1, -12, 1, -12), Size = UDim2.fromOffset(150, 36), ZIndex = z + 3, Visible = false }, holder)
	T.corner(btn, 6); T.edge(btn)
	-- (40 px for the cap: on a phone T.key hides it and centres the word)
	T.new("UIPadding", { PaddingLeft = UDim.new(0, 40) }, btn)
	local cap = T.key(btn, "X", UDim2.new(0, -33, 0.5, -11))
	T.new("UIScale", { Name = "Counter" }, btn)
	cap:SetAttribute("Pad", "ButtonY") -- (a pad's own button for it: Y)
	for _, d in cap:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex = z + 4 end end
	cap.ZIndex = z + 4
	local h: Handle
	h = {
		holder = holder, vp = vp0, model = nil, plan = nil, open = false, t0 = 0, closing = false, backdrop = bd, grid = grid,
		btn = btn, cap = cap, lines = nil, props = {}, shownAt = 0, fovCam = nil, fovBase = 30,
		toggle = function() h.set(not h.open) end,
		set = function(on: boolean)
			if on == h.open or not h.plan then return end
			h.open = on
			h.closing = not on
			h.t0 = os.clock()
			fade(h, on)
			label(h)
			play(if on then "card_dash" else "scythe_form")
		end,
		isOpen = function() return h.open end,
	}
	btn.MouseButton1Click:Connect(function() h.toggle() end)
	table.insert(ExplodedView.handles, h)
	return h
end

-- X / Y: the view on screen that showed up last
UIS.InputBegan:Connect(function(io: InputObject, _gp: boolean)
	if io.KeyCode ~= Enum.KeyCode.X and io.KeyCode ~= Enum.KeyCode.ButtonY then return end
	if UIS:GetFocusedTextBox() then return end
	local h = active
	if h and h.plan and shown(h.holder) then h.toggle() end
end)

-- every frame: follow each view's model, show its button, move the parts
RunService.RenderStepped:Connect(function()
	local now = os.clock()
	local newest: Handle? = nil
	for _, h in ExplodedView.handles do
		local vis = h.holder.Parent ~= nil and shown(h.holder)
		if not vis then
			if h.shownAt ~= 0 then
				h.shownAt = 0
				-- (the screen went away: back together at once, no sound)
				if h.plan and (h.open or h.closing) then GunExplode.home(h.plan) end
				if h.open or h.closing then h.open = false; h.closing = false; fade(h, false); label(h) end
				if h.lines then h.lines:Destroy(); h.lines = nil end
			end
			h.btn.Visible = false
			continue
		end
		if h.shownAt == 0 then h.shownAt = now end
		if not newest or h.shownAt > newest.shownAt then newest = h end
		-- the viewport and its model now (a screen rebuilds them)
		local vp = h.vp
		if not vp or vp.Parent ~= h.holder then
			vp = h.holder:FindFirstChildWhichIsA("ViewportFrame")
			h.vp = vp
			if vp then h.backdrop.ZIndex = vp.ZIndex - 1 end
			if vp and h.open then h.fovCam = nil; fade(h, true) end
		end
		local m = if vp then vp:FindFirstChildWhichIsA("Model") else nil
		-- (only a built weapon comes apart: its own Root right under it. not a crate, a hat, a card, a shop bundle of guns)
		if m and (m.Name == "Bundle" or not m:FindFirstChild("Root")) then m = nil end
		if m ~= h.model then
			h.model = m
			h.plan = if m then GunExplode.plan(m) else nil
			if h.lines then h.lines:Destroy(); h.lines = nil end
			if h.plan and h.open then makeLines(h); h.t0 = now end -- (a new weapon while apart: it comes apart too)
		end
		h.btn.Visible = h.plan ~= nil
		if h.btn.Visible then
			local u = h.btn:FindFirstChild("Counter") :: UIScale?
			local s = shrink(h.btn)
			local want = if s < 0.8 then math.min(0.8 / s, 3.5) else 1
			if u and math.abs(u.Scale - want) > 0.01 then u.Scale = want end
		end
		local plan = h.plan
		if not plan then continue end
		if h.open then
			if not h.lines then makeLines(h) end
			local t = now - h.t0
			local function f(g: any): number return ease((t - (g.step - 1) * STAGGER) / DUR) end
			GunExplode.pose(plan, f)
			drawLines(h, f)
		elseif h.closing then
			local t = now - h.t0
			local last = plan.steps
			local function f(g: any): number
				local x = math.clamp((t - (last - g.step) * STAGGER_IN) / DUR_IN, 0, 1)
				return 1 - x * x * (3 - 2 * x)
			end
			GunExplode.pose(plan, f)
			drawLines(h, f)
			if t > (last - 1) * STAGGER_IN + DUR_IN + 0.02 then
				GunExplode.home(plan)
				h.closing = false
				if h.lines then h.lines:Destroy(); h.lines = nil end
			end
		end
	end
	active = newest
end)

return ExplodedView
