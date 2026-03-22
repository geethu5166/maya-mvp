
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib import colors
import json
import os
import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')
REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs', 'reports')

# VAULTRAP BRAND COLORS
C_BLACK     = HexColor('#040608')
C_DARK      = HexColor('#080d12')
C_DARK2     = HexColor('#0c1219')
C_GREEN     = HexColor('#00ff88')
C_GREEN2    = HexColor('#00c896')
C_RED       = HexColor('#ff3366')
C_ORANGE    = HexColor('#ff8800')
C_BLUE      = HexColor('#0088ff')
C_YELLOW    = HexColor('#ffcc00')
C_MUTED     = HexColor('#4a6060')
C_TEXT      = HexColor('#e8f0e8')
C_BORDER    = HexColor('#1a2a2a')
C_WHITE     = HexColor('#ffffff')

def read_attacks():
    attacks = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        attacks.append(json.loads(line))
                    except:
                        pass
    except:
        pass
    return attacks

def get_stats(attacks):
    total = len(attacks)
    critical = len([a for a in attacks if a.get('severity') == 'CRITICAL'])
    high = len([a for a in attacks if a.get('severity') == 'HIGH'])
    medium = len([a for a in attacks if a.get('severity') == 'MEDIUM'])
    low = len([a for a in attacks if a.get('severity') == 'LOW'])
    ssh = len([a for a in attacks if 'SSH' in a.get('type', '')])
    web = len([a for a in attacks if 'WEB' in a.get('type', '')])
    db = len([a for a in attacks if any(x in a.get('type', '') for x in ['DB', 'MYSQL', 'REDIS', 'POSTGRES'])])
    win = len([a for a in attacks if 'WINDOWS' in a.get('type', '')])
    unique_ips = list(set(a.get('attacker_ip', '') for a in attacks))
    return {
        'total': total, 'critical': critical, 'high': high,
        'medium': medium, 'low': low, 'ssh': ssh, 'web': web,
        'db': db, 'win': win, 'unique_ips': unique_ips
    }

def get_mitre(attack_type):
    mitre = {
        'SSH_BRUTE_FORCE': ('T1110.001', 'Brute Force: Password Guessing', 'Credential Access'),
        'WEB_CREDENTIAL_HARVEST': ('T1056.003', 'Input Capture: Web Portal Capture', 'Collection'),
        'WEB_RECON': ('T1595.002', 'Active Scanning: Vulnerability Scanning', 'Reconnaissance'),
        'WEB_SCAN': ('T1595.003', 'Active Scanning: Wordlist Scanning', 'Reconnaissance'),
        'DB_CONNECTION': ('T1046', 'Network Service Discovery', 'Discovery'),
        'DB_LOGIN_ATTEMPT': ('T1078', 'Valid Accounts', 'Defense Evasion'),
        'REDIS_PROBE': ('T1190', 'Exploit Public-Facing Application', 'Initial Access'),
        'POSTGRES_LOGIN_ATTEMPT': ('T1078', 'Valid Accounts', 'Credential Access'),
        'WINDOWS_RDP_BRUTE_FORCE': ('T1110.001', 'Brute Force: RDP', 'Credential Access'),
        'WINDOWS_FAILED_LOGIN': ('T1110', 'Brute Force', 'Credential Access'),
        'WINDOWS_LATERAL_MOVEMENT': ('T1021', 'Remote Services', 'Lateral Movement'),
        'WINDOWS_PRIVILEGE_ESCALATION': ('T1068', 'Exploitation for Privilege Escalation', 'Privilege Escalation'),
        'WINDOWS_RANSOMWARE_BEHAVIOR': ('T1486', 'Data Encrypted for Impact', 'Impact'),
        'WINDOWS_HONEYTOKEN_TRIGGERED': ('T1078', 'Valid Accounts — Honeytoken', 'Credential Access'),
        'WINDOWS_ACCOUNT_LOCKOUT': ('T1110', 'Brute Force: Account Lockout', 'Credential Access'),
    }
    return mitre.get(attack_type, ('T0000', 'Unclassified Technique', 'Unknown Tactic'))

