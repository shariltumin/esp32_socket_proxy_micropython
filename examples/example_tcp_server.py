# example_tcp_server.py
from pico_client import BridgeClient, ProxySocket
import gc

def tcp_server_example(host, port=8080):
    client = BridgeClient()
    server_sock = ProxySocket(client, typ=ProxySocket.SOCK_STREAM)
    
    try:
        print(f"Binding to port {port}...")
        server_sock.bind((host, port), timeout_s=5)
        
        print(f"Listening on port {port}...")
        server_sock.listen(5, timeout_s=5)
        
        print("Server ready! Waiting for connections...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                print("\nWaiting for connection...")
                conn_sock, addr = server_sock.accept(timeout_s=3600)
                print(f"Connection from {addr}")
                
                data = conn_sock.recv(1024, timeout_s=5)
                if data:
                    print(f"Received: {data}")
                    response = b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello, World!"
                    conn_sock.send(response)
                    print("Response sent")
                
                conn_sock.close()
                gc.collect()
                
            except OSError as e:
                print(f"Accept timeout or error: {e}")
                
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_sock.close()
        gc.collect()

def main():
    print("=" * 50)
    print("TCP Server Example")
    print("=" * 50)
    print("This example creates a simple HTTP server")
    print("Test with: curl http://<esp32-ip>:8080")
    print("=" * 50)
    
    host = "192.168.4.87" # the IP of ESP32 proxy
    port = 8080
    tcp_server_example(host, port)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
