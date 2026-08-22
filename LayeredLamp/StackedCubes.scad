//StackedCubes Example

x = 10;
y = 7;
z = 3;

function randno(f) = f * (rands(-0.51,0.51,1)[0]); 

function shift(a,f) = ((f*a) - a) / 2.0;

function CubeLayer(n, f=1.0) = [
  [  0 - shift(x,f),  0 - shift(y,f),  n*z ],
  [  0 - shift(x,f),  y + shift(y,f),  n*z ],
  [  x + shift(x,f),  y + shift(y,f),  n*z ],
  [  x + shift(x,f),  0 - shift(y,f),  n*z ]];
  
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

//echo(CubePoints);
//echo(CubeFaces);

polyhedron( CubePoints, CubeFaces );