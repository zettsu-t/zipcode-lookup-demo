# はがき配布サービス — アーキテクチャ設計

## 1. 構成方針

本サービスはフロントエンドとバックエンドを**意図的に分離する**。

```
[ブラウザ]
    ↓ HTML form / fetch API
[Django フロントエンド]
    ↓ HTTP GET
[FastAPI バックエンド]
    ↓ 読み込み済みインデックス
[ken_all.csv / JIGYOSYO.CSV]
```

### なぜ分けるか

一枚岩のDjangoアプリとして実装することも技術的には可能だが、あえて分離する理由は以下の通り。

| 関心事 | Django | FastAPI |
|--------|--------|---------|
| 役割 | ユーザーの画面と操作 | データの検索と返却 |
| 状態 | アプリケーションデータ（Sender, Guest） | 郵便番号インデックス（起動時に構築） |
| 変更頻度 | UIの変更に追従 | 検索ロジックの変更に追従 |
| 将来の置き換え | — | 住所SaaSに差し替え可能 |

変更要求がバックエンドにのみ影響する場合、Djangoは一切触らない。これが分離の実質的な価値である。

---

## 2. コンポーネント構成

```
repo/
├── frontend/          # Django
│   ├── manage.py
│   ├── config/        # settings.py, urls.py
│   └── app/
│       ├── models.py  # Sender, Guest
│       ├── views.py
│       ├── urls.py
│       └── templates/
│           ├── sender.html   # 差出人登録（順引き補完つき）
│           └── guest.html    # 出席者リスト（stage 2で逆引き補完追加）
│
├── backend/           # FastAPI
│   ├── main.py
│   ├── routers/
│   │   ├── zipcode.py   # GET /api/v1/zip?code=   順引き（stage 1）
│   │   └── address.py   # GET /api/v2/address?q=  逆引き（stage 2）
│   └── services/
│       ├── ken_all.py   # ken_all.csv 読み込み・インデックス構築
│       └── jigyosyo.py  # JIGYOSYO.CSV 読み込み・インデックス構築
│
├── data/              # CSVファイル置き場（.gitignoreで除外）
│   ├── ken_all.csv
│   └── JIGYOSYO.CSV
│
└── docker-compose.yml
```

---

## 3. データベース

| サービス | DB | 備考 |
|---------|-----|------|
| Django | SQLite | デモ用途のため簡潔さを優先 |
| FastAPI | なし（メモリ上のインデックス） | 起動時にCSVを読み込んで構築 |

FastAPIは永続化DBを持たない。CSVの内容をメモリ上に展開することで、外部DB依存なしに100ms以内の応答を実現する。

特記事項として、FastAPIがリクエストをスレッドプールで処理する際に、DBMSを適切に扱うよう注意する。そうでないと `[sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.]` のようなエラーが発生する。

SQLiteのインメモリ接続はデフォルトでスレッド安全でない。起動時（メインスレッド）に作成した接続をリクエストスレッドで使うと上記エラーになる。接続作成時に `check_same_thread=False` を指定することで回避できる。読み込み専用のため競合は発生しない。

```python
conn = sqlite3.connect(":memory:", check_same_thread=False)
```

---

## 4. API エンドポイント一覧

詳細は `api_contract.md` および `openapi_spec.yaml` を参照。

| エンドポイント | メソッド | stage | 説明 |
|--------------|---------|-------|------|
| `/api/v1/zip` | GET | 1 | 郵便番号→住所の順引き |
| `/api/v2/address` | GET | 2 | 住所→郵便番号の逆引き |

バージョニング方針：URLパスにバージョンを含める（`/api/v1/`, `/api/v2/`）。既存エンドポイントは変更しない。stage 2の追加は`/api/v2/`として新設する。

---

## 5. Django → FastAPI 通信

- DjangoのビューまたはテンプレートのJavaScriptからFastAPIを呼ぶ
- 通信はHTTP GETのみ
- FastAPIのベースURLは Django の設定ファイル（`settings.py`）に環境変数として持つ
- Django はバックエンドの実装詳細（インデックス構造、CSVフォーマット等）を知らない

---

## 6. 開発環境

### パッケージ管理

