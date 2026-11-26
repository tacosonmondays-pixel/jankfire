--!strict
-- HOLDOUT's hider animations (26 Nov 2026; roblox/docs/HUNT.md section 7): mocap from the owner's Mixamo clips,
-- retargeted for R15 and R6 (HuntConfig.ANIMS). Played on your own body, so Roblox shows them to everyone.
--   HuntAnims.locomotion(ch, on)   swap the avatar's own idle and run (its Animate script's ids) for the mode's, or back
--   HuntAnims.track(hum, name)     the loaded track ("haymaker", "jab", "shove", "liedown", "lying"), or nil
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any

local HuntAnims = {}

local function rig(hum: Humanoid): string return if hum.RigType == Enum.HumanoidRigType.R6 then "R6" else "R15" end
local function animator(hum: Humanoid): Animator?
	local a = hum:FindFirstChildOfClass("Animator")
	return a
end

local cache: { [Humanoid]: { [string]: AnimationTrack } } = setmetatable({}, { __mode = "k" }) :: any
function HuntAnims.track(hum: Humanoid, name: string): AnimationTrack?
	local set = cache[hum]
	if not set then set = {}; cache[hum] = set end
	local t = set[name]
	if t then return t end
	local id = (HC.ANIMS[rig(hum)] or {})[name]
	local an = animator(hum)
	if not id or not an then return nil end
	local a = Instance.new("Animation")
	a.AnimationId = "rbxassetid://" .. tostring(id)
	local ok, tr = pcall(function() return an:LoadAnimation(a) end)
	if not ok or not tr then return nil end
	set[name] = tr
	return tr
end

-- the avatar's Animate script: its idle (two takes) and run Animations get the mode's ids; the originals wait in an
-- attribute on each, and come back with on = false. Animate is restarted so the swap shows at once
local SLOTS = { { "idle", "Animation1", "idle" }, { "idle", "Animation2", "idle" }, { "run", "RunAnim", "run" } }
function HuntAnims.locomotion(ch: Model, on: boolean)
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local animate = ch:FindFirstChild("Animate")
	if not hum or not animate then return end
	local ids = HC.ANIMS[rig(hum)] or {}
	local changed = false
	for _, s in SLOTS do
		local folder = animate:FindFirstChild(s[1])
		local an = folder and folder:FindFirstChild(s[2])
		if not (an and an:IsA("Animation")) then continue end
		if on then
			local id = ids[s[3]]
			if id and an:GetAttribute("HuntOrig") == nil then
				an:SetAttribute("HuntOrig", an.AnimationId)
				an.AnimationId = "rbxassetid://" .. tostring(id)
				changed = true
			end
		else
			local orig = an:GetAttribute("HuntOrig")
			if type(orig) == "string" then
				an.AnimationId = orig
				an:SetAttribute("HuntOrig", nil)
				changed = true
			end
		end
	end
	if changed and animate:IsA("LocalScript") then
		local an = animator(hum)
		if an then for _, t in an:GetPlayingAnimationTracks() do if t.Priority == Enum.AnimationPriority.Idle or t.Priority == Enum.AnimationPriority.Movement or t.Priority == Enum.AnimationPriority.Core then t:Stop(0.15) end end end
		animate.Enabled = false
		animate.Enabled = true
	end
end

return HuntAnims
