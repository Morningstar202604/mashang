#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 catalog.json 的顶层 "app"（APK 自更新）段，并重算目录自签名 sha256。

用法:
  python3 tools/update_catalog.py --version-name 0.3.8 --version-code 14 \
      --apk-url releases/pynow-0.3.8.apk --apk-sha256 <64hex>

说明:
- catalog 自签名机制: 剥离顶层 "sha256" 字段后对原文做 SHA-256（与
  app/src/main/java/.../ContentCenter.kt 的 stripSelfSha 完全一致）。
- 运行后请把对应 APK 上传/提交到 apk-url 指向的位置。
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "catalog.json"
SHA_FIELD = re.compile(r'"sha256"\s*:\s*"[0-9a-f]{64}"')


def strip_self_sha(text: str) -> str:
    """与 ContentCenter.stripSelfSha 完全一致：只剥离【第一次出现】的 64 位 hex
    sha256 字段（即顶层目录签名），packs[].sha256 等子字段保留原值并进入签名
    覆盖范围——若替换全部 sha256 字段，目录对"篡改各包哈希"将失去校验能力，
    且 packs[].sha256 会被清空导致内容中心拒绝下载（2026-10-19 回归测试锁定）。"""
    return SHA_FIELD.sub('"sha256": ""', text, count=1)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--version-name", required=True)
    p.add_argument("--version-code", required=True, type=int)
    p.add_argument("--apk-url", required=True)
    p.add_argument("--apk-sha256", required=True)
    args = p.parse_args()

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    data["app"] = {
        "versionCode": args.version_code,
        "versionName": args.version_name,
        "apkUrl": args.apk_url,
        "apkSha256": args.apk_sha256,
    }
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    new_sha = hashlib.sha256(strip_self_sha(text).encode("utf-8")).hexdigest()
    # 重新注入自签名
    final = SHA_FIELD.sub(f'"sha256": "{new_sha}"', text, count=1)
    CATALOG.write_text(final, encoding="utf-8")
    print(f"OK {CATALOG}  app={args.version_name}({args.version_code})  sha256={new_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
