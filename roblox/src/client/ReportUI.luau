--!strict
-- REPORT a player (server/Reports.luau, docs/ANTI-CHEAT.md "Reports"): a small window with the four reasons. opened
-- from the player card (ProfileUI), the end-of-match board (ReportClient.client) and the party panel's rows (PartyUI):
--   require(script.Parent.ReportUI).open(userId, "card" | "board" | "party")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local me = Players.LocalPlayer

local ReportUI = {}
local REASONS = { { "cheating", "CHEATING" }, { "chat", "ABUSIVE CHAT" }, { "griefing", "GRIEFING" }, { "other", "OTHER" } }
local gui: ScreenGui? = nil

function ReportUI.close()
	if gui then gui:Destroy(); gui = nil end
	MenuCursor.set("report", false)
end

function ReportUI.isOpen(): boolean return gui ~= nil end

function ReportUI.open(userId: number, ctx: string?)
	if type(userId) ~= "number" or userId == me.UserId then return end
	ReportUI.close()
	local remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):FindFirstChild("Report") :: RemoteFunction?
	local g = T.new("ScreenGui", { Name = "ReportDialog", ResetOnSpawn = false, DisplayOrder = 70, IgnoreGuiInset = true, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
	gui = g
	MenuCursor.set("report", true, function() return g.Parent ~= nil end) -- (the mouse is free and shows while it's up)
	local root = T.scaled(g)
	-- (Modal: frees the mouse from first person while this is up)
	local scrim = T.new("TextButton", { Name = "Scrim", Text = "", AutoButtonColor = false, Modal = true, BackgroundColor3 = Color3.new(0, 0, 0),
		BackgroundTransparency = 0.5, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, root)
	scrim.Activated:Connect(ReportUI.close)
	local plate = T.plate(root, "Panel", UDim2.new(0.5, -190, 0.5, -170), UDim2.fromOffset(380, 340))
	plate.BackgroundTransparency = 0.04
	local who = Players:GetPlayerByUserId(userId)
	local title = T.text(plate, "Title", "REPORT " .. string.upper(if who then who.DisplayName else "this player"), 18, T.TEXT, T.FONT_TITLE)
	title.Position = UDim2.fromOffset(20, 16); title.Size = UDim2.fromOffset(340, 24)
	title.TextTruncate = Enum.TextTruncate.AtEnd
	local sub = T.text(plate, "Sub", "Goes to the game's owner with the last 3 minutes of public chat and this match's recording. Roblox's own Report is in the Esc menu.", 12, T.MUTED)
	sub.Position = UDim2.fromOffset(20, 44); sub.Size = UDim2.fromOffset(340, 46)
	sub.TextWrapped = true; sub.TextYAlignment = Enum.TextYAlignment.Top
	local status = T.text(plate, "Status", "", 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center)
	status.Position = UDim2.fromOffset(20, 304); status.Size = UDim2.fromOffset(340, 18)
	local busy = false
	for i, r in REASONS do
		local b = T.new("TextButton", {
			Name = "Reason_" .. r[1], Text = r[2], FontFace = T.FONT_BOLD, TextSize = 14, TextColor3 = T.TEXT, AutoButtonColor = true,
			BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, Position = UDim2.fromOffset(20, 96 + (i - 1) * 42), Size = UDim2.fromOffset(340, 36),
		}, plate)
		T.corner(b, 4)
		b.Activated:Connect(function()
			if busy or not remote then return end
			busy = true
			status.Text = "SENDING"
			local ok, res = pcall(function() return (remote :: RemoteFunction):InvokeServer("send", userId, r[1], ctx or "other") end)
			if gui ~= g then return end
			if ok and type(res) == "table" and res.ok then
				status.Text = if res.again then "ALREADY REPORTED" else "REPORT SENT"
				status.TextColor3 = T.ACCENT
				task.delay(1.4, function() if gui == g then ReportUI.close() end end)
			else
				status.Text = string.upper(tostring(if ok and type(res) == "table" and res.why then res.why else "couldn't send it: try again"))
				status.TextColor3 = T.DANGER
				busy = false
			end
		end)
	end
	local cancel = T.new("TextButton", {
		Name = "Cancel", Text = "CANCEL", FontFace = T.FONT_BOLD, TextSize = 13, TextColor3 = T.MUTED, AutoButtonColor = true,
		BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(20, 266), Size = UDim2.fromOffset(340, 28),
	}, plate)
	T.corner(cancel, 4)
	cancel.Activated:Connect(ReportUI.close)
end

return ReportUI
