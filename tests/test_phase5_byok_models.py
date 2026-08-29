"""Phase 5: bring-your-own-key + live free-model discovery."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from src.api import app
from src.engines import model_registry
from src.engines.factory import EngineFactory
from src.engines.openrouter_engine import OpenRouterEngine
from src.runner import run_intelligence_pipeline

client = TestClient(app)

_FAKE_MODELS = [
    {"id": "free/small:free", "name": "Small", "context_length": 8000, "pricing": {"prompt": "0", "completion": "0"}},
    {"id": "free/big", "name": "Big", "context_length": 200000, "pricing": {"prompt": "0", "completion": "0"}},
    {"id": "paid/x", "name": "Paid", "context_length": 32000, "pricing": {"prompt": "0.5", "completion": "1"}},
]


def test_list_models_endpoint_shape(monkeypatch):
    monkeypatch.setattr(model_registry.OpenRouterModelRegistry, "fetch_available_models", lambda self: _FAKE_MODELS)
    body = client.get("/api/v1/models").json()
    assert body["provider"] == "openrouter"
    assert body["count"] == 2  # paid/x excluded
    ids = [m["id"] for m in body["models"]]
    assert ids == ["free/big", "free/small:free"]  # sorted by context length desc
    assert "changes frequently" in body["note"]


def test_list_models_rejects_other_providers():
    assert client.get("/api/v1/models?provider=openai").status_code == 400


def test_free_model_list_excludes_non_chat_and_prefers_chat_families(monkeypatch):
    fake = [
        {"id": "acme/lyria-audio:free", "context_length": 999999, "pricing": {"prompt": "0", "completion": "0"}},
        {"id": "acme/inkling-small:free", "context_length": 999999, "pricing": {"prompt": "0", "completion": "0"}},
        {"id": "meta/llama-3.3-70b:free", "context_length": 128000, "pricing": {"prompt": "0", "completion": "0"}},
        {"id": "obscure/model-x:free", "context_length": 200000, "pricing": {"prompt": "0", "completion": "0"}},
    ]
    monkeypatch.setattr(model_registry.OpenRouterModelRegistry, "fetch_available_models", lambda self: fake)
    ids = [m["id"] for m in model_registry.OpenRouterModelRegistry().get_free_tier_candidates()]
    assert "acme/lyria-audio:free" not in ids  # audio excluded
    assert "acme/inkling-small:free" not in ids  # agentic-only excluded
    assert ids[0] == "meta/llama-3.3-70b:free"  # chat family ranked above obscure/model-x


def test_resolve_working_free_model_probes_and_caches(monkeypatch):
    reg = model_registry.OpenRouterModelRegistry(api_key="k-probe-test")
    reg._resolved.clear()
    monkeypatch.setattr(
        model_registry.OpenRouterModelRegistry,
        "get_free_tier_candidates",
        lambda self: [
            {"id": "bad/one:free", "chat_family": True, "context_length": 1},
            {"id": "good/two:free", "chat_family": True, "context_length": 1},
        ],
    )
    probed: list[str] = []

    def fake_probe(self, mid):
        probed.append(mid)
        return mid == "good/two:free"

    monkeypatch.setattr(model_registry.OpenRouterModelRegistry, "_probe", fake_probe)
    assert reg.resolve_working_free_model() == "good/two:free"
    assert probed == ["bad/one:free", "good/two:free"]
    # cached: no more probes
    probed.clear()
    assert reg.resolve_working_free_model() == "good/two:free"
    assert probed == []


def test_factory_threads_model_and_key():
    eng = EngineFactory.create("openrouter", model_name="free/big", api_key="sk-user-123")
    assert isinstance(eng, OpenRouterEngine)
    assert eng.model_name == "free/big"
    assert eng.api_key == "sk-user-123"


def test_scan_records_byok_flag_but_not_the_key(monkeypatch):
    monkeypatch.delenv("AIBT_API_KEYS", raising=False)
    r = client.post(
        "/api/v1/scan",
        json={"vertical_id": "ecommerce_retail_th", "engine_type": "mock", "count": 4, "model_name": "some/model"},
        headers={"X-Provider-Key": "sk-super-secret-xyz"},
    )
    assert r.status_code == 200
    task_id = r.json()["task_id"]
    prog = client.get(f"/api/v1/scan/{task_id}/progress").json()

    assert prog["byok"] is True
    assert prog["model_name"] == "some/model"
    # the secret must not appear anywhere in the serialised task state
    assert "sk-super-secret-xyz" not in json.dumps(prog)


def test_runner_never_leaks_key_into_summary(tmp_path):
    result = run_intelligence_pipeline(
        vertical_id="ecommerce_retail_th",
        count=4,
        engine_type="mock",
        output_dir=str(tmp_path),
        engine_api_key="sk-should-not-appear",
        engine_model="mock/custom",
    )
    blob = json.dumps(result)
    assert "sk-should-not-appear" not in blob
    assert result["byok"] is True
    assert isinstance(result["engine_model"], str)

    summary_file = tmp_path / f"latest_run_summary_{result['vertical_id']}.json"
    assert "sk-should-not-appear" not in summary_file.read_text(encoding="utf-8")
