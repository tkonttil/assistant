#!/usr/bin/env python3
"""
Migration Step 3: Apply - Upload changes to Home Assistant.

This script:
1. Validates all files
2. Stops Docker container (if not already stopped)
3. Uploads all changes from output/
4. Starts Docker container with new configuration
5. Home Assistant runs with updated configuration

Usage: python scripts/migration_step3_apply.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from home_assistant_migration.simple_migration import SimpleMigration


def main():
    """Main function for step 3 apply."""
    print("🚀 Migration Step 3: Apply")
    print("=" * 50)
    
    try:
        migration = SimpleMigration()
        result = migration.step3_apply()
        
        print(f"\n✅ Migration applied successfully!")
        print(f"🔍 Validation: {result['validation']['valid']} valid, {result['validation']['invalid']} invalid")
        print(f"📤 Uploaded:")
        print(f"   - Areas: {result['uploaded']['areas']}")
        print(f"   - Devices: {result['uploaded']['devices']}")
        print(f"   - Entities: {result['uploaded']['entities']}")
        print(f"   - Automations: {result['uploaded']['automations']}")
        print(f"▶️  Docker container is running with new configuration")
        print(f"🏠 Home Assistant is live with your changes!")
        print("\n🎉 Migration complete!")
        
    except Exception as e:
        print(f"\n❌ Apply failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()