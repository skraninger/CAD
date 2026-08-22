include <BOSL2/std.scad>
include <BOSL2/threading.scad>

$fn=80;

dish_r = 43;
dish_h = 8;

cap_r = 46;
cap_h = 12;

pie_h = 6;
pie_r = 43;
pie_offset = 2;

sep = 5;

pin_reduce = 1.0;
pin_h = dish_h - pin_reduce;
pin_r = 6;
pin_offset = 0.5;

hole_r = 4;

fit = 1;

fifth = 360/5;

wheel_radius = dish_r;
wheel_height = dish_h;
hole_count = 40;

nib_r = 1.5;
nib_l = 32;
nib_offset = 8;

//type = "screw";
//type = "pin";
type = "magnet";

pin_cut = 0.5;
pin_tip_h = 2;
pin_tip_r = hole_r + 0.5;

magnet_r = 4;
magnet_h = 4;

function break(delta,angle) = [delta*cos(angle), delta*sin(angle), 0 ];

//seed = 125;
seed = 129;
rndx = rands(-1.0, 1.0, hole_count+1, seed);
rndy = rands(-1.0, 1.0, hole_count+1, seed*2);
rndz = rands(-1.0, 1.0, hole_count+1, seed*3);
rndr = rands(-1.0, 1.0, hole_count+1, seed*4);

function notinmiddle(x, y, d) = ! (abs(x) < d && abs(y) < d);

//Cyclintrical nibs at each angle around 360 degrees
module nibs(nib_radius, nib_length, nib_angle, nib_offset) {
    for (a=[0:nib_angle:360]) {
        rotate([90, 0, a])
            translate([0,0,nib_offset])
                cylinder(h=nib_length, r=nib_radius);
    }
}

module cheeze_holes() {
    // Subtractive bubble loop
    for (i = [1 : hole_count]) {
        seed_x = rndx[i] * wheel_radius * 0.85;
        seed_y = rndy[i] * wheel_radius * 0.85;
        seed_z = abs(rndz[i]) * wheel_height;
        
        // Randomize hole radius between 1mm and 6mm
        hole_radius = 1 + abs(rndr[i] * 5);
        
        // Move the bubbles into position and cut them out
        if (notinmiddle(seed_x, seed_y, 10))
            translate([seed_x, seed_y, seed_z])
                sphere(r = hole_radius);
    }
}

module pin(cut=true) {
    difference() {
        union() {
            cylinder(r=hole_r, h=pin_h);
            translate([0,0,pin_h-pin_tip_h])
                cylinder(h=pin_tip_h, r2=hole_r, r1=pin_tip_r);
        }
        if (cut) {
            #translate([-pin_tip_r-0.5,-pin_cut/2,0])
                cube([pin_tip_r*2+1, pin_cut, pin_h]);
        }
    }
}

module magnet() {
    cylinder(h=magnet_h, r=magnet_r);
}

difference() {

    //cylinder(h=cap_h,r=cap_r,center=true);
    cyl(h=cap_h,r=cap_r,center=true, rounding= 2);

    //NO CHEEZE HOLES
    //cheeze_holes();
    
    #translate([0,0,6])
    text3d("Cheeze Shreader", h=2, size=6, center=true, font=":style=bold");
    
    //Nibs
    color("blue")
    rotate([0,0,fifth/4])
        translate([0, 0, (dish_h-nib_r-(cap_h-dish_h))/2])
            nibs(nib_r, nib_l, fifth/2, nib_offset);

    translate([0, 0, -cap_h/2])
    {
        translate([0, 0, dish_h/2])
            cylinder(h=dish_h,r=dish_r+fit,center=true);
        //cyl(h=dish_h,r=dish_r,center=true, rounding=.5);

        color("red")
            translate(break(sep,fifth/2))
                pie_slice(ang=fifth, l=pie_h, r=pie_r);
    }
}

//Add the pin with the threaded hole
//!translate([0,0,-(pin_h/2+(cap_h-dish_h)/2)])
translate([0,0,(cap_h-dish_h)/2-pin_h])
difference() {
    color("blue")
    cylinder(h=pin_h, r=pin_r);
    
    color("red")
    if (type == "screw") {
        rotate([180,0,0])
            threaded_rod(d = 6.35, l = pin_h+1, pitch = 1.27);
    }

    if (type == "pin") {
        scale([1.02,1.02,1])
            pin(false);
    }

    #if (type == "magnet") {
        magnet();
    }
}
