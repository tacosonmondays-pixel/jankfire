--!strict
-- TRADING on this client (docs/TRADING.md): the server's pushes into TradeUI, the trade screens in PadNav's list (a
-- controller moves through them; B backs out), and the Studio test attribute.
-- LocalPlayer attribute TradeTest (Studio): "open" (asks the server for the state and shows a trade if one is open),
-- "history", "close", "closehistory", "request:<userId>", "fake:844x390", "real"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local me = Players.LocalPlayer
local TradeUI = require(script.Parent:WaitForChild("TradeUI")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local Push = Remotes:WaitForChild("TradePush") :: RemoteEvent

Push.OnClientEvent:Connect(function(msg: any) TradeUI.onPush(msg) end)

-- a controller: PadNav keeps the selection inside these while they're up
task.spawn(function()
	local m = script.Parent:WaitForChild("Pad", 10)
	if not m then return end
	local ok, Pad = pcall(require, m)
	if not ok or type(Pad) ~= "table" then return end
	local menus = (Pad :: any).MENUS
	if type(menus) ~= "table" then return end
	menus.trade = { gui = "JankTrade", back = function() TradeUI.backOut() end }
	menus.tradehistory = { gui = "JankTradeHistory", back = function() TradeUI.closeHistory() end }
end)

-- a trade already open when this client starts (a respawn doesn't lose it: the guis don't reset)
task.defer(function()
	local r = Remotes:WaitForChild("Trade", 10)
	if not r then return end
	local ok, st = pcall(function() return (r :: RemoteFunction):InvokeServer("state") end)
	if ok and type(st) == "table" then
		if st.trade then TradeUI.onPush({ t = "trade", view = st.trade }) end
		for _, a in (if type(st.asks) == "table" then st.asks else {}) do TradeUI.onPush({ t = "ask", from = a.from, name = a.name, ends = a.ends }) end
	end
end)

if RunService:IsStudio() then
	me:GetAttributeChangedSignal("TradeTest"):Connect(function()
		local v = me:GetAttribute("TradeTest")
		if type(v) ~= "string" then return end
		me:SetAttribute("TradeTest", nil)
		local cmd, arg = string.match(v, "^(%a+):?(.*)$")
		if cmd == "open" then
			task.spawn(function()
				local r = (Remotes:WaitForChild("Trade") :: RemoteFunction):InvokeServer("state")
				if type(r) == "table" and r.trade then TradeUI.onPush({ t = "trade", view = r.trade }) end
			end)
		elseif cmd == "history" then TradeUI.history()
		elseif cmd == "close" then TradeUI.close()
		elseif cmd == "closehistory" then TradeUI.closeHistory()
		elseif cmd == "request" then TradeUI.request(tonumber(arg) or 0)
		elseif cmd == "fake" then
			local w, h = string.match(arg or "", "^(%d+)x(%d+)$")
			TradeUI.fakeScreen(if w then Vector2.new(tonumber(w) :: number, tonumber(h) :: number) else nil)
		elseif cmd == "real" then TradeUI.fakeScreen(nil)
		end
	end)
end
