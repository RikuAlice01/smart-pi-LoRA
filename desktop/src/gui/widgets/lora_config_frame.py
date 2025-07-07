"""
LoRa configuration widget
"""

import customtkinter as ctk
from src.core.config import LoRaConfig

class LoRaConfigFrame(ctk.CTkFrame):
    """Frame for LoRa parameter configuration"""
    
    def __init__(self, parent, config: LoRaConfig):
        super().__init__(parent)
        
        self.config = config
        self.setup_widgets()
        self.load_config(config)
    
    def setup_widgets(self):
        """Setup LoRa configuration widgets"""
        # Title
        title_label = ctk.CTkLabel(self, text="LoRa Configuration", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Frequency
        freq_label = ctk.CTkLabel(self, text="Frequency (MHz):")
        freq_label.grid(row=1, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.freq_var = ctk.StringVar()
        self.freq_entry = ctk.CTkEntry(self, textvariable=self.freq_var, width=100)
        self.freq_entry.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Bandwidth
        bw_label = ctk.CTkLabel(self, text="Bandwidth (kHz):")
        bw_label.grid(row=2, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.bw_var = ctk.StringVar()
        self.bw_combo = ctk.CTkComboBox(
            self,
            variable=self.bw_var,
            values=["125", "250", "500"],
            width=100
        )
        self.bw_combo.grid(row=2, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Spreading Factor
        sf_label = ctk.CTkLabel(self, text="Spreading Factor:")
        sf_label.grid(row=3, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.sf_var = ctk.StringVar()
        self.sf_combo = ctk.CTkComboBox(
            self,
            variable=self.sf_var,
            values=["6", "7", "8", "9", "10", "11", "12"],
            width=100
        )
        self.sf_combo.grid(row=3, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Coding Rate
        cr_label = ctk.CTkLabel(self, text="Coding Rate:")
        cr_label.grid(row=4, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.cr_var = ctk.StringVar()
        self.cr_combo = ctk.CTkComboBox(
            self,
            variable=self.cr_var,
            values=["5", "6", "7", "8"],
            width=100
        )
        self.cr_combo.grid(row=4, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Power Level
        power_label = ctk.CTkLabel(self, text="Power Level (dBm):")
        power_label.grid(row=5, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.power_var = ctk.StringVar()
        self.power_entry = ctk.CTkEntry(self, textvariable=self.power_var, width=100)
        self.power_entry.grid(row=5, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Sync Word
        sync_label = ctk.CTkLabel(self, text="Sync Word (hex):")
        sync_label.grid(row=6, column=0, sticky="w", padx=(10, 5), pady=5)
        
        self.sync_var = ctk.StringVar()
        self.sync_entry = ctk.CTkEntry(self, textvariable=self.sync_var, width=100)
        self.sync_entry.grid(row=6, column=1, sticky="ew", padx=(5, 10), pady=(5, 10))
        
        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)
    
    def load_config(self, config: LoRaConfig):
        """Load configuration values"""
        self.freq_var.set(str(config.frequency))
        self.bw_var.set(str(config.bandwidth))
        self.sf_var.set(str(config.spreading_factor))
        self.cr_var.set(str(config.coding_rate))
        self.power_var.set(str(config.power_level))
        self.sync_var.set(f"0x{config.sync_word:02X}")
    
    def update_config(self, config: LoRaConfig):
        """Update configuration with current values"""
        try:
            config.frequency = float(self.freq_var.get())
            config.bandwidth = int(self.bw_var.get())
            config.spreading_factor = int(self.sf_var.get())
            config.coding_rate = int(self.cr_var.get())
            config.power_level = int(self.power_var.get())
            
            # Parse sync word (handle hex format)
            sync_str = self.sync_var.get().replace('0x', '').replace('0X', '')
            config.sync_word = int(sync_str, 16)
            
        except ValueError as e:
            print(f"Error updating LoRa config: {e}")
