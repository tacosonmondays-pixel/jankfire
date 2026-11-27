--!nocheck
-- THE ROTUNDA, LARGER, WITH THE HOTEL'S SPAWN (26 Nov 2026). The owner: "The hotel hub looks cute but I like the round
-- circle pad area of the current one and the hotel spawn area can the current main hub be redone just larger? Can you
-- make a few versions of that?" Main's reading: keep THE ROTUNDA's design and its round pad ring, make the room bigger
-- (never the pads), and bring THE HOTEL's lobby across as it is, as the place you spawn into before walking into the ring.
-- Not a new builder:
--   * the ring: HubRotunda's pre-v3 form (Layout "lifts", palette "glow") through its own plan warp (Hub v3's: plan x K,
--     heights by a band map) at this version's K; its old lounge wing (and the VIP room behind it) taken away; sides 6
--     and 8 walls (R.OPEN), side 7 one wide opening under its lintel; its pads swapped after the warp for HubKit's classic
--     pads at their own size (K.CLASSIC_SIZE, pastel TeamColors), each where the old one stood, facing into its bay, its
--     board flat on the bay's back wall: the bays grow with K, the pads don't
--   * the lobby: HubHotel's lobby alone (opts.lobbyOnly: its VIP suite, lifts, reception, loadout, bundles, zombies room)
--     with one wide opening in its N wall (opts.northOpen) against the ring's side 7
-- Versions (HRH.V): A 1.3 joined straight on; B 1.6 joined straight on (more floor between the pads); C 1.6, the lobby
-- raised as a landing that looks over the ring, wide steps down. Staging only until the owner picks.
--   usage (Edit): local HRH = require(game.ServerStorage.PolishBackup.HubRotHotel:Clone()); print(HRH.build("A", workspace.HubStaging))
local HRH = {}
HRH.V = {
	A = { k = 1.3, lift = 0, site = Vector3.new(-1800, 240, -40000) },
	B = { k = 1.6, lift = 0, site = Vector3.new(-1800, 240, -42000) },
	C = { k = 1.6, lift = 4.5, site = Vector3.new(-1800, 240, -44000) },
}
local PB = game:GetService("ServerStorage"):WaitForChild("PolishBackup")
local CS = game:GetService("CollectionService")

