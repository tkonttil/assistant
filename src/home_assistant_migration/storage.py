"""
Storage logic for Home Assistant data.
"""

import os
import toml
from typing import Dict, Any, List
from .models import Area, Device, Automation, EntityState


class Storage:
    """Storage logic for Home Assistant data."""

    def __init__(self, base_path: str = "migration"):
        """Initialize the storage."""
        self.base_path = base_path
        self.current_path = os.path.join(base_path, "current")
        self.desired_path = os.path.join(base_path, "desired")
        self.migrations_path = os.path.join(base_path, "migrations")
        
        # Ensure directories exist
        os.makedirs(self.current_path, exist_ok=True)
        os.makedirs(self.desired_path, exist_ok=True)
        os.makedirs(self.migrations_path, exist_ok=True)

    def store_current_setup(self, data: Dict[str, Any]) -> None:
        """Store the current setup in the migration/current directory."""
        print(f"Storing current setup in {self.current_path}")
        
        # Store config
        config_path = os.path.join(self.current_path, "config.toml")
        with open(config_path, "w") as f:
            toml.dump(data["config"], f)
        
        # Store entities
        entities_path = os.path.join(self.current_path, "entities.toml")
        with open(entities_path, "w") as f:
            toml.dump(self._convert_entities_to_dict(data["entities"]), f)
        
        # Store states
        states_path = os.path.join(self.current_path, "states.toml")
        with open(states_path, "w") as f:
            toml.dump(self._convert_states_to_dict(data["states"]), f)
        
        # Store domains
        domains_path = os.path.join(self.current_path, "domains.toml")
        with open(domains_path, "w") as f:
            # Convert domains to a simple list format
            domains_list = list(data["domains"])
            toml.dump({"domains": domains_list}, f)

    def _convert_entities_to_dict(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Convert entities to a dictionary for TOML storage."""
        result = {}
        for domain, group in entities.items():
            result[domain] = {}
            for entity_name, entity in group.entities.items():
                result[domain][entity_name] = {
                    "entity_id": entity.state.entity_id,
                    "state": entity.state.state,
                    "attributes": entity.state.attributes,
                }
        return result

    def _convert_states_to_dict(self, states: List[EntityState]) -> Dict[str, Any]:
        """Convert states to a dictionary for TOML storage."""
        result = {}
        for state in states:
            result[state.entity_id] = {
                "state": state.state,
                "attributes": state.attributes,
            }
        return result

    def load_current_setup(self) -> Dict[str, Any]:
        """Load the current setup from the migration/current directory."""
        data = {}
        
        # Load config
        config_path = os.path.join(self.current_path, "config.toml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data["config"] = toml.load(f)
        
        # Load entities
        entities_path = os.path.join(self.current_path, "entities.toml")
        if os.path.exists(entities_path):
            with open(entities_path, "r") as f:
                data["entities"] = toml.load(f)
        
        # Load states
        states_path = os.path.join(self.current_path, "states.toml")
        if os.path.exists(states_path):
            with open(states_path, "r") as f:
                data["states"] = toml.load(f)
        
        # Load domains
        domains_path = os.path.join(self.current_path, "domains.toml")
        if os.path.exists(domains_path):
            with open(domains_path, "r") as f:
                data["domains"] = toml.load(f)
        
        return data