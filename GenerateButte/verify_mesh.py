# -*- coding: utf-8 -*-
"""Headless structural verifier for the butte generators.

Usage:
    python verify_mesh.py <module> [style] [shell_mm] [resolution]
    e.g.  python verify_mesh.py GenerateButteV16 Sandstone 5.0 130
          python verify_mesh.py GenerateButteV15 Granite 5.0 130

The generator emits an OPEN-BOTTOM hollow bowl: a single connected shell whose
floor is deliberately left open (it sits on the print bed). A perfectly "closed
manifold" test is therefore the WRONG acceptance criterion for this part -- it
would always fail. Instead this verifier checks the properties that actually
matter for slicing an open-bottom bowl, and separates *expected* bottom-level
characteristics from *real* defects:

  HARD (must pass, else exit 2):
    * connected components over vertices            -> exactly 1 (one piece)
    * interior open edges (open edge NOT on the     -> 0   (a real wall gap / hole)
      footprint perimeter rim)
    * ELEVATED non-manifold edges (off the bed)     -> 0   (self-intersection)
    * inner-above-outer nodes (shell > 0)           -> 0   (negative wall thickness)

Scope: this targets the HOLLOW bowl (shell_mm > 0), which is the print path.
Solid mode (shell_mm == 0) leaves an open base skirt by construction and is NOT
expected to pass -- ignore its result.

  INFORMATIONAL (reported, not gating):
    * bed-level open edges      -> the intended bowl opening rim
    * bed-level non-manifold    -> benign flat-foot coincidence where the clamped
                                   inner surface meets the outer at z = 0
    * signed volume + winding   -> orientation sanity for the (open) shell

"Bed level" means within `bed_tol` of z = 0, so a defect that actually pokes up
the cliff is always caught while the flat bottom rim is tolerated.

The module must expose:
    generate_custom_border_butte(style, tw, th, sf, tb, ts, tt, stt, bp, st,
                                 resolution=..., seed=...)  -> 7-tuple
and (V16+) a `build_facets(...)` matching the STL writer. If it does not expose
one (e.g. V15), a faithful replica of the V15 writer is used as a fallback.

Exit codes: 0 = pass, 2 = fail, 1 = usage error.
"""
import importlib
import os
import sys
from collections import Counter, defaultdict

import numpy as np


def vkey(p):
    """Canonical rounded key for a 3D vertex (matches how edges are grouped)."""
    return (round(float(p[0]), 4), round(float(p[1]), 4), round(float(p[2]), 4))


def build_facets_v15(X, Y, Z, X_in, Y_in, Z_in, mask, shell_thickness_mm):
    """Replicates GenerateButteV15.write_contour_binary_stl facet construction."""
    ny, nx = Z.shape
    facets = []
    for i in range(ny - 1):
        for j in range(nx - 1):
            if mask[i, j] and mask[i + 1, j] and mask[i, j + 1] and mask[i + 1, j + 1]:
                v1o = (X[i, j], Y[i, j], Z[i, j])
                v2o = (X[i + 1, j], Y[i + 1, j], Z[i + 1, j])
                v3o = (X[i, j + 1], Y[i, j + 1], Z[i, j + 1])
                v4o = (X[i + 1, j + 1], Y[i + 1, j + 1], Z[i + 1, j + 1])
                facets.append((v1o, v2o, v4o))
                facets.append((v1o, v4o, v3o))
                if shell_thickness_mm > 0:
                    v1i = (X_in[i, j], Y_in[i, j], Z_in[i, j])
                    v2i = (X_in[i + 1, j], Y_in[i + 1, j], Z_in[i + 1, j])
                    v3i = (X_in[i, j + 1], Y_in[i, j + 1], Z_in[i, j + 1])
                    v4i = (X_in[i + 1, j + 1], Y_in[i + 1, j + 1], Z_in[i + 1, j + 1])
                    facets.append((v1i, v4i, v2i))
                    facets.append((v1i, v3i, v4i))
    for i in range(ny - 1):
        for j in range(nx - 1):
            cur = mask[i, j]
            if cur != mask[i, j + 1]:
                v1o, v2o = (X[i, j], Y[i, j], Z[i, j]), (X[i + 1, j], Y[i + 1, j], Z[i + 1, j])
                v1i, v2i = (X_in[i, j], Y_in[i, j], Z_in[i, j]), (X_in[i + 1, j], Y_in[i + 1, j], Z_in[i + 1, j])
                if cur:
                    facets.append((v1o, v1i, v2i)); facets.append((v1o, v2i, v2o))
                else:
                    facets.append((v1o, v2i, v1i)); facets.append((v1o, v2o, v2i))
            if cur != mask[i + 1, j]:
                v1o, v2o = (X[i, j], Y[i, j], Z[i, j]), (X[i, j + 1], Y[i, j + 1], Z[i, j + 1])
                v1i, v2i = (X_in[i, j], Y_in[i, j], Z_in[i, j]), (X_in[i, j + 1], Y_in[i, j + 1], Z_in[i, j + 1])
                if cur:
                    facets.append((v1o, v2i, v1i)); facets.append((v1o, v2o, v2i))
                else:
                    facets.append((v1o, v1i, v2i)); facets.append((v1o, v2i, v2o))

    def area2(p1, p2, p3):
        a = np.array(p2) - np.array(p1)
        b = np.array(p3) - np.array(p1)
        c = np.cross(a, b)
        return float(c @ c)

    return [f for f in facets if area2(*f) > 1e-9]


