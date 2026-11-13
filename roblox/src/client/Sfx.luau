--!strict
-- the sounds: the web game's synth sounds (public/js/audio.js) rendered to .ogg files (roblox/assets/sounds/, list in
-- SOUNDS.md). Roblox can only play uploaded audio, so each one is a Sound in ReplicatedStorage.JankfireSounds with an
-- empty SoundId until the owner uploads the file and pastes its id in. silent until then, never an error
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

local Sfx = {}
local lib = ReplicatedStorage:WaitForChild("JankfireSounds", 5)
local holder = Instance.new("Part")
holder.Name = "JankfireSfx"; holder.Anchored = true; holder.CanCollide = false; holder.CanQuery = false; holder.CanTouch = false
holder.Transparency = 1; holder.Size = Vector3.new(0.1, 0.1, 0.1)
holder.Parent = workspace

local function src(name: string): Sound?
	local s = lib and lib:FindFirstChild(name)
	if s and s:IsA("Sound") and s.SoundId ~= "" then return s end
	return nil
end

-- play a sound: on you (no position) or out in the world at `at`
function Sfx.play(name: string, at: Vector3?, vol: number?, pitch: number?)
	local s = src(name)
	if not s then return end
	local c = s:Clone()
	c.Volume = s.Volume * (vol or 1)
	c.PlaybackSpeed = s.PlaybackSpeed * (pitch or 1)
	if at then
		local a = Instance.new("Attachment")
		a.WorldPosition = at
		a.Parent = workspace.Terrain
		c.RollOffMinDistance = 15; c.RollOffMaxDistance = 600
		c.Parent = a
		c.Ended:Once(function() a:Destroy() end)
		c:Play()
		task.delay(6, function() if a.Parent then a:Destroy() end end)
	else
		c.Parent = SoundService -- (a Sound in SoundService plays for you alone, not in the world)
		c.Ended:Once(function() c:Destroy() end)
		c:Play()
		task.delay(6, function() if c.Parent then c:Destroy() end end)
	end
end

-- the Redline gets brighter, higher and shorter as k (0 full HP -> 1 at 0 HP) rises: three renders + a pitch nudge
function Sfx.redline(k: number, at: Vector3?)
	local name = if k < 0.33 then "gun_redline_k0" elseif k < 0.75 then "gun_redline_k5" else "gun_redline_k10"
	Sfx.play(name, at, 1, 1 + (k % 0.4) * 0.1)
end

local _ = holder
return Sfx
