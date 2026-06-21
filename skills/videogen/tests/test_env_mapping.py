import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from videogen import load_env_from_paths  # noqa: E402


def test_load_env_maps_project_octo_config_to_newapi_aliases(tmp_path: Path):
    api_env = tmp_path / "apps" / "api" / ".env"
    api_env.parent.mkdir(parents=True)
    api_env.write_text(
        "\n".join(
            [
                "OCTO_API_KEY=test-octo-key",
                "OCTO_BASE_URL=https://otuapi.com",
                "MINMAX_API_KEY=test-minmax-key",
            ]
        ),
        encoding="utf-8",
    )

    env = load_env_from_paths([tmp_path / ".env.local", api_env])

    assert env["NEWAPI_API_KEY"] == "test-octo-key"
    assert env["NEWAPI_BASE_URL"] == "https://otuapi.com"
    assert env["MINIMAX_API_KEY"] == "test-octo-key"
    assert env["MINIMAX_BASE_URL"] == "https://otuapi.com"
