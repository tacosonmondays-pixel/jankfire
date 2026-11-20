--!strict
-- EMOTE MUSIC (19 Nov 2026; Shared.Flair MUSIC, doc FLAIR.md "Emote music"). the owner asked for an instrumental to go
-- with the dance emotes ("si there a copyright free instriumental to go with it?"): each dance emote has one licensed
-- track from Roblox's own audio library (its music partners' production music, cleared for Roblox experiences), an
-- instrumental, its start set on a beat. this script plays it for every player who is doing that emote:
--   * where: from the dancer (a Sound in their HumanoidRootPart): you hear another dancer within about 40 studs, low
--   * when: the moment their emote starts (the player attribute Emote, FlairServer's) to the moment it ends; never while
--     a match round is live (Zone "match" with RoundEnds set): the hub, lobbies, between rounds and after the match only
--   * volume: the MUSIC slider (SoundService.JankMaster.Music, SettingsApply); another player's music only while the
--     settings switch OTHERS' EMOTE MUSIC (snd.emoteMusic) is on. your own always plays (the slider can still mute it)
-- nothing on the server: each screen makes its own sounds
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

local Flair = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Flair")) :: any
local me = Players.LocalPlayer

local MAX_DIST = 40   -- studs: past this another dancer's music can't be heard
local MIN_DIST = 8    -- full volume inside this
local FADE = 0.25     -- seconds of fade out when the emote ends

local SettingsMod: any = nil
local function setting(key: string, default: any): any
	if SettingsMod == nil then
		local m = script.Parent:FindFirstChild("Settings")
		local ok, r = false, nil
		if m and m:IsA("ModuleScript") then ok, r = pcall(require, m) end
		SettingsMod = if ok and type(r) == "table" then r else false
	end
	if SettingsMod then
		local ok, v = pcall(SettingsMod.get, key)
		if ok and v ~= nil then return v end
	end
	return default
end
local function musicGroup(): SoundGroup?
	local m = SoundService:FindFirstChild("JankMaster")
	local g = m and m:FindFirstChild("Music")
	return if g and g:IsA("SoundGroup") then g else nil
end

local playing: { [Player]: { snd: Sound, id: string } } = {}

local function stop(p: Player)
	local x = playing[p]
	if not x then return end
	playing[p] = nil
	local s = x.snd
	local v0 = s.Volume
	task.spawn(function()
		local t0 = os.clock()
		while s.Parent and os.clock() - t0 < FADE do
			s.Volume = v0 * (1 - (os.clock() - t0) / FADE)
			task.wait()
		end
		s:Destroy()
	end)
end

-- may this player's emote have music now?
local function allowed(p: Player): boolean
	if p:GetAttribute("Zone") == "match" and p:GetAttribute("RoundEnds") ~= nil then return false end -- (a live round)
	if p ~= me and setting("snd.emoteMusic", true) == false then return false end
	return true
end

local function update(p: Player)
	local id = p:GetAttribute("Emote")
	local track = if type(id) == "string" then Flair.music(id) else nil
	local x = playing[p]
	if x and (x.id ~= id or not track or not allowed(p)) then stop(p); x = nil end
	if x or not track or not allowed(p) then return end
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart")
	if not (root and root:IsA("BasePart")) then return end
	local s = Instance.new("Sound")
	s.Name = "EmoteMusic"
	s.SoundId = track.sound
	s.Volume = track.volume
	s.Looped = true
	s.RollOffMode = Enum.RollOffMode.InverseTapered
	s.RollOffMinDistance = MIN_DIST
	s.RollOffMaxDistance = MAX_DIST
	if track.from and track.to then
		-- (one stretch of the track, on its beats, looped: it starts with the dance)
		s.PlaybackRegionsEnabled = true
		s.PlaybackRegion = NumberRange.new(track.from, track.to)
		s.LoopRegion = NumberRange.new(track.from, track.to)
	end
	s.SoundGroup = musicGroup()
	s.Parent = root
	s:Play()
	playing[p] = { snd = s, id = id :: string }
end

local function watch(p: Player)
	p:GetAttributeChangedSignal("Emote"):Connect(function() update(p) end)
	p:GetAttributeChangedSignal("RoundEnds"):Connect(function() update(p) end)
	p:GetAttributeChangedSignal("Zone"):Connect(function() update(p) end)
	p.CharacterRemoving:Connect(function() stop(p) end)
	update(p)
end
for _, p in Players:GetPlayers() do watch(p) end
Players.PlayerAdded:Connect(watch)
Players.PlayerRemoving:Connect(stop)
-- (the switch turned off: others' music stops now)
task.spawn(function()
	local m = script.Parent:WaitForChild("Settings", 30)
	if not m then return end
	local ok, S = pcall(require, m)
	if ok and type(S) == "table" and type((S :: any).watch) == "function" then
		pcall((S :: any).watch, "snd.emoteMusic", function()
			for p in pairs(playing) do if p ~= me then update(p) end end
			for _, p in Players:GetPlayers() do if p ~= me then update(p) end end
		end)
	end
end)