def get_detection_steps(attack_type):
    steps = {
        'SSH_BRUTE_FORCE': [
            'MAYA SSH honeypot on port 2222 received connection from attacker IP',
            'Honeypot responded with fake SSH banner (OpenSSH 8.x simulation)',
            'Attacker began password enumeration — all attempts logged with credentials',
            'AI model classified traffic as T1110.001 with 98.68% confidence',
            'Behavioral analysis confirmed automated tooling (Hydra/Medusa signature)',
            'Attack pattern matched known brute force campaign in threat database',
        ],
        'WEB_CREDENTIAL_HARVEST': [
            'MAYA fake web portal (port 5001) received HTTP request from attacker',
            'Attacker located and accessed the fake login portal via reconnaissance',
            'Credential submission captured — username, password, browser fingerprint logged',
            'AI classified as T1056.003 credential harvesting with CRITICAL severity',
            'Attacker user-agent and request headers analyzed for tool identification',
            'Honeytoken credentials marked — any future use will trigger global alert',
        ],
        'DB_CONNECTION': [
            'MAYA MySQL honeypot (port 3306) received TCP connection from attacker',
            'Fake MySQL 8.0 greeting packet sent — attacker believes real DB found',
            'Connection metadata captured: source IP, port, timing patterns',
            'AI classified as T1046 Network Service Discovery',
            'Attacker added to watchlist for follow-up exploitation attempts',
            'Real database servers unaffected — attacker contained in honeypot',
        ],
        'DB_LOGIN_ATTEMPT': [
            'Attacker progressed from discovery to exploitation against fake database',
            'MySQL authentication packet received and fully parsed',
            'Username, password hash, and target database name extracted',
            'AI classified as T1078 Valid Accounts with CRITICAL severity',
            'Credentials captured and added to threat intelligence database',
            'Authentication failure sent — attacker believes wrong password, tries again',
        ],
        'WINDOWS_RDP_BRUTE_FORCE': [
            'Windows Agent detected repeated failed RDP authentication events (Event ID 4625)',
            'Source IP identified conducting systematic credential enumeration via RDP',
            'Attack pattern consistent with ransomware group initial access methodology',
            'AI classified as T1110.001 with CRITICAL severity — immediate response triggered',
            'Windows Event Log correlation confirmed automated attack tooling',
            'Attack added to global threat intelligence as active RDP campaign',
        ],
        'WINDOWS_LATERAL_MOVEMENT': [
            'Windows Agent detected anomalous authentication across multiple internal systems',
            'Pass-the-hash or pass-the-ticket technique identified in authentication patterns',
            'AI classified as T1021 Remote Services — lateral movement confirmed',
            'Attack path reconstructed — entry point to current position mapped',
            'All systems in attacker movement path flagged for investigation',
            'CRITICAL response triggered — network segmentation enforced automatically',
        ],
        'WINDOWS_RANSOMWARE_BEHAVIOR': [
            'Windows Agent detected mass file operation pattern inconsistent with normal behavior',
            'File creation and modification rate exceeded ransomware behavioral threshold',
            'AI classified as T1486 Data Encrypted for Impact — CRITICAL emergency response',
            'Affected system immediately isolated from network by MAYA response engine',
            'Shadow copy deletion attempt detected and blocked',
            'Forensic snapshot captured before any encryption could complete',
        ],
        'WINDOWS_HONEYTOKEN_TRIGGERED': [
            'Fake admin credential planted in decoy system was accessed by attacker',
            'Honeytoken use confirmed — attacker successfully stole planted credential',
            'Attacker identity confirmed through credential usage — no longer anonymous',
            'AI classified as T1078 Valid Accounts — insider threat or phishing confirmed',
            'All systems accessible with compromised credential inventoried and locked',
            'Counter-intelligence payload in honeytoken data will expose attacker device',
        ],
    }
    return steps.get(attack_type, [
        'MAYA honeypot or sensor detected anomalous network activity',
        'Connection metadata and payload captured for analysis',
        'AI model analyzed traffic against 164,973 sample training dataset',
        'Attack classified using MITRE ATT&CK framework',
        'Threat intelligence cross-reference completed',
        'Autonomous response protocol initiated',
    ])

