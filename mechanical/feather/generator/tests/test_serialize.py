"""G8 tests — DXF/SVG serializers."""

import json
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from feathergen.serialize import (
    serialize_all,
    serialize_feather,
    write_dxf,
    write_svg,
)

FEATHERS = json.loads(
    (Path(__file__).resolve().parents[1] / "feathers.json").read_text(encoding="utf-8")
)

# The DSH sandbox denies writes into tempfile-created dirs (pip fails the same
# way), so tests use a workspace-local scratch dir instead of pytest's tmp_path.
SCRATCH = Path(__file__).resolve().parents[1] / ".test-out"


@pytest.fixture(autouse=True)
def out_dir():
    shutil.rmtree(SCRATCH, ignore_errors=True)
    os.makedirs(SCRATCH, exist_ok=True)
    yield str(SCRATCH)
    shutil.rmtree(SCRATCH, ignore_errors=True)


def row(feather_id):
    return next(f for f in FEATHERS["feathers"] if f["id"] == feather_id)


# --- DXF --------------------------------------------------------------------


def test_dxf_emitted(out_dir):
    p = write_dxf([(0, 0), (10, 0), (10, 10), (0, 10)], "S", out_dir, "test.dxf")
    assert os.path.exists(p)
    assert p.endswith(".dxf")


def test_dxf_single_closed_polyline_on_layer(out_dir):
    p = write_dxf([(0, 0), (10, 0), (10, 10), (0, 10)], "P", out_dir, "P4.dxf")
    import ezdxf

    doc = ezdxf.readfile(p)
    msp = doc.modelspace()
    polylines = list(msp.query("LWPOLYLINE"))
    assert len(polylines) == 1
    pl = polylines[0]
    assert pl.dxf.layer == "P"
    assert pl.is_closed
    assert len(pl.get_points()) >= 4


def test_dxf_expected_layer_created(out_dir):
    import ezdxf

    write_dxf([(0, 0), (1, 1), (0, 1)], "GC", out_dir, "gc.dxf")
    doc = ezdxf.readfile(os.path.join(out_dir, "dxf", "gc.dxf"))
    assert "GC" in doc.layers


# --- SVG --------------------------------------------------------------------


def test_svg_well_formed(out_dir):
    p = write_svg([(0, 0), (10, 0), (10, 10), (0, 10)], out_dir, "test.svg")
    # parse must not raise
    ET.parse(p)


def test_svg_has_path_and_title(out_dir):
    p = write_svg([(0, 0), (10, 0), (10, 10), (0, 10)], out_dir, "t.svg", title="P4")
    root = ET.parse(p).getroot()
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    path = root.find("{http://www.w3.org/2000/svg}path")
    assert path is not None
    assert "Z" in path.attrib["d"]
    title = root.find("{http://www.w3.org/2000/svg}title")
    assert title is not None and title.text == "P4"


def test_svg_closed_outline(out_dir):
    p = write_svg([(0, 0), (10, 0), (10, 10), (0, 10)], out_dir, "c.svg")
    root = ET.parse(p).getroot()
    d = root.find("{http://www.w3.org/2000/svg}path").attrib["d"]
    assert d.startswith("M")
    assert d.endswith("Z")


def test_svg_degenerate_bbox_raises(out_dir):
    with pytest.raises(ValueError, match="degenerate"):
        write_svg([(0, 0), (0, 0)], out_dir, "bad.svg")


# --- serialize_feather / serialize_all --------------------------------------


def test_serialize_feather_returns_paths(out_dir):
    res = serialize_feather(row("P4"), out_dir)
    assert set(res) == {"dxf", "svg"}
    for kind, p in res.items():
        assert os.path.exists(p)
        assert p.endswith(f".{kind}")
    assert res["dxf"].endswith("P4.dxf")
    assert res["svg"].endswith("P4.svg")


def test_serialize_all_covers_every_feather(out_dir):
    res = serialize_all(FEATHERS["feathers"], out_dir)
    assert set(res) == {f["id"] for f in FEATHERS["feathers"]}
    assert len(res) == len(FEATHERS["feathers"])
    # spot check a lit + an unlit feather both exist
    assert "P4" in res and "BC8" in res


def test_serialize_all_outputs_parseable(out_dir):
    res = serialize_all(FEATHERS["feathers"], out_dir)
    import ezdxf

    for fid, paths in res.items():
        doc = ezdxf.readfile(paths["dxf"])
        pls = list(doc.modelspace().query("LWPOLYLINE"))
        assert len(pls) == 1, fid
        assert pls[0].dxf.layer == row(fid)["group"], fid
        ET.parse(paths["svg"])


def test_serialize_feather_layer_matches_group(out_dir):
    import ezdxf

    res = serialize_feather(row("GC5"), out_dir)
    doc = ezdxf.readfile(res["dxf"])
    assert doc.modelspace().query("LWPOLYLINE")[0].dxf.layer == "GC"


def test_serialize_with_adjustment(out_dir):
    res0 = serialize_feather(row("P4"), out_dir)
    p0 = res0["dxf"]
    with open(p0, "rb") as fh:
        content0 = fh.read()
    # serialize again with a different adjustment into the same dir — the
    # returned path is the same but the file content must differ
    res1 = serialize_feather(row("P4"), out_dir, vane_ratio_adjustment=-0.5)
    assert p0 == res1["dxf"]
    with open(res1["dxf"], "rb") as fh:
        content1 = fh.read()
    assert content0 != content1
    assert os.path.exists(res1["svg"])
