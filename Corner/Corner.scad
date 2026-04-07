$fn=100;

ID = 30;
OD = 32;

leg1_len = 30;
leg2_len = 30;

corner_rad = 20;

fin_width = 10;
fin_depth = 35;
fin_height = 2;
fin_leg1 = 20;
fin_leg2 = 30;

module fin(width, depth, height, tleg1, tleg2) {
    cube([width, depth, height]);
    linear_extrude(height)
        polygon([[0,0],[tleg1,0],[0,tleg2]]);
}

module corner(diameter, corner_radius) {
    rotate_extrude(angle=90)
        translate([corner_radius,0,0])
            circle(d=diameter);
}

module corner_legs(diameter, corner_radius, leg1_lenth, leg2_lenth)
{
    //Corner
    corner(diameter, corner_radius);

    //leg1
    translate([corner_radius,0,0])
        rotate([90,0,0])
            cylinder(leg1_lenth, d=diameter);

    //leg2
    translate([-leg2_lenth, corner_radius,0])
        rotate([0,90,0])
            cylinder(leg2_lenth, d=diameter);
}

difference(){
    union() {
        corner_legs(OD, corner_rad, leg1_len, leg2_len);
        translate([(OD-corner_rad)/2,(OD-corner_rad)/2,0])
            rotate([180,180,0])
                translate([0,0,-fin_height/2])
                    fin(fin_width, fin_depth, fin_height,
                        fin_leg1, fin_leg2);
    }
    corner_legs(ID, corner_rad, leg1_len, leg2_len);
}

