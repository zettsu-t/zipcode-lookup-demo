"""FastAPI統合テスト（実CSV使用）。DATA_DIRが設定されている場合のみ実行。"""

import os
import pytest
from fastapi.testclient import TestClient

DATA_DIR = os.environ.get("DATA_DIR", "data")
pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(DATA_DIR, "utf_ken_all.csv")),
    reason="実CSVが必要です。DATA_DIRを設定してください。",
)


@pytest.fixture(scope="module")
def client():
    from services import ken_all

    ken_all.load(DATA_DIR)
    from main import app

    return TestClient(app)


def test_valid_zipcode_with_hyphen(client):
    resp = client.get("/api/v1/zip?code=231-0017")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zipcode"] == "231-0017"
    assert "神奈川県" in data["address"]


def test_valid_zipcode_without_hyphen(client):
    resp = client.get("/api/v1/zip?code=2310017")
    assert resp.status_code == 200


def test_invalid_format(client):
    resp = client.get("/api/v1/zip?code=abc")
    # FastAPIのQueryバリデーションが先に動くと422、ハンドラ内チェックなら400
    assert resp.status_code in (400, 422)


def test_not_found(client):
    resp = client.get("/api/v1/zip?code=000-0000")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "zipcode not found"
