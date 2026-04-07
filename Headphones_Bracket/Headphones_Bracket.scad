$fn = 50;

//Minkowski rounding
roundover = 1;

holder_width = 25;
//Thicker is stronger
holder_thickness = 5;

//Size the clip for the surface
top_inner_width = 20;
top_outer_length = 60;
top_outer_width = top_inner_width + 2 * holder_thickness;
top_inner_length = top_outer_length - holder_thickness;

//:Headphone holder length
hp_length = 40;
//:Headphone holder width
hp_width = 40;
//:Headphone holder lip
hp_lip = 8;

hp_outer_length = hp_length + 4 * holder_thickness;
hp_outer_width = hp_width + 2 * holder_thickness;

cutout_length = 3 * holder_thickness;
cutout_width = hp_width - hp_lip;;

//NOTE: These fudgy numbers need to be adjusted
//  when the other sizes are changed 
//  to change the size of the "round" part
//
//:Rounded holder (fudge to fit)
round_diameter = 50;
//:Tip of round (fudge)
round_cutoff = 3.5;

module cylinder_slice(diameter, height, cutoff, center=true) {
    r = diameter / 2;
    dx = center ? r : r - sqrt(2*r*cutoff - cutoff^2);
    dy = diameter - cutoff;
    translate([-dx, -dy, 0])
    difference() {
        translate([r,r,0])
            cylinder(h=height,d=diameter);
        translate([0,-cutoff,0])
            cube([diameter,diameter,height]);
    }
}

minkowski() {
union() {
difference(){
    //top block
    cube([top_outer_length,top_outer_width,holder_width]);

    //top cutout
    translate([holder_thickness,holder_thickness,0])
        cube([top_inner_length,top_inner_width,holder_width]);
}


color("red")
translate([0,-top_outer_width,0])
    difference() {
        //bottom block
        cube([hp_outer_length,top_outer_width,holder_width]);

        //bottom cutout
        translate([holder_thickness,holder_thickness,0])
            cube([hp_length,hp_width,holder_width]);

        //side cutout
        translate([0,hp_lip+holder_thickness,0])
            cube([cutout_length, cutout_width, holder_width]);
    }

//Rounded part
dz = sqrt(round_diameter * round_cutoff - round_cutoff^2);
color("blue")
translate([holder_thickness, -hp_width+3*holder_thickness, dz])
rotate([0,90,0])
    cylinder_slice(round_diameter, hp_width, round_cutoff);


}
sphere(d=roundover);
}

