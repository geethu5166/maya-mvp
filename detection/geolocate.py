import requests
import json

def get_location(ip):
    """
    Takes an IP address and returns country,
    city, and coordinates.
    Uses free API - no key needed.
    """
    # Skip private/local IPs
    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.'):
        return {
            "country": "Local Network",
            "city": "Localhost",
            "lat": 17.3850,
            "lon": 78.4867,
            "flag": "IN"
        }
    
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}",
            timeout=5
        )
        data = response.json()
        if data['status'] == 'success':
            return {
                "country": data.get('country', 'Unknown'),
                "city": data.get('city', 'Unknown'),
                "lat": data.get('lat', 0),
                "lon": data.get('lon', 0),
                "flag": data.get('countryCode', '??')
            }
    except:
        pass
    
    return {
        "country": "Unknown",
        "city": "Unknown", 
        "lat": 0,
        "lon": 0,
        "flag": "??"
    }

if __name__ == "__main__":
    # Test with a real IP
    test_ips = ["8.8.8.8", "1.1.1.1", "127.0.0.1"]
    for ip in test_ips:
        loc = get_location(ip)
        print(f"{ip} → {loc['city']}, {loc['country']}")
