include <BOSL2/std.scad>

$fn=180;        //resolution

strip_length = 300;
strip_width = 12.2;
strip_depth = 0.7;
led_width = 6.25;
led_depth = 2;

block_width = 55;
block_depth = 5;

y_shift = -block_depth/2;

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
 
 module ledblock(yshift) {
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

ledblock(y_shift);


rotate([0,0,120])
    translate([-block_width,0,0])
        ledblock(y_shift);
        
translate([block_width,0,0])
    rotate([0,0,-120])
        ledblock(y_shift);
