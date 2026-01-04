"""
Tortoise ORM model for category table
"""

from tortoise.models import Model
from tortoise import fields


class Category(Model):
    """
    Category model
    
    Represents the category table in the OpenCart database.
    
    Attributes:
        category_id (int(11)) - Primary key
        image (varchar(255)), nullable
        parent_id (int(11)), nullable, default: 0
        sort_order (int(3)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
    """

    category_id = fields.IntField(pk=True)
    image = fields.CharField(max_length=255, null=True)
    parent_id = fields.IntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_category"
        indexes = [("parent_id",)]

