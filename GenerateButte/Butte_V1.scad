// 90-Degree Rotated Sigmoid Butte (Broad Dome / Shield Profile)
// Press F6 to cleanly render the final geometry

/* [Dimensions] */
max_height = 100;
base_radius = 25;
top_radius = 15;

/* [Resolution] */
layers = 60;        // Vertical resolution
fragments = 72;     // Circular resolution

/* [Texture Settings] */
texture_amplitude = 4.0; 

// Pseudo-random noise function based on sine wave coordinates
function noise(x, y, z) = frac(sin(x * 12.9898 + y * 78.233 + z * 45.164) * 43758.5453);
function frac(x) = x - floor(x);

// Rotated Sigmoid Profile: Calculates Height (Z) based on a given Radius (R)
function sigmoid_height(r) = 
    // Normalize radius between base and top into a [-6, 6] sigmoid domain
    let(r_norm = ((r - top_radius) / (base_radius - top_radius)) * 12 - 6)
    let(sigmoid = 1 / (1 + exp(-r_norm))) // Standard sigmoid curve
    // Invert sigmoid so height is max at top_radius and drops to 0 at base_radius
    max_height * (1 - sigmoid);

module rotated_sigmoid_butte() {
    // Step radially outward from top_radius to base_radius instead of up by layers
    let(r_step = (base_radius - top_radius) / layers)
    
    // Obfuscated indices to bypass the system's character-stripping bug
    let(f_bottom = concat([0, 3, 2]))
    let(f_top    = concat([1, 4, 5]))
    let(f_wall   = concat([2, 3, 5, 4]))
    let(f_seam_l = concat([0, 2, 4, 1]))
    let(f_seam_r = concat([0, 1, 5, 3]))
    let(all_faces = [f_bottom, f_top, f_wall, f_seam_l, f_seam_r])

    for (i = [0 : layers - 1]) {
        let(
            r1 = top_radius + i * r_step,
            r2 = top_radius + (i + 1) * r_step,
            z1_base = sigmoid_height(r1),
            z2_base = sigmoid_height(r2)
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

// Generate the rotated terrain feature
rotated_sigmoid_butte();
