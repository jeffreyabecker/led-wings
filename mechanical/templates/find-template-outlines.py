#!/usr/bin/env python3
"""Find as-built feather-template outlines on the printed 24x36" grid background.

For each de-skewed photo this script:

  1. calibrates against the printed ruler -- px-per-inch measured *separately* in
     X and Y (see "Why two calibration axes" below);
  2. segments the cardboard / tape templates from the printed background;
  3. extracts one outer outline polygon per template;
  4. measures each outline in physical units (cm);
  5. writes an overlay PNG, a mask PNG, a 1:1 SVG, polygons in JSON, and a
     measurement CSV.

Usage
-----
    python find-template-outlines.py                          # every image
    python find-template-outlines.py --images "S1-5.jpg"      # one image
    python find-template-outlines.py --px-per-inch 100        # skip calibration
    python find-template-outlines.py --px-per-inch 101.8,112  # per-axis override
    python find-template-outlines.py --split                  # split touching parts

Layout
------
    as-built/
      source-images/     the photos (raw/ = camera originals, unskewed/ = de-skewed)
      labels.csv         image,index -> feather label, transcribed from the marks
      outlines/          OUTPUT, tracked:   <stem>.svg / <stem>.json, outlines.json,
                         calibration.json, templates-measured.csv
      scratch/           OUTPUT, ignored:   <stem>.overlay.png / .gridcheck.png / .mask.png

Geometry (SVG + JSON + CSV) is small, textual and worth versioning, so it goes to
outlines/. The rasters are ~15 MB each and fully regenerable, so they go to scratch/.

Each SVG carries one black outline path per template (`<g id="outlines">`, stroke 0.5)
plus the feather-code labels. The outline is a smooth cubic-Bezier idealisation of the
detected edge, not a faithful trace of it: see fit_closed_beziers for why the tolerance is
the smoothing lever. Tune with --fit-mm; --no-smooth falls back to the raw RDP polyline.

--feathers additionally writes ONE self-contained SVG per feather
(as-built/scratch/feathers/<label>.svg) with the source photo crop embedded under the
outline, for hand-tweaking in a vector editor. These share the sheet's mm frame, so a
tweaked path keeps its absolute position. An existing file that differs is left untouched
(--feather-force overrides) so hand edits are not silently regenerated over.

NOTE the measurements (templates-measured.csv / the JSON) are still computed from the RDP
polygon, not from the smooth curve, so the drawn outline sits up to ~1.5 mm away from the
reported width. That is deliberate -- switching the measurement source would change
length/width/area, and since detection indices are assigned by area it could renumber
templates and invalidate as-built/labels.csv.

Why two calibration axes
-----------------------
These photos are *not* metrically rectified. Measured against the printed ruler:

    P1-6_B1-5.jpg            101.83 px/in X    112.24 px/in Y   (+11% stretch Y)
    S1-6.jpg                 105.08 px/in X     94.63 px/in Y   (-10% squash Y)
    SC1-8_A1-4_...jpg        107.21 px/in X    106.02 px/in Y   ( -1% )

so a single px/inch figure would corrupt every across-feather width. The two axes
are therefore measured independently and all geometry is done in physical units.

Detection
---------
Templates are saturated (cardboard hue ~14 sat ~91, blue tape hue ~110 sat ~130)
against a near-neutral printed sheet (sat 15-22), so saturation separates them
cleanly without touching the dark checkerboard patch or the printed ink. The
printed grid has 1" numbered cells, a 1/4" dot grid and 3/4" checkerboard patches.

Caveat: a *white paper* template has the same saturation as the sheet and is NOT
found by the default pass; the expected count parsed from the filename is reported
so the shortfall is visible. --pale adds a best-effort brightness pass (expect false
positives; verify the overlay).
"""
from __future__ import annotations

import argparse
import base64
import csv
import glob
import json
import math
import os
import re
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AS_BUILT = os.path.join(HERE, "as-built")
DEFAULT_IN = os.path.join(AS_BUILT, "source-images", "unskewed")
DEFAULT_OUT = os.path.join(AS_BUILT, "outlines")     # tracked: geometry + measurements
DEFAULT_SCRATCH = os.path.join(AS_BUILT, "scratch")  # ignored: regenerable rasters
DEFAULT_LABELS = os.path.join(AS_BUILT, "labels.csv")

INCH_CM = 2.54
SAT_MIN_CM2 = 3.0        # reject specks / handwriting flecks below this area
DEFAULT_FIT_MM = 1.0     # smooth-outline Bezier tolerance: this IS the smoothing lever
DEFAULT_SMOOTH_MM = 1.0  # light pre-smoothing only -- see the note in fit_closed_beziers


# --------------------------------------------------------------------------- #
# feather labels
# --------------------------------------------------------------------------- #
def load_labels(path):
    """Read image -> {index: (label, length_cm, x_cm)}.

    Labels are transcribed from the **hand-written marks on the templates**. Where a
    mark disagrees with any other source, the mark wins: marks ride on the physical
    part, whereas detection indices are derived (they are assigned by area, so they
    are not positional and can renumber if segmentation changes).

    The length/centroid recorded alongside each label are advisory anchors: if they
    no longer match, the mapping has gone stale and the script says so instead of
    silently mislabelling a feather.
    """
    if not path or not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                idx = int(row["index"])
            except (KeyError, TypeError, ValueError):
                continue
            label = (row.get("label") or "").strip()
            if not label:
                continue

            def num(key):
                try:
                    return float(row[key])
                except (KeyError, TypeError, ValueError):
                    return None

            out.setdefault((row.get("image") or "").strip(), {})[idx] = (
                label, num("length_cm"), num("x_cm"))
    return out


# --------------------------------------------------------------------------- #
# calibration
# --------------------------------------------------------------------------- #
def _ap_fit(vals, t_lo, t_hi, n=4000):
    """Best period T such that vals ~= p0 + k*T for integers k."""
    vals = np.asarray(sorted(vals), float)
    if vals.size < 4:
        return None
    ts = np.linspace(t_lo, t_hi, n)
    ang = (vals[None, :] % ts[:, None]) / ts[:, None] * 2 * np.pi
    r = np.hypot(np.cos(ang).mean(axis=1), np.sin(ang).mean(axis=1))
    i = int(np.argmax(r))
    if i in (0, n - 1):          # best fit at the edge of the window -> unreliable
        return None
    t0 = ts[i]
    # refine, then least-squares the (k, position) line for a sub-pixel period
    t = t0
    for span in (t0 * 0.02, t0 * 0.002):
        cand = np.linspace(t - span, t + span, 400)
        ang = (vals[None, :] % cand[:, None]) / cand[:, None] * 2 * np.pi
        r = np.hypot(np.cos(ang).mean(axis=1), np.sin(ang).mean(axis=1))
        t = float(cand[int(np.argmax(r))])
    k = np.round((vals - _phase(vals, t)) / t)
    A = np.c_[np.ones_like(k), k]
    (p0, t), *_ = np.linalg.lstsq(A, vals, rcond=None)
    resid = vals - A @ np.array([p0, t])
    return (float(t), float(p0), _concentration(vals, t), float(resid.std()), int(vals.size))


