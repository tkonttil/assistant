"""
Enhanced Migration Manager for Home Assistant configurations.

This version adds an input folder step where files are first downloaded from
Home Assistant to an input folder, then processed to create the current setup.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml

from .ssh_client import SSHClient


class MigrationManagerV2:
    """Enhanced manager for Home Assistant configuration migrations."""

    def __init__(self):
        """Initialize the migration manager."""
        self.client = SSHClient()
        self.input_dir = "input"
        self.current_dir = "migration/current"
        self.desired_dir = "migration/desired"
        self.migrations_dir = "migration/migrations"
        self.output_dir = "output"

    def download_to_input(self) -> Dict[str, Any]:
        """
        Download files from Home Assistant directly to the input folder.
        This is the first step and doesn't require any existing local setup.
        
        Returns:
            Dictionary containing counts of downloaded items.
        """
        print("=== Downloading to Input Folder ===")
        
        # Create input directory
        self._ensure_directory_exists(self.input_dir)
        
        # Copy entire .storage directory
        self.client.copy_storage_directory(f"{self.input_dir}/.storage")
        
        # Download configuration files
        config_files = self.client.fetch_configuration_files()
        
        # Create metadata
        self._create_metadata("input", "Direct download from Home Assistant")
        
        # Count files in .storage directory
        storage_path = f"{self.input_dir}/.storage"
        area_count = 0
        device_count = 0
        entity_count = 0
        automation_count = 0
        
        if os.path.exists(storage_path):
            # Count registry files
            try:
                with open(f"{storage_path}/core.area_registry", 'r') as f:
                    area_data = json.load(f)
                    area_count = len(area_data.get('data', {}).get('areas', []))
            except:
                pass
            
            try:
                with open(f"{storage_path}/core.device_registry", 'r') as f:
                    device_data = json.load(f)
                    device_count = len(device_data.get('data', {}).get('devices', []))
            except:
                pass
            
            try:
                with open(f"{storage_path}/core.entity_registry", 'r') as f:
                    entity_data = json.load(f)
                    entity_count = len(entity_data.get('data', {}).get('entities', []))
            except:
                pass
        
        # Count automations
        automations_path = f"{self.input_dir}/automations.yaml"
        if os.path.exists(automations_path):
            try:
                with open(automations_path, 'r') as f:
                    automation_data = yaml.safe_load(f)
                    if automation_data:
                        automation_count = len(automation_data)
            except:
                pass
        
        return {
            "areas": area_count,
            "devices": device_count,
            "entities": entity_count,
            "automations": automation_count,
            "configuration_files": len([k for k, v in config_files.items() if v])
        }

    def create_current_from_input(self, transformations=None) -> None:
        """
        Create the current setup from the input folder.
        Optionally apply transformations during creation to keep input pristine.
        
        Args:
            transformations: Optional dictionary of transformations to apply
                           Format: {'areas': {'area_id': {'field': 'value'}}}
        """
        print("=== Creating Current Setup from Input ===")
        
        # Remove existing current directory
        if os.path.exists(self.current_dir):
            shutil.rmtree(self.current_dir)
        
        # Create current directory structure
        self._ensure_directory_exists(self.current_dir)
        areas_dir = f"{self.current_dir}/areas"
        devices_dir = f"{self.current_dir}/devices"
        entities_dir = f"{self.current_dir}/entities"
        automations_dir = f"{self.current_dir}/automations"
        
        os.makedirs(areas_dir, exist_ok=True)
        os.makedirs(devices_dir, exist_ok=True)
        os.makedirs(entities_dir, exist_ok=True)
        os.makedirs(automations_dir, exist_ok=True)
        
        # Parse .storage files from input and create individual JSON files
        storage_path = f"{self.input_dir}/.storage"
        
        # Process areas
        if os.path.exists(f"{storage_path}/core.area_registry"):
            with open(f"{storage_path}/core.area_registry", 'r') as f:
                area_registry = json.load(f)
            
            for area in area_registry['data']['areas']:
                area_id = area['id']
                area_file = f"{areas_dir}/{area_id}.json"
                with open(area_file, 'w') as f:
                    json.dump(area, f, indent=2)
        
        # Process devices
        if os.path.exists(f"{storage_path}/core.device_registry"):
            with open(f"{storage_path}/core.device_registry", 'r') as f:
                device_registry = json.load(f)
            
            for device in device_registry['data']['devices']:
                device_id = device['id']
                device_file = f"{devices_dir}/{device_id}.json"
                with open(device_file, 'w') as f:
                    json.dump(device, f, indent=2)
        
        # Process entities
        if os.path.exists(f"{storage_path}/core.entity_registry"):
            with open(f"{storage_path}/core.entity_registry", 'r') as f:
                entity_registry = json.load(f)
            
            for entity in entity_registry['data']['entities']:
                entity_id = entity['id']
                # Create safe filename
                safe_id = entity_id.replace('.', '_')
                entity_file = f"{entities_dir}/{safe_id}.json"
                with open(entity_file, 'w') as f:
                    json.dump(entity, f, indent=2)
        
        # Copy configuration files
        for config_file in ['configuration.yaml', 'automations.yaml', 'scripts.yaml', 'scenes.yaml']:
            src_path = f"{self.input_dir}/{config_file}"
            if os.path.exists(src_path):
                shutil.copy2(src_path, f"{self.current_dir}/{config_file}")
        
        # Apply transformations if provided
        if transformations:
            self._apply_transformations(transformations)
        
        # Update metadata
        self._create_metadata("current", "Created from input folder")
        
        print("✅ Current setup created from input")

    def download_current_setup(self) -> Dict[str, Any]:
        """
        Download the current Home Assistant setup via SSH.
        This is a convenience method that combines download_to_input and create_current_from_input.
        Also handles moving existing deltas to applied_migrations folder.
        
        Returns:
            Dictionary containing counts of downloaded items.
        """
        print("=== Downloading Current Setup ===")
        
        # Move any existing deltas to applied_migrations before downloading
        self._move_existing_deltas_to_applied()
        
        # Download to input first
        result = self.download_to_input()
        
        # Then create current from input
        self.create_current_from_input()
        
        print(f"✅ Download and setup completed")
        return result

    def _move_existing_deltas_to_applied(self) -> None:
        """Move any existing delta directories to applied_migrations folder."""
        import os
        import shutil
        from datetime import datetime
        
        delta_dir = "delta"
        applied_dir = "applied_migrations"
        
        # Create applied_migrations directory if it doesn't exist
        if not os.path.exists(applied_dir):
            os.makedirs(applied_dir)
            print(f"   📁 Created {applied_dir} directory")
        
        # 1. Handle delta directory
        if os.path.exists(delta_dir):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            applied_delta_dir = f"{applied_dir}/delta_{timestamp}"
            
            shutil.move(delta_dir, applied_delta_dir)
            print(f"   ✅ Archived existing delta to {applied_delta_dir}")
        
        # 2. Archive existing migration directories
        migrations_dir = "migration/migrations"
        if os.path.exists(migrations_dir):
            migration_dirs = []
            for item in os.listdir(migrations_dir):
                item_path = os.path.join(migrations_dir, item)
                if os.path.isdir(item_path):
                    migration_dirs.append(item_path)
            
            if migration_dirs:
                # Sort by timestamp (newest first)
                migration_dirs.sort(reverse=True)
                
                # Archive all existing migrations
                for migration_dir in migration_dirs:
                    migration_name = os.path.basename(migration_dir)
                    archive_path = f"{applied_dir}/migration_{migration_name}"
                    
                    shutil.copytree(migration_dir, archive_path)
                    print(f"   ✅ Archived migration {migration_name} to {archive_path}")
                
                # Clear the migrations directory for new cycle
                shutil.rmtree(migrations_dir)
                os.makedirs(migrations_dir, exist_ok=True)
                print(f"   ✅ Cleared migrations directory for new cycle")
        
        print(f"   ✅ Migration archiving completed - {len(os.listdir(applied_dir)) if os.path.exists(applied_dir) else 0} items archived")

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

    def generate_consolidated_output(self) -> Dict[str, Any]:
        """
        Generate consolidated output by reading from input and applying transformations.
        This ensures output contains the final transformed state ready for upload.
        
        Returns:
            Dictionary containing output generation results.
        """
        print("=== Generating Consolidated Output from Input with Transformations ===")
        
        # Ensure output directory exists and is clean
        if os.path.exists(self.output_dir):
            import shutil
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Rebuild .storage directory from current (which has transformations applied)
        # This ensures output contains the transformed data, not raw input
        storage_output_dir = f"{self.output_dir}/.storage"
        os.makedirs(storage_output_dir, exist_ok=True)
        
        # Rebuild area registry from current (transformed) data
        # Read version from input to preserve compatibility
        import json
        with open(f"{self.input_dir}/.storage/core.area_registry", 'r') as f:
            input_area_registry = json.load(f)
        area_registry = {
            "version": input_area_registry["version"],
            "minor_version": input_area_registry["minor_version"],
            "key": "core.area_registry",
            "data": {"areas": []}
        }
        
        areas_dir = f"{self.current_dir}/areas"
        if os.path.exists(areas_dir):
            import json
            for area_file in os.listdir(areas_dir):
                if area_file.endswith('.json'):
                    with open(f"{areas_dir}/{area_file}", 'r') as f:
                        area = json.load(f)
                    area_registry['data']['areas'].append(area)
            
            with open(f"{storage_output_dir}/core.area_registry", 'w') as f:
                json.dump(area_registry, f, indent=2)
            print(f"   ✅ Created transformed area registry with {len(area_registry['data']['areas'])} areas")
        
        # Rebuild device registry from current data
        # Read version from input to preserve compatibility
        with open(f"{self.input_dir}/.storage/core.device_registry", 'r') as f:
            input_device_registry = json.load(f)
        device_registry = {
            "version": input_device_registry["version"],
            "minor_version": input_device_registry["minor_version"],
            "key": "core.device_registry",
            "data": {"devices": []}
        }
        
        devices_dir = f"{self.current_dir}/devices"
        if os.path.exists(devices_dir):
            for device_file in os.listdir(devices_dir):
                if device_file.endswith('.json'):
                    with open(f"{devices_dir}/{device_file}", 'r') as f:
                        device = json.load(f)
                    device_registry['data']['devices'].append(device)
            
            with open(f"{storage_output_dir}/core.device_registry", 'w') as f:
                json.dump(device_registry, f, indent=2)
            print(f"   ✅ Created device registry with {len(device_registry['data']['devices'])} devices")
        
        # Rebuild entity registry from current data
        # Read version from input to preserve compatibility
        with open(f"{self.input_dir}/.storage/core.entity_registry", 'r') as f:
            input_entity_registry = json.load(f)
        entity_registry = {
            "version": input_entity_registry["version"],
            "minor_version": input_entity_registry["minor_version"],
            "key": "core.entity_registry",
            "data": {"entities": []}
        }
        
        entities_dir = f"{self.current_dir}/entities"
        if os.path.exists(entities_dir):
            for entity_file in os.listdir(entities_dir):
                if entity_file.endswith('.json'):
                    with open(f"{entities_dir}/{entity_file}", 'r') as f:
                        entity = json.load(f)
                    entity_registry['data']['entities'].append(entity)
            
            with open(f"{storage_output_dir}/core.entity_registry", 'w') as f:
                json.dump(entity_registry, f, indent=2)
            print(f"   ✅ Created entity registry with {len(entity_registry['data']['entities'])} entities")
        
        # Copy YAML configuration files from current (may have been modified)
        yaml_files = ['configuration.yaml', 'automations.yaml', 'scripts.yaml', 'scenes.yaml']
        copied_yaml = 0
        for yaml_file in yaml_files:
            src_path = f"{self.current_dir}/{yaml_file}"
            if os.path.exists(src_path):
                import shutil
                shutil.copy2(src_path, f"{self.output_dir}/{yaml_file}")
                copied_yaml += 1
                print(f"   ✅ Copied {yaml_file}")
        
        # Copy other .storage files from input (unchanged data)
        input_storage_src = f"{self.input_dir}/.storage"
        if os.path.exists(input_storage_src):
            for storage_file in os.listdir(input_storage_src):
                if (storage_file not in ['core.area_registry', 'core.device_registry', 'core.entity_registry'] and
                    os.path.isfile(f"{input_storage_src}/{storage_file}")):
                    src_path = f"{input_storage_src}/{storage_file}"
                    dest_path = f"{storage_output_dir}/{storage_file}"
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, dest_path)
            print(f"   ✅ Copied other .storage files from input")
        
        # Copy individual JSON files from desired to output (after applying migrations)
        self._copy_desired_files_to_output()
        
        # Count all output files
        output_files = []
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                output_files.append(os.path.join(root, file))
        
        # Count storage files
        storage_files = []
        if os.path.exists(storage_output_dir):
            for root, dirs, files in os.walk(storage_output_dir):
                for file in files:
                    storage_files.append(file)
        
        result = {
            "output_dir": self.output_dir,
            "total_files": len(output_files),
            "storage_files": len(storage_files),
            "yaml_files": copied_yaml,
            "file_list": output_files
        }
        
        print(f"✅ Consolidated output generated: {len(output_files)} files")
        print(f"   Output contains transformed data from current setup")
        return result

    def apply_migrations_to_create_output(self) -> Dict[str, Any]:
        """
        Apply migration deltas to input files to create output.
        This preserves all unchanged files from input and only applies specific changes.
        
        Returns:
            Dictionary containing output generation results.
        """
        print("=== Applying Migrations to Create Output ===")
        
        # Ensure output directory exists and is clean
        if os.path.exists(self.output_dir):
            import shutil
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create .storage directory in output
        storage_output_dir = f"{self.output_dir}/.storage"
        os.makedirs(storage_output_dir, exist_ok=True)
        
        # First, copy ALL files from input to output unchanged
        input_storage_src = f"{self.input_dir}/.storage"
        if os.path.exists(input_storage_src):
            # Import shutil here since we're in a method
            import shutil
            # Copy all .storage files from input to output
            for storage_file in os.listdir(input_storage_src):
                src_path = f"{input_storage_src}/{storage_file}"
                # Skip the nested .storage directory - it's a bug
                if storage_file == ".storage":
                    continue
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, f"{storage_output_dir}/{storage_file}", dirs_exist_ok=True)
                elif os.path.isfile(src_path):
                    shutil.copy2(src_path, f"{storage_output_dir}/{storage_file}")
            print(f"   ✅ Copied all .storage files from input")
        
        # Copy YAML configuration files from input
        yaml_files = ['configuration.yaml', 'automations.yaml', 'scripts.yaml', 'scenes.yaml']
        copied_yaml = 0
        for yaml_file in yaml_files:
            src_path = f"{self.input_dir}/{yaml_file}"
            if os.path.exists(src_path):
                shutil.copy2(src_path, f"{self.output_dir}/{yaml_file}")
                copied_yaml += 1
                print(f"   ✅ Copied {yaml_file} from input")
        
        # For apply_migrations_to_create_output, we want the output to reflect the desired state
        # Since desired already contains all the changes, we can simply copy from desired
        # This is more reliable than trying to apply deltas to input files
        
        # Copy individual JSON files from desired to output
        self._copy_desired_files_to_output()
        
        # Also update the registry files to match the desired state
        self._update_registries_from_desired(storage_output_dir)
        
        # Count all output files
        output_files = []
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                output_files.append(os.path.join(root, file))
        
        # Count storage files
        storage_files = []
        if os.path.exists(storage_output_dir):
            for root, dirs, files in os.walk(storage_output_dir):
                for file in files:
                    storage_files.append(file)
        
        result = {
            "output_dir": self.output_dir,
            "total_files": len(output_files),
            "storage_files": len(storage_files),
            "yaml_files": copied_yaml,
            "file_list": output_files
        }
        
        print(f"✅ Output created by applying migrations to input: {len(output_files)} files")
        print(f"   Output preserves unchanged files and applies migration changes")
        return result

    def _apply_change_to_output_files(self, change: Dict[str, Any], storage_dir: str) -> None:
        """Apply a single change to the output registry files."""
        import json
        
        change_type = change['type']
        item_type = change['item_type']
        item_id = change['item_id']
        data = change.get('data', {})
        
        # Determine which registry file to modify
        if item_type == 'area':
            registry_file = f"{storage_dir}/core.area_registry"
            registry_key = 'areas'
        elif item_type == 'device':
            registry_file = f"{storage_dir}/core.device_registry"
            registry_key = 'devices'
        elif item_type == 'entity':
            registry_file = f"{storage_dir}/core.entity_registry"
            registry_key = 'entities'
        else:
            return  # Skip other types for now
        
        if not os.path.exists(registry_file):
            return
        
        # Load the registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        
        if change_type == 'add':
            # Add the new item to the registry
            registry['data'][registry_key].append(data)
            print(f"   ✅ Added {item_type} {item_id}")
        elif change_type == 'remove':
            # Remove the item from the registry
            registry['data'][registry_key] = [
                item for item in registry['data'][registry_key] 
                if item.get('id') != item_id
            ]
            print(f"   ✅ Removed {item_type} {item_id}")
        elif change_type == 'modify':
            # Modify the existing item
            for item in registry['data'][registry_key]:
                if item.get('id') == item_id:
                    item.update(data)
                    print(f"   ✅ Modified {item_type} {item_id}")
                    break
        
        # Save the modified registry
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
        
        # Also update the individual JSON file in output directory
        if change_type in ['add', 'modify']:
            individual_dir = f"{self.output_dir}/{item_type}s"
            if not os.path.exists(individual_dir):
                os.makedirs(individual_dir, exist_ok=True)
            
            individual_file = f"{individual_dir}/{item_id}.json"
            with open(individual_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"   ✅ Updated individual {item_type} file {item_id}.json")

    def generate_migration_delta(self) -> Dict[str, Any]:
        """
        Generate migration delta containing only the files that have changed.
        This creates a minimal output with just the differences between current and desired.
        
        Returns:
            Dictionary containing delta generation results.
        """
        print("=== Generating Migration Delta ===")
        
        # Ensure delta directory exists and is clean
        delta_dir = "delta"
        if os.path.exists(delta_dir):
            import shutil
            shutil.rmtree(delta_dir)
        os.makedirs(delta_dir, exist_ok=True)
        
        # Get changes from comparison
        changes = self._compare_setups()
        print(f"   Found {len(changes)} changes to apply")
        
        # Create delta structure
        delta_areas_dir = f"{delta_dir}/areas"
        delta_devices_dir = f"{delta_dir}/devices"
        delta_entities_dir = f"{delta_dir}/entities"
        delta_automations_dir = f"{delta_dir}/automations"
        
        # Apply each change to create delta files
        area_changes = 0
        device_changes = 0
        entity_changes = 0
        automation_changes = 0
        
        for change in changes:
            change_type = change['type']
            item_type = change['item_type']
            item_id = change['item_id']
            data = change.get('data')  # Use .get() to handle missing 'data' key
            
            if change_type == 'add' and data is not None:
                if item_type == 'area':
                    os.makedirs(delta_areas_dir, exist_ok=True)
                    with open(f"{delta_areas_dir}/{item_id}.json", 'w') as f:
                        import json
                        json.dump(data, f, indent=2)
                    area_changes += 1
                    print(f"   ✅ Added area: {item_id}")
                
                elif item_type == 'device':
                    os.makedirs(delta_devices_dir, exist_ok=True)
                    with open(f"{delta_devices_dir}/{item_id}.json", 'w') as f:
                        import json
                        json.dump(data, f, indent=2)
                    device_changes += 1
                    print(f"   ✅ Added device: {item_id}")
                
                elif item_type == 'entity':
                    os.makedirs(delta_entities_dir, exist_ok=True)
                    safe_id = item_id.replace('.', '_')
                    with open(f"{delta_entities_dir}/{safe_id}.json", 'w') as f:
                        import json
                        json.dump(data, f, indent=2)
                    entity_changes += 1
                    print(f"   ✅ Added entity: {item_id}")
                
                elif item_type == 'automation':
                    os.makedirs(delta_automations_dir, exist_ok=True)
                    with open(f"{delta_automations_dir}/{item_id}.yaml", 'w') as f:
                        import yaml
                        yaml.dump(data, f)
                    automation_changes += 1
                    print(f"   ✅ Added automation: {item_id}")
            
            elif change_type == 'modify':
                if item_type == 'area':
                    os.makedirs(delta_areas_dir, exist_ok=True)
                    with open(f"{delta_areas_dir}/{item_id}.json", 'w') as f:
                        import json
                        json.dump(data, f, indent=2)
                    area_changes += 1
                    print(f"   ✅ Modified area: {item_id}")
                
                # Similar logic for other item types...
            
            elif change_type == 'delete':
                # For deletions, we could create delete markers
                print(f"   ⚠️  Delete change detected: {item_type} {item_id}")
        
        # Count all delta files
        delta_files = []
        for root, dirs, files in os.walk(delta_dir):
            for file in files:
                delta_files.append(os.path.join(root, file))
        
        result = {
            "delta_dir": delta_dir,
            "total_changes": len(changes),
            "area_changes": area_changes,
            "device_changes": device_changes,
            "entity_changes": entity_changes,
            "automation_changes": automation_changes,
            "delta_files": delta_files,
            "changes": changes
        }
        
        print(f"✅ Migration delta generated: {len(delta_files)} files")
        print(f"   Changes: {area_changes} areas, {device_changes} devices, {entity_changes} entities, {automation_changes} automations")
        return result

    def _copy_current_files_to_output(self) -> None:
        """Copy individual JSON files from current to output as reference."""
        # Create subdirectories in output
        areas_dir = f"{self.output_dir}/areas"
        devices_dir = f"{self.output_dir}/devices"
        entities_dir = f"{self.output_dir}/entities"
        
        os.makedirs(areas_dir, exist_ok=True)
        os.makedirs(devices_dir, exist_ok=True)
        os.makedirs(entities_dir, exist_ok=True)
        
        # Copy area files
        current_areas_dir = f"{self.current_dir}/areas"
        if os.path.exists(current_areas_dir):
            import shutil
            for area_file in os.listdir(current_areas_dir):
                if area_file.endswith('.json'):
                    shutil.copy2(f"{current_areas_dir}/{area_file}", f"{areas_dir}/{area_file}")
            print(f"   ✅ Copied transformed area files to output/areas/")
        
        # Copy device files
        current_devices_dir = f"{self.current_dir}/devices"
        if os.path.exists(current_devices_dir):
            for device_file in os.listdir(current_devices_dir):
                if device_file.endswith('.json'):
                    shutil.copy2(f"{current_devices_dir}/{device_file}", f"{devices_dir}/{device_file}")
            print(f"   ✅ Copied device files to output/devices/")
        
        # Copy entity files
        current_entities_dir = f"{self.current_dir}/entities"
        if os.path.exists(current_entities_dir):
            for entity_file in os.listdir(current_entities_dir):
                if entity_file.endswith('.json'):
                    shutil.copy2(f"{current_entities_dir}/{entity_file}", f"{entities_dir}/{entity_file}")
            print(f"   ✅ Copied entity files to output/entities/")

    def _copy_desired_files_to_output(self) -> None:
        """Copy individual JSON files from desired to output as reference."""
        # Create subdirectories in output
        areas_dir = f"{self.output_dir}/areas"
        devices_dir = f"{self.output_dir}/devices"
        entities_dir = f"{self.output_dir}/entities"
        
        os.makedirs(areas_dir, exist_ok=True)
        os.makedirs(devices_dir, exist_ok=True)
        os.makedirs(entities_dir, exist_ok=True)
        
        # Copy area files from desired (which has the migrations applied)
        desired_areas_dir = f"{self.desired_dir}/areas"
        if os.path.exists(desired_areas_dir):
            import shutil
            for area_file in os.listdir(desired_areas_dir):
                if area_file.endswith('.json'):
                    shutil.copy2(f"{desired_areas_dir}/{area_file}", f"{areas_dir}/{area_file}")
            print(f"   ✅ Copied desired area files to output/areas/")
        
        # Copy device files from desired
        desired_devices_dir = f"{self.desired_dir}/devices"
        if os.path.exists(desired_devices_dir):
            for device_file in os.listdir(desired_devices_dir):
                if device_file.endswith('.json'):
                    shutil.copy2(f"{desired_devices_dir}/{device_file}", f"{devices_dir}/{device_file}")
            print(f"   ✅ Copied desired device files to output/devices/")
        
        # Copy entity files from desired
        desired_entities_dir = f"{self.desired_dir}/entities"
        if os.path.exists(desired_entities_dir):
            for entity_file in os.listdir(desired_entities_dir):
                if entity_file.endswith('.json'):
                    shutil.copy2(f"{desired_entities_dir}/{entity_file}", f"{entities_dir}/{entity_file}")
            print(f"   ✅ Copied desired entity files to output/entities/")

    def _update_registries_from_desired(self, storage_dir: str) -> None:
        """Update registry files in output to match the desired state while preserving all input data."""
        import json
        import shutil
        
        print("   🔄 Updating registries from desired state...")
        
        # Update area registry
        desired_areas_dir = f"{self.desired_dir}/areas"
        if os.path.exists(desired_areas_dir):
            # Load input registry to preserve ALL data
            with open(f"{self.input_dir}/.storage/core.area_registry", 'r') as f:
                input_area_registry = json.load(f)
            
            # Create new registry preserving all input data structure
            area_registry = {
                "version": input_area_registry["version"],
                "minor_version": input_area_registry["minor_version"],
                "key": "core.area_registry",
                "data": {}
            }
            
            # Copy ALL keys from input data to preserve structure
            for key, value in input_area_registry['data'].items():
                if key == 'areas':
                    # For areas, use the areas from desired
                    area_registry['data'][key] = []
                    for area_file in os.listdir(desired_areas_dir):
                        if area_file.endswith('.json'):
                            with open(f"{desired_areas_dir}/{area_file}", 'r') as f:
                                area = json.load(f)
                            area_registry['data'][key].append(area)
                else:
                    # Preserve all other keys exactly as they are
                    area_registry['data'][key] = value
            
            # Save updated registry
            with open(f"{storage_dir}/core.area_registry", 'w') as f:
                json.dump(area_registry, f, indent=2)
            print(f"   ✅ Updated area registry with {len(area_registry['data']['areas'])} areas")
        
        # Update device registry
        desired_devices_dir = f"{self.desired_dir}/devices"
        if os.path.exists(desired_devices_dir):
            # Load input registry to preserve ALL data
            with open(f"{self.input_dir}/.storage/core.device_registry", 'r') as f:
                input_device_registry = json.load(f)
            
            # Create new registry preserving all input data structure
            device_registry = {
                "version": input_device_registry["version"],
                "minor_version": input_device_registry["minor_version"],
                "key": "core.device_registry",
                "data": {}
            }
            
            # Copy ALL keys from input data to preserve structure
            for key, value in input_device_registry['data'].items():
                if key == 'devices':
                    # For devices, use the devices from desired
                    device_registry['data'][key] = []
                    for device_file in os.listdir(desired_devices_dir):
                        if device_file.endswith('.json'):
                            with open(f"{desired_devices_dir}/{device_file}", 'r') as f:
                                device = json.load(f)
                            device_registry['data'][key].append(device)
                else:
                    # Preserve all other keys exactly as they are
                    device_registry['data'][key] = value
            
            # Save updated registry
            with open(f"{storage_dir}/core.device_registry", 'w') as f:
                json.dump(device_registry, f, indent=2)
            print(f"   ✅ Updated device registry with {len(device_registry['data']['devices'])} devices")
        
        # Update entity registry
        desired_entities_dir = f"{self.desired_dir}/entities"
        if os.path.exists(desired_entities_dir):
            # Load input registry to preserve ALL data
            with open(f"{self.input_dir}/.storage/core.entity_registry", 'r') as f:
                input_entity_registry = json.load(f)
            
            # Create new registry preserving all input data structure
            entity_registry = {
                "version": input_entity_registry["version"],
                "minor_version": input_entity_registry["minor_version"],
                "key": "core.entity_registry",
                "data": {}
            }
            
            # Copy ALL keys from input data to preserve structure
            for key, value in input_entity_registry['data'].items():
                if key == 'entities':
                    # For entities, use the entities from desired
                    entity_registry['data'][key] = []
                    for entity_file in os.listdir(desired_entities_dir):
                        if entity_file.endswith('.json'):
                            with open(f"{desired_entities_dir}/{entity_file}", 'r') as f:
                                entity = json.load(f)
                            entity_registry['data'][key].append(entity)
                else:
                    # Preserve all other keys exactly as they are
                    entity_registry['data'][key] = value
            
            # Save updated registry
            with open(f"{storage_dir}/core.entity_registry", 'w') as f:
                json.dump(entity_registry, f, indent=2)
            print(f"   ✅ Updated entity registry with {len(entity_registry['data']['entities'])} entities")

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

    def _store_areas(self, areas: List[Dict[str, Any]], folder_type: str) -> None:
        """Store areas in the specified folder."""
        if folder_type == "input":
            dir_path = f"{self.input_dir}/areas"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/areas"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/areas"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        self._ensure_directory_exists(dir_path)
        
        for area in areas:
            file_path = f"{dir_path}/{area['id']}.json"
            with open(file_path, 'w') as f:
                json.dump(area, f, indent=2)

    def _store_devices(self, devices: List[Dict[str, Any]], folder_type: str) -> None:
        """Store devices in the specified folder."""
        if folder_type == "input":
            dir_path = f"{self.input_dir}/devices"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/devices"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/devices"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        self._ensure_directory_exists(dir_path)
        
        for device in devices:
            file_path = f"{dir_path}/{device['id']}.json"
            with open(file_path, 'w') as f:
                json.dump(device, f, indent=2)

    def _store_entities(self, entities: List[Dict[str, Any]], folder_type: str) -> None:
        """Store entities in the specified folder."""
        if folder_type == "input":
            dir_path = f"{self.input_dir}/entities"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/entities"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/entities"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        self._ensure_directory_exists(dir_path)
        
        for entity in entities:
            file_path = f"{dir_path}/{entity['entity_id']}.json"
            with open(file_path, 'w') as f:
                json.dump(entity, f, indent=2)

    def _store_automations(self, automations: List[Dict[str, Any]], folder_type: str) -> None:
        """Store automations in the specified folder."""
        if folder_type == "input":
            dir_path = f"{self.input_dir}/automations"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/automations"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/automations"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        self._ensure_directory_exists(dir_path)
        
        for i, automation in enumerate(automations):
            automation_id = automation.get('id', f'automation_{i+1}')
            file_path = f"{dir_path}/{automation_id}.yaml"
            
            with open(file_path, 'w') as f:
                yaml.dump(automation, f)

    def _create_metadata(self, folder_type: str, description: str = "Fetched via SSH") -> None:
        """Create metadata file for a setup."""
        if folder_type == "input":
            dir_path = self.input_dir
        elif folder_type == "current":
            dir_path = self.current_dir
        elif folder_type == "desired":
            dir_path = self.desired_dir
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Home Assistant VM',
            'method': 'SSH/Docker',
            'description': description
        }
        
        with open(f"{dir_path}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

    def _compare_setups(self) -> List[Dict[str, Any]]:
        """Compare current and desired setups to identify changes."""
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

    def _load_areas(self, folder_type: str) -> List[Dict[str, Any]]:
        """Load areas from the specified folder."""
        areas = []
        if folder_type == "input":
            dir_path = f"{self.input_dir}/areas"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/areas"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/areas"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.json'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        areas.append(json.load(f))
        
        return areas

    def _load_devices(self, folder_type: str) -> List[Dict[str, Any]]:
        """Load devices from the specified folder."""
        devices = []
        if folder_type == "input":
            dir_path = f"{self.input_dir}/devices"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/devices"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/devices"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.json'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        devices.append(json.load(f))
        
        return devices

    def _load_entities(self, folder_type: str) -> List[Dict[str, Any]]:
        """Load entities from the specified folder."""
        entities = []
        if folder_type == "input":
            dir_path = f"{self.input_dir}/entities"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/entities"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/entities"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.json'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        entities.append(json.load(f))
        
        return entities

    def _load_automations(self, folder_type: str) -> List[Dict[str, Any]]:
        """Load automations from the specified folder."""
        automations = []
        if folder_type == "input":
            dir_path = f"{self.input_dir}/automations"
        elif folder_type == "current":
            dir_path = f"{self.current_dir}/automations"
        elif folder_type == "desired":
            dir_path = f"{self.desired_dir}/automations"
        else:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.yaml') or file.endswith('.yml'):
                    with open(f"{dir_path}/{file}", 'r') as f:
                        automations.append(yaml.safe_load(f))
        
        return automations

    def _compare_items(self, current_items: List[Dict[str, Any]], desired_items: List[Dict[str, Any]], item_type: str) -> List[Dict[str, Any]]:
        """Compare items of a specific type between current and desired setups."""
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

    def _apply_transformations(self, transformations: Dict[str, Any]) -> None:
        """
        Apply transformations to files in the current directory.
        
        Args:
            transformations: Dictionary of transformations to apply
                           Format: {'areas': {'area_id': {'field': 'value'}}}
        """
        print("   Applying transformations...")
        
        # Apply area transformations
        if 'areas' in transformations:
            for area_id, changes in transformations['areas'].items():
                area_file = f"{self.current_dir}/areas/{area_id}.json"
                if os.path.exists(area_file):
                    with open(area_file, 'r') as f:
                        area = json.load(f)
                    
                    for field, value in changes.items():
                        area[field] = value
                    
                    with open(area_file, 'w') as f:
                        json.dump(area, f, indent=2)
                    
                    print(f"   ✅ Transformed area {area_id}: {changes}")
        
        # Apply device transformations
        if 'devices' in transformations:
            for device_id, changes in transformations['devices'].items():
                device_file = f"{self.current_dir}/devices/{device_id}.json"
                if os.path.exists(device_file):
                    with open(device_file, 'r') as f:
                        device = json.load(f)
                    
                    for field, value in changes.items():
                        device[field] = value
                    
                    with open(device_file, 'w') as f:
                        json.dump(device, f, indent=2)
                    
                    print(f"   ✅ Transformed device {device_id}: {changes}")
        
        # Apply entity transformations
        if 'entities' in transformations:
            for entity_id, changes in transformations['entities'].items():
                entity_file = f"{self.current_dir}/entities/{entity_id}.json"
                if os.path.exists(entity_file):
                    with open(entity_file, 'r') as f:
                        entity = json.load(f)
                    
                    for field, value in changes.items():
                        entity[field] = value
                    
                    with open(entity_file, 'w') as f:
                        json.dump(entity, f, indent=2)
                    
                    print(f"   ✅ Transformed entity {entity_id}: {changes}")

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
                        # Use custom loader that handles Home Assistant's special tags
                        with open(file_path, 'r') as f:
                            content = f.read()
                            # Check for Home Assistant special tags
                            if '!include' in content or '!include_dir' in content or '!secret' in content:
                                # These are valid Home Assistant YAML files with special tags
                                # We can't parse them with standard YAML, but they're valid for HA
                                valid += 1
                            else:
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
        areas_dir = f"{self.current_dir}/areas"
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
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Write to output directory
        local_path = f"{self.output_dir}/core.area_registry"
        
        with open(local_path, 'w') as f:
            json.dump(area_registry, f, indent=2)
        
        # Deploy
        remote_path = f"{self.client.config_dir}/.storage/core.area_registry"
        self.client.deploy_file(local_path, remote_path)
        
        return len(areas)

    def _upload_devices(self) -> int:
        """Upload devices to Home Assistant."""
        devices_dir = f"{self.current_dir}/devices"
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
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Write to output directory
        local_path = f"{self.output_dir}/core.device_registry"
        
        with open(local_path, 'w') as f:
            json.dump(device_registry, f, indent=2)
        
        # Deploy
        remote_path = f"{self.client.config_dir}/.storage/core.device_registry"
        self.client.deploy_file(local_path, remote_path)
        
        return len(devices)

    def _upload_entities(self) -> int:
        """Upload entities to Home Assistant."""
        entities_dir = f"{self.current_dir}/entities"
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
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Write to output directory
        local_path = f"{self.output_dir}/core.entity_registry"
        
        with open(local_path, 'w') as f:
            json.dump(entity_registry, f, indent=2)
        
        # Deploy
        remote_path = f"{self.client.config_dir}/.storage/core.entity_registry"
        self.client.deploy_file(local_path, remote_path)
        
        return len(entities)

    def _upload_automations(self) -> int:
        """Upload automations to Home Assistant."""
        automations_dir = f"{self.current_dir}/automations"
        if not os.path.exists(automations_dir):
            return 0
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Count automations
        count = 0
        for file in os.listdir(automations_dir):
            if file.endswith('.yaml') or file.endswith('.yml'):
                # Copy to output directory
                local_path = f"{automations_dir}/{file}"
                output_path = f"{self.output_dir}/{file}"
                shutil.copy2(local_path, output_path)
                
                # Deploy from output directory
                remote_path = f"{self.client.config_dir}/automations/{file}"
                self.client.deploy_file(output_path, remote_path)
                count += 1
        
        return count
