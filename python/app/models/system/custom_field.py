"""
Tortoise ORM model for custom_field table
"""

from tortoise.models import Model
from tortoise import fields


class CustomField(Model):
    """
    CustomField model
    
    Represents the custom_field table in the OpenCart database.
    
    Attributes:
        custom_field_id (int(11)) - Primary key
        type (varchar(32)), nullable
        value (text), nullable
        validation (varchar(255)), nullable
        location (varchar(10)), nullable
        status (tinyint(1)), nullable, default: 0
        sort_order (int(3)), nullable, default: 0
    """

    custom_field_id = fields.IntField(pk=True)
    type = fields.CharField(max_length=32, null=True)
    value = fields.TextField(null=True)
    validation = fields.CharField(max_length=255, null=True)
    location = fields.CharField(max_length=10, null=True)
    status = fields.SmallIntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_custom_field"

