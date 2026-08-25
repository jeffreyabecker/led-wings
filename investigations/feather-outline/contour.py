"""Contour tracing via marching squares (no OpenCV/skimage).

For each 2x2 cell of the mask we compute which of its 4 edges are crossed by the
iso-contour (an edge is crossed when its two corners differ in state), then
connect the crossing points. This is correct *by construction* — no hardcoded
case table to get wrong. The whole segment set is chained into closed loops via
a point-adjacency graph. The largest outer loop of a blob is the feather outline.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
from scipy import ndimage as ndi


def _marching_squares(mask: np.ndarray):
    """Return chained closed loops as lists of (y, x) vertex tuples."""
    h, w = mask.shape
    # Interior crossing points are computed per cell using corner states.
    segs = []

    for i in range(h - 1):
        for j in range(w - 1):
            TL = mask[i, j]
            TR = mask[i, j + 1]
            BL = mask[i + 1, j]
            BR = mask[i + 1, j + 1]

            # edges crossed (midpoint coords in this cell's local frame)
            crossings = []
            if TL != TR:  # top edge
                crossings.append(("top", (i, j + 0.5)))
            if TR != BR:  # right edge
                crossings.append(("right", (i + 0.5, j + 1)))
            if BL != BR:  # bottom edge
                crossings.append(("bottom", (i + 1, j + 0.5)))
            if TL != BL:  # left edge
                crossings.append(("left", (i + 0.5, j)))

            nc = len(crossings)
            if nc == 0:
                continue
            if nc == 2:
                a = crossings[0][1]
                b = crossings[1][1]
                segs.append((a, b))
            elif nc == 4:
                # saddle: pair consecutive edges in circular order consistently
                # order top(0) right(1) bottom(2) left(3)
                order = {e: k for k, (e, _) in enumerate(crossings)}
                # pair top<->right and bottom<->left (even circular grouping)
                pts = {e: p for e, p in crossings}
                segs.append((pts["top"], pts["right"]))
                segs.append((pts["bottom"], pts["left"]))
            else:
                # nc == 1 or 3 shouldn't happen for a binary field; skip conservatively
                pass

    return _chain(segs)


def _chain(segs):
    """Chain segments into closed loops by matching endpoints."""
    adj = defaultdict(list)

    def key(p):
        return (round(p[0], 6), round(p[1], 6))

    for a, b in segs:
        adj[key(a)].append(key(b))
        adj[key(b)].append(key(a))

    used = set()
    loops = []
    for start in list(adj.keys()):
        if start in used:
            continue
        loop = [start]
        used.add(start)
        cur = start
        prev = None
        while True:
            nbrs = [p for p in adj[cur] if p != prev and p not in used]
            if not nbrs:
                break
            nxt = nbrs[0]
            if nxt == start and len(loop) > 2:
                loop.append(start)
                break
            loop.append(nxt)
            used.add(nxt)
            prev, cur = cur, nxt
            if cur == start and len(loop) > 2:
                break
        loops.append(loop)
    return loops


def contour_polygons(mask: np.ndarray) -> list[np.ndarray]:
    """Return ordered (y, x) contour vertex arrays for all contours."""
    pad = np.zeros((mask.shape[0] + 2, mask.shape[1] + 2), dtype=bool)
    pad[1:-1, 1:-1] = mask.astype(bool)
    loops = _marching_squares(pad)
    outs = []
    for loop in loops:
        arr = np.array(loop, dtype=float)
        arr[:, 0] -= 1.0
        arr[:, 1] -= 1.0
        outs.append(arr)
    return outs


def closed_contour(
    mask: np.ndarray,
    largest: bool = True,
    simplify_eps: float = 1.2,
    smooth_k: int = 4,
) -> list[tuple[float, float]]:
    """Return the largest outer contour of a binary blob as an (x, y) polygon."""
    mask = ndi.binary_fill_holes(mask.astype(bool))
    polys = contour_polygons(mask)
    if not polys:
        return []
    if largest:
        polys.sort(key=lambda p: len(p), reverse=True)
    arr = polys[0]  # (y, x)
    pts = [(float(x), float(y)) for (y, x) in arr if len(arr) > 3]
    if len(pts) < 4:
        return pts
    pts = simplify_closed(pts, eps=simplify_eps)
    pts = smooth_closed(pts, k=smooth_k)
    return pts


def simplify_closed(pts: list[tuple[float, float]], eps: float = 1.0) -> list[tuple[float, float]]:
    """Douglas-Peucker on a closed loop (best of several start rotations)."""
    if len(pts) < 4:
        return list(pts)
    closed = pts + [pts[0]]

    def dp(points):
        if len(points) < 3:
            return points
        p0 = np.array(points[0], dtype=float)
        pn = np.array(points[-1], dtype=float)
        seg = pn - p0
        sl = np.hypot(*seg)
        arr = np.array(points, dtype=float)
        if sl == 0:
            dists = np.linalg.norm(arr - p0, axis=1)
        else:
            dists = np.abs(np.cross(seg, arr[1:-1] - p0)) / sl
        idx = int(np.argmax(dists))
        if dists[idx] > eps:
            left = dp(points[: idx + 2])
            right = dp(points[idx + 1 :])
            return left[:-1] + right
        return [points[0], points[-1]]

    best, best_len = None, 10**9
    n = len(closed)
    step = max(1, n // 6)
    for start in range(0, n, step):
        rot = closed[start:] + closed[1 : start + 1]
        simp = dp(rot)
        if len(simp) < best_len:
            best_len, best = len(simp), simp
    return best[:-1] if best else list(pts)


def smooth_closed(pts: list[tuple[float, float]], k: int = 4) -> list[tuple[float, float]]:
    """Circular moving-average smoothing."""
    if len(pts) < k * 2 + 2:
        return list(pts)
    arr = np.array(pts, dtype=float)
    pad = np.vstack([arr[-k:], arr, arr[:k]])
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    x = np.convolve(pad[:, 0], ker, mode="same")[k:-k]
    y = np.convolve(pad[:, 1], ker, mode="same")[k:-k]
    return list(zip(x.tolist(), y.tolist()))
