"""
VIGIL - Agent Mode
Advanced autonomous agent capabilities for Vigil
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime

# Import task manager enums for type checking
try:
    from core.task_manager import TaskStatus, TaskPriority
except ImportError:
    # Define fallback if import fails during testing
    class TaskStatus:
        TODO = "todo"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        BLOCKED = "blocked"
        CANCELLED = "cancelled"
    
    class TaskPriority:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        URGENT = "urgent"


class AgentMode(Enum):
    """Agent operation modes."""
    PASSIVE = "passive"  # Only responds when explicitly called
    ACTIVE = "active"    # Proactively monitors and assists
    AUTONOMOUS = "autonomous"  # Fully autonomous task execution
    PROJECT_MANAGER = "project_manager"  # Active project management mode


@dataclass
class AgentTask:
    """Represents an autonomous task for the agent."""
    id: str
    description: str
    priority: int = 5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None


class AgentSystem:
    """
    Manages Vigil's agent modes and autonomous capabilities.
    
    Agent modes:
    - PASSIVE: Default mode, responds only to user input
    - ACTIVE: Monitors context and proactively offers assistance
    - AUTONOMOUS: Executes tasks independently
    - PROJECT_MANAGER: Actively manages projects, tracks commitments, reminds user
    """
    
    def __init__(self, brain=None, task_manager=None, memory=None):
        """Initialize agent system."""
        self.brain = brain
        self.task_manager = task_manager
        self.memory = memory
        
        self.current_mode = AgentMode.PASSIVE
        self.autonomous_tasks: Dict[str, AgentTask] = {}
        self.mode_callbacks: Dict[AgentMode, List[Callable]] = {
            mode: [] for mode in AgentMode
        }
        
        # Project manager specific settings
        self.pm_check_interval = 3600  # Check every hour
        self.pm_last_check = time.time()
        self.pm_active_projects: List[str] = []
        
        # Active monitoring flags
        self.monitoring_active = False
        self.monitoring_interval = 300  # 5 minutes
    
    def set_mode(self, mode: AgentMode) -> bool:
        """Set the agent operation mode."""
        if not isinstance(mode, AgentMode):
            return False
        
        old_mode = self.current_mode
        self.current_mode = mode
        
        print(f"[Agent] Mode changed: {old_mode.value} -> {mode.value}")
        
        # Trigger mode-specific setup
        if mode == AgentMode.PROJECT_MANAGER:
            self._activate_project_manager_mode()
        elif mode == AgentMode.ACTIVE:
            self._activate_active_mode()
        elif mode == AgentMode.AUTONOMOUS:
            self._activate_autonomous_mode()
        
        # Call registered callbacks
        for callback in self.mode_callbacks.get(mode, []):
            try:
                callback()
            except Exception as e:
                print(f"[Agent] Error in mode callback: {e}")
        
        return True
    
    def get_mode(self) -> AgentMode:
        """Get current agent mode."""
        return self.current_mode
    
    def register_mode_callback(self, mode: AgentMode, callback: Callable):
        """Register a callback for when a specific mode is activated."""
        if mode not in self.mode_callbacks:
            self.mode_callbacks[mode] = []
        self.mode_callbacks[mode].append(callback)
    
    def _activate_project_manager_mode(self):
        """Activate project manager mode."""
        print("[Agent] 🎯 Project Manager mode activated")
        print("[Agent] - Tracking commitments and deadlines")
        print("[Agent] - Monitoring project progress")
        print("[Agent] - Will proactively check in on tasks")
        
        self.monitoring_active = True
    
    def _activate_active_mode(self):
        """Activate active assistance mode."""
        print("[Agent] 🟢 Active mode enabled")
        print("[Agent] - Monitoring for opportunities to assist")
        print("[Agent] - Will offer suggestions proactively")
        
        self.monitoring_active = True
    
    def _activate_autonomous_mode(self):
        """Activate autonomous mode."""
        print("[Agent] 🤖 Autonomous mode enabled")
        print("[Agent] - Can execute tasks independently")
        print("[Agent] - Will report back on completion")
        
        self.monitoring_active = True
    
    def should_intervene(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Determine if agent should proactively intervene based on context.
        
        Returns:
            Optional message/suggestion if intervention is warranted
        """
        if self.current_mode == AgentMode.PASSIVE:
            return None
        
        # Project Manager interventions
        if self.current_mode == AgentMode.PROJECT_MANAGER:
            return self._check_project_manager_interventions(context)
        
        # Active mode interventions
        if self.current_mode == AgentMode.ACTIVE:
            return self._check_active_interventions(context)
        
        return None
    
    def _check_project_manager_interventions(self, context: Dict[str, Any]) -> Optional[str]:
        """Check if project manager should intervene."""
        current_time = time.time()
        
        # Check if enough time has passed since last check
        if current_time - self.pm_last_check < self.pm_check_interval:
            return None
        
        self.pm_last_check = current_time
        
        if not self.task_manager:
            return None
        
        # Check for overdue tasks
        todos = self.task_manager.list_tasks(status=TaskStatus.TODO)
        urgent_tasks = [t for t in todos if t.priority in [TaskPriority.URGENT, TaskPriority.HIGH]]
        
        if urgent_tasks:
            tasks_list = ", ".join([t.title for t in urgent_tasks[:3]])
            return f"Hey, you have {len(urgent_tasks)} urgent task(s) that need attention: {tasks_list}"
        
        # Check for blocked tasks
        blocked = self.task_manager.list_tasks(status=TaskStatus.BLOCKED)
        if blocked:
            return f"I notice you have {len(blocked)} blocked task(s). Need help unblocking them?"
        
        return None
    
    def _check_active_interventions(self, context: Dict[str, Any]) -> Optional[str]:
        """Check if active agent should offer assistance."""
        # Look for patterns that might need help
        if context.get("error_detected"):
            return "I noticed an error. Would you like me to help troubleshoot?"
        
        if context.get("repetitive_action"):
            return "I see you're doing this repeatedly. Want me to automate it?"
        
        return None
    
    def queue_autonomous_task(
        self,
        description: str,
        priority: int = 5,
        **kwargs
    ) -> AgentTask:
        """Queue a task for autonomous execution."""
        import uuid
        task_id = str(uuid.uuid4())
        
        task = AgentTask(
            id=task_id,
            description=description,
            priority=priority,
            **kwargs
        )
        
        self.autonomous_tasks[task_id] = task
        return task
    
    def execute_autonomous_task(self, task_id: str) -> bool:
        """Execute an autonomous task."""
        task = self.autonomous_tasks.get(task_id)
        if not task:
            return False
        
        if self.current_mode != AgentMode.AUTONOMOUS:
            print(f"[Agent] Cannot execute autonomous task in {self.current_mode.value} mode")
            return False
        
        task.status = "running"
        
        try:
            # Use brain to figure out how to execute the task
            if self.brain:
                prompt = f"""As an autonomous agent, execute this task:
                
Task: {task.description}

Break it down into steps and execute them. Report the result.
"""
                response = self.brain.think(prompt)
                
                if response:
                    task.result = response.text
                    task.status = "completed"
                    return True
            
            task.status = "failed"
            task.error = "No brain available"
            return False
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an autonomous task."""
        task = self.autonomous_tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "description": task.description,
            "status": task.status,
            "result": task.result,
            "error": task.error
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get current agent capabilities based on mode."""
        base_capabilities = {
            "voice_interaction": True,
            "knowledge_base": True,
            "memory": True,
        }
        
        mode_capabilities = {
            AgentMode.PASSIVE: {
                "proactive_assistance": False,
                "autonomous_execution": False,
                "project_tracking": False,
            },
            AgentMode.ACTIVE: {
                "proactive_assistance": True,
                "autonomous_execution": False,
                "project_tracking": False,
                "context_monitoring": True,
            },
            AgentMode.AUTONOMOUS: {
                "proactive_assistance": True,
                "autonomous_execution": True,
                "project_tracking": False,
                "task_queuing": True,
            },
            AgentMode.PROJECT_MANAGER: {
                "proactive_assistance": True,
                "autonomous_execution": False,
                "project_tracking": True,
                "deadline_monitoring": True,
                "commitment_tracking": True,
            }
        }
        
        return {
            **base_capabilities,
            **mode_capabilities.get(self.current_mode, {}),
            "current_mode": self.current_mode.value
        }
    
    def get_status_summary(self) -> str:
        """Get a summary of agent status."""
        capabilities = self.get_capabilities()
        
        summary = f"""Agent Status:
Mode: {self.current_mode.value.upper()}

Capabilities:
"""
        for cap, enabled in capabilities.items():
            if cap != "current_mode":
                status = "✓" if enabled else "✗"
                cap_name = cap.replace("_", " ").title()
                summary += f"  {status} {cap_name}\n"
        
        if self.autonomous_tasks:
            pending = len([t for t in self.autonomous_tasks.values() if t.status == "pending"])
            running = len([t for t in self.autonomous_tasks.values() if t.status == "running"])
            summary += f"\nQueued Tasks: {pending} pending, {running} running"
        
        return summary


if __name__ == "__main__":
    # Test agent system
    agent = AgentSystem()
    
    print("Testing Agent System...")
    print("=" * 50)
    
    print("\nInitial mode:", agent.get_mode().value)
    
    print("\nSwitching to ACTIVE mode...")
    agent.set_mode(AgentMode.ACTIVE)
    
    print("\nCapabilities:")
    caps = agent.get_capabilities()
    for cap, enabled in caps.items():
        print(f"  {cap}: {enabled}")
    
    print("\nSwitching to PROJECT_MANAGER mode...")
    agent.set_mode(AgentMode.PROJECT_MANAGER)
    
    print("\nStatus summary:")
    print(agent.get_status_summary())
