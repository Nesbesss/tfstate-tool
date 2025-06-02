"""
High-level operations for the tfstate-tool.
"""

import os
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Confirm

from .core import TerraformStateManager

console = Console()

class TerraformStateOperations:
    """High-level operations wrapper for TerraformStateManager."""
    
    def __init__(self, state_file: str):
        """Initialize operations with a state file."""
        self.manager = TerraformStateManager(state_file)
        self.state_file = state_file
    
    def list_resources_pretty(self, resource_type: Optional[str] = None,
                             name_pattern: Optional[str] = None) -> None:
        """Display resources in a pretty tree format."""
        resources = self.manager.list_resources(resource_type, name_pattern)
        
        if not resources:
            console.print("[yellow]No resources found matching criteria[/yellow]")
            return
        
        # Group by type
        by_type = {}
        for resource in resources:
            rtype = resource["type"]
            if rtype not in by_type:
                by_type[rtype] = []
            by_type[rtype].append(resource)
        
        # Create tree
        tree = Tree("🏗️  Terraform Resources")
        
        for rtype, type_resources in sorted(by_type.items()):
            type_branch = tree.add(f"📦 {rtype} ({len(type_resources)} instances)")
            
            for resource in sorted(type_resources, key=lambda x: x["name"]):
                resource_branch = type_branch.add(
                    f"🔧 {resource['name']} "
                    f"[dim]({resource['instances']} instance{'s' if resource['instances'] != 1 else ''})[/dim]"
                )
        
        console.print(tree)
        console.print(f"\n[green]Total: {len(resources)} resources[/green]")
    
    def list_resources_table(self, resource_type: Optional[str] = None,
                            name_pattern: Optional[str] = None) -> None:
        """Display resources in a table format."""
        resources = self.manager.list_resources(resource_type, name_pattern)
        
        if not resources:
            console.print("[yellow]No resources found matching criteria[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Address", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Name", style="yellow")
        table.add_column("Mode", style="blue")
        table.add_column("Instances", justify="right", style="red")
        
        for resource in sorted(resources, key=lambda x: x["address"]):
            table.add_row(
                resource["address"],
                resource["type"],
                resource["name"],
                resource["mode"],
                str(resource["instances"])
            )
        
        console.print(table)
        console.print(f"\n[green]Total: {len(resources)} resources[/green]")
    
    def export_resource_safe(self, address: str, output_file: str) -> bool:
        """Export a resource with user confirmation if file exists."""
        if os.path.exists(output_file):
            if not Confirm.ask(f"File {output_file} exists. Overwrite?"):
                console.print("[yellow]Export cancelled[/yellow]")
                return False
        
        if self.manager.export_resource(address, output_file):
            console.print(f"[green]Resource {address} exported to {output_file}[/green]")
            return True
        else:
            console.print(f"[red]Resource {address} not found[/red]")
            return False
    
    def modify_resource_safe(self, address: str, attribute_path: str, 
                           new_value: str) -> bool:
        """Modify a resource attribute with backup and confirmation."""
        # Check if resource exists
        if not self.manager.get_resource(address):
            console.print(f"[red]Resource {address} not found[/red]")
            return False
        
        # Confirm the operation
        console.print(f"[yellow]Modifying {address}:{attribute_path} = {new_value}[/yellow]")
        if not Confirm.ask("Continue with modification?"):
            console.print("[yellow]Modification cancelled[/yellow]")
            return False
        
        # Create backup
        backup_path = self.manager.create_backup()
        console.print(f"[blue]Backup created: {backup_path}[/blue]")
        
        try:
            # Try to convert value to appropriate type
            converted_value = self._convert_value(new_value)
            
            if self.manager.modify_resource_attribute(address, attribute_path, converted_value):
                self.manager._save_state()
                console.print(f"[green]Successfully modified {address}[/green]")
                return True
            else:
                console.print(f"[red]Failed to modify {address}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error during modification: {e}[/red]")
            return False
    
    def delete_resource_safe(self, address: str) -> bool:
        """Delete a resource with backup and confirmation."""
        # Check if resource exists
        if not self.manager.get_resource(address):
            console.print(f"[red]Resource {address} not found[/red]")
            return False
        
        # Confirm the operation
        console.print(f"[red]WARNING: This will delete {address} from the state file![/red]")
        console.print("[yellow]This does not destroy the actual resource in your cloud provider.[/yellow]")
        
        if not Confirm.ask("Are you sure you want to continue?"):
            console.print("[yellow]Deletion cancelled[/yellow]")
            return False
        
        # Create backup
        backup_path = self.manager.create_backup()
        console.print(f"[blue]Backup created: {backup_path}[/blue]")
        
        try:
            if self.manager.delete_resource(address):
                self.manager._save_state()
                console.print(f"[green]Successfully deleted {address} from state[/green]")
                return True
            else:
                console.print(f"[red]Failed to delete {address}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error during deletion: {e}[/red]")
            return False
    
    def move_resource_safe(self, old_address: str, new_address: str) -> bool:
        """Move a resource with backup and confirmation."""
        # Check if old resource exists
        if not self.manager.get_resource(old_address):
            console.print(f"[red]Resource {old_address} not found[/red]")
            return False
        
        # Check if new address already exists
        if self.manager.get_resource(new_address):
            console.print(f"[red]Resource {new_address} already exists[/red]")
            return False
        
        # Confirm the operation
        console.print(f"[yellow]Moving {old_address} → {new_address}[/yellow]")
        if not Confirm.ask("Continue with move?"):
            console.print("[yellow]Move cancelled[/yellow]")
            return False
        
        # Create backup
        backup_path = self.manager.create_backup()
        console.print(f"[blue]Backup created: {backup_path}[/blue]")
        
        try:
            if self.manager.move_resource(old_address, new_address):
                self.manager._save_state()
                console.print(f"[green]Successfully moved {old_address} to {new_address}[/green]")
                return True
            else:
                console.print(f"[red]Failed to move {old_address}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error during move: {e}[/red]")
            return False
    
    def validate_state_file(self) -> bool:
        """Validate the state file and report any issues."""
        is_valid, errors = self.manager.validate_state()
        
        if is_valid:
            console.print("[green]✅ State file is valid[/green]")
        else:
            console.print("[red]❌ State file has validation errors:[/red]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
        
        return is_valid
    
    def _convert_value(self, value_str: str):
        """Convert string value to appropriate Python type."""
        # Try to parse as JSON first (handles booleans, numbers, null, objects, arrays)
        try:
            import json
            return json.loads(value_str)
        except json.JSONDecodeError:
            # If not valid JSON, return as string
            return
