--!strict
-- your own avatar's hands and forearms in first person (instead of code boxes): the hand and lower-arm meshes cloned
-- off your character into a little Humanoid model with a copy of your Shirt and BodyColors, so your skin tone and the
-- shirt's sleeves show on them like they do on your body. (layered clothing only renders on a full character, so a
-- layered jacket doesn't come along.) used by the weapons' Viewmodel and the Shredder's viewmodel.
-- the wrist stays straight: the hand carries on along its forearm and only turns about it, so a hand never folds back
-- on itself. what changes per hold is where the forearm comes from and which way the palm faces
local Players = game:GetService("Players")

local AvatarArms = {}

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
		for _, p in { hand, fore } do
			local w = Instance.new("WeldConstraint"); w.Part0 = root; w.Part1 = p; w.Parent = p
			p.Parent = arms
		end
	end
	arms.Parent = parent
	return true
end

return AvatarArms
