# bridge.py
# UART v3 protocol: SLIP framing + CRC16 + (type, seq) + pack payload
import struct
import time

# SLIP constants
_END = 0xC0
_ESC = 0xDB
_ESC_END = 0xDC
_ESC_ESC = 0xDD

# Protocol
V3 = 3
T_REQ  = 1
T_RESP = 2
T_ACK  = 3

# Packet layout (before SLIP):
# [0]=ver (1)
# [1]=type (1)
# [2:4]=seq (uint16 LE)
# [4:6]=plen (uint16 LE)
# [6:8]=crc16 (uint16 LE)  crc over bytes[0:6] + payload
# [8:]=payload (CBOR, plen bytes)

MAX_PAYLOAD_SIZE = 65535

def _crc16_ccitt(data: bytes, init=0xFFFF) -> int:
    crc = init
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF

def slip_encode(raw: bytes) -> bytes:
    if not raw:
        return bytes([_END, _END])
    out = bytearray(len(raw) * 2 + 2)
    idx = 0
    out[idx] = _END
    idx += 1
    for b in raw:
        if b == _END:
            out[idx] = _ESC
            idx += 1
            out[idx] = _ESC_END
            idx += 1
        elif b == _ESC:
            out[idx] = _ESC
            idx += 1
            out[idx] = _ESC_ESC
            idx += 1
        else:
            out[idx] = b
            idx += 1
    out[idx] = _END
    idx += 1
    return bytes(out[:idx])

class SlipStream:
    def __init__(self, max_frame_size=8192):
        self._buf = bytearray()
        self._esc = False
        self._max_frame_size = max_frame_size

    def _buf_clear(self):
        # MicroPython compatibility across ports/builds
        try:
            self._buf.clear()
            return
        except AttributeError:
            pass
        try:
            self._buf[:] = b""
            return
        except TypeError:
            # Some builds don't support slice operations on bytearray
            self._buf = bytearray()

    def feed(self, data: bytes):
        if not data:
            return []
        frames = []
        for b in data:
            if b == _END:
                if self._buf:
                    if len(self._buf) <= self._max_frame_size:
                        frames.append(bytes(self._buf))
                    self._buf_clear()
                self._esc = False
                continue

            if self._esc:
                if b == _ESC_END:
                    self._buf.append(_END)
                elif b == _ESC_ESC:
                    self._buf.append(_ESC)
                else:
                    self._buf.append(b)
                self._esc = False
                continue

            if b == _ESC:
                self._esc = True
                continue

            if len(self._buf) < self._max_frame_size:
                self._buf.append(b)

        return frames

def pack_packet(msg_type: int, seq: int, payload: bytes = b"") -> bytes:
    if payload is None:
        payload = b""
    plen = len(payload)
    if plen > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload too large: {plen} > {MAX_PAYLOAD_SIZE}")
    hdr_wo_crc = bytes([V3, msg_type]) + struct.pack("<HH", seq & 0xFFFF, plen & 0xFFFF)
    crc = _crc16_ccitt(hdr_wo_crc + payload)
    raw = hdr_wo_crc + struct.pack("<H", crc) + payload
    return slip_encode(raw)

def unpack_packet(raw: bytes):
    # returns (msg_type, seq, payload_bytes) or None if invalid
    if raw is None or len(raw) < 8:
        return None
    ver = raw[0]
    if ver != V3:
        return None
    msg_type = raw[1]
    seq, plen = struct.unpack("<HH", raw[2:6])
    crc = struct.unpack("<H", raw[6:8])[0]
    if len(raw) != 8 + plen:
        return None
    if plen > MAX_PAYLOAD_SIZE:
        return None
    payload = raw[8:8+plen]
    calc = _crc16_ccitt(raw[0:6] + payload)
    if calc != crc:
        return None
    return (msg_type, seq, payload)

def ticks_ms():
    return time.ticks_ms()

def ticks_add(a, b):
    return time.ticks_add(a, b)

def ticks_diff(a, b):
    return time.ticks_diff(a, b)

