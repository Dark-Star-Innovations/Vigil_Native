+   1 #!/usr/bin/env python3
+   2 """
+   3 VIGIL - The Watchful Guardian
+   4 =============================
+   5 
+   6 A voice-first AI companion that never sleeps.
+   7 
+   8 Features:
+   9 - Always-on wake word detection
+  10 - Multi-LLM support (GPT-4o, Claude, Gemini)
+  11 - Voice input (Whisper) and output (ElevenLabs)
+  12 - Daily midnight reflections
+  13 - Custom knowledge base
+  14 - Memory and learning from interactions
+  15 
+  16 Usage:
+  17     python vigil.py
+  18 
+  19 Wake words: "Vigil", "Hey Vigil", "Yo Vigil", "Yo V", "Help",
+  20             "The truth will set you free"
+  21 
+  22 Author: Louis (Bizy/Lazurith)
+  23 """
+  24 
+  25 import sys
+  26 import time
+  27 import signal
+  28 import threading
+  29 from pathlib import Path
+  30 
+  31 # Add parent directory to path for imports
+  32 sys.path.insert(0, str(Path(__file__).parent))
+  33 
+  34 from config.settings import (
+  35     BOT_NAME,
+  36     BOT_TITLE,
+  37     WAKE_WORDS,
+  38     PRIMARY_USER_NAME,
+  39     Paths,
+  40 )
+  41 from core.listener import WakeWordListener
+  42 from core.voice_input import VoiceInput
+  43 from core.voice_output import VoiceOutput
+  44 from core.brain import Brain
+  45 from core.memory import Memory
+  46 from knowledge.codex import AscensionCodex
+  47 from knowledge.shrines import ShrineVirtues
+  48 from knowledge.roles import SacredRoles
+  49 from knowledge.knowledge_base import KnowledgeBase
+  50 from reflection.daily_reflection import ReflectionSystem
from core.task_manager import TaskManager
from core.service_connectors import ConnectorManager
from core.agent_mode import AgentSystem, AgentMode
from core.always_on_top import AlwaysOnTopInterface
+  51 
+  52 
+  53 class Vigil:
+  54     """
+  55     The main Vigil application.
+  56 
+  57     Orchestrates all components:
+  58     - Wake word detection
+  59     - Speech-to-text
+  60     - LLM processing
+  61     - Text-to-speech
+  62     - Memory & learning
+  63     - Daily reflections
+  64     """
+  65 
+  66     def __init__(self):
+  67         print(f"""
+  68 ╔══════════════════════════════════════════════════════════════╗
+  69 ║                                                              ║
+  70 ║     ██╗   ██╗██╗ ██████╗ ██╗██╗                             ║
+  71 ║     ██║   ██║██║██╔════╝ ██║██║                             ║
+  72 ║     ██║   ██║██║██║  ███╗██║██║                             ║
+  73 ║     ╚██╗ ██╔╝██║██║   ██║██║██║                             ║
+  74 ║      ╚████╔╝ ██║╚██████╔╝██║███████╗                        ║
+  75 ║       ╚═══╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝                        ║
+  76 ║                                                              ║
+  77 ║                  THE WATCHFUL GUARDIAN                       ║
+  78 ║                                                              ║
+  79 ╚══════════════════════════════════════════════════════════════╝
+  80         """)
+  81 
+  82         print(f"[{BOT_NAME}] Initializing systems...")
+  83 
+  84         # Ensure directories exist
+  85         Paths.ensure_directories()
+  86 
+  87         # Initialize components
+  88         self.voice_input = VoiceInput()
+  89         self.voice_output = VoiceOutput()
+  90         self.brain = Brain()
+  91         self.memory = Memory()
+  92         self.knowledge_base = KnowledgeBase()
+  93         self.reflection_system = ReflectionSystem(

        # Task management and integrations
        self.task_manager = TaskManager()
        self.connector_manager = ConnectorManager()
        self.agent_system = AgentSystem(
            brain=self.brain,
            task_manager=self.task_manager,
            memory=self.memory
        )
        self.always_on_top_interface = None
+  94             brain=self.brain,
+  95             memory=self.memory
+  96         )
+  97 
+  98         # Wake word listener
+  99         self.listener = WakeWordListener(
+ 100             on_wake=self._on_wake_word_detected,
+ 101             on_error=self._on_listener_error
+ 102         )
+ 103 
+ 104         # State
+ 105         self.is_running = False
+ 106         self.is_processing = False
+ 107         self._shutdown_event = threading.Event()
+ 108 
+ 109         print(f"[{BOT_NAME}] All systems initialized.")
+ 110         print(f"[{BOT_NAME}] Wake words: {', '.join(WAKE_WORDS)}")
+ 111 
+ 112     def _on_wake_word_detected(self, phrase: str):
+ 113         """Handle wake word detection."""
+ 114         if self.is_processing:
+ 115             return
+ 116 
+ 117         self.is_processing = True
+ 118 
+ 119         try:
+ 120             # Extract command from wake phrase
+ 121             command = self._extract_command(phrase)
+ 122 
+ 123             if command:
+ 124                 # User said something after wake word
+ 125                 self._process_command(command)
+ 126             else:
+ 127                 # Just wake word - prompt for input
+ 128                 self._acknowledge_wake()
+ 129                 self._listen_for_command()
+ 130 
+ 131         finally:
+ 132             self.is_processing = False
+ 133 
+ 134     def _extract_command(self, phrase: str) -> str:
+ 135         """Extract command from the wake phrase."""
+ 136         phrase_lower = phrase.lower()
+ 137 
+ 138         # Find which wake word was used
+ 139         for wake_word in sorted(WAKE_WORDS, key=len, reverse=True):
+ 140             if wake_word.lower() in phrase_lower:
+ 141                 idx = phrase_lower.find(wake_word.lower())
+ 142                 remaining = phrase[idx + len(wake_word):].strip()
+ 143                 # Clean up
+ 144                 remaining = remaining.strip(",.?!")
+ 145                 return remaining.strip()
+ 146 
+ 147         return phrase
+ 148 
+ 149     def _acknowledge_wake(self):
+ 150         """Acknowledge that we heard the wake word."""
+ 151         responses = [
+ 152             f"I'm here, {PRIMARY_USER_NAME}.",
+ 153             "Listening.",
+ 154             "Yes?",
+ 155             f"What do you need, {PRIMARY_USER_NAME}?",
+ 156             "I'm with you.",
+ 157         ]
+ 158         import random
+ 159         response = random.choice(responses)
+ 160         self.voice_output.speak(response)
+ 161 
+ 162     def _listen_for_command(self):
+ 163         """Listen for the user's command after wake word."""
+ 164         text = self.voice_input.listen_and_transcribe(timeout=10, phrase_limit=30)
+ 165         if text:
+ 166             self._process_command(text)
+ 167 
+ 168     def _process_command(self, command: str):
+ 169         """Process a user command."""
+ 170         print(f"[{BOT_NAME}] Processing: '{command}'")
+ 171 
        # Check for task management and system commands
        command_lower = command.lower()
        
        if "create task" in command_lower or "new task" in command_lower or "add task" in command_lower:
            return self._handle_create_task(command)
        elif "list tasks" in command_lower or "show tasks" in command_lower:
            return self._handle_list_tasks(command)
        elif "agent mode" in command_lower or "activate agent" in command_lower:
            return self._handle_agent_mode(command)
        elif "show interface" in command_lower or "open interface" in command_lower or "project manager" in command_lower:
            return self._handle_show_interface()
        elif "add connector" in command_lower or "connect to" in command_lower:
            return self._handle_add_connector(command)
        elif "list connectors" in command_lower or "show connectors" in command_lower:
            return self._handle_list_connectors()

