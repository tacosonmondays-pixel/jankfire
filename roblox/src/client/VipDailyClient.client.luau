--!strict
-- THE VIP DAILY REWARD, the player's side (the server is VipDaily.luau, the table Shared.VipDailyData).
--   the prompt on Trisangle ("VipDailyPrompt", tagged): its words are set here for this player only: "Daily reward" when
--   it's ready, "Back in 7h 12m" once today's is taken, "VIP daily reward" for a player who isn't VIP.
--   the server's word (JankfireRemotes.VipDaily):
--     won    -> Trisangle says one word over her head ("Here."), then the reveal: LootOpening.reward (the loot
--               session's, its reel and prize style) when it has one, else a plain reel here in the shop's look
--     later  -> "Tomorrow." from her and a callout with the time left
--     notvip -> the shop opened straight onto the VIP tile (BACK closes it)
--     error  -> a callout
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")
local TextChatService = game:GetService("TextChatService")
local UIS = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Shop = require(Shared:WaitForChild("Shop")) :: any
local T = require(script.Parent:WaitForChild("Theme"))
local Hud = require(script.Parent:WaitForChild("Hud")) :: any

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new = T.new
local TAG = "VipDailyPrompt"

local function now(): number return workspace:GetServerTimeNow() end
local function left(at: number): string
	local s = math.max(0, math.floor(at - now()))
	local h, m = s // 3600, (s % 3600) // 60
	return if h > 0 then ("%dh %dm"):format(h, m) else ("%dm"):format(math.max(1, m))
end

-- ---------------------------------------------------------------- the prompt's words
local function words(pr: ProximityPrompt)
	if me:GetAttribute("VIP") ~= true then pr.ActionText = "VIP daily reward"; return end
	local at = tonumber(me:GetAttribute("VipDailyNext")) or 0
	pr.ActionText = if at > now() then "Back in " .. left(at) else "Daily reward"
end
local function all() for _, pr in CollectionService:GetTagged(TAG) do if pr:IsA("ProximityPrompt") then words(pr) end end end
CollectionService:GetInstanceAddedSignal(TAG):Connect(function(pr) if pr:IsA("ProximityPrompt") then words(pr) end end)
me:GetAttributeChangedSignal("VipDailyNext"):Connect(all)
me:GetAttributeChangedSignal("VIP"):Connect(all)
task.spawn(function() while true do all(); task.wait(20) end end)

-- ---------------------------------------------------------------- Trisangle's one word
local function say(text: string)
	for _, pr in CollectionService:GetTagged(TAG) do
		-- (the prompt sits on her avatar once the hub has moved it there, else on her seat beside the avatar)
		local m = pr:FindFirstAncestorOfClass("Model")
		if not (m and m:FindFirstChild("Head")) then
			local spot = pr.Parent
			local who = spot and spot:GetAttribute("Who")
			m = spot and spot.Parent and spot.Parent:FindFirstChild("Regular_" .. tostring(who)) :: any
		end
		local head = m and m:FindFirstChild("Head")
		if head then pcall(function() TextChatService:DisplayBubble(head :: BasePart, text) end); return end
	end
end

-- ---------------------------------------------------------------- the plain reveal (until LootOpening.reward)
local function rarityColor(r: string): Color3
	local e = Shop.RARITY and Shop.RARITY[r]
	return if e and e.color then e.color else T.MUTED
end
local open = false
local function plainReveal(msg: any)
	if open then return end
	open = true
	local prize = msg.prize
	local gui = new("ScreenGui", { Name = "JankVipDaily", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 40, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
	local dim = new("Frame", { BackgroundColor3 = Color3.fromRGB(6, 7, 9), BackgroundTransparency = 0.3, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, gui)
	local root = T.scaled(gui)
	local plate = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.04, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(640, 330) }, root)
	T.corner(plate, 8); T.edge(plate)
	local eb = T.text(plate, "Eyebrow", "DAILY REWARD  ·  " .. string.upper(tostring(msg.who or "Trisangle")), 12, T.MUTED, T.FONT_BOLD)
	eb.Position = UDim2.fromOffset(22, 18); eb.Size = UDim2.new(1, -44, 0, 16)
	-- the reel: cards slide under a fixed amber mark and stop on the prize
	local CW, GAP = 128, 10
	local win = new("Frame", { BackgroundColor3 = T.CARD, BorderSizePixel = 0, ClipsDescendants = true, Position = UDim2.fromOffset(22, 48), Size = UDim2.new(1, -44, 0, 132) }, plate)
	T.corner(win, 6)
	local strip = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(0, 0, 1, 0) }, win)
	local reel = if type(msg.reel) == "table" and #msg.reel > 0 then msg.reel else { prize }
	local land = tonumber(msg.land) or #reel
	for i, pz in reel do
		local c = new("Frame", { BackgroundColor3 = T.BG, BorderSizePixel = 0, Position = UDim2.fromOffset((i - 1) * (CW + GAP) + GAP, 10), Size = UDim2.fromOffset(CW, 112) }, strip)
		T.corner(c, 5)
		new("Frame", { BackgroundColor3 = rarityColor(pz.rarity), BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 4) }, c)
		local kindWord = if pz.kind == "brass" then "BRASS" elseif pz.kind == "container" then "CONTAINER" else string.upper(Shop.KIND_NAMES and Shop.KIND_NAMES[pz.kind] or pz.kind)
		local k = T.text(c, "Kind", kindWord, 10, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
		k.Position = UDim2.fromOffset(6, 14); k.Size = UDim2.new(1, -12, 0, 12)
		local n = T.text(c, "Name", string.upper(tostring(pz.name)), 14, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
		n.Position = UDim2.fromOffset(6, 40); n.Size = UDim2.new(1, -12, 0, 40); n.TextWrapped = true
	end
	new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 0), Size = UDim2.new(0, 3, 1, 0), ZIndex = 3 }, win)
	-- (where the prize card's middle sits under the mark)
	local winW = 640 - 44
	local endX = winW / 2 - ((land - 1) * (CW + GAP) + GAP + CW / 2) + math.random(-38, 38)
	strip.Position = UDim2.fromOffset(winW / 2 - (GAP + CW / 2) + CW * 2, 0)
	local name = T.text(plate, "Prize", "", 30, T.TEXT, T.FONT_TITLE)
	name.Position = UDim2.fromOffset(22, 196); name.Size = UDim2.new(1, -44, 0, 36)
	local line = T.text(plate, "Rarity", "", 13, T.MUTED, T.FONT_BOLD)
	line.Position = UDim2.fromOffset(22, 234); line.Size = UDim2.new(1, -44, 0, 16)
	local done = new("TextButton", { AutoButtonColor = false, BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.new(1, -22, 1, -18), Size = UDim2.fromOffset(150, 44), FontFace = T.FONT_BOLD, TextSize = 15, Text = "DONE", TextColor3 = T.INK, Visible = false }, plate)
	T.corner(done)
	local closed = false
	local function close()
		if closed then return end
		closed = true
		gui:Destroy()
		open = false
	end
	done.MouseButton1Click:Connect(close)
	local tw = T.tween(strip, 3.2, { Position = UDim2.fromOffset(endX, 0) }, Enum.EasingStyle.Quint, Enum.EasingDirection.Out)
	tw.Completed:Wait()
	if closed then return end
	name.Text = string.upper(tostring(prize.name))
	name.TextColor3 = if prize.tier == "best" then rarityColor(prize.rarity) else T.TEXT
	local how = if prize.kind == "brass" then "added to your Brass"
		elseif prize.kind == "container" then "in your containers: open it in the shop [B]"
		else "yours: wear it from the loadout [L]"
	line.Text = string.upper(if prize.rarity and Shop.RARITY and Shop.RARITY[prize.rarity] then Shop.RARITY[prize.rarity].name else tostring(prize.rarity)) .. "  ·  " .. string.upper(how)
	if msg.late then line.Text ..= "  ·  ARRIVING SHORTLY" end
	done.Visible = true
	local c = UIS.InputBegan:Connect(function(io, gp)
		if gp then return end
		if io.KeyCode == Enum.KeyCode.Return or io.KeyCode == Enum.KeyCode.Space or io.KeyCode == Enum.KeyCode.ButtonA then close() end
	end)
	gui.Destroying:Connect(function() c:Disconnect() end)
end

local function reveal(msg: any)
	local m = script.Parent:FindFirstChild("LootOpening")
	if m and m:IsA("ModuleScript") then
		local ok, Op = pcall(require, m)
		if ok and type(Op) == "table" and type((Op :: any).reward) == "function" then
			-- (no sub-line: her one word is the bubble over her head; the reveal reads "FROM TRISANGLE")
			local spec = { title = "DAILY REWARD", who = msg.who or "Trisangle", line = nil, prize = msg.prize, reel = msg.reel, land = msg.land }
			local fine, err = pcall((Op :: any).reward, spec)
			if fine then return end
			warn("[jankfire] vip daily: the opening's reveal broke: " .. tostring(err))
		end
	end
	plainReveal(msg)
end

-- ---------------------------------------------------------------- the server's word
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("VipDaily", 60) :: RemoteEvent?
if Remote then
	Remote.OnClientEvent:Connect(function(msg: any)
		if type(msg) ~= "table" then return end
		if msg.t == "won" then
			say("Here.")
			task.spawn(reveal, msg)
		elseif msg.t == "later" then
			say("Tomorrow.")
			Hud.callout("BACK IN " .. string.upper(left(tonumber(msg.at) or now())), 1.6)
		elseif msg.t == "notvip" then
			local m = script.Parent:FindFirstChild("ShopUI")
			local ok, S = pcall(require, m :: ModuleScript)
			if ok and type(S) == "table" and type((S :: any).open) == "function" then (S :: any).open(nil, "vip") end
		elseif msg.t == "error" then
			Hud.callout(string.upper(tostring(msg.why or "try again")), 1.6)
		end
	end)
end
