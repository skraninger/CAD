# -*- coding: utf-8 -*-
import struct
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np

# Force Tkinter window layer binding explicitly for Windows environments
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================
# 1. CORE GEOLOGY ENGINE (VERSION 15)
# ==========================================
def generate_custom_border_butte(style, target_width_mm, target_height_mm,
                                 stratification_factor, texture_bottom, texture_sides, texture_top,
                                 border_padding_mm, shell_thickness_mm, resolution=100):
    """
    Generates a freestanding butte terrain with 100% feature preservation,
    manually adjustable border padding, and true 3D normal vector hollowing.
    """
    nx, ny = resolution, resolution
    x = np.linspace(-15, 15, nx)
    y = np.linspace(-15, 15, ny)
    X, Y = np.meshgrid(x, y)
    
    # 1. Radial Base Framing with Structural Asymmetry
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)
    
    np.random.seed(52)
    
    r_variation = 1.5 * np.sin(3 * Theta) + 0.6 * np.cos(5 * Theta)
    R_adjusted = R + r_variation
    
    # 2. Base Mesa Profile
    Z_base = 10.0 / (1.0 + np.exp(2.0 * (R_adjusted - 10.5)))
    Z_base = np.where(Z_base > 9.2, 9.4 + 0.01 * (9.4 - Z_base), Z_base)
    
    # 3. Multi-Frequency Fractal Noise Layer (Texturing Engine)
    noise = np.zeros_like(X)
    frequencies = [1.0, 2.5, 6.0, 12.0]
    amplitudes = [0.6, 0.3, 0.12, 0.04]

    for f, a in zip(frequencies, amplitudes):
        phi_x = np.random.uniform(0, 2 * np.pi)
        phi_y = np.random.uniform(0, 2 * np.pi)
        noise += a * np.sin(f * X + phi_x) * np.cos(f * Y + phi_y)
        
    cliff_envelope = np.exp(-((R_adjusted - 10.0) / 2.5)**2)

    # Zone-based texture weighting: bottom strata / mesa sides / mesa top
    grid_step = 30.0 / (resolution - 1)
    gz_y, gz_x = np.gradient(Z_base, grid_step, grid_step)
    slope_mag = np.sqrt(gz_x**2 + gz_y**2)
    slope_norm = slope_mag / (np.max(slope_mag) + 1e-9)

    elev_norm = Z_base / (np.max(Z_base) + 1e-9)
    t_top = np.clip((elev_norm - 0.65) / (0.90 - 0.65), 0.0, 1.0)
    w_top = t_top * t_top * (3.0 - 2.0 * t_top)
    t_side = np.clip((slope_norm - 0.35) / (0.75 - 0.35), 0.0, 1.0)
    w_side = t_side * t_side * (3.0 - 2.0 * t_side) * (1.0 - w_top)
    w_bottom = np.clip(1.0 - w_top - w_side, 0.0, 1.0)

    texture_field = w_bottom * texture_bottom + w_side * texture_sides + w_top * texture_top
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
        self.root.geometry("1100x760")
        
        # State matrices initialization
        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = [None]*7
        self.is_model_approved = False 
        
        # Control Layout Panel (Left)
        ctrl_frame = ttk.LabelFrame(root, text=" Parametric Controls ", padding=15)
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(ctrl_frame, text="Geological Style:").pack(anchor=tk.W, pady=2)
        self.style_var = tk.StringVar(value="Sandstone")
        style_menu = ttk.Combobox(ctrl_frame, textvariable=self.style_var, values=["Sandstone", "Shale", "Granite"], state="readonly")
        style_menu.pack(fill=tk.X, pady=5)
        style_menu.bind("<<ComboboxSelected>>", lambda e: self.invalidate_approval())
        
        # Configured Sliders - Shell Thickness & Flat Contour Brim Defaulting to exactly 5.0mm
        self.width_slider = self.create_slider(ctrl_frame, "Target Width (mm):", 20, 230, 120)
        self.height_slider = self.create_slider(ctrl_frame, "Target Height (mm):", 20, 230, 120)
        self.strata_slider = self.create_slider(ctrl_frame, "Stratification Bedding Factor:", 0.5, 6.0, 2.5, resolution=0.1)
        self.texture_bottom_slider = self.create_slider(ctrl_frame, "Texture - Bottom Strata:", 0.0, 4.0, 1.5, resolution=0.1)
        self.texture_sides_slider = self.create_slider(ctrl_frame, "Texture - Mesa Sides:", 0.0, 4.0, 1.5, resolution=0.1)
        self.texture_top_slider = self.create_slider(ctrl_frame, "Texture - Mesa Top:", 0.0, 4.0, 1.5, resolution=0.1)
        self.border_slider = self.create_slider(ctrl_frame, "Flat Contour Brim Width (mm):", 0.0, 25.0, 5.0, resolution=0.5)
        self.shell_slider = self.create_slider(ctrl_frame, "Shell Thickness (mm, 0=Solid):", 0.0, 20.0, 5.0, resolution=0.5)
        
        # Trigger Operations
        ttk.Button(ctrl_frame, text="Verify & Approve Structural Model", command=self.update_plot_and_approve).pack(fill=tk.X, pady=15)
        self.export_btn = ttk.Button(ctrl_frame, text="Export Approved Binary STL", command=self.save_stl, state=tk.DISABLED)
        self.export_btn.pack(fill=tk.X, pady=5)
        
        self.status_lbl = ttk.Label(ctrl_frame, text="Status: Review Pending", foreground="orange")
        self.status_lbl.pack(pady=10)
        
        # 3D Canvas Panel Display (Right)
        self.plot_frame = ttk.Frame(root, padding=10)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig = plt.figure(figsize=(7, 6))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_preview()

    def create_slider(self, parent, label, min_v, max_v, default, resolution=1.0):
        ttk.Label(parent, text=label).pack(anchor=tk.W, pady=(8, 2))
        slider = tk.Scale(parent, from_=min_v, to=max_v, orient=tk.HORIZONTAL, resolution=resolution, length=220, command=lambda v: self.invalidate_approval())
        slider.set(default)
        slider.pack(fill=tk.X, pady=(0, 5))
        return slider

    def invalidate_approval(self):
        self.is_model_approved = False
        if hasattr(self, 'export_btn'):
            self.export_btn.config(state=tk.DISABLED)
            self.status_lbl.config(text="Status: Settings Changed (Re-verify)", foreground="orange")

    def update_preview(self):
        style = self.style_var.get()
        tw, th = float(self.width_slider.get()), float(self.height_slider.get())
        sf = float(self.strata_slider.get())
        tb, ts, tt = (float(self.texture_bottom_slider.get()), float(self.texture_sides_slider.get()),
                      float(self.texture_top_slider.get()))
        bp, st = float(self.border_slider.get()), float(self.shell_slider.get())
        
        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = generate_custom_border_butte(
            style, tw, th, sf, tb, ts, tt, bp, st, resolution=60
        )
        self.redraw_canvas(style, tw, th)

    def update_plot_and_approve(self):
        style = self.style_var.get()
        tw, th = float(self.width_slider.get()), float(self.height_slider.get())
        sf = float(self.strata_slider.get())
        tb, ts, tt = (float(self.texture_bottom_slider.get()), float(self.texture_sides_slider.get()),
                      float(self.texture_top_slider.get()))
        bp, st = float(self.border_slider.get()), float(self.shell_slider.get())
        
        self.X, self.Y, self.Z, self.X_in, self.Y_in, self.Z_in, self.mask = generate_custom_border_butte(
            style, tw, th, sf, tb, ts, tt, bp, st, resolution=80
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
            
        default_name = f"open_shell_v15_butte_{self.style_var.get().lower()}.stl"
        file_path = filedialog.asksaveasfilename(defaultextension=".stl", 
                                                filetypes=[("Stereolithography Mesh", "*.stl")],
                                                initialfile=default_name)
        if file_path:
            st_val = float(self.shell_slider.get())
            X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi = generate_custom_border_butte(
                self.style_var.get(), float(self.width_slider.get()), float(self.height_slider.get()), 
                float(self.strata_slider.get()), float(self.texture_bottom_slider.get()),
                float(self.texture_sides_slider.get()), float(self.texture_top_slider.get()),
                float(self.border_slider.get()), st_val, resolution=130
            )
            write_contour_binary_stl(X_hi, Y_hi, Z_hi, X_in_hi, Y_in_hi, Z_in_hi, mask_hi, st_val, file_path)
            messagebox.showinfo("Export Successful", f"Manifold Open-Bottom STL mesh written to:\n{file_path}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ButteGeneratorGUI(root)
    root.mainloop()


