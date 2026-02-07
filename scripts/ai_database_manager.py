"""
AI Database Manager - Level 2: Controlled Access + Approval System
AI agents can read, create tables, and perform safe operations.
Critical operations require email approval.
"""

import os
import sys
import json
import hashlib
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import get_database


def _get_env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


# ==================== SECURITY RULES ====================

SAFE_OPERATIONS = {
    "SELECT": "*",  # All tables
    "INSERT": ["ai_metrics_*", "ai_analytics_*", "ai_reports_*"],  # Only AI tables
    "UPDATE": {
        # Table: [allowed columns]
        "agents": ["merit_score", "trust_score"],
        "ai_metrics_*": "*",
    },
}

BLACKLIST = {
    "DELETE": ["agents", "posts", "comments", "elections"],
    "DROP": ["agents", "posts", "comments", "elections"],
    "TRUNCATE": ["agents", "posts", "comments"],
}

AI_TABLE_PREFIX = "ai_"


def is_safe_operation(operation: str, table: str, columns: Optional[List[str]] = None) -> bool:
    """
    Check if operation is safe without approval.
    """
    operation = operation.upper()
    
    # SELECT always safe
    if operation == "SELECT":
        return True
    
    # AI-prefixed tables have more freedom
    if table.startswith(AI_TABLE_PREFIX):
        if operation in ["CREATE", "INSERT", "UPDATE"]:
            return True
        # DELETE on AI tables needs approval
        return False
    
    # INSERT on whitelisted tables
    if operation == "INSERT":
        for pattern in SAFE_OPERATIONS["INSERT"]:
            if pattern.endswith("*"):
                if table.startswith(pattern[:-1]):
                    return True
            elif table == pattern:
                return True
        return False
    
    # UPDATE with column restrictions
    if operation == "UPDATE":
        if table in SAFE_OPERATIONS["UPDATE"]:
            allowed = SAFE_OPERATIONS["UPDATE"][table]
            if allowed == "*":
                return True
            if columns and all(col in allowed for col in columns):
                return True
        return False
    
    # Everything else needs approval
    return False


def is_blacklisted(operation: str, table: str) -> bool:
    """
    Check if operation is absolutely forbidden.
    """
    operation = operation.upper()
    if operation in BLACKLIST:
        return table in BLACKLIST[operation]
    return False


# ==================== AI ANALYSIS & PROPOSAL ====================

def analyze_and_propose_database_task():
    """
    AI analyzes database and proposes improvement.
    """
    # Try Gemini first (free, no rate limit), fallback to OpenAI
    gemini_key = _get_env("GEMINI_API_KEY")
    openai_key = _get_env("OPENAI_API_KEY")
    
    use_gemini = bool(gemini_key)
    
    if use_gemini:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    elif openai_key:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
    else:
        return {"error": "No AI API key available"}
    
    # Get current table structure
    db = get_database()
    try:
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        tables_result = db.client.rpc('exec_sql', {'query': tables_query}).execute()
        existing_tables = [r['table_name'] for r in (tables_result.data or [])]
    except:
        existing_tables = ["agents", "posts", "comments", "elections"]
    
    prompt = f"""Du er en AI database administrator for EYAVAP-systemet.

EKSISTERENDE TABELLER:
{json.dumps(existing_tables, indent=2)}

MISSION: Foreslå en database-forbedring.

SIKRE OPERATIONER (ingen godkendelse):
✅ CREATE TABLE ai_* (nye AI-tabeller)
✅ SELECT fra alle tabeller
✅ INSERT til ai_* tabeller
✅ UPDATE agents.merit_score, agents.trust_score

KRÆVER GODKENDELSE (email):
⚠️ DELETE fra ai_* tabeller
⚠️ UPDATE til andre felter
⚠️ ALTER TABLE

FORBUDT (absolut):
❌ DROP agents/posts/comments/elections
❌ DELETE fra agents/posts/comments
❌ TRUNCATE kritiske tabeller

FORSLAG EKSEMPLER:
- Ny tabel: ai_metrics_engagement (agent engagement tracking)
- Ny tabel: ai_analytics_trends (trend analysis)
- UPDATE agents.merit_score (baseret på performance)
- Ny tabel: ai_reports_daily (daily summaries)

Return JSON:
{{
  "task_name": "kort navn",
  "description": "1-2 sætninger om formål",
  "operation": "CREATE/INSERT/UPDATE/DELETE",
  "table_name": "tabel navn",
  "sql_query": "præcis SQL query",
  "requires_approval": true/false,
  "benefit": "hvorfor er dette nyttigt?"
}}

IMPORTANT:
- Foreslå kun NYTTIGE forbedringer
- Brug korrekt PostgreSQL syntax
- Hvis tabellen eksisterer, foreslå noget andet"""

    if use_gemini:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)
    else:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        result = json.loads(response.choices[0].message.content)
    
    # Security validation
    operation = result.get("operation", "").upper()
    table = result.get("table_name", "")
    
    if is_blacklisted(operation, table):
        return {
            "error": "Operation is blacklisted",
            "reason": f"{operation} on {table} is forbidden"
        }
    
    result["requires_approval"] = not is_safe_operation(operation, table)
    
    return result


