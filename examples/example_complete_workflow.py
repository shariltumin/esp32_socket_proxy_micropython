# example_complete_workflow.py
from pico_client import BridgeClient, ProxySocket, getaddrinfo
from events import Work
from ringbuffer import Ring
import gc
import time

work = Work()
client = BridgeClient()
message_queue = Ring(2048)

def check_connectivity():
    try:
        result = client.call("ping", {}, timeout_ms=2000)
        print(f"[Connectivity] Ping: {result['t_ms']} ms")
        
        wifi = client.call("wifi_status", {}, timeout_ms=2000)
        if wifi["connected"]:
            print(f"[Connectivity] WiFi: {wifi['ifconfig'][0]}")
        else:
            print("[Connectivity] WiFi: Disconnected")
    except Exception as e:
        print(f"[Connectivity] Error: {e}")
    gc.collect()

def fetch_data():
    try:
        print("[Fetch] Starting HTTP request...")
        sock = ProxySocket(client)
        
        sock.connect(("example.com", 80), timeout_s=10)
        request = b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
        sock.send(request)
        
        response = sock.recv(512, timeout_s=5)
        sock.close()
        
        if response:
            msg_id = int(time.time()) % 65535 + 1
            message_queue.put(msg_id, response[:100])
            print(f"[Fetch] Data queued: ID={msg_id}, Size={len(response)} bytes")
        else:
            print("[Fetch] No data received")
            
    except Exception as e:
        print(f"[Fetch] Error: {e}")
    gc.collect()

def process_queue():
    if message_queue.is_empty():
        return
    
    try:
        msg_id, data = message_queue.get()
        print(f"[Process] Processing message ID={msg_id}")
        print(f"[Process] Data preview: {data[:50]}...")
        print(f"[Process] Queue remaining: {len(message_queue.list())}")
    except Exception as e:
        print(f"[Process] Error: {e}")
    gc.collect()

def status_report():
    print("\n" + "=" * 50)
    print("STATUS REPORT")
    print("=" * 50)
    print(f"Queue size: {len(message_queue)} bytes")
    print(f"Messages pending: {len(message_queue.list())}")
    print(f"Message IDs: {message_queue.list()}")
    print("=" * 50 + "\n")
    gc.collect()

def main():
    print("=" * 50)
    print("Complete Workflow Example")
    print("=" * 50)
    print("This demo shows:")
    print("  - Event-driven multitasking")
    print("  - Network connectivity checks")
    print("  - HTTP data fetching")
    print("  - Message queue processing")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    work.repeat(check_connectivity, every=5000)
    work.repeat(fetch_data, every=15000)
    work.repeat(process_queue, every=2000)
    work.repeat(status_report, every=20000)
    
    work.at(fetch_data, at=2000)
    
    try:
        work.start()
    except KeyboardInterrupt:
        print("\n\nStopping...")
        work.stop()
    
    print("\nFinal queue status:")
    print(f"  Messages remaining: {len(message_queue.list())}")
    print(f"  Queue size: {len(message_queue)} bytes")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
