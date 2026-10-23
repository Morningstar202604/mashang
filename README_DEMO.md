# 码上 · 功能演示素材（历史存档 · v0.3.7）

> **状态：历史存档。** 截图与视频拍摄于 v0.3.4–v0.3.7 期间，部分界面（首页 PY//NOW 字标、30 讲口径）已被 2026-10 品牌重塑替换；当前界面见根 `README.md` 的 Screenshots 一节（`demo/app/`）。

目录内为重构期（v0.3.4–v0.3.7）的演示素材，仅供参考；现行截图与视频以 README 与 `demo/app/` 为准。

## 宣传视频（18 秒 · 1080x1920 竖屏）
- **demo/new/promo.mp4** — 开场"码上，就是马上。"品牌文案 + 首页界面推近，
  首页带"38 讲 · 五幕课程 · 完全离线 · 判题实战"信息字幕，适合应用商店/社媒宣传

## 功能导览视频（16 秒 · 1080x1920 竖屏）
- **demo/new/usage.mp4** — 首页 → 课程（含第四幕）→ 实战判题 → 终端 → 挑战 → 我的，
  六屏切片渐变导览，展示完整学习闭环

## 功能截图（1080x1920）
| 页面 | 截图 |
|---|---|
| 首页（任务/课程体系/继续行动） | demo/new/home.png |
| 课程（0/49 · 章节解锁 · 第四幕新课） | demo/new/lessons.png |
| 实战判题（判题通过 · 变量快照 · XP） | demo/new/judge.png |
| Python 终端（REPL） | demo/new/terminal.png |
| 挑战（8 关闯关，含 2 道 JS） | demo/new/arena.png |
| 我的（进阶工具/主题切换 7+自定义） | demo/new/profile.png |

## 生成方式（可复现）
- 截图：`demo/new/screens.html` 为 6 屏 UI 复刻（真实课程/挑战数据），
  浏览器 CDP 按 420x900@2x viewport 截图后 LANCZOS 放大到 1080x1920
- 视频：ffmpeg zoompan 推近 + xfade 渐变拼接（1080x1920，`-preset faster -crf 30`）

> 说明：旧版截图/视频（demo/home.png、demo/promo-video.mp4 等）为 v0.3.4 旧 UI，仅存档。
