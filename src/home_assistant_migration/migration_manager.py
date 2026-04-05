"""
Migration manager for Home Assistant configurations.

This module provides a high-level interface for managing the migration process,
including downloading the current setup, creating desired configurations,
generating migration scripts, and deploying changes.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml

from .ssh_client import SSHClient


class MigrationManager:
    """Manager for Home Assistant configuration migrations."""

    def __init__(self):
        """Initialize the migration manager."""
        self.client = SSHClient()
        self.current_dir = "migration/current"
        self.desired_dir = "migration/desired"
        self.migrations_dir = "migration/migrations"
        
    def download_current_setup(self) -> Dict[str, Any]:
        """
        Download the current Home Assistant setup via SSH.
        
        Returns:
            Dictionary containing counts of downloaded items.
        """
        print("=== Downloading Current Setup ===")
        
        # Create directories
        self._ensure_directory_exists(self.current_dir)
        
        # Download areas
        areas = self.client.fetch_areas()
        self._store_areas(areas, "current")
        
        # Download devices
        devices = self.client.fetch_devices()
        self._store_devices(devices, "current")
        
        # Download entities
        entities = self.client.fetch_entities()
        self._store_entities(entities, "current")
        
        # Download automations
        automations = self.client.fetch_automations()
        self._store_automations(automations, "current")
        
        # Create metadata
        self._create_metadata("current")
        
        return {
            "areas": len(areas),
            "devices": len(devices),
            "entities": len(entities),
            "automations": len(automations)
        }

    def copy_current_to_desired(self) -> None:
        """
        Copy the current setup to the desired directory.
        This is useful for starting a new migration from the current state.
        """
        print("=== Copying Current to Desired ===")
        
        # Remove existing desired directory
        if os.path.exists(self.desired_dir):
            shutil.rmtree(self.desired_dir)
        
        # Copy current to desired
        shutil.copytree(self.current_dir, self.desired_dir)
        
        # Update metadata
        self._create_metadata("desired", "Copied from current setup")
        
        print("✅ Current setup copied to desired")

    def create_migration_data(self, migration_name: str, description: str) -> Dict[str, Any]:
        """
        Create migration data by comparing current and desired setups.
        
        Args:
            migration_name: Name of the migration
            description: Description of the migration
            
        Returns:
            Dictionary containing migration details.
        """
        print(f"=== Creating Migration: {migration_name} ===")
        
        # Ensure migrations directory exists
        self._ensure_directory_exists(self.migrations_dir)
        
        # Create migration directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_dir = f"{self.migrations_dir}/{timestamp}_{migration_name}"
        self._ensure_directory_exists(migration_dir)
        
        # Compare and generate migration data
        migration_data = {
            "name": migration_name,
            "timestamp": timestamp,
            "description": description,
            "changes": self._compare_setups()
        }
        
        # Save migration data
        migration_file = f"{migration_dir}/migration.json"
        with open(migration_file, 'w') as f:
            json.dump(migration_data, f, indent=2)
        
        print(f"✅ Migration data created: {migration_file}")
        
        return migration_data

    def run_migration(self, migration_name: str) -> None:
        """
        Run a migration to create new versions of data to be uploaded.
        
        Args:
            migration_name: Name of the migration to run
        """
        print(f"=== Running Migration: {migration_name} ===")
        
        # Find the migration
        migration_dir = self._find_migration_dir(migration_name)
        if not migration_dir:
            raise ValueError(f"Migration '{migration_name}' not found")
        
        # Load migration data
        with open(f"{migration_dir}/migration.json", 'r') as f:
            migration_data = json.load(f)
        
        # Apply changes
        for change in migration_data['changes']:
            self._apply_change(change)
        
        # Update current setup
        self.copy_desired_to_current()
        
        print(f"✅ Migration '{migration_name}' applied successfully")

    def validate_and_upload(self) -> Dict[str, Any]:
        """
        Validate YAML and JSON files and upload them to Home Assistant.
        
        Returns:
            Dictionary containing validation and upload results.
        """
        print("=== Validating and Uploading ===")
        
        # Validate files
        validation_results = self._validate_files()
        print(f"✅ Validation completed: {validation_results['valid']} valid, {validation_results['invalid']} invalid")
        
        if validation_results['invalid'] > 0:
            print("⚠️  Warning: Some files are invalid. Upload aborted.")
            return validation_results
        
        # Upload areas
        areas_uploaded = self._upload_areas()
        
        # Upload devices
        devices_uploaded = self._upload_devices()
        
        # Upload entities
        entities_uploaded = self._upload_entities()
        
        # Upload automations
        automations_uploaded = self._upload_automations()
        
        # Restart Home Assistant
        self.client.restart_home_assistant()
        
        # Update current setup
        self.download_current_setup()
        
        return {
            "validation": validation_results,
            "uploaded": {
                "areas": areas_uploaded,
                "devices": devices_uploaded,
                "entities": entities_uploaded,
                "automations": automations_uploaded
            }
        }

    def copy_desired_to_current(self) -> None:
        """Copy desired setup to current (after successful migration)."""
        print("=== Updating Current Setup ===")
        
        # Remove existing current directory
        if os.path.exists(self.current_dir):
            shutil.rmtree(self.current_dir)
        
        # Copy desired to current
        shutil.copytree(self.desired_dir, self.current_dir)
        
        # Update metadata
        self._create_metadata("current", "Updated from desired after migration")
        
        print("✅ Current setup updated from desired")

    def _ensure_directory_exists(self, directory: str) -> None:
        """Ensure a directory exists, create if it doesn't."""
        Path(directory).mkdir(parents=True, exist_ok=True)

    def _store_areas(self, areas: List[Dict[str, Any]], setup_type: str) -> None:
        """Store areas in the specified setup directory."""
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/areas"
        self._ensure_directory_exists(dir_path)
        
        for area in areas:
            file_path = f"{dir_path}/{area['id']}.json"
            with open(file_path, 'w') as f:
                json.dump(area, f, indent=2)

    def _store_devices(self, devices: List[Dict[str, Any]], setup_type: str) -> None:
        """Store devices in the specified setup directory."""
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/devices"
        self._ensure_directory_exists(dir_path)
        
        for device in devices:
            file_path = f"{dir_path}/{device['id']}.json"
            with open(file_path, 'w') as f:
                json.dump(device, f, indent=2)

    def _store_entities(self, entities: List[Dict[str, Any]], setup_type: str) -> None:
        """Store entities in the specified setup directory."""
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/entities"
        self._ensure_directory_exists(dir_path)
        
        for entity in entities:
            file_path = f"{dir_path}/{entity['entity_id']}.json"
            with open(file_path, 'w') as f:
                json.dump(entity, f, indent=2)

    def _store_automations(self, automations: List[Dict[str, Any]], setup_type: str) -> None:
        """Store automations in the specified setup directory."""
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/automations"
        self._ensure_directory_exists(dir_path)
        
        for i, automation in enumerate(automations):
            automation_id = automation.get('id', f'automation_{i+1}')
            file_path = f"{dir_path}/{automation_id}.yaml"
            
            with open(file_path, 'w') as f:
                yaml.dump(automation, f)

    def _create_metadata(self, setup_type: str, description: str = "Fetched via SSH") -> None:
        """Create metadata file for a setup."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Home Assistant VM',
            'method': 'SSH/Docker',
            'description': description
        }
        
        dir_path = self.current_dir if setup_type == 'current' else self.desired_dir
        with open(f"{dir_path}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

    def _compare_setups(self) -> List[Dict[str, Any]]:
        """
        Compare current and desired setups to identify changes.
        
        Returns:
            List of change dictionaries.
        """
        changes = []
        
        # Compare areas
        current_areas = self._load_areas("current")
        desired_areas = self._load_areas("desired")
        changes.extend(self._compare_items(current_areas, desired_areas, "area"))
        
        # Compare devices
        current_devices = self._load_devices("current")
        desired_devices = self._load_devices("desired")
        changes.extend(self._compare_items(current_devices, desired_devices, "device"))
        
        # Compare entities
        current_entities = self._load_entities("current")
        desired_entities = self._load_entities("desired")
        changes.extend(self._compare_items(current_entities, desired_entities, "entity"))
        
        # Compare automations
        current_automations = self._load_automations("current")
        desired_automations = self._load_automations("desired")
        changes.extend(self._compare_items(current_automations, desired_automations, "automation"))
        
        return changes

    def _load_areas(self, setup_type: str) -> List[Dict[str, Any]]:
        """Load areas from the specified setup directory."""
        areas = []
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/areas"
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.json'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        areas.append(json.load(f))
        
        return areas

    def _load_devices(self, setup_type: str) -> List[Dict[str, Any]]:
        """Load devices from the specified setup directory."""
        devices = []
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/devices"
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.json'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        devices.append(json.load(f))
        
        return devices

    def _load_entities(self, setup_type: str) -> List[Dict[str, Any]]:
        """Load entities from the specified setup directory."""
        entities = []
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/entities"
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.json'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        entities.append(json.load(f))
        
        return entities

    def _load_automations(self, setup_type: str) -> List[Dict[str, Any]]:
        """Load automations from the specified setup directory."""
        automations = []
        dir_path = f"{self.current_dir if setup_type == 'current' else self.desired_dir}/automations"
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.yaml') or file.endswith('.yml'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        automations.append(yaml.safe_load(f))
        
        return automations

    def _compare_items(self, current_items: List[Dict[str, Any]], desired_items: List[Dict[str, Any]], item_type: str) -> List[Dict[str, Any]]:
        """
        Compare items of a specific type between current and desired setups.
        
        Args:
            current_items: List of current items
            desired_items: List of desired items
            item_type: Type of items (area, device, entity, automation)
            
        Returns:
            List of change dictionaries.
        """
        changes = []
        
        # Create dictionaries for easy lookup
        current_dict = {self._get_item_id(item, item_type): item for item in current_items}
        desired_dict = {self._get_item_id(item, item_type): item for item in desired_items}
        
        # Find added, removed, and modified items
        all_ids = set(current_dict.keys()) | set(desired_dict.keys())
        
        for item_id in all_ids:
            current_item = current_dict.get(item_id)
            desired_item = desired_dict.get(item_id)
            
            if current_item is None:
                # Item added
                changes.append({
                    'type': 'add',
                    'item_type': item_type,
                    'item_id': item_id,
                    'data': desired_item
                })
            elif desired_item is None:
                # Item removed
                changes.append({
                    'type': 'remove',
                    'item_type': item_type,
                    'item_id': item_id
                })
            elif current_item != desired_item:
                # Item modified
                changes.append({
                    'type': 'modify',
                    'item_type': item_type,
                    'item_id': item_id,
                    'old_data': current_item,
                    'new_data': desired_item
                })
        
        return changes

    def _get_item_id(self, item: Dict[str, Any], item_type: str) -> str:
        """Get the ID of an item based on its type."""
        if item_type == 'area':
            return item.get('id')
        elif item_type == 'device':
            return item.get('id')
        elif item_type == 'entity':
            return item.get('entity_id')
        elif item_type == 'automation':
            return item.get('id', str(hash(json.dumps(item, sort_keys=True))))
        else:
            return str(id(item))

    def _apply_change(self, change: Dict[str, Any]) -> None:
        """Apply a single change to the desired setup."""
        item_type = change['item_type']
        item_id = change['item_id']
        
        if change['type'] == 'add':
            # For add, the item is already in desired, so no action needed
            pass
        elif change['type'] == 'remove':
            # Remove the item from desired
            dir_path = f"{self.desired_dir}/{item_type}s"
            file_pattern = f"{dir_path}/{item_id}.*"
            
            for file in os.listdir(dir_path):
                if file.startswith(item_id):
                    os.remove(f"{dir_path}/{file}")
        elif change['type'] == 'modify':
            # Update the item in desired (already done, just ensure it's there)
            pass

    def _find_migration_dir(self, migration_name: str) -> Optional[str]:
        """Find the directory of a migration by name."""
        if not os.path.exists(self.migrations_dir):
            return None
        
        for item in os.listdir(self.migrations_dir):
            if migration_name in item:
                full_path = f"{self.migrations_dir}/{item}"
                if os.path.isdir(full_path):
                    return full_path
        
        return None

    def _validate_files(self) -> Dict[str, Any]:
        """Validate all JSON and YAML files in the desired directory."""
        valid = 0
        invalid = 0
        errors = []
        
        # Validate JSON files
        for root, dirs, files in os.walk(self.desired_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                if file.endswith('.json'):
                    try:
                        with open(file_path, 'r') as f:
                            json.load(f)
                        valid += 1
                    except Exception as e:
                        invalid += 1
                        errors.append(f"Invalid JSON: {file_path} - {str(e)}")
                
                elif file.endswith('.yaml') or file.endswith('.yml'):
                    try:
                        with open(file_path, 'r') as f:
                            yaml.safe_load(f)
                        valid += 1
                    except Exception as e:
                        invalid += 1
                        errors.append(f"Invalid YAML: {file_path} - {str(e)}")
        
        return {
            'valid': valid,
            'invalid': invalid,
            'errors': errors
        }

    def _upload_areas(self) -> int:
        """Upload areas to Home Assistant."""
        areas_dir = f"{self.desired_dir}/areas"
        if not os.path.exists(areas_dir):
            return 0
        
        # Load all areas
        areas = []
        for file in os.listdir(areas_dir):
            if file.endswith('.json'):
                with open(f"{areas_dir}/{file}", 'r') as f:
                    areas.append(json.load(f))
        
        # Create area registry
        area_registry = {
            "version": 1,
            "minor_version": 9,
            "key": "core.area_registry",
            "data": {
                "areas": areas
            }
        }
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Write to output directory
        local_path = f"{output_dir}/core.area_registry"
        
        with open(local_path, 'w') as f:
            json.dump(area_registry, f, indent=2)
        
        # Deploy
        remote_path = f"{self.client.config_dir}/.storage/core.area_registry"
        self.client.deploy_file(local_path, remote_path)
        
        return len(areas)

    def _upload_devices(self) -> int:
        """Upload devices to Home Assistant."""
        devices_dir = f"{self.desired_dir}/devices"
        if not os.path.exists(devices_dir):
            return 0
        
        # Load all devices
        devices = []
        for file in os.listdir(devices_dir):
            if file.endswith('.json'):
                with open(f"{devices_dir}/{file}", 'r') as f:
                    devices.append(json.load(f))
        
        # Create device registry
        device_registry = {
            "version": 1,
            "minor_version": 9,
            "key": "core.device_registry",
            "data": {
                "devices": devices
            }
        }
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Write to output directory
        local_path = f"{output_dir}/core.device_registry"
        
        with open(local_path, 'w') as f:
            json.dump(device_registry, f, indent=2)
        
        # Deploy
        remote_path = f"{self.client.config_dir}/.storage/core.device_registry"
        self.client.deploy_file(local_path, remote_path)
        
        return len(devices)

    def _upload_entities(self) -> int:
        """Upload entities to Home Assistant."""
        entities_dir = f"{self.desired_dir}/entities"
        if not os.path.exists(entities_dir):
            return 0
        
        # Load all entities
        entities = []
        for file in os.listdir(entities_dir):
            if file.endswith('.json'):
                with open(f"{entities_dir}/{file}", 'r') as f:
                    entities.append(json.load(f))
        
        # Create entity registry
        entity_registry = {
            "version": 1,
            "minor_version": 9,
            "key": "core.entity_registry",
            "data": {
                "entities": entities
            }
        }
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Write to output directory
        local_path = f"{output_dir}/core.entity_registry"
        
        with open(local_path, 'w') as f:
            json.dump(entity_registry, f, indent=2)
        
        # Deploy
        remote_path = f"{self.client.config_dir}/.storage/core.entity_registry"
        self.client.deploy_file(local_path, remote_path)
        
        return len(entities)

    def _upload_automations(self) -> int:
        """Upload automations to Home Assistant."""
        automations_dir = f"{self.desired_dir}/automations"
        if not os.path.exists(automations_dir):
            return 0
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Count automations
        count = 0
        for file in os.listdir(automations_dir):
            if file.endswith('.yaml') or file.endswith('.yml'):
                # Copy to output directory
                local_path = f"{automations_dir}/{file}"
                output_path = f"{output_dir}/{file}"
                shutil.copy2(local_path, output_path)
                
                # Deploy from output directory
                remote_path = f"{self.client.config_dir}/automations/{file}"
                self.client.deploy_file(output_path, remote_path)
                count += 1
        
        return count
