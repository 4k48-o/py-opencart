"""
Tortoise ORM model for user_group table
"""

from tortoise.models import Model
from tortoise import fields


class UserGroup(Model):
    """
    UserGroup model
    
    Represents the user_group table in the OpenCart database.
    
    Attributes:
        user_group_id (int(11)) - Primary key
        name (varchar(64)), nullable
        permission (text), nullable
    """

    user_group_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=True)
    permission = fields.TextField(null=True)

    class Meta:
        table = "oc_user_group"

