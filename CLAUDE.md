# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Conversation Guidelines

- 常に日本語で会話する

## このレポジトリで開発するもの

結婚式の返礼はがきを送るウェブサービスを開発する。
詳細は各ドキュメントを参照。ここにはClaude Codeへの指示のみ書く。

---

## アーキテクチャ

**フロントエンド（Django）とバックエンド（FastAPI）を分離する。これは意図的な設計判断であり、変更しない。**

- `frontend/` : Django。画面・モデル・フォーム。DBはSQLite。
- `backend/`  : FastAPI。郵便番号検索APIのみ。DBなし。
- `backend/data/` : CSVファイル置き場。Gitに含めない。

DjangoからFastAPIへの通信はHTTP GETのみ。
Djangoはバックエンドの実装詳細（インデックス構造・CSVフォーマット・検索アルゴリズム）を知ってはならない。
詳細は `architecture.md` および `api_contract.md` を参照。

---

## 開発ステージ

| stage | やること | 完了条件 |
|-------|---------|---------|
| 1 | Django CRUD + 順引き補完 | `docker compose up` でブラウザ動作確認 |

**このブランチは Stage 1 完了状態です。Stage 2 の機能は含みません。**

---

## やること

- `requirements.md` の機能要件・非機能要件を実装する
- `api_contract.md` のエンドポイント仕様に厳密に従う
- `data_schema.md` のモデル定義に従う
- テストを書いてから、または書きながら実装する（`make test` が通ることを確認する）
- コードを変更したら `make test` を実行する
- 実装前に影響範囲を列挙する（既存コードを読んでから手を動かす）

---

## やらないこと

- DjangoとFastAPIを1プロセスに統合しない
- FastAPIにDBを持たせない（PostgreSQL等を追加しない）
- 認証・ログイン機能を追加しない
- はがき印刷機能を追加しない
- CSVファイルをリポジトリに含めない（`data/` は `.gitignore` 対象）
- CSVを自動ダウンロードするコードを書かない
- フロントエンドのJavaScriptに検索ロジックを書かない
- ユーザー入力の正規表現をそのまま検索エンジンに渡さない（ReDOS対策）
- スコープ外の機能を「ついでに」実装しない

---

## データソース

### ken_all.csv（一般住所）
- 文字コード：UTF-8
- 列（0-indexed）：2=郵便番号, 6=都道府県, 7=市区町村, 8=町域
- 検索用フルアドレス = 列6 + 列7 + 列8

CSVは `backend/data/` に手動配置する。起動時にCSVが存在しない場合はエラーで終了する（サイレントに無効化しない）。

---

## テスト

```bash
make test        # ユニット + インテグレーション
make test-e2e    # E2E（docker compose up が前提）
make test-all    # 全テスト
```

---

## 郵便番号フォーマット

ハイフンあり形式（`NNN-NNNN`）で統一する。
CSVのハイフンなし7桁は読み込み時に変換する。

---

## Docker

```bash
docker compose up      # 全サービス起動
docker compose up backend   # バックエンドのみ
```

- Django : `http://localhost:8000`
- FastAPI : `http://localhost:8001`
- FastAPI SwaggerUI : `http://localhost:8001/docs`
