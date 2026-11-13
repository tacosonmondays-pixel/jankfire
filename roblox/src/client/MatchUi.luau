--!strict
-- step 3's screens in JANKFIRE's comic look: the TRAINING / BACK TO THE MATCH button, the Training weapon picker
-- (one weapon per slot, every ported weapon listed, so each new one shows up here to test), and the end-of-match vote
-- (mode cards, then map cards: click one, see the counts, the winner pops)
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))

local PINK, YELLOW, CYAN, PANEL = Color3.fromRGB(255, 79, 216), Color3.fromRGB(255, 225, 77), Color3.fromRGB(79, 216, 255), Color3.fromRGB(18, 8, 24)
local FONT = Font.new("rbxasset://fonts/families/ComicNeueAngular.json", Enum.FontWeight.Bold)
local me = Players.LocalPlayer

local U = {}
U.onRoom = nil :: ((string) -> ())?
U.onLoadout = nil :: (({ string }) -> ())?
U.onVote = nil :: ((string, number) -> ())?

local gui = Instance.new("ScreenGui")
gui.Name = "JankfireMatch"; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true; gui.DisplayOrder = 3
gui.Parent = me:WaitForChild("PlayerGui")

-- a button: yellow main (black border, pink offset shadow, tilted), or white
local function button(parent: Instance, text: string, pos: UDim2, size: UDim2, main: boolean): TextButton
	local sh = Instance.new("Frame")
	sh.BackgroundColor3 = if main then PINK else Color3.new(0, 0, 0); sh.BorderSizePixel = 0
	sh.Position = pos + UDim2.fromOffset(5, 5); sh.Size = size; sh.Rotation = if main then -1.5 else 0
	sh.Parent = parent
	local b = Instance.new("TextButton")
	b.Position = pos; b.Size = size; b.Rotation = if main then -1.5 else 0
	b.BackgroundColor3 = if main then YELLOW else Color3.new(1, 1, 1); b.BorderSizePixel = 0; b.AutoButtonColor = true
	b.FontFace = FONT; b.TextScaled = true; b.TextColor3 = Color3.new(0, 0, 0); b.Text = text
	local st = Instance.new("UIStroke"); st.Thickness = 3; st.Color = Color3.new(0, 0, 0); st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; st.Parent = b
	local pad = Instance.new("UIPadding"); pad.PaddingLeft = UDim.new(0, 6); pad.PaddingRight = UDim.new(0, 6); pad.Parent = b
	b.Parent = parent
	b:GetPropertyChangedSignal("Visible"):Connect(function() sh.Visible = b.Visible end)
	return b
end
local function panel(parent: Instance, pos: UDim2, size: UDim2): Frame
	local sh = Instance.new("Frame")
	sh.BackgroundColor3 = CYAN; sh.BorderSizePixel = 0; sh.Position = pos + UDim2.fromOffset(8, 8); sh.Size = size
	sh.Parent = parent
	local f = Instance.new("Frame")
	f.BackgroundColor3 = PANEL; f.BackgroundTransparency = 0.05; f.BorderSizePixel = 0; f.Position = pos; f.Size = size
	local st = Instance.new("UIStroke"); st.Color = PINK; st.Thickness = 4; st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; st.Parent = f
	f.Parent = parent
	f:GetPropertyChangedSignal("Visible"):Connect(function() sh.Visible = f.Visible end)
	return f
end
local function label(parent: Instance, text: string, pos: UDim2, size: UDim2, color: Color3?): TextLabel
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1; t.Position = pos; t.Size = size; t.FontFace = FONT; t.TextScaled = true
	t.Text = text; t.TextColor3 = color or Color3.new(1, 1, 1); t.TextStrokeTransparency = 0.3
	t.Parent = parent
	return t
end

-- ---------------------------------------------------------------- the room button (top left) + the picker button
local roomBtn = button(gui, "TRAINING (T)", UDim2.fromOffset(18, 16), UDim2.fromOffset(210, 44), true)
local pickBtn = button(gui, "WEAPONS (B)", UDim2.fromOffset(18, 70), UDim2.fromOffset(210, 36), false)
pickBtn.Visible = false
local function room(): string
	local r = me:GetAttribute("Room")
	return if type(r) == "string" then r else "ffa"
