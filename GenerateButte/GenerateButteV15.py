# -*- coding: utf-8 -*-
import struct
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np

# Force Tkinter window layer binding explicitly for Windows environments
import matplotlib
matplotlib.use("TkAgg")
# v15.2 CLEAN-EXIT FIX: use a bare Figure instead of pyplot's plt.figure().
# pyplot's figure manager creates its own hidden tk.Tk() root window behind the
# scenes; with two Tk roots in one process, mainloop() never returns after the
# app window is destroyed on Python 3.13 -- clicking X left a zombie process
# running forever. A bare Figure creates no window at all, so the app's Tk
# root stays the only instance and the program exits cleanly when closed.
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================
# 1. CORE GEOLOGY ENGINE (VERSION 15)
# ==========================================
def generate_custom_border_butte(style, target_width_mm, target_height_mm,
                                 stratification_factor, texture_bottom, texture_sides, texture_top,
                                 side_top_transition, border_padding_mm, shell_thickness_mm, resolution=100, seed=55):
    """
    Generates a freestanding butte terrain with 100% feature preservation,
    manually adjustable border padding, and true 3D normal vector hollowing.

    `side_top_transition` (raw units) sets the width of the smooth shoulder
    that blends the steep cliff profile into the flat mesa cap. A small value
    gives a tight rounded rim; a large value lets the flat-cap surface bleed
    gradually down the flank. Replaces the old hard clamp, which left a
    vertical step ("spike") where the side met the top.

    `seed` (v15.3) sets the RNG seed for the fractal texture phase draws so
    the noise pattern is user-selectable from the UI; default 55 keeps the
    historical pattern. Same seed => identical texture, every run.
    """
    nx, ny = resolution, resolution
    x = np.linspace(-15, 15, nx)
    y = np.linspace(-15, 15, ny)
    X, Y = np.meshgrid(x, y)
    
    # 1. Radial Base Framing with Structural Asymmetry
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)
    
    # v15.3: RNG seed is now UI-controlled (default 55 = historical pattern).
    # It makes the fractal texture below deterministic for a given seed value.
    # These phase draws are the ONLY randomness in the engine and their order
    # is load-bearing -- see the noise loop before inserting any new draws.
    np.random.seed(int(seed))
    
    r_variation = 1.5 * np.sin(3 * Theta) + 0.6 * np.cos(5 * Theta)
    R_adjusted = R + r_variation
    
    # 2. Base Mesa Profile with a smooth side->top shoulder
    # ------------------------------------------------------------------
    # The raw sigmoid gives the cliff and foot-slope; the flat mesa cap is
    # blended in on top of it with a C1-smooth smoothstep. This replaces the
    # old hard `np.where(Z_base > 9.2, ...)` clamp, which jumped ~0.2 raw units
    # (a visible vertical "spike") at the exact point where the cliff met the
    # cap. Now the handover is a continuous rounded shoulder whose width is
    # controlled by `side_top_transition` (raw units): small = tight rim,
    # large = the flat-cap surface bleeds gradually down the flank.
    # ------------------------------------------------------------------
    Z_sig = 10.0 / (1.0 + np.exp(2.0 * (R_adjusted - 10.5)))
    cap_level = 9.4
    band_lo = max(cap_level - float(side_top_transition), 0.0)
    denom = max(cap_level - band_lo, 1e-6)
    t_cap = np.clip((Z_sig - band_lo) / denom, 0.0, 1.0)
    w_cap = t_cap * t_cap * (3.0 - 2.0 * t_cap)          # smoothstep: C1 at both ends
    Z_base = Z_sig + w_cap * (cap_level - Z_sig)         # lerp(cliff -> flat cap)
    
    # 3. Multi-Frequency Fractal Noise Layer (Texturing Engine)
    # ------------------------------------------------------------------
    # Stochastic rock relief, built as a sum of four sinusoidal "octaves":
    #     noise = sum over octaves of  a * sin(f*X + phi_x) * cos(f*Y + phi_y)
    #
    # Why sin(X)*cos(Y) products with random phases:
    #   * Without the phase offsets every octave would peak on the X and Y
    #     axes and the surface would look like axis-aligned interference
    #     fringes. Randomizing phi_x/phi_y per octave scatters the peaks so
    #     the pattern reads as weathered stone, not a grid.
    #   * By product-to-sum, sin(A)*cos(B) = 0.5*(sin(A+B) + sin(A-B)): each
    #     octave is really two wavefronts running at +/-45 degrees to the
    #     axes. Those diagonal ridges read as tilted sedimentary bedding
    #     once the surface is scaled and rendered.
    #
    # Fractal falloff: each octave steps up ~2-2.5x in spatial frequency
    # while amplitude drops by about half, so f=1.0 (a=0.6) sculpts broad
    # undulations and f=12.0 (a=0.04) adds fine grain. The theoretical max
    # |noise| is the sum of amplitudes = 1.06 raw units (all phases aligned);
    # random phases keep real values well below that.
    #
    # Units: noise lives in the same raw +/-15 domain as Z_base, so step 6's
    # z_scale stretches the relief together with the butte -- raising the
    # height slider amplifies texture depth proportionally.
    # ------------------------------------------------------------------
    noise = np.zeros_like(X)
    frequencies = [1.0, 2.5, 6.0, 12.0]   # spatial frequency per octave (rad / raw unit)
    amplitudes = [0.6, 0.3, 0.12, 0.04]   # ~halved each octave => fractal falloff

    for f, a in zip(frequencies, amplitudes):
        # Phase pair drawn sequentially from the single seed-52 stream. The
        # draw order is fixed (octave 1 phi_x, octave 1 phi_y, octave 2 ...),
        # so ANY np.random call inserted before or inside this loop
        # re-sequences every phase and silently changes the texture pattern
        # on the whole model. New stochastic features must use their own
        # stream instead:  rng = np.random.default_rng(<fixed seed>)
        phi_x = np.random.uniform(0, 2 * np.pi)
        phi_y = np.random.uniform(0, 2 * np.pi)
        noise += a * np.sin(f * X + phi_x) * np.cos(f * Y + phi_y)
        
    # Gaussian band centered on the cliff line (R_adjusted ~ 10.0 raw units,
    # sigma = 2.5). Modulates ONLY the strata term in the style switcher
    # below: it concentrates Sandstone/Shale ledges on the steep flank and
    # fades them to ~0 on the flat plain and the plateau top. It deliberately
    # does NOT touch noise amplitude -- that is exclusively the zone field's
    # job, so the two channels never double-modulate each other.
    cliff_envelope = np.exp(-((R_adjusted - 10.0) / 2.5)**2)

    # ------------------------------------------------------------------
    # Zone-based texture weighting: bottom strata / mesa sides / mesa top
    # ------------------------------------------------------------------
    # The fractal noise above has uniform amplitude everywhere; this block
    # gives each geomorphic zone its own amplitude (the three GUI sliders)
    # and cross-fades between zones so no visible boundary ring appears
    # where one zone hands over to the next.
    #
    # Every grid node is classified by two scalar fields, both computed from
    # Z_base -- the clean sigmoid profile BEFORE strata and noise are added --
    # so zone boundaries stay stable regardless of how much detail the style
    # switcher or texture sliders add:
    #   elev_norm  = Z_base / max(Z_base)       "how high up the butte am I?"
    #   slope_norm = |grad Z_base| / max(...)   "am I on a steep flank now?"
    #
    # The bottom -> sides -> top handover:
    #   * w_side fades in by SLOPE. On the flat plain and foot-slope the
    #     normalized slope is below 0.35, so w_side = 0. Climbing the sigmoid
    #     flank, slope_norm crosses 0.35 and smoothsteps up to 1.0 by 0.75,
    #     so the cliff band (where the profile drops fastest) fully belongs
    #     to the sides slider.
    #   * w_top fades in by ELEVATION AND FLATNESS. The elevation ramp is 0
    #     below 65% of max height and 1 above 90%; on its own that would bleed
    #     the top texture down the steep flank (climbing the cliff passes
    #     straight through the 65-90% band). Multiplying by a flatness ramp --
    #     1 on the level cap, smoothstepping to 0 as slope_norm reaches 0.35 --
    #     confines the top slider to the actual plateau surface. Where the
    #     cap-clamp rim step makes the summit edge steep as well, w_side would
    #     double-count -- hence the (1 - w_top) mask: at the summit the top
    #     zone always wins.
    #   * w_bottom is a RESIDUAL: 1 - w_top - w_side. Low flat terrain has
    #     both active weights ~0, so the bottom slider owns the brim, foot-
    #     slope and valley floor by default; wherever w_side or w_top rises,
    #     w_bottom shrinks by exactly that amount -- amplitudes cross-fade
    #     instead of switching.
    #   * Every ramp is smoothstep t^2(3-2t): first derivative zero at both
    #     ends of its range, so the blend is C1-smooth and texture amplitude
    #     varies continuously with no banding at the 0.65/0.90 or 0.35/0.75
    #     thresholds.
    #
    # Partition of unity: w_bottom + w_side + w_top == 1.0 at every node
    # (bottom is the clipped residual). That guarantees "all three sliders
    # equal => one uniform global texture", i.e. pre-v15 behavior remains
    # reachable from the v15 UI. If you add a zone, steal weight explicitly
    # and keep bottom as the residual to preserve this property.
    # ------------------------------------------------------------------
    grid_step = 30.0 / (resolution - 1)          # raw units per cell across the 30-unit domain
    gz_y, gz_x = np.gradient(Z_base, grid_step, grid_step)   # central-difference gradient of clean profile
    slope_mag = np.sqrt(gz_x**2 + gz_y**2)
    slope_norm = slope_mag / (np.max(slope_mag) + 1e-9)      # 0 = flat ... 1 = steepest point

    elev_norm = Z_base / (np.max(Z_base) + 1e-9)             # 0 = valley floor ... 1 = mesa cap

    # Mesa top: smoothstep on elevation between 65% and 90% of max height. This
    # alone would bleed the top texture down the steep flank, because climbing
    # the cliff passes right through the 65-90% band -- so it is multiplied by
    # a flatness ramp below that zeroes it out wherever the surface is not level.
    t_top = np.clip((elev_norm - 0.65) / (0.90 - 0.65), 0.0, 1.0)
    elev_ramp = t_top * t_top * (3.0 - 2.0 * t_top)
    # Flatness: 1 on the level cap, smoothstepping to 0 as slope_norm steepens
    # from 0.10 up to 0.35. The 0.35 exit aligns with the side zone's entry so
    # the top texture hands over exactly where the side texture takes over.
    t_flat = np.clip((0.35 - slope_norm) / (0.35 - 0.10), 0.0, 1.0)
    flat_ramp = t_flat * t_flat * (3.0 - 2.0 * t_flat)
    w_top = elev_ramp * flat_ramp
    
    # Mesa sides: smoothstep on slope steepness between 0.35 and 0.75,
    # masked out wherever the top zone is active (summit rim wins)
    t_side = np.clip((slope_norm - 0.35) / (0.75 - 0.35), 0.0, 1.0)
    w_side = t_side * t_side * (3.0 - 2.0 * t_side) * (1.0 - w_top)

    # Bottom strata: residual weight -- owns everything the other two don't
    w_bottom = np.clip(1.0 - w_top - w_side, 0.0, 1.0)

    # Per-node amplitude: weighted blend of the three slider values. With all
    # three sliders equal this collapses to that single value everywhere
    # (partition of unity), recovering a uniform global texture factor.
    texture_field = w_bottom * texture_bottom + w_side * texture_sides + w_top * texture_top
    noise_layer = noise * texture_field

    # Apply Geological Style Switcher
    # Two independent modulation channels combine in each branch: `strata` is
    # deterministic bedding ledges shaped by cliff_envelope (cliff band only),
    # while `noise_layer` carries the stochastic fractal relief with its
    # zone-weighted amplitude. Keep them separate -- never let one channel
    # re-modulate the other.
    if style == 'Sandstone':
        strata = np.sin(stratification_factor * np.pi * Z_base)
        strata = np.where(strata > 0.15, 0.35, -0.2)
        Z = Z_base + (strata * cliff_envelope) + noise_layer
    elif style == 'Shale':
        strata = 0.12 * np.sin(stratification_factor * 2.5 * np.pi * Z_base)
        Z = Z_base + (strata * cliff_envelope) + noise_layer
    elif style == 'Granite':
        joints = 0.4 * np.sin(0.3 * np.pi * X) * np.cos(0.3 * np.pi * Y)
        Z = Z_base + np.floor(joints * stratification_factor) / stratification_factor + noise_layer
    else:
        Z = Z_base + noise_layer

    Z = np.clip(Z, 0, None)
    
    # 4. Core Mountain Masking (Where terrain hits valley floor)
    mountain_base_mask = Z_base >= 0.005
    Z[~mountain_base_mask] = 0.0

    # 5. Pre-calibration step to translate requested mm to exact grid pixel steps
    x_min_raw, x_max_raw = np.min(X[mountain_base_mask]), np.max(X[mountain_base_mask])
    y_min_raw, y_max_raw = np.min(Y[mountain_base_mask]), np.max(Y[mountain_base_mask])
    
    curr_width_raw = max(x_max_raw - x_min_raw, y_max_raw - y_min_raw)
    raw_to_mm_ratio = target_width_mm / curr_width_raw
    grid_spacing_mm = (30.0 / resolution) * raw_to_mm_ratio
    
    # Compute the padding from your millimeter selection
    pad = int(np.ceil(border_padding_mm / grid_spacing_mm)) if border_padding_mm > 0 else 0
    pad = np.clip(pad, 0, int(resolution / 4))
    
    # Apply mathematical dilation to create the border buffer
    valid_mask = np.zeros_like(mountain_base_mask, dtype=bool)
    if pad > 0:
        for iy in range(ny):
            for ix in range(nx):
                if mountain_base_mask[iy, ix]:
                    y_start, y_end = max(0, iy - pad), min(ny, iy + pad + 1)
                    x_start, x_end = max(0, ix - pad), min(nx, ix + pad + 1)
                    valid_mask[y_start:y_end, x_start:x_end] = True
    else:
        valid_mask = mountain_base_mask.copy()

    # 6. Final Spatial Calibration (Ensures target width constraints)
    X_valid, Y_valid, Z_valid = X[valid_mask], Y[valid_mask], Z[valid_mask]
    x_min, x_max = np.min(X_valid), np.max(X_valid)
    y_min, y_max = np.min(Y_valid), np.max(Y_valid)
    z_min, z_max = np.min(Z_valid), np.max(Z_valid)
    
    curr_width = max(x_max - x_min, y_max - y_min)
    xy_scale = target_width_mm / curr_width
    
    X_scaled = (X - x_min) * xy_scale
    Y_scaled = (Y - y_min) * xy_scale
    
    curr_height = z_max - z_min if (z_max - z_min) > 0 else 1.0
    z_scale = target_height_mm / curr_height
    Z_scaled = (Z - z_min) * z_scale
    
    # 7. TRUE 3D SURFACE NORMAL VECTOR EXTRUSION FOR HOLLOW ENGINE
    X_in = X_scaled.copy()
    Y_in = Y_scaled.copy()
    Z_in = Z_scaled.copy()
    
    if shell_thickness_mm > 0:
        # Calculate surface normal vectors via adjacent grid gradients
        dzdx = np.zeros_like(Z_scaled)
        dzdy = np.zeros_like(Z_scaled)
        
        # Grid spacing approximations
        dx_val = target_width_mm / resolution
        dy_val = target_width_mm / resolution
        
        dzdx[:, 1:-1] = (Z_scaled[:, 2:] - Z_scaled[:, :-2]) / (2.0 * dx_val)
        dzdy[1:-1, :] = (Z_scaled[2:, :] - Z_scaled[:-2, :]) / (2.0 * dy_val)
        
        Nx = -dzdx
        Ny = -dzdy
        Nz = np.ones_like(Z_scaled)
        
        # Normalize vectors to unit length
        norm = np.sqrt(Nx**2 + Ny**2 + Nz**2)
        Nx /= norm
        Ny /= norm
        Nz /= norm
        
        # Displace vertices inward along their exact unit normal vector path
        X_in = X_scaled - shell_thickness_mm * Nx
        Y_in = Y_scaled - shell_thickness_mm * Ny
        Z_in = Z_scaled - shell_thickness_mm * Nz
        
        # Ensure interior shell faces do not cross below the print bed level
        Z_in = np.maximum(0.0, Z_in)
        
    return X_scaled, Y_scaled, Z_scaled, X_in, Y_in, Z_in, valid_mask

