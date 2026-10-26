include <BOSL2/std.scad>

$fn=180;        //resolution

base_height = 170;
//base_od = 40.8;
base_od = 41.4;
base_wall = 3;
base_id = base_od - (2 * base_wall);
base_fit = 1.00;

tube(h=base_height, od=base_od, wall=base_wall, chamfer1=1.5);