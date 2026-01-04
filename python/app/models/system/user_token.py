"""
Tortoise ORM model for user_token table
"""

from tortoise.models import Model
from tortoise import fields
from .user import User


class UserToken(Model):
    """
    UserToken model
    
    Represents the user_token table in the OpenCart database.
    
    Attributes:
        user_token_id (int(11)) - Primary key
        user_id (int(11)), nullable
        code (text), nullable
        type (varchar(10)), nullable
        date_added (datetime), nullable
    """

    user_token_id = fields.IntField(pk=True)
    user_id = fields.IntField(null=True)
    code = fields.TextField(null=True)
    type = fields.CharField(max_length=10, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_user_token"

    async def get_user(self):
        """Get related User"""
        if self.user_id:
            return await User.get(user_id=self.user_id)
        return None
