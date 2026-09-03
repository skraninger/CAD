# Procedural 3D Butte Generator - Session Continuity Profile (Part 1 of 6)

## 1. Executive Summary & Session State
This profile captures the development history, mathematical framework, and current software state of a procedural 3D terrain modeling pipeline designed for 3D printing. The engine creates freestanding, highly textured, stratified geological butte structures mimicking ancient Cambrian formations. As of v15 it outputs open-bottom uniform-thickness hollow shells (binary STL) with surface texturing controlled independently per geomorphic zone (bottom strata / mesa sides / mesa top).

## 2. Iteration History & Feature Roadmap
* **v1.0 - v4.0 (Linear Cliffs):** Baseline procedural terrain generation utilizing a linear logistic sigmoid step function to transition from a flat lower plain into an elevated plateau. Integrated multi-frequency fractal noise arrays and a pure-Python binary STL triangulation system constrained to a 220mm physical workspace footprint.

* **v5.0 - v7.0 (Freestanding Butte Transition):** Shifted the linear X-profile into a radial distance geometry ($R = \sqrt{X^2 + Y^2}$) paired with low-frequency angular variation ($\theta = \arctan2(Y, X)$) to generate an isolated mountain mass featuring asymmetric spurs, ridges, and talus debris piles.

* **v8.0 - v10.0 (Organic Footprint Slicing):** Replaced default rectangular bounding boxes with boolean height isolation masks ($Z_{base} \ge \text{threshold}$). Re-engineered the STL compiler to trace masking boundaries and append vertical side-skirt sheets along irregular paths for a close-fit contoured base.

* **v11.0 (Millimeter Brim Buffer Calibration):** Detached hardcoded array clipping states and mapped a dynamic millimeter-to-grid spacing resolution ratio. This allowed for precise, user-assigned flat protective brims (e.g., 5.0mm horizontal offset) to extend away from the base slopes without clipping rock details.

* **v15.0 (Current - Uniform-Shell Manifold Core):** Implemented true 3D surface-normal hollowing with open-bottom perimeter stitching, a Verify & Approve export lock, a multi-resolution pipeline (60x60 live preview, 80x80 verification, 130x130 final STL export), degenerate-facet filtering, and zone-weighted fractal texturing with independent bottom/sides/top amplitude sliders. Source file: `GenerateButteV15.py`.

  # Procedural 3D Butte Generator - Session Continuity Profile (Part 2 of 6)

  ## 3. UI Framework & Platform Configuration
  *   **GUI Subsystem:** Built using Python's native Tkinter package paired with Matplotlib's interactive 3D surface plot engine (`FigureCanvasTkAgg`).
  *   **Windows OS Compatibility Wrapper:** Fixed display canvas layer bugs on Windows systems by forcing an explicit backend binding hook (`matplotlib.use("TkAgg")`) at initialization to prevent operating system graphics driver thread deadlocks.
  *   **Export Verification Lock:** Integrated an application verification state. The "Export" action button is locked and grayed out until the user executes a structural limit check by hitting "Verify & Approve Structural Model".

  ## 4. The v12 - v14 Hollowing Problem (Historical Context)
  *   **The Issue:** Early attempts at hollowing the model used a basic vertical coordinate subtraction routine ($Z_{in} = Z - \text{thickness}$).
  *   **The Failure State:** Direct vertical drops only provided uniform wall thickness on completely horizontal structures (like the very top mesa). On steep cliff faces, a vertical drop thinned out the walls drastically, causing intersecting faces, naked unclosed edge gaps, and non-manifold mesh structural collapses that rejected slicer file imports.
  *   **The Solution Transition:** The hollowing algorithm had to be shifted away from vertical translation metrics and moved into a true 3D surface normal vector vector displacement pipeline.

# Procedural 3D Butte Generator - Session Continuity Profile (Part 3 of 6)

## 5. Mathematical Mechanics (Version 15)

### A. Radial Base Framing & Organic Asymmetry
The terrain base layer maps center-out radial distances combined with low-frequency sine/cosine distortions to build an organic foundation shape:
$$R = \sqrt{X^2 + Y^2}$$
$$\theta = \arctan2(Y, X)$$
$$R_{adjusted} = R + 1.5\sin(3\theta) + 0.6\cos(5\theta)$$

