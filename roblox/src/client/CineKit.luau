--!strict
-- CineKit (27 Nov 2026): the small shared piece for a scripted camera on the client, written for HOUSE HUNT's gunman
-- intro (client/HuntIntro.client.luau) after asking the finishers and the victory scene for theirs (both tied to their
-- own bodies). Letterbox bars, a shot list played against any clock, a shake. Nothing in it knows a scene.
--   CineKit.bars(on, t?)                 the letterbox in or out over t s (0.12 of the screen each, black)
--   CineKit.play(shots, clock) -> run    steps the camera every frame: run.stop(), run.shot (the current one's name)
--     shots: { { name, t0, t1, cam = (u) -> CFrame, fov = number | (u) -> number, shake = number | (u) -> number } }
--     (u = 0..1 through the shot; a cut is just the next shot; the camera stays where the last shot ended)
--     clock: () -> seconds since the scene began (the caller's: a server clock keeps a phone or a slow load on time)
--   CineKit.shake(cf, amount, t)         cf moved by a smooth noise shake (amount ~ studs; its turn ~ 4x as degrees)
--   CineKit.ease(u), CineKit.lerp(a, b, u)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local K = {}

function K.ease(u: number): number
	u = math.clamp(u, 0, 1)
	return u * u * (3 - 2 * u)
end
function K.lerp(a: number, b: number, u: number): number return a + (b - a) * u end

function K.shake(cf: CFrame, amount: number, t: number): CFrame
	if amount <= 0 then return cf end
	local n = math.noise
	local p = Vector3.new(n(t * 9, 1.3), n(t * 9, 7.1), n(t * 9, 13.7)) * amount
	local r = math.rad(amount * 4)
	return cf * CFrame.new(p) * CFrame.Angles(n(t * 7, 3.3) * r, n(t * 7, 5.9) * r, n(t * 7, 9.1) * r * 0.6)
end

-- the bars: one ScreenGui, made on first use
local gui: ScreenGui? = nil
local top: Frame?, bottom: Frame? = nil, nil
local BAR = 0.12
local function ensure()
	if gui and gui.Parent then return end
	local pg = Players.LocalPlayer:WaitForChild("PlayerGui")
	local g = Instance.new("ScreenGui")
	g.Name = "CineBars"; g.IgnoreGuiInset = true; g.ResetOnSpawn = false; g.DisplayOrder = 900
	g.ScreenInsets = Enum.ScreenInsets.None
	local function bar(name: string, y: number, ay: number): Frame
		local f = Instance.new("Frame")
		f.Name = name; f.BackgroundColor3 = Color3.new(0, 0, 0); f.BorderSizePixel = 0
		f.AnchorPoint = Vector2.new(0, ay); f.Position = UDim2.fromScale(0, y); f.Size = UDim2.fromScale(1, BAR)
		f.Parent = g
		return f
	end
	top = bar("Top", -BAR, 0); bottom = bar("Bottom", 1 + BAR, 1)
	g.Parent = pg
	gui = g
end
function K.bars(on: boolean, t: number?)
	ensure()
	local ti = TweenInfo.new(t or 0.4, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
	TweenService:Create(top :: Frame, ti, { Position = UDim2.fromScale(0, if on then 0 else -BAR) }):Play()
	TweenService:Create(bottom :: Frame, ti, { Position = UDim2.fromScale(0, if on then 1 else 1 + BAR) }):Play()
end

export type Shot = { name: string, t0: number, t1: number, cam: (number) -> CFrame, fov: any?, shake: any? }
export type Run = { stop: () -> (), shot: string?, done: boolean }

local n = 0
function K.play(shots: { Shot }, clock: () -> number): Run
	n += 1
	local key = "CineKit" .. n
	local cam = workspace.CurrentCamera
	local run: Run = { stop = function() end, shot = nil, done = false }
	cam.CameraType = Enum.CameraType.Scriptable
	local function step()
		local t = clock()
		local s: Shot? = nil
		for _, x in shots do if t >= x.t0 and t < x.t1 then s = x; break end end
		if not s then
			if t >= shots[#shots].t1 then s = shots[#shots] else return end
		end
		local sh = s :: Shot
		local u = math.clamp((t - sh.t0) / math.max(1e-3, sh.t1 - sh.t0), 0, 1)
		run.shot = sh.name
		local cf = sh.cam(u)
		local amp = if type(sh.shake) == "function" then sh.shake(u) elseif type(sh.shake) == "number" then sh.shake else 0
		cam.CameraType = Enum.CameraType.Scriptable
		cam.CFrame = K.shake(cf, amp, t)
		if sh.fov then cam.FieldOfView = if type(sh.fov) == "function" then sh.fov(u) else sh.fov end
	end
	RunService:BindToRenderStep(key, Enum.RenderPriority.Camera.Value + 2, step)
	run.stop = function()
		if run.done then return end
		run.done = true
		pcall(function() RunService:UnbindFromRenderStep(key) end)
	end
	return run
end

return K
