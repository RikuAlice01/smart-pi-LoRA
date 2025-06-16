#!/usr/bin/env python3
"""
Data management utility for LoRa sensor node
Provides tools for managing buffered data
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from data_buffer import DataBuffer, BufferConfig

def print_statistics(data_buffer: DataBuffer):
    """Print detailed buffer statistics"""
    stats = data_buffer.get_statistics()
    
    print("\n=== Data Buffer Statistics ===")
    print(f"Total Records: {stats.get('total_records', 0)}")
    print(f"Unsent Records: {stats.get('unsent_records', 0)}")
    print(f"Memory Buffer Size: {stats.get('memory_buffer_size', 0)}")
    print(f"Database Size: {stats.get('db_size_mb', 0):.2f} MB")
    print(f"Failed Transmissions: {stats.get('failed_transmissions', 0)}")
    print(f"Successful Flushes: {stats.get('successful_flushes', 0)}")
    
    if stats.get('oldest_record'):
        oldest = datetime.fromtimestamp(stats['oldest_record'])
        print(f"Oldest Record: {oldest.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if stats.get('newest_record'):
        newest = datetime.fromtimestamp(stats['newest_record'])
        print(f"Newest Record: {newest.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if stats.get('last_flush'):
        last_flush = datetime.fromtimestamp(stats['last_flush'])
        print(f"Last Flush: {last_flush.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if stats.get('last_cleanup'):
        last_cleanup = datetime.fromtimestamp(stats['last_cleanup'])
        print(f"Last Cleanup: {last_cleanup.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("==============================\n")

def export_data(data_buffer: DataBuffer, hours: int, format: str):
    """Export data to file"""
    print(f"Exporting last {hours} hours of data in {format.upper()} format...")
    
    end_time = time.time()
    start_time = end_time - (hours * 3600)
    
    filename = data_buffer.export_data(start_time, end_time, format)
    
    if filename:
        print(f"✅ Data exported to: {filename}")
        return True
    else:
        print("❌ Export failed")
        return False

def cleanup_data(data_buffer: DataBuffer, days: int):
    """Cleanup old data"""
    print(f"Cleaning up data older than {days} days...")
    
    # Temporarily override retention policy
    original_retention = data_buffer.config.max_retention_days
    data_buffer.config.max_retention_days = days
    
    try:
        data_buffer.cleanup_old_data()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
    finally:
        # Restore original retention policy
        data_buffer.config.max_retention_days = original_retention

def show_recent_data(data_buffer: DataBuffer, limit: int):
    """Show recent unsent data"""
    print(f"Showing last {limit} unsent records...")
    
    unsent_data = data_buffer.get_unsent_data(limit)
    
    if not unsent_data:
        print("No unsent data found")
        return
    
    print(f"\nFound {len(unsent_data)} unsent records:")
    print("-" * 80)
    
    for i, record in enumerate(unsent_data, 1):
        timestamp = datetime.fromtimestamp(record['timestamp'])
        print(f"{i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {record['device_id']}")
        
        # Show some data fields
        data = record['data']
        if 'temperature' in data:
            print(f"   Temperature: {data['temperature']}°C")
        if 'humidity' in data:
            print(f"   Humidity: {data['humidity']}%")
        if 'pressure' in data:
            print(f"   Pressure: {data['pressure']} hPa")
        print()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Data management utility for LoRa sensor node')
    parser.add_argument('--db', default='sensor_data.db', help='Database file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Statistics command
    subparsers.add_parser('stats', help='Show buffer statistics')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to file')
    export_parser.add_argument('--hours', type=int, default=24, help='Hours of data to export')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old data')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Delete data older than N days')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show recent unsent data')
    show_parser.add_argument('--limit', type=int, default=10, help='Number of records to show')
    
    # Flush command
    subparsers.add_parser('flush', help='Flush memory buffer to database')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize data buffer
    try:
        buffer_config = BufferConfig()
        buffer_config.db_path = args.db
        data_buffer = DataBuffer(buffer_config)
        
        if args.command == 'stats':
            print_statistics(data_buffer)
        
        elif args.command == 'export':
            export_data(data_buffer, args.hours, args.format)
        
        elif args.command == 'cleanup':
            cleanup_data(data_buffer, args.days)
        
        elif args.command == 'show':
            show_recent_data(data_buffer, args.limit)
        
        elif args.command == 'flush':
            print("Flushing memory buffer to database...")
            data_buffer.flush_to_database()
            print("✅ Flush completed")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    import time
    sys.exit(main())
