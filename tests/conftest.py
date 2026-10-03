"""Central pytest fixtures for KatzenSuchApp tests."""

import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest


def _make_mock_config(db_path: Path):
    class MockConfig:
        pass
    mc = MockConfig()
    mc.db_path = str(db_path)
    mc.auth_db_path = str(db_path.parent / "auth.db")
    mc.api_host = "http://localhost"
    mc.api_port = "8000"
    mc.api_base_url = "http://localhost:8000"
    mc.ollama_url = "http://fake-ollama:11434/api/chat"
    mc.ollama_model = "test-model"
    mc.ollama_timeout = 30
    mc.cities = ["Berlin", "Hamburg", "München"]
    mc.scraper_interval_minutes = 15
    mc.log_level = "INFO"
    mc.secret_key = "test-secret"
    mc.jwt_algorithm = "HS256"
    mc.access_token_expire_minutes = 30
    mc.platform_configs = {}
    mc.filter_criteria = {
        "alter_min": 2,
        "alter_max": 8,
        "einzelgaenger": True,
        "kein_freigang_noetig": True
    }
    return mc


@pytest.fixture
def mock_config():
    """Create a fresh mock Config instance."""
    tmp_path = Path(tempfile.mkdtemp())
    db_path = tmp_path / "test_seen.db"
    return _make_mock_config(db_path), tmp_path


@pytest.fixture
def temp_db(mock_config):
    """Temporary DB with Config patched before imports."""
    mock_cfg, tmp_path = mock_config
    db_path = Path(mock_cfg.db_path)

    with patch('classes.Cconfig.Config', return_value=mock_cfg):
        from modules.db_utils import init_db
        if db_path.exists():
            db_path.unlink()
        init_db()
        yield db_path
        # cleanup
        try:
            db_path.unlink()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def patch_config_autouse():
    """Auto-patch Config for all tests to avoid real .env loading."""
    tmp_path = Path(tempfile.mkdtemp())
    db_path = tmp_path / "test_seen.db"
    mock_cfg = _make_mock_config(db_path)
    with patch('classes.Cconfig.Config', return_value=mock_cfg):
        yield
