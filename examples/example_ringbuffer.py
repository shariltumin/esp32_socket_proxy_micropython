# example_ringbuffer.py
from ringbuffer import Ring
import gc

def demo_basic_operations():
    print("=" * 50)
    print("Basic Ring Buffer Operations")
    print("=" * 50)
    
    buffer = Ring(1024)
    
    print("\n1. Adding messages...")
    buffer.put(1, b"First message")
    buffer.put(2, b"Second message")
    buffer.put(3, b"Third message")
    print(f"   Buffer size: {len(buffer)} bytes")
    print(f"   Message IDs: {buffer.list()}")
    
    print("\n2. Getting messages (FIFO)...")
    msg_id, msg = buffer.get()
    print(f"   Got: ID={msg_id}, Data={msg}")
    
    msg_id, msg = buffer.get()
    print(f"   Got: ID={msg_id}, Data={msg}")
    
    print(f"   Remaining IDs: {buffer.list()}")
    
    print("\n3. Peeking (non-destructive)...")
    msg_id, msg = buffer.peek()
    print(f"   Peeked: ID={msg_id}, Data={msg}")
    print(f"   IDs still in buffer: {buffer.list()}")
    
    print("\n4. Pulling specific message...")
    buffer.put(4, b"Fourth message")
    buffer.put(5, b"Fifth message")
    print(f"   Before pull: {buffer.list()}")
    
    msg_id, msg = buffer.pull(4)
    print(f"   Pulled: ID={msg_id}, Data={msg}")
    print(f"   After pull: {buffer.list()}")
    
    print("\n5. Clearing buffer...")
    buffer.clear()
    print(f"   Buffer empty: {buffer.is_empty()}")
    print(f"   Buffer size: {len(buffer)} bytes")
    
    gc.collect()

def demo_wraparound():
    print("\n" + "=" * 50)
    print("Ring Buffer Wraparound Demo")
    print("=" * 50)
    
    buffer = Ring(256)
    
    print("\n1. Filling buffer...")
    for i in range(1, 11):
        buffer.put(i, b"X" * 20)
    print(f"   Added 10 messages, size: {len(buffer)} bytes")
    
    print("\n2. Removing half...")
    for i in range(5):
        buffer.get()
    print(f"   Remaining: {buffer.list()}")
    
    print("\n3. Adding more (wraparound)...")
    for i in range(11, 16):
        buffer.put(i, b"Y" * 20)
    print(f"   IDs: {buffer.list()}")
    print(f"   Size: {len(buffer)} bytes")
    
    print("\n4. Draining buffer...")
    count = 0
    while not buffer.is_empty():
        msg_id, msg = buffer.get()
        count += 1
    print(f"   Drained {count} messages")
    
    gc.collect()

def demo_message_queue():
    print("\n" + "=" * 50)
    print("Message Queue Simulation")
    print("=" * 50)
    
    buffer = Ring(2048)
    
    print("\n1. Producer: Adding messages...")
    messages = [
        (101, b"Task: Process data"),
        (102, b"Task: Send notification"),
        (103, b"Task: Update database"),
        (104, b"Task: Generate report"),
    ]
    
    for msg_id, msg in messages:
        buffer.put(msg_id, msg)
        print(f"   Queued: ID={msg_id}")
    
    print(f"\n2. Queue status:")
    print(f"   Pending tasks: {len(buffer.list())}")
    print(f"   Task IDs: {buffer.list()}")
    
    print("\n3. Consumer: Processing tasks...")
    while not buffer.is_empty():
        msg_id, msg = buffer.get()
        print(f"   Processing: ID={msg_id}, Task={msg.decode()}")
    
    print("\n4. Queue empty!")
    
    gc.collect()

def main():
    print("Ring Buffer Examples")
    print()
    
    demo_basic_operations()
    demo_wraparound()
    demo_message_queue()
    
    print("\n" + "=" * 50)
    print("All demos completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
