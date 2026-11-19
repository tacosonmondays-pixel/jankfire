--!strict
-- THE OWNER'S ANNOUNCEMENTS on everyone's screen (19 Nov 2026, the owner: "write announcements that go across the
-- screen across all servers"). OwnerDev.server sends DevFx { k = "announce", text, from }: text Roblox's filter has
-- already had on the owner's server (shown as plain text here, never rich text). on every screen:
--   a dark band sweeps in across the screen between two gold lines, the line rides in from the right and lands in the
--   middle, holds about 6 s (a long line a little longer), then rides off to the left and the band follows it out
--   outside a match: a big band in the upper third (up to 30 px text, shrunk to fit)
--   in a MATCH: a slimmer band high on the screen, well clear of the crosshair (up to 21 px text)
-- over the HUD. one at a time: another waits for the one showing (at most 3 waiting). sounds are recordings from the
-- place's library (Sfx): slap_whoosh as it sweeps in, ting as the line lands. no voices
-- the chat line ("[ANNOUNCEMENT] <owner>: <text>") is OwnerDev.client's giftChat, from the server's own DevFx line
-- Studio photos: player attribute AnnounceTest = a text shows it here only; AnnounceHold = true holds it on screen
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local J = script.Parent
local T = require(J:WaitForChild("Theme")) :: any
local Sfx: any = nil
local function sound(name: string, vol: number?)
	if Sfx == nil then local ok, m = pcall(require, J:WaitForChild("Sfx")); Sfx = if ok then m else false end
	if Sfx then pcall(Sfx.play, name, nil, vol) end
end

local HUB = { y = 0.27, h = 118, text = 30, label = 13 }
local MATCH = { y = 0.17, h = 74, text = 21, label = 11 }

local queue: { any } = {}
local showing = false

local function show(a: any)
	local inMatch = me:GetAttribute("Zone") == "match"
	local L = if inMatch then MATCH else HUB
	local gui = T.new("ScreenGui", { Name = "JankAnnounce", IgnoreGuiInset = true, DisplayOrder = 90, ResetOnSpawn = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
	local band = T.new("Frame", { Name = "Band", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(-1, 0, L.y, 0),
		Size = UDim2.new(1, 0, 0, L.h), BackgroundColor3 = T.BG, BackgroundTransparency = 0.12, BorderSizePixel = 0, ClipsDescendants = true }, gui)
	for i, y in { 0, 1 } do
		T.new("Frame", { Name = "Line" .. i, AnchorPoint = Vector2.new(0, y), Position = UDim2.fromScale(0, y), Size = UDim2.new(1, 0, 0, 2),
			BackgroundColor3 = T.ACCENT, BorderSizePixel = 0 }, band)
	end
	local head = T.text(band, "From", ("ANNOUNCEMENT  ·  %s"):format(string.upper(tostring(a.from))), L.label, T.ACCENT, T.FONT_BOLD, Enum.TextXAlignment.Center)
	head.AnchorPoint = Vector2.new(0.5, 0)
	head.Position = UDim2.new(1.6, 0, 0, if inMatch then 7 else 12)
	head.Size = UDim2.new(0.86, 0, 0, L.label + 4)
	local line = T.text(band, "Text", tostring(a.text), L.text, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
	line.RichText = false
	line.AnchorPoint = Vector2.new(0.5, 1)
	line.Position = UDim2.new(1.6, 0, 1, if inMatch then -8 else -14)
	line.Size = UDim2.new(0.86, 0, 0, L.h - L.label - (if inMatch then 22 else 34))
	line.TextWrapped = true
	line.TextScaled = true
	T.new("UITextSizeConstraint", { MaxTextSize = L.text, MinTextSize = 12 }, line)

	-- in: the band sweeps across, then the words ride in from the right and land in the middle
	sound("slap_whoosh", 0.5)
	T.tween(band, 0.32, { Position = UDim2.new(0, 0, L.y, 0) }, Enum.EasingStyle.Quart, Enum.EasingDirection.Out)
	task.wait(0.12)
	T.tween(head, 0.42, { Position = UDim2.new(0.5, 0, head.Position.Y.Scale, head.Position.Y.Offset) }, Enum.EasingStyle.Quart, Enum.EasingDirection.Out)
	T.tween(line, 0.5, { Position = UDim2.new(0.5, 0, line.Position.Y.Scale, line.Position.Y.Offset) }, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
	task.wait(0.4)
	sound("ting", 0.55)
	-- hold: about 6 s on screen in all; a long line a little longer
	local n = utf8.len(tostring(a.text)) or #tostring(a.text)
	task.wait(math.clamp(4.6 + n * 0.025, 5, 7.5))
	while RunService:IsStudio() and me:GetAttribute("AnnounceHold") == true do task.wait(0.2) end
	-- out: the words ride off to the left, the band follows
	T.tween(line, 0.4, { Position = UDim2.new(-0.6, 0, line.Position.Y.Scale, line.Position.Y.Offset) }, Enum.EasingStyle.Quart, Enum.EasingDirection.In)
	T.tween(head, 0.4, { Position = UDim2.new(-0.6, 0, head.Position.Y.Scale, head.Position.Y.Offset) }, Enum.EasingStyle.Quart, Enum.EasingDirection.In)
	task.wait(0.12)
	T.tween(band, 0.36, { Position = UDim2.new(1, 0, L.y, 0) }, Enum.EasingStyle.Quart, Enum.EasingDirection.In)
	task.wait(0.4)
	gui:Destroy()
end

local function push(a: any)
	if #queue >= 3 then return end
	table.insert(queue, a)
	if showing then return end
	showing = true
	task.spawn(function()
		while #queue > 0 do
			local nxt = table.remove(queue, 1)
			local ok, err = pcall(show, nxt)
			if not ok then
				warn("[jankfire] announcement: " .. tostring(err))
				local g = me:FindFirstChildOfClass("PlayerGui") and (me:FindFirstChildOfClass("PlayerGui") :: PlayerGui):FindFirstChild("JankAnnounce")
				if g then g:Destroy() end
			end
		end
		showing = false
	end)
end

local Fx = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("DevFx", 60) :: RemoteEvent?
if Fx then
	Fx.OnClientEvent:Connect(function(d: any)
		if type(d) ~= "table" or d.k ~= "announce" or type(d.text) ~= "string" or d.text == "" then return end
		push({ text = string.sub(d.text, 1, 480), from = string.sub(tostring(d.from or ""), 1, 32) })
	end)
end

if RunService:IsStudio() then
	me:GetAttributeChangedSignal("AnnounceTest"):Connect(function()
		local v = me:GetAttribute("AnnounceTest")
		if type(v) == "string" and v ~= "" then push({ text = v, from = me.DisplayName }) end
	end)
end
