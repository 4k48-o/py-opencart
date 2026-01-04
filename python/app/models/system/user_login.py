"""
Tortoise ORM model for user_login table
"""

from tortoise.models import Model
from tortoise import fields
from .user import User


class UserLogin(Model):
    """
    UserLogin model
    
    Represents the user_login table in the OpenCart database.
    
    Attributes:
        user_login_id (int(11)) - Primary key
        user_id (int(11)), nullable
        ip (varchar(40)), nullable
        user_agent (varchar(255)), nullable
        date_added (datetime), nullable
    """

    user_login_id = fields.IntField(pk=True)
    user_id = fields.IntField(null=True)
    ip = fields.CharField(max_length=40, null=True)
    user_agent = fields.CharField(max_length=255, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_user_login"

    async def get_user(self):
        """Get related User"""
        if self.user_id:
            return await User.get(user_id=self.user_id)
        return None
