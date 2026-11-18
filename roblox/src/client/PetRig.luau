--!strict
-- one pet's model and its moves (Shared.Flair PETS; doc FLAIR.md, "Pets"). client only: the follower (Pets.client) and
-- the equip screen's preview (FlairUI) both use it.
--   PetRig.new(id, silhouette?) -> rig | nil      a copy of ReplicatedStorage.JankfirePets.<id> (PolishBackup.PetImport
--                                                 builds those from the uploads: a Root part at the pet's middle on the
--                                                 floor, facing -Z, and MeshParts that carry their joint: Role, Joint,
--                                                 Side, Front, N). silhouette: every part flat black, the picker's look
--                                                 for a pet you haven't found
--   rig:pose(cf, phase, move, t)                  every piece placed in one BulkMoveTo: cf = where the pet stands (on the
--                                                 floor, facing its LookVector); phase = the gait's clock (radians, it
--                                                 runs with the ground covered); move = 0 standing .. 1 going; t = time
--   rig:hide(on) / rig:destroy()
-- the gaits (Flair.PETS[id].gait), all cheap sums of sines, nothing on the server:
--   waddle  the mannequin is one stiff piece: it rocks from one foot onto the other like a wind-up toy, twisting a little,
--           leaning into the walk; standing, it sways and looks about
--   crawl   the slug's hands reach forward in turn (each lifts and comes down ahead) while its plate drums bunch and
--           stretch in a wave from the mask back; standing, the mask looks about and the drums breathe
--   trot    the dog's legs swing in diagonal pairs, its body bobs and its head nods; the tail wags all the time (faster
--           on the move); standing, it tilts its head now and then
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Flair = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Flair")) :: any

local PetRig = {}
PetRig.__index = PetRig

type Piece = { part: BasePart, base: CFrame, role: string, joint: Vector3, side: number, front: boolean, n: number }
export type Rig = typeof(setmetatable({} :: {
	id: string, gait: string, model: Model, pieces: { Piece }, parts: { BasePart }, cfs: { CFrame }, hidden: boolean,
	feet: number, byRole: { [string]: { Piece } },
}, PetRig))

local rad, sin, cos, abs, max = math.rad, math.sin, math.cos, math.abs, math.max

function PetRig.template(id: string): Model?
	local kit = ReplicatedStorage:FindFirstChild("JankfirePets")
	local m = kit and kit:FindFirstChild(id)
	return if m and m:IsA("Model") then m else nil
end

function PetRig.new(id: string, silhouette: boolean?): Rig?
	local info = Flair.pet(id)
	local tpl = PetRig.template(id)
	if not info or not tpl then return nil end
	local m = tpl:Clone()
	local root = m:FindFirstChild("Root") :: BasePart?
	if not root then m:Destroy(); return nil end
	local rcf = root.CFrame
	local pieces: { Piece } = {}
	local byRole: { [string]: { Piece } } = {}
	for _, d in m:GetDescendants() do
		if d:IsA("Sound") or d:IsA("Script") or d:IsA("LocalScript") then
			d:Destroy()
		elseif d:IsA("BasePart") then
			d.Anchored = true
			d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			d.Massless = true
			if d ~= root and d:GetAttribute("Role") then
				local j = d:GetAttribute("Joint")
				local pc: Piece = { part = d, base = rcf:ToObjectSpace(d.CFrame), role = tostring(d:GetAttribute("Role")),
					joint = if typeof(j) == "Vector3" then j else Vector3.zero, side = tonumber(d:GetAttribute("Side")) or 0,
					front = d:GetAttribute("Front") == true, n = tonumber(d:GetAttribute("N")) or 0 }
				table.insert(pieces, pc)
				byRole[pc.role] = byRole[pc.role] or {}
				table.insert(byRole[pc.role], pc)
				if silhouette then
					if d:IsA("MeshPart") then (d :: MeshPart).TextureID = "" end
					d.Color = Color3.fromRGB(8, 8, 10)
					d.Material = Enum.Material.SmoothPlastic
					if pc.role == "shell" then d.Transparency = 1 end
				end
			end
		end
	end
	root.Transparency = 1
	local parts, cfs = {}, {}
	for i, pc in pieces do parts[i] = pc.part; cfs[i] = pc.part.CFrame end
	local self = setmetatable({
		id = id, gait = info.gait, model = m, pieces = pieces, parts = parts, cfs = cfs, hidden = false,
		feet = tonumber(m:GetAttribute("Feet")) or 0.095, byRole = byRole,
	}, PetRig)
	return self
