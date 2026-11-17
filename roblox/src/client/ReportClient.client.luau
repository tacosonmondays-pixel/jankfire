--!strict
-- REPORT buttons on the end-of-match board (FightHud's JankfireFight.Hud...End.Board rows): one on every row but your
-- own, opening ReportUI (server/Reports.luau). the rows carry no user id, so a row's name (the DisplayName FightHud
-- writes in its Cell2) is matched to a player still in this server; two players with the same name get no button.
-- a row with a UserId attribute uses that instead
local Players = game:GetService("Players")

local T = require(script.Parent:WaitForChild("Theme"))
local ReportUI = require(script.Parent:WaitForChild("ReportUI"))
local me = Players.LocalPlayer

local function uidFor(row: Instance): number?
	local a = row:GetAttribute("UserId")
	if type(a) == "number" then return a end
	local cell = row:FindFirstChild("Cell2")
	local name = if cell and cell:IsA("TextLabel") then cell.Text else nil
	if not name or name == "" then return nil end
	local found: Player? = nil
	for _, p in Players:GetPlayers() do
		if p.DisplayName == name then
			if found then return nil end
			found = p
		end
	end
	return if found then found.UserId else nil
end

local function decorate(row: Instance)
	if not row:IsA("Frame") or row.Name ~= "Row" or row:FindFirstChild("Report") then return end
	local board = row.Parent
	if not board or board.Name ~= "Board" or not board.Parent or board.Parent.Name ~= "End" then return end
	task.defer(function()
		if not row.Parent then return end
		local uid = uidFor(row)
		if not uid or uid == me.UserId then return end
		local b = T.new("TextButton", {
			Name = "Report", Text = "REPORT", FontFace = T.FONT_BOLD, TextSize = 11, TextColor3 = T.MUTED, AutoButtonColor = true,
			BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 192, 0.5, 0),
			Size = UDim2.fromOffset(62, 22), ZIndex = 8, Modal = true, -- (Modal: the mouse is free while the board is up)
		}, row)
		T.corner(b, 4)
		b.Activated:Connect(function() ReportUI.open(uid, "board") end)
	end)
end

local pg = me:WaitForChild("PlayerGui")
pg.DescendantAdded:Connect(decorate)
for _, d in pg:GetDescendants() do decorate(d) end
