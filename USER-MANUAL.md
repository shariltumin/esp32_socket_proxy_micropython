# MicroPython UART Socket Proxy - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [API Reference](#api-reference)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Introduction

The MicroPython UART Socket Proxy enables network connectivity for devices without built-in networking capabilities. By connecting a Raspberry Pi Pico to an ESP32 via UART, the Pico can perform network operations as if it had native WiFi support.

### Key Benefits

- **Transparent API**: Use familiar socket programming patterns
- **Reliable Communication**: SLIP framing and CRC16 ensure data integrity
- **Memory Efficient**: Optimized for resource-constrained devices
- **Extensible**: Support for events and message queuing

## Installation

### Step 1: Prepare Your Hardware

1. **Raspberry Pi Pico**
   - Install MicroPython firmware (v1.19 or later recommended)
   - Connect via USB for file transfer

2. **ESP32-C3 (or compatible)**
   - Install MicroPython firmware (v1.19 or later recommended)
   - Connect via USB for file transfer

3. **Wire Connections**
   ```
   Pico GP0 (TX)  → ESP32 GP8 (RX)
   Pico GP1 (RX)  → ESP32 GP9 (TX)
   Pico GP2 (CTS) → ESP32 GP4 (RTS)
   Pico GP3 (RTS) → ESP32 GP5 (CTS)
   Pico GND       → ESP32 GND
   ```

### Step 2: Upload Files

#### To ESP32:
```bash
# Using ampy, rshell, or Thonny
ampy -p /dev/ttyUSB0 put bridge.py
ampy -p /dev/ttyUSB0 put cbor3.py
ampy -p /dev/ttyUSB0 put esp32_config.py
ampy -p /dev/ttyUSB0 put esp32_proxy.py
```

#### To Pico:
```bash
ampy -p /dev/ttyACM0 put bridge.py
ampy -p /dev/ttyACM0 put cbor3.py
ampy -p /dev/ttyACM0 put pico_config.py
ampy -p /dev/ttyACM0 put pico_client.py
ampy -p /dev/ttyACM0 put events.py      # Optional
ampy -p /dev/ttyACM0 put ringbuffer.py  # Optional
```

#### mpremote:

Or, use `mpremote` to run the tests and examples, before uploading `mpy` files 

## Configuration

### ESP32 Configuration

Edit `esp32_config.py`:

```python
# WiFi Credentials
SSID, PASSWORD = "YourSSID", "YourPassword"

# UART Settings
UART_ID = 0
BAUD = 1_400_000  # Adjust based on your setup

# Pin Configuration
TX = 8
RX = 9
RTS = 4
CTS = 5
```

### Pico Configuration

Edit `pico_config.py`:

```python
# UART Settings
UART_ID = 0
BAUD = 1_400_000  # Must match ESP32

# Pin Configuration
TX = 0
RX = 1
CTS = 2
RTS = 3
```

### Baud Rate Selection

| Baud Rate | Reliability | Speed | Use Case |
|:----------|:------------|:------|:---------|
| 115200    | Excellent   | Slow  | Initial testing |
| 460800    | Very Good   | Medium| Stable operation |
| 921600    | Good        | Fast  | With flow control |
| 1400000   | Fair        | Very Fast | Optimal hardware |

**Recommendation**: Start with 115200, then increase once stable.

## Basic Usage

### Starting the ESP32 Proxy

Create `main.py` on ESP32:

```python
# main.py
import esp32_proxy
```

The ESP32 will:
1. Connect to WiFi
2. Initialize UART
3. Start listening for requests

### Simple HTTP Request (Pico)

```python
from pico_client import BridgeClient, ProxySocket
import gc

def http_get(host, path="/"):
    client = BridgeClient()
    sock = ProxySocket(client)
    
    try:
        # Connect
        print(f"Connecting to {host}...")
        sock.connect((host, 80), timeout_s=10)
        
        # Send request
        request = f"GET {path} HTTP/1.1\\r\\nHost: {host}\\r\\nConnection: close\\r\\n\\r\\n"
        sock.send(request.encode())
        
        # Receive response
        response = bytearray()
        while True:
            chunk = sock.recv(512, timeout_s=5)
            if not chunk:
                break
            response.extend(chunk)
        
        return response.decode('utf-8', errors='ignore')
    
    finally:
        sock.close()
        gc.collect()

# Usage
result = http_get("example.com")
print(result[:500])
```

### DNS Lookup

