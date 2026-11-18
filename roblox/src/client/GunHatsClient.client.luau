-- the weapon hats on this client (GunHats.luau): their moving bits every frame (the propeller turns, the halo bobs,
-- the googly pupils rattle: on your gun, everyone's, the previews and the racks), your hats on the hub armory's
-- display guns (the boards show the weapons as you carry them: your pick's hat on each), and the hat models fetched
-- up front so a hat never comes out blank the first time
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local GunHats = require(Shared:WaitForChild("GunHats"))
local me = Players.LocalPlayer

RunService.RenderStepped:Connect(function(dt) GunHats.step(dt) end)

task.spawn(function()
	local lib = ReplicatedStorage:WaitForChild("JankfireHats", 15)
	if lib then pcall(function() game:GetService("ContentProvider"):PreloadAsync(lib:GetChildren()) end) end
end)

-- the armory's boards: every display gun named "Rack_w_<id>" (HubRotunda's B.gun) wears your hat for that weapon
local function racks()
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	if not hub then return 0 end
	local n = 0
	-- (a piece of the hub that ZoneCull has put aside on this client waits in ReplicatedStorage.ZoneCullHidden)
	local list = hub:GetDescendants()
	local aside = ReplicatedStorage:FindFirstChild("ZoneCullHidden")
	if aside then for _, d in aside:GetDescendants() do table.insert(list, d) end end
	for _, d in list do
		if d:IsA("Model") then
			local wid = string.match(d.Name, "^Rack_w_([%w_]+)$")
			if wid then
				if GunHats.attachDisplay(d, wid, GunHats.hatFor(me, wid)) then n += 1 end
			end
		end
	end
	return n
end
me:GetAttributeChangedSignal("Hats"):Connect(racks)

-- hats on hands (GunHats.attachHand; 18 Nov 2026, the Blood Cross: your own hand is the weapon): wherever the hold code
-- puts a HatSpot (an Attachment tagged GunHatSpot, AvatarArms.hatSpot), the owner's hat for that weapon stands on it.
-- first person (the spot is in the camera): inside the viewmodel's weapon model as its GunHat, so it hides while you aim
-- and with the view, like a gun's hat; third person: on the body's hand, GunHats.THIRD bigger. a spot that goes takes
-- its hat with it; a new pick (the Hats attribute) puts every spot's hat on again
local CS = game:GetService("CollectionService")
local onSpot: { [Attachment]: Model } = {}
local function placeSpot(att: Instance)
	if not att:IsA("Attachment") then return end
	local old = onSpot[att]
	if old then old:Destroy(); onSpot[att] = nil end
	local wid = att:GetAttribute("Weapon")
	if type(wid) ~= "string" or not att.Parent then return end
	local uid = att:GetAttribute("Owner")
	local who = if type(uid) == "number" and uid ~= 0 then Players:GetPlayerByUserId(uid) else me -- (0: a test body)
	local id = GunHats.hatFor(who, wid)
	if not id then return end
	local cam = workspace.CurrentCamera
	local fp = cam ~= nil and att:IsDescendantOf(cam)
	local holder: Instance? = nil
	if fp then
		local m: Instance = att
		while m.Parent and m.Parent ~= cam do m = m.Parent :: Instance end
		local was = m:FindFirstChild("GunHat")
		if m:IsA("Model") and not (was and not was:GetAttribute("HandSpot")) then
			if was then was:Destroy() end
			holder = m
		end
	end
	local hat = GunHats.attachHand(att, id, if fp then nil else GunHats.THIRD, holder)
	if hat then onSpot[att] = hat end
end
local function dropSpot(att: Instance)
	local hat = onSpot[att :: Attachment]
	if hat then hat:Destroy(); onSpot[att :: Attachment] = nil end
end
for _, a in CS:GetTagged("GunHatSpot") do task.defer(placeSpot, a) end
CS:GetInstanceAddedSignal("GunHatSpot"):Connect(function(a) task.defer(placeSpot, a) end)
CS:GetInstanceRemovedSignal("GunHatSpot"):Connect(dropSpot)
-- (a pick changes: that player's Hats attribute puts the hats on their spots again)
local function mine(att: Instance, p: Player): boolean
	local uid = att:GetAttribute("Owner")
	return uid == p.UserId or ((uid == 0 or uid == nil) and p == me)
end
local function repick(p: Player)
	for _, a in CS:GetTagged("GunHatSpot") do
		if mine(a, p) then placeSpot(a) end
	end
end
local function watch(p: Player) p:GetAttributeChangedSignal("Hats"):Connect(function() repick(p) end) end
for _, p in Players:GetPlayers() do watch(p) end
Players.PlayerAdded:Connect(watch)
-- (a spot whose hand went loses its hat; a hat the view rebuilt away while its spot stayed goes back on; a hat on a
-- body's hand fades with that hand, as the game hides your own body when the camera is in it)
RunService.Heartbeat:Connect(function()
	for att, hat in onSpot do
		if not att.Parent then
			if hat.Parent then hat:Destroy() end
			onSpot[att] = nil
		elseif not hat.Parent then
			onSpot[att] = nil
			task.defer(placeSpot, att)
		elseif hat.Parent == att.Parent then
			local hand = att.Parent :: BasePart
			local f = math.max(hand.LocalTransparencyModifier, if hand.Transparency >= 0.99 then 1 else 0)
			if hat:GetAttribute("Fade") ~= f then
				hat:SetAttribute("Fade", f)
				for _, p in hat:GetChildren() do
					if p:IsA("BasePart") then p.LocalTransparencyModifier = f end
				end
			end
		end
	end
end)
task.spawn(function()
	-- (the hub may still be arriving: try a few times)
	for _ = 1, 6 do
		if workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub") then racks() end
		task.wait(2)
	end
end)
