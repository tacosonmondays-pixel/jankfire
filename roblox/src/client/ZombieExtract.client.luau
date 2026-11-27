--!strict
-- ZOMBIES extraction, your side (27 Nov 2026; roblox/docs/ZOMBIES.md 4; the server: server/ZombieExtract.luau).
--   the offer: EXTRACTION with the round band's odds (the owner's rewards are random, so their odds are on screen),
--     Y to call it (EXTRACT on a phone), the votes, the break's countdown
--   the hold-out: EXTRACTION · <area> with the time to the helicopter, then to the lift-off, and a marker on the pad
--     (on the screen's edge when it's behind you)
--   the helicopter: drawn here from the server's times (XT0, XLift) by ZM.heliAt; rotors turning, a searchlight, a red
--     beacon, its recorded hover (zm_heli) on its body
--   the reward screen after the extraction film (ZombieCine): Brass, XP, each roll with its odds and what dropped
-- plain labels only (the owner: no flavour text)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local okR, Roster = pcall(require, Shared:WaitForChild("Roster"))
local function wrapName(id: string): string
	local row = okR and Roster and Roster.wrapById and Roster.wrapById[id]
	return string.upper(if row and row.name then row.name else id)
end
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Keys = require(script.Parent:WaitForChild("Keys")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local zr = Remotes:WaitForChild("Zm") :: RemoteEvent
local me = Players.LocalPlayer
local XC, XR = ZM.X, ZM.XR
local function srv(): number return workspace:GetServerTimeNow() end
local function arena(): Model?
	local n = me:GetAttribute("ZmArena")
	local a = if type(n) == "string" then workspace:FindFirstChild(n) else nil
	return if a and a:IsA("Model") then a else nil
end
local function clock(s: number): string
	s = math.max(0, math.ceil(s))
	return string.format("%d:%02d", s // 60, s % 60)
end
local function pct(p: number): string
	local v = p * 100
	return (if v < 1 and v > 0 then string.format("%.1f", v) else string.format("%d", math.floor(v + 0.5))) .. "%"
end

local gui = T.new("ScreenGui", { Name = "JankZmExtract", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 7, Enabled = true }, me:WaitForChild("PlayerGui"))
local root = T.scaled(gui)

-- ------------------------------------------------------------------ the offer
local offer = T.plate(root, "Offer", UDim2.new(0.5, -230, 0, 200), UDim2.fromOffset(460, 132))
offer.Visible = false
local oTitle = T.text(offer, "Title", "EXTRACTION", 20, T.ACCENT, T.FONT_HEAVY)
oTitle.Position = UDim2.fromOffset(14, 8); oTitle.Size = UDim2.fromOffset(200, 24)
local oTime = T.text(offer, "Time", "", 16, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right)
oTime.Position = UDim2.new(1, -94, 0, 10); oTime.Size = UDim2.fromOffset(80, 20)
T.key(offer, "Y", UDim2.fromOffset(14, 38))
local oCall = T.text(offer, "Call", "CALL IT", 14, T.TEXT, T.FONT_BOLD)
oCall.Position = UDim2.fromOffset(44, 38); oCall.Size = UDim2.fromOffset(240, 22)
local oVotes = T.text(offer, "Votes", "", 14, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
oVotes.Position = UDim2.new(1, -214, 0, 38); oVotes.Size = UDim2.fromOffset(200, 22)
local oOdds = T.text(offer, "Odds", "", 13, T.SOFT, T.FONT)
oOdds.Position = UDim2.fromOffset(14, 66); oOdds.Size = UDim2.new(1, -28, 0, 18)
local oWraps = T.text(offer, "Wraps", "", 13, T.SOFT, T.FONT)
oWraps.Position = UDim2.fromOffset(14, 86); oWraps.Size = UDim2.new(1, -28, 0, 18)
local oPay = T.text(offer, "Pay", "", 13, T.MUTED, T.FONT)
oPay.Position = UDim2.fromOffset(14, 106); oPay.Size = UDim2.new(1, -28, 0, 18)
-- (a phone: a button instead of the key)
local oBtn = T.new("TextButton", { Name = "Extract", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Text = "EXTRACT",
	TextColor3 = T.INK, FontFace = T.FONT_HEAVY, TextSize = 15, AutoButtonColor = true, Visible = false,
	Position = UDim2.new(1, -126, 1, 8), Size = UDim2.fromOffset(112, 36) }, offer)
T.corner(oBtn)
local offerN = 0
-- the band's odds, and each zombies wrap's own share of the wrap roll (by weight among the ones open at that round)
local function oddsLine(n: number): (string, string, string)
	local b = ZM.xBand(n)
	if not b then return "", "", "" end
	local parts = {}
	for _, k in XR.rolls do
		if k == "wrap" and #ZM.xWraps(n) == 0 then continue end
		table.insert(parts, XR.names[k] .. "  " .. pct(b[k] or 0))
	end
	local ws, total = ZM.xWraps(n), 0
	for _, w in ws do total += (w.w or 1) end
	local wp = {}
	for _, w in ws do table.insert(wp, wrapName(w.id) .. "  " .. pct((b.wrap or 0) * (w.w or 1) / math.max(1, total))) end
	return table.concat(parts, "     "), table.concat(wp, "     "), string.format("+%d BRASS   +%d XP   (rounds %d+ odds)", b.brass, b.xp, b.from)
end
local function showOffer(n: number, need: number?)
	offerN = n
	local o, w, p = oddsLine(n)
	oOdds.Text, oWraps.Text, oPay.Text = o, w, p
	oVotes.Text = if need and need > 1 then ("VOTES 0/" .. need) else ""
	oBtn.Visible = Keys.isTouch()
	offer.Visible = true
end
local function vote()
	if not offer.Visible then return end
	zr:FireServer({ k = "xcall" })
end
Keys.began(function(io: any, gp: boolean)
	if gp then return end
	if io.KeyCode == Enum.KeyCode.Y then vote() end
end)
oBtn.Activated:Connect(vote)

-- ------------------------------------------------------------------ the hold-out
local hold = T.plate(root, "Hold", UDim2.new(0.5, -170, 0, 200), UDim2.fromOffset(340, 56))
hold.Visible = false
local hTitle = T.text(hold, "Title", "EXTRACTION", 16, T.ACCENT, T.FONT_HEAVY)
hTitle.Position = UDim2.fromOffset(14, 6); hTitle.Size = UDim2.new(1, -28, 0, 20)
local hTime = T.text(hold, "Time", "", 14, T.TEXT, T.FONT_BOLD)
hTime.Position = UDim2.fromOffset(14, 29); hTime.Size = UDim2.new(1, -28, 0, 20)
local mark = T.new("Frame", { Name = "Pad", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundTransparency = 1, Size = UDim2.fromOffset(80, 44), Visible = false }, gui)
local dia = T.new("Frame", { Name = "Dia", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = T.ACCENT, BorderSizePixel = 0,
	Position = UDim2.new(0.5, 0, 0, 10), Size = UDim2.fromOffset(12, 12), Rotation = 45 }, mark)
T.edge(dia, Color3.new(0, 0, 0), 0.4)
local dist = T.text(mark, "Dist", "", 13, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
dist.Position = UDim2.fromOffset(0, 20); dist.Size = UDim2.new(1, 0, 0, 18)

-- ------------------------------------------------------------------ the helicopter (local, from the server's times)
-- which one flies: ZM.X.heli, a model in ReplicatedStorage.JankfireZmKit (ZmKit.importHeli). Its rotors turn about their
-- hubs (the model's HubMain / HubTail attributes: a 3-blade rotor's box centre isn't its hub); every zh_rotor* piece
-- about the main hub on the model's up axis, every zh_tail* piece about the tail hub on its side axis
local heli: Model? = nil
type Spinner = { p: BasePart, fromHub: CFrame }
local parts: { rotors: { Spinner }, tails: { Spinner }, doors: { Spinner }, beacon: BasePart?, body: BasePart?, hubMain: CFrame, hubTail: CFrame } =
	{ rotors = {}, tails = {}, doors = {}, beacon = nil, body = nil, hubMain = CFrame.new(), hubTail = CFrame.new() }
local folder = Instance.new("Folder")
folder.Name = "ZmLocal"
local spin, spinT, rate = 0, 0, 0
local function build(): Model?
	if heli then return heli end
	local kit = ReplicatedStorage:FindFirstChild("JankfireZmKit")
	local want = me:GetAttribute("ZmHeli") -- (a test's side-by-side: this client's own pick over ZM.X.heli)
	local src = kit and (kit:FindFirstChild(if type(want) == "string" then want else (XC.heli or "Heli")) or kit:FindFirstChild("Heli"))
	if not src or not src:IsA("Model") then return nil end
	local m = src:Clone()
	local piv = m:GetPivot()
	local hm, ht = m:GetAttribute("HubMain"), m:GetAttribute("HubTail")
	local rotorAt, tailAt = nil, nil
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored, d.CanCollide, d.CanQuery, d.CanTouch = true, false, false, false
			local nm = string.lower(d.Name)
			if string.find(nm, "zh_rotor", 1, true) then rotorAt = rotorAt or d.Position
			elseif string.find(nm, "zh_tail", 1, true) then tailAt = tailAt or d.Position
			elseif string.find(nm, "zh_beacon", 1, true) then parts.beacon = d
			elseif string.find(nm, "zh_body", 1, true) then parts.body = parts.body or d
			elseif string.find(nm, "zh_open", 1, true) or string.find(nm, "zh_cabin", 1, true) then
				if not d:FindFirstChild("CabinLight") then
					local cl = Instance.new("PointLight") -- (the cabin's warm light: the way in and the glass read at night)
					cl.Name = "CabinLight"; cl.Color = Color3.fromRGB(255, 214, 168); cl.Range = 14; cl.Brightness = 1.4; cl.Shadows = false
					cl.Parent = d
				end
			elseif string.find(nm, "zh_lamp", 1, true) or string.find(nm, "zh_search", 1, true) then
				if not d:FindFirstChildOfClass("SpotLight") then
					local sl = Instance.new("SpotLight")
					sl.Face = Enum.NormalId.Bottom; sl.Angle = 50; sl.Range = 70; sl.Brightness = 3.5
					sl.Color = Color3.fromRGB(240, 238, 226); sl.Shadows = true
					sl.Parent = d
				end
			end
		end
	end
	parts.hubMain = CFrame.new(if typeof(hm) == "Vector3" then hm else (if rotorAt then piv:PointToObjectSpace(rotorAt) else Vector3.zero))
	parts.hubTail = CFrame.new(if typeof(ht) == "Vector3" then ht else (if tailAt then piv:PointToObjectSpace(tailAt) else Vector3.zero))
	for _, d in m:GetDescendants() do
		if not d:IsA("BasePart") then continue end
		local nm = string.lower(d.Name)
		if string.find(nm, "zh_door", 1, true) then
			table.insert(parts.doors, { p = d, fromHub = piv:ToObjectSpace(d.CFrame) }) -- (the sliding door: from the pivot)
		elseif string.find(nm, "zh_rotor", 1, true) then
			table.insert(parts.rotors, { p = d, fromHub = (piv * parts.hubMain):ToObjectSpace(d.CFrame) })
		elseif string.find(nm, "zh_tail", 1, true) then
			table.insert(parts.tails, { p = d, fromHub = (piv * parts.hubTail):ToObjectSpace(d.CFrame) })
		end
	end
	if parts.beacon then
		local pl = Instance.new("PointLight")
		pl.Color = Color3.fromRGB(220, 50, 40); pl.Range = 10; pl.Brightness = 2; pl.Name = "Blink"
		pl.Parent = parts.beacon
	end
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	local hs = lib and lib:FindFirstChild("zm_heli")
	if hs and hs:IsA("Sound") and parts.body then
		local s = hs:Clone()
		s.Name = "Hover"
		s.Looped = true
		s.RollOffMode = Enum.RollOffMode.InverseTapered
		s.RollOffMinDistance = 30; s.RollOffMaxDistance = 900
		s.Parent = parts.body
	end
	heli = m
	return m
end
local function drop()
	if heli then heli:Destroy() end
	heli = nil
	parts.rotors, parts.tails, parts.doors, parts.beacon, parts.body = {}, {}, {}, nil, nil
	rate, spin, spinT = 0, 0, 0
end

-- ------------------------------------------------------------------ the reward card (A PLATE)
-- (27 Nov, main: "a proper centred A PLATE card at a readable size on a phone, with the dropped item called out big (its
-- icon or wrap swatch), and the odds smaller underneath". UiKit's A: bone, ink, near-square, ExtraBold caps for names
-- and numbers, Medium sentence case for anything said, the stencil slit only on the hero numbers, colour only for rarity)
local K = require(script.Parent:WaitForChild("UiKit")) :: any
local okLT, LootTable = pcall(require, Shared:WaitForChild("LootTable"))
local A = K.A
-- (27 Nov test: a ZIndex on the card hid its own children under it; none here, the dim first and the card after it)
local dim = T.new("Frame", { Name = "RewardDim", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.4, BorderSizePixel = 0,
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(4, 4), Visible = false }, root)
local card = K.new("Frame", { Name = "Reward", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), BackgroundColor3 = A.BONE,
	BorderSizePixel = 0, Size = UDim2.fromOffset(600, 0), AutomaticSize = Enum.AutomaticSize.Y, Visible = false }, root)
K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, card)
K.new("UIPadding", { PaddingLeft = UDim.new(0, 30), PaddingRight = UDim.new(0, 30), PaddingTop = UDim.new(0, 26), PaddingBottom = UDim.new(0, 24) }, card)
K.new("UIListLayout", { Padding = UDim.new(0, 16), SortOrder = Enum.SortOrder.LayoutOrder }, card)
local function rarityColor(r: string?): Color3
	local row = okLT and LootTable and LootTable.RARITY and r and LootTable.RARITY[r]
	return if row and row.color then row.color else A.INK2
end
-- a flat glyph for a container (no picture to load): the crate's slatted box, the bag's body and handle, the can and cap
local function glyph(parent: Instance, kind: string)
	local function box(pos: UDim2, size: UDim2, col: Color3, rad: number?): Frame
		local f = K.new("Frame", { BackgroundColor3 = col, BorderSizePixel = 0, Position = pos, Size = size, AnchorPoint = Vector2.new(0.5, 0.5) }, parent)
		if rad then K.new("UICorner", { CornerRadius = UDim.new(0, rad) }, f) end
		return f
	end
	if kind == "crate" then
		box(UDim2.fromScale(0.5, 0.56), UDim2.fromOffset(96, 66), A.INK, 3)
		box(UDim2.fromScale(0.5, 0.42), UDim2.fromOffset(100, 8), A.BONE2)
		for _, x in { 0.36, 0.64 } do box(UDim2.fromScale(x, 0.6), UDim2.fromOffset(6, 44), A.BONE2) end
	elseif kind == "bag" then
		local h = box(UDim2.fromScale(0.5, 0.36), UDim2.fromOffset(46, 30), Color3.new(1, 1, 1), 15)
		h.BackgroundTransparency = 1
		K.new("UIStroke", { Color = A.INK, Thickness = 6 }, h)
		box(UDim2.fromScale(0.5, 0.62), UDim2.fromOffset(106, 58), A.INK, 14)
		box(UDim2.fromScale(0.5, 0.6), UDim2.fromOffset(106, 6), A.BONE2)
	else -- the spray can
		box(UDim2.fromScale(0.5, 0.3), UDim2.fromOffset(22, 16), A.INK2, 3)
		box(UDim2.fromScale(0.5, 0.6), UDim2.fromOffset(46, 84), A.INK, 8)
		box(UDim2.fromScale(0.5, 0.52), UDim2.fromOffset(46, 7), A.BONE2)
	end
end
-- a wrap's swatch: its palette as hard bands on the diagonal, the way the wrap reads on a gun
local function swatch(parent: Instance, id: string)
	local row = okR and Roster and Roster.wrapById and Roster.wrapById[id]
	local pal: { Color3 } = if row and row.pal and #row.pal > 0 then row.pal else { A.INK }
	local f = K.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(112, 112) }, parent)
	K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, f)
	local keys = {}
	local n = math.max(2, #pal * 3)
	for b = 0, n - 1 do
		local c = pal[(b % #pal) + 1]
		local a0, a1 = b / n, (b + 1) / n
		table.insert(keys, ColorSequenceKeypoint.new(a0, c))
		table.insert(keys, ColorSequenceKeypoint.new(if b == n - 1 then 1 else a1 - 0.001, c))
	end
	K.new("UIGradient", { Rotation = 45, Color = ColorSequence.new(keys) }, f)
end
local WHY = { share = "Not enough of the squad's fight", up = "Down for too long", active = "Not active enough", round = "Too early", error = "Something broke" }
local function line(parent: Instance, order: number, a: string, b: string, c: string, cCol: Color3?)
	local f = K.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 22), LayoutOrder = order }, parent)
	local l1 = K.text(f, "A", a, 15, A.INK, K.SANS_BOLD); l1.Size = UDim2.new(0.5, 0, 1, 0)
	local l2 = K.text(f, "B", b, 15, A.INK2, K.SANS, Enum.TextXAlignment.Right); l2.Position = UDim2.fromScale(0.5, 0); l2.Size = UDim2.new(0.18, 0, 1, 0)
	local l3 = K.text(f, "C", c, 15, cCol or A.INK2, K.SANS_BOLD, Enum.TextXAlignment.Right); l3.Position = UDim2.fromScale(0.68, 0); l3.Size = UDim2.new(0.32, 0, 1, 0)
end
local rewardUp = false
local function showReward(res: any)
	for _, c in card:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	-- 1. the title: EXTRACTED and the round, big (27 Nov, the owner: "boom displays your round")
	local head = K.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 70), LayoutOrder = 1 }, card)
	local t1 = K.text(head, "Title", "EXTRACTED", 44, A.INK, K.SANS_HEAVY); t1.Position = UDim2.fromOffset(0, 10); t1.Size = UDim2.new(0.62, 0, 0, 50)
	local rl = K.text(head, "RoundL", "ROUND", 14, A.INK2, K.SANS_HEAVY, Enum.TextXAlignment.Right); rl.Position = UDim2.fromScale(0.62, 0); rl.Size = UDim2.new(0.38, 0, 0, 16)
	local rh = K.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 14), Size = UDim2.fromOffset(160, 56) }, head)
	K.new("UIListLayout", { HorizontalAlignment = Enum.HorizontalAlignment.Right }, rh)
	local _, _, setR = K.hero(rh, "N", 56, K.SANS_HEAVY, A.INK, false, true)
	setR(tostring(res.n))
	-- 1b. the small stats
	local st = res.stats
	if type(st) == "table" then
		local row = K.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 44), LayoutOrder = 2 }, card)
		local mm = math.floor((tonumber(st.time) or 0) / 60)
		local items = { { tostring(st.kills or 0), "KILLS" }, { tostring(st.revives or 0), "REVIVES" },
			{ tostring(st.dmg or 0), "DAMAGE" }, { string.format("%d:%02d", mm, (tonumber(st.time) or 0) % 60), "TIME SURVIVED" } }
		for i, it in items do
			local c = K.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale((i - 1) * 0.25, 0), Size = UDim2.new(0.25, 0, 1, 0) }, row)
			local a = K.text(c, "N", it[1], 24, A.INK, K.SANS_HEAVY); a.Size = UDim2.new(1, 0, 0, 26)
			local b = K.text(c, "L", it[2], 12, A.INK2, K.SANS_BOLD); b.Position = UDim2.fromOffset(0, 27); b.Size = UDim2.new(1, 0, 0, 14)
		end
	end
	-- 2. what dropped, big (the last hit in the list: the wrap before the crate before the bag before the can)
	local best = nil
	for _, r in (res.rolls or {}) :: { any } do if r.hit then best = r end end
	local drop = K.new("Frame", { BackgroundColor3 = A.BONE2, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 150), LayoutOrder = 3 }, card)
	K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, drop)
	if best then
		local art = K.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(150, 150) }, drop)
		local name, sub, rar = XR.names[best.k] or string.upper(best.k), "", nil
		if best.k == "wrap" and best.wrap then
			swatch(art, best.wrap)
			local row = okR and Roster and Roster.wrapById and Roster.wrapById[best.wrap]
			name = wrapName(best.wrap)
			rar = row and row.rarity
			sub = (if rar then (string.upper(string.sub(rar, 1, 1)) .. string.sub(rar, 2) .. " zombies wrap") else "Zombies wrap") .. ", on every gun"
		else
			glyph(art, best.k)
			sub = if best.k == "spray" then "A spray can from one of the sets" elseif best.k == "bag" then "A duffel bag, set 1" else "A crate, case 1"
		end
		local n1 = K.text(drop, "Name", name, 30, A.INK, K.SANS_HEAVY); n1.Position = UDim2.fromOffset(160, 34); n1.Size = UDim2.new(1, -176, 0, 36)
		n1.TextTruncate = Enum.TextTruncate.AtEnd
		local n2 = K.text(drop, "Sub", sub, 16, A.INK2, K.SANS); n2.Position = UDim2.fromOffset(160, 74); n2.Size = UDim2.new(1, -176, 0, 22)
		local n3 = K.text(drop, "Odds", "DROPPED  ·  " .. pct(best.p or 0), 14, A.INK, K.SANS_HEAVY); n3.Position = UDim2.fromOffset(160, 102); n3.Size = UDim2.new(1, -176, 0, 20)
		if rar then
			K.new("Frame", { Name = "Lip", BackgroundColor3 = rarityColor(rar), BorderSizePixel = 0, Position = UDim2.new(0, 0, 1, -6), Size = UDim2.new(1, 0, 0, 6) }, drop)
		end
	else
		drop.Size = UDim2.new(1, 0, 0, 58)
		local said = if res.ok then "Nothing dropped this time" else ("No rewards: " .. string.lower(WHY[res.why] or tostring(res.why or "")))
		local n = K.text(drop, "None", said, 18, A.INK2, K.SANS, Enum.TextXAlignment.Center)
		n.Size = UDim2.fromScale(1, 1)
	end
	-- 3. Brass and XP, hero numbers
	if res.ok then
		local heroes = K.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 74), LayoutOrder = 4 }, card)
		for i, it in { { "+" .. tostring(res.brass), "BRASS" }, { "+" .. tostring(res.xp), "XP" } } do
			local col = K.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale((i - 1) * 0.5, 0), Size = UDim2.new(0.5, 0, 1, 0) }, heroes)
			local _, _, set = K.hero(col, "N", 52, K.SANS_HEAVY, A.INK, false, true)
			set(it[1])
			local l = K.text(col, "L", it[2], 14, A.INK2, K.SANS_HEAVY); l.Position = UDim2.fromOffset(2, 54); l.Size = UDim2.new(1, 0, 0, 18)
		end
	end
	-- 4. the odds, small
	local odds = K.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = 5 }, card)
	K.new("UIListLayout", { Padding = UDim.new(0, 2), SortOrder = Enum.SortOrder.LayoutOrder }, odds)
	local o = 0
	for _, r in (res.rolls or {}) :: { any } do
		o += 1
		local hit = r.hit == true
		local said = if hit and r.wrap then wrapName(r.wrap) elseif hit then "DROPPED" elseif r.owned then "ALL OWNED" else "—"
		line(odds, o, XR.names[r.k] or string.upper(r.k), pct(r.p or 0), said, if hit then A.INK else A.INK2)
	end
	-- 5. what's said
	local foot = if res.dry then "A Studio test: nothing was granted" elseif res.ok then ("The odds for rounds " .. tostring(res.band or res.n) .. " and up") else ""
	if foot ~= "" then
		local f = K.text(card, "Foot", foot, 14, A.INK2, K.SANS); f.Size = UDim2.new(1, 0, 0, 18); f.LayoutOrder = 6
	end
	-- 6. back to the lobby: the button (or Enter); on its own when the game ends a few seconds later anyway
	local bar = K.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 44), LayoutOrder = 7 }, card)
	local btn = K.new("TextButton", { Name = "Lobby", AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0), Size = UDim2.fromOffset(220, 44),
		BackgroundColor3 = A.INK, BorderSizePixel = 0, Text = "BACK TO LOBBY", TextColor3 = A.BONE, FontFace = K.SANS_HEAVY, TextSize = 16, AutoButtonColor = true }, bar)
	K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, btn)
	btn.Activated:Connect(function() zr:FireServer({ k = "xhome" }); btn.Text = "LEAVING" end)
	local hint = K.text(bar, "Hint", if Keys.isTouch() then "" else "Enter", 14, A.INK2, K.SANS, Enum.TextXAlignment.Right)
	hint.Position = UDim2.new(1, -352, 0, 0); hint.Size = UDim2.new(0, 120, 1, 0)
	dim.Visible, card.Visible, rewardUp = true, true, true
	me:SetAttribute("LoadoutOpen", true) -- (the mouse free for the button; the hands and guns hold still)
	task.delay(16, function() dim.Visible, card.Visible, rewardUp = false, false, false; me:SetAttribute("LoadoutOpen", nil) end)
