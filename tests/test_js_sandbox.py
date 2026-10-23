"""JS 沙箱边界回归（Rhino ClassShutter）。

背景：2026-10-22 模拟器实测发现 Rhino 默认把 Java 类暴露给脚本，
`Packages.java.lang.Runtime.getRuntime().exec(["id"]).waitFor()` 返回 0，
即用户可以执行任意系统命令。修复方式：Context 上装 ClassShutter 全拒绝。

本测试是静态契约（Kotlin 无法在纯 Python 环境执行）；行为验证已在
模拟器上完成，见 out/sec_poc.png / out/sec_poc_fixed.png。
"""
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JS_BRIDGE = os.path.join(
    ROOT, "app", "src", "main", "java", "com", "pyneon", "academy", "js", "JsBridge.kt"
)


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class JsSandboxTests(unittest.TestCase):
    def test_class_shutter_installed(self):
        text = _read(JS_BRIDGE)
        self.assertIn(
            "ClassShutter", text,
            "JsBridge 必须给 Rhino Context 安装 ClassShutter（否则可访问 Java 类）",
        )
        self.assertRegex(
            text,
            r"setClassShutter\(\s*ClassShutter\s*\{\s*_?\s*->\s*false\s*\}\s*\)",
            "ClassShutter 必须全部拒绝（不得放行任何 Java 类）",
        )

    def test_shutter_is_set_on_every_context(self):
        """必须在 ContextFactory.makeContext 里设置，保证所有新建 Context 都受保护。"""
        text = _read(JS_BRIDGE)
        make_ctx = re.search(r"override fun makeContext\(\): JsContext \{(.*?)\n        \}", text, re.S)
        self.assertIsNotNone(make_ctx, "未找到 makeContext 实现")
        self.assertIn("setClassShutter", make_ctx.group(1), "makeContext 内必须设置 ClassShutter")


if __name__ == "__main__":
    unittest.main()