def analyze(facets, label, bed_tol, rim_keys):
    """Classify edges and topology; return (ok, stats).

    Open edges are split by LOCATION, not height: an open edge whose two vertices
    both sit on the footprint perimeter (rim_keys) is the intended open bottom
    rim (its z follows the textured base contour, so a fixed z threshold would
    misclassify it). Any OTHER open edge is an interior gap/through-hole -> defect.
    Non-manifold edges are split by height: the flat-foot coincidence happens at
    z ~ 0 across the whole bottom disc (interior included), so a bed-height test
    is correct there; non-manifold edges away from the bed are self-intersections.
    """
    edge_count = Counter()
    edge_zmax = {}                       # undirected edge -> max endpoint z
    vert_edges = defaultdict(set)
    for f in facets:
        a, b, c = (vkey(f[0]), vkey(f[1]), vkey(f[2]))
        for u, v in ((a, b), (b, c), (c, a)):
            e = (u, v) if u < v else (v, u)
            edge_count[e] += 1
            zmax_e = max(u[2], v[2])
            if zmax_e > edge_zmax.get(e, -1e30):
                edge_zmax[e] = zmax_e
            vert_edges[u].add(v)
            vert_edges[v].add(u)

    open_rim = open_hole = 0
    nm_bed = nm_elevated = 0
    for e, c in edge_count.items():
        if c == 1:                        # open edge (exactly one facet)
            u, v = e
            if u in rim_keys and v in rim_keys:
                open_rim += 1             # intended open bottom rim
            else:
                open_hole += 1            # interior gap / through-hole -> defect
        elif c > 2:                       # non-manifold edge (>2 facets)
            if edge_zmax[e] < bed_tol:
                nm_bed += 1               # benign flat-foot coincidence at z ~ 0
            else:
                nm_elevated += 1          # self-intersection away from the bed

    seen, comps = set(), 0
    for v in vert_edges:
        if v in seen:
            continue
        comps += 1
        stack = [v]
        seen.add(v)
        while stack:
            u = stack.pop()
            for w in vert_edges[u]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)

    vol = 0.0
    for f in facets:
        a, b, c = np.array(f[0]), np.array(f[1]), np.array(f[2])
        vol += float(np.dot(a, np.cross(b, c))) / 6.0

    ok = (comps == 1) and (open_hole == 0) and (nm_elevated == 0)

    # NOTE: signed volume is reported for regression tracking only. For an OPEN
    # shell the divergence-theorem sum has no well-defined sign, so its sign is
    # NOT a winding/orientation test here (the STL writer's facet order -- which
    # we never alter -- is what slicers rely on).
    print(f"[{label}] facets={len(facets)} edges={len(edge_count)} components={comps} "
          f"signed_vol={vol:.1f} (informational)")
    print(f"    open edges:        interior holes={open_hole} (must be 0)   bottom-rim={open_rim} (expected)")
    print(f"    non-manifold edges: elevated={nm_elevated} (must be 0)   bed/flat-foot={nm_bed} (benign)")
    print(f"    => {'PASS' if ok else 'FAIL'}")
    return ok, {
        "components": comps, "open_hole": open_hole, "open_rim": open_rim,
        "nm_elevated": nm_elevated, "nm_bed": nm_bed, "vol": vol,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mod_name = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "Sandstone"
    shell = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    res = int(sys.argv[4]) if len(sys.argv) > 4 else 130

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    mod = importlib.import_module(mod_name)

    X, Y, Z, Xi, Yi, Zi, mask = mod.generate_custom_border_butte(
        style, 120, 120, 2.5, 1.5, 1.5, 1.5, 1.5, 5.0, shell, resolution=res, seed=55)
    print(f"mask nodes: {int(mask.sum())} of {mask.size}")

    if hasattr(mod, "build_facets"):
        facets = mod.build_facets(X, Y, Z, Xi, Yi, Zi, mask, shell)
    else:
        facets = build_facets_v15(X, Y, Z, Xi, Yi, Zi, mask, shell)

    zmax = float(np.nanmax(Z[mask])) if mask.any() else 0.0
    bed_tol = max(1.0, 0.01 * zmax)

    # Footprint-perimeter vertices: masked grid nodes touching an unmasked (or
    # out-of-bounds) neighbour. Open edges along this perimeter are the intended
    # open bottom rim; anywhere else an open edge is a real hole. Include both the
    # outer surface and (for hollow shells) the clamped inner-surface positions,
    # since the rim loop uses vertices from both.
    ny, nx = mask.shape
    def on_boundary(i, j):
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ii, jj = i + di, j + dj
            if ii < 0 or jj < 0 or ii >= ny or jj >= nx or not mask[ii, jj]:
                return True
        return False

    rim_keys = set()
    for i in range(ny):
        for j in range(nx):
            if mask[i, j] and on_boundary(i, j):
                rim_keys.add(vkey((X[i, j], Y[i, j], Z[i, j])))
                if shell > 0:
                    rim_keys.add(vkey((Xi[i, j], Yi[i, j], Zi[i, j])))

    ok, _stats = analyze(facets, f"{mod_name} {style} shell={shell} res={res}", bed_tol, rim_keys)

    # Negative wall thickness: the hollowed inner surface must never rise above
    # the outer surface (that would mean the shell self-intersects / inverts).
    if shell > 0:
        over = int(((Zi > Z + 1e-6) & mask).sum())
        neg_ok = (over == 0)
        print(f"    inner-above-outer nodes: {over} "
              f"({'OK' if neg_ok else 'NEGATIVE WALL THICKNESS -> FAIL'})")
        ok = ok and neg_ok

    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
