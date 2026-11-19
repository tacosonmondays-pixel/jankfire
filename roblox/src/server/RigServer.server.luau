--!strict
-- the Overdrive Rig gadget's server (Rig.luau, a module so the gadget's use can call Rig.start): required here at
-- server start, so its remote, its clock and ServerStorage.JankRig are up before anyone presses G
require(script.Parent:WaitForChild("Rig"))
