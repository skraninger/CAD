dist=4;
r=4;
thick=2;
height=5;

turns=5;
deg=360 * turns;

points=[for(i=[0:deg])let(r=r+i/360*dist)[cos(i),sin(i)]*r];
points2=[for(i=[deg:-1:0])let(r=r-thick+i/360*dist)[cos(i),sin(i)]*r];

linear_extrude(height)
polygon(concat(points,points2));