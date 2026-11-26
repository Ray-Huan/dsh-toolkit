#!/usr/bin/env python3
"""列表页采集：把网页里的列表抓成 CSV / Excel。

不依赖第三方库（xlsx 需要 openpyxl，没有就只出 CSV）。

用法示例
--------
1) 先看结构：
   python scrape.py https://example.com/list --dump

2) 用选择器抓：
   python scrape.py https://example.com/list ^
       --item "div.item" ^
       --field "title=span.title" ^
       --field "price=span.price" ^
       --field "link=a@href" ^
       --out result.csv

选择器语法
----------
  tag            标签名
  tag.cls        带某个 class
  tag.cls1.cls2  带多个 class
  *              任意标签
  a@href         取属性（写在 field 值里）
  text           取文本（默认）

参数
----
  --item          每条记录的容器选择器
  --field k=sel   字段名=选择器，可重复
  --limit N       最多抓多少条
  --delay 0.5     每次请求间隔（秒）
  --pages N       翻页页数（配合 --page-param）
  --page-param p  页码参数名，例如 page
  --out FILE      输出文件（.csv 或 .xlsx）
  --dump          只打印页面里出现最多的 class，帮你找选择器
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text_parts")

    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.parent = parent
        self.text_parts = []

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def text(self):
        out = list(self.text_parts)
        for c in self.children:
            out.append(c.text())
        return re.sub(r"\s+", " ", "".join(out)).strip()

    def descendants(self):
        for c in self.children:
            yield c
            yield from c.descendants()


VOID = {"br", "img", "input", "meta", "link", "hr", "source", "area", "base", "col", "embed", "track", "wbr"}


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [])
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs, self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].text_parts.append(data)


def parse_selector(sel: str):
    attr = None
    if "@" in sel:
        sel, attr = sel.split("@", 1)
    sel = sel.strip()
    if sel in ("", "*"):
        return None, set(), attr
    parts = sel.split(".")
    tag = parts[0] or None
    return tag, set(p for p in parts[1:] if p), attr


def match(node: Node, tag, classes) -> bool:
    if node.tag == "#root":
        return False
    if tag and node.tag != tag:
        return False
    if classes and not classes.issubset(node.classes):
        return False
    return True


def select_all(root: Node, selector: str):
    tag, classes, _ = parse_selector(selector)
    return [n for n in root.descendants() if match(n, tag, classes)]


def field_value(node: Node, selector: str) -> str:
    tag, classes, attr = parse_selector(selector)
    if selector.strip() in ("", "*", "self"):
        target = node
    else:
        hits = [n for n in node.descendants() if match(n, tag, classes)]
        target = hits[0] if hits else None
    if target is None:
        return ""
    if attr:
        val = target.attrs.get(attr, "")
        if attr == "href" and val.startswith("/"):
            val = val  # 相对链接保留原样
        return val.strip()
    return target.text()


def fetch(url: str, timeout=20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def dump_classes(root: Node):
    counts = {}
    for n in root.descendants():
        for c in n.classes:
            counts[c] = counts.get(c, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:40]
    print("页面里出现最多的 class（次数 / 名字）：")
    for name, n in top:
        print(f"{n:5d}  .{name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--item", default="")
    ap.add_argument("--field", action="append", default=[])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--page-param", default="page")
    ap.add_argument("--out", default="result.csv")
    ap.add_argument("--dump", action="store_true")
    args = ap.parse_args()

    fields = []
    for f in args.field:
        if "=" not in f:
            print(f"字段写法应为 名字=选择器：{f}")
            return 2
        k, v = f.split("=", 1)
        fields.append((k.strip(), v.strip()))

    rows = []
    for page in range(1, max(1, args.pages) + 1):
        url = args.url
        if args.pages > 1:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{args.page_param}={page}"
        try:
            html = fetch(url)
        except Exception as e:  # noqa: BLE001
            print(f"抓取失败：{url} -> {e}")
            break

        tb = TreeBuilder()
        tb.feed(html)

        if args.dump:
            dump_classes(tb.root)
            return 0

        if not args.item:
            print("缺少 --item，先用 --dump 看看结构。")
            return 2

        nodes = select_all(tb.root, args.item)
        print(f"第 {page} 页：找到 {len(nodes)} 条")
        for n in nodes:
            row = {k: field_value(n, sel) for k, sel in fields}
            if any(v for v in row.values()):
                rows.append(row)
            if args.limit and len(rows) >= args.limit:
                break
        if args.limit and len(rows) >= args.limit:
            break
        time.sleep(args.delay)

    if not rows:
        print("没抓到数据，检查选择器。")
        return 1

    headers = [k for k, _ in fields]
    if args.out.lower().endswith(".xlsx"):
        try:
            from openpyxl import Workbook
        except ImportError:
            print("没有 openpyxl，改输出 CSV。")
            args.out = args.out.rsplit(".", 1)[0] + ".csv"
    if args.out.lower().endswith(".xlsx"):
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append([r.get(h, "") for h in headers])
        wb.save(args.out)
    else:
        with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(rows)

    print(f"已写入 {args.out}，共 {len(rows)} 条。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
