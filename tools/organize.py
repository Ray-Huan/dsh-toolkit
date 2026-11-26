#!/usr/bin/env python3
"""整理杂乱文件夹：按类型/日期归类，支持试运行与撤销。

用法：
  python organize.py <目录>                 # 试运行，只打印计划
  python organize.py <目录> --apply         # 真整理
  python organize.py <目录> --by date       # 按修改日期分到 2026-11 这种目录
  python organize.py <目录> --apply --undo  # 撤销上一次整理

无第三方依赖，Windows/macOS/Linux 通用。
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

KINDS = {
    "图片": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic", ".svg"},
    "视频": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"},
    "音频": {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"},
    "文档": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md"},
    "压缩包": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "安装包": {".exe", ".msi", ".dmg", ".apk", ".deb"},
    "代码": {".py", ".js", ".ts", ".json", ".yml", ".yaml", ".html", ".css", ".sh", ".ps1"},
}
SKIP_DIRS = {"图片", "视频", "音频", "文档", "压缩包", "安装包", "代码", "其他"}


def kind_of(p: Path) -> str:
    ext = p.suffix.lower()
    for name, exts in KINDS.items():
        if ext in exts:
            return name
    return "其他"


def target_dir(root: Path, p: Path, by: str) -> Path:
    if by == "date":
        return root / time.strftime("%Y-%m", time.localtime(p.stat().st_mtime))
    return root / kind_of(p)


def unique(dst: Path) -> Path:
    if not dst.exists():
        return dst
    stem, suffix = dst.stem, dst.suffix
    i = 1
    while True:
        cand = dst.with_name(f"{stem} ({i}){suffix}")
        if not cand.exists():
            return cand
        i += 1


def collect(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.iterdir()):
        if p.is_dir():
            if p.name in SKIP_DIRS:
                continue
            continue
        if p.name.startswith(".") or p.name == "organize_undo.json":
            continue
        out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--by", choices=["type", "date"], default="type")
    ap.add_argument("--undo", action="store_true")
    args = ap.parse_args()

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"目录不存在：{root}")
        return 2

    undo_file = root / "organize_undo.json"

    if args.undo:
        if not undo_file.exists():
            print("没有找到撤销记录。")
            return 1
        records = json.loads(undo_file.read_text(encoding="utf-8"))
        for rec in reversed(records):
            src, dst = Path(rec["from"]), Path(rec["to"])
            if dst.exists():
                shutil.move(str(dst), str(unique(src)))
        undo_file.unlink()
        for d in sorted(root.iterdir(), reverse=True):
            if d.is_dir() and d.name in SKIP_DIRS or (d.is_dir() and d.name[:4].isdigit() and "-" in d.name):
                try:
                    d.rmdir()
                except OSError:
                    pass
        print(f"已撤销 {len(records)} 个文件。")
        return 0

    files = collect(root)
    if not files:
        print("这个目录里没有需要整理的文件。")
        return 0

    plan, records = [], []
    for p in files:
        dst = unique(target_dir(root, p, args.by) / p.name)
        plan.append((p, dst))
        records.append({"from": str(p), "to": str(dst)})

    for src, dst in plan:
        print(f"{src.name}  ->  {dst.relative_to(root)}")

    print(f"\n共 {len(plan)} 个文件。")
    if not args.apply:
        print("这是试运行，加 --apply 才会真的移动。")
        return 0

    for src, dst in plan:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    undo_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print("整理完成。要撤销就加 --undo。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
