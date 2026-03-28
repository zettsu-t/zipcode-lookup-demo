"""E2Eテスト（ブラウザ）: docker compose up 後に実行する。スクリーンショットを残す。

実行前に playwright のブラウザをインストールすること:
    make install-playwright
"""

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

BASE = "http://localhost:8000"
SCREENSHOTS = Path(__file__).parent / "screenshots"


# ── スクリーンショット ─────────────────────────────────────────────────────


class TestScreenshots:
    """全画面の代表的な状態を撮影する。CI での目視確認・スクショぺたぺた撲滅用。"""

    def test_s1_sender_empty(self, page: Page):
        """S-1: 差出人未登録状態"""
        # 未登録状態を作るため既存データをクリア（ベストエフォート）
        page.goto(f"{BASE}/sender/")
        page.screenshot(path=str(SCREENSHOTS / "s1_sender.png"), full_page=True)
        expect(page.locator("h2")).to_have_text("差出人設定")

    def test_s1_sender_after_save(self, page: Page):
        """S-1: 差出人登録後"""
        page.goto(f"{BASE}/sender/")
        page.locator("#id_zipcode").fill("231-0017")
        page.locator("#id_address").fill("神奈川県横浜市中区")
        # names フィールドはテキストエリア
        page.locator("textarea").fill("山田 太郎\n山田 花子")
        page.locator("button[type=submit]").click()
        page.wait_for_url(f"{BASE}/sender/")
        page.screenshot(path=str(SCREENSHOTS / "s1_sender_saved.png"), full_page=True)
        expect(page.locator("h2")).to_have_text("差出人設定")

    def test_s2_guest_list_empty(self, page: Page):
        """S-2: 出席者0件"""
        # 出席者がいない状態（既存テスト環境では存在する場合もあるが撮影のみ）
        page.goto(f"{BASE}/guests/")
        page.screenshot(path=str(SCREENSHOTS / "s2_guest_list.png"), full_page=True)
        expect(page.locator("h2")).to_have_text("出席者リスト")

    def test_s3_guest_add_form(self, page: Page):
        """S-3: 出席者追加フォーム"""
        page.goto(f"{BASE}/guests/new/")
        page.screenshot(path=str(SCREENSHOTS / "s3_guest_add.png"), full_page=True)
        expect(page.locator("h2")).to_contain_text("出席者追加")

    def test_s4_guest_edit_form(self, page: Page):
        """S-4: 出席者編集フォーム（テスト用ゲストを作成して撮影）"""
        _create_guest(page, "スクショ テスト")
        # 最初の編集リンクをクリック
        page.goto(f"{BASE}/guests/")
        page.locator("a[href*='/edit/']").first.click()
        page.screenshot(path=str(SCREENSHOTS / "s4_guest_edit.png"), full_page=True)
        expect(page.locator("h2")).to_contain_text("出席者編集")

    def test_s5_guest_delete_confirm(self, page: Page):
        """S-5: 出席者削除確認"""
        page.goto(f"{BASE}/guests/")
        delete_links = page.locator("a[href*='/delete/']")
        if delete_links.count() == 0:
            pytest.skip("削除対象ゲストなし")
        delete_links.first.click()
        page.screenshot(path=str(SCREENSHOTS / "s5_guest_delete_confirm.png"), full_page=True)
        expect(page.locator("h2")).to_have_text("出席者削除確認")

    def test_s2_guest_list_with_guests(self, page: Page):
        """S-2: 出席者あり状態"""
        page.goto(f"{BASE}/guests/")
        page.screenshot(path=str(SCREENSHOTS / "s2_guest_list_with_guests.png"), full_page=True)


# ── 郵便番号 → 住所補完 ────────────────────────────────────────────────────


class TestZipcodeAutoComplete:
    """郵便番号フィールドの自動補完（JS 動作）を検証する。"""

    def test_enter_key_fills_address_on_sender(self, page: Page):
        """S-1: Enter キーで住所補完される"""
        page.goto(f"{BASE}/sender/")
        zipcode_input = page.locator("#id_zipcode")
        address_input = page.locator("#id_address")

        address_input.fill("")  # アドレス欄をクリア
        zipcode_input.fill("2310017")
        zipcode_input.press("Enter")

        expect(address_input).not_to_have_value("", timeout=5000)
        assert "神奈川" in address_input.input_value()

        page.screenshot(path=str(SCREENSHOTS / "s1_sender_zip_enter.png"), full_page=True)

    def test_blur_fills_address_on_sender(self, page: Page):
        """S-1: フォーカスが外れると住所補完される"""
        page.goto(f"{BASE}/sender/")
        zipcode_input = page.locator("#id_zipcode")
        address_input = page.locator("#id_address")

        address_input.fill("")
        zipcode_input.fill("1000001")
        address_input.click()  # blur を発生させる

        expect(address_input).not_to_have_value("", timeout=5000)
        assert "東京" in address_input.input_value()

        page.screenshot(path=str(SCREENSHOTS / "s1_sender_zip_blur.png"), full_page=True)

    def test_enter_key_fills_address_on_guest_form(self, page: Page):
        """S-3: 出席者追加フォームでも Enter キー補完が動く"""
        page.goto(f"{BASE}/guests/new/")
        zipcode_input = page.locator("#id_zipcode")
        address_input = page.locator("#id_address")

        zipcode_input.fill("2310017")
        zipcode_input.press("Enter")

        expect(address_input).not_to_have_value("", timeout=5000)
        assert "神奈川" in address_input.input_value()

        page.screenshot(path=str(SCREENSHOTS / "s3_guest_add_zip_enter.png"), full_page=True)

    def test_enter_key_fills_address_on_guest_edit_form(self, page: Page):
        """S-4: 出席者編集フォームでも Enter キー補完が動く"""
        _create_guest(page, "補完テスト 次郎")
        page.goto(f"{BASE}/guests/")
        # 作成したゲストの編集ページへ
        edit_links = page.locator("a[href*='/edit/']")
        if edit_links.count() == 0:
            pytest.skip("編集対象ゲストなし")
        edit_links.last.click()

        zipcode_input = page.locator("#id_zipcode")
        address_input = page.locator("#id_address")
        address_input.fill("")
        zipcode_input.fill("2310017")
        zipcode_input.press("Enter")

        expect(address_input).not_to_have_value("", timeout=5000)
        assert "神奈川" in address_input.input_value()

        page.screenshot(path=str(SCREENSHOTS / "s4_guest_edit_zip_enter.png"), full_page=True)

    def test_focus_moves_to_address_after_completion(self, page: Page):
        """Enter キー補完後にフォーカスが住所欄に移動する"""
        page.goto(f"{BASE}/sender/")
        zipcode_input = page.locator("#id_zipcode")
        address_input = page.locator("#id_address")

        address_input.fill("")
        zipcode_input.fill("2310017")
        zipcode_input.press("Enter")

        expect(address_input).not_to_have_value("", timeout=5000)
        # 補完後に address がフォーカスを持つ
        expect(address_input).to_be_focused()


# ── ヘルパー ──────────────────────────────────────────────────────────────


def _create_guest(page: Page, name: str) -> None:
    """テスト用ゲストをブラウザ経由で作成する。"""
    page.goto(f"{BASE}/guests/new/")
    page.locator("textarea").fill(name)
    page.locator("button[type=submit]").click()
    page.wait_for_url(f"{BASE}/guests/")
