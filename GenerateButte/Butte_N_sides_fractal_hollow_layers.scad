// 100% Manifold Parametric Sigmoid Butte (Inverted Bowl)
// Fully resolved keyframe array vectors to eliminate all compilation syntax errors.

/* [Footprint Settings & Keyframes] */
// Exactly 8 integers. Index 0 is the absolute TOP, Index 7 is the BASE floor.
// The model smoothly morphs from one shape to the next as it steps down the layers.
side_keyframes = [3, 3, 3, 4, 4, 6, 6, 6]; 

// Controls corner smoothness. 0.0 = perfectly sharp, 1.0 = fully round (circle)
corner_rounding_factor = 0.4; 

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
base_extension_factor = 0.6; 

/* [Asymmetry Engine] */
center_shift_x = 5.0;
center_shift_y = -3.0;
skew_factor_x = 1.20;
skew_factor_y = 0.95;

/* [Resolution] */
layers = 56;        // Total concentric slicing layers (multiples of 7 or 8 for clean transitions)
fragments = 120;    // High circular detail helps different side shapes morph without tearing

/* [Fractal Noise Settings] */
side_xy_amplitude = 3.0; 
top_z_amplitude = 2.0; 
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

// Dynamic multi-stage morphing mapping function
function ring_point(angle, t) =
    let(
        c = cos(angle), s = sin(angle),
        
        // Map continuous t (0.0 to 1.0) across the 7 transition spans between our 8 indices
        raw_index = t * 7,
        idx1 = min(7, max(0, floor(raw_index))),
        idx2 = min(7, max(0, ceil(raw_index))),
        blend_factor = raw_index - idx1,
        
        // Fetch target side counts from the keyframe look-up array
        sides1 = max(3, side_keyframes[idx1]),
        sides2 = max(3, side_keyframes[idx2]),
        
        // Evaluate the sharp radius for both adjacent shapes
        sharp_r1 = get_poly_r(angle, sides1),
        sharp_r2 = get_poly_r(angle, sides2),
        
        // Smoothly interpolate between the two shape profiles
        sharp_r = (1.0 - blend_factor) * sharp_r1 + (blend_factor * sharp_r2),
        
        // Apply global corner rounding factor to soft-blend against a perfect cylinder
        r_blend = (1.0 - corner_rounding_factor) * sharp_r + (corner_rounding_factor * base_radius),
        actual_r = t * r_blend
    )
    [actual_r * c, actual_r * s];

module morphing_directional_noise_bowl() {
    pts_per_layer = fragments * 2;
    
    // --- 1. GENERATE NOISE POINT GRID ---
    all_points = [ for (i = [0 : layers]) 
        let(
            t = i / layers,
            z_base = tunable_sigmoid_height(t),
            z_in_base = max(0, z_base - wall_thickness),
            
            is_top = pow(1 - t, 4), 
            is_side = 1.0 - is_top,
            floor_env = 1.0 - pow(t, 4),
            
            cx = center_shift_x * (1 - t),
            cy = center_shift_y * (1 - t)
        )
        for (inner_outer = [0 : 1]) 
            for (j = [0 : fragments - 1])
                let(
                    a = j * (360 / fragments),
                    raw_pt = ring_point(a, t),
                    
                    pt_out_x = (raw_pt[0] * skew_factor_x) + cx,
                    pt_out_y = (raw_pt[1] * skew_factor_y) + cy,
                    
                    vx = pt_out_x - cx,
                    vy = pt_out_y - cy,
                    len = max(0.1, sqrt(vx*vx + vy*vy)),
                    dx = vx / len,
                    dy = vy / len,
                    
                    noise_side = fractal_noise(pt_out_x, pt_out_y, z_base) * side_xy_amplitude * is_side * floor_env,
                    noise_top  = fractal_noise(pt_out_x, pt_out_y, z_base) * top_z_amplitude * is_top,
                    
                    final_out_x = pt_out_x + (dx * noise_side),
                    final_out_y = pt_out_y + (dy * noise_side),
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

morphing_directional_noise_bowl();