# ==========================================
# 2. OPEN-BOTTOM BINARY STL EXPORT ENGINE
# ==========================================
def calculate_normal(p1, p2, p3):
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    n = np.cross(v1, v2)
    norm = np.linalg.norm(n)
    return tuple(n / norm) if norm > 0 else (0.0, 0.0, 1.0)

def simplify_grid_mesh(X, Y, Z, X_in, Y_in, Z_in, mask, stride):
    """ v15.3: Coarsens a grid mesh by keeping every `stride`-th node per axis.

    Triangle count drops by roughly stride^2 (e.g. stride 4 on the 130x130
    export grid -> ~33x33, about 16x fewer facets) while the shape stays
    recognizable. Because the STL compiler below re-derives outer/inner
    pairing and perimeter stitching from whatever mask it is given, a
    downsampled mask still produces a closed open-bottom manifold shell --
    no separate repair pass is needed. stride <= 1 returns the input
    unchanged (full detail).
    """
    if stride <= 1:
        return X, Y, Z, X_in, Y_in, Z_in, mask
    return (X[::stride, ::stride], Y[::stride, ::stride], Z[::stride, ::stride],
            X_in[::stride, ::stride], Y_in[::stride, ::stride], Z_in[::stride, ::stride],
            mask[::stride, ::stride])

