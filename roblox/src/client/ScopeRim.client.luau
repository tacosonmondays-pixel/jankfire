--!strict
-- ScopeRim: a high-tier skin's touch on the sniper's scope (18 Nov 2026; the owner on the Seraph set: "when you scope
-- with the seraph a lot of details are lost and the vfx too"). A scoped gun hides itself behind FightHud's scope (black
-- outside a round lens), so its own effects can't show; instead the scope gets the skin's: a soft glow round the lens
-- edge, a few bits drifting in the black outside the lens, a faint shimmer of sparkles along the rim. Nothing inside the
-- lens past its outer tenth: the reticle and the view stay clear. Reusable: a skin's SkinSets.FX row may carry
--   scope = { colour = rim glow, glow = 0..1 strength, bits = { texture = "feather" | "sparkle", colour, n, size = share
--             of the screen's height }, shimmer = { colour, n } }
-- This script only adds its own frames under FightHud's Scope frame (PlayerGui.JankfireFight.Scope) at run time; it
-- does not change FightHud. It reads the held weapon and skin off Viewmodel (VM.wid, VM.skin).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local me = Players.LocalPlayer
local VM = require(script.Parent:WaitForChild("Viewmodel")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")

local TEX = {
	feather = "rbxassetid://92745845385867",
	sparkle = "rbxassetid://118739981349944",
	glow = "rbxassetid://107753175681578",
}
local function rowOf(skin: string?): any
	if type(skin) ~= "string" then return nil end
	local m = Shared:FindFirstChild("SkinSets")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, SS = pcall(require, m)
	local fx = ok and type(SS) == "table" and (SS :: any).FX
	local r = fx and fx[skin]
	return r and r.scope
end

type Rim = { holder: Frame, rings: { { f: Frame, s: UIStroke, k: number, tr: number } }, bits: { any }, sparks: { any }, row: any, skin: string }
local rim: Rim? = nil
local t = 0

local function clear()
	if rim then rim.holder:Destroy(); rim = nil end
end
local function build(scope: Frame, row: any, skin: string): Rim
	local holder = Instance.new("Frame")
	holder.Name = "SkinRim"; holder.BackgroundTransparency = 1; holder.Size = UDim2.fromScale(1, 1); holder.ZIndex = 0
	holder.Parent = scope
	local col = row.colour or Color3.fromRGB(255, 214, 120)
	-- the glow: rings centred on the lens, from a little inside its edge out over the black, fading outward and inward
	local rings = {}
	for i, k in { -0.02, -0.008, 0.004, 0.016, 0.03, 0.046 } do
		local f = Instance.new("Frame")
		f.Name = "Glow" .. i; f.BackgroundTransparency = 1; f.AnchorPoint = Vector2.new(0.5, 0.5); f.Position = UDim2.fromScale(0.5, 0.5)
		f.ZIndex = 0
		local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0.5, 0); c.Parent = f
		local s = Instance.new("UIStroke"); s.Color = col; s.Parent = f
		f.Parent = holder
		local tr = ({ 0.82, 0.62, 0.45, 0.6, 0.78, 0.9 })[i]
		table.insert(rings, { f = f, s = s, k = k, tr = tr })
	end
	-- the bits drifting in the black outside the lens
	local bits = {}
	local b = row.bits
	if b then
		for i = 1, (b.n or 7) do
			local im = Instance.new("ImageLabel")
			im.BackgroundTransparency = 1; im.Image = TEX[b.texture or "feather"] or TEX.feather; im.ImageColor3 = b.colour or Color3.new(1, 1, 1)
			im.AnchorPoint = Vector2.new(0.5, 0.5); im.ZIndex = 0; im.ImageTransparency = 1
			im.Parent = holder
			table.insert(bits, { im = im, seed = i * 1.7 + math.random(), size = b.size or 0.045, life = 3.5 + math.random() * 2, t0 = -math.random() * 4 })
		end
	end
	-- the shimmer: sparkles twinkling on and off along the rim
	local sparks = {}
	local sh = row.shimmer
	if sh then
		for i = 1, (sh.n or 10) do
			local im = Instance.new("ImageLabel")
			im.BackgroundTransparency = 1; im.Image = TEX.sparkle; im.ImageColor3 = sh.colour or Color3.fromRGB(255, 240, 200)
			im.AnchorPoint = Vector2.new(0.5, 0.5); im.ZIndex = 0; im.ImageTransparency = 1
			im.Parent = holder
			table.insert(sparks, { im = im, a = (i - 1) / (sh.n or 10) * 2 * math.pi + math.random() * 0.4, ph = math.random() * 6, rate = 0.6 + math.random() * 0.7 })
		end
	end
	return { holder = holder, rings = rings, bits = bits, sparks = sparks, row = row, skin = skin }
end

RunService.RenderStepped:Connect(function(dt: number)
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local hud = pg and pg:FindFirstChild("JankfireFight")
	local scope = hud and hud:FindFirstChild("Scope") :: Frame?
	local lens = scope and scope:FindFirstChild("Lens") :: Frame?
	local skin = VM.skin
	local row = if scope and scope.Visible then rowOf(skin) else nil
	if not (row and scope and lens) then clear(); return end
	if not rim or rim.skin ~= skin or rim.holder.Parent ~= scope then clear(); rim = build(scope, row, skin :: string) end
	local R = rim :: Rim
	t += dt
	local c = lens.AbsolutePosition + lens.AbsoluteSize / 2 - scope.AbsolutePosition
	local D = lens.AbsoluteSize.Y -- (the lens across, px)
	local H = scope.AbsoluteSize.Y
	local strength = row.glow or 1
	local breathe = 0.85 + 0.15 * math.sin(t * 1.6)
	-- the glow rings: each about 1.4 % of the screen's height thick
	local w = math.max(1, H * 0.014)
	for _, g in R.rings do
		local d = D + g.k * 2 * H
		g.f.Size = UDim2.fromOffset(d, d)
		g.s.Thickness = w
		g.s.Transparency = 1 - (1 - g.tr) * strength * breathe
	end
	-- the bits: each drifts down and round the outside of the lens, turning, fading in and out over its life
	for _, b in R.bits do
		local age = t - b.t0
		if age > b.life then b.t0 = t; b.seed += 3.1; age = 0; b.life = 3.5 + math.random() * 2 end
		local u = age / b.life
		-- (beside the lens, where the black is: half on each side, spread over 100 degrees of the rim, drifting round)
		local side = if math.floor(b.seed * 10) % 2 == 0 then 0 else math.pi
		local a = side + math.sin(b.seed * 7.1) * 0.9 + u * 0.35 * (if side == 0 then 1 else -1)
		local r = D / 2 + H * (0.035 + 0.08 * ((math.sin(b.seed * 5.3) + 1) / 2))
		local p = c + Vector2.new(math.cos(a), math.sin(a)) * r + Vector2.new(math.sin(t * 1.3 + b.seed) * H * 0.01, u * H * 0.06)
		local sz = H * b.size
		b.im.Position = UDim2.fromOffset(p.X, p.Y); b.im.Size = UDim2.fromOffset(sz, sz)
		b.im.Rotation = (b.seed * 90 + age * 40) % 360
		b.im.ImageTransparency = 1 - math.clamp(math.min(u / 0.2, (1 - u) / 0.3), 0, 1) * 0.85
	end
	-- the shimmer: on the rim itself, a twinkle now and then
	for _, s in R.sparks do
		local tw = math.max(0, math.sin(t * s.rate * 2 + s.ph)) ^ 6
		local r = D / 2 + H * 0.006
		local p = c + Vector2.new(math.cos(s.a), math.sin(s.a)) * r
		local sz = H * (0.02 + 0.025 * tw)
		s.im.Position = UDim2.fromOffset(p.X, p.Y); s.im.Size = UDim2.fromOffset(sz, sz)
		s.im.Rotation = t * 30 % 360
		s.im.ImageTransparency = 1 - tw * 0.95
	end
end)
