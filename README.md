# MicroPython UART Socket Proxy

## Overview

This project implements a robust UART-based socket proxy that enables Raspberry Pi Pico (or other non-network devices) to access network functionalities (WiFi, TCP/IP sockets, DNS) by leveraging an ESP32 microcontroller running MicroPython. The system provides a transparent socket API that makes network programming on resource-constrained devices intuitive and reliable.

## Features

*   **Robust UART Communication:** Serial communication using SLIP framing and CRC16 for data integrity
*   **CBOR Serialization:** Fast and reliable data transmission using CBOR instead of JSON
*   **Network Proxy:** ESP32 acts as a proxy, providing WiFi connectivity and handling socket operations
*   **DNS Resolution:** Perform DNS lookups via the ESP32 proxy
*   **Socket-like API:** `ProxySocket` class mimics the standard Python `socket` API
*   **TCP Client & Server:** Full support for TCP client connections and server operations (bind, listen, accept)
*   **UDP Client & Server:** Support for UDP datagram operations (sendto, recvfrom)
*   **SSL/TLS Support:** Secure socket connections using ssl.wrap_socket()
*   **Reliable Protocol:** Request re-sending and response caching for robustness over serial links
*   **Memory Efficient:** Designed for resource-constrained MicroPython environments with explicit garbage collection
*   **Event-Driven Multitasking:** Optional `events.py` library for cooperative multitasking
*   **Ring Buffer:** Optional `ringbuffer.py` for efficient message queuing

## Architecture

The system follows a client-server model:

1.  **Pico (Client):** Runs `pico_client.py` and uses the `ProxySocket` API for network operations
2.  **UART Bridge:** Translates operations into structured requests using SLIP encoding
3.  **ESP32 (Proxy Server):** Runs `esp32_proxy.py`, performs actual network operations
4.  **Response:** ESP32 sends results back over UART to the Pico

## Getting Started

### Prerequisites Hardware

*   Raspberry Pi Pico with MicroPython firmware
*   ESP32-C3 (or compatible) with MicroPython firmware
*   UART serial connection between Pico and ESP32
*   Hardware flow control (RTS/CTS) recommended for stable high-speed communication

### Prerequisites Software

#### CBOR

https://github.com/shariltumin/cbor-v3-micropython

#### Events and Ringbuffer (optional)

https://github.com/shariltumin/event-flow-scheduler-micropython

### Hardware Setup

Connect the UART pins between your Pico and ESP32:

| Pin Function | Pico Pin | ESP32-C3 Pin |
| :----------- | :------- | :----------- |
| TX           | GP0      | GP8          |
| RX           | GP1      | GP9          |
| CTS (Pico In)| GP2      | GP4 (ESP32 RTS) |
| RTS (Pico Out)| GP3     | GP5 (ESP32 CTS) |

*Note: Adjust pin numbers in `esp32_config.py` and `pico_config.py` if your hardware differs.*

### Software Setup

#### ESP32 Configuration

1. Edit `esp32_config.py` to set your WiFi credentials:
```python
SSID, PASSWORD = "your_ssid", "your_password"
```

2. Upload these files to your ESP32:
   - `bridge.mpy`
   - `cbor3.mpy`
   - `esp32_proxy.mpy`
   - `esp32_config.py`

3. Run `esp32_proxy` on boot (add to `main.py` or `boot.py`)

#### Pico Configuration

1. Upload these files to your Pico:
   - `bridge.mpy`
   - `cbor3.mpy`
   - `pico_client.mpy`
   - `pico_config.py`

2. Optionally upload for advanced features:
   - `events.mpy` (for event-driven multitasking)
   - `ringbuffer.mpy` (for message queuing)

## Usage

### Basic Example

```python
from pico_client import BridgeClient, ProxySocket
import gc

def main():
    print("Initializing BridgeClient...")
    c = BridgeClient()
    s = None
    try:
        print("Opening ProxySocket...")
        s = ProxySocket(c)

        print("Connecting to example.com:80...")
        s.connect(("example.com", 80), timeout_s=5)

        request_data = b"GET / HTTP/1.1\\r\\nHost: example.com\\r\\nConnection: close\\r\\n\\r\\n"
        print(f"Sending {len(request_data)} bytes...")
        s.send(request_data)

        received_data = bytearray()
        print("Receiving response...")
        while True:
            chunk = s.recv(512, timeout_s=5)
            if not chunk:
                break
            received_data.extend(chunk)
            print(f"Received {len(chunk)} bytes, total: {len(received_data)}")

        print(f"Total received: {len(received_data)} bytes")
        print("--- Response Snippet ---")
        print(received_data.decode('utf-8')[:500])

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if s:
            s.close()
        gc.collect()

main()
```

### Using Events for Multitasking

```python
from events import Work
from pico_client import BridgeClient, ProxySocket

work = Work()

def network_task():
    c = BridgeClient()
    s = ProxySocket(c)
    s.connect(("example.com", 80))
    s.send(b"GET / HTTP/1.1\\r\\nHost: example.com\\r\\n\\r\\n")
    data = s.recv(512)
    print(f"Received: {len(data)} bytes")
    s.close()

def periodic_task():
    print("Periodic task running...")

work.do(network_task)
work.repeat(periodic_task, every=1000)
work.start()
```