def _phase(vals, t):
    ang = (vals % t) / t * 2 * np.pi
    return math.atan2(float(np.sin(ang).mean()), float(np.cos(ang).mean())) / (2 * np.pi) * t


def _concentration(vals, t):
    ang = (vals % t) / t * 2 * np.pi
    return float(np.hypot(np.cos(ang).mean(), np.sin(ang).mean()))


def _ap_robust(pos, t_lo, t_hi, rounds=6):
    """AP fit with iterative outlier rejection -> period of a grid-line comb."""
    pos = np.asarray(sorted(pos), float)
    out = None
    for _ in range(rounds):
        fit = _ap_fit(pos, t_lo, t_hi)
        if fit is None:
            return out
        t, p0, r, sd, n = fit
        out = (t, p0, _concentration(pos, t), float(np.std(pos - (p0 + np.round((pos - p0) / t) * t))), n)
        keep = np.abs(pos - (p0 + np.round((pos - p0) / t) * t)) < 0.30 * t
        if keep.all() or keep.sum() < 5:
            return out
        pos = pos[keep]
        t_lo, t_hi = 0.98 * t, 1.02 * t
    return out


def _detrend(prof, deg=3):
    """Remove low-order illumination/coverage trend, which otherwise dominates the
    spectrum of a line-comb profile and hides the grid frequency."""
    n = prof.size
    if n < deg + 2:
        return prof
    x = np.linspace(-1.0, 1.0, n)
    A = np.vander(x, deg + 1)
    coef, *_ = np.linalg.lstsq(A, prof, rcond=None)
    return prof - A @ coef


def _fft_period(prof, lo=30.0, hi=520.0):
    """Dominant period of a 1-D profile via windowed FFT (coarse but robust)."""
    n = prof.size
    if n < 64:
        return None
    x = _detrend(prof) * np.hanning(n)
    F = np.abs(np.fft.rfft(x))
    f_lo = max(1, int(math.floor(n / hi)))
    f_hi = min(F.size - 2, int(math.ceil(n / lo)))
    if f_hi <= f_lo:
        return None
    j = f_lo + int(np.argmax(F[f_lo:f_hi + 1]))
    return _refine_period(F, j, n)


def _refine_period(F, j, n):
    """Parabolic peak interpolation -> sub-bin period from FFT magnitude bin j."""
    d = 0.0
    if 0 < j < F.size - 1:
        a, b, c = F[j - 1], F[j], F[j + 1]
        denom = a - 2 * b + c
        if abs(denom) > 1e-12:
            d = 0.5 * (a - c) / denom
    return n / (j + d)


def _local_maxima(score, thr, min_dist):
    """Peaks above thr, strongest first, suppressing anything within min_dist."""
    cand = np.flatnonzero(score > thr)
    if cand.size == 0:
        return np.array([], dtype=int)
    blocked = np.zeros(score.size, bool)
    taken = []
    for i in cand[np.argsort(-score[cand])]:
        if blocked[i]:
            continue
        taken.append(int(i))
        blocked[max(0, i - min_dist):i + min_dist + 1] = True
    return np.array(sorted(taken), dtype=int)


def _mat_mask_calib(bgr, sat_t=45.0, v_min=140.0, s_max=35.0):
    """Pixels that are definitely printed sheet: near-neutral and not dark ink."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    tmpl = (hsv[:, :, 1] > sat_t).astype(np.uint8)
    tmpl = cv2.dilate(cv2.morphologyEx(tmpl, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)),
                      np.ones((13, 13), np.uint8))
    return (tmpl == 0) & (hsv[:, :, 1] < s_max) & (hsv[:, :, 2] > v_min)


def _line_frac_profile(gray, ok, axis, lo, hi, delta=3.5, min_cnt=40):
    """Per-column (axis=0) or per-row (axis=1) fraction of sheet pixels darker
    than that column/row's own sheet median: ~1 on a printed grid line."""
    if axis == 0:
        band, okb = gray[lo:hi].astype(np.float32), ok[lo:hi]
    else:
        band, okb = gray[:, lo:hi].T.astype(np.float32), ok.T[lo:hi]
    med = np.median(np.where(okb, band, np.nan), axis=0)
    med = np.nan_to_num(med, nan=float(np.nanmedian(band)))
    darker = (band < (med[None, :] - delta)) & okb
    cnt = okb.sum(axis=0)
    return np.where(cnt >= min_cnt, darker.sum(axis=0) / np.maximum(cnt, 1), 0.0)


def _pitch_from_bands(gray, ok, axis, bands, seed):
    """One grid pitch estimate per clean band: peak the line comb, then AP-fit it
    over a narrow window around `seed` so a multiple of the pitch cannot win."""
    out = []
    for lo, hi in bands:
        if hi - lo < 32:
            continue
        prof = _detrend(_line_frac_profile(gray, ok, axis, lo, hi))
        if prof.max() < 0.20:
            continue
        pk = _local_maxima(prof, 0.40 * prof.max(), max(6, int(0.5 * seed)))
        if pk.size < 6:
            continue
        fit = _ap_robust(pk, 0.92 * seed, 1.08 * seed)
        if fit is None or fit[4] < 6:
            continue
        t, p0, r, sd, n = fit
        out.append({"px_per_in": t, "phase_px": p0, "fit_r": r, "resid_px": sd,
                    "n": n, "band": [int(lo), int(hi)]})
    return out


