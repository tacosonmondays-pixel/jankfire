--!strict
-- one pet's model and its moves (Shared.Flair PETS; doc FLAIR.md, "Pets"). client only: the follower (Pets.client) and
-- the equip screen (FlairUI) both use it.
--   PetRig.new(id, silhouette?) -> rig | nil      a copy of ReplicatedStorage.JankfirePets.<id> (PolishBackup.PetImport
--                                                 builds those from the uploads): a Root part at the pet's middle on the
--                                                 floor, facing -Z, and either
--                                                   * stiff pieces (the mini mannequin): MeshParts that carry their joint
--                                                     (attributes Role, Joint, Side, Front, N), or
--                                                   * one skinned MeshPart (the meat dog, the train slug, attribute
--                                                     Skinned on the model): its Bones are turned, the mesh bends with them
--                                                 silhouette: flat black, the picker's look for a pet you haven't found
--   rig:pose(cf, phase, move, t)                  cf = where the pet stands (on the floor, facing its LookVector); phase
--                                                 = the gait's clock (radians, it runs with the ground covered); move = 0
--                                                 standing .. 1 going; t = time. the parts move in one BulkMoveTo; a
--                                                 skinned pet's bones get their Transform (a handful a frame)
--   rig:hide(on) / rig:destroy()
-- the gaits (Flair.PETS[id].gait), cheap sums of sines, nothing on the server:
--   waddle  the mannequin is one stiff piece: it rocks from one foot onto the other like a wind-up toy, twisting a little,
--           leaning into the walk; standing, it sways and looks about
--   crawl   the slug's hands reach forward in turn (the arm lifts at the shoulder, the forearm at the elbow) while its body
--           bunches and stretches in a wave from the collar back; standing, it looks about and breathes
--   trot    the dog's legs swing in diagonal pairs, its body bobs and its head nods; the tail wags all the time (faster
--           on the move); standing, it tilts its head now and then
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Flair = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Flair")) :: any

local PetRig = {}
PetRig.__index = PetRig

type Piece = { part: BasePart, base: CFrame, role: string, joint: Vector3, side: number, front: boolean, n: number }
type BoneR = { bone: Bone, rest: CFrame, restInv: CFrame, pivot: Vector3 }
export type Rig = typeof(setmetatable({} :: {
	id: string, gait: string, model: Model, pieces: { Piece }, parts: { BasePart }, cfs: { CFrame }, hidden: boolean,
	feet: number, skinned: boolean, bones: { [string]: BoneR }, rootPart: BasePart, rootBase: CFrame,
}, PetRig))

local rad, sin, cos, abs, max = math.rad, math.sin, math.cos, math.abs, math.max

function PetRig.template(id: string): Model?
	local kit = ReplicatedStorage:FindFirstChild("JankfirePets")
	local m = kit and kit:FindFirstChild(id)
	return if m and m:IsA("Model") then m else nil
end

local function blacken(d: BasePart)
	if d:IsA("MeshPart") then (d :: MeshPart).TextureID = "" end
	d.Color = Color3.fromRGB(8, 8, 10)
	d.Material = Enum.Material.SmoothPlastic
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
	local bones: { [string]: BoneR } = {}
	local skinned = m:GetAttribute("Skinned") == true
	for _, d in m:GetDescendants() do
		if d:IsA("Sound") or d:IsA("Script") or d:IsA("LocalScript") then
			d:Destroy()
		elseif d:IsA("Bone") then
			-- (its rest frame in the pet's own frame; the turn it takes is written in that frame, then carried into the bone's)
			local rest = rcf:ToObjectSpace(d.WorldCFrame)
			bones[d.Name] = { bone = d, rest = rest, restInv = rest:Inverse(), pivot = rest.Position }
		elseif d:IsA("BasePart") then
			d.Anchored = true
			d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			d.Massless = true
			if d ~= root then
				local j = d:GetAttribute("Joint")
				local pc: Piece = { part = d, base = rcf:ToObjectSpace(d.CFrame), role = tostring(d:GetAttribute("Role") or "body"),
					joint = if typeof(j) == "Vector3" then j else Vector3.zero, side = tonumber(d:GetAttribute("Side")) or 0,
					front = d:GetAttribute("Front") == true, n = tonumber(d:GetAttribute("N")) or 0 }
				table.insert(pieces, pc)
				if silhouette then
					blacken(d)
					if pc.role == "shell" then d.Transparency = 1 end
				end
			end
		end
	end
	root.Transparency = 1
	-- (the Root moves too: GetPivot and the bounding box follow the pet)
	local parts, cfs = { root :: BasePart }, { rcf }
	for _, pc in pieces do table.insert(parts, pc.part); table.insert(cfs, pc.part.CFrame) end
	local self = setmetatable({
		id = id, gait = info.gait, model = m, pieces = pieces, parts = parts, cfs = cfs, hidden = false,
		feet = tonumber(m:GetAttribute("Feet")) or 0.095, skinned = skinned, bones = bones,
		rootPart = root :: BasePart, rootBase = CFrame.identity,
	}, PetRig)
	return self
end

