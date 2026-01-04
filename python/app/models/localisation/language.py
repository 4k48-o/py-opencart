"""
Tortoise ORM model for language table
"""

from tortoise.models import Model
from tortoise import fields


class Language(Model):
    """
    Language model
    
    Represents the language table in the OpenCart database.
    
    Attributes:
        language_id (int(11)) - Primary key
        name (varchar(32)), nullable
        code (varchar(5)), nullable
        locale (varchar(255)), nullable
        extension (varchar(255)), nullable
        sort_order (int(3)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
    """

    language_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32, null=True)
    code = fields.CharField(max_length=5, null=True)
    locale = fields.CharField(max_length=255, null=True)
    extension = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_language"
        indexes = [("name",)]

