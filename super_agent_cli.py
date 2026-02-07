#!/usr/bin/env python3
"""
EYAVAP Super Agent CLI
Quick access to super agent missions
"""

import sys
import json
from super_agent_engine import SuperAgentEngine, execute_mission


def print_help():
    print("""
🚀 EYAVAP Super Agent CLI

Kullanım:
  python super_agent_cli.py mission "<objective>"     # Yeni mission başlat
  python super_agent_cli.py status <mission_id>       # Mission durumunu görüntüle
  python super_agent_cli.py quick "<objective>"       # Hızlı one-shot mission

Örnekler:
  python super_agent_cli.py mission "Analyser klimaforandringer i Danmark"
  python super_agent_cli.py status abc123def456
  python super_agent_cli.py quick "Find de bedste AI-artikler denne uge"

Özellikler:
  ✓ ReAct: Reasoning + Acting döngüsü
  ✓ AutoGPT: Görev ayrıştırma ve hafıza
  ✓ BabyAGI: Önceliklendirme
  ✓ CrewAI: Rol-bazlı işbirliği
  ✓ AutoGen: Multi-agent sohbet
  ✓ LangGraph: Checkpoint sistemi
    """)


def run_mission(objective: str):
    """Start new mission with full tracking"""
    print(f"\n🚀 Starting mission: {objective}\n")
    
    engine = SuperAgentEngine()
    mission_id = engine.create_mission(objective)
    
    print(f"📋 Mission ID: {mission_id}")
    print("⏳ Decomposing goal into tasks...")
    
    engine.decompose_goal(mission_id)
    tasks = engine.missions[mission_id].tasks
    print(f"✓ Created {len(tasks)} tasks\n")
    
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. {task.goal} (Priority: {task.priority})")
    
    print(f"\n⏳ Executing mission...")
    result = engine.run_mission(mission_id)
    
    print(f"\n✅ Mission completed!")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result


def get_status(mission_id: str):
    """Get mission status"""
    engine = SuperAgentEngine()
    
    if mission_id not in engine.missions:
        print(f"❌ Mission {mission_id} not found")
        return
    
    state = engine.get_mission_state(mission_id)
    print(f"\n📊 Mission Status: {mission_id}\n")
    print(json.dumps(state, indent=2, ensure_ascii=False))


def quick_mission(objective: str):
    """Quick one-shot mission"""
    print(f"\n⚡ Quick mission: {objective}\n")
    result = execute_mission(objective)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help" or command == "--help" or command == "-h":
        print_help()
    
    elif command == "mission":
        if len(sys.argv) < 3:
            print("❌ Missing objective. Usage: python super_agent_cli.py mission \"<objective>\"")
            return
        objective = sys.argv[2]
        run_mission(objective)
    
    elif command == "status":
        if len(sys.argv) < 3:
            print("❌ Missing mission_id. Usage: python super_agent_cli.py status <mission_id>")
            return
        mission_id = sys.argv[2]
        get_status(mission_id)
    
    elif command == "quick":
        if len(sys.argv) < 3:
            print("❌ Missing objective. Usage: python super_agent_cli.py quick \"<objective>\"")
            return
        objective = sys.argv[2]
        quick_mission(objective)
    
    else:
        print(f"❌ Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