local function rotunda(k)
	local m = PB.HubRotunda:Clone(); m:SetAttribute("Layout", "lifts"); m:SetAttribute("LoungeStyle", "lounge")
	local R = require(m); m:Destroy()
	-- the warp at this K; the heights' band map eased toward Hub v3's by how far K is past 1 (1.5 = v3's own)
	local t = math.clamp((k - 1) / 0.5, 0, 1.25)
	local H = {}
	for i, p in R.V3.H do H[i] = { p[1], p[1] + (p[2] - p[1]) * t } end
	R.HALL_K = k; R.V3.K = k; R.V3.H = H
	R.OPEN[6] = nil; R.OPEN[8] = nil -- (walls: the lobby comes in through side 7 alone)
	return R
end

-- the parts' frame-local box: x across, y up, d out along F's look (d = -z)
local function inBox(F, p)
	local v = F:PointToObjectSpace(p)
	return v.X, v.Y, -v.Z
end

function HRH.build(which, parent, opts)
	opts = opts or {}
	assert(game:GetService("RunService"):IsEdit(), "Edit mode only")
	local V = HRH.V[which]; assert(V, "no version " .. tostring(which))
	local site = opts.site or V.site
	local k = V.k
	-- (26 Nov, the owner picked B: "B (1.6x, flat join)", the new default hub) opts.live: built to go into Map.Hub
	-- (HRH.install), the lobby's light zone made; opts.fixes: the judges' five fixes (HRH.fixes); opts.name / lobbyName
	local LIVE, FIX = opts.live == true, opts.fixes == true
	local name = opts.name or ("RotHotel_" .. which)
	local old = parent:FindFirstChild(name); if old then old:Destroy() end
	local near = workspace:GetPartBoundsInBox(CFrame.new(site + Vector3.new(0, 30, 40)), Vector3.new(320, 120, 360), OverlapParams.new())
	if #near > 0 then return "the site is not empty: " .. near[1]:GetFullName() end
	local out = {}
	local root = Instance.new("Folder"); root.Name = name; root.Parent = parent
	root:SetAttribute("MiniGamesOff", true); root:SetAttribute("Version", which); root:SetAttribute("K", k); root:SetAttribute("Site", site)
	root:SetAttribute("LobbyName", opts.lobbyName or "Lobby")

	-- 1. the ring
	local R = rotunda(k)
	R.ROOM = "Ring"
	local ok, res = pcall(R.build, "stage", { version = 3, palette = "glow", at = site, stage = "HubStage_" .. name })
	if not ok then return "RING BUILD ERROR: " .. tostring(res) end
	table.insert(out, "ring: " .. tostring(res):sub(1, 160))
	local stage = workspace.Map:FindFirstChild("HubStage_" .. name)
	local ring = stage and stage:FindFirstChild("Ring")
	if not ring then return table.concat(out, "\n") .. "\nno ring" end
	ring.Parent = root
	stage:Destroy()
	local A, T = R.A, R.WALL
	local F7 = R.frame(site, 180, 0) -- (the lounge's side, due south: +x west, d south)
	local hm = function(y) return R.hmap(R.V3.H, y) end
	-- 2. the old lounge wing and the VIP room behind it, the ring's own spawns and arrivals, away
	local LX, cx, cd = R.LOUNGE_X + 2.5, 20.6, 25.2 - 1.5
	local cut = 0
	local function wing(p)
		local x, y, d = inBox(F7, p)
		if d <= 0 or math.abs(x) > LX * k then return false end
		return d > (A + T + 0.3) * k or (math.abs(x) > cx * k and d > cd * k)
	end
	local function inModel(d) local q = d.Parent; while q and q ~= ring do if q:IsA("Model") then return true end; q = q.Parent end; return false end
	local doomed = {}
	for _, d in ring:GetDescendants() do
		if d:IsA("Model") and not inModel(d) then
			local cf = d:GetBoundingBox()
			if wing(cf.Position) then doomed[d] = true end
		elseif d:IsA("BasePart") and not inModel(d) then -- (a loose part: not inside a model below the ring; Workspace itself is a Model)
			if wing(d.Position) then doomed[d] = true end
		end
	end
	for d in doomed do if d.Parent then d:Destroy(); cut += 1 end end
	local g = ring:FindFirstChild("Game")
	for _, n in { "HubSpawns", "HubArrive" } do local f = g and g:FindFirstChild(n); if f then f:ClearAllChildren() end end
	-- 3. sides 6 and 8: walls now, their arch stones and the collision boxes that held the arch open away; side 7: one
	-- wide opening up to its lintel (the arch, its boxes, its threshold glow and its word away)
	local wo = (A + T) * math.tan(math.pi / R.N) -- (a side's half width at its outer face, before the warp)
	local function sideCut(side, opening)
		local Fs = R.frame(site, side * 360 / R.N, 0)
		local n = 0
		for _, d in ring:GetDescendants() do
			if d:IsA("BasePart") then
				local x, y, dd = inBox(Fs, d.Position)
				local nm = d.Name
				local arch = nm:match("^Arch") or nm == "ArchBoxL" or nm == "ArchBoxR"
				local inSide = math.abs(x) < wo * k + 0.5 and dd > (A - 1.5) * k and dd < (A + T + 1.5) * k
				if inSide and (arch or (opening and (nm == "Threshold" or nm == "DoorGlow" or nm:match("^Way_")) )) then d:Destroy(); n += 1 end
			elseif d:IsA("Model") and d.Name:match("^Way_") then
				local x, y, dd = inBox(Fs, (d:GetBoundingBox()).Position)
				if opening and math.abs(x) < wo * k + 0.5 and dd > (A - 4) * k then d:Destroy(); n += 1 end
			end
		end
		return n
	end
	table.insert(out, ("lounge wing away: %d pieces; arches away: side 6 %d, side 8 %d, side 7 %d"):format(cut, sideCut(6), sideCut(8), sideCut(7, true)))
	local headY = hm(12) -- (the lintel's underside: the opening's head)

	-- 4. the pads: HubKit's classic pads at their own size where the old ones stood
	local K = require(PB.HubKit:Clone())
	local S = K.S
	local qp = Instance.new("Folder"); qp.Name = "QueuePads"; qp.Parent = root
	for _, n in { "Scenery", "Shell", "HubSpawns", "HubArrive" } do local f = Instance.new("Folder"); f.Name = n; f.Parent = root end
	S.root = root; S.site = CFrame.new(); S.hub = "rothotel"; S.live = false; S.style = "warm"; S.accent = "5fbcbf"; S.count = 0; S.lamps = 0; S.missing = 0
	local walls = {}
	for _, d in ring:GetDescendants() do if d:IsA("BasePart") and (d.Name == "BackWall" or d.Name == "UpperWall") then table.insert(walls, d) end end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = walls -- (the bays' back walls only: not the old board in front of one)
	local byId = {}; for _, md in K.MODES do byId[md.id] = md end
	local oldPads = (g and g:FindFirstChild("QueuePads")) and g.QueuePads:GetChildren() or {}
	local made, bad = 0, {}
	for _, m in oldPads do
		local base, s1 = m:FindFirstChild("Base"), m:FindFirstChild("Side1")
		local md = byId[m:GetAttribute("Mode")]
		if not (base and s1 and md) then table.insert(bad, m.Name); continue end
		local out3 = s1.CFrame.LookVector * Vector3.new(1, 0, 1); out3 = out3.Unit -- (into the bay)
		local c = base.Position
		local floorY = base.Position.Y - base.Size.Y / 2
		local sz = K.CLASSIC_SIZE[md.id] or { 13.6, 11 }
		local upper = m:GetAttribute("Bank") == "upper"
		local by = if upper then (if FIX then 5.0 else 5.4) else 7.2 -- (the screen style's upper boards a step lower: the wall's band over them)
		-- the bay's back wall behind it: a ray out from the pad at the board's height
		local hit = workspace:Raycast(Vector3.new(c.X, floorY + by, c.Z), out3 * 40, rp)
		local wallAt = if hit then hit.Position else (c + out3 * (sz[2] / 2 + 1))
		local back = Vector3.new(wallAt.X, floorY, wallAt.Z) - out3 * 0.6 -- (the pad's back edge 0.6 off the wall)
		local front = back - out3 * sz[2]
		local fpos = Vector3.new(front.X, floorY, front.Z)
		-- (keep the old pad's middle if the new one fits there; else against the wall)
		local fOld = Vector3.new(c.X, floorY, c.Z) - out3 * sz[2] / 2
		if (Vector3.new(c.X, 0, c.Z) - Vector3.new(wallAt.X, 0, wallAt.Z)).Magnitude > sz[2] / 2 + 0.8 then fpos = fOld end
		local F = CFrame.lookAt(fpos, fpos + out3)
		-- (0.05 off the wall: K.padClassic's board stands wholly in front of boardAt since 27 Nov)
		local boardAt = CFrame.lookAt(Vector3.new(wallAt.X, floorY + by, wallAt.Z) - out3 * 0.05, Vector3.new(wallAt.X, floorY + by, wallAt.Z) - out3)
		-- the old pad, its bezel and its board's frame away
		local oc = m:GetPivot().Position
		for _, d in ring:GetDescendants() do
			if (d:IsA("Model") and d.Name == "Bezel") or (d:IsA("BasePart") and d.Name == "BoardFrame") then
				local p = if d:IsA("Model") then (d:GetBoundingBox()).Position else d.Position
				if (Vector3.new(p.X, 0, p.Z) - Vector3.new(wallAt.X, 0, wallAt.Z)).Magnitude < 3 and math.abs(p.Y - (floorY + by)) < 4 then d:Destroy() end
			end
		end
		local nm, bank = m.Name, m:GetAttribute("Bank")
		-- (the UPSTAIRS board's rows are copies of an upper pad's count kept inside that pad (Mirror): they go to the new one)
		local mirrors = {}
		for _, c in m:GetChildren() do if c:GetAttribute("Mirror") then c.Parent = root; table.insert(mirrors, c) end end
		m:Destroy()
		-- (an upper bay's guide rails stand either side of its old, narrower board: the new board fits between them)
		local bw
		if upper then
			local lim = math.huge
			for _, d in ring:GetDescendants() do
				if d:IsA("BasePart") and d.Name == "UpperRail" then
					local lp = boardAt:PointToObjectSpace(d.Position)
					if math.abs(lp.Z) < 3 and math.abs(lp.X) < 12 and math.abs(lp.Y) < 8 then lim = math.min(lim, math.abs(lp.X) - d.Size.X / 2) end
				end
			end
			if lim < 6.6 then bw = math.max(6, 2 * (lim - 0.6)) end -- (the frame is 0.5 wider each side; 0.1 to spare)
		end
		local np = K.padClassic(F, md, bank, nm, { boardAt = boardAt, boardW = bw, screen = FIX, boardH = if FIX and upper then 6.0 else nil })
		for _, c in mirrors do
			c.Parent = np
			for _, l in c:GetDescendants() do
				if l:IsA("TextLabel") and l.Name == "Status" then -- (its counts in the classic pads' team colours)
					local counts = {}
					for t = 1, md.teams do table.insert(counts, ('<font color="#%s">0/%d</font>'):format(K.TEAM[t], md.size)) end
					l.Text = table.concat(counts, "   vs   ")
				end
			end
		end
		made += 1
	end
	-- (the ring's way out to training: its door data kept for HRH.install, which hands it to Map.Hub.Doors as every hub's)
	local dr = g and g:FindFirstChild("Doors")
	if dr then dr.Parent = root end
	if g then g:Destroy() end
	table.insert(out, ("pads: %d classic pads at their own size%s"):format(made, if #bad > 0 then "; missed " .. table.concat(bad, ",") else ""))

	-- 5. the lobby, against side 7, its N opening as wide as the side's
	local HH = require(PB.HubHotel:Clone())
	-- (no wider than the clear way between the two piers that flank side 7: the opening stops at their faces)
	local clear, pierZ = math.huge, math.huge -- (and the piers' nearest reach toward the middle, where C's step cheeks stop)
	do
		-- (each pier part's box corners near the opening: the nearest to the middle line is the pier's inner edge; the
		-- piers' parts are not queryable, so no rays)
		local z0, z1 = (A - 0.2) * k - 6, (A + T) * k + 0.5
		for _, d in ring:GetDescendants() do
			if d:IsA("BasePart") and d:FindFirstAncestor("Pier") then
				local o = d.Position - site
				if o.Z > z0 - 6 and o.Z < z1 + 6 and math.abs(o.X) < wo * k + 6 then
					for _, cx in { -0.5, 0.5 } do for _, cz in { -0.5, 0.5 } do
						local c = (d.CFrame * CFrame.new(d.Size.X * cx, 0, d.Size.Z * cz)).Position - site
						if c.Z > z0 and c.Z < z1 then clear = math.min(clear, math.abs(c.X)) end
						if c.Z > z0 - 6 then pierZ = math.min(pierZ, c.Z) end
					end end
				end
			end
		end
	end
	local half = math.min(wo * k - 1.4, clear - 0.1)
	local lobbyZ = (A + T) * k + 34
	local lift = V.lift
	local ok2, lob = pcall(HH.build, K, root, opts.lobbyName or "Lobby", CFrame.new(site + Vector3.new(0, lift, lobbyZ)), LIVE,
		{ lobbyOnly = true, northOpen = { -half, half, math.min(headY - lift, 16) }, withBar = FIX, northPortal = FIX, lookZ0 = -33,
			golfZ = { -21, 73 } }) -- (the golf room 29 further from the ring: its gym reaches 61 out toward the lobby)
	if not ok2 then return table.concat(out, "\n") .. "\nLOBBY BUILD ERROR: " .. tostring(lob) end
	table.insert(out, ("lobby: %d instances, at z +%.1f, %.1f up; its opening %.1f wide, %.1f high"):format(#lob:GetDescendants(), lobbyZ, lift, 2 * half, math.min(headY - lift, 16)))
	-- the opening's passage: a floor and a lid through the ring's wall and the lobby's, the same width
	S.root = root; S.site = CFrame.new()
	local P = K.P
	local zIn, zOut = (A - 0.2) * k, lobbyZ - 32
	local function wbox(name, x0, x1, y0, y1, z0, z1, hex, mat, o)
		return K.part("Shell", name, CFrame.new(site + Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), Vector3.new(x1 - x0, y1 - y0, z1 - z0), hex, mat, o)
	end
	local zMid = (zIn + (A + T) * k) / 2
	if FIX then -- (the judges: the warm hotel meets the cool ring at a threshold: the lobby's stone, a cream sill, the ring's floor)
		wbox("PassageFloor", -half, half, lift - 1, lift - 0.03, zMid + 0.45, (A + T) * k, "a39784")
		wbox("Threshold", -half, half, lift - 1, lift + 0.03, zMid - 0.45, zMid + 0.45, "d9cdb5") -- (0.03 proud: it shows over the ring's floor, no flicker)
		wbox("PassageFloor", -half, half, lift - 1, lift - 0.03, zIn, zMid - 0.45, "4a515c")
	else
		wbox("PassageFloor", -half, half, lift - 1, lift - 0.03, zIn, (A + T) * k, "a3947f") -- (through the ring's wall only, a hair under the floors either side)
	end
	-- 6. C: the landing just inside the ring at the lobby's height, wide steps down to the ring's floor
	if lift > 0 then
		local land = 5
		wbox("Landing", -half, half, -1, lift, zIn - land, zIn, "a3947f")
		local n = math.ceil(lift / 0.5)
		local run = 1.1
		for i = 1, n do
			local top = lift - i * (lift / n)
			if top > 0.01 then wbox("Step", -half, half, -1, top, zIn - land - i * run, zIn - land - (i - 1) * run, "b8aa93") end
		end
		-- (the cheeks stop where the piers begin: between the piers the landing is walled by them)
		for _, s in { -1, 1 } do wbox("StepCheek", s * half, s * (half + 1), -1, lift + 0.6, zIn - land - n * run, math.min(zIn, pierZ - 0.05), P.cream) end
		table.insert(out, ("C: a landing %.1f up, %d steps"):format(lift, n))
	end
	-- 7. the judges' fixes in the ring (HRH.fixes): the teal glow quieted, the training gate, the passage's light, a spectate board
	if FIX then table.insert(out, HRH.fixes(root, ring, R, K, site, k, { zIn = zIn, zOut = (A + T) * k, half = half, lift = lift, headY = headY })) end
	-- 8. the arrival and the spawns are the lobby's (K.begin made them under Lobby); the ring's way out to training stays
	table.insert(out, ("spawns %d (lobby), pads %d, parts %d"):format(#lob.HubSpawns:GetChildren(), #qp:GetChildren(), #root:GetDescendants()))
	return table.concat(out, "\n"), root
end

-- the judges' fixes for the ring part (26 Nov, the owner picked B; the twelve judges' common notes):
--   * the teal glow quieted so the pads are the brightest things: every teal/cyan neon in the ring (the dais rings, the
--     jump discs, the outlines round the balcony openings, the sill lines, the dome's ring) becomes a plain muted teal;
--     the bays' white ceiling panels and the thin white pier tubes a step down
--   * the training gate reads as a way in: its amber light bar over the head gone, the red lasers softer (TrainingDoors
--     keeps whatever see-through they start with), TRAINING named over the gate
--   * the passage: a warm light at its lobby end, a cooler one at the ring's (the light steps down between them)
--   * a spectate board on the ring's side-8 wall (the lounge that had one is gone)
local TEAL_MUTED, PANEL_DIM, TUBE_DIM = "6c8b89", "d6cebf", "c9c1b2"
function HRH.fixes(root, ring, R, K, site, k, o)
	local out = {}
	local quiet, dimmed = 0, 0
	for _, d in ring:GetDescendants() do
		if d:IsA("BasePart") and d.Material == Enum.Material.Neon then
			local h, sat, v = d.Color:ToHSV()
			if h > 0.42 and h < 0.58 and sat > 0.3 then
				d.Material = Enum.Material.SmoothPlastic; d.Color = Color3.fromHex(TEAL_MUTED); quiet += 1
				for _, l in d:GetChildren() do if l:IsA("Light") then l.Brightness *= 0.35 end end
			elseif sat < 0.2 and v > 0.85 then
				if d.Name == "PadCoffer" or d.Name == "BayGlow" then d.Color = Color3.fromHex(PANEL_DIM); dimmed += 1
				elseif d.Name:match("FinLight$") or d.Name == "PierBackLight" then d.Color = Color3.fromHex(TUBE_DIM); dimmed += 1 end
			end
		end
	end
	-- (ZFight: the balcony decks' lip strip, glowing no more, lay 0.02 over the deck and flickered: the decks keep their edge)
	local lips = 0
	for _, d in ring:GetDescendants() do if d:IsA("BasePart") and d.Name == "UpperNosing" then d:Destroy(); lips += 1 end end
	table.insert(out, ("glow: %d teal neons quieted, %d white panels and tubes a step down, %d deck lip strips away"):format(quiet, dimmed, lips))
	-- the gate
	local gate, lasers, bars = nil, 0, 0
	for _, d in ring:GetDescendants() do
		if d.Name == "GateLightBar" then d:Destroy(); bars += 1
		elseif d:IsA("BasePart") and d.Name == "LaserBar" then d.Transparency = math.max(d.Transparency, 0.35); lasers += 1
		elseif d:IsA("BasePart") and d.Name == "LaserField" then d.Transparency = math.max(d.Transparency, 0.94)
		elseif d:IsA("Model") and d.Name == "TrainingShutter" then gate = d end
	end
	local S = K.S
	S.root = root; S.site = CFrame.new()
	if gate then
		local c, top = gate:GetAttribute("Center"), gate:GetAttribute("Top")
		if typeof(c) == "Vector3" and type(top) == "number" then
			local dg = Vector3.new(site.X - c.X, 0, site.Z - c.Z).Unit
			local at = Vector3.new(c.X, top + 1.8, c.Z) + dg * 2.0 -- (on the face of the portal kit's head, which stands 1.86 out)
			K.wordSign(CFrame.lookAt(at, at + dg), "Scenery", "GateSign", 7.4, 1.5, 0, 0, 0, "TRAINING", { accent = S.accent or "5fbcbf", bg = "28324a" })
		end
	end
	table.insert(out, ("gate: light bar %d away, %d lasers softer, TRAINING over it: %s"):format(bars, lasers, tostring(gate ~= nil)))
	-- the passage's light, warm at the lobby's end, cooler at the ring's
	local function lamp(nm, z, hex, br)
		local p = Instance.new("Part"); p.Name = nm; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Transparency = 1; p.Size = Vector3.new(0.4, 0.4, 0.4); p.CFrame = CFrame.new(site + Vector3.new(0, o.lift + math.min(o.headY - o.lift, 16) - 1.2, z))
		local l = Instance.new("PointLight"); l.Color = Color3.fromHex(hex); l.Range = 14; l.Brightness = br; l.Shadows = false; l.Parent = p
		p.Parent = root:FindFirstChild("Scenery") or root
	end
	lamp("PassageLampWarm", o.zOut + 1.0, "ffe2b8", 0.9)
	lamp("PassageLampCool", o.zIn - 0.5, "dfe8ff", 0.6)
	-- a spectate board on side 8's wall, under the balcony
	local Fs = R.frame(site, 8 * 360 / R.N, 0)
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { ring }
	local hit = workspace:Raycast(site + Vector3.new(0, 5, 0), Fs.LookVector * 140, rp)
	if hit then
		local dir = Fs.LookVector
		local up = workspace:Raycast(hit.Position - dir * 1.2, Vector3.new(0, 40, 0), rp)
		local yb = if up then up.Position.Y - site.Y else 12
		local face = Vector3.new(hit.Position.X, site.Y + yb - 0.85 - 2.7, hit.Position.Z) - dir * 0.05
		K.spectateSpot(CFrame.lookAt(face, face - dir), 9.6, 5.4)
		table.insert(out, ("spectate: on %s at %.1f out, its middle %.1f up"):format(hit.Instance.Name, (Vector3.new(hit.Position.X, 0, hit.Position.Z) - Vector3.new(site.X, 0, site.Z)).Magnitude, yb - 3.55))
	else
		table.insert(out, "spectate: NO wall found on side 8")
	end
	return table.concat(out, " | ")
end

-- the seven fair-judge views and the spawn-to-ring walk for a built version (world frames): spawn, pad area, pad close-up,
-- centre, side room, gym, exit; walk1..3
function HRH.views(root)
	local site = root:GetAttribute("Site")
	local k = root:GetAttribute("K") or 1 -- (none: the live Rotunda, Map.Hub.Classic, for the same spots at its own size)
	local lob = root:FindFirstChild(root:GetAttribute("LobbyName") or "Lobby")
	local up = Vector3.yAxis
	local v = {}
	local spawnC = Vector3.zero; local n = 0
	local sf = (lob and lob:FindFirstChild("HubSpawns")) or root:FindFirstChild("HubSpawns")
	for _, s in sf:GetChildren() do spawnC += s.Position; n += 1 end
	spawnC /= math.max(n, 1)
	local lobSite = lob and lob:GetAttribute("Site") or Vector3.new(spawnC.X, site.Y, spawnC.Z)
	v.spawn = { spawnC + up * 5.6, spawnC + up * 7 + Vector3.new(0, 0, -30) }
	v.pads = { site + Vector3.new(0, 9, 24 * k), site + Vector3.new(0, 4, -20 * k) }
	local pm = root.QueuePads:FindFirstChild("2v2") or root.QueuePads:GetChildren()[1]
	local s1 = pm.Side1.Position
	local d = Vector3.new(site.X - s1.X, 0, site.Z - s1.Z).Unit
	v.closeup = { s1 + d * 15 + up * 6.5, s1 + up * 3.5 - d * 2 }
	-- (the centre shot: as high over the balcony's ring band as the live Rotunda's is, 1 over it, at every size)
	local rpv = RaycastParams.new(); rpv.FilterType = Enum.RaycastFilterType.Include; rpv.FilterDescendantsInstances = { root }
	local uh = workspace:Raycast(site + Vector3.new(16 * k, 2, 16 * k), Vector3.new(0, 60, 0), rpv)
	local cy = if uh and uh.Position.Y - site.Y < 20 then uh.Position.Y - site.Y + 1 else 13
	v.centre = { site + Vector3.new(16 * k, cy, 16 * k), site + up * 5 }
	v.side = { lobSite + Vector3.new(-6, 6.2, 6), lobSite + Vector3.new(24, 4, -16) }
	local box
	for _, x in root:GetDescendants() do if x:IsA("BasePart") and x.Name == "MiniGameSpot" and x:GetAttribute("Game") == "box" then box = x end end
	local bc = box and box.Position or site
	local db = Vector3.new(site.X - bc.X, 0, site.Z - bc.Z).Unit
	v.gym = { bc + db * 22 * k + up * 7, bc + up * 2.5 }
	local gate
	for _, x in root:GetDescendants() do if x:IsA("BasePart") and x.Name == "TrainingShutter" or (x:IsA("BasePart") and x.Name == "GateBack") then gate = x end end
	local gc = gate and gate.Position or site
	local dg = Vector3.new(site.X - gc.X, 0, site.Z - gc.Z).Unit
	v.exit = { Vector3.new(gc.X, site.Y, gc.Z) + dg * 18 * k + up * 5.6, Vector3.new(gc.X, site.Y + 4, gc.Z) }
	v.walk1 = { lobSite + Vector3.new(0, 5.6, 0), lobSite + Vector3.new(0, 6, -40) }
	v.walk2 = { lobSite + Vector3.new(0, 5.6, -26), site + Vector3.new(0, 5, 0) }
	v.walk3 = { site + Vector3.new(0, 5.6, 28 * k - 2), site + Vector3.new(0, 4, -10) }
	return v
end

-- (the Play function test now; going live once the owner picks) a built version wired as a hub: Map.Hub.<its folder> with
-- Hub / Title / Order / Site, its pads, spawns and arrivals direct children (the lobby's spawns and arrivals: you arrive
-- in the lobby), every marker's Hub its id, its way to training in Map.Hub.Doors with the same door data as the Hotel's
-- (as HubClassic does). Edit mode; HRH.uninstall(id) takes all of it away again (a test copy is never saved)
function HRH.install(root, id, title, order)
	assert(game:GetService("RunService"):IsEdit(), "Edit mode only")
	local hub = workspace.Map.Hub
	assert(not hub:FindFirstChild(root.Name), "Map.Hub." .. root.Name .. " is already there")
	local lob = root:FindFirstChild(root:GetAttribute("LobbyName") or "Lobby")
	if lob then
		for _, n in { "HubSpawns", "HubArrive" } do
			local f = lob:FindFirstChild(n)
			if f then for _, c in f:GetChildren() do c.Parent = root[n] end; f:Destroy() end
		end
		local q = lob:FindFirstChild("QueuePads"); if q and #q:GetChildren() == 0 then q:Destroy() end
		for _, a in { "Hub", "Title", "Order", "Accent", "MiniGamesOff" } do lob:SetAttribute(a, nil) end -- (not a hub of its own; its Site stays for HRH.views)
	end
	root:SetAttribute("Hub", id); root:SetAttribute("Title", title); root:SetAttribute("Order", order or 9); root:SetAttribute("MiniGamesOff", nil)
	local NAMES = { HubSpawn = true, Arrive = true, NPCPoint = true, HubNPC = true, MiniGameSpot = true, HubSeat = true, VipPrompt = true, VipRoom = true, JumpPadTop = true }
	for _, d in root:GetDescendants() do
		if d:GetAttribute("Hub") ~= nil or #CS:GetTags(d) > 0 or NAMES[d.Name] then d:SetAttribute("Hub", id) end
		if d:GetAttribute("Built") == "Rotunda" then d:SetAttribute("Built", nil) end
	end
	for _, p in root.QueuePads:GetChildren() do p:SetAttribute("Hub", id); p:SetAttribute("ForShow", nil) end
	local doors = {}
	local dr = root:FindFirstChild("Doors")
	if dr then
		local ht = hub.Doors:FindFirstChild("HotelToTraining")
		for _, door in dr:GetChildren() do
			door:SetAttribute("Hub", id); door:SetAttribute("Built", nil); door:SetAttribute("ForShow", nil)
			if door.Name:match("ToTraining$") then
				door.Name = root.Name .. "ToTraining"
				if ht then for a, v in ht:GetAttributes() do if door:GetAttribute(a) == nil and a ~= "Hub" then door:SetAttribute(a, v) end end end
			end
			door.Parent = hub.Doors
			table.insert(doors, door.Name)
		end
		dr:Destroy()
	end
	-- (a live build's light zone: K.lookZone made it beside the lobby, under this root; HubLife reads Map.Hub.LookZones)
	local lz = root:FindFirstChild("LookZones")
	if lz then
		local zf = hub:FindFirstChild("LookZones")
		if not zf then zf = Instance.new("Folder"); zf.Name = "LookZones"; zf.Parent = hub end
		for _, z in lz:GetChildren() do
			local old = zf:FindFirstChild(z.Name); if old then old:Destroy() end
			z:SetAttribute("Hub", id); z.Parent = zf
		end
		lz:Destroy()
	end
	root.Parent = hub
	return ("Map.Hub.%s as hub %q (%s): %d pads, %d spawns, %d arrivals, doors %s"):format(root.Name, id, title, #root.QueuePads:GetChildren(),
		#root.HubSpawns:GetChildren(), #root.HubArrive:GetChildren(), if #doors > 0 then table.concat(doors, ", ") else "NONE")
end
function HRH.uninstall(id)
	local hub = workspace.Map.Hub
	local n = 0
	for _, c in hub:GetChildren() do if c:GetAttribute("Hub") == id and c:GetAttribute("Version") ~= nil then c:Destroy(); n += 1 end end
	for _, d in hub.Doors:GetChildren() do if d:GetAttribute("Hub") == id then d:Destroy(); n += 1 end end
	local zf = hub:FindFirstChild("LookZones")
	if zf then for _, z in zf:GetChildren() do if z:GetAttribute("Hub") == id then z:Destroy(); n += 1 end end end
	return n
end

return HRH
