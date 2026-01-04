"""
Tortoise ORM model for banner_image table
"""

from tortoise.models import Model
from tortoise import fields
from .banner import Banner
from ..localisation.language import Language


class BannerImage(Model):
    """
    BannerImage model
    
    Represents the banner_image table in the OpenCart database.
    
    Attributes:
        banner_image_id (int(11)) - Primary key
        banner_id (int(11)), nullable
        language_id (int(11)), nullable
        title (varchar(64)), nullable
        link (varchar(255)), nullable
        image (varchar(255)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    banner_image_id = fields.IntField(pk=True)
    banner_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    title = fields.CharField(max_length=64, null=True)
    link = fields.CharField(max_length=255, null=True)
    image = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_banner_image"

    async def get_banner(self):
        """Get related Banner"""
        if self.banner_id:
            return await Banner.get(banner_id=self.banner_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
