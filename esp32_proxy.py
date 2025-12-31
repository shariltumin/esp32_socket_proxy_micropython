# esp32_proxy.py
from esp32_config import uart_setup, wifi_connect, set_time
from cbor3 import dumps as pack, loads as unpack
import time
import socket
import tls # use tls directly
import gc

from bridge import (
    SlipStream, pack_packet, unpack_packet,
    T_REQ, T_RESP, T_ACK,
    ticks_ms
)

sta = wifi_connect()
uart = uart_setup()
ok = set_time()

DEBUG = 0
RESP_CACHE_MAX = 16
SOCKET_TIMEOUT_DEFAULT = 5.0
MAX_SID = 1024

class SockTable:
    def __init__(self):
        self._next = 0
        self._m = {}

    def new(self, family, typ, proto=0):
        s = socket.socket(family, typ, proto)
        self._next = (self._next%MAX_SID)+1
        sid = self._next
        self._m[sid] = s
        if DEBUG: print('DEBUG socktab:', self._m) 
        return sid

    def get(self, sid):
        sid = int(sid)
        if sid not in self._m:
            raise KeyError(f"Socket {sid} not found")
        return self._m[sid]

    def close(self, sid):
        sid = int(sid)
        s = self._m.pop(sid, None)
        if s:
            try:
                s.close()
            except:
                pass
        if DEBUG: print('DEBUG socktab:', self._m) 

    def close_all(self):
        for sid in list(self._m.keys()):
            self.close(sid)

def handle_req(socktab: SockTable, req: dict) -> dict:
    global sta
    op = req.get("op")
    args = req.get("args", {}) or {}

    if DEBUG: print('DEBUG:', op, args)

    try:
        # RPC like. Add more when needed
        if op == "sock_reset":
            # Close all sockets and clear the table
            socktab.close_all()
            return {"ok": True, "result": True}

        if op == "ping":
            return {"ok": True, "result": {"pong": True, "t_ms": ticks_ms(), "echo": "I see you, you see me"}}

        if op == "get_time":
            return {"ok": True, "result": {"time": time.time()}}

        if op == "set_time":
            host = args.get("host")
            if not host:
               host = 'pool.ntp.org' # global ntp servers pool
            if set_time(host=host):
               return {"ok": True, "result": {"time": time.time()}}
            else:
               return {"ok": False, "error": f"ntp server {host} not responding."}

        if op == "wifi_status":
            return {"ok": True, "result": {"connected": sta.isconnected(), "ifconfig": sta.ifconfig() if sta.isconnected() else None}}

        if op == "dns":
            host = args.get("host")
            if not host:
                return {"ok": False, "error": "missing_host"}
            port = int(args.get("port", 80))
            family = int(args.get("family", 0))
            typ = int(args.get("type", 0))
            proto = int(args.get("proto", 0))
            try:
               res = socket.getaddrinfo(host, port, family, typ, proto)
               out = []
               for r in res:
                   af, ty, pr, canon, sa = r
                   out.append([af, ty, pr, canon, sa])
               return {"ok": True, "result": out}
            except Exception as e:
               return {"ok": False, "error": "dns_error", "detail": repr(e)}

        # Socket commands
        if op == "sock_open":
            family = int(args.get("family", 2))
            typ = int(args.get("type", 1))
            proto = int(args.get("proto", 0))
            try:
               sid = socktab.new(family, typ, proto)
               return {"ok": True, "result": {"sid": sid}}
            except Exception as e:
               return {"ok": False, "error": "sock_open_error", "detail": repr(e)}

        if op == "sock_settimeout":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            timeout_ms = args.get("timeout_ms", None)
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError):
                return {"ok": False, "error": "invalid_sid_type", "detail": repr(e)}
            try:
               if timeout_ms is None:
                   s.settimeout(None)
               else:
                   s.settimeout(max(0, int(timeout_ms)) / 1000.0)
               return {"ok": True, "result": True}
            except Exception as e:
               return {"ok": False, "error": "sock_settimeout_error", "detail": repr(e)}

        if op == "sock_connect":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            host = args.get("host")
            if not host:
                return {"ok": False, "error": "missing_host"}
            port = int(args.get("port", 80))
            ssl = args.get("ssl")
            timeout_ms = int(args.get("timeout_ms", 5000))
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
               if not ssl: # can not settimeout() for ssl wrap
                  s.settimeout(max(0, timeout_ms) / 1000.0)
               addr = socket.getaddrinfo(host, port)[0][-1]
               s.connect(addr)
               return {"ok": True, "result": True}
            except Exception as e:
               # On connect failure, drop the socket so it doesn’t leak
               socktab.close(sid)
               return {"ok": False, "error": "sock_connect_error", "detail": repr(e)}

        if op == "sock_send":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            data = args.get("data")
            if data is None:
                return {"ok": False, "error": "missing_data"}
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
               n = s.send(data)
               return {"ok": True, "result": {"n": n}}
            except Exception as e:
               # Failed send => connection probably broken; clean it up
               socktab.close(sid)
               return {"ok": False, "error": "sock_send_error", "detail": repr(e)}

        if op == "sock_recv":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            n = int(args.get("n", 512))
            ssl = args.get("ssl")
            timeout_ms = int(args.get("timeout_ms", 5000))
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
               if not ssl: # tls socket has no settimeout()
                  s.settimeout(max(0, timeout_ms) / 1000.0)
               data = s.recv(n)
               return {"ok": True, "result": {"data": data, "n": len(data), "eof": (len(data) == 0)}}
            except Exception as e:
               # Failed recv => connection probably broken; clean it up
               socktab.close(sid)
               return {"ok": False, "error": "sock_recv_error", "detail": repr(e)}

        if op == "sock_close":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            try:
               sid = int(sid)
               socktab.close(sid)
               return {"ok": True, "result": True}
            except Exception as e:
               return {"ok": False, "error": "sock_close_error", "detail": repr(e)}

        if op == "sock_bind":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            host = args.get("host", "")
            port = int(args.get("port", 0))
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # server
                addr = (host, port) if host else ("0.0.0.0", port)
                s.bind(addr)
                return {"ok": True, "result": True}
            except Exception as e:
                return {"ok": False, "error": "sock_bind_error", "detail": repr(e)}

        if op == "sock_listen":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            backlog = int(args.get("backlog", 5))
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
                s.listen(backlog)
                return {"ok": True, "result": True}
            except Exception as e:
                return {"ok": False, "error": "sock_listen_error", "detail": repr(e)}

        if op == "sock_accept":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            timeout_ms = int(args.get("timeout_ms", 5000))
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
                s.settimeout(max(0, timeout_ms) / 1000.0)
                conn, addr = s.accept()
                socktab._next = (socktab._next%MAX_SID)+1
                new_sid = socktab._next
                socktab._m[new_sid] = conn
                return {"ok": True, "result": {"sid": new_sid, "addr": addr}}
            except Exception as e:
                return {"ok": False, "error": "sock_accept_error", "detail": repr(e)}

        if op == "sock_sendto":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            data = args.get("data")
            if data is None:
                return {"ok": False, "error": "missing_data"}
            host = args.get("host")
            port = int(args.get("port", 0))
            if not host or not port:
                return {"ok": False, "error": "missing_host_or_port"}
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
                addr = (host, port)
                n = s.sendto(data, addr)
                return {"ok": True, "result": {"n": n}}
            except Exception as e:
                # Failed sendto => connection probably broken; clean it up
                socktab.close(sid)
                return {"ok": False, "error": "sock_sendto_error", "detail": repr(e)}

        if op == "sock_recvfrom":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            n = int(args.get("n", 512))
            timeout_ms = int(args.get("timeout_ms", 5000))
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
                s.settimeout(max(0, timeout_ms) / 1000.0)
                data, addr = s.recvfrom(n)
                return {"ok": True, "result": {"data": data, "n": len(data), "addr": addr}}
            except Exception as e:
                # Failed recvfrom => connection probably broken; clean it up
                socktab.close(sid)
                return {"ok": False, "error": "sock_recvfrom_error", "detail": repr(e)}

        if op == "sock_wrap_ssl":
            sid = args.get("sid")
            if sid is None:
                return {"ok": False, "error": "missing_sid"}
            server_hostname = args.get("server_hostname")
            try:
                sid = int(sid)
                s = socktab.get(sid)
            except (ValueError, TypeError, KeyError) as e:
                return {"ok": False, "error": "invalid_sid", "detail": repr(e)}
            try:
                ssl = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
                ssl.verify_mode = tls.CERT_NONE
                # ssl.load_verify_locations(cacert) # MBEDTLS_ERR_SSL_CA_CHAIN_REQUIRED
                # ssl_sock = ssl.wrap_socket(s, server_side=False, server_hostname=server_hostname)
                ssl_sock = ssl.wrap_socket(s, server_side=False)
                socktab._m[sid] = ssl_sock
                return {"ok": True, "result": True}
            except Exception as e:
                return {"ok": False, "error": "sock_wrap_ssl_error", "detail": repr(e)}

        return {"ok": False, "error": "unknown_op", "detail": op}

    except KeyError as e:
        return {"ok": False, "error": "missing_parameter", "detail": repr(e)}
    except ValueError as e:
        return {"ok": False, "error": "invalid_parameter", "detail": repr(e)}
    except Exception as e:
        return {"ok": False, "error": "exception", "detail": repr(e)}

