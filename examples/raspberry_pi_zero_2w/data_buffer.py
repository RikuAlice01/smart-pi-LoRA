"""
Data buffering system for Raspberry Pi LoRa node
Handles local data storage, buffering, and offline operation
"""

import json
import sqlite3
import time
import os
import threading
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import gzip
import pickle

@dataclass
class BufferConfig:
    """Configuration for data buffering"""
    # Database settings
    db_path: str = "sensor_data.db"
    max_db_size_mb: int = 100
    
    # Buffer settings
    max_memory_buffer: int = 1000
    flush_interval: int = 30  # seconds
    
    # Retention settings
    max_retention_days: int = 30
    cleanup_interval: int = 3600  # seconds (1 hour)
    
    # Export settings
    export_batch_size: int = 100
    compression_enabled: bool = True

class DataBuffer:
    """Manages local data buffering and persistence"""
    
    def __init__(self, config: BufferConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Memory buffers
        self.sensor_buffer = []
        self.transmission_buffer = []
        self.failed_transmissions = []
        
        # Threading
        self.buffer_lock = threading.Lock()
        self.db_lock = threading.Lock()
        
        # Background threads
        self.flush_thread = None
        self.cleanup_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            "total_records": 0,
            "memory_buffer_size": 0,
            "db_size_mb": 0,
            "failed_transmissions": 0,
            "successful_flushes": 0,
            "last_cleanup": None,
            "last_flush": None
        }
        
        # Initialize database
        self.init_database()
        
        self.logger.info("Data buffer initialized")
    
    def init_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                # Create sensor data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        device_id TEXT NOT NULL,
                        data_json TEXT NOT NULL,
                        data_type TEXT DEFAULT 'sensor',
                        transmitted BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        transmitted_at DATETIME NULL
                    )
                ''')
                
                # Create transmission log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transmission_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        device_id TEXT NOT NULL,
                        payload_size INTEGER NOT NULL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT NULL,
                        retry_count INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
                    ON sensor_data(timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sensor_transmitted 
                    ON sensor_data(transmitted)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_transmission_timestamp 
                    ON transmission_log(timestamp)
                ''')
                
                conn.commit()
                self.logger.info(f"Database initialized: {self.config.db_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def start(self):
        """Start background threads"""
        if self.running:
            return
        
        self.running = True
        
        # Start flush thread
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        self.logger.info("Data buffer background threads started")
    
    def stop(self):
        """Stop background threads and flush remaining data"""
        self.running = False
        
        # Wait for threads to finish
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=5)
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        # Final flush
        self.flush_to_database()
        
        self.logger.info("Data buffer stopped")
    
    def add_sensor_data(self, data: Dict[str, Any]):
        """Add sensor data to buffer"""
        try:
            with self.buffer_lock:
                # Add timestamp if not present
                if 'timestamp' not in data:
                    data['timestamp'] = time.time()
                
                # Add to memory buffer
                self.sensor_buffer.append({
                    'timestamp': data['timestamp'],
                    'device_id': data.get('device_id', 'unknown'),
                    'data': data,
                    'type': 'sensor'
                })
                
                # Limit memory buffer size
                if len(self.sensor_buffer) > self.config.max_memory_buffer:
                    self.sensor_buffer.pop(0)
                
                self.stats["memory_buffer_size"] = len(self.sensor_buffer)
                
            self.logger.debug(f"Added sensor data to buffer: {data.get('device_id', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to add sensor data to buffer: {e}")
    
    def add_transmission_log(self, device_id: str, payload_size: int, 
                           success: bool, error_message: str = None):
        """Add transmission log entry"""
        try:
            log_entry = {
                'timestamp': time.time(),
                'device_id': device_id,
                'payload_size': payload_size,
                'success': success,
                'error_message': error_message
            }
            
            with self.buffer_lock:
                self.transmission_buffer.append(log_entry)
                
                if not success:
                    self.stats["failed_transmissions"] += 1
            
            self.logger.debug(f"Added transmission log: {device_id} - {'Success' if success else 'Failed'}")
            
        except Exception as e:
            self.logger.error(f"Failed to add transmission log: {e}")
    
    def get_unsent_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get unsent data from database"""
        try:
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, device_id, data_json, data_type
                    FROM sensor_data 
                    WHERE transmitted = FALSE 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                ''', (limit,))
                
                results = []
                for row in cursor.fetchall():
                    try:
                        data = json.loads(row[3])
                        results.append({
                            'id': row[0],
                            'timestamp': row[1],
                            'device_id': row[2],
                            'data': data,
                            'type': row[4]
                        })
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse JSON for record {row[0]}")
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get unsent data: {e}")
            return []
    
    def mark_as_transmitted(self, record_ids: List[int]):
        """Mark records as transmitted"""
        try:
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                placeholders = ','.join(['?'] * len(record_ids))
                cursor.execute(f'''
                    UPDATE sensor_data 
                    SET transmitted = TRUE, transmitted_at = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                ''', record_ids)
                
                conn.commit()
                self.logger.debug(f"Marked {len(record_ids)} records as transmitted")
                
        except Exception as e:
            self.logger.error(f"Failed to mark records as transmitted: {e}")
    
    def flush_to_database(self):
        """Flush memory buffers to database"""
        try:
            with self.buffer_lock:
                sensor_data = self.sensor_buffer.copy()
                transmission_data = self.transmission_buffer.copy()
                self.sensor_buffer.clear()
                self.transmission_buffer.clear()
            
            if not sensor_data and not transmission_data:
                return
            
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert sensor data
                for record in sensor_data:
                    cursor.execute('''
                        INSERT INTO sensor_data (timestamp, device_id, data_json, data_type)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        record['timestamp'],
                        record['device_id'],
                        json.dumps(record['data']),
                        record['type']
                    ))
                
                # Insert transmission logs
                for log in transmission_data:
                    cursor.execute('''
                        INSERT INTO transmission_log 
                        (timestamp, device_id, payload_size, success, error_message)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        log['timestamp'],
                        log['device_id'],
                        log['payload_size'],
                        log['success'],
                        log['error_message']
                    ))
                
                conn.commit()
                
                self.stats["successful_flushes"] += 1
                self.stats["last_flush"] = time.time()
                self.stats["total_records"] += len(sensor_data)
                
                self.logger.info(f"Flushed {len(sensor_data)} sensor records and "
                               f"{len(transmission_data)} transmission logs to database")
                
        except Exception as e:
            self.logger.error(f"Failed to flush data to database: {e}")
    
    def cleanup_old_data(self):
        """Remove old data based on retention policy"""
        try:
            cutoff_time = time.time() - (self.config.max_retention_days * 24 * 3600)
            
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old sensor data
                cursor.execute('''
                    DELETE FROM sensor_data 
                    WHERE timestamp < ? AND transmitted = TRUE
                ''', (cutoff_time,))
                
                sensor_deleted = cursor.rowcount
                
                # Delete old transmission logs
                cursor.execute('''
                    DELETE FROM transmission_log 
                    WHERE timestamp < ?
                ''', (cutoff_time,))
                
                log_deleted = cursor.rowcount
                
                # Vacuum database to reclaim space
                cursor.execute('VACUUM')
                
                conn.commit()
                
                self.stats["last_cleanup"] = time.time()
                
                self.logger.info(f"Cleanup completed: deleted {sensor_deleted} sensor records "
                               f"and {log_deleted} transmission logs")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def get_database_size(self) -> float:
        """Get database size in MB"""
        try:
            if os.path.exists(self.config.db_path):
                size_bytes = os.path.getsize(self.config.db_path)
                size_mb = size_bytes / (1024 * 1024)
                self.stats["db_size_mb"] = round(size_mb, 2)
                return size_mb
            return 0
        except Exception as e:
            self.logger.error(f"Failed to get database size: {e}")
            return 0
    
    def export_data(self, start_time: float = None, end_time: float = None, 
                   format: str = 'json') -> str:
        """Export data to file"""
        try:
            # Set default time range if not provided
            if end_time is None:
                end_time = time.time()
            if start_time is None:
                start_time = end_time - (24 * 3600)  # Last 24 hours
            
            # Generate filename
            start_dt = datetime.fromtimestamp(start_time)
            end_dt = datetime.fromtimestamp(end_time)
            filename = f"sensor_data_{start_dt.strftime('%Y%m%d_%H%M')}_{end_dt.strftime('%Y%m%d_%H%M')}"
            
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, device_id, data_json, transmitted, created_at
                    FROM sensor_data 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC
                ''', (start_time, end_time))
                
                records = []
                for row in cursor.fetchall():
                    try:
                        data = json.loads(row[2])
                        records.append({
                            'timestamp': row[0],
                            'device_id': row[1],
                            'data': data,
                            'transmitted': bool(row[3]),
                            'created_at': row[4]
                        })
                    except json.JSONDecodeError:
                        continue
                
                if format.lower() == 'json':
                    filename += '.json'
                    if self.config.compression_enabled:
                        filename += '.gz'
                        with gzip.open(filename, 'wt') as f:
                            json.dump(records, f, indent=2)
                    else:
                        with open(filename, 'w') as f:
                            json.dump(records, f, indent=2)
                
                elif format.lower() == 'csv':
                    import csv
                    filename += '.csv'
                    
                    with open(filename, 'w', newline='') as f:
                        if records:
                            # Flatten the data structure for CSV
                            fieldnames = ['timestamp', 'device_id', 'transmitted', 'created_at']
                            # Add data fields from first record
                            if records[0]['data']:
                                fieldnames.extend(records[0]['data'].keys())
                            
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            
                            for record in records:
                                row = {
                                    'timestamp': record['timestamp'],
                                    'device_id': record['device_id'],
                                    'transmitted': record['transmitted'],
                                    'created_at': record['created_at']
                                }
                                row.update(record['data'])
                                writer.writerow(row)
                
                self.logger.info(f"Exported {len(records)} records to {filename}")
                return filename
                
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        try:
            # Update database size
            self.get_database_size()
            
            # Get record counts from database
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM sensor_data')
                total_records = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM sensor_data WHERE transmitted = FALSE')
                unsent_records = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM transmission_log WHERE success = FALSE')
                failed_transmissions = cursor.fetchone()[0]
                
                # Get oldest and newest records
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data')
                time_range = cursor.fetchone()
                
            self.stats.update({
                "total_records": total_records,
                "unsent_records": unsent_records,
                "failed_transmissions": failed_transmissions,
                "oldest_record": time_range[0] if time_range[0] else None,
                "newest_record": time_range[1] if time_range[1] else None
            })
            
            return self.stats.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return self.stats.copy()
    
    def _flush_loop(self):
        """Background thread for periodic flushing"""
        while self.running:
            try:
                time.sleep(self.config.flush_interval)
                if self.running:
                    self.flush_to_database()
            except Exception as e:
                self.logger.error(f"Error in flush loop: {e}")
    
    def _cleanup_loop(self):
        """Background thread for periodic cleanup"""
        while self.running:
            try:
                time.sleep(self.config.cleanup_interval)
                if self.running:
                    self.cleanup_old_data()
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")

class OfflineManager:
    """Manages offline operation and data synchronization"""
    
    def __init__(self, data_buffer: DataBuffer):
        self.data_buffer = data_buffer
        self.logger = logging.getLogger(__name__)
        
        # Offline state
        self.is_online = True
        self.offline_since = None
        self.sync_in_progress = False
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        
    def set_offline(self):
        """Set system to offline mode"""
        if self.is_online:
            self.is_online = False
            self.offline_since = time.time()
            self.logger.warning("System is now OFFLINE - buffering data locally")
    
    def set_online(self):
        """Set system to online mode and start sync"""
        if not self.is_online:
            offline_duration = time.time() - self.offline_since if self.offline_since else 0
            self.is_online = True
            self.offline_since = None
            self.logger.info(f"System is now ONLINE - was offline for {offline_duration:.1f} seconds")
            
            # Start background sync
            threading.Thread(target=self._sync_offline_data, daemon=True).start()
    
    def _sync_offline_data(self):
        """Synchronize offline data"""
        if self.sync_in_progress:
            return
        
        self.sync_in_progress = True
        self.logger.info("Starting offline data synchronization...")
        
        try:
            # Get unsent data in batches
            batch_size = 50
            total_synced = 0
            
            while True:
                unsent_data = self.data_buffer.get_unsent_data(batch_size)
                if not unsent_data:
                    break
                
                # Process batch
                synced_ids = []
                for record in unsent_data:
                    # Here you would normally send the data via LoRa
                    # For now, we'll just mark it as transmitted
                    synced_ids.append(record['id'])
                
                # Mark as transmitted
                if synced_ids:
                    self.data_buffer.mark_as_transmitted(synced_ids)
                    total_synced += len(synced_ids)
                
                # Small delay between batches
                time.sleep(1)
            
            self.logger.info(f"Offline data synchronization completed: {total_synced} records synced")
            
        except Exception as e:
            self.logger.error(f"Failed to sync offline data: {e}")
        finally:
            self.sync_in_progress = False
