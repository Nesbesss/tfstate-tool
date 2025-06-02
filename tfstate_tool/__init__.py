"""
tfstate-tool: A Python CLI tool for managing Terraform state files.
"""

__version__ = "1.0.0"
__author__ = "Nesbesss"

from .core import TerraformStateManager

__all__ = ["TerraformStateManager"]