"""
Threat Intelligence Integration Service.
Enriches events with data from multiple threat intelligence sources.

Sources:
1. IP Reputation (AbuseIPDB, Shodan)
2. Domain Intelligence (URLhaus, Phishtank)
3. Hash Matching (VirusTotal, YARA)
4. GeoIP Enrichment (MaxMind GeoIP2)
5. Threat Feeds (MISP, OTX, CERTS)
6. Custom YARA Rules
"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import re

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class ThreatIntel:
    """Threat intelligence enrichment result"""
    source: str  # Data source
    threat_level: ThreatLevel
    confidence: float  # 0-1
    details: Dict[str, Any]
    timestamp: datetime
    ttl: int  # Time to live in seconds


@dataclass
class EnrichedEvent:
    """Event enriched with threat intelligence"""
    event_id: str
    original_data: Dict[str, Any]
    threat_intel: List[ThreatIntel]
    is_known_threat: bool
    aggregated_threat_level: ThreatLevel
    enrichment_score: float  # 0-1


class IPReputationChecker:
    """IP reputation checking from multiple sources"""
    
    def __init__(self):
        """Initialize IP reputation checker"""
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour
    
    async def check_ip(self, ip: str) -> Optional[ThreatIntel]:
        """
        Check IP reputation across sources.
        
        Args:
            ip: IP address to check
            
        Returns:
            ThreatIntel or None
        """
        try:
            # Check cache first
            if ip in self.cache:
                cached_data, timestamp = self.cache[ip]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_data
            
            # Simulate checking multiple sources
            threat_level = await self._analyze_ip(ip)
            
            intel = ThreatIntel(
                source='IP_REPUTATION',
                threat_level=threat_level,
                confidence=0.85,
                details={
                    'ip': ip,
                    'is_vpn': await self._is_vpn(ip),
                    'is_proxy': await self._is_proxy(ip),
                    'is_datacenter': await self._is_datacenter(ip),
                    'abuse_reports': await self._get_abuse_reports(ip),
                    'last_seen': datetime.now().isoformat()
                },
                timestamp=datetime.now(),
                ttl=3600
            )
            
            # Cache result
            self.cache[ip] = (intel, datetime.now())
            
            return intel
        except Exception as e:
            logger.warning(f"IP reputation check failed for {ip}: {e}")
            return None
    
    async def _analyze_ip(self, ip: str) -> ThreatLevel:
        """Analyze IP threat level"""
        # Private IP ranges
        if ip.startswith(('192.168.', '10.', '172.')):
            return ThreatLevel.LOW
        
        # Known malicious patterns (stub for real API calls)
        malicious_patterns = [
            r'^1\.179\.',  # Known C2 range
            r'^185\.220\.',  # Tor exit node range
        ]
        
        for pattern in malicious_patterns:
            if re.match(pattern, ip):
                return ThreatLevel.CRITICAL
        
        return ThreatLevel.UNKNOWN
    
    async def _is_vpn(self, ip: str) -> bool:
        """Check if IP is VPN"""
        # Would call real API
        return False
    
    async def _is_proxy(self, ip: str) -> bool:
        """Check if IP is proxy"""
        # Would call real API
        return False
    
    async def _is_datacenter(self, ip: str) -> bool:
        """Check if IP is datacenter"""
        # Would call real API
        return False
    
    async def _get_abuse_reports(self, ip: str) -> int:
        """Get abuse report count"""
        # Would call real API
        return 0


class DomainIntelligence:
    """Domain and URL threat intelligence"""
    
    def __init__(self):
        """Initialize domain intelligence checker"""
        self.cache = {}
        self.cache_ttl = 3600
    
    async def check_domain(self, domain: str) -> Optional[ThreatIntel]:
        """
        Check domain/URL reputation.
        
        Args:
            domain: Domain or URL to check
            
        Returns:
            ThreatIntel or None
        """
        try:
            # Check cache
            if domain in self.cache:
                cached_data, timestamp = self.cache[domain]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_data
            
            threat_level = await self._analyze_domain(domain)
            
            intel = ThreatIntel(
                source='DOMAIN_INTEL',
                threat_level=threat_level,
                confidence=0.80,
                details={
                    'domain': domain,
                    'is_phishing': threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH],
                    'is_malware_host': threat_level == ThreatLevel.CRITICAL,
                    'url_reputation': 'MALICIOUS' if threat_level == ThreatLevel.CRITICAL else 'UNKNOWN',
                    'detected_by': 'Phishtank/URLhaus',
                    'last_checked': datetime.now().isoformat()
                },
                timestamp=datetime.now(),
                ttl=3600
            )
            
            self.cache[domain] = (intel, datetime.now())
            return intel
        except Exception as e:
            logger.warning(f"Domain check failed for {domain}: {e}")
            return None
    
    async def _analyze_domain(self, domain: str) -> ThreatLevel:
        """Analyze domain threat level"""
        # Known phishing domains (stub)
        phishing_domains = [
            'suspicious-login-verify.com',
            'confirm-account-security.net',
            'update-password-required.org'
        ]
        
        if any(domain.lower().endswith(d) for d in phishing_domains):
            return ThreatLevel.CRITICAL
        
        # Suspicious patterns
        if 'verify' in domain.lower() and 'login' in domain.lower():
            return ThreatLevel.HIGH
        
        return ThreatLevel.UNKNOWN


class FileHashMatcher:
    """Hash-based threat detection (malware, exploits)"""
    
    def __init__(self):
        """Initialize hash matcher"""
        self.malware_hashes = set()  # Would load from VirusTotal, etc.
        self.yara_rules = []  # Would load YARA rules
    
    async def match_hash(self, file_hash: str, hash_type: str = 'sha256') -> Optional[ThreatIntel]:
        """
        Match file hash against threat database.
        
        Args:
            file_hash: Hash of file
            hash_type: Type of hash (md5, sha1, sha256)
            
        Returns:
            ThreatIntel or None if no match
        """
        try:
            # Check against known malware
            if file_hash.lower() in self.malware_hashes:
                return ThreatIntel(
                    source='HASH_MATCH',
                    threat_level=ThreatLevel.CRITICAL,
                    confidence=0.99,
                    details={
                        'hash': file_hash,
                        'hash_type': hash_type,
                        'threat': 'Known malware/exploit',
                        'sources': ['VirusTotal', 'Malshare']
                    },
                    timestamp=datetime.now(),
                    ttl=86400  # 24 hours
                )
            
            return None
        except Exception as e:
            logger.warning(f"Hash match failed: {e}")
            return None


class GeoIPEnricher:
    """Geographic IP enrichment"""
    
    def __init__(self):
        """Initialize GeoIP enricher"""
        self.cache = {}
        self.cache_ttl = 86400  # 24 hours
    
    async def enrich_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Enrich IP with geographic data.
        
        Args:
            ip: IP address
            
        Returns:
            Geographic data dictionary
        """
        try:
            if ip in self.cache:
                cached_data, timestamp = self.cache[ip]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_data
            
            # Simulate GeoIP lookup
            geo_data = await self._lookup_geoip(ip)
            self.cache[ip] = (geo_data, datetime.now())
            return geo_data
        except Exception as e:
            logger.warning(f"GeoIP enrichment failed: {e}")
            return None
    
    async def _lookup_geoip(self, ip: str) -> Dict[str, Any]:
        """Simulate GeoIP lookup"""
        # Would call real GeoIP2 API
        return {
            'country': 'US',
            'country_code': 'US',
            'region': 'California',
            'city': 'San Francisco',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'timezone': 'America/Los_Angeles',
            'isp': 'Unknown ISP'
        }


