# test_bridge.py
import gc
from bridge import (
    slip_encode, SlipStream, pack_packet, unpack_packet,
    T_REQ, T_RESP, T_ACK, _crc16_ccitt
)

def test_crc16():
    print("Testing CRC16...")
    data = b"Hello, World!"
    crc = _crc16_ccitt(data)
    assert isinstance(crc, int)
    assert 0 <= crc <= 0xFFFF
    
    crc2 = _crc16_ccitt(data)
    assert crc == crc2
    print("  CRC16: PASS")

def test_slip_encode():
    print("Testing SLIP encoding...")
    
    raw = b"Hello"
    encoded = slip_encode(raw)
    assert encoded[0] == 0xC0
    assert encoded[-1] == 0xC0
    
    raw_with_end = b"\xC0Hello"
    encoded = slip_encode(raw_with_end)
    assert b"\xDB\xDC" in encoded
    
    raw_with_esc = b"\xDBHello"
    encoded = slip_encode(raw_with_esc)
    assert b"\xDB\xDD" in encoded
    
    print("  SLIP encoding: PASS")

def test_slip_stream():
    print("Testing SLIP stream...")
    
    stream = SlipStream()
    
    raw = b"Test message"
    encoded = slip_encode(raw)
    frames = stream.feed(encoded)
    assert len(frames) == 1
    assert frames[0] == raw
    
    stream = SlipStream()
    part1 = encoded[:5]
    part2 = encoded[5:]
    frames1 = stream.feed(part1)
    assert len(frames1) == 0
    frames2 = stream.feed(part2)
    assert len(frames2) == 1
    assert frames2[0] == raw
    
    print("  SLIP stream: PASS")

def test_packet_pack_unpack():
    print("Testing packet pack/unpack...")
    
    payload = b"Test payload"
    seq = 42
    
    packed = pack_packet(T_REQ, seq, payload)
    assert isinstance(packed, bytes)
    assert len(packed) > len(payload)
    
    stream = SlipStream()
    frames = stream.feed(packed)
    assert len(frames) == 1
    
    result = unpack_packet(frames[0])
    assert result is not None
    msg_type, recv_seq, recv_payload = result
    assert msg_type == T_REQ
    assert recv_seq == seq
    assert recv_payload == payload
    
    print("  Packet pack/unpack: PASS")

def test_packet_corruption():
    print("Testing packet corruption detection...")
    
    payload = b"Test"
    packed = pack_packet(T_REQ, 1, payload)
    
    stream = SlipStream()
    frames = stream.feed(packed)
    raw = frames[0]
    
    corrupted = bytearray(raw)
    corrupted[10] ^= 0xFF
    
    result = unpack_packet(bytes(corrupted))
    assert result is None
    
    print("  Corruption detection: PASS")

def test_empty_payload():
    print("Testing empty payload...")
    
    packed = pack_packet(T_ACK, 1, b"")
    stream = SlipStream()
    frames = stream.feed(packed)
    
    result = unpack_packet(frames[0])
    assert result is not None
    msg_type, seq, payload = result
    assert msg_type == T_ACK
    assert payload == b""
    
    print("  Empty payload: PASS")

def test_large_payload():
    print("Testing large payload...")
    
    payload = b"X" * 4096
    packed = pack_packet(T_REQ, 100, payload)
    
    stream = SlipStream()
    frames = stream.feed(packed)
    
    result = unpack_packet(frames[0])
    assert result is not None
    msg_type, seq, recv_payload = result
    assert recv_payload == payload
    
    print("  Large payload: PASS")

def test_sequence_wraparound():
    print("Testing sequence wraparound...")
    
    packed1 = pack_packet(T_REQ, 65535, b"test")
    packed2 = pack_packet(T_REQ, 0, b"test")
    packed3 = pack_packet(T_REQ, 1, b"test")
    
    stream = SlipStream()
    for packed in [packed1, packed2, packed3]:
        frames = stream.feed(packed)
        result = unpack_packet(frames[0])
        assert result is not None
    
    print("  Sequence wraparound: PASS")

def run_all_tests():
    print("=" * 50)
    print("Running Bridge Tests")
    print("=" * 50)
    
    tests = [
        test_crc16,
        test_slip_encode,
        test_slip_stream,
        test_packet_pack_unpack,
        test_packet_corruption,
        test_empty_payload,
        test_large_payload,
        test_sequence_wraparound,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
        gc.collect()
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        raise SystemExit(1)
