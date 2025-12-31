# example_tcp_echo.py
from pico_client import BridgeClient, ProxySocket
import gc

def tcp_echo_test(host, port, message):
    client = BridgeClient()
    sock = ProxySocket(client)
    
    try:
        print(f"Connecting to {host}:{port}...")
        sock.connect((host, port), timeout_s=10)
        print("Connected!")
        
        print(f"Sending: {message}")
        sock.send(message.encode())
        
        print("Receiving echo...")
        response = sock.recv(1024, timeout_s=5)
        
        if response:
            print(f"Received: {response.decode()}")
            return response
        else:
            print("No response received")
            return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()
        gc.collect()

def main():
    print("=" * 50)
    print("TCP Echo Example")
    print("=" * 50)
    print("Note: This requires an echo server running")
    print("You can use: nc -l 7777 (on Linux/Mac)")
    print("=" * 50)
    
    host = "192.168.4.27" # use ifconfig -a to get Linux server IP
    port = 7777
    message = "Hello from Pico!"
    
    tcp_echo_test(host, port, message)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
