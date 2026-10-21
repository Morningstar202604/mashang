"""发布前版本一致性校验（fail-closed）。

- tag 必须是 v<major>.<minor>.<patch>
- tag 必须等于 app/build.gradle.kts 的 versionName
- versionCode 必须比「上一个 tag」对应提交里的 versionCode 更大
用法：在 tag 触发的 CI 中运行（需要 GITHUB_REF_NAME，本地可用 --tag 指定）。
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

GRADLE = Path("app/build.gradle.kts")
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def read_version(text):
    name = re.search(r'versionName\s*=\s*"([^"]+)"', text)
    code = re.search(r"versionCode\s*=\s*(\d+)", text)
    if not name or not code:
        sys.exit("无法从 app/build.gradle.kts 解析 versionName/versionCode")
    return name.group(1), int(code.group(1))


def version_code_at(ref):
    try:
        text = subprocess.run(
            ["git", "show", f"{ref}:app/build.gradle.kts"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    _, code = read_version(text)
    return code


def previous_tag(current):
    out = subprocess.run(
        ["git", "tag", "--sort=-v:refname"], capture_output=True, text=True,
    ).stdout.split()
    tags = [t for t in out if TAG_RE.match(t) and t != current]
    return tags[0] if tags else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default=os.environ.get("GITHUB_REF_NAME", ""))
    args = parser.parse_args()
    tag = args.tag.strip()
    if not tag:
        sys.exit("缺少 tag（GITHUB_REF_NAME 或 --tag）")

    if not TAG_RE.match(tag):
        sys.exit(f"tag 格式错误：{tag}（需 v<major>.<minor>.<patch>）")

    version_name, version_code = read_version(GRADLE.read_text(encoding="utf-8"))
    if tag != f"v{version_name}":
        sys.exit(f"tag {tag} 与 versionName {version_name} 不一致（应为 v{version_name}）")
    print(f"tag={tag} versionName={version_name} versionCode={version_code}")

    prev = previous_tag(tag)
    if prev:
        prev_code = version_code_at(prev)
        if prev_code is not None and version_code <= prev_code:
            sys.exit(
                f"versionCode 未递增：当前 {version_code} <= 上一版 {prev} 的 {prev_code}"
            )
        print(f"versionCode 递增检查通过（{prev}: {prev_code} -> {version_code}）")
    else:
        print("没有更早的 tag，跳过递增检查")


if __name__ == "__main__":
    main()
