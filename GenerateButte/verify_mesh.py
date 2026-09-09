# -*- coding: utf-8 -*-
"""Headless watertightness verifier for the butte generators.

Usage:
    python verify_mesh.py <module> [style] [shell_mm] [resolution]
    e.g.  python verify_mesh.py GenerateButteV15 Sandstone 5.0 130
          python verify_mesh.py GenerateButteV16 Granite 5.0 130

Imports the named module from this directory, regenerates the grid with the
module's engine, rebuilds the facet list in memory using the module's own STL
writer logic (via its write function pointed at a temp file is NOT used here --
we re-derive facets by calling the module's writer into a BytesIO-free path),
then checks:
  * open edges        (shared by exactly 1 facet)  -> must be 0
  * non-manifold edges (shared by >2 facets)       -> must be 0
  * connected components over vertices             -> must be 1
  * signed volume sign/winding consistency         -> should be > 0 (outward)
  * inner-above-outer node count                   -> negative wall thickness risk

The module must expose:
  generate_custom_border_butte(style, tw, th, sf, tb, ts, tt, stt, bp, st,
                               resolution=..., seed=...)  -> 7-tuple
  and either write_contour_binary_stl(...) (V15 signature) or an equivalent.
To keep this generic, the facet list is rebuilt here with the same rules as the
module's writer; if the module changes its writer internals, update build_facets
below to match (or have the module expose a build_facets function and use it).
"""
import importlib
import os
import sys
import tempfile
from collections import Counter, defaultdict

import numpy as np


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


def analyze(facets, label):
    def key(p):
        return (round(float(p[0]), 4), round(float(p[1]), 4), round(float(p[2]), 4))

    edge_count = Counter()
    vert_edges = defaultdict(set)
    for f in facets:
        a, b, c = (key(f[0]), key(f[1]), key(f[2]))
        for u, v in ((a, b), (b, c), (c, a)):
            e = (u, v) if u < v else (v, u)
            edge_count[e] += 1
            vert_edges[u].add(v)
            vert_edges[v].add(u)

    open_edges = sum(1 for c in edge_count.values() if c == 1)
    nonmanifold = sum(1 for c in edge_count.values() if c > 2)

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

    ok = (open_edges == 0) and (nonmanifold == 0) and (comps == 1)
    print(f"[{label}] facets={len(facets)} edges={len(edge_count)} "
          f"open={open_edges} nonmanifold={nonmanifold} components={comps} "
          f"vol={vol:.1f} => {'PASS' if ok else 'FAIL'}")
    return ok


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

    # Prefer a module-exposed facet builder if present (V16+), else V15 replica.
    if hasattr(mod, "build_facets"):
        facets = mod.build_facets(X, Y, Z, Xi, Yi, Zi, mask, shell)
    else:
        facets = build_facets_v15(X, Y, Z, Xi, Yi, Zi, mask, shell)

    ok = analyze(facets, f"{mod_name} {style} shell={shell} res={res}")

    if shell > 0:
        over = (Zi > Z + 1e-6) & mask
        print(f"inner-above-outer nodes: {int(over.sum())} "
              f"({'OK' if over.sum() == 0 else 'NEGATIVE WALL THICKNESS RISK'})")

    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