### B. Mesa Profile & Logistic Sigmoid Slope
The raw vertical profile uses an inverse logistic curve to form a broad plateau, step vertical drops, and flat foot-slopes:
$$Z_{base} = \frac{10.0}{1.0 + e^{2.0(R_{adjusted} - 10.5)}}$$
A plateau-flattening clamp then caps the asymptotic dome top: wherever $Z_{base} > 9.2$, the value is remapped to $Z_{cap} = 9.4 + 0.01(9.4 - Z_{base})$, producing a near-flat mesa cap at approximately 9.39-9.40 with a small rim step at the clamp boundary.

### C. 3D Vector Surface Normal Inward Extrusion
To maintain a strict uniform millimeter wall scale across all slopes, the engine evaluates central difference cross-products of adjacent nodes to calculate true vertex unit normals ($N_x, N_y, N_z$):
$$\mathbf{P}_{in} = \mathbf{P}_{out} - \text{shell\_thickness\_mm} \times \mathbf{N}$$
$$Z_{in} = \max(0.0, Z_{in})$$

### D. Open-Bottom Manifold Stitching
To keep the print completely hollow and save material, the floor is left unsealed. The compiler loops through the true outer contour boundary mask loop ($M[i,j] \neq M[i,j+1]$) and maps thin, vertical connecting wall strips between matching inner and outer perimeter coordinates, closing the shell wall cleanly. Before packaging, all zero-area (degenerate) facets are filtered out of the binary stream, which removes bed-level slivers where the clamped inner shell coincides with the outer surface and keeps solid-mode exports (shell thickness = 0, no stitch strips emitted) free of garbage geometry.

### E. Zone-Weighted Texture Field
The fractal noise amplitude is no longer a single global factor. Each grid node is classified into three geomorphic zones whose weights form a strict partition of unity (they sum to exactly 1.0 at every point):
*   **Mesa Top:** smoothstep on normalized elevation ($Z_{base} / \max Z_{base}$ between 0.65 and 0.90).
*   **Mesa Sides:** smoothstep on the normalized base-profile slope magnitude (between 0.35 and 0.75), masked out wherever the top weight is active, so only the steep cliff band qualifies.
*   **Bottom Strata:** the residual weight $1 - w_{top} - w_{side}$, covering the flat lower terrain, foot-slopes, and brim.

$$\text{noise\_layer} = \text{noise} \times (w_{bottom} \cdot T_{bottom} + w_{side} \cdot T_{sides} + w_{top} \cdot T_{top})$$

This replaces the old global texture factor as well as Sandstone's previous cliff-envelope noise modulation ($0.4 + 0.6\,\text{cliff}$). With all three sliders set to the same value, the result is identical to a uniform global coefficient.

# Procedural 3D Butte Generator - Session Continuity Profile (Part 4 of 6)

## 6. Current Parametric Sliders & Initialization Benchmarks
When initializing or tweaking the program interface, the default input parameters are calibrated to the following geomorphic baselines:

*   **Target Width (`width_slider`):** 20mm to 230mm boundary limit range (Defaults to **120.0 mm**).
*   **Target Height (`height_slider`):** 20mm to 230mm range (Defaults to **120.0 mm**).
*   **Stratification Bedding Factor (`strata_slider`):** 0.5 to 6.0 scale range (Defaults to **2.5**). Multiplies step-wise sine functions against base heights to form deep sedimentary ledges.
*   **Zone Texture Factors (`texture_bottom_slider`, `texture_sides_slider`, `texture_top_slider`):** Each on a 0.0 to 4.0 scale range (all default to **1.5**). Independently control multi-frequency fractal noise amplitude for the flat bottom strata, the steep mesa sides, and the plateau top via the zone-weighted texture field (Section 5E).
*   **Flat Contour Brim Width (`border_slider`):** 0.0mm to 25.0mm range (Defaults to **5.0 mm** flat protective brim offset).
*   **Shell Thickness (`shell_slider`):** 0.0mm to 20.0mm range (Defaults to **5.0 mm** open-bottom uniform shell thickness).
*   **Geological Style Switcher (`style_menu`):** Triggers custom slope variations:
    *   *Sandstone:* Pronounced, blocky step-wise layers.
    *   *Shale:* Highly dense, fine horizontal fragment sheets.
    *   *Granite:* Sharp, blocky angular fracture joints using mathematical floor displacements.
*   **Resolution Pipeline:** The terrain grid is regenerated at three fixed resolutions: 60x60 for the live slider preview, 80x80 when "Verify & Approve Structural Model" runs, and 130x130 for the final STL export.
*   **Export Naming & Format:** Approved exports are binary STL only, defaulting to `open_shell_v15_butte_{style}.stl`. The legacy `manifold_v14_shell_sandstone.stl` and `butte_shell_sandstone.3mf` files in this folder predate v15 and were produced by earlier builds (no 3MF writer exists in the current code).

