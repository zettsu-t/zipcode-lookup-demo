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
    rows = [_row("2310017", "神奈川県", "横浜市中区", "港町")]
    with open(
        os.path.join(str(tmp_path), "utf_ken_all.csv"), "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)
    ken_all.load(str(tmp_path))
    result = ken_all.lookup("231-0017")
    assert result == {"zipcode": "231-0017", "address": "神奈川県横浜市中区港町"}


def test_unknown_zipcode(tmp_path):
    rows = [_row("2310017", "神奈川県", "横浜市中区", "港町")]
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


def _load_tmp(tmp_path, rows):
    with open(
        os.path.join(str(tmp_path), "utf_ken_all.csv"), "w", encoding="utf-8", newline=""
    ) as f:
        csv.writer(f).writerows(rows)
    ken_all.load(str(tmp_path))


def test_search_partial_match(tmp_path):
    _load_tmp(
        tmp_path,
        [
            _row("2310017", "神奈川県", "横浜市中区", "港町"),
            _row("1000001", "東京都", "千代田区", "千代田"),
        ],
    )
    results = ken_all.search("横浜市")
    assert len(results) == 1
    assert results[0]["zipcode"] == "231-0017"
    assert results[0]["type"] == "general"


def test_search_wildcard(tmp_path):
    _load_tmp(
        tmp_path,
        [
            _row("2310017", "神奈川県", "横浜市中区", "港町"),
            _row("2310045", "神奈川県", "横浜市中区", "伊勢佐木町"),
        ],
    )
    results = ken_all.search("神奈川*港町")
    assert len(results) == 1
    assert results[0]["zipcode"] == "231-0017"


def test_search_no_match(tmp_path):
    _load_tmp(tmp_path, [_row("2310017", "神奈川県", "横浜市中区", "港町")])
    assert ken_all.search("存在しない") == []
