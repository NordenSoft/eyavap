"""
AI-Driven Feature Development
Agents autonomously propose, code, and deploy new features every 15 minutes.
"""

import os
import sys
import json
import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def _get_env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


def send_feature_email(proposal: dict, result: dict):
    """
    Send email notification about AI-developed feature.
    """
    gmail_user = _get_env("GMAIL_USER")
    gmail_pass = _get_env("GMAIL_APP_PASSWORD")
    to_email = _get_env("REPORT_EMAIL", gmail_user)
    
    if not gmail_user or not gmail_pass:
        print("⚠️ Email credentials missing")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if result.get("success"):
        subject = f"🤖 AI Agent: Ny feature udviklet - {proposal.get('feature_name')}"
        body = f"""
EYAVAP AI AGENT - FEATURE DEVELOPMENT
========================================

⏰ Tidspunkt: {timestamp}

💡 FEATURE
----------
Navn: {proposal.get('feature_name')}
Beskrivelse: {proposal.get('description')}

🔧 IMPLEMENTATION
-----------------
Fil modificeret: {result.get('file')}
Ændring: {result.get('summary')}

📊 STATUS
---------
✅ Feature succesfuldt implementeret og deployed

🚀 Næste AI udvikling om 15 minutter

---
EYAVAP Autonomous AI System
Systemet udvikler sig selv automatisk
"""
    else:
        subject = f"ℹ️ AI Agent: Feature skipped"
        body = f"""
EYAVAP AI AGENT - FEATURE DEVELOPMENT
========================================

⏰ Tidspunkt: {timestamp}

💡 FEATURE FORSLAG
------------------
Navn: {proposal.get('feature_name')}
Beskrivelse: {proposal.get('description')}

⏭️ STATUS
---------
Feature blev ikke implementeret
Årsag: {result.get('reason', 'Unknown')}

🔄 AI forsøger igen om 15 minutter

---
EYAVAP Autonomous AI System
"""
    
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_email
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email error: {e}")


def analyze_system_and_propose_feature():
    """
    AI analyzes the current system and proposes a new feature to implement.
    """
    from openai import OpenAI
    
    api_key = _get_env("OPENAI_API_KEY")
    if not api_key:
        return {"error": "No OpenAI API key"}
    
    client = OpenAI(api_key=api_key)
    
    prompt = """Du er en AI-udvikler agent i EYAVAP-systemet.

MISSION: Foreslå en lille, implementerbar forbedring til systemet.

SYSTEM OVERSIGT:
- 999 danske AI-agenter diskuterer aktuelle emner
- Social stream, valg, compliance, læring
- Streamlit dashboard + Supabase backend
- GitHub Actions automation

REGLER:
- Forslag skal være LILLE (5-20 linjer kode)
- IKKE ændre eksisterende funktionalitet
- IKKE røre ved database schema eller valgregler
- Kun UX, performance, nye metrics, eller små AI-forbedringer

FOKUS:
- Dashboard nye metrics
- Social stream UX forbedringer
- Monitoring udvidelser
- Små optimiseringer

Return JSON:
{
  "feature_name": "kort navn",
  "description": "1-2 sætninger",
  "file_to_modify": "sti til fil",
  "implementation": "konkret kode-snippet eller instruktion"
}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    
    result = json.loads(response.choices[0].message.content)
    return result


def implement_feature(proposal: dict):
    """
    AI implements the proposed feature.
    """
    from openai import OpenAI
    
    api_key = _get_env("OPENAI_API_KEY")
    if not api_key:
        return {"error": "No OpenAI API key"}
    
    client = OpenAI(api_key=api_key)
    
    file_path = proposal.get("file_to_modify")
    if not file_path:
        return {"error": "No file specified"}
    
    # Read current file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            current_code = f.read()
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}
    
    prompt = f"""Du er en AI-udvikler agent.

FEATURE PROPOSAL:
{json.dumps(proposal, indent=2)}

CURRENT FILE CONTENT:
{current_code[:10000]}

TASK: Implementér denne feature ved at give præcis kode-ændring.

Return JSON:
{{
  "changes_made": true/false,
  "new_code": "hele den nye fil (hvis changes_made=true)",
  "summary": "kort beskrivelse af ændringen"
}}

IMPORTANT:
- Hvis feature allerede eksisterer eller ikke er passende, return changes_made=false
- Behold ALLE eksisterende funktioner
- Tilføj kun den nye feature
- Sørg for korrekt Python syntax"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    
    result = json.loads(response.choices[0].message.content)
    
    if result.get("changes_made") and result.get("new_code"):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result["new_code"])
            return {
                "success": True,
                "file": file_path,
                "summary": result.get("summary", "Feature implemented"),
            }
        except Exception as e:
            return {"error": f"Cannot write file: {e}"}
    
    return {"success": False, "reason": "No changes needed or inappropriate feature"}


def main():
    print("🤖 AI Feature Development Agent Starting...")
    
    # 1. Analyze and propose
    print("\n📊 Analyzing system...")
    proposal = analyze_system_and_propose_feature()
    
    if "error" in proposal:
        print(f"❌ Analysis error: {proposal['error']}")
        return
    
    print(f"💡 Feature proposed: {proposal.get('feature_name')}")
    print(f"   Description: {proposal.get('description')}")
    print(f"   Target file: {proposal.get('file_to_modify')}")
    
    # 2. Implement
    print("\n🔧 Implementing feature...")
    result = implement_feature(proposal)
    
    if result.get("success"):
        print(f"✅ Feature implemented: {result.get('summary')}")
        print(f"   Modified: {result.get('file')}")
    elif "error" in result:
        print(f"❌ Implementation error: {result['error']}")
    else:
        print(f"⏭️ Skipped: {result.get('reason')}")
    
    # 3. Send email notification
    print("\n📧 Sending email notification...")
    send_feature_email(proposal, result)


if __name__ == "__main__":
    main()
