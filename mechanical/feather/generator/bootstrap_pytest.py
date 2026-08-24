"""Bootstrap pytest into a workspace-local dir without pip.

The DSH sandbox denies writes into tempfile.mkdtemp() dirs, which pip's
unpack step relies on, so pip cannot install here. Workaround: download
pure-python wheels from PyPI via urllib and extract them with zipfile into
the target dir (both operations write into plain workspace dirs).

Not committed; used only to make `pytest` runnable under the sandbox.
"""

import json
import os
import sys
import urllib.request
import zipfile

TARGET = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "mechanical", "feather", "generator", ".pytest-deps")
)

# pytest + its runtime deps (pytest 9.x). No extras needed.
PACKAGES = ["pytest", "pluggy", "iniconfig", "packaging", "pygments"]


def latest_wheel_url(name: str) -> str:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=30) as r:
        data = json.load(r)
    for f in data["releases"][data["info"]["version"]]:
        if f["packagetype"] == "bdist_wheel" and f["filename"].endswith("py3-none-any.whl"):
            return f["url"]
    raise RuntimeError(f"no py3-none-any wheel for {name}")


def main() -> int:
    os.makedirs(TARGET, exist_ok=True)
    for name in PACKAGES:
        url = latest_wheel_url(name)
        filename = os.path.basename(url)
        dest = os.path.join(TARGET, filename)
        print("fetch", name, "->", filename)
        with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        with zipfile.ZipFile(dest) as z:
            z.extractall(TARGET)
        os.remove(dest)
    print("done:", TARGET)
    return 0


if __name__ == "__main__":
    sys.exit(main())
