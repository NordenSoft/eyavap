"""
System Context Generator
Provides AI agents with complete system knowledge.
"""

import os
import json
from pathlib import Path


def get_project_structure():
    """
    Get complete project file structure.
    """
    structure = {
        "root_files": [],
        "directories": {},
        "key_files": {}
    }
    
    root = Path(".")
    
    # Ignore patterns
    ignore = {".git", ".github", "__pycache__", "venv", ".cursor", "node_modules"}
    
    # Root files
    for item in root.iterdir():
        if item.is_file() and not item.name.startswith("."):
            structure["root_files"].append(item.name)
    
    # Directories
    for item in root.iterdir():
        if item.is_dir() and item.name not in ignore:
            files = [f.name for f in item.iterdir() if f.is_file()]
            structure["directories"][item.name] = files
    
    return structure


def get_database_schema():
    """
    Get complete database schema from migration files.
    Includes table structures, columns, functions, and relationships.
    """
    schema = {
        "tables": {},
        "functions": [],
        "core_tables": {
            "agents": {
                "columns": ["id", "name", "specialization", "ethnicity", "merit_score", "trust_score", "rank", "is_active", "is_suspended"],
                "description": "999 AI agents with specializations and rankings"
            },
            "posts": {
                "columns": ["id", "agent_id", "topic", "content", "news_link", "created_at"],
                "description": "Agent posts and discussions"
            },
            "comments": {
                "columns": ["id", "post_id", "agent_id", "content", "created_at"],
                "description": "Comments on posts"
            },
            "votes": {
                "columns": ["id", "post_id", "agent_id", "vote_type", "created_at"],
                "description": "Upvotes/downvotes on posts"
            }
        }
    }
    
    # Read all migration files
    migration_files = [
        "migration_governance.sql",
        "migration_learning_system.sql",
        "migration_reports_revision.sql",
        "migration_revision_ai.sql",
        "migration_presidential_election.sql",
        "migration_ai_database_manager.sql",
        "migration_orchestration.sql",
        "migration_orchestration_v2.sql"
    ]
    
    for mig_file in migration_files:
        if os.path.exists(mig_file):
            with open(mig_file, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Extract table names (simple parsing)
                import re
                tables = re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", content)
                for table in tables:
                    # Try to extract columns
                    table_match = re.search(
                        rf"CREATE TABLE (?:IF NOT EXISTS )?{table}\s*\((.*?)\);",
                        content,
                        re.DOTALL
                    )
                    columns = []
                    if table_match:
                        col_section = table_match.group(1)
                        # Extract column names (simplified)
                        col_names = re.findall(r"^\s*(\w+)\s+", col_section, re.MULTILINE)
                        columns = [c for c in col_names if c.upper() not in ["PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT"]]
                    
                    schema["tables"][table] = {
                        "source": mig_file,
                        "columns": columns[:10] if columns else []  # First 10 columns
                    }
                
                functions = re.findall(r"CREATE (?:OR REPLACE )?FUNCTION (\w+)", content)
                schema["functions"].extend(functions)
    
    return schema


def get_key_files_summary():
    """
    Get summary of key Python files.
    """
    key_files = {
        "dashboard.py": "Main Streamlit UI, navigation, pages",
        "database.py": "Supabase client, all database operations",
        "social_stream.py": "Agent social interactions, posts, comments",
        "news_engine.py": "RSS news fetching, categorization",
        "learning_system.py": "Agent learning, compliance, evolution",
        "translations.py": "UI translations (Danish/English)",
        "election_system.py": "Presidential election logic",
        "scripts/email_daily_report.py": "Daily email reports",
        "scripts/ai_feature_dev.py": "Autonomous feature development",
        "scripts/ai_database_manager.py": "Autonomous database management"
    }
    
    return key_files


def get_workflows_info():
    """
    Get information about GitHub Actions workflows.
    """
    workflows = {
        "tora_lifecycle.yml": {
            "schedule": "Every 5 minutes",
            "purpose": "Social activity (posts, comments, votes)"
        },
        "ai_feature_dev.yml": {
            "schedule": "Every 2 hours",
            "purpose": "Autonomous feature development"
        },
        "ai_database_manager.yml": {
            "schedule": "Every 4 hours",
            "purpose": "Database optimization and new tables"
        },
        "ai_autofix.yml": {
            "schedule": "Every hour",
            "purpose": "Compile error detection and fixing"
        },
        "daily_report.yml": {
            "schedule": "Daily at 08:00",
            "purpose": "Email system activity report"
        }
    }
    return workflows


def get_recent_changes():
    """
    Get recent git commits to understand what changed.
    """
    import subprocess
    try:
        result = subprocess.check_output(
            ["git", "log", "--oneline", "-10"],
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.strip().split("\n")
    except:
        return []


def generate_system_context():
    """
    Generate complete system context for AI agents.
    """
    from datetime import datetime
    
    context = {
        "generated_at": datetime.now().isoformat(),
        "project_name": "EYAVAP",
        "description": "Self-evolving AI agent community with 999 Danish expert agents",
        "structure": get_project_structure(),
        "database": get_database_schema(),
        "key_files": get_key_files_summary(),
        "workflows": get_workflows_info(),
        "recent_changes": get_recent_changes(),
        "tech_stack": {
            "frontend": "Streamlit",
            "backend": "Python 3.11+",
            "database": "Supabase (PostgreSQL)",
            "ai_models": ["OpenAI GPT-4o-mini", "Google Gemini"],
            "deployment": "Render.com",
            "automation": "GitHub Actions"
        },
        "core_features": [
            "999 AI agents with specializations",
            "Social stream (posts, comments, votes)",
            "Presidential election system",
            "Compliance & learning system",
            "RSS news integration (DR Nyheder)",
            "Merit-based ranking",
            "Autonomous evolution",
            "AI-driven development",
            "Self-updating context system"
        ],
        "agent_capabilities": {
            "ai_feature_dev": "Can modify Python files, add features, update UI",
            "ai_database_manager": "Can create tables, optimize queries, add indexes",
            "ai_autofix": "Can fix compile errors, syntax issues",
            "social_agents": "Can post, comment, vote, discuss"
        }
    }
    
    return context


def save_context():
    """
    Save system context to JSON file.
    """
    context = generate_system_context()
    
    with open("system_context.json", "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
    
    return context


if __name__ == "__main__":
    context = save_context()
    print("✅ System context generated and saved!")
    print(f"⏰ Generated at: {context.get('generated_at')}")
    print(f"📊 Root files: {len(context['structure']['root_files'])}")
    print(f"📁 Directories: {len(context['structure']['directories'])}")
    print(f"🗄️ Tables: {len(context['database']['tables']) + len(context['database']['core_tables'])}")
    print(f"⚙️ Functions: {len(context['database']['functions'])}")
    print(f"🔄 Workflows: {len(context['workflows'])}")
    print(f"📝 Recent commits: {len(context['recent_changes'])}")
    print("\n💡 AI agents now have complete system knowledge!")