```python
from pico_client import BridgeClient, getaddrinfo

client = BridgeClient()
addresses = getaddrinfo(client, "google.com", 80)
print("Resolved addresses:", addresses)
```

## Advanced Features

### Event-Driven Programming

The `events.py` library enables cooperative multitasking:

#### Example: Periodic Network Check

```python
from events import Work
from pico_client import BridgeClient

work = Work()
client = BridgeClient()

def check_connection():
    try:
        result = client.call("ping", {}, timeout_ms=2000)
        print("Ping OK:", result)
    except Exception as e:
        print("Ping failed:", e)

# Run every 5 seconds
work.repeat(check_connection, every=5000)
work.start()
```

#### Example: Event-Triggered Actions

```python
from events import Work

work = Work()

def on_data_received(data):
    print(f"Processing: {data}")

def trigger_data():
    work.trigger_event("data_ready", pkg=("Hello", "World"))

# Register event handler
work.on(on_data_received, when="data_ready")

# Trigger event
work.do(trigger_data)
work.start()
```

### Ring Buffer for Message Queuing

```python
from ringbuffer import Ring

# Create 4KB buffer
buffer = Ring(4096)

# Producer
def add_messages():
    buffer.put(1, b"First message")
    buffer.put(2, b"Second message")
    buffer.put(3, b"Third message")

# Consumer
def process_messages():
    while True:
        msg_id, msg = buffer.get()
        if msg_id == 0:
            break
        print(f"Message {msg_id}: {msg}")

add_messages()
process_messages()
```

### Combining Events and Ring Buffer

```python
from events import Work
from ringbuffer import Ring
from pico_client import BridgeClient, ProxySocket

work = Work()
buffer = Ring(2048)
client = BridgeClient()

def network_receiver():
    sock = ProxySocket(client)
    sock.connect(("example.com", 80))
    sock.send(b"GET / HTTP/1.1\\r\\nHost: example.com\\r\\n\\r\\n")
    
    msg_id = 1
    while True:
        data = sock.recv(512, timeout_s=5)
        if not data:
            break
        buffer.put(msg_id, data)
        msg_id += 1
        work.trigger_event("data_available")
    
    sock.close()

def data_processor():
    msg_id, msg = buffer.get()
    if msg_id > 0:
        print(f"Processing message {msg_id}: {len(msg)} bytes")

work.do(network_receiver)
work.on(data_processor, when="data_available", repeat=True)
work.start()
```

## API Reference

### BridgeClient

#### Constructor
```python
client = BridgeClient()
```

#### Methods

**`call(op, args=None, timeout_ms=8000, resend_ms=200)`**
- Send a request to ESP32 and wait for response
- `op`: Operation name (string)
- `args`: Dictionary of arguments
- `timeout_ms`: Maximum wait time
- `resend_ms`: Interval for request retransmission
- Returns: Result dictionary
- Raises: `OSError` on timeout or error

### ProxySocket

#### Constructor
```python
sock = ProxySocket(client, family=AF_INET, typ=SOCK_STREAM, proto=0)
```

#### Methods

**`connect(addr, timeout_s=5)`**
- Connect to remote host
- `addr`: Tuple of (host, port)
- `timeout_s`: Connection timeout
- Raises: `OSError` on failure

**`send(data)`**
- Send data over socket
- `data`: Bytes or bytearray
- Returns: Number of bytes sent
- Raises: `OSError` on failure

**`recv(n, timeout_s=5)`**
- Receive up to n bytes
- `n`: Maximum bytes to receive
- `timeout_s`: Receive timeout
- Returns: Bytes received (empty if EOF)
- Raises: `OSError` on failure

**`close()`**
- Close the socket
- Safe to call multiple times

**`settimeout(timeout_s)`**
- Set socket timeout
- `timeout_s`: Timeout in seconds (None for blocking)

**`bind(addr, timeout_s=5)`**
- Bind socket to address (for server sockets)
- `addr`: Tuple of (host, port)
- `timeout_s`: Operation timeout
- Raises: `OSError` on failure

**`listen(backlog=5, timeout_s=5)`**
- Listen for incoming connections (for server sockets)
- `backlog`: Maximum number of queued connections
- `timeout_s`: Operation timeout
- Raises: `OSError` on failure

**`accept(timeout_s=5)`**
- Accept incoming connection (for server sockets)
- `timeout_s`: Accept timeout
- Returns: Tuple of (new_socket, address)
- Raises: `OSError` on failure

**`sendto(data, addr)`**
- Send UDP datagram to address
- `data`: Bytes or bytearray
- `addr`: Tuple of (host, port)
- Returns: Number of bytes sent
- Raises: `OSError` on failure

