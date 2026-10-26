"""The backend implements exactly the operations in openapi.yaml (contract-first)."""

from pathlib import Path

import yaml

from learnloop.main import create_app
from tests.conftest import make_config

SPEC = Path(__file__).resolve().parents[3] / "openapi.yaml"
METHODS = {"get", "post", "put", "patch", "delete"}


def _ops(paths: dict) -> set[tuple[str, str]]:
    return {(p, m) for p, item in paths.items() for m in item if m in METHODS}


def test_routes_match_contract():
    contract = yaml.safe_load(SPEC.read_text())
    app = create_app(make_config(), telemetry_mode="none")
    implemented = _ops(app.openapi()["paths"])
    assert implemented == _ops(contract["paths"])


def test_success_status_codes_match_contract():
    contract = yaml.safe_load(SPEC.read_text())
    app_paths = create_app(make_config(), telemetry_mode="none").openapi()["paths"]
    for path, item in contract["paths"].items():
        for method, op in item.items():
            if method not in METHODS:
                continue
            want = {c for c in op["responses"] if c.startswith("2")}
            got = {c for c in app_paths[path][method]["responses"] if c.startswith("2")}
            assert want == got, (method, path, want, got)
