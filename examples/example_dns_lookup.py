# example_dns_lookup.py
from pico_client import BridgeClient, getaddrinfo
import gc

def dns_lookup(hostname, port=80):
    print(f"Looking up {hostname}...")
    
    client = BridgeClient()
    
    try:
        addresses = getaddrinfo(client, hostname, port)
        
        print(f"\nFound {len(addresses)} address(es):")
        for i, addr_info in enumerate(addresses, 1):
            family, socktype, proto, canonname, sockaddr = addr_info
            print(f"\n  Address {i}:")
            print(f"    Family: {family}")
            print(f"    Type: {socktype}")
            print(f"    Protocol: {proto}")
            print(f"    Canonical name: {canonname}")
            print(f"    Socket address: {sockaddr}")
        
        return addresses
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        gc.collect()

def main():
    print("=" * 50)
    print("DNS Lookup Example")
    print("=" * 50)
    
    hostnames = [
        "example.com",
        "google.com",
        "github.com",
    ]
    
    for hostname in hostnames:
        print()
        dns_lookup(hostname)
        print("-" * 50)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
