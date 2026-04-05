"""
SSH client for accessing Home Assistant VM.

This module provides functionality to connect to the Home Assistant VM via SSH,
execute commands, and transfer files. For local development with Docker, it uses
direct Docker access to emulate SSH operations.
"""

import os
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv


class SSHClient:
    """Client for interacting with Home Assistant VM via SSH or Docker."""

    def __init__(self):
        """Initialize the SSH client."""
        load_dotenv()
        
        # SSH configuration
        self.ssh_host = os.getenv("HASS_SSH_HOST", "localhost")
        self.ssh_port = int(os.getenv("HASS_SSH_PORT", "22"))
        self.ssh_user = os.getenv("HASS_SSH_USER", "root")
        self.ssh_password = os.getenv("HASS_SSH_PASSWORD")
        self.ssh_key_path = os.getenv("HASS_SSH_KEY_PATH")
        self.config_dir = os.getenv("HASS_CONFIG_DIR", "/config")
        
        # Docker configuration (for local development)
        self.use_docker = os.getenv("HASS_USE_DOCKER", "true").lower() == "true"
        self.docker_container = os.getenv("HASS_DOCKER_CONTAINER", "homeassistant")
        
        # Validate configuration
        if self.use_docker:
            self._validate_docker_setup()
        else:
            self._validate_ssh_setup()

    def _validate_docker_setup(self):
        """Validate Docker setup."""
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("Docker is not available or not running")
            
            # Check if the container is running
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", self.docker_container],
                capture_output=True,
                text=True
            )
            if result.stdout.strip() != "true":
                raise RuntimeError(f"Container {self.docker_container} is not running")
                
        except Exception as e:
            raise RuntimeError(f"Docker validation failed: {e}")

    def _validate_ssh_setup(self):
        """Validate SSH setup."""
        if not self.ssh_key_path and not self.ssh_password:
            raise ValueError("Either SSH key path or password must be provided")

    def execute_command(self, command: str) -> str:
        """Execute a command on the Home Assistant VM."""
        if self.use_docker:
            return self._execute_docker_command(command)
        else:
            return self._execute_ssh_command(command)

    def _execute_docker_command(self, command: str) -> str:
        """Execute a command in the Docker container."""
        try:
            # Use docker exec to run the command
            full_command = ["docker", "exec", self.docker_container, "bash", "-c", command]
            result = subprocess.run(full_command, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker command failed: {e.stderr}") from e

    def _execute_ssh_command(self, command: str) -> str:
        """Execute a command via SSH."""
        import paramiko
        
        try:
            # Initialize SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the VM
            if self.ssh_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_user,
                    pkey=private_key
                )
            else:
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_user,
                    password=self.ssh_password
                )
            
            # Execute the command
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode()
            error = stderr.read().decode()
            
            # Close the connection
            ssh.close()
            
            if error:
                raise RuntimeError(f"SSH command failed: {error}")
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"SSH execution failed: {e}") from e

    def fetch_file(self, remote_path: str, local_path: str):
        """Fetch a file from the Home Assistant VM."""
        if self.use_docker:
            self._fetch_docker_file(remote_path, local_path)
        else:
            self._fetch_ssh_file(remote_path, local_path)

    def _fetch_docker_file(self, remote_path: str, local_path: str):
        """Fetch a file from the Docker container."""
        try:
            # Create local directory if it doesn't exist
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Use docker cp to copy the file
            full_remote_path = f"{self.docker_container}:{remote_path}"
            result = subprocess.run(["docker", "cp", full_remote_path, local_path], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                # Check if the error is due to missing file
                error_msg = result.stdout + (result.stderr if result.stderr else "")
                if "Could not find the file" in error_msg:
                    raise FileNotFoundError(f"File not found: {remote_path}")
                raise RuntimeError(f"Docker file fetch failed: {error_msg}")
            
        except subprocess.CalledProcessError as e:
            # Check if the error is due to missing file
            error_msg = str(e.stderr) if e.stderr else str(e)
            if "Could not find the file" in error_msg:
                raise FileNotFoundError(f"File not found: {remote_path}")
            raise RuntimeError(f"Docker file fetch failed: {error_msg}") from e

    def _fetch_ssh_file(self, remote_path: str, local_path: str):
        """Fetch a file via SSH."""
        import paramiko
        
        try:
            # Initialize SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the VM
            if self.ssh_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_user,
                    pkey=private_key
                )
            else:
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_user,
                    password=self.ssh_password
                )
            
            # Use SCP to fetch the file
            scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
            scp.get(remote_path, local_path)
            scp.close()
            ssh.close()
            
        except Exception as e:
            raise RuntimeError(f"SSH file fetch failed: {e}") from e

    def deploy_file(self, local_path: str, remote_path: str):
        """Deploy a file to the Home Assistant VM."""
        if self.use_docker:
            self._deploy_docker_file(local_path, remote_path)
        else:
            self._deploy_ssh_file(local_path, remote_path)

    def _deploy_docker_file(self, local_path: str, remote_path: str):
        """Deploy a file to the Docker container."""
        try:
            # Use docker cp to copy the file
            full_remote_path = f"{self.docker_container}:{remote_path}"
            subprocess.run(["docker", "cp", local_path, full_remote_path], check=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker file deploy failed: {e.stderr}") from e

    def _deploy_ssh_file(self, local_path: str, remote_path: str):
        """Deploy a file via SSH."""
        import paramiko
        
        try:
            # Initialize SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the VM
            if self.ssh_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_user,
                    pkey=private_key
                )
            else:
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_user,
                    password=self.ssh_password
                )
            
            # Use SCP to deploy the file
            scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
            scp.put(local_path, remote_path)
            scp.close()
            ssh.close()
            
        except Exception as e:
            raise RuntimeError(f"SSH file deploy failed: {e}") from e

    def restart_home_assistant(self):
        """Restart Home Assistant to apply changes."""
        if self.use_docker:
            self._restart_docker_home_assistant()
        else:
            self._restart_ssh_home_assistant()

    def _restart_docker_home_assistant(self):
        """Restart Home Assistant in the Docker container."""
        try:
            # Restart the container
            subprocess.run(["docker", "restart", self.docker_container], check=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Docker restart failed: {e.stderr}") from e

    def _restart_ssh_home_assistant(self):
        """Restart Home Assistant via SSH."""
        try:
            # Execute the restart command
            self.execute_command("ha core restart")
            
        except Exception as e:
            raise RuntimeError(f"Home Assistant restart failed: {e}") from e

    def fetch_areas(self) -> List[Dict[str, Any]]:
        """Fetch areas from Home Assistant."""
        try:
            # Fetch the area registry file
            remote_path = f"{self.config_dir}/.storage/core.area_registry"
            local_path = ".storage/core.area_registry"
            self.fetch_file(remote_path, local_path)
            
            # Read and parse the file
            with open(local_path, 'r') as f:
                area_registry = json.load(f)
            
            return area_registry['data']['areas']
            
        except FileNotFoundError:
            # No areas defined, return empty list
            print("Warning: No area registry found - returning empty list")
            return []
        except Exception as e:
            raise RuntimeError(f"Failed to fetch areas: {e}") from e

    def fetch_devices(self) -> List[Dict[str, Any]]:
        """Fetch devices from Home Assistant."""
        try:
            # Fetch the device registry file
            remote_path = f"{self.config_dir}/.storage/core.device_registry"
            local_path = ".storage/core.device_registry"
            self.fetch_file(remote_path, local_path)
            
            # Read and parse the file
            with open(local_path, 'r') as f:
                device_registry = json.load(f)
            
            return device_registry['data']['devices']
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch devices: {e}") from e

    def fetch_entities(self) -> List[Dict[str, Any]]:
        """Fetch entities from Home Assistant."""
        try:
            # Fetch the entity registry file
            remote_path = f"{self.config_dir}/.storage/core.entity_registry"
            local_path = ".storage/core.entity_registry"
            self.fetch_file(remote_path, local_path)
            
            # Read and parse the file
            with open(local_path, 'r') as f:
                entity_registry = json.load(f)
            
            return entity_registry['data']['entities']
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch entities: {e}") from e

    def fetch_automations(self) -> List[Dict[str, Any]]:
        """Fetch automations from Home Assistant."""
        try:
            automations = []
            
            # Try to fetch automations from a directory first
            try:
                command = f"ls -1 {self.config_dir}/automations/"
                files = self.execute_command(command).splitlines()
                
                for file in files:
                    if file.endswith('.yaml') or file.endswith('.yml'):
                        remote_path = f"{self.config_dir}/automations/{file}"
                        local_path = f"automations/{file}"
                        self.fetch_file(remote_path, local_path)
                        
                        # Read and parse the file
                        with open(local_path, 'r') as f:
                            import yaml
                            automation = yaml.safe_load(f)
                            automations.append(automation)
            except Exception:
                # If directory doesn't exist, try to fetch automations.yaml
                try:
                    remote_path = f"{self.config_dir}/automations.yaml"
                    local_path = "automations/automations.yaml"
                    self.fetch_file(remote_path, local_path)
                    
                    # Read and parse the file
                    with open(local_path, 'r') as f:
                        import yaml
                        automations_data = yaml.safe_load(f)
                        
                        # Handle both list and dict formats
                        if isinstance(automations_data, list):
                            automations = automations_data
                        elif isinstance(automations_data, dict):
                            # If it's a dict with automation IDs as keys
                            automations = list(automations_data.values())
                except Exception:
                    # If neither works, return empty list
                    pass
            
            return automations
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch automations: {e}") from e
    
    def fetch_configuration_files(self) -> Dict[str, Any]:
        """Fetch all configuration YAML files from Home Assistant."""
        try:
            config_files = {}
            
            # Fetch main configuration.yaml
            try:
                remote_path = f"{self.config_dir}/configuration.yaml"
                local_path = "configuration.yaml"
                self.fetch_file(remote_path, local_path)
                # Copy the file as-is since it may contain !include tags
                import shutil
                shutil.copy(local_path, "input/configuration.yaml")
                config_files['configuration'] = "File copied as-is due to !include tags"
            except Exception as e:
                print(f"Warning: Could not fetch configuration.yaml: {e}")
            
            # Fetch automations.yaml
            try:
                remote_path = f"{self.config_dir}/automations.yaml"
                local_path = "automations.yaml"
                self.fetch_file(remote_path, local_path)
                # Copy the file as-is
                shutil.copy(local_path, "input/automations.yaml")
                config_files['automations'] = "File copied as-is"
            except Exception as e:
                print(f"Warning: Could not fetch automations.yaml: {e}")
            
            # Fetch scripts.yaml
            try:
                remote_path = f"{self.config_dir}/scripts.yaml"
                local_path = "scripts.yaml"
                self.fetch_file(remote_path, local_path)
                # Copy the file as-is
                shutil.copy(local_path, "input/scripts.yaml")
                config_files['scripts'] = "File copied as-is"
            except Exception as e:
                print(f"Warning: Could not fetch scripts.yaml: {e}")
            
            # Fetch scenes.yaml
            try:
                remote_path = f"{self.config_dir}/scenes.yaml"
                local_path = "scenes.yaml"
                self.fetch_file(remote_path, local_path)
                # Copy the file as-is
                shutil.copy(local_path, "input/scenes.yaml")
                config_files['scenes'] = "File copied as-is"
            except Exception as e:
                print(f"Warning: Could not fetch scenes.yaml: {e}")
            
            return config_files
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch configuration files: {e}") from e
    
    def copy_storage_directory(self, local_dest_path: str):
        """Copy the entire .storage directory from Home Assistant."""
        try:
            if self.use_docker:
                # Copy the entire .storage directory from Docker container
                # Note: docker cp creates the target directory, so we copy to a temp location first
                temp_copy_path = f"{local_dest_path}.temp"
                subprocess.run([
                    "docker", "cp", 
                    f"{self.docker_container}:{self.config_dir}/.storage", 
                    temp_copy_path
                ], check=True)
                
                # Move the contents from the temp .storage directory to the actual destination
                temp_storage_path = f"{temp_copy_path}/.storage"
                if os.path.exists(temp_storage_path):
                    # Ensure destination exists
                    os.makedirs(local_dest_path, exist_ok=True)
                    
                    # Move all contents from temp .storage to destination
                    for item in os.listdir(temp_storage_path):
                        src = os.path.join(temp_storage_path, item)
                        dst = os.path.join(local_dest_path, item)
                        if os.path.exists(dst):
                            if os.path.isdir(src):
                                shutil.rmtree(dst)
                            else:
                                os.remove(dst)
                        shutil.move(src, dst)
                    
                    # Remove the temp directory
                    shutil.rmtree(temp_copy_path)
                else:
                    # Fallback to direct copy if structure is different
                    shutil.move(temp_copy_path, local_dest_path)
            else:
                # For SSH, we would need to use scp or rsync
                raise NotImplementedError("SSH storage directory copy not implemented yet")
        except Exception as e:
            raise RuntimeError(f"Failed to copy storage directory: {e}") from e

    def deploy_config(self, config_type: str, config_data: Dict[str, Any]):
        """Deploy a configuration to Home Assistant."""
        try:
            # Determine the file path based on config type
            if config_type == "areas":
                remote_path = f"{self.config_dir}/.storage/core.area_registry"
                local_path = ".storage/core.area_registry"
            elif config_type == "devices":
                remote_path = f"{self.config_dir}/.storage/core.device_registry"
                local_path = ".storage/core.device_registry"
            elif config_type == "entities":
                remote_path = f"{self.config_dir}/.storage/core.entity_registry"
                local_path = ".storage/core.entity_registry"
            else:
                raise ValueError(f"Unknown config type: {config_type}")
            
            # Write the config data to a local file
            with open(local_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Deploy the file
            self.deploy_file(local_path, remote_path)
            
        except Exception as e:
            raise RuntimeError(f"Failed to deploy config: {e}") from e

    def deploy_automation(self, automation_name: str, automation_data: Dict[str, Any]):
        """Deploy an automation to Home Assistant."""
        try:
            # Write the automation to a local file
            local_path = f"automations/{automation_name}.yaml"
            with open(local_path, 'w') as f:
                import yaml
                yaml.dump(automation_data, f)
            
            # Deploy the file
            remote_path = f"{self.config_dir}/automations/{automation_name}.yaml"
            self.deploy_file(local_path, remote_path)
            
        except Exception as e:
            raise RuntimeError(f"Failed to deploy automation: {e}") from e

    def copy_storage_directory(self, local_dest_path: str):
        """Copy the entire .storage directory from Home Assistant."""
        try:
            if self.use_docker:
                # Copy the entire .storage directory from Docker container
                subprocess.run([
                    "docker", "cp", 
                    f"{self.docker_container}:{self.config_dir}/.storage", 
                    local_dest_path
                ], check=True)
            else:
                # For SSH, we would need to use scp or rsync
                raise NotImplementedError("SSH storage directory copy not implemented yet")
        except Exception as e:
            raise RuntimeError(f"Failed to copy storage directory: {e}") from e
