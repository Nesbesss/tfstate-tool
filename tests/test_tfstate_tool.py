"""
Unit tests for tfstate-tool.
"""

import json
import tempfile
import unittest
from pathlib import Path

from tfstate_tool.core import TerraformStateManager

class TestTerraformStateManager(unittest.TestCase):
    """Test cases for TerraformStateManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_state = {
            "version": 4,
            "terraform_version": "1.0.0",
            "serial": 1,
            "lineage": "test-lineage",
            "outputs": {},
            "resources": [
                {
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "test_instance",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": [
                        {
                            "schema_version": 1,
                            "attributes": {
                                "ami": "ami-12345678",
                                "instance_type": "t3.micro",
                                "tags": {
                                    "Name": "TestInstance",
                                    "Environment": "test"
                                }
                            }
                        }
                    ]
                }
            ]
        }
        
        # Create temporary state file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.tfstate', delete=False)
        json.dump(self.sample_state, self.temp_file, indent=2)
        self.temp_file.close()
        
        self.manager = TerraformStateManager(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        Path(self.temp_file.name).unlink(missing_ok=True)
    
    def test_load_state(self):
        """Test loading state file."""
        self.assertIsNotNone(self.manager.state_data)
        self.assertEqual(self.manager.state_data["version"], 4)
        self.assertEqual(len(self.manager.state_data["resources"]), 1)
    
    def test_list_resources(self):
        """Test listing resources."""
        resources = self.manager.list_resources()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["address"], "aws_instance.test_instance")
        self.assertEqual(resources[0]["type"], "aws_instance")
        self.assertEqual(resources[0]["name"], "test_instance")
    
    def test_filter_resources_by_type(self):
        """Test filtering resources by type."""
        resources = self.manager.list_resources(resource_type="aws_instance")
        self.assertEqual(len(resources), 1)
        
        resources = self.manager.list_resources(resource_type="aws_s3_bucket")
        self.assertEqual(len(resources), 0)
    
    def test_get_resource(self):
        """Test getting a specific resource."""
        resource = self.manager.get_resource("aws_instance.test_instance")
        self.assertIsNotNone(resource)
        self.assertEqual(resource["type"], "aws_instance")
        self.assertEqual(resource["name"], "test_instance")
        
        # Test non-existent resource
        resource = self.manager.get_resource("aws_instance.nonexistent")
        self.assertIsNone(resource)
    
    def test_export_resource(self):
        """Test exporting a resource to JSON."""
        export_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        export_file.close()
        
        try:
            success = self.manager.export_resource("aws_instance.test_instance", export_file.name)
            self.assertTrue(success)
            
            # Verify exported content
            with open(export_file.name, 'r') as f:
                exported_data = json.load(f)
            
            self.assertEqual(exported_data["type"], "aws_instance")
            self.assertEqual(exported_data["name"], "test_instance")
            
        finally:
            Path(export_file.name).unlink(missing_ok=True)
    
    def test_modify_resource_attribute(self):
        """Test modifying a resource attribute."""
        success = self.manager.modify_resource_attribute(
            "aws_instance.test_instance",
            "instances.0.attributes.tags.Environment",
            "production"
        )
        self.assertTrue(success)
        
        # Verify the change
        resource = self.manager.get_resource("aws_instance.test_instance")
        env_tag = resource["instances"][0]["attributes"]["tags"]["Environment"]
        self.assertEqual(env_tag, "production")
    
    def test_delete_resource(self):
        """Test deleting a resource."""
        # Verify resource exists
        resource = self.manager.get_resource("aws_instance.test_instance")
        self.assertIsNotNone(resource)
        
        # Delete the resource
        success = self.manager.delete_resource("aws_instance.test_instance")
        self.assertTrue(success)
        
        # Verify resource is gone
        resource = self.manager.get_resource("aws_instance.test_instance")
        self.assertIsNone(resource)
        
        # Verify resources list is empty
        resources = self.manager.list_resources()
        self.assertEqual(len(resources), 0)
    
    def test_move_resource(self):
        """Test moving (renaming) a resource."""
        success = self.manager.move_resource(
            "aws_instance.test_instance",
            "aws_instance.renamed_instance"
        )
        self.assertTrue(success)
        
        # Verify old resource is gone
        old_resource = self.manager.get_resource("aws_instance.test_instance")
        self.assertIsNone(old_resource)
        
        # Verify new resource exists
        new_resource = self.manager.get_resource("aws_instance.renamed_instance")
        self.assertIsNotNone(new_resource)
        self.assertEqual(new_resource["name"], "renamed_instance")
    
    def test_validate_state(self):
        """Test state validation."""
        is_valid, errors = self.manager.validate_state()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_create_backup(self):
        """Test creating a backup."""
        backup_path = self.manager.create_backup()
        self.assertTrue(Path(backup_path).exists())
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        self.assertEqual(backup_data["version"], 4)
        self.assertEqual(len(backup_data["resources"]), 1)
        
        # Clean up
        Path(backup_path).unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()