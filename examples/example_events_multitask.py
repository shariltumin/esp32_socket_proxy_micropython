# example_events_multitask.py
from events import Work
from pico_client import BridgeClient
import time
import gc

work = Work()
client = BridgeClient()

counter = {"value": 0}

def periodic_ping():
    try:
        result = client.call("ping", {}, timeout_ms=2000)
        print(f"[{counter['value']}] Ping OK: {result['t_ms']} ms")
    except Exception as e:
        print(f"[{counter['value']}] Ping failed: {e}")
    gc.collect()

def increment_counter():
    counter["value"] += 1
    print(f"Counter: {counter['value']}")

def check_wifi():
    try:
        result = client.call("wifi_status", {}, timeout_ms=2000)
        if result["connected"]:
            print(f"WiFi OK: {result['ifconfig'][0]}")
        else:
            print("WiFi disconnected!")
    except Exception as e:
        print(f"WiFi check failed: {e}")
    gc.collect()

def trigger_event_demo():
    print("Triggering custom event...")
    work.trigger_event("custom_event", pkg=("Event", "Data"))

def event_handler(msg1, msg2):
    print(f"Event received: {msg1}, {msg2}")

def main():
    print("=" * 50)
    print("Events Multitasking Example")
    print("=" * 50)
    print("Running multiple tasks concurrently...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    work.repeat(periodic_ping, every=3000)
    work.repeat(increment_counter, every=1000)
    work.repeat(check_wifi, every=10000)
    work.at(trigger_event_demo, at=5000)
    work.on(event_handler, when="custom_event")
    
    try:
        work.start()
    except KeyboardInterrupt:
        print("\nStopping...")
        work.stop()
    
    print("Done!")

if __name__ == "__main__":
    main()
