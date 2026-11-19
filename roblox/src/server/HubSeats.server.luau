--!strict
-- seats people can sit on in the hub (19 Nov 2026, the owner: "add seating spots on top of the arcade machine", "seats
-- in the lounge are sittable", "seats in vip room work too"). any BasePart tagged HubSeat gets a Seat (or is one) with
-- a Sit prompt: its CFrame on the cushion's top, its LookVector the way you face sitting. builders tag their seats (the
-- arcade cabinet's lid: MiniGames.server; the lounge's and the VIP room's sofas: the hub's builder).
-- the server seats you (TeleportT first: the anti-cheat), a jump stands you up. touching a seat never sits you (only the
-- prompt does). while someone sits there the tagged part's attribute SeatTaken is true and its prompt is hidden, so the
-- hub's regulars (HubNPCs) can pass a taken seat by and wait for a free one. a regular's own place can carry the tag
-- too: while its attribute NpcHere is true (HubNPCs sets it when its regular is on it) it counts as taken.
-- not while you're in a mini-game (MiniGame), dead, or already sitting
local CollectionService = game:GetService("CollectionService")

local TAG = "HubSeat"
local REACH = 12 -- (studs: further than the prompt reaches, a moving body's slack)

local function setup(p: Instance)
	if not p:IsA("BasePart") or p:GetAttribute("HubSeatOn") then return end
	p:SetAttribute("HubSeatOn", true)
	local seat: Seat
	if p:IsA("Seat") then
		seat = p
	else
		local s = Instance.new("Seat")
		s.Name = "HubSeatSeat"; s.Size = Vector3.new(1.8, 0.2, 1.8); s.Transparency = 1; s.Anchored = true
		s.CanCollide = false; s.CanQuery = false; s.CastShadow = false
		s.CFrame = p.CFrame * CFrame.new(0, 0.1, 0)
		s.Parent = p
		seat = s
	end
	seat.CanTouch = false
	seat.Disabled = true
	local at = Instance.new("Attachment")
	at.Name = "SitAt"; at.Position = Vector3.new(0, 1.3, 0)
	at.Parent = seat
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "SitPrompt"; pr.ActionText = "Sit"; pr.ObjectText = ""
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
	pr.MaxActivationDistance = 7; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
	pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
	pr.Parent = at
	local function refresh()
		local taken = seat.Occupant ~= nil or p:GetAttribute("NpcHere") == true
		if p:GetAttribute("SeatTaken") ~= taken then p:SetAttribute("SeatTaken", taken) end
		pr.Enabled = not taken
	end
	pr.Triggered:Connect(function(plr: Player)
		if seat.Occupant or p:GetAttribute("NpcHere") == true or plr:GetAttribute("MiniGame") ~= nil then return end
		local ch = plr.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root or hum.Health <= 0 or hum.SeatPart ~= nil then return end
		if (root.Position - seat.Position).Magnitude > REACH then return end
		plr:SetAttribute("TeleportT", os.clock())
		seat.Disabled = false
		seat:Sit(hum)
	end)
	seat:GetPropertyChangedSignal("Occupant"):Connect(function()
		if seat.Occupant == nil then seat.Disabled = true end -- (only the prompt seats you)
		refresh()
	end)
	p:GetAttributeChangedSignal("NpcHere"):Connect(refresh)
	refresh()
end

for _, p in CollectionService:GetTagged(TAG) do task.spawn(setup, p) end
CollectionService:GetInstanceAddedSignal(TAG):Connect(setup)
