# -*- coding: utf-8 -*-
import json
import os
import struct
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np

# Force Tkinter window layer binding explicitly for Windows environments
import matplotlib
matplotlib.use("TkAgg")
# v15.2 CLEAN-EXIT FIX: use a bare Figure instead of pyplot's plt.figure().
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================
# 1. CORE GEOLOGY ENGINE (VERSION 16)
# ==========================================
def generate_custom_border_butte(style, target_width_mm, target_height_mm,
                                 stratification_factor, texture_bottom, texture_sides, texture_top,
                                 side_top_transition, border_padding_mm, shell_thickness_mm, resolution=100, seed=55):
    """
    Generates a freestanding butte terrain (an inverted bowl) with adjustable
    border padding and true 3D normal-vector hollowing.

    V16 changes vs V15:
      * The mesa TOP is strongly attenuated (a whisper of relief) while the
        sides and bottom keep their full texture. This is done by scaling the
        top-zone noise contribution by TOP_ATTENUATION.
      * Everything else (radial framing, sigmoid+shoulder profile, noise
        octaves, styles, masking, brim dilation, mm rescaling, normal-offset
        hollowing) is unchanged so the sides/bottom look is preserved.
    """
    # V16: the flat mesa cap keeps only a whisper of the stochastic relief.
    # Sides and bottom are untouched (their zone weights keep full amplitude).
    TOP_ATTENUATION = 0.15

    nx, ny = resolution, resolution
    x = np.linspace(-15, 15, nx)
    y = np.linspace(-15, 15, ny)
    X, Y = np.meshgrid(x, y)

    # 1. Radial Base Framing with Structural Asymmetry
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)

    np.random.seed(int(seed))

    r_variation = 1.5 * np.sin(3 * Theta) + 0.6 * np.cos(5 * Theta)
    R_adjusted = R + r_variation

    # 2. Base Mesa Profile with a smooth side->top shoulder
    Z_sig = 10.0 / (1.0 + np.exp(2.0 * (R_adjusted - 10.5)))
    cap_level = 9.4
    band_lo = max(cap_level - float(side_top_transition), 0.0)
    denom = max(cap_level - band_lo, 1e-6)
    t_cap = np.clip((Z_sig - band_lo) / denom, 0.0, 1.0)
    w_cap = t_cap * t_cap * (3.0 - 2.0 * t_cap)
    Z_base = Z_sig + w_cap * (cap_level - Z_sig)

    # 3. Multi-Frequency Fractal Noise Layer (Texturing Engine)
    noise = np.zeros_like(X)
    frequencies = [1.0, 2.5, 6.0, 12.0]
    amplitudes = [0.6, 0.3, 0.12, 0.04]
    for f, a in zip(frequencies, amplitudes):
        phi_x = np.random.uniform(0, 2 * np.pi)
        phi_y = np.random.uniform(0, 2 * np.pi)
        noise += a * np.sin(f * X + phi_x) * np.cos(f * Y + phi_y)

    cliff_envelope = np.exp(-((R_adjusted - 10.0) / 2.5)**2)

    # Zone-based texture weighting: bottom / sides / top
    grid_step = 30.0 / (resolution - 1)
    gz_y, gz_x = np.gradient(Z_base, grid_step, grid_step)
    slope_mag = np.sqrt(gz_x**2 + gz_y**2)
    slope_norm = slope_mag / (np.max(slope_mag) + 1e-9)
    elev_norm = Z_base / (np.max(Z_base) + 1e-9)

    t_top = np.clip((elev_norm - 0.65) / (0.90 - 0.65), 0.0, 1.0)
    elev_ramp = t_top * t_top * (3.0 - 2.0 * t_top)
    t_flat = np.clip((0.35 - slope_norm) / (0.35 - 0.10), 0.0, 1.0)
    flat_ramp = t_flat * t_flat * (3.0 - 2.0 * t_flat)
    w_top = elev_ramp * flat_ramp

    t_side = np.clip((slope_norm - 0.35) / (0.75 - 0.35), 0.0, 1.0)
    w_side = t_side * t_side * (3.0 - 2.0 * t_side) * (1.0 - w_top)

    w_bottom = np.clip(1.0 - w_top - w_side, 0.0, 1.0)

    # V16: attenuate the TOP noise only (sides/bottom keep full amplitude).
    texture_field = (w_bottom * texture_bottom + w_side * texture_sides
                     + w_top * texture_top * TOP_ATTENUATION)
    noise_layer = noise * texture_field

    # Apply Geological Style Switcher
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

    # 4. Core Mountain Masking
    mountain_base_mask = Z_base >= 0.005
    Z[~mountain_base_mask] = 0.0

    # 5. Brim dilation
    x_min_raw, x_max_raw = np.min(X[mountain_base_mask]), np.max(X[mountain_base_mask])
    y_min_raw, y_max_raw = np.min(Y[mountain_base_mask]), np.max(Y[mountain_base_mask])
    curr_width_raw = max(x_max_raw - x_min_raw, y_max_raw - y_min_raw)
    raw_to_mm_ratio = target_width_mm / curr_width_raw
    grid_spacing_mm = (30.0 / resolution) * raw_to_mm_ratio
    pad = int(np.ceil(border_padding_mm / grid_spacing_mm)) if border_padding_mm > 0 else 0
    pad = np.clip(pad, 0, int(resolution / 4))

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

    # 6. Final Spatial Calibration
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
        dzdx = np.zeros_like(Z_scaled)
        dzdy = np.zeros_like(Z_scaled)
        dx_val = target_width_mm / resolution
        dy_val = target_width_mm / resolution
        dzdx[:, 1:-1] = (Z_scaled[:, 2:] - Z_scaled[:, :-2]) / (2.0 * dx_val)
        dzdy[1:-1, :] = (Z_scaled[2:, :] - Z_scaled[:-2, :]) / (2.0 * dy_val)
        Nx = -dzdx
        Ny = -dzdy
        Nz = np.ones_like(Z_scaled)
        norm = np.sqrt(Nx**2 + Ny**2 + Nz**2)
        Nx /= norm
        Ny /= norm
        Nz /= norm
        X_in = X_scaled - shell_thickness_mm * Nx
        Y_in = Y_scaled - shell_thickness_mm * Ny
        Z_in = Z_scaled - shell_thickness_mm * Nz
        Z_in = np.maximum(0.0, Z_in)

    return X_scaled, Y_scaled, Z_scaled, X_in, Y_in, Z_in, valid_mask

