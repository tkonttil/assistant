"""
Tools for designing the desired setup in migration/desired directory.
"""

import os
import toml
from typing import Dict, Any, List
from .models import Area, Device, Automation


class DesiredSetup:
    """Tools for designing the desired setup."""

    def __init__(self, base_path: str = "migration"):
        """Initialize the desired setup tools."""
        self.base_path = base_path
        self.desired_path = os.path.join(base_path, "desired")
        
        # Ensure directories exist
        os.makedirs(self.desired_path, exist_ok=True)
        os.makedirs(os.path.join(self.desired_path, "areas"), exist_ok=True)
        os.makedirs(os.path.join(self.desired_path, "devices"), exist_ok=True)
        os.makedirs(os.path.join(self.desired_path, "automations"), exist_ok=True)

    def create_area(self, area: Area) -> None:
        """Create an area in the desired setup."""
        area_path = os.path.join(self.desired_path, "areas", f"{area.id}.toml")
        with open(area_path, "w") as f:
            toml.dump({
                "id": area.id,
                "name": area.name,
                "devices": area.devices,
            }, f)

    def create_device(self, device: Device) -> None:
        """Create a device in the desired setup."""
        device_path = os.path.join(self.desired_path, "devices", f"{device.id}.toml")
        with open(device_path, "w") as f:
            toml.dump({
                "id": device.id,
                "name": device.name,
                "area": device.area,
                "model": device.model,
                "manufacturer": device.manufacturer,
                "capabilities": device.capabilities,
            }, f)

    def create_automation(self, automation: Automation) -> None:
        """Create an automation in the desired setup."""
        automation_path = os.path.join(self.desired_path, "automations", f"{automation.id}.toml")
        with open(automation_path, "w") as f:
            toml.dump({
                "id": automation.id,
                "name": automation.name,
                "trigger": automation.trigger,
                "action": automation.action,
                "condition": automation.condition,
            }, f)

    def load_area(self, area_id: str) -> Area:
        """Load an area from the desired setup."""
        area_path = os.path.join(self.desired_path, "areas", f"{area_id}.toml")
        if not os.path.exists(area_path):
            raise FileNotFoundError(f"Area {area_id} not found")
        
        with open(area_path, "r") as f:
            data = toml.load(f)
        
        return Area(**data)

    def load_device(self, device_id: str) -> Device:
        """Load a device from the desired setup."""
        device_path = os.path.join(self.desired_path, "devices", f"{device_id}.toml")
        if not os.path.exists(device_path):
            raise FileNotFoundError(f"Device {device_id} not found")
        
        with open(device_path, "r") as f:
            data = toml.load(f)
        
        return Device(**data)

    def load_automation(self, automation_id: str) -> Automation:
        """Load an automation from the desired setup."""
        automation_path = os.path.join(self.desired_path, "automations", f"{automation_id}.toml")
        if not os.path.exists(automation_path):
            raise FileNotFoundError(f"Automation {automation_id} not found")
        
        with open(automation_path, "r") as f:
            data = toml.load(f)
        
        return Automation(**data)

    def list_areas(self) -> List[str]:
        """List all areas in the desired setup."""
        areas_path = os.path.join(self.desired_path, "areas")
        if not os.path.exists(areas_path):
            return []
        
        return [f.replace(".toml", "") for f in os.listdir(areas_path) if f.endswith(".toml")]

    def list_devices(self) -> List[str]:
        """List all devices in the desired setup."""
        devices_path = os.path.join(self.desired_path, "devices")
        if not os.path.exists(devices_path):
            return []
        
        return [f.replace(".toml", "") for f in os.listdir(devices_path) if f.endswith(".toml")]

    def list_automations(self) -> List[str]:
        """List all automations in the desired setup."""
        automations_path = os.path.join(self.desired_path, "automations")
        if not os.path.exists(automations_path):
            return []
        
        return [f.replace(".toml", "") for f in os.listdir(automations_path) if f.endswith(".toml")]

    def delete_area(self, area_id: str) -> None:
        """Delete an area from the desired setup."""
        area_path = os.path.join(self.desired_path, "areas", f"{area_id}.toml")
        if os.path.exists(area_path):
            os.remove(area_path)

    def delete_device(self, device_id: str) -> None:
        """Delete a device from the desired setup."""
        device_path = os.path.join(self.desired_path, "devices", f"{device_id}.toml")
        if os.path.exists(device_path):
            os.remove(device_path)

    def delete_automation(self, automation_id: str) -> None:
        """Delete an automation from the desired setup."""
        automation_path = os.path.join(self.desired_path, "automations", f"{automation_id}.toml")
        if os.path.exists(automation_path):
            os.remove(automation_path)