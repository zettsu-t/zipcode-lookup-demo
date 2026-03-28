"""ken_all.pyのユニットテスト（実CSVを使わず、一時ファイルで検証）"""

import csv
import os
from services import ken_all


def _row(zipcode: str, pref: str, city: str, area: str) -> list[str]:
    return [
        "01101",
        "060  ",
        zipcode,
        "カナ",
        "カナ",
        "カナ",
        pref,
        city,
        area,
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]


def test_simple_lookup(tmp_path):
    rows = [_row("2310045", "神奈川県", "横浜市中区", "伊勢佐木町")]
    with open(
        os.path.join(str(tmp_path), "utf_ken_all.csv"), "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)
    ken_all.load(str(tmp_path))
    result = ken_all.lookup("231-0045")
    assert result == {"zipcode": "231-0045", "address": "神奈川県横浜市中区伊勢佐木町"}


def test_unknown_zipcode(tmp_path):
    rows = [_row("2310045", "神奈川県", "横浜市中区", "伊勢佐木町")]
    with open(
        os.path.join(str(tmp_path), "utf_ken_all.csv"), "w", encoding="utf-8", newline=""
    ) as f:
        csv.writer(f).writerows(rows)
    ken_all.load(str(tmp_path))
    assert ken_all.lookup("000-0000") is None


def test_split_record(tmp_path):
    """括弧で分割されたレコードが結合されること"""
    rows = [
        _row("1000001", "東京都", "千代田区", "千代田（次のビルを除く"),
        _row("1000001", "東京都", "千代田区", "ほげビル以外）"),
    ]
    with open(
        os.path.join(str(tmp_path), "utf_ken_all.csv"), "w", encoding="utf-8", newline=""
    ) as f:
        csv.writer(f).writerows(rows)
    ken_all.load(str(tmp_path))
    result = ken_all.lookup("100-0001")
    assert result is not None
    assert "次のビルを除く" in result["address"]
