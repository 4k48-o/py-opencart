"""
Tortoise ORM model for filter_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class FilterDescription(Model):
    """
    FilterDescription model
    
    Represents the filter_description table in the OpenCart database.
    
    Attributes:
        filter_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(64)), nullable
    """

    filter_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_filter_description"
        unique_together = (("filter_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
