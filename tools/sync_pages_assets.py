#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把内容中心需要的目录与课程包同步到 docs/（GitHub Pages 发布目录）。

内容中心的三级回退源：
  1. https://badhope.github.io/mashang/catalog.json      ← 本脚本产物
  2. https://raw.githubusercontent.com/badhope/mashang/main/catalog.json
  3. https://api.gitcode.com/api/v5/repos/badhope/mashang/raw/catalog.json

Pages 源是 CDN、免鉴权、对移动网络最稳；GitCode 源作为兜底。
生成后做逐字节校验：Pages 副本必须与仓库根同源文件一致，否则 CI 直接失败。
"""
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PACKS = ROOT / "content_packs"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync() -> list[str]:
    problems: list[str] = []
    catalog_src = ROOT / "catalog.json"
    catalog_dst = DOCS / "catalog.json"
    if not catalog_src.exists():
        problems.append("缺少 catalog.json")
    else:
        catalog_dst.write_bytes(catalog_src.read_bytes())
        if sha256(catalog_src) != sha256(catalog_dst):
            problems.append("catalog.json 同步后哈希不一致")

    packs_dst = DOCS / "content_packs"
    packs_dst.mkdir(exist_ok=True)
    expected = {p.name for p in PACKS.glob("*.json")}
    for src in sorted(PACKS.glob("*.json")):
        dst = packs_dst / src.name
        dst.write_bytes(src.read_bytes())
        if sha256(src) != sha256(dst):
            problems.append(f"{src.name} 同步后哈希不一致")
    for stale in packs_dst.glob("*.json"):
        if stale.name not in expected:
            stale.unlink()
            print(f"removed stale {stale.relative_to(ROOT)}")

    # 网页版（在线试玩）：整目录镜像到 docs/web/，与根 web/ 逐字节一致
    web_src = ROOT / "web"
    web_dst = DOCS / "web"
    web_dst.mkdir(exist_ok=True)
    for name in ("index.html", "app.js", "style.css", "data.js", "engine.js", "robots.txt"):
        src = web_src / name
        if not src.exists():
            problems.append(f"web/{name} 缺失")
            continue
        (web_dst / name).write_bytes(src.read_bytes())
        if sha256(src) != sha256(web_dst / name):
            problems.append(f"web/{name} 同步后哈希不一致")

    # catalog 里登记的每个包都必须在 Pages 目录存在，且 sha256 与文件一致
    if catalog_src.exists():
        catalog = json.loads(catalog_src.read_text(encoding="utf-8"))
        for pack in catalog.get("packs", []):
            f = packs_dst / f"{pack['id']}.json"
            if not f.exists():
                problems.append(f"catalog 登记的 {pack['id']} 在 docs/content_packs 缺失")
                continue
            digest = sha256(f)
            if digest != pack.get("sha256"):
                problems.append(f"{pack['id']} sha256 与 catalog 不符（{digest[:12]}…）")
    return problems


def main() -> int:
    problems = sync()
    if problems:
        print("同步失败：")
        for p in problems:
            print(" -", p)
        return 1
    print("OK docs/catalog.json + docs/content_packs/ + docs/web/ 已同步")
    return 0


if __name__ == "__main__":
    sys.exit(main())
