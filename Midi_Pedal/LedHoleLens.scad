//include <BOSL2/std.scad>
$fn=80;

//hole for led
led_diam = 5.1;
wall_thickness = 4;

plug_top = led_diam * 1.05;
plug_bottom = led_diam * 0.85;
plug_height = wall_thickness;

lens_diameter = 7;
lens_radius = lens_diameter/2;

lens_cut = lens_radius - sqrt(lens_radius^2-(plug_top/2)^2);

cylinder(plug_height,plug_bottom/2,plug_top/2);
    
translate([0,0,plug_height-(lens_radius)])
    difference() {
        translate([0,0,lens_cut])
            sphere(lens_radius);
        cube(lens_diameter, center=true);
}