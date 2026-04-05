#!/usr/bin/env python3
"""
Fetch current Home Assistant setup via SSH and store it in the migration/current folder.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
sys.path.insert(0, './src')

from home_assistant_migration.ssh_client import SSHClient

def ensure_directory_exists(directory: str):
    """Ensure a directory exists, create if it doesn't."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def fetch_and_store_areas(client: SSHClient):
    """Fetch areas and store them in the current directory."""
    print("Fetching areas...")
    areas = client.fetch_areas()
    
    # Store in migration/current/areas/
    ensure_directory_exists("migration/current/areas")
    
    for area in areas:
        area_id = area['id']
        area_file = f"migration/current/areas/{area_id}.json"
        
        with open(area_file, 'w') as f:
            json.dump(area, f, indent=2)
    
    print(f"✅ Stored {len(areas)} areas")

def fetch_and_store_devices(client: SSHClient):
    """Fetch devices and store them in the current directory."""
    print("Fetching devices...")
    devices = client.fetch_devices()
    
    # Store in migration/current/devices/
    ensure_directory_exists("migration/current/devices")
    
    for device in devices:
        device_id = device['id']
        device_file = f"migration/current/devices/{device_id}.json"
        
        with open(device_file, 'w') as f:
            json.dump(device, f, indent=2)
    
    print(f"✅ Stored {len(devices)} devices")

def fetch_and_store_entities(client: SSHClient):
    """Fetch entities and store them in the current directory."""
    print("Fetching entities...")
    entities = client.fetch_entities()
    
    # Store in migration/current/entities/
    ensure_directory_exists("migration/current/entities")
    
    for entity in entities:
        entity_id = entity['entity_id']
        entity_file = f"migration/current/entities/{entity_id}.json"
        
        with open(entity_file, 'w') as f:
            json.dump(entity, f, indent=2)
    
    print(f"✅ Stored {len(entities)} entities")

def fetch_and_store_automations(client: SSHClient):
    """Fetch automations and store them in the current directory."""
    print("Fetching automations...")
    automations = client.fetch_automations()
    
    # Store in migration/current/automations/
    ensure_directory_exists("migration/current/automations")
    
    for i, automation in enumerate(automations):
        # Use automation ID or generate a filename
        automation_id = automation.get('id', f'automation_{i+1}')
        automation_file = f"migration/current/automations/{automation_id}.yaml"
        
        # Write YAML file
        import yaml
        with open(automation_file, 'w') as f:
            yaml.dump(automation, f)
    
    print(f"✅ Stored {len(automations)} automations")

def create_migration_metadata():
    """Create a metadata file for this migration fetch."""
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'source': 'Home Assistant VM',
        'method': 'SSH/Docker',
        'description': 'Current setup fetched via SSH'
    }
    
    with open("migration/current/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("✅ Created migration metadata")

def main():
    try:
        print("=== Fetching Current Home Assistant Setup via SSH ===\n")
        
        # Initialize SSH client
        print("Initializing SSH client...")
        client = SSHClient()
        print("✅ SSH client initialized\n")
        
        # Create migration/current directory structure
        ensure_directory_exists("migration/current")
        
        # Fetch and store all configurations
        fetch_and_store_areas(client)
        fetch_and_store_devices(client)
        fetch_and_store_entities(client)
        fetch_and_store_automations(client)
        
        # Create metadata
        create_migration_metadata()
        
        print("\n✅ All configurations fetched and stored successfully!")
        print("\nDirectory structure:")
        print("  migration/current/")
        print("    ├── areas/            # Area configurations")
        print("    ├── devices/          # Device configurations")
        print("    ├── entities/         # Entity configurations")
        print("    ├── automations/      # Automation configurations")
        print("    └── metadata.json     # Migration metadata")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
