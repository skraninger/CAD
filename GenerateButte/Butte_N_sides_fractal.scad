// Parametric N-Sided Tunable Sigmoid Butte with Fractal Noise & Asymmetry
// Press F6 to cleanly render the final geometry

/* [Footprint Settings] */
// Number of sides for the base footprint (3 = Triangle, 4 = Square, 5 = Pentagon, etc.)
sides = 7; 

/* [Dimensions] */
max_height = 200;
base_radius = 100;    // Center-to-vertex radius at the base
top_ratio = 0.4;     // Fraction of size remaining at the plateau flat (0.0 to 1.0)

/* [Sigmoid Tuning Parameter] */
// k controls the steepness of the transition.
// Low k (1.0) = gentle slope. High k (6.0+) = sharp cliff wall.
k = 6; 

/* [Asymmetry Engine] */
// Shift the peak center point away from [0,0] to warp the slope balance
center_shift_x = 6.0;
center_shift_y = -4.0;
// Stretch one axis more than the other to deform the uniform footprint
skew_factor_x = 1.25;
skew_factor_y = 0.90;

/* [Resolution] */
layers = 45;        // Radial/concentric ring resolution
fragments = 80;     // Total points per ring profile layer

/* [Fractal Noise Settings] */
// Total height displacement of the rock formations
fractal_amplitude = 10; 
// Number of detail layers (octaves). 1 = simple bumps, 3+ = rugged fractal crags.
octaves = 3; 

// Core pseudo-random generator
function raw_noise(x, y, z) = frac(sin(x * 12.9898 + y * 78.233 + z * 45.164) * 43758.5453);
function frac(x) = x - floor(x);

// Recursive Fractal Noise (fBm): Loops through octaves to build complex terrain
function fractal_noise(x, y, z, current_octave = 0, current_amp = 1.0, current_freq = 0.15) =
    current_octave >= octaves ? 0 :
    (raw_noise(x * current_freq, y * current_freq, z * current_freq) - 0.5) * current_amp + 
    fractal_noise(x, y, z, current_octave + 1, current_amp * 0.5, current_freq * 2.15);

// Tunable Sigmoid Function: Calculates Height (Z) based on interpolation factor (t) from 0 to 1
function tunable_sigmoid_height(t) = 
    let(r_norm = t * 2 - 1)
    let(numerator = k * r_norm)
    let(denominator = sqrt(1 + pow(k * r_norm, 2)))
    let(sigmoid = (numerator / denominator) * 0.5 + 0.5)
    max_height * (1 - sigmoid);

// Generalized mapping function to project circular angles onto an N-sided polygon perimeter
function ring_point(angle, current_scale) =
    let(
        c = cos(angle),
        s = sin(angle),
        num_sides = max(3, floor(sides)),
        segment_angle = 360 / num_sides,
        
        // Wrap the angle within the current polygon segment slice
        local_angle = (angle + 90) % segment_angle,
        half_seg = segment_angle / 2,
        
        // Universal polar equation for flat polygonal facet distance
        poly_factor = cos(half_seg) / cos(local_angle - half_seg),
        max_r = base_radius * poly_factor,
        
        // Interpolate scale outward from the plateau center to base boundary ring
        actual_r = top_ratio * max_r + (1 - top_ratio) * max_r * current_scale
    )
    [actual_r * c, actual_r * s];

module asymmetric_fractal_butte() {
    // Variable mappings to safely bypass numeric array truncation bugs
    let(p0=0, p1=1, p2=2, p3=3, p4=4, p5=5)
    let(f_bottom = [p0, p3, p2])
    let(f_top    = [p1, p4, p5])
    let(f_wall   = [p2, p3, p5, p4])
    let(f_seam_l = [p0, p2, p4, p1])
    let(f_seam_r = [p0, p1, p5, p3])
    let(all_faces = [f_bottom, f_top, f_wall, f_seam_l, f_seam_r])

    let(t_step = 1.0 / layers)
    
    for (i = [0 : layers - 1]) {
        let(
            t1 = i * t_step,
            t2 = (i + 1) * t_step,
            z1_base = tunable_sigmoid_height(t1),
            z2_base = tunable_sigmoid_height(t2)
        )
        
        for (j = [0 : fragments - 1]) {
            let(
                a1 = j * (360 / fragments),
                a2 = (j + 1) * (360 / fragments),
                
                // 1. Get true structural positions along the polygon path
                raw_pt11 = ring_point(a1, t1),
                raw_pt12 = ring_point(a2, t1),
                raw_pt21 = ring_point(a1, t2),
                raw_pt22 = ring_point(a2, t2),
                
                // 2. Inject Asymmetry: Skew the coordinates and shift the center point
                pt11 = [(raw_pt11.x * skew_factor_x) + center_shift_x * (1 - t1), (raw_pt11.y * skew_factor_y) + center_shift_y * (1 - t1)],
                pt12 = [(raw_pt12.x * skew_factor_x) + center_shift_x * (1 - t1), (raw_pt12.y * skew_factor_y) + center_shift_y * (1 - t1)],
                pt21 = [(raw_pt21.x * skew_factor_x) + center_shift_x * (1 - t2), (raw_pt21.y * skew_factor_y) + center_shift_y * (1 - t2)],
                pt22 = [(raw_pt22.x * skew_factor_x) + center_shift_x * (1 - t2), (raw_pt22.y * skew_factor_y) + center_shift_y * (1 - t2)],
                
                // 3. Sample multi-layered Fractal Noise instead of single sine waves
                n11 = fractal_noise(pt11.x, pt11.y, z1_base) * fractal_amplitude,
                n12 = fractal_noise(pt12.x, pt12.y, z1_base) * fractal_amplitude,
                n21 = fractal_noise(pt21.x, pt21.y, z2_base) * fractal_amplitude,
                n22 = fractal_noise(pt22.x, pt22.y, z2_base) * fractal_amplitude,
                
                // 4. Calculate final Z positions while making sure noise scales down to 0 at absolute base
                z11 = max(0, z1_base + n11 * (1 - t1)),
                z12 = max(0, z1_base + n12 * (1 - t1)),
                z21 = max(0, z2_base + n21 * (1 - t2)),
                z22 = max(0, z2_base + n22 * (1 - t2))
            )
            
            polyhedron(
                points = [
                    [center_shift_x * (1 - t1), center_shift_y * (1 - t1), z11], // 0: Shifted center inner
                    [center_shift_x * (1 - t2), center_shift_y * (1 - t2), z21], // 1: Shifted center outer
                    [pt11.x, pt11.y, z11],                                         // 2: Inner Ring Left
                    [pt12.x, pt12.y, z12],                                         // 3: Inner Ring Right
                    [pt21.x, pt21.y, z21],                                         // 4: Outer Ring Left
                    [pt22.x, pt22.y, z22]                                          // 5: Outer Ring Right
                ],
                faces = all_faces
            );
        }
    }
}

// Generate the high-detail landmass
asymmetric_fractal_butte();
