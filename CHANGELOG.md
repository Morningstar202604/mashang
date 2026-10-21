# Changelog

## [Unreleased] - 品牌重塑与多语言架构

### Verified
- **APK 构建通过**（2026-10-20）：本机搭 Android SDK（cmdline-tools + platform-tools + platforms;android-36 + build-tools;36.0.0，许可已接受）后 `./gradlew assembleDebug` BUILD SUCCESSFUL（7m29s，48 tasks）；产物 38.3 MB（arm64-v8a），aapt 元信息验证：applicationId com.pyneon.academy / versionName 0.3.7 / 应用名「码上」/ minSdk 24 / targetSdk 35；dex 内确认 JsBridge / LanguageRuntime / LanguageRegistry / LangChipsKt / Rhino 均已编入；assets 内 JS 语法与挑战数据完整。品牌重塑与多语言全部代码经真实 Kotlin 编译验证
- **签名 release 构建通过**：`KEYSTORE_PATH` 等环境变量注入凭据后 `./gradlew assembleRelease` BUILD SUCCESSFUL（63 tasks，R8 混淆 + 资源压缩 + lintVital + 签名）；apksigner verify PASS；APK 22.1 MB（较 debug −42%），dex 59.7→4.7 MB。**修复一处 R8 裁剪缺口**：`org.mozilla.classfile` 包不在原 keep 范围内会被裁掉（解释模式虽不用编译器，但部分 Rhino 路径引用），keep 规则扩大为 `org.mozilla.**` 后 ClassFileWriter/ContextFactory 均确认在 dex 内

### Changed
- 品牌重塑：「码上Python / PY//NOW」→「码上 / Mashang」，去除单一语言命名；应用内全部文案中立化（终端/开屏/帮助/证书/主题等）
- 课程数量口径统一：内置 38 讲 + 内容中心扩展包 11 讲（README 原「30 讲」与实际数据不符，一并修正）
- 许可表述统一为 MIT（AboutScreen / SettingsScreen 原「非商业许可」文案与 LICENSE 矛盾，已修正）
- **多语言运行时抽象**（新增 `lang/LanguageRuntime.kt`）：
  - `LanguageRuntime` 接口统一 run / check / repl / warmup / ensureStarted 五组能力，跨语言通信沿用既有 JSON 契约，新增语言只需另起一个"说同一种 JSON"的后端
  - `LanguageRegistry` 负责注册 / 当前语言持久化（SharedPreferences）/ 未知 id 回落；`UnsupportedRuntime` 保证 UI 层永不拿到 null，未内置语言以可读错误回显而非崩溃
  - `PyBridge` 改为实现 `LanguageRuntime`，注册于 `PyNeonApp.onCreate`；`RunResult` / `VarInfo` 由 `py` 包迁移至 `lang` 包
  - 6 个界面（Terminal / Home / Profile / Boot / LessonDetail / Arena）全部改走 `LanguageRegistry`，不再直接引用 `PyBridge`
  - 课程数据模型新增 `lang` 字段：`Lesson` / `Challenge` 默认 `python`（旧 JSON 零改动兼容），`Block.CodeBlock.lang` 可显式覆盖以支持"同讲对比两门语言"的教学片段
  - `LessonRepository` 新增 `languages()` / `lessonsByLang()` 供后续语言切换器使用
- `tools/update_catalog.py`：`strip_self_sha` 改为只剥离顶层 sha256（与 Kotlin `ContentCenter.stripSelfSha` 的 replaceFirst 语义一致），原实现会清空全部 packs[].sha256 导致内容中心拒绝下载

### Added
- **JavaScript 运行时落地**（新增 `js/JsBridge.kt`，依赖 `org.mozilla:rhino:1.7.15`，Apache-2.0）：
  - 第二个 `LanguageRuntime` 实现：Rhino 解释模式（`optimizationLevel = -1`，ART 上的硬性要求），指令计数看门狗等价 Python 侧 settrace
  - 结果契约与 runner.py 逐项对齐（ok/stdout/stderr/error/duration_ms/variables/passed）；print / console.log|warn|error / input（stdin 队列）/ assert 宿主函数注入
  - 判题语义对齐 runner.py：用例间共享状态；变量快照先于判题采集，测试赋值不污染面板
  - REPL 支持括号平衡续行、空行强制提交；R8 保留规则补齐 `org.mozilla.javascript.**`
