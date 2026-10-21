"""CI 产物探针（tests/ci_apk_probe.py）的回归测试。

背景：GitHub runner 与本机构建出的 Chaquopy app.imy 布局不同
（runner.py / runner.pyc / __pycache__/runner.cpython-3XX.pyc），
探针必须三种都接受，否则 CI 假红。本测试用最小伪造 APK 锁住该行为，
并验证缺资源时确实失败（fail-closed）。
"""
import io
import json
import marshal
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "tests" / "ci_apk_probe.py"

LAYOUTS = ("py", "pyc", "pycache")


def _inner_archive(layout):
    runner_src = (ROOT / "app/src/main/python/runner.py").read_text(encoding="utf-8")
    repl_src = (ROOT / "app/src/main/python/repl.py").read_text(encoding="utf-8")
    pyc = b"\x00" * 16 + marshal.dumps(compile(runner_src, "runner.py", "exec"))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if layout == "py":
            z.writestr("runner.py", runner_src)
            z.writestr("repl.py", repl_src)
        elif layout == "pyc":
            z.writestr("runner.pyc", pyc)
            z.writestr("repl.pyc", b"\x00" * 16)
        else:
            z.writestr("__pycache__/runner.cpython-313.pyc", pyc)
            z.writestr("__pycache__/repl.cpython-313.pyc", b"\x00" * 16)
    return buf.getvalue()


def _write_apk(path, layout, *, with_assets=True):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("assets/chaquopy/app.imy", _inner_archive(layout))
        if with_assets:
            for name in ("lessons_basic.json", "lessons_mid.json", "lessons_adv.json",
                         "lessons_pro.json", "challenges.json"):
                z.writestr(f"assets/{name}", json.dumps([]))
            z.writestr("assets/syntaxes/javascript.tmLanguage.json", "{}")
        z.writestr("AndroidManifest.xml", "com.pyneon.academy".encode("utf-16-le"))
        for i in range(520):
            z.writestr(f"res/dummy_{i}.txt", "x")


class ApkProbeTests(unittest.TestCase):
    def _run(self, apk):
        return subprocess.run(
            [sys.executable, str(PROBE), str(apk)],
            capture_output=True, text=True, encoding="utf-8",
        )

    def test_accepts_all_chaquopy_layouts(self):
        for layout in LAYOUTS:
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as tmp:
                apk = Path(tmp) / "app.apk"
                _write_apk(apk, layout)
                result = self._run(apk)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("ALL APK PROBES PASSED", result.stdout)

    def test_fails_when_lessons_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp) / "app.apk"
            _write_apk(apk, "py", with_assets=False)
            result = self._run(apk)
            self.assertEqual(result.returncode, 1)
            self.assertIn("缺少 assets/lessons_basic.json", result.stdout)


if __name__ == "__main__":
    unittest.main()