end
roomBtn.Activated:Connect(function()
	if U.onRoom then U.onRoom(if room() == "training" then "ffa" else "training") end
end)
local function refreshRoom()
	local tr = room() == "training"
	roomBtn.Text = if tr then "BACK TO THE MATCH (T)" else "TRAINING (T)"
	pickBtn.Visible = tr
end
me:GetAttributeChangedSignal("Room"):Connect(refreshRoom)
refreshRoom()

-- ---------------------------------------------------------------- the weapon picker (Training)
local picker = panel(gui, UDim2.new(0.5, -330, 0.5, -200), UDim2.fromOffset(660, 400))
picker.Visible = false
label(picker, "PICK YOUR LOADOUT", UDim2.fromOffset(16, 8), UDim2.new(1, -32, 0, 44), YELLOW)
local SLOTS = { "primary", "secondary", "melee" }
local choice: { string } = {}
local slotLists: { Frame } = {}
for i, slot in SLOTS do
	label(picker, string.upper(slot), UDim2.new((i - 1) / 3, 16, 0, 60), UDim2.new(1 / 3, -32, 0, 28), CYAN)
	local col = Instance.new("Frame")
	col.BackgroundTransparency = 1; col.Position = UDim2.new((i - 1) / 3, 16, 0, 94); col.Size = UDim2.new(1 / 3, -32, 1, -160)
	local l = Instance.new("UIListLayout"); l.Padding = UDim.new(0, 8); l.Parent = col
	col.Parent = picker
	slotLists[i] = col
end
local okBtn = button(picker, "LOCK IN", UDim2.new(1, -196, 1, -58), UDim2.fromOffset(176, 44), true)
local function current(): { string }
	local s = me:GetAttribute("Loadout")
	local out = {}
	if type(s) == "string" then for w in string.gmatch(s, "[^,]+") do table.insert(out, w) end end
	return if #out == 3 then out else table.clone(Weapons.loadout)
end
local function recolor()
	for i in SLOTS do
		for _, b in slotLists[i]:GetChildren() do
			local id = b:GetAttribute("Weapon")
			local w = type(id) == "string" and Weapons.list[id]
			if b:IsA("TextButton") and w then
				b.BackgroundColor3 = if choice[i] == id then w.color else Color3.fromRGB(40, 24, 52)
				b.TextColor3 = if choice[i] == id then Color3.new(0, 0, 0) else w.color
			end
		end
	end
end
local function fillPicker()
	choice = current()
	for i, slot in SLOTS do
		local col = slotLists[i]
		for _, c in col:GetChildren() do if c:IsA("TextButton") then c:Destroy() end end
		local ids = {}
		for id, w in Weapons.list do if w.slot == slot then table.insert(ids, id) end end
		table.sort(ids)
		for _, id in ids do
			local w = Weapons.list[id]
			local b = Instance.new("TextButton")
			b.Size = UDim2.new(1, 0, 0, 40); b.FontFace = FONT; b.TextScaled = true; b.Text = w.name; b.BorderSizePixel = 0
			b:SetAttribute("Weapon", id)
			local st = Instance.new("UIStroke"); st.Thickness = 2; st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; st.Color = w.color; st.Parent = b
			b.Activated:Connect(function() choice[i] = id; recolor() end)
			b.Parent = col
		end
	end
	recolor()
end
function U.togglePicker()
	if room() ~= "training" then picker.Visible = false; return end
	picker.Visible = not picker.Visible
	if picker.Visible then fillPicker() end
end
pickBtn.Activated:Connect(U.togglePicker)
okBtn.Activated:Connect(function()
	if U.onLoadout then U.onLoadout(table.clone(choice)) end
	picker.Visible = false
end)
me:GetAttributeChangedSignal("Room"):Connect(function() if room() ~= "training" then picker.Visible = false end end)
function U.pickerOpen(): boolean return picker.Visible end

-- ---------------------------------------------------------------- the vote
local vote = panel(gui, UDim2.new(0.5, -440, 0.5, -170), UDim2.fromOffset(880, 340))
vote.Visible = false
local vTitle = label(vote, "", UDim2.fromOffset(16, 8), UDim2.new(1, -32, 0, 48), YELLOW)
local vTime = label(vote, "", UDim2.new(1, -120, 0, 12), UDim2.fromOffset(100, 36), CYAN)
local cardRow = Instance.new("Frame")
cardRow.BackgroundTransparency = 1; cardRow.Position = UDim2.fromOffset(20, 70); cardRow.Size = UDim2.new(1, -40, 1, -90); cardRow.Parent = vote
local cl = Instance.new("UIListLayout"); cl.FillDirection = Enum.FillDirection.Horizontal; cl.Padding = UDim.new(0, 14)
cl.HorizontalAlignment = Enum.HorizontalAlignment.Center; cl.Parent = cardRow
local cards: { TextButton } = {}
local voteStage = ""
local voteEnds = 0
local myPick = 0

