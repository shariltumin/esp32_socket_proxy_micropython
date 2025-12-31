# test_pico_client.py
import gc
import time
from pico_client import BridgeClient, ProxySocket

def test_ping():
    print("Testing ping...")
    try:
        client = BridgeClient()
        result = client.call("ping", {}, timeout_ms=5000)
        assert result is not None
        assert "pong" in result
        assert result["pong"] == True
        print("  Ping: PASS")
        return True
    except Exception as e:
        print(f"  Ping: FAIL - {e}")
        return False

def test_get_time():
    print("Testing get_time...")
    try:
        client = BridgeClient()
        result = client.call("get_time", {}, timeout_ms=5000)
        assert result is not None
        assert "time" in result
        assert result["time"] > 10  #
        print(f"  Now: {result["time"]} Ping: PASS")
        return True
    except Exception as e:
        print(f"  get_time: FAIL - {e}")
        return False

def test_wifi_status():
    print("Testing WiFi status...")
    try:
        client = BridgeClient()
        result = client.call("wifi_status", {}, timeout_ms=3000)
        assert result is not None
        assert "connected" in result
        print(f"  WiFi connected: {result['connected']}")
        print("  WiFi status: PASS")
        return True
    except Exception as e:
        print(f"  WiFi status: FAIL - {e}")
        return False

def test_dns():
    print("Testing DNS resolution...")
    try:
        client = BridgeClient()
        result = client.call("dns", {"host": "example.com", "port": 80}, timeout_ms=10000)
        assert result is not None
        assert len(result) > 0
        print(f"  Resolved {len(result)} addresses")
        print("  DNS: PASS")
        return True
    except Exception as e:
        print(f"  DNS: FAIL - {e}")
        return False

def test_socket_open_close():
    print("Testing socket open/close...")
    try:
        client = BridgeClient()
        sock = ProxySocket(client)
        assert sock.sid > 0
        sock.close()
        print("  Socket open/close: PASS")
        return True
    except Exception as e:
        print(f"  Socket open/close: FAIL - {e}")
        return False

def test_http_request():
    print("Testing HTTP request...")
    try:
        client = BridgeClient()
        sock = ProxySocket(client)
        
        print("  Connecting to example.com:80...")
        sock.connect(("example.com", 80), timeout_s=10)
        
        request = b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
        print(f"  Sending {len(request)} bytes...")
        sent = sock.send(request)
        assert sent == len(request)
        
        print("  Receiving response...")
        response = bytearray()
        chunks = 0
        while chunks < 10:
            chunk = sock.recv(512, timeout_s=5)
            if not chunk:
                break
            response.extend(chunk)
            chunks += 1
            print(f"    Chunk {chunks}: {len(chunk)} bytes")
        
        sock.close()
        
        assert len(response) > 0
        assert b"HTTP" in response
        print(f"  Total received: {len(response)} bytes")
        print("  HTTP request: PASS")
        return True
    except Exception as e:
        print(f"  HTTP request: FAIL - {e}")
        return False

def test_multiple_requests():
    print("Testing multiple sequential requests...")
    try:
        client = BridgeClient()
        
        for i in range(3):
            print(f"  Request {i+1}/3...")
            result = client.call("ping", {}, timeout_ms=3000)
            assert result["pong"] == True
            time.sleep_ms(100)
        
        print("  Multiple requests: PASS")
        return True
    except Exception as e:
        print(f"  Multiple requests: FAIL - {e}")
        return False

def test_timeout_handling():
    print("Testing timeout handling...")
    try:
        client = BridgeClient()
        
        try:
            result = client.call("invalid_op", {}, timeout_ms=1000)
            print("  Timeout handling: FAIL - Should have raised error")
            return False
        except OSError:
            print("  Timeout handling: PASS")
            return True
    except Exception as e:
        print(f"  Timeout handling: FAIL - {e}")
        return False

