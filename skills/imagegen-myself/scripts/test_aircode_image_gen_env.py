import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name("aircode_image_gen.py")


def load_module():
    spec = importlib.util.spec_from_file_location("aircode_image_gen_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EnvPriorityTests(unittest.TestCase):
    def test_masked_does_not_reveal_key_prefix_or_suffix(self):
        module = load_module()

        self.assertEqual(module._masked("configured-test-token"), "configured")
        self.assertEqual(module._masked(None), "missing")

    def test_skill_local_env_overrides_workspace_env_for_myself_provider(self):
        module = load_module()
        keys = [
            "NEWAPI_BASE_URL",
            "NEWAPI_API_KEY",
            "IMAGEGEN_MYSELF_BASE_URL",
            "IMAGEGEN_MYSELF_API_KEY",
        ]
        original_env = {key: os.environ.get(key) for key in keys}
        original_cwd = Path.cwd()
        try:
            for key in keys:
                os.environ.pop(key, None)
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                skill_dir = root / "skill"
                scripts_dir = skill_dir / "scripts"
                workspace = root / "workspace"
                scripts_dir.mkdir(parents=True)
                workspace.mkdir()
                (skill_dir / ".env.local").write_text(
                    "\n".join(
                        [
                            "NEWAPI_BASE_URL=https://skill.example",
                            "NEWAPI_API_KEY=skill-key",
                        ]
                    ),
                    encoding="utf-8",
                )
                (workspace / ".env").write_text(
                    "\n".join(
                        [
                            "NEWAPI_BASE_URL=https://workspace.example",
                            "NEWAPI_API_KEY=workspace-key",
                        ]
                    ),
                    encoding="utf-8",
                )
                module.__file__ = str(scripts_dir / "aircode_image_gen.py")
                os.chdir(workspace)
                try:
                    module._load_local_env()
                    providers = module._providers()
                finally:
                    os.chdir(original_cwd)

                self.assertEqual(providers[0].base_url, "https://skill.example/v1")
                self.assertEqual(providers[0].api_key, "skill-key")
        finally:
            os.chdir(original_cwd)
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_extracts_url_when_provider_does_not_return_b64_json(self):
        module = load_module()

        payload = {"data": [{"url": "https://cdn.example/image.png"}]}

        self.assertEqual(module._extract_image_url(payload), "https://cdn.example/image.png")

    def test_write_image_from_url_downloads_bytes(self):
        module = load_module()

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, _exc_type, _exc, _tb):
                return False

            def read(self):
                return b"png-bytes"

        with tempfile.TemporaryDirectory() as tmp, patch.object(module.urllib.request, "urlopen", return_value=FakeResponse()):
            out = Path(tmp) / "image.png"
            saved = module._write_image_from_url("https://cdn.example/image.png", str(out), force=False)

            self.assertEqual(saved, out)
            self.assertEqual(out.read_bytes(), b"png-bytes")


if __name__ == "__main__":
    unittest.main()
