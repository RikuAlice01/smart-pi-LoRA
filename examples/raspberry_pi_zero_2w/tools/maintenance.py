#!/usr/bin/env python3
"""
Maintenance tools for LoRa Sensor Node
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class MaintenanceTool:
    """System maintenance tools"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.log_dir = self.base_path / "logs"
        self.backup_dir = self.base_path / "backups"
    
    def run_maintenance(self):
        """Run all maintenance tasks"""
        print("🔧 LoRa Sensor Node Maintenance")
        print("=" * 40)
        
        tasks = [
            ("Clean Log Files", self.clean_logs),
            ("Backup Configuration", self.backup_config),
            ("Update System", self.update_system),
            ("Check Disk Space", self.check_disk_space),
            ("Optimize Performance", self.optimize_performance)
        ]
        
        for task_name, task_func in tasks:
            print(f"\n🔧 {task_name}...")
            try:
                task_func()
                print(f"✅ {task_name}: Completed")
            except Exception as e:
                print(f"❌ {task_name}: Failed - {e}")
    
    def clean_logs(self):
        """Clean old log files"""
        if not self.log_dir.exists():
            print("  No log directory found")
            return
        
        # Remove logs older than 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        removed_count = 0
        total_size = 0
        
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                size = log_file.stat().st_size
                log_file.unlink()
                removed_count += 1
                total_size += size
        
        print(f"  Removed {removed_count} old log files ({total_size} bytes)")
        
        # Compress large current logs
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                compressed_file = log_file.with_suffix('.log.gz')
                subprocess.run(['gzip', '-c', str(log_file)], 
                             stdout=open(compressed_file, 'wb'))
                log_file.unlink()
                print(f"  Compressed {log_file.name}")
    
    def backup_config(self):
        """Backup configuration files"""
        self.backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"config_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # Backup config directory
        config_dir = self.base_path / "config"
        if config_dir.exists():
            shutil.copytree(config_dir, backup_path / "config")
        
        # Backup keyfile
        keyfile = self.base_path / "keyfile.bin"
        if keyfile.exists():
            shutil.copy2(keyfile, backup_path / "keyfile.bin")
        
        # Create archive
        archive_path = self.backup_dir / f"{backup_name}.tar.gz"
        subprocess.run(['tar', '-czf', str(archive_path), '-C', 
                       str(self.backup_dir), backup_name])
        
        # Remove temporary directory
        shutil.rmtree(backup_path)
        
        print(f"  Configuration backed up to {archive_path}")
        
        # Keep only last 10 backups
        backups = sorted(self.backup_dir.glob("config_backup_*.tar.gz"))
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                old_backup.unlink()
                print(f"  Removed old backup: {old_backup.name}")
    
    def update_system(self):
        """Update system packages"""
        print("  Updating package list...")
        subprocess.run(['sudo', 'apt', 'update'], check=True)
        
        print("  Checking for upgrades...")
        result = subprocess.run(['apt', 'list', '--upgradable'], 
                              capture_output=True, text=True)
        
        upgradable = len([line for line in result.stdout.split('\n') 
                         if '/' in line and 'upgradable' in line])
        
        if upgradable > 0:
            print(f"  {upgradable} packages can be upgraded")
            response = input("  Upgrade packages? (y/N): ")
            if response.lower() == 'y':
                subprocess.run(['sudo', 'apt', 'upgrade', '-y'], check=True)
                print("  ✅ Packages upgraded")
        else:
            print("  ✅ System is up to date")
    
    def check_disk_space(self):
        """Check and clean disk space"""
        # Check disk usage
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            usage_line = lines[1].split()
            used_percent = usage_line[4].rstrip('%')
            print(f"  Disk usage: {used_percent}%")
            
            if int(used_percent) > 90:
                print("  ⚠️  High disk usage detected")
                self.clean_disk_space()
        
        # Check log directory size
        if self.log_dir.exists():
            total_size = sum(f.stat().st_size for f in self.log_dir.rglob('*') if f.is_file())
            print(f"  Log directory size: {total_size / 1024 / 1024:.1f} MB")
    
    def clean_disk_space(self):
        """Clean disk space"""
        print("  Cleaning disk space...")
        
        # Clean package cache
        subprocess.run(['sudo', 'apt', 'clean'], check=True)
        subprocess.run(['sudo', 'apt', 'autoremove', '-y'], check=True)
        
        # Clean temporary files
        temp_dirs = ['/tmp', '/var/tmp']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except:
                        pass
        
        print("  ✅ Disk space cleaned")
    
    def optimize_performance(self):
        """Optimize system performance"""
        # Check swap usage
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if 'SwapTotal' in line:
                        swap_total = int(line.split()[1])
                        if swap_total == 0:
                            print("  ⚠️  No swap configured")
                            self.setup_swap()
                        break
        except:
            pass
        
        # Check for memory leaks
        try:
            result = subprocess.run(['ps', 'aux', '--sort=-%mem'], 
                                  capture_output=True, text=True)
            lines = result.stdout.split('\n')[1:6]  # Top 5 processes
            print("  Top memory consumers:")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 11:
                        print(f"    {parts[10]}: {parts[3]}%")
        except:
            pass
    
    def setup_swap(self):
        """Setup swap file"""
        response = input("  Setup 1GB swap file? (y/N): ")
        if response.lower() != 'y':
            return
        
        try:
            # Create swap file
            subprocess.run(['sudo', 'fallocate', '-l', '1G', '/swapfile'], check=True)
            subprocess.run(['sudo', 'chmod', '600', '/swapfile'], check=True)
            subprocess.run(['sudo', 'mkswap', '/swapfile'], check=True)
            subprocess.run(['sudo', 'swapon', '/swapfile'], check=True)
            
            # Make permanent
            with open('/etc/fstab', 'a') as f:
                f.write('/swapfile none swap sw 0 0\n')
            
            print("  ✅ Swap file created and enabled")
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to setup swap: {e}")


if __name__ == "__main__":
    maintenance = MaintenanceTool()
    maintenance.run_maintenance()
