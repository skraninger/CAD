# AGENTS.md

## Repo layout
Monorepo of independent 3D-printing CAD projects. Each top-level folder is a
self-contained project with no shared build, test, lint, or package system —
there is nothing to run at the repo root. Work inside one project folder at a time.

- Most projects are **OpenSCAD**: the `.scad` file is the source of truth and
  `.stl` / `.3mf` are generated exports. Edit the `.scad`, re-export with
  external OpenSCAD — never hand-edit mesh files.
- `GenerateButte/` is a Python GUI generator (see below).
- `Midi_Pedal/` and `LayeredLamp/` also contain firmware (CircuitPython /
  Arduino ATtiny) alongside the CAD parts.

## GenerateButte (procedural butte generator)
Python + Tkinter + Matplotlib GUI that outputs open-bottom hollow-shell binary
STL for 3D printing. Requires `numpy` and `matplotlib` (tkinter ships with
Python). No requirements.txt — `pip install numpy matplotlib`.

- **Current version is V16** (`GenerateButteV16.py`, launched by
  `GenerateButte.bat`). Run: `python GenerateButteV16.py`.
  `GenerateButteV15.py` is the prior version, kept for reference. V16 changes vs
  V15: (a) `TOP_ATTENUATION = 0.15` attenuates mesa-top texture; (b) **smooth zone
  hand-offs** — each per-zone texture is multiplied by a smoothstep weight that
  reaches 0 at the zone boundary, and the side stratification pattern is continuous
  (no hard step), so there are no +z spikes where sides meet top or base. The
  `zone_blend` engine arg / "Zone Blend" slider widens (>1) or tightens (<1) every
  hand-off ramp.
- **Headless structural check** (run before/after engine or STL-writer edits):
  ```
  python verify_mesh.py GenerateButteV16 Sandstone 5.0 130
  ```
  Args: `<module> [style] [shell_mm] [resolution]`. Exits 0 = pass, 2 = fail.
  It is tuned for the **open-bottom bowl**: it hard-fails only on multiple
  components, *interior* open edges (real wall holes — open edges on the footprint
  rim are the expected bottom opening), elevated non-manifold edges, and negative
  wall thickness. The flat-foot z=0 coincidence is reported as benign, not fatal.
  A healthy hollow mesh **exits 0**; use it to confirm an edit didn't introduce a
  real defect (and watch `signed_vol` magnitude for regressions). Solid mode
  (`shell_mm == 0`) has an open base skirt by construction and is out of scope.
- **Read `GenerateButte/Procedural 3D Butte Generator - Session Continuity Profile.md`
  before modifying the engine or STL writer.** It has the full code map and the
  load-bearing invariants below.

### Invariants that are easy to break (GenerateButteV15/V16.py)
- `matplotlib.use("TkAgg")` must stay directly under the imports (Windows thread-deadlock fix).
- The preview is a bare `matplotlib.figure.Figure`, **never** pyplot's
  `plt.figure()` — pyplot spawns a second hidden Tk root and `mainloop()` hangs
  on window close (zombie process). Do not "simplify" this back.
- Geometry math runs in a fixed raw-unit ±15 (30×30) domain before mm rescaling;
  constants like sigmoid center 10.5, cap level 9.4, and zone thresholds are raw
  units, not millimeters. Move them together if the domain changes.
- `np.random.seed(int(seed))` is set before the fractal phase draws and the four
  frequency phases draw sequentially from that one stream. Adding a random draw
  before the loop shifts every texture for every seed — use a separate
  `np.random.default_rng(...)` for new stochastic features.
- Zone texture weights (`w_bottom + w_side + w_top`) form a partition of unity;
  keep that so "all three sliders equal ⇒ uniform global texture" still holds.
- The no-spike guarantee comes from **gating side detail by `w_side`** (a smoothstep
  of slope that is 0 on both the flat top and flat base) and using a *continuous*
  side pattern (`tanh`/`sin`, never `np.where` hard steps). Reintroducing a hard
  step or gating by the old `cliff_envelope` Gaussian brings back +z spikes at the
  shoulder. `zone_blend` only rescales the smoothstep ramp widths.
- STL winding: outer triangles up/outward, inner reversed (down/inward), stitch
  strips alternate. Reordering vertices flips normals and slicers reject the file.
- Zero-area degenerate facets are filtered in the writer (area² > 1e-9); no stitch
  strips are emitted when shell thickness = 0 (solid mode).
- Adding a GUI control = 2 touch points: one `add_slider_row`/`add_entry_row` in
  `__init__`, and read it once in `get_params()`. Engine arg order is fixed.