[uv](https://github.com/astral-sh/uv) を使う。pipより高速で、仮想環境の作成・パッケージインストールを一貫して扱える。

```bash
make install   # .venv を作成し、全パッケージをインストールしてフックを登録する
```

- 仮想環境は `.venv/`（`.gitignore` 対象）
- `ruff`・`pyyaml` は `.venv` 内にインストールされる
- コマンド実行は `.venv/bin/python` / `.venv/bin/ruff` を直接呼ぶ（`source .venv/bin/activate` 不要）

### コード品質

[ruff](https://docs.astral.sh/ruff/) でフォーマットとlintを行う。設定はルートの `pyproject.toml` に集約する。

```bash
make format    # ruff format（自動修正）
make lint      # ruff check（エラーがあれば終了コード1）
```

### サポート構成

| 環境 | 状態 | 備考 |
|------|------|------|
| Ubuntu 24 ネイティブ | ◎ 基本 | 開発・検証の基準環境 |
| Windows 11 + WSL + Ubuntu 22 | ○ 動作確認済み | WSL2を前提とする |
| WSL + Dockerコンテナ | ○ 動作確認済み | Dockerfileのベースイメージは軽量ディストリビューション（Alpine or Debian slim）を使う |

### Dockerfileのベースイメージ方針

Ubuntu ベースは使わない。軽量なベースイメージを選ぶ。具体的なディストリビューションは実装時に決定する。

### 動作確認の基準

- `make test` が Ubuntu 24 ネイティブで通ること
- `make test` が WSL + Ubuntu 22 で通ること

---

## 7. 起動方法

### Docker（推奨）

```bash
docker compose up
```

### ローカル（Docker不使用）

```bash
make dev-migrate   # 初回のみ
make dev           # バックエンド・フロントエンド両方を起動
make dev-down      # 停止
```

- Django: `http://localhost:8000`
- FastAPI: `http://localhost:8001`

FastAPI 起動時に `data/` 以下のCSVを読み込んでインデックスを構築する。CSVが存在しない場合は起動エラーとする（サイレントに無効化しない）。

---

## 8. 成果物一覧

Claude Codeが生成するファイルの全リスト。`*` は本ドキュメント群（Claude Codeへの入力）として既に存在するもの。

```
repo/
├── * CLAUDE.md
├── * CONTRIBUTING.md  (contributing.md を改名)
├── * .gitignore
├── * .gitattributes
├── * .pre-commit-config.yaml  (architecture.mdの記述から生成)
├── LICENSE                    # MIT License（別途入手）
├── README.md                  # クイックスタート・CSV配置手順・makeコマンド一覧
├── Makefile                   # architecture.mdのセクション11から生成
├── pyproject.toml             # uv + 依存パッケージ定義
├── docker-compose.yml         # architecture.mdのセクション13から生成
├── .spectral.yaml             # openapi_spec.yamlのLint設定
├── .env.example               # 環境変数のテンプレート（BACKEND_URL等）
│
├── * docs/
│   ├── * requirements.md
│   ├── * data_schema.md
│   ├── * architecture.md
│   ├── * api_contract.md
│   └── * openapi_spec.yaml
│
├── frontend/                  # Django
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   └── app/
│       ├── models.py          # Sender, Guest
│       ├── views.py
│       ├── urls.py
│       ├── templates/
│       │   ├── sender.html    # 差出人登録（順引き補完つき）
│       │   └── guest.html     # 出席者リスト（stage 2で逆引き補完追加）
│       └── tests/
│           └── unit/
│
├── backend/                   # FastAPI
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── main.py
│   ├── routers/
│   │   ├── zipcode.py         # GET /api/v1/zip    順引き（stage 1）
│   │   └── address.py         # GET /api/v2/address 逆引き（stage 2）
│   ├── services/
│   │   ├── ken_all.py         # ken_all.csv 読み込み・インデックス構築
│   │   └── jigyosyo.py        # JIGYOSYO.CSV 読み込み・インデックス構築
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── tests/
│   └── e2e/                   # Playwright E2Eテスト
│
├── data/                      # CSVファイル置き場（.gitignoreで除外）
│   ├── ken_all.csv            # 別途ダウンロード
│   └── JIGYOSYO.CSV           # 別途ダウンロード
│
└── .github/
    └── workflows/
        └── ci.yml             # make ci を自動実行
```

---

## 9. やらないこと（この設計で明示的に除外するもの）

- DjangoとFastAPIを1プロセスに統合する
- FastAPIにDBを持たせる（PostgreSQL等）
- 認証・セッション管理
- CSVのホスティング・自動ダウンロード（手動で `backend/data/` に配置する）

---

## 10. 品質保証

### パイプライン全体像

```
git commit
    │
    ▼
[pre-commit hook]  scripts/hooks/pre-commit
    ├─ ruff format backend/ frontend/   → 自動修正してステージングに追加
    ├─ ruff check  backend/ frontend/   → 問題があれば失敗・コミット中断
    └─ backend/ が変更されていたら
           └─ make schema               → docs/openapi_spec.yaml を再生成してステージングに追加
    │
    ▼  （フックが通れば）
[コミット確定]
```

`make test` は CI と同じ内容をローカルで手動実行するためのコマンド。

### 現在の実装（stage 1）

| ゲート | タイミング | ツール | 対象 | CSV必要 |
|--------|-----------|--------|------|---------|
| フォーマット | コミット時（自動） | ruff format | `backend/` `frontend/` | — |
| Lint | コミット時（自動） | ruff check | `backend/` `frontend/` | — |
| スキーマ同期 | `backend/` 変更時（自動） | `scripts/export_openapi.py` | `docs/openapi_spec.yaml` | — |
| ユニットテスト | 手動 `make test` | pytest | `backend/tests/unit/` `frontend/tests/unit/` | — |
| インテグレーションテスト | 手動 `make test` | pytest + httpx | `backend/tests/integration/` | 必要 |
| スキーマ適合テスト | 手動 `make test-spec` | schemathesis | `docs/openapi_spec.yaml` vs 実装 | 必要 |

#### テスト設定

テストの設定はルートの `pyproject.toml` に集約する。

```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests", "frontend/tests"]
asyncio_mode = "strict"
```

`backend/tests/` と `frontend/tests/` の `__init__.py` は置かない。同名パッケージの衝突を避けるため、pytestのファイルベース発見を使う。

#### OpenAPI スキーマの同期

`docs/openapi_spec.yaml` は `scripts/export_openapi.py` によって FastAPI の実装から自動生成される。手書きしない。

```bash
make schema   # 手動で再生成したいとき
```

pre-commit hook が `backend/` の変更を検出すると自動で再生成・ステージングするため、実装と仕様書の乖離がコミット時点で防がれる。

---

### テスト戦略（全 stage）

テストはアーキテクチャの構造に従って4層に分ける。分離した設計はテストの独立性を保証する。

#### 層の定義

| 層 | 対象 | ツール | stage |
|----|------|--------|-------|
| ユニットテスト | 関数・クラス単体 | pytest | 1, 2 |
| コンポーネントテスト | Django / FastAPI 各サービス単体 | pytest + httpx | 1, 2 |
| E2Eテスト | ブラウザ操作（Django + FastAPI 結合） | Playwright | 1, 2 |
| 外部仕様テスト | FastAPI の実装が openapi_spec.yaml に準拠しているか | schemathesis | 2 |

### ユニットテスト

FastAPIはDBを持たずメモリインデックスのみのため、テスト用フィクスチャとして小さなCSVを渡せば外部依存なしでテストできる。

```python
# 例：実CSVに依存しないテスト
def test_京橋は複数都道府県ヒットする(small_index):
    results = lookup_by_address("京橋", small_index)
    prefectures = {r["address"][:3] for r in results}
    assert len(prefectures) > 1
```

### コンポーネントテスト（FastAPI）

実CSV（`data/ken_all.csv`, `data/JIGYOSYO.CSV`）を使って実データで検証する。ユニットテストとは明示的に分けて管理する。

代表的なテストケース：

| テストケース | 期待値 | 検証内容 |
|------------|--------|---------|
| `神奈川県庁` | `231-8588` | 大口事業所の即答 |
| `東京大学大学院数理科学研究科` | `153-8914` | 大口事業所・長い名称 |
| `京橋` | 複数件・複数都道府県 | 地名重複の仕様確認 |
| `.*` | 件数 < 100 | ReDOS・ワイルドカード制御 |
| `` （空文字） | 400エラー | 入力バリデーション |

### E2Eテスト（Playwright）

ブラウザを通じてDjangoとFastAPIの結合を検証する。

```
シナリオ例（stage 2）：
1. 出席者登録画面を開く
2. 住所欄に「横浜市中区」と入力（IME確定）
3. 候補が表示されることを確認
4. 候補をクリックして郵便番号欄が補完されることを確認
```

### 外部仕様テスト（schemathesis）

`openapi_spec.yaml` を仕様書として、FastAPIの実装がその契約に準拠しているかを自動検証する。仕様書を書いた意味をここで完結させる。

```bash
schemathesis run openapi_spec.yaml --url http://localhost:8001
```

schemathesisは仕様からテストケースを自動生成する。人間が書いたテストでは見落としがちなエッジケース（型の境界値・必須パラメータ欠落等）を網羅する。

#### テスト実行

```bash
make test           # ユニット + インテグレーション
make test-spec      # スキーマ適合テスト（CSV必要。バックエンドを自動起動して schemathesis を実行）
make test-e2e       # E2Eテスト・未実装（docker compose up が前提）
make test-all       # ユニット + インテグレーション + E2E
```

#### スキーマ適合テスト（schemathesis）

`docs/openapi_spec.yaml` を契約として、FastAPI 実装がその仕様に準拠しているかを検査する。

```
make test-spec の動作:
  1. backend/data/utf_ken_all.csv の存在を確認（なければエラーメッセージで終了）
  2. バックエンドをポート 8001 で起動（既に起動中なら再利用）
  3. schemathesis run docs/openapi_spec.yaml --checks all を実行
  4. 終了時（正常・エラー・Ctrl+C 問わず）バックエンドを停止
```

schemathesis は仕様書のパラメータ型・必須項目からテストケースを自動生成し、以下を検査する。

- 5xx レスポンスが返らないこと
- レスポンスのステータスコードが仕様と一致すること
- レスポンスボディが仕様のスキーマと一致すること

---

## 11. Makefile

めんどくさくて忘れがちな操作を `make` 一発で実行できるようにする。

```makefile
# セットアップ（uv で仮想環境を作成してインストール、フックを登録）
install:
    uv venv
    uv pip install -e "backend[dev]" -e "frontend[dev]" ruff pyyaml

# コード整形・静的解析（.venv/bin/ruff を直接呼ぶ）
format:
    $(RUFF) format backend/ frontend/
lint:
    $(RUFF) check backend/ frontend/

# OpenAPI スキーマ生成（FastAPI の実装から自動生成）
schema:
    $(PY) scripts/export_openapi.py > docs/openapi_spec.yaml

# テスト（testpaths は pyproject.toml で設定）
test:
    $(PY) -m pytest -v
test-e2e:
    $(PY) -m pytest tests/e2e/ -v
test-all:
    make test
    make test-e2e

# Docker
up:
    docker compose up
down:
    docker compose down
build:
    docker compose build

# git フック登録
install-hooks:
    cp scripts/hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
```

---

## 12. pre-commit hook

コミット前に自動実行する。「めんどくさくて忘れがちなこと」を強制する。

フックは `scripts/hooks/pre-commit` に置き、`make install`（または `make install-hooks`）で `.git/hooks/pre-commit` にコピーされる。

```sh
# scripts/hooks/pre-commit の動作
1. ruff format backend/ frontend/   # 自動修正して再ステージング
2. ruff check backend/ frontend/    # 問題があれば失敗
3. backend/ のファイルが変更されていたら:
   - scripts/export_openapi.py を実行して docs/openapi_spec.yaml を再生成
   - git add docs/openapi_spec.yaml  # 自動でコミットに含める
```

`backend/` 以下のファイルが変更された場合のみスキーマを再生成するため、フロントエンド変更時は余計な処理が走らない。

---

## 13. デプロイ

### コンテナ構成

```yaml
# docker-compose.yml 構成イメージ
services:
  frontend:   # Django
    build: ./frontend
    ports: ["8000:8000"]
    environment:
      BACKEND_URL: http://backend:8001
    depends_on: [backend]

  backend:    # FastAPI
    build: ./backend
    ports: ["8001:8001"]
    volumes:
      - ./backend/data:/app/data:ro   # CSVをread-onlyでマウント
```

### CSVの配置（手動）

```bash
# docker compose up の前に実施する
mkdir -p data/
cp /path/to/ken_all.csv data/
cp /path/to/JIGYOSYO.CSV data/
docker compose up
```

CSVは `data/` ディレクトリにマウントされ、FastAPIが起動時に読み込む。CSVが存在しない場合、FastAPIは起動エラーで終了する（サイレントに無効化しない）。

### 完了条件

| stage | 確認内容 |
|-------|---------|
| 1 | `docker compose up` 後、ブラウザで差出人登録・順引き補完が動作する |
| 2 | `make test-all` 全通過 + `docker compose up` 後にE2Eテストが通過する |
