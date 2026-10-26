// 100% Manifold Parametric Sigmoid Butte (Inverted Bowl)
// Fixed scoped lookup variable array passing to eliminate all undefined operations.

/* [Footprint Settings & Keyframes] */
// Exactly 8 integers. Index 0 is the absolute TOP, Index 7 is the BASE floor.
side_keyframes = [3, 3, 3, 3, 6, 6, 6, 6]; 

// Controls corner smoothness. 0.0 = perfectly sharp, 1.0 = fully round (circle)
corner_rounding_factor = 0.4; 

/* [Twist Matrix Setting] */
// Total degrees of rotation from top to bottom. (Positive = clockwise, Negative = CCW)
twist_degrees = 120; 

/* [Dimensions] */
max_height = 190;
base_radius = 40;    

/* [Hollow Core Settings] */
wall_thickness = 4.0; // Uniform shell thickness for the inverted bowl cavity

/* [Sigmoid Tuning Parameter] */
k = 4.5; // Slope steepness (Higher = sharper cliff walls, flatter top)

/* [Base Control Setting] */
// Controls how much flat rim spreads at the bottom. 
// 0.2 = Cuts off sharply (minimal flat space). 1.0 = Full smooth flattening rim.
base_extension_factor = 0.55; 

/* [Asymmetry Engine] */
center_shift_x = 5.0;
center_shift_y = -3.0;
skew_factor_x = 1.20;
skew_factor_y = 0.95;

/* [Resolution] */
layers = 56;        // Total concentric slicing layers
fragments = 120;    // High circular detail helps shapes morph without tearing

/* [Sedimentary Strata Texture] */
// Low-frequency horizontal banding frequency (higher = more layers)
strata_frequency = 0.8; 

// Horizontal outward/inward push intensity of the sedimentary layers
strata_intensity = 20; 

/* [Fractal Noise Settings] */
side_xy_amplitude = 10; 
top_z_amplitude = 5.0; 
octaves = 3; 

// Mathematical Utilities
function raw_noise(x, y, z) = frac(sin(x * 12.9898 + y * 78.233 + z * 45.164) * 43758.5453);
function frac(x) = x - floor(x);

function fractal_noise(x, y, z, current_octave = 0, current_amp = 1.0, current_freq = 0.15) =
    current_octave >= octaves ? 0 :
    (raw_noise(x * current_freq, y * current_freq, z * current_freq) - 0.5) * current_amp + 
    fractal_noise(x, y, z, current_octave + 1, current_amp * 0.5, current_freq * 2.15);

function tunable_sigmoid_height(t) = 
    let(domain_end = -6 + (12 * base_extension_factor))
    let(r_norm = -6 + (domain_end - (-6)) * t) 
    let(numerator = k * r_norm)
    let(denominator = sqrt(1 + pow(k * r_norm, 2)))
    let(sigmoid = (numerator / denominator) * 0.5 + 0.5)
    let(sig_at_zero = ( (k * (-6)) / sqrt(1 + pow(k * (-6), 2)) ) * 0.5 + 0.5)
    let(sig_at_end = (numerator / denominator) * 0.5 + 0.5)
    max_height * (1 - (sig_at_end - sig_at_zero) / (1 - sig_at_zero));

// Single polygon mapping engine
function get_poly_r(angle, sides_count) =
    let(
        segment_angle = 360 / sides_count,
        local_angle = (angle + 90) % segment_angle,
        half_seg = segment_angle / 2,
        poly_factor = cos(half_seg) / cos(local_angle - half_seg)
    )
    base_radius * poly_factor;

// FIXED: Keyframes array is now explicitly passed as a function argument parameter
function ring_point(angle, t, keyframes) =
    let(
        c = cos(angle), s = sin(angle),
        
        raw_index = t * 7,
        idx1 = min(7, max(0, floor(raw_index))),
        idx2 = min(7, max(0, ceil(raw_index))),
        blend_factor = raw_index - idx1,
        
        sides1 = max(3, keyframes[idx1]),
        sides2 = max(3, keyframes[idx2]),
        
        sharp_r1 = get_poly_r(angle, sides1),
        sharp_r2 = get_poly_r(angle, sides2),
        
        sharp_r = (1.0 - blend_factor) * sharp_r1 + (blend_factor * sharp_r2),
        r_blend = (1.0 - corner_rounding_factor) * sharp_r + (corner_rounding_factor * base_radius),
        
        t_clamped = max(1.0 / layers, t),
        actual_r = t_clamped * r_blend
    )
    [actual_r * c, actual_r * s];

