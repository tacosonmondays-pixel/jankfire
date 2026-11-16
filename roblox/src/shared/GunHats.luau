--!strict
-- the weapon hats: a small hat that sits on your gun (JANKFIRE's "hat" cosmetic, shared/cosmetics.js COSMETICS.hat).
-- one per weapon, picked in the loadout screen, kept by the server with your loadout (Loadout.luau, attribute "Hats":
-- "ar=crown;katana=duck"). the hats are models of their own (tools/roblox/hat_models.py -> ReplicatedStorage.JankfireHats,
-- see roblox/docs/GUN-HATS.md); where each sits on each gun is data (GunHatData.SPOTS, measured by
-- tools/roblox/hat_spots.py). a hat rides INSIDE the weapon's model as a Model named "GunHat" (so it moves, hides and
-- goes away with the gun), and every hat part carries NoWrap (and WrapTr = 1), which WeaponModels.wrap skips: a wrap
-- never paints a hat. shown in first person (Viewmodel), on everyone's third-person gun (Fight.showWeapon), on the
-- Shredder (a Tool), on the loadout's previews and on the hub's armory racks (GunHatsClient). in first person the hat
-- hides while you aim (the web game: W.aim >= 0.3), so it is never in the sight picture. the moving bits (the
-- propeller, the halo, the googly pupils) run on the client only (GunHats.step)
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")
local D = require(script.Parent:WaitForChild("GunHatData")) :: any

local GunHats = {}
GunHats.D = D
GunHats.ORDER = D.ORDER :: { string }
GunHats.HATS = D.HATS :: { [string]: { name: string, rarity: string } }
GunHats.TAG = "GunHatMove"
GunHats.AIM_HIDE = 0.3
-- on a gun in someone's hands (third person) a hat is drawn this much bigger than in first person: at the size that
-- reads in your own hands it was a few pixels on another player's gun (16 Nov 2026, in-hall photos)
GunHats.THIRD = 1.5
-- reload clips during which the first-person hat steps away too: the Marble Shotgun's bag pours into the jar the hat
-- sits on
GunHats.HIDE_CLIPS = { reload_marbles = true }

-- the Shredder is a Tool: its kit pieces sit on the Handle in the gun frame WeaponImport.kitShredder builds from the
-- web Tool's Muzzle / sh_hub / sh_bell2 (measured 16 Nov 2026 from PolishBackup.WeaponSets.web.Shredder: this frame and
-- scale put the kit pieces exactly on their file bounds). a Tool may carry its own (attributes HatFrame, HatK)
local SHRED_FRAME = CFrame.new(-0.121364594, 0.464999974, -0.293563843, 0.858965874, 1.73003828e-05, 0.512032807,
	-2.01230505e-05, 1, -3.00123517e-08, -0.512032747, -1.02778822e-05, 0.858965993)
local SHRED_K = 2.98198798

function GunHats.valid(id: any): boolean
	return type(id) == "string" and D.HATS[id] ~= nil
end

-- a player's hat on one weapon (nil = none), from the "Hats" attribute the server keeps
function GunHats.hatFor(p: Player?, wid: string): string?
	local s = p and p:GetAttribute("Hats")
	if type(s) ~= "string" then return nil end
	for w, h in string.gmatch(s, "([%w_]+)=([%w_]+)") do
		if w == wid then return if h ~= "none" and D.HATS[h] then h else nil end
	end
	return nil
end

function GunHats.template(id: string): Model?
	local lib = ReplicatedStorage:FindFirstChild("JankfireHats")
	local t = lib and lib:FindFirstChild("hat_" .. id)
	return if t and t:IsA("Model") then t else nil
end

local function quiet(p: BasePart, anchored: boolean)
	p.Anchored = anchored; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true; p.CastShadow = false
	p:SetAttribute("NoWrap", true); p:SetAttribute("WrapTr", 1) -- (WeaponModels.wrap leaves these alone)
end

