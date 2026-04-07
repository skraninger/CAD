$fn=80;

// X Dimensions
bar_width = 6.3;
nib_width = 2.7;
top_width = 31.7;

// Y Dimensions
nib_depth = 2.7;
fork_depth = 6.3;
slot_depth = 4;

nib1_depth = 97.12;
nib2_depth = 183.59;
bar_depth = 211.59;

// Z Dimension
height = 13;

// Roundover;
roundover = 0.02;

top_depth = (2 * fork_depth) + slot_depth;

minkowski(){
    union(){
        // Top fork
        difference() {
            cube([top_width, top_depth, height]);
            translate([bar_width, bar_width, 0])
                cube([top_width - bar_width, slot_depth, height]);
         }

        // Side bar
        cube([bar_width, bar_depth, height]);

        // Nib #1
        translate([-nib_width, nib1_depth, 0])
            cube([nib_width, nib_depth, height]);
          
        // Nib #2
        translate([-nib_width, nib2_depth, 0])
            cube([nib_width, nib_depth, height]);
        
    }
    sphere(r=roundover);
}

// Text #1
translate([nib_depth/2,nib1_depth-nib_depth,height/8])
    rotate([90,0,270])
        linear_extrude(nib_depth)
            text("MAX",size=8);

// Text #2
translate([nib_depth/2,nib2_depth-nib_depth,height/8])
    rotate([90,0,270])
        linear_extrude(nib_depth)
            text("MIN",size=8);
