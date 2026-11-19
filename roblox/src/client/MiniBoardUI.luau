--!strict
-- CHESS and CHECKERS, your side (shared/MiniGames.luau; server/MiniBoard; the rules: shared/Chess, shared/Checkers).
-- MiniGames.client calls this.
--   world: every client sets the pieces on each games table from the table's Pos (the kit's pieces, painted ivory for
--          A and slate for B), slides the last move across (a little hop; a checkers jump hops square by square), the
--          taken pieces sink away, and two quiet marks show the last move; a king in check sits on a red square
--   your screen: who plays who and whose move, the picker (CHESS / CHECKERS) and the bot buttons before a game,
--          READY with two people, OFFER DRAW / RESIGN in one; the result after. click or tap a piece, then where it
--          goes (its moves shown as quiet dots); a pad moves a square cursor (D-pad or the stick), A picks, X offers a
--          draw, Y resigns
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local MG = require(Shared:WaitForChild("MiniGames")) :: any
local Chess = require(Shared:WaitForChild("Chess")) :: any
local Checkers = require(Shared:WaitForChild("Checkers")) :: any

local M = {}
local me = Players.LocalPlayer
local L = MG.L.board
local LIGHT, DARK = Color3.fromHex("e6e0d4"), Color3.fromHex("525a67")
local PIECE = { P = "mg_pawn", N = "mg_knight", B = "mg_bishop", R = "mg_rook", Q = "mg_queen", K = "mg_king" }

local function now(): number return workspace:GetServerTimeNow() end
local function sqLocal(s: number): Vector3
	local f, r = s % 8, s // 8
	return Vector3.new((f - 3.5) * L.sq, L.surface, (3.5 - r) * L.sq)
end
local function split(s: any): { number }
	local out = {}
	if type(s) ~= "string" then return out end
	for x in string.gmatch(s, "%d+") do table.insert(out, tonumber(x) :: number) end
	return out
