import feedparser
import requests
import json
import datetime
import os
import time
import hashlib

INTEL_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'threat_intel.log')
NEWS_CACHE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'news_cache.json')

# ═══════════════════════════════════════════
# FREE THREAT INTELLIGENCE FEEDS
# ═══════════════════════════════════════════
THREAT_FEEDS = {
    "hacking_news": [
        "https://feeds.feedburner.com/TheHackersNews",
        "https://www.bleepingcomputer.com/feed/",
        "https://feeds.feedburner.com/securityweek",
        "https://www.darkreading.com/rss.xml",
        "https://threatpost.com/feed/",
        "https://www.cybersecuritydive.com/feeds/news/",
    ],
    "india_cyber": [
        "https://www.cert-in.org.in/RSS/CERTInAlerts.rss",
        "https://indianexpress.com/section/technology/cyber-crime/feed/",
    ],
    "exploit_db": [
        "https://www.exploit-db.com/rss.xml",
    ],
    "vulnerability": [
        "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
        "https://www.cvedetails.com/vulnerability-feed.php?vendor_id=0&product_id=0&version_id=0&hasexp=0&opec=0&opov=0&opcsrf=0&opfileinc=0&opgpriv=0&opsqli=0&opxss=0&opdirt=0&opmemc=0&ophttpr=0&opbyp=0&opginf=0&opdos=0&orderby=3&cvssscoremin=0",
    ]
}

def check_ip_full(ip):
    """
    Complete IP intelligence check.
    Combines multiple free sources like a real threat analyst.
    """
    intel = {
        "ip": ip,
        "timestamp": datetime.datetime.now().isoformat(),
        "geolocation": {},
        "reputation": {},
        "network_info": {},
        "verdict": "UNKNOWN",
        "risk_score": 0,
        "is_vpn": False,
        "is_tor": False,
        "is_proxy": False,
        "threat_tags": []
    }

    # Skip local
    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
        intel["verdict"] = "LOCAL_NETWORK"
        return intel

    # Source 1 — IP-API (free, no key needed)
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,hosting,query", timeout=5)
        data = r.json()
        if data.get('status') == 'success':
            intel["geolocation"] = {
                "country": data.get('country', ''),
                "country_code": data.get('countryCode', ''),
                "region": data.get('regionName', ''),
                "city": data.get('city', ''),
                "lat": data.get('lat', 0),
                "lon": data.get('lon', 0),
                "timezone": data.get('timezone', ''),
                "isp": data.get('isp', ''),
                "org": data.get('org', ''),
            }
            intel["is_proxy"] = data.get('proxy', False)
            intel["is_vpn"] = data.get('hosting', False)

            if intel["is_proxy"]:
                intel["threat_tags"].append("PROXY")
                intel["risk_score"] += 20
            if intel["is_vpn"]:
                intel["threat_tags"].append("VPN/HOSTING")
                intel["risk_score"] += 15
    except Exception as e:
        pass

    # Source 2 — Check against known Tor exit nodes
    try:
        tor_check = requests.get(f"https://check.torproject.org/torbulkexitlist", timeout=5)
        if ip in tor_check.text:
            intel["is_tor"] = True
            intel["threat_tags"].append("TOR_EXIT_NODE")
            intel["risk_score"] += 40
    except:
        pass

    # Source 3 — IPQualityScore free check
    try:
        r = requests.get(
            f"https://ipqualityscore.com/api/json/ip/YOUR_FREE_KEY/{ip}",
            timeout=5
        )
        data = r.json()
        if data.get('success'):
            if data.get('fraud_score', 0) > 75:
                intel["threat_tags"].append("HIGH_FRAUD_SCORE")
                intel["risk_score"] += 30
            if data.get('bot_status'):
                intel["threat_tags"].append("BOT")
                intel["risk_score"] += 25
            if data.get('recent_abuse'):
                intel["threat_tags"].append("RECENT_ABUSE")
                intel["risk_score"] += 20
    except:
        pass

    # Final verdict
    if intel["risk_score"] >= 70:
        intel["verdict"] = "MALICIOUS"
    elif intel["risk_score"] >= 40:
        intel["verdict"] = "SUSPICIOUS"
    elif intel["risk_score"] >= 20:
        intel["verdict"] = "MODERATE_RISK"
    else:
        intel["verdict"] = "CLEAN"

    return intel

