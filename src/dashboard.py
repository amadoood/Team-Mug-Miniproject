# dashboard.py
# To be run on a student's computer (not the Pico)

import requests
import time

# --- Configuration ---
# Students should populate this list with the IP address(es) of their Pico
PICO_IPS = [
    "192.168.1.101",
]


def get_device_status(ip):
    """Fetches /health and /sensor data from a single device."""
    status = {"ip": ip, "device_id": "N/A", "status": "Error", "norm": 0.0}
    try:
        # Get health status
        health_res = requests.get(f"http://{ip}/health", timeout=1)
        health_res.raise_for_status()
        health_data = health_res.json()
        status.update(health_data)
        status["status"] = health_data.get("status", "Unknown")

    except requests.exceptions.RequestException as e:
        status["status"] = f"Offline ({type(e).__name__})"

    return status


def render_dashboard(statuses):
    """Renders the collected statuses to the console."""

    print("--- Pico Orchestra Dashboard --- (Press Ctrl+C to exit)")
    print("-" * 60)
    print(f"{'IP Address':<16} {'Device ID':<25} {'Status':<10} {'Light Level':<20}")
    print("-" * 60)

    for status in statuses:
        print(f"{status['ip']:<16} {status['device_id']:<25} {status['status'].capitalize():<10} ")

    print("-" * 60)


try:
    while True:
        all_statuses = [get_device_status(ip) for ip in PICO_IPS]
        render_dashboard(all_statuses)
        time.sleep(1)  # Refresh every second

except KeyboardInterrupt:
    print("\nDashboard stopped.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
