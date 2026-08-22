include <BOSL2/std.scad>


//StackedCubes
//Number of layers
layers = 27;

x = 50;
y = 50;
z = 6;

stack_height = (layers-1) * z;

slot_w = 11;
slot_d = 3.5;
slot_h = stack_height+z;
slot_offset = (y / 2) - 13;

random_range = 0.25;

bottom_size = [120,120,40];
bottom_chamfer = 5;
bottom_inside = [95,95,25];

type = "lamp"; // [lamp,pin,bottom]
//type = "bottom"; // [lamp,pin,bottom]

//Randoms with no seed:
//
function randno(f) = f * (rands(0-random_range,random_range,1)[0]); 
function randplus(f) = f * (rands(0,random_range,1)[0]); 
function randminus(f) = f * (rands(0-random_range,0,1)[0]); 
function randalt(f,i) = (i%2==0)?randplus(f):randminus(f);

//Randoms with seed:
//
randcount = (layers+1)*4;

//Lamp-1
//randseed = 123458;
//Lamp-2
//randseed = 123461;
//Lamp-3
//randseed = 123471;
//Lamp-4
randseed = 123476;


//randslist = rands(0-random_range,random_range,randcount,randseed);
randslistp = rands(0,random_range,randcount,randseed);
randslistm = rands(0-random_range,0,randcount,randseed);

function randnol(f,n) = f * randlist[n]; 
function randplusl(f,n) = f * randslistp[n]; 
function randminusl(f,n) = f * randslistm[n]; 
function randaltl(f,i,n) = (i%2==0)?randplusl(f,n):randminusl(f,n);

function shift(a,f) = ((f*a) - a) / 2.0;

function CubeLayer(n, f=1.0) = [
  [  0 - shift(x,f),  0 - shift(y,f),  n*z ],
  [  0 - shift(x,f),  y + shift(y,f),  n*z ],
  [  x + shift(x,f),  y + shift(y,f),  n*z ],
  [  x + shift(x,f),  0 - shift(y,f),  n*z ]];
  
function CubeLayerR(n,f1=1.0,f2=1.0,f3=1.0,f4=1.0) = [
  [  0 - shift(x,f1),  0 - shift(y,f1),  n*z ],
  [  0 - shift(x,f2),  y + shift(y,f2),  n*z ],
  [  x + shift(x,f3),  y + shift(y,f3),  n*z ],
  [  x + shift(x,f4),  0 - shift(y,f4),  n*z ]];

function CubeLayerR2(n,
    xf1=1.0,xf2=1.0,xf3=1.0,xf4=1.0,
    yf1=1.0,yf2=1.0,yf3=1.0,yf4=1.0) = [
  [  0 - shift(x,xf1),  0 - shift(y,yf1),  n*z ],
  [  0 - shift(x,xf2),  y + shift(y,yf2),  n*z ],
  [  x + shift(x,xf3),  y + shift(y,yf3),  n*z ],
  [  x + shift(x,xf4),  0 - shift(y,yf4),  n*z ]];

//No top
function CubeFacesB(n) = [
  [n+0,n+1,n+2,n+3]]; // bottom
  
//No bottom or top
function CubeFacesL(n) = [
  [n+4,n+5,n+1,n+0],  // front
  [n+5,n+6,n+2,n+1],  // right
  [n+6,n+7,n+3,n+2],  // back
  [n+7,n+4,n+0,n+3]]; // left

//No bottom
function CubeFacesT(n) = [
  [n+7,n+6,n+5,n+4]]; // Top


/* ORIGINAL EXAMPLE USED TO TEST
CubePoints = concat(
    CubeLayer(0), //Bottom
    CubeLayer(1, 1 + randno(1)),
    CubeLayer(2, 1 + randno(1)),
    CubeLayer(3, 1 + randno(1))); //Top

CubeFaces = concat(
    CubeFacesB(0),
    CubeFacesL(0),
    CubeFacesL(1*4),
    CubeFacesL(2*4),
    CubeFacesT(2*4));

polyhedron( CubePoints, CubeFaces );
*/

module pin_8() {
    hull() {
        translate([0,0,5])
        regular_prism(8, side1=2, side2=0.1, h=3);

        translate([0,0,-5])
        regular_prism(8, side1=0.1, side2=2, h=3);
    }
}

module make_pin() {
    rotate([90,22.5,0])
        pin_8();
}

function flatten(l) = [ for (a = l) for (b = a) b ] ;

//Points at the top should be the same as the bottom for stacking
//For now, bottom and top are not random, but square
//
AllPoints = concat(CubeLayer(0),
    flatten([for(i=[1:layers-2])(
        CubeLayerR(i,
            1 + randaltl(1,i,i*4),
            1 + randaltl(1,i,i*4+1),
            1 + randaltl(1,i,i*4+2),
            1 + randaltl(1,i,i*4+3)))]
        ),
        CubeLayer(layers-1)
    );

AllFaces = concat(CubeFacesB(0), CubeFacesL(0),
    flatten([for(i=[1:layers-2])(CubeFacesL(4*i))]),
    CubeFacesT((layers-2)*4));
    
//echo(AllPoints);
//echo(AllFaces);

if (type == "lamp") {
difference(){
    minkowski() {
        translate([-x/2,-y/2,0])
        polyhedron( AllPoints, AllFaces );
        sphere(0.5);
    }

    #color("green")
        translate([-slot_w/2,-slot_d/2+slot_offset,-1])
            cube([slot_w, slot_d, slot_h]);
    
    #color("red")
        scale([2,2,2])
            pin_8();
    }
    
    #color("red")
        translate([0,0,stack_height])
        scale([2,2,2])
            pin_8();
}

if (type == "pin")
    scale([2,2,2])
        make_pin();
        
if (type == "bottom")
    difference() {
        translate([0,0,-bottom_size[2]/2])
            cuboid(bottom_size,chamfer=bottom_chamfer);
        #translate([0,0,
            -bottom_inside[2]/2
            -(bottom_size[2]-bottom_inside[2])])
            cube(bottom_inside,center=true);
        #color("red")
            scale([2,2,2])
                pin_8();        
    }

    
    