"""UI 静态契约回归（不需要模拟器，捕捉会回归的界面缺陷）。

每条都对应 2026-10-21 模拟器验收时实际发现并修复的问题：
  R1 代码编辑器必须把真实 scopeName 传给 sora TextMate（否则静默降级成
     白底默认主题，在深色 UI 里出现刺眼白框）
  R2 主题 JSON 必须覆盖 sora 需要的 colors 键（否则部分控件仍是浅色）
  R3 首页「课程体系」文案的讲数必须与 assets 里 Python 课程数一致
  R4 帮助中心的挑战数必须与 challenges.json 一致
  R5 键盘弹出时底部导航必须收起（否则要么被盖住点不到，要么挤掉输入区）
"""
import json
import os
import pathlib
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "app", "src", "main", "assets")
JAVA = os.path.join(ROOT, "app", "src", "main", "java", "com", "pyneon", "academy")


def _read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


def _python_lesson_count():
    total = 0
    for name in ("lessons_basic.json", "lessons_mid.json", "lessons_adv.json", "lessons_pro.json"):
        with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
            total += len(json.load(f))
    return total


def _challenge_count():
    with open(os.path.join(ASSETS, "challenges.json"), encoding="utf-8") as f:
        return len(json.load(f))


class EditorThemeTests(unittest.TestCase):
    def test_grammar_scope_name_is_passed(self):
        text = _read(JAVA, "ui", "components", "CodeEditor.kt")
        self.assertIn("withGrammarSource(", text)
        # 必须用三参数重载（grammarSource, name, scopeName）
        self.assertRegex(
            text,
            r"withGrammarSource\(\s*grammarSource,\s*language,\s*scopeName\s*\)",
            "必须把 scopeName 传给 withGrammarSource（否则默认 source.string 导致降级白底）",
        )
        self.assertIn('"source.python"', text)
        self.assertIn('"source.js"', text)

    def test_theme_covers_sora_color_keys(self):
        text = _read(JAVA, "ui", "components", "CodeEditor.kt")
        for key in (
            "editor.background",
            "editor.foreground",
            "editor.lineHighlightBackground",
            "editorLineNumber.foreground",
            "editorCursor.foreground",
            "editor.selectionBackground",
        ):
            self.assertIn(key, text, f"主题缺 {key}，对应控件会退回默认浅色")


class CopyCountTests(unittest.TestCase):
    def test_home_track_lesson_count_matches_assets(self):
        """首页主线卡片的讲数由 TrackRepository 的 spec 定义，必须与 assets 一致。"""
        text = _read(JAVA, "data", "TrackRepository.kt")
        m = re.search(r'"python", "Python 主线".*?\(1\.\.(\d+)\)', text, re.S)
        self.assertIsNotNone(m, "TrackRepository 缺少 Python 主线课程 id 区间")
        self.assertEqual(
            int(m.group(1)), _python_lesson_count(),
            "首页课程卡片讲数与 assets 不一致",
        )

    def test_tracks_only_lists_real_content(self):
        """路线页不得再有「开发中 x%」这类没有实现的占位轨道。"""
        text = _read(JAVA, "data", "TrackRepository.kt")
        self.assertNotIn("DEVELOPING", text, "TrackRepository 仍有占位轨道状态")
        for fake in ("Java", "React", "机器学习", "Docker"):
            self.assertNotIn(f'"{fake}"', text, f"TrackRepository 仍列出未实现路线：{fake}")
        screen = _read(JAVA, "screens", "TracksScreen.kt")
        self.assertIn("NOT_INSTALLED", screen, "未下载的内容包应显示为可下载")
        self.assertIn("onOpenContentHub", screen, "未装载路线应引导到内容中心")

    def test_help_challenge_count_is_dynamic(self):
        """帮助中心的挑战数必须从 challenges.json 读取，不能硬编码。

        2026-10-22 界面巡检：原实现写死「8 个实战闯关」，一旦挑战增删就会与
        角斗场列表脱节。改为断言「文案引用 totalChallenges」+「总数来自 assets」。
        """
        text = _read(JAVA, "screens", "HelpScreen.kt")
        self.assertIn("challenges.json", text, "挑战数必须从 assets 读取")
        self.assertIn("$totalChallenges", text, "挑战数文案必须引用动态变量")
        self.assertGreaterEqual(_challenge_count(), 1, "challenges.json 至少应有 1 道题")


