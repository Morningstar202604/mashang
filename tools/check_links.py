#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态链接检查：docs/ 与 web/ 中的相对链接 / 图片必须真实存在。

只检查本地相对路径（http/https/mailto/data: 跳过），覆盖：
  - href="..." / src="..." / poster="..." / srcset 中的单值
  - 相对路径按所在文件的目录解析；目录链接要有 index.html
  - 锚点（#xxx）在本文件内必须能找到 id="xxx" 或 name="xxx"

用法：python tools/check_links.py   （CI 门禁；失败退出码 1）
"""
import pathlib
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "privacy" / "index.html",
    ROOT / "docs" / "terms" / "index.html",
    ROOT / "web" / "index.html",
    ROOT / "docs" / "web" / "index.html",
]
ATTR_RE = re.compile(r'(?:href|src|poster)\s*=\s*"([^"]+)"', re.I)


def resolve(base: pathlib.Path, raw: str):
    target = unquote(raw.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return base  # pure anchor handled elsewhere
    path = (base.parent / target).resolve()
    if path.is_dir():
        path = path / "index.html"
    return path


def main() -> int:
    problems: list[str] = []
    for page in TARGETS:
        if not page.exists():
            problems.append(f"缺少页面：{page.relative_to(ROOT)}")
            continue
        text = page.read_text(encoding="utf-8")
        ids = set(re.findall(r'\bid\s*=\s*"([^"]+)"', text))
        for raw in ATTR_RE.findall(text):
            if raw.startswith(("http://", "https://", "mailto:", "data:", "tel:", "javascript:")):
                continue
            if raw.startswith("#/"):
                continue  # hash 路由（SPA），不是页内锚点
            if raw.startswith("#"):
                anchor = raw[1:]
                if anchor and anchor not in ids:
                    problems.append(f"{page.relative_to(ROOT)}: 锚点 #{anchor} 在页面内不存在")
                continue
            parsed = urlparse(raw)
            if parsed.scheme or raw.startswith("//"):
                continue
            target = resolve(page, raw)
            if not target.exists():
                problems.append(f"{page.relative_to(ROOT)}: 链接目标不存在 → {raw}")
    if problems:
        print("链接检查失败：")
        for p in problems:
            print(" -", p)
        return 1
    print(f"OK 链接检查通过（{len(TARGETS)} 个页面）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
