## Init

### on esp32-c3
```bash
$ mpr a1 mount .
Local directory . is mounted at /remote
Connected to MicroPython at /dev/ttyACM1
Use Ctrl-] or Ctrl-x to exit this shell
>
MicroPython v1.27.0-kaki5 on 2025-12-14; ESP32-C3 BlueBoard CUSB (KAKI5) with ESP32-C3
>>> import esp32_proxy
Connecting WiFi...
  Still connecting... (10/40)
WiFi OK: 192.168.4.87
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=8, rx=9, rts=4, cts=5
UART v3 bridge ready

```

## Examples


### example_tcp_echo

#### On Linux PC
```bash
$ ncat -v -4 -l 192.168.4.27 7777 -c 'cat'
Ncat: Version 7.94SVN ( https://nmap.org/ncat )
Ncat: Listening on 192.168.4.27:7777
Ncat: Connection from 192.168.4.87:64994.
```

#### On Pico
```bash
>>> 
>>> import example_tcp_echo as t
>>> t.main()
==================================================
TCP Echo Example
==================================================
Note: This requires an echo server running
You can use: nc -l 7777 (on Linux/Mac)
==================================================
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
Connecting to 192.168.4.27:7777...
Connected!
Sending: Hello from Pico!
Receiving echo...
Received: Hello from Pico!

Done!
```

### example_tcp_server

#### On Pico
```bash
MicroPython v1.27.0-kaki5 on 2025-12-10; Black Board RP2040 with RP2040
>>>
>>> 
>>> import example_tcp_server as t
>>> t.main()
==================================================
TCP Server Example
==================================================
This example creates a simple HTTP server
Test with: curl http://<esp32-ip>:8080
==================================================
UART: 1400000 baud, rxbuf=16384, flow=ON, timeout=0
PINS: tx=0, rx=1, rts=3, cts=2
Binding to port 8080...
Listening on port 8080...
Server ready! Waiting for connections...
Press Ctrl+C to stop

Waiting for connection...
Connection from ('192.168.4.27', 43558)
Received: b'GET / HTTP/1.1\r\nHost: 192.168.4.87:8080\r\nUser-Agent: curl/8.5.0\r\nAccept: */*\r\n\r\n'
Response sent

Waiting for connection...
Connection from ('192.168.4.27', 43692)
Received: b'GET / HTTP/1.1\r\nHost: 192.168.4.87:8080\r\nUser-Agent: curl/8.5.0\r\nAccept: */*\r\n\r\n'
Response sent

Waiting for connection...
Accept timeout or error: bridge_timeout: sock_accept

Waiting for connection...

Shutting down server...

Done!
>>> 
```

#### On Linux PC
```bash
$ curl http://192.168.4.87:8080
Hello, World!:~$ curl http://192.168.4.87:8080
Hello, World!:~$ 
```
