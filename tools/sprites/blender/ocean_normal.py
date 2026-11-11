# Proof: a tiling water normal map from Blender's Ocean modifier (a real wave spectrum, no fluid solver needed).
# The ocean tile repeats exactly, so the map does too. Reads the displaced grid straight from the mesh (no render).
# Run: blender52 -b -P tools/sprites/blender/ocean_normal.py [-- <px> <choppiness> <wind m/s>]
import bpy, sys, os
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PX = int(args[0]) if args else 256; CHOP = float(args[1]) if len(args) > 1 else 0.0; WIND = float(args[2]) if len(args) > 2 else 6.0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../public/sprites/ocean_normal.png')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=2); o = bpy.context.object
m = o.modifiers.new('ocean', 'OCEAN'); m.geometry_mode = 'GENERATE'
m.resolution = 16; m.viewport_resolution = 16  # the grid is resolution^2 squares a side
m.spatial_size = 12; m.size = 1.0; m.repeat_x = m.repeat_y = 1
m.wave_scale = 0.6; m.choppiness = CHOP; m.wind_velocity = WIND; m.wave_scale_min = 0.01; m.damping = 0.3; m.wave_alignment = 0.2; m.time = 3.0; m.random_seed = 7
dg = bpy.context.evaluated_depsgraph_get(); me = o.evaluated_get(dg).to_mesh()
n = len(me.vertices); side = int(round(n ** 0.5)); co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
order = np.lexsort((co[:, 0], co[:, 1])); H = co[order, 2].reshape(side, side)[:-1, :-1]  # drop the repeated last row/column: the tile wraps
G = H.shape[0]; cell = m.spatial_size / G
# resample to PX with wrap, then normals from the height differences
idx = (np.arange(PX) + 0.5) * G / PX - 0.5; i0 = np.floor(idx).astype(int); f = idx - i0
def samp(Hm):
    a = Hm[np.ix_(i0 % G, i0 % G)]; b = Hm[np.ix_(i0 % G, (i0 + 1) % G)]; c = Hm[np.ix_((i0 + 1) % G, i0 % G)]; d = Hm[np.ix_((i0 + 1) % G, (i0 + 1) % G)]
    fx = f[None, :]; fy = f[:, None]; return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
Hp = samp(H); step = m.spatial_size / PX
nx = (np.roll(Hp, 1, 1) - np.roll(Hp, -1, 1)) / (2 * step); ny = (np.roll(Hp, 1, 0) - np.roll(Hp, -1, 0)) / (2 * step)
k = 1.0 / max(1e-6, np.percentile(np.hypot(nx, ny), 98))  # scale so the steepest slopes use the range
nx *= k * 0.9; ny *= k * 0.9; l = np.sqrt(nx * nx + ny * ny + 1)
px = np.ones((PX, PX, 4), dtype=np.float32); px[:, :, 0] = nx / l * 0.5 + 0.5; px[:, :, 1] = ny / l * 0.5 + 0.5; px[:, :, 2] = 1 / l * 0.5 + 0.5
img = bpy.data.images.new('n', PX, PX, alpha=False); img.colorspace_settings.name = 'Non-Color'
img.pixels[:] = px.reshape(-1); img.filepath_raw = OUT; img.file_format = 'PNG'; img.save()
print('grid', G, 'wrote', OUT, os.path.getsize(OUT) // 1024, 'kB')
