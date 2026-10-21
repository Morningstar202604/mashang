#!/usr/bin/env bash
# 在 Linux CI 上准备 Android SDK（GitHub runner 预装但版本可能不足；
# GitCode / Gitee 的托管 Runner 未预装，需要自行安装）。
# 幂等：已存在所需组件时直接复用，只补齐缺失部分。
set -euo pipefail

SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/android-sdk}}"
CMDLINE_ROOT="$SDK_ROOT/cmdline-tools/latest"
SDKMANAGER="$CMDLINE_ROOT/bin/sdkmanager"

need_pkg() {
  "$SDKMANAGER" --list_installed 2>/dev/null | awk '{print $1}' | grep -qx "$1" && return 1 || return 0
}

if [ ! -x "$SDKMANAGER" ]; then
  echo "==> 安装 Android cmdline-tools 到 $SDK_ROOT"
  mkdir -p "$SDK_ROOT/cmdline-tools"
  TMP_ZIP="$(mktemp -d)/cmdline-tools.zip"
  curl -fsSL --retry 3 -o "$TMP_ZIP" \
    https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
  unzip -q "$TMP_ZIP" -d "$SDK_ROOT/cmdline-tools"
  rm -rf "$CMDLINE_ROOT"
  mv "$SDK_ROOT/cmdline-tools/cmdline-tools" "$CMDLINE_ROOT"
fi

export ANDROID_SDK_ROOT="$SDK_ROOT"
export ANDROID_HOME="$SDK_ROOT"

yes | "$SDKMANAGER" --licenses > /dev/null 2>&1 || true

PACKAGES=()
need_pkg "platform-tools" && PACKAGES+=("platform-tools")
need_pkg "platforms;android-36" && PACKAGES+=("platforms;android-36")
need_pkg "build-tools;36.0.0" && PACKAGES+=("build-tools;36.0.0")

if [ ${#PACKAGES[@]} -gt 0 ]; then
  echo "==> 安装 SDK 组件: ${PACKAGES[*]}"
  "$SDKMANAGER" --install "${PACKAGES[@]}"
else
  echo "==> SDK 组件已齐备"
fi

printf 'sdk.dir=%s\n' "$SDK_ROOT" > local.properties
echo "ANDROID_SDK_ROOT=$ANDROID_SDK_ROOT"
"$SDKMANAGER" --list_installed | head -20
