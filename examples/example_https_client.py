# example_https_client.py
from pico_client import BridgeClient, ProxySocket
import gc

def https_request(host, path="/"):
    client = BridgeClient()
    sock = ProxySocket(client)
    
    try:
        print(f"Connecting to {host}:443...")
        sock.connect((host, 443), ssl=True)
        print("Connected!")
        
        print("Wrapping socket with SSL/TLS...")
        sock.wrap_ssl(server_hostname=host)
        print("SSL/TLS connection established!")
        
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        print(f"Sending HTTPS request...")
        sock.send(request.encode())
        
        print("Receiving response...")
        response = bytearray()
        chunks = 0
        while chunks < 10:
            chunk = sock.recv(1024, ssl=True)
            if not chunk:
                break
            response.extend(chunk)
            chunks += 1
            print(f"  Chunk {chunks}: {len(chunk)} bytes")
        
        print(f"\nTotal received: {len(response)} bytes")
        print("\n--- Response Snippet ---")
        print(response[:500].decode('utf-8'))
        
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()
        gc.collect()

def main():
    print("=" * 50)
    print("HTTPS Client Example")
    print("=" * 50)
    print("This example makes an HTTPS request using SSL/TLS")
    print("=" * 50)
    
    host = "www.google.com"
    path = "/"
    
    https_request(host, path)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
