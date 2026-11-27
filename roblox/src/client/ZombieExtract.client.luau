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
local heli: Model? = nil
local parts: { rotor: BasePart?, tail: BasePart?, beacon: BasePart?, body: BasePart?, rotOff: CFrame, tailOff: CFrame } =
	{ rotor = nil, tail = nil, beacon = nil, body = nil, rotOff = CFrame.new(), tailOff = CFrame.new() }
local folder = Instance.new("Folder")
folder.Name = "ZmLocal"
local spin, spinT, rate = 0, 0, 0
local function build(): Model?
	if heli then return heli end
	local kit = ReplicatedStorage:FindFirstChild("JankfireZmKit")
	local src = kit and kit:FindFirstChild("Heli")
	if not src or not src:IsA("Model") then return nil end
	local m = src:Clone()
	local piv = m:GetPivot()
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored, d.CanCollide, d.CanQuery, d.CanTouch = true, false, false, false
			local nm = string.lower(d.Name)
			if string.find(nm, "zh_rotor", 1, true) then parts.rotor = d; parts.rotOff = piv:ToObjectSpace(d.CFrame)
			elseif string.find(nm, "zh_tail", 1, true) then parts.tail = d; parts.tailOff = piv:ToObjectSpace(d.CFrame)
			elseif string.find(nm, "zh_beacon", 1, true) then parts.beacon = d
			elseif string.find(nm, "zh_body", 1, true) then parts.body = d
			elseif string.find(nm, "zh_open", 1, true) then
				local cl = Instance.new("PointLight") -- (the cabin's warm light out of the open side: the way in reads at night)
				cl.Color = Color3.fromRGB(255, 214, 168); cl.Range = 14; cl.Brightness = 1.4; cl.Shadows = false
				cl.Parent = d
			elseif string.find(nm, "zh_lamp", 1, true) then
				local sl = Instance.new("SpotLight")
				sl.Face = Enum.NormalId.Bottom; sl.Angle = 50; sl.Range = 70; sl.Brightness = 3.5
				sl.Color = Color3.fromRGB(240, 238, 226); sl.Shadows = true
				sl.Parent = d
			end
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
	parts.rotor, parts.tail, parts.beacon, parts.body = nil, nil, nil, nil
	rate, spin, spinT = 0, 0, 0
end

-- ------------------------------------------------------------------ the reward screen
local rew = T.plate(root, "Reward", UDim2.new(0.5, -250, 0.5, -170), UDim2.fromOffset(500, 340))
rew.Visible = false
local rTitle = T.text(rew, "Title", "", 26, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
rTitle.Position = UDim2.fromOffset(0, 16); rTitle.Size = UDim2.new(1, 0, 0, 32)
local rRows = T.new("Frame", { Name = "Rows", BackgroundTransparency = 1, Position = UDim2.fromOffset(28, 64), Size = UDim2.new(1, -56, 1, -100) }, rew)
T.new("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, rRows)
local rFoot = T.text(rew, "Foot", "", 12, T.DIM, T.FONT_BOLD, Enum.TextXAlignment.Center)
rFoot.Position = UDim2.new(0, 0, 1, -30); rFoot.Size = UDim2.new(1, 0, 0, 18)
local function rline(order: number, a: string, b: string, c: string, col: Color3?)
	local f = T.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 24), LayoutOrder = order }, rRows)
	local l1 = T.text(f, "A", a, 16, T.TEXT, T.FONT_BOLD); l1.Size = UDim2.new(0.5, 0, 1, 0)
	local l2 = T.text(f, "B", b, 15, T.MUTED, T.FONT, Enum.TextXAlignment.Right); l2.Position = UDim2.fromScale(0.5, 0); l2.Size = UDim2.new(0.2, 0, 1, 0)
	local l3 = T.text(f, "C", c, 16, col or T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right); l3.Position = UDim2.fromScale(0.7, 0); l3.Size = UDim2.new(0.3, 0, 1, 0)
end
local WHY = { share = "NOT ENOUGH OF THE SQUAD'S FIGHT", up = "DOWN FOR TOO LONG", active = "NOT ACTIVE ENOUGH", round = "TOO EARLY", error = "SOMETHING BROKE" }
local function showReward(res: any)
	for _, c in rRows:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	rTitle.Text = "EXTRACTED  ·  ROUND " .. tostring(res.n)
	local o = 0
	if res.ok then
		o += 1; rline(o, "BRASS", "", "+" .. tostring(res.brass), T.ACCENT)
		o += 1; rline(o, "XP", "", "+" .. tostring(res.xp), T.ACCENT)
	else
		o += 1; rline(o, "NO REWARDS", "", "", T.DANGER)
		o += 1; rline(o, WHY[res.why] or tostring(res.why or ""), "", "", T.MUTED)
	end
	for _, r in (res.rolls or {}) :: { any } do
		o += 1
		local hit = r.hit == true
		local said = if hit and r.wrap then wrapName(r.wrap) elseif hit then "DROPPED" elseif r.owned then "ALL OWNED" else "—"
		rline(o, XR.names[r.k] or r.k, pct(r.p or 0), said, if hit then T.ACCENT else T.DIM)
	end
	rFoot.Text = if res.dry then "STUDIO TEST  ·  NOTHING WAS GRANTED" else ""
	rew.Visible = true
	task.delay(16, function() rew.Visible = false end)
end
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
	elseif x.k == "xreward" then
		local a = arena()
		local lift = a and a:GetAttribute("XLift")
		local at = if type(lift) == "number" then lift - XC.board + XC.outro else srv()
		task.delay(math.max(0, at - srv()), function() showReward(x.res) end)
	elseif x.k == "xover" then
		local res = x.res
		if type(res) ~= "table" then return end
		xpToast.Text = if res.ok and (res.xp or 0) > 0 then ("+" .. tostring(res.xp) .. " XP" .. (if res.dry then "  (STUDIO TEST)" else ""))
			elseif not res.ok and res.why and WHY[res.why] then ("NO XP  ·  " .. WHY[res.why]) else ""
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
	if parts.rotor then
		parts.rotor.CFrame = cf * parts.rotOff * CFrame.Angles(0, spin, 0)
		parts.rotor.Transparency = math.clamp((rate - 10) / 30, 0, 0.45) -- (a blur at speed)
	end
	if parts.tail then parts.tail.CFrame = cf * parts.tailOff * CFrame.Angles(spinT, 0, 0) end
	if parts.beacon then
		local on = (os.clock() % 1.2) < 0.16
		parts.beacon.Transparency = if on then 0 else 0.75
		local bl = parts.beacon:FindFirstChild("Blink") :: PointLight?
		if bl then bl.Enabled = on end
	end
	lastSt = st
end)
me:GetAttributeChangedSignal("ZmArena"):Connect(function()
	if not me:GetAttribute("ZmArena") then
		offer.Visible = false; hold.Visible = false; mark.Visible = false
		drop()
	end
end)
