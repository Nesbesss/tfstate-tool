# tfstate-tool

A Python CLI tool for safely managing Terraform state files (`terraform.tfstate`).

## Features

- **List Resources**: Display a tree-like view of all resources and their types
- **Filter Resources**: Filter by resource type or name patterns
- **Export to JSON**: Export specific resources to separate JSON files
- **Modify Values**: Update resource attributes in the state file
- **Delete Resources**: Remove resources from state (terraform forget equivalent)
- **Move Resources**: Rename/move resource addresses (terraform state mv equivalent)
- **Automatic Backup**: Creates backups before any destructive operations

## Installation

```bash
git clone https://github.com/Nesbesss/tfstate-tool.git
cd tfstate-tool
pip install -r requirements.txt
pip install -e .
```

## Usage

### Basic Commands

```bash
# List all resources
tfstate-tool list terraform.tfstate

# Filter resources by type
tfstate-tool list terraform.tfstate --type aws_instance

# Filter resources by name pattern
tfstate-tool list terraform.tfstate --name "*web*"

# Export a resource to JSON
tfstate-tool export terraform.tfstate aws_instance.web_server output.json

# Modify a resource attribute
tfstate-tool modify terraform.tfstate aws_instance.web_server tags.Environment production

# Move a resource
tfstate-tool move terraform.tfstate aws_instance.old_name aws_instance.new_name

# Delete a resource from state
tfstate-tool delete terraform.tfstate aws_instance.unused_server
```

### Example Usage

See `examples/main.py` for demonstration of the core functionality.

## Safety Features

- Automatic backup creation before any modifications
- Confirmation prompts for destructive operations
- State file validation before and after operations
- Rollback capability using backups

## Development

```bash
# Run tests
python -m pytest tests/

# Install in development mode
pip install -e .
```

## License

MIT License