end
-- the film's own skip (ZombieCine: Space) asks for the card at once
local pendingRes: any = nil
me:GetAttributeChangedSignal("ZmCardNow"):Connect(function()
	if me:GetAttribute("ZmCardNow") and pendingRes then local r = pendingRes; pendingRes = nil; showReward(r) end
	me:SetAttribute("ZmCardNow", nil)
end)
Keys.began(function(io: any, gp: boolean)
	if gp or not rewardUp then return end
	if io.KeyCode == Enum.KeyCode.Return then zr:FireServer({ k = "xhome" }) end
end)
local xpToast = T.text(root, "XpToast", "", 18, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Center, true)
xpToast.AnchorPoint = Vector2.new(0.5, 0); xpToast.Position = UDim2.new(0.5, 0, 0.5, 168); xpToast.Size = UDim2.fromOffset(500, 24)

zr.OnClientEvent:Connect(function(x: any)
	if type(x) ~= "table" then return end
	if x.k == "xoffer" then
		showOffer(tonumber(x.n) or 0, tonumber(x.need))
	elseif x.k == "xvote" then
		oVotes.Text = string.format("VOTES %d/%d", tonumber(x.yes) or 0, tonumber(x.need) or 1)
	elseif x.k == "xcall" then
		offer.Visible = false
	elseif x.k == "xout" then
		-- out with the helicopter: the round's HUD (the round, the boss bar, the credits) stays off from the film on
		for _, nm in (x.who or {}) :: { any } do if nm == me.DisplayName then me:SetAttribute("ZmHudOff", true) end end
	elseif x.k == "xreward" then
		local a = arena()
		local lift = a and a:GetAttribute("XLift")
		local at = if type(lift) == "number" then lift - XC.board + XC.outro else srv()
		pendingRes = x.res
		task.delay(math.max(0, at - srv()), function() if pendingRes == x.res then pendingRes = nil; showReward(x.res) end end)
	elseif x.k == "xover" then
		local res = x.res
		if type(res) ~= "table" then return end
		xpToast.Text = if res.ok and (res.xp or 0) > 0 then ("+" .. tostring(res.xp) .. " XP" .. (if res.dry then "  (STUDIO TEST)" else ""))
			elseif not res.ok and res.why and WHY[res.why] then ("No XP: " .. string.lower(WHY[res.why])) else ""
		task.delay(10, function() xpToast.Text = "" end)
	end
end)

