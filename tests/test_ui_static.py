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
        text = _read(JAVA, "data", "TrackRepository.kt")
        m = re.search(r'progressHint = "(\d+) 讲', text)
        self.assertIsNotNone(m, "TrackRepository 缺少 progressHint 讲数")
        self.assertEqual(
            int(m.group(1)), _python_lesson_count(),
            "首页课程卡片讲数与 assets 不一致",
        )

    def test_help_challenge_count_matches_assets(self):
        text = _read(JAVA, "screens", "HelpScreen.kt")
        m = re.search(r"「挑战」页有 (\d+) 个实战闯关", text)
        self.assertIsNotNone(m, "帮助中心缺少挑战数文案")
        self.assertEqual(int(m.group(1)), _challenge_count(), "帮助中心挑战数与 challenges.json 不一致")


class KeyboardInsetTests(unittest.TestCase):
    def test_bottom_bar_hidden_while_ime_visible(self):
        text = _read(JAVA, "nav", "AppNav.kt")
        self.assertIn("WindowInsets.isImeVisible", text)
        self.assertRegex(
            text,
            r"if \(showBar && !WindowInsets\.isImeVisible\)",
            "键盘弹出时必须隐藏底部导航，否则遮挡/挤压输入区",
        )


if __name__ == "__main__":
    unittest.main()
