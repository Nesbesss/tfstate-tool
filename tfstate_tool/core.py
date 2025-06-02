"""
Core functionality for Terraform state file management.
"""

import json
import os
import shutil
import fnmatch
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

class TerraformStateManager:
    """Main class for managing Terraform state files."""
    
    def __init__(self, state_file: str):
        """Initialize with a state file path."""
        self.state_file = Path(state_file)
        self.state_data = None
        self._load_state()
    
    def _load_state(self) -> None:
        """Load and validate the Terraform state file."""
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in state file: {e}")
        
        # Basic validation
        if not isinstance(self.state_data, dict):
            raise ValueError("State file must contain a JSON object")
        
        if "resources" not in self.state_data:
            raise ValueError("State file missing 'resources' key")
    
    def _save_state(self) -> None:
        """Save the current state data back to the file."""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state_data, f, indent=2)
    
    def create_backup(self) -> str:
        """Create a backup of the current state file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.state_file}.backup_{timestamp}"
        shutil.copy2(self.state_file, backup_path)
        return backup_path
    
    def list_resources(self, resource_type: Optional[str] = None, 
                      name_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all resources, optionally filtered by type or name pattern."""
        resources = []
        
        for resource in self.state_data.get("resources", []):
            resource_info = {
                "address": f"{resource.get('type', 'unknown')}.{resource.get('name', 'unknown')}",
                "type": resource.get("type"),
                "name": resource.get("name"),
                "mode": resource.get("mode", "managed"),
                "instances": len(resource.get("instances", []))
            }
            
            # Apply filters
            if resource_type and resource_info["type"] != resource_type:
                continue
            
            if name_pattern and not fnmatch.fnmatch(resource_info["address"], name_pattern):
                continue
            
            resources.append(resource_info)
        
        return resources
    
    def get_resource(self, address: str) -> Optional[Dict[str, Any]]:
        """Get a specific resource by its address."""
        try:
            resource_type, resource_name = address.split(".", 1)
        except ValueError:
            raise ValueError(f"Invalid resource address format: {address}")
        
        for resource in self.state_data.get("resources", []):
            if (resource.get("type") == resource_type and 
                resource.get("name") == resource_name):
                return resource
        
        return None
    
    def export_resource(self, address: str, output_file: str) -> bool:
        """Export a specific resource to a JSON file."""
        resource = self.get_resource(address)
        if not resource:
            return False
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resource, f, indent=2)
        
        return True
    
    def modify_resource_attribute(self, address: str, attribute_path: str, 
                                 new_value: Any) -> bool:
        """Modify a specific attribute of a resource."""
        resource = self.get_resource(address)
        if not resource:
            return False
        
        # Navigate to the attribute
        keys = attribute_path.split(".")
        current = resource
        
        # Navigate to the parent of the target attribute
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the new value
        current[keys[-1]] = new_value
        
        return True
    
    def delete_resource(self, address: str) -> bool:
        """Delete a resource from the state file."""
        try:
            resource_type, resource_name = address.split(".", 1)
        except ValueError:
            raise ValueError(f"Invalid resource address format: {address}")
        
        resources = self.state_data.get("resources", [])
        original_count = len(resources)
        
        # Remove the resource
        self.state_data["resources"] = [
            r for r in resources 
            if not (r.get("type") == resource_type and r.get("name") == resource_name)
        ]
        
        return len(self.state_data["resources"]) < original_count
    
    def move_resource(self, old_address: str, new_address: str) -> bool:
        """Move (rename) a resource from old_address to new_address."""
        resource = self.get_resource(old_address)
        if not resource:
            return False
        
        try:
            new_type, new_name = new_address.split(".", 1)
        except ValueError:
            raise ValueError(f"Invalid new address format: {new_address}")
        
        # Check if new address already exists
        if self.get_resource(new_address):
            raise ValueError(f"Resource already exists at address: {new_address}")
        
        # Update the resource
        resource["type"] = new_type
        resource["name"] = new_name
        
        return True
    
    def validate_state(self) -> Tuple[bool, List[str]]:
        """Validate the current state structure."""
        errors = []
        
        if not isinstance(self.state_data, dict):
            errors.append("State data must be a dictionary")
            return False, errors
        
        if "resources" not in self.state_data:
            errors.append("Missing 'resources' key")
        
        if "version" not in self.state_data:
            errors.append("Missing 'version' key")
        
        resources = self.state_data.get("resources", [])
        if not isinstance(resources, list):
            errors.append("'resources' must be a list")
        
        # Validate each resource
        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                errors.append(f"Resource {i} must be a dictionary")
                continue
            
            if "type" not in resource:
                errors.append(f"Resource {i} missing 'type'")
            
            if "name" not in resource:
                errors.append(f"Resource {i} missing 'name'")
        
        return len(errors) == 0, errors