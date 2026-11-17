--!strict
-- SMALL LOOPING PREVIEWS of kill effects and emotes on cards (the owner, 17 Nov 2026: "for kill effects in shop can they
-- be small previews? same with in inv?"). the shop's cards, its inventory and its inspect panel use it; anyone may.
--   FlairAnim.attach(frame, kind, id) -> handle | nil: draws over `frame` (a square tile; it keeps the frame's own
--   still picture underneath for when nothing can play)
--     kill:  the effect's flipbook (Shared.FlairSheets, the VFX session's sheets), stepped frame by frame. no sheet yet:
--            nil (the still tile stays)
--     emote: a copy of your own avatar in a ViewportFrame inside a WorldModel (so it animates) doing the emote, looped
--   handle.stop() / FlairAnim.detach(frame) take it away (the frame going away does too)
-- cheap on purpose: one stepper for all; only a preview that's on screen plays (its ScreenGui enabled, every ancestor
-- visible, inside its scrolling frame's view and the screen), at most MAX at once, flipbooks at their own fps; the rest
-- hold their frame (emotes pause)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local me = Players.LocalPlayer

local A = {}
local MAX = 8
local BG = Color3.fromRGB(22, 24, 30) -- (the flair tile's dark)

type Handle = { frame: GuiObject, kind: string, root: GuiObject, step: (number, boolean) -> (), stop: () -> (), dead: boolean }
local live: { Handle } = {}

local function sheets(): any
	local m = Shared:FindFirstChild("FlairSheets")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, S = pcall(require, m)
	return if ok and type(S) == "table" then S else nil
end
local function flair(): any
	local m = Shared:FindFirstChild("Flair")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, F = pcall(require, m)
	return if ok and type(F) == "table" then F else nil
end

local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function round(o: Instance, r: number) new("UICorner", { CornerRadius = UDim.new(0, r) }, o) end

-- is it on screen? its ScreenGui on, every GuiObject above it visible, and its box inside every scrolling frame's view
local function shown(g: GuiObject): boolean
	if not g:IsDescendantOf(game) then return false end
	local a, s = g.AbsolutePosition, g.AbsoluteSize
	if s.X < 2 or s.Y < 2 then return false end
	local x0, y0, x1, y1 = a.X, a.Y, a.X + s.X, a.Y + s.Y
	local p: Instance? = g
	while p do
		if p:IsA("GuiObject") then
			if not p.Visible then return false end
			if p:IsA("ScrollingFrame") or p.ClipsDescendants then
				local pa, ps = p.AbsolutePosition, p.AbsoluteSize
				if x1 < pa.X or y1 < pa.Y or x0 > pa.X + ps.X or y0 > pa.Y + ps.Y then return false end
			end
		elseif p:IsA("LayerCollector") then
			if not (p :: any).Enabled then return false end
			break
		end
		p = p.Parent
	end
	local cam = workspace.CurrentCamera
	if cam then
		local v = cam.ViewportSize
		if x1 < 0 or y1 < -60 or x0 > v.X or y0 > v.Y then return false end
	end
	return true
end

-- ---------------------------------------------------------------- kill effects: the flipbook
local function flipbook(frame: GuiObject, id: string): Handle?
	local S = sheets()
	local sh = S and S.kill and S.kill[id]
	if type(sh) ~= "table" or type(sh.image) ~= "string" then return nil end
	local cols, px = tonumber(sh.cols) or 4, tonumber(sh.px) or 256
	local n = math.max(1, tonumber(sh.n) or 16)
	local fps = tonumber(sh.fps) or 10
	local hold = tonumber(sh.hold) or 0
	local z = frame.ZIndex + 3
	-- (any shape of frame: the backdrop fills it, the frame's picture sits in a square in the middle, and the words are
	-- placed in that square, so they land on the sheet's panel whatever the card's shape)
	local back = new("Frame", { Name = "FlairAnim", BackgroundColor3 = BG, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z }, frame)
	round(back, 6)
	local img = new("ImageLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(1, 1), Image = sh.image, ImageRectSize = Vector2.new(px, px), ImageRectOffset = Vector2.zero,
		ScaleType = Enum.ScaleType.Stretch, ZIndex = z }, back)
	new("UIAspectRatioConstraint", { AspectRatio = 1 }, img)
	local words: TextLabel? = nil
	local w = sh.words
	if type(w) == "table" and type(w.text) == "string" then
		words = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromScale(w.x or 0, w.y or 0), Size = UDim2.fromScale(w.w or 1, w.h or 0.2),
			Text = w.text, TextScaled = true, TextColor3 = w.color or Color3.fromRGB(236, 240, 246), Font = Enum.Font.Code, Visible = false, ZIndex = z + 1 }, img)
	end
	local t = math.random() * (n / fps) -- (cards next to each other don't all play in step)
	local last = -1
	local h: Handle
	h = {
		frame = frame, kind = "kill", root = back, dead = false,
		step = function(dt: number, on: boolean)
			if on then t += dt end
			local f = math.floor(t * fps) % (n + hold)
			if f >= n then f = n - 1 end
			if f == last then return end
			last = f
			img.ImageRectOffset = Vector2.new((f % cols) * px, math.floor(f / cols) * px)
			if words and w then (words :: TextLabel).Visible = f + 1 >= (w.from or 1) and f + 1 <= (w.to or n) end
		end,
		stop = function()
			h.dead = true
			back:Destroy()
		end,
	}
	h.step(0, true)
	return h
end

-- ---------------------------------------------------------------- emotes: you, doing it
local tpl: Model? = nil
local tplFor: Model? = nil
local function avatar(): Model?
	local ch = me.Character
	if not ch then return tpl end
	if tpl and tplFor == ch then return tpl end
	local was = ch.Archivable
	ch.Archivable = true
	local ok, c = pcall(function() return ch:Clone() end)
	ch.Archivable = was
	if not ok or not c then return tpl end
	local m = c :: Model
	for _, d in m:GetDescendants() do
		if d:IsA("LuaSourceContainer") or d:IsA("Sound") or d:IsA("Tool") or d:IsA("ForceField") or d:IsA("BillboardGui")
			or d:IsA("ParticleEmitter") or d:IsA("Trail") or d:IsA("Beam") then
			d:Destroy()
		elseif d:IsA("BasePart") then
			d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		end
	end
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then root.Anchored = true end
	if tpl then tpl:Destroy() end
	tpl, tplFor = m, ch
	return m
end

local function emote(frame: GuiObject, id: string): Handle?
	local F = flair()
	local e = F and F.info("emote", id)
	if not e or type(e.anim) ~= "string" or e.anim == "rbxassetid://0" then return nil end
	local src = avatar()
	if not src then return nil end
	local z = frame.ZIndex + 3
	local holder = new("Frame", { Name = "FlairAnim", BackgroundColor3 = BG, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z, ClipsDescendants = true }, frame)
	round(holder, 6)
	local rc = F.RARITY_COLOR and F.RARITY_COLOR[e.rarity]
	if rc then
		local glow = new("Frame", { BackgroundColor3 = rc, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z }, holder)
		round(glow, 6)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.7, 0.92), NumberSequenceKeypoint.new(1, 0.7) }) }, glow)
	end
	-- (the shop's own 3D light, V.show's: the pastel colours read as they do on the guns and in the inspect panel)
	local vp = new("ViewportFrame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = z + 1,
		Ambient = Color3.fromRGB(150, 153, 162), LightColor = Color3.fromRGB(255, 248, 240), LightDirection = Vector3.new(-0.5, -1, -0.7) }, holder)
	local world = new("WorldModel", {}, vp)
	local m = src:Clone()
	m:PivotTo(CFrame.identity)
	m.Parent = world
	local cam = new("Camera", { FieldOfView = 30 }, vp)
	vp.CurrentCamera = cam
	-- (framed on the body, not its accessories (a big hat or a staff would shrink it): feet just above the bottom edge,
	-- the head with room for raised arms, from the front a little to the side)
	local lo, hi = math.huge, -math.huge
	for _, p in m:GetChildren() do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
			lo = math.min(lo, p.Position.Y - p.Size.Y / 2)
			hi = math.max(hi, p.Position.Y + p.Size.Y / 2)
		end
	end
	local cf, size = m:GetBoundingBox()
	if lo == math.huge then lo, hi = cf.Position.Y - size.Y / 2, cf.Position.Y + size.Y / 2 end
	local r = (hi - lo) * 0.64 -- (half the height the frame shows: a fifth over the head for raised arms)
	local d = r / math.tan(math.rad(cam.FieldOfView / 2))
	local look = Vector3.new(cf.Position.X, lo + r * 0.93, cf.Position.Z)
	local face = (m:GetPivot().LookVector * Vector3.new(1, 0, 1)).Unit
	if face.Magnitude ~= face.Magnitude then face = Vector3.new(0, 0, -1) end
	cam.CFrame = CFrame.lookAt(look + (face * d) + face:Cross(Vector3.yAxis) * (d * 0.2), look)
	local hum = m:FindFirstChildOfClass("Humanoid")
	local an = hum and (hum:FindFirstChildOfClass("Animator") or new("Animator", {}, hum))
	-- (the flair session's way, FlairUI's stand-in: priority Action4, in over 0.3 s; a one-shot is let go 0.35 s before
	-- its end, rests about 0.7 s, and starts again, so it never snaps back at a loop's seam. a looping emote just loops.
	-- the clip, its length and whether it loops are read from Flair now: the ids change when the emotes are remade)
	local track: AnimationTrack? = nil
	local loops = e.loop == true
	local len = math.max(0.8, tonumber(e.len) or 3)
	if an then
		local anim = new("Animation", { AnimationId = e.anim })
		local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
		if ok and tr then
			track = tr
			tr.Looped = loops
			tr.Priority = Enum.AnimationPriority.Action4
		end
	end
	local REST = 0.7
	local t = 0 -- (time in this round of the cycle, only counted while it's on screen)
	local going, playing = false, false
	local h: Handle
	h = {
		frame = frame, kind = "emote", root = holder, dead = false,
		step = function(dt: number, on: boolean)
			local tr = track
			if not tr then return end
			if on ~= playing then
				playing = on
				if going then tr:AdjustSpeed(if on then 1 else 0) end
			end
			if not on then return end
			if not going and t == 0 then tr:Play(0.3); going = true end
			t += dt
			if loops then return end
			if going and t >= len - 0.35 then tr:Stop(0.35); going = false end
			if not going and t >= len + REST then t = 0 end
		end,
		stop = function()
			h.dead = true
			if track then pcall(function() (track :: AnimationTrack):Stop(0) end) end
			holder:Destroy()
		end,
	}
	return h
end

-- ---------------------------------------------------------------- the stepper
function A.attach(frame: GuiObject, kind: string, id: string): any
	local h = if kind == "kill" then flipbook(frame, id) elseif kind == "emote" then emote(frame, id) else nil
	if not h then return nil end
	table.insert(live, h)
	return h
end
function A.detach(frame: GuiObject)
	for _, h in live do if h.frame == frame and not h.dead then h.stop() end end
end
-- (how many play right now: a test reads it)
A.playing = 0

RunService.RenderStepped:Connect(function(dt)
	if #live == 0 then A.playing = 0; return end
	local n = 0
	for i = #live, 1, -1 do
		local h = live[i]
		if h.dead or not h.root:IsDescendantOf(game) then
			if not h.dead then h.dead = true end
			table.remove(live, i)
		else
			local on = n < MAX and shown(h.frame)
			if on then n += 1 end
			h.step(dt, on)
		end
	end
	A.playing = n
end)

return A