# ==================== APPROVAL SYSTEM ====================

def generate_approval_token(task: Dict) -> str:
    """
    Generate unique approval token.
    """
    data = f"{task.get('sql_query')}{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def send_approval_email(task: Dict, token: str) -> bool:
    """
    Send approval request email.
    """
    gmail_user = _get_env("GMAIL_USER")
    gmail_pass = _get_env("GMAIL_APP_PASSWORD")
    to_email = _get_env("REPORT_EMAIL", gmail_user)
    
    if not gmail_user or not gmail_pass:
        print("⚠️ Email credentials missing")
        return False
    
    subject = f"⚠️ AI Database Operation Requires Approval"
    
    body = f"""
EYAVAP AI DATABASE MANAGER
========================================

🤖 AI agent wants to perform a database operation that requires your approval.

📋 TASK DETAILS
---------------
Task: {task.get('task_name')}
Description: {task.get('description')}
Operation: {task.get('operation')}
Table: {task.get('table_name')}
Benefit: {task.get('benefit')}

📝 SQL QUERY
------------
{task.get('sql_query')}

⏰ APPROVAL DEADLINE
--------------------
You have 5 minutes to approve or reject this operation.
After 5 minutes, it will be automatically rejected.

🔐 APPROVAL TOKEN
-----------------
Token: {token}

To approve, reply to this email with:
Subject: APPROVE {token}

To reject, reply with:
Subject: REJECT {token}

⚠️ WARNING
----------
Only approve if you understand the operation and trust the AI's judgment.

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
        print(f"✅ Approval email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


# ==================== EXECUTION ====================

def execute_database_task(task: Dict) -> Dict:
    """
    Execute approved database task.
    """
    db = get_database()
    sql = task.get("sql_query", "")
    
    if not sql:
        return {"error": "No SQL query provided"}
    
    try:
        # Execute query
        result = db.client.rpc('exec_sql', {'query': sql}).execute()
        
        return {
            "success": True,
            "operation": task.get("operation"),
            "table": task.get("table_name"),
            "task": task.get("task_name"),
            "rows_affected": len(result.data or [])
        }
    except Exception as e:
        return {
            "error": str(e),
            "operation": task.get("operation"),
            "table": task.get("table_name")
        }


def send_result_email(task: Dict, result: Dict):
    """
    Send execution result email.
    """
    gmail_user = _get_env("GMAIL_USER")
    gmail_pass = _get_env("GMAIL_APP_PASSWORD")
    to_email = _get_env("REPORT_EMAIL", gmail_user)
    
    if not gmail_user or not gmail_pass:
        return
    
    success = result.get("success", False)
    subject = f"{'✅' if success else '❌'} AI Database Task: {task.get('task_name')}"
    
    if success:
        body = f"""
EYAVAP AI DATABASE MANAGER - RESULT
========================================

✅ Task completed successfully

📋 TASK
-------
{task.get('task_name')}
{task.get('description')}

🔧 OPERATION
------------
{task.get('operation')} on {task.get('table_name')}

📊 RESULT
---------
Rows affected: {result.get('rows_affected', 0)}

💡 BENEFIT
----------
{task.get('benefit')}

---
EYAVAP Autonomous AI System
"""
    else:
        body = f"""
EYAVAP AI DATABASE MANAGER - ERROR
========================================

❌ Task failed

📋 TASK
-------
{task.get('task_name')}

❌ ERROR
--------
{result.get('error', 'Unknown error')}

🔧 ATTEMPTED OPERATION
----------------------
{task.get('operation')} on {task.get('table_name')}

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
    except Exception as e:
        print(f"❌ Email error: {e}")


# ==================== MAIN ====================

def main():
    print("🤖 AI Database Manager - Level 2 (Controlled Access)")
    
    # 1. Analyze and propose
    print("\n📊 Analyzing database...")
    task = analyze_and_propose_database_task()
    
    if "error" in task:
        print(f"❌ Analysis error: {task.get('error')}")
        if "reason" in task:
            print(f"   Reason: {task['reason']}")
        return
    
    print(f"💡 Task proposed: {task.get('task_name')}")
    print(f"   Operation: {task.get('operation')} on {task.get('table_name')}")
    print(f"   Benefit: {task.get('benefit')}")
    
    # 2. Check if approval needed
    if task.get("requires_approval"):
        print("\n⚠️ This operation requires approval")
        token = generate_approval_token(task)
        
        if send_approval_email(task, token):
            print(f"📧 Approval email sent. Token: {token}")
            print("⏰ Waiting for manual approval (not automated yet)")
            # In production: Store task and token in database, check later
            return
        else:
            print("❌ Could not send approval email, aborting")
            return
    
    # 3. Execute safe operation
    print("\n✅ Safe operation, executing...")
    result = execute_database_task(task)
    
    if result.get("success"):
        print(f"✅ Task completed: {result.get('task')}")
        print(f"   Rows affected: {result.get('rows_affected', 0)}")
    else:
        print(f"❌ Task failed: {result.get('error')}")
    
    # 4. Send result email
    print("\n📧 Sending result email...")
    send_result_email(task, result)


if __name__ == "__main__":
    main()
