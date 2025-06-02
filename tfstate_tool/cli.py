"""
Command-line interface for tfstate-tool.
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from .operations import TerraformStateOperations
from .utils import validate_state_file_path, find_state_files, setup_logging

console = Console()

def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="A tool for managing Terraform state files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tfstate-tool list terraform.tfstate
  tfstate-tool list terraform.tfstate --type aws_instance
  tfstate-tool export terraform.tfstate aws_instance.web output.json
  tfstate-tool modify terraform.tfstate aws_instance.web tags.env prod
  tfstate-tool move terraform.tfstate aws_instance.old aws_instance.new
  tfstate-tool delete terraform.tfstate aws_instance.unused
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List resources in state file")
    list_parser.add_argument("state_file", help="Path to terraform.tfstate file")
    list_parser.add_argument("--type", help="Filter by resource type")
    list_parser.add_argument("--name", help="Filter by name pattern (supports wildcards)")
    list_parser.add_argument("--format", choices=["tree", "table"], default="tree",
                           help="Output format (default: tree)")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export resource to JSON")
    export_parser.add_argument("state_file", help="Path to terraform.tfstate file")
    export_parser.add_argument("address", help="Resource address (e.g., aws_instance.web)")
    export_parser.add_argument("output_file", help="Output JSON file path")
    
    # Modify command
    modify_parser = subparsers.add_parser("modify", help="Modify resource attribute")
    modify_parser.add_argument("state_file", help="Path to terraform.tfstate file")
    modify_parser.add_argument("address", help="Resource address (e.g., aws_instance.web)")
    modify_parser.add_argument("attribute", help="Attribute path (e.g., tags.Environment)")
    modify_parser.add_argument("value", help="New value")
    
    # Move command
    move_parser = subparsers.add_parser("move", help="Move/rename resource")
    move_parser.add_argument("state_file", help="Path to terraform.tfstate file")
    move_parser.add_argument("old_address", help="Current resource address")
    move_parser.add_argument("new_address", help="New resource address")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete resource from state")
    delete_parser.add_argument("state_file", help="Path to terraform.tfstate file")
    delete_parser.add_argument("address", help="Resource address to delete")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate state file")
    validate_parser.add_argument("state_file", help="Path to terraform.tfstate file")
    
    # Find command
    find_parser = subparsers.add_parser("find", help="Find state files in directory")
    find_parser.add_argument("directory", nargs="?", default=".", help="Directory to search")
    
    return parser

def handle_list_command(args) -> int:
    """Handle the list command."""
    try:
        ops = TerraformStateOperations(args.state_file)
        
        if args.format == "tree":
            ops.list_resources_pretty(args.type, args.name)
        else:
            ops.list_resources_table(args.type, args.name)
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

def handle_export_command(args) -> int:
    """Handle the export command."""
    try:
        ops = TerraformStateOperations(args.state_file)
        
        if ops.export_resource_safe(args.address, args.output_file):
            return 0
        else:
            return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

def handle_modify_command(args) -> int:
    """Handle the modify command."""
    try:
        ops = TerraformStateOperations(args.state_file)
        
        if ops.modify_resource_safe(args.address, args.attribute, args.value):
            return 0
        else:
            return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

def handle_move_command(args) -> int:
    """Handle the move command."""
    try:
        ops = TerraformStateOperations(args.state_file)
        
        if ops.move_resource_safe(args.old_address, args.new_address):
            return 0
        else:
            return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

def handle_delete_command(args) -> int:
    """Handle the delete command."""
    try:
        ops = TerraformStateOperations(args.state_file)
        
        if ops.delete_resource_safe(args.address):
            return 0
        else:
            return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

def handle_validate_command(args) -> int:
    """Handle the validate command."""
    try:
        ops = TerraformStateOperations(args.state_file)
        
        if ops.validate_state_file():
            return 0
        else:
            return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

def handle_find_command(args) -> int:
    """Handle the find command."""
    try:
        state_files = find_state_files(args.directory)
        
        if not state_files:
            console.print(f"[yellow]No .tfstate files found in {args.directory}[/yellow]")
            return 1
        
        console.print(f"[green]Found {len(state_files)} state file(s):[/green]")
        for state_file in sorted(state_files):
            console.print(f"  📄 {state_file}")
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Validate state file for commands that need it
    if args.command != "find" and hasattr(args, 'state_file'):
        if not validate_state_file_path(args.state_file):
            console.print(f"[red]Error: State file not found or not readable: {args.state_file}[/red]")
            return 1
    
    # Route to appropriate handler
    handlers = {
        "list": handle_list_command,
        "export": handle_export_command,
        "modify": handle_modify_command,
        "move": handle_move_command,
        "delete": handle_delete_command,
        "validate": handle_validate_command,
        "find": handle_find_command,
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        console.print(f"[red]Unknown command: {args.command}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())