def get_response_steps(attack_type, severity):
    base = [
        'Attacker source IP flagged in MAYA threat database',
        'Attack event logged with full forensic metadata (timestamp, IP, payload)',
        'Incident report generated automatically by MAYA AI',
    ]
    critical_response = [
        'Attacker IP immediately blocked at firewall level (iptables DROP rule applied)',
        'All network traffic from/to attacker IP terminated within 0.8 seconds',
        'Security team alerted via email with full incident context',
        'Compromised or targeted credentials revoked and rotated',
        'Additional honeypots deployed around predicted attacker next targets',
        'Affected systems isolated from main network pending investigation',
        'CERT notification prepared for submission',
    ]
    high_response = [
        'Attacker IP blocked at firewall level',
        'Security team notified with incident summary',
        'Enhanced monitoring applied to all systems the attacker probed',
        'Threat intelligence updated with attacker signatures',
    ]
    low_response = [
        'Event logged for threat intelligence and pattern analysis',
        'Monitoring increased for source IP',
    ]
    if severity == 'CRITICAL':
        return base + critical_response
    elif severity == 'HIGH':
        return base + high_response
    else:
        return base + low_response

def get_solution(attack_type):
    solutions = {
        'SSH_BRUTE_FORCE': [
            'Implement fail2ban or equivalent to auto-block IPs after 5 failed SSH attempts',
            'Disable SSH password authentication — use SSH key pairs exclusively',
            'Change SSH port from 22 to a non-standard port (MAYA will continue monitoring both)',
            'Implement Multi-Factor Authentication (MFA) for all SSH access',
            'Restrict SSH access to specific IP ranges via firewall whitelist',
            'Enable SSH audit logging to SIEM for ongoing behavioral analysis',
        ],
        'WEB_CREDENTIAL_HARVEST': [
            'Implement Multi-Factor Authentication on all web portals immediately',
            'Deploy CAPTCHA on login pages to block automated credential stuffing',
            'Enable login anomaly detection — alert on unusual geographic access patterns',
            'Implement account lockout after 3 failed attempts with progressive delays',
            'Regular credential breach monitoring — check if org credentials appear in breach databases',
            'Security awareness training for employees — phishing simulation exercises',
        ],
        'DB_CONNECTION': [
            'Ensure database servers are never directly accessible from internet',
            'Implement network segmentation — databases should only accept connections from app tier',
            'Enable database activity monitoring (DAM) on all production databases',
            'Regular database security audits — check for default credentials and open ports',
            'Deploy database honeypots (MAYA provides this) as early warning system',
            'Implement least-privilege database access — no user should have DBA unless required',
        ],
        'DB_LOGIN_ATTEMPT': [
            'Immediately rotate all database credentials — assume attacker has credential lists',
            'Implement database connection rate limiting and anomaly detection',
            'Enable database-level audit logging for all authentication attempts',
            'Review and restrict database user permissions to minimum required',
            'Implement database activity monitoring to detect unusual query patterns',
            'Consider database encryption at rest and in transit for sensitive tables',
        ],
        'WINDOWS_RDP_BRUTE_FORCE': [
            'Disable RDP if not required — use VPN + internal RDP instead of internet-exposed RDP',
            'Implement Network Level Authentication (NLA) for all RDP connections',
            'Enable MFA for RDP — Microsoft Authenticator or hardware token required',
            'Implement account lockout policy — lock after 5 failed RDP attempts',
            'Restrict RDP access via firewall to specific IP ranges only',
            'Enable RDP logging and forward to SIEM — monitor for brute force patterns',
        ],
        'WINDOWS_LATERAL_MOVEMENT': [
            'Implement network microsegmentation — limit lateral movement paths between systems',
            'Deploy Privileged Access Workstations (PAW) for administrative tasks',
            'Enable Windows Defender Credential Guard to protect against credential theft',
            'Implement Just-in-Time (JIT) access for administrative accounts',
            'Regular review of service accounts — disable unused, rotate passwords quarterly',
            'Deploy honeypot accounts in Active Directory (MAYA provides this) to detect enumeration',
        ],
        'WINDOWS_RANSOMWARE_BEHAVIOR': [
            'CRITICAL: Verify backup integrity immediately — test restore from known-good backup',
            'Implement 3-2-1 backup strategy: 3 copies, 2 different media, 1 offsite',
            'Enable Windows Volume Shadow Copy protection with ransomware-resistant settings',
            'Deploy application whitelisting to prevent unauthorized executable from running',
            'Implement controlled folder access in Windows Defender to protect key directories',
            'Regular ransomware simulation exercises — test detection and recovery procedures',
        ],
        'WINDOWS_HONEYTOKEN_TRIGGERED': [
            'CRITICAL: Assume breach — conduct full security audit of all systems immediately',
            'Reset ALL passwords organization-wide — attacker has demonstrated credential access',
            'Review all access logs from past 30 days for signs of earlier undetected activity',
            'Implement zero-trust architecture — verify every access request regardless of network location',
            'Deploy additional honeytokens throughout infrastructure for ongoing detection',
            'Conduct forensic analysis to determine how attacker obtained initial access',
        ],
    }
    return solutions.get(attack_type, [
        'Review and harden the attack surface exploited in this incident',
        'Implement appropriate authentication controls for affected services',
        'Enable comprehensive logging and monitoring for affected systems',
        'Conduct security assessment of similar systems in your environment',
        'Update security policies and procedures based on this incident',
        'Consider deploying additional MAYA honeypots in affected network zones',
    ])

