# owner look refs, 2026-11-12 (vibrant / clean outdoor look)

The owner sent these three screenshots of another mech hero shooter and asked: "How do we get nicer more vibrant textures like this".
They are **look references only**. Copy the feel (light, colour, softness), never the assets, layouts or characters.
This branch stays off `main`.

| file | what to take from it |
|---|---|
| `01_park_blossoms.webp` | bright yellow-green grass with soft low-frequency mottling, no visible tiling; big clumpy pink blossom canopies; pale paving; pastel peach clouds |
| `02_grass_hill_trees.webp` | dense leafy canopies lit yellow-green on top, darker underneath; soft light shadows; distance fades into blue haze |
| `03_running_track.webp` | flat terracotta track with crisp white lines, light concrete kerb; deep blue sky to pale horizon; clean anti-aliased edges |

What makes it read as "vibrant" (coordinator notes):
- painted, low-frequency ground textures (big soft colour variation, almost no high-frequency noise)
- smooth filtering + mipmaps + anisotropy, and anti-aliasing (no shimmer, no jaggies)
- high-key light: bright warm sun, strong sky/hemisphere fill, so shadows are soft and coloured instead of black
- a gentle saturation/vibrance grade on top of filmic tone mapping
- sky gradient (deep blue top, pale horizon) with pastel lit clouds, plus aerial haze on far objects
- stylised dense trees (leaf clusters, gradient shading) instead of single blobs