- **语言包 · JavaScript 启程**（`content_packs/js-basics.json`，6 讲 ES5 入门，经内容中心分发，catalog 已登记重签）：
  - 与 Python 课一一对照移植（greet/damage/slugify/access/peak/freq），判题统一 `assert(cond, msg)` + `===`
  - 参考答案直接放在 `exercise.solution`（单一事实源，validate_content 结构检查与 node 判题共用）
- **语言切换 UI**：新增 `ui/components/LangChipRow` 共用组件；终端页可切换运行时（自动重置 REPL 会话），课程列表页按语言过滤
- **编辑器与示例高亮多语言适配**：
  - 新增原创精简语法 `assets/syntaxes/javascript.tmLanguage.json`（plist，scopeName source.js，与 JsBridge.grammarScope 一致；scope 命名与 PyNeon 主题 tokenColors 对齐）
  - `CodeEditor.createEditor` 按 `language` 加载 `syntaxes/<language>.tmLanguage.json`，未内置语法的语言降级纯文本（复用既有降级路径）
  - `buildAnnotatedString`（只读示例正则高亮）支持 javascript：独立关键词/内置表，注释前缀 `#`→`//`
  - 接线：课程练习编辑器与三个内容卡片（CodeExampleCard/PracticeCard/FillCard）按 `lesson.lang` / `block.lang` 取高亮，训练场挑战按 `challenge.lang`
- **训练场 JS 挑战 ×2**（`challenges.json`，lang=javascript，参考答案内嵌 `solution` 字段）：霓虹计数器·JS 版（js-c1）、括号防火墙·JS 版（js-c2）；validate_content 判题分流（Python runner 只跑 Python 挑战）
- 软著登记材料：`tools/softcopy_source.py` 自动生成符合受理要求的源程序册（前 30 页 + 后 30 页、每页 50 行、页眉标注软件名+版本号、仅收录原创文件）；`docs/softcopy/软件说明书.md`（10 章设计说明书）；`docs/softcopy/申请指南.md`（流程、申请表填写模板、前置事项、补正自查）

### Fixed
- catalog.json 中 dsa-basics / dsa-mastery 的 sha256 与文件实际哈希不符（commit 5004113 改内容未同步目录），应用内下载必被完整性校验拦截；已重算并重签目录自签名
- HelpScreen 内置课程数由硬编码 38 改为动态统计；WelcomeTutorial 的「38 讲」等表述随品牌中立化
- 分享标签 `#PY_NOW` 随旧品牌退役，改为 `#码上 #Mashang #编程学习`；`docs/logo.svg` 同步更名为 码上 / MASHANG
- js02 判题期望值勘误：damage(1, 100) = Math.floor(√1) − Math.floor(100/2) = **−49**（原写成 −50），由 node 实跑测试捕获

### CI/CD（2026-10-21）
- **GitHub Actions 重建**（`.github/workflows/ci.yml`）：`python-tests`（unittest discover + 内容校验 + web 生成产物可复现）→ `android-build`（lintDebug 阻断 + assembleDebug + APK 产物探针）→ `release`（tag 触发，Secrets 还原 keystore → 签名构建 → apksigner 验签 + 证书主体断言 → 探针 `--require-release` → 发布）；支持 `workflow_dispatch` 演练模式，不消耗版本号即可验证签名链路
- **GitCode AtomGit Action 流水线**（`.gitcode/workflows/ci.yml`）：同一套门禁；托管 Runner 未预装 Android SDK，新增幂等脚本 `scripts/ci/install_android_sdk.sh`
- **APK 产物探针**（`tests/ci_apk_probe.py`）：校验 app.imy 内 runner/repl 模块（兼容 `.py` / `.pyc` / `__pycache__/*.pyc` 三种 Chaquopy 布局）、threading+settrace 看门狗、课程与挑战 JSON 可解析、JS 语法资源、AXML 包名；`--require-release` 额外校验 dex 与 APK 签名块
- **lint 阻断级错误归零**：`ContentCenter` 的 `ByteArrayOutputStream.toString(Charset)`（API 33）改 `toString("UTF-8")`；`ViewModels` 的 `java.time.LocalDate/ZoneId`（API 26 或 desugaring）改 `Calendar` 折算天序号
- 实测：GitHub 三仓 + GitCode 主仓同一 commit 全部 success；release 演练包 apksigner v2 验签通过（CN=Mashang）

