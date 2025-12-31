# example_udp_server.py
from pico_client import BridgeClient, ProxySocket
import gc

def udp_server_example(port=5000):
    client = BridgeClient()
    sock = ProxySocket(client, typ=ProxySocket.SOCK_DGRAM)
    
    try:
        print(f"Binding UDP socket to port {port}...")
        sock.bind(("0.0.0.0", port), timeout_s=5)
        
        print(f"UDP server listening on port {port}...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                print("\nWaiting for UDP datagram...")
                data, addr = sock.recvfrom(1024, timeout_s=30)
                print(f"Received from {addr}: {data.decode()}")
                
                response = b"Echo: " + data
                sent = sock.sendto(response, addr)
                print(f"Sent {sent} bytes back to {addr}")
                
                gc.collect()
                
            except OSError as e:
                print(f"Receive timeout or error: {e}")
                
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()
        gc.collect()

def main():
    print("=" * 50)
    print("UDP Server Example")
    print("=" * 50)
    print("This example creates a UDP echo server")
    print("Test with: echo 'test' | nc -u <esp32-ip> 5000")
    print("=" * 50)
    
    udp_server_example(5000)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