def _dot_period(bgr, gray, patch=512, step=128, min_clean=0.95):
    """1/4" dot-grid period per axis, median over many clean sheet patches.

    The dot grid is present everywhere on the sheet and is independent of the major
    1" lines, so it gives the coarse scale that disambiguates which harmonic of the
    line comb is the 1" pitch. Individual patches are noisy; the median is stable.
    """
    ok = _mat_mask_calib(bgr, v_min=120.0)
    h, w = gray.shape
    integ = cv2.integral(ok.astype(np.float32))
    tx, ty = [], []
    win = np.outer(np.hanning(patch), np.hanning(patch)).astype(np.float32)

    def peak(c, n):
        f_lo = max(4, int(math.floor(n / 45.0)))
        f_hi = min(c.size - 2, int(math.ceil(n / 15.0)))
        if f_hi <= f_lo:
            return None
        col = c[f_lo:f_hi + 1]
        j = f_lo + int(np.argmax(col))
        if col.max() < 0.15 * c[1:].max():
            return None
        k = _refine_period(c, j, n)
        return k if 15.0 < k < 45.0 else None

    for y in range(0, h - patch + 1, step):
        for x in range(0, w - patch + 1, step):
            s = (integ[y + patch, x + patch] - integ[y, x + patch]
                 - integ[y + patch, x] + integ[y, x])
            if s / float(patch * patch) < min_clean:
                continue
            a = gray[y:y + patch, x:x + patch].astype(np.float32)
            c = np.fft.fftshift(np.abs(np.fft.fft2((a - a.mean()) * win)))[patch // 2:, patch // 2:]
            px = peak(c[0, :], patch)
            py = peak(c[:, 0], patch)
            if px and py:
                tx.append(px)
                ty.append(py)
    if len(tx) < 6:
        return None
    return {"x": float(np.median(tx)), "y": float(np.median(ty)), "patches": len(tx)}


def calibrate(bgr, override=None, sheet=None):
    """Per-axis px-per-inch for one image, plus independent cross-checks.

    The 1" pitch is measured from the printed major grid lines, which give the
    highest precision (a least-squares fit over ~30 lines). The ambiguous part is
    *which* harmonic of that comb is the 1" line, so several coarse seeds are tried
    and scored by how well independent bands agree -- a wrong harmonic fits the
    bands inconsistently, a right one fits them all to a fraction of a pixel.
    """
    if override is not None:
        tx, ty = override
        return {"source": "override",
                "x": {"px_per_in": tx}, "y": {"px_per_in": ty}}
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    ok = _mat_mask_calib(bgr)
    bands_h = [(int(f * h), int(f * h) + int(0.07 * h)) for f in (0.02, 0.30, 0.58, 0.86)]
    bands_w = [(int(f * w), int(f * w) + int(0.07 * w)) for f in (0.02, 0.30, 0.58, 0.86)]

    seeds = []
    dots = _dot_period(bgr, gray)
    if dots:
        seeds.append((4.0 * dots["x"], 4.0 * dots["y"], "1/4\" dot grid x4"))
    fft = {}
    for axis, bands in ((0, bands_h), (1, bands_w)):
        vals = [_fft_period(_detrend(_line_frac_profile(gray, ok, axis, lo, hi)))
                for lo, hi in bands]
        vals = [v for v in vals if v]
        fft[axis] = float(np.median(vals)) if vals else None
    if fft.get(0) and fft.get(1):
        for k in (1, 2, 3, 4, 5, 6):
            seeds.append((fft[0] / k, fft[1] / k, f"grid-line FFT/{k}"))
    if not seeds:
        return None

    def combine(fits):
        t = float(np.median([f["px_per_in"] for f in fits]))
        best = min(fits, key=lambda f: abs(f["px_per_in"] - t))
        return {"px_per_in": t, "phase_px": best["phase_px"], "fit_r": best["fit_r"],
                "resid_px": best["resid_px"], "n": best["n"], "bands": len(fits),
                "band_spread_px": max(abs(f["px_per_in"] - t) for f in fits)}

    best = None
    for sx, sy, label in seeds:
        fx = _pitch_from_bands(gray, ok, 0, bands_h, sx)
        fy = _pitch_from_bands(gray, ok, 1, bands_w, sy)
        if len(fx) < 2 or len(fy) < 2:
            continue
        cx, cy = combine(fx), combine(fy)
        score = max(cx["band_spread_px"] / cx["px_per_in"],
                    cy["band_spread_px"] / cy["px_per_in"])
        if best is None or score < best[0]:
            best = (score, label, cx, cy)
    if best is None:
        return None

    score, label, cx, cy = best
    notes = []
    if not dots:
        notes.append("no clean dot patches; grid pitch seeded from the line FFT alone")
    if score > 0.01:
        notes.append(f"calibration bands disagree by {100 * score:.2f}%")
    if dots:
        rx, ry = cx["px_per_in"] / dots["x"], cy["px_per_in"] / dots["y"]
        if not (3.6 < rx < 4.4) or not (3.6 < ry < 4.4):
            notes.append(f"pitch is {rx:.2f}/{ry:.2f} dot cells, expected ~4")

    # independent sanity check: on a full 24x36" sheet the crop margins must match
    if sheet:
        sw, sh = sheet
        mx = (w - sw * cx["px_per_in"]) / 2.0 / cx["px_per_in"]
        my = (h - sh * cy["px_per_in"]) / 2.0 / cy["px_per_in"]
        if mx < -0.5 or my < -0.5:
            notes.append(f"sheet does not fit the frame (margins {mx:.2f}\", {my:.2f}\")")
        elif abs(mx - my) > 0.5:
            notes.append(f"X/Y sheet margins differ ({mx:.2f}\" vs {my:.2f}\")")
    return {"source": "grid", "seed": label, "x": cx, "y": cy, "dots": dots, "notes": notes}


# --------------------------------------------------------------------------- #
# segmentation
# --------------------------------------------------------------------------- #
def _fill_holes(mask):
    h, w = mask.shape
    ff = mask.copy()
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    return cv2.bitwise_or(mask, (ff == 0).astype(np.uint8))


def template_mask(bgr, sat_t=45.0, pale=False):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = (hsv[:, :, 1] > sat_t).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    m = _fill_holes(m)

    if pale:
        # best-effort pass for white/paper templates: locally brighter than the
        # sheet, detected against a very large median background.
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        ds = 4
        small = cv2.resize(gray, (w // ds, h // ds), interpolation=cv2.INTER_AREA)
        bg = cv2.medianBlur(small, 151)                      # ~600 px at full res
        bright = ((small.astype(np.int16) - bg.astype(np.int16) > 22)
                  & (small > 195)).astype(np.uint8)
        bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
        up = cv2.resize(bright * 255, (w, h), interpolation=cv2.INTER_NEAREST)
        up[m > 0] = 0
        m = cv2.bitwise_or(m, (up > 0).astype(np.uint8))
    return m


def split_component(comp):
    """Watershed one merged blob into its template cores.

    Seeds are distance-transform maxima; returns [comp] unchanged when the blob
    looks like a single template. Feathers have a broad middle, so the peak test is
    deliberately strict -- a loose one chops one feather into several pieces.
    """
    dist = cv2.distanceTransform(comp.astype(np.uint8), cv2.DIST_L2, 5)
    if dist.max() <= 0:
        return [comp]
    peaks = ((cv2.dilate(dist, np.ones((15, 15), np.uint8)) == dist)
             & (dist > 0.50 * dist.max()))
    n, lab = cv2.connectedComponents(peaks.astype(np.uint8))
    if n <= 2:
        return [comp]
    markers = np.zeros(comp.shape, np.int32)          # 0 = unknown for watershed
    markers[peaks] = lab[peaks] + 1                   # seeds carry labels >= 2
    cv2.watershed(cv2.cvtColor(comp.astype(np.uint8) * 255, cv2.COLOR_GRAY2BGR), markers)
    out = [(markers == k) & comp for k in range(2, n + 1)]
    out = [m for m in out if m.sum() > 0]
    return out if len(out) > 1 else [comp]


# --------------------------------------------------------------------------- #
# measurement (all geometry in physical units, so the X/Y scale difference is honoured)
# --------------------------------------------------------------------------- #
def measure(poly_cm):
    pts = np.asarray(poly_cm, float)
    x, y = pts[:, 0], pts[:, 1]
    area = 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))

    hull = cv2.convexHull(pts.astype(np.float32)).reshape(-1, 2).astype(float)
    length = width = 0.0
    angle = 0.0
    if len(hull) >= 3:
        best_len, best_wid = 0.0, float("inf")
        for i in range(len(hull)):
            edge = hull[(i + 1) % len(hull)] - hull[i]
            ln = float(np.hypot(*edge))
            if ln < 1e-9:
                continue
            u = edge / ln
            nrm = np.array([-u[1], u[0]])
            d = hull @ u
            wn = hull @ nrm
            ext_u = float(d.max() - d.min())
            ext_n = float(wn.max() - wn.min())
            if ext_u > best_len:
                best_len, angle = ext_u, math.degrees(math.atan2(u[1], u[0]))
            if ext_n > best_len:
                best_len, angle = ext_n, math.degrees(math.atan2(nrm[1], nrm[0]))
            best_wid = min(best_wid, ext_u, ext_n)
        length, width = best_len, best_wid

    (_, (rw, rh), _) = cv2.minAreaRect(pts.astype(np.float32))
    return {
        "area_cm2": area,
        "length_cm": length,
        "width_cm": width,
        "aspect": (length / width) if width > 0 else 0.0,
        "angle_deg": angle,
        "rect_w_cm": min(rw, rh),
        "rect_h_cm": max(rw, rh),
    }


# --------------------------------------------------------------------------- #
# smooth (cubic Bezier) outline
#
# The SVG outline is the smooth cubic-Bezier idealisation of the detected edge. It is
# fitted to the *unsimplified* contour, not to the RDP polygon, so the fit is not limited
# by the polygon's own tolerance.
#
# Measurements are still taken from the RDP polygon (see measure()): the smooth curve is
# allowed to sit up to --fit-mm away from the detected edge, and since detection indices
# are assigned by area, re-deriving area from the smooth curve could renumber templates
# and invalidate as-built/labels.csv.
#
# Fitting is done in physical units (cm) so the tolerance is isotropic; the contour
# carries ~10% different scale in X and Y.
# --------------------------------------------------------------------------- #
def _smooth_closed(pts, sigma):
    """Gaussian-smooth a closed polyline, wrapping at the ends. sigma in samples."""
    if sigma <= 1e-9:
        return pts.astype(float)
    r = max(1, int(round(3.0 * sigma)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.empty((len(pts), 2), float)
    for j in range(2):
        pad = np.r_[pts[-r:, j], pts[:, j], pts[:r, j]]
        out[:, j] = np.convolve(pad, k, mode="valid")
    return out


def _bezier_eval(ctrl, u):
    u = np.asarray(u, float)[:, None]
    return (((1 - u) ** 3) * ctrl[0] + 3 * ((1 - u) ** 2) * u * ctrl[1]
            + 3 * (1 - u) * (u ** 2) * ctrl[2] + (u ** 3) * ctrl[3])


def _chord_u(pts):
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    u = np.r_[0.0, np.cumsum(d)]
    return u / u[-1] if u[-1] > 0 else u


def _span_error(pts, ctrl, u):
    d = np.linalg.norm(_bezier_eval(ctrl, u) - pts, axis=1)
    return float(d.max()), int(np.argmax(d))


def _reparam(pts, u, ctrl):
    q = _bezier_eval(ctrl, u)
    d1 = (3 * (1 - u)[:, None] ** 2 * (ctrl[1] - ctrl[0])
          + 6 * ((1 - u) * u)[:, None] * (ctrl[2] - ctrl[1])
          + 3 * (u ** 2)[:, None] * (ctrl[3] - ctrl[2]))
    d2 = (6 * (1 - u)[:, None] * (ctrl[2] - 2 * ctrl[1] + ctrl[0])
          + 6 * u[:, None] * (ctrl[3] - 2 * ctrl[2] + ctrl[1]))
    num = ((q - pts) * d1).sum(1)
    den = (d1 * d1).sum(1) + ((q - pts) * d2).sum(1)
    return np.clip(u - num / np.where(np.abs(den) < 1e-12, 1e-12, den), 0.0, 1.0)


def _bezier_through(pts, u, t0, t1):
    """Least-squares cubic Bezier with fixed end tangents (Schneider, Graphics Gems 1990)."""
    n = len(pts)
    a = np.empty((n, 2, 2))
    for i in range(n):
        b1 = 3.0 * (1.0 - u[i]) ** 2 * u[i]
        b2 = 3.0 * (1.0 - u[i]) * u[i] ** 2
        # column 0 pairs with t0 (P1), column 1 with t1 (P2). np.outer(t, scalar) is
        # (2,1) and broadcast-fills BOTH columns, silently degenerating the fit.
        a[i] = np.column_stack([t0 * b1, t1 * b2])
    c = np.zeros((2, 2))
    x = np.zeros(2)
    p0, p3 = pts[0], pts[-1]
    for i in range(n):
        b0 = (1.0 - u[i]) ** 3
        b1 = 3.0 * (1.0 - u[i]) ** 2 * u[i]
        b2 = 3.0 * (1.0 - u[i]) * u[i] ** 2
        b3 = u[i] ** 3
        tmp = pts[i] - ((b0 + b1) * p0 + (b2 + b3) * p3)
        c += a[i].T @ a[i]
        x += a[i].T @ tmp
    det = c[0, 0] * c[1, 1] - c[1, 0] * c[0, 1]
    seg = float(np.linalg.norm(p3 - p0))
    if abs(det) < 1e-12:
        al = ar = seg / 3.0
    else:
        al = (x[0] * c[1, 1] - c[0, 1] * x[1]) / det
        ar = (c[0, 0] * x[1] - x[0] * c[1, 0]) / det
        al, ar = min(max(al, 0.0), seg), min(max(ar, 0.0), seg)
    return np.array([p0, p0 + t0 * al, p3 + t1 * ar, p3])


def _fit_span(pts, t0, t1, tol, out, depth=0):
    if len(pts) < 2 or depth > 20:
        return
    if len(pts) == 2:
        d = float(np.linalg.norm(pts[1] - pts[0])) / 3.0
        out.append(np.array([pts[0], pts[0] + t0 * d, pts[1] + t1 * d, pts[1]]))
        return
    u = _chord_u(pts)
    ctrl = _bezier_through(pts, u, t0, t1)
    e, split = _span_error(pts, ctrl, u)
    if e > tol:
        # Always try reparameterising before paying for a split. Schneider's original
        # "error*error" retry band, taken literally, disables the retry for small
        # tolerances and over-splits badly (a circle needed 14 segments instead of 7).
        for _ in range(8):
            u = _reparam(pts, u, ctrl)
            ctrl = _bezier_through(pts, u, t0, t1)
            e, split = _span_error(pts, ctrl, u)
            if e <= tol:
                break
    if e <= tol:
        out.append(ctrl)
        return
    split = min(max(split, 1), len(pts) - 2)
    tan = pts[split - 1] - pts[split + 1]
    nn = float(np.linalg.norm(tan))
    tan = tan / nn if nn > 1e-9 else t0
    _fit_span(pts[:split + 1], t0, tan, tol, out, depth + 1)
    _fit_span(pts[split:], -tan, t1, tol, out, depth + 1)


def fit_closed_beziers(raw_cm, mm_per_px, tol_mm, smooth_mm, samples=600):
    """Closed loop -> list of cubic Bezier control quadruples (in cm).

    The loop is split at two well-separated low-curvature points so each open span
    starts and ends where a tangent is well defined.

    `tol_mm` is the smoothing lever: because the fitter subdivides only where the
    error exceeds the tolerance, a generous tolerance flattens the ragged hand-cut
    edge along the flanks while still spending segments to follow the tip.

    `smooth_mm` is deliberately NOT the lever. Measured over all 42 templates, raising
    pre-smoothing to 3-6 mm cut the tip so hard that the feather lost 1.5-4.0 mm of
    length, where raising the tolerance to the same segment count lost 0.3 mm. Keep
    this small (~1 mm, the hand-cut roughness scale) and turn `tol_mm` instead.
    """
    if len(raw_cm) < 16:
        return []
    sigma = smooth_mm / max(mm_per_px, 1e-9)          # mm -> samples
    pts = _smooth_closed(np.asarray(raw_cm, float), sigma)
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(np.r_[pts, pts[:1]], axis=0), axis=1))]
    if not np.isfinite(d[-1]) or d[-1] <= 0:
        return []
    m = max(32, min(samples, len(pts)))
    u = np.linspace(0.0, d[-1], m, endpoint=False)
    c = np.c_[np.interp(u, d, np.r_[pts[:, 0], pts[0, 0]]),
              np.interp(u, d, np.r_[pts[:, 1], pts[0, 1]])]

    d1 = np.gradient(c, axis=0)
    d2 = np.gradient(d1, axis=0)
    sp = np.linalg.norm(d1, axis=1)
    k = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum(sp ** 3, 1e-12)
    k = np.convolve(np.r_[k, k, k], np.ones(15) / 15.0, "same")[len(k):2 * len(k)]
    a = int(np.argmin(k))
    idx = np.arange(len(c))
    dist = np.minimum(np.abs(idx - a), len(c) - np.abs(idx - a))
    b = int(np.argmin(np.where(dist > len(c) * 0.25, k, np.inf)))
    hi, lo = max(a, b), min(a, b)

    tol = max(tol_mm / 10.0, 1e-7)                    # mm -> cm
    out = []
    for span in (np.r_[c[hi:], c[:lo + 1]], c[lo:hi + 1]):
        if len(span) < 3:
            continue
        t0 = span[1] - span[0]
        t0 = t0 / max(float(np.linalg.norm(t0)), 1e-9)
        t1 = span[-1] - span[-2]
        t1 = t1 / max(float(np.linalg.norm(t1)), 1e-9)
        _fit_span(span, t0, t1, tol, out)
    return out


