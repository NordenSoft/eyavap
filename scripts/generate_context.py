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
    """
    schema = {
        "tables": {},
        "functions": [],
        "triggers": []
    }
    
    # Read all migration files
    migration_files = [
        "migration_governance.sql",
        "migration_learning_system.sql",
        "migration_reports_revision.sql",
        "migration_revision_ai.sql",
        "migration_presidential_election.sql",
        "migration_ai_database_manager.sql"
    ]
    
    for mig_file in migration_files:
        if os.path.exists(mig_file):
            with open(mig_file, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Extract table names (simple parsing)
                import re
                tables = re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", content)
                for table in tables:
                    schema["tables"][table] = {"source": mig_file}
                
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


def generate_system_context():
    """
    Generate complete system context for AI agents.
    """
    context = {
        "project_name": "EYAVAP",
        "description": "Self-evolving AI agent community with 999 Danish expert agents",
        "structure": get_project_structure(),
        "database": get_database_schema(),
        "key_files": get_key_files_summary(),
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
            "AI-driven development"
        ]
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
    print("✅ System context generated!")
    print(f"📊 Files: {len(context['structure']['root_files'])}")
    print(f"📁 Directories: {len(context['structure']['directories'])}")
    print(f"🗄️ Tables: {len(context['database']['tables'])}")
    print(f"⚙️ Functions: {len(context['database']['functions'])}")
