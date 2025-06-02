#!/usr/bin/env python3
"""
Example usage of tfstate-tool functionality.

This demonstrates how to use the TerraformStateManager class directly
and shows the main CLI operations.
"""

import json
import tempfile
from pathlib import Path

from tfstate_tool.core import TerraformStateManager
from tfstate_tool.operations import TerraformStateOperations

def create_sample_state_file():
    """Create a sample Terraform state file for demonstration."""
    sample_state = {
        "version": 4,
        "terraform_version": "1.0.0",
        "serial": 1,
        "lineage": "example-lineage",
        "outputs": {},
        "resources": [
            {
                "mode": "managed",
                "type": "aws_instance",
                "name": "web_server",
                "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 1,
                        "attributes": {
                            "ami": "ami-12345678",
                            "instance_type": "t3.micro",
                            "tags": {
                                "Name": "WebServer",
                                "Environment": "development"
                            },
                            "vpc_security_group_ids": ["sg-12345678"],
                            "subnet_id": "subnet-12345678"
                        }
                    }
                ]
            },
            {
                "mode": "managed",
                "type": "aws_instance",
                "name": "database_server",
                "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 1,
                        "attributes": {
                            "ami": "ami-87654321",
                            "instance_type": "t3.small",
                            "tags": {
                                "Name": "DatabaseServer",
                                "Environment": "development"
                            },
                            "vpc_security_group_ids": ["sg-87654321"],
                            "subnet_id": "subnet-87654321"
                        }
                    }
                ]
            },
            {
                "mode": "managed",
                "type": "aws_s3_bucket",
                "name": "app_bucket",
                "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 0,
                        "attributes": {
                            "bucket": "my-app-bucket-12345",
                            "tags": {
                                "Purpose": "Application Storage",
                                "Environment": "development"
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.tfstate', delete=False)
    json.dump(sample_state, temp_file, indent=2)
    temp_file.close()
    
    return temp_file.name

def demonstrate_basic_operations():
    """Demonstrate basic tfstate-tool operations."""
    print("🚀 tfstate-tool Example Demonstration")
    print("=" * 50)
    
    # Create sample state file
    state_file = create_sample_state_file()
    print(f"📄 Created sample state file: {state_file}")
    
    try:
        # Initialize the manager
        print("\n1. Initializing TerraformStateManager...")
        manager = TerraformStateManager(state_file)
        print("✅ State file loaded successfully!")
        
        # List all resources
        print("\n2. Listing all resources...")
        resources = manager.list_resources()
        for resource in resources:
            print(f"   📦 {resource['address']} ({resource['instances']} instance(s))")
        
        # Filter by type
        print("\n3. Filtering by type 'aws_instance'...")
        aws_instances = manager.list_resources(resource_type="aws_instance")
        for resource in aws_instances:
            print(f"   🖥️  {resource['address']}")
        
        # Get specific resource
        print("\n4. Getting specific resource 'aws_instance.web_server'...")
        web_server = manager.get_resource("aws_instance.web_server")
        if web_server:
            tags = web_server["instances"][0]["attributes"]["tags"]
            print(f"   🏷️  Tags: {tags}")
        
        # Export resource
        print("\n5. Exporting web_server to JSON...")
        export_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        export_file.close()
        
        if manager.export_resource("aws_instance.web_server", export_file.name):
            print(f"   💾 Exported to: {export_file.name}")
            with open(export_file.name, 'r') as f:
                exported_data = json.load(f)
                print(f"   📊 Exported {len(exported_data)} keys")
        
        # Create backup before modifications
        print("\n6. Creating backup before modifications...")
        backup_path = manager.create_backup()
        print(f"   💾 Backup created: {backup_path}")
        
        # Modify resource attribute
        print("\n7. Modifying resource attribute...")
        success = manager.modify_resource_attribute(
            "aws_instance.web_server", 
            "instances.0.attributes.tags.Environment", 
            "production"
        )
        if success:
            print("   ✅ Modified Environment tag to 'production'")
            manager._save_state()
            print("   💾 State file updated")
        
        # Verify modification
        web_server_updated = manager.get_resource("aws_instance.web_server")
        env_tag = web_server_updated["instances"][0]["attributes"]["tags"]["Environment"]
        print(f"   🔍 Verified Environment tag: {env_tag}")
        
        # Move resource (rename)
        print("\n8. Moving (renaming) resource...")
        success = manager.move_resource("aws_instance.database_server", "aws_instance.db_server")
        if success:
            print("   ✅ Moved database_server to db_server")
            manager._save_state()
        
        # List resources again to show the change
        print("\n9. Listing resources after move...")
        resources_after = manager.list_resources()
        for resource in resources_after:
            print(f"   📦 {resource['address']}")
        
        # Validate state
        print("\n10. Validating state file...")
        is_valid, errors = manager.validate_state()
        if is_valid:
            print("   ✅ State file is valid")
        else:
            print("   ❌ State file has errors:")
            for error in errors:
                print(f"      • {error}")
        
        print("\n🎉 Demonstration completed successfully!")
        print(f"\nFiles created during demo:")
        print(f"   📄 State file: {state_file}")
        print(f"   💾 Backup: {backup_path}")
        print(f"   📊 Export: {export_file.name}")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
    
    finally:
        # Clean up (optional - comment out to keep files for inspection)
        # Path(state_file).unlink(missing_ok=True)
        # Path(backup_path).unlink(missing_ok=True)
        # Path(export_file.name).unlink(missing_ok=True)
        pass

def demonstrate_cli_operations():
    """Demonstrate CLI-style operations using TerraformStateOperations."""
    print("\n" + "=" * 50)
    print("🎯 CLI Operations Demonstration")
    print("=" * 50)
    
    # Create sample state file
    state_file = create_sample_state_file()
    
    try:
        # Initialize operations
        ops = TerraformStateOperations(state_file)
        
        print("\n1. Pretty tree view of resources...")
        ops.list_resources_pretty()
        
        print("\n2. Table view of AWS instances only...")
        ops.list_resources_table(resource_type="aws_instance")
        
        print("\n3. Validating state file...")
        ops.validate_state_file()
        
        print("\n🎉 CLI operations demonstration completed!")
        
    except Exception as e:
        print(f"❌ Error during CLI demonstration: {e}")

def demonstrate_deletion():
    """Demonstrate resource deletion (commented out for safety)."""
    print("\n" + "=" * 50)
    print("⚠️  Resource Deletion Demonstration (Safe Mode)")
    print("=" * 50)
    
    state_file = create_sample_state_file()
    
    try:
        manager = TerraformStateManager(state_file)
        
        print("\nResources before deletion:")
        resources_before = manager.list_resources()
        for resource in resources_before:
            print(f"   📦 {resource['address']}")
        
        print(f"\nTotal resources: {len(resources_before)}")
        
        # Note: Actual deletion is commented out for safety
        # Uncomment the following lines to test deletion
        """
        print("\nDeleting aws_s3_bucket.app_bucket...")
        backup_path = manager.create_backup()
        print(f"Backup created: {backup_path}")
        
        success = manager.delete_resource("aws_s3_bucket.app_bucket")
        if success:
            manager._save_state()
            print("✅ Resource deleted successfully")
            
            print("\nResources after deletion:")
            resources_after = manager.list_resources()
            for resource in resources_after:
                print(f"   📦 {resource['address']}")
            
            print(f"Total resources: {len(resources_after)}")
        """
        
        print("\n💡 Deletion demonstration completed (in safe mode)")
        print("   Uncomment the deletion code in the script to test actual deletion")
        
    except Exception as e:
        print(f"❌ Error during deletion demonstration: {e}")

if __name__ == "__main__":
    # Run demonstrations
    demonstrate_basic_operations()
    demonstrate_cli_operations()
    demonstrate_deletion()
    
    print("\n" + "=" * 50)
    print("📖 Example CLI Commands:")
    print("=" * 50)
    print("# List all resources")
    print("tfstate-tool list terraform.tfstate")
    print()
    print("# List only AWS instances")
    print("tfstate-tool list terraform.tfstate --type aws_instance")
    print()
    print("# Export a resource")
    print("tfstate-tool export terraform.tfstate aws_instance.web_server web_server.json")
    print()
    print("# Modify a resource attribute")
    print("tfstate-tool modify terraform.tfstate aws_instance.web_server tags.Environment production")
    print()
    print("# Move/rename a resource")
    print("tfstate-tool move terraform.tfstate aws_instance.old aws_instance.new")
    print()
    print("# Delete a resource from state")
    print("tfstate-tool delete terraform.tfstate aws_instance.unused")
    print()
    print("# Validate state file")
    print("tfstate-tool validate terraform.tfstate")