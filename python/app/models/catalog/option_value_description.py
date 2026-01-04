"""
Tortoise ORM model for option_value_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language
from .option import Option


class OptionValueDescription(Model):
    """
    OptionValueDescription model
    
    Represents the option_value_description table in the OpenCart database.
    
    Attributes:
        option_value_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        option_id (int(11)), nullable
        name (varchar(128)), nullable
    """

    option_value_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    option_id = fields.IntField(null=True)
    name = fields.CharField(max_length=128, null=True)

    class Meta:
        table = "oc_option_value_description"
        unique_together = (("option_value_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
    async def get_option(self):
        """Get related Option"""
        if self.option_id:
            return await Option.get(option_id=self.option_id)
        return None
