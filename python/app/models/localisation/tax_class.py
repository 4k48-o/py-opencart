"""
Tortoise ORM model for tax_class table
"""

from tortoise.models import Model
from tortoise import fields


class TaxClass(Model):
    """
    TaxClass model
    
    Represents the tax_class table in the OpenCart database.
    
    Attributes:
        tax_class_id (int(11)) - Primary key
        title (varchar(32)), nullable
        description (varchar(255)), nullable
    """

    tax_class_id = fields.IntField(pk=True)
    title = fields.CharField(max_length=32, null=True)
    description = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_tax_class"

