--!strict
-- the hub/training gate's portal (GateKit: the surface behind the door and the lasers, tagged "GatePortal"), alive on
-- your own screen: its soft round of paler light turns slowly (one turn every 40 s) and breathes a little, so an open
-- gate reads as a way through, not a dead end (main, for the owner, 17 Nov). calm on purpose: no flicker, nothing fast.
-- any part tagged GatePortal with a SurfaceGui whose Swirl frame has a UIGradient named Turn gets it; portals out of
-- your world (ZoneCull) or far from the camera are left alone
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")

local TURN = 360 / 40 -- (degrees a second)
local FAR = 180

type Portal = { part: BasePart, turn: UIGradient, swirl: Frame, phase: number }
local portals: { [Instance]: Portal } = {}

local function add(p: Instance)
	if not p:IsA("BasePart") or portals[p] then return end
	local sg = p:FindFirstChildOfClass("SurfaceGui")
	local swirl = sg and sg:FindFirstChild("Swirl")
	local turn = swirl and swirl:FindFirstChild("Turn")
	if not swirl or not swirl:IsA("Frame") or not turn or not turn:IsA("UIGradient") then return end
	portals[p] = { part = p, turn = turn, swirl = swirl, phase = math.random() * 40 }
end
CollectionService:GetInstanceAddedSignal("GatePortal"):Connect(function(p) task.defer(add, p) end)
CollectionService:GetInstanceRemovedSignal("GatePortal"):Connect(function(p) portals[p] = nil end)
for _, p in CollectionService:GetTagged("GatePortal") do add(p) end

RunService.RenderStepped:Connect(function()
	local cam = workspace.CurrentCamera
	if not cam then return end
	local eye = cam.CFrame.Position
	local now = os.clock()
	for p, g in portals do
		if not g.part.Parent then portals[p] = nil; continue end
		if not g.part:IsDescendantOf(workspace) or (g.part.Position - eye).Magnitude > FAR then continue end
		local t = now + g.phase
		g.turn.Rotation = (t * TURN) % 360
		-- (a slow breath: the round swells a touch and settles, every 7 s)
		local b = math.sin(t / 7 * 2 * math.pi)
		g.swirl.Size = UDim2.fromScale(1.15 + 0.04 * b, 0.97 + 0.03 * b)
	end
end)