**`recvfrom(n, timeout_s=5)`**
- Receive UDP datagram
- `n`: Maximum bytes to receive
- `timeout_s`: Receive timeout
- Returns: Tuple of (data, address)
- Raises: `OSError` on failure

**`wrap_ssl(server_hostname=None, timeout_s=5)`**
- Wrap socket with SSL/TLS
- `server_hostname`: Server hostname for SNI
- `timeout_s`: Operation timeout
- Raises: `OSError` on failure

### Work (Events)

#### Constructor
```python
work = Work(max_tasks=256)
```

#### Methods

**`do(job, params=())`**
- Execute job immediately
- Returns: Task ID

**`at(job, params=(), at=0)`**
- Execute job after delay
- `at`: Delay in milliseconds
- Returns: Task ID

**`repeat(job, params=(), at=0, every=0)`**
- Execute job repeatedly
- `every`: Interval in milliseconds
- Returns: Task ID

**`on(job, params=(), when=None, at=0, repeat=False)`**
- Execute job when event triggers
- `when`: Event flag name
- Returns: Task ID

**`trigger_event(flag, pkg=())`**
- Trigger an event
- `flag`: Event name
- `pkg`: Data to pass to handlers
- Returns: Number of tasks triggered

**`cancel(task_id)`**
- Cancel a task
- Returns: True if cancelled

**`start()`**
- Start the event loop (blocking)

**`stop()`**
- Stop the event loop

### Ring (Buffer)

#### Constructor
```python
buffer = Ring(size)
```
- `size`: Buffer size in bytes (minimum 8)

#### Methods

**`put(msg_id, msg_bytes)`**
- Add message to buffer
- `msg_id`: Unique ID (1-65535)
- `msg_bytes`: Message data
- Raises: `MemoryError` if full

**`get()`**
- Get next message
- Returns: Tuple (msg_id, msg_bytes)
- Returns: (0, b'') if empty

**`peek()`**
- Look at next message without removing
- Returns: Tuple (msg_id, msg_bytes) or None

**`pull(msg_id)`**
- Get specific message by ID
- Returns: Tuple (msg_id, msg_bytes)
- Returns: (0, b'') if not found

**`list()`**
- List all message IDs
- Returns: List of integers

**`clear()`**
- Clear all messages

**`is_empty()`**
- Check if buffer is empty
- Returns: Boolean

**`is_full()`**
- Check if buffer is full
- Returns: Boolean

## Examples

### Example 1: Simple HTTP Client

```python
from pico_client import BridgeClient, ProxySocket

def fetch_url(url):
    # Parse URL (simple version)
    if url.startswith("http://"):
        url = url[7:]
    parts = url.split('/', 1)
    host = parts[0]
    path = '/' + parts[1] if len(parts) > 1 else '/'
    
    client = BridgeClient()
    sock = ProxySocket(client)
    
    try:
        sock.connect((host, 80), timeout_s=10)
        request = f"GET {path} HTTP/1.1\\r\\nHost: {host}\\r\\nConnection: close\\r\\n\\r\\n"
        sock.send(request.encode())
        
        response = bytearray()
        while True:
            chunk = sock.recv(1024, timeout_s=5)
            if not chunk:
                break
            response.extend(chunk)
        
        return response
    finally:
        sock.close()

# Usage
data = fetch_url("http://example.com/")
print(data.decode('utf-8', errors='ignore'))
```

### Example 2: JSON API Client

```python
from pico_client import BridgeClient, ProxySocket
import json

def api_request(host, path, method="GET", data=None):
    client = BridgeClient()
    sock = ProxySocket(client)
    
    try:
        sock.connect((host, 80), timeout_s=10)
        
        # Build request
        request = f"{method} {path} HTTP/1.1\\r\\n"
        request += f"Host: {host}\\r\\n"
        request += "Content-Type: application/json\\r\\n"
        
        if data:
            body = json.dumps(data)
            request += f"Content-Length: {len(body)}\\r\\n"
            request += "\\r\\n"
            request += body
        else:
            request += "\\r\\n"
        
        sock.send(request.encode())
        
        # Receive response
        response = bytearray()
        while True:
            chunk = sock.recv(512, timeout_s=5)
            if not chunk:
                break
            response.extend(chunk)
        
        # Parse response
        response_str = response.decode('utf-8')
        header_end = response_str.find('\\r\\n\\r\\n')
        if header_end > 0:
            body = response_str[header_end+4:]
            return json.loads(body)
        
        return None
    finally:
        sock.close()

# Usage
result = api_request("api.example.com", "/data", "GET")
print(result)
```

