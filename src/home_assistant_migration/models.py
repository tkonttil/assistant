"""
Data models for Home Assistant entities.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Area(BaseModel):
    """Model for an area in Home Assistant."""
    id: str
    name: str
    devices: List[str] = []


class Device(BaseModel):
    """Model for a device in Home Assistant."""
    id: str
    name: str
    area: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    capabilities: List[str] = []


class Automation(BaseModel):
    """Model for an automation in Home Assistant."""
    id: str
    name: str
    trigger: Dict[str, Any]
    action: Dict[str, Any]
    condition: Optional[Dict[str, Any]] = None


class EntityState(BaseModel):
    """Model for an entity state in Home Assistant."""
    entity_id: str
    state: str
    attributes: Dict[str, Any] = {}


class Migration(BaseModel):
    """Model for a migration script."""
    id: str
    description: str
    changes: List[Dict[str, Any]]
    dependencies: List[str] = []
    rollback: Optional[List[Dict[str, Any]]] = None