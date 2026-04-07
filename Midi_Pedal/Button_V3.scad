include <BOSL2/std.scad>
$fn=80;

//scaling to cutout inside of hinge
cutout_scale = 1.04;

//wall thickness
wall_thickness = 4;

//hinge block
//hb_width = 40;
hb_width = 40;
hb_depth = 50;
hb_height = 20;

//hinge connect
//hc_width = hb_width - 22;
//hc_width = hb_width - 15;
hc_width = 20;
hc_depth = hb_depth - 20;
hc_height = hb_height;
hc_extra = 0.2;

//button
b_width = 40;
b_depth = hb_depth;
b_height = hb_height+1;
b_rounding = hb_width / 2;

//slant
s_width = 40;
s_height = 10;

//hinge pin
h_width_p = 2.5;
h_diam_p = 8;

//hinge pin end
h_width_e = 3;
h_diam_e = 3;

//hole for switch
//switch_top_diam = 10;
switch_top_diam = 15;

//switch_bot_diam = 20;
switch_bot_diam = b_width - 2 * wall_thickness;
switch_indent = 3;

//screw dimensions
screw_hole_diam = 4.2;
screw_thread_diam = 2.9;
screw_space = 5.5;
screw_length = 16;

//cutout for led
led_width = hb_width - hc_width -screw_space
    - 2*wall_thickness;
led_depth = hb_depth - 2*wall_thickness;
led_height = hb_height - wall_thickness;

//hole for led
led_diam = 5.1;

//fudge for texture height
texture_height = 2;

module rounding(r_depth,r_height,r_separation=0) {
    r_sep_delta = (r_separation == 0) ? 0 : r_separation - r_height;
    
    color("blue")
    union() {
        translate([0,r_depth,0])
            rotate([90,0,0])
                linear_extrude(height=r_depth)
                    mask2d_roundover(r=r_height/2);
                
        translate([0,0,r_height+r_sep_delta])
            rotate([-90,0,0])
                linear_extrude(height=r_depth)
                    mask2d_roundover(r=r_height/2);
    }
}

module cut_t2() {
    hyp_len = sqrt(s_width^2 + s_height^2); // Hypotenuse length
    angle = atan(s_height / s_width); // Hypotenuse angle

    translate([0,b_depth,0])
    rotate([180,0,-90])
    wedge([b_depth, s_width, s_height])
    attach("hypot")
    textured_tile("dots", size=[b_depth, hyp_len],
        tex_reps=[7,5], style="concave", tex_depth=-2)
    ;
}

module screw_holes(invert=true) {
    //screw hole center offsets
    sc1_hole_center_x = led_width + 2*wall_thickness
        + screw_thread_diam/2;
    sc1_hole_center_y = led_depth + wall_thickness
        - screw_thread_diam/2;
    sc2_hole_center_x = led_width + 2*wall_thickness
        + screw_thread_diam/2;
    sc2_hole_center_y = wall_thickness
        + screw_thread_diam/2;

    invert_angle = invert ? 180 : 0;
    
    //screw holes
    color("red")
    translate([sc1_hole_center_x, sc1_hole_center_y, 0])
        rotate([invert_angle,0,0])
            cylinder(screw_length,d=screw_thread_diam);
    
    //screw holes
    color("orange")
    translate([sc1_hole_center_x, sc2_hole_center_y, 0])
        rotate([invert_angle,0,0])
            cylinder(screw_length,d=screw_thread_diam);
}

module button(cutout=true) {

    difference() {
        //main switch body
        //0.5 = fudge for wedge cutout
        b_width_fudge = b_width - 0.5;
        cube([b_width_fudge, b_depth, b_height]);

        //rounding of the front
        translate([b_width_fudge,0,0])
            rotate([90,0,180])
                rounding(b_height, b_rounding, b_depth);
        
        //slant with buttons
        color("blue")
        translate([b_width,0,b_height])
        cut_t2();

        if (cutout) {
            c_width = b_width - 2 * wall_thickness;
            c_depth = b_depth - 2 * wall_thickness;
            c_height = b_height-s_height-wall_thickness;
            c_rounding = c_width / 2;
            
            /*
            //inside cutout
            translate([wall_thickness, wall_thickness, 0])
                difference() {
                    cube([c_width, c_depth, c_height]);
                    //rounding of the cutout front
                    translate([c_width,0,0])
                        rotate([90,0,180])
                            rounding(c_height, c_rounding,
                                c_depth);
                }
            */
            
            //switch center offset
            ph_hole_center_offset = s_width/2;

            //switch top indent
            color("purple")
            translate([ph_hole_center_offset, hb_depth/2,
                b_height-s_height-wall_thickness
                +switch_indent])
                    rotate([180,0,0])
                        cylinder(switch_indent+c_height,
                            d1=switch_top_diam,
                            d2=switch_bot_diam);
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
    pin_x_offset = hc_width/2;
    pin_z_offset = hc_height/2;

    translate([pin_x_offset,0,pin_z_offset])
    rotate([90,0,0]) pin();

    translate([pin_x_offset,hc_depth,pin_z_offset])
    rotate([-90,0,0]) pin();
}

module button_and_pins(cutout=true) {
    button(true);
    pins();
}

module connector(cutout=true) {
    difference() {
        union() {
            cube([hc_width+hc_extra, hc_depth, hc_height]);
            pins();
        }
        
        //rouding
        color("blue")
        if (cutout) {
            rounding(hc_depth,hc_height);
        }
   }
}

module all() {

    pin_x_offset = hc_width/2 + hb_width-hc_width;
    pin_z_offset = hc_height/2;

    color("red")
    difference() {

        //hinge block
        //center around pin pivot for scale operation
        translate([-pin_x_offset, -hb_depth/2, -pin_z_offset])
            cube([hb_width, hb_depth, hb_height]);
            
        //rouding of hinge block
        translate([-pin_x_offset, -hb_depth/2, -pin_z_offset])
            translate([hb_width,hb_depth,0])
                rotate([0,0,180])
                    rounding(hb_depth,hb_height);
        
        //led cutout
        translate([-pin_x_offset, -hb_depth/2, -pin_z_offset])
            translate([wall_thickness,wall_thickness,0])
                union(){
                    cube([led_width, led_depth, led_height]);
                    translate([led_width/2,led_depth/2,led_height])
                        cylinder(wall_thickness*2,d=led_diam);
                }
        
        //screw holes
        translate([-pin_x_offset, -hb_depth/2, -pin_z_offset])
            screw_holes(false);
    
        //hinge cutout - a bit bigger than the hinged part
        scale([cutout_scale,cutout_scale,cutout_scale])
        translate([-pin_x_offset, -hb_depth/2, -pin_z_offset])
            translate([hb_width-hc_width,(hb_depth-hc_depth)/2,0])
                connector(false);
    }

    //Add the block back in
    translate([-pin_x_offset, -hb_depth/2, -pin_z_offset])
        translate([hb_width-hc_width,(hb_depth-hc_depth)/2,0])
            connector(true);
            
    //button slanting part
    translate([-pin_x_offset, -hb_depth/2, -pin_z_offset])
        translate([hb_width+hc_extra,0,0])
            button();
        
}

difference() {
    all();
    //look at a slice
    //translate([-50,-50,0]) cube([100,100,100]);
}