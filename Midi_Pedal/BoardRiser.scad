//include <BOSL2/std.scad>
$fn=80;

riser_height = 6.8;
wall_thickness = 2;
riser_x_separation = 50;
riser_y_separation = 40;

//screw dimensions
screw_thread_diam = 3.2;
screw_length = 6;

//riser
riser_diam = screw_thread_diam + 2*wall_thickness;

//base
base_side_x = riser_x_separation + riser_diam * 2;
base_side_y = riser_y_separation + riser_diam * 2;
base_height = 2;

module riser_with_hole() {
    difference() {
        cylinder(h=riser_height, d=riser_diam);
        translate([0,0,riser_height-screw_length])
            cylinder(h=riser_height, d=screw_thread_diam);
    }
}

color("green")
cube([base_side_x, base_side_y, base_height]);

riser1_x = riser_diam;
riser1_y = riser_diam;

color("red")
translate([riser1_x, riser1_y, 0])
    riser_with_hole();

riser2_x = riser_diam;
riser2_y = riser_diam+riser_y_separation;

color("red")
translate([riser2_x, riser2_y, 0])
    riser_with_hole();

riser3_x = riser_diam+riser_x_separation;
riser3_y = riser_diam;

color("red")
translate([riser3_x, riser3_y, 0])
    riser_with_hole();

riser4_x = riser_diam+riser_x_separation;
riser4_y = riser_diam+riser_y_separation;

color("red")
translate([riser4_x, riser4_y, 0])
    riser_with_hole();
