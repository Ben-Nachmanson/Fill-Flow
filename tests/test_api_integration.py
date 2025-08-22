import os
import time
import requests

BASE = os.getenv('BASE_URL', 'http://localhost:8000')


def wait_for_health(timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(f"{BASE}/healthz", timeout=1)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("service not healthy")


def wait_for_order_filled(order_id, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        r = requests.get(f"{BASE}/orders/{order_id}", timeout=2)
        if r.status_code == 200:
            data = r.json()
            status = (data.get("status") or "").upper()
            # support both status field or fills presence
            if status == "FILLED" or data.get("fills"):
                return data
        time.sleep(0.5)
    raise AssertionError(f"order {order_id} not filled within {timeout}s")


def test_health():
    assert wait_for_health()


def test_create_order_and_fill():
    wait_for_health()
    payload = {"symbol": "FOO", "side": "BUY", "qty": 1, "price": 100}
    r = requests.post(f"{BASE}/orders", json=payload)
    assert r.status_code == 200
    data = r.json()
    order_id = data["id"]

    # poll until filled (faster and less flaky than fixed sleep)
    filled = wait_for_order_filled(order_id, timeout=30)
    assert filled
