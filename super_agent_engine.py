"""
EYAVAP Super Agent Engine
Combines best features from ReAct, AutoGPT, BabyAGI, CrewAI, AutoGen, and LangGraph
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from supabase import create_client


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentRole(Enum):
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"


@dataclass
class Task:
    """Single task unit (BabyAGI style)"""
    id: str
    goal: str
    priority: int
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)  # ReAct thought trace
    actions: List[Dict] = field(default_factory=list)  # ReAct actions
    observations: List[str] = field(default_factory=list)  # ReAct observations
    result: Optional[Dict] = None
    checkpoint_data: Dict = field(default_factory=dict)  # LangGraph checkpointing
    created_at: float = field(default_factory=time.time)
    
    def add_reasoning(self, thought: str):
        """Add reasoning step (ReAct)"""
        self.reasoning.append(f"[{datetime.now().isoformat()}] {thought}")
    
    def add_action(self, action: Dict):
        """Add action taken (ReAct)"""
        self.actions.append({**action, "timestamp": datetime.now().isoformat()})
    
    def add_observation(self, observation: str):
        """Add observation from environment (ReAct)"""
        self.observations.append(f"[{datetime.now().isoformat()}] {observation}")
    
    def save_checkpoint(self):
        """Save current state (LangGraph)"""
        self.checkpoint_data = {
            "status": self.status.value,
            "reasoning_count": len(self.reasoning),
            "actions_count": len(self.actions),
            "timestamp": datetime.now().isoformat()
        }


@dataclass
class Mission:
    """High-level mission (AutoGPT style goal)"""
    id: str
    objective: str
    context: Dict
    tasks: List[Task] = field(default_factory=list)
    status: str = "active"
    collaboration_requests: List[Dict] = field(default_factory=list)  # AutoGen style
    memory: Dict = field(default_factory=dict)  # Short-term memory
    created_at: float = field(default_factory=time.time)


class SuperAgentEngine:
    """
    Hybrid Agent Engine combining:
    - ReAct: Reasoning + Acting with thought traces
    - AutoGPT: Goal decomposition, memory, iterative refinement
    - BabyAGI: Task generation and prioritization
    - CrewAI: Role-based collaboration and delegation
    - AutoGen: Multi-agent conversation and code execution
    - LangGraph: State graphs, checkpointing, cyclic workflows
    """
    
    def __init__(self):
        self.supabase = self._get_supabase()
        self.missions: Dict[str, Mission] = {}
        self.agent_roles: Dict[str, AgentRole] = {}  # agent_id -> role
        self.global_memory: Dict[str, Any] = {}  # Long-term memory (AutoGPT)
        
    def _get_supabase(self):
        """Get Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")
        return create_client(url, key)
    
    def _get_openai_client(self):
        """Get OpenAI client for AI operations"""
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY")
        return OpenAI(api_key=api_key)
    
    def _assign_roles(self, agents: List[Dict]) -> Dict[str, AgentRole]:
        """Assign roles to agents based on specialization (CrewAI style)"""
        roles = {}
        for agent in agents:
            spec = agent.get("specialization", "").lower()
            
            if any(w in spec for w in ["forskning", "research", "analyse"]):
                roles[agent["id"]] = AgentRole.RESEARCHER
            elif any(w in spec for w in ["data", "statistik", "teknologi"]):
                roles[agent["id"]] = AgentRole.ANALYZER
            elif any(w in spec for w in ["politik", "ledelse", "økonomi"]):
                roles[agent["id"]] = AgentRole.IMPLEMENTER
            elif any(w in spec for w in ["kvalitet", "overvågning"]):
                roles[agent["id"]] = AgentRole.REVIEWER
            else:
                roles[agent["id"]] = AgentRole.COORDINATOR
        
        return roles
    
    def create_mission(self, objective: str, context: Dict = None) -> str:
        """
        Create new mission (AutoGPT style)
        Returns mission_id
        """
        mission_id = hashlib.md5(f"{objective}{time.time()}".encode()).hexdigest()[:12]
        mission = Mission(
            id=mission_id,
            objective=objective,
            context=context or {}
        )
        self.missions[mission_id] = mission
        
        # Log to database
        try:
            self.supabase.table("ai_activity_log").insert({
                "task_name": f"mission_created",
                "task_type": "super_agent",
                "status": "created",
                "result": {"mission_id": mission_id, "objective": objective}
            }).execute()
        except:
            pass
        
        return mission_id
    
    def decompose_goal(self, mission_id: str, max_tasks: int = 10) -> List[Task]:
        """
        Decompose mission into tasks (BabyAGI + AutoGPT style)
        Uses AI to intelligently break down the goal
        """
        mission = self.missions.get(mission_id)
        if not mission:
            return []
        
        client = self._get_openai_client()
        
        prompt = f"""Du er EYAVAP Mission Planner. Nedbryd dette mål i konkrete opgaver.

MÅL: {mission.objective}
KONTEKST: {json.dumps(mission.context, indent=2)}

Opret 3-{max_tasks} opgaver med:
1. Klar beskrivelse
2. Prioritet (1-10, hvor 10 er højest)
3. Afhængigheder (hvilke opgaver skal fuldføres først)

JSON format:
{{
  "tasks": [
    {{
      "goal": "opgave beskrivelse",
      "priority": 8,
      "dependencies": []
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        data = json.loads(response.choices[0].message.content)
        tasks = []
        
        for i, task_data in enumerate(data.get("tasks", [])[:max_tasks]):
            task = Task(
                id=f"{mission_id}_task_{i+1}",
                goal=task_data.get("goal", ""),
                priority=task_data.get("priority", 5),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        mission.tasks = tasks
        return tasks
    
    def assign_task(self, task: Task, agents: List[Dict]) -> Optional[str]:
        """
        Assign task to best-fit agent (CrewAI style role matching)
        Returns agent_id
        """
        if not agents:
            return None
        
        # Ensure roles are assigned
        if not self.agent_roles:
            self.agent_roles = self._assign_roles(agents)
        
        # Simple matching: find agent with highest merit score in relevant role
        # (In production, use more sophisticated matching)
        sorted_agents = sorted(agents, key=lambda a: a.get("merit_score", 0), reverse=True)
        
        for agent in sorted_agents:
            if agent["id"] not in [t.assigned_to for m in self.missions.values() for t in m.tasks if t.status == TaskStatus.IN_PROGRESS]:
                task.assigned_to = agent["id"]
                task.status = TaskStatus.IN_PROGRESS
                return agent["id"]
        
        return None
    
    def execute_task_react(self, task: Task, agent: Dict, max_iterations: int = 5) -> Dict:
        """
        Execute task using ReAct loop (Reasoning + Acting)
        Think → Act → Observe → (repeat)
        """
        client = self._get_openai_client()
        
        for iteration in range(max_iterations):
            # THINK: Reasoning step
            think_prompt = f"""Du er agent {agent.get('name')} ({agent.get('specialization')}).