function U.voteStage(stage: string, infos: { any }, ends: number, single: boolean)
	voteStage, voteEnds, myPick = stage, ends, 0
	for _, c in cards do c:Destroy() end
	cards = {}
	vTitle.Text = if stage == "mode" then "VOTE: NEXT MODE" else "VOTE: NEXT MAP"
	if single then vTitle.Text = if stage == "mode" then "NEXT MODE" else "NEXT MAP" end
	for i, c in infos do
		local b = Instance.new("TextButton")
		b.Size = UDim2.new(0, 196, 1, -10); b.BackgroundColor3 = Color3.new(1, 1, 1); b.BorderSizePixel = 0
		b.Rotation = if i % 2 == 0 then 1.5 else -1.5; b.Text = ""; b.AutoButtonColor = true
		local st = Instance.new("UIStroke"); st.Thickness = 4; st.Color = Color3.new(0, 0, 0); st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; st.Parent = b
		local n = label(b, tostring(c.name or c.id), UDim2.fromOffset(8, 10), UDim2.new(1, -16, 0, 56), Color3.new(0, 0, 0))
		n.TextStrokeTransparency = 1
		local d = label(b, tostring(c.desc or ""), UDim2.fromOffset(10, 74), UDim2.new(1, -20, 0, 90), Color3.fromRGB(60, 40, 80))
		d.TextStrokeTransparency = 1; d.TextScaled = false; d.TextSize = 18; d.TextWrapped = true
		if c.event then
			local ev = label(b, "TODAY'S EVENT", UDim2.new(0, 8, 1, -78), UDim2.new(1, -16, 0, 26), PINK)
			ev.TextStrokeTransparency = 1
		end
		local cnt = label(b, "", UDim2.new(0, 8, 1, -44), UDim2.new(1, -16, 0, 36), Color3.new(0, 0, 0))
		cnt.Name = "Count"; cnt.TextStrokeTransparency = 1
		b.Activated:Connect(function() if not single then U.pick(i) end end)
		b.Parent = cardRow
		table.insert(cards, b)
	end
	vote.Visible = true
	vote.Size = UDim2.fromOffset(920, 360)
	TweenService:Create(vote, TweenInfo.new(0.15, Enum.EasingStyle.Back), { Size = UDim2.fromOffset(880, 340) }):Play()
end
-- your vote (a click on a card, or keys 1-4): the card lights up
function U.pick(i: number)
	if voteEnds <= 0 or not cards[i] then return end
	myPick = i
	for j, o in cards do o.BackgroundColor3 = if j == i then YELLOW else Color3.new(1, 1, 1) end
	if U.onVote then U.onVote(voteStage, i) end
end
function U.voteCounts(stage: string, counts: { number })
	if stage ~= voteStage then return end
	for i, c in cards do
		local l = c:FindFirstChild("Count") :: TextLabel?
		if l then l.Text = if (counts[i] or 0) > 0 then ("%d vote%s"):format(counts[i], if counts[i] == 1 then "" else "s") else "" end
	end
end
function U.voteResult(stage: string, win: number, counts: { number })
	U.voteCounts(stage, counts)
	for j, o in cards do
		o.BackgroundColor3 = if j == win then YELLOW else Color3.fromRGB(120, 110, 130)
		if j == win then TweenService:Create(o, TweenInfo.new(0.2, Enum.EasingStyle.Back), { Rotation = -4 }):Play() end
	end
	voteEnds = 0
end
function U.reveal(gameName: string, mapName: string)
	for _, c in cards do c:Destroy() end
	cards = {}
	vTitle.Text = ("%s ON %s"):format(string.upper(gameName), string.upper(mapName))
	vote.Visible = true
	voteEnds = 0
end
function U.voteDone() vote.Visible = false; voteEnds = 0 end
function U.step()
	vTime.Text = if voteEnds > 0 then tostring(math.max(0, math.ceil(voteEnds - workspace:GetServerTimeNow()))) else ""
	local _ = myPick
end

return U
