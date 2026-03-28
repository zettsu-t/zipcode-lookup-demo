import sys
import os

# backend/ ディレクトリを sys.path に追加し、main / routers / services を importable にする
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
