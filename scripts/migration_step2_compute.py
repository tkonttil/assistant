#!/usr/bin/env python3
"""
Migration Step 2: Compute - Create migration based on modifications.

This script:
1. Compares migration/current/ vs migration/desired/
2. Creates migration in migration/migrations/
3. Generates output files in output/
4. Container remains stopped

Usage: python scripts/migration_step2_compute.py MIGRATION_NAME "MIGRATION_DESCRIPTION"

Example:
    python scripts/migration_step2_compute.py "add_new_area" "Adding living room area"
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from home_assistant_migration.simple_migration import SimpleMigration


def main():
    """Main function for step 2 compute."""
    print("🔍 Migration Step 2: Compute")
    print("=" * 50)
    
    # Check arguments
    if len(sys.argv) < 3:
        print('❌ Usage: python scripts/migration_step2_compute.py MIGRATION_NAME "MIGRATION_DESCRIPTION"')
        print('Example: python scripts/migration_step2_compute.py add_area "Adding living room"')
        sys.exit(1)
    
    migration_name = sys.argv[1]
    description = sys.argv[2]
    
    try:
        migration = SimpleMigration()
        result = migration.step2_compute(migration_name, description)
        
        print(f"\n✅ Migration '{migration_name}' computed successfully!")
        print(f"📋 Description: {description}")
        print(f"📁 Migration saved to: migration/migrations/")
        print(f"📦 Output ready in: {result['output']['output_dir']}")
        print(f"📝 Changes detected: {len(result['migration']['changes'])}")
        print(f"🛑 Docker container is still stopped")
        print("\n📌 Next step: Apply the migration by running:")
        print("   python scripts/migration_step3_apply.py")
        
    except Exception as e:
        print(f"\n❌ Compute failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()