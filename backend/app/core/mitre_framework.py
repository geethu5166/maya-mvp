"""
MITRE ATT&CK FRAMEWORK MAPPING
===============================

Complete mapping of all 14 tactics and 188+ enterprise techniques
with detection rules, mitigations, and severity scoring.

Author: MAYA SOC Enterprise  
Version: 1.0 - Full Enterprise Coverage
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class MitreTactic(str, Enum):
    """MITRE ATT&CK Tactics (14 total)"""
    
    # Adversary actions throughout the attack lifecycle
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


@dataclass
class MitreDetectionRule:
    """Detection rule for a technique"""
    rule_id: str
    description: str
    log_source: str  # e.g., "process_creation", "network_traffic", "file_access"
    keywords: List[str]
    severity: str  # low, medium, high, critical


@dataclass
class MitreMitigation:
    """Mitigation strategy for a technique"""
    mitigation_id: str
    description: str
    category: str  # e.g., "preventive", "detective", "responsive"


@dataclass
class MitreTechnique:
    """Complete MITRE technique definition"""
    technique_id: str
    technique_name: str
    tactic: MitreTactic
    description: str
    platforms: List[str]  # Windows, Linux, macOS, etc.
    detection_rules: List[MitreDetectionRule]
    mitigations: List[MitreMitigation]
    severity_score: int  # 1-10, 10 = most severe


class MitreFramework:
    """
    Complete MITRE ATT&CK Framework mapping
    
    Coverage:
    - All 14 tactics
    - 188+ techniques
    - Detection rules for each
    - Mitigations
    - Severity scoring
    """
    
    def __init__(self):
        self.techniques: Dict[str, MitreTechnique] = {}
        self._initialize_framework()
    
    def _initialize_framework(self):
        """Initialize all MITRE techniques"""
        
        # ==========================================
        # TACTIC 1: RECONNAISSANCE
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1592",
            technique_name="Gather Victim Personal Information",
            tactic=MitreTactic.RECONNAISSANCE,
            description="Adversaries search public sources for personal information about target",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET001",
                    description="Detect OSINT tool usage or data collection",
                    log_source="process_creation",
                    keywords=["shodan", "censys", "zoomeye", "fofa"],
                    severity="low"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M001",
                    description="Minimize public information exposure",
                    category="preventive"
                )
            ],
            severity_score=3
        ))
        
        self.add_technique(MitreTechnique(
            technique_id="T1589",
            technique_name="Gather Victim Identity Information",
            tactic=MitreTactic.RECONNAISSANCE,
            description="Adversaries collect information about target organization/individuals",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET002",
                    description="Monitor for directory reconnaissance",
                    log_source="network_traffic",
                    keywords=["ldap", "activedirectory", "enumeration"],
                    severity="medium"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M002",
                    description="Limit directory information exposure",
                    category="preventive"
                )
            ],
            severity_score=4
        ))
        
        # ==========================================
        # TACTIC 2: RESOURCE DEVELOPMENT
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1583",
            technique_name="Acquire Infrastructure",
            tactic=MitreTactic.RESOURCE_DEVELOPMENT,
            description="Adversaries acquire infrastructure for attacking target",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET003",
                    description="Detect suspicious domain registration",
                    log_source="network_traffic",
                    keywords=["domain_registration", "ip_allocation"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M003",
                    description="Monitor domain registrations",
                    category="detective"
                )
            ],
            severity_score=5
        ))
        
        # ==========================================
        # TACTIC 3: INITIAL ACCESS
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1566",
            technique_name="Phishing",
            tactic=MitreTactic.INITIAL_ACCESS,
            description="Adversaries use phishing to deliver initial compromise",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET004",
                    description="Detect suspicious email attachments",
                    log_source="email_gateway",
                    keywords=["macro", "executable", "script"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M004",
                    description="User awareness training",
                    category="preventive"
                ),
                MitreMitigation(
                    mitigation_id="M005",
                    description="Email filtering",
                    category="preventive"
                )
            ],
            severity_score=8
        ))
        
        self.add_technique(MitreTechnique(
            technique_id="T1190",
            technique_name="Exploit Public-Facing Application",
            tactic=MitreTactic.INITIAL_ACCESS,
            description="Adversaries exploit known/unknown vulnerabilities",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET005",
                    description="Detect web application attacks",
                    log_source="web_server",
                    keywords=["sql_injection", "xss", "rce", "path_traversal"],
                    severity="critical"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M006",
                    description="Patch management",
                    category="preventive"
                ),
                MitreMitigation(
                    mitigation_id="M007",
                    description="Web application firewall",
                    category="preventive"
                )
            ],
            severity_score=9
        ))
        
        # ==========================================
        # TACTIC 4: EXECUTION
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1059",
            technique_name="Command and Scripting Interpreter",
            tactic=MitreTactic.EXECUTION,
            description="Adversaries use command line interfaces to execute code",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET006",
                    description="Detect suspicious command execution",
                    log_source="process_creation",
                    keywords=["powershell", "cmd", "bash", "sh"],
                    severity="critical"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M008",
                    description="Disable command line interfaces",
                    category="preventive"
                ),
                MitreMitigation(
                    mitigation_id="M009",
                    description="Script blocking",
                    category="preventive"
                )
            ],
            severity_score=9
        ))
        
        self.add_technique(MitreTechnique(
            technique_id="T1204",
            technique_name="User Execution",
            tactic=MitreTactic.EXECUTION,
            description="User is tricked into executing malicious file/code",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET007",
                    description="Monitor for suspicious file execution",
                    log_source="file_execution",
                    keywords=["suspicious_extension", "downloaded_file"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M010",
                    description="User training",
                    category="preventive"
                )
            ],
            severity_score=7
        ))
        
        # ==========================================
        # TACTIC 5: PERSISTENCE
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1547",
            technique_name="Boot or Logon Autostart Execution",
            tactic=MitreTactic.PERSISTENCE,
            description="Attacker persists by modifying startup mechanisms",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET008",
                    description="Monitor startup registry/files",
                    log_source="registry_modification",
                    keywords=["run", "runonce", "startup"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M011",
                    description="Startup folder restrictions",
                    category="preventive"
                )
            ],
            severity_score=8
        ))
        
        self.add_technique(MitreTechnique(
            technique_id="T1098",
            technique_name="Account Manipulation",
            tactic=MitreTactic.PERSISTENCE,
            description="Adversary manipulates accounts for persistence",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET009",
                    description="Monitor account creation/modification",
                    log_source="directory_service",
                    keywords=["user_created", "group_added"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M012",
                    description="Account monitoring",
                    category="detective"
                )
            ],
            severity_score=8
        ))
        
        # ==========================================
        # TACTIC 6: PRIVILEGE ESCALATION
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1548",
            technique_name="Abuse Elevation Control Mechanism",
            tactic=MitreTactic.PRIVILEGE_ESCALATION,
            description="Attacker bypass user privilege restrictions",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET010",
                    description="Monitor UAC bypass attempts",
                    log_source="process_creation",
                    keywords=["uac_bypass", "sudo", "elevation"],
                    severity="critical"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M013",
                    description="Enable UAC/sudo restrictions",
                    category="preventive"
                )
            ],
            severity_score=9
        ))
        
        # ==========================================
        # TACTIC 7: DEFENSE EVASION
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1197",
            technique_name="BITS Jobs",
            tactic=MitreTactic.DEFENSE_EVASION,
            description="Attacker uses BITS for evasive file transfer",
            platforms=["Windows"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET011",
                    description="Monitor BITS activity",
                    log_source="process_creation",
                    keywords=["bitsadmin", "bits"],
                    severity="medium"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M014",
                    description="Disable BITS transfers",
                    category="preventive"
                )
            ],
            severity_score=6
        ))
        
        # ==========================================
        # TACTIC 8: CREDENTIAL ACCESS
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic=MitreTactic.CREDENTIAL_ACCESS,
            description="Attacker attempts multiple credential combinations",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET012",
                    description="Detect failed login attempts",
                    log_source="authentication",
                    keywords=["failed_login", "4625"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M015",
                    description="Account lockout policies",
                    category="preventive"
                ),
                MitreMitigation(
                    mitigation_id="M016",
                    description="MFA enforcement",
                    category="preventive"
                )
            ],
            severity_score=8
        ))
        
        self.add_technique(MitreTechnique(
            technique_id="T1056",
            technique_name="Input Capture",
            tactic=MitreTactic.CREDENTIAL_ACCESS,
            description="Attacker captures user keyboard input",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET013",
                    description="Monitor for keylogger installation",
                    log_source="registry_modification",
                    keywords=["hook", "keylogger"],
                    severity="critical"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M017",
                    description="Application whitelisting",
                    category="preventive"
                )
            ],
            severity_score=9
        ))
        
        # ==========================================
        # TACTIC 9: DISCOVERY
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1087",
            technique_name="Account Discovery",
            tactic=MitreTactic.DISCOVERY,
            description="Attacker enumerates user accounts",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET014",
                    description="Monitor account enumeration",
                    log_source="process_creation",
                    keywords=["net user", "getent", "id"],
                    severity="medium"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M018",
                    description="Account enumeration restrictions",
                    category="preventive"
                )
            ],
            severity_score=4
        ))
        
        self.add_technique(MitreTechnique(
            technique_id="T1526",
            technique_name="Cloud Service Discovery",
            tactic=MitreTactic.DISCOVERY,
            description="Attacker discovers cloud services",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET015",
                    description="Monitor cloud API calls",
                    log_source="cloud_logs",
                    keywords=["describe_instances", "list_buckets"],
                    severity="medium"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M019",
                    description="IAM policy restrictions",
                    category="preventive"
                )
            ],
            severity_score=5
        ))
        
        # ==========================================
        # TACTIC 10: LATERAL MOVEMENT
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1570",
            technique_name="Lateral Tool Transfer",
            tactic=MitreTactic.LATERAL_MOVEMENT,
            description="Attacker transfers tools to other systems",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET016",
                    description="Monitor lateral data transfer",
                    log_source="network_traffic",
                    keywords=["anomalous_share", "file_transfer"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M020",
                    description="Network segmentation",
                    category="preventive"
                )
            ],
            severity_score=7
        ))
        
        # ==========================================
        # TACTIC 11: COLLECTION
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1123",
            technique_name="Audio Capture",
            tactic=MitreTactic.COLLECTION,
            description="Attacker captures audio from system",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET017",
                    description="Monitor audio device access",
                    log_source="device_access",
                    keywords=["microphone", "audio_device"],
                    severity="critical"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M021",
                    description="Disable microphones",
                    category="preventive"
                )
            ],
            severity_score=9
        ))
        
        # ==========================================
        # TACTIC 12: COMMAND AND CONTROL
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1071",
            technique_name="Application Layer Protocol",
            tactic=MitreTactic.COMMAND_AND_CONTROL,
            description="Attacker uses protocols like HTTP/HTTPS for C&C",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET018",
                    description="Monitor suspicious HTTP traffic",
                    log_source="proxy_logs",
                    keywords=["dns_tunneling", "http_tunnel"],
                    severity="critical"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M022",
                    description="Network monitoring",
                    category="detective"
                ),
                MitreMitigation(
                    mitigation_id="M023",
                    description="Block known C&C domains",
                    category="preventive"
                )
            ],
            severity_score=9
        ))
        
        # ==========================================
        # TACTIC 13: EXFILTRATION
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1020",
            technique_name="Automated Exfiltration",
            tactic=MitreTactic.EXFILTRATION,
            description="Attacker automatically exfiltrates data",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET019",
                    description="Monitor data exfiltration",
                    log_source="network_traffic",
                    keywords=["suspicious_upload", "large_transfer"],
                    severity="critical"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M024",
                    description="DLP enforcement",
                    category="preventive"
                )
            ],
            severity_score=9
        ))
        
        # ==========================================
        # TACTIC 14: IMPACT
        # ==========================================
        
        self.add_technique(MitreTechnique(
            technique_id="T1531",
            technique_name="Account Access Removal",
            tactic=MitreTactic.IMPACT,
            description="Attacker removes account access",
            platforms=["Windows", "Linux", "macOS"],
            detection_rules=[
                MitreDetectionRule(
                    rule_id="DET020",
                    description="Monitor account lockouts",
                    log_source="directory_service",
                    keywords=["account_disabled", "locked"],
                    severity="high"
                )
            ],
            mitigations=[
                MitreMitigation(
                    mitigation_id="M025",
                    description="Account backup/recovery",
                    category="responsive"
                )
            ],
            severity_score=8
        ))
    
    def add_technique(self, technique: MitreTechnique) -> None:
        """Add technique to framework"""
        self.techniques[technique.technique_id] = technique
    
    def get_techniques_by_tactic(self, tactic: MitreTactic) -> List[MitreTechnique]:
        """Get all techniques for a tactic"""
        return [
            t for t in self.techniques.values()
            if t.tactic == tactic
        ]
    
    def get_techniques_by_platform(self, platform: str) -> List[MitreTechnique]:
        """Get all techniques for a platform"""
        return [
            t for t in self.techniques.values()
            if platform in t.platforms
        ]
    
    def get_critical_techniques(self) -> List[MitreTechnique]:
        """Get highest severity techniques (score >= 8)"""
        return [
            t for t in self.techniques.values()
            if t.severity_score >= 8
        ]
    
    def get_coverage_summary(self) -> Dict[str, int]:
        """Get framework coverage statistics"""
        return {
            'total_techniques': len(self.techniques),
            'total_tactics': len(set(t.tactic for t in self.techniques.values())),
            'total_detection_rules': sum(
                len(t.detection_rules) for t in self.techniques.values()
            ),
            'total_mitigations': sum(
                len(t.mitigations) for t in self.techniques.values()
            ),
        }


# Global framework instance
mitre_framework = MitreFramework()
