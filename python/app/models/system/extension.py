"""
Tortoise ORM model for extension table
"""

from tortoise.models import Model
from tortoise import fields


class Extension(Model):
    """
    Extension model
    
    Represents the extension table in the OpenCart database.
    
    Attributes:
        extension_id (int(11)) - Primary key
        extension (varchar(255)), nullable
        type (varchar(32)), nullable
        code (varchar(128)), nullable
    """

    extension_id = fields.IntField(pk=True)
    extension = fields.CharField(max_length=255, null=True)
    type = fields.CharField(max_length=32, null=True)
    code = fields.CharField(max_length=128, null=True)

    class Meta:
        table = "oc_extension"

