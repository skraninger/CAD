# GenerateButte V16 Rework — Session Handoff State

Saved: 2026-09-06 (session interrupted; resume from here)
Status: **Diagnosis complete. V16 not yet written.** No project files modified except the new `verify_mesh.py` (added this session).

## 1. Task (user request, verbatim intent)

Modify the logic of `GenerateButteV15.py` and create a new **`GenerateButteV16.py`** that fixes:

1. **Holes from inside to outside** — the exported shell has through-holes; must be a watertight butte shell with no interior→exterior holes.
2. **Mesa top too textured** — top must be only *slightly* textured (smoother). Sides and bottom must NOT change in character.
3. **Three resolutions are unnecessary** — V15 regenerates the grid at 60×60 (preview), 80×80 (verify/approve), 130×130 (export). Collapse to a single resolution pipeline.

User explicitly allowed: change or eliminate the features that tried and failed to fix this
(separate bottom/sides/top textures, side→top blending, mesh simplification). "Any of the logic can
change, including the core generation logic."

## 2. Environment

- Windows (win32), PowerShell 5.1, Python 3.13.9, numpy 2.3.5, matplotlib 3.10.6
- Project dir: `D:\Projects\GIT\skraninger\CAD\GenerateButte`
- GUI invariants that MUST be preserved (see Session Continuity Profile.md §3):
  - `matplotlib.use("TkAgg")` directly below imports.
  - Preview canvas uses bare `matplotlib.figure.Figure`, NEVER pyplot `plt.figure()` (v15.2 clean-exit fix; pyplot spawns a second hidden Tk root → zombie process on close under Python 3.13).
- Headless testing works: importing the module does not launch the GUI (guarded by `__main__`).

## 3. Files

| File | State |
|---|---|
| `GenerateButteV15.py` | Original, UNMODIFIED (reference) |
| `verify_mesh.py` | NEW this session — headless watertightness verifier (see §6) |
| `GenerateButteV16.py` | **TO BE CREATED** |
| `Procedural 3D Butte Generator - Session Continuity Profile.md` | V15 history doc; read for context, do not edit yet |
| `GenerateButte.bat` | Runs `python GenerateButtev15.py` — update to V16 when done |

Git note: `git status` shows `GenerateButteV15.py` as Modified with ~156 uncommitted insertions —
that is the v15.3–v15.6 work from EARLIER sessions (seed control, simplification, compact GUI,
param save/load), never committed. The working copy IS the current V15; do not revert it.

## 4. Diagnosis of V15 (COMPLETED — verified empirically)

Headless run of V15 engine + writer logic, defaults (Sandstone, seed 55, 120×120mm,
strata 2.5, textures 1.5/1.5/1.5, transition 1.5, brim 5mm, shell 5mm, res 130):

```
mask nodes: 14309 of 16900
facets=56208 edges=76542 open=66 nonmanifold=7803 components=1 vol=-205098.5 => FAIL
inner-above-outer nodes: 0 (OK)
```

### Root cause A — open edges = literal holes (66 of them)
`write_contour_binary_stl` triangulates the outer surface only over cells whose **four mask corners
are all valid**, but places skirt (stitch) quads on **mask-transition edges** (one endpoint valid,
one invalid). These two edge sets do NOT match at staircase corners of the mask boundary:

- The true boundary loop of the outer triangle sheet consists of edges where **both endpoints are
  valid** but only one adjacent cell is fully covered (concave notches of the fully-covered-cell
  union). Those edges get NO skirt → open edges → holes.
- Skirt quads placed on T→F transition edges attach to edges that belong to **no** outer triangle
  (the adjacent cells are never fully valid) → dangling quads with their own open edges.

### Root cause B — non-manifold double skin (7803 edges, count>2)
On every flat z=0 region (the brim/padding ring), the inner surface **coincides exactly** with the
outer: normal is straight up, offset `P_in = P_out - t*N` gives z=-t, clamped to 0 → inner == outer.
Both skins are emitted over those cells → each shared edge carries 4 facets (2 outer + 2 inner) →
non-manifold. The padding ring is large: `mountain_base_mask = Z_base >= 0.005` extends to
R≈14.3 raw units in the ±15 domain, plus ~6 cells of pad → mask covers 85% of the grid.

