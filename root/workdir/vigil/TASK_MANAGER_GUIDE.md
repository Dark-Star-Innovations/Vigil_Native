# Task Manager and Service Connectors

## Overview

Vigil now includes comprehensive task management capabilities and service integration connectors, transforming it into a powerful project management assistant.

## Features

### 1. Task Management

Vigil can now create, track, and manage tasks across different platforms.

#### Creating Tasks

**Voice Command:**
```
"Vigil, create a new task"
"Vigil, add task"
```

**Programmatic:**
```python
from core.task_manager import TaskManager, TaskPriority

tm = TaskManager()
task = tm.create_task(
    title="Complete project documentation",
    description="Write comprehensive docs for new features",
    priority=TaskPriority.HIGH,
    tags=["documentation", "urgent"]
)
```

#### Listing Tasks

**Voice Command:**
```
"Vigil, list my tasks"
"Vigil, show tasks"
```

**Programmatic:**
```python
# List all tasks
all_tasks = tm.list_tasks()

# Filter by status
from core.task_manager import TaskStatus
todo_tasks = tm.list_tasks(status=TaskStatus.TODO)

# Filter by platform
github_tasks = tm.list_tasks(platform="github")
```

#### Task Properties

- **ID**: Unique identifier
- **Title**: Task name
- **Description**: Detailed description
- **Status**: `todo`, `in_progress`, `completed`, `blocked`, `cancelled`
- **Priority**: `low`, `medium`, `high`, `urgent`
- **Tags**: Custom tags for organization
- **Platform**: Associated platform (if synced)
- **Due Date**: Optional deadline
- **Metadata**: Custom data storage

### 2. Service Connectors

Vigil can connect to various platforms and services.

#### Pre-configured Platforms

The following platforms have pre-configured connectors:

- **Project Management**: Taskade
- **Social Media**: YouTube, Facebook, X (Twitter)
- **Development**: GitHub, Replit, VS Code
- **E-commerce**: Shopify, eBay, Stripe
- **AI/ML**: OpenAI, Google AI Studio, Runway
- **Creative**: CapCut, Canva, Veo3
- **Cloud**: AWS
- **Communication**: Gmail, Lovable
- **Data**: Base44

#### Adding Connectors

**Via Environment Variables:**
```env
# .env file
GITHUB_TOKEN=your_github_token_here
TASKADE_API_KEY=your_taskade_key_here
OPENAI_API_KEY=your_openai_key_here
```

**Via Voice Command:**
```
"Vigil, add connector"
# Then follow the prompts
```

**Programmatically:**
```python
from core.service_connectors import ConnectorManager

cm = ConnectorManager()

# Add a pre-configured platform
cm.add_platform_connector("github", "ghp_yourtoken")

# Add a custom connector
cm.add_custom_connector(
    name="MyAPI",
    url="https://api.example.com",
    api_key="your_api_key",
    auth_type="bearer"
)
```

#### Custom URL Connectors

For unorthodox or custom websites:

```python
from core.service_connectors import CustomConnector

connector = CustomConnector(
    name="Custom Service",
    url="https://your-service.com/api",
    api_key="optional_key",
    custom_headers={
        "X-Custom-Header": "value"
    },
    auth_type="bearer"  # or "basic", "api-key", "custom"
)

# Test connection
if connector.test_connection():
    print("Connected!")

# Get data
data = connector.get_data("endpoint/path")

# Post data
result = connector.post_data("endpoint/path", {"key": "value"})
```

### 3. Agent Modes

Vigil supports multiple operating modes for different use cases.

#### Available Modes

**PASSIVE** (Default)
- Only responds when explicitly called
- No proactive assistance
- Minimal system overhead

**ACTIVE**
- Monitors context for opportunities to assist
- Offers suggestions proactively
- Helpful for ongoing work

**AUTONOMOUS**
- Can execute tasks independently
- Queues and completes work without constant supervision
- Reports results when done

**PROJECT_MANAGER**
- Actively tracks commitments and deadlines
- Reminds you of urgent tasks
- Monitors project progress
- Keeps you accountable

#### Switching Modes

**Voice Commands:**
```
"Vigil, activate agent mode passive"
"Vigil, set agent mode to active"
"Vigil, enable autonomous mode"
"Vigil, activate project manager mode"
```

**Programmatically:**
```python
from core.agent_mode import AgentSystem, AgentMode

agent = AgentSystem(brain=brain, task_manager=tm, memory=memory)

# Set mode
agent.set_mode(AgentMode.PROJECT_MANAGER)

# Check current mode
current = agent.get_mode()
print(f"Current mode: {current.value}")

# Get capabilities
caps = agent.get_capabilities()
```

### 4. Always-On-Top Interface

A persistent overlay window for quick access to Vigil.

#### Features

- **Always visible**: Stays on top of other windows
- **Quick chat**: Send messages without voice
- **Task list**: View and manage tasks
- **Keyboard shortcut**: `Ctrl+Shift+V` to show/hide

#### Opening the Interface

**Voice Command:**
```
"Vigil, show interface"
"Vigil, open project manager"
```

**Programmatically:**
```python
from core.always_on_top import AlwaysOnTopInterface

def handle_message(msg: str) -> str:
    return process_message(msg)

interface = AlwaysOnTopInterface(
    on_message_callback=handle_message
)
interface.start()
```

## Usage Examples

### Example 1: Project Management Workflow

