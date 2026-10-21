"""Web 端与 App 内置内容的同源一致性回归网（S9 切片）。

锁定七条契约（见 .aqg/code-construction/mashang-web-sync-cleanup.md）：
  R1 data.js 课程/挑战 == app/src/main/assets（含 lessons_pro）
  R2 engine.js 内嵌 ENGINE_PY == app/src/main/python/runner.py（逐字节）
  R3 内置课程结构字段：chapter int / chapterName 非空 / exercise.xp > 0
  R4 Pyodide 版本串在 index.html 与 app.js 一致且回退源 >= 2
  R5 web 角斗场按 lang 分流（JS 挑战不得进 Python 判题路径）
  R6 品牌残留为零（web/index.html、docs/index.html、README.zh-CN.md）
  R7 重置清除错题本/复习卡（Kotlin 静态契约）
"""
import json
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "app", "src", "main", "assets")
WEB = os.path.join(ROOT, "web")

LESSON_FILES = [
    "lessons_basic.json",
    "lessons_mid.json",
    "lessons_adv.json",
    "lessons_pro.json",
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _load_assets():
    lessons = []
    for name in LESSON_FILES:
        lessons.extend(json.loads(_read(os.path.join(ASSETS, name))))
    challenges = json.loads(_read(os.path.join(ASSETS, "challenges.json")))
    return lessons, challenges


def _parse_data_js():
    text = _read(os.path.join(WEB, "data.js"))
    m = re.search(r"window\.LESSONS = (.*?);\nwindow\.CHALLENGES = (.*?);\n", text, re.S)
    if not m:
        raise AssertionError("data.js 无法解析 window.LESSONS / window.CHALLENGES")
    return json.loads(m.group(1)), json.loads(m.group(2))


def _parse_engine_js():
    text = _read(os.path.join(WEB, "engine.js"))
    m = re.search(r"window\.ENGINE_PY = (.*?);\nwindow\.REPL_HELPER_PY", text, re.S)
    if not m:
        raise AssertionError("engine.js 无法解析 window.ENGINE_PY")
    return json.loads(m.group(1))


class TestWebDataSync(unittest.TestCase):
    def test_web_lessons_match_assets(self):
        """R1: 课程逐条一致（id 序列 + chapter + order）。"""
        assets_lessons, _ = _load_assets()
        web_lessons, _ = _parse_data_js()
        self.assertEqual(
            [l["id"] for l in web_lessons],
            [l["id"] for l in assets_lessons],
            "data.js 课程 id 序列与 assets 不一致（需重跑 python web/gen_data.py）",
        )
        for w, a in zip(web_lessons, assets_lessons):
            self.assertEqual(w.get("chapter"), a.get("chapter"), f"{a['id']} chapter 漂移")
            self.assertEqual(w.get("order"), a.get("order"), f"{a['id']} order 漂移")

    def test_web_challenges_match_assets(self):
        """R1: 挑战逐条一致（含 lang 字段，JS 挑战不得被静默丢弃）。"""
        _, assets_challenges = _load_assets()
        _, web_challenges = _parse_data_js()
        self.assertEqual(
            [c["id"] for c in web_challenges],
            [c["id"] for c in assets_challenges],
            "data.js 挑战 id 序列与 assets 不一致（需重跑 python web/gen_data.py）",
        )
        for w, a in zip(web_challenges, assets_challenges):
            self.assertEqual(w.get("lang", "python"), a.get("lang", "python"), f"{a['id']} lang 漂移")

    def test_web_engine_matches_runner(self):
        """R2: ENGINE_PY 与 runner.py 逐字节一致。"""
        embedded = _parse_engine_js()
        current = _read(os.path.join(ROOT, "app", "src", "main", "python", "runner.py"))
        self.assertEqual(
            embedded,
            current,
            "engine.js 内嵌引擎与 runner.py 不一致（需重跑 python web/gen_data.py）",
        )


class TestLessonSchema(unittest.TestCase):
    def test_chapter_is_int_and_exercise_xp_positive(self):
        """R3: chapter 为 int、chapterName 非空、exercise.xp 为正整数。"""
        assets_lessons, _ = _load_assets()
        problems = []
        for l in assets_lessons:
            lid = l["id"]
            if not isinstance(l.get("chapter"), int) or isinstance(l.get("chapter"), bool):
                problems.append(f"{lid}: chapter 非 int（{l.get('chapter')!r}）")
            if not (l.get("chapterName") or "").strip():
                problems.append(f"{lid}: chapterName 为空")
            ex = l.get("exercise")
            if ex:
                xp = ex.get("xp")
                if not isinstance(xp, int) or isinstance(xp, bool) or xp <= 0:
                    problems.append(f"{lid}: exercise.xp 非正 int（{xp!r}）")
        self.assertEqual(problems, [], f"课程结构问题: {problems}")


class TestPyodidePin(unittest.TestCase):
    def _app_version(self):
        text = _read(os.path.join(WEB, "app.js"))
        m = re.search(r'PYODIDE_VERSION\s*=\s*"([0-9.]+)"', text)
        self.assertIsNotNone(m, "app.js 缺少 PYODIDE_VERSION 常量")
        return m.group(1), text

    def test_index_and_app_versions_match(self):
        """R4: index.html 脚本 URL 与 app.js 常量版本一致。"""
        version, _ = self._app_version()
        html = _read(os.path.join(WEB, "index.html"))
        m = re.search(r"pyodide/v([0-9.]+)/full/pyodide\.js", html)
        self.assertIsNotNone(m, "index.html 未引用 pyodide/v<版本>/full/pyodide.js")
        self.assertEqual(m.group(1), version, "index.html 与 app.js 的 Pyodide 版本不一致")

    def test_fallback_sources(self):
        """R4: 至少 3 个引擎源（1 主 + >=2 回退），主机去重后 >= 2。"""
        _, text = self._app_version()
        m = re.search(r"PYODIDE_SOURCES\s*=\s*\[(.*?)\];", text, re.S)
        self.assertIsNotNone(m, "app.js 缺少 PYODIDE_SOURCES 回退链")
        urls = re.findall(r'"(https://[^"]+)"', m.group(1))
        self.assertGreaterEqual(len(urls), 3, f"引擎源不足 3 个: {urls}")
        hosts = {re.match(r"https://([^/]+)", u).group(1) for u in urls}
        self.assertGreaterEqual(len(hosts), 2, f"回退源主机去重后不足 2 个: {hosts}")


class TestArenaLangSplit(unittest.TestCase):
    def test_js_challenges_not_routed_to_python(self):
        """R5: 角斗场按 lang 分流，JS 挑战标注「App 内体验」。"""
        text = _read(os.path.join(WEB, "app.js"))
        self.assertRegex(
            text,
            r"function splitChallenges",
            "app.js 缺少 splitChallenges 分流函数",
        )
        seg = text[text.index("function splitChallenges"):][:800]
        # 断言真实分流逻辑：python 进判题组，其余进 appOnly 组
        self.assertRegex(
            seg,
            r'if \(\(ch\.lang \|\| "python"\) === "python"\) python\.push\(ch\);\s*\n\s*else appOnly\.push\(ch\);',
            "splitChallenges 未把非 python 挑战放进 appOnly",
        )
        self.assertNotIn("if (true)", seg, "splitChallenges 出现恒真短路")
        self.assertIn("App 内体验", text, "app.js 缺少 JS 挑战的「App 内体验」标注")
        # 渲染路径必须真的只用 split.python 进判题卡片
        arena = text[text.index("function renderArena"):][:1200]
        self.assertIn("split.python.forEach", arena, "renderArena 未使用 python 分流结果")
        self.assertIn("split.appOnly.forEach", arena, "renderArena 未渲染 appOnly 卡片")


class TestBrandResidue(unittest.TestCase):
    def test_no_residue(self):
        """R6: 三处品牌残留为零。"""
        targets = [
            os.path.join(WEB, "index.html"),
            os.path.join(ROOT, "docs", "index.html"),
            os.path.join(ROOT, "README.zh-CN.md"),
        ]
        patterns = ["码上 · 码上", "PY//NOW", "码上Python", "码上PYTHON"]
        hits = []
        for path in targets:
            text = _read(path)
            for p in patterns:
                if p in text:
                    hits.append(f"{os.path.relpath(path, ROOT)}: {p}")
        self.assertEqual(hits, [], f"品牌残留: {hits}")
        self.assertIn("码上", _read(os.path.join(WEB, "index.html")), "web 首页应含新品牌名")


class TestResetClearsAll(unittest.TestCase):
    def test_progress_store_reset_deletes_mistakes_and_review(self):
        """R7: reset 必须经 UserDataFiles.deleteAll 删除，且失败要留痕。"""
        data_dir = os.path.join(
            ROOT, "app", "src", "main", "java", "com", "pyneon", "academy", "data"
        )
        text = _read(os.path.join(data_dir, "ProgressStore.kt"))
        m = re.search(r"suspend fun reset\(context: Context\) \{(.*?)\n    \}", text, re.S)
        self.assertIsNotNone(m, "未找到 ProgressStore.reset 实现")
        body = m.group(1)
        self.assertIn("UserDataFiles.deleteAll(", body, "reset 未调用 UserDataFiles.deleteAll")
        self.assertIn("it.clear()", body, "reset 未清 DataStore")
        self.assertIn("Log.w", body, "reset 删除失败未记录日志")

        files = _read(os.path.join(data_dir, "UserDataFiles.kt"))
        for fname in ("pyneon_mistakes.json", "pyneon_review_cards.json"):
            self.assertIn(fname, files, f"UserDataFiles 未覆盖 {fname}")

        for fname in ("ViewModels.kt", "BackupUtil.kt"):
            src = _read(os.path.join(data_dir, fname))
            self.assertNotIn('"pyneon_mistakes.json"', src, f"{fname} 仍硬编码文件名")
            self.assertNotIn('"pyneon_review_cards.json"', src, f"{fname} 仍硬编码文件名")

    def test_profile_dialog_copy_covers_cleared_data(self):
        """R7: 档案页重置弹窗文案覆盖错题本与复习卡。"""
        text = _read(
            os.path.join(
                ROOT,
                "app", "src", "main", "java", "com", "pyneon", "academy",
                "screens", "ProfileScreen.kt",
            )
        )
        seg = text[text.index("确认格式化？"):][:700]
        self.assertIn("错题本", seg, "重置弹窗文案未提及错题本")
        self.assertIn("复习卡", seg, "重置弹窗文案未提及复习卡")


if __name__ == "__main__":
    unittest.main()