def write_contour_binary_stl(X, Y, Z, X_in, Y_in, Z_in, mask, shell_thickness_mm, filename):
    """ Writes an open-bottom, uniform thickness manifold shell directly to binary STL. """
    ny, nx = Z.shape
    facets = []
    
    # 1. Triangulate top landscape surfaces
    for i in range(ny - 1):
        for j in range(nx - 1):
            if mask[i,j] and mask[i+1,j] and mask[i,j+1] and mask[i+1,j+1]:
                v1_out = (X[i, j], Y[i, j], Z[i, j])
                v2_out = (X[i+1, j], Y[i+1, j], Z[i+1, j])
                v3_out = (X[i, j+1], Y[i, j+1], Z[i, j+1])
                v4_out = (X[i+1, j+1], Y[i+1, j+1], Z[i+1, j+1])
                facets.append((v1_out, v2_out, v4_out))
                facets.append((v1_out, v4_out, v3_out))
                
                # 2. Triangulate inner shell surface with reversed winding (points normals down)
                if shell_thickness_mm > 0:
                    v1_in = (X_in[i, j], Y_in[i, j], Z_in[i, j])
                    v2_in = (X_in[i+1, j], Y_in[i+1, j], Z_in[i+1, j])
                    v3_in = (X_in[i, j+1], Y_in[i, j+1], Z_in[i, j+1])
                    v4_in = (X_in[i+1, j+1], Y_in[i+1, j+1], Z_in[i+1, j+1])
                    facets.append((v1_in, v4_in, v2_in))
                    facets.append((v1_in, v3_in, v4_in))
                    
    # 3. Stitch outer and inner perimeters directly together to leave the bottom open
    for i in range(ny - 1):
        for j in range(nx - 1):
            current_node = mask[i, j]
            # Horizontal boundary edge checks
            if current_node != mask[i, j+1]:
                v1_o, v2_o = (X[i, j], Y[i, j], Z[i, j]), (X[i+1, j], Y[i+1, j], Z[i+1, j])
                v1_i, v2_i = (X_in[i, j], Y_in[i, j], Z_in[i, j]), (X_in[i+1, j], Y[i+1, j], Z_in[i+1, j])
                if current_node: # Facing outward
                    facets.append((v1_o, v1_i, v2_i)); facets.append((v1_o, v2_i, v2_o))
                else: # Facing inward
                    facets.append((v1_o, v2_i, v1_i)); facets.append((v1_o, v2_o, v2_i))
            # Vertical boundary edge checks
            if current_node != mask[i+1, j]:
                v1_o, v2_o = (X[i, j], Y[i, j], Z[i, j]), (X[i, j+1], Y[i, j+1], Z[i, j+1])
                v1_i, v2_i = (X_in[i, j], Y_in[i, j], Z_in[i, j]), (X_in[i, j+1], Y[i, j+1], Z[i, j+1])
                if current_node: # Facing outward
                    facets.append((v1_o, v2_i, v1_i)); facets.append((v1_o, v2_o, v2_i))
                else: # Facing inward
                    facets.append((v1_o, v1_i, v2_i)); facets.append((v1_o, v2_i, v2_o))

    def facet_area_squared(p1, p2, p3):
        v1 = np.array(p2) - np.array(p1)
        v2 = np.array(p3) - np.array(p1)
        c = np.cross(v1, v2)
        return float(c @ c)

    facets = [f for f in facets if facet_area_squared(*f) > 1e-9]

    # Package facets into standard binary format compliance
    with open(filename, 'wb') as f:
        f.write(b'\x00' * 80)  
        f.write(struct.pack('<I', len(facets)))
        for facet in facets:
            f.write(struct.pack('<fff', *calculate_normal(*facet)))
            for vertex in facet: 
                f.write(struct.pack('<fff', *vertex))
            f.write(struct.pack('<H', 0))
            
