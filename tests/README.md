# Tests

## test_bridge

### Dependencies

* cbor3.mpy
* bridge.mpy

### Run test
```bash
>>> import test_bridge
>>> test_bridge.run_all_tests()
==================================================
Running Bridge Tests
==================================================
Testing CRC16...
  CRC16: PASS
Testing SLIP encoding...
  SLIP encoding: PASS
Testing SLIP stream...
  SLIP stream: PASS
Testing packet pack/unpack...
  Packet pack/unpack: PASS
Testing packet corruption detection...
  Corruption detection: PASS
Testing empty payload...
  Empty payload: PASS
Testing large payload...
  Large payload: PASS
Testing sequence wraparound...
  Sequence wraparound: PASS
==================================================
Results: 8 passed, 0 failed
==================================================
True
>>>
```

## test_pico_client

### Dependencies

* cbor3.mpy
* bridge.mpy
* pico_client.mpy
* esp32_proxy.mpy

### Configuration

* pico_config.py
* esp32_config.py

### Run test on ESP32
```bash
>>> import esp32_proxy
Connecting WiFi...
  Still connecting... (10/40)
WiFi OK: 192.168.4.87
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=8, rx=9, rts=4, cts=5
UART v3 bridge ready
```

### Run test on Pico
```bash
>>> import test_pico_client
>>> test_pico_client.run_all_tests()
==================================================
Running Pico Client Tests
==================================================
NOTE: These tests require ESP32 to be running
==================================================

Testing ping...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Ping: PASS

Testing get_time...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Now: 820084036 Ping: PASS

Testing WiFi status...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  WiFi connected: True
  WiFi status: PASS

Testing DNS resolution...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Resolved 1 addresses
  DNS: PASS

Testing socket open/close...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Socket open/close: PASS

Testing HTTP request...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Connecting to example.com:80...
  Sending 56 bytes...
  Receiving response...
    Chunk 1: 512 bytes
    Chunk 2: 310 bytes
  Total received: 822 bytes
  HTTP request: PASS

Testing multiple sequential requests...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Request 1/3...
  Request 2/3...
  Request 3/3...
  Multiple requests: PASS

Testing timeout handling...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Timeout handling: PASS

Testing socket reuse...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Connection 1/3: OK
  Connection 2/3: OK
  Connection 3/3: OK
  Socket reuse: PASS

Testing large data transfer...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Transferred 822 bytes
  Large transfer: PASS

Testing UDP socket operations...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Binding UDP socket...
  Sending UDP datagram...
  UDP socket: PASS

Testing TCP server operations...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Binding server socket...
  Listening on port 9999...
  TCP server operations: PASS

Testing SSL operations...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Connecting to www.google.com:443...
  Wrapping socket with SSL...
  Sending HTTPS request...
  Receiving HTTPS response...
  SSL operations: PASS

==================================================
Results: 13 passed, 0 failed
==================================================
True
```

### Run test on Pico - Stress test. Stability and memory leak
```bash
>>> import test_pico_client
>>> import time
>>> for i in range(1000):
...     print(f'Test #{i+1} ==============================')
...     test_pico_client.run_all_tests()
...     time.sleep(3)
Test #1 ==============================
==================================================
Running Pico Client Tests
==================================================
NOTE: These tests require ESP32 to be running
==================================================

Testing ping...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Ping: PASS

Testing get_time...
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
  Now: 820526370 Ping: PASS
...
```

