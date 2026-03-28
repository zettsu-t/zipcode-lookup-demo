#!/bin/sh
# バックエンドを起動し schemathesis でスキーマ検査を実行する。
# 終了時（正常・エラー・Ctrl+C を問わず）バックエンドを停止する。
set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
PYTHON="$REPO_ROOT/.venv/bin/python"
SCHEMATHESIS="$REPO_ROOT/.venv/bin/schemathesis"
PORT=8001

# DATA_DIR が絶対パスならそのまま、相対パスなら backend/ 基準で解決する
# （uvicorn は backend/ で起動するため DATA_DIR のデフォルトは backend/data/）
DATA_DIR="${DATA_DIR:-$REPO_ROOT/backend/data}"
case "$DATA_DIR" in
    /*) CSV="$DATA_DIR/utf_ken_all.csv" ;;
    *)  CSV="$REPO_ROOT/backend/$DATA_DIR/utf_ken_all.csv" ;;
esac

# CSV の存在確認
if [ ! -f "$CSV" ]; then
    echo "ERROR: $CSV が見つかりません。"
    echo "日本郵便のサイトからダウンロードして backend/data/ に配置してください。"
    echo "  https://www.post.japanpost.jp/zipcode/dl/utf-zip.html"
    exit 1
fi

# バックエンドが既に起動中か確認
STARTED_BACKEND=0
if curl -sf "http://localhost:$PORT/openapi.json" > /dev/null 2>&1; then
    echo "Backend already running on port $PORT, using it."
else
    echo "Starting backend on port $PORT..."
    cd "$REPO_ROOT/backend"
    "$PYTHON" -m uvicorn main:app --host 127.0.0.1 --port $PORT --log-level warning &
    BACKEND_PID=$!
    STARTED_BACKEND=1
    cd "$REPO_ROOT"

    # 終了時にバックエンドを必ず停止する
    trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT INT TERM

    # 起動待ち（最大 10 秒）
    for i in $(seq 1 10); do
        if curl -sf "http://localhost:$PORT/openapi.json" > /dev/null 2>&1; then
            echo "Backend ready."
            break
        fi
        if [ "$i" = "10" ]; then
            echo "ERROR: Backend did not start within 10 seconds."
            exit 1
        fi
        sleep 1
    done
fi

# schemathesis 実行
cd "$REPO_ROOT"
"$SCHEMATHESIS" run docs/openapi_spec.yaml \
    --url "http://localhost:$PORT" \
    --checks all
