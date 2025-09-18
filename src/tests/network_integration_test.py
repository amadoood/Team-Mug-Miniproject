import requests

PICO_IP = "10.255.106.135"

def test_health_endpoint():
    url = f"http://{PICO_IP}/health"
    resp = requests.get(url, timeout=2)

    assert resp["status_code"] == 200
    assert resp["status"] == "OK"

def test_stop_endpoint():
    url = f"http://{PICO_IP}/stop"
    resp = requests.post(url, timeout=2)

    assert resp["message"] == "All sounds stopped."
    assert resp["status"] == "OK"


test_health_endpoint()
test_stop_endpoint()

