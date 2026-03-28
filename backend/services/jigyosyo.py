"""
JIGYOSYO.CSV（大口事業所）を読み込んでインメモリSQLiteインデックスを構築する。

CSV列（0-indexed）:
  2: 事業所名（漢字）
  3: 都道府県
  4: 市区町村
  5: 町域
  7: 郵便番号（7桁、ハイフンなし）

検索キー: 事業所名（列2）
"""

import csv
import os
import sqlite3
import sys

_conn: sqlite3.Connection | None = None


def _to_hyphen(digits: str) -> str:
    d = digits.replace("-", "")
    return f"{d[:3]}-{d[3:]}"


def _like_pattern(query: str) -> str:
    """ユーザクエリをSQLite LIKEパターンに変換する。LIKE特殊文字をエスケープし、*を%に変換する。"""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    if "*" in escaped:
        inner = escaped.replace("*", "%")
        prefix = "" if inner.startswith("%") else "%"
        suffix = "" if inner.endswith("%") else "%"
        return f"{prefix}{inner}{suffix}"
    return f"%{escaped}%"


def load(data_dir: str) -> None:
    global _conn
    path = os.path.join(data_dir, "JIGYOSYO.CSV")
    if not os.path.exists(path):
        print(
            f"ERROR: {path} が見つかりません。CSVを配置してから起動してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("CREATE TABLE jigyosyo (zipcode TEXT NOT NULL, address TEXT NOT NULL)")

    rows = []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 8:
                continue
            name = row[2].strip()
            zipcode = _to_hyphen(row[7].strip())
            if name and zipcode:
                rows.append((zipcode, name))

    conn.executemany("INSERT INTO jigyosyo VALUES (?, ?)", rows)
    conn.commit()
    _conn = conn
    print(f"jigyosyo loaded: {len(rows)} entries from {path}")


def search(query: str, limit: int = 101) -> list[dict]:
    """事業所名の部分一致検索。ワイルドカード * 使用可。"""
    if _conn is None:
        return []
    cur = _conn.execute(
        "SELECT zipcode, address FROM jigyosyo WHERE address LIKE ? ESCAPE '\\' LIMIT ?",
        (_like_pattern(query), limit),
    )
    return [{"zipcode": row[0], "address": row[1], "type": "jigyosho"} for row in cur]
