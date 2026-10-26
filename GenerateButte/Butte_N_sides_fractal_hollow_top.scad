// 100% Manifold Parametric N-Sided Tunable Sigmoid Butte (Inverted Bowl)
// Side noise moves geometry on the XY plane; top noise moves on the Z axis.

/* [Footprint Settings] */
sides = 5; // Number of sides for the footprint (3=Triangle, 4=Square, 5=Pentagon...)

/* [Dimensions] */
max_height = 180;
base_radius = 50;    

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
layers = 45;        // Concentric ring slicing resolution
fragments = 72;     // Points per perimeter loop layer

/* [Fractal Noise Settings] */
// XY plane horizontal displacement amplitude for side walls
side_xy_amplitude = 10.0; 

// Pure vertical Z-axis displacement amplitude for the top plateau
top_z_amplitude = 3.0; 

octaves = 3; 

// Mathematical Utilities (Array bracket indexed for multi-version safety)
function raw_noise(x, y, z) = frac(sin(x * 12.9898 + y * 78.233 + z * 45.164) * 43758.5453);
function frac(x) = x - floor(x);

function fractal_noise(x, y, z, current_octave = 0, current_amp = 1.0, current_freq = 0.15) =
    current_octave >= octaves ? 0 :
    (raw_noise(x * current_freq, y * current_freq, z * current_freq) - 0.5) * current_amp + 
    fractal_noise(x, y, z, current_octave + 1, current_amp * 0.5, current_freq * 2.15);

// Adjusted Sigmoid Profile mapping using the base_extension_factor parameter
function tunable_sigmoid_height(t) = 
    let(domain_end = -6 + (12 * base_extension_factor))
    let(r_norm = -6 + (domain_end - (-6)) * t) 
    let(numerator = k * r_norm)
    let(denominator = sqrt(1 + pow(k * r_norm, 2)))
    let(sigmoid = (numerator / denominator) * 0.5 + 0.5)
    
    let(sig_at_zero = ( (k * (-6)) / sqrt(1 + pow(k * (-6), 2)) ) * 0.5 + 0.5)
    let(sig_at_end = (numerator / denominator) * 0.5 + 0.5)
    max_height * (1 - (sig_at_end - sig_at_zero) / (1 - sig_at_zero));

function ring_point(angle, current_scale) =
    let(
        c = cos(angle), s = sin(angle),
        num_sides = max(3, floor(sides)),
        segment_angle = 360 / num_sides,
        local_angle = (angle + 90) % segment_angle,
        half_seg = segment_angle / 2,
        poly_factor = cos(half_seg) / cos(local_angle - half_seg),
        max_r = base_radius * poly_factor,
        actual_r = current_scale * max_r
    )
    [actual_r * c, actual_r * s];

module directional_noise_bowl() {
    pts_per_layer = fragments * 2;
    
    // --- 1. GENERATE DIRECTIONAL NOISE POINT GRID ---
    all_points = [ for (i = [0 : layers]) 
        let(
            t = i / layers,
            z_base = tunable_sigmoid_height(t),
            z_in_base = max(0, z_base - wall_thickness),
            
            // Mix factor: 1.0 when near the center top, drops to 0.0 down the walls
            is_top = pow(1 - t, 4), 
            is_side = 1.0 - is_top,
            
            // Dampen side displacement near the absolute ground floor
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
                    
                    // Sample independent noise profiles
                    noise_side = fractal_noise(pt_out_x, pt_out_y, z_base) * side_xy_amplitude * is_side * floor_env,
                    noise_top  = fractal_noise(pt_out_x, pt_out_y, z_base) * top_z_amplitude * is_top,
                    
                    // Side texture pushes coordinate outward/inward along its XY normal vector axis
                    final_out_x = pt_out_x + (dx * noise_side),
                    final_out_y = pt_out_y + (dy * noise_side),
                    final_out_z = max(0, z_base + noise_top),
                    
                    // Inner cavity wall mirrors the same coordinates but remains smooth/untextured
                    pt_in_x = pt_out_x - (dx * wall_thickness),
                    pt_in_y = pt_out_y - (dy * wall_thickness)
                )
                inner_outer == 0 ? 
                    [pt_in_x, pt_in_y, z_in_base] : 
                    [final_out_x, final_out_y, final_out_z]
    ];

    // --- 2. GENERATE CONTINUOUS SURFACE FACES ---
    all_faces = concat(
        // A. RADIAL QUAD STRIPS
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
        
        // B. BASE RIM SEALS
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

directional_noise_bowl();
