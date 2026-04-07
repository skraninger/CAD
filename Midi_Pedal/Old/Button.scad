include <BOSL2/std.scad>
$fn=50;

//button
b_width = 64;
b_depth = 40;
b_height = 20;
b_thickness = 5;

//slant
s_width = 40;
s_height = 10;

//hinge pin
h_width_p = 2;
h_diam_p = 8;

//hinge pin end
h_width_e = 3;
h_diam_e = 4;

//hinge block
hb_width = s_width;
hb_depth = b_depth+20;
hb_height = b_height;

//
//conical hole for led
//bottom diameter to
led_diam = 2;
led_width = hb_width - (b_width - s_width) - 2*b_thickness;
led_depth = hb_depth - 2*b_thickness;
led_height = hb_height - b_thickness;

//fudge for texture height
texture_height = 2;

module cut_t() {
    //cut triangle points
    cut_p1 = [b_width, b_height];
    cut_p2 = [b_width, b_height-s_height];
    cut_p3 = [b_width-s_width, b_height];

    color("red")
    translate([0,b_depth,0])
    rotate([90,0,0])
        linear_extrude(height = b_depth,)    
            polygon(points=[cut_p1,cut_p2,cut_p3]);
}

module cut_t2() {
    hyp_len = sqrt(b_depth^2 + s_height^2); // Hypotenuse length
    angle = atan(s_height / b_depth); // Hypotenuse angle

    translate([0,b_depth,0])
    rotate([180,0,-90])
    wedge([b_depth, s_width, s_height])
    attach("hypot")
    textured_tile("dots", size=[b_depth, hyp_len+1],
        tex_reps=[5,5], style="concave", tex_depth=-2)
    ;
}

module button(cutout=true) {
difference() {

//main switch body
cube([b_width,b_depth,b_height]);

color("blue")
translate([b_width,0,b_height])
cut_t2();

//cutout insert
//cut_i_width = s_width - 2*b_thickness;
cut_i_width = b_width - 2*b_thickness;
cut_i_depth = b_depth - 2*b_thickness;
cut_i_height = b_height - s_height - b_thickness - texture_height;
//cut_i_x_offset = b_width - s_width + b_thickness;
cut_i_x_offset = b_thickness;
cut_i_y_offset = b_thickness;

if (cutout) {
    color("green")
    translate([cut_i_x_offset, cut_i_y_offset, 0])
        cube([cut_i_width, cut_i_depth, cut_i_height]);
}

//rouding on bottom left
color("blue")
if (cutout) {
    union() {
        translate([0,b_depth,0])
            rotate([90,0,0])
                linear_extrude(height=b_depth)
                    mask2d_roundover(r=b_height/2);
                
        translate([0,0,b_height])
            rotate([-90,0,0])
                linear_extrude(height=b_depth)
                    mask2d_roundover(r=b_height/2);
   }
   }
}
}

//hinge pin
module pin() {
    color("green")
    cylinder(h=h_width_p,d=h_diam_p);

    color("red")
    translate([0,0,h_width_p])
    cylinder(h=h_width_e, r1=h_diam_p/2, r2=h_diam_e/2);
}

module pins() {
    pin_x_offset = (b_width-s_width)/2;
    pin_z_offset = b_height/2;

    translate([pin_x_offset,0,pin_z_offset])
    rotate([90,0,0]) pin();

    translate([pin_x_offset,b_depth,pin_z_offset])
    rotate([-90,0,0]) pin();
}

module button_pins() {
}

//Centering offsets so that scale works 
pin_x_offset = (b_width-s_width)/2;
pin_z_offset = b_height/2;
center_y_offset = b_depth / 2;

//fudge for the angle cutoff with the extra -1
hb_x_offset = -pin_x_offset - hb_width + b_width - s_width - 1;
hb_y_offset = -(hb_depth - b_depth)/2 - center_y_offset;
hb_z_offset = -pin_z_offset;


difference() {
    color("red")
    translate([hb_x_offset,hb_y_offset,hb_z_offset])
    difference() {
        cube([hb_width, hb_depth, hb_height]);
        translate([b_thickness,b_thickness,0])
            cube([led_width, led_depth, led_height]);        
    }
    //cutout for the button, a little bigger
    scale([1.02,1.02,1.02])
        translate([-pin_x_offset,-center_y_offset,-pin_z_offset])
            union () {
            button(false);
            pins();
        }
}

//button comes back in
translate([-pin_x_offset,-center_y_offset,-pin_z_offset])
    union () {
    button(true);
    pins();
}

