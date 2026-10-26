$fn=180; 	//resolution
SQsize=10;	//cross=section and spacing
SpiralD=100;//~spiral diameter

for(i=[SQsize:SQsize*2:SpiralD-SQsize]){
	arcscale(i);}

module arcscale(i){
	translate([SQsize/2,00])
		arc(i+SQsize,-1);
	translate([-SQsize/2,00])
		arc(i,1);}
module arc(T,S){
	rotate_extrude(angle=S*180)
		translate([T,00])
			square(SQsize);}