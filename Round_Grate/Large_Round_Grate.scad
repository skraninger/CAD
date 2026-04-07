$fn=100;

Tube_ID = 93;
Tube_OD = 103;
Tube_Length = 40;
Cap_OD = 130;
Cap_Thickness = 8;
Spine_Thickness = 2;
Spine_Count = 36;
Cutout_Count = 10;
Vertical_Cutout = 6.5;
Bridge_Count = 1;

Inner_Radius = 46.5;
Zscale = .6;

Type = "R"; //[R:Radial, V:Vertical]
Inside = "S"; //[S:Sphere, C:Cone]
Generate = "G"; //[G:Grate, T:Tube]

module TubeAndCap(L, OD, ID, C_OD, C_THICK) {
    difference() {
        union() {
            translate([0,0,C_THICK])
                cylinder(h=L, r=OD/2);
            cylinder(h=C_THICK, r=C_OD/2);
        }
        cylinder(h=L+C_THICK, r=ID/2);
    }
}

module HalfCylinder(rad, thick, cut) {
    difference() {
        cylinder(h=thick, r=rad);
        translate([-rad,-rad,0])
            cube([cut,rad*2,thick]);
    }
}

module Spoke(rad, thick) {
    rotate([0,-90,0])
        HalfCylinder(rad, thick, rad);
}
module RoundGrate(num_spokes, rad, thick, c_thick,
    c_od, c_id, ir) {
    difference() {
        union() {
            // create cap
            //translate([0,0,-c_thick]) 
            difference() {
                cylinder(h=c_thick, r=c_od/2);
                cylinder(h=c_thick, r=c_id/2);        
            }

            // create spokes
            for (snum=[1:num_spokes]) {
                rotate( [0, 0, snum*(360/num_spokes)] )
                    Spoke(rad, thick);
            }
        }
        // cutout inner sphere
        if (ir > 0)
            if (Inside == "S") {
                sphere(ir);
            } else {
                cylinder(h=ir*sqrt(2),r1=ir,r2=0);
            }
            
    }
}

module VerticalSpoke(od, thick, bridges) {
    sep = od / (bridges + 1);
    difference() {
        cube([od,thick,od]);
        translate([-thick/2, 0, 0])
            for (snum=[1:bridges]) {
                translate([snum*sep,0,0])
                    cube([thick,thick,od]);
            }
    }    
}

module VerticalGrate(num_spokes, rad, thick, c_thick,
    c_od, c_id, ir, bc) {
        
    cr = c_od / 2;       
    cl = c_id / 2;
        
    sepl = (c_id - thick) / (num_spokes-1);
    //bw = sepl - thick; // bar width
        
    union() {

        // create cap
        difference() {
            cylinder(h=c_thick, r=c_od/2);
            cylinder(h=c_thick, r=c_id/2);        
        }

        // cutout sphere`
        difference() {
            sphere(d=c_od);
            translate([0,0,-cr])
                cube(c_od,center = true);
            
            // top and bottom cutouts
            //translate([-cr,cl-thick,0])
            //    VerticalSpoke(c_od,thick,bc);            
            //translate([-cr,-cl,0])
            //    VerticalSpoke(c_od,thick,bc);            

            //middle cutouts
            translate([-cr,sepl/2,0])
                for (snum=[1:num_spokes]) {
                    translate([0,cl-(snum*sepl),0])
                        VerticalSpoke(c_od,thick,bc);            
                }
                        
            // cutout inner sphere
            if (ir > 0)
                if (Inside == "S") {
                    sphere(ir);
                } else {
                    cylinder(h=ir*sqrt(2),r1=ir,r2=0);
                }
        }   
    }
}

//HalfCylinder(Cap_OD,Spine_Thickness);
//Spoke(Cap_OD,Spine_Thickness);

//VerticalGrate(Cutout_Count,Cap_OD/2,Vertical_Cutout,
//    Cap_Thickness/Zscale, Cap_OD, Tube_ID,
//    Inner_Radius);

//VerticalSpoke(Cap_OD, Vertical_Cutout, 3);


render() {
    if (Generate == "G") {
        if (Type == "R") {
            scale([1, 1, Zscale])
            RoundGrate(Spine_Count,Cap_OD/2,Spine_Thickness,
                Cap_Thickness/Zscale, Cap_OD, Tube_ID,
                Inner_Radius);
        } else {
            scale([1, 1, Zscale])
            VerticalGrate(Cutout_Count,Cap_OD/2,Vertical_Cutout,
                Cap_Thickness/Zscale, Cap_OD, Tube_ID,
                Inner_Radius,Bridge_Count);            
        }
                
    } else {
        //rotate([0,-180,0])
            TubeAndCap(Tube_Length, Tube_OD, Tube_ID, Cap_OD, Cap_Thickness/Zscale);
    }
}


