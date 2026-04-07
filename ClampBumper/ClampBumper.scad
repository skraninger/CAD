include <BOSL2/std.scad>
$fn=80;

thickness = 3.4;

outer_width = 61.2;
outer_depth = 44.5;
outer_height = 11.4;
outer_radius = 10;

inner_width = 52;
inner_depth = 28.5;
inner_height = outer_height - thickness;
inner_radius = 7;

cut_width = outer_width - thickness;
cut_depth = outer_depth - 2*thickness;
cut_height = outer_height - 2*thickness;
cut_radius = outer_radius-thickness;

difference() {
    cuboid([outer_width,outer_depth,outer_height],
        rounding=outer_radius,edges=[FRONT+LEFT,BACK+LEFT]);
    
    translate([(outer_width-inner_width)/2,0,thickness])    
            cuboid([inner_width,inner_depth,inner_height],
                rounding=inner_radius,edges=[FRONT+LEFT,BACK+LEFT]);

    translate([thickness,0,0])
        cuboid([cut_width,cut_depth,cut_height],
           rounding=cut_radius,edges=[FRONT+LEFT,BACK+LEFT]);
}