OPGAVE: {task.goal}
TIDLIGERE TANKER: {json.dumps(task.reasoning[-3:], indent=2) if task.reasoning else "Ingen"}
TIDLIGERE HANDLINGER: {json.dumps(task.actions[-3:], indent=2) if task.actions else "Ingen"}
OBSERVATIONER: {json.dumps(task.observations[-3:], indent=2) if task.observations else "Ingen"}

TÆNK: Hvad er næste logiske skridt? Skal du:
1. Indsamle mere information?
2. Analysere data?
3. Tage en handling?
4. Afslutte opgaven?

Svar kort på dansk (max 100 ord)."""

            think_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": think_prompt}],
                temperature=0.7,
                max_tokens=150
            )
            
            thought = think_response.choices[0].message.content
            task.add_reasoning(thought)
            
            # Check if task should be completed
            if any(word in thought.lower() for word in ["afslut", "færdig", "komplet", "done"]):
                task.status = TaskStatus.COMPLETED
                task.result = {"final_thought": thought}
                break
            
            # ACT: Determine action
            act_prompt = f"""Baseret på din tanke: "{thought}"

HANDLING: Vælg én handling at udføre:
- "research": Undersøg emnet
- "analyze": Analyser data
- "create": Opret indhold
- "review": Gennemgå kvalitet
- "delegate": Bed anden agent om hjælp
- "complete": Afslut opgaven

