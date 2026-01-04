"""
Tortoise ORM model for return_action table
"""

from tortoise.models import Model
from tortoise import fields
from .language import Language


class ReturnAction(Model):
    """
    ReturnAction model
    
    Represents the return_action table in the OpenCart database.
    
    Attributes:
        return_action_id (int(11)) - Primary key
        language_id (int(11)) - Primary key, default: 0
        name (varchar(64)), nullable
    """

    return_action_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_return_action"
        unique_together = (("return_action_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