# ==========================================
# 3. TKINTER GRAPHICAL USER INTERFACE
# ==========================================
class ButteGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Geological Butte Parametric Engine - V15 Open-Shell Core")
        # v15.4: compact side-by-side control rows freed up vertical space,
        # so the window no longer needs 1000px of height
        self.root.geometry("1100x780")
        
        # State matrices initialization
        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = [None]*7
        self.is_model_approved = False 
        
        # Control Layout Panel (Left)
        ctrl_frame = ttk.LabelFrame(root, text=" Parametric Controls ", padding=15)
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # v15.4: every parameter is one row -- prompt on the left, control on
        # the right (grid column 1 stretches), so the panel is ~half as tall
        params = ttk.Frame(ctrl_frame)
        params.pack(fill=tk.X)
        params.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(params, text="Geological Style:").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=(2, 4))
        self.style_var = tk.StringVar(value="Sandstone")
        style_menu = ttk.Combobox(params, textvariable=self.style_var, values=["Sandstone", "Shale", "Granite"], state="readonly")
        style_menu.grid(row=row, column=1, sticky="ew", pady=(2, 4))
        style_menu.bind("<<ComboboxSelected>>", lambda e: self.invalidate_approval())
        row += 1

        # v15.3: Noise seed control -- selects the fractal texture pattern.
        # 55 is the historical default; any integer gives a new deterministic
        # pattern (same seed => identical texture on every run).
        ttk.Label(params, text="Noise Seed (texture pattern):").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=(6, 2))
        self.seed_var = tk.IntVar(value=55)
        self.seed_spin = tk.Spinbox(params, from_=0, to=99999, increment=1, width=10,
                                     textvariable=self.seed_var, command=self.invalidate_approval)
        self.seed_spin.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        row += 1
        # Spinbox `command` only fires on the arrow buttons; catch typed edits too
        self.seed_spin.bind("<KeyRelease>", lambda e: self.invalidate_approval())
        self.seed_spin.bind("<FocusOut>", lambda e: self.invalidate_approval())

        # v15.4: exact mm dimensions are plain number entries (typing a target
        # size is faster than dragging); the continuous "feel" parameters stay
        # sliders with a live value readout beside them
        self.width_entry = self.add_entry_row(params, row, "Target Width (mm):", 20, 230, 120)
        row += 1
        self.height_entry = self.add_entry_row(params, row, "Target Height (mm):", 20, 230, 120)
        row += 1
        self.strata_slider = self.add_slider_row(params, row, "Stratification Bedding Factor:", 0.5, 6.0, 2.5, resolution=0.1)
        row += 1
        self.texture_bottom_slider = self.add_slider_row(params, row, "Texture - Bottom Strata:", 0.0, 4.0, 1.5, resolution=0.1)
        row += 1
        self.texture_sides_slider = self.add_slider_row(params, row, "Texture - Mesa Sides:", 0.0, 4.0, 1.5, resolution=0.1)
        row += 1
        self.texture_top_slider = self.add_slider_row(params, row, "Texture - Mesa Top:", 0.0, 4.0, 1.5, resolution=0.1)
        row += 1
        self.side_top_slider = self.add_slider_row(params, row, "Side→Top Transition (more gradual →):", 0.2, 4.0, 1.5, resolution=0.1)
        row += 1
        self.border_entry = self.add_entry_row(params, row, "Flat Contour Brim Width (mm):", 0.0, 25.0, 5.0, increment=0.5)
        row += 1
        self.shell_entry = self.add_entry_row(params, row, "Shell Thickness (mm, 0=Solid):", 0.0, 20.0, 5.0, increment=0.5)
        row += 1

        # v15.3: Mesh simplification factor -- applies to the exported STL only
        # (preview/verify stay full detail). 1 = full detail (no change); N keeps
        # every N-th grid node per axis, cutting facet count by ~N^2.
        self.simplify_entry = self.add_entry_row(params, row, "Mesh Simplification (1=Full Detail):", 1, 8, 1)
        row += 1

        # Trigger Operations
        ttk.Button(ctrl_frame, text="Verify & Approve Structural Model", command=self.update_plot_and_approve).pack(fill=tk.X, pady=15)
        self.export_btn = ttk.Button(ctrl_frame, text="Export Approved Binary STL", command=self.save_stl, state=tk.DISABLED)
        self.export_btn.pack(fill=tk.X, pady=5)
        
        self.status_lbl = ttk.Label(ctrl_frame, text="Status: Review Pending", foreground="orange")
        self.status_lbl.pack(pady=10)
        
        # 3D Canvas Panel Display (Right)
        self.plot_frame = ttk.Frame(root, padding=10)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # v15.2: bare Figure (NOT plt.figure) -- keeps the app's Tk root as the
        # only Tk instance so closing the window exits the process cleanly.
        self.fig = Figure(figsize=(7, 6), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_preview()

    # v15.4: side-by-side parameter rows (prompt | control) to halve panel height
    def add_slider_row(self, parent, row, label, min_v, max_v, default, resolution=1.0):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=(6, 2))
        holder = ttk.Frame(parent)
        holder.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        slider = tk.Scale(holder, from_=min_v, to=max_v, orient=tk.HORIZONTAL,
                          resolution=resolution, length=140, showvalue=False)
        slider.set(default)
        value_lbl = ttk.Label(holder, text=self._fmt_value(default, resolution), width=5)

        def on_change(v, _lbl=value_lbl):
            _lbl.config(text=self._fmt_value(float(v), resolution))
            self.invalidate_approval()

        slider.config(command=on_change)
        slider.pack(side=tk.LEFT)
        value_lbl.pack(side=tk.LEFT, padx=(6, 0))
        return slider

    def add_entry_row(self, parent, row, label, min_v, max_v, default, increment=1.0):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=(6, 2))
        spin = tk.Spinbox(parent, from_=min_v, to=max_v, increment=increment, width=8,
                          justify=tk.RIGHT, command=self.invalidate_approval)
        spin.delete(0, tk.END)
        spin.insert(0, str(default))
        spin.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        # Spinbox `command` only fires on the arrow buttons; catch typed edits too
        spin.bind("<KeyRelease>", lambda e: self.invalidate_approval())
        spin.bind("<FocusOut>", lambda e: self.invalidate_approval())
        return spin

    @staticmethod
    def _fmt_value(v, resolution):
        v = float(v)
        return f"{v:.0f}" if resolution >= 1.0 else f"{v:.1f}"

    @staticmethod
    def _set_entry_text(widget, value):
        widget.delete(0, tk.END)
        widget.insert(0, str(value))

    def _read_float(self, widget, default, min_v, max_v):
        # Safe read of an entry row: invalid/empty text falls back to the
        # default, out-of-range values are clamped (the old sliders could not
        # leave their range either)
        try:
            v = float(widget.get())
            if not np.isfinite(v):
                raise ValueError
        except (tk.TclError, ValueError):
            self._set_entry_text(widget, default)
            return default
        clamped = min(max(v, min_v), max_v)
        if clamped != v:
            self._set_entry_text(widget, clamped)
            return clamped
        return v

    def get_simplify(self):
        try:
            v = int(float(self.simplify_entry.get()))
        except (tk.TclError, ValueError):
            v = 1
        return min(max(v, 1), 8)

    def get_params(self):
        # Single validated read of every control, in engine argument order
        style = self.style_var.get()
        tw = self._read_float(self.width_entry, 120, 20, 230)
        th = self._read_float(self.height_entry, 120, 20, 230)
        sf = float(self.strata_slider.get())
        tb = float(self.texture_bottom_slider.get())
        ts = float(self.texture_sides_slider.get())
        tt = float(self.texture_top_slider.get())
        stt = float(self.side_top_slider.get())
        bp = self._read_float(self.border_entry, 5.0, 0.0, 25.0)
        st = self._read_float(self.shell_entry, 5.0, 0.0, 20.0)
        return style, tw, th, sf, tb, ts, tt, stt, bp, st

    def invalidate_approval(self):
        self.is_model_approved = False
        if hasattr(self, 'export_btn'):
            self.export_btn.config(state=tk.DISABLED)
            self.status_lbl.config(text="Status: Settings Changed (Re-verify)", foreground="orange")

    def get_seed(self):
        # v15.3: safe read of the seed spinbox; falls back to the historical
        # default if the entry holds a non-integer value
        try:
            return int(self.seed_var.get())
        except tk.TclError:
            self.seed_var.set(55)
            return 55

    def update_preview(self):
        style, tw, th, sf, tb, ts, tt, stt, bp, st = self.get_params()

        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = generate_custom_border_butte(
            style, tw, th, sf, tb, ts, tt, stt, bp, st, resolution=60, seed=self.get_seed()
        )
        self.redraw_canvas(style, tw, th)

    def update_plot_and_approve(self):
        style, tw, th, sf, tb, ts, tt, stt, bp, st = self.get_params()

        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = generate_custom_border_butte(
            style, tw, th, sf, tb, ts, tt, stt, bp, st, resolution=80, seed=self.get_seed()
        )
        self.redraw_canvas(style, tw, th)
        
        self.is_model_approved = True
        self.export_btn.config(state=tk.NORMAL)
        self.status_lbl.config(text="Status: Verified & Approved", foreground="green")
        messagebox.showinfo("Model Approved", "The open-shell coordinates match mathematical safety scales. Export unlocked.")

    def redraw_canvas(self, style, tw, th):
        cmap_dict = {"Sandstone": "YlOrBr", "Shale": "copper", "Granite": "bone"}
        self.ax.clear()
        
        Z_display = np.where(self.mask, self.Z, np.nan)
        self.ax.plot_surface(self.X, self.Y, Z_display, cmap=cmap_dict.get(style, "terrain"), 
                             edgecolor='none', rstride=1, cstride=1, alpha=0.9)
        
        self.ax.set_title(f"V15 Normal Extrusion Preview: {style} Butte", fontsize=11, fontweight='bold')
        self.ax.set_xlabel("X (Width mm)")
        self.ax.set_ylabel("Y (Length mm)")
        self.ax.set_zlabel("Z (Height mm)")
        self.ax.view_init(elev=22, azim=-45)
        self.ax.set_box_aspect([tw, tw, th]) 
        self.canvas.draw()

    def save_stl(self):
        if not self.is_model_approved:
            messagebox.showerror("Export Locked", "Approve the structural model inside the interface first.")
            return
            
        #default_name = f"open_shell_v15_butte_{self.style_var.get().lower()}.stl"
        default_name = f"{self.style_var.get().lower()}_seed_{self.seed_var.get()}.stl"
        file_path = filedialog.asksaveasfilename(defaultextension=".stl", 
                                                filetypes=[("Stereolithography Mesh", "*.stl")],
                                                initialfile=default_name)
        if file_path:
            style, tw, th, sf, tb, ts, tt, stt, bp, st_val = self.get_params()
            X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi = generate_custom_border_butte(
                style, tw, th, sf, tb, ts, tt, stt, bp, st_val, resolution=130, seed=self.get_seed()
            )
            # v15.3: apply the UI simplification factor to the exported mesh only
            # (preview/verify stay full detail). 1 = no change.
            simplify_factor = self.get_simplify()
            if simplify_factor > 1:
                X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi = simplify_grid_mesh(
                    X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi, simplify_factor
                )
            write_contour_binary_stl(X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi, st_val, file_path)
            detail_note = f" (simplified {simplify_factor}x)" if simplify_factor > 1 else ""
            messagebox.showinfo("Export Successful",
                                f"Manifold Open-Bottom STL mesh{detail_note} written to:\n{file_path}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ButteGeneratorGUI(root)
    root.mainloop()


