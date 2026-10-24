# 贡献指南 · Contributing

感谢关注「码上 · Mashang」！这是一个 Kotlin + Jetpack Compose 的 Android 离线编程学习终端，附浏览器端（Pyodide）。欢迎课程内容、Bug 修复、UI 打磨、多语言翻译与文档改进。

## 环境准备

| 工具 | 版本 | 用途 |
|---|---|---|
| JDK | 17 | Gradle / Kotlin 编译 |
| Android SDK | compileSdk 36 / build-tools 36.0.0 | 构建 APK |
| Python | 3.13 | 引擎测试与内容校验 |
| Node.js | 20+ | JS 课程判题测试 |

Chaquopy **17.0.0** 与 AGP **8.13.2**、Kotlin **2.4.10**、Gradle **9.5.0** 精确匹配，升级任一项前必须核对 [Chaquopy 兼容表](https://chaquo.com/chaquo/current/android.html)。

## 提交流程

1. Fork → 从 `main` 拉分支（`feat/xxx`、`fix/xxx`、`content/xxx`）
2. 改动 + 本地验证（见下）
3. 一个 PR 聚焦一件事，描述里写清「为什么」与「怎么验证」
4. CI 全绿后合并；不要 force-push 共享分支

## 本地验证

```bash
# Python 引擎 + 内容（128 条，必须全绿）
python -m unittest discover -s tests -v
python tests/validate_content.py

# 网页端与 App 内容/引擎同源
python web/gen_data.py
python tools/sync_pages_assets.py
git diff --exit-code -- web/data.js web/engine.js docs/web docs/catalog.json

# Android
./gradlew :app:lintDebug :app:testDebugUnitTest :app:assembleDebug
```

## 课程内容

1. 在 `app/src/main/assets/lessons_*.json` 新增或修改课程块（结构见 `ARCHITECTURE.md` 第 3 节）
2. 在 `tests/validate_content.py` 的 `SOLUTIONS` 中补充参考答案
3. 运行 `python tests/validate_content.py`，必须 **55 个判题项、201 条用例全 PASS、0 结构问题**
4. 练习 `tests` 使用 assert；**禁止只断言变量存在** —— 需要验证输出时用 `__stdout__`（例如 `assert name in __stdout__`）
5. 内容包修改后必须重算 `catalog.json`：`python tools/update_catalog.py` 并提交新的 sha256

## 代码约定

- Kotlin：跟随现有 Compose 写法；新 UI 组件放 `ui/components`；不要绕过 `LanguageRuntime` 直接调用 `PyBridge`
- Python 引擎：只改 `app/src/main/python/runner.py`，然后 `python web/gen_data.py` 同步网页端
- 不引入新的第三方 Python 包（保持构建零 PyPI 依赖）；Android 新依赖需说明包体与构建代价
- 提交信息：`feat:` / `fix:` / `docs:` / `content:` / `chore:`

## 安全

keystore、密码、token 一律不得进入仓库（`.gitignore` 已拦截常见文件名）。发现泄露请直接发私密安全报告，见 [SECURITY.md](SECURITY.md)。

## 发布流程（维护者）

1. 按 SemVer 定版本；`app/build.gradle.kts` 的 `versionName`/`versionCode` 是唯一来源
2. 更新 `CHANGELOG.md` 与三语 README 中的版本/截图
3. 本地跑完上面的验证清单
4. 合入 `main`，CI 全绿
5. `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
6. GitHub Actions 自动签名构建、验签（`CN=Mashang`）、创建 Release；`mirror-sync` 推送 GitCode / Gitee / 两个 GitHub 镜像
7. 确认 Pages 部署完成：<https://badhope.github.io/mashang/>

变更记录以 GitHub Releases 与 `CHANGELOG.md` 为准。