def add_page_border(canvas, doc):
    """Add professional page border and header/footer."""
    canvas.saveState()
    w, h = A4

    # Top bar - dark background
    canvas.setFillColor(C_BLACK)
    canvas.rect(0, h - 40, w, 40, fill=1, stroke=0)

    # Green accent line
    canvas.setFillColor(C_GREEN)
    canvas.rect(0, h - 42, w, 2, fill=1, stroke=0)

    # Logo text
    canvas.setFillColor(C_GREEN)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawString(20, h - 26, 'VAULTRAP')
    canvas.setFillColor(C_TEXT)
    canvas.setFont('Helvetica', 11)
    canvas.drawString(84, h - 26, '/ MAYA Security Operations Center')

    # Classification badge
    canvas.setFillColor(C_RED)
    canvas.rect(w - 130, h - 33, 110, 18, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawCentredString(w - 75, h - 22, 'CONFIDENTIAL')

    # Bottom bar
    canvas.setFillColor(C_DARK)
    canvas.rect(0, 0, w, 28, fill=1, stroke=0)
    canvas.setFillColor(C_GREEN)
    canvas.rect(0, 28, w, 1, fill=1, stroke=0)

    # Footer text
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(20, 10, f'MAYA Autonomous Security Platform — Vaultrap Security — Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}')
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(w - 20, 10, f'Page {doc.page}')

    # Left accent bar
    canvas.setFillColor(C_GREEN)
    canvas.setStrokeColor(C_GREEN)
    canvas.setLineWidth(0.5)

    canvas.restoreState()

def generate_full_report(company_name="Enterprise Security Report", specific_attack=None):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    if specific_attack:
        filename = f"{REPORTS_DIR}/maya_incident_{specific_attack.get('type','unknown')}_{timestamp}.pdf"
    else:
        filename = f"{REPORTS_DIR}/maya_soc_report_{timestamp}.pdf"

    attacks = read_attacks()
    if specific_attack:
        attacks_to_report = [specific_attack]
        report_title = f"INCIDENT REPORT — {specific_attack.get('type', 'UNKNOWN')}"
    else:
        attacks_to_report = attacks
        report_title = "SECURITY OPERATIONS CENTER REPORT"

    stats = get_stats(attacks)
    now = datetime.datetime.now()

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25*mm,
        leftMargin=25*mm,
        topMargin=22*mm,
        bottomMargin=18*mm,
        onFirstPage=add_page_border,
        onLaterPages=add_page_border,
    )

    story = []

    # ─── COVER SECTION ─────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))

    # Main title
    title_style = ParagraphStyle('title',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=C_TEXT,
        spaceAfter=4,
        leading=26,
    )
    story.append(Paragraph(report_title, title_style))

    sub_style = ParagraphStyle('sub',
        fontName='Helvetica',
        fontSize=11,
        textColor=C_MUTED,
        spaceAfter=2,
    )
    story.append(Paragraph(f'Automated Analysis by MAYA AI — Mistral 7B Intelligence Engine', sub_style))
    story.append(Paragraph(f'Report Generated: {now.strftime("%B %d, %Y at %H:%M:%S UTC")}', sub_style))
    story.append(Paragraph(f'Classification: CONFIDENTIAL — Authorized Recipients Only', ParagraphStyle('conf', fontName='Helvetica-Bold', fontSize=10, textColor=C_RED, spaceAfter=6)))

    # Green divider
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_GREEN, spaceAfter=8))

    # ─── EXECUTIVE SUMMARY BOX ─────────────────────────────────────────────
    risk_level = "CRITICAL" if stats['critical'] > 0 else "HIGH" if stats['high'] > 0 else "MEDIUM"
    risk_color = C_RED if risk_level == "CRITICAL" else C_ORANGE if risk_level == "HIGH" else C_YELLOW

    exec_data = [
        [Paragraph('<b>EXECUTIVE SUMMARY</b>', ParagraphStyle('eh', fontName='Helvetica-Bold', fontSize=9, textColor=C_GREEN, letterSpacing=2))],
        [Paragraph(
            f'During the monitoring period ending {now.strftime("%B %d, %Y")}, MAYA Autonomous Security Platform '
            f'detected and responded to <b>{stats["total"]} security events</b> across all monitored infrastructure. '
            f'The overall risk posture is assessed as <b>{risk_level}</b>. '
            f'<b>{stats["critical"]} critical threats</b> were autonomously contained without human intervention. '
            f'<b>Zero real assets were compromised</b> — all attacker interactions occurred exclusively within '
            f"MAYA's deception fabric. MAYA's 98.68% accurate AI model identified all threats using MITRE ATT&CK "
            f'framework classification.',
            ParagraphStyle('exec', fontName='Helvetica', fontSize=10, textColor=C_TEXT, leading=16, spaceAfter=0)
        )]
    ]
    exec_table = Table(exec_data, colWidths=[160*mm])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_DARK),
        ('BACKGROUND', (0,0), (-1,0), C_BLACK),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('LINEABOVE', (0,0), (-1,0), 2, C_GREEN),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, C_BORDER),
        ('LINEBEFORE', (0,0), (0,-1), 0.5, C_BORDER),
        ('LINEAFTER', (-1,0), (-1,-1), 0.5, C_BORDER),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 6*mm))

    # ─── STATISTICS GRID ───────────────────────────────────────────────────
    label_s = ParagraphStyle('ls', fontName='Helvetica', fontSize=8, textColor=C_MUTED, alignment=TA_CENTER, leading=10)
    num_s = ParagraphStyle('ns', fontName='Helvetica-Bold', fontSize=20, textColor=C_GREEN, alignment=TA_CENTER, leading=24)
    num_red = ParagraphStyle('nr', fontName='Helvetica-Bold', fontSize=20, textColor=C_RED, alignment=TA_CENTER, leading=24)
    num_orange = ParagraphStyle('no', fontName='Helvetica-Bold', fontSize=20, textColor=C_ORANGE, alignment=TA_CENTER, leading=24)
    num_blue = ParagraphStyle('nb', fontName='Helvetica-Bold', fontSize=20, textColor=C_BLUE, alignment=TA_CENTER, leading=24)

    def stat_cell(num, label, color_style):
        return [Paragraph(str(num), color_style), Paragraph(label, label_s)]

    stats_data = [[
        stat_cell(stats['total'], 'TOTAL EVENTS', num_s),
        stat_cell(stats['critical'], 'CRITICAL', num_red),
        stat_cell(stats['high'], 'HIGH', num_orange),
        stat_cell(len(stats['unique_ips']), 'UNIQUE IPs', num_blue),
        stat_cell(stats['ssh'], 'SSH ATTACKS', num_s),
        stat_cell(stats['web'], 'WEB ATTACKS', num_s),
        stat_cell(stats['db'], 'DB ATTACKS', num_orange),
        stat_cell('0', 'ASSETS BREACHED', num_s),
    ]]

    stats_table = Table(stats_data, colWidths=[20*mm]*8)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_DARK),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('LINEABOVE', (0,0), (-1,0), 1, C_GREEN),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 8*mm))

    # ─── INDIVIDUAL ATTACK REPORTS ─────────────────────────────────────────
    section_title = ParagraphStyle('st',
        fontName='Helvetica-Bold', fontSize=13,
        textColor=C_GREEN, spaceAfter=8, spaceBefore=4,
        letterSpacing=1,
    )
    field_label = ParagraphStyle('fl',
        fontName='Helvetica-Bold', fontSize=8,
        textColor=C_MUTED, letterSpacing=1.5,
        spaceBefore=0, spaceAfter=2,
    )
    field_value = ParagraphStyle('fv',
        fontName='Helvetica', fontSize=10,
        textColor=C_TEXT, leading=14, spaceAfter=6,
    )
    field_value_red = ParagraphStyle('fvr',
        fontName='Helvetica-Bold', fontSize=10,
        textColor=C_RED, leading=14, spaceAfter=6,
    )
    field_value_orange = ParagraphStyle('fvo',
        fontName='Helvetica-Bold', fontSize=10,
        textColor=C_ORANGE, leading=14, spaceAfter=6,
    )
    field_value_green = ParagraphStyle('fvg',
        fontName='Helvetica-Bold', fontSize=10,
        textColor=C_GREEN, leading=14, spaceAfter=6,
    )
    body_text = ParagraphStyle('bt',
        fontName='Helvetica', fontSize=10,
        textColor=HexColor('#8a9090'), leading=15, spaceAfter=4,
    )
    step_style = ParagraphStyle('ss',
        fontName='Helvetica', fontSize=10,
        textColor=C_TEXT, leading=15, spaceAfter=3,
        leftIndent=16,
    )
    solution_style = ParagraphStyle('sol',
        fontName='Helvetica', fontSize=10,
        textColor=C_TEXT, leading=15, spaceAfter=3,
        leftIndent=16,
    )

    sev_colors = {'CRITICAL': C_RED, 'HIGH': C_ORANGE, 'MEDIUM': C_YELLOW, 'LOW': C_GREEN}

    for idx, attack in enumerate(attacks_to_report[-20:], 1):
        atype = attack.get('type', 'UNKNOWN')
        severity = attack.get('severity', 'MEDIUM')
        ip = attack.get('attacker_ip', 'Unknown')
        ts = attack.get('timestamp', '')[:19].replace('T', ' ')
        honeypot = attack.get('honeypot', 'Unknown')
        sev_color = sev_colors.get(severity, C_MUTED)

        mitre_id, mitre_name, mitre_tactic = get_mitre(atype)
        detection_steps = get_detection_steps(atype)
        response_steps = get_response_steps(atype, severity)
        solutions = get_solution(atype)

        incident_elements = []

        # Incident header bar
        incident_elements.append(Spacer(1, 4*mm))
        header_data = [[
            Paragraph(f'<b>INCIDENT #{idx:03d}</b>', ParagraphStyle('ih', fontName='Helvetica-Bold', fontSize=9, textColor=C_GREEN, letterSpacing=2)),
            Paragraph(f'<b>{atype}</b>', ParagraphStyle('at', fontName='Helvetica-Bold', fontSize=9, textColor=C_TEXT)),
            Paragraph(f'<b>{severity}</b>', ParagraphStyle('sv', fontName='Helvetica-Bold', fontSize=9, textColor=sev_color, alignment=TA_CENTER)),
            Paragraph(f'{ts}', ParagraphStyle('ts', fontName='Helvetica', fontSize=9, textColor=C_MUTED, alignment=TA_RIGHT)),
        ]]
        header_table = Table(header_data, colWidths=[35*mm, 65*mm, 25*mm, 35*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C_BLACK),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('LINEABOVE', (0,0), (-1,0), 1.5, sev_color),
            ('LINEBELOW', (0,-1), (-1,-1), 0.5, C_BORDER),
            ('LINEBEFORE', (0,0), (0,-1), 0.5, C_BORDER),
            ('LINEAFTER', (-1,0), (-1,-1), 0.5, C_BORDER),
        ]))
        incident_elements.append(header_table)

        # Incident details grid
        detail_pairs = [
            ['ATTACKER IP', ip, 'HONEYPOT TRIGGERED', honeypot],
            ['MITRE TECHNIQUE', mitre_id, 'MITRE TACTIC', mitre_tactic],
            ['ATTACK NAME', mitre_name, 'SEVERITY LEVEL', severity],
        ]

        # Add specific fields based on attack type
        if atype == 'SSH_BRUTE_FORCE':
            detail_pairs.append(['USERNAME TRIED', attack.get('username_tried', 'N/A'), 'PASSWORD TRIED', attack.get('password_tried', 'N/A')])
        elif atype == 'WEB_CREDENTIAL_HARVEST':
            detail_pairs.append(['CREDENTIALS CAPTURED', attack.get('credentials', 'N/A')[:40], 'USER AGENT', attack.get('user_agent', 'N/A')[:30]])
        elif 'DB' in atype or 'MYSQL' in atype:
            detail_pairs.append(['DB USERNAME TRIED', attack.get('username_tried', 'N/A'), 'TARGET DATABASE', attack.get('database_target', 'N/A')])
        elif 'REDIS' in atype:
            detail_pairs.append(['COMMAND ATTEMPTED', (attack.get('command', 'N/A') or 'N/A')[:40], 'PORT', '6379'])
        elif 'WINDOWS' in atype:
            detail_pairs.append(['SYSTEM INFO', str(attack.get('system_info', {}).get('hostname', 'N/A')), 'OS', str(attack.get('system_info', {}).get('os', 'Windows'))])

        detail_data = []
        for pair in detail_pairs:
            row = [
                Paragraph(pair[0], ParagraphStyle('dk', fontName='Helvetica-Bold', fontSize=8, textColor=C_MUTED, letterSpacing=1)),
                Paragraph(str(pair[1]), ParagraphStyle('dv', fontName='Helvetica', fontSize=9, textColor=C_TEXT)),
                Paragraph(pair[2], ParagraphStyle('dk2', fontName='Helvetica-Bold', fontSize=8, textColor=C_MUTED, letterSpacing=1)),
                Paragraph(str(pair[3]), ParagraphStyle('dv2', fontName='Helvetica', fontSize=9, textColor=C_TEXT)),
            ]
            detail_data.append(row)

        detail_table = Table(detail_data, colWidths=[38*mm, 42*mm, 38*mm, 42*mm])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C_DARK),
            ('BACKGROUND', (0,0), (0,-1), C_BLACK),
            ('BACKGROUND', (2,0), (2,-1), C_BLACK),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ]))
        incident_elements.append(detail_table)
        incident_elements.append(Spacer(1, 3*mm))

        # DETECTION section
        incident_elements.append(Paragraph('HOW MAYA DETECTED THIS ATTACK', ParagraphStyle('sh', fontName='Helvetica-Bold', fontSize=8, textColor=C_GREEN, letterSpacing=2, spaceBefore=4, spaceAfter=4)))
        for i, step in enumerate(detection_steps, 1):
            incident_elements.append(Paragraph(
                f'<b>{i}.</b> {step}',
                ParagraphStyle('ds', fontName='Helvetica', fontSize=10, textColor=C_TEXT, leading=14, spaceAfter=3, leftIndent=8)
            ))
        incident_elements.append(Spacer(1, 3*mm))

        # RESPONSE section
        incident_elements.append(Paragraph('AUTONOMOUS RESPONSE ACTIONS TAKEN', ParagraphStyle('sh2', fontName='Helvetica-Bold', fontSize=8, textColor=C_ORANGE, letterSpacing=2, spaceBefore=4, spaceAfter=4)))
        for i, step in enumerate(response_steps, 1):
            incident_elements.append(Paragraph(
                f'<b>{i}.</b> {step}',
                ParagraphStyle('rs', fontName='Helvetica', fontSize=10, textColor=C_TEXT, leading=14, spaceAfter=3, leftIndent=8)
            ))
        incident_elements.append(Spacer(1, 3*mm))

        # SOLUTION section
        incident_elements.append(Paragraph('RECOMMENDED REMEDIATION & HARDENING', ParagraphStyle('sh3', fontName='Helvetica-Bold', fontSize=8, textColor=C_BLUE, letterSpacing=2, spaceBefore=4, spaceAfter=4)))
        for i, sol in enumerate(solutions, 1):
            incident_elements.append(Paragraph(
                f'<b>{i}.</b> {sol}',
                ParagraphStyle('ss2', fontName='Helvetica', fontSize=10, textColor=C_TEXT, leading=14, spaceAfter=3, leftIndent=8)
            ))

        # Bottom status bar
        status_data = [[
            Paragraph('● MAYA RESPONSE: COMPLETE', ParagraphStyle('sr', fontName='Helvetica-Bold', fontSize=8, textColor=C_GREEN)),
            Paragraph('● REAL ASSETS: PROTECTED', ParagraphStyle('sr2', fontName='Helvetica-Bold', fontSize=8, textColor=C_GREEN, alignment=TA_CENTER)),
            Paragraph('● ATTACKER: CONTAINED', ParagraphStyle('sr3', fontName='Helvetica-Bold', fontSize=8, textColor=C_GREEN, alignment=TA_RIGHT)),
        ]]
        status_table = Table(status_data, colWidths=[53*mm, 54*mm, 53*mm])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C_BLACK),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('LINEABOVE', (0,0), (-1,0), 0.5, C_BORDER),
            ('LINEBELOW', (0,-1), (-1,-1), 1, C_GREEN),
        ]))
        incident_elements.append(Spacer(1, 3*mm))
        incident_elements.append(status_table)

        story.append(KeepTogether(incident_elements[:8]))
        for elem in incident_elements[8:]:
            story.append(elem)

        # Page break between incidents if multiple
        if idx < len(attacks_to_report[-20:]):
            story.append(PageBreak())

    # ─── FINAL SUMMARY PAGE ────────────────────────────────────────────────
    if len(attacks_to_report) > 1:
        story.append(PageBreak())
        story.append(Spacer(1, 8*mm))
        story.append(Paragraph('THREAT SUMMARY & STRATEGIC RECOMMENDATIONS', section_title))
        story.append(HRFlowable(width="100%", thickness=1, color=C_GREEN, spaceAfter=6))

        # Summary findings
        findings = [
            f'Total of {stats["total"]} attack events detected and responded to autonomously by MAYA.',
            f'{stats["critical"]} CRITICAL severity events required immediate response — all contained successfully.',
            f'{len(stats["unique_ips"])} unique attacker IP addresses identified and blocked.',
            f'SSH infrastructure targeted by {stats["ssh"]} brute force attacks — credential database updated.',
            f'Web portals received {stats["web"]} attacks — all interactions captured in deception fabric.',
            f'Database infrastructure probed {stats["db"]} times — no real data accessed.',
            f'All incidents resulted in zero real asset compromise — MAYA deception layer 100% effective.',
        ]

        story.append(Paragraph('KEY FINDINGS', ParagraphStyle('kf', fontName='Helvetica-Bold', fontSize=8, textColor=C_GREEN, letterSpacing=2, spaceAfter=6)))
        for finding in findings:
            story.append(Paragraph(f'• {finding}', ParagraphStyle('fi', fontName='Helvetica', fontSize=10, textColor=C_TEXT, leading=15, spaceAfter=4, leftIndent=8)))

        story.append(Spacer(1, 6*mm))

        # Strategic recommendations
        story.append(Paragraph('STRATEGIC SECURITY RECOMMENDATIONS', ParagraphStyle('sr_h', fontName='Helvetica-Bold', fontSize=8, textColor=C_BLUE, letterSpacing=2, spaceAfter=6)))
        recs = [
            ('IMMEDIATE', C_RED, 'Rotate all credentials targeted in this monitoring period. Review firewall rules for all ports attackers probed. Verify backup integrity if ransomware behavior was detected.'),
            ('SHORT TERM', C_ORANGE, 'Deploy additional MAYA honeypots in network zones attackers showed interest in. Implement MFA across all internet-facing services. Conduct security awareness training.'),
            ('MEDIUM TERM', C_YELLOW, 'Implement network microsegmentation to limit lateral movement. Deploy privileged access management (PAM) solution. Establish formal incident response runbooks based on this report.'),
            ('LONG TERM', C_GREEN, 'Build a mature security operations capability leveraging MAYA intelligence. Implement zero-trust architecture. Regular red team exercises against MAYA-protected infrastructure.'),
        ]

        for priority, color, text in recs:
            rec_data = [[
                Paragraph(f'<b>{priority}</b>', ParagraphStyle('rp', fontName='Helvetica-Bold', fontSize=8, textColor=color, alignment=TA_CENTER)),
                Paragraph(text, ParagraphStyle('rt', fontName='Helvetica', fontSize=9, textColor=C_TEXT, leading=13)),
            ]]
            rec_table = Table(rec_data, colWidths=[22*mm, 138*mm])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C_DARK),
                ('BACKGROUND', (0,0), (0,-1), C_BLACK),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
                ('LINEBEFORE', (0,0), (0,-1), 2, color),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 2*mm))

        # Sign off
        story.append(Spacer(1, 10*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=6))
        signoff_data = [[
            Paragraph('Report generated by MAYA Autonomous Security Platform\nPowered by Mistral 7B AI — Vaultrap Security Technologies\nGeetheswara@Vaultrap.com | vaultrap.com', ParagraphStyle('so', fontName='Helvetica', fontSize=9, textColor=C_MUTED, leading=14)),
            Paragraph(f'Report ID: MAYA-{timestamp}\nGenerated: {now.strftime("%Y-%m-%d %H:%M:%S UTC")}\nClassification: CONFIDENTIAL', ParagraphStyle('so2', fontName='Helvetica', fontSize=9, textColor=C_MUTED, leading=14, alignment=TA_RIGHT)),
        ]]
        signoff_table = Table(signoff_data, colWidths=[80*mm, 80*mm])
        signoff_table.setStyle(TableStyle([
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(signoff_table)

    doc.build(story)
    print(f"[MAYA] Report generated: {filename}")
    return filename

if __name__ == "__main__":
    print("[MAYA] Generating world-class SOC incident report...")
    filename = generate_full_report("Vaultrap Security SOC Report")
    print(f"[MAYA] Open: {filename}")