module twisted_strata_morphing_bowl() {
    pts_per_layer = fragments * 2;
    
    // --- 1. GENERATE TWISTED POINT GRID ---
    all_points = [ for (i = [0 : layers]) 
        let(
            t = i / layers,
            t_clamped = max(1.0 / layers, t),
            
            z_base = tunable_sigmoid_height(t),
            z_in_base = max(0, z_base - wall_thickness),
            
            is_top = pow(1 - t, 4), 
            is_side = 1.0 - is_top,
            floor_env = 1.0 - pow(t, 4),
            
            cx = center_shift_x * (1 - t_clamped),
            cy = center_shift_y * (1 - t_clamped),
            
            rot_angle = t * twist_degrees,
            rc = cos(rot_angle),
            rs = sin(rot_angle)
        )
        for (inner_outer = [0 : 1]) 
            for (j = [0 : fragments - 1])
                let(
                    a = j * (360 / fragments),
                    // FIXED: Explicitly passed global side_keyframes array into the lookup logic
                    raw_pt = ring_point(a, t, side_keyframes),
                    
                    rotated_raw_x = raw_pt[0] * rc - raw_pt[1] * rs,
                    rotated_raw_y = raw_pt[0] * rs + raw_pt[1] * rc,
                    
                    pt_out_x = (rotated_raw_x * skew_factor_x) + cx,
                    pt_out_y = (rotated_raw_y * skew_factor_y) + cy,
                    
                    vx = pt_out_x - cx,
                    vy = pt_out_y - cy,
                    len = max(0.1, sqrt(vx*vx + vy*vy)),
                    dx = vx / len,
                    dy = vy / len,
                    
                    noise_side = fractal_noise(pt_out_x, pt_out_y, z_base) * side_xy_amplitude * is_side * floor_env,
                    noise_top  = fractal_noise(pt_out_x, pt_out_y, z_base) * top_z_amplitude * is_top,
                    
                    strata_offset = sin(z_base * strata_frequency * 36.0) * strata_intensity * is_side * floor_env,
                    
                    final_out_x = pt_out_x + (dx * (noise_side + strata_offset)),
                    final_out_y = pt_out_y + (dy * (noise_side + strata_offset)),
                    final_out_z = max(0, z_base + noise_top),
                    
                    pt_in_x = pt_out_x - (dx * wall_thickness),
                    pt_in_y = pt_out_y - (dy * wall_thickness)
                )
                inner_outer == 0 ? 
                    [pt_in_x, pt_in_y, z_in_base] : 
                    [final_out_x, final_out_y, final_out_z]
    ];

    // --- 2. GENERATE SURFACE FACES ---
    all_faces = concat(
        [ for (i = [0 : layers - 1])
            for (j = [0 : fragments - 1])
                let(
                    j_next = (j + 1) % fragments,
                    layer_now  = i * pts_per_layer,
                    layer_next = (i + 1) * pts_per_layer,
                    
                    in_now_l  = layer_now + j,
                    in_now_r  = layer_now + j_next,
                    in_next_l = layer_next + j,
                    in_next_r = layer_next + j_next,
                    
                    out_now_l  = layer_now + fragments + j,
                    out_now_r  = layer_now + fragments + j_next,
                    out_next_l = layer_next + fragments + j,
                    out_next_r = layer_next + fragments + j_next
                )
                each [
                    [out_now_l, out_now_r, out_next_r], [out_now_l, out_next_r, out_next_l], 
                    [in_now_r, in_now_l, in_next_l],   [in_now_r, in_next_l, in_next_r]     
                ]
        ],
        
        [ for (j = [0 : fragments - 1])
            let(
                j_next = (j + 1) % fragments,
                base_layer = layers * pts_per_layer,
                
                in_l  = base_layer + j,
                in_r  = base_layer + j_next,
                out_l = base_layer + fragments + j,
                out_r = base_layer + fragments + j_next
            )
            each [
                [in_l, in_r, out_r], [in_l, out_r, out_l]
            ]
        ]
    );

    polyhedron(points = all_points, faces = all_faces);
}

twisted_strata_morphing_bowl();
