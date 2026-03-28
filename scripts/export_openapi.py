#!/usr/bin/env python3
"""FastAPIのOpenAPIスキーマをYAML形式でstdoutに出力する。

使い方:
    python scripts/export_openapi.py > docs/openapi_spec.yaml
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from main import app  # noqa: E402

schema = app.openapi()
yaml.dump(schema, stream=sys.stdout, allow_unicode=True, sort_keys=False, default_flow_style=False)