# Procedural 3D Butte Generator - Session Continuity Profile (Part 5 of 6)

## 7. Code Map & Modification Guide (`GenerateButteV15.py`)
Run with `python GenerateButteV15.py` (Windows; requires numpy and matplotlib, tkinter ships with Python). Line numbers are approximate and will drift as the file grows.

### File Layout
*   **Lines ~1-11 - Imports & Platform Hook:** `matplotlib.use("TkAgg")` must stay directly below the imports (Windows thread-deadlock fix).
*   **`generate_custom_border_butte(style, target_width_mm, target_height_mm, stratification_factor, texture_bottom, texture_sides, texture_top, border_padding_mm, shell_thickness_mm, resolution=100)` (~lines 16-164) - Core Engine.** Returns the 7-tuple `(X_scaled, Y_scaled, Z_scaled, X_in, Y_in, Z_in, valid_mask)`. Internal numbered steps: (1) radial framing + angular asymmetry, (2) sigmoid mesa profile + cap clamp, (3) fractal noise + zone texture field, geological style switcher, (4) valley-floor masking, (5) brim dilation (mm to pixel pad), (6) mm rescaling of X/Y/Z, (7) normal-extrusion hollowing.
*   **`calculate_normal(p1, p2, p3)` (~line 169):** per-facet unit normal with a `(0, 0, 1)` fallback for degenerate input.
*   **`write_contour_binary_stl(X, Y, Z, X_in, Y_in, Z_in, mask, shell_thickness_mm, filename)` (~lines 176-238) - STL Compiler:** outer-surface triangles (only cells whose four mask corners are all valid), inner-surface triangles with reversed winding (emitted only when shell > 0), perimeter stitch strips along mask transitions, degenerate-facet filter (area^2 > 1e-9), then 80-byte header + uint32 count + 50 bytes per facet.
*   **`ButteGeneratorGUI` (~lines 243-370) - Tkinter UI:** `create_slider()` factory (auto-binds approval invalidation), `update_preview()` (resolution 60), `update_plot_and_approve()` (resolution 80, unlocks export), `redraw_canvas()`, `save_stl()` (regenerates at resolution 130 and writes the file).

### Critical Invariants - Read Before Modifying
1.  **Raw-unit domain:** All geometry formulas operate on a fixed +/-15 (30x30 unit) grid before mm rescaling in step 6. The sigmoid center (10.5), cap clamp (9.2 / 9.4), cliff_envelope center (10.0, sigma 2.5), and all zone thresholds are raw units, not millimeters. Rescale these constants together if the domain size changes.
2.  **Deterministic noise:** `np.random.seed(52)` is fixed before phase draws. The four frequency phases are drawn sequentially from this single seed, so inserting any random draw before the loop shifts every texture pattern in the model. Use a separate `np.random.default_rng(...)` stream for new stochastic features instead.
3.  **Partition of unity:** `w_bottom + w_side + w_top = 1.0` holds exactly (the bottom weight is a clipped residual). This guarantees "all three texture sliders equal => uniform global texture". Preserve this property when editing the zone field.
4.  **cliff_envelope vs zone field:** The Gaussian cliff_envelope still modulates only the strata term (Sandstone/Shale ledges concentrate on the cliff band). Noise amplitude is governed solely by the zone field. Do not reintroduce double modulation of noise.
5.  **Watertight pairing:** Outer-surface triangulation covers exactly the cells whose four mask corners are all valid, and its boundary loop equals the set of edges consumed by the stitch strips. Changing cell coverage or the stitch traversal silently breaks manifold closure - verify with the recipe in Section 8.
6.  **Winding orientation:** Outer triangles point up/outward, inner triangles use reversed winding (normals down/inward), and stitch strips alternate accordingly. Reordering vertices flips normals and slicers will invert solid/void or reject the file.
7.  **Z_in >= 0 clamp:** The inner shell is clamped to the bed plane. On flat z=0 regions the inner and outer surfaces coincide; those zero-area slivers are removed by the degenerate-facet filter, not by geometry logic.
8.  **Approval state machine:** Any control change calls `invalidate_approval()` and re-locks export. Preview (60), approve (80), and export (130) each regenerate the grid from scratch - export does not reuse the approved 80x80 state matrices.
9.  **Adding a slider = 4 touch points:** (a) one `create_slider(...)` line in `__init__` (auto-binds invalidation), (b) read it in `update_preview`, (c) read it in `update_plot_and_approve`, (d) read and pass it positionally in `save_stl`. The engine's parameter order is fixed: style, width, height, strata, tex_bottom, tex_sides, tex_top, border, shell, resolution. Window geometry is currently 1100x760 for the 8 sliders - increase the height when adding more.