-- a hat as a Model "GunHat" with its foot at `foot`, f studs for every template stud. carrier = the part it rides
-- (welded to it), or nil: anchored (the previews, the racks: whoever moves the model moves the hat)
function GunHats.make(id: string, foot: CFrame, f: number, carrier: BasePart?): Model?
	local t = GunHats.template(id)
	if not t then return nil end
	local anchored = carrier == nil
	local m = Instance.new("Model")
	m.Name = "GunHat"
	m:SetAttribute("Hat", id)
	local base = Instance.new("Part")
	base.Name = "HatFoot"; base.Size = Vector3.one * 0.05; base.Transparency = 1
	quiet(base, anchored)
	base.CFrame = foot
	base.Parent = m
	m.PrimaryPart = base
	if carrier then
		local w = Instance.new("Weld")
		w.Name = "HatWeld"; w.Part0 = carrier; w.Part1 = base; w.C0 = carrier.CFrame:ToObjectSpace(foot)
		w.Parent = base
	end
	local spm = f / (D.UNIT :: number) -- (studs per metre, for the moving bits' reach)
	local moves = D.MOVES[id] or {}
	local piv = t:GetPivot()
	for _, src in t:GetChildren() do
		if not src:IsA("BasePart") then continue end
		local p = src:Clone()
		for _, c in p:GetChildren() do c:Destroy() end
		local rel = piv:ToObjectSpace(src.CFrame)
		local at = CFrame.new(rel.Position * f) * rel.Rotation
		p.Size = src.Size * f
		p.CFrame = foot * at
		quiet(p, anchored)
		local mv = moves[p.Name]
		if mv then
			p:SetAttribute("HatRest", at)
			p:SetAttribute("HatKind", mv.kind)
			p:SetAttribute("HatSpeed", mv.speed or 0)
			p:SetAttribute("HatAmp", (mv.amp or 0) * spm)
			if mv.u then p:SetAttribute("HatU", mv.u) end
			if mv.v then p:SetAttribute("HatV", mv.v) end
			if not anchored then
				local w = Instance.new("Weld")
				w.Name = "HatJoint"; w.Part0 = base; w.Part1 = p; w.C0 = at
				w.Parent = p
			end
			CollectionService:AddTag(p, GunHats.TAG)
		elseif not anchored then
			local w = Instance.new("WeldConstraint")
			w.Part0 = base; w.Part1 = p
			w.Parent = p
		end
		p.Parent = m
	end
	return m
end

-- the piece of a weapon model a hat at `pos` rides: the smallest piece whose box holds the point just under the hat's
-- foot (the cover, the slide, the scope ... not the whole body), else the nearest one
local function carrierOf(m: Model, root: BasePart, pos: Vector3, down: Vector3): BasePart
	local best: BasePart, bestD, bestV = root, math.huge, math.huge
	local q = pos - down
	for _, c in m:GetChildren() do
		if not c:IsA("BasePart") or c == root or c.Transparency >= 0.99 then continue end
		local l = c.CFrame:PointToObjectSpace(q)
		local h = c.Size / 2
		local out = Vector3.new(math.max(math.abs(l.X) - h.X, 0), math.max(math.abs(l.Y) - h.Y, 0), math.max(math.abs(l.Z) - h.Z, 0)).Magnitude
		local vol = c.Size.X * c.Size.Y * c.Size.Z
		if out < bestD - 1e-4 or (math.abs(out - bestD) <= 1e-4 and vol < bestV) then best, bestD, bestV = c, out, vol end
	end
	return best
end

-- the turn of a spot: yaw round the gun's up axis, then pitch about its x (90 stands a hat on the gun's back end)
local function turnOf(sp: any): CFrame
	return CFrame.Angles(0, math.rad(sp.yaw or 0), 0) * CFrame.Angles(math.rad(sp.pitch or 0), 0, 0)
end

-- a hat on a weapon model from WeaponModels.build (root = its PrimaryPart, k = studs per metre). any old hat goes.
-- anchored = true for a model that is moved by pivoting it (the loadout's previews); boost = a size factor on top of
-- the spot's (GunHats.THIRD for a gun in someone's hands). returns the hat or nil
function GunHats.attach(m: Model, wid: string, id: string?, k: number, anchored: boolean?, boost: number?): Model?
	local old = m:FindFirstChild("GunHat")
	if old then old:Destroy() end
	local sp = D.SPOTS[wid]
	local root = m.PrimaryPart
	if not id or not GunHats.valid(id) or id == "none" or not sp or not root then return nil end
	local foot = root.CFrame * CFrame.new(sp.at * k) * turnOf(sp)
	local carrier = if anchored then nil else carrierOf(m, root, foot.Position, foot.UpVector * 0.004 * k)
	local hat = GunHats.make(id, foot, (D.UNIT :: number) * k * sp.s * (boost or 1), carrier)
	if hat then hat.Parent = m end
	return hat