JSON format:
{{
  "action": "research",
  "details": "kort beskrivelse"
}}"""

            act_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": act_prompt}],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            action = json.loads(act_response.choices[0].message.content)
            task.add_action(action)
            
            # OBSERVE: Simulate environment feedback
            observation = self._simulate_action_result(action, task, agent)
            task.add_observation(observation)
            
            # Save checkpoint (LangGraph style)
            task.save_checkpoint()
            
            # Check if action was "complete"
            if action.get("action") == "complete":
                task.status = TaskStatus.COMPLETED
                task.result = {"action": action, "observation": observation}
                break
        
        return task.result or {"status": "max_iterations_reached"}
    
    def _simulate_action_result(self, action: Dict, task: Task, agent: Dict) -> str:
        """
        Simulate environment feedback for action (ReAct observe step)
        In production, this would execute actual tools/APIs
        """
        action_type = action.get("action", "unknown")
        details = action.get("details", "")
        
        responses = {
            "research": f"✅ Forskning udført: {details}. Fandt 5 relevante kilder.",
            "analyze": f"✅ Analyse komplet: {details}. Identificeret 3 nøglepunkter.",
            "create": f"✅ Indhold oprettet: {details}. Klar til review.",
            "review": f"✅ Review gennemført: {details}. Kvalitetsscore: 8/10.",
            "delegate": f"✅ Delegeret til specialist: {details}. Afventer svar.",
            "complete": f"✅ Opgave fuldført: {details}."
        }
        
        return responses.get(action_type, f"❓ Ukendt handling: {action_type}")
    
    def request_collaboration(self, mission_id: str, requester_id: str, request: str) -> Dict:
        """
        Multi-agent collaboration (AutoGen style)
        One agent requests help from others
        """
        mission = self.missions.get(mission_id)
        if not mission:
            return {"error": "Mission not found"}
        
        collab_request = {
            "id": hashlib.md5(f"{requester_id}{request}{time.time()}".encode()).hexdigest()[:8],
            "requester": requester_id,
            "request": request,
            "status": "pending",
            "responses": [],
            "created_at": datetime.now().isoformat()
        }
        
        mission.collaboration_requests.append(collab_request)
        
        # In production, this would notify other agents and collect responses
        return collab_request
    
    def run_mission(self, mission_id: str, max_concurrent_tasks: int = 3) -> Dict:
        """
        Execute entire mission (combines all approaches)
        1. Decompose goal (AutoGPT + BabyAGI)
        2. Assign tasks (CrewAI)
        3. Execute with ReAct loop
        4. Enable collaboration (AutoGen)
        5. Checkpoint progress (LangGraph)
        """
        mission = self.missions.get(mission_id)
        if not mission:
            return {"error": "Mission not found"}
        
        # Step 1: Decompose goal into tasks
        if not mission.tasks:
            self.decompose_goal(mission_id)
        
        # Step 2: Get available agents
        agents_res = self.supabase.table("agents").select("*").eq("status", "active").limit(50).execute()
        agents = agents_res.data or []
        
        # Step 3: Execute tasks
        results = []
        for task in mission.tasks:
            # Skip if has unfulfilled dependencies
            if any(dep_id not in [t.id for t in mission.tasks if t.status == TaskStatus.COMPLETED] for dep_id in task.dependencies):
                task.status = TaskStatus.BLOCKED
                continue
            
            # Assign to agent
            if not task.assigned_to:
                agent_id = self.assign_task(task, agents)
                if not agent_id:
                    continue
            
            # Execute with ReAct
            agent = next((a for a in agents if a["id"] == task.assigned_to), None)
            if agent:
                result = self.execute_task_react(task, agent)
                results.append({
                    "task_id": task.id,
                    "status": task.status.value,
                    "result": result
                })
        
        # Step 4: Update mission status
        all_completed = all(t.status in [TaskStatus.COMPLETED, TaskStatus.BLOCKED] for t in mission.tasks)
        if all_completed:
            mission.status = "completed"
        
        # Step 5: Log results
        try:
            self.supabase.table("ai_activity_log").insert({
                "task_name": f"mission_execution",
                "task_type": "super_agent",
                "status": mission.status,
                "result": {
                    "mission_id": mission_id,
                    "tasks_completed": sum(1 for r in results if r["status"] == "completed"),
                    "total_tasks": len(mission.tasks)
                }
            }).execute()
        except:
            pass
        
        return {
            "mission_id": mission_id,
            "status": mission.status,
            "tasks": results,
            "collaboration_requests": len(mission.collaboration_requests)
        }
    
    def get_mission_state(self, mission_id: str) -> Dict:
        """Get full mission state (for debugging/monitoring)"""
        mission = self.missions.get(mission_id)
        if not mission:
            return {"error": "Mission not found"}
        
        return {
            "id": mission.id,
            "objective": mission.objective,
            "status": mission.status,
            "tasks": [
                {
                    "id": t.id,
                    "goal": t.goal,
                    "status": t.status.value,
                    "assigned_to": t.assigned_to,
                    "reasoning_steps": len(t.reasoning),
                    "actions_taken": len(t.actions),
                    "observations": len(t.observations)
                }
                for t in mission.tasks
            ],
            "collaboration_requests": len(mission.collaboration_requests),
            "memory_items": len(mission.memory)
        }


# Convenience function for quick missions
def execute_mission(objective: str, context: Dict = None) -> Dict:
    """
    One-shot mission execution
    Usage: result = execute_mission("Analyser klimaforandringer i Danmark")
    """
    engine = SuperAgentEngine()
    mission_id = engine.create_mission(objective, context)
    result = engine.run_mission(mission_id)
    return result


if __name__ == "__main__":
    # Test run
    print("🚀 EYAVAP Super Agent Engine initialized")
    print("Combining: ReAct + AutoGPT + BabyAGI + CrewAI + AutoGen + LangGraph")
    
    # Example mission
    engine = SuperAgentEngine()
    mission_id = engine.create_mission(
        objective="Analyser de vigtigste politiske emner i Danmark denne uge",
        context={"timeframe": "7 days", "focus": "politik"}
    )
    
    print(f"\n📋 Mission created: {mission_id}")
    print(f"Objective: {engine.missions[mission_id].objective}")
    
    # Run mission
    result = engine.run_mission(mission_id)
    print(f"\n✅ Mission result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
