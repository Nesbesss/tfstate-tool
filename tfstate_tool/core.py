"""
Core functionality for Terraform state file management.
"""

import json
import os
import shutil
import fnmatch
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
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
    
    def _navigate_to_path(self, data: Any, path_parts: List[str]) -> Tuple[Any, str]:
        """Navigate to a path in the data structure, handling arrays and objects.
        
        Returns:
            Tuple of (parent_object, final_key) where the value should be set
        """
        current = data
        
        # Navigate to the parent of the target attribute
        for i, key in enumerate(path_parts[:-1]):
            # Check if this key represents an array index
            if key.isdigit():
                index = int(key)
                if not isinstance(current, list):
                    raise ValueError(f"Expected list at path component '{key}', got {type(current)}")
                if index >= len(current):
                    raise ValueError(f"Index {index} out of range for list of length {len(current)}")
                current = current[index]
            else:
                # It's a dictionary key
                if not isinstance(current, dict):
                    raise ValueError(f"Expected dict at path component '{key}', got {type(current)}")
                if key not in current:
                    current[key] = {}
                current = current[key]
        
        return current, path_parts[-1]
    
    def modify_resource_attribute(self, address: str, attribute_path: str, 
                                 new_value: Any) -> bool:
        """Modify a specific attribute of a resource."""
        resource = self.get_resource(address)
        if not resource:
            return False
        
        # Split the path and navigate to the target
        keys = attribute_path.split(".")
        
        try:
            parent, final_key = self._navigate_to_path(resource, keys)
            
            # Handle the final key (could be array index or dict key)
            if final_key.isdigit():
                index = int(final_key)
                if not isinstance(parent, list):
                    raise ValueError(f"Expected list for index {final_key}, got {type(parent)}")
                if index >= len(parent):
                    raise ValueError(f"Index {index} out of range for list of length {len(parent)}")
                parent[index] = new_value
            else:
                if not isinstance(parent, dict):
                    raise ValueError(f"Expected dict for key {final_key}, got {type(parent)}")
                parent[final_key] = new_value
            
            return True
            
        except (ValueError, IndexError, KeyError) as e:
            print(f"Error modifying attribute: {e}")
            return False
    
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
