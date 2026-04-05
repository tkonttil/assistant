#!/usr/bin/env python3
"""
Fix entity areas by ensuring they stick in Home Assistant.

This script modifies both the entity registry and creates proper
customization entries to ensure area assignments persist.

Usage: python scripts/fix_entity_areas.py entity_id area_id
Example: python scripts/fix_entity_areas.py sensor.my_sensor living_room
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/fix_entity_areas.py entity_id area_id")
        print("Example: python scripts/fix_entity_areas.py sensor.my_sensor living_room")
        sys.exit(1)
    
    entity_id = sys.argv[1]
    area_id = sys.argv[2]
    
    print(f"🔧 Fixing area for {entity_id} -> {area_id}")
    
    # Step 1: Update entity registry
    try:
        with open('input/.storage/core.entity_registry', 'r') as f:
            entity_reg = json.load(f)
        
        # Find and update the entity
        updated = False
        for entity in entity_reg['data']['entities']:
            if entity.get('entity_id') == entity_id:
                entity['area_id'] = area_id
                updated = True
                print(f"✅ Updated {entity_id} in entity registry")
                break
        
        if updated:
            # Save to output
            os.makedirs('output/.storage', exist_ok=True)
            with open('output/.storage/core.entity_registry', 'w') as f:
                json.dump(entity_reg, f, indent=2)
        
    except Exception as e:
        print(f"⚠️  Could not update entity registry: {e}")
    
    # Step 2: Create customize.yaml entry
    try:
        customize_file = 'migration/desired/customize.yaml'
        os.makedirs(os.path.dirname(customize_file), exist_ok=True)
        
        # Load existing customizations
        customizations = {}
        if os.path.exists(customize_file):
            with open(customize_file, 'r') as f:
                import yaml
                try:
                    customizations = yaml.safe_load(f) or {}
                except:
                    pass
        
        # Add our customization
        customizations[entity_id] = {
            'area': area_id
        }
        
        # Save back
        import yaml
        with open(customize_file, 'w') as f:
            yaml.dump(customizations, f, default_flow_style=False)
        
        print(f"✅ Added customization for {entity_id} in {customize_file}")
        
    except Exception as e:
        print(f"⚠️  Could not create customization: {e}")
    
    print("\n📌 Next steps:")
    print("1. Run 'make compute' to include these changes")
    print("2. Run 'make apply' to upload to Home Assistant")
    print("3. The customization will ensure the area sticks")

if __name__ == "__main__":
    main()