--!nocheck
-- the seven fair-judge views of a live hub (26 Nov 2026, the hub fix pass): parks the Edit camera on one of them.
--   local V = require(game.ServerStorage.PolishBackup.HubView7:Clone())
--   print(V("Square", 1, "hub"))   -- HUB = the Map.Hub folder, VIEW 1..7, LOOK = a HubLook look to preview ("" keeps it)
-- 1 spawn, 2 pad area, 3 pad close-up, 4 centre, 5 side room, 6 gym, 7 exit to training. The judges' frames are these,
-- the same seven for every hub (scratchpad judge_hub7.md is the rubric)
return function(HUB, VIEW, LOOK)
	local f = workspace.Map.Hub[HUB]
	local site = f:GetAttribute("Site")
	local up = Vector3.yAxis
	local function flat(v) v = Vector3.new(v.X, 0, v.Z); return if v.Magnitude > 1e-3 then v.Unit else Vector3.new(0, 0, -1) end
	local function centroid(list) local s, n = Vector3.zero, 0; for _, p in list do s += p; n += 1 end; return if n > 0 then s / n else site end
	local spawns = {}; for _, s in f.HubSpawns:GetChildren() do if s:IsA("BasePart") then table.insert(spawns, s.Position) end end
	local spawnC = centroid(spawns)
	local spawnLook = flat(f.HubSpawns:GetChildren()[1].CFrame.LookVector)
	local pads = {}; for _, m in f.QueuePads:GetChildren() do local s1 = m:FindFirstChild("Side1"); if s1 then table.insert(pads, s1.Position) end end
	local padC = centroid(pads)
	local function find(pred) for _, d in f:GetDescendants() do if d:IsA("BasePart") and pred(d) then return d end end end
	local pos, at
	local function floorAt(p) local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { f }
		local r = workspace:Raycast(p + up * 0.5, -up * 40, rp); return if r then r.Position.Y else site.Y end
	local function ground(c, dist, eye, look) local d = flat(site - c); local fy = floorAt(c); local q = c + d * dist
		return Vector3.new(q.X, floorAt(q + up * 2) + eye, q.Z), Vector3.new(c.X, fy + look, c.Z) end
	if VIEW == 1 then pos = spawnC + up * 5.6; at = pos + spawnLook * 30 + up * 1.5
	elseif VIEW == 2 then local d = flat(spawnC - padC); pos = padC + d * 30 + up * 8; at = padC + up * 3
	elseif VIEW == 3 then
		local pm = f.QueuePads:FindFirstChild("2v2") or f.QueuePads:GetChildren()[1]
		local s1 = pm.Side1.Position
		local scr = pm:FindFirstChild("Screen", true) or pm:FindFirstChild("Sign", true)
		local tgt = if scr and scr:IsA("BasePart") then scr.Position else s1 + up * 6
		local d = flat(site - s1)
		pos = s1 + d * 16 + up * 6.5; at = (s1 + tgt) / 2
	elseif VIEW == 4 then local d = flat(spawnC - site); pos = site + d * 26 + up * 11; at = site + up * 6
	elseif VIEW == 5 then
		local p = find(function(d) return d.Name:match("[Ss]ofa") and not d:FindFirstAncestor("Vip") end) or find(function(d) return d.Name == "ShopSign" end)
		local c = if p then p.Position else site
		pos, at = ground(c, 18, 6.5, 4)
	elseif VIEW == 6 then
		local p = find(function(d) return d.Name == "MiniGameSpot" and d:GetAttribute("Game") == "box" end)
		local c = if p then p.Position else site
		pos, at = ground(c, 22, 7.5, 2.5)
	else
		local door = workspace.Map.Hub.Doors:FindFirstChild(HUB .. "ToTraining")
		local c = if door then door.Position else site
		pos, at = ground(c, 18, 5.6, 4)
	end
	if LOOK and LOOK ~= "" then local L = require(game.ReplicatedStorage.Jankfire.HubLook:Clone()); if game.Lighting:GetAttribute("Previewing") then L.preview(false) end; L.preview(LOOK) end
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Scriptable
	cam.FieldOfView = 70
	cam.CFrame = CFrame.lookAt(pos, at)
	task.wait(if LOOK and LOOK ~= "" then 6 else 3.5)
	return ("%s view %d at %s"):format(HUB, VIEW, tostring(pos - site))
end
