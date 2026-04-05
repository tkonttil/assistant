#!/usr/bin/env python3
"""
Deploy output configuration to Home Assistant Docker container.
This script uploads the transformed output files to the running container.
"""

import sys
import json
import os
sys.path.insert(0, './src')

from home_assistant_migration.ssh_client import SSHClient

def main():
    try:
        # Initialize the SSH client
        print("=== Deploying Output to Home Assistant Docker ===")
        print("Initializing SSH client...")
        client = SSHClient()
        print("✅ SSH client initialized")
        
        # Define file paths
        output_dir = "output"
        config_dir = client.config_dir
        
        # 1. Deploy registry files
        print("\n📁 Deploying registry files...")
        
        registry_files = [
            ("core.area_registry", "Area Registry"),
            ("core.device_registry", "Device Registry"),
            ("core.entity_registry", "Entity Registry")
        ]
        
        for registry_file, description in registry_files:
            local_path = f"{output_dir}/.storage/{registry_file}"
            remote_path = f"{config_dir}/.storage/{registry_file}"
            
            if os.path.exists(local_path):
                print(f"  📄 Deploying {description}...")
                client.deploy_file(local_path, remote_path)
                print(f"  ✅ {description} deployed")
            else:
                print(f"  ⚠️  {description} not found in output")
        
        # 2. Deploy configuration YAML files
        print("\n📄 Deploying configuration files...")
        
        yaml_files = [
            ("configuration.yaml", "Main Configuration"),
            ("automations.yaml", "Automations"),
            ("scripts.yaml", "Scripts"),
            ("scenes.yaml", "Scenes")
        ]
        
        for yaml_file, description in yaml_files:
            local_path = f"{output_dir}/{yaml_file}"
            remote_path = f"{config_dir}/{yaml_file}"
            
            if os.path.exists(local_path):
                print(f"  📄 Deploying {description}...")
                client.deploy_file(local_path, remote_path)
                print(f"  ✅ {description} deployed")
            else:
                print(f"  ⚠️  {description} not found in output")
        
        # 3. Restart Home Assistant to apply changes
        print("\n🔄 Restarting Home Assistant...")
        client.restart_home_assistant()
        print("✅ Home Assistant restarted")
        
        # 4. Verify deployment
        print("\n🔍 Verifying deployment...")
        
        # Check areas
        areas = client.fetch_areas()
        print(f"  📋 Areas: {len(areas)}")
        for area in areas:
            print(f"    - {area['id']}: {area['name']}")
        
        # Check devices
        devices = client.fetch_devices()
        print(f"  🖥️  Devices: {len(devices)}")
        
        # Check entities
        entities = client.fetch_entities()
        print(f"  📡 Entities: {len(entities)}")
        
        print("\n✅ Deployment completed successfully!")
        print("💡 Home Assistant should now reflect the new configuration.")
        print("🕒 Please allow a few minutes for Home Assistant to fully restart.")
        
    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
