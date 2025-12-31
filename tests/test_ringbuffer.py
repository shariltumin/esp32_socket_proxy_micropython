# test_ringbuffer.py
import gc
from ringbuffer import Ring

def test_basic_put_get():
    print("Testing basic put/get...")
    buffer = Ring(1024)
    
    buffer.put(1, b"Hello")
    buffer.put(2, b"World")
    
    msg_id, msg = buffer.get()
    assert msg_id == 1
    assert msg == b"Hello"
    
    msg_id, msg = buffer.get()
    assert msg_id == 2
    assert msg == b"World"
    
    msg_id, msg = buffer.get()
    assert msg_id == 0
    assert msg == b""
    
    print("  Basic put/get: PASS")

def test_empty_buffer():
    print("Testing empty buffer...")
    buffer = Ring(512)
    
    assert buffer.is_empty()
    assert not buffer.is_full()
    
    msg_id, msg = buffer.get()
    assert msg_id == 0
    
    print("  Empty buffer: PASS")

def test_buffer_full():
    print("Testing buffer full...")
    buffer = Ring(64)
    
    try:
        for i in range(1, 20):
            buffer.put(i, b"X" * 10)
    except MemoryError:
        pass
    
    assert buffer.is_full() or len(buffer) > 50
    print("  Buffer full: PASS")

def test_peek():
    print("Testing peek...")
    buffer = Ring(512)
    
    buffer.put(1, b"First")
    buffer.put(2, b"Second")
    
    msg_id, msg = buffer.peek()
    assert msg_id == 1
    assert msg == b"First"
    
    msg_id, msg = buffer.peek()
    assert msg_id == 1
    
    msg_id, msg = buffer.get()
    assert msg_id == 1
    
    print("  Peek: PASS")

def test_pull():
    print("Testing pull...")
    buffer = Ring(1024)
    
    buffer.put(1, b"First")
    buffer.put(2, b"Second")
    buffer.put(3, b"Third")
    
    msg_id, msg = buffer.pull(2)
    assert msg_id == 2
    assert msg == b"Second"
    
    msg_id, msg = buffer.get()
    assert msg_id == 1
    
    msg_id, msg = buffer.get()
    assert msg_id == 3
    
    print("  Pull: PASS")

def test_list():
    print("Testing list...")
    buffer = Ring(1024)
    
    buffer.put(10, b"A")
    buffer.put(20, b"B")
    buffer.put(30, b"C")
    
    ids = buffer.list()
    assert ids == [10, 20, 30]
    
    buffer.get()
    ids = buffer.list()
    assert ids == [20, 30]
    
    print("  List: PASS")

def test_clear():
    print("Testing clear...")
    buffer = Ring(512)
    
    buffer.put(1, b"Data")
    buffer.put(2, b"More")
    
    assert not buffer.is_empty()
    
    buffer.clear()
    assert buffer.is_empty()
    assert len(buffer) == 0
    
    print("  Clear: PASS")

def test_wraparound():
    print("Testing wraparound...")
    buffer = Ring(128)
    
    for i in range(1, 11):
        buffer.put(i, b"X" * 8)
    
    for i in range(1, 6):
        msg_id, msg = buffer.get()
        assert msg_id == i
    
    for i in range(11, 16):
        buffer.put(i, b"Y" * 8)
    
    for i in range(6, 16):
        msg_id, msg = buffer.get()
        assert msg_id == i
    
    print("  Wraparound: PASS")

def test_large_messages():
    print("Testing large messages...")
    buffer = Ring(8192)
    
    large_msg = b"Z" * 2000
    buffer.put(1, large_msg)
    
    msg_id, msg = buffer.get()
    assert msg_id == 1
    assert msg == large_msg
    
    print("  Large messages: PASS")

def test_invalid_inputs():
    print("Testing invalid inputs...")
    buffer = Ring(512)
    
    try:
        buffer.put(0, b"Invalid")
        assert False, "Should reject msg_id 0"
    except ValueError:
        pass
    
    try:
        buffer.put(70000, b"Invalid")
        assert False, "Should reject msg_id > 65535"
    except ValueError:
        pass
    
    try:
        buffer.put(1, "Not bytes")
        assert False, "Should reject non-bytes"
    except TypeError:
        pass
    
    print("  Invalid inputs: PASS")

def run_all_tests():
    print("=" * 50)
    print("Running Ring Buffer Tests")
    print("=" * 50)
    
    tests = [
        test_basic_put_get,
        test_empty_buffer,
        test_buffer_full,
        test_peek,
        test_pull,
        test_list,
        test_clear,
        test_wraparound,
        test_large_messages,
        test_invalid_inputs,
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
