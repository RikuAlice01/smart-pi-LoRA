"""
Control panel widget for sending commands and controlling the application
"""

import customtkinter as ctk
from typing import Callable

class ControlFrame(ctk.CTkFrame):
    """Frame for application controls"""
    
    def __init__(self, parent, send_callback: Callable, mock_callback: Callable):
        super().__init__(parent)
        
        self.send_callback = send_callback
        self.mock_callback = mock_callback
        
        self.setup_widgets()
    
    def setup_widgets(self):
        """Setup control widgets"""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(self, text="Controls", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, pady=(10, 15), sticky="w")
        
        # Command sending section
        cmd_frame = ctk.CTkFrame(self)
        cmd_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        cmd_frame.grid_columnconfigure(0, weight=1)
        
        cmd_label = ctk.CTkLabel(cmd_frame, text="Send Command:")
        cmd_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.cmd_entry = ctk.CTkEntry(cmd_frame, placeholder_text="Enter command...")
        self.cmd_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.cmd_entry.bind("<Return>", self.on_send_command)
        
        send_btn = ctk.CTkButton(
            cmd_frame,
            text="Send",
            command=self.on_send_command,
            width=100
        )
        send_btn.grid(row=2, column=0, pady=(5, 10))
        
        # Quick commands
        quick_frame = ctk.CTkFrame(self)
        quick_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        quick_frame.grid_columnconfigure(0, weight=1)
        quick_frame.grid_columnconfigure(1, weight=1)
        
        quick_label = ctk.CTkLabel(quick_frame, text="Quick Commands:")
        quick_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        
        # Common LoRa commands
        commands = [
            ("Get Status", "AT+STATUS?"),
            ("Get Version", "AT+VER?"),
            ("Reset", "AT+RESET"),
            ("Get Config", "AT+CFG?")
        ]
        
        for i, (label, command) in enumerate(commands):
            btn = ctk.CTkButton(
                quick_frame,
                text=label,
                command=lambda cmd=command: self.send_quick_command(cmd),
                width=120,
                height=30
            )
            row = (i // 2) + 1
            col = i % 2
            btn.grid(row=row, column=col, padx=5, pady=2, sticky="ew")
        
        # Application controls
        app_frame = ctk.CTkFrame(self)
        app_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(15, 10))
        app_frame.grid_columnconfigure(0, weight=1)
        
        app_label = ctk.CTkLabel(app_frame, text="Application:")
        app_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.mock_btn = ctk.CTkButton(
            app_frame,
            text="Toggle Mock Data",
            command=self.mock_callback,
            fg_color="orange",
            hover_color="darkorange"
        )
        self.mock_btn.grid(row=1, column=0, pady=(5, 10), sticky="ew", padx=10)
    
    def on_send_command(self, event=None):
        """Handle send command button/enter key"""
        command = self.cmd_entry.get().strip()
        if command:
            self.send_callback(command)
            self.cmd_entry.delete(0, "end")
    
    def send_quick_command(self, command: str):
        """Send a quick command"""
        self.send_callback(command)
