# pico_client.py
import time
from machine import UART, Pin
from cbor3 import dumps as pack, loads as unpack
from pico_config import uart_setup
import gc

from bridge import (
    SlipStream, pack_packet, unpack_packet,
    T_REQ, T_RESP, T_ACK,
    ticks_ms, ticks_add, ticks_diff
)

class BridgeClient:
    def __init__(self):
        self.uart = uart_setup()
        self.slip = SlipStream()
        self.seq = 1

        self._acked = set()
        self._resp = {}
        self._max_acked_size = 100
        self._max_resp_size = 50

    def _next_seq(self):
        s = self.seq & 0xFFFF
        self.seq = (self.seq + 1) & 0xFFFF
        if self.seq == 0:
            self.seq = 1
        return s

    def _pump(self):
        n = self.uart.any()
        if not n:
            return
        data = self.uart.read(n) or b""
        for raw in self.slip.feed(data):
            pkt = unpack_packet(raw)
            if not pkt:
                continue
            msg_type, seq, payload = pkt

            if msg_type == T_ACK:
                self._acked.add(seq)
                if len(self._acked) > self._max_acked_size:
                    self._acked.clear()
                continue

            if msg_type == T_RESP:
                self.uart.write(pack_packet(T_ACK, seq, b""))
                try:
                    obj = unpack(payload) if payload else {}
                except Exception as e:
                    obj = {"ok": False, "error": "bad_payload", "detail": repr(e)}
                self._resp[seq] = obj
                if len(self._resp) > self._max_resp_size:
                    oldest_keys = sorted(self._resp.keys())[:10]
                    for k in oldest_keys:
                        self._resp.pop(k, None)
                continue

    def call(self, op: str, args=None, timeout_ms=8000, resend_ms=200):
        if args is None:
            args = {}
        if not isinstance(op, str) or not op:
            raise ValueError("Invalid operation")

        seq = self._next_seq()
        req_obj = {"op": op, "args": args}

        try:
            req_payload = pack(req_obj)
        except Exception as e:
            raise ValueError(f"Failed to pack request: {e}")

        req_pkt = pack_packet(T_REQ, seq, req_payload)

        deadline = ticks_add(ticks_ms(), int(timeout_ms))
        next_send = 0

        self._acked.discard(seq)
        self._resp.pop(seq, None)

        while ticks_diff(deadline, ticks_ms()) > 0:
            now = ticks_ms()
            if next_send == 0 or ticks_diff(now, next_send) >= 0:
                self.uart.write(req_pkt)
                next_send = ticks_add(now, int(resend_ms))

            self._pump()

            if seq in self._resp:
                resp = self._resp.pop(seq)
                if not resp.get("ok", False):
                    error = resp.get("error", "remote_error")
                    detail = resp.get("detail", "")
                    raise OSError(f"{error}: {detail}")
                return resp.get("result")

            time.sleep_ms(1)
            gc.collect()

        raise OSError(f"bridge_timeout: {op}")