### Root cause C — inconsistent winding (signed volume NEGATIVE: -205098.5)
Some facets point inward (stitch quad winding and/or the coincident double skin). Slicers may invert
solid/void or reject the file. A correct outward-wound closed shell must give positive signed volume.

### Secondary risk (not triggered at defaults, but latent)
Noise relief amplitude can reach ~1.06 raw units × texture factor 1.5 ≈ 6mm of bump on a 0.92mm
grid pitch, vs a 5mm shell → per-vertex normal offset can self-intersect the inner surface on
noisy cliffs for other seeds/styles/shell values (inner-above-outer = 0 at defaults only).

### V15 geometry facts (raw units, ±15 domain — needed for the rewrite)
- `R_adj = R + 1.5*sin(3θ) + 0.6*cos(5θ)`; `Z_sig = 10/(1+exp(2*(R_adj-10.5)))`
- Cap: smoothstep blend of Z_sig to `cap_level=9.4`, band width = `side_top_transition` (default 1.5)
- Noise: 4 octaves f=[1.0,2.5,6.0,12.0], a=[0.6,0.3,0.12,0.04], random phases from
  `np.random.seed(seed)` (draw order is load-bearing; default seed 55)
- Zone texture field: w_top (elev 0.65–0.90 × flatness), w_side (slope 0.35–0.75, masked by 1-w_top),
  w_bottom = residual; partition of unity
- `cliff_envelope = exp(-((R_adj-10)/2.5)^2)` modulates only the strata term
- Step 4: `Z[~mountain_base_mask] = 0` → padding ring AND everything outside is exactly z=0
- valid_mask = square dilation of mountain_base_mask by pad cells (brim mm → grid cells)
- Style switcher: Sandstone (step ledges), Shale (fine sheets), Granite (floor joints)

## 5. V16 design decisions (agreed direction — implement these)

### 5.1 New STL writer: watertight by construction (fixes holes + double skin + winding)
Replace the mask-transition stitching with a **covered-cell boundary** construction:

- `covered[i,j] = mask[i,j] & mask[i+1,j] & mask[i,j+1] & mask[i+1,j+1]`
- Outer triangles over all covered cells (winding → outward/up normals).
- Inner triangles over covered cells **only where a real cavity exists** (e.g. cell min of
  `Z - Z_in > eps`), reversed winding — this eliminates the coincident double skin on the brim.
- Skirt quads along the **true boundary edges of the covered-cell union**: an edge is a boundary
  edge iff exactly one of its two adjacent cells is covered (out-of-domain = not covered).
  - horizontal edge nodes (i,j)-(i,j+1): boundary iff `covered[i,j] XOR covered[i-1,j]`
  - vertical edge nodes (i,j)-(i+1,j): boundary iff `covered[i,j] XOR covered[i,j-1]`
- This guarantees ∂skirt = ∂outer exactly → no open edges, by construction.

**OPEN ISSUE to resolve during implementation:** suppressing inner faces where Z_in≈Z creates a
transition contour *inside* the sheet (where cavity begins/ends) that also needs closing. Two
candidate resolutions (decide while coding, verify with `verify_mesh.py`):
  - (a) Keep inner surface over ALL covered cells but MERGE coincident vertices: wherever
    Z_in == Z (within eps), snap the inner vertex to the outer vertex AND skip the degenerate
    quads — risky, needs care.
  - (b) **Preferred:** make the cavity region's boundary lie ON the bed plane so no interior
    transition exists: emit inner faces only over cells fully above the cavity floor and close the
    bottom with a flat bed-plane triangulation of the footing ring (both the outer perimeter loop
    and the cavity-floor loop sit at z=0; disk ∪ annulus ∪ disk = closed sphere, no vertical skirt
    needed at all). Cells straddling Z_in=0 need edge splitting or a conservative cell test.
  - (c) Fallback if (b) gets messy: keep V15-style single skirt loop but define the inner surface
    over the SAME covered cells everywhere and accept a zero-thickness brim, fixing only the
    boundary-edge set + winding — then check whether the slicer-relevant non-manifold edges
    disappear. (Less clean; last resort.)

Whichever is chosen: final mesh MUST pass `verify_mesh.py` (open=0, nonmanifold=0, components=1,
vol>0) across styles/seeds/shells (see §6 matrix).

