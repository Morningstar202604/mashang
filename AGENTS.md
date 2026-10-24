# 码上 · Mashang — 仓库开发说明

赛博朋克风离线编程学习终端（Android，内置 CPython 3.13 + Rhino JavaScript），附浏览器端（Pyodide）。产品说明见 `README.zh-CN.md`，架构与契约见 `ARCHITECTURE.md`，设计规范见 `BRAND_GUIDELINES.md`。

## 技术栈锁定（勿随意变更）

Chaquopy **17.0.0** 与 AGP **8.13.2** / Kotlin **2.4.10** / Gradle **9.5.0**（wrapper 锁定）精确匹配。任何一项升级前必须核对 [Chaquopy 兼容表](https://chaquo.com/chaquo/current/android.html)（17.0 支持 AGP 7.3.x–9.2.x、Python 3.13）。

- JDK 17（`JAVA_HOME`）
- Android SDK：compileSdk 36 / targetSdk 35 / build-tools 36.0.0（`ANDROID_HOME`）
- 模拟器验收：`./gradlew :app:assembleDebug -PemulatorAbi=true`（Chaquopy 只读 defaultConfig 的 abiFilters，默认只打 arm64-v8a）
- 仓库链：阿里云镜像 → google() → mavenCentral() 三级回退（`settings.gradle.kts`）

## 常用命令

```bash
./gradlew :app:assembleDebug              # Debug APK → app/build/outputs/apk/debug/
./gradlew :app:assembleRelease            # 签名 release（需 KEYSTORE_PATH 等 4 个环境变量）
python -m unittest discover -s tests -v   # 桌面单元测试（runner.py / repl.py / 内容 / CI 契约）
python tests/validate_content.py          # 课程 × 答案全量判题校验
python web/gen_data.py                    # 重新生成 web/data.js + engine.js
python tools/sync_pages_assets.py         # 同步 catalog / 课程包 / 网页端到 docs/（Pages）
python tools/check_links.py               # 页面相对链接检查
python tools/make_brand_assets.py         # 重建 banner / 海报 / OG 图
```

- `tests/` 用例自行把 `app/src/main/python` 加入 `sys.path`，不要改动该机制。
- Python 引擎改动后必须跑桌面测试并重新生成网页端；UI/构建改动必须 `./gradlew :app:assembleDebug` 验证。

## 验证契约（完成任何代码任务前）

1. 相关测试真实运行通过（引用退出码与关键输出作为证据）
2. `python tests/validate_content.py` 0 失败
3. `./gradlew :app:lintDebug :app:testDebugUnitTest` 通过
4. 图片/页面改动后 `python tools/sync_pages_assets.py && python tools/check_links.py`

## 设计规范

颜色 Token、组件语言（切角卡片/霓虹描边/扫描线/Glitch）严格遵循 `BRAND_GUIDELINES.md` 的色板（Neon Cyan `#00E5FF` / Green `#00FF9C` / Magenta `#FF2D78` / Yellow `#F7FF00` / Bg `#0A0E17` / `#111827` / Dim `#6B7280`），禁止自造色值。

## 工具环境

- Kotlin 由 kotlin-lsp 提供诊断；Python 由 pyright 提供诊断（`pyrightconfig.json`）。
- 模拟器截图坐标必须先用 `uiautomator dump` 取真实 bounds；`adb shell input text` 遇空格写 `%s`，含括号/引号的代码用带引号包裹的单参数形式。
