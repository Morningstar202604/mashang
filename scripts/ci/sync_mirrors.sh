#!/usr/bin/env bash
# 把当前 commit 推送到四个镜像仓（GitCode / Gitee / GitHub X33834 / GitHub Morningstar202604）。
# 只在 badhope 主仓的 CI 中运行（其余仓不配置这些 Secrets，脚本直接跳过）。
#
# 需要环境变量（GitHub Secrets）：
#   MIRROR_GITCODE_TOKEN / MIRROR_GITEE_TOKEN
#   MIRROR_GH_X33834_TOKEN / MIRROR_GH_MORNINGSTAR_TOKEN
set -euo pipefail

if [ -z "${MIRROR_GITCODE_TOKEN:-}" ]; then
  echo "未配置镜像凭据，跳过（本仓不是主仓）"
  exit 0
fi

SHA="$(git rev-parse HEAD)"
echo "sync mirrors for $SHA"

# git 需要一个"待推送"的 ref：CI checkout 是 detached HEAD，先建本地分支
git checkout -q -B ci-sync "$SHA"

push_one() {
  local label="$1" url="$2"
  echo "==> $label"
  git -c credential.helper= push --force "$url" ci-sync:refs/heads/main
}

push_one "GitCode"            "https://oauth2:${MIRROR_GITCODE_TOKEN}@gitcode.com/badhope/mashang.git"
push_one "Gitee"              "https://oauth2:${MIRROR_GITEE_TOKEN}@gitee.com/badhope/mashang.git"
push_one "GitHub X33834"      "https://X33834:${MIRROR_GH_X33834_TOKEN}@ghfast.top/https://github.com/X33834/mashang"
push_one "GitHub Morningstar" "https://Morningstar202604:${MIRROR_GH_MORNINGSTAR_TOKEN}@ghfast.top/https://github.com/Morningstar202604/mashang"

echo "all mirrors synced to $SHA"