+ 172         # Detect role and domain
+ 173         role = SacredRoles.detect_role(command)
+ 174         domain = SacredRoles.detect_domain(command)
+ 175 
+ 176         # Get knowledge context
+ 177         codex_context = AscensionCodex.get_context_for_query(command)
+ 178         shrine_context = ShrineVirtues.get_context_for_query(command)
+ 179         role_context = SacredRoles.get_role_context(command)
+ 180         kb_context = self.knowledge_base.get_context_for_query(command)
+ 181         user_context = self.memory.get_user_context()
+ 182 
+ 183         # Build enhanced prompt with context
+ 184         enhanced_prompt = f"""{command}
+ 185 
+ 186 ---
+ 187 ## CONTEXT FOR VIGIL
+ 188 
+ 189 {user_context}
+ 190 
+ 191 {role_context}
+ 192 
+ 193 {codex_context}
+ 194 
+ 195 {shrine_context}
+ 196 
+ 197 {kb_context}
+ 198 ---
+ 199 
+ 200 Respond naturally as Vigil. Keep voice responses concise (2-4 sentences) unless the task requires detailed output.
+ 201 """
+ 202 
+ 203         # Get response from brain
+ 204         response = self.brain.think(enhanced_prompt)
+ 205 
+ 206         if response:
+ 207             # Speak the response
+ 208             self.voice_output.speak(response.text)
+ 209 
+ 210             # Record interaction in memory
+ 211             self.memory.record_interaction(
+ 212                 user_input=command,
+ 213                 vigil_response=response.text,
+ 214                 mode=domain or "conversation",
+ 215             )
+ 216         else:
+ 217             error_msg = "I apologize, I'm having trouble processing that. Could you try again?"
+ 218             self.voice_output.speak(error_msg)
+ 219 
+ 220     def _on_listener_error(self, error: Exception):
+ 221         """Handle listener errors."""
+ 222         print(f"[{BOT_NAME}] Listener error: {error}")
+ 223 
+ 224     def _startup_greeting(self):
+ 225         """Greet the user on startup."""
+ 226         greeting = f"Vigil online. I am with you, {PRIMARY_USER_NAME}. Say my name when you need me."
+ 227         print(f"[{BOT_NAME}] {greeting}")
+ 228         self.voice_output.speak(greeting)
+ 229 

    # Task Management Command Handlers
    def _handle_create_task(self, command: str):
        """Handle task creation command."""
        response_text = "I'll help you create a task. What's the task title?"
        self.voice_output.speak(response_text)
        
        # Listen for task title
        title = self.voice_input.listen_and_transcribe(timeout=10, phrase_limit=20)
        if not title:
            self.voice_output.speak("I didn't catch that. Let's try again later.")
            return
        
        # Create the task
        from core.task_manager import TaskPriority
        task = self.task_manager.create_task(
            title=title,
            priority=TaskPriority.MEDIUM,
            tags=["voice-created"]
        )
        
        response = f"Task created: {title}. I'll help you track this."
        self.voice_output.speak(response)
        self.memory.record_interaction(
            user_input=command,
            vigil_response=response,
            mode="task_management"
        )
    
    def _handle_list_tasks(self, command: str):
        """Handle list tasks command."""
        from core.task_manager import TaskStatus
        
        tasks = self.task_manager.list_tasks()
        total = len(tasks)
        
        if total == 0:
            response = "You have no tasks yet. Would you like to create one?"
        else:
            todo_count = len([t for t in tasks if t.status == TaskStatus.TODO])
            in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
            completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            
            response = f"You have {total} tasks: {todo_count} to do, {in_progress} in progress, {completed} completed."
            
            # List up to 3 urgent/high priority tasks
            urgent_tasks = [t for t in tasks if t.priority.value in ["urgent", "high"] and t.status != TaskStatus.COMPLETED]
            if urgent_tasks:
                task_names = ", ".join([t.title for t in urgent_tasks[:3]])
                response += f" Urgent: {task_names}."
        
        self.voice_output.speak(response)
        self.memory.record_interaction(
            user_input=command,
            vigil_response=response,
            mode="task_management"
        )
    
    def _handle_agent_mode(self, command: str):
        """Handle agent mode activation."""
        command_lower = command.lower()
        
        if "passive" in command_lower:
            self.agent_system.set_mode(AgentMode.PASSIVE)
            response = "Agent mode set to passive. I'll only respond when called."
        elif "active" in command_lower:
            self.agent_system.set_mode(AgentMode.ACTIVE)
            response = "Active mode enabled. I'll proactively assist you."
        elif "autonomous" in command_lower:
            self.agent_system.set_mode(AgentMode.AUTONOMOUS)
            response = "Autonomous mode activated. I can execute tasks independently."
        elif "project" in command_lower or "manager" in command_lower:
            self.agent_system.set_mode(AgentMode.PROJECT_MANAGER)
            response = "Project Manager mode activated. I'll track your commitments."
        else:
            current_mode = self.agent_system.get_mode().value
            response = f"Current agent mode: {current_mode}. Say passive, active, autonomous, or project manager to change."
        
        self.voice_output.speak(response)
        self.memory.record_interaction(
            user_input=command,
            vigil_response=response,
            mode="system"
        )
    
    def _handle_show_interface(self):
        """Handle showing the always-on-top interface."""
        if self.always_on_top_interface is None or not self.always_on_top_interface.is_running:
            def handle_interface_message(msg: str) -> str:
                # Process message through brain
                response = self.brain.think(msg)
                return response.text if response else "I'm having trouble processing that."
            
            def handle_interface_close():
                print(f"[{BOT_NAME}] Interface closed")
            
            self.always_on_top_interface = AlwaysOnTopInterface(
                on_message_callback=handle_interface_message,
                on_close_callback=handle_interface_close
            )
            self.always_on_top_interface.start()
            
            response = "Opening project manager interface."
        else:
            response = "Interface is already open."
        
        self.voice_output.speak(response)
    
    def _handle_add_connector(self, command: str):
        """Handle adding a service connector."""
        response_text = "Which service would you like to connect? For example: GitHub, Taskade, or a custom URL."
        self.voice_output.speak(response_text)
        
        service_name = self.voice_input.listen_and_transcribe(timeout=10, phrase_limit=10)
        if not service_name:
            self.voice_output.speak("I didn't catch that. Let's try again later.")
            return
        
        response = f"To connect to {service_name}, you'll need to add API credentials to your environment configuration. Check the connector manager settings."
        self.voice_output.speak(response)
        
        self.memory.record_interaction(
            user_input=command,
            vigil_response=response,
            mode="system"
        )
    
    def _handle_list_connectors(self):
        """Handle listing available connectors."""
        connectors = self.connector_manager.list_connectors()
        platforms = self.connector_manager.get_available_platforms()
        
        if connectors:
            connector_list = ", ".join(connectors)
            response = f"Active connectors: {connector_list}."
        else:
            response = "No connectors are currently active."
        
        response += f" I can connect to: {', '.join(platforms[:5])} and more."
        
        self.voice_output.speak(response)