### Web / 桌面端（S9 切片）
- **web 三落后补齐**：`gen_data.py` 收录 `lessons_pro.json`（38 讲全量，原仅前 30 讲）；`engine.js` 引擎随 `runner.py` 重生成；Pyodide 由 0.26.4 升到 **0.29.5（CPython 3.13.2，与手机端 Chaquopy 3.13 对齐）**，`index.html` 主源改 jsdelivr，`app.js` 增 fastly.jsdelivr / unpkg 两级回退
- **修复 web 判题全线不可用**：Pyodide 未启用 SharedArrayBuffer 时 `threading.Thread.start()` 抛 `RuntimeError: can't start new thread`，导致任何运行/判题都报错。`runner.py` 两处 `Thread` 启动加 except 降级为主线程执行（settrace 看门狗仍能掐断纯 Python 死循环；C 阻塞调用失去超时保护，与既有 E1 限制一致）。真浏览器验证：运行示例/判题通过/判题失败/ZeroDivisionError/REPL/`while True` 超时全部符合预期
- 角斗场按 `challenge.lang` 分流：2 道 JS 挑战渲染为带「App 内体验」徽标的不可运行卡片，不进 Python 判题路径；补 `.app-only` / `.badge` 样式
- **品牌残留清零**：`web/index.html`（标题/字标/启动 ASCII 艺术，原「PY//NOW」艺术字含一处 U+FFFD 乱码）、`docs/index.html`（标题/导航/英雄区/页脚「码上 · 码上」「码上PYTHON」）、`README.zh-CN.md`（alt 文本）统一为「码上 / Mashang」；docs 课程幕次与统计（30→38 讲、8 挑战）同步
- **重置补齐**：`ProgressStore.reset` 除清 DataStore 外同步删除 `pyneon_mistakes.json` / `pyneon_review_cards.json`（BackupUtil 同源文件名），档案页弹窗文案加「错题本与复习卡」

### Tests
- 新增 tests/test_web_sync.py：7 组契约测试锁定 web 与 App 内容/引擎同源（R1-R7，含逐字节比对 ENGINE_PY 与 runner.py）
- 新增 tests/test_engine_desktop.py::test_no_thread_fallback_runs_inline：模拟无多线程环境，验证降级路径下常规执行 / 死循环超时 / 判题三项行为
- 新增 tests/test_update_catalog.py：4 项回归测试锁定 catalog 剥离语义与包哈希一致性（先红后绿）；packs 计数改为动态断言（随语言包扩充不再失效）
- 新增 tests/test_multilang_content.py：11 项契约测试 —— lang 字段合法性、id 跨语言唯一性、规划中语言不得出现在课程里、LanguageRuntime 接口完整性、**UI 层不得直接引用 PyBridge**（该项在重构前为红，重构后转绿）
- 新增 tests/test_js_lessons.py：9 项行为测试，用 node（vm 模块 + 超时）真实执行 js-basics 包的每讲代码块与判题（Rhino 无法在本沙箱编译，但课程内容是语言本身，可在任何 ES 引擎验证）