end

-- the Shredder (a Tool): the hat on its Handle, in the gun frame. any old hat goes
function GunHats.attachTool(tool: Instance, id: string?): Model?
	local old = tool:FindFirstChild("GunHat")
	if old then old:Destroy() end
	local h = tool:FindFirstChild("Handle")
	local sp = D.SPOTS.shredder
	if not id or not GunHats.valid(id) or id == "none" or not sp or not (h and h:IsA("BasePart")) then return nil end
	local fr, kk = tool:GetAttribute("HatFrame"), tool:GetAttribute("HatK")
	local frame: CFrame = if typeof(fr) == "CFrame" then fr else SHRED_FRAME
	local K: number = if type(kk) == "number" then kk else SHRED_K
	local foot = h.CFrame * frame * CFrame.new(sp.at * K) * turnOf(sp)
	local hat = GunHats.make(id, foot, (D.UNIT :: number) * K * sp.s, if h.Anchored then nil else h)
	if hat then hat.Parent = tool end
	return hat
end

-- the hat for a copy of the Shredder's parts (the loadout's preview): placed from the Tool's own Handle, anchored
function GunHats.attachToolCopy(m: Model, tool: Instance, id: string?): Model?
	local old = m:FindFirstChild("GunHat")
	if old then old:Destroy() end
	local h = tool:FindFirstChild("Handle")
	local sp = D.SPOTS.shredder
	if not id or not GunHats.valid(id) or id == "none" or not sp or not (h and h:IsA("BasePart")) then return nil end
	local fr, kk = tool:GetAttribute("HatFrame"), tool:GetAttribute("HatK")
	local frame: CFrame = if typeof(fr) == "CFrame" then fr else SHRED_FRAME
	local K: number = if type(kk) == "number" then kk else SHRED_K
	local foot = h.CFrame * frame * CFrame.new(sp.at * K) * turnOf(sp)
	local hat = GunHats.make(id, foot, (D.UNIT :: number) * K * sp.s, nil)
	if hat then hat.Parent = m end
	return hat
end

-- a hat on a display copy of a weapon template (JankfireWeapons.w_<id> cloned, scaled and moved: the hub's armory
-- racks). the template's file bounds say where the gun frame is in it; the copy's biggest piece against the
-- template's says how it was scaled and moved. anchored
function GunHats.attachDisplay(g: Model, wid: string, id: string?): Model?
	local old = g:FindFirstChild("GunHat")
	if old then old:Destroy() end
	local sp = D.SPOTS[wid]
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
	local t = lib and lib:FindFirstChild("w_" .. wid)
	if not id or not GunHats.valid(id) or id == "none" or not sp or not (t and t:IsA("Model")) then return nil end
	local flo, fhi = t:GetAttribute("FileLo"), t:GetAttribute("FileHi")
	if typeof(flo) ~= "Vector3" or typeof(fhi) ~= "Vector3" then return nil end
	local tcf, tsize = t:GetBoundingBox()
	local fsz = fhi - flo
	local U = Vector3.new(tsize.X / math.max(fsz.X, 1e-4), tsize.Y / math.max(fsz.Y, 1e-4), tsize.Z / math.max(fsz.Z, 1e-4))
	-- the same piece in both: the template's biggest piece whose name is its own
	local count: { [string]: number } = {}
	for _, d in t:GetDescendants() do if d:IsA("BasePart") then count[d.Name] = (count[d.Name] or 0) + 1 end end
	local tp: BasePart? = nil
	for _, d in t:GetDescendants() do
		if d:IsA("BasePart") and count[d.Name] == 1 and (not tp or d.Size.Magnitude > (tp :: BasePart).Size.Magnitude) then tp = d end
	end
	local cpi = tp and g:FindFirstChild((tp :: BasePart).Name, true)
	local cp: BasePart? = if cpi and cpi:IsA("BasePart") then cpi else nil
	if not tp or not cp then return nil end
	local s = cp.Size.Magnitude / math.max(tp.Size.Magnitude, 1e-6)
	local R = cp.CFrame.Rotation * tp.CFrame.Rotation:Inverse()
	local function map(x: Vector3): Vector3 return cp.Position + R:VectorToWorldSpace((x - tp.Position) * s) end
	local at = tcf:PointToWorldSpace((sp.at - (flo + fhi) / 2) * U)
	local foot = CFrame.new(map(at)) * (R * tcf.Rotation) * turnOf(sp)
	local spm = (U.X + U.Y + U.Z) / 3 * s
	local hat = GunHats.make(id, foot, (D.UNIT :: number) * spm * sp.s, nil)
	if hat then hat.Parent = g end
	return hat
