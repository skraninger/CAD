include <BOSL2/std.scad>

id = 26;
d = 2;
od = id+d;

spiral_h = d/2;
spiral_w = 0.65;
spirals = 5;

function fibonacci(nth) = 
    nth == 0 || nth == 1 ? nth : (
        fibonacci(nth - 1) + fibonacci(nth - 2)
    );

module sector(radius, angles, fn = 24) {
    r = radius / cos(180 / fn);
    step = -360 / fn;

    points = concat([[0, 0]],
        [for(a = [angles[0] : step : angles[1] - 360]) 
            [r * cos(a), r * sin(a)]
        ],
        [[r * cos(angles[1]), r * sin(angles[1])]]
    );

    difference() {
        circle(radius, $fn = fn);
        polygon(points);
    }
}

module arc(radius, angles, width = 1, fn = 24) {
    difference() {
        sector(radius + width, angles, fn);
        sector(radius, angles, fn);
    }
} 

module golden_spiral(from, to, thickness) {
    if(from <= to) {
        f1 = fibonacci(from);
        f2 = fibonacci(from + 1);

        arc(f1, [0, 90], thickness, 48);

        offset = f2 - f1;

        translate([0, -offset, 0]) rotate(90)
            golden_spiral(from + 1, to, thickness);
    }
}

resize([od*.95, od*.95, spiral_h])
union() {
    linear_extrude(1) for(a = [0 : 360 / spirals : 360 - 360 / spirals]) {
        rotate(a) golden_spiral(spiral_h, 6, spiral_w); 
    }

    //Adds the 2nd spiral, as per the comments
    mirror([0, 1, 0]) linear_extrude(1) for(a = [0 : 360 / spirals : 360 - 360 / spirals]) {
        rotate(a) golden_spiral(spiral_h, 6, spiral_w); 
    }
}

tube(h=d, od=od, wall=d);
        
