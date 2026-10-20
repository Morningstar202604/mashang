"""
JavaScript 语言包 · 真实引擎行为验证
====================================

JsBridge（Rhino）在本沙箱无法编译运行（无 Android SDK），但课程内容与判题
脚本是**语言本身**，可以在任何符合 ECMAScript 的引擎里执行。本测试用 node
（vm 模块 + 超时）真实执行 js-basics 包的每一讲：

  1. 语法检查：代码块 / 练习起始码 / 参考答案必须能编译
  2. 代码块实跑：所有 runnable 代码块执行不抛错（对照 output 块由人工审读）
  3. 判题实跑：exercise.solution + 逐条 tests 在共享作用域执行，全部通过

宿主函数语义与 JsBridge 对齐：print/console.log 捕获、assert(cond, msg) 抛
AssertionError、input() 抛 InputError。Rhino 与 node 的差异（ES6 子集）由
课程内容约束规避——本包统一 ES5 风格（见 js01 的 warn 块）。

node 未安装时整组跳过（结构检查已由 validate_content.py 覆盖）。
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "content_packs" / "js-basics.json"

# 与 JsBridge.checkInternal 的判题语义一一对应
HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const task = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

function makeSandbox() {
  const out = [];
  const sandbox = {
    print: function () { out.push(Array.prototype.slice.call(arguments).map(String).join(' ')); },
    input: function () { throw new Error('InputError: 运行台不支持交互式输入'); },
    assert: function (cond, msg) {
      if (!cond) throw new Error('AssertionError: ' + (msg || '断言未通过'));
    }
  };
  sandbox.console = { log: sandbox.print, info: sandbox.print, warn: sandbox.print, error: sandbox.print };
  return { sandbox: sandbox, out: out };
}

const result = { parse: [], blocks: [], judge: { ok: false, failures: [], output: '' } };

// 1) 语法检查（只编译不执行）
const sources = task.blocks.concat([task.starter, task.solution]);
sources.forEach(function (src, i) {
  try { new Function(src); }
  catch (e) { result.parse.push({ index: i, error: String((e && e.message) || e) }); }
});

// 2) 可运行代码块真实执行
task.blocks.forEach(function (src, i) {
  try {
    const sb = makeSandbox();
    vm.createContext(sb.sandbox);
    vm.runInContext(src, sb.sandbox, { timeout: 5000 });
  } catch (e) { result.blocks.push({ index: i, error: String((e && e.message) || e) }); }
});

// 3) 判题：参考答案 + 逐条测试，共享作用域（用例间可共享状态）
try {
  const sb = makeSandbox();
  vm.createContext(sb.sandbox);
  vm.runInContext(task.solution, sb.sandbox, { timeout: 5000 });
  task.tests.forEach(function (t, i) {
    try { vm.runInContext(t, sb.sandbox, { timeout: 2000 }); }
    catch (e) { result.judge.failures.push({ index: i + 1, reason: String((e && e.message) || e) }); }
  });
  result.judge.output = sb.out.join('\n');
  result.judge.ok = result.judge.failures.length === 0;
} catch (e) {
  result.judge.failures.push({ index: 0, reason: 'user-code: ' + String((e && e.message) || e) });
}

process.stdout.write(JSON.stringify(result));
"""


def _find_node():
    found = shutil.which("node")
    if found:
        return found
    for candidate in (r"C:\Program Files\nodejs\node.exe",):
        if os.path.exists(candidate):
            return candidate
    return None


NODE = _find_node()

CHALLENGES = ROOT / "app" / "src" / "main" / "assets" / "challenges.json"


