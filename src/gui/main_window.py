"""
Main application window
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from src.core.config import AppConfig
from src.core.serial_manager import SerialManager, SerialData
from src.core.encryption import EncryptionManager
from src.core.mock_data import MockDataGenerator
from src.gui.widgets.connection_frame import ConnectionFrame
from src.gui.widgets.lora_config_frame import LoRaConfigFrame
from src.gui.widgets.data_display_frame import DataDisplayFrame
from src.gui.widgets.control_frame import ControlFrame

KEYFILE = 'keyfile.bin'

def load_key():
    if not os.path.exists(KEYFILE):
        raise FileNotFoundError(f"Key file '{KEYFILE}' not found.")
    with open(KEYFILE, 'rb') as f:
        key = f.read()
        if len(key) != 32:
            raise ValueError("Key length must be exactly 32 bytes (256 bits).")
        return key

EN_KEY = base64.b64encode(load_key()).decode('utf-8')

class MainWindow:
    """Main application window"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.root = ctk.CTk()
        self.setup_window()
        
        # Core components
        self.serial_manager = SerialManager(self.on_serial_data_received)
        self.encryption_manager = EncryptionManager(
            method=config.encryption.method,
            key=EN_KEY
        )
        self.mock_generator = MockDataGenerator(self.on_mock_data_received)
        
        # GUI components
        self.connection_frame = None
        self.lora_config_frame = None
        self.data_display_frame = None
        self.control_frame = None
        
        self.setup_gui()
        self.setup_menu()
        
        # Status
        self.is_mock_mode = False
        
    def setup_window(self):
        """Setup main window properties"""
        self.root.title("LoRa SX126x Gateway")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
    
    def setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Toggle Mock Mode", command=self.toggle_mock_mode)
        tools_menu.add_command(label="Clear Data", command=self.clear_data)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_gui(self):
        """Setup GUI components"""
        # Title frame
        title_frame = ctk.CTkFrame(self.root)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="LoRa SX126x Gateway", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Main content frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Left panel (Configuration) - Make it scrollable
        left_panel_container = ctk.CTkFrame(main_frame)
        left_panel_container.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(10, 5), pady=10)
        left_panel_container.grid_columnconfigure(0, weight=1)
        left_panel_container.grid_rowconfigure(0, weight=1)

        # Create scrollable frame
        self.left_scrollable_frame = ctk.CTkScrollableFrame(left_panel_container, width=300)
        self.left_scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.left_scrollable_frame.grid_columnconfigure(0, weight=1)

        # Connection frame
        self.connection_frame = ConnectionFrame(
            self.left_scrollable_frame, 
            self.config.serial,
            self.on_connect_clicked,
            self.on_disconnect_clicked
        )
        self.connection_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # LoRa configuration frame
        self.lora_config_frame = LoRaConfigFrame(self.left_scrollable_frame, self.config.lora)
        self.lora_config_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Control frame
        self.control_frame = ControlFrame(
            self.left_scrollable_frame,
            self.on_send_command,
            self.toggle_mock_mode
        )
        self.control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # Right panel (Data Display)
        self.data_display_frame = DataDisplayFrame(main_frame)
        self.data_display_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 10), pady=10)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(
            self.root, 
            text="Ready", 
            anchor="w"
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
    
    def on_connect_clicked(self, port: str, baudrate: int):
        """Handle connect button click"""
        if self.serial_manager.connect(port, baudrate):
            self.update_status(f"Connected to {port} at {baudrate} baud")
            self.connection_frame.set_connected(True)
        else:
            messagebox.showerror("Connection Error", f"Failed to connect to {port}")
    
    def on_disconnect_clicked(self):
        """Handle disconnect button click"""
        self.serial_manager.disconnect()
        self.update_status("Disconnected")
        self.connection_frame.set_connected(False)
    
    def on_serial_data_received(self, data: SerialData):
        """Handle received serial data"""
        print(f"Received serial data: {data.decoded_data}")
        try:
            # Check if data is encrypted
            if self.config.encryption.enabled and self.encryption_manager.is_encrypted(data.decoded_data):
                decrypted_data = self.encryption_manager.decrypt(data.decoded_data)
                self.data_display_frame.add_data(decrypted_data, data.timestamp, encrypted=True)
            else:
                print("###### NON-ENCRYPTED DATA ######")
                self.data_display_frame.add_data(data.decoded_data.strip(), data.timestamp)
                
        except Exception as e:
            print(f"Error processing serial data: {e}")
    
    def on_mock_data_received(self, data: str):
        """Handle mock data"""
        print(f"Received mock data: {data}")
        import time
        self.data_display_frame.add_data(data, time.time(), mock=True)
    
    def on_send_command(self, command: str):
        """Handle send command"""
        if self.serial_manager.is_connected:
            if self.serial_manager.send_data(command + "\n"):
                self.update_status(f"Sent: {command}")
            else:
                messagebox.showerror("Send Error", "Failed to send command")
        else:
            messagebox.showwarning("Not Connected", "Please connect to a serial port first")
    
    def toggle_mock_mode(self):
        """Toggle mock data generation"""
        if self.is_mock_mode:
            self.mock_generator.stop()
            self.is_mock_mode = False
            self.update_status("Mock mode disabled")
        else:
            self.mock_generator.start(interval=3.0)
            self.is_mock_mode = True
            self.update_status("Mock mode enabled")
    
    def clear_data(self):
        """Clear all displayed data"""
        self.data_display_frame.clear_data()
        self.update_status("Data cleared")
    
    def save_config(self):
        """Save current configuration"""
        # Update config with current GUI values
        self.lora_config_frame.update_config(self.config.lora)
        self.connection_frame.update_config(self.config.serial)
        
        self.config.save_config()
        self.update_status("Configuration saved")
    
    def load_config(self):
        """Load configuration"""
        self.config.load_config()
        
        # Update GUI with loaded values
        self.lora_config_frame.load_config(self.config.lora)
        self.connection_frame.load_config(self.config.serial)
        
        self.update_status("Configuration loaded")
    
    def update_status(self, message: str):
        """Update status bar"""
        self.status_bar.configure(text=message)
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About", 
            "LoRa SX126x Gateway v1.0\n\n"
            "A desktop application for receiving and displaying\n"
            "LoRa sensor data via USB UART connection.\n\n"
            "Built with Python 3.10 and CustomTkinter"
        )
    
    def on_closing(self):
        """Handle application closing"""
        # Stop all background processes
        self.serial_manager.disconnect()
        self.mock_generator.stop()
        
        # Save configuration
        self.save_config()
        
        # Close application
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
