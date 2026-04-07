$fn = 50;

inch_to_mm = 25.4; //Convert from inches to mm
//roundover = .9;
roundover = 2;

foot_width = 1;
foot_depth = 0.5;
foot_height = 1.25;

fit_offset = 0.075;
bottom_offset = 0.15;

riser_offset = 0.1;

riser_width = foot_width + 2 * riser_offset;
riser_depth = foot_depth + 2 * riser_offset;
riser_height = foot_height + riser_offset;

pocket_width = foot_width + 2 * fit_offset;
pocket_depth = foot_depth + 2 * fit_offset;
pocket_height = riser_offset;

bottom_width = foot_width + 2 * (bottom_offset + riser_offset);
bottom_depth = foot_depth + 2 * (bottom_offset + riser_offset);
bottom_height = bottom_offset;

module riser() {
    difference(){
        cube([riser_width, riser_depth, riser_height]);
        translate([riser_offset-fit_offset,
            riser_offset-fit_offset,
            riser_height - pocket_height])
                cube([pocket_width, pocket_depth, pocket_height]);
    }
    translate([-bottom_offset, -bottom_offset, 0])
        cube([bottom_width, bottom_depth, bottom_height]);
};


minkowski() {
    scale([inch_to_mm, inch_to_mm, inch_to_mm]) riser();
    sphere(d=roundover);
}

//translate([50,0,0])
//minkowski() {
//    scale([inch_to_mm, inch_to_mm, inch_to_mm]) riser();
//    sphere(d=foo);
//}


