import os
import time
import requests

BASE = os.getenv('BASE_URL', 'http://localhost:8000')


def test_health():
    r = requests.get(f"{BASE}/healthz")
    assert r.status_code == 200


def test_create_order_and_fill():
    payload = {"symbol": "FOO", "side": "BUY", "qty": 1, "price": 100}
    r = requests.post(f"{BASE}/orders", json=payload)
    assert r.status_code == 200
    data = r.json()
    order_id = data["id"]

    # give worker a moment
    time.sleep(2)

    r = requests.get(f"{BASE}/orders/{order_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "FILLED"
