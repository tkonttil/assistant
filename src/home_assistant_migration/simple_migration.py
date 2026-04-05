"""
Simple three-step migration process for Home Assistant.

This module provides a simplified interface for the migration workflow:
1. Setup: Download current state and prepare for modifications
2. Compute: Create migration based on user modifications
3. Apply: Upload changes to Home Assistant
"""

from .migration_manager_v2 import MigrationManagerV2
from typing import Dict, Any, Optional


class SimpleMigration:
    """Simplified migration interface with three main steps."""

    def __init__(self):
        """Initialize the simple migration interface."""
        self.manager = MigrationManagerV2()

    def step1_setup(self, transformations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Step 1: Setup migration environment.
        
        - Archives previous migrations
        - Clears input and migrations directories
        - Downloads current state from Home Assistant to input/
        - Transforms input to migration/current
        - Copies migration/current to migration/desired for user modifications
        
        Args:
            transformations: Optional transformations to apply during setup
                           Format: {'areas': {'area_id': {'field': 'value'}}}
        
        Returns:
            Dictionary containing setup results and counts.
        """
        print("=== Step 1: Setup Migration Environment ===")
        
        # Archive previous migrations and clear directories
        self.manager._move_existing_deltas_to_applied()
        
        # Clear input and migrations directories if they exist
        import shutil
        import os
        
        for directory in ["input", "migration/migrations"]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                print(f"   🧹 Cleared {directory} directory")
        
        # Download from Home Assistant to input
        print("   📥 Downloading from Home Assistant...")
        download_result = self.manager.download_to_input()
        
        # Transform from input to migration/current
        print("   🔧 Creating current setup...")
        self.manager.create_current_from_input(transformations)
        
        # Copy migration/current to migration/desired
        print("   📋 Preparing desired setup...")
        self.manager.copy_current_to_desired()
        
        print("✅ Setup complete! Ready for user modifications in migration/desired/")
        
        return {
            "status": "setup_complete",
            "download_counts": download_result,
            "current_dir": "migration/current",
            "desired_dir": "migration/desired",
            "instructions": "Make your modifications in migration/desired/ then run step2_compute()"
        }

    def step2_compute(self, migration_name: str, description: str) -> Dict[str, Any]:
        """
        Step 2: Compute migration and create output.
        
        - Creates migration in migration/migrations based on differences
        - Generates output from input and migration/migrations
        
        Args:
            migration_name: Name of the migration
            description: Description of the migration
        
        Returns:
            Dictionary containing migration and output generation results.
        """
        print(f"=== Step 2: Compute Migration '{migration_name}' ===")
        
        # Create migration data by comparing current and desired
        print("   🔍 Computing changes...")
        migration_data = self.manager.create_migration_data(migration_name, description)
        
        # Apply migrations to create output
        print("   📦 Creating output...")
        output_result = self.manager.apply_migrations_to_create_output()
        
        print(f"✅ Migration computed and output created!")
        print(f"   Migration saved to: migration/migrations/{migration_name}")
        print(f"   Output ready in: {output_result['output_dir']}")
        
        return {
            "status": "migration_computed",
            "migration": migration_data,
            "output": output_result,
            "next_step": "Run step3_apply() to upload changes to Home Assistant"
        }

    def step3_apply(self) -> Dict[str, Any]:
        """
        Step 3: Apply migration by uploading output to Home Assistant.
        
        - Validates files
        - Uploads areas, devices, entities, and automations
        - Restarts Home Assistant
        - Updates current setup
        
        Returns:
            Dictionary containing upload results and validation status.
        """
        print("=== Step 3: Apply Migration to Home Assistant ===")
        
        # Validate and upload
        print("   🔍 Validating files...")
        upload_result = self.manager.validate_and_upload()
        
        print("✅ Migration applied successfully!")
        print(f"   Uploaded: {upload_result['uploaded']}")
        print("   Home Assistant has been restarted with the new configuration")
        
        return {
            "status": "migration_applied",
            "validation": upload_result['validation'],
            "uploaded": upload_result['uploaded'],
            "message": "Migration complete! Home Assistant has been updated."
        }


def simple_migration_workflow():
    """
    Complete simple migration workflow example.
    
    Example usage:
        from home_assistant_migration.simple_migration import simple_migration_workflow
        simple_migration_workflow()
    """
    migration = SimpleMigration()
    
    # Step 1: Setup
    print("Starting migration workflow...")
    setup_result = migration.step1_setup()
    print(f"Setup complete. Current state in {setup_result['current_dir']}")
    print(f"Make your modifications in {setup_result['desired_dir']}")
    
    # User would make modifications here...
    # For example: edit files in migration/desired/
    
    # Step 2: Compute
    input("Press Enter after making your modifications to continue...")
    compute_result = migration.step2_compute("test_migration", "Test migration using simple workflow")
    print(f"Migration computed. Output ready in {compute_result['output']['output_dir']}")
    
    # Step 3: Apply
    input("Press Enter to apply the migration to Home Assistant...")
    apply_result = migration.step3_apply()
    print("Migration complete!")


if __name__ == "__main__":
    simple_migration_workflow()