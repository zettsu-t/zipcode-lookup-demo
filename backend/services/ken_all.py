"""
ken_all.csv（UTF-8版）を読み込んで郵便番号インデックスを構築する。

CSV列（0-indexed）:
  2: 郵便番号（7桁、ハイフンなし）
  6: 都道府県
  7: 市区町村
  8: 町域

町域名が複数行に分割されているレコードは結合する（括弧が閉じていない場合に検出）。
"""

import csv
import os
import sqlite3
import sys

# {zipcode_with_hyphen: address_string}
_index: dict[str, str] = {}

# 逆引き用インメモリSQLite
_rev_conn: sqlite3.Connection | None = None


def _like_pattern(query: str) -> str:
    """ユーザクエリをSQLite LIKEパターンに変換する。LIKE特殊文字をエスケープし、*を%に変換する。"""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    if "*" in escaped:
        inner = escaped.replace("*", "%")
        prefix = "" if inner.startswith("%") else "%"
        suffix = "" if inner.endswith("%") else "%"
        return f"{prefix}{inner}{suffix}"
    return f"%{escaped}%"


def _to_hyphen(digits: str) -> str:
    return f"{digits[:3]}-{digits[3:]}"


def load(data_dir: str) -> None:
    global _index, _rev_conn
    path = os.path.join(data_dir, "utf_ken_all.csv")
    if not os.path.exists(path):
        print(
            f"ERROR: {path} が見つかりません。CSVを配置してから起動してください。", file=sys.stderr
        )
        sys.exit(1)

    index: dict[str, str] = {}
    pending_zip: str | None = None
    pending_parts: list[str] = []

    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 9:
                continue
            zipcode = _to_hyphen(row[2].strip())
            pref = row[6].strip()
            city = row[7].strip()
            area = row[8].strip()

            if pending_zip == zipcode:
                # 前の行の続き（括弧が未閉の場合）
                pending_parts.append(area)
                combined = "".join(pending_parts)
                if combined.count("(") == combined.count(")") and combined.count(
                    "（"
                ) == combined.count("）"):
                    index[zipcode] = combined
                    pending_zip = None
                    pending_parts = []
            else:
                if pending_zip is not None:
                    # 前のzipが未完のまま次のzipが来た（異常ケース）→ そのまま保存
                    index[pending_zip] = "".join(pending_parts)
                    pending_zip = None
                    pending_parts = []

                full_address = pref + city + area
                # 括弧が開いたまま → 次行に続く
                if area.count("(") != area.count(")") or area.count("（") != area.count("）"):
                    pending_zip = zipcode
                    pending_parts = [full_address]
                else:
                    index[zipcode] = full_address

    if pending_zip:
        index[pending_zip] = "".join(pending_parts)

    _index = index

    # 逆引き用インデックスを構築
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("CREATE TABLE ken_all (zipcode TEXT NOT NULL, address TEXT NOT NULL)")
    conn.executemany("INSERT INTO ken_all VALUES (?, ?)", index.items())
    conn.commit()
    _rev_conn = conn

    print(f"ken_all loaded: {len(_index)} entries from {path}")


def lookup(zipcode: str) -> dict | None:
    """ハイフンあり形式のzipcodeで検索。見つからなければNone。"""
    address = _index.get(zipcode)
    if address is None:
        return None
    return {"zipcode": zipcode, "address": address}


def search(query: str, limit: int = 101) -> list[dict]:
    """住所の部分一致検索。ワイルドカード * 使用可。"""
    if _rev_conn is None:
        return []
    cur = _rev_conn.execute(
        "SELECT zipcode, address FROM ken_all WHERE address LIKE ? ESCAPE '\\' LIMIT ?",
        (_like_pattern(query), limit),
    )
    return [{"zipcode": row[0], "address": row[1], "type": "general"} for row in cur]
