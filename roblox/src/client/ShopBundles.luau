-- THE SHOP'S NEWER PARTS (19 Nov 2026). ShopUI.luau reached Roblox's limit for a script's Source set from Studio
-- (200,000 characters), so what came after it lives here; ShopUI.ext() requires this once and hands over its own
-- helpers and tables (C). what's here:
--   pair / unpair   a container's Robux and coin prices side by side, at every count (the owner: "if you have coins the
--                   robux icon disappers for containers": x5 / x10 had no Robux product, so they showed coins only)
--   askCount        INVENTORY's OPEN asks how many first (the owner: "when you open from your inventory before it opens
--                   it should proimpt how many you want to open")
--   rows / tile     BUNDLES in rows by rank (the owner: "I like how they display their bundles I want something similar
--                   but differnt", of another game's shop; ours in our own form)
--   pose            a bundle's hero: your avatar posed with its gun over a backdrop (the owner: "like the backdrop they
--                   have character render in a dynamic pose holding a weapon and then little boxes")
return function(C: any): any
	local UI, S, V, T, Shop, Till, Purse, Money, ShopUI = C.UI, C.S, C.V, C.T, C.Shop, C.Till, C.Purse, C.Money, C.ShopUI
	local card, rarityColor, txt, button, new, itemChip, play, commas = C.card, C.rarityColor, C.txt, C.button, C.new, C.itemChip, C.play, C.commas
	local me, Roster, WeaponModels, GunHats, ROBUX = C.me, C.Roster, C.WeaponModels, C.GunHats, C.ROBUX
	local CS = game:GetService("CollectionService")
	local X = {}

	-- ==================================================================== both prices
	-- in the space BUY had: BUY itself becomes the Robux one (amber, the Robux mark), and beside it the coin one (the coin
	-- icon and the number; greyed while you're short, and then a press opens COINS). on a card and on the inspect panel;
	-- the coin button is made once per parent
	X.coinBtns = setmetatable({}, { __mode = "k" }) :: { [Instance]: any }
	function X.pair(parent: Instance, buy: any, o: any, n: number, coins: number)
		local p, s = buy.face.Position, buy.face.Size
		local half = UDim2.new(s.X.Scale / 2, (s.X.Offset - 8) / 2, s.Y.Scale, s.Y.Offset)
		buy.face.Size = half
		local cb: any = X.coinBtns[parent]
		if not cb or not cb.face.Parent then
			cb = button(parent, "", "dark", half)
			cb.face.Name = "CoinPay"
			cb.face.TextSize = buy.face.TextSize
			-- (the coin icon and the number in one centred row)
			local row = new("Frame", { Name = "Row", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
				Size = UDim2.fromScale(0, 1), AutomaticSize = Enum.AutomaticSize.X }, cb.face)
			new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), VerticalAlignment = Enum.VerticalAlignment.Center,
				HorizontalAlignment = Enum.HorizontalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder }, row)
			local ic = new("CanvasGroup", { Name = "Coin", BackgroundTransparency = 1, Size = UDim2.fromOffset(18, 18), LayoutOrder = 1 }, row)
			cb.drawn = Purse.icon("brass", ic, 18)
			ic.Visible = cb.drawn
			cb.ic = ic
			cb.num = txt(row, "", buy.face.TextSize, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
			cb.num.LayoutOrder = 2; cb.num.AutomaticSize = Enum.AutomaticSize.X; cb.num.Size = UDim2.fromScale(0, 1); cb.num.TextTruncate = Enum.TextTruncate.None
			cb.row = row
			cb.face.MouseButton1Click:Connect(function()
				local id, cost = cb.face:GetAttribute("Offer"), cb.face:GetAttribute("Coins")
				if type(id) ~= "string" or type(cost) ~= "number" then return end
				if Purse.of("brass") >= cost then ShopUI.ask(id, "coins") else ShopUI.tab("coins") end
			end)
			X.coinBtns[parent] = cb
		end
		cb.face.Visible = true
		cb.face.ZIndex = buy.face.ZIndex
		cb.row.ZIndex = buy.face.ZIndex + 1; cb.ic.ZIndex = buy.face.ZIndex + 1; cb.num.ZIndex = buy.face.ZIndex + 1
		cb.face.Size = half
		cb.face.Position = UDim2.new(p.X.Scale + s.X.Scale / 2, p.X.Offset + s.X.Offset / 2 + 4, p.Y.Scale, p.Y.Offset)
		cb.face:SetAttribute("Offer", o.id)
		cb.face:SetAttribute("Coins", coins)
		local can = Purse.of("brass") >= coins
		buy.set(ROBUX .. " " .. commas((o.robux or 0) * n), true)
		cb.set("", can)
		cb.num.Text = if cb.drawn then commas(coins) else Purse.words("brass", coins)
		cb.num.TextColor3 = if can then T.TEXT else T.DIM
		cb.ic.GroupTransparency = if can then 0 else 0.55
	end
	-- (the inspect panel, showing something else: its coin button goes)
	function X.unpair(parent: Instance)
		local cb = X.coinBtns[parent]
		if cb then cb.face.Visible = false end
	end

	-- ==================================================================== how many, from INVENTORY
	-- 1 to 10 at a go (the loot server's most): 1 / 5 / 10 / ALL where you have that many, - and + to step, OPEN and
	-- CANCEL. the last count is remembered (Settings "loot.openN"). one in stock: it just opens. a pad: the D-pad moves
	-- between them, A presses, B cancels (PadNav: ShopUI.unpanel). the shop's one extra panel (Money.panel), in its own
	-- "count" mode
	X.count, X.countId = 1, nil :: string?
	local function settings(): any
		local m = script.Parent:FindFirstChild("Settings")
		if not (m and m:IsA("ModuleScript")) then return nil end
		local ok, s = pcall(require, m)
		return if ok and type(s) == "table" and type(s.get) == "function" then s else nil
	end
	function X.paintCount()
		local cid = X.countId
		if not cid or not UI.pCount then return end
		local most = math.max(1, math.min(Till.count(cid), 10))
		X.count = math.clamp(X.count, 1, most)
		UI.pNum.Text = tostring(X.count)
		UI.pMinus.set("-", X.count > 1)
		UI.pPlus.set("+", X.count < most)
		for _, it in UI.pChips do
			local on = it.n == X.count
			it.btn.mark.Visible = on
			it.btn.base = if on then T.CARD_HI else T.CARD
			it.btn.face.BackgroundColor3 = it.btn.base
		end
		UI.pYes.set("OPEN  x" .. X.count, true)
	end
	function X.askCount(cid: string)
		local o = Shop.offer(cid)
		local have = Till.count(cid)
		if not o or o.type ~= "container" or have <= 0 or S.busy then return end
		if have == 1 then ShopUI.openBox(cid, 1); return end
		local most = math.min(have, 10)
		if not UI.pCount then
			UI.pCount = new("Frame", { Name = "HowMany", BackgroundTransparency = 1, Position = UDim2.fromOffset(22, 96), Size = UDim2.new(1, -44, 0, 150), Visible = false, ZIndex = 46 }, UI.panel)
			UI.pChipRow = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 52), ZIndex = 46 }, UI.pCount)
			new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), HorizontalAlignment = Enum.HorizontalAlignment.Center,
				SortOrder = Enum.SortOrder.LayoutOrder }, UI.pChipRow)
			local step = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 70), Size = UDim2.new(1, 0, 0, 64), ZIndex = 46 }, UI.pCount)
			UI.pMinus = button(step, "-", "dark", UDim2.fromOffset(64, 64), UDim2.new(0.5, -150, 0, 0))
			UI.pPlus = button(step, "+", "dark", UDim2.fromOffset(64, 64), UDim2.new(0.5, 86, 0, 0))
			for _, b in { UI.pMinus, UI.pPlus } do b.face.ZIndex = 47; b.face.TextSize = 30 end
			UI.pNum = txt(step, "1", 44, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
			UI.pNum.Position = UDim2.new(0.5, -80, 0, 0); UI.pNum.Size = UDim2.fromOffset(160, 64); UI.pNum.ZIndex = 47
			UI.pMinus.face.MouseButton1Click:Connect(function() if X.count > 1 then X.count -= 1; play("click"); X.paintCount() end end)
			UI.pPlus.face.MouseButton1Click:Connect(function() X.count += 1; play("click"); X.paintCount() end)
			UI.pChips = {}
		end
		for _, c in UI.pChipRow:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
		table.clear(UI.pChips)
		local list = {}
		for _, k in { 1, 5, 10 } do if k <= most then table.insert(list, { n = k, word = tostring(k) }) end end
		if most ~= 1 and most ~= 5 and most ~= 10 then table.insert(list, { n = most, word = "ALL  " .. most }) end
		for i, it in list do
			local b = button(UI.pChipRow, it.word, "dark", UDim2.fromOffset(if #it.word > 2 then 112 else 84, 52))
			b.face.LayoutOrder = i; b.face.ZIndex = 47; b.face.TextSize = 18; b.mark.ZIndex = 48
			b.face.MouseButton1Click:Connect(function() X.count = it.n; play("click"); X.paintCount() end)
			table.insert(UI.pChips, { n = it.n, btn = b })
		end
		Money.mode = "count"
		X.countId = cid
		local set = settings()
		X.count = math.clamp(math.floor(tonumber(set and set.get("loot.openN")) or 1), 1, most)
		Money.panel("OPEN " .. string.upper(o.name) .. "S", ("you have %d. up to 10 at a go"):format(have), Vector2.new(170, 190), false)
		UI.pList.Visible = false
		UI.pCount.Visible = true
		UI.panel.Size = UDim2.fromOffset(math.min((S.W or 1280) - 24, 520), 330)
		Money.onYes = function()
			local n = X.count
			local s2 = settings()
			if s2 and type(s2.set) == "function" then pcall(s2.set, "loot.openN", n) end
			Money.unpanel()
			ShopUI.openBox(cid, n)
		end
		X.paintCount()
	end
	-- (Studio tests, ShopTest "countn:<n>" / "countn:go": the panel's count, and its OPEN)
	function X.countTest(v: string?)
		if Money.mode ~= "count" then return end
		if v == "go" then if Money.onYes then Money.onYes() end; return end
		local k = tonumber(v)
		if k then X.count = math.floor(k); X.paintCount() end
	end

	-- ==================================================================== the bundle's hero, posed
	-- YOUR avatar, caught mid-stride on its own run animation, holding the bundle's gun the way the game holds it in third
	-- person: ThirdPerson poses any body tagged TPRig (TPWeapon, Skin, TP = pitch / yaw degrees / 1 = aiming), both hands
	-- from the hold table. no angle set by hand. once it has settled it's frozen into a statue: every part anchored where
	-- it stands, the joints, the Animator and the tag gone (nothing to do a frame), the gun copied first (ThirdPerson takes
	-- its own away) and dressed in the bundle's wrap and hat. one statue per bundle, kept while your body is the same
	-- (X.statues). no body (dead, loading) or no gun: the guns' own picture stays. X.POSE: the numbers to tune
	X.POSE = { pose = "sprint", pitch = 0, phase = 0.32, camYaw = 70, low = 0.06, fov = 24, settle = 0.9, wideH = 1.06, cardH = 0.78, cardUp = 0.12 }
	-- (19 Nov, the owner via main: "more dynamic": the legs and hips from one mid-stride frame of a real run / sprint clip
	-- in the vault (Mixamo, mixamo-19nov), chosen by the widest stride: scratchpad run_frames.py, the same mapping as
	-- tools/blender/mixamo_r15.py. a joint's Transform each, x y z then the rotation's 9; the arms, the waist and the
	-- head are ThirdPerson's (the hold). R15 bodies only: an R6 body keeps its own run, held. compared in Studio on
	-- BUNDLES: the sprint at a 70-degree camera read best, the gun side-on toward the viewer)
	X.POSES = {
		run_lean = { -- (01_run_lean_style100.fbx, frame 7)
			LowerTorso = { 0, -0.0238, 0, 0.98754, 0.03734, -0.1529, -0.01046, 0.98488, 0.17292, 0.15704, -0.16917, 0.973 },
			UpperTorso = { 0, 0, 0, 0.67851, -0.40023, 0.61599, 0.05977, 0.86585, 0.49673, -0.73216, -0.30021, 0.61141 },
			Head = { 0, 0, 0, 0.77056, 0.34353, -0.53687, -0.33174, 0.9354, 0.1224, 0.54423, 0.08379, 0.83474 },
			LeftUpperArm = { 0, 0, 0, 0.92876, 0.37066, -0.0045, -0.14856, 0.3833, 0.9116, 0.33962, -0.84598, 0.41106 },
			LeftLowerArm = { 0, 0, 0, 1, 0, 0, 0, 0.8225, -0.56877, 0, 0.56877, 0.8225 },
			LeftHand = { 0, 0, 0, 0.93167, -0.34052, 0.12666, 0.32406, 0.9365, 0.13401, -0.16425, -0.0838, 0.98285 },
			RightUpperArm = { 0, 0, 0, -0.37687, -0.72071, 0.58185, 0.80783, -0.56308, -0.17422, 0.45319, 0.40438, 0.79442 },
			RightLowerArm = { 0, 0, 0, 1, 0, 0, 0, 0.94615, -0.32374, 0, 0.32374, 0.94615 },
			RightHand = { 0, 0, 0, 0.32691, -0.49841, -0.80294, -0.05702, 0.83767, -0.54319, 0.94333, 0.22336, 0.24543 },
			LeftUpperLeg = { 0, 0, 0, 0.95342, 0.22496, -0.20096, -0.27637, 0.38452, -0.88077, -0.12086, 0.89529, 0.42878 },
			LeftLowerLeg = { 0, 0, 0, 0.98615, -0.1255, 0.10848, 0.0864, 0.94682, 0.30994, -0.14161, -0.29628, 0.94455 },
			LeftFoot = { 0, 0, 0, 0.90179, -0.43124, -0.02835, 0.23828, 0.44141, 0.86509, -0.36055, -0.78688, 0.50082 },
			RightUpperLeg = { 0, 0, 0, 0.99587, -0.05326, -0.07358, 0.06851, 0.97229, 0.22351, 0.05964, -0.22763, 0.97192 },
			RightLowerLeg = { 0, 0, 0, 0.98793, -0.09771, 0.12017, -0.08946, 0.27331, 0.95776, -0.12643, -0.95695, 0.26127 },
			RightFoot = { 0, 0, 0, 0.9537, 0.28365, 0.09996, -0.27167, 0.66996, 0.69091, 0.12901, -0.68607, 0.716 },
		},
		sprint = { -- (02_sprint_standard.fbx, frame 13)
			LowerTorso = { 0, -0.188, 0, 0.9818, -0.09077, -0.16679, 0.13619, 0.9487, 0.28535, 0.13234, -0.30287, 0.9438 },
			UpperTorso = { 0, 0, 0, 0.91281, 0.40452, -0.05605, -0.29707, 0.7519, 0.58856, 0.28022, -0.52059, 0.80651 },
			Head = { 0, 0, 0, 0.89907, -0.09166, 0.4281, 0.32745, 0.78983, -0.5186, -0.29059, 0.60644, 0.74013 },
			LeftUpperArm = { 0, 0, 0, 0.82091, 0.02638, -0.57044, -0.10903, 0.9878, -0.11122, 0.56055, 0.1535, 0.81377 },
			LeftLowerArm = { 0, 0, 0, 0.9999, 0.01312, -0.00434, -0.00511, 0.05931, -0.99823, -0.01284, 0.99815, 0.05937 },
			LeftHand = { 0, 0, 0, 0.92344, 0.36138, -0.12912, -0.37939, 0.91029, -0.16563, 0.05768, 0.20194, 0.9777 },
			RightUpperArm = { 0, 0, 0, 0.89095, -0.30265, 0.33854, 0.33367, 0.942, -0.03599, -0.30801, 0.14503, 0.94026 },
			RightLowerArm = { 0, 0, 0, 0.97051, -0.22041, -0.09762, -0.07692, 0.10065, -0.99194, 0.22846, 0.9702, 0.08073 },
			RightHand = { 0, 0, 0, 0.93883, 0.10963, 0.32646, 0.17838, 0.65609, -0.7333, -0.29457, 0.74668, 0.5964 },
			LeftUpperLeg = { 0, 0, 0, 0.92153, 0.1386, 0.36273, -0.18074, 0.97987, 0.08476, -0.34368, -0.14367, 0.92803 },
			LeftLowerLeg = { 0, 0, 0, 0.98776, 0.02305, -0.15426, 0.12578, 0.46712, 0.8752, 0.09223, -0.88389, 0.45851 },
			LeftFoot = { 0, 0, 0, 0.94999, 0.12657, 0.28549, -0.16898, 0.97713, 0.12906, -0.26263, -0.17085, 0.94965 },
			RightUpperLeg = { 0, 0, 0, 0.97287, 0.22917, -0.03186, -0.15943, 0.5642, -0.8101, -0.16768, 0.7932, 0.58543 },
			RightLowerLeg = { 0, 0, 0, 0.9916, 0.0245, 0.127, -0.0613, 0.95365, 0.29462, -0.1139, -0.29993, 0.94714 },
			RightFoot = { 0, 0, 0, 0.99454, -0.01253, -0.1036, 0.01625, 0.99925, 0.03517, 0.10308, -0.03666, 0.994 },
		},
		bow_lean = { -- (03_sprint_bow_lean.fbx, frame 13)
			LowerTorso = { 0, -0.3103, 0, 0.8207, 0.14585, -0.55243, 0.27015, 0.75292, 0.60012, 0.50346, -0.64175, 0.57852 },
			UpperTorso = { 0, 0, 0, 0.90624, -0.06005, -0.41847, 0.34498, 0.67722, 0.64989, 0.24437, -0.73332, 0.63444 },
			Head = { 0, 0, 0, 0.6851, 0.61295, 0.3936, 0.33274, 0.21733, -0.91763, -0.64801, 0.75964, -0.05506 },
			LeftUpperArm = { 0, 0, 0, 0.4664, 0.88456, -0.00392, -0.38566, 0.19935, -0.90085, -0.79608, 0.42167, 0.43412 },
			LeftLowerArm = { 0, 0, 0, 0.79808, 0.07632, -0.5977, -0.44316, 0.74645, -0.49641, 0.40826, 0.66105, 0.62955 },
			LeftHand = { 0, 0, 0, 0.92447, 0.16111, 0.34555, -0.15263, 0.98692, -0.05182, -0.34938, -0.00483, 0.93697 },
			RightUpperArm = { 0, 0, 0, 0.84029, -0.23812, 0.48704, 0.35323, 0.92198, -0.15867, -0.41126, 0.30537, 0.85885 },
			RightLowerArm = { 0, 0, 0, 0.99864, -0.02249, 0.04701, 0.05163, 0.3044, -0.95114, 0.00708, 0.95228, 0.30515 },
			RightHand = { 0, 0, 0, 0.9592, -0.28122, 0.0291, 0.28142, 0.93985, -0.19362, 0.0271, 0.19391, 0.98064 },
			LeftUpperLeg = { 0, 0, 0, 0.91385, 0.02815, 0.40507, 0.11889, 0.93532, -0.33322, -0.38825, 0.35268, 0.8514 },
			LeftLowerLeg = { 0, 0, 0, 0.95638, -0.23906, 0.16788, -0.01501, 0.53374, 0.84552, -0.29173, -0.81116, 0.50687 },
			LeftFoot = { 0, 0, 0, 0.99634, -0.064, -0.0566, 0.08285, 0.88554, 0.45712, 0.02086, -0.46014, 0.8876 },
			RightUpperLeg = { 0, 0, 0, 0.93941, 0.28582, -0.18927, -0.23002, 0.1162, -0.96622, -0.25418, 0.95121, 0.17491 },
			RightLowerLeg = { 0, 0, 0, 0.96061, 0.18334, 0.20884, -0.27316, 0.76113, 0.58827, -0.0511, -0.62215, 0.78123 },
			RightFoot = { 0, 0, 0, 0.99708, 0.07624, -0.00346, -0.07428, 0.95911, -0.27311, -0.0175, 0.27257, 0.96198 },
		},
		ninja = { -- (05_ninja_run.fbx, frame 14)
			LowerTorso = { 0, -0.4124, 0, 0.98783, -0.08523, 0.13009, -0.0344, 0.696, 0.71721, -0.15167, -0.71296, 0.6846 },
			UpperTorso = { 0, 0, 0, 0.94491, 0.23584, -0.227, -0.12221, 0.8975, 0.42373, 0.30367, -0.37265, 0.87688 },
			Head = { 0, 0, 0, 0.99107, 0.03253, 0.1293, 0.0897, 0.55478, -0.82715, -0.09864, 0.83136, 0.54691 },
			LeftUpperArm = { 0, 0, 0, 0.80566, 0.45867, -0.37487, -0.31644, 0.86821, 0.38221, 0.50077, -0.18931, 0.84462 },
			LeftLowerArm = { 0, 0, 0, 0.96155, -0.13354, 0.23997, 0.24597, 0.80738, -0.53631, -0.12213, 0.57472, 0.80919 },
			LeftHand = { 0, 0, 0, 0.93519, -0.35413, 0.00403, 0.35166, 0.92989, 0.10789, -0.04196, -0.09948, 0.99415 },
			RightUpperArm = { 0, 0, 0, 0.87663, -0.47434, 0.0807, 0.42348, 0.84024, 0.33862, -0.22843, -0.26267, 0.93745 },
			RightLowerArm = { 0, 0, 0, 0.95519, 0.28242, 0.08865, -0.19931, 0.83507, -0.51277, -0.21885, 0.47212, 0.85394 },
			RightHand = { 0, 0, 0, 0.89171, 0.44778, 0.06595, -0.4366, 0.81258, 0.38613, 0.11931, -0.37311, 0.92008 },
			LeftUpperLeg = { 0, 0, 0, 0.99809, -0.0222, 0.05762, 0.03874, 0.95177, -0.30436, -0.04809, 0.30601, 0.95081 },
			LeftLowerLeg = { 0, 0, 0, 0.99332, 0.05972, -0.09871, -0.00981, 0.89623, 0.44347, 0.11495, -0.43954, 0.89084 },
			LeftFoot = { 0, 0, 0, 0.99968, -0.02531, -0.00286, 0.02466, 0.93415, 0.35602, -0.00634, -0.35597, 0.93447 },
			RightUpperLeg = { 0, 0, 0, 0.96762, -0.17337, 0.18347, 0.09364, -0.42846, -0.8987, 0.23442, 0.88677, -0.39835 },
			RightLowerLeg = { 0, 0, 0, 0.93299, 0.21252, -0.29047, 0.08688, 0.65022, 0.75476, 0.34927, -0.72942, 0.58818 },
			RightFoot = { 0, 0, 0, 0.98729, 0.14846, -0.05666, -0.08279, 0.78492, 0.61404, 0.13564, -0.60155, 0.78724 },
		},
	}
	X.statues = {} :: { [string]: any }
	local function statueCam(cam: Camera, m: Model, wide: boolean)
		local P = X.POSE
		local cf, size = m:GetBoundingBox()
		local f = m:GetAttribute("Facing")
		local fv: Vector3 = if typeof(f) == "Vector3" then f else Vector3.new(0, 0, -1)
		local a = math.rad(P.camYaw)
		local dir = Vector3.new(fv.X * math.cos(a) - fv.Z * math.sin(a), 0, fv.X * math.sin(a) + fv.Z * math.cos(a))
		dir = if dir.Magnitude > 1e-3 then dir.Unit else Vector3.new(0, 0, -1)
		local hgt = size.Y
		local frameH = hgt * (if wide then P.wideH else P.cardH)
		local focus = cf.Position + Vector3.new(0, if wide then 0 else hgt * P.cardUp, 0)
		local dist = (frameH / 2) / math.tan(math.rad(P.fov / 2))
		cam.FieldOfView = P.fov
		cam.CFrame = CFrame.lookAt(focus + dir * dist - Vector3.new(0, hgt * P.low, 0), focus)
	end
	X.statueCam = statueCam
	local function unjoint(root: Instance)
		for _, d in root:GetDescendants() do
			if d:IsA("JointInstance") or d:IsA("Constraint") or d:IsA("WeldConstraint") then d:Destroy() end
		end
	end
	-- (yields: builds the statue in wm and returns it, or nil)
	function X.makeStatue(ch: Model, o: any, wm: Instance): Model?
		local h = o.hero or {}
		local wid = h.weapon
		local was = ch.Archivable
		ch.Archivable = true
		local okC, rig = pcall(function() return ch:Clone() end)
		ch.Archivable = was
		if not okC or not rig then return nil end
		-- (nothing of the player's runs or shows in it: scripts, the gun in their hands, tools, name tags, sounds)
		for _, d in rig:GetDescendants() do
			if d:IsA("LuaSourceContainer") or d:IsA("Tool") or d:IsA("ForceField") or d:IsA("BillboardGui") or d:IsA("Sound")
				or d.Name == "HeldWeapon" or d.Name == "TPGun" or d.Name == "TPGun2" or d.Name == "TPRigArms" then d:Destroy() end
		end
		for k in rig:GetAttributes() do rig:SetAttribute(k, nil) end
		rig.Name = "ShopPose"
		local hum = rig:FindFirstChildOfClass("Humanoid")
		local root = rig:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root then rig:Destroy(); return nil end
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.RequiresNeck = false
		hum.BreakJointsOnDeath = false
		root.Anchored = true
		rig:PivotTo(CFrame.new())
		rig:SetAttribute("Facing", root.CFrame.LookVector)
		rig.Parent = wm
		-- the stride: a real run's frame (X.POSES) on an R15 body; else its own run (its animation pack's), held
		local an = hum:FindFirstChildOfClass("Animator")
		local pz = X.POSES[X.POSE.pose]
		if pz and hum.RigType == Enum.HumanoidRigType.R15 then
			if an then an:Destroy(); an = nil end -- (nothing else writes the legs: the frame stays)
			for _, j in rig:GetDescendants() do
				local p1 = if j:IsA("Motor6D") then j.Part1 elseif j:IsA("AnimationConstraint") and j.Attachment1 then j.Attachment1.Parent else nil
				local v = p1 and pz[p1.Name]
				if v then (j :: any).Transform = CFrame.new(table.unpack(v)) end
			end
		end
		local live = ch:FindFirstChild("Animate")
		local runF = live and live:FindFirstChild("run")
		local a0 = runF and runF:FindFirstChildOfClass("Animation")
		local id = if a0 and a0.AnimationId ~= "" then a0.AnimationId
			elseif hum.RigType == Enum.HumanoidRigType.R6 then "rbxassetid://180426354" else "rbxassetid://913376220"
		if an then -- (no real-run frame for this body: its own run, held)
			local anim = Instance.new("Animation")
			anim.AnimationId = id
			local okT, track = pcall(function() return an:LoadAnimation(anim) end)
			if okT and track then
				track:Play(0, 1, 0)
				local t0 = os.clock()
				while track.Length <= 0 and os.clock() - t0 < 2 do task.wait() end
				if track.Length > 0 then track.TimePosition = track.Length * X.POSE.phase end
				track:AdjustSpeed(0)
			end
		end
		-- the hold: ThirdPerson's, as it holds the gun on any body
		if type(h.skin) == "string" then rig:SetAttribute("Skin", h.skin) end
		rig:SetAttribute("TP", Vector3.new(X.POSE.pitch, 0, 1))
		rig:SetAttribute("TPWeapon", wid)
		CS:AddTag(rig, "TPRig")
		local t0 = os.clock()
		while os.clock() - t0 < 4 do
			task.wait()
			if not rig.Parent then return nil end
			if rig:FindFirstChild("TPGun") and os.clock() - t0 > X.POSE.settle then break end
		end
		local gun = rig:FindFirstChild("TPGun")
		if not gun then CS:RemoveTag(rig, "TPRig"); rig:Destroy(); return nil end
		-- frozen
		local keep = gun:Clone()
		local at = {}
		for _, d in rig:GetDescendants() do if d:IsA("BasePart") then at[d] = d.CFrame end end
		CS:RemoveTag(rig, "TPRig")
		rig:SetAttribute("TPWeapon", nil)
		rig:SetAttribute("TP", nil)
		if an then an:Destroy() end
		task.wait(); task.wait() -- (ThirdPerson lets go: its own gun goes)
		if not rig.Parent then return nil end
		unjoint(rig)
		for p, cf in at do if p.Parent then p.Anchored = true; p.CFrame = cf end end
		for _, d in keep:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true end end
		unjoint(keep)
		keep.Name = "Gun"
		if type(h.wrap) == "string" and h.wrap ~= "default" then pcall(WeaponModels.wrap, keep, h.wrap, "full") end
		if type(h.hat) == "string" and h.hat ~= "none" then
			local k = keep:GetAttribute("K")
			pcall(GunHats.attach, keep, wid, h.hat, if type(k) == "number" then k else 3, true, GunHats.THIRD)
		end
		keep.Parent = rig
		return rig
	end
	-- (Studio tests: the player attribute ShopPoseTest = JSON merged into X.POSE, e.g. {"pose":"sprint","camYaw":75};
	-- the statues are made again and BUNDLES redrawn)
	if game:GetService("RunService"):IsStudio() then
		me:GetAttributeChangedSignal("ShopPoseTest"):Connect(function()
			local okJ, v = pcall(function() return game:GetService("HttpService"):JSONDecode(me:GetAttribute("ShopPoseTest")) end)
			if not okJ or type(v) ~= "table" then return end
			for k2, x in v do X.POSE[k2] = x end
			X.statues = {}
			if S.open and S.tab == "bundles" then ShopUI.fillBundles() end
		end)
	end
	-- a bundle's statue in the stage frame; done(true) once it stands, done(false) if it can't be made
	function X.pose(stage: GuiObject, o: any, wide: boolean, done: (boolean) -> ())
		local ch = me.Character
		local wid = (o.hero or {}).weapon
		if not ch or type(wid) ~= "string" or not Roster.byId[wid] or not ch:FindFirstChild("HumanoidRootPart") then done(false); return end
		local vp = new("ViewportFrame", { Name = "Posed", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = stage.ZIndex + 1,
			Ambient = Color3.fromRGB(150, 153, 162), LightColor = Color3.fromRGB(255, 248, 240), LightDirection = Vector3.new(-0.6, -0.9, -0.4) }, stage)
		local cam = new("Camera", { FieldOfView = X.POSE.fov }, vp)
		vp.CurrentCamera = cam
		local wm = Instance.new("WorldModel")
		wm.Parent = vp
		local c = X.statues[o.id]
		if c and c.ch == ch and c.model then
			local m = c.model:Clone()
			m.Parent = wm
			statueCam(cam, m, wide)
			done(true)
			return
		end
		task.spawn(function()
			local ok, m = pcall(X.makeStatue, ch, o, wm)
			if ok and m and vp.Parent then
				X.statues[o.id] = { ch = ch, model = m:Clone() }
				statueCam(cam, m, wide)
				done(true)
			else
				if not ok then warn("[jankfire] shop: a bundle's pose: " .. tostring(m)) end
				if vp.Parent then vp:Destroy() end
				done(false)
			end
		end)
	end

	-- ==================================================================== BUNDLES, by rank
	-- size says rank (the featured one the full width, then rows of two and three, a lone last one the full width again;
	-- a phone: twos). each card: the backdrop (a faint wash of the bundle's rarity colour, a pale slab leaning across,
	-- three speed streaks), your avatar posed with its gun over it (X.pose; till then, or without one, the guns), every
	-- thing in it as a chip along the foot (ALL on a wrap that's every gun's, "+N" past what fits), the price with what
	-- it saves next to it (one line, never the button's amber), OWNED quietly in the price's place, the card where it was.
	-- click: the inspect panel; the price: the confirm with every item pictured
	local function bundleSave(o: any): number?
		-- (what it saves on its things bought one by one: in coins when coins buy it, else in Robux)
		local c = Purse.coins(o)
		if c then
			local sep = 0
			for _, it in Shop.contents(o) do
				local _, r = Shop.itemInfo(it.kind, it.id)
				local p = Shop.coinPrice({ type = "single", kind = it.kind, rarity = r })
				if not p then return nil end
				sep += p
			end
			return if sep > 0 then 1 - c / sep else nil
		end
		local w = Shop.worth(o)
		return if w > 0 and (o.robux or 0) > 0 then 1 - o.robux / w else nil
	end
	function X.tile(parent: Instance, o: any, x: number, y: number, w: number, h: number, wide: boolean, featured: boolean): TextButton
		local k = S.compact
		local c = card(parent, nil)
		c.Name = "Bundle_" .. o.id
		c.Position = UDim2.fromOffset(x, y); c.Size = UDim2.fromOffset(w, h)
		local pad = if k then 12 else 18
		local col = rarityColor(o.rarity)
		-- the backdrop: the wash from the corner the hero stands in, a pale slab leaning across, three speed streaks
		local tint = new("Frame", { Name = "Tint", BackgroundColor3 = col, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 0 }, c)
		T.corner(tint)
		new("UIGradient", { Rotation = if wide then 0 else -30, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.42, 0.95), NumberSequenceKeypoint.new(1, 0.78) }) }, tint)
		local slab = new("Frame", { Name = "Slab", BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.25, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(if wide then 0.74 else 0.7, 0, 0.5, 0), Size = UDim2.new(if wide then 0.3 else 0.44, 0, 2.2, 0), Rotation = 16, ZIndex = 0 }, c)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7), NumberSequenceKeypoint.new(0.5, 0),
			NumberSequenceKeypoint.new(1, 0.7) }) }, slab)
		for si, sl in { { 0.3, 0.34 }, { 0.44, 0.22 }, { 0.56, 0.28 } } do
			local streak = new("Frame", { Name = "Streak", BackgroundColor3 = T.TEXT, BackgroundTransparency = 0.8, BorderSizePixel = 0, ZIndex = 1,
				Position = UDim2.new(if wide then 0.46 else 0.32, 0, sl[1], 0), Size = UDim2.new(sl[2], 0, 0, if si == 2 then 3 else 2) }, c)
			new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.35, 0.1),
				NumberSequenceKeypoint.new(1, 1) }) }, streak)
		end
		-- the guns (big, running off the right edge: the card clips them), shown till the posed hero stands in for them
		local view = new("Frame", { Name = "View", BackgroundTransparency = 1, ZIndex = 1,
			Position = if wide then UDim2.new(0.38, 0, 0, -8) else UDim2.new(0.14, 0, 0, if k then 24 else 34),
			Size = if wide then UDim2.new(0.74, 0, 1, 16) else UDim2.new(1, 0, 1, -(if k then 96 else 118)) }, c)
		V.put(view, o, nil, "hover", if wide then 1.28 else 1.22)
		local stage = new("Frame", { Name = "Stage", BackgroundTransparency = 1, ZIndex = 2,
			Position = if wide then UDim2.new(0.42, 0, 0, -4) else UDim2.new(0.3, 0, 0, 4),
			Size = if wide then UDim2.new(0.62, 0, 1, 8) else UDim2.new(0.74, 0, 1, -(if k then 56 else 64)) }, c)
		X.pose(stage, o, wide, function(ok) if view.Parent then view.Visible = not ok end end)
		-- the words, top left
		local items = Shop.contents(o)
		local every = 0
		for _, it in items do if it.kind == "wrap" and it.every then every += 1 end end
		local head = if featured then string.format('<font color="%s">FEATURED</font>', T.hex(T.ACCENT))
			else string.format('<font color="%s">%s</font>', T.hex(col), string.upper(o.rarity or ""))
		local eb = txt(c, head .. "  ·  " .. #items .. " ITEMS" .. (if every > 0 and not k then "  ·  " .. every .. " FOR EVERY GUN" else ""), 11, T.MUTED, T.FONT_BOLD)
		eb.RichText = true; eb.ZIndex = 4
		eb.Position = UDim2.fromOffset(pad, if k then 10 else 16); eb.Size = UDim2.new(if wide then 0.5 else 1, -2 * pad, 0, 14)
		local name = txt(c, string.upper(o.name), if wide then (if k then 24 else 34) else (if k then 18 else 22), T.TEXT, T.FONT_TITLE)
		name.ZIndex = 4
		name.Position = UDim2.fromOffset(pad, if k then 26 else 34); name.Size = UDim2.new(if wide then 0.5 else 1, -2 * pad, 0, if wide then (if k then 30 else 40) else 26)
		new("UIStroke", { Thickness = 1, Transparency = 0.6, Color = Color3.new(0, 0, 0), ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, name)
		if wide and not k and type(o.blurb) == "string" then
			local bl = txt(c, o.blurb, 14, T.MUTED); bl.ZIndex = 4
			bl.Position = UDim2.fromOffset(pad, 80); bl.Size = UDim2.new(0.42, 0, 0, 38)
			bl.TextWrapped = true; bl.TextTruncate = Enum.TextTruncate.None; bl.TextYAlignment = Enum.TextYAlignment.Top
		end
		-- the price (bottom right; a wide card: bottom left, under the chips) and what it saves
		local miss = Till.missing(o)
		local ph = if k then 40 else 44
		local pw = if k then 124 else 156
		local buy = button(c, "", "main", UDim2.fromOffset(pw, ph), if wide then UDim2.new(0, pad, 1, -(pad + ph)) else UDim2.new(1, -(pad + pw), 1, -(pad + ph)))
		buy.face.ZIndex = 5
		if miss == 0 then buy.set("OWNED", false)
		elseif Shop.free() then buy.set("CLAIM", true)
		else buy.set(Purse.cost(o), true) end
		buy.face.MouseButton1Click:Connect(function() if miss > 0 then ShopUI.ask(o.id) else ShopUI.inspect(o.id) end end)
		local save = if miss > 0 and not Shop.free() then bundleSave(o) else nil
		if save and save >= 0.05 then
			local sv = new("Frame", { Name = "Save", BackgroundColor3 = T.BG, BackgroundTransparency = 0.1, BorderSizePixel = 0, ZIndex = 5,
				AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 22) }, c)
			T.corner(sv, 4)
			T.edge(sv)
			new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, sv)
			local st = txt(sv, ("SAVE %d%%"):format(math.floor(save * 100 + 0.5)), 12, T.TEXT, T.FONT_BOLD)
			st.AutomaticSize = Enum.AutomaticSize.X; st.Size = UDim2.fromOffset(0, 22); st.ZIndex = 6; st.TextTruncate = Enum.TextTruncate.None
			if wide then sv.Position = UDim2.new(0, pad + pw + 10, 1, -(pad + ph / 2 + 11))
			else sv.AnchorPoint = Vector2.new(1, 0); sv.Position = UDim2.new(1, -pad, 1, -(pad + ph + 28)) end
		end
		-- every thing in it, as chips: along the foot, left of the price (a wide card: over the price). more than fit: "+N"
		local cs = if k then 40 else 46
		local footW = if wide then w * 0.5 - 2 * pad else w - 2 * pad - pw - 10
		local foot = new("Frame", { Name = "Chips", BackgroundTransparency = 1, ZIndex = 4, Size = UDim2.fromOffset(footW, cs),
			Position = if wide then UDim2.new(0, pad, 1, -(pad + ph + 10 + cs)) else UDim2.new(0, pad, 1, -(pad + cs + (ph - cs) / 2)) }, c)
		new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder }, foot)
		local fits = math.max(1, math.floor((footW + 6) / (cs + 6)))
		local show = if #items > fits then fits - 1 else #items
		for i = 1, show do
			local it = items[i]
			itemChip(foot, it, i)
			if it.kind == "wrap" and it.every then
				for _, f in foot:GetChildren() do
					if f:IsA("Frame") and f.LayoutOrder == i then
						local tag = new("TextLabel", { Name = "All", BackgroundColor3 = T.BG, BackgroundTransparency = 0.05, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
							Position = UDim2.new(1, 2, 0, -3), Size = UDim2.fromOffset(24, 13), FontFace = T.FONT_BOLD, TextSize = 9, Text = "ALL",
							TextColor3 = T.SOFT, ZIndex = 9 }, f)
						T.corner(tag, 3)
					end
				end
			end
		end
		if #items > show then
			local more = new("Frame", { BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, Size = UDim2.fromOffset(cs, cs), LayoutOrder = 99, ZIndex = 6 }, foot)
			T.corner(more, 5)
			local ml = txt(more, "+" .. (#items - show), 15, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center); ml.Size = UDim2.fromScale(1, 1); ml.ZIndex = 7
		end
		if miss == 0 then c.BackgroundTransparency = 0.25 end -- (OWNED: a touch quieter, still there)
		c.MouseButton1Click:Connect(function() ShopUI.inspect(o.id) end)
		return c
	end
	-- the grid of them: the first (today's featured) the full width, then twos and threes, a lone last one the full
	-- width; a phone: twos. (rot: Shop.rotation(), whose hero is the featured one)
	function X.rows(list: { any }, rot: any)
		local layout = UI.bundleGrid:FindFirstChildOfClass("UIGridLayout")
		if layout then layout.Parent = nil end
		UI.bundleGrid.AutomaticSize = Enum.AutomaticSize.None
		local bw = (S.bw or 1100) - 12
		local k = S.compact
		local gap = if k then 10 else 14
		local y, i, row = 0, 1, 0
		while i <= #list do
			local left = #list - i + 1
			local take
			if i == 1 then take = 1
			elseif k then take = if left == 1 then 1 else 2
			elseif left <= 3 then take = left
			else
				take = if row % 2 == 1 then 2 else 3
				if left - take == 1 then take = if take == 2 then 3 else 2 end
			end
			local h = if take == 1 then (if k then 210 else 290) elseif take == 2 then (if k then 220 else 300) else 270
			local w = (bw - (take - 1) * gap) / take
			for j = 0, take - 1 do
				local o = list[i + j]
				X.tile(UI.bundleGrid, o, j * (w + gap), y, w, h, take == 1, o.id == rot.hero)
			end
			y += h + gap; i += take; row += 1
		end
		UI.bundleGrid.Size = UDim2.new(1, 0, 0, math.max(0, y - gap))
	end

	-- ==================================================================== CONTAINERS: crates and bags, then the spray sets
	-- (20 Nov 2026, the owner: "the current skins in the case set is case 1, duffel bag set 1, but can you divide the
	-- sprays into different sets?"): the Crate (CASE 1) and the Duffel Bag (SET 1) side by side, then SPRAY SETS three to
	-- a row, every card ShopUI.boxCard's, on one page that scrolls (it keeps its place when filled again). the first Spray
	-- Can isn't sold: it shows in INVENTORY while you have some
	function X.boxes()
		local page = UI.pages.containers
		UI.boxRow.Visible = false
		local sc = page:FindFirstChild("BoxScroll") :: ScrollingFrame?
		if not sc then
			sc = new("ScrollingFrame", { Name = "BoxScroll", BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1),
				CanvasSize = UDim2.new(), ScrollBarThickness = 4, ScrollingDirection = Enum.ScrollingDirection.Y }, page)
		end
		local s = sc :: ScrollingFrame
		for _, c in s:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
		local k = S.compact
		local gap = if k then 10 else 14
		-- (the page's size in the shop's own units: its AbsoluteSize is on screen, after the shop's UIScale)
		local k0 = 1
		local a: Instance? = s.Parent
		while a do
			local u = a:FindFirstChildOfClass("UIScale")
			if u then k0 *= u.Scale end
			a = a.Parent
		end
		local W = (if s.AbsoluteSize.X > 100 then s.AbsoluteSize.X / k0 else (S.bw or 1100)) - 16
		local H = if s.AbsoluteSize.Y > 100 then s.AbsoluteSize.Y / k0 else 520
		local h = math.max(if k then 250 else 420, H - 34) -- (a row fills the page, its heading above it)
		local y = 4 -- (and 4 in from the left: room for a card's lift under the mouse)
		local function head(text: string)
			local l = txt(s, text, 15, T.MUTED, T.FONT_BOLD)
			l.Position = UDim2.fromOffset(4, y); l.Size = UDim2.new(1, -16, 0, 22)
			y += 30
		end
		local function row(list: { any }, per: number)
			local w = (W - (per - 1) * gap) / per
			for i, o in list do
				local col = (i - 1) % per
				if i > 1 and col == 0 then y += h + gap end
				local c = ShopUI.boxCard(s, o, i)
				c.Position = UDim2.fromOffset(4 + col * (w + gap), y); c.Size = UDim2.fromOffset(w, h)
			end
			if #list > 0 then y += h + gap end
		end
		local top, sprays = {}, {}
		for _, o in Shop.containers do
			if not o.legacy then table.insert(if o.spray then sprays else top, o) end
		end
		head("CRATES AND BAGS"); row(top, 2)
		head("SPRAY SETS"); row(sprays, 3)
		s.CanvasSize = UDim2.fromOffset(0, y)
	end

	-- ==================================================================== FEATURED's right column (27 Nov 2026)
	-- the owner's pick from the ui-mocks sheet: the shop home is A PLATE's. the featured set as a tall card, the daily
	-- offers beside it, and on the right CRATES (the Crate, the Duffel Bag, the spray cans) and COINS (the packs) as plain
	-- rows on a bone panel. a crate's prices are its own buttons: tickets, then coins, each greyed with "need N more"
	-- while you're short; a press asks to buy (ShopUI.ask: the odds first). a coin pack's button is its Robux price
	-- (ShopUI.prompt once Robux is on). ShopUI.layout places the column (sidePlace); fillFeatured fills it (sideFill)
	local INK, BONE, LIP = Color3.fromRGB(29, 31, 35), Color3.fromRGB(229, 226, 219), Color3.fromRGB(170, 164, 152)
	function X.sidePlace(w: number, gap: number)
		local page = UI.pages.featured
		local f = page:FindFirstChild("Side") :: Frame?
		if not f then
			f = new("Frame", { Name = "Side", BackgroundTransparency = 1 }, page)
		end
		local side = f :: Frame
		side.Visible = w > 0
		side.AnchorPoint = Vector2.new(1, 0)
		side.Position = UDim2.fromScale(1, 0)
		side.Size = UDim2.new(0, w, 1, 0)
		X.sideGap = gap
	end
	-- a price you press: ink with bone words and the pads' lip under it; short of it: greyed, "need N more" under it
	local function priceBtn(parent: Instance, icon: string?, words: string, ok: boolean, need: string?, x: UDim, w: number): TextButton
		local b = new("TextButton", { Name = "Price", AutoButtonColor = false, BackgroundColor3 = if ok then INK else T.TRACK, BorderSizePixel = 0,
			AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(x.Scale, x.Offset, 0.5, if need then -7 else -2), Size = UDim2.fromOffset(w, 32),
			Text = "", ZIndex = 4 }, parent)
		new("UICorner", { CornerRadius = UDim.new(0, 8) }, b)
		local lip = new("Frame", { Name = "Lip", BackgroundColor3 = if ok then Color3.new(0, 0, 0) else LIP, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 3), Size = UDim2.fromScale(1, 1), ZIndex = 3 }, b)
		new("UICorner", { CornerRadius = UDim.new(0, 8) }, lip)
		local row = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0, 1),
			AutomaticSize = Enum.AutomaticSize.X, ZIndex = 5 }, b)
		new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 5), VerticalAlignment = Enum.VerticalAlignment.Center,
			HorizontalAlignment = Enum.HorizontalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder }, row)
		if icon then
			local ic = new("CanvasGroup", { BackgroundTransparency = 1, Size = UDim2.fromOffset(16, 16), LayoutOrder = 1, ZIndex = 5,
				GroupTransparency = if ok then 0 else 0.4 }, row)
			if not Purse.icon(icon, ic, 16) then ic:Destroy() end
		end
		local l = txt(row, words, 15, if ok then BONE else T.DIM, T.FONT_HEAVY, Enum.TextXAlignment.Center)
		l.AutomaticSize = Enum.AutomaticSize.X; l.Size = UDim2.fromOffset(0, 32); l.LayoutOrder = 2; l.ZIndex = 5; l.RichText = true
		if need then
			local n = txt(parent, need, 11, Color3.fromRGB(150, 84, 40), T.FONT_BOLD, Enum.TextXAlignment.Center)
			n.AnchorPoint = Vector2.new(1, 0); n.Position = UDim2.new(x.Scale, x.Offset, 0.5, 13); n.Size = UDim2.fromOffset(w, 14); n.ZIndex = 4
		end
		return b
	end
	function X.sideFill()
		local page = UI.pages.featured
		local side = page:FindFirstChild("Side") :: Frame?
		if not side or not side.Visible then return end
		for _, c in side:GetChildren() do c:Destroy() end
		local gap = X.sideGap or 14
		-- the crates: the Crate, the Duffel Bag, then one row for the spray cans (their sets are on CONTAINERS)
		local boxes, sprays = {}, {}
		for _, o in Shop.containers do
			if not o.legacy then table.insert(if o.spray then sprays else boxes, o) end
		end
		local rows = table.clone(boxes)
		if #sprays > 0 then table.insert(rows, sprays[1]) end
		local function head(text: string, y: UDim)
			local l = txt(side, text, 15, Color3.new(1, 1, 1), T.FONT_HEAVY)
			l.Position = UDim2.new(0, 0, y.Scale, y.Offset); l.Size = UDim2.new(1, 0, 0, 22)
			l.TextStrokeTransparency = 0.8
		end
		local split = 0.47
		head("CRATES", UDim.new(0, 0))
		local crates = new("Frame", { Name = "Crates", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 28),
			Size = UDim2.new(1, 0, split, -28 - gap / 2) }, side)
		T.corner(crates)
		new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder }, crates)
		local tix, coins = Purse.of("tix"), Purse.of("brass")
		for i, o in rows do
			local isSpray = o.spray == true
			local function go() if isSpray then ShopUI.tab("containers") else ShopUI.ask(o.id) end end
			local r = new("TextButton", { Name = "Row" .. i, AutoButtonColor = false, BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 1, BorderSizePixel = 0,
				Text = "", Size = UDim2.new(1, 0, 1 / #rows, 0), LayoutOrder = i }, crates)
			if i > 1 then new("Frame", { Name = "Rule", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 1) }, r) end
			local view = new("Frame", { Name = "View", BackgroundTransparency = 1, Position = UDim2.fromOffset(4, 4), Size = UDim2.new(0, 96, 1, -8) }, r)
			pcall(V.put, view, o, nil, "none", 1.05)
			local name = txt(r, string.upper(if isSpray then "Spray can" else o.name), 18, T.TEXT, T.FONT_HEAVY)
			name.Position = UDim2.new(0, 108, 0.5, -20); name.Size = UDim2.new(0.5, -60, 0, 22)
			local what = ({ crate = "One random skin", bag = "One random hat" } :: any)[o.id] or (if isSpray then ("One random wrap · %d sets"):format(#sprays) else "")
			local sub = txt(r, what, 13, T.MUTED, T.FONT_BOLD)
			sub.Position = UDim2.new(0, 108, 0.5, 2); sub.Size = UDim2.new(0.5, -60, 0, 16)
			local p = Purse.price(o.id)
			local x = UDim.new(1, -12)
			if p and p.brass then
				local okB = coins >= p.brass
				priceBtn(r, "brass", commas(p.brass), okB, if okB then nil else "need " .. commas(p.brass - coins) .. " more", x, 86).MouseButton1Click:Connect(go)
				x = UDim.new(1, -12 - 86 - 26)
				if p.tix then
					local orL = txt(r, "or", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
					orL.AnchorPoint = Vector2.new(1, 0.5); orL.Position = UDim2.new(1, -12 - 86 - 2, 0.5, -2); orL.Size = UDim2.fromOffset(22, 14)
				end
			end
			if p and p.tix then
				local okT = tix >= p.tix
				priceBtn(r, "tix", tostring(p.tix), okT, if okT then nil else "need " .. (p.tix - tix) .. " more", x, 70).MouseButton1Click:Connect(go)
			end
			if not p then
				priceBtn(r, nil, if Shop.free() then "CLAIM" else ROBUX .. " " .. commas(o.robux or 0), true, nil, x, 96).MouseButton1Click:Connect(go)
			end
			r.MouseButton1Click:Connect(go)
			r.MouseEnter:Connect(function() r.BackgroundTransparency = 0 end)
			r.MouseLeave:Connect(function() r.BackgroundTransparency = 1 end)
		end
		-- the coin packs: the amount, the bonus under it, the Robux price
		head("COINS", UDim.new(split, gap / 2))
		local packs = Shop.coinPacks()
		local panel = new("Frame", { Name = "Coins", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.new(0, 0, split, gap / 2 + 28),
			Size = UDim2.new(1, 0, 1 - split, -28 - gap / 2) }, side)
		T.corner(panel)
		new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder }, panel)
		local sell = Shop.ROBUX == true and not Shop.free()
		for i, o in packs do
			local r = new("Frame", { Name = "Pack" .. i, BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1 / #packs, 0), LayoutOrder = i }, panel)
			if i > 1 then new("Frame", { Name = "Rule", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 1) }, r) end
			local bonus = tonumber(o.bonus) or 0
			local amt = txt(r, ('%s <font size="13" color="#56534d">coins</font>'):format(commas(o.amount - bonus)), 24, T.TEXT, T.FONT_HEAVY)
			amt.RichText = true
			amt.Position = UDim2.new(0, 16, 0.5, if bonus > 0 then -20 else -13); amt.Size = UDim2.new(0.6, 0, 0, 28)
			if bonus > 0 then
				local bo = txt(r, "+" .. commas(bonus) .. " bonus", 13, T.MUTED, T.FONT_BOLD)
				bo.Position = UDim2.new(0, 16, 0.5, 8); bo.Size = UDim2.new(0.6, 0, 0, 16)
			end
			local b = priceBtn(r, nil, ROBUX .. " " .. commas(o.robux), sell and Shop.productFor(o) ~= nil, nil, UDim.new(1, -16), 104)
			b.MouseButton1Click:Connect(function() if sell then ShopUI.prompt(o) else ShopUI.tab("coins") end end)
		end
	end

	-- ==================================================================== owned, display only
	-- an owned skin with no single offer (a set's piece, a VIP skin: neither is sold alone) opens the inspect panel all
	-- the same, as "view:skin:<id>": OWNED, no BUY and no GIFT, its finisher's PREVIEW where it has one. this offer is
	-- this client's only, never Shop.offer (the server's Purchases, Gifts and ShopReceipts read that), so it sells nothing
	X.views = {} :: { [string]: any }
	function X.viewOffer(id: string): any
		local kind, iid = string.match(id, "^view:(%a+):(.+)$")
		if kind ~= "skin" or not iid then return nil end
		local v = X.views[id]
		if v then return v end
		local okI, name, r = pcall(Shop.itemInfo, "skin", iid)
		if not okI or type(name) ~= "string" or not Till.owns("skin", iid, nil) then return nil end
		v = { id = id, type = "single", kind = "skin", item = iid, weapon = Shop.skinWeapon(iid), rarity = r or "common", name = name, robux = 0, view = true }
		X.views[id] = v
		return v
	end

	return X
end