def test_socket_reuse():
    print("Testing socket reuse...")
    try:
        client = BridgeClient()
        
        for i in range(3):
            sock = ProxySocket(client)
            sock.connect(("example.com", 80), timeout_s=10)
            sock.send(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
            data = sock.recv(256, timeout_s=5)
            sock.close()
            assert len(data) > 0
            print(f"  Connection {i+1}/3: OK")
            gc.collect()
        
        print("  Socket reuse: PASS")
        return True
    except Exception as e:
        print(f"  Socket reuse: FAIL - {e}")
        return False

def test_large_transfer():
    print("Testing large data transfer...")
    try:
        client = BridgeClient()
        sock = ProxySocket(client)

        sock.connect(("example.com", 80), timeout_s=10)
        sock.send(b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")

        total = 0
        while total < 5000:
            chunk = sock.recv(1024, timeout_s=5)
            if not chunk:
                break
            total += len(chunk)

        sock.close()
        print(f"  Transferred {total} bytes")
        print("  Large transfer: PASS")
        return True
    except Exception as e:
        print(f"  Large transfer: FAIL - {e}")
        return False

def test_udp_socket():
    print("Testing UDP socket operations...")
    try:
        client = BridgeClient()
        sock = ProxySocket(client, typ=ProxySocket.SOCK_DGRAM)

        print("  Binding UDP socket...")
        sock.bind(("0.0.0.0", 0), timeout_s=5)

        print("  Sending UDP datagram...")
        test_data = b"UDP test message"
        sent = sock.sendto(test_data, ("8.8.8.8", 53))
        assert sent > 0

        sock.close()
        print("  UDP socket: PASS")
        return True
    except Exception as e:
        print(f"  UDP socket: FAIL - {e}")
        return False

def test_tcp_server_operations():
    print("Testing TCP server operations...")
    try:
        client = BridgeClient()
        server_sock = ProxySocket(client, typ=ProxySocket.SOCK_STREAM)

        print("  Binding server socket...")
        server_sock.bind(("0.0.0.0", 9999), timeout_s=5)

        print("  Listening on port 9999...")
        server_sock.listen(5, timeout_s=5)

        server_sock.close()
        print("  TCP server operations: PASS")
        return True
    except Exception as e:
        print(f"  TCP server operations: FAIL - {e}")
        return False

def test_ssl_operations():
    print("Testing SSL operations...")
    try:
        client = BridgeClient()
        sock = ProxySocket(client)

        print("  Connecting to www.google.com:443...")
        #sock.connect(("www.google.com", 443), timeout_s=10)
        sock.connect(("www.google.com", 443), ssl=True)

        print("  Wrapping socket with SSL...")
        #sock.wrap_ssl(server_hostname="www.google.com", timeout_s=10)
        sock.wrap_ssl(server_hostname="www.google.com")

        print("  Sending HTTPS request...")
        request = b"GET / HTTP/1.1\r\nHost: www.google.com\r\nConnection: close\r\n\r\n"
        sent = sock.send(request)
        assert sent == len(request)

        print("  Receiving HTTPS response...")
        # response = sock.recv(512, timeout_s=5)
        response = sock.recv(512, ssl=True)
        assert len(response) > 0
        assert b"HTTP" in response

        sock.close()
        print("  SSL operations: PASS")
        return True
    except Exception as e:
        print(f"  SSL operations: FAIL - {e}")
        return False

def run_all_tests():
    print("=" * 50)
    print("Running Pico Client Tests")
    print("=" * 50)
    print("NOTE: These tests require ESP32 to be running")
    print("=" * 50)
    
    tests = [
        ("Ping", test_ping),
        ("Get Current time", test_get_time),
        ("WiFi Status", test_wifi_status),
        ("DNS Resolution", test_dns),
        ("Socket Open/Close", test_socket_open_close),
        ("HTTP Request", test_http_request),
        ("Multiple Requests", test_multiple_requests),
        ("Timeout Handling", test_timeout_handling),
        ("Socket Reuse", test_socket_reuse),
        ("Large Transfer", test_large_transfer),
        ("UDP Socket", test_udp_socket),
        ("TCP Server Operations", test_tcp_server_operations),
        ("SSL Operations", test_ssl_operations),
    ]
    
    passed = 0
    failed = 0
    
    for name, test in tests:
        print()
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  {name}: ERROR - {e}")
            failed += 1
        gc.collect()
        time.sleep_ms(500)
    
    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        print("\nSome tests failed. Check ESP32 connection.")
