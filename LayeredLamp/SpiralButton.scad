include <BOSL2/std.scad>

$fn=180;        //resolution


id = 25.5;
d = 2;

SQsize=d/2;      //cross-section and spacing
SpiralD=(id-d)/2;    //~spiral diameter

module arcscale(i){
    translate([SQsize,00])
        arc(i+SQsize,-1);
    translate([0,00])
        arc(i,1);}
module arc(T,S){
    rotate_extrude(angle=S*180)
        translate([T,00])
            square(SQsize);} 
 
// Using outer/inner diameter bounds
difference(){
    union() {
        //torus(od=id+d, id=id);
        tube(h=d, od=id+d, wall=d/2);
        cylinder(d=id+d,h=d/2);
    }

    for(i=[SQsize:SQsize*2:SpiralD-SQsize]){
        arcscale(i);}
}
