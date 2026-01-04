"""
Tortoise ORM model for user table
"""

from tortoise.models import Model
from tortoise import fields
from .user_group import UserGroup


class User(Model):
    """
    User model
    
    Represents the user table in the OpenCart database.
    
    Attributes:
        user_id (int(11)) - Primary key
        user_group_id (int(11)), nullable, default: 0
        username (varchar(20)), nullable
        password (varchar(255)), nullable
        firstname (varchar(32)), nullable
        lastname (varchar(32)), nullable
        email (varchar(96)), nullable
        image (varchar(255)), nullable, default: 
        ip (varchar(40)), nullable, default: 
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    user_id = fields.IntField(pk=True)
    user_group_id = fields.IntField(null=True, default=0)
    username = fields.CharField(max_length=20, null=True)
    password = fields.CharField(max_length=255, null=True)
    firstname = fields.CharField(max_length=32, null=True)
    lastname = fields.CharField(max_length=32, null=True)
    email = fields.CharField(max_length=96, null=True)
    image = fields.CharField(max_length=255, null=True, default='')
    ip = fields.CharField(max_length=40, null=True, default='')
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_user"

    async def get_user_group(self):
        """Get related UserGroup"""
        if self.user_group_id:
            return await UserGroup.get(user_group_id=self.user_group_id)
        return None
