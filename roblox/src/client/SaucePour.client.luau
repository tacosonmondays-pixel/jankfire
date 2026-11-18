--!strict
-- the Hot Sauce poured into the mouth (owner, 18 Nov 2026: "cant eh hotsauce be lkike turned and poured into your
-- moth?"). while someone swigs (the player attribute Swig, set by HoldWeapons.server while the trigger is held) and the
-- bottle has tipped over (Viewmodel's SWIG, ThirdPerson's TP.T.swig), a red stream runs from its cap down into their
-- mouth and a few drops fall off it. yours in first person from the viewmodel's cap; everyone's, and yours in third
-- person, from the third-person bottle. looks only: the swig's numbers are HoldWeapons'. a TPRig test body (ThirdPerson's
-- stand-in for a second player) pours when its own Swig attribute is true, so a solo Play can photograph a face.
-- and the Hot Sauce's bar (owner, 18 Nov: "can oyu also add a bar for the hothacue"): one bar in the weapon plate where
-- the katana's edge meter sits, first person only, while the Hot Sauce is out. no text. it fills with your swig over
-- its 3 s (the breath of fire you'll get), goes red and blinks past 3 s (let go now and it burns you), and drains as you
-- breathe the fire out
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Weapons = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Weapons"))
local VM = require(script.Parent:WaitForChild("Viewmodel")) :: any
local TP = require(script.Parent:WaitForChild("ThirdPerson")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Hold = require(script.Parent:WaitForChild("HoldClient")) :: any

local S = Weapons.S
local P = {
	start = 0.45, fadeIn = 0.15, fadeOut = 0.08, -- s into the swig before it pours (the bottle turns first); its fades
	color = Color3.fromRGB(176, 32, 16), -- hot sauce
	wFP = 0.014 * S, wTP = 0.03 * S, -- the stream's width at the cap (first person, third person); 70 % at the mouth
	mouthFP = Vector3.new(0, -0.115, -0.07) * S, -- your mouth from the camera (below the screen's bottom edge)
	mouthTP = Vector3.new(0, -0.27, -0.5), -- a mouth from its head's middle, in head heights
	drops = 16, -- drops a second off the cap
}
local TEX_STREAM = "rbxassetid://72229869149513" -- (Fx's TEX.tracer: a soft-edged core, v across it)
local TEX_DROP = "rbxassetid://96136840417410" -- (Fx's TEX.blob)

local me = Players.LocalPlayer
type Pour = { a0: Attachment, a1: Attachment, beam: Beam, drops: ParticleEmitter, t0: number, k: number }
local pours: { [Instance]: Pour } = {} -- (by player, or by TPRig body)

local function make(): Pour
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Name, a1.Name = "SauceCap", "SauceMouth"
	a0.Parent, a1.Parent = workspace.Terrain, workspace.Terrain
	local b = Instance.new("Beam")
	b.Attachment0, b.Attachment1 = a0, a1
	b.Texture, b.TextureMode, b.TextureSpeed = TEX_STREAM, Enum.TextureMode.Stretch, 0
	b.Color = ColorSequence.new(P.color)
	b.LightEmission, b.LightInfluence, b.Brightness = 0.15, 0.6, 1
	b.FaceCamera, b.Segments = true, 1
	b.Transparency = NumberSequence.new(1)
	b.Parent = a0
	local e = Instance.new("ParticleEmitter")
	e.Texture = TEX_DROP
	e.Color = ColorSequence.new(P.color)
	e.Size = NumberSequence.new(0.008 * S) -- (Size is half the width: a 1.6 cm drop)
	e.Transparency = NumberSequence.new(0.1)
	e.Lifetime = NumberRange.new(0.3, 0.45)
	e.Speed = NumberRange.new(0.3, 1.2)
	e.SpreadAngle = Vector2.new(35, 35)
	e.Acceleration = Vector3.new(0, -9.8 * S, 0)
	e.LightEmission, e.LightInfluence = 0.1, 0.6
	e.EmissionDirection = Enum.NormalId.Front -- (off the cap toward the mouth, then they fall)
	e.Rate = 0
	e.Parent = a0
	return { a0 = a0, a1 = a1, beam = b, drops = e, t0 = os.clock(), k = 0 }
end
local function drop(p: Instance)
	local o = pours[p]
	if not o then return end
	pours[p] = nil
	o.drops.Rate = 0
	o.beam.Enabled = false
	local a0, a1 = o.a0, o.a1
	task.delay(0.6, function() a0:Destroy(); a1:Destroy() end) -- (the last drops fall)
end
Players.PlayerRemoving:Connect(drop)

-- your own view is first person unless the shoulder camera is on (Arsenal's thirdPerson(): scoped in counts as first)
local function firstPerson(): boolean
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local cam = workspace.CurrentCamera
	if me:GetAttribute("ThirdPerson") == true and me:GetAttribute("TPScope") ~= true then return false end
	return not (root and cam and (cam.CFrame.Position - root.Position).Magnitude > 4.5)
end

-- the cap and the mouth this frame, and the stream's width; nil when there's no bottle to pour from
local function ends(p: Instance, ch: Model?): (Vector3?, Vector3?, number)
	local head = ch and ch:FindFirstChild("Head") :: BasePart?
	if not ch or not head then return nil, nil, 0 end
	if p == me and firstPerson() then
		local cam = workspace.CurrentCamera
		local cap = VM.attachment("Muzzle") :: Vector3?
		if not cap or not cam then return nil, nil, 0 end
		return cap, cam.CFrame * P.mouthFP, P.wFP
	end
	local ok, cap = pcall(TP.muzzle, ch)
	if not ok or typeof(cap) ~= "Vector3" then return nil, nil, 0 end
	return cap, head.CFrame * (P.mouthTP * head.Size.Y), P.wTP
end

local function step(dt: number, p: Instance, ch: Model?)
	local on = p:GetAttribute("Swig") == true and p.Parent ~= nil
	local o = pours[p]
	if on and not o then o = make(); pours[p] = o end
	if not o then return end
	local O = o :: Pour
	local cap, mouth, w = ends(p, ch)
	local want = if on and cap and os.clock() - O.t0 >= P.start then 1 else 0
	O.k = math.clamp(O.k + (if want > O.k then dt / P.fadeIn else -dt / P.fadeOut), 0, 1)
	if not on and O.k <= 0 then drop(p); return end
	if cap and mouth then
		O.a0.WorldCFrame = CFrame.lookAt(cap, mouth)
		-- (the stream falls: drawn from the cap to the mouth, its far end eased in as it pours)
		O.a1.WorldPosition = cap:Lerp(mouth, O.k)
		O.beam.Width0, O.beam.Width1 = w, w * 0.7
		O.beam.Transparency = NumberSequence.new(1 - 0.92 * O.k)
		O.beam.Enabled = O.k > 0.01
		O.drops.Rate = if want == 1 then P.drops else 0
	else
		O.beam.Enabled = false
		O.drops.Rate = 0
	end
end
-- ------------------------------------------------------------------ the bar
local SAUCE = Color3.fromRGB(255, 122, 26) -- (the Hot Sauce's colour, Weapons.list.cig)
local FIRE = Color3.fromRGB(255, 196, 120) -- (the breath going out: its flame's bright core)
local bar: { f: Frame, fill: Frame, edge: UIStroke }? = nil
local shown = 0
local function buildBar()
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local g = pg and pg:FindFirstChild("JankfireFight")
	local sc = g and g:FindFirstChild("Scaled")
	local plate = sc and sc:FindFirstChild("Ammo")
	if not plate then return nil end
	local old = plate:FindFirstChild("Sauce")
	if old then old:Destroy() end
	-- (as wide as the katana's five bars, in the same place: the plate's right, where a gun's count goes)
	local f = T.new("Frame", {
		Name = "Sauce", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, BackgroundTransparency = 0.15, ClipsDescendants = true,
		AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -16, 0, 25), Size = UDim2.fromOffset(77, 5), Visible = false,
	}, plate)
	T.corner(f, 2)
	local fill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = SAUCE, Size = UDim2.fromScale(0, 1) }, f)
	T.corner(fill, 2)
	local edge = T.new("UIStroke", { Color = T.DANGER, Thickness = 1, Transparency = 1 }, f)
	return { f = f, fill = fill, edge = edge }
end
local function drawBar(dt: number)
	if not bar or not bar.f.Parent then bar = buildBar() end
	local b = bar
	if not b then return end
	local on = VM.wid == "cig" and (me:GetAttribute("Zone") ~= "hub" or me:GetAttribute("DevArms") == true) and me.Character ~= nil and firstPerson()
	if b.f.Visible ~= on then b.f.Visible = on end
	if not on then shown = 0; return end
	local now = os.clock()
	local ok, wid, k = pcall(Hold.charging)
	local swig = if ok and wid == "cig" then math.clamp(tonumber(k) or 0, 0, 1) else nil
	local okE, ex = pcall(Hold.exhale)
	local out = if okE then math.clamp(tonumber(ex) or 0, 0, 1) else 0
	local want = swig or out
	shown += (want - shown) * math.min(1, dt * 20)
	if math.abs(want - shown) < 0.002 then shown = want end
	b.fill.Size = UDim2.fromScale(shown, 1)
	local over = swig ~= nil and swig >= 1 -- (past the 3 s: let go now and it burns you)
	local blink = over and math.floor(now * 8) % 2 == 0
	b.fill.BackgroundColor3 = if over then T.DANGER elseif swig == nil and out > 0 then FIRE else SAUCE
	b.fill.BackgroundTransparency = if blink then 0.5 else 0
	b.edge.Transparency = if over then 0.2 else 1
end

RunService.RenderStepped:Connect(function(dt: number)
	drawBar(dt)
	for _, p in Players:GetPlayers() do step(dt, p, p.Character) end
	for _, m in CollectionService:GetTagged("TPRig") do if m:IsA("Model") then step(dt, m, m) end end
	for k in pours do if not k.Parent then drop(k) end end -- (a body gone mid-pour)
end)
