include <BOSL2/std.scad>

$fn=180;        //resolution

one_led_length = 16.5;
led_per_side = 13;
strip_length = led_per_side * one_led_length;
strip_width = 12.2;
strip_depth = 0.7;
led_width = 6.25;
led_depth = 2;

block_width = 45;
block_depth = 6;

y_shift = -block_depth/2;

part = "base"; //[base,top,lightpole]

block_type = "triangular"; //[triangular,square]
t_block_width = 60;

//polygon
//    TW = led_width
//    --
//   |  | TD = led_depth
// --    --
//|        | BD = strip_depth
// --------  left edge = (0,0)
//    BW = strip_width

TW = led_width;
TD = led_depth;
BW = strip_width;
BD = strip_depth;

points = [[0,0],[BW,0],
 [BW,BD],[(BW+TW)/2,BD],
 [(BW+TW)/2,TD],[(BW-TW)/2,TD],
 [(BW-TW)/2,BD],[0,BD]];
 
base_height = 27;
base_od = 88;
base_wall = 3;
base_id = base_od - (2 * base_wall);
base_fit = 1.00;
 
 module ledblock(block_width, yshift) {
    translate([0,yshift,0])
    union() {
        difference() {
            cube([block_width,block_depth,strip_length]);
            #translate([(block_width-strip_width)/2,
                block_depth-led_depth,0])
                linear_extrude(strip_length) polygon(points);
         }
         //add cylinders on each end
         translate([0,block_depth/2,0])
            cylinder(h=strip_length, d=block_depth);
         translate([block_width,block_depth/2,0])
            cylinder(h=strip_length, d=block_depth);
    }
}

// Triangular
module triangular_block() {
    translate([-t_block_width/2,sin(60)*block_width/2,0]) {
        ledblock(t_block_width,y_shift);

        rotate([0,0,120])
            translate([-t_block_width,0,0])
                ledblock(t_block_width, y_shift);
                
        translate([t_block_width,0,0])
            rotate([0,0,-120])
                ledblock(t_block_width, y_shift);
    }
}

// Square
module square_block() {
    translate([-block_width/2,block_width/2,0]) {
        ledblock(block_width, y_shift);

        rotate([0,0,90])
            translate([-block_width,0,0])
                ledblock(block_width, y_shift);
                
        translate([block_width,0,0])
            rotate([0,0,-90])
                ledblock(block_width, y_shift);

        translate([block_width,-block_width,0,])
            rotate([0,0,-180])
                ledblock(block_width, y_shift);
    }
}

module round_base() {
    translate([0,0,base_height/2])
    tube(h=base_height, od=base_od, wall=base_wall,chamfer1=1.5);
    cylinder(h=base_wall, d=base_od-base_wall);
}

if (part == "lightpole") {
    if (block_type == "triangular") {
        triangular_block();
    }

    if (block_type == "square") {
        square_block();
    }
}

if (part == "base") {
    difference() {
        round_base();
        if (block_type == "triangular")
            scale([base_fit,base_fit,1]) hull() triangular_block();
        else
            scale([base_fit,base_fit,1]) hull() square_block();
    }
}

if (part == "top") {

}

