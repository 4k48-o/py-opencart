"""
Tortoise ORM model for option_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class OptionDescription(Model):
    """
    OptionDescription model
    
    Represents the option_description table in the OpenCart database.
    
    Attributes:
        option_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(128)), nullable
    """

    option_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=128, null=True)

    class Meta:
        table = "oc_option_description"
        unique_together = (("option_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
