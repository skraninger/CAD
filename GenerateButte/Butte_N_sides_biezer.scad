// 100% Manifold Parametric Bezier Butte (Inverted Bowl) - PART 1 OF 2
// Fixed radius multiplier bug to unlock the true wide flat table-top plateau.

/* [Footprint Settings & Keyframes] */
// Exactly 8 integers. Smoothly morphs from top shape (Index 0) to base shape (Index 7)
side_keyframes = [4, 3, 4, 3, 5, 6, 5, 6]; 

// Controls corner smoothness. 0.0 = perfectly sharp, 1.0 = fully round (circle)
corner_rounding_factor = 0.4; 

/* [Twist Matrix Setting] */
// Total degrees of rotation from top to bottom. (Positive = clockwise, Negative = CCW)
twist_degrees = 120; 

/* [Dimensions] */
max_height = 190;
base_radius = 50;    

// Fraction of the base radius used for the top plateau (0.55 = wide table-top plateau)
top_plateau_ratio = 0.55; 

/* [Bezier Profile Controls] */
// Control points define [Radius Offset%, Height%] relative to the space between top and base.
bezier_P1 = [0.00, 0.70]; // Upper control handle (0.00 forces perfectly vertical walls)
bezier_P2 = [0.00, 0.30]; // Lower control handle (0.00 forces perfectly vertical walls)

/* [Hollow Core Settings] */
wall_thickness = 4.0; // Uniform shell thickness for the inverted bowl cavity

/* [Asymmetry Engine] */
center_shift_x = 5.0;
center_shift_y = -3.0;
skew_factor_x = 1.20;
skew_factor_y = 0.95;

/* [Resolution] */
layers = 23;        // Vertical slicing steps for the side walls
fragments = 120;    // Points per loop ring

// Number of concentric detail rings added across the top flat cap to boost plateau texture density
top_grid_rings = 10; 

/* [Sedimentary Strata Texture] */
strata_frequency = 1.8; 
strata_intensity = 6; 

/* [Fractal Noise Settings & Seed] */
noise_seed = 42; 
side_xy_amplitude = 4; 
top_z_amplitude = 2; 
octaves = 3; 

// ============================================================================
// CORE MATHEMATICAL ENGINE
// ============================================================================

function raw_noise(x, y, z) = 
    let(s_mod = noise_seed * 13.13)
    frac(sin((x + s_mod) * 12.9898 + (y - s_mod) * 78.233 + (z + s_mod) * 45.164) * 43758.5453);
    
function frac(x) = x - floor(x);

function fractal_noise(x, y, z, current_octave = 0, current_amp = 1.0, current_freq = 0.15) =
    current_octave >= octaves ? 0 :
    (raw_noise(x * current_freq, y * current_freq, z * current_freq) - 0.5) * current_amp + 
    fractal_noise(x, y, z, current_octave + 1, current_amp * 0.5, current_freq * 2.15);

function casteljau(t) =
    let(
        r_top = base_radius * top_plateau_ratio,
        p0 = [r_top, max_height],
        p1 = [r_top + (base_radius - r_top) * bezier_P1[0], max_height * bezier_P1[1]],
        p2 = [r_top + (base_radius - r_top) * bezier_P2[0], max_height * bezier_P2[1]],
        p3 = [base_radius, 0],
        
        q0 = (1 - t) * p0 + t * p1,
        q1 = (1 - t) * p1 + t * p2,
        q2 = (1 - t) * p2 + t * p3,
        
        r0 = (1 - t) * q0 + t * q1,
        r1 = (1 - t) * q1 + t * q2
    )
    (1 - t) * r0 + t * r1;

function get_poly_r(angle, sides_count, current_radius) =
    let(
        segment_angle = 360 / sides_count,
        local_angle = (angle + 90) % segment_angle,
        half_seg = segment_angle / 2,
        poly_factor = cos(half_seg) / cos(local_angle - half_seg)
    )
    current_radius * poly_factor;

