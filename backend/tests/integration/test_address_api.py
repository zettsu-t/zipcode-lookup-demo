"""FastAPI逆引きAPIの統合テスト（実CSV使用）。DATA_DIRが設定されている場合のみ実行。"""

import os
import pytest
from fastapi.testclient import TestClient

DATA_DIR = os.environ.get("DATA_DIR", "data")
pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(DATA_DIR, "utf_ken_all.csv"))
    or not os.path.exists(os.path.join(DATA_DIR, "JIGYOSYO.CSV")),
    reason="実CSVが必要です。DATA_DIRを設定してください。",
)


@pytest.fixture(scope="module")
def client():
    from services import jigyosyo, ken_all

    ken_all.load(DATA_DIR)
    jigyosyo.load(DATA_DIR)
    from main import app

    return TestClient(app)


# ── バリデーション ──────────────────────────────────────────────────────────


def test_empty_query_returns_400(client):
    resp = client.get("/api/v2/address?q=")
    assert resp.status_code in (400, 422)


def test_one_char_query_returns_400(client):
    resp = client.get("/api/v2/address", params={"q": "東"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "query too short"


# ── 大口事業所 ───────────────────────────────────────────────────────────────


def test_kanagawa_prefectural_office(client):
    """神奈川県庁が231-8588・type=jigyoshoで返ること"""
    resp = client.get("/api/v2/address", params={"q": "神奈川県庁"})
    assert resp.status_code == 200
    results = resp.json()
    match = next((r for r in results if r["zipcode"] == "231-8588"), None)
    assert match is not None
    assert match["type"] == "jigyosho"


def test_tokyo_university_math(client):
    """東京大学大学院数理科学研究科が153-8914・type=jigyoshoで返ること。
    CSV上の事業所名は「東京大学大学院　数理科学研究科」（全角スペースあり）のため、
    部分一致する「数理科学研究科」でクエリする。
    """
    resp = client.get("/api/v2/address", params={"q": "数理科学研究科"})
    assert resp.status_code == 200
    results = resp.json()
    match = next((r for r in results if r["zipcode"] == "153-8914"), None)
    assert match is not None
    assert match["type"] == "jigyosho"


# ── 一般住所 ─────────────────────────────────────────────────────────────────


def test_kyobashi_returns_multiple_prefectures(client):
    """京橋は複数都道府県にヒットすること"""
    resp = client.get("/api/v2/address", params={"q": "京橋"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 1
    prefectures = {r["address"][:3] for r in results}
    assert len(prefectures) > 1


# ── 順序 ────────────────────────────────────────────────────────────────────


def test_jigyosho_comes_before_general(client):
    """jigyoshoがgeneralより先に返ること"""
    resp = client.get("/api/v2/address", params={"q": "神奈川県庁"})
    assert resp.status_code == 200
    results = resp.json()
    types = [r["type"] for r in results]
    if "jigyosho" in types and "general" in types:
        assert types.index("jigyosho") < types.index("general")


# ── 件数制限・ワイルドカード ─────────────────────────────────────────────────


def test_wildcard_dot_star_returns_empty(client):
    """正規表現 .* を入力しても件数超過で空リストが返ること（ReDOS対策）"""
    resp = client.get("/api/v2/address", params={"q": ".*"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_wildcard_asterisk_works(client):
    """ワイルドカード * が使えること。
    「伊勢*町」は伊勢市を含む町名も多くヒットして件数超過になるため、
    より限定的な「伊勢佐木*」を使う（横浜市中区のみ）。
    """
    resp = client.get("/api/v2/address", params={"q": "伊勢佐木*"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert all("伊勢佐木" in r["address"] for r in results)


# ── レスポンス形式 ───────────────────────────────────────────────────────────


def test_response_schema(client):
    """レスポンスのフィールド構造が正しいこと"""
    resp = client.get("/api/v2/address", params={"q": "横浜市中区"})
    assert resp.status_code == 200
    for item in resp.json():
        assert "zipcode" in item
        assert "address" in item
        assert item["type"] in ("general", "jigyosho")
        # 郵便番号のフォーマット確認（NNN-NNNN）
        assert len(item["zipcode"]) == 8
        assert item["zipcode"][3] == "-"