end
-- the position as a 64-entry list of piece letters ("" empty) and whose they are ("A" / "B")
local function parse(game: string, pos: string): ({ string }, { string })
	local ch, own = table.create(64, ""), table.create(64, "")
	local board = string.match(pos, "^(%S+)") or ""
	for i = 1, math.min(64, #board) do
		local c = string.sub(board, i, i)
		if c ~= "." then
			ch[i] = c
			if game == "chess" then own[i] = if string.upper(c) == c then "A" else "B"
			else own[i] = if c == "a" or c == "A" then "A" else "B" end
		end
	end
	return ch, own
end

local kitF: Instance? = nil
local function kitPart(name: string): BasePart?
	kitF = kitF or (ReplicatedStorage:FindFirstChild("JankfireMiniGames") and ReplicatedStorage.JankfireMiniGames:FindFirstChild("Kit"))
	local m = kitF and kitF:FindFirstChild(name)
	local p = m and m:FindFirstChildWhichIsA("BasePart")
	return p
end

-- one piece's look: a model of one or two parts, its origin on the square
local function makePiece(game: string, c: string, side: string): Model
	local m = Instance.new("Model")
	m.Name = "Piece"
	local parts: { BasePart } = {}
	if game == "chess" then
		local src = kitPart(PIECE[string.upper(c)] or "mg_pawn")
		if src then table.insert(parts, src:Clone()) end
	else
		local src = kitPart("mg_man")
		if src then
			table.insert(parts, src:Clone())
			if c == "A" or c == "B" then -- (a king: two stacked)
				local top = src:Clone()
				top:SetAttribute("Up", 0.1)
				table.insert(parts, top)
			end
		end
	end
	for _, p in parts do
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Material = Enum.Material.SmoothPlastic
		p.Color = if side == "A" then LIGHT else DARK
		p:SetAttribute("Off", p.CFrame.Position) -- (where it sits in the kit's own frame)
		p:SetAttribute("Rot", p.CFrame - p.CFrame.Position)
		p.Parent = m
	end
	-- a knight looks to its own left (its profile is what you see from your chair)
	local yaw = 0
	if game == "chess" and string.upper(c) == "N" then yaw = if side == "A" then -math.pi / 2 else math.pi / 2 end
	m:SetAttribute("Yaw", yaw)
	return m
end
local function placePiece(m: Model, cf: CFrame)
	local yaw = (m:GetAttribute("Yaw") or 0) :: number
	for _, p in m:GetChildren() do
		if p:IsA("BasePart") then
			local off = (p:GetAttribute("Off") or Vector3.zero) :: Vector3
			local up = (p:GetAttribute("Up") or 0) :: number
			local rot = (p:GetAttribute("Rot") or CFrame.identity) :: CFrame
			p.CFrame = cf * CFrame.Angles(0, yaw, 0) * CFrame.new(off + Vector3.new(0, up, 0)) * rot
		end
	end
end

local function mark(parent: Instance, name: string, color: Color3, alpha: number, size: number?): BasePart
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = color; p.Transparency = alpha
	local s = (size or 1) * L.sq
	p.Size = Vector3.new(s, 0.02, s)
	p.Parent = parent
	return p
end

-- ------------------------------------------------------------------ the world (everyone)
type View = { model: Model, root: BasePart, holder: Folder, pieces: { [number]: { m: Model, c: string, side: string } }, anims: { any },
	game: string, lastSeen: string?, marks: { BasePart }, check: BasePart, local_: { BasePart }, sel: BasePart, cursor: BasePart }
local views: { [Model]: View } = {}

local function boardCF(v: View): CFrame return v.root.CFrame end

local function rebuild(v: View, api: any, animate: boolean)
	local game = (v.model:GetAttribute("Game") or "chess") :: string
	local pos = v.model:GetAttribute("Pos")
	if type(pos) ~= "string" then return end
	if game ~= v.game then
		for _, e in v.pieces do e.m:Destroy() end
		table.clear(v.pieces)
		v.game = game
		animate = false
	end
	local ch, own = parse(game, pos)
	local last = v.model:GetAttribute("Last")
	local cf = boardCF(v)
	-- the move just made: slide that piece along its path, sink what it took
	if animate and type(last) == "string" and last ~= v.lastSeen then
		local path = split(last)
		local from, to = path[1], path[#path]
		local e = from and v.pieces[from]
		if e and to then
			local took = split(v.model:GetAttribute("Took"))
			if v.pieces[to] and not table.find(took, to) then table.insert(took, to) end
			for _, s in took do
				local t = v.pieces[s]
				if t and t ~= e then
					v.pieces[s] = nil
					table.insert(v.anims, { kind = "sink", m = t.m, t0 = os.clock() + 0.2, at = cf * CFrame.new(sqLocal(s)) })
				end
			end
			v.pieces[from] = nil
			v.pieces[to] = e
			local pts = {}
			for _, s in path do table.insert(pts, sqLocal(s)) end
			table.insert(v.anims, { kind = "move", m = e.m, pts = pts, t0 = os.clock(), dur = 0.22 * (#pts - 1) + 0.08, to = to })
			-- castling: the rook comes round too
			if game == "chess" and string.upper(e.c) == "K" and math.abs(to - from) == 2 then
				local rf, rt = if to > from then from + 3 else from - 4, if to > from then from + 1 else from - 1
				local r = v.pieces[rf]
				if r then
					v.pieces[rf] = nil
					v.pieces[rt] = r
					table.insert(v.anims, { kind = "move", m = r.m, pts = { sqLocal(rf), sqLocal(rt) }, t0 = os.clock() + 0.1, dur = 0.3, to = rt })
				end
			end
			task.delay(0.22 * (#path - 1) + 0.1, function()
				-- (a piece set down: the gavel's wooden knock, pitched up and quiet)
				local at = (cf * CFrame.new(sqLocal(to))).Position
				if not api.playAny({ "mini_piece" }, at, 0.45) then api.Sfx.play("gavel_strike", at, 0.2, 1.7) end
			end)
		end
	end
	v.lastSeen = if type(last) == "string" then last else nil
	-- everything else as it should be (a new game, a promotion, a crowning, a first look)
	for i = 1, 64 do
		local s = i - 1
		local e = v.pieces[s]
		local want = ch[i]
		if want == "" then
			if e then e.m:Destroy(); v.pieces[s] = nil end
		elseif not e or e.c ~= want then
			if e then e.m:Destroy() end
			local m = makePiece(game, want, own[i])
			m.Parent = v.holder
			placePiece(m, cf * CFrame.new(sqLocal(s)))
			v.pieces[s] = { m = m, c = want, side = own[i] }
		end
	end
	-- the last move's marks, the check
	local lp = split(last)
	for i, mk in v.marks do
		local s = if i == 1 then lp[1] else lp[#lp]
		mk.Transparency = if s and #lp >= 2 then 0.55 else 1
		if s then mk.CFrame = cf * CFrame.new(sqLocal(s) + Vector3.new(0, 0.011, 0)) end
	end
	local ck = v.model:GetAttribute("Check")
	v.check.Transparency = if type(ck) == "number" then 0.35 else 1
	if type(ck) == "number" then v.check.CFrame = cf * CFrame.new(sqLocal(ck) + Vector3.new(0, 0.012, 0)) end
end

function M.world(model: Model, api: any): ((number) -> ())?
	local root = model:WaitForChild("Root", 10) :: BasePart?
	if not root then return nil end
	local holder = Instance.new("Folder")
	holder.Name = "BoardView"
	holder.Parent = model
	local v: View = { model = model, root = root, holder = holder, pieces = {}, anims = {}, game = "", lastSeen = nil, marks = {},
		check = mark(holder, "Check", api.T.DANGER, 1), local_ = {}, sel = mark(holder, "Sel", api.T.ACCENT, 1), cursor = mark(holder, "Cursor", api.T.TEXT, 1) }
	for i = 1, 2 do table.insert(v.marks, mark(holder, "Last" .. i, Color3.fromRGB(226, 196, 120), 1)) end
	views[model] = v
	rebuild(v, api, false)
	for _, a in { "Pos", "Game" } do
		model:GetAttributeChangedSignal(a):Connect(function() rebuild(v, api, true) end)
	end
	model:GetAttributeChangedSignal("Check"):Connect(function() rebuild(v, api, false) end)
	return function(dt: number)
		if #v.anims == 0 then return end
		local cf = boardCF(v)
		local t = os.clock()
		for i = #v.anims, 1, -1 do
			local a = v.anims[i]
			if a.kind == "move" then
				local u = math.clamp((t - a.t0) / a.dur, 0, 1)
				local legs = #a.pts - 1
				local x = u * legs
				local leg = math.min(legs, math.floor(x) + 1)
				local lu = x - (leg - 1)
				local p0, p1 = a.pts[leg], a.pts[leg + 1]
				local e = lu * lu * (3 - 2 * lu)
				local p = p0:Lerp(p1, e) + Vector3.new(0, math.sin(math.pi * lu) * 0.32, 0)
				placePiece(a.m, cf * CFrame.new(p))
				if u >= 1 then
					placePiece(a.m, cf * CFrame.new(a.pts[#a.pts]))
					table.remove(v.anims, i)
				end
			elseif a.kind == "sink" then
				local u = math.clamp((t - a.t0) / 0.3, 0, 1)
				if u > 0 then
					placePiece(a.m, a.at * CFrame.new(0, -0.5 * u * u, 0))
					for _, p in a.m:GetChildren() do if p:IsA("BasePart") then p.Transparency = u end end
				end
				if u >= 1 then a.m:Destroy(); table.remove(v.anims, i) end
			end
		end
	end
end

-- ------------------------------------------------------------------ your screen
local S: { [string]: any } = {}

local function rules(): any return if S.model:GetAttribute("Game") == "checkers" then Checkers else Chess end
local function state(): any
	local pos = S.model:GetAttribute("Pos")
	if type(pos) ~= "string" then return nil end
	local ok, st = pcall(rules().decode, pos)
	return if ok then st else nil
end
local function myTurn(): boolean
	return S.model:GetAttribute("State") == "play" and S.model:GetAttribute("Turn") == S.side
end
-- the legal moves from s: { [to] = true }
local function targets(s: number): { [number]: boolean }
	local st = state()
	local out = {}
	if not st then return out end
	if S.model:GetAttribute("Game") == "checkers" then
		for _, m in Checkers.legal(st) do if m.path[1] == s then out[m.path[#m.path]] = true end end
	else
		for _, m in Chess.legal(st) do if Chess.from(m) == s then out[Chess.to(m)] = true end end
	end
	return out
end

local function clearDots()
	for _, d in S.dots or {} do d:Destroy() end
	S.dots = {}
end
local function showSel()
	local v = views[S.model]
	if not v then return end
	clearDots()
	if S.sel == nil then v.sel.Transparency = 1; return end
	local cf = v.root.CFrame
	v.sel.Transparency = 0.45
	v.sel.CFrame = cf * CFrame.new(sqLocal(S.sel) + Vector3.new(0, 0.013, 0))
	for to in targets(S.sel) do
		local occupied = v.pieces[to] ~= nil
		local d = mark(v.holder, "Dot", if occupied then S.api.T.DANGER else Color3.fromRGB(240, 242, 245), if occupied then 0.5 else 0.35, if occupied then 0.92 else 0.32)
		if not occupied then d.Shape = Enum.PartType.Cylinder; d.Size = Vector3.new(0.02, 0.32 * L.sq, 0.32 * L.sq) end
		d.CFrame = cf * CFrame.new(sqLocal(to) + Vector3.new(0, 0.014, 0)) * (if occupied then CFrame.identity else CFrame.Angles(0, 0, math.pi / 2))
		table.insert(S.dots, d)
	end
end

local function pick(s: number)
	if not myTurn() then S.sel = nil; showSel(); return end
	local v = views[S.model]
	local e = v and v.pieces[s]
	if S.sel ~= nil and targets(S.sel)[s] then
		S.api.send({ op = "move", from = S.sel, to = s })
		S.sel = nil
		showSel()
		return
	end
	if e and e.side == S.side and next(targets(s)) ~= nil then
		S.sel = s
		S.api.Sfx.play("click", nil, 0.35)
	else
		S.sel = nil
	end
	showSel()
end

local function squareAt(x: number, y: number): number?
	local v = views[S.model]
	if not v then return nil end
	local ray = workspace.CurrentCamera:ScreenPointToRay(x, y)
	local cf = v.root.CFrame
	local o = cf:PointToObjectSpace(ray.Origin)
	local d = cf:VectorToObjectSpace(ray.Direction)
	if math.abs(d.Y) < 1e-4 then return nil end
	local t = (L.surface - o.Y) / d.Y
	if t < 0 then return nil end
	local h = o + d * t
	local f, r = math.floor(h.X / L.sq + 4), math.floor(4 - h.Z / L.sq)
	if f < 0 or f > 7 or r < 0 or r > 7 then return nil end
	return r * 8 + f
end

local RESULT = { mate = "CHECKMATE", resign = "RESIGNED", time = "ON TIME", stale = "STALEMATE", agreed = "DRAW AGREED",
	fifty = "NO PROGRESS IN 50 MOVES", ["repeat"] = "SAME POSITION THREE TIMES", material = "NOT ENOUGH TO MATE", blocked = "NO MOVES LEFT", left = "OPPONENT LEFT" }

local function layout()
	local api = S.api
	local T = api.T
	local m = S.model
	local st = m:GetAttribute("State")
	local o = if S.side == "A" then "B" else "A"
	local oppName = m:GetAttribute(o .. "Name")
	local oppBot = (m:GetAttribute(o .. "Id") or 0) == -1
	local game = (m:GetAttribute("Game") or "chess") :: string
	S.youL.Text = "YOU · " .. (if S.side == "A" then "LIGHT" else "DARK")
	S.oppL.Text = if oppName then string.upper(oppName :: string) .. " · " .. (if S.side == "A" then "DARK" else "LIGHT") else "EMPTY SEAT"
	for _, b in S.panel:GetChildren() do if b:IsA("GuiButton") then b.Visible = false end end
	local shown: { GuiButton } = {}
	local function show(b: GuiButton) b.Visible = true; table.insert(shown, b) end
	S.banner.Text = ""
	S.bannerSub.Text = ""
	if st == "play" then
		local drawBy = m:GetAttribute("Draw")
		if drawBy == o then show(S.acceptB); show(S.declineB) else show(S.drawB) end
		show(S.resignB)
		S.drawB.Text = if drawBy == S.side then "DRAW OFFERED" else "OFFER DRAW"
	else
		show(S.chessB); show(S.checkersB)
		S.chessB.BackgroundColor3 = if game == "chess" then T.CARD_HI else T.CARD
		S.checkersB.BackgroundColor3 = if game == "checkers" then T.CARD_HI else T.CARD
		S.chessB.TextColor3 = if game == "chess" then T.ACCENT else T.TEXT
		S.checkersB.TextColor3 = if game == "checkers" then T.ACCENT else T.TEXT
		if not oppName or oppBot then for _, b in S.botB do show(b) end end
		if oppName and not oppBot then
			show(S.readyB)
			S.readyB.Text = if m:GetAttribute("Ready" .. S.side) then "WAITING" else "READY"
		elseif oppBot and st == "over" then
			show(S.againB)
		end
		if st == "over" then
			local res = m:GetAttribute("Result")
			local why = RESULT[(m:GetAttribute("Why") or "") :: string] or ""
			S.banner.Text = if res == "draw" then "DRAW" elseif res == S.side then "YOU WIN" else "YOU LOSE"
			S.banner.TextColor3 = if res == S.side then T.ACCENT else T.TEXT
			S.bannerSub.Text = why
		elseif not oppName then
			S.bannerSub.Text = "WAITING FOR AN OPPONENT, OR PLAY A BOT"
		elseif m:GetAttribute("Ready" .. o) then
			S.bannerSub.Text = string.upper(oppName :: string) .. " IS READY"
		end
	end
	S.panel.Size = UDim2.fromOffset(170, #shown * 46)
	local y = 0
	for _, b in S.panel:GetChildren() do
		if b:IsA("GuiButton") and b.Visible then b.Position = UDim2.fromOffset(0, (b:GetAttribute("Order") :: number) * 46) end
	end
	-- (the visible ones, packed in their order)
	table.sort(shown, function(a, b) return (a:GetAttribute("Order") :: number) < (b:GetAttribute("Order") :: number) end)
	for i, b in shown do b.Position = UDim2.fromOffset(0, (i - 1) * 46); y = i end
	S.first = shown[1]
	api.nav(api.padOn() and st ~= "play", shown[1])
	if st ~= "play" then S.sel = nil; showSel() end
end

function M.open(api: any, model: Model, side: string)
	local T = api.T
	S = { api = api, model = model, side = side, sel = nil, dots = {}, conns = {}, botB = {}, cur = if side == "A" then 4 else 59, repT = 0, confirmResign = 0 }
	local root = api.root
	local info = T.plate(root, "Info", UDim2.new(0, 18, 0, 18), UDim2.fromOffset(330, 76))
	S.youL = T.text(info, "You", "", 14, T.ACCENT, T.FONT_BOLD)
	S.youL.Position = UDim2.fromOffset(14, 8); S.youL.Size = UDim2.new(1, -28, 0, 18)
	S.oppL = T.text(info, "Opp", "", 14, T.SOFT, T.FONT_BOLD)
	S.oppL.Position = UDim2.fromOffset(14, 28); S.oppL.Size = UDim2.new(1, -28, 0, 18)
	S.turnL = T.text(info, "Turn", "", 13, T.MUTED, T.FONT_TITLE)
	S.turnL.Position = UDim2.fromOffset(14, 50); S.turnL.Size = UDim2.new(1, -28, 0, 18)
	S.banner = T.text(root, "Banner", "", 34, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.banner.AnchorPoint = Vector2.new(0.5, 0.5); S.banner.Position = UDim2.fromScale(0.5, 0.2); S.banner.Size = UDim2.fromOffset(600, 44)
	S.bannerSub = T.text(root, "BannerSub", "", 15, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.bannerSub.AnchorPoint = Vector2.new(0.5, 0); S.bannerSub.Position = UDim2.new(0.5, 0, 0.2, 26); S.bannerSub.Size = UDim2.fromOffset(600, 20)
	S.panel = T.new("Frame", { Name = "Panel", BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -18, 0.55, 0), Size = UDim2.fromOffset(170, 200) }, root)
	local order = 0
	local function btn(name: string, text: string, accent: boolean?, fn: () -> ()): TextButton
		local b = api.button(S.panel, name, text, UDim2.new(), UDim2.fromOffset(170, 40), accent)
		order += 1
		b:SetAttribute("Order", order)
		b.Activated:Connect(fn)
		return b
	end
	S.chessB = btn("Chess", "CHESS", false, function() api.send({ op = "pick", game = "chess" }) end)
	S.checkersB = btn("Checkers", "CHECKERS", false, function() api.send({ op = "pick", game = "checkers" }) end)
	for i, lv in MG.LEVELS do
		S.botB[i] = btn("Bot_" .. lv, "BOT · " .. MG.LEVEL_NAME[lv], i == 2, function() api.send({ op = "bot", level = lv }) end)
	end
	S.readyB = btn("Ready", "READY", true, function() api.send({ op = "ready" }) end)
	S.againB = btn("Again", "PLAY AGAIN", true, function() api.send({ op = "ready" }) end)
	S.drawB = btn("Draw", "OFFER DRAW", false, function() if model:GetAttribute("Draw") ~= side then api.send({ op = "draw" }) end end)
	S.acceptB = btn("Accept", "ACCEPT DRAW", true, function() api.send({ op = "draw" }) end)
	S.declineB = btn("Decline", "DECLINE", false, function() api.send({ op = "decline" }) end)
	local function resign()
		if os.clock() - S.confirmResign < 3 then api.send({ op = "resign" }); S.confirmResign = 0; S.resignB.Text = "RESIGN"
		else S.confirmResign = os.clock(); S.resignB.Text = "PRESS AGAIN"
			task.delay(3, function() if S.resignB and os.clock() - S.confirmResign >= 2.9 then S.resignB.Text = "RESIGN" end end) end
	end
	S.resign = resign
	S.resignB = btn("Resign", "RESIGN", false, resign)
	S.note = T.text(root, "Note", "", 14, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.note.AnchorPoint = Vector2.new(0.5, 1); S.note.Position = UDim2.new(0.5, 0, 1, -18); S.note.Size = UDim2.fromOffset(700, 20)
	for _, a in { "State", "AName", "BName", "AId", "BId", "Game", "Draw", "ReadyA", "ReadyB", "Result", "Why" } do
		table.insert(S.conns, model:GetAttributeChangedSignal(a):Connect(layout))
	end
	table.insert(S.conns, model:GetAttributeChangedSignal("Pos"):Connect(function()
		S.sel = nil; showSel()
		if model:GetAttribute("State") == "play" and model:GetAttribute("Turn") == side then api.Sfx.play("loot_tick", nil, 0.35) end
	end))
	-- clicks and taps on the board
	table.insert(S.conns, UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
		if gp then return end
		if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then
			local s = squareAt(io.Position.X, io.Position.Y)
			if s then S.cur = s; pick(s) elseif S.sel then S.sel = nil; showSel() end
		end
		-- the pad's square cursor
		local k = io.KeyCode
		local d = if k == Enum.KeyCode.DPadUp then 8 elseif k == Enum.KeyCode.DPadDown then -8 elseif k == Enum.KeyCode.DPadRight then 1 elseif k == Enum.KeyCode.DPadLeft then -1 else 0
		if d ~= 0 and model:GetAttribute("State") == "play" then
			if side == "B" then d = -d end
			local f, r = S.cur % 8, S.cur // 8
			if math.abs(d) == 1 then f = math.clamp(f + d, 0, 7) else r = math.clamp(r + d // 8, 0, 7) end
			S.cur = r * 8 + f
			S.curMoved = os.clock()
		end
		if k == Enum.KeyCode.ButtonX and model:GetAttribute("State") == "play" then
			if model:GetAttribute("Draw") == (if side == "A" then "B" else "A") or model:GetAttribute("Draw") ~= side then api.send({ op = "draw" }) end
		elseif k == Enum.KeyCode.ButtonY and model:GetAttribute("State") == "play" then
			S.resign()
		end
	end))
	layout()
	-- the camera: over your side of the board, looking down on it
	local mirror = if side == "A" then 1 else -1
	api.camera = function(): CFrame?
		local r = model:FindFirstChild("Root") :: BasePart?
		if not r then return nil end
		local eye = r.CFrame * Vector3.new((L.cam.side or 0) * mirror, L.surface + L.cam.up, L.cam.back * mirror)
		local at = r.CFrame * Vector3.new(0, L.surface, -L.cam.aim * mirror)
		return CFrame.lookAt(eye, at)
	end
	-- what the camera must see (MiniGames.client fades an accessory only if it stands in front of one of these)
	api.viewPoints = function(): { Vector3 }
		local r = model:FindFirstChild("Root") :: BasePart?
		if not r then return {} end
		local e = 4 * L.sq
		local out = {}
		for _, o in { Vector3.zero, Vector3.new(-e, 0, e), Vector3.new(e, 0, e), Vector3.new(-e, 0, -e), Vector3.new(e, 0, -e), Vector3.new(0, 0, e), Vector3.new(-e, 0, 0), Vector3.new(e, 0, 0) } do
			table.insert(out, r.CFrame * (Vector3.new(0, L.surface + 0.3, 0) + o))
		end
		return out
	end
	api.fov = 58
	-- the piece you point at (or have picked, or the pad's square is on), named (the owner, 19 Nov: "chess pieces
	-- should be easier to tell what they are"; the pieces got their own outlines too)
	local NAMES = { P = "PAWN", N = "KNIGHT", B = "BISHOP", R = "ROOK", Q = "QUEEN", K = "KING" }
	S.pieceL = T.text(root, "Piece", "", 18, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.pieceL.AnchorPoint = Vector2.new(0.5, 1); S.pieceL.Position = UDim2.new(0.5, 0, 1, -44); S.pieceL.Size = UDim2.fromOffset(300, 24)
	S.step = RunService.RenderStepped:Connect(function(dt: number)
		local st = model:GetAttribute("State")
		local o = if side == "A" then "B" else "A"
		do
			local s: number? = S.sel
			if s == nil and api.padOn() then s = S.cur end
			if s == nil and not api.isTouch() then
				local mp = UIS:GetMouseLocation()
				local inset = game:GetService("GuiService"):GetGuiInset()
				s = squareAt(mp.X, mp.Y - inset.Y)
			end
			local v = views[model]
			local e = s ~= nil and v and v.pieces[s :: number] or nil
			local name = e and model:GetAttribute("Game") == "chess" and NAMES[string.upper(tostring(e.c))] or nil
			S.pieceL.Text = name or ""
			S.pieceL.TextColor3 = if e and e.side == side then T.ACCENT else T.SOFT
		end
		if st == "play" then
			local mine = model:GetAttribute("Turn") == side
			local left = MG.BOARD.MOVE_LIMIT - (now() - ((model:GetAttribute("MoveAt") or now()) :: number))
			S.turnL.Text = (if mine then "YOUR MOVE" else "THEIR MOVE") .. (if left < 30 then ("  ·  %d s"):format(math.max(0, math.ceil(left))) else "")
			S.turnL.TextColor3 = if mine then T.ACCENT else T.MUTED
			S.note.Text = if model:GetAttribute("Draw") == o then "A DRAW IS OFFERED" elseif api.padOn() then "MOVE THE SQUARE · " .. api.Pad.short("ButtonA") .. " PICK · " .. api.Pad.short("ButtonX") .. " DRAW · " .. api.Pad.short("ButtonY") .. " RESIGN" else ""
		else
			S.turnL.Text = ""
			S.note.Text = ""
		end
		-- the pad: the stick steps the cursor too
		local v = views[model]
		if v then
			local pad = api.padOn() and st == "play"
			if pad then
				local stick = api.Pad.stick(1)
				if stick.Magnitude > 0.55 and os.clock() - S.repT > 0.18 then
					S.repT = os.clock()
					local dx = if math.abs(stick.X) > 0.5 then (if stick.X > 0 then 1 else -1) else 0
					local dy = if math.abs(stick.Y) > 0.5 then (if stick.Y > 0 then 1 else -1) else 0
					if side == "B" then dx, dy = -dx, -dy end
					local f, r = math.clamp(S.cur % 8 + dx, 0, 7), math.clamp(S.cur // 8 + dy, 0, 7)
					S.cur = r * 8 + f
				end
				v.cursor.Transparency = 0.6
				v.cursor.Size = Vector3.new(L.sq, 0.02, L.sq)
				v.cursor.CFrame = v.root.CFrame * CFrame.new(sqLocal(S.cur) + Vector3.new(0, 0.016, 0))
			else
				v.cursor.Transparency = 1
			end
		end
	end)
end

function M.close()
	if S.step then S.step:Disconnect() end
	for _, c in S.conns or {} do c:Disconnect() end
	clearDots()
	local v = S.model and views[S.model]
	if v then v.sel.Transparency = 1; v.cursor.Transparency = 1 end
	if S.api then S.api.camera = nil; S.api.fov = nil; S.api.nav(false) end
	S = {}
end

function M.remote(d: any)
	if d.op == "no" and S.note then
		S.note.Text = if d.why == "declined" then "THE BOT DECLINED" elseif d.why == "turn" then "NOT YOUR MOVE" else "NOT A LEGAL MOVE"
		S.api.Sfx.play("empty", nil, 0.4)
		task.delay(2, function() if S.note and S.note.Text ~= "" then S.note.Text = "" end end)
	end
end

function M.space(down: boolean, io: any): boolean
	if not S.model then return false end
	if io and io.KeyCode == Enum.KeyCode.ButtonA then
		if down and S.model:GetAttribute("State") == "play" then pick(S.cur) end
		return true
	end
	return false
end

function M.back(): boolean
	if S.sel ~= nil then S.sel = nil; showSel(); return true end
	return false
end

function M.confirmLeave(): string?
	if S.model and S.model:GetAttribute("State") == "play" then return "PRESS AGAIN TO LEAVE: YOU RESIGN" end
	return nil
end

function M.test(v: string): string
	local a, b = string.match(v, "^board:move:(%d+),(%d+)$")
	if a and b then
		S.sel = tonumber(a); S.api.send({ op = "move", from = tonumber(a), to = tonumber(b) }); return "sent"
	end
	local s = string.match(v, "^board:pick:(%d+)$")
	if s then pick(tonumber(s) :: number); return "sel " .. tostring(S.sel) .. " dots " .. #(S.dots or {}) end
	return game:GetService("HttpService"):JSONEncode({ sel = S.sel, state = S.model and S.model:GetAttribute("State"), turn = S.model and S.model:GetAttribute("Turn"), pos = S.model and S.model:GetAttribute("Pos") })
end

return M
