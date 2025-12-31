# Examples

This directory contains example scripts demonstrating how to use the UART Socket Bridge system.

## Available Examples

### 1. HTTP GET Request (`example_http_get.py`)
Demonstrates making HTTP GET requests through the bridge.
```python
python example_http_get.py
```
Features:
- Connecting to remote servers
- Sending HTTP requests
- Receiving and processing responses
- Proper resource cleanup

### 2. DNS Lookup (`example_dns_lookup.py`)
Shows how to perform DNS lookups for hostnames.
```python
python example_dns_lookup.py
```
Features:
- Resolving hostnames to IP addresses
- Handling multiple address families
- Error handling

### 3. TCP Echo Client (`example_tcp_echo.py`)
Simple TCP client that sends and receives data.
```python
python example_tcp_echo.py
```
Features:
- TCP socket connection
- Sending data
- Receiving echoed data
- Connection management

Note: Requires an echo server running (e.g., `nc -l 7777`)

### 4. Event-Driven Multitasking (`example_events_multitask.py`)
Demonstrates the event system for concurrent task execution.
```python
python example_events_multitask.py
```
Features:
- Periodic task scheduling
- One-time delayed tasks
- Event triggering and handling
- Multiple concurrent tasks

### 5. Ring Buffer Usage (`example_ringbuffer.py`)
Shows various ring buffer operations and patterns.
```python
python example_ringbuffer.py
```
Features:
- Basic put/get operations
- Peeking and pulling messages
- Buffer wraparound
- Message queue simulation

### 6. Complete Workflow (`example_complete_workflow.py`)
Comprehensive example combining all components.
```python
python example_complete_workflow.py
```
Features:
- Network connectivity monitoring
- Periodic HTTP data fetching
- Message queue processing
- Status reporting
- Event-driven architecture

## Running Examples

1. Ensure your ESP32 and Pico are properly connected and configured
2. Upload the necessary files to your Pico (pico_client.py, events.py, ringbuffer.py)
3. Start the ESP32 proxy
4. Run any example script on the Pico

## Customization

Feel free to modify these examples for your specific use case:
- Change hostnames and ports
- Adjust timing intervals
- Add custom event handlers
- Implement your own message processing logic

## Troubleshooting

If examples fail:
1. Check UART connections between ESP32 and Pico
2. Verify ESP32 WiFi configuration
3. Ensure correct baud rate (115200)
4. Check network connectivity
5. Review error messages for specific issues

## Additional Resources

- See `USER-MANUAL.md` for detailed API documentation
- See `README.md` for system overview
- See `tests/` directory for unit tests
