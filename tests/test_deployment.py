"""Offline pre-deployment regression checks. No real credentials or API calls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from io import BytesIO
from unittest.mock import patch

from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from streamlit.elements.widgets.button import marshall_file

from ai_storyboard import resolve_api_key
from storyboard import generate_storyboard

ROOT = Path(__file__).resolve().parents[1]


class DeploymentTests(unittest.TestCase):
    def test_environment_cannot_enable_developer_key(self):
        with patch.dict(os.environ, {"VIDEOPROMPT_LOCAL_DEV": "1", "DEEPSEEK_API_KEY": "mock-developer-only"}), patch("ai_storyboard.generate_ai") as api:
            self.assertEqual(resolve_api_key("", True), "")
            self.assertEqual(resolve_api_key("mock-user", True), "mock-user")
            app = AppTest.from_file(str(ROOT / "app.py")).run()
            app.radio[0].set_value("AI智能模式").run()
            app.text_area[0].set_value("少女观察大殿。").run()
            self.assertFalse(app.checkbox)
            next(b for b in app.button if b.label == "开始AI生成").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(app.error)
            api.assert_not_called()

    def test_two_users_source_response_and_exports_are_isolated(self):
        def fake_ai(payload, key):
            source = json.loads(payload["messages"][1]["content"])["文案"]
            return generate_storyboard(source, "通用", 5), {"total_tokens": len(source)}

        with patch("ai_storyboard.generate_ai", side_effect=fake_ai), patch("ai_storyboard.build_opener", side_effect=AssertionError("No network")):
            first, second = [AppTest.from_file(str(ROOT / "app.py")).run() for _ in range(2)]
            for app, tag, key in ((first, "mock-private-A", "mock-key-A"), (second, "mock-private-B", "mock-key-B")):
                app.radio[0].set_value("AI智能模式").run()
                app.text_area[0].set_value(tag).run()
                app.text_input[0].set_value(key).run()
                next(b for b in app.button if b.label == "开始AI生成").click().run()
                self.assertFalse(app.exception)
            for app, own, other in ((first, "mock-private-A", "mock-private-B"), (second, "mock-private-B", "mock-private-A")):
                with patch("streamlit.elements.widgets.button.marshall_file", wraps=marshall_file) as download:
                    app.run()
                self.assertFalse(app.exception)
                self.assertEqual(app.text_area[0].value, own)
                self.assertIn(own, app.code[-1].value)
                self.assertNotIn(other, app.code[-1].value)
                self.assertNotIn(other, app.session_state["scenes"].to_string())
                calls = {call.args[2].label: call.args[1] for call in download.call_args_list}
                csv = calls["下载 CSV"].decode("utf-8-sig")
                sheet = load_workbook(BytesIO(calls["下载 Excel"])).active
                excel_text = str(list(sheet.values))
                for text in (csv, excel_text):
                    self.assertIn(own, text)
                    self.assertNotIn(other, text)
                    self.assertNotIn("mock-key-A", text)
                    self.assertNotIn("mock-key-B", text)

    def test_gitignore_upload_policy(self):
        self.assertIsNotNone(shutil.which("git"), "git is needed to verify actual ignore rules")
        ignored = [".venv/file", "nested/__pycache__/a.pyc", ".env", ".env.local", ".streamlit/secrets.toml",
                   "logs/server.log", ".cache/file", "exports/result.csv", "personal_data/story.txt",
                   "data/input.txt", "private/input.txt", "uploads/input.txt", "api_key.txt", "credentials.txt",
                   "certificate.pem", "draft.xlsx", "cache/response.json", "secret.key"]
        allowed = ["app.py", "ai_storyboard.py", "storyboard.py", "generator.py", "requirements.txt", "README.md",
                   ".gitignore", ".streamlit/config.toml", "tests/test_ai_storyboard.py", "tests/test_deployment.py",
                   "tests/test_generator.py", "tests/test_storyboard.py"]
        temp_root = ROOT / ".tmp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            shutil.copyfile(ROOT / ".gitignore", Path(folder) / ".gitignore")
            subprocess.run(["git", "init", "--quiet", folder], check=True, capture_output=True)
            check = subprocess.run(["git", "-c", f"core.excludesFile={os.devnull}", "check-ignore", "--no-index", "--stdin", "-z"],
                                   cwd=folder, input=("\0".join(ignored + allowed) + "\0").encode(), capture_output=True)
            self.assertIn(check.returncode, (0, 1))
            matches = set(check.stdout.decode().split("\0")) - {""}
            self.assertEqual(set(ignored), matches)

    def test_cloud_config_and_dependency_constraints(self):
        from importlib.metadata import version
        from packaging.requirements import Requirement

        config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text(encoding="utf-8-sig"))
        self.assertEqual(config["client"]["showErrorDetails"], "none")
        self.assertFalse(config["browser"]["gatherUsageStats"])
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8-sig").splitlines():
            if line.strip() and not line.startswith("#"):
                requirement = Requirement(line)
                self.assertIn(version(requirement.name), requirement.specifier)


if __name__ == "__main__":
    unittest.main()
