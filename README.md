# Claude Code と叶える変更要求をデモンストレーションする素材

本リポジトリは、Claude Code と人間が共同で、Webアプリの変更要求を体験をするための素材である。どんな変更要求をどう叶えるのかはネタバレしないように、別リポジトリに置く。

## シナリオ

このリポジトリは、結婚式の出席者に返礼はがきを送付するWebサービスを模している。公開サーバで運用するだけの堅牢性はないので、ローカル環境で実行すること。

本プロジェクトのファイルはほぼすべて、Claude Sonnet 4.6 + Claude Code の出力である。ドキュメントについては、Claude Sonnet 4.6 と、作者である私の共同執筆である。

## 機能

手短に言うと、返礼はがきの差出人(結婚した人)と、受取人(結婚式に出席した人)それぞれの、住所と郵便番号を入力する機能を用意した。開発はStage 1/2の2段階で実施する。

### Stage 1 : 差出人(自分)の住所登録と出席者リスト管理

郵便番号を入力すると住所を自動補完する(順引き)

### Stage 2 : 出席者の住所登録

ネタバレしないように、別リポジトリに置いた。

## 外部データ

日本郵便の [サイト](https://www.post.japanpost.jp/zipcode/download.html) からCSVファイルをダウンロードして、 `backend/data/` に配置する。配置するファイルは以下の二種類からなる。

### 住所の郵便番号

[こちら](https://www.post.japanpost.jp/zipcode/dl/utf/zip/utf_ken_all.zip) からダウンロードして、同梱の `utf_ken_all.csv` を配置する。無加工にする。

### 事業所の個別郵便番号

1. [こちら](https://www.post.japanpost.jp/zipcode/dl/jigyosyo/zip/jigyosyo.zip) からダウンロードして、同梱の `JIGYOSYO.CSV` を取り出す
2. `JIGYOSYO.CSV` をShift_JISからUTF-8に変換する。このとき変換不能な文字を捨てないと、Pythonでエラーになることがある。具体的には以下のコマンド実行する。

```bash
# nkfがなければインストールする
sudo apt-get install nkf
# Shift_JISからUTF-8に変換する。このとき変換不能な文字を捨てる
mv JIGYOSYO.CSV JIGYOSYO_SJIS.CSV
iconv -c -f SJIS -t UTF-8 JIGYOSYO_SJIS.CSV > JIGYOSYO.CSV
```

## クイックスタート

作者は Windows 11 + WSL + Ubuntu 22 で動作確認した。

### 1. 実行環境を用意する

- Python 3.11+
- uv でPythonパッケージを管理する
- Docker / Docker Compose

E2Eブラウザテスト（`make test-e2e`）を実行する場合は、Chromiumのシステム依存ライブラリを別途インストールする。

```bash
make install
sudo .venv/bin/playwright install --with-deps chromium
```

### 2. セットアップ

```bash
make install
```

### 3. 起動

```bash
# Docker で起動する
docker compose up

# ローカルで起動する
make dev
```

ブラウザから下記ローカルホストにアクセスすると、GUIが見える。

- Django(フロントエンド): http://localhost:8000
- FastAPI(バックエンド): http://localhost:8001
- FastAPI SwaggerUI: http://localhost:8001/docs

## 開発コマンド

必要なことはすべて `make` から実行する。

```bash
make install             # 依存パッケージのインストール
make install-playwright  # Playwrightブラウザのインストール(E2Eテストを実行する場合)
make format              # コード整形(ruff)
make lint           # 静的解析(ruff + mypy)
make test           # ユニット + インテグレーションテスト
make test-e2e       # E2Eテスト(docker compose up が前提)
make test-all       # 全テスト
make schema         # OpenAPIスキーマ再生成
make reset-db       # 住所録リセット(db.sqlite3 を削除して migrate)
make up             # docker compose up
make down           # docker compose down
make dev            # Dockerではなく直接フロントエンド/バックエンドを起動する
make dev-down       # 直接起動したフロントエンド/バックエンドを終了する
```

## アーキテクチャ

フロントエンド(Django)とバックエンド(FastAPI)を **意図的に分離** した。これは変更要求を受け入れやすくするためである。

```
[ブラウザ]
    ↓ HTML form / fetch API
[Django :8000]
    ↓ HTTP GET
[FastAPI :8001]
    ↓ 起動時に構築したメモリインデックス
[backend/data/utf_ken_all.csv / JIGYOSYO.CSV]
```

変更要求がバックエンドにのみ影響する場合、Django は一切触らない。詳細は [`docs/architecture.md`](docs/architecture.md) を参照すること。

## ドキュメント

|ドキュメント|内容|
|:-----------|:----|
| [`docs/requirements.md`](docs/requirements.md) | 要求仕様書 |
| [`docs/architecture.md`](docs/architecture.md) | アーキテクチャ仕様書 |
| [`docs/data_schema.md`](docs/data_schema.md) | データスキーマ定義 |
| [`docs/api_contract.md`](docs/api_contract.md) | API契約(文章) |
| [`docs/openapi_spec.yaml`](docs/openapi_spec.yaml) | OpenAPI仕様書 |
| [`docs/screen_spec.md`](docs/screen_spec.md) | 画面仕様書 |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code向け開発規約 |
| [`contributing.md`](contributing.md) | 開発規約 |

## 技術スタック

|カテゴリ|技術|
|:-------|:---|
| フロントエンド | Python 3.11+ / Django 5.x |
| バックエンド | Python 3.11+ / FastAPI |
| DB | SQLite(Django)/ インメモリSQLite(FastAPI) |
| テスト | pytest / Playwright / schemathesis |
| コード品質 | ruff / mypy |
| パッケージ管理 | uv |
| コンテナ | Docker / Docker Compose |

## 免責事項

本リポジトリの内容および実行結果について、作者は一切責任を負いません。特に郵便番号の辞書として使ったときに、正確なデータが表示されることを保証していません。Agentic Coding の練習としてお使いください。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開しています。自由にご活用ください。詳細は [LICENSE](LICENSE) を参照してください。