function ring_point(angle, t, keyframes, current_radius) =
    let(
        c = cos(angle), s = sin(angle),
        raw_index = t * 7,
        idx1 = min(7, max(0, floor(raw_index))),
        idx2 = min(7, max(0, ceil(raw_index))),
        blend_factor = raw_index - idx1,
        
        sides1 = max(3, keyframes[idx1]),
        sides2 = max(3, keyframes[idx2]),
        
        sharp_r1 = get_poly_r(angle, sides1, current_radius),
        sharp_r2 = get_poly_r(angle, sides2, current_radius),
        
        sharp_r = (1.0 - blend_factor) * sharp_r1 + (blend_factor * sharp_r2),
        r_blend = (1.0 - corner_rounding_factor) * sharp_r + (corner_rounding_factor * current_radius)
        
        // REMOVED THE FAULTY "t * r_blend" MULTIPLIER PINCH TRUNCATION BUGS
    )
    [r_blend * c, r_blend * s];
// 100% Manifold Parametric Bezier Butte (Inverted Bowl) - PART 2 OF 2
// Append this block directly after Part 1 to run the generator script.

module continuous_high_detail_butte() {
    pts_per_layer = fragments * 2;
    z_top_surface = max_height;
    
    // --- 1. GENERATE DYNAMIC POINT ARRAY ---
    all_points = concat(
        // Index 0 & 1: Absolute central apex center points for the roof cap geometry
        [[center_shift_x, center_shift_y, z_top_surface + fractal_noise(center_shift_x, center_shift_y, z_top_surface) * top_z_amplitude]],
        [[center_shift_x, center_shift_y, z_top_surface - wall_thickness]],
        
        // STAGE A: HIGH-DENSITY TOP PLATEAU SUBDIVISION RINGS (Slices inward from 1.0 down to 0.0)
        [ for (k_ring = [0 : top_grid_rings - 1])
            let(
                t_cap = (top_grid_rings - k_ring) / top_grid_rings,
                z_base = z_top_surface,
                z_in_base = max(0, z_base - wall_thickness),
                bezier_coord = casteljau(0),
                p_rad = bezier_coord[0], 
                current_r = p_rad * t_cap, // Controlled compression explicitly locked to plateau radius bounds
                cx = center_shift_x,
                cy = center_shift_y
            )
            for (inner_outer = [0 : 1]) 
                for (j = [0 : fragments - 1])
                    let(
                        a = j * (360 / fragments),
                        raw_pt = ring_point(a, 0, side_keyframes, current_r),
                        
                        pt_out_x = (raw_pt[0] * skew_factor_x) + cx,
                        pt_out_y = (raw_pt[1] * skew_factor_y) + cy,
                        
                        vx = pt_out_x - cx, vy = pt_out_y - cy,
                        len = max(0.1, sqrt(vx*vx + vy*vy)),
                        dx = vx / len, dy = vy / len,
                        noise_top = fractal_noise(pt_out_x, pt_out_y, z_base) * top_z_amplitude,
                        pt_in_x = pt_out_x - (dx * wall_thickness),
                        pt_in_y = pt_out_y - (dy * wall_thickness)
                    )
                    inner_outer == 0 ? 
                        [pt_in_x, pt_in_y, z_in_base] : 
                        [pt_out_x, pt_out_y, max(0, z_base + noise_top)]
        ],
        
        // STAGE B: STANDARD VERTICAL SIDE WALL LAYERS
        [ for (i = [1 : layers]) 
            let(
                t = i / layers,
                bezier_coord = casteljau(t),
                current_r = bezier_coord[0], 
                z_base    = bezier_coord[1], 
                z_in_base = max(0, z_base - wall_thickness),
                floor_env = 1.0 - pow(t, 4),
                cx = center_shift_x * (1 - t),
                cy = center_shift_y * (1 - t),
                rot_angle = t * twist_degrees,
                rc = cos(rot_angle), rs = sin(rot_angle)
            )
            for (inner_outer = [0 : 1]) 
                for (j = [0 : fragments - 1])
                    let(
                        a = j * (360 / fragments),
                        raw_pt = ring_point(a, t, side_keyframes, current_r),
                        
                        rotated_raw_x = raw_pt[0] * rc - raw_pt[1] * rs,
                        rotated_raw_y = raw_pt[0] * rs + raw_pt[1] * rc,
                        
                        pt_out_x = (rotated_raw_x * skew_factor_x) + cx,
                        pt_out_y = (rotated_raw_y * skew_factor_y) + cy,
                        vx = pt_out_x - cx, vy = pt_out_y - cy,
                        len = max(0.1, sqrt(vx*vx + vy*vy)),
                        dx = vx / len, dy = vy / len,
                        noise_side = fractal_noise(pt_out_x, pt_out_y, z_base) * side_xy_amplitude * floor_env,
                        strata_offset = sin(z_base * strata_frequency * 36.0) * strata_intensity * floor_env,
                        final_out_x = pt_out_x + (dx * (noise_side + strata_offset)),
                        final_out_y = pt_out_y + (dy * (noise_side + strata_offset)),
                        pt_in_x = pt_out_x - (dx * wall_thickness),
                        pt_in_y = pt_out_y - (dy * wall_thickness)
                    )
                    inner_outer == 0 ? 
                        [pt_in_x, pt_in_y, z_in_base] : 
                        [final_out_x, final_out_y, z_base]
        ]
    );

