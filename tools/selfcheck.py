#!/usr/bin/env python3
"""Smoke test: runs both tools on throwaway directories. No network.

    python tools/selfcheck.py
"""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable


def run(args, cwd=None):
    p = subprocess.run([PY, *args], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def test_organize() -> None:
    root = Path(tempfile.mkdtemp(prefix="org-"))
    try:
        (root / "note.txt").write_text("x", encoding="utf-8")
        (root / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (root / "doc.pdf").write_bytes(b"%PDF-1.4")

        code, out = run([str(HERE / "organize.py"), str(root), "--apply"])
        assert code == 0, out
        moved = [p for p in root.rglob("*") if p.is_file() and p.parent != root]
        assert len(moved) >= 3, f"expected files moved, got {moved}"

        code, out = run([str(HERE / "organize.py"), str(root), "--undo"])
        assert code == 0, out
        back = sorted(p.name for p in root.iterdir() if p.is_file())
        assert back == ["doc.pdf", "note.txt", "shot.png"], back
        print("organize: ok")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_scrape() -> None:
    root = Path(tempfile.mkdtemp(prefix="scr-"))
    try:
        html = (
            '<html><body><div class="list">'
            '<div class="item"><span class="title">A</span><span class="price">1.5</span>'
            '<a href="/a">x</a></div>'
            '<div class="item"><span class="title">B</span><span class="price">2.5</span>'
            '<a href="/b">x</a></div>'
            "</div></body></html>"
        )
        page = root / "index.html"
        page.write_text(html, encoding="utf-8")
        url = page.as_uri()
        out_csv = root / "out.csv"

        code, out = run([str(HERE / "scrape.py"), url, "--dump"])
        assert code == 0 and ".item" in out, out

        code, out = run([str(HERE / "scrape.py"), url, "--item", "div.item",
                         "--field", "名称=span.title", "--field", "价格=span.price",
                         "--field", "链接=a@href", "--out", str(out_csv)])
        assert code == 0, out

        with out_csv.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        assert [r["名称"] for r in rows] == ["A", "B"], rows
        assert rows[0]["链接"] == "/a", rows
        print("scrape: ok")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_organize()
    test_scrape()
    print("all checks passed")
