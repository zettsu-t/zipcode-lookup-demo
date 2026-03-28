# contributing.md
# はがき配布サービス — 開発規約

---

## 言語・フレームワーク

| 対象 | 言語・バージョン |
|------|----------------|
| フロントエンド | Python 3.12 / Django 5.x |
| バックエンド | Python 3.12 / FastAPI 0.11x |
| テスト | pytest / Playwright |
| コンテナ | Docker / docker compose |

---

## コーディング規約

### Python 共通
- フォーマッタ：`ruff format`
- リンタ：`ruff check`
- 型チェック：`mypy`
- 実行：`make lint`

### 命名規則
- モデル・クラス：PascalCase（例：`Sender`, `Guest`）
- 関数・変数：snake_case
- 定数：UPPER_SNAKE_CASE
- テスト関数：日本語可（例：`def test_京橋は複数都道府県ヒットする():`）

### テスト
- テストファイルは実装ファイルと同じディレクトリに置く
- ユニットテストは外部依存なしで動くこと（フィクスチャCSVを使う）
- インテグレーションテストは `tests/integration/` に置く
- E2Eテストは `tests/e2e/` に置く

---

## Git規約

### ブランチ戦略
```
main          本番相当。直接pushしない。
feature/*     機能追加（例：feature/reverse-zipcode）
fix/*         バグ修正
```

### コミットメッセージ
```
feat: 逆引きエンドポイントを追加
fix: 郵便番号のハイフン変換を修正
test: 京橋の複数ヒットテストを追加
docs: CLAUDE.mdにFTS5の制約を追記
chore: .gitignoreにCSVを追加
```

### マージ前チェックリスト
- [ ] `make test` が通る
- [ ] `make lint` が通る
- [ ] `docker compose up` でブラウザ動作確認できる

---

## ディレクトリ規約

```
frontend/
  app/
    tests/          ユニットテスト（Django）
  tests/
    integration/    インテグレーションテスト（Django）

backend/
  routers/          エンドポイント定義
  services/         CSVロード・インデックス構築
  tests/            ユニットテスト（FastAPI）
  tests/integration/  インテグレーションテスト（FastAPI）

tests/
  e2e/              E2Eテスト（Playwright）

data/               CSVファイル置き場（Gitに含めない）
```

---

## Makefile ターゲット

```bash
make install     # 依存パッケージのインストール
make lint        # ruff + mypy
make test        # ユニット + インテグレーション
make test-e2e    # E2E（docker compose up が前提）
make test-all    # 全テスト
make up          # docker compose up
make down        # docker compose down
```