## [0.3.7] - 2026-09-14
### Added
- 亮色主题「白纸模式」：新增第 6 套主题，白底深字、全套色彩按白底重新调优；主题切换即时生效，无需重启
- APK 自更新：设置页新增「检查更新」，从 GitCode 主仓目录（catalog.json）拉取版本信息、下载并校验 SHA-256 后交给系统安装器
- 内容代码块支持 `stdin` 字段：含 `input()` 的示例可直接运行（如第 5 课交互输入示例）
- 增补包 · DSA 算法基础（5 讲）：复杂度直觉 / 双指针 / 哈希表 / 栈与队列 / 递归记忆化
- 增补包 · DSA 算法进阶（5 讲）：手写排序 / 二分查找 / 贪心找零 / 链表思维 / 最大子段和
- L0 离线规则教练（CoachEngine）：判题/运行报错时提供「诊断 → 三步引导 → 修复示例」，只提示不代写；练习页新增「问教练」，终端新增 `/coach` `/help` 命令
### Changed
- 全局色彩 Token 重构为 NeonTokens + CompositionLocal：Bg0/TextHi/NeonCyan 等名称在 Compose 下跟随当前主题，为明暗双主题打底
- 版本号单一来源：AppConstants 改为读取 BuildConfig（发版只改 build.gradle.kts）
- release 构建开启 R8 混淆 + 资源压缩，并补齐 Chaquopy / kotlinx.serialization 保留规则
- `tools/upload_release.sh`：检测到签名凭据时自动构建并发布签名 release 包，上传后自动同步 catalog.json 的 app 段
- UI 可读性整改：正文/代码/判题结果优先保证清晰
  - 正文改用系统无衬线字体并放大字号（bodyMedium 13→14sp、bodySmall 11→12sp），标题保留等宽字维持赛博视觉
  - 判题/运行结果移除逐字动画，直接展示，一眼看清
  - 全站特效收敛到装饰区：开屏 / 首页 Banner / 终端 / 证书 / 角斗场保留扫描线+故障字；课程详情、课程列表、设置、隐私政策、帮助中心、学习历史、个人档案、内容中心、备份、复习、关于等页面移除全屏网格与扫描线，纯阅读页（隐私政策/帮助）标题亦改为普通文本
  - 扫描线透明度 0.05 → 0.028，减少对内容的视觉干扰
### Fixed
- l25（datetime/random）两处示例用 `date.today()` 却硬编码期望输出 → 改为固定日期，输出可复现
- 内容包 bonus-27 `sum: 30→31`、dsa03 `neon 2→1` 期望输出错误修正
- 代码编辑器文字颜色改为跟随主题（原硬编码白色）
- 内容中心目录加载失败：catalog 自签名改为「剥离顶层 sha256 字段后的文本」计算（原校验自引用不可满足，内容中心此前无法检查更新）
- catalog.json 补充全部包的 sha256 字段（原目录缺失 sha256，下载链路会被安全校验拦下）

## [0.3.6] - 2026-09-13
### Fixed
- 修复 APK 缺失：重写 `tools/upload_release.sh` 适配 GitCode API（原脚本指向已删除的 GitHub 仓库）
- 应用内全部外链改指 GitCode 主仓：关于页/设置页/分享/隐私政策/用户协议（原指向已删除的 GitHub 仓库，打开均 404）
- 毕业证书二维码与页脚 URL 改指 GitCode 主仓
- 「内容中心」课程包目录源改指 `raw.gitcode.com`（原 `raw.githubusercontent.com` 已失效，联网下载功能此前不可用）
- 版本号统一为 0.3.6 / versionCode 12（AppConstants 此前停留在 0.3.4/10，与 build.gradle.kts 不一致）
- LICENSE / README / README.zh-CN / 华为上架指南清理失效的 GitHub 链接
- 调高 Gradle 构建内存（-Xmx2g），消除 CI 内存告警

## [0.3.5] - 2026-09-06
### Fixed
- CodeEditor addStyle bug: `print` 的 `t` and `(` characters disappearing
- Brand name spacing: `码上Python` → `码上 Python` (6 places)
- Hardcoded lesson count: `30 讲` → dynamic `LessonRepository.lessons(context).size`
- Color spec violations: Bg0, Bg1, TextHi, TextDim aligned to BRAND_GUIDELINES.md
- Hardcoded color values in LessonsScreen and NeonButton → color constants
- Wording inconsistency: `随时开练` → `随时学习`
- Misleading text: `CPython 在线` → `CPython 就绪`

### Added
- Theme switching system with 5 color themes: Cyber Neon / Deep Space Gray / Aurora Green / Twilight Purple / Twilight Orange
- Theme persistence via SharedPreferences
- README_DEMO.md with screenshots and feature documentation

### Changed
- Kotlin badge: 2.0 → 2.4
- Chaquopy version: 16.0 → 17.0.0

## [0.3.4] - 2026-09-04
### Fixed
- Bug 修复与体验优化补丁（详见 RELEASE_NOTES_v0.3.4.md）。

## [0.3.3] - 2026-08-31
### Changed
- Architecture Overhaul & Multilingual Support。