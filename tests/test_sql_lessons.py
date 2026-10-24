"""SQL 课程包真执行门禁。

每一讲的参考答案都送进 `app/src/main/python/sql_runner.py` 的判题函数，
用真实 sqlite3 执行并逐条跑判题用例；任何一讲失败即视为内容与引擎漂移。
"""

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app" / "src" / "main" / "python"))

import sql_runner  # noqa: E402


class SqlPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack_path = ROOT / "content_packs" / "sql-basics.json"
        cls.lessons = json.loads(cls.pack_path.read_text(encoding="utf-8"))

    def test_pack_exists_and_has_lessons(self):
        self.assertTrue(self.pack_path.is_file())
        self.assertGreaterEqual(len(self.lessons), 6)
        self.assertTrue(all(l["lang"] == "sql" for l in self.lessons))

    def test_every_solution_passes_its_tests(self):
        for lesson in self.lessons:
            ex = lesson["exercise"]
            with self.subTest(lesson=lesson["id"]):
                result = sql_runner.check_sql(ex["solution"], ex["tests"])
                self.assertTrue(
                    result["passed"],
                    f'{lesson["id"]} 未通过：{result["error"]}',
                )

    def test_every_runnable_block_executes(self):
        for lesson in self.lessons:
            for index, block in enumerate(lesson["blocks"], start=1):
                if block.get("type") != "code" or not block.get("runnable"):
                    continue
                with self.subTest(lesson=lesson["id"], block=index):
                    result = sql_runner.run_sql(block["code"])
                    self.assertTrue(result["ok"], f'{lesson["id"]}#{index}: {result["error"]}')

    def test_sandbox_denies_attach(self):
        result = sql_runner.run_sql("ATTACH DATABASE '/tmp/evil.db' AS evil;")
        self.assertFalse(result["ok"])
        self.assertEqual("DatabaseError", result["error"]["type"])

    def test_each_run_starts_from_a_clean_database(self):
        first = sql_runner.run_sql("CREATE TABLE t(x INTEGER); INSERT INTO t VALUES (1);")
        self.assertTrue(first["ok"])
        second = sql_runner.run_sql("SELECT * FROM t;")
        self.assertFalse(second["ok"], "第二次运行应看到全新的空库")

    def test_null_and_grouping_semantics(self):
        sql = (
            "CREATE TABLE r(h TEXT, p INTEGER);"
            "INSERT INTO r VALUES ('a',1),('a',NULL),('b',3);"
        )
        result = sql_runner.check_sql(
            sql + "SELECT h, COALESCE(SUM(p),0) AS total FROM r GROUP BY h ORDER BY h;",
            [
                "assert columns == ['h','total'], columns",
                "assert rows == [['a',1],['b',3]], rows",
            ],
        )
        self.assertTrue(result["passed"], result["error"])

    def test_test_failure_reports_first_reason(self):
        result = sql_runner.check_sql("SELECT 1 AS a;", ["assert rows == [[2]], '应为 2'"])
        self.assertFalse(result["passed"])
        self.assertEqual("TestFailed", result["error"]["type"])
        self.assertIn("应为 2", result["error"]["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