    // --- 2. GENERATE WATER-TIGHT MESH INDICES ---
    total_rings = top_grid_rings + layers;
    all_faces = concat(
        // A. CEILING APEX CAP SEALS
        [ for (j = [0 : fragments - 1])
            let(
                j_next = (j + 1) % fragments,
                last_ring_offset = (top_grid_rings - 1) * pts_per_layer,
                in_p1  = 2 + last_ring_offset + j, 
                in_p2  = 2 + last_ring_offset + j_next,
                out_p1 = 2 + last_ring_offset + fragments + j, 
                out_p2 = 2 + last_ring_offset + fragments + j_next
            )
            each [
                [0, out_p1, out_p2], 
                [1, in_p2, in_p1]    
            ]
        ],
        
        // B. RADIAL WALL SHELLS
        [ for (i = [0 : total_rings - 2])
            for (j = [0 : fragments - 1])
                let(
                    j_next = (j + 1) % fragments,
                    layer_now  = 2 + i * pts_per_layer,
                    layer_next = 2 + (i + 1) * pts_per_layer,
                    in_now_l  = layer_now + j, in_now_r  = layer_now + j_next,
                    in_next_l = layer_next + j, in_next_r = layer_next + j_next,
                    out_now_l  = layer_now + fragments + j, out_now_r  = layer_now + fragments + j_next,
                    out_next_l = layer_next + fragments + j, out_next_r = layer_next + fragments + j_next
                )
                each [
                    [out_now_l, out_now_r, out_next_r], [out_now_l, out_next_r, out_next_l], 
                    [in_now_r, in_now_l, in_next_l],   [in_now_r, in_next_l, in_next_r]     
                ]
        ],
        
        // C. BASE FLOOR RIM SEALS
        [ for (j = [0 : fragments - 1])
            let(
                j_next = (j + 1) % fragments,
                base_layer = 2 + (total_rings - 1) * pts_per_layer,
                in_l  = base_layer + j, in_r  = base_layer + j_next,
                out_l = base_layer + fragments + j, out_r = base_layer + fragments + j_next
            )
            each [
                [in_l, in_r, out_r], [in_l, out_r, out_l]
            ]
        ]
    );

    polyhedron(points = all_points, faces = all_faces);
}

// Render the stable solid
continuous_high_detail_butte();
