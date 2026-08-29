from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "5.0.0"


def test_get_verticals():
    response = client.get("/api/v1/verticals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    vertical_ids = [v["vertical_id"] for v in data]
    assert "ecommerce_retail_th" in vertical_ids
    assert "ev_automotive_th" in vertical_ids
    assert "banking_fintech_th" in vertical_ids


def test_create_custom_vertical():
    payload = {
        "vertical_id": "test_luxury_watch_th",
        "name_th": "ตลาดนาฬิกาหรู",
        "name_en": "Luxury Watch Market",
        "focal_brand": "rolex",
        "categories": ["นาฬิกาดำน้ำ", "Dress Watch"],
        "brands": [
            {"id": "rolex", "name": "Rolex", "aliases": ["โรเล็กซ์"], "is_focal_brand": True},
            {"id": "omega", "name": "Omega", "aliases": ["โอเมก้า"], "is_focal_brand": False},
        ],
    }
    response = client.post("/api/v1/verticals", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] in ["CREATED", "UPDATED"]


def test_trigger_mock_scan():
    payload = {
        "vertical_id": "ecommerce_retail_th",
        "engine_type": "mock",
        "count": 5,
        "include_control_set": True,
    }
    response = client.post("/api/v1/scan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "QUEUED"

    task_id = data["task_id"]
    # Check progress endpoint
    prog_res = client.get(f"/api/v1/scan/{task_id}/progress")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["task_id"] == task_id
    assert prog_data["status"] in ["QUEUED", "RUNNING", "COMPLETED"]


def test_get_metrics():
    response = client.get("/api/v1/metrics/ecommerce_retail_th")
    assert response.status_code == 200
    data = response.json()
    assert "vertical_id" in data
    assert "metrics" in data


def test_export_data():
    response = client.get("/api/v1/export/ecommerce_retail_th?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
