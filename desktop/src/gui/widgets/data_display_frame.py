"""
Data display widget for showing received sensor data
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
from typing import Dict, Any, List

class DataDisplayFrame(ctk.CTkFrame):
    """Frame for displaying received data"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.data_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
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
        
        # Raw data tab
        self.raw_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.raw_frame, text="Raw Data")
        self.setup_raw_data_tab()
        
        # Parsed data tab
        self.parsed_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.parsed_frame, text="Sensor Data")
        self.setup_parsed_data_tab()
        
        # Statistics tab
        self.stats_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        self.setup_statistics_tab()
    
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
        columns = ("Time", "Device", "Temperature", "Humidity", "Pressure", "Battery", "RSSI")
        self.data_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100, anchor="center")
        
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
    
    def setup_statistics_tab(self):
        """Setup statistics tab"""
        self.stats_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_rowconfigure(0, weight=1)
        
        # Statistics display
        stats_text_frame = ctk.CTkFrame(self.stats_frame)
        stats_text_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        stats_text_frame.grid_columnconfigure(0, weight=1)
        stats_text_frame.grid_rowconfigure(0, weight=1)
        
        self.stats_text = ctk.CTkTextbox(stats_text_frame, wrap="word")
        self.stats_text.grid(row=0, column=0, sticky="nsew")
        
        # Update button
        update_stats_btn = ctk.CTkButton(
            self.stats_frame,
            text="Update Statistics",
            command=self.update_statistics
        )
        update_stats_btn.grid(row=1, column=0, pady=10)
    
    def add_data(self, data: str, timestamp: float, encrypted: bool = False, mock: bool = False):
        """Add new data to display"""
        print(f"Adding data: {data} at {timestamp}, encrypted={encrypted}, mock={mock}")
        # Format timestamp
        dt = datetime.fromtimestamp(timestamp)
        time_str = dt.strftime("%H:%M:%S")
        
        # Add to raw data display
        prefix = "[ENCRYPTED]" if encrypted else "[MOCK]" if mock else "[RAW]"
        print(f"Data prefix: {prefix}")

        if prefix == "[RAW]":
            data = data.strip()
            clean_data = (data.replace('\r', '')
                            .replace('\t', ' ')
                            .replace('\x00', '')
                            .replace('\x12\x12', '')
                            .strip())
            print(f"Clean data: {clean_data}")
            print(f"Clean data repr: {repr(clean_data)}")
        else:
            clean_data = data.strip()
        # สร้าง raw line
        raw_line = f"[{time_str}] {prefix} {clean_data}\n"
            
        print(f"Raw line: {raw_line}")
        print(f"Raw line repr: {repr(raw_line)}")

        # แทรกใน Text widget
        self.raw_text.insert("end", raw_line)
        self.raw_text.see("end")

        # เพิ่มการ flush เพื่อให้แน่ใจว่าข้อมูลแสดงทันที  
        self.raw_text.update_idletasks()
        
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
                    
        except (json.JSONDecodeError, KeyError):
            # Not valid JSON or sensor data
            pass
    
    def is_sensor_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains sensor information"""
        required_fields = ["device_id", "temperature", "humidity"]
        return all(field in data for field in required_fields)
    
    def add_parsed_data(self, data: Dict[str, Any], time_str: str):
        """Add parsed sensor data to tree view"""
        values = (
            time_str,
            data.get("device_id", "Unknown"),
            f"{data.get('temperature', 0):.1f}°C",
            f"{data.get('humidity', 0):.1f}%",
            f"{data.get('pressure', 0):.1f} hPa",
            f"{data.get('battery', 0):.1f}%",
            f"{data.get('rssi', 0)} dBm"
        )
        
        self.data_tree.insert("", "end", values=values)
        
        # Auto-scroll to bottom
        children = self.data_tree.get_children()
        if children:
            self.data_tree.see(children[-1])
    
    def clear_data(self):
        """Clear all displayed data"""
        self.raw_text.delete("1.0", "end")
        
        # Clear tree view
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Clear history
        self.data_history.clear()
        
        # Clear statistics
        self.stats_text.delete("1.0", "end")
    
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
    
    def update_statistics(self):
        """Update statistics display"""
        if not self.data_history:
            self.stats_text.delete("1.0", "end")
            self.stats_text.insert("1.0", "No data available for statistics")
            return
        
        # Calculate statistics
        stats = self.calculate_statistics()
        
        # Format statistics text
        stats_text = self.format_statistics(stats)
        
        # Update display
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from data history"""
        if not self.data_history:
            return {}
        
        # Device counts
        devices = {}
        temperatures = []
        humidities = []
        pressures = []
        batteries = []
        
        for entry in self.data_history:
            device_id = entry.get("device_id", "Unknown")
            devices[device_id] = devices.get(device_id, 0) + 1
            
            if "temperature" in entry:
                temperatures.append(entry["temperature"])
            if "humidity" in entry:
                humidities.append(entry["humidity"])
            if "pressure" in entry:
                pressures.append(entry["pressure"])
            if "battery" in entry:
                batteries.append(entry["battery"])
        
        stats = {
            "total_messages": len(self.data_history),
            "devices": devices,
            "temperature": self.calc_stats(temperatures),
            "humidity": self.calc_stats(humidities),
            "pressure": self.calc_stats(pressures),
            "battery": self.calc_stats(batteries)
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
    
    def format_statistics(self, stats: Dict[str, Any]) -> str:
        """Format statistics for display"""
        if not stats:
            return "No statistics available"
        
        text = f"=== DATA STATISTICS ===\n\n"
        text += f"Total Messages: {stats['total_messages']}\n\n"
        
        # Device statistics
        text += "Device Message Counts:\n"
        for device, count in stats['devices'].items():
            text += f"  {device}: {count} messages\n"
        text += "\n"
        
        # Sensor statistics
        for sensor, data in stats.items():
            if sensor in ['temperature', 'humidity', 'pressure', 'battery'] and data['count'] > 0:
                unit = {"temperature": "°C", "humidity": "%", "pressure": " hPa", "battery": "%"}[sensor]
                text += f"{sensor.title()} Statistics:\n"
                text += f"  Count: {data['count']}\n"
                text += f"  Min: {data['min']:.2f}{unit}\n"
                text += f"  Max: {data['max']:.2f}{unit}\n"
                text += f"  Average: {data['avg']:.2f}{unit}\n\n"
        
        return text
