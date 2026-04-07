include <BOSL2/std.scad>
include <BOSL2/threading.scad>
$fn=80;
th_od = 42.83;
th_id = 40.4;
th_len = 19.5;
th_pitch = 6.3;
th_depth = (th_od - th_id) / 2;
th_turns = th_len / th_pitch;

angle = 45;

cyl_length = 38;
cyl_hole = 13;

grip_stop = 1.5;
grip_len = 14;
grip_diameter = 30;

top_length = 22;
top_diameter = 55;

topround = 5;
roundedge = 1.5;

tophole = 10;

thread_helix(d=th_id, pitch=th_pitch,
    thread_depth=th_depth, flank_angle=angle, turns=th_turns);

up(roundedge)
cyl(h=cyl_length, r=th_id/2, center=true, rounding=roundedge);

difference() {
    up(top_length/2+cyl_length/2)
    rotate_sweep(
        arc(r=top_diameter/2,angle=[-30,30],n=45),
        caps=true, texture="diamonds",
        tex_size=[5,5], tex_depth=1,
        tex_taper=0, convexity=10);

    //up(top_length/2+cyl_length/2)
    //cyl(h=top_length, r=top_diameter/2, center=true, rounding=topround);

    up(top_length/2+cyl_length/2)
    rotate([90,0,0])
    regular_prism(n=4,h=top_diameter*2, r=tophole/2, center=true);

}
    
/*
down(th_len/2+grip_len/2-grip_stop)
regular_prism(n=8,h=grip_len+grip_stop, r=grip_diameter/2, center=true);

down(th_len/2+grip_len/2+bottom_len/2)
regular_prism(n=8,h=bottom_len,
    r=bottom_diameter/2, center=true, rounding=1.5);
*/