end

-- first person: the hat hides while you aim, and through the clips in HIDE_CLIPS (Arsenal hides every viewmodel part
-- with the Hide attribute)
function GunHats.aim(m: Model, aim: number, clip: string?)
	local hat = m:FindFirstChild("GunHat")
	if not hat then return end
	local hide = aim >= GunHats.AIM_HIDE or (clip ~= nil and GunHats.HIDE_CLIPS[clip] == true)
	if hat:GetAttribute("Hidden") == hide then return end
	hat:SetAttribute("Hidden", hide)
	for _, p in hat:GetChildren() do
		if p:IsA("BasePart") then p:SetAttribute("Hide", if hide then true else nil) end
	end
end

-- ------------------------------------------------------------------ the moving bits (client, every frame)
-- spin: round the hat's up axis; bob: up and down; rattle: a new jitter in the eyes' plane twenty times a second.
-- a welded bit is moved through its joint, an anchored one (a preview, a rack, the Shredder's first-person copy) from
-- its hat's foot. bits far from the camera are left alone
local live: { [BasePart]: boolean } = {}
local started = false
local rattleT = 0
local camPos = Vector3.zero
function GunHats.step(dt: number)
	if not started then
		started = true
		for _, p in CollectionService:GetTagged(GunHats.TAG) do if p:IsA("BasePart") then live[p] = true end end
		CollectionService:GetInstanceAddedSignal(GunHats.TAG):Connect(function(p) if p:IsA("BasePart") then live[p] = true end end)
		CollectionService:GetInstanceRemovedSignal(GunHats.TAG):Connect(function(p) live[p :: BasePart] = nil end)
	end
	local now = os.clock()
	local cam = workspace.CurrentCamera
	if cam then camPos = cam.CFrame.Position end
	rattleT += dt
	local doRattle = rattleT >= 0.05
	if doRattle then rattleT = 0 end
	for p in live do
		if not p.Parent then live[p] = nil; continue end
		if p:IsDescendantOf(workspace) and (p.Position - camPos).Magnitude > 150 then continue end
		local rest = p:GetAttribute("HatRest")
		if typeof(rest) ~= "CFrame" then continue end
		local kind = p:GetAttribute("HatKind")
		local amp = (p:GetAttribute("HatAmp") :: number?) or 0
		local speed = (p:GetAttribute("HatSpeed") :: number?) or 0
		local off: CFrame
		if kind == "spin" then
			off = rest * CFrame.Angles(0, (now * speed) % (2 * math.pi), 0)
		elseif kind == "bob" then
			off = rest + Vector3.new(0, math.sin(now * speed * 2 * math.pi) * amp, 0)
		elseif kind == "rattle" then
			if not doRattle then continue end
			local u, v = p:GetAttribute("HatU"), p:GetAttribute("HatV")
			local du = if typeof(u) == "Vector3" then u else Vector3.xAxis
			local dv = if typeof(v) == "Vector3" then v else Vector3.yAxis
			off = rest + (du * (math.random() * 2 - 1) + dv * (math.random() * 2 - 1)) * amp
		else
			continue
		end
		local j = p:FindFirstChild("HatJoint")
		if j and j:IsA("Weld") and not p.Anchored then
			j.C0 = off
		else
			local hat = p.Parent
			local foot = hat and hat:FindFirstChild("HatFoot")
			if foot and foot:IsA("BasePart") then p.CFrame = foot.CFrame * off end
		end
	end
end

return GunHats
