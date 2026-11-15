--!strict
-- your own avatar's hands and forearms in first person (instead of code boxes): the hand and lower-arm meshes cloned
-- off your character into a little Humanoid model with a copy of your Shirt and BodyColors, so your skin tone and the
-- shirt's sleeves show on them like they do on your body. (layered clothing only renders on a full character, so a
-- layered jacket doesn't come along.) used by the weapons' Viewmodel and the Shredder's viewmodel.
-- the wrist stays straight: the hand carries on along its forearm and only turns about it, so a hand never folds back
-- on itself. what changes per hold is where the forearm comes from and which way the palm faces
--
-- THE LOOK is a switch. "kit" (the default since 2026-11-15) dresses your arm shapes in the game's own glove, sleeve
-- and cuff, so the hands look finished whatever the avatar wears: a pale or untextured avatar arm blew out to a plain
-- white shape under the lamps. "avatar" is the first version: your skin tone and your shirt's sleeves.
local Players = game:GetService("Players")

local AvatarArms = {}

-- (the module's "Look" attribute, if it is set, wins over this: a place or a test can switch without editing code)
AvatarArms.LOOK = "kit" -- "kit" | "avatar"
function AvatarArms.look(): string
	local a = script:GetAttribute("Look")
	return if a == "kit" or a == "avatar" then a else AvatarArms.LOOK
end
AvatarArms.KIT = {
	glove = Color3.fromRGB(33, 35, 40), -- charcoal, matte
	sleeve = Color3.fromRGB(46, 49, 56), -- graphite (flat: Fabric's weave read as noise this close to the eye)
	cuff = Color3.fromRGB(24, 25, 29), -- the band at the wrist
	trim = Color3.fromRGB(64, 68, 77), -- a lighter edge on the cuff (kept dark: you look down the arm, so a pale one shows as a plate)
	pad = Color3.fromRGB(44, 47, 54), -- the plate on the back of the hand
}

-- sizes in metres x k (the viewmodel's studs per metre)
AvatarArms.HAND = 0.12 -- the hand across
AvatarArms.FORE_T = 0.12 -- forearm thickness
AvatarArms.FORE_L = 0.75 -- forearm length: it runs back and down off screen, so the hands never float

-- a hold, in the weapon's frame (+X right, +Y up, -Z forward):
--   back = the forearm's way from the wrist to the elbow (the fingers point the other way)
--   palm = the way the palm faces (it faces the grip, so the hand sits on the far side of the spot from it), or
--   across + sign = a handle running across the palm (katana): the palm faces across x back (sign flips it)
type Pose = { back: Vector3, palm: Vector3?, across: Vector3?, sign: number? }
AvatarArms.POSES = {
	gun = {
		Right = { back = Vector3.new(0.25, -0.5, 1), palm = Vector3.new(-1, 0, 0) }, -- round the grip from the right
		Left = { back = Vector3.new(-0.35, -0.55, 0.8), palm = Vector3.new(0, 1, 0) }, -- flat under the barrel
	},
	katana = { -- both up the handle from below, the backs of the hands toward you
		Right = { back = Vector3.new(0.779, -0.245, 0.577), across = Vector3.zAxis, sign = -1 },
		Left = { back = Vector3.new(0.639, -0.243, 0.729), across = Vector3.zAxis, sign = -1 },
	},
} :: { [string]: { [string]: Pose } }

-- fist is relative to `root` (the weapon's root part): its position is the grip spot, its rotation the weapon's frame
-- for the pose. kind picks the pose set (gun if unknown). (arm is from the old version and isn't used)
export type Spot = { side: string, fist: CFrame, arm: CFrame?, kind: string? }

local KEEP = { SurfaceAppearance = true, SpecialMesh = true }
local function limb(src: BasePart): BasePart
	local c = src:Clone()
	for _, d in c:GetChildren() do if not KEEP[d.ClassName] then d:Destroy() end end
	c.Anchored = false; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false
	c.Massless = true; c.Transparency = 0
	return c
end

-- a piece of the kit: the limb's own shape in one flat colour (its skin picture and surface come off)
local function dress(p: BasePart, color: Color3, material: Enum.Material)
	for _, d in p:GetChildren() do if d:IsA("SurfaceAppearance") then d:Destroy() end end
	if p:IsA("MeshPart") then p.TextureID = "" end
	p.Color = color; p.Material = material; p.Reflectance = 0
end

-- builds the arms under `parent`, welded to `root`; false if your character isn't ready (use the code hands then)
function AvatarArms.build(parent: Instance, root: BasePart, spots: { Spot }, k: number): boolean
	local ch = Players.LocalPlayer and Players.LocalPlayer.Character
	if not ch or #spots == 0 or not ch:FindFirstChildOfClass("Humanoid") then return false end
	for _, s in spots do
		if not (ch:FindFirstChild(s.side .. "Hand") and ch:FindFirstChild(s.side .. "LowerArm")) then return false end
	end
	local old = parent:FindFirstChild("AvatarArms")
	if old then old:Destroy() end
	local arms = Instance.new("Model")
	arms.Name = "AvatarArms"
	local kit = AvatarArms.look() == "kit"
	if not kit then
		-- (a Humanoid in the model makes the Shirt and BodyColors show on the limbs, as they do on your body)
		local hum = Instance.new("Humanoid")
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		hum.RigType = Enum.HumanoidRigType.R15
		hum.RequiresNeck = false; hum.BreakJointsOnDeath = false
		pcall(function() (hum :: any).EvaluateStateMachine = false end)
		hum.Parent = arms
		for _, c in ch:GetChildren() do
			if c:IsA("Shirt") or c:IsA("BodyColors") then c:Clone().Parent = arms end
		end
	end
	for _, s in spots do
		local set = AvatarArms.POSES[s.kind or (if parent.Name == "katana" then "katana" else "gun")] or AvatarArms.POSES.gun
		local pz = set[s.side] or set.Right
		local hand = limb(ch:FindFirstChild(s.side .. "Hand") :: BasePart)
		local fore = limb(ch:FindFirstChild(s.side .. "LowerArm") :: BasePart)
		hand.Size *= AvatarArms.HAND * k / math.max(hand.Size.X, hand.Size.Z)
		fore.Size = Vector3.new(AvatarArms.FORE_T * k, AvatarArms.FORE_L * k, AvatarArms.FORE_T * k * fore.Size.Z / fore.Size.X)
		local W = root.CFrame * s.fist
		local Y = W:VectorToWorldSpace(pz.back.Unit) -- a limb mesh's +Y is its elbow end, -Y its fingers
		local P: Vector3
		if pz.across then
			P = W:VectorToWorldSpace(pz.across):Cross(Y) * (pz.sign or 1)
		else
			P = W:VectorToWorldSpace((pz.palm :: Vector3).Unit)
		end
		P = P - Y * P:Dot(Y)
		P = if P.Magnitude > 1e-4 then P.Unit else W.RightVector
		local X = if s.side == "Right" then -P else P -- a right palm faces the mesh's -X, a left one +X
		local Z = X:Cross(Y)
		local thick = hand.Size.X
		-- palm against the grip: the hand sits half a hand off it, the fingers a little past it
		local centre = W.Position - P * thick * 0.5 - Y * hand.Size.Y * 0.1
		hand.CFrame = CFrame.fromMatrix(centre, X, Y, Z)
		local wrist = centre + Y * hand.Size.Y * 0.42
		fore.CFrame = CFrame.fromMatrix(wrist + Y * fore.Size.Y * 0.5, X, Y, Z)
		local set2: { BasePart } = { hand, fore }
		if kit then
			local K = AvatarArms.KIT
			dress(hand, K.glove, Enum.Material.SmoothPlastic)
			dress(fore, K.sleeve, Enum.Material.SmoothPlastic)
			-- the cuff and its light line are thin slices of the forearm's own shape, a little wider: they fit a
			-- blocky arm and a round one alike
			local function band(name: string, wide: number, long: number, at: number, color: Color3)
				local b = limb(ch:FindFirstChild(s.side .. "LowerArm") :: BasePart)
				b.Name = s.side .. name
				b.Size = Vector3.new(fore.Size.X * wide, long * k, fore.Size.Z * wide)
				b.CFrame = CFrame.fromMatrix(wrist + Y * at * k, X, Y, Z)
				dress(b, color, Enum.Material.SmoothPlastic)
				table.insert(set2, b)
			end
			band("Cuff", 1.14, 0.055, 0.03, K.cuff)
			band("Trim", 1.17, 0.009, 0.052, K.trim)
			-- a low plate on the back of the hand (the side away from the palm)
			local pad = Instance.new("Part")
			pad.Name = s.side .. "Pad"
			pad.Size = Vector3.new(thick * 0.22, hand.Size.Y * 0.4, hand.Size.Z * 0.62)
			pad.CFrame = CFrame.fromMatrix(centre - P * thick * 0.5 + Y * hand.Size.Y * 0.05, X, Y, Z)
			pad.Color = K.pad; pad.Material = Enum.Material.SmoothPlastic
			pad.Anchored = false; pad.CanCollide = false; pad.CanQuery = false; pad.CanTouch = false; pad.CastShadow = false; pad.Massless = true
			table.insert(set2, pad)
		end
		for _, p in set2 do
			local w = Instance.new("WeldConstraint"); w.Part0 = root; w.Part1 = p; w.Parent = p
			p.Parent = arms
		end
	end
	arms.Parent = parent
	return true
end

return AvatarArms
