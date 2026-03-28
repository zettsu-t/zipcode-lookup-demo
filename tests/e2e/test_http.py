"""E2Eテスト（HTTPレベル）: docker compose up 後に実行する。ブラウザ不要。"""

import re
import uuid

import pytest
import requests

# 実行ごとにユニークなIDを付与し、DB 残留レコードと衝突しないようにする
_RUN_ID = uuid.uuid4().hex[:6]

BASE = "http://localhost:8000"
BACKEND = "http://localhost:8001"


def _csrf_post(path: str, data: dict) -> requests.Response:
    """CSRFトークンを取得してDjangoへPOSTする。"""
    s = requests.Session()
    s.get(f"{BASE}{path}")
    token = s.cookies.get("csrftoken", "")
    return s.post(
        f"{BASE}{path}",
        data={**data, "csrfmiddlewaretoken": token},
        allow_redirects=False,
    )


# ── 疎通確認 ────────────────────────────────────────────────────────────────


class TestConnectivity:
    def test_frontend_responds(self):
        resp = requests.get(f"{BASE}/guests/")
        assert resp.status_code == 200

    def test_backend_openapi_responds(self):
        resp = requests.get(f"{BACKEND}/openapi.json")
        assert resp.status_code == 200


# ── 差出人 CRUD ─────────────────────────────────────────────────────────────


class TestSender:
    def test_get_returns_200(self):
        resp = requests.get(f"{BASE}/sender/")
        assert resp.status_code == 200
        assert "差出人設定" in resp.text

    def test_post_valid_data_redirects(self):
        resp = _csrf_post(
            "/sender/",
            {
                "names": "山田 太郎\n山田 花子",
                "zipcode": "231-0045",
                "address": "神奈川県横浜市中区伊勢佐木町",
            },
        )
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/sender/")

    def test_saved_data_appears_in_form(self):
        resp = requests.get(f"{BASE}/sender/")
        assert "山田 太郎" in resp.text

    def test_post_empty_names_stays_on_page(self):
        resp = _csrf_post(
            "/sender/",
            {
                "names": "",
                "zipcode": "231-0045",
                "address": "神奈川県横浜市中区伊勢佐木町",
            },
        )
        # バリデーションエラーのため 200 でフォームを再表示
        assert resp.status_code == 200


# ── 出席者 CRUD ─────────────────────────────────────────────────────────────


class TestGuests:
    GUEST_NAME = f"E2Eテスト_{_RUN_ID}"

    def test_list_returns_200(self):
        resp = requests.get(f"{BASE}/guests/")
        assert resp.status_code == 200
        assert "出席者リスト" in resp.text

    def test_create_form_returns_200(self):
        resp = requests.get(f"{BASE}/guests/new/")
        assert resp.status_code == 200
        assert "出席者追加" in resp.text

    def test_create_guest_redirects_to_list(self):
        resp = _csrf_post(
            "/guests/new/",
            {
                "names": self.GUEST_NAME,
                "zipcode": "",
                "address": "",
            },
        )
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/guests/")

    def test_created_guest_appears_in_list(self):
        resp = requests.get(f"{BASE}/guests/")
        assert self.GUEST_NAME in resp.text

    def test_edit_form_returns_200(self):
        pk = _find_guest_pk(self.GUEST_NAME)
        resp = requests.get(f"{BASE}/guests/{pk}/edit/")
        assert resp.status_code == 200
        assert "出席者編集" in resp.text

    def test_edit_guest_redirects_to_list(self):
        pk = _find_guest_pk(self.GUEST_NAME)
        resp = _csrf_post(
            f"/guests/{pk}/edit/",
            {
                "names": self.GUEST_NAME,
                "zipcode": "231-0045",
                "address": "神奈川県横浜市中区伊勢佐木町",
            },
        )
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/guests/")

    def test_edited_data_appears_in_list(self):
        resp = requests.get(f"{BASE}/guests/")
        assert "231-0045" in resp.text

    def test_delete_confirm_returns_200(self):
        pk = _find_guest_pk(self.GUEST_NAME)
        resp = requests.get(f"{BASE}/guests/{pk}/delete/")
        assert resp.status_code == 200
        assert "削除確認" in resp.text
        assert self.GUEST_NAME in resp.text

    def test_delete_guest_redirects_to_list(self):
        pk = _find_guest_pk(self.GUEST_NAME)
        resp = _csrf_post(f"/guests/{pk}/delete/", {})
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/guests/")

    def test_deleted_guest_not_in_list(self):
        resp = requests.get(f"{BASE}/guests/")
        assert self.GUEST_NAME not in resp.text


def _find_guest_pk(name: str) -> str:
    """出席者リストのHTMLから指定した名前のゲストの pk を取得する。"""
    resp = requests.get(f"{BASE}/guests/")
    # <tr>…</tr> 単位で解析し、名前列（2列目）と編集リンクの pk を照合する
    for row_m in re.finditer(r"<tr>(.*?)</tr>", resp.text, re.DOTALL):
        row = row_m.group(1)
        cells = re.findall(r"<td>(.*?)</td>", row, re.DOTALL)
        edit_m = re.search(r'href="/guests/(\d+)/edit/"', row)
        if len(cells) >= 2 and edit_m and name in cells[1]:
            return edit_m.group(1)
    pytest.skip(f"ゲスト '{name}' が見つからない")


# ── 郵便番号プロキシ ─────────────────────────────────────────────────────────


class TestZipLookupProxy:
    def test_valid_7digit_zip(self):
        resp = requests.get(f"{BASE}/zip/lookup/", params={"code": "2310045"})
        assert resp.status_code == 200
        data = resp.json()
        assert "address" in data
        assert "神奈川" in data["address"]

    def test_valid_hyphen_zip(self):
        resp = requests.get(f"{BASE}/zip/lookup/", params={"code": "231-0045"})
        assert resp.status_code == 200
        data = resp.json()
        assert "神奈川" in data["address"]

    def test_unknown_zip_returns_404(self):
        resp = requests.get(f"{BASE}/zip/lookup/", params={"code": "0000000"})
        assert resp.status_code == 404

    def test_invalid_format_returns_error(self):
        resp = requests.get(f"{BASE}/zip/lookup/", params={"code": "invalid"})
        assert resp.status_code in (400, 422)