+ 230     def run(self):
+ 231         """Main run loop."""
+ 232         self.is_running = True
+ 233 
+ 234         # Start reflection scheduler
+ 235         self.reflection_system.start_scheduler()
+ 236 
+ 237         # Start wake word listener
+ 238         self.listener.start()
+ 239 
+ 240         # Greet user
+ 241         self._startup_greeting()
+ 242 
+ 243         print(f"\n[{BOT_NAME}] ═══════════════════════════════════════════")
+ 244         print(f"[{BOT_NAME}] Vigil is now active and listening.")
+ 245         print(f"[{BOT_NAME}] Say one of the wake words to begin.")
+ 246         print(f"[{BOT_NAME}] Press Ctrl+C to shutdown.")
+ 247         print(f"[{BOT_NAME}] ═���═════════════════════════════════════════\n")
+ 248 
+ 249         # Keep running until shutdown
+ 250         try:
+ 251             while not self._shutdown_event.is_set():
+ 252                 # Check for new day (for memory)
+ 253                 self.memory.new_day_check()
+ 254                 time.sleep(1)
+ 255         except KeyboardInterrupt:
+ 256             print(f"\n[{BOT_NAME}] Shutdown requested...")
+ 257 
+ 258         self.shutdown()
+ 259 
+ 260     def shutdown(self):
+ 261         """Graceful shutdown."""
+ 262         print(f"[{BOT_NAME}] Shutting down...")
+ 263 
+ 264         self._shutdown_event.set()
+ 265         self.is_running = False
+ 266 
+ 267         # Stop components
+ 268         self.listener.stop()
+ 269         self.reflection_system.stop_scheduler()
+ 270 
+ 271         # Farewell
+ 272         farewell = f"Until next time, {PRIMARY_USER_NAME}. Stay vigilant."
+ 273         self.voice_output.speak(farewell)
+ 274 
+ 275         print(f"[{BOT_NAME}] Goodbye.")
+ 276 
+ 277 
+ 278 def main():
+ 279     """Entry point."""
+ 280     # Handle Ctrl+C gracefully
+ 281     vigil = Vigil()
+ 282 
+ 283     def signal_handler(sig, frame):
+ 284         vigil.shutdown()
+ 285         sys.exit(0)
+ 286 
+ 287     signal.signal(signal.SIGINT, signal_handler)
+ 288     signal.signal(signal.SIGTERM, signal_handler)
+ 289 
+ 290     # Run Vigil
+ 291     vigil.run()
+ 292 
+ 293 
+ 294 if __name__ == "__main__":
+ 295     main()
