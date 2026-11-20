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
	X.POSE = { pitch = 0, phase = 0.32, camYaw = 34, low = 0.06, fov = 24, settle = 0.9, wideH = 1.06, cardH = 0.78, cardUp = 0.12 }
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
		-- the stride: its own run (the avatar's animation pack's, if it has one), held a third of the way in
		local an = hum:FindFirstChildOfClass("Animator")
		local live = ch:FindFirstChild("Animate")
		local runF = live and live:FindFirstChild("run")
		local a0 = runF and runF:FindFirstChildOfClass("Animation")
		local id = if a0 and a0.AnimationId ~= "" then a0.AnimationId
			elseif hum.RigType == Enum.HumanoidRigType.R6 then "rbxassetid://180426354" else "rbxassetid://913376220"
		if an then
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

	return X
end