class ProxySocket:
    AF_INET = 2
    SOCK_STREAM = 1
    SOCK_DGRAM = 2

    def __init__(self, client: BridgeClient, family=None, typ=None, proto=0):
        if family is None:
            family = self.AF_INET
        if typ is None:
            typ = self.SOCK_STREAM
        self.c = client
        self._closed = False
        try:
            r = self.c.call("sock_open", {"family": int(family), "type": int(typ), "proto": int(proto)}, timeout_ms=4000)
            self.sid = int(r["sid"])
        except Exception as e:
            raise OSError(f"Failed to open socket: {e}")

    def _check_closed(self):
        if self._closed:
            raise OSError("Socket is closed")

    def settimeout(self, timeout_s):
        self._check_closed()
        if timeout_s is None:
            self.c.call("sock_settimeout", {"sid": self.sid, "timeout_ms": None}, timeout_ms=2000)
        else:
            self.c.call("sock_settimeout", {"sid": self.sid, "timeout_ms": int(timeout_s * 1000)}, timeout_ms=2000)

    def connect(self, addr, ssl=False, timeout_s=5):
        self._check_closed()
        if not isinstance(addr, (tuple, list)) or len(addr) != 2:
            raise ValueError("Address must be (host, port) tuple")
        host, port = addr
        if ssl:
            self.c.call("sock_connect", {"sid": self.sid, "host": host, "port": int(port), "ssl": True, "timeout_ms": 0}, timeout_ms=int(timeout_s * 1000) + 2000)
        else:
            self.c.call("sock_connect", {"sid": self.sid, "host": host, "port": int(port), "ssl": False, "timeout_ms": int(timeout_s * 1000)}, timeout_ms=int(timeout_s * 1000) + 2000)

    def send(self, data: bytes):
        self._check_closed()
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data, 'utf-8')
        if not data:
            return 0
        r = self.c.call("sock_send", {"sid": self.sid, "data": data}, timeout_ms=8000)
        return int(r["n"])

    def recv(self, n: int, ssl=False, timeout_s=5):
        self._check_closed()
        if n <= 0:
            raise ValueError("Receive size must be positive")
        if ssl:
            r = self.c.call("sock_recv", {"sid": self.sid, "n": int(n), "ssl": True, "timeout_ms": 0}, timeout_ms=int(timeout_s * 1000) + 2000)
        else:
            r = self.c.call("sock_recv", {"sid": self.sid, "n": int(n), "ssl": False, "timeout_ms": int(timeout_s * 1000)}, timeout_ms=int(timeout_s * 1000) + 2000)
        return r["data"]

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.c.call("sock_close", {"sid": self.sid}, timeout_ms=2000)
        except:
            pass

    def bind(self, addr, timeout_s=5):
        self._check_closed()
        if not isinstance(addr, (tuple, list)) or len(addr) != 2:
            raise ValueError("Address must be (host, port) tuple")
        host, port = addr
        self.c.call("sock_bind", {"sid": self.sid, "host": host, "port": int(port)}, timeout_ms=int(timeout_s * 1000) + 2000)

    def listen(self, backlog=5, timeout_s=5):
        self._check_closed()
        self.c.call("sock_listen", {"sid": self.sid, "backlog": int(backlog)}, timeout_ms=int(timeout_s * 1000) + 2000)

    def accept(self, timeout_s=5):
        self._check_closed()
        r = self.c.call("sock_accept", {"sid": self.sid, "timeout_ms": int(timeout_s * 1000)}, timeout_ms=int(timeout_s * 1000) + 2000)
        # new_sock = ProxySocket.__new__(ProxySocket)
        # new_sock = type(ProxySocket).__call__(ProxySocket)
        new_sock = object.__new__(ProxySocket)
        # new_sock = ProxySocket(self.c, typ=ProxySocket.SOCK_STREAM) # WRONG!
        new_sock.c = self.c
        new_sock._closed = False
        new_sock.sid = int(r["sid"])
        return new_sock, r["addr"]

    def sendto(self, data: bytes, addr):
        self._check_closed()
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data, 'utf-8')
        if not data:
            return 0
        if not isinstance(addr, (tuple, list)) or len(addr) != 2:
            raise ValueError("Address must be (host, port) tuple")
        host, port = addr
        r = self.c.call("sock_sendto", {"sid": self.sid, "data": data, "host": host, "port": int(port)}, timeout_ms=8000)
        return int(r["n"])

    def recvfrom(self, n: int, timeout_s=5):
        self._check_closed()
        if n <= 0:
            raise ValueError("Receive size must be positive")
        r = self.c.call("sock_recvfrom", {"sid": self.sid, "n": int(n), "timeout_ms": int(timeout_s * 1000)}, timeout_ms=int(timeout_s * 1000) + 2000)
        return r["data"], r["addr"]

    def wrap_ssl(self, server_hostname=None, timeout_s=5):
        self._check_closed()
        self.c.call("sock_wrap_ssl", {"sid": self.sid, "server_hostname": server_hostname}, timeout_ms=int(timeout_s * 1000) + 2000)

def getaddrinfo(client: BridgeClient, host: str, port: int):
    if not isinstance(host, str) or not host:
        raise ValueError("Invalid host")
    if not isinstance(port, int) or port < 0 or port > 65535:
        raise ValueError("Invalid port")
    return client.call("dns", {"host": host, "port": int(port)}, timeout_ms=6000)

