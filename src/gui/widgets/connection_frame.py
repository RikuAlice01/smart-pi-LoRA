"""
Connection configuration widget
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Callable, List
from src.core.serial_manager import SerialManager
from src.core.config import SerialConfig

class ConnectionFrame(ctk.CTkFrame):
    """Frame for serial connection configuration"""
    
    def __init__(self, parent, config: SerialConfig, connect_callback: Callable, disconnect_callback: Callable):
        super().__init__(parent)
        
        self.config = config
        self.connect_callback = connect_callback
        self.disconnect_callback = disconnect_callback
        self.is_connected = False
        
        self.setup_widgets()
        self.load_config(config)
    
    def setup_widgets(self):
        """Setup connection widgets"""
        # Title
        title_label = ctk.CTkLabel(self, text="Serial Connection", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Port selection
        port_label = ctk.CTkLabel(self, text="Port:")
        port_label.grid(row=1, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.port_var = ctk.StringVar()
        self.port_combo = ctk.CTkComboBox(
            self, 
            variable=self.port_var,
            values=self.get_available_ports(),
            width=150
        )
        self.port_combo.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Refresh ports button
        self.refresh_btn = ctk.CTkButton(
            self, 
            text="Refresh", 
            command=self.refresh_ports,
            width=80
        )
        self.refresh_btn.grid(row=2, column=1, sticky="e", padx=(5, 10), pady=5)
        
        # Baudrate
        baudrate_label = ctk.CTkLabel(self, text="Baudrate:")
        baudrate_label.grid(row=3, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.baudrate_var = ctk.StringVar()
        self.baudrate_combo = ctk.CTkComboBox(
            self,
            variable=self.baudrate_var,
            values=["9600", "19200", "38400", "57600", "115200"],
            width=150
        )
        self.baudrate_combo.grid(row=3, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Connection buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(15, 10))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        self.connect_btn = ctk.CTkButton(
            button_frame,
            text="Connect",
            command=self.on_connect,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.connect_btn.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        self.disconnect_btn = ctk.CTkButton(
            button_frame,
            text="Disconnect",
            command=self.on_disconnect,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.disconnect_btn.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        
        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)
    
    def get_available_ports(self) -> List[str]:
        """Get available serial ports"""
        temp_manager = SerialManager()
        return temp_manager.get_available_ports()
    
    def refresh_ports(self):
        """Refresh available ports"""
        ports = self.get_available_ports()
        self.port_combo.configure(values=ports)
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
    
    def on_connect(self):
        """Handle connect button"""
        port = self.port_var.get()
        try:
            baudrate = int(self.baudrate_var.get())
        except ValueError:
            baudrate = 9600
        
        if port:
            self.connect_callback(port, baudrate)
    
    def on_disconnect(self):
        """Handle disconnect button"""
        self.disconnect_callback()
    
    def set_connected(self, connected: bool):
        """Update connection state"""
        self.is_connected = connected
        if connected:
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.port_combo.configure(state="disabled")
            self.baudrate_combo.configure(state="disabled")
        else:
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")
            self.port_combo.configure(state="normal")
            self.baudrate_combo.configure(state="normal")
    
    def load_config(self, config: SerialConfig):
        """Load configuration values"""
        if config.port:
            self.port_var.set(config.port)
        self.baudrate_var.set(str(config.baudrate))
    
    def update_config(self, config: SerialConfig):
        """Update configuration with current values"""
        config.port = self.port_var.get()
        try:
            config.baudrate = int(self.baudrate_var.get())
        except ValueError:
            config.baudrate = 9600
