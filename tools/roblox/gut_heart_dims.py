# The heart tower's numbers (studs above its foot), with no Blender in them: the look (gut_heart.py) and the hit boxes
# (gut_layout.py) both read these, so the stair you climb is the stair you see.
import math

PLINTH = ((19.5, 1.5), (16.0, 3.0))   # two round steps: (radius, top)
CORE_TOP = 102.0       # the core column's top, under the cradle
BALC_Y = 21.0          # the balcony: a walkway ring round the stair that the legs hold (the stair's walkable top)
BALC_R0, BALC_R1 = 14.4, 21.0
STAIR_R0, STAIR_R1 = 5.4, 14.0
STAIR_RISE, STAIR_STEP = 1.25, math.radians(22.5)   # one tread: 1.25 up, 22.5 degrees round (20 studs a turn)
STAIR_FROM = 3.5       # the first tread's top (the plinth's top is 3); tread 14's top is the balcony's floor
HEART_Y, HEART_W, HEART_D = 134.0, 36.0, 21.0
LEG_FOOT = 31.0        # the legs' feet: this far out

def stair_treads(y_from=STAIR_FROM, y_to=CORE_TOP - 4, phase=0.0):
    """every tread: (angle, top y). angle 0 = +x; +angle turns toward +z"""
    out, y, a = [], y_from, phase
    while y <= y_to + 1e-6:
        out.append((a, y)); y += STAIR_RISE; a += STAIR_STEP
    return out

def walk_treads(phase=0.0):
    """the treads you can climb: up to the balcony's floor"""
    return [t for t in stair_treads(phase=phase) if t[1] <= BALC_Y + 1e-6]