def check_domain_full(domain):
    """
    Complete domain intelligence.
    Checks reputation, age, DNS, blacklists.
    """
    intel = {
        "domain": domain,
        "timestamp": datetime.datetime.now().isoformat(),
        "verdict": "UNKNOWN",
        "risk_score": 0,
        "threat_tags": [],
        "dns_records": {},
        "blacklisted": False
    }

    # Check DNS
    try:
        r = requests.get(f"https://dns.google/resolve?name={domain}&type=A", timeout=5)
        data = r.json()
        if data.get('Status') == 0:
            answers = data.get('Answer', [])
            intel["dns_records"]["A"] = [a.get('data') for a in answers]
            intel["resolves"] = True
        else:
            intel["resolves"] = False
            intel["threat_tags"].append("DOES_NOT_RESOLVE")
    except:
        pass

    # Check MX records (phishing domains often have no MX)
    try:
        r = requests.get(f"https://dns.google/resolve?name={domain}&type=MX", timeout=5)
        data = r.json()
        intel["dns_records"]["MX"] = len(data.get('Answer', [])) > 0
    except:
        pass

    # Check against Google Safe Browsing
    try:
        r = requests.post(
            "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=YOUR_KEY",
            json={
                "client": {"clientId": "maya", "clientVersion": "1.0"},
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": f"http://{domain}"}]
                }
            },
            timeout=5
        )
        if r.json().get('matches'):
            intel["blacklisted"] = True
            intel["threat_tags"].append("GOOGLE_SAFE_BROWSING_HIT")
            intel["risk_score"] += 80
    except:
        pass

    # Final verdict
    if intel["risk_score"] >= 70:
        intel["verdict"] = "MALICIOUS"
    elif intel["risk_score"] >= 40:
        intel["verdict"] = "SUSPICIOUS"
    else:
        intel["verdict"] = "CLEAN"

    return intel

def fetch_threat_news():
    """
    Fetch latest cybersecurity news from multiple sources.
    Real-time threat intelligence from:
    - The Hacker News
    - BleepingComputer
    - Dark Reading
    - SecurityWeek
    - Exploit-DB
    - NVD CVE feed
    - CERT-In India alerts
    """
    all_news = []
    
    for category, feeds in THREAT_FEEDS.items():
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    news_item = {
                        "category": category,
                        "title": entry.get('title', ''),
                        "summary": entry.get('summary', '')[:300],
                        "link": entry.get('link', ''),
                        "published": entry.get('published', ''),
                        "source": feed.feed.get('title', feed_url),
                        "fetched_at": datetime.datetime.now().isoformat()
                    }
                    all_news.append(news_item)
                    print(f"[INTEL] {category} | {news_item['title'][:60]}...")
            except Exception as e:
                pass

    # Save to cache
    with open(NEWS_CACHE, 'w') as f:
        json.dump(all_news, f, indent=2)

    print(f"\n[INTEL] Fetched {len(all_news)} threat intelligence items")
    return all_news

def get_upi_threats():
    """
    Specifically monitor for UPI and Indian payment fraud.
    """
    upi_feeds = [
        "https://www.rbi.org.in/rss/RBINotifications.aspx",
        "https://www.npci.org.in/rss-feeds",
    ]
    
    upi_threats = []
    keywords = ['upi', 'payment fraud', 'india bank', 'phishing india', 
                'cyber fraud india', 'sim swap', 'qr code fraud']
    
    for feed_url in upi_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                if any(kw in title or kw in summary for kw in keywords):
                    upi_threats.append({
                        "title": entry.get('title', ''),
                        "summary": entry.get('summary', '')[:200],
                        "link": entry.get('link', ''),
                        "source": feed.feed.get('title', ''),
                        "relevance": "UPI_FRAUD"
                    })
        except:
            pass

    return upi_threats

def run_continuous_intel():
    """
    Continuously fetch threat intelligence.
    Updates every 30 minutes.
    MAYA stays up to date with every new threat.
    """
    print("[INTEL] MAYA Threat Intelligence Engine started")
    print("[INTEL] Fetching from: Hacker News, BleepingComputer, Dark Reading,")
    print("[INTEL]                SecurityWeek, Exploit-DB, NVD CVE, CERT-In")
    print("[INTEL] Updating every 30 minutes")
    print("-" * 60)

    while True:
        print(f"\n[INTEL] Fetching latest threat intelligence...")
        news = fetch_threat_news()
        upi = get_upi_threats()
        
        print(f"[INTEL] {len(news)} global threats | {len(upi)} UPI threats found")
        print(f"[INTEL] Next update in 30 minutes...")
        
        time.sleep(1800)  # 30 minutes

if __name__ == "__main__":
    print("[INTEL] Testing MAYA Threat Intelligence Engine...")
    print("\n[INTEL] Checking IP reputation...")
    result = check_ip_full("8.8.8.8")
    print(json.dumps(result, indent=2))
    
    print("\n[INTEL] Fetching latest threat news...")
    news = fetch_threat_news()
    print(f"\n[INTEL] Latest threats:")
    for item in news[:5]:
        print(f"  [{item['category']}] {item['title'][:70]}")