@unittest.skipUnless(NODE, "未找到 node，无法执行 JS 行为验证（结构检查仍由 validate_content.py 覆盖）")
class JsPackBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lessons = json.loads(PACK.read_text(encoding="utf-8"))
        cls.tmp = tempfile.TemporaryDirectory()
        cls.harness_path = os.path.join(cls.tmp.name, "js_harness.js")
        with open(cls.harness_path, "w", encoding="utf-8") as f:
            f.write(HARNESS)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run_node(self, lesson) -> dict:
        task = {
            "blocks": [b["code"] for b in lesson["blocks"] if b["type"] == "code"],
            "starter": lesson["exercise"]["starterCode"],
            "solution": lesson["exercise"]["solution"],
            "tests": lesson["exercise"]["tests"],
        }
        task_path = os.path.join(self.tmp.name, f"{lesson['id']}_task.json")
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False)
        proc = subprocess.run(
            [NODE, self.harness_path, task_path],
            capture_output=True, text=True, timeout=60, encoding="utf-8",
        )
        if proc.returncode != 0:
            self.fail(f"node 执行失败（{lesson['id']}）: {proc.stderr.strip()}")
        return json.loads(proc.stdout)

    def test_pack_contract(self):
        """R1：包级契约 —— lang=javascript、代码块显式 runnable、判题与答案齐备"""
        for lesson in self.lessons:
            with self.subTest(lesson=lesson["id"]):
                self.assertEqual("javascript", lesson.get("lang"))
                code_blocks = [b for b in lesson["blocks"] if b["type"] == "code"]
                self.assertTrue(code_blocks, f"{lesson['id']}: 至少一个代码块")
                for b in code_blocks:
                    # 下载包 defaultRunnable=false，块必须显式 runnable:true 才有运行按钮
                    self.assertTrue(b.get("runnable"), f"{lesson['id']}: 代码块需显式 runnable")
                ex = lesson["exercise"]
                self.assertTrue(ex["tests"], f"{lesson['id']}: 至少一条判题")
                self.assertTrue(ex.get("solution"), f"{lesson['id']}: 需参考答案")

    def test_lessons_share_no_duplicate_order(self):
        """R2：order 段位 300+，不与内置 Python 课（1-38）或 bonus 包（200+）冲突"""
        for lesson in self.lessons:
            with self.subTest(lesson=lesson["id"]):
                self.assertGreaterEqual(lesson["order"], 300)

    def test_js01_greeting(self):
        self._assert_lesson_ok("js01")

    def test_js02_math(self):
        self._assert_lesson_ok("js02")

    def test_js03_strings(self):
        self._assert_lesson_ok("js03")

    def test_js04_branches(self):
        self._assert_lesson_ok("js04")

    def test_js05_arrays(self):
        self._assert_lesson_ok("js05")

    def test_js06_objects(self):
        self._assert_lesson_ok("js06")

    def _assert_lesson_ok(self, lid):
        lesson = next(l for l in self.lessons if l["id"] == lid)
        result = self._run_node(lesson)

        # 1) 全部源码可编译
        self.assertEqual(
            [], result["parse"],
            f"{lid}: 存在语法错误 {[p['error'] for p in result['parse']]}"
        )
        # 2) 代码块实跑无异常
        self.assertEqual(
            [], result["blocks"],
            f"{lid}: 代码块运行报错 {[b['error'] for b in result['blocks']]}"
        )
        # 3) 参考答案通过全部判题
        self.assertTrue(
            result["judge"]["ok"],
            f"{lid}: 判题未全过 {result['judge']['failures']}"
        )

    def test_judged_output_is_captured(self):
        """R3：判题过程中 print/console.log 的输出必须可见（教学诊断依赖它）"""
        lesson = next(l for l in self.lessons if l["id"] == "js01")
        result = self._run_node(lesson)
        self.assertIn("HELLO, v", result["judge"]["output"])


class JsChallengeBehaviorTests(unittest.TestCase):
    """训练场 JS 挑战：与课程共用同一 node 判题通道（契约与 JsBridge 对齐）"""

    @classmethod
    def setUpClass(cls):
        cls.challenges = json.loads(CHALLENGES.read_text(encoding="utf-8"))
        cls.tmp = tempfile.TemporaryDirectory()
        cls.harness_path = os.path.join(cls.tmp.name, "js_harness.js")
        with open(cls.harness_path, "w", encoding="utf-8") as f:
            f.write(HARNESS)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _judge(self, challenge) -> dict:
        task = {
            "blocks": [],
            "starter": challenge["starterCode"],
            "solution": challenge["solution"],
            "tests": challenge["tests"],
        }
        task_path = os.path.join(self.tmp.name, f"{challenge['id']}_task.json")
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False)
        proc = subprocess.run(
            [NODE, self.harness_path, task_path],
            capture_output=True, text=True, timeout=60, encoding="utf-8",
        )
        if proc.returncode != 0:
            self.fail(f"node 执行失败（{challenge['id']}）: {proc.stderr.strip()}")
        return json.loads(proc.stdout)

    def test_challenge_contract(self):
        """R1：JS 挑战必须带 lang=javascript 与参考答案（Python 挑战不受影响）"""
        js_challenges = [c for c in self.challenges if c.get("lang") == "javascript"]
        self.assertGreaterEqual(len(js_challenges), 2, "至少两道 JS 挑战")
        for c in js_challenges:
            with self.subTest(challenge=c["id"]):
                self.assertTrue(c.get("solution"), f"{c['id']}: 缺少参考答案")
                self.assertTrue(c["tests"], f"{c['id']}: 缺少判题")

    def test_js_challenge_c1_neon_fb(self):
        self._assert_challenge_ok("js-c1")

    def test_js_challenge_c2_brackets(self):
        self._assert_challenge_ok("js-c2")

    def _assert_challenge_ok(self, cid):
        challenge = next(c for c in self.challenges if c["id"] == cid)
        result = self._judge(challenge)
        self.assertTrue(
            result["judge"]["ok"],
            f"{cid}: 判题未全过 {result['judge']['failures']}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
