"""
Engine JSON contract tests (desktop level, no Android dependency).

This module is the desktop equivalent of audit finding K1: it guards the
JSON contract produced by the Python engine that the Android/Kotlin bridge
consumes. If anyone changes ``runner.py`` in a way that drops or re-types a
field, these tests must fail on CI and block the push/PR.

The engine lives under ``app/src/main/python`` and is imported directly by
adding that directory to ``sys.path`` (same approach as test_engine_desktop.py).

用法：python -m unittest discover -s tests（CI 走这条；不要用 pytest 风格裸函数，
unittest 不会收集）。
"""

import json
import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python")
)

import runner


def _run_code(payload):
    """Drive run_code_json with a dict payload, return the parsed result."""
    return json.loads(runner.run_code_json(json.dumps(payload)))


def _check_exercise(payload):
    """Drive check_exercise_json with a dict payload, return the parsed result."""
    return json.loads(runner.check_exercise_json(json.dumps(payload)))


class EngineContractTests(unittest.TestCase):
    def test_run_code_json_success_contract(self):
        result = _run_code({"code": "x = 1 + 2\nname = 'neo'\nprint('hello neon')"})

        for field in ("ok", "stdout", "stderr", "error", "variables", "duration_ms"):
            self.assertIn(field, result, "run_code_json missing field: %s" % field)

        self.assertIsInstance(result["ok"], bool, "ok must be bool")
        self.assertIsInstance(result["stdout"], str, "stdout must be str")
        self.assertIsInstance(result["stderr"], str, "stderr must be str")
        self.assertIsNone(result["error"], "successful run must have null error")
        self.assertIsInstance(result["duration_ms"], (int, float), "duration_ms must be number")
        self.assertIsInstance(result["variables"], list, "variables must be list")

        for var in result["variables"]:
            self.assertEqual(set(var.keys()), {"name", "type", "value"}, "variable shape wrong: %s" % var)
            self.assertIsInstance(var["name"], str)
            self.assertIsInstance(var["type"], str)
            self.assertIsInstance(var["value"], str)

        self.assertNotIn("passed", result, "run_code_json must not contain 'passed'")
        self.assertTrue(result["ok"])

    def test_run_code_json_error_contract(self):
        result = _run_code({"code": "x = 1 / 0"})

        self.assertFalse(result["ok"])
        self.assertNotIn("passed", result, "run_code_json must not contain 'passed'")

        error = result["error"]
        self.assertIsInstance(error, dict, "error must be dict on failure")
        for key in ("type", "message", "traceback"):
            self.assertIn(key, error, "error missing key: %s" % key)
        self.assertIsInstance(error["type"], str)
        self.assertIsInstance(error["message"], str)
        self.assertIsInstance(error["traceback"], str)

    def test_check_exercise_json_has_passed(self):
        result = _check_exercise(
            {
                "code": "def square(n):\n    return n * n",
                "tests": ["assert square(3) == 9", "assert square(-2) == 4"],
            }
        )

        self.assertIn("passed", result, "check_exercise_json must contain 'passed'")
        self.assertIsInstance(result["passed"], bool, "passed must be bool")
        self.assertTrue(result["passed"])
        self.assertIsInstance(result["ok"], bool, "check result must carry ok(bool)")

    def test_check_exercise_json_failure_passed_false(self):
        result = _check_exercise(
            {
                "code": "def double(n):\n    return n * 2",
                "tests": ["assert double(2) == 4", "assert double(3) == 7"],
            }
        )

        self.assertIsInstance(result["passed"], bool)
        self.assertFalse(result["passed"])

    def test_info_json_has_python_version(self):
        info = json.loads(runner.info_json())

        self.assertIn("python_version", info, "info_json must contain python_version")
        self.assertIsInstance(info["python_version"], str, "python_version must be str")
        self.assertTrue(info["python_version"], "python_version must be non-empty")


if __name__ == "__main__":
    unittest.main()
