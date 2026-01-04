"""
Tortoise ORM model for module table
"""

from tortoise.models import Model
from tortoise import fields


class Module(Model):
    """
    Module model
    
    Represents the module table in the OpenCart database.
    
    Attributes:
        module_id (int(11)) - Primary key
        name (varchar(64)), nullable
        code (varchar(64)), nullable
        setting (text), nullable
    """

    module_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=True)
    code = fields.CharField(max_length=64, null=True)
    setting = fields.TextField(null=True)

    class Meta:
        table = "oc_module"