class NavigationRouteTests(unittest.TestCase):
    """所有 navigate("x") 目标必须在 NavHost 里注册，否则点击即崩。

    2026-10-21 模拟器实测：ProfileScreen 的「备份/恢复」调用 navigate("backup")，
    但 AppNav 从未注册该路由 → IllegalArgumentException 直接闪退。
    """

    def test_every_navigate_target_is_registered(self):
        nav = _read(JAVA, "nav", "AppNav.kt")
        registered = {
            r.split("/")[0] for r in re.findall(r'composable\("([^"]+)"\)', nav)
        }
        self.assertTrue(registered, "未解析到任何 composable 路由")

        targets = {}
        for path in (pathlib.Path(JAVA)).rglob("*.kt"):
            text = path.read_text(encoding="utf-8")
            for m in re.finditer(r'navigate\(\s*"([^"$]+)"', text):
                targets.setdefault(m.group(1), set()).add(path.name)

        missing = {
            route: sorted(files)
            for route, files in targets.items()
            if route.split("/")[0] not in registered
        }
        self.assertEqual(missing, {}, f"navigate 目标未注册（点击会崩溃）: {missing}")


class KeyboardInsetTests(unittest.TestCase):
    def test_bottom_bar_hidden_while_ime_visible(self):
        text = _read(JAVA, "nav", "AppNav.kt")
        self.assertIn("WindowInsets.isImeVisible", text)
        self.assertRegex(
            text,
            r"if \(showBar && !WindowInsets\.isImeVisible\)",
            "键盘弹出时必须隐藏底部导航，否则遮挡/挤压输入区",
        )


class VisualRegressionTests(unittest.TestCase):
    """2026-10-22 模拟器逐屏点验发现、且可静态锁定的界面缺陷。"""

    def test_glitch_text_does_not_double_draw_permanently(self):
        """GlitchText 若常驻偏移绘制两份彩色副本，中文标题会糊成重影。

        必须用「只在短脉冲内绘制副本」的实现（amount 门控）。
        """
        text = _read(JAVA, "ui", "effects", "Effects.kt")
        seg = text[text.index("fun GlitchText"):][:1400]
        self.assertIn("amount", seg, "GlitchText 需要抖动强度门控")
        self.assertRegex(seg, r"if \(amount > [0-9.]+f?\)", "副本必须在静止期不绘制")

    def test_streak_screen_is_scrollable(self):
        """连击台 6 个徽章 + 主卡在 1080×2400 上超出屏幕，必须可滚动。"""
        text = _read(JAVA, "screens", "StreakScreen.kt")
        self.assertIn("verticalScroll(rememberScrollState())", text)

    def test_badge_grid_is_responsive(self):
        """徽章格固定 4 列会在窄屏溢出、固定宽度会在宽屏留白。"""
        text = _read(JAVA, "screens", "StreakScreen.kt")
        self.assertIn("BoxWithConstraints", text)
        self.assertIn("maxWidth", text)

    def test_code_inputs_disable_ime_autocapitalization(self):
        """代码大小写敏感：终端/填空/自定义颜色输入必须关掉 IME 自动大写。"""
        for rel in (("screens", "TerminalScreen.kt"), ("screens", "LessonBlockCards.kt"),
                    ("screens", "ProfileScreen.kt")):
            text = _read(JAVA, *rel)
            self.assertIn("KeyboardType.Password", text, f"{rel[-1]} 未关闭自动大写")
            self.assertIn("autoCorrect = false", text, f"{rel[-1]} 未关闭自动纠错")

    def test_js_error_message_has_no_duplicated_type(self):
        """Rhino 的 EcmaError.message 自带「ReferenceError: …」，不能直接拼 type。"""
        text = _read(JAVA, "js", "JsBridge.kt")
        self.assertIn('removePrefix("${e.type}: ")', text)

    def test_secondary_pages_have_top_back(self):
        """帮助/隐私/关于原先只能滚到底部点返回。"""
        for name in ("HelpScreen.kt", "PrivacyPolicyScreen.kt", "AboutScreen.kt"):
            text = _read(JAVA, "screens", name)
            self.assertIn("ArrowBack", text, f"{name} 缺少顶部返回")

    def test_home_challenge_button_uses_fire_icon(self):
        text = _read(JAVA, "screens", "HomeScreen.kt")
        seg = text[text.index('label = "挑战"'):][:300]
        self.assertIn("LocalFireDepartment", seg, "挑战按钮不应使用人像图标")


if __name__ == "__main__":
    unittest.main()
