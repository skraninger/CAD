include <BOSL2/std.scad>
include <BOSL2/threading.scad>
$fn=80;
th_od = 25;
th_id = 18.1;
th_len = 29;
th_pitch = 5.8;
th_depth = (th_od - th_id) / 2;
th_turns = th_len / th_pitch;

cyl_length = 38;
cyl_hole = 13;

grip_stop = 1.5;
grip_len = 14;
grip_diameter = 30;

bottom_len = 7;
bottom_diameter = 49;

thread_helix(d=th_id, pitch=th_pitch,
    thread_depth=th_depth, flank_angle=20, turns=th_turns);

difference() {
    cyl(h=cyl_length, r=th_id/2, center=true, rounding=1.5);
    cyl(h=cyl_length+10, r=cyl_hole/2, center=true);
}

down(th_len/2+grip_len/2-grip_stop)
regular_prism(n=8,h=grip_len+grip_stop, r=grip_diameter/2, center=true);

down(th_len/2+grip_len/2+bottom_len/2)
regular_prism(n=8,h=bottom_len,
    r=bottom_diameter/2, center=true, rounding=1.5);
