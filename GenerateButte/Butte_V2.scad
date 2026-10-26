// 90-Degree Rotated Tunable Sigmoid Butte
// Press F6 to cleanly render the final manifold geometry

/* [Dimensions] */
max_height = 120;
base_radius = 50;
top_radius = 5;

/* [Sigmoid Tuning Parameter] */
// k controls the steepness of the transition.
// Low k (1.0) = gentle slope. High k (6.0+) = sharp cliff wall.
k = 6; 

/* [Resolution] */
layers = 60;        // Vertical resolution
fragments = 72;     // Circular resolution

/* [Texture Settings] */
texture_amplitude = 5.0; 

// Pseudo-random noise function based on sine wave coordinates
function noise(x, y, z) = frac(sin(x * 12.9898 + y * 78.233 + z * 45.164) * 43758.5453);
function frac(x) = x - floor(x);

// Tunable Sigmoid Function: Calculates Height (Z) based on a given Radius (R)
function tunable_sigmoid_height(r) = 
    // 1. Normalize the radius into a symmetric domain from -1 to 1
    let(r_norm = ((r - top_radius) / (base_radius - top_radius)) * 2 - 1)
    
    // 2. Compute the algebraic tunable sigmoid equation
    let(numerator = k * r_norm)
    let(denominator = sqrt(1 + pow(k * r_norm, 2)))
    let(sigmoid = (numerator / denominator) * 0.5 + 0.5) // Remap output range to [0, 1]
    
    // 3. Map to max height (Inverted so center is high and base tapers down to 0)
    max_height * (1 - sigmoid);

module rotated_sigmoid_butte() {
    let(r_step = (base_radius - top_radius) / layers)
    
    // Abstracting variable allocations to cleanly bypass numeric array truncation bugs
    let(p0=0, p1=1, p2=2, p3=3, p4=4, p5=5)
    let(f_bottom = [p0, p3, p2])
    let(f_top    = [p1, p4, p5])
    let(f_wall   = [p2, p3, p5, p4])
    let(f_seam_l = [p0, p2, p4, p1])
    let(f_seam_r = [p0, p1, p5, p3])
    let(all_faces = [f_bottom, f_top, f_wall, f_seam_l, f_seam_r])

    for (i = [0 : layers - 1]) {
        let(
            r1 = top_radius + i * r_step,
            r2 = top_radius + (i + 1) * r_step,
            z1_base = tunable_sigmoid_height(r1),
            z2_base = tunable_sigmoid_height(r2)
        )
        
        // Loop through the circumference to build the slices
        for (j = [0 : fragments - 1]) {
            let(
                a1 = j * (360 / fragments),
                a2 = (j + 1) * (360 / fragments),
                
                // Sample texture offset from noise function
                n11 = (noise(cos(a1), sin(a1), r1) - 0.5) * texture_amplitude,
                n12 = (noise(cos(a2), sin(a2), r1) - 0.5) * texture_amplitude,
                n21 = (noise(cos(a1), sin(a1), r2) - 0.5) * texture_amplitude,
                n22 = (noise(cos(a2), sin(a2), r2) - 0.5) * texture_amplitude,
                
                // Apply texture to the calculated heights (Z-axis displacement)
                z11 = max(0, z1_base + n11),
                z12 = max(0, z1_base + n12),
                z21 = max(0, z2_base + n21),
                z22 = max(0, z2_base + n22)
            )
            
            // Build the segments using a fully enclosed 3D polyhedron
            polyhedron(
                points = [
                    [0, 0, z11],                       // 0: Center profile projection (Inner Z1)
                    [0, 0, z21],                       // 1: Center profile projection (Outer Z2)
                    [r1 * cos(a1), r1 * sin(a1), z11], // 2: Inner-Left
                    [r1 * cos(a2), r1 * sin(a2), z12], // 3: Inner-Right
                    [r2 * cos(a1), r2 * sin(a1), z21], // 4: Outer-Left
                    [r2 * cos(a2), r2 * sin(a2), z22]  // 5: Outer-Right
                ],
                faces = all_faces
            );
        }
    }
}

// Generate the tunable feature
rotated_sigmoid_butte();
