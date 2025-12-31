# example_udp_client.py
from pico_client import BridgeClient, ProxySocket
import gc

def udp_client_example(host, port, message):
    client = BridgeClient()
    sock = ProxySocket(client, typ=ProxySocket.SOCK_DGRAM)
    
    try:
        print(f"Sending UDP message to {host}:{port}...")
        sent = sock.sendto(message.encode(), (host, port))
        print(f"Sent {sent} bytes")
        
        print("Waiting for response...")
        data, addr = sock.recvfrom(1024, timeout_s=5)
        print(f"Received from {addr}: {data.decode()}")
        
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()
        gc.collect()

def main():
    print("=" * 50)
    print("UDP Client Example")
    print("=" * 50)
    print("This example sends a UDP message and waits for response")
    print("Test with: nc -u -l 5000 (on Linux/Mac)")
    print("=" * 50)
    
    host = "192.168.1.100"
    port = 5000
    message = "Hello UDP Server!"
    
    udp_client_example(host, port, message)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