end

-- a turn of `a` about the axis through point j (the pet's own frame), as one CFrame to put before a piece's base
local function about(j: Vector3, r: CFrame): CFrame
	return CFrame.new(j) * r * CFrame.new(-j)
end

function PetRig.pose(self: Rig, cf: CFrame, phase: number, move: number, t: number)
	local m = math.clamp(move, 0, 1)
	local idle = 1 - m
	local g = self.gait
	for i, pc in self.pieces do
		local x = CFrame.identity
		if g == "waddle" then
			-- rock onto one foot, then the other; a twist and a lean with it; standing: a slow sway, a look about
			local roll = rad(11) * m * sin(phase) + rad(2.2) * idle * sin(t * 1.7)
			local pivot = Vector3.new(if roll > 0 then -self.feet else self.feet, 0, 0)
			local yaw = rad(9) * m * cos(phase) + rad(16) * idle * sin(t * 0.41) * max(0, sin(t * 0.23))
			x = CFrame.Angles(0, yaw, 0) * about(pivot, CFrame.Angles(0, 0, roll)) * CFrame.Angles(-rad(5) * m, 0, 0)
		elseif g == "crawl" then
			if pc.role == "mask" then
				x = CFrame.new(0, 0.03 * m * sin(phase * 2) + 0.012 * idle * sin(t * 2.1), -0.05 * m * sin(phase))
					* about(pc.joint, CFrame.Angles(rad(3) * m * sin(phase), rad(12) * idle * sin(t * 0.5), 0))
			elseif pc.role == "seg" then
				local w = phase - pc.n * 0.9
				x = CFrame.new(0, 0.035 * m * max(0, sin(w + math.pi / 2)) + 0.012 * idle * sin(t * 2 - pc.n),
					-0.07 * m * sin(w))
			elseif pc.role == "arm" then
				-- (on the front drum: it moves with it) each hand lifts and comes down ahead, in turn
				local w = phase + (if pc.side > 0 then math.pi else 0)
				local lift = rad(26) * m * max(0, sin(w)) + rad(7) * idle * max(0, sin(t * 2.6 + pc.side)) ^ 6
				local sweep = rad(7) * m * cos(w) * pc.side
				local seg = phase - 0.9
				x = CFrame.new(0, 0.035 * m * max(0, sin(seg + math.pi / 2)), -0.07 * m * sin(seg))
					* about(pc.joint, CFrame.Angles(lift, sweep, 0))
			end
		elseif g == "trot" then
			local bob = 0.045 * m * abs(sin(phase)) + 0.012 * idle * sin(t * 2.4)
			local body = CFrame.new(0, bob, 0) * about(Vector3.new(0, 0.58, 0), CFrame.Angles(rad(2.5) * m * sin(phase * 2), 0, 0))
			if pc.role == "body" then
				x = body
			elseif pc.role == "leg" then
				local diag = (pc.front and pc.side < 0) or (not pc.front and pc.side > 0)
				local a = rad(34) * m * sin(phase + (if diag then 0 else math.pi))
				x = body * about(pc.joint, CFrame.Angles(a, 0, 0))
			elseif pc.role == "head" then
				local tilt = rad(14) * idle * sin(t * 0.7) * max(0, sin(t * 0.31)) ^ 2
				x = body * about(pc.joint, CFrame.Angles(rad(5) * m * sin(phase * 2 + 0.6), rad(8) * idle * sin(t * 0.45), tilt))
			elseif pc.role == "tail" then
				local wag = rad(30) * sin(t * (9 + 8 * m))
				x = body * about(pc.joint, CFrame.Angles(0, wag, 0))
			end
		end
		self.cfs[i] = cf * x * pc.base
	end
	workspace:BulkMoveTo(self.parts, self.cfs, Enum.BulkMoveMode.FireCFrameChanged)
end

-- hide or show the whole pet on this screen only (first person, too near the camera)
function PetRig.hide(self: Rig, on: boolean)
	if self.hidden == on then return end
	self.hidden = on
	for _, p in self.parts do p.LocalTransparencyModifier = if on then 1 else 0 end
end

function PetRig.destroy(self: Rig)
	self.model:Destroy()
end

return PetRig
