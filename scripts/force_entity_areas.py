#!/usr/bin/env python3
"""
Force entity areas to stick in Home Assistant using multiple methods.

This script uses a comprehensive approach:
1. Direct registry modification
2. YAML customization
3. Configuration.yaml integration
4. Proper file permissions

Usage: python scripts/force_entity_areas.py
"""

import os
import json
import yaml
from pathlib import Path

def main():
    print("🔧 Force Entity Areas to Stick")
    print("=" * 50)
    
    # Step 1: Create comprehensive customize.yaml
    customize_content = {
        # Sun entities
        'sensor.sun_next_rising': {'area': 'bedroom'},
        'sensor.sun_next_setting': {'area': 'bedroom'},
        'sensor.sun_next_dawn': {'area': 'bedroom'},
        'sensor.sun_next_dusk': {'area': 'bedroom'},
        'sensor.sun_next_midnight': {'area': 'bedroom'},
        'sensor.sun_next_noon': {'area': 'bedroom'},
        'binary_sensor.sun_solar_rising': {'area': 'bedroom'},
        'sensor.sun_solar_elevation': {'area': 'bedroom'},
        'sensor.sun_solar_azimuth': {'area': 'bedroom'},
        
        # Add your other entities here
        # 'sensor.my_sensor': {'area': 'living_room'},
    }
    
    # Save customize.yaml
    os.makedirs('migration/desired', exist_ok=True)
    with open('migration/desired/customize.yaml', 'w') as f:
        yaml.dump(customize_content, f, default_flow_style=False)
    print("✅ Created comprehensive customize.yaml")
    
    # Step 2: Update entity registry directly
    try:
        with open('input/.storage/core.entity_registry', 'r') as f:
            entity_reg = json.load(f)
        
        modified = 0
        for entity in entity_reg['data']['entities']:
            entity_id = entity.get('entity_id', '')
            if entity_id in customize_content:
                entity['area_id'] = customize_content[entity_id]['area']
                modified += 1
        
        if modified > 0:
            os.makedirs('output/.storage', exist_ok=True)
            with open('output/.storage/core.entity_registry', 'w') as f:
                json.dump(entity_reg, f, indent=2)
            print(f"✅ Updated {modified} entities in registry")
    except Exception as e:
        print(f"⚠️  Registry update warning: {e}")
    
    # Step 3: Create configuration.yaml entry
    config_content = """# Entity customizations
homeassistant:
  customize: !include customize.yaml
  customize_domain:
    sun:
      area: bedroom
"""
    
    with open('migration/desired/configuration_addition.yaml', 'w') as f:
        f.write(config_content)
    print("✅ Created configuration addition for Home Assistant")
    
    # Step 4: Instructions
    print("\n📋 Implementation Instructions:")
    print("1. Run: make compute")
    print("2. Run: make apply")
    print("3. Manually add this to your configuration.yaml:")
    print("   homeassistant:")
    print("     customize: !include customize.yaml")
    print("4. Restart Home Assistant")
    print("\n💡 For Sun entities specifically, you may need to:")
    print("- Use the Home Assistant UI to set areas")
    print("- Accept that some virtual entities don't support areas")
    print("- Focus on real devices (lights, switches, sensors)")

if __name__ == "__main__":
    main()