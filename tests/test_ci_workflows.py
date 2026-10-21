"""CI 配置的静态校验（不需要网络/平台凭据）。

锁住两类真实踩过的坑：
  R1 YAML 必须能被严格解析——重复键会被 GitHub 直接判为 Invalid workflow
     （2026-10-21 实际发生：mirror-sync 的 checkout 步骤写了两个 with:）
  R2 关键门禁必须在位：lint、JVM 单测、debug/release 构建、APK 探针、
     版本校验、镜像同步；任何一项被删都要显式改测试，不能悄悄消失
"""
import os
import unittest
from pathlib import Path

try:
    import yaml  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - 取决于运行环境
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = [
    ROOT / ".github/workflows/ci.yml",
    ROOT / ".gitcode/workflows/ci.yml",
    ROOT / ".workflow/MasterPipeline.yml",
]


def _strict_load(path):
    if yaml is None:
        if os.environ.get("REQUIRE_YAML") == "1":
            raise AssertionError(
                "REQUIRE_YAML=1 但未安装 PyYAML：CI 不允许跳过 workflow 静态校验"
            )
        raise unittest.SkipTest("未安装 PyYAML；由平台自身校验器兜底")

    class Strict(yaml.SafeLoader):
        pass

    def no_duplicates(loader, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"{path.name}: 重复键 {key!r}（行 {key_node.start_mark.line + 1}）")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    Strict.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicates
    )
    return yaml.load(path.read_text(encoding="utf-8"), Loader=Strict)


class WorkflowSyntaxTests(unittest.TestCase):
    def test_all_workflows_parse_without_duplicate_keys(self):
        for path in WORKFLOWS:
            with self.subTest(path=path.name):
                doc = _strict_load(path)
                self.assertIsInstance(doc, dict)
                # GitHub/GitCode 用 jobs，Gitee Go 用 stages —— 都要求至少有一层任务
                self.assertTrue(
                    "jobs" in doc or "stages" in doc,
                    f"{path.name} 既无 jobs 也无 stages",
                )


class GitHubGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    def test_required_gates_present(self):
        required = [
            "python -m unittest discover -s tests",
            "python tests/validate_content.py",
            "python web/gen_data.py",
            "git diff --exit-code -- web/data.js web/engine.js",
            "./gradlew :app:lintDebug",
            "./gradlew :app:lintRelease",
            "./gradlew :app:testDebugUnitTest",
            "./gradlew :app:assembleDebug",
            "./gradlew :app:assembleRelease",
            "python tests/ci_apk_probe.py",
            "scripts/ci/check_release_version.py",
            "bash scripts/ci/sync_mirrors.sh",
        ]
        missing = [c for c in required if c not in self.text]
        self.assertEqual(missing, [], f"CI 缺少门禁步骤: {missing}")

    def test_no_green_washing(self):
        # 允许的唯一 || true 是 SDK license 接受（后续 --list_installed 是硬门禁）
        bad = []
        for line in self.text.splitlines():
            if "|| true" in line and "--licenses" not in line:
                bad.append(line.strip())
            if "continue-on-error" in line:
                bad.append(line.strip())
        self.assertEqual(bad, [], f"发现吞错写法: {bad}")

    def test_release_is_gated_by_version_and_signature(self):
        self.assertIn("check_release_version.py", self.text)
        self.assertIn("apksigner", self.text)
        self.assertIn("--require-release", self.text)
        self.assertIn("environment: release", self.text)

    def test_mirror_sync_is_primary_repo_only(self):
        self.assertIn("github.repository == 'badhope/mashang-python'", self.text)

    def test_js_tests_are_forced_to_run(self):
        self.assertIn('REQUIRE_NODE: "1"', self.text)

    def test_yaml_check_is_enforced_on_github(self):
        self.assertIn('REQUIRE_YAML: "1"', self.text)


if __name__ == "__main__":
    unittest.main()
