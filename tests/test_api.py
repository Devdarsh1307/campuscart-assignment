import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from app import create_app  # noqa: E402


@pytest.fixture
def client():
    a = create_app("sqlite:///:memory:")
    a.init_db()
    return a.test_client()


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json["status"] == "ok"


def test_health_fails_when_flag_set(client, monkeypatch):
    monkeypatch.setenv("FAIL_HEALTH", "1")
    assert client.get("/health").status_code == 500


def test_products(client):
    assert len(client.get("/products").json) == 2


def test_order_roundtrip(client):
    assert client.post("/orders", json={"item": "Notebook", "qty": 2}).status_code == 201
    assert client.get("/orders").json == [{"id": 1, "item": "Notebook", "qty": 2}]


def test_order_validation(client):
    assert client.post("/orders", json={"item": "", "qty": 0}).status_code == 400
