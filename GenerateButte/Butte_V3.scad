// Rectangular Tunable Sigmoid Butte (Patched Manifold Geometry)
// Press F6 to cleanly render the final geometry

/* [Dimensions] */
max_height = 30;
base_length = 80;    // Total size along X axis at the base
base_width = 60;     // Total size along Y axis at the base
top_ratio = 0.2;     // Fraction of size remaining at the plateau flat (0.0 to 1.0)

/* [Sigmoid Tuning Parameter] */
// k controls the steepness of the transition.
// Low k (1.0) = gentle slope. High k (6.0+) = sharp cliff wall.
k = 3.5; 

/* [Resolution] */
layers = 40;        // Radial/concentric ring resolution
fragments = 72;     // Points per rectangular ring profile

/* [Texture Settings] */
texture_amplitude = 1.0; 

// Pseudo-random noise function based on space coordinates
function noise(x, y, z) = frac(sin(x * 12.9898 + y * 78.233 + z * 45.164) * 43758.5453);
function frac(x) = x - floor(x);

// Tunable Sigmoid Function: Calculates Height (Z) based on interpolation factor (t) from 0 to 1
function tunable_sigmoid_height(t) = 
    let(r_norm = t * 2 - 1)
    let(numerator = k * r_norm)
    let(denominator = sqrt(1 + pow(k * r_norm, 2)))
    let(sigmoid = (numerator / denominator) * 0.5 + 0.5)
    max_height * (1 - sigmoid);

// Patched Mapping Function: Smoothly maps circular angles to a solid rectangular box footprint without any dead zones
function ring_point(angle, current_scale) =
    let(
        c = cos(angle),
        s = sin(angle),
        // Calculate the square-clipping metric to establish continuous scale factors
        rect_factor = 1 / max(abs(c) / (base_length / 2), abs(s) / (base_width / 2)),
        
        // Calculate total radius out to the edge of the true bounding box frame
        max_r = rect_factor,
        
        // Interpolate scale outward from the plateau center to base boundary ring
        actual_r = top_ratio * max_r + (1 - top_ratio) * max_r * current_scale
    )
    [actual_r * c, actual_r * s];

module rectangular_sigmoid_butte() {
    // Variable mappings to safely bypass numeric array truncation bugs
    let(p0=0, p1=1, p2=2, p3=3, p4=4, p5=5)
    let(f_bottom = [p0, p3, p2])
    let(f_top    = [p1, p4, p5])
    let(f_wall   = [p2, p3, p5, p4])
    let(f_seam_l = [p0, p2, p4, p1])
    let(f_seam_r = [p0, p1, p5, p3])
    let(all_faces = [f_bottom, f_top, f_wall, f_seam_l, f_seam_r])

    // Step from inner plateau (t=0) to outer base edge (t=1)
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
                
                // Get true structural positions along the complete closed path
                pt11 = ring_point(a1, t1),
                pt12 = ring_point(a2, t1),
                pt21 = ring_point(a1, t2),
                pt22 = ring_point(a2, t2),
                
                // Sample noise continuously based on spatial coordinates
                n11 = (noise(pt11.x, pt11.y, z1_base) - 0.5) * texture_amplitude,
                n12 = (noise(pt12.x, pt12.y, z1_base) - 0.5) * texture_amplitude,
                n21 = (noise(pt21.x, pt21.y, z2_base) - 0.5) * texture_amplitude,
                n22 = (noise(pt22.x, pt22.y, z2_base) - 0.5) * texture_amplitude,
                
                // Displace height (Z axis) safely
                z11 = max(0, z1_base + n11),
                z12 = max(0, z1_base + n12),
                z21 = max(0, z2_base + n21),
                z22 = max(0, z2_base + n22)
            )
            
            polyhedron(
                points = [
                    [0, 0, z11],               // 0: Center projection inner
                    [0, 0, z21],               // 1: Center projection outer
                    [pt11.x, pt11.y, z11],     // 2: Inner Ring Left
                    [pt12.x, pt12.y, z12],     // 3: Inner Ring Right
                    [pt21.x, pt21.y, z21],     // 4: Outer Ring Left
                    [pt22.x, pt22.y, z22]      // 5: Outer Ring Right
                ],
                faces = all_faces
            );
        }
    }
}

// Generate the solid rectangular terrain feature
rectangular_sigmoid_butte();