def main():
    global uart
    check = uart.any
    read = uart.read
    write = uart.write
    collect = gc.collect
    delay = time.sleep_ms

    slip = SlipStream()
    slip_feed = slip.feed
    socktab = SockTable()

    resp_cache = {}
    resp_cache_order = []

    print("UART v3 bridge ready")

    try:
        while True:
            n = check()
            if n:
                data = read(n) or b""
                for raw in slip_feed(data):
                    pkt = unpack_packet(raw)
                    if not pkt:
                        continue
                    msg_type, seq, payload = pkt

                    if msg_type in (T_REQ, T_RESP):
                        write(pack_packet(T_ACK, seq, b""))

                    if msg_type == T_ACK:
                        if seq in resp_cache:
                            resp_cache.pop(seq, None)
                        continue

                    if msg_type != T_REQ:
                        continue

                    cached = resp_cache.get(seq)
                    if cached:
                        write(cached)
                        continue

                    req = unpack(payload) if payload else {}
                    resp_obj = handle_req(socktab, req)
                    resp_payload = pack(resp_obj)
                    resp_pkt = pack_packet(T_RESP, seq, resp_payload)

                    resp_cache[seq] = resp_pkt
                    resp_cache_order.append(seq)
                    if len(resp_cache_order) > RESP_CACHE_MAX:
                        old = resp_cache_order.pop(0)
                        resp_cache.pop(old, None)

                    write(resp_pkt)

                    if DEBUG:
                        print("REQ", seq, req, "RESP", resp_obj)
                collect()

            else:
                delay(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        socktab.close_all()
    except Exception as e:
        print(f"Fatal error: {e}")
        socktab.close_all()
        raise

main()