-- a turn r about the point j (the pet's own frame)
local function about(j: Vector3, r: CFrame): CFrame
	return CFrame.new(j) * r * CFrame.new(-j)
end

-- a bone's Transform for a move x written in the pet's frame (x: where the bone's rest frame goes, relative to the rest of
-- the pet: for a bone whose parent moves too, x is relative to that parent's move)
local function setBone(b: BoneR?, x: CFrame)
	if not b then return end
	b.bone.Transform = b.restInv * x * b.rest
end

function PetRig.pose(self: Rig, cf: CFrame, phase: number, move: number, t: number)
	local m = math.clamp(move, 0, 1)
	local idle = 1 - m
	local g = self.gait
	self.cfs[1] = cf
	if self.skinned then
		for i, pc in self.pieces do self.cfs[i + 1] = cf * pc.base end
		local B = self.bones
		if g == "trot" then
			local bob = 0.04 * m * abs(sin(phase)) + 0.01 * idle * sin(t * 2.4)
			local body = CFrame.new(0, bob, 0) * about(Vector3.new(0, 0.58, 0.1), CFrame.Angles(rad(2.5) * m * sin(phase * 2), 0, 0))
			setBone(B.body, body)
			for _, nm in { "legFL", "legFR", "legBL", "legBR" } do
				local b = B[nm]
				if b then
					local diag = nm == "legFL" or nm == "legBR"
					local a = rad(32) * m * sin(phase + (if diag then 0 else math.pi))
					setBone(b, body * about(b.pivot, CFrame.Angles(a, 0, 0)))
				end
			end
			local h = B.head
			if h then
				local tilt = rad(14) * idle * sin(t * 0.7) * max(0, sin(t * 0.31)) ^ 2
				setBone(h, body * about(h.pivot, CFrame.Angles(rad(5) * m * sin(phase * 2 + 0.6), rad(8) * idle * sin(t * 0.45), tilt)))
			end
			local tl = B.tail
			if tl then setBone(tl, body * about(tl.pivot, CFrame.Angles(0, rad(30) * sin(t * (9 + 8 * m)), 0))) end
		elseif g == "crawl" then
			-- the body: a wave from the collar back, each part bunching forward and back, a little lift on the reach
			for k = 0, 4 do
				local b = B["s" .. k]
				if b then
					local w = phase - k * 0.9
					local x = CFrame.new(0, 0.03 * m * max(0, sin(w + math.pi / 2)) + 0.01 * idle * sin(t * 2 - k), -0.06 * m * sin(w))
					if k == 0 then
						x = x * about(b.pivot, CFrame.Angles(rad(3) * m * sin(phase), rad(10) * idle * sin(t * 0.5), 0))
					end
					setBone(b, x)
				end
			end
			-- the arms (they hang from the front part, so their moves are relative to it): each in turn lifts at the
			-- shoulder and the elbow, reaches, and comes down ahead
			for _, side in { "L", "R" } do
				local sd = if side == "R" then 1 else -1
				local w = phase + (if sd > 0 then math.pi else 0)
				local reach = max(0, sin(w))
				local lift = rad(22) * m * reach + rad(6) * idle * max(0, sin(t * 2.6 + sd)) ^ 6
				local arm, fore = B["arm" .. side], B["fore" .. side]
				if arm then setBone(arm, about(arm.pivot, CFrame.Angles(lift, rad(6) * m * cos(w) * sd, 0))) end
				if fore then setBone(fore, about(fore.pivot, CFrame.Angles(rad(14) * m * reach, 0, 0))) end
			end
		end
	else
		for i, pc in self.pieces do
			local x = CFrame.identity
			if g == "waddle" then
				-- rock onto one foot, then the other; a twist and a lean with it; standing: a slow sway, a look about
				local roll = rad(11) * m * sin(phase) + rad(2.2) * idle * sin(t * 1.7)
				local pivot = Vector3.new(if roll > 0 then -self.feet else self.feet, 0, 0)
				local yaw = rad(9) * m * cos(phase) + rad(16) * idle * sin(t * 0.41) * max(0, sin(t * 0.23))
				x = CFrame.Angles(0, yaw, 0) * about(pivot, CFrame.Angles(0, 0, roll)) * CFrame.Angles(-rad(5) * m, 0, 0)
			end
			self.cfs[i + 1] = cf * x * pc.base
		end
	end
	workspace:BulkMoveTo(self.parts, self.cfs, Enum.BulkMoveMode.FireCFrameChanged)
end

-- hide or show the whole pet on this screen only (the camera inside it). force: write it again even if unchanged (the
-- follower does now and then, so nothing else that touches LocalTransparencyModifier can leave it hidden); only parts
-- that differ are written
function PetRig.hide(self: Rig, on: boolean, force: boolean?)
	if self.hidden == on and not force then return end
	self.hidden = on
	local want = if on then 1 else 0
	for _, p in self.parts do
		if p ~= self.rootPart and p.LocalTransparencyModifier ~= want then p.LocalTransparencyModifier = want end
	end
end

function PetRig.destroy(self: Rig)
	self.model:Destroy()
end

return PetRig
