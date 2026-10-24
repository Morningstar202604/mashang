# 码上 · 网页版（Web Client）

Android 之外的**第二端**：纯前端网页，浏览器里直接学 Python。与手机端**共用同一套课程 JSON** 与**同一份判题引擎 `runner.py`**（Pyodide 0.29.5 在浏览器内跑 CPython 3.13.2），所以判题语义与变量快照两端一致。

在线地址：<https://badhope.github.io/mashang/web/>

## 如何打开（任选其一）

### 方式 A：本地静态服务（推荐）
```bash
cd web
python -m http.server 8765
# 打开 http://127.0.0.1:8765/
```

### 方式 B：直接双击 `index.html`
课程与引擎已内联进 `data.js` / `engine.js`，无需 fetch。Pyodide 内核首次加载需要联网（jsdelivr → fastly.jsdelivr → unpkg 三级回退），之后浏览器会缓存。

## 功能

- **指挥台**：主线进度环、XP / 段位、每日行动、能力矩阵。
- **课程列表**：38 讲按五幕分组、语言筛选、完成/锁定状态。
- **课程详情**：14 种内容块全量渲染（含 `fill` 填空、`order` 排序、`quiz` 随堂问、`practice`、`exercise`）。
- **可运行代码块**：运行后显示 stdout + **变量快照面板**。
- **实战判题**：`assert` 用例，通过才记录通关与 XP。
- **终端 REPL**：有状态会话；表达式自动回显 repr；↑/↓ 历史；Shift+Enter 换行；Ctrl+L 清屏；一键重置。
- **角斗场**：8 个挑战，其中 6 个 Python 可直接判题，2 个 JavaScript 标注「App 内体验」。
- **进度存档**：`localStorage`（key `mashang.web.v1`）保存 XP、通关、已解练习；hash 路由（`#/lesson/l01`、`#/challenge/c01`）刷新/分享可恢复。
- **明暗主题**：右上角 ◐ 切换，写入 `localStorage`。

## 执行与安全模型

- 用户代码在 **Web Worker** 内执行；主线程 15 秒无响应即 `terminate()`，页面不会冻结。
- 所有用户/课程文本用 `textContent` 插入，不做 HTML 字符串拼接（防 DOM XSS）。
- 无 Worker 的旧浏览器降级到主线程执行（此时 C 阻塞调用无法中断，需刷新页面）。
- 引擎加载失败时提供「重试 / 仅浏览课程」两条路径，课程仍可阅读。

## 引擎同源机制

- 课程：`app/src/main/assets/lessons_*.json` + `challenges.json` → `data.js`
- 引擎：`app/src/main/python/runner.py` → `engine.js`（内联 `window.ENGINE_PY`）
- 网页端在 Pyodide 中 `runPython(window.ENGINE_PY)` 后调用 `run_code_json` / `check_exercise_json`；REPL 辅助（表达式回显 + 持久命名空间）在 `gen_data.py` 的 `REPL_HELPER_PY` 中
- 重新生成：`python gen_data.py`；同源性由 `tests/test_web_sync.py` 逐字节校验

## 已知边界

- 首屏需下载约 12 MB Pyodide WASM（仅首次，之后走浏览器缓存）。
- 网页版是 App 的**子集**：不含成就、连击、毕业证书、内容中心下载；2 道 JavaScript 挑战仅 App 内可运行。
- Pyodide 的 Python 代码可经 `js` 模块访问浏览器全局，属于「运行用户自己代码」的固有边界，详见仓库 `SECURITY.md`。
