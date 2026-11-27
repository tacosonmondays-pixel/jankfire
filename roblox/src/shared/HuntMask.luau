--!strict
-- HOUSE HUNT's gunman mask (27 Nov 2026; roblox/docs/HUNT.md section 11): a plain chunky horror mask of our own (no
-- logos), worn while he has the role, so he reads as the game's villain and hiders can spot him. The server puts it on
-- the real body (HuntRound, at his spawn); the intro puts it on its stand-in body at the snap (HuntIntro).
--   HuntMask.wear(character) -> Model?   fits the kit's hi_mask to the head (scaled to it), welded; nil if no kit/head
--   HuntMask.off(character)              takes it off
-- The kit (tools/roblox/hunt_intro_models.py): ReplicatedStorage[HuntConfig.INTRO.kit].hi_mask, built round a head at
-- HuntIntroData.origin.mask, its face toward -z.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Data = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntIntroData")) :: any

local M = {}
M.NAME = "HuntMask"

function M.off(character: Instance?)
	local old = character and character:FindFirstChild(M.NAME)
	if old then old:Destroy() end
end

function M.wear(character: Model?): Model?
	if not character then return nil end
	local head = character:FindFirstChild("Head") :: BasePart?
	local kit = ReplicatedStorage:FindFirstChild(HC.INTRO.kit)
	local src = kit and kit:FindFirstChild("hi_mask")
	if not head or not src then return nil end
	M.off(character)
	local mask = src:Clone() :: Model
	mask.Name = M.NAME
	local o: Vector3 = Data.origin.mask
	-- its size: the R15 head is 1.2 tall at the default scale; an R6 head's mesh reads about 1.25
	local hum = character:FindFirstChildOfClass("Humanoid")
	local r6 = hum ~= nil and hum.RigType == Enum.HumanoidRigType.R6
	local s = if r6 then 1.05 else math.clamp(head.Size.Y / 1.2, 0.7, 1.6)
	for _, p in mask:GetDescendants() do
		if p:IsA("BasePart") then
			local rel = CFrame.new(-o) * p.CFrame
			if s ~= 1 then
				rel = CFrame.new(rel.Position * s) * rel.Rotation
				p.Size = p.Size * s
			end
			p.CFrame = head.CFrame * rel
			p.Anchored = false; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
			p.CastShadow = true
			local w = Instance.new("WeldConstraint")
			w.Part0 = head; w.Part1 = p; w.Parent = p
		end
	end
	mask.Parent = character
	return mask
end

return M
