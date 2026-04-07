include <BOSL2/std.scad>
$fn=50;

//scaling to cutout inside of hinge
cutout_scale = 1.03;

//wall thickness
wall_thickness = 4;

//wall thickness for the base
base_wall_thickness = 5;

//inset for bottom
bottom_inset_height = 5;

//Length used to cut through the wall
wall_cut = 6;

//from the button for placeholder
hb_width = 40;
hb_depth = 50;
hb_height = 20;
hc_width = 20;
hc_extra = 0.2;
s_width = 40;

//base size
base_width = 20;
base_depth = 140;
base_height = 50;

//slant
slant_width = 190;
slant_height = 30;

//render top or bottom
//top_or_bottom = "template";
//top_or_bottom = "top";
top_or_bottom = "bottom";

//screw dimensions
screw_hole_diam = 4.1;
screw_thread_diam = 2.8;
screw_space = 5.5;
screw_length = 16;

//cutout for led
led_width = hb_width - hc_width -screw_space
    - 2*wall_thickness;
led_depth = hb_depth - 2*wall_thickness;
led_height = hb_height - wall_thickness;

//hole for led
led_diam = 5.1;

//hole for switch
switch_hole_diam = 12;

//top size
top_height = base_height+20;

//box size
box_width = base_width + slant_width;
box_depth = base_depth;
box_height = base_height;

//side screw tab
tab_diameter = 14;
tab_hole_height = tab_diameter / 2;

module cut_t2(t_width, t_depth, t_height) {
    translate([0,t_depth,0])
        rotate([180,0,-90])
            wedge([t_depth, t_width, t_height]);
}   

module button_placeholder() {
    ph_width = hb_width+s_width+hc_extra;
    ph_depth = hb_depth;
    ph_height = hb_height;

    //button hole center offset
    ph_hole_center_offset = hb_width+s_width/2;

    //button placeholder cube
    union() {
        color("blue")
        cube([ph_width, ph_depth, ph_height]);
        
        //switch hole cutout
        color("green")
        translate([ph_hole_center_offset, ph_depth/2, 0])
            rotate([180,0,0])
                cylinder(wall_cut,d=switch_hole_diam);

        //led slot
        color("green")
        translate([wall_thickness, wall_thickness, -wall_cut])
            cube([led_width, led_depth, wall_cut]);

        //screw hole center offsets
        sc1_hole_center_x = led_width + 2*wall_thickness
            + screw_hole_diam/2;
        sc1_hole_center_y = led_depth + wall_thickness
            - screw_hole_diam/2;
        sc2_hole_center_x = led_width + 2*wall_thickness
            + screw_hole_diam/2;
        sc2_hole_center_y = wall_thickness
            + screw_hole_diam/2;

        //screw holes
        color("red")
        translate([sc1_hole_center_x, sc1_hole_center_y, 0])
            rotate([180,0,0])
                cylinder(wall_cut,d=screw_hole_diam);
        
        //screw holes
        color("orange")
        translate([sc1_hole_center_x, sc2_hole_center_y, 0])
            rotate([180,0,0])
                cylinder(wall_cut,d=screw_hole_diam);
    }
}

module slanted_base() {
    color("yellow")
    difference() {
        cube([box_width,box_depth,box_height]);
        
        //slant cut out
        color("red")
        translate([box_width,0,box_height])
            cut_t2(slant_width,box_depth,slant_height);
    }
    
    //color("green")
    //cube([base_width,base_depth,top_height]);
}

module four_buttons() {
    //calculate distances to each button center
    bw = hb_width+s_width+hc_extra;
    bd = hb_depth;
    bh = hb_height;

    hyp_len = sqrt(slant_width^2 + slant_height^2); // Hypotenuse length
    angle = atan(slant_height / slant_width); // Hypotenuse angle

    z1 = hyp_len * 3/4 * sin(angle) + base_height - slant_height;
    z2 = hyp_len / 4 * sin(angle) + base_height - slant_height;

    b1_x_off = slant_width / 4;
    b1_y_off = base_depth / 4;
    b1_z_off = z1;

    b2_x_off = slant_width * 3/4;
    b2_y_off = base_depth / 4;
    b2_z_off = z2;

    b3_x_off = slant_width / 4;
    b3_y_off = base_depth * 3/4;
    b3_z_off = z1;

