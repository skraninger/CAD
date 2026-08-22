include <BOSL2/std.scad>

$fn=80;

cap_r = 46;
cap_h = 12;
bottom_h = 6;

dish_r = 43;
dish_h = 8;

pie_h = 6;
pie_r = 43;
pie_z = -pie_h/2 + (dish_h-pie_h)/2;

sep = 5;

hole_r = 4;

pin_h = dish_h;
pin_r = 6;
pin_offset = 0.5;

nib_r = 1.5;
nib_l = 32;
nib_offset = 8;

fifth = 360/5;

wheel_radius = dish_r;
wheel_height = dish_h;
hole_count = 40;

//type = "screw";
//type = "pin";
type = "magnet";

pin_cut = 0.5;
pin_tip_h = 2;
pin_tip_r = hole_r + 0.5;

magnet_r = 4;
magnet_h = 4;

//seed = 125;
seed = 129;
rndx = rands(-1.0, 1.0, hole_count+1, seed);
rndy = rands(-1.0, 1.0, hole_count+1, seed*2);
rndz = rands(-1.0, 1.0, hole_count+1, seed*3);
rndr = rands(-1.0, 1.0, hole_count+1, seed*4);

function break(delta,angle,z=0) = [delta*cos(angle), delta*sin(angle), z];

//Cyclintrical nibs at each angle around 360 degrees
module nibs(nib_radius, nib_length, nib_angle, nib_offset) {
    for (a=[0:nib_angle:360]) {
        rotate([90, 0, a])
            translate([0,0,nib_offset])
                cylinder(h=nib_length, r=nib_radius);
    }
}
 
function notinmiddle(x, y, d) = ! (abs(x) < d && abs(y) < d);

module cheeze_holes() {
    // Subtractive bubble loop
    for (i = [1 : hole_count]) {
        seed_x = rndx[i] * wheel_radius * 0.85;
        seed_y = rndy[i] * wheel_radius * 0.85;;
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
    color("green")
        cylinder(h=magnet_h, r=magnet_r);
}

difference() {

//Main cylinder
cylinder(h=dish_h,r=dish_r,center=true);
//cyl(h=dish_h,r=dish_r,center=true, rounding=.5);

//Cutout for the pin
cylinder(h=dish_h,r=pin_r+pin_offset,center=true);

//Pie cutouts 1-5
color("red")
    translate(break(sep,fifth/2,pie_z))
        pie_slice(ang=fifth, l=pie_h, r=pie_r);

color("blue")
    translate(break(sep,fifth/2+fifth,pie_z))
        pie_slice(ang=fifth, l=pie_h, r=pie_r, spin=fifth);

color("yellow")
    translate(break(sep,fifth/2+fifth*2,pie_z))
        pie_slice(ang=fifth, l=pie_h, r=pie_r, spin=fifth*2);

color("green")
    translate(break(sep,fifth/2+fifth*3,pie_z))
        pie_slice(ang=fifth, l=pie_h, r=pie_r, spin=fifth*3);

color("violet")
    translate(break(sep,fifth/2+fifth*4,pie_z))
        pie_slice(ang=fifth, l=pie_h, r=pie_r, spin=fifth*4);

//NO CHEEZE HOLES
//translate([0, 0, -(dish_h+bottom_h)/2-3])
//    cheeze_holes();

}

//Nibs
rotate([0,0,fifth/4])
    translate([0, 0, (dish_h-nib_r)/2])
        nibs(nib_r, nib_l, fifth, nib_offset);

//Bottom with hole
difference() {
    translate([0, 0, -(dish_h+bottom_h)/2])
        cyl(h=bottom_h, r=cap_r, center=true, rounding=2);
    
    if (type == "screw")
        translate([0, 0, -(dish_h+bottom_h)/2])
            cylinder(h=bottom_h, r=hole_r, center=true);
    
    if (type == "magnet")
        #translate([0, 0, -(dish_h+bottom_h+magnet_h/2)/2])
            magnet();

//NO CHEEZE HOLES            
//    translate([0, 0, -(dish_h+bottom_h)/2-3])
//        cheeze_holes();

    #translate([0,0,-9.5])
        rotate([180,0,0])
        text3d("Cheeze Shreader", h=2, size=6,
            center=true, font=":style=bold");
}

if (type == "pin")
    translate([0, 0, -(dish_h)/2])
        pin();
    