-- ------------------------------------------------------------------ every frame: the HUD's numbers, the helicopter
local labels: { [Instance]: { [string]: string } } = setmetatable({}, { __mode = "k" }) :: any
local function areaLabel(a: Model, id: string): string
	local c = labels[a]
	if not c then
		c = {}
		local ok, map = pcall(ZM.read, a)
		if ok and map then for k, ar in map.areas do c[k] = string.upper(ar.label) end end
		labels[a] = c
	end
	return c[id] or string.upper(id)
end
local lastSt = nil
RunService.RenderStepped:Connect(function(dt: number)
	local a = arena()
	local st = a and a:GetAttribute("XSt")
	if not a or (st ~= "offer" and offer.Visible) then offer.Visible = false end
	if offer.Visible and a then
		local bu = a:GetAttribute("BreakUntil")
		oTime.Text = if type(bu) == "number" then clock(bu - srv()) else ""
	end
	local z = a and XC.zones[a.Name]
	local t0 = a and a:GetAttribute("XT0")
	if not a or not z or type(t0) ~= "number" or (st ~= "hold" and st ~= "out") then
		hold.Visible = false; mark.Visible = false
		if heli then drop() end
		if folder.Parent then folder.Parent = nil end
		lastSt = st
		return
	end
	local pad = ZM.padOf(a:GetPivot(), z)
	local t = srv() - t0
	local liftAt = a:GetAttribute("XLift")
	local lift = if type(liftAt) == "number" then liftAt - t0 else nil
	-- the HUD (the hold-out only)
	if st == "hold" then
		hold.Visible = true
		hTitle.Text = "EXTRACTION  ·  " .. areaLabel(a, z.area or "")
		hTime.Text = if t < XC.over then ("HELICOPTER  " .. clock(XC.over - t)) else ("LIFT-OFF  " .. clock(XC.hold - t))
		local cam = workspace.CurrentCamera
		local P = pad.Position + Vector3.new(0, 7, 0)
		local v, on = cam:WorldToViewportPoint(P)
		local vs = cam.ViewportSize
		local px, py = v.X, v.Y
		if not on then
			-- behind you or off screen: on the edge, the side it's on
			local rel = cam.CFrame:PointToObjectSpace(P)
			local dir = Vector2.new(rel.X, -rel.Y)
			if dir.Magnitude < 1e-3 then dir = Vector2.new(0, 1) end
			dir = dir.Unit
			local cx, cy = vs.X / 2, vs.Y / 2
			local k = math.min((cx - 50) / math.max(1e-3, math.abs(dir.X)), (cy - 50) / math.max(1e-3, math.abs(dir.Y)))
			px, py = cx + dir.X * k, cy + dir.Y * k
		end
		mark.Position = UDim2.fromOffset(px, py)
		local ch = me.Character
		local hrp = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local d = if hrp then (hrp.Position - pad.Position).Magnitude else 0
		dist.Text = string.format("%d m", math.floor(d / 3.57 + 0.5))
		mark.Visible = true
	else
		hold.Visible = false; mark.Visible = false
	end
	-- the helicopter
	local cf = ZM.heliAt(pad, z, t, lift)
	if lift and t > lift + 13 then cf = nil end -- (gone into the fog)
	local m = if cf then build() else nil
	if not m or not cf then
		if heli and heli.Parent then heli.Parent = nil end
		return
	end
	if not folder.Parent then folder.Parent = workspace end
	if m.Parent ~= folder then
		m.Parent = folder
		local s = parts.body and parts.body:FindFirstChild("Hover") :: Sound?
		if s and not s.IsPlaying then s:Play() end
	end
	m:PivotTo(cf)
	-- the rotors: spinning up as it comes in, full on the pad
	local want = if t < XC.arrive + 1 then 6 else 24
	rate += (want - rate) * math.min(1, dt * 0.8)
	spin = (spin + rate * dt) % (math.pi * 2)
	spinT = (spinT + rate * 1.9 * dt) % (math.pi * 2)
	local blur = math.clamp((rate - 10) / 30, 0, 0.4) -- (a blur at speed)
	for _, r in parts.rotors do
		r.p.CFrame = cf * parts.hubMain * CFrame.Angles(0, spin, 0) * r.fromHub
		r.p.Transparency = blur
	end
	for _, r in parts.tails do r.p.CFrame = cf * parts.hubTail * CFrame.Angles(spinT, 0, 0) * r.fromHub end
	-- the door: out of the hull a hair, then back along the boom, as the film says (ZM.X.film.door; from the lift-off)
	if #parts.doors > 0 then
		local open = Vector3.zero
		if lift then
			local ft = t - (lift - XC.board)
			local d0, d1 = XC.film.door[1], XC.film.door[2]
			local pop = math.clamp((ft - d0) / 0.25, 0, 1)
			local sl = math.clamp((ft - d0 - 0.2) / math.max(0.1, d1 - d0 - 0.2), 0, 1)
			sl = sl * sl * (3 - 2 * sl)
			local dA = heli and heli:GetAttribute("DoorAt")
			local side = if typeof(dA) == "Vector3" and dA.X < 0 then -1 else 1 -- (out of the hull on the door's own side)
			open = Vector3.new(math.abs(XC.doorSlide.X) * side * pop, 0, XC.doorSlide.Z * sl)
		end
		for _, r in parts.doors do r.p.CFrame = cf * CFrame.new(open) * r.fromHub end
	end
	if parts.beacon then
		local on = (os.clock() % 1.2) < 0.16
		parts.beacon.Transparency = if on then 0 else 0.75
		local bl = parts.beacon:FindFirstChild("Blink") :: PointLight?
		if bl then bl.Enabled = on end
	end
	lastSt = st
end)
me:GetAttributeChangedSignal("ZmArena"):Connect(function()
	if me:GetAttribute("ZmArena") then
		-- the helicopters' meshes and pictures loaded at the start (27 Nov test: built late, it showed grey for 2 s)
		task.spawn(function()
			local kit = ReplicatedStorage:WaitForChild("JankfireZmKit", 10)
			if kit then pcall(function() game:GetService("ContentProvider"):PreloadAsync(kit:GetChildren()) end) end
		end)
	end
	if not me:GetAttribute("ZmArena") then
		offer.Visible = false; hold.Visible = false; mark.Visible = false
		drop()
		me:SetAttribute("ZmHudOff", nil)
	end
end)
-- while the reward card is up the card has the screen: every other HUD off and the first-person gun hidden (held each
-- frame: some HUDs set themselves), each put back as it was
local heldGuis: { [ScreenGui]: boolean } = {}
local heldVm: { [BasePart]: number } = {}
RunService.RenderStepped:Connect(function()
	if rewardUp then
		local pg = me:FindFirstChild("PlayerGui")
		if pg then
			for _, g in pg:GetChildren() do
				if g:IsA("ScreenGui") and g ~= gui and g.Name ~= "CineBars" and g.Name ~= "JankZmCine" then
					if heldGuis[g] == nil then heldGuis[g] = g.Enabled end
					if g.Enabled then g.Enabled = false end
				end
			end
		end
		for _, d in workspace.CurrentCamera:GetDescendants() do
			if d:IsA("BasePart") and d.LocalTransparencyModifier < 1 then
				if heldVm[d] == nil then heldVm[d] = d.LocalTransparencyModifier end
				d.LocalTransparencyModifier = 1
			end
		end
	elseif next(heldGuis) or next(heldVm) then
		for g, was in heldGuis do if g.Parent then g.Enabled = was end end
		for d, was in heldVm do if d.Parent then d.LocalTransparencyModifier = was end end
		table.clear(heldGuis); table.clear(heldVm)
	end
end)