### Using Ring Buffer for Message Queuing

```python
from ringbuffer import Ring

buffer = Ring(1024)
buffer.put(1, b"Hello")
buffer.put(2, b"World")

msg_id, msg = buffer.get()
print(f"Message {msg_id}: {msg}")
```

## Notes of Scrip Files 

*   **`bridge.py`**: Core communication protocol (SLIP, CRC16, packet framing)
*   **`cbor3.py`**: CBOR serialization for MicroPython
*   **`esp32_config.py`**: ESP32 UART and WiFi configuration
*   **`esp32_proxy.py`**: ESP32 server implementation
*   **`pico_config.py`**: Pico UART configuration
*   **`pico_client.py`**: Pico client implementation with `ProxySocket` API
*   **`events.py`**: Event-driven cooperative multitasking library
*   **`ringbuffer.py`**: Efficient ring buffer for message queuing

## File Structure
```
.
├── bridge.py
├── esp32_config.py
├── esp32_proxy.py
├── examples
│   ├── bridge.mpy
│   ├── cbor3.mpy
│   ├── esp32_config.py
│   ├── esp32_proxy.mpy
│   ├── example_complete_workflow.py
│   ├── example_dns_lookup.py
│   ├── example_events_multitask.py
│   ├── example_http_get.py
│   ├── example_https_client.py
│   ├── example_ringbuffer.py
│   ├── example_tcp_echo.py
│   ├── example_tcp_server.py
│   ├── example_udp_client.py
│   ├── example_udp_server.py
│   ├── pico_client.mpy
│   ├── pico_config.py
│   ├── README.md
│   └── RUN_LOG.md
├── MPY
│   ├── bridge.mpy
│   ├── cbor3.mpy
│   ├── esp32_proxy.mpy
│   ├── events.mpy
│   ├── pico_client.mpy
│   └── ringbuffer.mpy
├── pico_client.py
├── pico_config.py
├── README.md
├── tests
│   ├── bridge.mpy
│   ├── cbor3.mpy
│   ├── esp32_config.py
│   ├── esp32_proxy.mpy
│   ├── pico_client.mpy
│   ├── pico_config.py
│   ├── README.md
│   ├── ringbuffer.mpy
│   ├── test_bridge.py
│   ├── test_pico_client.py
│   └── test_ringbuffer.py
└── USER-MANUAL.md
```

## Advanced Features

### Event-Driven Programming

The `events.py` library provides cooperative multitasking:

*   **Scheduled Tasks**: Run tasks at specific times or intervals
*   **Event Triggers**: Tasks can wait for and respond to events
*   **Repeating Tasks**: Automatically repeat tasks at intervals
*   **Task Management**: Cancel, monitor, and control task execution

### Ring Buffer

The `ringbuffer.py` provides efficient message queuing:

*   **Fixed-size Buffer**: Pre-allocated memory for predictable performance
*   **Message IDs**: Each message has a unique identifier
*   **Selective Retrieval**: Get messages by ID or in order
*   **Memory Efficient**: Circular buffer with automatic cleanup

## API Reference

### BridgeClient

*   `call(op, args, timeout_ms, resend_ms)`: Send a request to ESP32

### ProxySocket

*   `connect(addr, timeout_s)`: Connect to remote host
*   `send(data)`: Send data
*   `recv(n, timeout_s)`: Receive up to n bytes
*   `close()`: Close socket
*   `settimeout(timeout_s)`: Set socket timeout
*   `bind(addr, timeout_s)`: Bind socket to address (for server sockets)
*   `listen(backlog, timeout_s)`: Listen for incoming connections (for server sockets)
*   `accept(timeout_s)`: Accept incoming connection (for server sockets)
*   `sendto(data, addr)`: Send UDP datagram to address
*   `recvfrom(n, timeout_s)`: Receive UDP datagram
*   `wrap_ssl(server_hostname, timeout_s)`: Wrap socket with SSL/TLS

### Work (Events)

*   `do(job, params)`: Execute job immediately
*   `at(job, params, at)`: Execute job after delay
*   `repeat(job, params, every)`: Execute job repeatedly
*   `on(job, params, when)`: Execute job when event triggers
*   `trigger_event(flag, pkg)`: Trigger an event
*   `start()`: Start the event loop

### Ring (Buffer)

*   `put(msg_id, msg_bytes)`: Add message to buffer
*   `get()`: Get next message
*   `peek()`: Look at next message without removing
*   `pull(msg_id)`: Get specific message by ID
*   `list()`: List all message IDs

## Troubleshooting

### Connection Issues

*   Verify UART pins are correctly connected
*   Check baud rate matches on both devices
*   Enable hardware flow control if available
*   Reduce baud rate if experiencing data corruption

### Memory Issues

*   Call `gc.collect()` regularly
*   Reduce buffer sizes in config files
*   Limit concurrent socket operations

### Timeout Errors

*   Increase timeout values
*   Check WiFi connection on ESP32
*   Verify network connectivity

## Future Enhancements

*   MQTT protocol support
*   Enhanced error reporting
*   Watchdog timers
*   Connection pooling

## License

This project is open source. See LICENSE file for details.


