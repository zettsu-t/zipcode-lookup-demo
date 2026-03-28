"""E2Eテスト共通設定。docker compose up が前提。"""

from pathlib import Path
import pytest

BASE_URL = "http://localhost:8000"
BACKEND_URL = "http://localhost:8001"
SCREENSHOTS = Path(__file__).parent / "screenshots"


@pytest.fixture(scope="session", autouse=True)
def ensure_screenshots_dir():
    SCREENSHOTS.mkdir(exist_ok=True)
