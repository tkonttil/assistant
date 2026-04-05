#!/usr/bin/env python3
"""
Migration Step 1: Setup - Download current state and prepare for modifications.

This script:
1. Archives previous migrations
2. Clears input and migrations directories
3. Stops Docker container
4. Downloads current state from Home Assistant to input/
5. Creates migration/current/
6. Copies to migration/desired/
7. Leaves Docker container stopped for safe modifications

Usage: python scripts/migration_step1_setup.py [--transformations TRANSFORMATIONS_FILE]
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from home_assistant_migration.simple_migration import SimpleMigration


def main():
    """Main function for step 1 setup."""
    print("🚀 Migration Step 1: Setup")
    print("=" * 50)
    
    # Parse arguments
    transformations = None
    if len(sys.argv) > 1 and sys.argv[1] == "--transformations":
        if len(sys.argv) > 2:
            transformations_file = sys.argv[2]
            try:
                with open(transformations_file, 'r') as f:
                    transformations = json.load(f)
                print(f"📋 Loaded transformations from {transformations_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not load transformations: {e}")
        else:
            print("⚠️  Warning: --transformations requires a file path")
    
    # Initialize and run setup
    try:
        migration = SimpleMigration()
        result = migration.step1_setup(transformations)
        
        print("\n✅ Setup Complete!")
        print(f"📁 Current state: {result['current_dir']}")
        print(f"📝 Modify files in: {result['desired_dir']}")
        print(f"🛑 Docker container is stopped - safe to modify files")
        print("\n📌 Next step: Make your modifications, then run:")
        print("   python scripts/migration_step2_compute.py")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()