### 5.2 Smoother mesa top (fixes "too much texture")
Sides/bottom keep their current look. On the flat cap only:
- Strongly attenuate the stochastic noise (target: just a whisper of relief), and/or
- Low-pass it: on the cap use only the lowest octave(s) so no fine grain remains, and/or
- Blend Z toward the clean cap level over the plateau (e.g. keep ~10–25% of low-freq noise).
Implementation note: the zone field already isolates the top via `w_top` (elev×flatness ramp);
scale/replace the noise contribution there. Keep the partition-of-unity property if the three
texture sliders are kept. **User allowed eliminating** the 3-zone texture system, side→top blending,
and mesh simplification if simpler logic solves the problems — but sides/bottom appearance must be
preserved, so the zone field (or an equivalent) for bottom/sides should stay in some form.

### 5.3 Single resolution pipeline (fixes "three resolutions")
- One grid resolution used for preview, verify/approve, AND export.
- Add ONE "Mesh Resolution" spinbox (suggested default 130, range ~40–260) read in `get_params()`;
  remove the 60/80/130 triple regeneration and the Mesh Simplification control + `simplify_grid_mesh`.
- Preview at full res on every slider move is acceptable (numpy grid build is fast; matplotlib
  plot_surface at 130×130 is fine).

### 5.4 Keep / preserve from V15
- Engine steps 1–6 (radial framing, sigmoid+shoulder profile, noise, styles, masking, brim dilation,
  mm rescaling) — sides/bottom look must be unchanged.
- Normal-offset hollowing math is fine in principle; the MESH WRITER is what's broken. If the chosen
  writer design (§5.1b) needs the inner surface to stay strictly above z=0 inside the cavity, keep
  `Z_in = max(0, ...)` clamping as-is.
- GUI structure: bare Figure, TkAgg hook, compact rows, get_params() validation, save/load JSON
  params (update key set if controls change), approval state machine (any change → re-verify),
  export naming pattern.
- Deterministic seed handling (`np.random.seed(seed)` before phase draws; don't reorder draws).

## 6. Verification protocol (MUST pass before declaring done)

`verify_mesh.py <module> [style] [shell] [res]` — checks open edges, non-manifold edges, connected
components, signed volume sign, inner-above-outer nodes. Exit code 0 = PASS. If V16 exposes a
`build_facets(...)` function the verifier uses it automatically (preferred: expose one so the
verifier tests the REAL writer logic, not a replica).

Test matrix for `GenerateButteV16`:
- styles: Sandstone, Shale, Granite
- shell: 0.0 (solid mode — must also be watertight), 2.0, 5.0, 10.0
- seeds: 55, 60, 7 (at least)
- res: 90 and 130
- Also eyeball top smoothness in the GUI preview (manual step for the user).

## 7. Exact resume point / next actions

1. Implement `GenerateButteV16.py` per §5 (copy V15 as base, rewrite writer + top texture + resolution).
2. Expose `build_facets(X,Y,Z,Xi,Yi,Zi,mask,shell)` in the module; run:
   `python verify_mesh.py GenerateButteV16 Sandstone 5.0 130` → iterate until PASS.
3. Run the full §6 matrix (script it if handy: loop styles×shells×seeds).
4. Manual GUI check: window opens, preview renders, top looks smooth, export writes STL, close X exits cleanly.
5. Update `GenerateButte.bat` to run V16; optionally append a V16 section to the Session Continuity Profile.md.

## 8. Scratch notes (analysis trail)

- Temp copy of first diagnostic: `C:\Users\skran\AppData\Local\Temp\opencode\diag_v15.py` (may be
  cleaned up; superseded by project `verify_mesh.py`).
- Mask boundary is at the OUTER edge of the padding ring where terrain is exactly z=0 with zero
  gradient → V15's stitch quads there are flat z=0 patches (not all degenerate — they have XY area
  when the in-node normal has a horizontal component, which it usually doesn't 6 cells out → most
  get filtered by the area test; the survivors + notch edges = the 66 open edges).
- Signed volume of a consistent outward-wound closed shell = enclosed volume > 0. V15's negative
  value confirms winding bugs independent of the edge-count issues.
- `inner-above-outer nodes: 0` at defaults means node-level negative thickness isn't the hole cause;
  topology (open edges) + double skin are.