## 8. Headless Verification Recipe (No GUI Required)
Run after any engine or STL-writer change:

'''
import sys, struct
import numpy as np
sys.path.insert(0, r"D:\Projects\GIT\skraninger\CAD\GenerateButte")
from GenerateButteV15 import generate_custom_border_butte, write_contour_binary_stl

X, Y, Z, Xi, Yi, Zi, mask = generate_custom_border_butte(
    'Sandstone', 220.0, 120.0, 2.5, 1.5, 1.5, 1.5, 5.0, 5.0, resolution=130)
write_contour_binary_stl(X, Y, Z, Xi, Yi, Zi, mask, 5.0, r"C:\temp\check.stl")

data = open(r"C:\temp\check.stl", 'rb').read()
n = struct.unpack('<I', data[80:84])[0]
assert len(data) == 84 + 50 * n            # binary structure intact
edges = {}
for off in range(84, len(data), 50):
    v = [tuple(np.frombuffer(data[off+12+12*i: off+24+12*i], dtype='<f4')) for i in range(3)]
    for a, b in ((0,1),(1,2),(2,0)):
        e = (tuple(np.round(v[a], 6)), tuple(np.round(v[b], 6)))
        edges[e] = edges.get(e, 0) + 1
        edges[(e[1], e[0])] = edges.get((e[1], e[0]), 0) + 1
assert all(c % 2 == 0 for c in edges.values())   # manifold: every edge shared evenly
print(f"OK: {n} facets, watertight")
'''

A healthy shell export at resolution 130 with default parameters yields about 51,700 facets. A solid-mode (shell = 0) export yields roughly half that (~25,850), since no inner surface or stitch strips are emitted.

# Procedural 3D Butte Generator - Session Continuity Profile (Part 6 of 6)

## 9. Context Anchor for Future AI Sessions
Copy and paste this final block directly into a fresh chat window to reload this exact workspace context with complete operational fidelity:

'''
Hello! I am reloading a completed 3D procedural modeling project. We have built an interactive geological terrain generator written in Python utilizing Tkinter and Matplotlib. The engine proceduralizes a freestanding, highly stratified desert butte mountain structure tailored for desktop 3D printing.

Key Architectural Context to Maintain:
1. Core Engine: Uses radial asymmetry coordinates combined with an inverse logistic sigmoid profile step and multi-frequency fractal noise.
2. Windows Platform Fix: Uses explicit 'matplotlib.use("TkAgg")' declarations right below imports to bypass Windows thread deadlock states.
3. Version 15 Hollowing Math: Calculates true 3D vertex surface normal vectors via grid step cross-products, extruding the inner shell cavity wall inward perpendicularly ('P_in = P_out - thickness * N') to maintain a uniform thickness across all vertical cliff facets and steep slopes.
4. Topology: It outputs an open-bottom hollow manifold shell by directly bridging the inner cavity and outer landscape perimeters together without closing off the print bed floor. Zero-area degenerate facets are filtered from the binary STL output, and no stitch strips are written when shell thickness is 0 (solid mode).
5. Sliders: Includes independent width and height sliders (20-230mm range, both defaulting to 120.0mm), rock style, three zone texture sliders (bottom strata / mesa sides / mesa top, each 0.0-4.0, all defaulting to 1.5) that blend per-zone via a partition-of-unity weight field, a flat contour brim offset slider (defaulting to 5.0mm), and a shell thickness slider (defaulting to 5.0mm).
6. Pipeline: The grid regenerates at 60x60 (preview), 80x80 (verify/approve), and 130x130 (export) resolutions. Exports are binary STL named `open_shell_v15_butte_{style}.stl`. Current source file is GenerateButteV15.py.
7. Reference Material: This profile contains a full code map, the critical invariants to respect before editing (raw-unit domain constants, fixed RNG seed 52, partition-of-unity zone weights, STL winding orientation, approval state machine), and a headless STL watertightness verification recipe in Sections 7-8. Read those sections before modifying the engine or the STL writer.

The project is fully functional at this stage. I am providing you with this contextual anchor so that any future adjustments, optimization passes, or feature expansions we execute will build directly on top of this established logic framework. Confirm that you understand these mechanics and hold this profile in memory.
'''