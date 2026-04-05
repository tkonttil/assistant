"""
Migration script generation for transforming current setup to desired setup.
"""

import os
import toml
from typing import Dict, Any, List
from datetime import datetime
from .models import Migration


class MigrationGenerator:
    """Generate migration scripts to transform current setup to desired setup."""

    def __init__(self, base_path: str = "migration"):
        """Initialize the migration generator."""
        self.base_path = base_path
        self.migrations_path = os.path.join(base_path, "migrations")
        
        # Ensure the migrations directory exists
        os.makedirs(self.migrations_path, exist_ok=True)

    def generate_migration(self, migration_id: str, description: str,
                           changes: List[Dict[str, Any]]) -> str:
        """Generate a migration script."""
        migration = Migration(
            id=migration_id,
            description=description,
            changes=changes,
            dependencies=[],
            rollback=None,
        )
        
        # Create the migration file
        migration_file = os.path.join(self.migrations_path, f"{migration_id}.toml")
        with open(migration_file, "w") as f:
            toml.dump({
                "id": migration.id,
                "description": migration.description,
                "changes": migration.changes,
                "dependencies": migration.dependencies,
                "rollback": migration.rollback,
            }, f)
        
        return migration_file

    def compare_setups(self, current_setup: Dict[str, Any],
                      desired_setup: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare current and desired setups to identify changes."""
        changes = []
        
        # Compare areas
        current_areas = current_setup.get("areas", {})
        desired_areas = desired_setup.get("areas", {})
        
        current_area_ids = set(current_areas.keys())
        desired_area_ids = set(desired_areas.keys())
        
        # Added areas
        for area_id in desired_area_ids - current_area_ids:
            changes.append({
                "entity_type": "area",
                "entity_id": area_id,
                "change_type": "add",
                "details": {
                    "area_id": area_id,
                    "name": desired_areas[area_id]["name"],
                    "devices": desired_areas[area_id]["devices"],
                },
            })
        
        # Removed areas
        for area_id in current_area_ids - desired_area_ids:
            changes.append({
                "entity_type": "area",
                "entity_id": area_id,
                "change_type": "remove",
                "details": {
                    "area_id": area_id,
                },
            })
        
        # Compare devices
        current_devices = current_setup.get("devices", {})
        desired_devices = desired_setup.get("devices", {})
        
        current_device_ids = set(current_devices.keys())
        desired_device_ids = set(desired_devices.keys())
        
        # Added devices
        for device_id in desired_device_ids - current_device_ids:
            changes.append({
                "entity_type": "device",
                "entity_id": device_id,
                "change_type": "add",
                "details": {
                    "device_id": device_id,
                    "name": desired_devices[device_id]["name"],
                    "area": desired_devices[device_id]["area"],
                },
            })
        
        # Removed devices
        for device_id in current_device_ids - desired_device_ids:
            changes.append({
                "entity_type": "device",
                "entity_id": device_id,
                "change_type": "remove",
                "details": {
                    "device_id": device_id,
                },
            })
        
        # Compare automations
        current_automations = current_setup.get("automations", {})
        desired_automations = desired_setup.get("automations", {})
        
        current_automation_ids = set(current_automations.keys())
        desired_automation_ids = set(desired_automations.keys())
        
        # Added automations
        for automation_id in desired_automation_ids - current_automation_ids:
            changes.append({
                "entity_type": "automation",
                "entity_id": automation_id,
                "change_type": "add",
                "details": {
                    "automation_id": automation_id,
                    "name": desired_automations[automation_id]["name"],
                },
            })
        
        # Removed automations
        for automation_id in current_automation_ids - desired_automation_ids:
            changes.append({
                "entity_type": "automation",
                "entity_id": automation_id,
                "change_type": "remove",
                "details": {
                    "automation_id": automation_id,
                },
            })
        
        return changes

    def apply_migration(self, migration_id: str) -> None:
        """Apply a migration script."""
        migration_file = os.path.join(self.migrations_path, f"{migration_id}.toml")
        if not os.path.exists(migration_file):
            raise FileNotFoundError(f"Migration {migration_id} not found")
        
        with open(migration_file, "r") as f:
            migration_data = toml.load(f)
        
        # Here you would implement the logic to apply the migration
        # For now, we'll just print the changes
        print(f"Applying migration {migration_id}: {migration_data['description']}")
        for change in migration_data["changes"]:
            print(f"  - {change['change_type']} {change['entity_type']}.{change['entity_id']}")

    def list_migrations(self) -> List[str]:
        """List all available migrations."""
        if not os.path.exists(self.migrations_path):
            return []
        
        return [f.replace(".toml", "") for f in os.listdir(self.migrations_path) if f.endswith(".toml")]

    def generate_migration_id(self, description: str) -> str:
        """Generate a unique migration ID based on timestamp and description."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # Create a simple slug from the description
        slug = description.lower().replace(" ", "_")
        return f"{timestamp}_{slug}"