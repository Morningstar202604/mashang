# 变更记录 · Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。完整发布说明见 [GitHub Releases](https://github.com/badhope/mashang/releases)。

## [Unreleased]

## [0.4.0] - 2026-10-24

### Added
- **网页版（第二端）**：`web/` 纯前端 + Pyodide 0.29.5（CPython 3.13.2），与 App 共用同一套课程 JSON 与同一份 `runner.py`
  - 执行放入 **Web Worker**，15 秒超时强制终止，页面不再被用户死循环冻结
  - 进度 / XP 存 `localStorage`，hash 路由（`#/lesson/l01`、`#/challenge/c01`）刷新与分享可恢复
  - 补齐 `fill` 填空块、章节分组、语言筛选、明暗主题、移动端折叠导航、键盘与读屏可用性
  - 全部用户/课程文本改用 `textContent` 渲染，修复 REPL 输出导致的 DOM XSS
  - 引擎加载失败提供「重试 / 仅浏览课程」两条路径，不再整页卡死
- **应用内检查更新**：设置页读取 GitHub Releases 公开版本号，仅提示 + 打开发布页，不自动下载、不申请安装权限（`utils/UpdateChecker.kt` + JVM 单测）
- **真实课程路线页**：`TrackRepository` 改为按实际装载内容生成（Python 主线 38 讲 / JS 6 讲 / DSA 10 讲 / 彩蛋 1 讲），未下载的包显示「可下载」并跳内容中心；删除 20 条虚构「开发中 x%」占位轨道与「建设中」页
- **内容中心三级源**：GitHub Pages → GitHub raw → GitCode API；新增 `tools/sync_pages_assets.py` 把 catalog、课程包、网页端镜像进 `docs/` 并逐字节校验
- **文档体系**：新增 `ARCHITECTURE.md`（架构、契约、测试布局、已知边界）、`FAQ.md`、`ROADMAP.md`；重写 `SECURITY.md`（威胁模型 / 支持版本 / 响应时限）、`CONTRIBUTING.md`（环境、验证命令、内容规范）、`CODE_OF_CONDUCT.md`（执行流程与联系人）；Issue 模板补环境字段与 `config.yml`
- **展示资产**：全部截图按 v0.4.0 实机重拍（1080×2400，16 张）；重制 `docs/banner.png`、`demo/promo-poster.jpg`、OG 分享图；宣传片压到 3.0 MB、官网演示片压到 1.3 MB；`tools/make_brand_assets.py` 可重复生成

### Changed
- 版本 0.3.8 → **0.4.0**（versionCode 14 → 15）
- 课程幕次修正：27-30 归「第四幕 · 边界之外」、31-38 归「第五幕 · 生产实战」（原 31-38 与 27-30 同为第 4 幕，导致五幕结构实际只有四幕）
- 判题契约升级：`check_exercise` 向用例注入 `__stdout__` / `__stderr__`，l01 起要求真正 `print` 出内容（原实现只赋值不输出也能过关）
- 毕业 / 首页 / 课程详情进度统一按 `LessonRepository.mainline()`（`l01..l38`）统计，下载的 DSA 包不再把「x/38」变成「x/49」
- 应用内外链改指 GitHub 主仓；隐私政策 / 用户协议指向 Pages 稳定地址
- 官网 `docs/index.html`：移动端折叠导航、Hero SVG 等比、OG/Twitter/JSON-LD、统计口径改为 63 判题项 / 230 用例、修正「限时挑战」「赛博黑客」「1/3/7 天复习」「8 模块全离线」等不实表述，新增网页版区块与入口

### Fixed
- 判题失败时控制台重复叠加「TestFailed」与「代码运行出错」两块红色面板；`TestFailed` 现在只显示一次并给出可执行建议
- 证书页生成海报后无任何反馈（原 `TODO`），现在成功/失败均有 Toast
- 帮助中心「更新怎么获取」文案与新检查更新链路对齐
- 网页端 REPL 输入 `1+1` / `'a'.upper()` 无回显（改为表达式 eval + repr 回显，语句仍按 exec 执行）
- 网页端点击「下载 App」会抢走导航 active 态（选择器限定 `[data-tab]`）

### Tests
- unittest 128 条全绿；`validate_content.py` 55 个 Python 判题项 / 201 条用例 0 失败
- 新增 `test_ui_static.py::test_tracks_only_lists_real_content`（禁止占位轨道回归）、`UpdateCheckerTest`（3 条语义化版本比较）
- 品牌资产指纹更新为 v0.4.0 重建产物；`test_web_sync` 读文件改为 `with open`（消除 ResourceWarning）
- Playwright 真实浏览器验收：引擎在线、课程 38 讲 / 5 幕、填空判题、XSS 注入无效、REPL 状态与回显、移动端 390px 无横向溢出、深链刷新恢复
- 模拟器验收：首页 / 课程 / 详情 / 判题通过 +140XP / 判题失败面板 / Python+JS 终端 / 角斗场 / 路线页 / 内容中心下载 / 设置检查更新

## [0.3.8] - 2026-10-23

### Added
- JavaScript 运行时（Rhino 1.7.15，解释模式）与 6 讲语言包；`LanguageRuntime` 抽象 + 语言切换 UI
- L0 离线规则教练、错题本 + SM-2 复习、7 套主题 + 自定义主色
- 内容中心课程包：彩蛋 1 讲、DSA 基础/进阶各 5 讲、JavaScript 启程 6 讲（共 17 讲）

### Fixed
- 界面巡检 12 项（GlitchText 重影、连击台滚动、IME 自动大写、Rhino 错误双前缀等）
- 「备份/恢复」路由未注册导致点击闪退；毕业口径被扩展包污染；catalog sha256 的 CRLF 陷阱

> 更早版本（0.3.7 及以前）见 git 历史与 GitHub Releases。
