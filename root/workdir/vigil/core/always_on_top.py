"""
VIGIL - Always-On-Top Interface
Provides an always-on-top overlay for quick access to Vigil
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Callable
import threading


class AlwaysOnTopInterface:
    """
    Always-on-top interface for Vigil.
    Provides quick access to task management and communication.
    """
    
    def __init__(
        self,
        on_message_callback: Optional[Callable[[str], str]] = None,
        on_close_callback: Optional[Callable] = None
    ):
        """Initialize the interface."""
        self.on_message_callback = on_message_callback
        self.on_close_callback = on_close_callback
        
        self.root = None
        self.is_running = False
        self.is_visible = True
        
        # UI components
        self.text_display = None
        self.input_field = None
        self.task_list = None
    
    def _create_window(self):
        """Create the main window."""
        self.root = tk.Tk()
        self.root.title("Vigil - Project Manager")
        self.root.geometry("400x600")
        
        # Make window always on top
        self.root.attributes('-topmost', True)
        
        # Make window transparent when desired
        self.root.attributes('-alpha', 0.95)
        
        # Create UI
        self._create_ui()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Hotkey to toggle visibility (Ctrl+Shift+V)
        self.root.bind('<Control-Shift-V>', self._toggle_visibility)
    
    def _create_ui(self):
        """Create the UI components."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🎯 VIGIL - Project Manager",
            font=('Helvetica', 14, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.rowconfigure(1, weight=1)
        
        # Chat tab
        chat_frame = ttk.Frame(notebook, padding="5")
        notebook.add(chat_frame, text="Chat")
        
        # Chat display
        self.text_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=40,
            height=15,
            state='disabled',
            font=('Helvetica', 10)
        )
        self.text_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        
        # Input frame
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, pady=(5, 0), sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        self.input_field = ttk.Entry(input_frame, font=('Helvetica', 10))
        self.input_field.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.input_field.bind('<Return>', self._on_send_message)
        
        send_button = ttk.Button(input_frame, text="Send", command=self._on_send_message)
        send_button.grid(row=0, column=1)
        
        # Tasks tab
        tasks_frame = ttk.Frame(notebook, padding="5")
        notebook.add(tasks_frame, text="Tasks")
        
        # Task list
        task_list_frame = ttk.Frame(tasks_frame)
        task_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tasks_frame.rowconfigure(0, weight=1)
        tasks_frame.columnconfigure(0, weight=1)
        
        # Task tree view
        self.task_list = ttk.Treeview(
            task_list_frame,
            columns=('Priority', 'Status'),
            show='tree headings',
            height=15
        )
        self.task_list.heading('#0', text='Task')
        self.task_list.heading('Priority', text='Priority')
        self.task_list.heading('Status', text='Status')
        self.task_list.column('Priority', width=70)
        self.task_list.column('Status', width=70)
        
        task_scrollbar = ttk.Scrollbar(task_list_frame, orient=tk.VERTICAL, command=self.task_list.yview)
        self.task_list.configure(yscrollcommand=task_scrollbar.set)
        
        self.task_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        task_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        task_list_frame.rowconfigure(0, weight=1)
        task_list_frame.columnconfigure(0, weight=1)
        
        # Task buttons
        task_button_frame = ttk.Frame(tasks_frame)
        task_button_frame.grid(row=1, column=0, pady=(5, 0), sticky=tk.W)
        
        ttk.Button(task_button_frame, text="Add Task", command=self._on_add_task).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(task_button_frame, text="Refresh", command=self._on_refresh_tasks).grid(row=0, column=1)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, pady=(5, 0), sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Toggle button
        toggle_button = ttk.Button(
            status_frame,
            text="Hide (Ctrl+Shift+V)",
            command=self._toggle_visibility
        )
        toggle_button.grid(row=0, column=1, sticky=tk.E)
        status_frame.columnconfigure(1, weight=1)
        
        # Initial message
        self._add_message("Vigil", "Project Manager ready. How can I help?", "system")
    
    def _on_send_message(self, event=None):
        """Handle send message."""
        message = self.input_field.get().strip()
        if not message:
            return
        
        # Clear input
        self.input_field.delete(0, tk.END)
        
        # Display user message
        self._add_message("You", message, "user")
        
        # Get response
        if self.on_message_callback:
            try:
                response = self.on_message_callback(message)
                self._add_message("Vigil", response, "assistant")
            except Exception as e:
                self._add_message("System", f"Error: {e}", "error")
        else:
            self._add_message("Vigil", "Message received (no callback set)", "assistant")
    
    def _add_message(self, sender: str, message: str, msg_type: str = "normal"):
        """Add a message to the chat display."""
        if not self.text_display:
            return
        
        self.text_display.configure(state='normal')
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        
        # Format based on type
        if msg_type == "user":
            prefix = f"[{timestamp}] You: "
            self.text_display.insert(tk.END, prefix, "user_tag")
        elif msg_type == "assistant":
            prefix = f"[{timestamp}] Vigil: "
            self.text_display.insert(tk.END, prefix, "assistant_tag")
        elif msg_type == "system":
            prefix = f"[{timestamp}] System: "
            self.text_display.insert(tk.END, prefix, "system_tag")
        else:
            prefix = f"[{timestamp}] {sender}: "
            self.text_display.insert(tk.END, prefix)
        
        self.text_display.insert(tk.END, message + "\n\n")
        
        # Configure tags
        self.text_display.tag_config("user_tag", foreground="blue", font=('Helvetica', 10, 'bold'))
        self.text_display.tag_config("assistant_tag", foreground="green", font=('Helvetica', 10, 'bold'))
        self.text_display.tag_config("system_tag", foreground="gray", font=('Helvetica', 10, 'italic'))
        
        # Scroll to end
        self.text_display.see(tk.END)
        self.text_display.configure(state='disabled')
    
    def _on_add_task(self):
        """Handle add task button."""
        self._add_message("System", "Task creation dialog would open here", "system")
    
    def _on_refresh_tasks(self):
        """Handle refresh tasks button."""
        self._add_message("System", "Refreshing tasks...", "system")
        # Clear current tasks
        for item in self.task_list.get_children():
            self.task_list.delete(item)
        
        # Add sample tasks (would load from task manager in real implementation)
        self._add_task_to_list("Sample Task 1", "high", "todo")
        self._add_task_to_list("Sample Task 2", "medium", "in_progress")
    
    def _add_task_to_list(self, title: str, priority: str, status: str):
        """Add a task to the task list."""
        self.task_list.insert('', 'end', text=title, values=(priority, status))
    
    def _toggle_visibility(self, event=None):
        """Toggle window visibility."""
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
        else:
            self.root.deiconify()
            self.is_visible = True
    
    def _on_close(self):
        """Handle window close."""
        if self.on_close_callback:
            self.on_close_callback()
        self.stop()
    
    def start(self):
        """Start the interface in a separate thread."""
        if self.is_running:
            return
        
        self.is_running = True
        
        def run():
            self._create_window()
            self.root.mainloop()
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop the interface."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def show_notification(self, message: str):
        """Show a notification in the interface."""
        if self.text_display:
            self._add_message("Notification", message, "system")
    
    def update_tasks(self, tasks: list):
        """Update the task list."""
        if not self.task_list:
            return
        
        # Clear current tasks
        for item in self.task_list.get_children():
            self.task_list.delete(item)
        
        # Add new tasks
        for task in tasks:
            title = task.get('title', 'Untitled')
            priority = task.get('priority', 'medium')
            status = task.get('status', 'todo')
            self._add_task_to_list(title, priority, status)


if __name__ == "__main__":
    # Test the interface
    def handle_message(msg: str) -> str:
        return f"Echo: {msg}"
    
    def handle_close():
        print("Interface closed")
    
    interface = AlwaysOnTopInterface(
        on_message_callback=handle_message,
        on_close_callback=handle_close
    )
    
    print("Starting always-on-top interface...")
    print("Press Ctrl+C to exit")
    
    interface.start()
    
    # Keep main thread alive
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping interface...")
        interface.stop()