def bezier_max_dev_cm(beziers, raw_cm, per_seg=12):
    """Largest distance from the fitted curve back to the detected (unsmoothed) edge."""
    if not beziers or len(raw_cm) < 4:
        return 0.0
    samp = np.vstack([_bezier_eval(b, np.linspace(0.0, 1.0, per_seg)) for b in beziers])
    ref = np.asarray(raw_cm, float)[::max(1, len(raw_cm) // 800)]
    d = np.linalg.norm(samp[:, None, :] - ref[None, :, :], axis=2).min(axis=1)
    return float(d.max())


# --------------------------------------------------------------------------- #
# outputs
# --------------------------------------------------------------------------- #
def write_overlay(bgr, items, path):
    vis = bgr.copy()
    thick = max(3, round(bgr.shape[1] / 700))
    for it in items:
        cnt = np.asarray(it["polygon_px"], np.int32).reshape(-1, 1, 2)
        colour = (0, 0, 255) if it.get("pale") else (0, 200, 0)
        cv2.polylines(vis, [cnt], True, colour, thick, cv2.LINE_AA)
        c = tuple(np.round(it["centroid_px"]).astype(int))
        cv2.drawMarker(vis, c, colour, cv2.MARKER_CROSS, thick * 5, max(1, thick // 2))
        # just the feather code: dimensions belong in the CSV/JSON, not stamped on the drawing
        tag = it.get("label") or f"#{it['index']}"
        org = (int(it["bbox_px"][0]), max(20, int(it["bbox_px"][1]) - 8))
        for col, off in (((0, 0, 0), thick), (colour, 1)):
            cv2.putText(vis, tag, (org[0] + off, org[1] + off), cv2.FONT_HERSHEY_SIMPLEX,
                        bgr.shape[1] / 2400.0, col, thick, cv2.LINE_AA)
    cv2.imwrite(path, vis)


def write_gridcheck(bgr, cal, path):
    """Draw the fitted 1" grid over the photo.

    The quickest way to confirm a calibration by eye: the drawn lines should sit on
    the printed grid and step with the printed ruler numbers.
    """
    vis = bgr.copy()
    h, w = vis.shape[:2]
    for axis, colour in ((0, (0, 0, 255)), (1, (255, 0, 0))):
        c = cal["x" if axis == 0 else "y"]
        t, ph = c["px_per_in"], c.get("phase_px", 0.0) or 0.0
        span = w if axis == 0 else h
        for k in range(int(-ph / t) - 1, int((span - ph) / t) + 2):
            p = int(round(ph + k * t))
            if axis == 0:
                if 0 <= p < w:
                    cv2.line(vis, (p, 0), (p, h), colour, 2)
            elif 0 <= p < h:
                cv2.line(vis, (0, p), (w, p), colour, 2)
    cv2.imwrite(path, vis)


def _path_d(it, bz):
    """SVG path data (mm) for one template: smooth Bezier if fitted, else the polyline."""
    if bz:
        cp = [np.asarray(b, float) * 10.0 for b in bz]
        return f"M {cp[0][0][0]:.3f},{cp[0][0][1]:.3f} " + " ".join(
            f"C {c[1][0]:.3f},{c[1][1]:.3f} {c[2][0]:.3f},{c[2][1]:.3f} "
            f"{c[3][0]:.3f},{c[3][1]:.3f}" for c in cp) + " Z"
    pts = np.asarray(it["polygon_cm"], float) * 10.0
    return "M " + " L ".join(f"{p[0]:.3f},{p[1]:.3f}" for p in pts) + " Z"


def write_feather_svgs(bgr, items, smooth, tx, ty, out_dir, margin_mm=8.0, quality=92,
                       force=False):
    """One self-contained SVG per template: the photo underneath the outline.

    Written to be opened in a vector editor for hand-tweaking. Two properties matter:

    * the raster is embedded (base64 JPEG), so the file never depends on a sibling image
      surviving a move or a copy into a project folder;
    * the viewBox is the *sheet's* mm frame, not a local one, so every file shares one
      coordinate system and a tweaked path keeps its absolute position. Only width/height
      are trimmed to the crop, so the file opens zoomed on that feather at 1:1.

    The photo crop is placed with preserveAspectRatio="none" over its own mm rectangle:
    the scan is anisotropic (~10% difference between X and Y px/inch), so stretching the
    crop to the calibrated mm box is what makes it register with the path.

    An existing file that differs is left alone unless `force` is set -- these files are
    meant to be hand-edited, and silently regenerating over that work would be the worst
    possible failure mode. Returns (written, kept).
    """
    h_img, w_img = bgr.shape[:2]
    os.makedirs(out_dir, exist_ok=True)
    written, kept = [], []
    for it, bz in zip(items, smooth if smooth else [None] * len(items)):
        x, y, bw, bh = it["bbox_px"]
        px_per_mm_x, px_per_mm_y = tx / 25.4, ty / 25.4
        mx, my = int(round(margin_mm * px_per_mm_x)), int(round(margin_mm * px_per_mm_y))
        x0, y0 = max(0, x - mx), max(0, y - my)
        x1, y1 = min(w_img, x + bw + mx), min(h_img, y + bh + my)
        crop = bgr[y0:y1, x0:x1]
        if crop.size == 0:
            continue
        ok, buf = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            continue
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")

        # crop rectangle in the sheet's mm frame
        vx, vy = x0 / px_per_mm_x, y0 / px_per_mm_y
        vw, vh = (x1 - x0) / px_per_mm_x, (y1 - y0) / px_per_mm_y
        tag = it.get("label") or f"t{it['index']}"
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{vw:.2f}mm" height="{vh:.2f}mm" '
            f'viewBox="{vx:.3f} {vy:.3f} {vw:.3f} {vh:.3f}">',
            f'  <image x="{vx:.3f}" y="{vy:.3f}" width="{vw:.3f}" height="{vh:.3f}" '
            f'preserveAspectRatio="none" xlink:href="data:image/jpeg;base64,{b64}"/>',
            '  <g id="outlines" fill="none" stroke="#000" stroke-width="0.5">',
            f'    <path id="{tag}" d="{_path_d(it, bz)}"/>',
            '  </g>',
            '  <g id="labels" font-family="sans-serif" font-size="6" fill="#d40000">',
            f'    <text x="{vx + 1.5:.2f}" y="{vy + 6:.2f}">{tag}</text>',
            '  </g>',
            '</svg>',
            '',
        ]
        path = os.path.join(out_dir, f"{tag}.svg")
        text = "\n".join(lines)
        if not force and os.path.exists(path):
            try:
                if open(path, encoding="utf-8").read() != text:
                    kept.append(tag)
                    continue
            except OSError:
                pass
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        written.append((tag, path, len(lines[2]) / 1024.0))
    return written, kept


def write_svg(items, out_w_cm, out_h_cm, path, smooth=None):
    """1:1 physical SVG (user units = mm), one black outline path per template.

    The outline is the smooth cubic-Bezier idealisation when a fit is available (the
    default), falling back to the RDP polyline for any template that could not be fit
    or when --no-smooth is given. Path ids are the feather labels either way.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{out_w_cm * 10:.2f}mm" height="{out_h_cm * 10:.2f}mm" '
        f'viewBox="0 0 {out_w_cm * 10:.3f} {out_h_cm * 10:.3f}">',
        '  <g id="outlines" fill="none" stroke="#000" stroke-width="0.5">',
    ]
    for it, bz in zip(items, smooth if smooth else [None] * len(items)):
        tag = it.get("label") or f"t{it['index']}"
        if bz:
            cp = [np.asarray(b, float) * 10.0 for b in bz]
            d = f"M {cp[0][0][0]:.3f},{cp[0][0][1]:.3f} " + " ".join(
                f"C {c[1][0]:.3f},{c[1][1]:.3f} {c[2][0]:.3f},{c[2][1]:.3f} "
                f"{c[3][0]:.3f},{c[3][1]:.3f}" for c in cp) + " Z"
        else:
            pts = np.asarray(it["polygon_cm"], float) * 10.0
            d = "M " + " L ".join(f"{p[0]:.3f},{p[1]:.3f}" for p in pts) + " Z"
        lines.append(f'    <path id="{tag}" d="{d}"/>')
    lines.append('  </g>')

    lines += [
        '  <g id="labels" font-family="sans-serif" font-size="6" fill="#000">',
    ]
    for it in items:
        tag = it.get("label") or f"t{it['index']}"
        cx, cy = np.asarray(it["centroid_cm"], float) * 10.0
        lines.append(f'    <text x="{cx:.2f}" y="{cy:.2f}" text-anchor="middle">'
                     f'{tag}</text>')
    lines += ['  </g>', '</svg>', '']
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


# --------------------------------------------------------------------------- #
# expected count from the filename, e.g. SC1-8_A1-4_PC1-3 -> 8+4+3
# --------------------------------------------------------------------------- #
def expected_count(stem):
    """How many templates the filename says are in the photo.

    Handles grouped ranges (`SC1-8_A1-4_PC1-3` -> 8+4+3) and a bare single label
    (`B5` -> 1, for a solo photo of one template).
    """
    total, groups = 0, []
    for name, a, b in re.findall(r"([A-Za-z]+)(\d+)-(\d+)", stem):
        n = int(b) - int(a) + 1
        groups.append(f"{name}{a}-{b}={n}")
        total += n
    if total:
        return total, groups
    m = re.fullmatch(r"\s*([A-Za-z]+)(\d+)\s*", stem)
    if m:
        return 1, [f"{m.group(1)}{m.group(2)}=1"]
    return 0, []


# --------------------------------------------------------------------------- #
def process(path, out_dir, scratch_dir, args):
    bgr = cv2.imread(path)
    if bgr is None:
        print(f"  ! cannot read {path}", file=sys.stderr)
        return None
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    stem = os.path.splitext(os.path.basename(path))[0]
    print(f"\n=== {os.path.basename(path)}  ({w}x{h})")

    cal = calibrate(bgr, override=args.px_per_inch, sheet=args.sheet_in)
    if cal is None:
        print("  ! calibration failed; pass --px-per-inch", file=sys.stderr)
        return None
    tx = cal["x"]["px_per_in"]
    ty = cal["y"]["px_per_in"]
    aspect_err = 100.0 * (ty / tx - 1.0)
    print(f"  calibration [{cal['source']}]: X={tx:.2f} px/in  Y={ty:.2f} px/in  "
          f"(Y/X {aspect_err:+.1f}%)")
    if cal["source"] == "grid":
        for axis in ("x", "y"):
            c = cal[axis]
            print(f"    {axis.upper()}: {c['bands']} bands, r={c['fit_r']:.3f}, "
                  f"resid={c['resid_px']:.2f} px, band spread {c['band_spread_px']:.2f} px")
        if cal.get("dots"):
            d = cal["dots"]
            print(f"    1/4\" dot grid: {d['patches']} clean patches, "
                  f"x={d['x']:.2f} y={d['y']:.2f} px -> "
                  f"{tx / d['x']:.2f} / {ty / d['y']:.2f} cells per inch")
        for note in cal.get("notes", []):
            print(f"    ! {note}")

    mask = template_mask(bgr, sat_t=args.sat_threshold, pale=args.pale)

    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    px_per_cm_x, px_per_cm_y = tx / INCH_CM, ty / INCH_CM
    min_area_px = args.min_area_cm2 * px_per_cm_x * px_per_cm_y
    sat = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[:, :, 1]

    keep = [i for i in range(1, n) if stats[i][4] >= min_area_px]
    med_area = float(np.median([stats[i][4] for i in keep])) if keep else 0.0
    pieces = []
    for i in keep:
        comp = (lab == i)
        # only genuinely merged templates (area outliers) are candidates for splitting
        if args.split and len(keep) > 2 and med_area > 0 and stats[i][4] > 1.8 * med_area:
            sub = split_component(comp)
            if len(sub) > 1:
                print(f"    split one {stats[i][4]} px blob into {len(sub)} templates")
            pieces.extend(sub)
        else:
            pieces.append(comp)

    items = []
    for comp in pieces:
        cmask = comp.astype(np.uint8)
        # dense contour: the polygon uses approxPolyDP, the Bezier outline fits the
        # unsimplified boundary, so ask for every point
        cnts, _ = cv2.findContours(cmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cnts:
            continue
        cnt = max(cnts, key=cv2.contourArea)
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, max(1.5, 0.0015 * peri), True).reshape(-1, 2)
        if len(approx) < 3:
            continue
        poly_px = approx.astype(float)
        # px -> cm with an independent scale per axis
        poly_cm = np.c_[poly_px[:, 0] / tx * INCH_CM, poly_px[:, 1] / ty * INCH_CM]
        m = measure(poly_cm)
        mom = cv2.moments(cmask, binaryImage=True)
        cx = mom["m10"] / mom["m00"] if mom["m00"] else float(poly_px[:, 0].mean())
        cy = mom["m01"] / mom["m00"] if mom["m00"] else float(poly_px[:, 1].mean())
        x0, y0, bw, bh = cv2.boundingRect(cnt)
        items.append({
            "index": 0,
            # a piece too neutral to have come from the saturation pass was found
            # by the optional --pale brightness pass
            "pale": bool(float(sat[comp].mean()) < args.sat_threshold),
            "area_px": int(cv2.countNonZero(cmask)),
            "bbox_px": [int(x0), int(y0), int(bw), int(bh)],
            "centroid_px": [float(cx), float(cy)],
            "centroid_from_image_origin_cm": [float(cx / tx * INCH_CM),
                                              float(cy / ty * INCH_CM)],
            "n_vertices": int(len(approx)),
            "polygon_px": poly_px.round(2).tolist(),
            "polygon_cm": poly_cm.round(4).tolist(),
            "centroid_cm": [float(poly_cm[:, 0].mean()), float(poly_cm[:, 1].mean())],
            **{k: round(v, 3) for k, v in m.items()},
            # temporary: consumed for the SVG outline, dropped before any JSON is written
            "_raw_cm": np.c_[cnt.reshape(-1, 2)[:, 0] / tx * INCH_CM,
                             cnt.reshape(-1, 2)[:, 1] / ty * INCH_CM].round(4),
        })

    items.sort(key=lambda it: -it["area_cm2"])
    for j, it in enumerate(items, 1):
        it["index"] = j

    lab = args.label_map.get(os.path.basename(path), {})
    for it in items:
        entry = lab.get(it["index"])
        it["label"] = entry[0] if entry else None
        if entry and entry[1] is not None and abs(entry[1] - it["length_cm"]) > 0.5:
            print(f"    ! label file calls #{it['index']} '{entry[0]}' ({entry[1]:.2f} cm) "
                  f"but it now measures {it['length_cm']:.2f} cm -- indices may have shifted")
    stale = sorted(set(lab) - {it["index"] for it in items})
    if stale:
        print(f"    ! label file lists indices not detected: {stale}")

    # Bezier outline for the SVG. NOT fed to the measurements -- see the note above.
    mm_per_px = 25.4 * 0.5 * (1.0 / tx + 1.0 / ty)
    smooth, devs = [], []
    for it in items:
        raw_cm = it.pop("_raw_cm", None)
        bz = []
        if raw_cm is not None and not args.no_smooth:
            bz = fit_closed_beziers(np.asarray(raw_cm, float), mm_per_px,
                                    args.fit_mm, args.smooth_mm)
            devs.append(bezier_max_dev_cm(bz, np.asarray(raw_cm, float)))
        smooth.append(bz)
    if any(smooth):
        n = [len(b) for b in smooth if b]
        print(f"    outline: {sum(n)} cubic segments (median {np.median(n):.0f}), "
              f"tol {args.fit_mm} mm, pre-smooth {args.smooth_mm} mm, "
              f"max deviation from the detected edge {max(devs) * 10:.2f} mm")

    exp_total, exp_groups = expected_count(stem)
    print(f"  templates: {len(items)} detected"
          + (f"  (filename implies {exp_total}: {', '.join(exp_groups)})" if exp_total else ""))
    if exp_total and len(items) != exp_total:
        print(f"  ! count mismatch: {len(items)} detected vs {exp_total} expected")
    for it in items:
        tag = it["label"] or f"#{it['index']}"
        print(f"    {tag:>5s}  {it['length_cm']:6.2f} x {it['width_cm']:5.2f} cm  "
              f"area {it['area_cm2']:7.2f} cm2  aspect {it['aspect']:4.2f}  "
              f"at ({it['centroid_from_image_origin_cm'][0]:5.1f},"
              f"{it['centroid_from_image_origin_cm'][1]:5.1f}) cm")

    # Labels are transcribed from the marks, but indices are position-blind, so show
    # each series in physical reading order (top row first, then left to right within
    # a row): a scrambled assignment is obvious here (e.g. "P2 P3 P4 P1" means the
    # mapping and the geometry disagree).
    labelled = [it for it in items if it["label"]]
    if labelled:
        groups = {}
        for it in labelled:
            m = re.match(r"([A-Za-z]+)", it["label"])
            groups.setdefault(m.group(1) if m else "?", []).append(it)
        parts = []
        for prefix in sorted(groups):
            grp = groups[prefix]
            band = 0.5 * float(np.median([t["bbox_px"][3] for t in grp]))
            rows = []                              # [anchor_y, [items]]
            for it in sorted(grp, key=lambda t: t["centroid_px"][1]):
                for r in rows:
                    if abs(it["centroid_px"][1] - r[0]) <= band:
                        r[1].append(it)
                        break
                else:
                    rows.append([it["centroid_px"][1], [it]])
            ordered = []
            for _, row in rows:
                ordered.extend(sorted(row, key=lambda t: t["centroid_px"][0]))
            parts.append(" ".join(t["label"] for t in ordered))
        print("    label order: " + " | ".join(parts))

    # geometry -> outlines/ (tracked);  regenerable rasters -> scratch/ (ignored)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(scratch_dir, exist_ok=True)
    write_overlay(bgr, items, os.path.join(scratch_dir, f"{stem}.overlay.png"))
    write_gridcheck(bgr, cal, os.path.join(scratch_dir, f"{stem}.gridcheck.png"))
    cv2.imwrite(os.path.join(scratch_dir, f"{stem}.mask.png"), mask * 255)
    if args.feathers:
        feather_dir = args.feather_out or os.path.join(scratch_dir, "feathers")
        got, kept = write_feather_svgs(bgr, items, smooth, tx, ty, feather_dir,
                                       margin_mm=args.feather_margin_mm,
                                       force=args.feather_force)
        kb = sum(g[2] for g in got)
        print(f"    feather files: {len(got)} written, {len(kept)} kept -> {feather_dir} "
              f"({kb / 1024.0:.2f} MB written)")
        if kept:
            print(f"    ! kept existing (hand-edited?) {', '.join(kept[:6])}"
                  f"{' ...' if len(kept) > 6 else ''} -- "
                  f"use --feather-force to regenerate them")
    write_svg(items, w / tx * INCH_CM, h / ty * INCH_CM,
              os.path.join(out_dir, f"{stem}.svg"), smooth=smooth)
    with open(os.path.join(out_dir, f"{stem}.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump({"image": os.path.basename(path), "size_px": [w, h],
                   "calibration": {k: v for k, v in cal.items() if not k.endswith("_all")},
                   "expected_count": exp_total or None,
                   "expected_groups": exp_groups,
                   "templates": items}, f, indent=1)

    return {"image": os.path.basename(path), "calibration": cal, "templates": items,
            "expected_count": exp_total or None, "stem": stem}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", default=os.path.join(DEFAULT_IN, "*.jpg"),
                    help="glob of source images (default: as-built/source-images/unskewed/*.jpg)")
    ap.add_argument("--px-per-inch", default=None,
                    help="skip auto-calibration, e.g. 100 or 101.8,112.0 (X[,Y])")
    ap.add_argument("--sheet-in", default="36,24",
                    help="printed sheet size in inches W,H, used only as a "
                         "margin sanity check (default 36,24)")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="geometry output folder, tracked (default as-built/outlines)")
    ap.add_argument("--scratch", default=DEFAULT_SCRATCH,
                    help="raster/QC output folder, git-ignored (default as-built/scratch)")
    ap.add_argument("--labels", default=DEFAULT_LABELS,
                    help="CSV mapping image,index -> feather label "
                         "(default as-built/labels.csv)")
    ap.add_argument("--sat-threshold", type=float, default=45.0,
                    help="saturation threshold for template detection (default 45)")
    ap.add_argument("--min-area-cm2", type=float, default=SAT_MIN_CM2,
                    help=f"discard blobs smaller than this (default {SAT_MIN_CM2})")
    ap.add_argument("--pale", action="store_true",
                    help="add best-effort brightness pass for white/paper templates")
    ap.add_argument("--split", action="store_true",
                    help="watershed-split templates that touch each other")
    ap.add_argument("--fit-mm", type=float, default=DEFAULT_FIT_MM,
                    help="max deviation of the smooth SVG outline path -- this is the "
                         f"smoothing lever; larger = flatter flanks (default {DEFAULT_FIT_MM} mm)")
    ap.add_argument("--smooth-mm", type=float, default=DEFAULT_SMOOTH_MM,
                    help="Gaussian pre-smoothing before the fit. Keep small (~1 mm): "
                         "raising it rounds the tip and shortens the feather "
                         f"(default {DEFAULT_SMOOTH_MM} mm)")
    ap.add_argument("--no-smooth", action="store_true",
                    help="emit the unsmoothed RDP polyline outline instead of the "
                         "finite-tolerance Bezier idealisation")
    ap.add_argument("--feathers", action="store_true",
                    help="also write one self-contained SVG per feather (embedded photo "
                         "crop + outline, sheet mm frame) for editing in a vector editor")
    ap.add_argument("--feather-out", default=None,
                    help="where to write the per-feather SVGs (default <scratch>/feathers)")
    ap.add_argument("--feather-margin-mm", type=float, default=8.0,
                    help="photo context to include around each feather (default 8 mm)")
    ap.add_argument("--feather-force", action="store_true",
                    help="overwrite per-feather SVGs that already exist (default: keep an "
                         "existing file that differs, so hand-tweaked paths survive)")
    args = ap.parse_args()

    if args.px_per_inch:
        parts = [float(v) for v in args.px_per_inch.split(",")]
        args.px_per_inch = (parts[0], parts[1] if len(parts) > 1 else parts[0])
    args.sheet_in = tuple(float(v) for v in args.sheet_in.split(","))[:2]
    args.label_map = load_labels(args.labels)
    if args.label_map:
        print(f"labels : {args.labels}")
    elif args.labels:
        print(f"labels : {args.labels} (not found -- outputs will use #indices)")

    paths = sorted(glob.glob(args.images))
    if not paths:
        sys.exit(f"no images matched {args.images}")
    print(f"source  : {args.images}")
    print(f"outlines: {args.out}  (tracked)")
    print(f"scratch : {args.scratch}  (ignored)")

    results = [r for r in (process(p, args.out, args.scratch, args) for p in paths) if r]
    if not results:
        sys.exit("nothing processed")

    os.makedirs(args.out, exist_ok=True)
    rows = []
    for r in results:
        for t in r["templates"]:
            rows.append({
                "image": r["image"], "label": t.get("label") or "", "index": t["index"],
                "length_cm": f"{t['length_cm']:.2f}", "width_cm": f"{t['width_cm']:.2f}",
                "area_cm2": f"{t['area_cm2']:.2f}", "aspect": f"{t['aspect']:.2f}",
                "angle_deg": f"{t['angle_deg']:.1f}",
                "x_cm": f"{t['centroid_from_image_origin_cm'][0]:.2f}",
                "y_cm": f"{t['centroid_from_image_origin_cm'][1]:.2f}",
                "vertices": t["n_vertices"],
            })
    csv_path = os.path.join(args.out, "templates-measured.csv")
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                                lineterminator="\n")
            wr.writeheader()
            wr.writerows(rows)

    with open(os.path.join(args.out, "outlines.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump([{"image": r["image"], "calibration": r["calibration"],
                    "expected_count": r["expected_count"],
                    "templates": r["templates"]} for r in results], f, indent=1)
    with open(os.path.join(args.out, "calibration.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump([{"image": r["image"],
                    "x": r["calibration"]["x"], "y": r["calibration"]["y"]}
                   for r in results], f, indent=1)

    print()
    if rows:
        print(f"wrote {len(rows)} template rows -> {csv_path}")
    else:
        print("! no templates detected in any image -- check --sat-threshold")
    print(f"      geometry (per-image .svg/.json, outlines.json, calibration.json) -> {args.out}")
    print(f"      QC rasters (.overlay/.gridcheck/.mask .png) -> {args.scratch}")


if __name__ == "__main__":
    main()
