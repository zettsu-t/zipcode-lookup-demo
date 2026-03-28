"""jigyosyo.pyのユニットテスト（実CSVを使わず、一時ファイルで検証）"""

import csv
import os
from services import jigyosyo


def _write_csv(tmp_path, rows: list[list[str]]) -> str:
    path = os.path.join(str(tmp_path), "JIGYOSYO.CSV")
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)
    return str(tmp_path)


def _row(name: str, pref: str, city: str, area: str, zipcode: str) -> list[str]:
    """JIGYOSYO.CSV の列順に合わせたダミー行を返す（0-indexed: 2=name, 3=pref, 4=city, 5=area, 7=zipcode）"""
    return ["", "", name, pref, city, area, "", zipcode, "", "", ""]


def test_simple_search(tmp_path):
    data_dir = _write_csv(
        tmp_path, [_row("神奈川県庁", "神奈川県", "横浜市中区", "日本大通", "2318588")]
    )
    jigyosyo.load(data_dir)
    results = jigyosyo.search("神奈川県庁")
    assert len(results) == 1
    assert results[0]["zipcode"] == "231-8588"
    assert results[0]["address"] == "神奈川県庁"
    assert results[0]["type"] == "jigyosho"


def test_partial_match(tmp_path):
    data_dir = _write_csv(
        tmp_path,
        [
            _row("神奈川県庁", "神奈川県", "横浜市中区", "日本大通", "2318588"),
            _row("東京都庁", "東京都", "新宿区", "西新宿", "1638001"),
        ],
    )
    jigyosyo.load(data_dir)
    results = jigyosyo.search("県庁")
    assert len(results) == 1
    assert results[0]["address"] == "神奈川県庁"


def test_wildcard(tmp_path):
    data_dir = _write_csv(
        tmp_path,
        [
            _row("神奈川県庁", "神奈川県", "横浜市中区", "日本大通", "2318588"),
            _row("東京都庁", "東京都", "新宿区", "西新宿", "1638001"),
        ],
    )
    jigyosyo.load(data_dir)
    results = jigyosyo.search("*庁")
    assert len(results) == 2


def test_no_match(tmp_path):
    data_dir = _write_csv(
        tmp_path, [_row("神奈川県庁", "神奈川県", "横浜市中区", "日本大通", "2318588")]
    )
    jigyosyo.load(data_dir)
    assert jigyosyo.search("存在しない") == []


def test_sql_special_chars_are_escaped(tmp_path):
    """% や _ がSQL LIKE特殊文字として解釈されないこと"""
    data_dir = _write_csv(
        tmp_path,
        [
            _row("100%天然水", "東京都", "千代田区", "丸の内", "1000001"),
            _row("東京大学", "東京都", "文京区", "本郷", "1138654"),
        ],
    )
    jigyosyo.load(data_dir)
    # "%" を含む検索でも SQLインジェクションにならず、該当1件のみヒット
    results = jigyosyo.search("100%")
    assert len(results) == 1
    assert results[0]["address"] == "100%天然水"
