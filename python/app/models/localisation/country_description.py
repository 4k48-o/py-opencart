"""
Tortoise ORM model for country_description table
"""

from tortoise.models import Model
from tortoise import fields
from .language import Language


class CountryDescription(Model):
    """
    CountryDescription model
    
    Represents the country_description table in the OpenCart database.
    
    Attributes:
        country_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(255)), nullable
    """

    country_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_country_description"
        indexes = [("name",)]
        unique_together = (("country_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