### Example 3: Concurrent Operations with Events

```python
from events import Work
from pico_client import BridgeClient, ProxySocket
import gc

work = Work()
client = BridgeClient()

def fetch_data(url_id, host, path):
    sock = ProxySocket(client)
    try:
        sock.connect((host, 80), timeout_s=10)
        request = f"GET {path} HTTP/1.1\\r\\nHost: {host}\\r\\nConnection: close\\r\\n\\r\\n"
        sock.send(request.encode())
        
        data = bytearray()
        while True:
            chunk = sock.recv(512, timeout_s=5)
            if not chunk:
                break
            data.extend(chunk)
        
        print(f"URL {url_id}: Received {len(data)} bytes")
        work.trigger_event("fetch_complete", pkg=(url_id, data))
    except Exception as e:
        print(f"URL {url_id}: Error - {e}")
    finally:
        sock.close()
        gc.collect()

def process_result(url_id, data):
    print(f"Processing URL {url_id}: {len(data)} bytes")

# Schedule multiple fetches
work.do(fetch_data, params=(1, "example.com", "/"))
work.at(fetch_data, params=(2, "httpbin.org", "/get"), at=1000)
work.at(fetch_data, params=(3, "api.github.com", "/"), at=2000)

# Process results as they arrive
work.on(process_result, when="fetch_complete", repeat=True)

work.start()
```

### Example 4: Data Logger with Ring Buffer

```python
from ringbuffer import Ring
from pico_client import BridgeClient, ProxySocket
import time

buffer = Ring(8192)
client = BridgeClient()

def collect_data():
    sock = ProxySocket(client)
    sock.connect(("sensor-api.example.com", 80), timeout_s=10)

    msg_id = 1
    for i in range(10):
        request = f"GET /sensor/data HTTP/1.1\\r\\nHost: sensor-api.example.com\\r\\n\\r\\n"
        sock.send(request.encode())

        data = sock.recv(512, timeout_s=5)
        if data:
            buffer.put(msg_id, data)
            print(f"Collected sample {msg_id}")
            msg_id += 1

        time.sleep(1)

    sock.close()

def process_data():
    print("Processing collected data...")
    while True:
        msg_id, msg = buffer.get()
        if msg_id == 0:
            break
        print(f"Sample {msg_id}: {len(msg)} bytes")

# Collect data
collect_data()

# Process data
process_data()
```

### Example 5: TCP Server

```python
from pico_client import BridgeClient, ProxySocket

def run_tcp_server():
    client = BridgeClient()
    server_sock = ProxySocket(client, typ=ProxySocket.SOCK_STREAM)

    try:
        server_sock.bind(("0.0.0.0", 8080), timeout_s=5)
        server_sock.listen(5, timeout_s=5)
        print("Server listening on port 8080")

        while True:
            try:
                conn_sock, addr = server_sock.accept(timeout_s=30)
                print(f"Connection from {addr}")

                data = conn_sock.recv(1024, timeout_s=5)
                print(f"Received: {data}")

                response = b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello, World!"
                conn_sock.send(response)
                conn_sock.close()

            except OSError as e:
                print(f"Accept error: {e}")

    finally:
        server_sock.close()

run_tcp_server()
```

### Example 6: UDP Client/Server

```python
from pico_client import BridgeClient, ProxySocket

def udp_echo_server():
    client = BridgeClient()
    sock = ProxySocket(client, typ=ProxySocket.SOCK_DGRAM)

    try:
        sock.bind(("0.0.0.0", 5000), timeout_s=5)
        print("UDP server listening on port 5000")

        while True:
            data, addr = sock.recvfrom(1024, timeout_s=30)
            print(f"Received from {addr}: {data}")
            sock.sendto(b"Echo: " + data, addr)

    finally:
        sock.close()

def udp_client():
    client = BridgeClient()
    sock = ProxySocket(client, typ=ProxySocket.SOCK_DGRAM)

    try:
        message = b"Hello UDP Server"
        sock.sendto(message, ("192.168.1.100", 5000))
        print(f"Sent: {message}")

        data, addr = sock.recvfrom(1024, timeout_s=5)
        print(f"Received from {addr}: {data}")

    finally:
        sock.close()

udp_echo_server()
```

### Example 7: HTTPS Client with SSL

