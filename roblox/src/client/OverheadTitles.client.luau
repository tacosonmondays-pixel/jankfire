--!strict
-- THE TITLE OVER YOUR HEAD (17 Nov 2026, the owner: "can titles appear above head"): every player's card title (the
-- player card's title, Shared.CardStyles TITLES; the server's Stats publishes the one you wear as CardTitle) shows
-- just under their Roblox name, in the title's rarity colour, in the regulars' nametag style (HubNPCs' label).
--   * "No Title" (id none) shows nothing.
--   * hidden on anyone in a match (Zone == "match"), to keep fights clean: the scoreboard and the cards still have it.
--   * fades out from 45 to 60 studs; your own only shows when your camera is out (third person, menus).
--   * Settings "gfx.titles" (the settings page's SHOW TITLES; nil = on) turns them all off, for you only.
-- light on purpose: one BillboardGui per character, made here on this client and put on that character's Head, like
-- the regulars' nametags (nothing replicates), the same make as theirs (sized in studs, not always on top); one loop
-- every 0.1 s for the distance fade and the hiding rules.
-- Studio tests: a Model in the Workspace with the attribute TitleStandIn = true and its own CardTitle / Zone is shown
-- like a player (a copy of you, for a photo).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CardStyles = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("CardStyles")) :: any
local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local NEAR, FAR = 45, 60
local FONT = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)

-- the settings page's switch (the settings session's Settings module: get / watch), looked up once
local SettingsMod: any = nil
local function settings(): any
	if SettingsMod == nil then
		local m = script.Parent:FindFirstChild("Settings")
		local ok, res = false, nil
		if m and m:IsA("ModuleScript") then ok, res = pcall(require, m) end
		SettingsMod = if ok and type(res) == "table" and type(res.get) == "function" then res else false
	end
	return if SettingsMod then SettingsMod else nil
end
local function shown(): boolean
	local S = settings()
	if not S then return true end
	local ok, v = pcall(S.get, "gfx.titles")
	return not (ok and v == false)
end

-- (where a Billboard waits while its character has no head yet)
local folder = Instance.new("Folder")
folder.Name = "JankTitles"
folder.Parent = pg

-- p: the Player, or a Studio stand-in Model (both answer GetAttribute; charOf gives the body)
type Tag = { bb: BillboardGui, label: TextLabel, head: BasePart?, p: any, id: string }
local tags: { [any]: Tag } = {}
local function charOf(p: any): Model?
	return if typeof(p) == "Instance" and p:IsA("Player") then p.Character else p
end

