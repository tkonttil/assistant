#!/usr/bin/env python3
"""
Fix area assignments for REAL devices (not virtual entities like Sun).

This script works with actual devices that support area assignments:
- Lights, switches, sensors
- Media players, cameras
- Climate devices, covers
- Most integrations except virtual/calculated ones

Usage: python scripts/real_device_area_fix.py device_id area_id
Example: python scripts/real_device_area_fix.py sensor.living_room_motion living_room
"""

import sys
import os
import json
import yaml
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/real_device_area_fix.py device_id area_id")
        print("Example: python scripts/real_device_area_fix.py sensor.living_room_motion living_room")
        print("\nNote: This works for REAL devices only (not Sun, Weather, etc.)")
        sys.exit(1)
    
    device_id = sys.argv[1]
    area_id = sys.argv[2]
    
    print(f"🔧 Fixing area for REAL device: {device_id} -> {area_id}")
    
    # Step 1: Update device registry
    try:
        with open('input/.storage/core.device_registry', 'r') as f:
            device_reg = json.load(f)
        
        # Find and update the device
        device_found = False
        for device in device_reg['data']['devices']:
            if device.get('id') == device_id:
                device['area_id'] = area_id
                device_found = True
                print(f"✅ Updated device {device_id} in device registry")
                break
        
        if not device_found:
            print(f"⚠️  Device {device_id} not found in registry")
        else:
            # Save updated registry
            os.makedirs('output/.storage', exist_ok=True)
            with open('output/.storage/core.device_registry', 'w') as f:
                json.dump(device_reg, f, indent=2)
    
    except Exception as e:
        print(f"⚠️  Could not update device registry: {e}")
    
    # Step 2: Update entity registry for all entities from this device
    try:
        with open('input/.storage/core.entity_registry', 'r') as f:
            entity_reg = json.load(f)
        
        entity_updated = 0
        for entity in entity_reg['data']['entities']:
            # Check if this entity belongs to our device
            if entity.get('device_id') == device_id:
                entity['area_id'] = area_id
                entity_updated += 1
        
        if entity_updated > 0:
            with open('output/.storage/core.entity_registry', 'w') as f:
                json.dump(entity_reg, f, indent=2)
            print(f"✅ Updated {entity_updated} entities from device {device_id}")
        else:
            print(f"ℹ️  No entities found for device {device_id}")
    
    except Exception as e:
        print(f"⚠️  Could not update entity registry: {e}")
    
    # Step 3: Create customize.yaml backup
    try:
        customize_content = {
            f'sensor.{device_id.replace("_", " ").replace(" ", "_").lower()}': {'area': area_id}
        }
        
        os.makedirs('migration/desired', exist_ok=True)
        customize_file = 'migration/desired/customize.yaml'
        
        # Load existing or create new
        customizations = {}
        if os.path.exists(customize_file):
            with open(customize_file, 'r') as f:
                customizations = yaml.safe_load(f) or {}
        
        # Merge
        customizations.update(customize_content)
        
        with open(customize_file, 'w') as f:
            yaml.dump(customizations, f, default_flow_style=False)
        
        print(f"✅ Added backup customization to customize.yaml")
    
    except Exception as e:
        print(f"⚠️  Could not update customize.yaml: {e}")
    
    print("\n📋 Next steps:")
    print("1. Run: make compute")
    print("2. Run: make apply")
    print("3. Check Home Assistant UI - area should now appear!")
    print("\n💡 For virtual entities (Sun, Weather, etc.):")
    print("- Use Home Assistant UI customization")
    print("- Accept that some don't support areas")
    print("- Focus on real devices that actually benefit from areas")

if __name__ == "__main__":
    main()