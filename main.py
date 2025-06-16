"""
LoRa SX126x Gateway Desktop Application
Main entry point for the application
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from src.gui.main_window import MainWindow
from src.core.config import AppConfig
import sys
import os

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

def main():
    """Main application entry point"""
    try:
        # Initialize configuration
        config = AppConfig()
        
        # Create and run the main application
        app = MainWindow(config)
        app.run()
        
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
