# example_http_get.py
from pico_client import BridgeClient, ProxySocket
import gc

def http_get(host, path="/", port=80):
    client = BridgeClient()
    sock = ProxySocket(client)
    
    try:
        print(f"Connecting to {host}:{port}...")
        sock.connect((host, port), timeout_s=10)
        print("Connected!")
        
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        print(f"Sending request...")
        sock.send(request.encode())
        
        print("Receiving response...")
        response = bytearray()
        chunk_count = 0
        
        while True:
            chunk = sock.recv(512, timeout_s=5)
            if not chunk:
                break
            response.extend(chunk)
            chunk_count += 1
            print(f"  Chunk {chunk_count}: {len(chunk)} bytes (total: {len(response)})")
            
            if len(response) > 4096:
                print("  Limiting response to 4KB")
                break
        
        print(f"\nTotal received: {len(response)} bytes")
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        sock.close()
        gc.collect()

def main():
    print("=" * 50)
    print("HTTP GET Example")
    print("=" * 50)
    
    response = http_get("example.com", "/")
    
    if response:
        print("\n" + "=" * 50)
        print("Response Preview (first 500 chars):")
        print("=" * 50)
        try:
            # text = response.decode('utf-8', errors='ignore')
            text = response.decode('utf-8')
            print(text[:500])
        except:
            print("Could not decode response")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