```python
from pico_client import BridgeClient, ProxySocket

def https_request(host, path="/"):
    client = BridgeClient()
    sock = ProxySocket(client)

    try:
        sock.connect((host, 443), timeout_s=10)
        sock.wrap_ssl(server_hostname=host, timeout_s=10)
        print(f"SSL connection established to {host}")

        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.send(request.encode())

        response = bytearray()
        while True:
            chunk = sock.recv(1024, timeout_s=5)
            if not chunk:
                break
            response.extend(chunk)

        return response.decode('utf-8', errors='ignore')

    finally:
        sock.close()

result = https_request("www.google.com", "/")
print(result[:500])
```

## Troubleshooting

### Problem: Connection Timeout

**Symptoms**: `OSError: bridge_timeout`

**Solutions**:
1. Check UART wiring
2. Verify baud rates match
3. Increase timeout values
4. Check ESP32 WiFi connection
5. Enable hardware flow control

### Problem: Data Corruption

**Symptoms**: CRC errors, invalid packets

**Solutions**:
1. Reduce baud rate
2. Enable hardware flow control
3. Check for loose connections
4. Add shielding to UART wires
5. Reduce UART cable length

### Problem: Memory Errors

**Symptoms**: `MemoryError`, system crashes

**Solutions**:
1. Call `gc.collect()` more frequently
2. Reduce buffer sizes
3. Limit concurrent operations
4. Use smaller receive chunks
5. Close sockets promptly

### Problem: WiFi Connection Fails

**Symptoms**: ESP32 can't connect to WiFi

**Solutions**:
1. Verify SSID and password
2. Check WiFi signal strength
3. Restart ESP32
4. Check router settings
5. Try different WiFi channel

### Problem: Slow Performance

**Symptoms**: Operations take too long

**Solutions**:
1. Increase baud rate
2. Enable hardware flow control
3. Reduce timeout values
4. Optimize packet sizes
5. Use CBOR instead of JSON

## Best Practices

### Memory Management

```python
import gc

# Collect garbage regularly
def network_operation():
    try:
        # ... do work ...
        pass
    finally:
        gc.collect()

# Limit buffer sizes
MAX_RESPONSE_SIZE = 2048
response = bytearray()
while len(response) < MAX_RESPONSE_SIZE:
    chunk = sock.recv(512)
    if not chunk:
        break
    response.extend(chunk)
```

### Error Handling

```python
def robust_request(host, port, data, max_retries=3):
    client = BridgeClient()
    
    for attempt in range(max_retries):
        sock = None
        try:
            sock = ProxySocket(client)
            sock.connect((host, port), timeout_s=10)
            sock.send(data)
            result = sock.recv(1024, timeout_s=5)
            return result
        except OSError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
        finally:
            if sock:
                sock.close()
```

### Resource Cleanup

```python
class NetworkManager:
    def __init__(self):
        self.client = BridgeClient()
        self.sockets = []
    
    def create_socket(self):
        sock = ProxySocket(self.client)
        self.sockets.append(sock)
        return sock
    
    def cleanup(self):
        for sock in self.sockets:
            try:
                sock.close()
            except:
                pass
        self.sockets.clear()
        gc.collect()

# Usage
manager = NetworkManager()
try:
    sock = manager.create_socket()
    # ... use socket ...
finally:
    manager.cleanup()
```

### Timeout Configuration

```python
# Short timeout for quick operations
client.call("ping", {}, timeout_ms=1000)

# Medium timeout for DNS
getaddrinfo(client, "example.com", 80)  # 6000ms default

# Long timeout for large transfers
sock.recv(4096, timeout_s=30)
```

### Debugging

```python
# Enable debug output on ESP32
# In esp32_proxy.py:
DEBUG = 1  # Set to 1 for verbose logging

# Add logging on Pico
def debug_call(client, op, args):
    print(f"Calling {op} with {args}")
    try:
        result = client.call(op, args)
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        raise
```

## Performance Tips

1. **Use appropriate buffer sizes**: 512-1024 bytes for most operations
2. **Enable hardware flow control**: Prevents data loss at high speeds
3. **Batch operations**: Combine multiple small requests when possible
4. **Reuse connections**: Keep sockets open for multiple operations
5. **Monitor memory**: Call `gc.collect()` between operations
6. **Optimize timeouts**: Use shorter timeouts for quick operations
7. **Use events for concurrency**: Don't block on long operations

## Conclusion

This user manual covers the essential aspects of using the MicroPython UART Socket Proxy. For more information, examples, and updates, visit the project repository.