class YARAEngine:
    """YARA rule-based threat detection"""
    
    def __init__(self):
        """Initialize YARA engine"""
        self.rules = {}  # Would load actual YARA rules
    
    async def scan_data(self, data: str) -> List[Dict[str, Any]]:
        """
        Scan data against YARA rules.
        
        Args:
            data: Data to scan
            
        Returns:
            List of rule matches
        """
        try:
            matches = []
            
            # Simulate YARA scanning
            if 'malware' in data.lower():
                matches.append({
                    'rule_name': 'Malware_Indicator',
                    'category': 'malware',
                    'severity': 'CRITICAL'
                })
            
            if 'cmd.exe' in data.lower():
                matches.append({
                    'rule_name': 'Command_Execution',
                    'category': 'execution',
                    'severity': 'HIGH'
                })
            
            return matches
        except Exception as e:
            logger.warning(f"YARA scan failed: {e}")
            return []


class ThreatIntelService:
    """Complete threat intelligence service"""
    
    def __init__(self):
        """Initialize threat intelligence service"""
        self.ip_checker = IPReputationChecker()
        self.domain_checker = DomainIntelligence()
        self.hash_matcher = FileHashMatcher()
        self.geoip_enricher = GeoIPEnricher()
        self.yara_engine = YARAEngine()
        self.enrichment_cache = {}
    
    async def enrich_event(self, event: Dict[str, Any]) -> EnrichedEvent:
        """
        Enrich event with threat intelligence.
        
        Args:
            event: Event to enrich
            
        Returns:
            EnrichedEvent with threat intel
        """
        try:
            threat_intel_list = []
            
            # Check IP reputation
            source_ip = event.get('source_ip')
            if source_ip:
                ip_intel = await self.ip_checker.check_ip(source_ip)
                if ip_intel:
                    threat_intel_list.append(ip_intel)
            
            # Check domain
            domain = event.get('domain')
            if domain:
                domain_intel = await self.domain_checker.check_domain(domain)
                if domain_intel:
                    threat_intel_list.append(domain_intel)
            
            # Check file hash
            file_hash = event.get('file_hash')
            if file_hash:
                hash_intel = await self.hash_matcher.match_hash(file_hash)
                if hash_intel:
                    threat_intel_list.append(hash_intel)
            
            # GeoIP enrichment
            if source_ip:
                geo_data = await self.geoip_enricher.enrich_ip(source_ip)
                if geo_data and event.get('source_ip'):
                    event['geo_location'] = geo_data
            
            # YARA scan
            event_str = json.dumps(event)
            yara_matches = await self.yara_engine.scan_data(event_str)
            if yara_matches:
                logger.info(f"YARA matches found: {yara_matches}")
            
            # Aggregate threat level
            threat_levels = [t.threat_level for t in threat_intel_list]
            if ThreatLevel.CRITICAL in threat_levels:
                aggregated_level = ThreatLevel.CRITICAL
            elif ThreatLevel.HIGH in threat_levels:
                aggregated_level = ThreatLevel.HIGH
            elif ThreatLevel.MEDIUM in threat_levels:
                aggregated_level = ThreatLevel.MEDIUM
            elif ThreatLevel.LOW in threat_levels:
                aggregated_level = ThreatLevel.LOW
            else:
                aggregated_level = ThreatLevel.UNKNOWN
            
            # Calculate enrichment score
            enrichment_score = len(threat_intel_list) / 5.0  # Max 5 intel sources
            enrichment_score = min(1.0, enrichment_score)
            
            return EnrichedEvent(
                event_id=event.get('id', 'unknown'),
                original_data=event,
                threat_intel=threat_intel_list,
                is_known_threat=aggregated_level != ThreatLevel.UNKNOWN,
                aggregated_threat_level=aggregated_level,
                enrichment_score=enrichment_score
            )
        except Exception as e:
            logger.error(f"Event enrichment failed: {e}")
            return EnrichedEvent(
                event_id=event.get('id', 'unknown'),
                original_data=event,
                threat_intel=[],
                is_known_threat=False,
                aggregated_threat_level=ThreatLevel.UNKNOWN,
                enrichment_score=0.0
            )


# Global threat intelligence service instance
threat_intel_service = ThreatIntelService()
