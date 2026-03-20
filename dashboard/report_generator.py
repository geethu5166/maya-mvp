from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import json
import os
import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')
REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs', 'reports')

# Vaultrap brand colors
GREEN = HexColor('#00c896')
DARK = HexColor('#0a0e17')
DARK2 = HexColor('#0d1117')
GRAY = HexColor('#888888')
RED = HexColor('#e53935')
ORANGE = HexColor('#ff9800')
BLUE = HexColor('#42a5f5')

def read_attacks():
    attacks = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    attacks.append(json.loads(line))
    except:
        pass
    return attacks

def get_stats(attacks):
    return {
        'total': len(attacks),
        'critical': len([a for a in attacks if a.get('severity') == 'CRITICAL']),
        'high': len([a for a in attacks if a.get('severity') == 'HIGH']),
        'medium': len([a for a in attacks if a.get('severity') == 'MEDIUM']),
        'low': len([a for a in attacks if a.get('severity') == 'LOW']),
        'ssh': len([a for a in attacks if a.get('honeypot') == 'SSH']),
        'web': len([a for a in attacks if a.get('honeypot') == 'WEB']),
        'unique_ips': len(set(a.get('attacker_ip', '') for a in attacks))
    }

def generate_report(company_name="Demo Company"):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{REPORTS_DIR}/vaultrap_report_{timestamp}.pdf"
    
    attacks = read_attacks()
    stats = get_stats(attacks)
    now = datetime.datetime.now()
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    header_data = [[
        Paragraph('<font color="#00c896"><b>VAULTRAP</b></font><font color="white"> SECURITY</font>', 
                 ParagraphStyle('logo', fontSize=20, textColor=white)),
        Paragraph(f'<font color="#888888">MAVA Platform — Incident Report</font>',
                 ParagraphStyle('sub', fontSize=10, textColor=GRAY, alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('PADDING', (0,0), (-1,-1), 16),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [DARK2]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # Title
    story.append(Paragraph(
        '<font color="white"><b>Security Incident Report</b></font>',
        ParagraphStyle('title', fontSize=24, textColor=white, spaceAfter=6)
    ))
    story.append(Paragraph(
        f'<font color="#888888">Generated: {now.strftime("%B %d, %Y at %H:%M")} | Company: {company_name}</font>',
        ParagraphStyle('subtitle', fontSize=11, textColor=GRAY, spaceAfter=4)
    ))
    story.append(Paragraph(
        f'<font color="#888888">Report Period: Last 24 hours | Classification: CONFIDENTIAL</font>',
        ParagraphStyle('subtitle2', fontSize=11, textColor=GRAY)
    ))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph(
        '<font color="#00c896"><b>EXECUTIVE SUMMARY</b></font>',
        ParagraphStyle('section', fontSize=12, textColor=GREEN, spaceAfter=12)
    ))

    risk_level = "CRITICAL" if stats['critical'] > 0 else "HIGH" if stats['high'] > 0 else "MEDIUM"
    risk_color = "#e53935" if risk_level == "CRITICAL" else "#ff9800" if risk_level == "HIGH" else "#ffd600"

    summary_text = f"""
    During the monitoring period, MAVA detected and responded to <b>{stats['total']} security events</b> 
    across your network infrastructure. The overall risk level is assessed as 
    <font color="{risk_color}"><b>{risk_level}</b></font>.
    MAVA's autonomous response engine contained all threats without requiring manual intervention.
    <br/><br/>
    <font color="#00c896"><b>Key Finding:</b></font> {stats['critical']} critical threats were 
    automatically blocked and contained by MAVA before any damage could occur.
    """
    story.append(Paragraph(summary_text,
        ParagraphStyle('body', fontSize=11, textColor=HexColor('#cccccc'), 
                      leading=18, spaceAfter=16)))
    story.append(Spacer(1, 10))

    # Stats boxes
    stats_data = [[
        Paragraph(f'<font color="#00c896"><b>{stats["total"]}</b></font><br/><font color="#666666">Total Events</font>',
                 ParagraphStyle('stat', fontSize=11, alignment=TA_CENTER)),
        Paragraph(f'<font color="#e53935"><b>{stats["critical"]}</b></font><br/><font color="#666666">Critical</font>',
                 ParagraphStyle('stat', fontSize=11, alignment=TA_CENTER)),
        Paragraph(f'<font color="#ff9800"><b>{stats["high"]}</b></font><br/><font color="#666666">High</font>',
                 ParagraphStyle('stat', fontSize=11, alignment=TA_CENTER)),
        Paragraph(f'<font color="#42a5f5"><b>{stats["unique_ips"]}</b></font><br/><font color="#666666">Unique IPs</font>',
                 ParagraphStyle('stat', fontSize=11, alignment=TA_CENTER)),
        Paragraph(f'<font color="#00c896"><b>{stats["ssh"]}</b></font><br/><font color="#666666">SSH Attacks</font>',
                 ParagraphStyle('stat', fontSize=11, alignment=TA_CENTER)),
        Paragraph(f'<font color="#00c896"><b>{stats["web"]}</b></font><br/><font color="#666666">Web Attacks</font>',
                 ParagraphStyle('stat', fontSize=11, alignment=TA_CENTER)),
    ]]
    stats_table = Table(stats_data, colWidths=[1.1*inch]*6)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('PADDING', (0,0), (-1,-1), 14),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#1a2332')),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 24))

    # Attack Timeline
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#1a2332')))
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        '<font color="#00c896"><b>ATTACK TIMELINE</b></font>',
        ParagraphStyle('section', fontSize=12, textColor=GREEN, spaceAfter=12)
    ))

    # Table header
    table_data = [[
        Paragraph('<font color="#666666">TIMESTAMP</font>', 
                 ParagraphStyle('th', fontSize=9, textColor=GRAY)),
        Paragraph('<font color="#666666">ATTACKER IP</font>',
                 ParagraphStyle('th', fontSize=9, textColor=GRAY)),
        Paragraph('<font color="#666666">TYPE</font>',
                 ParagraphStyle('th', fontSize=9, textColor=GRAY)),
        Paragraph('<font color="#666666">SEVERITY</font>',
                 ParagraphStyle('th', fontSize=9, textColor=GRAY)),
        Paragraph('<font color="#666666">DETAILS</font>',
                 ParagraphStyle('th', fontSize=9, textColor=GRAY)),
    ]]

    severity_colors = {
        'CRITICAL': '#e53935',
        'HIGH': '#ff9800', 
        'MEDIUM': '#ffd600',
        'LOW': '#00c896'
    }

    for attack in attacks[-15:]:
        sev = attack.get('severity', 'LOW')
        sev_color = severity_colors.get(sev, '#00c896')
        
        if attack.get('type') == 'SSH_BRUTE_FORCE':
            detail = f"user:{attack.get('username_tried','')} pass:{attack.get('password_tried','')}"
        elif attack.get('type') == 'WEB_CREDENTIAL_HARVEST':
            detail = f"creds:{attack.get('credentials','')[:30]}"
        else:
            detail = f"path:{attack.get('path','N/A')}"

        table_data.append([
            Paragraph(f'<font color="#555555">{attack.get("timestamp","")[:19].replace("T"," ")}</font>',
                     ParagraphStyle('td', fontSize=8, textColor=GRAY)),
            Paragraph(f'<font color="#42a5f5">{attack.get("attacker_ip","")}</font>',
                     ParagraphStyle('td', fontSize=8, textColor=BLUE)),
            Paragraph(f'<font color="#42a5f5">{attack.get("type","")}</font>',
                     ParagraphStyle('td', fontSize=8, textColor=BLUE)),
            Paragraph(f'<font color="{sev_color}"><b>{sev}</b></font>',
                     ParagraphStyle('td', fontSize=8)),
            Paragraph(f'<font color="#666666">{detail}</font>',
                     ParagraphStyle('td', fontSize=8, textColor=GRAY)),
        ])

    attack_table = Table(table_data, 
                        colWidths=[1.3*inch, 1*inch, 1.5*inch, 0.7*inch, 2.2*inch])
    attack_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#080c12')),
        ('BACKGROUND', (0,1), (-1,-1), DARK2),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [DARK2, HexColor('#0d1520')]),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#1a2332')),
    ]))
    story.append(attack_table)
    story.append(Spacer(1, 24))

    # Recommendations
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#1a2332')))
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        '<font color="#00c896"><b>RECOMMENDATIONS</b></font>',
        ParagraphStyle('section', fontSize=12, textColor=GREEN, spaceAfter=12)
    ))

    recommendations = [
        ("Immediate", "Review and rotate all credentials that were targeted in credential harvesting attempts."),
        ("24 Hours", "Deploy additional deception assets in areas where attackers showed repeated interest."),
        ("This Week", "Conduct employee security awareness training — social engineering attempts detected."),
        ("Ongoing", "MAVA autonomous response is active. No manual intervention required for future incidents."),
    ]

    for priority, rec in recommendations:
        rec_color = "#e53935" if priority == "Immediate" else "#ff9800" if priority == "24 Hours" else "#ffd600" if priority == "This Week" else "#00c896"
        story.append(Paragraph(
            f'<font color="{rec_color}"><b>[{priority}]</b></font> <font color="#cccccc">{rec}</font>',
            ParagraphStyle('rec', fontSize=11, textColor=HexColor('#cccccc'), 
                          leading=18, spaceAfter=8)
        ))

    story.append(Spacer(1, 24))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        '<font color="#444444">This report was generated automatically by MAVA — Vaultrap Security Technologies | Geetheswara@Vaultrap.com | vaultrap.com</font>',
        ParagraphStyle('footer', fontSize=9, textColor=GRAY, alignment=TA_CENTER)
    ))

    # Build PDF
    doc.build(story)
    print(f"[VAULTRAP] Report generated: {filename}")
    return filename

if __name__ == "__main__":
    filename = generate_report("Demo Enterprise Ltd")
    print(f"[VAULTRAP] Open: {filename}")
