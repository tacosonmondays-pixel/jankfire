--!strict
-- ONE "A JUMP PAD THREW SOMEONE" SIGNAL ON THIS CLIENT (17 Nov 2026, the owner: "pads should glow when you step on
-- them!"). Whoever sees a launch fires it once; everyone who reacts listens, so the sound and the glow agree:
--   Steps.client (the sound session's: it watches every character leave the ground fast over a Pad part) fires it
--   next to its pad_launch sound; PadFlare.client (the VFX session's) lights the pad.
--   local PadSignal = require(script.Parent:WaitForChild("PadSignal"))
--   PadSignal.fire(pad, character, mine)            pad: the part with the Pad attribute; mine: your own character
--   PadSignal.launched:Connect(function(pad, character, mine) ... end)
local PadSignal = {}
local ev = Instance.new("BindableEvent")
PadSignal.launched = ev.Event
function PadSignal.fire(pad: BasePart, character: Model?, mine: boolean?)
	ev:Fire(pad, character, mine == true)
end
return PadSignal