```python
# Initialize components
from core.task_manager import TaskManager, TaskPriority
from core.agent_mode import AgentSystem, AgentMode

tm = TaskManager()
agent = AgentSystem(task_manager=tm)

# Create a project
project = tm.create_project(
    name="Website Redesign",
    description="Redesign company website with modern UI"
)

# Add tasks
task1 = tm.create_task(
    title="Design mockups",
    priority=TaskPriority.HIGH,
    tags=["design", "ui"]
)

task2 = tm.create_task(
    title="Implement frontend",
    priority=TaskPriority.MEDIUM,
    tags=["development", "react"]
)

# Add tasks to project
tm.add_task_to_project(project.id, task1.id)
tm.add_task_to_project(project.id, task2.id)

# Activate project manager mode
agent.set_mode(AgentMode.PROJECT_MANAGER)

# Get project stats
stats = tm.get_stats()
print(f"Completion rate: {stats['completion_rate']}%")
```

### Example 2: Multi-Platform Integration

```python
from core.service_connectors import ConnectorManager
from core.task_manager import TaskManager

cm = ConnectorManager()
tm = TaskManager()

# Connect to GitHub
cm.add_platform_connector("github", "your_token")

# Connect to Taskade
cm.add_platform_connector("taskade", "your_taskade_key")

# Sync tasks from GitHub issues (conceptual)
github = cm.get_connector("github")
if github:
    issues = github.get_data("repos/user/repo/issues")
    
    # Create local tasks from issues
    for issue in issues:
        tm.create_task(
            title=issue['title'],
            description=issue['body'],
            platform="github",
            platform_id=str(issue['id'])
        )
```

### Example 3: Autonomous Task Execution

```python
from core.agent_mode import AgentSystem, AgentMode
from core.brain import Brain

brain = Brain()
agent = AgentSystem(brain=brain)

# Switch to autonomous mode
agent.set_mode(AgentMode.AUTONOMOUS)

# Queue a task
task = agent.queue_autonomous_task(
    description="Research the latest React best practices and summarize",
    priority=8
)

# Execute the task
agent.execute_autonomous_task(task.id)

# Check status
status = agent.get_task_status(task.id)
print(f"Status: {status['status']}")
print(f"Result: {status['result']}")
```

## Configuration

### Environment Variables

Create a `.env` file in the config directory:

```env
# Existing Vigil settings
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...

# Service connectors
GITHUB_TOKEN=ghp_...
TASKADE_API_KEY=...
YOUTUBE_API_KEY=...
FACEBOOK_ACCESS_TOKEN=...
STRIPE_API_KEY=sk_...
SHOPIFY_ACCESS_TOKEN=...
GMAIL_API_KEY=...
CANVA_API_KEY=...
AWS_ACCESS_KEY=...
```

### Storage Locations

- **Tasks**: `~/.vigil/tasks/tasks.json`
- **Projects**: `~/.vigil/tasks/projects.json`
- **Connectors**: `~/.vigil/connectors/connectors.json`

## API Reference

### TaskManager

```python
class TaskManager:
    def create_task(title, description="", priority=MEDIUM, **kwargs) -> Task
    def get_task(task_id) -> Optional[Task]
    def update_task(task_id, **updates) -> Optional[Task]
    def delete_task(task_id) -> bool
    def list_tasks(status=None, platform=None, tags=None) -> List[Task]
    
    def create_project(name, description="", **kwargs) -> Project
    def add_task_to_project(project_id, task_id) -> bool
    def get_project_tasks(project_id) -> List[Task]
    def get_stats() -> Dict[str, Any]
```

### ConnectorManager

```python
class ConnectorManager:
    def add_platform_connector(platform, api_key, **kwargs) -> bool
    def add_custom_connector(name, url, api_key=None, **kwargs) -> bool
    def get_connector(name) -> Optional[ServiceConnector]
    def list_connectors() -> List[str]
    def test_connector(name) -> bool
    def remove_connector(name) -> bool
    def get_available_platforms() -> List[str]
```

### AgentSystem

```python
class AgentSystem:
    def set_mode(mode: AgentMode) -> bool
    def get_mode() -> AgentMode
    def should_intervene(context: Dict) -> Optional[str]
    def queue_autonomous_task(description, priority=5) -> AgentTask
    def execute_autonomous_task(task_id) -> bool
    def get_capabilities() -> Dict[str, Any]
```

## Troubleshooting

### Connector Issues

**Problem**: "No module named 'requests'"
```bash
pip install requests
```

**Problem**: Connector not connecting
- Verify API key is correct
- Check if service is accessible
- Test with: `cm.test_connector("platform_name")`

### Task Manager Issues

**Problem**: Tasks not persisting
- Check permissions on `~/.vigil/tasks/`
- Verify disk space

**Problem**: Can't import TaskManager
```bash
# Make sure you're in the correct directory
cd vigil
python -c "from core.task_manager import TaskManager; print('OK')"
```

### Interface Issues

**Problem**: Interface won't open
- Install tkinter: `sudo apt-get install python3-tk` (Linux)
- On Windows, tkinter should be included with Python

**Problem**: Interface appears behind other windows
- Click the window to bring it to front
- Press `Ctrl+Shift+V` to toggle

## Future Enhancements

Planned features for future releases:

- [ ] Bi-directional sync with external platforms
- [ ] Voice-activated task completion
- [ ] Calendar integration
- [ ] Team collaboration features
- [ ] Mobile app companion
- [ ] Advanced automation with custom workflows
- [ ] Integration with more platforms (Notion, Linear, Jira, etc.)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the example code
3. Check the source code in `core/` directory
4. File an issue on GitHub

## License

This feature is part of Vigil and follows the same license as the main project.