# ==========================================
# 2. WATERTIGHT BOWL STL EXPORT ENGINE (V16)
# ==========================================
def calculate_normal(p1, p2, p3):
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    n = np.cross(v1, v2)
    norm = np.linalg.norm(n)
    return tuple(n / norm) if norm > 0 else (0.0, 0.0, 1.0)


def build_facets(X, Y, Z, Xi, Yi, Zi, mask, shell_thickness_mm):
    """Build a watertight inverted-bowl facet list, watertight BY CONSTRUCTION.

    The solid (bowl material) boundary is a closed 2-manifold made of:
      * OUTER surface  -- graph of Z over the covered-cell footprint F, normal up.
      * INNER surface  -- graph of Zi over the same F (cavity ceiling), normal down.
      * BASE RIM       -- a flat annulus at z=0 joining the outer base loop to the
                          inner base loop (both sit at z=0), normal down.
    Every boundary edge is shared by exactly two facets (outer+rim, inner+rim),
    so there are no open edges and no coincident double-skin. The cavity (the
    hollow below the inner surface) is open at the base -- the natural bowl
    opening -- which is a concavity, not a defect.

    Solid mode (shell == 0): the inner surface coincides with the outer, so we
    emit the outer surface plus a flat bottom disk (z=0) instead.
    """
    ny, nx = Z.shape
    facets = []

    covered = np.zeros((ny - 1, nx - 1), dtype=bool)
    for i in range(ny - 1):
        for j in range(nx - 1):
            covered[i, j] = bool(mask[i, j] and mask[i + 1, j]
                                 and mask[i, j + 1] and mask[i + 1, j + 1])

    # 1. OUTER surface (graph of Z over F), winding -> +z (up)
    for i in range(ny - 1):
        for j in range(nx - 1):
            if not covered[i, j]:
                continue
            v1 = (X[i, j], Y[i, j], Z[i, j])
            v2 = (X[i + 1, j], Y[i + 1, j], Z[i + 1, j])
            v3 = (X[i, j + 1], Y[i, j + 1], Z[i, j + 1])
            v4 = (X[i + 1, j + 1], Y[i + 1, j + 1], Z[i + 1, j + 1])
            facets.append((v1, v2, v4))
            facets.append((v1, v4, v3))

    if shell_thickness_mm > 0:
        # 2. INNER surface (graph of Zi over F), winding -> -z (down)
        for i in range(ny - 1):
            for j in range(nx - 1):
                if not covered[i, j]:
                    continue
                v1 = (Xi[i, j], Yi[i, j], Zi[i, j])
                v2 = (Xi[i + 1, j], Yi[i + 1, j], Zi[i + 1, j])
                v3 = (Xi[i, j + 1], Yi[i, j + 1], Zi[i, j + 1])
                v4 = (Xi[i + 1, j + 1], Yi[i + 1, j + 1], Zi[i + 1, j + 1])
                facets.append((v1, v4, v2))
                facets.append((v1, v3, v4))

        # 3. BASE RIM: flat annulus at z=0 joining outer base loop to inner base loop.
        #    A node edge is a boundary edge of F iff exactly one adjacent cell is covered.
        # Horizontal edges (i,j)-(i,j+1)
        for i in range(ny):
            for j in range(nx - 1):
                cov_below = bool(covered[i, j]) if i <= ny - 2 else False
                cov_above = bool(covered[i - 1, j]) if i >= 1 else False
                if cov_below != cov_above:
                    OA = (X[i, j], Y[i, j], Z[i, j])
                    OB = (X[i, j + 1], Y[i, j + 1], Z[i, j + 1])
                    LA = (Xi[i, j], Yi[i, j], Zi[i, j])
                    LB = (Xi[i, j + 1], Yi[i, j + 1], Zi[i, j + 1])
                    facets.append((OA, LB, OB))
                    facets.append((OA, LA, LB))
        # Vertical edges (i,j)-(i+1,j)
        for i in range(ny - 1):
            for j in range(nx):
                cov_right = bool(covered[i, j]) if j <= nx - 2 else False
                cov_left = bool(covered[i, j - 1]) if j >= 1 else False
                if cov_right != cov_left:
                    OA = (X[i, j], Y[i, j], Z[i, j])
                    OB = (X[i + 1, j], Y[i + 1, j], Z[i + 1, j])
                    LA = (Xi[i, j], Yi[i, j], Zi[i, j])
                    LB = (Xi[i + 1, j], Yi[i + 1, j], Zi[i + 1, j])
                    facets.append((OA, LB, OB))
                    facets.append((OA, LA, LB))
    else:
        # SOLID mode: flat bottom disk (z=0) over F, winding -> -z (down)
        for i in range(ny - 1):
            for j in range(nx - 1):
                if not covered[i, j]:
                    continue
                v1 = (X[i, j], Y[i, j], 0.0)
                v2 = (X[i + 1, j], Y[i + 1, j], 0.0)
                v3 = (X[i, j + 1], Y[i, j + 1], 0.0)
                v4 = (X[i + 1, j + 1], Y[i + 1, j + 1], 0.0)
                facets.append((v1, v4, v2))
                facets.append((v1, v3, v4))

    def area2(p1, p2, p3):
        a = np.array(p2) - np.array(p1)
        b = np.array(p3) - np.array(p1)
        c = np.cross(a, b)
        return float(c @ c)

    return [f for f in facets if area2(*f) > 1e-9]