    b4_x_off = slant_width * 3/4;
    b4_y_off = base_depth * 3/4;
    b4_z_off = z2;

    b_off_x = base_width - bw/2;
    b_off_y = - bd/2;
    
    //fudge an extra ... not quite hight enough?
    b_off_z = bw/2 * sin(angle) + .1;
     
    //button placeholder cubes
    translate([b1_x_off+b_off_x, b1_y_off+b_off_y, b1_z_off+b_off_z])
        rotate([0, angle, 0])
            button_placeholder();

    translate([b2_x_off+b_off_x, b2_y_off+b_off_y, b2_z_off+b_off_z])
        rotate([0, angle, 0])
            button_placeholder();

    translate([b3_x_off+b_off_x, b3_y_off+b_off_y, b3_z_off+b_off_z])
        rotate([0, angle, 0])
            button_placeholder();

     translate([b4_x_off+b_off_x, b4_y_off+b_off_y, b4_z_off+b_off_z])
        rotate([0, angle, 0])
            button_placeholder();
}

module round_tab() {
    difference() {
        color("purple")
            rotate([90,0,0])
                pie_slice(h=base_wall_thickness, 
                    r=tab_diameter, ang=180, anchor=UP);
            translate([0 ,0,tab_hole_height])                       
                rotate([90,0,0])
                    cylinder(h=base_wall_thickness,d=screw_thread_diam);
                
    }
}

module tab_external_hole(hole_thickness=base_wall_thickness) {
    color("purple")
    translate([0,hole_thickness,tab_hole_height])
        rotate([90,0,0])
            cylinder(h=hole_thickness,d=screw_hole_diam);
}

module base_with_cutout() {
    difference() {
        //base box and slant
        slanted_base();

        //cutout bottom of base box and slant
        cut_size_x = (box_width - 2*base_wall_thickness) / box_width;
        cut_size_y = (box_depth - 2*base_wall_thickness) / box_depth;
        cut_size_z = (box_height - base_wall_thickness) / box_height;

        translate([base_wall_thickness,base_wall_thickness,0])
            scale([cut_size_x,cut_size_y,cut_size_z])
                slanted_base();
    }
}

function fit(original) = original * 0.97;
    
module bottom_with_cutout() {

    //testing
    //round_tab()

    color("green")
    translate([0,0,-base_wall_thickness])
        cube([box_width,box_depth,base_wall_thickness]);

    base_move = (2 - fit(1)) * base_wall_thickness;
    
    //cutout bottom of base box and slant
    base_fit_width = fit(box_width - 2*base_wall_thickness);
    base_fit_depth = fit(box_depth - 2*base_wall_thickness);
    base_fit_height = fit(base_wall_thickness/2);
    
    base_in_width = base_fit_width - 2* base_wall_thickness;
    base_in_depth = base_fit_depth - 2* base_wall_thickness;
    base_in_height = base_fit_height;
    
    translate([base_move, base_move, 0])
    difference() {
        cube([base_fit_width, base_fit_depth, base_fit_height]);
        translate([base_wall_thickness,base_wall_thickness,0])
            cube([base_in_width, base_in_depth, base_in_height]);
    }
    translate([box_width/2,base_wall_thickness,0])
        round_tab();
    translate([box_width/2,
        box_depth-3*base_wall_thickness,0])
        round_tab();
    
}

angle = atan(slant_height / slant_width); // Hypotenuse angle

if (top_or_bottom == "template") {
    ph_width = hb_width+s_width+hc_extra;
    ph_depth = hb_depth;
    ph_height = wall_thickness;

    //button placeholder template
    difference() {
        color("purple")
            cube([ph_width, ph_depth, ph_height]);
        translate([0,0,ph_height])
            button_placeholder();
    }
}
else {
    if (top_or_bottom == "top") {

        //rotate to flip over for printing
        translate([0,0,base_height])
        rotate([0,180-angle,0])
        difference() {
        
            //base
            base_with_cutout();

            //cut out button template
            four_buttons();
            
            //holes for screws
            translate([(base_width+slant_width)/2,0,0])
                tab_external_hole();
            translate([(base_width+slant_width)/2,
                base_depth-base_wall_thickness,0])
                tab_external_hole();
        }
    } else {
        //bottom
        bottom_with_cutout();
    }
}