local function make(p: any): Tag
	local bb = Instance.new("BillboardGui")
	bb.Name = "Title_" .. p.Name
	-- (the regulars' nametag's own make: sized in studs, the words scaled to fit. an AlwaysOnTop one didn't draw at
	-- all in a Play test, so it isn't; just under Roblox's own name, which sits about this high over the head)
	bb.Size = UDim2.new(7, 0, 0.55, 0)
	bb.StudsOffsetWorldSpace = Vector3.new(0, 2.05, 0)
	bb.LightInfluence = 0
	bb.AlwaysOnTop = false
	bb.MaxDistance = FAR + 2
	bb.ResetOnSpawn = false
	bb.Archivable = false -- (copies of a body, the equip screen's stand-in, replays, leave it behind)
	bb.Enabled = false
	local t = Instance.new("TextLabel")
	t.Name = "Title"
	t.BackgroundTransparency = 1
	t.Size = UDim2.fromScale(1, 1)
	t.FontFace = FONT
	t.TextScaled = true
	t.TextStrokeTransparency = 0.55
	t.TextStrokeColor3 = Color3.fromRGB(10, 12, 16)
	t.Text = ""
	local cap = Instance.new("UITextSizeConstraint")
	cap.MaxTextSize = 22
	cap.Parent = t
	t.Parent = bb
	bb.Parent = folder
	return { bb = bb, label = t, head = nil, p = p, id = "" }
end
local function rebuild(g: Tag)
	-- (the old one went with its head: a new one, the same in every way)
	local n = make(g.p)
	g.bb, g.label = n.bb, n.label
end

local function refresh(g: Tag)
	local id = g.p:GetAttribute("CardTitle")
	id = if type(id) == "string" then id else "none"
	g.id = id
	local i = CardStyles.info("title", id)
	local words = if i and type(i.text) == "string" then i.text else ""
	g.label.Text = words
	g.label.TextColor3 = (i and CardStyles.RARITY_COLOR[i.rarity]) or Color3.fromRGB(236, 240, 242)
	local ch = charOf(g.p)
	local head = ch and ch:FindFirstChild("Head") :: BasePart?
	if not pcall(function() g.bb.Parent = head or folder end) then
		rebuild(g)
		g.label.Text = words
		g.label.TextColor3 = (i and CardStyles.RARITY_COLOR[i.rarity]) or Color3.fromRGB(236, 240, 242)
		g.bb.Parent = head or folder
	end
	g.head = head
	g.bb.Adornee = head
end

local function add(p: Player)
	if tags[p] then return end
	local g = make(p)
	tags[p] = g
	refresh(g)
	p:GetAttributeChangedSignal("CardTitle"):Connect(function() refresh(g) end)
	p.CharacterAdded:Connect(function(ch)
		ch:WaitForChild("Head", 10)
		refresh(g)
	end)
end
for _, p in Players:GetPlayers() do task.spawn(add, p) end
Players.PlayerAdded:Connect(add)
Players.PlayerRemoving:Connect(function(p)
	local g = tags[p]
	tags[p] = nil
	if g then g.bb:Destroy() end
end)
if RunService:IsStudio() then
	local function standIn(m: Instance)
		if not m:IsA("Model") or m:GetAttribute("TitleStandIn") ~= true or tags[m] then return end
		local g = make(m)
		tags[m] = g
		refresh(g)
		m:GetAttributeChangedSignal("CardTitle"):Connect(function() refresh(g) end)
		m.AncestryChanged:Connect(function()
			if not m:IsDescendantOf(workspace) then tags[m] = nil; g.bb:Destroy() end
		end)
	end
	for _, m in workspace:GetChildren() do standIn(m) end
	workspace.ChildAdded:Connect(function(m) task.defer(standIn, m) end)
end

-- the hiding rules and the fade, ten times a second
local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Exclude
local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.1 then return end
	acc = 0
	local cam = workspace.CurrentCamera
	if not cam then return end
	local on = shown()
	local camPos = cam.CFrame.Position
	for p, g in tags do
		local head = g.head
		if head and not head:IsDescendantOf(workspace) then refresh(g); head = g.head end
		-- (a Studio test stands a player in a match with the attribute TitleZoneTest: the server rewrites Zone every 0.15 s)
		local zone = if RunService:IsStudio() and p:GetAttribute("TitleZoneTest") ~= nil then p:GetAttribute("TitleZoneTest") else p:GetAttribute("Zone")
		local show = on and head ~= nil and g.label.Text ~= "" and zone ~= "match"
		local d = if head then (head.Position - camPos).Magnitude else math.huge
		if show and p == me and d < 4 then show = false end -- (your own: not from your own eyes)
		if show and d > FAR then show = false end
		if show and p ~= me and head then
			-- (hidden behind walls: one ray from the camera to the head)
			local ch = charOf(p)
			local mine = me.Character
			ray.FilterDescendantsInstances = if mine then { ch :: Instance, mine } else { ch :: Instance }
			local hit = workspace:Raycast(camPos, head.Position - camPos, ray)
			if hit and hit.Instance and hit.Instance.Transparency < 0.5 and hit.Instance.CanCollide then show = false end
		end
		if g.bb.Enabled ~= show then g.bb.Enabled = show end
		if show then
			local a = math.clamp((d - NEAR) / (FAR - NEAR), 0, 1)
			g.label.TextTransparency = a
			g.label.TextStrokeTransparency = 0.55 + 0.45 * a
		end
	end
end)

-- the switch, live (Settings.watch, when the settings page has it)
task.spawn(function()
	local S = settings()
	if S and type(S.watch) == "function" then pcall(S.watch, "gfx.titles", function() acc = 1 end) end
end)