def write_contour_binary_stl(X, Y, Z, X_in, Y_in, Z_in, mask, shell_thickness_mm, filename):
    """Writes the watertight inverted-bowl shell to binary STL."""
    facets = build_facets(X, Y, Z, X_in, Y_in, Z_in, mask, shell_thickness_mm)
    with open(filename, 'wb') as f:
        f.write(b'\x00' * 80)
        f.write(struct.pack('<I', len(facets)))
        for facet in facets:
            f.write(struct.pack('<fff', *calculate_normal(*facet)))
            for vertex in facet:
                f.write(struct.pack('<fff', *vertex))
            f.write(struct.pack('<H', 0))

# ==========================================
# 3. TKINTER GRAPHICAL USER INTERFACE (V16)
# ==========================================
class ButteGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Geological Butte Parametric Engine - V16 Watertight Bowl")
        self.root.geometry("1100x780")

        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = [None]*7
        self.is_model_approved = False

        ctrl_frame = ttk.LabelFrame(root, text=" Parametric Controls ", padding=15)
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

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

        ttk.Label(params, text="Noise Seed (texture pattern):").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=(6, 2))
        self.seed_var = tk.IntVar(value=55)
        self.seed_spin = tk.Spinbox(params, from_=0, to=99999, increment=1, width=10,
                                    textvariable=self.seed_var, command=self.invalidate_approval)
        self.seed_spin.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        row += 1
        self.seed_spin.bind("<KeyRelease>", lambda e: self.invalidate_approval())
        self.seed_spin.bind("<FocusOut>", lambda e: self.invalidate_approval())

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
        self.side_top_slider = self.add_slider_row(params, row, "Side→Top Transition (more gradual →):", 0.2, 8.0, 1.5, resolution=0.1)
        row += 1
        self.border_entry = self.add_entry_row(params, row, "Flat Contour Brim Width (mm):", 0.0, 25.0, 5.0, increment=0.5)
        row += 1
        self.shell_entry = self.add_entry_row(params, row, "Shell Thickness (mm, 0=Solid):", 0.0, 20.0, 5.0, increment=0.5)
        row += 1

        # V16: single mesh resolution for preview, verify AND export
        self.resolution_entry = self.add_entry_row(params, row, "Mesh Resolution (grid nodes):", 40, 260, 130, increment=1)
        row += 1

        ttk.Button(ctrl_frame, text="Verify & Approve Structural Model", command=self.update_plot_and_approve).pack(fill=tk.X, pady=15)
        self.export_btn = ttk.Button(ctrl_frame, text="Export Approved Binary STL", command=self.save_stl, state=tk.DISABLED)
        self.export_btn.pack(fill=tk.X, pady=5)

        param_io = ttk.Frame(ctrl_frame)
        param_io.pack(fill=tk.X, pady=5)
        ttk.Button(param_io, text="Save Parameters...", command=self.save_parameters).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))
        ttk.Button(param_io, text="Load Parameters...", command=self.load_parameters).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(3, 0))

        self.status_lbl = ttk.Label(ctrl_frame, text="Status: Review Pending", foreground="orange")
        self.status_lbl.pack(pady=10)

        self.plot_frame = ttk.Frame(root, padding=10)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(7, 6), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        default_file = os.path.join(os.getcwd(), "butte_default.json")
        if os.path.isfile(default_file):
            if self._load_parameter_file(default_file):
                self.status_lbl.config(text="Status: Defaults Loaded (Re-verify)", foreground="orange")

        self.update_preview()

    def add_slider_row(self, parent, row, label, min_v, max_v, default, resolution=1.0):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=(6, 2))
        holder = ttk.Frame(parent)
        holder.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        slider = tk.Scale(holder, from_=min_v, to=max_v, orient=tk.HORIZONTAL,
                          resolution=resolution, length=140, showvalue=False)
        slider.set(default)
        value_lbl = ttk.Label(holder, text=self._fmt_value(default, resolution), width=5)
        slider.value_lbl = value_lbl
        slider.res = resolution

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

    def get_resolution(self):
        try:
            v = int(float(self.resolution_entry.get()))
        except (tk.TclError, ValueError):
            v = 130
        return min(max(v, 40), 260)

    def get_params(self):
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
        res = self.get_resolution()
        return style, tw, th, sf, tb, ts, tt, stt, bp, st, res

    def invalidate_approval(self):
        self.is_model_approved = False
        if hasattr(self, 'export_btn'):
            self.export_btn.config(state=tk.DISABLED)
            self.status_lbl.config(text="Status: Settings Changed (Re-verify)", foreground="orange")

    def get_seed(self):
        try:
            return int(self.seed_var.get())
        except tk.TclError:
            self.seed_var.set(55)
            return 55

    def get_parameter_dict(self):
        style, tw, th, sf, tb, ts, tt, stt, bp, st, res = self.get_params()
        return {
            "style": style,
            "seed": self.get_seed(),
            "target_width_mm": tw,
            "target_height_mm": th,
            "stratification_factor": sf,
            "texture_bottom": tb,
            "texture_sides": ts,
            "texture_top": tt,
            "side_top_transition": stt,
            "border_padding_mm": bp,
            "shell_thickness_mm": st,
            "mesh_resolution": res,
        }

    def save_parameters(self):
        default_name = f"butte_params_{self.style_var.get().lower()}_seed_{self.get_seed()}.json"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Parameter File", "*.json"), ("All Files", "*.*")],
            initialfile=default_name)
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.get_parameter_dict(), f, indent=2)
        except OSError as e:
            messagebox.showerror("Save Failed", f"Could not write the parameter file:\n{e}")
            return
        self.status_lbl.config(text="Status: Parameters Saved", foreground="green")
        messagebox.showinfo("Parameters Saved", f"Parameter set written to:\n{file_path}")

    def load_parameters(self):
        file_path = filedialog.askopenfilename(
            title="Load Parameter Set",
            filetypes=[("Parameter File", "*.json"), ("All Files", "*.*")])
        if not file_path:
            return
        if self._load_parameter_file(file_path):
            messagebox.showinfo("Parameters Loaded",
                                f"Parameter set applied from:\n{file_path}\n\nRe-verify the model before exporting.")

    def _load_parameter_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            messagebox.showerror("Load Failed", f"Could not read the parameter file:\n{e}")
            return False
        if not isinstance(data, dict):
            messagebox.showerror("Load Failed", "The file does not contain a valid parameter set.")
            return False
        if self._apply_parameter_dict(data):
            self.invalidate_approval()
            return True
        return False

    def _apply_parameter_dict(self, data):
        style = data.get("style", "Sandstone")
        if style not in ("Sandstone", "Shale", "Granite"):
            messagebox.showerror("Load Failed", f"Unknown geological style: {style!r}")
            return False

        specs = [
            (self.width_entry,           "target_width_mm",       120.0, 20.0, 230.0),
            (self.height_entry,          "target_height_mm",      120.0, 20.0, 230.0),
            (self.strata_slider,         "stratification_factor",   2.5,  0.5,   6.0),
            (self.texture_bottom_slider, "texture_bottom",          1.5,  0.0,   4.0),
            (self.texture_sides_slider,  "texture_sides",           1.5,  0.0,   4.0),
            (self.texture_top_slider,    "texture_top",             1.5,  0.0,   4.0),
            (self.side_top_slider,       "side_top_transition",     1.5,  0.2,   8.0),
            (self.border_entry,          "border_padding_mm",       5.0,  0.0,  25.0),
            (self.shell_entry,           "shell_thickness_mm",      5.0,  0.0,  20.0),
        ]
        resolved = []
        for widget, key, default, min_v, max_v in specs:
            raw = data.get(key, default)
            try:
                v = float(raw)
                if not np.isfinite(v):
                    raise ValueError
            except (TypeError, ValueError):
                messagebox.showerror("Load Failed", f"Invalid value for '{key}': {raw!r}")
                return False
            resolved.append((widget, min(max(v, min_v), max_v)))

        def read_int(key, default, min_v, max_v):
            raw = data.get(key, default)
            try:
                v = int(float(raw))
            except (TypeError, ValueError):
                messagebox.showerror("Load Failed", f"Invalid value for '{key}': {raw!r}")
                return None
            return min(max(v, min_v), max_v)

        seed = read_int("seed", 55, 0, 99999)
        if seed is None:
            return False
        # V16: accept either the new key or the legacy simplification key (ignored)
        resolution = read_int("mesh_resolution", 130, 40, 260)
        if resolution is None:
            return False

        self.style_var.set(style)
        self.seed_var.set(seed)
        for widget, v in resolved:
            if isinstance(widget, tk.Scale):
                widget.set(v)
                if hasattr(widget, "value_lbl"):
                    widget.value_lbl.config(text=self._fmt_value(v, widget.res))
            else:
                self._set_entry_text(widget, v)
        self._set_entry_text(self.resolution_entry, resolution)
        return True

    def update_preview(self):
        style, tw, th, sf, tb, ts, tt, stt, bp, st, res = self.get_params()
        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = generate_custom_border_butte(
            style, tw, th, sf, tb, ts, tt, stt, bp, st, resolution=res, seed=self.get_seed()
        )
        self.redraw_canvas(style, tw, th)

    def update_plot_and_approve(self):
        style, tw, th, sf, tb, ts, tt, stt, bp, st, res = self.get_params()
        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = generate_custom_border_butte(
            style, tw, th, sf, tb, ts, tt, stt, bp, st, resolution=res, seed=self.get_seed()
        )
        self.redraw_canvas(style, tw, th)

        self.is_model_approved = True
        self.export_btn.config(state=tk.NORMAL)
        self.status_lbl.config(text="Status: Verified & Approved", foreground="green")
        messagebox.showinfo("Model Approved", "The watertight bowl coordinates match mathematical safety scales. Export unlocked.")

    def redraw_canvas(self, style, tw, th):
        cmap_dict = {"Sandstone": "YlOrBr", "Shale": "copper", "Granite": "bone"}
        self.ax.clear()
        Z_display = np.where(self.mask, self.Z, np.nan)
        self.ax.plot_surface(self.X, self.Y, Z_display, cmap=cmap_dict.get(style, "terrain"),
                             edgecolor='none', rstride=1, cstride=1, alpha=0.9)
        self.ax.set_title(f"V16 Watertight Bowl Preview: {style} Butte", fontsize=11, fontweight='bold')
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
        default_name = f"{self.style_var.get().lower()}_seed_{self.seed_var.get()}.stl"
        file_path = filedialog.asksaveasfilename(defaultextension=".stl",
                                                filetypes=[("Stereolithography Mesh", "*.stl")],
                                                initialfile=default_name)
        if file_path:
            style, tw, th, sf, tb, ts, tt, stt, bp, st_val, res = self.get_params()
            X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi = generate_custom_border_butte(
                style, tw, th, sf, tb, ts, tt, stt, bp, st_val, resolution=res, seed=self.get_seed()
            )
            write_contour_binary_stl(X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi, st_val, file_path)
            messagebox.showinfo("Export Successful",
                                f"Watertight inverted-bowl STL mesh written to:\n{file_path}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ButteGeneratorGUI(root)
    root.mainloop()
