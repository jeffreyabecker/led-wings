#!/usr/bin/env python3
"""Generate Avery 5160 feather labels from feather-record.csv.

One label per feather per wing (L + R, mirrored templates) -> 122 labels,
laid out 3 x 10 per US Letter sheet (30/sheet). Each label shows the feather
name + wing and the measured TOT / WIRE lengths.

Usage:  python feather-labels.py
Output: feather-labels.pdf (next to this script)
Deps:   fpdf2  (pip install fpdf2)
"""
import csv
import os

from fpdf import FPDF

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "feather-record.csv")
OUT_PATH = os.path.join(HERE, "feather-labels.pdf")

# --- Avery 5160 (US Letter, mm) -------------------------------------------
PAGE_W, PAGE_H = 215.9, 279.4
LABEL_W, LABEL_H = 66.675, 25.4      # 2.625" x 1"
MARGIN_L = 4.7625                    # 0.1875"
MARGIN_T = 12.7                      # 0.5"
COLS, ROWS = 3, 10


def load_feathers(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def draw_label(pdf, x, y, name, wing, tot, wire):
    # dashed guide outline (matches the pre-cut Avery sheet)
    pdf.set_draw_color(160, 160, 160)
    pdf.set_dash_pattern(dash=1.2, gap=1.0)
    pdf.rect(x, y, LABEL_W, LABEL_H, style="D")
    pdf.set_dash_pattern()

    # name + wing, centered
    pdf.set_font("helvetica", "B", 16)
    pdf.set_xy(x, y + 3.0)
    pdf.cell(LABEL_W, 7.0, f"{name}  {wing}", align="C")

    # TOT / WIRE
    pdf.set_font("helvetica", "", 11)
    pdf.set_xy(x, y + 12.5)
    pdf.cell(LABEL_W, 5.0, f"TOT {tot} cm", align="C")
    pdf.set_xy(x, y + 17.5)
    pdf.cell(LABEL_W, 5.0, f"WIRE {wire} cm", align="C")


def main():
    feathers = load_feathers(CSV_PATH)
    labels = [
        (ft["feather"], wing, ft["total_cm"], ft["wire_cm"])
        for ft in feathers
        for wing in ("L", "R")
    ]

    pdf = FPDF(unit="mm", format="letter")
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)

    for i, (name, wing, tot, wire) in enumerate(labels):
        if i % (COLS * ROWS) == 0:
            pdf.add_page()
        pos = i % (COLS * ROWS)
        col, row = pos % COLS, pos // COLS
        x = MARGIN_L + col * LABEL_W
        y = MARGIN_T + row * LABEL_H
        draw_label(pdf, x, y, name, wing, tot, wire)

    pdf.output(OUT_PATH)
    print(f"Wrote {OUT_PATH}")
    print(f"  {len(labels)} labels, {len(feathers)} feather types x L/R")
    print(f"  {(len(labels) + COLS * ROWS - 1) // (COLS * ROWS)} sheet(s) (30 labels/sheet)")


if __name__ == "__main__":
    main()
