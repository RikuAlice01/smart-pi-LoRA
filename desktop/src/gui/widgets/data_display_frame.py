"""
Data display widget for showing received sensor data with improved statistics visualization
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
from typing import Dict, Any, List
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading

class DataDisplayFrame(ctk.CTkFrame):
    """Frame for displaying received data"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.data_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self._update_lock = threading.Lock()
        self._widget_references = set()  # Track widget references
        
        # Configure matplotlib to avoid threading issues
        matplotlib.use('Agg')
        plt.ioff()  # Turn off interactive mode
        
        self.setup_widgets()
    
    def setup_widgets(self):
        """Setup data display widgets"""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Title and controls
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(header_frame, text="Received Data", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Control buttons
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=1, padx=10, pady=10)
        
        self.clear_btn = ctk.CTkButton(
            controls_frame,
            text="Clear",
            command=self.clear_data,
            width=80
        )
        self.clear_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(
            controls_frame,
            text="Export",
            command=self.export_data,
            width=80
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Notebook for different views
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # Parsed data tab
        self.parsed_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.parsed_frame, text="Sensor Data")
        self.setup_parsed_data_tab()
        
        # Devices tab
        self.devices_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.devices_frame, text="Devices")
        self.setup_devices_tab()
        
        # Statistics tab
        self.stats_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        self.setup_statistics_tab()

        # Raw data tab
        self.raw_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.raw_frame, text="Raw Data")
        self.setup_raw_data_tab()
    
    def setup_raw_data_tab(self):
        """Setup raw data display tab"""
        self.raw_frame.grid_columnconfigure(0, weight=1)
        self.raw_frame.grid_rowconfigure(0, weight=1)
        
        # Text widget with scrollbar
        text_frame = ctk.CTkFrame(self.raw_frame)
        text_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        self.raw_text = ctk.CTkTextbox(text_frame, wrap="word")
        self.raw_text.grid(row=0, column=0, sticky="nsew")
    
    def setup_parsed_data_tab(self):
        """Setup parsed sensor data tab"""
        self.parsed_frame.grid_columnconfigure(0, weight=1)
        self.parsed_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview for structured data
        tree_frame = ctk.CTkFrame(self.parsed_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create Treeview
        columns = ("Time", "Device", "pH", "EC(µS/cm)", "TDS(ppm)", "Salinity(ppt)", "DO(mg/L)", "Sat(%)")
        self.data_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=80, anchor="center")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.data_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
    
    def setup_devices_tab(self):
        """Setup devices tab to show device information"""
        self.devices_frame.grid_columnconfigure(0, weight=1)
        self.devices_frame.grid_rowconfigure(0, weight=1)
        
        # Main container
        main_container = ctk.CTkFrame(self.devices_frame)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(main_container)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📱 Active Devices",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Devices display area
        self.devices_container = ctk.CTkScrollableFrame(main_container)
        self.devices_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.devices_container.grid_columnconfigure(0, weight=1)
        
        # Initialize with no devices message
        self.update_devices_display()
    
    def setup_statistics_tab(self):
        """Setup statistics tab with improved design"""
        self.stats_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_rowconfigure(0, weight=1)

        # Main container for statistics
        main_container = ctk.CTkFrame(self.stats_frame)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Header with controls
        header_frame = ctk.CTkFrame(main_container)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame, 
            text="📊 Sensor Data Statistics", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Controls
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=1, padx=10, pady=10)
        
        # Graph type selector
        self.graph_type_var = ctk.StringVar(value="overview")
        self.graph_type_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["overview", "trends", "comparison"],
            variable=self.graph_type_var,
            command=self.on_graph_type_change,
            width=120
        )
        self.graph_type_menu.pack(side="left", padx=5)
        
        # Statistics display area
        self.stats_container = ctk.CTkFrame(main_container)
        self.stats_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.stats_container.grid_columnconfigure(0, weight=1)
        self.stats_container.grid_rowconfigure(0, weight=1)
        
        # Scrollable frame for content
        self.stats_scroll = ctk.CTkScrollableFrame(self.stats_container)
        self.stats_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.stats_scroll.grid_columnconfigure(0, weight=1)
        
        self.canvas = None
        self.stats_info_frame = None
        
        # Initialize with empty display
        self.update_statistics()
    
    def safe_widget_destroy(self, widget):
        """Safely destroy a widget and remove from tracking"""
        try:
            if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                widget.destroy()
            if widget in self._widget_references:
                self._widget_references.remove(widget)
        except (tk.TclError, AttributeError):
            pass
    
    def add_data(self, data: str, timestamp: float, encrypted: bool = False, mock: bool = False):
        with self._update_lock:
            # Format timestamp
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%H:%M:%S")
            
            # Add to raw data display
            prefix = "[ENCRYPTED]" if encrypted else "[MOCK]" if mock else "[RAW]"

            data = data.strip()
            clean_data = (data.replace('\r', '')
                                .replace('\t', ' ')
                                .replace('\x00', '')
                                .replace('\x12', '')
                                .replace('\n', '')
                                .strip())
            
            raw_line = f"[{time_str}] {prefix} {clean_data}\n"
            # print(f"Raw line: {raw_line} at {timestamp}, encrypted={encrypted}, mock={mock}")

            # แทรกใน Text widget
            try:
                self.raw_text.insert("end", raw_line)
                self.raw_text.see("end")
                self.raw_text.update_idletasks()
            except tk.TclError:
                pass
            
            # Try to parse as JSON for structured display
            try:
                parsed_data = json.loads(clean_data)
                if self.is_sensor_data(parsed_data):
                    self.add_parsed_data(parsed_data, time_str)
                    
                    # Store in history
                    parsed_data['timestamp'] = timestamp
                    parsed_data['encrypted'] = encrypted
                    parsed_data['mock'] = mock
                    parsed_data['raw'] = "[RAW]"
                    self.data_history.append(parsed_data)
                    
                    # Limit history size
                    if len(self.data_history) > self.max_history:
                        self.data_history = self.data_history[-self.max_history:]
                    
                    # Schedule updates to avoid immediate widget operations
                    self.after(100, self.delayed_update)
                        
            except (json.JSONDecodeError, KeyError):
                # Not valid JSON or sensor data
                pass
    
    def delayed_update(self):
        """Delayed update to avoid widget conflicts"""
        try:
            self.update_statistics()
            self.update_devices_display()
        except tk.TclError:
            pass
    
    def is_sensor_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains sensor information"""
        return (
            isinstance(data.get("sensors"), dict) and
            isinstance(data.get("device_id"), str)
        )
            
    def add_parsed_data(self, data: Dict[str, Any], time_str: str):
        """Add parsed sensor data to tree view"""
        try:
            readings = data.get("sensors", {})
            device_id = data.get("device_id", "Unknown")

            values = (
                time_str,
                device_id,
                f"{readings.get('ph', 0):.2f}",
                f"{readings.get('ec', 0):.1f}",
                f"{readings.get('tds', 0):.1f}",
                f"{readings.get('sal', 0):.2f}",
                f"{readings.get('do', 0):.2f}",
                f"{readings.get('sat', 0):.1f}",
            )

            self.data_tree.insert("", "end", values=values)

            # Auto-scroll
            children = self.data_tree.get_children()
            if children:
                self.data_tree.see(children[-1])
        except tk.TclError:
            pass
    
    def update_devices_display(self):
        """Update devices display with latest information"""
        try:
            # Clear existing widgets safely
            for widget in self.devices_container.winfo_children():
                self.safe_widget_destroy(widget)
            
            if not self.data_history:
                # Show no devices message
                self.create_no_devices_message()
                return
            
            # Group data by device
            device_data = {}
            for entry in self.data_history:
                device_id = entry.get("device_id", "Unknown")
                if device_id not in device_data:
                    device_data[device_id] = {
                        "first_seen": entry["timestamp"],
                        "last_seen": entry["timestamp"],
                        "message_count": 0,
                        "latest_sensors": {}
                    }
                
                device_data[device_id]["last_seen"] = entry["timestamp"]
                device_data[device_id]["message_count"] += 1
                device_data[device_id]["latest_sensors"] = entry.get("sensors", {})
            
            # Create device cards
            row = 0
            for device_id, info in device_data.items():
                self.create_device_card(device_id, info, row)
                row += 1
                
        except tk.TclError:
            pass
    
    def create_no_devices_message(self):
        """Create no devices message"""
        try:
            no_devices_frame = ctk.CTkFrame(self.devices_container)
            no_devices_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=20)
            no_devices_frame.grid_columnconfigure(0, weight=1)
            self._widget_references.add(no_devices_frame)
            
            icon_label = ctk.CTkLabel(
                no_devices_frame,
                text="📱",
                font=ctk.CTkFont(size=48)
            )
            icon_label.grid(row=0, column=0, pady=(20, 10))
            self._widget_references.add(icon_label)
            
            message_label = ctk.CTkLabel(
                no_devices_frame,
                text="No devices detected yet",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            message_label.grid(row=1, column=0, pady=(0, 20))
            self._widget_references.add(message_label)
        except tk.TclError:
            pass
    
    def create_device_card(self, device_id: str, info: Dict[str, Any], row: int):
        """Create a card for each device"""
        try:
            card_frame = ctk.CTkFrame(self.devices_container)
            card_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
            card_frame.grid_columnconfigure(1, weight=1)
            self._widget_references.add(card_frame)
            
            # Device icon and ID
            icon_label = ctk.CTkLabel(
                card_frame,
                text="📱",
                font=ctk.CTkFont(size=24)
            )
            icon_label.grid(row=0, column=0, rowspan=2, padx=15, pady=15)
            self._widget_references.add(icon_label)
            
            device_label = ctk.CTkLabel(
                card_frame,
                text=f"Device: {device_id}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            device_label.grid(row=0, column=1, sticky="w", padx=10, pady=(15, 5))
            self._widget_references.add(device_label)
            
            # Device info
            first_seen = datetime.fromtimestamp(info["first_seen"]).strftime("%H:%M:%S")
            last_seen = datetime.fromtimestamp(info["last_seen"]).strftime("%H:%M:%S")
            
            info_text = f"Messages: {info['message_count']} | First seen: {first_seen} | Last seen: {last_seen}"
            info_label = ctk.CTkLabel(
                card_frame,
                text=info_text,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            info_label.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 5))
            self._widget_references.add(info_label)
            
            # Latest sensor values
            sensors_frame = ctk.CTkFrame(card_frame)
            sensors_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
            sensors_frame.grid_columnconfigure((0, 1, 2), weight=1)
            self._widget_references.add(sensors_frame)
            
            self.create_sensor_values_display(sensors_frame, info.get("latest_sensors", {}))
            
        except tk.TclError:
            pass
    
    def create_sensor_values_display(self, parent_frame, latest_sensors: Dict[str, Any]):
        """Create sensor values display"""
        try:
            sensors_title = ctk.CTkLabel(
                parent_frame,
                text="Latest Sensor Values:",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            sensors_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5))
            self._widget_references.add(sensors_title)
            
            # Display sensor values in a grid
            sensor_labels = {
                "ph": "pH",
                "ec": "EC (µS/cm)",
                "tds": "TDS (ppm)",
                "sal": "Salinity (ppt)",
                "do": "DO (mg/L)",
                "sat": "Sat (%)"
            }
            
            row_idx = 1
            col_idx = 0
            for sensor_key, label in sensor_labels.items():
                if sensor_key in latest_sensors:
                    value = latest_sensors[sensor_key]
                    sensor_text = f"{label}: {value:.2f}"
                    
                    sensor_label = ctk.CTkLabel(
                        parent_frame,
                        text=sensor_text,
                        font=ctk.CTkFont(size=11)
                    )
                    sensor_label.grid(row=row_idx, column=col_idx, padx=5, pady=2, sticky="w")
                    self._widget_references.add(sensor_label)
                    
                    col_idx += 1
                    if col_idx >= 3:
                        col_idx = 0
                        row_idx += 1
            
            # Add some padding at the bottom
            if row_idx > 1 or col_idx > 0:
                parent_frame.grid_rowconfigure(row_idx, minsize=10)
                
        except tk.TclError:
            pass
    
    def clear_data(self):
        """Clear all displayed data"""
        with self._update_lock:
            try:
                self.raw_text.delete("1.0", "end")
                
                # Clear tree view
                for item in self.data_tree.get_children():
                    self.data_tree.delete(item)
                
                # Clear history
                self.data_history.clear()
                
                # Clear and close matplotlib figures
                if self.canvas:
                    try:
                        self.canvas.get_tk_widget().destroy()
                    except tk.TclError:
                        pass
                    self.canvas = None
                
                plt.close('all')  # Close all matplotlib figures
                
                # Clear widget references
                for widget in self._widget_references.copy():
                    self.safe_widget_destroy(widget)
                self._widget_references.clear()
                
                if self.stats_info_frame:
                    self.safe_widget_destroy(self.stats_info_frame)
                    self.stats_info_frame = None
                
                # Update displays
                self.after(100, self.update_statistics)
                self.after(100, self.update_devices_display)
                
            except tk.TclError:
                pass
    
    def export_data(self):
        """Export data to file"""
        from tkinter import filedialog
        
        if not self.data_history:
            tk.messagebox.showwarning("No Data", "No data to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.data_history, f, indent=2)
                tk.messagebox.showinfo("Export Complete", f"Data exported to {filename}")
            except Exception as e:
                tk.messagebox.showerror("Export Error", f"Failed to export data: {e}")
    
    def on_graph_type_change(self, value):
        """Handle graph type change"""
        self.after(100, self.update_statistics)
    
    def update_statistics(self):
        """Update statistics display"""
        try:
            if not self.data_history:
                self.show_no_data_message()
                return

            stats = self.calculate_statistics()
            
            # Clear existing content safely
            for widget in self.stats_scroll.winfo_children():
                self.safe_widget_destroy(widget)
            
            # Create info cards
            self.create_info_cards(stats)
            
            # Create graphs based on selected type
            graph_type = self.graph_type_var.get()
            if graph_type == "overview":
                self.create_overview_graphs(stats)
            elif graph_type == "trends":
                self.create_trend_graphs(stats)
            elif graph_type == "comparison":
                self.create_comparison_graphs(stats)
                
        except tk.TclError:
            pass
    
    def show_no_data_message(self):
        """Show message when no data is available"""
        try:
            # Clear existing content
            for widget in self.stats_scroll.winfo_children():
                self.safe_widget_destroy(widget)
            
            no_data_frame = ctk.CTkFrame(self.stats_scroll)
            no_data_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=20)
            no_data_frame.grid_columnconfigure(0, weight=1)
            self._widget_references.add(no_data_frame)
            
            icon_label = ctk.CTkLabel(
                no_data_frame,
                text="📊",
                font=ctk.CTkFont(size=48)
            )
            icon_label.grid(row=0, column=0, pady=(20, 10))
            self._widget_references.add(icon_label)
            
            message_label = ctk.CTkLabel(
                no_data_frame,
                text="No data available for statistics",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            message_label.grid(row=1, column=0, pady=(0, 20))
            self._widget_references.add(message_label)
            
        except tk.TclError:
            pass
    
    def create_info_cards(self, stats: Dict[str, Any]):
        """Create information cards with statistics"""
        try:
            info_frame = ctk.CTkFrame(self.stats_scroll)
            info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            info_frame.grid_columnconfigure((0, 1, 2), weight=1)
            self._widget_references.add(info_frame)
            
            # Total messages card
            total_card = self.create_stat_card(
                info_frame,
                "📈 Total Messages",
                str(stats['total_messages']),
                "#4CAF50"
            )
            total_card.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            # Active devices card
            devices_count = len(stats['devices'])
            devices_card = self.create_stat_card(
                info_frame,
                "📱 Active Devices",
                str(devices_count),
                "#2196F3"
            )
            devices_card.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Latest reading card
            if self.data_history:
                latest_time = datetime.fromtimestamp(self.data_history[-1]['timestamp'])
                time_str = latest_time.strftime("%H:%M:%S")
                latest_card = self.create_stat_card(
                    info_frame,
                    "🕐 Latest Reading",
                    time_str,
                    "#FF9800"
                )
                latest_card.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
                
        except tk.TclError:
            pass
    
    def create_stat_card(self, parent, title: str, value: str, color: str):
        """Create a statistics card"""
        try:
            card = ctk.CTkFrame(parent)
            card.grid_columnconfigure(0, weight=1)
            self._widget_references.add(card)
            
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            title_label.grid(row=0, column=0, padx=10, pady=(10, 5))
            self._widget_references.add(title_label)
            
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=color
            )
            value_label.grid(row=1, column=0, padx=10, pady=(0, 10))
            self._widget_references.add(value_label)
            
            return card
            
        except tk.TclError:
            return None
    
    def create_overview_graphs(self, stats: Dict[str, Any]):
        """Create overview graphs with modern styling"""
        try:
            # Close any existing figures to prevent memory leaks
            plt.close('all')
            
            # Create matplotlib figure with proper settings
            fig = plt.figure(figsize=(15, 10))
            fig.suptitle('Sensor Data Overview', fontsize=16, fontweight='bold', y=0.98)
            
            # Modern color palette
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
            
            sensors = ["ph", "ec", "tds", "sal", "do", "sat"]
            sensor_names = {
                "ph": "pH Level",
                "ec": "Electrical Conductivity",
                "tds": "Total Dissolved Solids",
                "sal": "Salinity",
                "do": "Dissolved Oxygen",
                "sat": "Oxygen Saturation"
            }
            
            sensor_units = {
                "ph": "",
                "ec": "µS/cm",
                "tds": "ppm",
                "sal": "ppt",
                "do": "mg/L",
                "sat": "%"
            }
            
            for idx, sensor in enumerate(sensors):
                ax = fig.add_subplot(2, 3, idx + 1)
                
                data = stats.get(sensor, {})
                
                if data and data.get('count', 0) > 0:
                    # Create bar chart with gradient effect
                    values = [data["min"], data["avg"], data["max"]]
                    labels = ["Min", "Avg", "Max"]
                    
                    bars = ax.bar(labels, values, color=colors[idx], alpha=0.7, edgecolor='white', linewidth=2)
                    
                    # Add value labels on bars
                    for bar, value in zip(bars, values):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                               f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
                    
                    # Styling
                    ax.set_title(f'{sensor_names[sensor]}', fontsize=12, fontweight='bold', pad=15)
                    ax.set_ylabel(f'Value ({sensor_units[sensor]})', fontsize=10)
                    ax.grid(True, alpha=0.3, linestyle='--')
                    ax.set_facecolor('#f8f9fa')
                    
                    # Set y-axis to start from 0 with some padding
                    y_max = max(values) * 1.1
                    ax.set_ylim(0, y_max)
                    
                else:
                    ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', 
                           fontsize=12, transform=ax.transAxes, style='italic')
                    ax.set_title(f'{sensor_names[sensor]}', fontsize=12, fontweight='bold', pad=15)
                    ax.set_facecolor('#f8f9fa')
            
            plt.tight_layout()
            
            # Embed in tkinter
            self.embed_matplotlib_figure(fig, row=1)
            
        except Exception as e:
            print(f"Error creating overview graphs: {e}")
            self.show_graph_error("Error creating overview graphs")
    
    def create_trend_graphs(self, stats: Dict[str, Any]):
        """Create trend graphs showing data over time"""
        if len(self.data_history) < 2:
            self.show_insufficient_data_message("Need at least 2 data points for trend analysis")
            return
        
        try:
            # Close any existing figures
            plt.close('all')
            
            # Prepare time series data
            timestamps = [entry['timestamp'] for entry in self.data_history]
            time_labels = [datetime.fromtimestamp(ts).strftime("%H:%M:%S") for ts in timestamps]
            
            # Create figure with subplots
            fig = plt.figure(figsize=(15, 12))
            fig.suptitle('Sensor Data Trends Over Time', fontsize=16, fontweight='bold', y=0.98)
            
            sensors = ["ph", "ec", "tds", "sal", "do", "sat"]
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
            
            for idx, sensor in enumerate(sensors):
                ax = fig.add_subplot(3, 2, idx + 1)
                
                # Extract sensor values
                values = []
                for entry in self.data_history:
                    sensor_data = entry.get('sensors', {})
                    values.append(sensor_data.get(sensor, 0))
                
                if values:
                    # Create line plot with markers
                    ax.plot(range(len(values)), values, color=colors[idx], linewidth=2, 
                           marker='o', markersize=4, alpha=0.8)
                    
                    # Add trend line
                    if len(values) > 1:
                        z = np.polyfit(range(len(values)), values, 1)
                        p = np.poly1d(z)
                        ax.plot(range(len(values)), p(range(len(values))), 
                               color=colors[idx], linestyle='--', alpha=0.6)
                    
                    # Styling
                    ax.set_title(f'{sensor.upper()} Trend', fontsize=12, fontweight='bold')
                    ax.set_ylabel('Value', fontsize=10)
                    ax.grid(True, alpha=0.3)
                    ax.set_facecolor('#f8f9fa')
                    
                    # Set x-axis labels (show every nth label to avoid crowding)
                    step = max(1, len(time_labels) // 10)
                    ax.set_xticks(range(0, len(time_labels), step))
                    ax.set_xticklabels([time_labels[i] for i in range(0, len(time_labels), step)], 
                                      rotation=45, ha='right')
            
            plt.tight_layout()
            self.embed_matplotlib_figure(fig, row=1)
            
        except Exception as e:
            print(f"Error creating trend graphs: {e}")
            self.show_graph_error("Error creating trend graphs")
    
    def create_comparison_graphs(self, stats: Dict[str, Any]):
        """Create comparison graphs between different sensors"""
        try:
            # Close any existing figures
            plt.close('all')
            
            # Create radar chart for sensor comparison
            fig = plt.figure(figsize=(15, 7))
            fig.suptitle('Sensor Data Comparison', fontsize=16, fontweight='bold', y=0.98)
            
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)
            
            # Normalize data for radar chart
            sensors = ["ph", "ec", "tds", "sal", "do", "sat"]
            values = []
            labels = []
            
            for sensor in sensors:
                data = stats.get(sensor, {})
                if data and data.get('count', 0) > 0:
                    values.append(data['avg'])
                    labels.append(sensor.upper())
            
            if values:
                # Create pie chart for device distribution
                if stats['devices']:
                    device_names = list(stats['devices'].keys())
                    device_counts = list(stats['devices'].values())
                    
                    # Create pie chart
                    wedges, texts, autotexts = ax1.pie(device_counts, labels=device_names, 
                                                      autopct='%1.1f%%', startangle=90,
                                                      colors=plt.cm.Set3(np.linspace(0, 1, len(device_names))))
                    
                    ax1.set_title('Data Distribution by Device', fontsize=12, fontweight='bold')
                    
                    # Style the text
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                
                # Create bar chart for sensor averages
                colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
                bars = ax2.bar(labels, values, color=colors[:len(values)], alpha=0.7, 
                              edgecolor='white', linewidth=2)
                
                # Add value labels
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                            f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
                
                ax2.set_title('Average Sensor Values', fontsize=12, fontweight='bold')
                ax2.set_ylabel('Average Value', fontsize=10)
                ax2.grid(True, alpha=0.3, axis='y')
                ax2.set_facecolor('#f8f9fa')
                
                # Rotate x-axis labels
                plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
            
            plt.tight_layout()
            self.embed_matplotlib_figure(fig, row=1)
            
        except Exception as e:
            print(f"Error creating comparison graphs: {e}")
            self.show_graph_error("Error creating comparison graphs")
    
    def show_insufficient_data_message(self, message: str):
        """Show message when insufficient data for analysis"""
        try:
            info_frame = ctk.CTkFrame(self.stats_scroll)
            info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=20)
            info_frame.grid_columnconfigure(0, weight=1)
            self._widget_references.add(info_frame)
            
            icon_label = ctk.CTkLabel(
                info_frame,
                text="⚠️",
                font=ctk.CTkFont(size=48)
            )
            icon_label.grid(row=0, column=0, pady=(20, 10))
            self._widget_references.add(icon_label)
            
            message_label = ctk.CTkLabel(
                info_frame,
                text=message,
                font=ctk.CTkFont(size=14),
                wraplength=400
            )
            message_label.grid(row=1, column=0, pady=(0, 20))
            self._widget_references.add(message_label)
            
        except tk.TclError:
            pass
    
    def embed_matplotlib_figure(self, fig, row: int):
        """Embed matplotlib figure in tkinter"""
        try:
            # Clear existing canvas
            if self.canvas:
                try:
                    self.canvas.get_tk_widget().destroy()
                except tk.TclError:
                    pass
                self.canvas = None
            
            # Create new canvas
            canvas_frame = ctk.CTkFrame(self.stats_scroll)
            canvas_frame.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)
            canvas_frame.grid_columnconfigure(0, weight=1)
            canvas_frame.grid_rowconfigure(0, weight=1)
            self._widget_references.add(canvas_frame)
            
            self.canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            
        except Exception as e:
            print(f"Error embedding matplotlib figure: {e}")
            # Clean up in case of error
            if hasattr(fig, 'clear'):
                fig.clear()
            plt.close(fig)
    
    def show_graph_error(self, message: str):
        """Show error message when graph creation fails"""
        try:
            error_frame = ctk.CTkFrame(self.stats_scroll)
            error_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=20)
            error_frame.grid_columnconfigure(0, weight=1)
            self._widget_references.add(error_frame)
            
            icon_label = ctk.CTkLabel(
                error_frame,
                text="⚠️",
                font=ctk.CTkFont(size=48)
            )
            icon_label.grid(row=0, column=0, pady=(20, 10))
            self._widget_references.add(icon_label)
            
            message_label = ctk.CTkLabel(
                error_frame,
                text=message,
                font=ctk.CTkFont(size=14),
                wraplength=400
            )
            message_label.grid(row=1, column=0, pady=(0, 20))
            self._widget_references.add(message_label)
            
        except tk.TclError:
            pass
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from data history"""
        if not self.data_history:
            return {}
        
        devices = {}
        
        # เตรียม list เก็บค่าแต่ละ sensor
        ph_values = []
        ec_values = []
        tds_values = []
        sal_values = []
        do_values = []
        sat_values = []
        
        for entry in self.data_history:
            device_id = entry.get("device_id", "Unknown")
            devices[device_id] = devices.get(device_id, 0) + 1
            
            sensors = entry.get("sensors", {})
            if "ph" in sensors:
                ph_values.append(sensors["ph"])
            if "ec" in sensors:
                ec_values.append(sensors["ec"])
            if "tds" in sensors:
                tds_values.append(sensors["tds"])
            if "sal" in sensors:
                sal_values.append(sensors["sal"])
            if "do" in sensors:
                do_values.append(sensors["do"])
            if "sat" in sensors:
                sat_values.append(sensors["sat"])
        
        stats = {
            "total_messages": len(self.data_history),
            "devices": devices,
            "ph": self.calc_stats(ph_values),
            "ec": self.calc_stats(ec_values),
            "tds": self.calc_stats(tds_values),
            "sal": self.calc_stats(sal_values),
            "do": self.calc_stats(do_values),
            "sat": self.calc_stats(sat_values),
        }
        
        return stats
    
    def calc_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate min, max, average for a list of values"""
        if not values:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }
    
    def destroy(self):
        """Override destroy to cleanup properly"""
        try:
            # Close all matplotlib figures
            plt.close('all')
            
            # Clear widget references
            for widget in self._widget_references.copy():
                self.safe_widget_destroy(widget)
            self._widget_references.clear()
            
            # Clear canvas
            if self.canvas:
                try:
                    self.canvas.get_tk_widget().destroy()
                except tk.TclError:
                    pass
                self.canvas = None
            
            # Call parent destroy
            super().destroy()
            
        except tk.TclError:
            pass