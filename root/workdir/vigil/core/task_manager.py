"""
VIGIL - Task Manager
Manages tasks and projects across multiple platforms
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum


class TaskStatus(Enum):
    """Task status states."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task:
    """Represents a single task."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    platform: Optional[str] = None  # Which platform this task is from/synced to
    platform_id: Optional[str] = None  # ID on the external platform
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create task from dictionary."""
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])
        if isinstance(data.get('priority'), str):
            data['priority'] = TaskPriority(data['priority'])
        return cls(**data)


@dataclass
class Project:
    """Represents a project containing multiple tasks."""
    id: str
    name: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tasks: List[str] = field(default_factory=list)  # List of task IDs
    platform: Optional[str] = None
    platform_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert project to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Project':
        """Create project from dictionary."""
        return cls(**data)


class TaskManager:
    """
    Manages tasks and projects for Vigil.
    Provides CRUD operations and syncing with external platforms.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize task manager."""
        self.storage_path = storage_path or Path.home() / ".vigil" / "tasks"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.tasks_file = self.storage_path / "tasks.json"
        self.projects_file = self.storage_path / "projects.json"
        
        self.tasks: Dict[str, Task] = {}
        self.projects: Dict[str, Project] = {}
        
        self._load_data()

    def _load_data(self):
        """Load tasks and projects from disk."""
        # Load tasks
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                    self.tasks = {
                        task_id: Task.from_dict(task_data)
                        for task_id, task_data in tasks_data.items()
                    }
            except Exception as e:
                print(f"Error loading tasks: {e}")

        # Load projects
        if self.projects_file.exists():
            try:
                with open(self.projects_file, 'r') as f:
                    projects_data = json.load(f)
                    self.projects = {
                        proj_id: Project.from_dict(proj_data)
                        for proj_id, proj_data in projects_data.items()
                    }
            except Exception as e:
                print(f"Error loading projects: {e}")

    def _save_data(self):
        """Save tasks and projects to disk."""
        # Save tasks
        try:
            with open(self.tasks_file, 'w') as f:
                tasks_data = {
                    task_id: task.to_dict()
                    for task_id, task in self.tasks.items()
                }
                json.dump(tasks_data, f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")

        # Save projects
        try:
            with open(self.projects_file, 'w') as f:
                projects_data = {
                    proj_id: proj.to_dict()
                    for proj_id, proj in self.projects.items()
                }
                json.dump(projects_data, f, indent=2)
        except Exception as e:
            print(f"Error saving projects: {e}")

    # Task CRUD operations
    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        platform: Optional[str] = None,
        **kwargs
    ) -> Task:
        """Create a new task."""
        import uuid
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            tags=tags or [],
            platform=platform,
            **kwargs
        )
        
        self.tasks[task_id] = task
        self._save_data()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """Update a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now().isoformat()
        self._save_data()
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_data()
            return True
        return False

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        platform: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Task]:
        """List tasks with optional filtering."""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if platform:
            tasks = [t for t in tasks if t.platform == platform]
        
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        
        return tasks

    # Project CRUD operations
    def create_project(
        self,
        name: str,
        description: str = "",
        platform: Optional[str] = None,
        **kwargs
    ) -> Project:
        """Create a new project."""
        import uuid
        project_id = str(uuid.uuid4())
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            platform=platform,
            **kwargs
        )
        
        self.projects[project_id] = project
        self._save_data()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.projects.get(project_id)

    def update_project(self, project_id: str, **updates) -> Optional[Project]:
        """Update a project."""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.now().isoformat()
        self._save_data()
        return project

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self.projects:
            del self.projects[project_id]
            self._save_data()
            return True
        return False

    def add_task_to_project(self, project_id: str, task_id: str) -> bool:
        """Add a task to a project."""
        project = self.projects.get(project_id)
        if not project or task_id not in self.tasks:
            return False
        
        if task_id not in project.tasks:
            project.tasks.append(task_id)
            project.updated_at = datetime.now().isoformat()
            self._save_data()
        
        return True

    def get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks for a project."""
        project = self.projects.get(project_id)
        if not project:
            return []
        
        return [self.tasks[task_id] for task_id in project.tasks if task_id in self.tasks]

    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        total_tasks = len(self.tasks)
        completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        in_progress = len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS])
        blocked = len([t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED])
        todo = len([t for t in self.tasks.values() if t.status == TaskStatus.TODO])
        cancelled = len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED])
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "todo": todo,
            "cancelled": cancelled,
            "total_projects": len(self.projects),
            "completion_rate": (completed / total_tasks * 100) if total_tasks > 0 else 0
        }


if __name__ == "__main__":
    # Test the task manager
    tm = TaskManager()
    
    print("Creating test tasks...")
    task1 = tm.create_task(
        title="Test Task 1",
        description="This is a test task",
        priority=TaskPriority.HIGH,
        tags=["test", "example"]
    )
    print(f"Created task: {task1.id} - {task1.title}")
    
    task2 = tm.create_task(
        title="Test Task 2",
        description="Another test task",
        priority=TaskPriority.LOW
    )
    print(f"Created task: {task2.id} - {task2.title}")
    
    print("\nCreating test project...")
    project = tm.create_project(
        name="Test Project",
        description="A test project"
    )
    print(f"Created project: {project.id} - {project.name}")
    
    print("\nAdding tasks to project...")
    tm.add_task_to_project(project.id, task1.id)
    tm.add_task_to_project(project.id, task2.id)
    
    print("\nProject tasks:")
    for task in tm.get_project_tasks(project.id):
        print(f"  - {task.title} ({task.status.value})")
    
    print("\nStats:")
    stats = tm.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
